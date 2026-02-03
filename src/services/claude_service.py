import asyncio
import json
import logging
from pathlib import Path
from anthropic import Anthropic

from src.config import settings
from src.constants import CLAUDE_MAX_TOKENS
from src.models.claude_response import ClaudeResponse

logger = logging.getLogger(__name__)


class ClaudeService:
    """Claude API 服務"""
    def __init__(self):
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.anthropic_model
        self._system_prompt = None

    @property
    def system_prompt(self) -> str:
        """Load system prompt from file (cached)."""
        if self._system_prompt is None:
            prompt_path = Path(__file__).parent.parent / "prompts" / "system_prompt.md"
            self._system_prompt = prompt_path.read_text(encoding="utf-8")
        return self._system_prompt

    async def process_task(
        self,
        user_input: str,
        memories: str
    ) -> ClaudeResponse:
        """Process a task with Claude and return structured response."""
        logger.info(f"呼叫 Claude API，模型: {self.model}")
        logger.debug(f"使用者輸入: {user_input[:100]}...")

        # Build the user message with context
        user_message = f"""## Joey 的記憶

{memories}

---

## Joey 的任務

{user_input}

---

請以 JSON 格式回應。"""

        try:
            # Call Claude API (使用 to_thread 避免阻塞事件循環)
            response = await asyncio.to_thread(
                self.client.messages.create,
                model=self.model,
                max_tokens=CLAUDE_MAX_TOKENS,
                system=self.system_prompt,
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )

            # Extract text content
            content = response.content[0].text
            logger.info(f"Claude API 回應成功，內容長度: {len(content)} 字元")

            # Parse JSON from response
            parsed = self._parse_json_response(content)

            return parsed

        except Exception as e:
            logger.error(f"Claude API 呼叫失敗: {e}", exc_info=True)
            raise

    def _parse_json_response(self, content: str) -> ClaudeResponse:
        """Parse JSON response from Claude, handling various formats."""

        # Try to find JSON in the response
        json_str = content

        # Handle markdown code blocks
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            json_str = content[start:end].strip()
            logger.debug("從 ```json 區塊提取 JSON")
        elif "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            json_str = content[start:end].strip()
            logger.debug("從 ``` 區塊提取 JSON")

        # Parse JSON
        try:
            data = json.loads(json_str)
            logger.debug(f"JSON 解析成功，難度: {data.get('difficulty', 'unknown')}")
        except json.JSONDecodeError as e:
            # If parsing fails, create a fallback response
            logger.warning(f"JSON 解析失敗，使用備用回應: {e}")
            logger.debug(f"原始內容: {content[:200]}...")
            return ClaudeResponse(
                difficulty="simple",
                title="處理結果",
                simple_result={
                    "summary": "AI 回應（非結構化）",
                    "result": content
                },
                memory_updates=[],
                line_message="處理完成，請查看 Notion Review"
            )

        # Validate and create ClaudeResponse
        return ClaudeResponse(**data)


claude_service = ClaudeService()
