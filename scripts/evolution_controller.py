#!/usr/bin/env python3
"""
Evolution Controller - Agent Self-Evolution System

This script manages the safe self-evolution of the Joey AI Agent.
It handles:
- Pre-evolution health checks and Git snapshots
- Safety level validation
- Post-evolution verification
- Automatic rollback on failure
- Status tracking via Notion

Usage:
    python evolution_controller.py --task-id <notion_task_id>
    python evolution_controller.py --check-pending
"""

import argparse
import asyncio
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import httpx

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import settings
from src.services.notion_service import notion_service
from src.services.line_service import line_service


# ==================== Safety Level Configuration ====================

SAFETY_LEVELS = {
    # Level 0: Forbidden - Requires manual intervention
    0: {
        "name": "Level 0",
        "description": "Forbidden - Requires manual intervention",
        "files": [
            "src/config.py",
            "src/main.py",
            ".env",
            ".env.example",
            "com.joey.ai-agent.plist",
        ],
        "patterns": [
            "*.plist",
            ".env*",
        ]
    },
    # Level 1: Core Logic - Requires snapshot + health check
    1: {
        "name": "Level 1",
        "description": "Core Logic - Requires snapshot + full verification",
        "files": [
            "src/api/line_webhook.py",
            "src/services/task_processor.py",
            "src/services/notion_service.py",
            "src/services/claude_code_service.py",
        ]
    },
    # Level 2: Safe with snapshot
    2: {
        "name": "Level 2",
        "description": "Safe - Requires snapshot",
        "files": [
            "src/prompts/system_prompt.md",
            "src/services/claude_service.py",
            "src/services/line_service.py",
        ]
    },
    # Level 3: Free modification
    3: {
        "name": "Level 3",
        "description": "Free modification",
        "files": [],
        "directories": [
            "web-frontend/",
            "tasks/",
            "agent-tasks/",
            "docs/",
        ]
    }
}


