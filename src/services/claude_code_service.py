import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.config import settings

logger = logging.getLogger(__name__)


class ClaudeCodeService:
    """Service for executing tasks via Claude Code CLI."""

    def __init__(self):
        # Tasks folder inside the project directory for better isolation
        # On Mac mini: /Users/joeyserver/joey-ai-agent/tasks/
        self.project_dir = Path(__file__).parent.parent.parent  # Go up from services/ to project root
        self.tasks_dir = self.project_dir / "tasks"
        self.tasks_dir.mkdir(exist_ok=True)

    def _create_task_folder(self, title: str) -> Path:
        """Create a folder for the task."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        safe_title = "".join(c if c.isalnum() or c in "-_" else "_" for c in title)[:50]
        folder_name = f"{date_str}_{safe_title}"
        task_folder = self.tasks_dir / folder_name

        # Handle duplicate folder names
        counter = 1
        while task_folder.exists():
            task_folder = self.tasks_dir / f"{folder_name}_{counter}"
            counter += 1

        task_folder.mkdir(parents=True)
        return task_folder

    async def execute_task(
        self,
        prompt: str,
        title: str,
        on_progress: Optional[callable] = None
    ) -> dict:
        """
        Execute a task using Claude Code CLI.

        Args:
            prompt: The structured prompt for Claude Code
            title: Task title for folder naming
            on_progress: Optional callback for progress updates

        Returns:
            dict with keys: success, output, folder_path, error
        """
        task_folder = self._create_task_folder(title)
        logger.info(f"Created task folder: {task_folder}")

        # Add automated execution prefix to prompt
        automated_prefix = """[AUTOMATED EXECUTION MODE - RALPH WIGGUM LOOP]
你正在以自動化模式執行任務。你有完整的檔案讀寫權限。

## 🔄 Ralph Wiggum 循環執行模式（核心原則）

**你必須持續迭代直到達成目標，不要中途放棄！**

```
執行流程：
1. 理解目標 → 2. 執行任務 → 3. 驗證結果 → 4. 未達標？→ 分析問題 → 修正 → 回到步驟 2
                                              ↓
                                           達標？→ 輸出成功結果
```

### 迭代規則
- **最大迭代次數**：5 次（每次修正算一次迭代）
- **每次迭代必須**：明確說明「第 N 次迭代」和「修正了什麼」
- **禁止行為**：不要說「無法完成」或「需要人工介入」，除非已嘗試 5 次
- **成功標準**：必須通過所有驗證項目才算成功

### 迭代日誌格式
每次迭代時輸出：
```
=== 迭代 #N ===
問題：[發現的問題]
修正：[採取的修正措施]
驗證：[驗證結果]
狀態：[繼續迭代 / 成功完成]
```

## 重要指示

1. 直接執行任務，不要詢問確認或等待批准
2. 立即開始建立所有需要的檔案和資料夾
3. 如果需要下載外部資源，直接下載
4. 如果需要執行指令，直接執行
5. 使用 gh CLI 進行 GitHub 操作（已認證為 JoeyVIP）
6. **必須使用 Render 進行部署**
7. **遇到錯誤時自動修正並重試，不要停下來**

## 📱 響應式設計規範（嚴格遵守）

**所有網站必須同時支援桌面版和手機版，採用 Mobile-First 設計原則：**

### CSS 必要設定
```css
/* 1. Viewport meta tag（HTML head 必須包含）*/
<meta name="viewport" content="width=device-width, initial-scale=1.0">

/* 2. Mobile-First 基礎樣式 */
* {
  box-sizing: border-box;
}

body {
  margin: 0;
  padding: 0;
  font-size: 16px;
  line-height: 1.6;
}

img {
  max-width: 100%;
  height: auto;
}

/* 3. 容器彈性寬度 */
.container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}
```

### 響應式斷點（必須使用）
```css
/* 手機優先，逐步增強到大螢幕 */

/* 平板 (768px+) */
@media (min-width: 768px) {
  /* 平板樣式 */
}

/* 桌面 (1024px+) */
@media (min-width: 1024px) {
  /* 桌面樣式 */
}
```

### 導航列響應式要求
- 手機版：漢堡選單 ☰，點擊展開
- 桌面版：水平導航列
- 使用 CSS 或簡單 JS 切換

