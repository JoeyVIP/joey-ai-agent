import logging
import re
from typing import Optional

from src.services.notion_service import notion_service
from src.services.claude_service import claude_service
from src.services.claude_code_service import claude_code_service
from src.services.line_service import line_service
from src.models.claude_response import ClaudeResponse

logger = logging.getLogger(__name__)


def extract_result_urls(output: str) -> dict:
    """Extract URLs from Claude Code output with ---RESULT--- format."""
    result = {
        "github_url": None,
        "deploy_url": None,
        "deploy_platform": None,
        "project_name": None,
        "status": None
    }

    # Try to find the structured result block
    result_match = re.search(r'---RESULT---(.+?)---END---', output, re.DOTALL)
    if result_match:
        block = result_match.group(1)

        project_match = re.search(r'PROJECT_NAME:\s*(.+)', block)
        if project_match:
            result["project_name"] = project_match.group(1).strip()

        github_match = re.search(r'GITHUB_URL:\s*(.+)', block)
        if github_match:
            result["github_url"] = github_match.group(1).strip()

        deploy_match = re.search(r'DEPLOY_URL:\s*(.+)', block)
        if deploy_match:
            result["deploy_url"] = deploy_match.group(1).strip()

        platform_match = re.search(r'DEPLOY_PLATFORM:\s*(.+)', block)
        if platform_match:
            result["deploy_platform"] = platform_match.group(1).strip()

        status_match = re.search(r'STATUS:\s*(.+)', block)
        if status_match:
            result["status"] = status_match.group(1).strip()

    # Fallback: try to find Render URLs in the output (priority)
    if not result["deploy_url"]:
        render_match = re.search(r'https://[a-zA-Z0-9-]+\.onrender\.com[^\s]*', output)
        if render_match:
            result["deploy_url"] = render_match.group(0).rstrip('/')
            result["deploy_platform"] = "Render"

    # Try Railway URLs as second option
    if not result["deploy_url"]:
        railway_match = re.search(r'https://[a-zA-Z0-9-]+\.up\.railway\.app[^\s]*', output)
        if railway_match:
            result["deploy_url"] = railway_match.group(0).rstrip('/')
            result["deploy_platform"] = "Railway"

    # Only use GitHub Pages as last resort and mark it
    if not result["deploy_url"]:
        ghpages_match = re.search(r'https://[a-zA-Z0-9-]+\.github\.io/[a-zA-Z0-9-]+', output)
        if ghpages_match:
            result["deploy_url"] = ghpages_match.group(0)
            result["deploy_platform"] = "GitHub Pages (警告：應使用 Render)"

    if not result["github_url"]:
        github_match = re.search(r'https://github\.com/[a-zA-Z0-9-]+/[a-zA-Z0-9-]+', output)
        if github_match:
            result["github_url"] = github_match.group(0)

    return result


