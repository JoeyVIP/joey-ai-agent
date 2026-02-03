# Joey AI Agent - Claude Code 指南

這是 Joey 的個人 AI Agent 系統，運行於 Mac mini 上。

## 專案架構

```
joey-ai-agent/
├── src/
│   ├── main.py              # FastAPI 入口 (Level 0)
│   ├── config.py            # 環境變數設定 (Level 0)
│   ├── api/
│   │   ├── line_webhook.py  # LINE Webhook (Level 1)
│   │   └── health.py        # 健康檢查
│   ├── services/
│   │   ├── notion_service.py      # Notion 整合 (Level 1)
│   │   ├── task_processor.py      # 任務處理核心 (Level 1)
│   │   ├── claude_service.py      # Claude API (Level 2)
│   │   ├── claude_code_service.py # Claude Code 執行 (Level 1)
│   │   └── line_service.py        # LINE 推送 (Level 2)
│   ├── models/
│   │   └── claude_response.py     # 資料模型
│   └── prompts/
│       └── system_prompt.md       # 系統提示詞 (Level 2)
├── scripts/
│   ├── evolution_controller.py    # 進化控制器
│   └── create_evolution_task.py   # 建立進化任務
├── agent-tasks/
│   ├── submit_evolution.sh        # 提交進化任務
│   └── templates/
│       └── evolution-template.md  # 任務模板
├── web-frontend/                  # 前端程式碼 (Level 3)
└── tasks/                         # 任務輸出 (Level 3)
```

## 自體進化協議

### 安全分級制度

| 等級 | 說明 | 檔案範圍 |
|------|------|----------|
| **Level 0** | 禁止自動修改 | config.py, main.py, .env, plist |
| **Level 1** | 核心邏輯，需快照 + 完整驗證 | line_webhook.py, task_processor.py, notion_service.py, claude_code_service.py |
| **Level 2** | 安全修改，需快照 | system_prompt.md, claude_service.py, line_service.py |
| **Level 3** | 自由修改 | web-frontend/, tasks/, agent-tasks/, docs/ |

### 進化流程

當收到進化任務時，必須按照以下流程執行：

1. **讀取任務的安全等級**
   - 檢查任務中指定的檔案
   - 自動判斷最高限制等級

2. **Level 0 任務處理**
   - 拒絕執行
   - 回報需要人工介入
   - 更新 Notion 狀態為 `failed`

3. **Level 1-3 任務處理**
   ```
   a. 呼叫 evolution_controller.pre_evolution_check()
      - 檢查 /health 端點
      - 建立 Git 快照 (tag: pre-evolution-{task_id}-{timestamp})
      - 記錄開始時間到 Notion

   b. 執行修改
      - 根據任務描述進行程式碼修改
      - 遵循任務中的執行步驟

   c. 呼叫 evolution_controller.post_evolution_verify()
      - 檢查 /health 端點
      - 執行任務定義的驗證步驟

   d. 如驗證失敗
      - 呼叫 evolution_controller.rollback()
      - 回滾到快照
      - 重啟服務
      - 更新 Notion 狀態為 rolled_back
   ```

4. **將結果記錄到 Notion Evolution Database**
   - 更新狀態（completed / failed / rolled_back）
   - 記錄執行時間、Git tag、錯誤訊息

### 進化任務格式

使用 `agent-tasks/templates/evolution-template.md` 模板：

```markdown
# 進化任務：{標題}

## 安全等級
Level: {0-3}

## 目標
{描述要達成什麼}

## 修改範圍
- [ ] 檔案1: {路徑}
- [ ] 檔案2: {路徑}

## 執行步驟
1. ...
2. ...

## 驗證方式
- [ ] /health 回應 healthy
- [ ] {其他驗證項目}

## 回滾條件
- 如果 {條件} 則回滾
```

### 使用方式

**方式一：透過腳本提交任務**
```bash
# 建立任務（不執行）
./agent-tasks/submit_evolution.sh task.md

# 建立並執行任務
./agent-tasks/submit_evolution.sh task.md --execute
```

**方式二：檢查並執行 pending 任務**
```bash
python3 scripts/evolution_controller.py --check-pending
```

**方式三：直接執行指定任務**
```bash
python3 scripts/evolution_controller.py --task-id <notion_task_id>
```

## Notion 資料庫

### Evolution Database 欄位

| 欄位 | 類型 | 說明 |
|------|------|------|
| Name | Title | 進化標題 |
| Status | Select | pending / executing / verifying / completed / failed / rolled_back |
| Type | Select | prompt / code / frontend / config |
| Level | Select | Level 0 / Level 1 / Level 2 / Level 3 |
| Description | Rich Text | 變更描述與目標 |
| FilesModified | Rich Text | 修改的檔案列表 |
| VerificationSteps | Rich Text | 驗證步驟清單 |
| CreatedAt | Date | 任務建立時間 |
| StartedAt | Date | 開始執行時間 |
| CompletedAt | Date | 完成時間 |
| Duration | Number | 執行耗時（秒） |
| GitTagPre | Text | 進化前快照 tag |
| GitTagPost | Text | 進化後快照 tag |
| GitCommitHash | Text | 最終 commit hash |
| VerificationResult | Rich Text | 驗證結果詳情 |
| ErrorMessage | Rich Text | 錯誤訊息 |
| RollbackReason | Rich Text | 回滾原因 |
| AgentOutput | Rich Text | Agent 執行輸出摘要 |

### 狀態流轉

```
pending → executing → verifying → completed
              ↓           ↓
           failed    rolled_back
```

## 開發注意事項

1. **永遠不要直接修改 Level 0 檔案**
   - 這些檔案的變更需要人工審核

2. **修改 Level 1 檔案前務必備份**
   - 使用 evolution_controller 自動建立快照
   - 確保 /health 檢查通過後才算成功

3. **測試新功能時**
   - 先在 Level 3 區域（如 web-frontend）測試
   - 確認無誤後再考慮整合到核心

4. **查看進化歷史**
   - 到 Notion Evolution Database 查看所有進化記錄
   - 可追蹤失敗原因和回滾歷史

## 相關指令

```bash
# 健康檢查
curl http://localhost:8000/health

# 查看服務狀態
launchctl list | grep joey

# 重啟服務
launchctl kickstart -k gui/$(id -u)/com.joey.ai-agent

# 查看 Git 快照
git tag -l "pre-evolution-*"
git tag -l "post-evolution-*"

# 回滾到特定快照
git reset --hard pre-evolution-{tag}
```