### 字體大小響應式
- 標題：手機 1.5rem，桌面 2.5rem
- 內文：手機 1rem，桌面 1.125rem
- 使用 clamp() 更佳：`font-size: clamp(1.5rem, 4vw, 2.5rem);`

### Grid/Flexbox 響應式佈局
```css
/* 手機：單欄 */
.grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
}

/* 平板：雙欄 */
@media (min-width: 768px) {
  .grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* 桌面：三欄或更多 */
@media (min-width: 1024px) {
  .grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
```

### 避免的錯誤
- ❌ 固定寬度（如 width: 800px）
- ❌ 水平滾動條
- ❌ 文字太小（小於 14px）
- ❌ 按鈕太小難以點擊（最小 44x44px）
- ❌ 元素重疊或超出螢幕

## ⚠️ 部署規則（嚴格遵守）

**必須使用 Render 部署，禁止使用以下平台：**
- ❌ GitHub Pages
- ❌ Vercel
- ❌ Netlify
- ❌ Railway（API 不穩定）
- ❌ 任何其他平台

**Render 部署步驟：**
1. 建立網站專案（HTML/CSS/JS）
2. 建立 render.yaml 配置檔（必須）
3. 推送到 GitHub
4. 使用 Render API 建立 Static Site
5. 獲取 Render 網址（格式：xxx.onrender.com）

**⚠️ render.yaml 正確格式（必須使用這個，不要修改）：**
```yaml
services:
  - type: web
    name: 專案名稱
    env: static
    buildCommand: echo "Build complete"
    staticPublishPath: .
```

**🚫 禁止在 render.yaml 中使用以下設定：**
```yaml
# ❌ 絕對不要加 routes/rewrite 規則！會導致 CSS/JS MIME type 錯誤
routes:
  - type: rewrite
    source: /*
    destination: /index.html
```

**Render API 部署指令：**
```bash
curl -X POST 'https://api.render.com/v1/services' \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{
    "type": "static_site",
    "name": "專案名稱",
    "ownerId": "tea-d60dhri4d50c73ckulmg",
    "repo": "https://github.com/JoeyVIP/repo-name",
    "branch": "main",
    "autoDeploy": "yes",
    "serviceDetails": {
      "buildCommand": "echo Build complete",
      "publishPath": "."
    }
  }'
```

## 輸出格式（必須）

完成後，請在輸出的最後用以下格式回報結果：

---RESULT---
PROJECT_NAME: [專案名稱]
GITHUB_URL: [GitHub repo 網址]
DEPLOY_URL: [Render 網址，格式 xxx.onrender.com，如未部署填 PENDING]
DEPLOY_PLATFORM: Render
STATUS: [SUCCESS 或 PARTIAL 或 FAILED]
---END---

**STATUS 說明：**
- SUCCESS: 網站已部署，DEPLOY_URL 可訪問，桌面版和手機版視覺驗證都通過
- PARTIAL: GitHub 已推送，等待在 Render Dashboard 完成部署
- FAILED: 執行失敗

## 部署後驗證（必須執行）

部署完成後，使用 Playwright MCP 進行**桌面版和手機版雙重驗證**：

### 1. 桌面版驗證（預設視窗大小）
1. `browser_navigate` 到部署網址
2. `browser_console_messages` 檢查 CSS/JS 錯誤
3. `browser_take_screenshot` 截圖首頁（命名：desktop-home.png）
4. `browser_press_key "End"` 滾動到底部
5. `browser_take_screenshot` 截圖底部（命名：desktop-footer.png）

### 2. 手機版驗證（調整視窗大小）
1. `browser_resize` 設定寬度 375px，高度 667px（iPhone SE 尺寸）
2. `browser_navigate` 重新載入頁面
3. `browser_take_screenshot` 截圖手機版首頁（命名：mobile-home.png）
4. `browser_press_key "End"` 滾動到底部
5. `browser_take_screenshot` 截圖手機版底部（命名：mobile-footer.png）

### 驗證標準
**桌面版：**
- ✅ 無 CSS MIME type 錯誤
- ✅ 導航列水平排列
- ✅ 內容區塊正確顯示（多欄佈局）
- ✅ 無水平滾動條

**手機版：**
- ✅ 導航列變成漢堡選單或垂直排列
- ✅ 單欄佈局，無水平滾動
- ✅ 字體清晰可讀（不小於 14px）
- ✅ 按鈕大小適合觸控（最小 44x44px）
- ✅ 圖片自適應寬度

**如有問題，必須修復後重新部署！**