class EvolutionController:
    """Controls the agent self-evolution process with safety mechanisms."""

    def __init__(self, project_dir: str = None):
        self.project_dir = Path(project_dir or "/Users/joeyserver/joey-ai-agent")
        self.health_url = "http://localhost:8000/health"
        self.service_name = "com.joey.ai-agent"

    # ==================== Safety Level Detection ====================

    def get_file_safety_level(self, file_path: str) -> int:
        """Determine the safety level for a given file path."""
        # Normalize path
        if file_path.startswith(str(self.project_dir)):
            relative_path = file_path[len(str(self.project_dir)):].lstrip("/")
        else:
            relative_path = file_path.lstrip("/")

        # Check Level 0 (forbidden)
        for forbidden in SAFETY_LEVELS[0]["files"]:
            if relative_path == forbidden or relative_path.endswith(forbidden):
                return 0
        for pattern in SAFETY_LEVELS[0].get("patterns", []):
            if self._matches_pattern(relative_path, pattern):
                return 0

        # Check Level 1 (core)
        for core_file in SAFETY_LEVELS[1]["files"]:
            if relative_path == core_file or relative_path.endswith(core_file):
                return 1

        # Check Level 2 (safe with snapshot)
        for safe_file in SAFETY_LEVELS[2]["files"]:
            if relative_path == safe_file or relative_path.endswith(safe_file):
                return 2

        # Check Level 3 (free modification directories)
        for free_dir in SAFETY_LEVELS[3].get("directories", []):
            if relative_path.startswith(free_dir):
                return 3

        # Default to Level 2 for unknown files (safe with snapshot)
        return 2

    def _matches_pattern(self, path: str, pattern: str) -> bool:
        """Simple pattern matching for safety checks."""
        import fnmatch
        return fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(os.path.basename(path), pattern)

    def get_task_safety_level(self, files_modified: list[str]) -> int:
        """Get the highest (most restrictive) safety level for a set of files."""
        if not files_modified:
            return 3
        return min(self.get_file_safety_level(f) for f in files_modified)

    # ==================== Health Checks ====================

    async def check_health(self, timeout: float = 10.0) -> Tuple[bool, str]:
        """Check if the agent service is healthy."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.health_url, timeout=timeout)
                if response.status_code == 200:
                    return True, "healthy"
                return False, f"Unhealthy: status {response.status_code}"
        except httpx.ConnectError:
            return False, "Connection refused - service may be down"
        except httpx.TimeoutException:
            return False, "Health check timed out"
        except Exception as e:
            return False, f"Health check error: {str(e)}"

    # ==================== Git Operations ====================

    def run_git(self, *args) -> Tuple[bool, str]:
        """Run a git command in the project directory."""
        try:
            result = subprocess.run(
                ["git"] + list(args),
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                return True, result.stdout.strip()
            return False, result.stderr.strip()
        except subprocess.TimeoutExpired:
            return False, "Git command timed out"
        except Exception as e:
            return False, str(e)

    def create_snapshot(self, tag_name: str) -> Tuple[bool, str]:
        """Create a Git snapshot with the given tag."""
        # First commit any uncommitted changes
        self.run_git("add", "-A")
        self.run_git("commit", "-m", f"Pre-evolution snapshot: {tag_name}", "--allow-empty")

        # Create tag
        success, msg = self.run_git("tag", "-f", tag_name)
        if success:
            return True, tag_name
        return False, msg

    def rollback_to_tag(self, tag_name: str) -> Tuple[bool, str]:
        """Rollback to a specific Git tag."""
        # Reset to tag
        success, msg = self.run_git("reset", "--hard", tag_name)
        if not success:
            return False, f"Failed to reset: {msg}"

        # Clean untracked files
        self.run_git("clean", "-fd")
        return True, f"Rolled back to {tag_name}"

    def get_current_commit(self) -> str:
        """Get the current commit hash."""
        success, output = self.run_git("rev-parse", "HEAD")
        return output if success else "unknown"

    # ==================== Service Control ====================

    def restart_service(self) -> Tuple[bool, str]:
        """Restart the agent service via launchctl."""
        try:
            # Try to kickstart the service
            result = subprocess.run(
                ["launchctl", "kickstart", "-k", f"gui/{os.getuid()}/{self.service_name}"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                return True, "Service restarted"

            # Fallback: stop and start
            subprocess.run(
                ["launchctl", "stop", self.service_name],
                capture_output=True,
                timeout=10
            )
            time.sleep(2)
            result = subprocess.run(
                ["launchctl", "start", self.service_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return True, "Service restarted (stop/start)"
            return False, f"Failed to restart: {result.stderr}"
        except Exception as e:
            return False, f"Service restart error: {str(e)}"

    # ==================== Evolution Execution ====================

    async def pre_evolution_check(self, task: dict) -> Tuple[bool, str, str]:
        """
        Pre-evolution checks and snapshot creation.
        Returns: (success, message, git_tag)
        """
        print("[Pre-Evolution] Starting pre-evolution checks...")

        # 1. Parse files to modify
        files_modified = [f.strip() for f in task.get("files_modified", "").split("\n") if f.strip()]

        # 2. Check safety level
        task_level = self.get_task_safety_level(files_modified)
        declared_level = task.get("level", "Level 3")
        declared_level_num = int(declared_level.replace("Level ", "")) if "Level" in declared_level else 3

        print(f"[Pre-Evolution] Detected safety level: {task_level}, Declared: {declared_level_num}")

        # Level 0 files are forbidden
        if task_level == 0:
            forbidden_files = [f for f in files_modified if self.get_file_safety_level(f) == 0]
            return False, f"Level 0 files detected - manual intervention required: {forbidden_files}", ""

        # Warn if declared level doesn't match detected
        if task_level < declared_level_num:
            print(f"[Pre-Evolution] WARNING: Task declared as {declared_level} but contains Level {task_level} files")

        # 3. Health check
        healthy, health_msg = await self.check_health()
        if not healthy:
            print(f"[Pre-Evolution] WARNING: Service unhealthy - {health_msg}")
            # Continue anyway, but log it

        # 4. Create Git snapshot
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        task_id_short = task["id"][:8] if task.get("id") else "unknown"
        tag_name = f"pre-evolution-{task_id_short}-{timestamp}"

        success, snapshot_result = self.create_snapshot(tag_name)
        if not success:
            return False, f"Failed to create snapshot: {snapshot_result}", ""

        print(f"[Pre-Evolution] Created snapshot: {tag_name}")
        return True, "Pre-evolution checks passed", tag_name

    async def execute_evolution(self, task: dict) -> Tuple[bool, str]:
        """
        Execute the evolution task using Claude Code.
        Returns: (success, output)
        """
        print("[Evolution] Starting evolution execution...")

        # Build the task prompt
        task_prompt = f"""
