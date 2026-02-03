# Joey's AI Agent

LINE → Claude → Notion AI 助理

透過 LINE 傳送任務，由 Claude 判斷難度並處理，結果存到 Notion，最後通知你。

## 功能

- **簡單任務**：直接由 Claude 完成（知識問答、文字處理、建議等）
- **複雜任務**：準備好 prompt 和分析，方便你用 Claude Code 執行
- **記憶系統**：記住你的偏好、專案、客戶資訊

## 架構

```
LINE Message → FastAPI Webhook → Claude API → Notion → LINE Push
```

## 快速開始

### 1. 環境設定

```bash
cd joey-ai-agent
cp .env.example .env
# 編輯 .env 填入你的 API keys
```

### 2. 安裝依賴

```bash
pip install -r requirements.txt
```

### 3. 初始化 Notion 記憶

```bash
python scripts/setup_notion_databases.py
```

### 4. 啟動服務

```bash
# 開發模式
uvicorn src.main:app --reload

# 或用 Docker
docker-compose up -d
```

### 5. 設定 Cloudflare Tunnel

```bash
# 安裝 cloudflared
brew install cloudflared

# 登入
cloudflared tunnel login

# 建立 tunnel
cloudflared tunnel create joey-ai-agent

# 設定 config
cloudflared tunnel route dns joey-ai-agent your-domain.com

# 啟動
cloudflared tunnel run joey-ai-agent
```

### 6. 設定 LINE Webhook

到 LINE Developers Console：
1. 設定 Webhook URL：`https://your-domain.com/webhook/line`
2. 啟用 Webhook
3. 關閉自動回應訊息

## 環境變數

| 變數 | 說明 |
|------|------|
| `LINE_CHANNEL_SECRET` | LINE Channel Secret |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Channel Access Token |
| `JOEY_LINE_USER_ID` | 你的 LINE User ID |
| `NOTION_API_KEY` | Notion Integration Token |
| `NOTION_INBOX_DB_ID` | Inbox Database ID |
| `NOTION_REVIEW_DB_ID` | Review Database ID |
| `NOTION_MEMORY_DB_ID` | Memory Database ID |
| `ANTHROPIC_API_KEY` | Anthropic API Key |
| `ANTHROPIC_MODEL` | Claude 模型 (預設: claude-sonnet-4-20250514) |

## Notion 資料庫

### Inbox
暫存收到的任務

### Review
處理完成的任務結果
- 簡單任務：包含 Result
- 複雜任務：包含 Analysis、Preparation、PromptForClaudeCode

### Memory
你的記憶資料庫
- 基本資訊、偏好、專案、客戶等

## 測試

```bash
# 本地測試 webhook
python scripts/test_webhook.py "幫我想三個專案名稱"

# 健康檢查
curl http://localhost:8000/health
```

## 開機自動啟動 (Mac)

建立 LaunchAgent：

```bash
cat > ~/Library/LaunchAgents/com.joey.ai-agent.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.joey.ai-agent</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/docker-compose</string>
        <string>-f</string>
        <string>/path/to/joey-ai-agent/docker-compose.yml</string>
        <string>up</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
EOF

launchctl load ~/Library/LaunchAgents/com.joey.ai-agent.plist
```

## License

MIT