---

## 📊 狀態回報（必須）

每次完成一個步驟後，輸出狀態區塊：

```
---RALPH_STATUS---
STATUS: IN_PROGRESS | COMPLETE | BLOCKED
CURRENT_STEP: [目前步驟名稱]
ITERATION: [第幾次迭代]
TASKS_DONE: [已完成的任務數]
ISSUES_FOUND: [發現的問題數]
ISSUES_FIXED: [已修復的問題數]
EXIT_SIGNAL: false | true
NEXT_ACTION: [下一步要做什麼]
---END_RALPH_STATUS---
```

**EXIT_SIGNAL 規則：**
- `false`：繼續執行，還有工作要做
- `true`：任務完成，所有驗證通過，可以結束

**只有當以下條件都滿足時才設 EXIT_SIGNAL: true：**
1. 網站已成功部署到 Render
2. 桌面版 Playwright 驗證通過
3. 手機版 Playwright 驗證通過
4. 無 CSS/JS 錯誤
5. 輸出了 ---RESULT--- 區塊

---

現在開始執行以下任務：

"""
        full_prompt = automated_prefix + prompt

        # Write task.md
        task_file = task_folder / "task.md"
        task_file.write_text(f"# Task\n\n{prompt}")

        try:
            # Build the command
            # Using --print for non-interactive mode
            # Using --dangerously-skip-permissions for automated execution
            cmd = [
                "claude",
                "-p", full_prompt,
                "--print",
                "--dangerously-skip-permissions"
            ]

            # Set up environment with OAuth token and API keys
            env = os.environ.copy()

            # 🔧 修復 PATH 問題：確保 homebrew 和本地 bin 在 PATH 中
            # 這對於 MCP servers (npx), gh CLI, 和其他工具是必要的
            current_path = env.get("PATH", "")
            homebrew_paths = "/opt/homebrew/bin:/opt/homebrew/sbin"
            local_bin = f"/Users/{os.environ.get('USER', 'joeyserver')}/.local/bin"
            if homebrew_paths not in current_path:
                env["PATH"] = f"{homebrew_paths}:{local_bin}:{current_path}"

            if hasattr(settings, 'claude_code_oauth_token') and settings.claude_code_oauth_token:
                env["CLAUDE_CODE_OAUTH_TOKEN"] = settings.claude_code_oauth_token
            if hasattr(settings, 'render_api_key') and settings.render_api_key:
                env["RENDER_API_KEY"] = settings.render_api_key
            if hasattr(settings, 'github_token') and settings.github_token:
                env["GITHUB_TOKEN"] = settings.github_token

            logger.info(f"Executing Claude Code in {task_folder}")

            # Run the command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(task_folder),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )

            stdout, stderr = await process.communicate()
            output = stdout.decode("utf-8")
            error_output = stderr.decode("utf-8")

            # Write result.md
            result_file = task_folder / "result.md"
            result_content = f"# Result\n\n## Output\n\n{output}"
            if error_output:
                result_content += f"\n\n## Errors\n\n{error_output}"
            result_file.write_text(result_content)

            success = process.returncode == 0

            if success:
                logger.info("Claude Code execution completed successfully")
            else:
                logger.warning(f"Claude Code exited with code {process.returncode}")

            return {
                "success": success,
                "output": output,
                "folder_path": str(task_folder),
                "error": error_output if error_output else None,
                "return_code": process.returncode
            }

        except asyncio.TimeoutError:
            logger.error("Claude Code execution timed out")
            return {
                "success": False,
                "output": "",
                "folder_path": str(task_folder),
                "error": "Execution timed out",
                "return_code": -1
            }
        except Exception as e:
            logger.error(f"Error executing Claude Code: {e}", exc_info=True)
            return {
                "success": False,
                "output": "",
                "folder_path": str(task_folder),
                "error": str(e),
                "return_code": -1
            }

    async def execute_task_with_timeout(
        self,
        prompt: str,
        title: str,
        timeout_seconds: int = 3600,
        on_progress: Optional[callable] = None
    ) -> dict:
        """Execute task with a timeout."""
        try:
            return await asyncio.wait_for(
                self.execute_task(prompt, title, on_progress),
                timeout=timeout_seconds
            )
        except asyncio.TimeoutError:
            return {
                "success": False,
                "output": "",
                "folder_path": "",
                "error": f"Execution timed out after {timeout_seconds} seconds",
                "return_code": -1
            }

    async def execute_task_with_retry(
        self,
        prompt: str,
        title: str,
        max_retries: int = 10,
        timeout_seconds: int = 21600,  # 6 小時
        on_progress: Optional[callable] = None
    ) -> dict:
        """
        Execute task with automatic retry on failure (Ralph Wiggum pattern).
        支援長時間執行：預設每次迭代最多 6 小時，最多 10 次迭代。
        理論上可持續執行 60 小時（2.5 天）。

        Args:
            prompt: The structured prompt
            title: Task title
            max_retries: Maximum retry attempts (default 10)
            timeout_seconds: Timeout per attempt (default 6 hours = 21600 seconds)
            on_progress: Progress callback

        Returns:
            dict with execution result
        """
        last_result = None

        for attempt in range(1, max_retries + 1):
            logger.info(f"🔄 Ralph Loop: Attempt {attempt}/{max_retries} for '{title}'")

            # Add retry context to prompt if this is a retry
            retry_prompt = prompt
            if attempt > 1 and last_result:
                retry_context = f"""