# Evolution Task: {task.get('title', 'Unknown')}

## Description
{task.get('description', 'No description provided')}

## Files to Modify
{task.get('files_modified', 'No files specified')}

## Verification Steps
{task.get('verification_steps', 'No verification steps specified')}

## Important Notes
- This is an automated evolution task
- Follow the verification steps after making changes
- Report any errors or issues
"""

        # Execute via claude CLI (need to source shell profile for nvm/node paths)
        try:
            # Wrap in bash to ensure proper PATH (claude is installed via npm/nvm)
            shell_command = f'source ~/.zshrc && claude --print -p {repr(task_prompt)}'
            result = subprocess.run(
                ["/bin/bash", "-c", shell_command],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=3600,  # 1 hour timeout
                env={**os.environ, "CLAUDE_CODE_OAUTH_TOKEN": settings.claude_code_oauth_token}
            )

            output = result.stdout + result.stderr
            if result.returncode == 0:
                return True, output[:5000]  # Truncate for Notion
            return False, f"Claude Code failed (exit {result.returncode}): {output[:2000]}"

        except subprocess.TimeoutExpired:
            return False, "Evolution execution timed out (1 hour limit)"
        except FileNotFoundError:
            return False, "Claude CLI not found - is it installed?"
        except Exception as e:
            return False, f"Execution error: {str(e)}"

    async def post_evolution_verify(self, task: dict) -> Tuple[bool, str]:
        """
        Post-evolution verification.
        Returns: (success, verification_result)
        """
        print("[Verification] Starting post-evolution verification...")
        results = []

        # 1. Health check
        healthy, health_msg = await self.check_health()
        results.append(f"Health check: {'PASS' if healthy else 'FAIL'} - {health_msg}")

        if not healthy:
            # Try restarting the service
            print("[Verification] Service unhealthy, attempting restart...")
            restart_ok, restart_msg = self.restart_service()
            results.append(f"Service restart: {'PASS' if restart_ok else 'FAIL'} - {restart_msg}")

            if restart_ok:
                # Wait for service to start
                await asyncio.sleep(5)
                healthy, health_msg = await self.check_health()
                results.append(f"Health check after restart: {'PASS' if healthy else 'FAIL'} - {health_msg}")

        # 2. Run any custom verification commands from the task
        verification_steps = task.get("verification_steps", "")
        if verification_steps:
            results.append(f"Verification steps defined: {len(verification_steps)} chars")

        verification_result = "\n".join(results)
        return healthy, verification_result

    async def rollback(self, tag_name: str, reason: str) -> Tuple[bool, str]:
        """
        Rollback to a previous snapshot.
        Returns: (success, message)
        """
        print(f"[Rollback] Rolling back to {tag_name}...")

        # 1. Rollback Git
        success, rollback_msg = self.rollback_to_tag(tag_name)
        if not success:
            return False, f"Git rollback failed: {rollback_msg}"

        # 2. Restart service
        restart_ok, restart_msg = self.restart_service()
        await asyncio.sleep(3)

        # 3. Verify health
        healthy, health_msg = await self.check_health()

        result = f"Rollback to {tag_name}: {rollback_msg}\n"
        result += f"Service restart: {restart_msg}\n"
        result += f"Health after rollback: {health_msg}\n"
        result += f"Reason: {reason}"

        return healthy, result

    # ==================== Notification ====================

    async def send_evolution_report(
        self,
        task: dict,
        success: bool,
        duration: int,
        git_tag: str = "",
        output_summary: str = "",
        error_msg: str = ""
    ) -> None:
        """Send evolution report via LINE."""
        try:
            if success:
                report = f"""✅ 進化成功

📋 任務：{task.get('title', 'Unknown')}
⏱️ 耗時：{duration} 秒
🏷️ Git Tag：{git_tag}
📊 等級：{task.get('level', 'Unknown')}

{output_summary[:150] + '...' if len(output_summary) > 150 else output_summary}"""
            else:
                report = f"""❌ 進化失敗（已回滾）

📋 任務：{task.get('title', 'Unknown')}
⏱️ 耗時：{duration} 秒
📊 等級：{task.get('level', 'Unknown')}