class TaskProcessor:
    """
    Core task processing logic with two-stage execution:
    Stage 1: Claude API analyzes the task (fast, seconds)
    Stage 2: Claude Code executes complex tasks (can take minutes to hours)
    """

    async def process_task(
        self,
        user_input: str,
        source: str = "line",
        reply_token: Optional[str] = None
    ) -> None:
        """
        Main task processing flow:
        1. Create Inbox task
        2. Read Memory
        3. Stage 1: Claude API analyzes task
        4. Create Review task (with status)
        5. Stage 2: If complex, execute with Claude Code
        6. Update Memory (if needed)
        7. Delete Inbox task
        8. Push notification to Joey
        """
        inbox_task_id = None
        review_task_id = None

        try:
            # Step 1: Create Inbox task
            logger.info("Creating inbox task...")
            title = user_input[:50] + "..." if len(user_input) > 50 else user_input
            inbox_task_id = await notion_service.create_inbox_task(
                title=title,
                raw_input=user_input,
                source=source
            )
            logger.info(f"Inbox task created: {inbox_task_id}")

            # Update status to processing
            await notion_service.update_inbox_status(inbox_task_id, "processing")

            # Step 2: Read Memory
            logger.info("Reading memories...")
            memories = await notion_service.format_memories_for_prompt()

            # ============================================
            # Stage 1: Claude API Analysis (fast)
            # ============================================
            logger.info("Stage 1: Calling Claude API for task analysis...")
            response = await claude_service.process_task(
                user_input=user_input,
                memories=memories
            )
            logger.info(f"Claude response - difficulty: {response.difficulty}")

            # Step 4: Create Review task
            logger.info("Creating review task...")
            review_task_id = await self._create_review_task(response, inbox_task_id)

            # Notify Joey that task is being processed
            if response.difficulty == "complex":
                await line_service.push_to_joey(
                    f"📝 任務已建立：{response.title}\n\n"
                    f"難度：複雜任務\n"
                    f"狀態：執行中...\n\n"
                    f"我會在完成後通知你。"
                )

            # ============================================
            # Stage 2: Claude Code Execution (for complex tasks)
            # ============================================
            if response.difficulty == "complex" and response.complex_result:
                logger.info("Stage 2: Executing complex task with Claude Code...")

                # Update review task status to executing
                await notion_service.update_review_task_status(review_task_id, "executing")

                # Execute with Claude Code (Ralph Wiggum retry loop enabled)
                # 長時間任務支援：每次迭代最多 6 小時，最多重試 10 次
                # 理論上可以跑 60 小時（2.5 天）
                execution_result = await claude_code_service.execute_task_with_retry(
                    prompt=response.complex_result.prompt_for_claude_code,
                    title=response.title,
                    max_retries=10,  # 最多重試 10 次
                    timeout_seconds=21600  # 每次最多 6 小時
                )

                # Update review task with result
                if execution_result["success"]:
                    await notion_service.update_review_task_result(
                        page_id=review_task_id,
                        status="completed",
                        result=execution_result["output"][:2000],
                        folder_path=execution_result["folder_path"]
                    )

                    # Extract URLs from output
                    urls = extract_result_urls(execution_result["output"])

                    # Build Notion URL
                    notion_url = f"https://notion.so/{review_task_id.replace('-', '')}"

                    # Send simplified success notification
                    message_parts = [f"✅ {response.title}"]

                    if urls["deploy_url"]:
                        message_parts.append(f"\n🌐 {urls['deploy_url']}")

                    message_parts.append(f"\n📋 {notion_url}")

                    await line_service.push_to_joey("".join(message_parts))
                else:
                    await notion_service.update_review_task_result(
                        page_id=review_task_id,
                        status="failed",
                        result=f"執行失敗：{execution_result['error']}"
                    )

                    # Send failure notification
                    await line_service.push_to_joey(
                        f"❌ 任務失敗：{response.title}\n\n"
                        f"錯誤：{execution_result['error'][:300]}"
                    )
            else:
                # Simple task - just send the result
                await line_service.push_to_joey(response.line_message)

            # Step 5: Update Memory (if needed)
            if response.memory_updates:
                logger.info(f"Processing {len(response.memory_updates)} memory updates...")
                await self._process_memory_updates(response)

            # Step 6: Delete Inbox task
            logger.info("Deleting inbox task...")
            await notion_service.delete_inbox_task(inbox_task_id)

            logger.info("Task processing completed successfully")

        except Exception as e:
            logger.error(f"Error processing task: {e}", exc_info=True)

            # Try to notify Joey about the error
            try:
                error_message = f"❌ 處理任務時發生錯誤\n\n原始訊息：{user_input[:100]}...\n\n錯誤：{str(e)[:200]}"
                await line_service.push_to_joey(error_message)
            except Exception as notify_error:
                logger.error(f"Failed to send error notification: {notify_error}")

            # Update review task status to failed if it exists
            if review_task_id:
                try:
                    await notion_service.update_review_task_result(
                        page_id=review_task_id,
                        status="failed",
                        result=f"錯誤：{str(e)[:500]}"
                    )
                except Exception:
                    pass

            # Clean up inbox task if it was created
            if inbox_task_id:
                try:
                    await notion_service.delete_inbox_task(inbox_task_id)
                except Exception:
                    pass

            raise

    async def _create_review_task(
        self,
        response: ClaudeResponse,
        source_task_id: str
    ) -> str:
        """Create appropriate review task based on difficulty."""

        if response.difficulty == "simple" and response.simple_result:
            return await notion_service.create_review_task_simple(
                title=response.title,
                summary=response.simple_result.summary,
                result=response.simple_result.result,
                source_task_id=source_task_id
            )
        elif response.difficulty == "complex" and response.complex_result:
            return await notion_service.create_review_task_complex(
                title=response.title,
                summary=response.complex_result.summary,
                analysis=response.complex_result.analysis,
                preparation=response.complex_result.preparation,
                prompt_for_claude_code=response.complex_result.prompt_for_claude_code,
                estimated_time=response.complex_result.estimated_time,
                reason=response.complex_result.reason,
                source_task_id=source_task_id
            )
        else:
            # Fallback: create simple task with available info
            return await notion_service.create_review_task_simple(
                title=response.title,
                summary="無法解析完整回應",
                result=response.line_message,
                source_task_id=source_task_id
            )

    async def _process_memory_updates(self, response: ClaudeResponse) -> None:
        """Process memory updates from Claude response."""

        for update in response.memory_updates:
            try:
                if update.action == "create":
                    await notion_service.create_memory(
                        title=update.title,
                        category=update.category or "context",
                        content=update.content,
                        importance=update.importance or "medium"
                    )
                    logger.info(f"Created memory: {update.title}")

                elif update.action == "update":
                    # Find existing memory by title
                    existing = await notion_service.find_memory_by_title(update.title)
                    if existing:
                        await notion_service.update_memory(
                            page_id=existing["id"],
                            content=update.content,
                            importance=update.importance
                        )
                        logger.info(f"Updated memory: {update.title}")
                    else:
                        # Create if not found
                        await notion_service.create_memory(
                            title=update.title,
                            category=update.category or "context",
                            content=update.content,
                            importance=update.importance or "medium"
                        )
                        logger.info(f"Created memory (not found for update): {update.title}")

            except Exception as e:
                logger.error(f"Error processing memory update '{update.title}': {e}")


task_processor = TaskProcessor()