## ⚠️ 重試提示（第 {attempt} 次嘗試）

上一次執行失敗，錯誤資訊：
```
{last_result.get('error', '未知錯誤')}
```

請分析問題並修正後重試。不要重複同樣的錯誤。

---

"""
                retry_prompt = retry_context + prompt

            try:
                result = await asyncio.wait_for(
                    self.execute_task(retry_prompt, f"{title}_attempt{attempt}", on_progress),
                    timeout=timeout_seconds
                )

                # Check if execution was successful
                if result["success"]:
                    output = result.get("output", "")

                    # 停止條件（任一滿足即停止）：
                    # 1. 明確的 EXIT_SIGNAL: true
                    # 2. STATUS: COMPLETE
                    # 3. ---RESULT--- 區塊存在（表示任務有產出結果）
                    # 4. 部署成功的標誌（.onrender.com URL）

                    has_exit_signal = "EXIT_SIGNAL: true" in output
                    has_complete_status = "STATUS: COMPLETE" in output
                    has_result_block = "---RESULT---" in output
                    has_deploy_url = ".onrender.com" in output
                    has_success_status = "STATUS: SUCCESS" in output

                    # 簡單任務：有結果區塊就算完成
                    if has_result_block:
                        if has_success_status:
                            logger.info(f"✅ Ralph Loop: Task completed with SUCCESS on attempt {attempt}")
                        elif has_deploy_url:
                            logger.info(f"✅ Ralph Loop: Task completed with deploy URL on attempt {attempt}")
                        else:
                            logger.info(f"✅ Ralph Loop: Task completed with RESULT block on attempt {attempt}")
                        return result

                    # 明確的停止信號
                    if has_exit_signal or has_complete_status:
                        logger.info(f"✅ Ralph Loop: Task completed with exit signal on attempt {attempt}")
                        return result

                    # Process 成功但沒有明確輸出，也算完成（避免不必要的重試）
                    if result["return_code"] == 0:
                        logger.info(f"✅ Ralph Loop: Process succeeded on attempt {attempt}, treating as complete")
                        return result

                last_result = result

                # If not the last attempt, wait before retry
                if attempt < max_retries:
                    logger.warning(f"⏳ Ralph Loop: Attempt {attempt} incomplete, retrying in 10 seconds...")
                    await asyncio.sleep(10)

            except asyncio.TimeoutError:
                logger.error(f"⏰ Ralph Loop: Attempt {attempt} timed out")
                last_result = {
                    "success": False,
                    "output": "",
                    "folder_path": "",
                    "error": f"Attempt {attempt} timed out after {timeout_seconds} seconds",
                    "return_code": -1
                }
                if attempt < max_retries:
                    await asyncio.sleep(10)
            except Exception as e:
                logger.error(f"❌ Ralph Loop: Attempt {attempt} failed with error: {e}")
                last_result = {
                    "success": False,
                    "output": "",
                    "folder_path": "",
                    "error": str(e),
                    "return_code": -1
                }
                if attempt < max_retries:
                    await asyncio.sleep(10)

        logger.error(f"❌ Ralph Loop: All {max_retries} attempts failed for '{title}'")
        return last_result or {
            "success": False,
            "output": "",
            "folder_path": "",
            "error": f"All {max_retries} attempts failed",
            "return_code": -1
        }


claude_code_service = ClaudeCodeService()
