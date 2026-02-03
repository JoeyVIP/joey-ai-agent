"""
常數定義檔

將 magic numbers 統一定義於此，提升程式碼可讀性與可維護性。
"""

# ==================== Notion 相關常數 ====================

# Notion API 富文字欄位的最大長度限制
NOTION_MAX_TEXT_LENGTH = 2000

# ==================== Claude API 相關常數 ====================

# Claude API 回應的最大 token 數
CLAUDE_MAX_TOKENS = 4096

# ==================== LINE 相關常數 ====================

# LINE 訊息預覽長度（用於截斷通知）
LINE_MESSAGE_PREVIEW_LENGTH = 200

# LINE 日誌記錄的最大訊息長度
LINE_LOG_MESSAGE_LENGTH = 50

# LINE 檔案記錄的最大訊息長度
LINE_FILE_LOG_MESSAGE_LENGTH = 100

# ==================== 路徑相關常數 ====================

# 使用者 ID 記錄檔名稱
USER_IDS_LOG_FILENAME = "user_ids.log"

# ==================== Claude Code 服務相關常數 ====================

# 任務標題最大長度（用於資料夾命名）
TASK_TITLE_MAX_LENGTH = 50

# 任務重試間隔（秒）
TASK_RETRY_INTERVAL_SECONDS = 10

# 預設最大重試次數
TASK_MAX_RETRIES = 10

# 預設單次任務超時時間（秒，6 小時）
TASK_DEFAULT_TIMEOUT_SECONDS = 21600

# 預設單次執行超時時間（秒，1 小時）
TASK_EXECUTION_TIMEOUT_SECONDS = 3600