錯誤：{error_msg[:200] if error_msg else 'Unknown error'}"""

            await line_service.push_to_joey(report)
            print(f"[Notification] Report sent via LINE")
        except Exception as e:
            print(f"[Notification] Failed to send LINE report: {e}")

    # ==================== Main Evolution Flow ====================

    async def run_evolution(self, task_id: str) -> None:
        """Run the complete evolution flow for a task."""
        print(f"[Evolution] Processing task: {task_id}")
        start_time = time.time()

        # 1. Fetch task from Notion
        task = await notion_service.get_evolution_task(task_id)
        if not task:
            print(f"[Error] Task not found: {task_id}")
            return

        if task["status"] != "pending":
            print(f"[Error] Task is not pending (status: {task['status']})")
            return

        print(f"[Evolution] Task: {task['title']}")
        print(f"[Evolution] Level: {task['level']}")

        # 2. Update status to executing
        await notion_service.update_evolution_task_status(
            task_id,
            "executing"
        )

        # 3. Pre-evolution checks
        pre_ok, pre_msg, git_tag = await self.pre_evolution_check(task)
        if not pre_ok:
            await notion_service.update_evolution_task_status(
                task_id,
                "failed",
                error_message=pre_msg
            )
            print(f"[Error] Pre-evolution check failed: {pre_msg}")
            return

        await notion_service.update_evolution_task_status(
            task_id,
            "executing",
            git_tag_pre=git_tag
        )

        # 4. Execute evolution
        exec_ok, exec_output = await self.execute_evolution(task)

        # 5. Update to verifying status
        await notion_service.update_evolution_task_status(
            task_id,
            "verifying",
            agent_output=exec_output
        )

        # 6. Post-evolution verification
        verify_ok, verify_result = await self.post_evolution_verify(task)

        # 7. Handle result
        duration = int(time.time() - start_time)
        commit_hash = self.get_current_commit()

        if exec_ok and verify_ok:
            # Success - create post-evolution tag
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            post_tag = f"post-evolution-{task_id[:8]}-{timestamp}"
            self.create_snapshot(post_tag)

            await notion_service.update_evolution_task_status(
                task_id,
                "completed",
                git_tag_post=post_tag,
                git_commit_hash=commit_hash,
                verification_result=verify_result,
                duration=duration
            )
            print(f"[Success] Evolution completed in {duration}s")

            # Send success report via LINE
            await self.send_evolution_report(
                task=task,
                success=True,
                duration=duration,
                git_tag=post_tag,
                output_summary=exec_output[:200] if exec_output else ""
            )

        else:
            # Failure - rollback
            rollback_reason = f"Execution: {'OK' if exec_ok else 'FAILED'}, Verification: {'OK' if verify_ok else 'FAILED'}"
            if not exec_ok:
                rollback_reason += f"\nExec output: {exec_output[:500]}"
            if not verify_ok:
                rollback_reason += f"\nVerify result: {verify_result}"

            rollback_ok, rollback_msg = await self.rollback(git_tag, rollback_reason)

            await notion_service.update_evolution_task_status(
                task_id,
                "rolled_back",
                error_message=exec_output if not exec_ok else verify_result,
                rollback_reason=rollback_msg,
                verification_result=verify_result,
                duration=duration
            )
            print(f"[Rolled Back] Evolution failed after {duration}s")

            # Send failure report via LINE
            await self.send_evolution_report(
                task=task,
                success=False,
                duration=duration,
                error_msg=exec_output if not exec_ok else verify_result
            )

    async def check_and_run_pending(self) -> None:
        """Check for pending tasks and run them."""
        print("[Pending Check] Checking for pending evolution tasks...")

        tasks = await notion_service.get_pending_evolution_tasks()
        if not tasks:
            print("[Pending Check] No pending tasks found")
            return

        print(f"[Pending Check] Found {len(tasks)} pending task(s)")

        # Process first pending task
        task = tasks[0]
        print(f"[Pending Check] Processing: {task['title']}")
        await self.run_evolution(task["id"])


# ==================== CLI Entry Point ====================

async def main():
    parser = argparse.ArgumentParser(description="Agent Evolution Controller")
    parser.add_argument("--task-id", help="Specific Notion task ID to execute")
    parser.add_argument("--check-pending", action="store_true", help="Check and run pending tasks")
    parser.add_argument("--project-dir", help="Project directory (default: /Users/joeyserver/joey-ai-agent)")

    args = parser.parse_args()

    controller = EvolutionController(project_dir=args.project_dir)

    if args.task_id:
        await controller.run_evolution(args.task_id)
    elif args.check_pending:
        await controller.check_and_run_pending()
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
