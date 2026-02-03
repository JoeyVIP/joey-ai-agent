# 網站建立服務 - 迭代紀錄

## 目的

記錄每次專案執行的問題與改進，持續優化 AI Agent 的表現。

---

## 迭代紀錄

### Iteration #1 - 太空貓咖啡館 (2026-02-03)

**專案資訊**
- 名稱：太空貓咖啡館
- 素材來源：Google Drive
- 目標平台：Railway

**執行結果**
- ✅ Google Drive 下載：成功
- ✅ 網站建立：成功（HTML+CSS+JS）
- ✅ GitHub 推送：成功
- ❌ Railway 部署：失敗（選擇了 GitHub Pages）
- ⚠️ LINE 通知：自動流程未發送

**問題分析**

| 問題 | 根因 | 解決方案 |
|------|------|----------|
| 使用 GitHub Pages 而非 Railway | Prompt 沒有明確禁止其他平台 | 在 prompt 中加入禁止清單和強制 Railway 指示 |
| LINE 通知未發送 | 可能是 async 問題或靜默失敗 | 需要加入 logging 和 error handling |

**改進措施**
1. ✅ 建立 `skills/deploy-website.md` 模板
2. ✅ 更新 prompt 加入禁止清單
3. ✅ 加入 Railway 配置範本
4. [ ] 修復 LINE 通知問題
5. [ ] 驗證 Railway 部署

**下一步**
- 重新測試完整流程
- 確認 Railway 部署成功

---

### Iteration #2 - Railway 問題排查 (2026-02-03)

**專案資訊**
- 目標：解決 Railway 部署問題
- 方法：測試各種 Token 和 API 方式

**測試結果**
- ❌ Railway CLI：Unauthorized 錯誤
- ❌ 新建 Team Token：同樣失敗
- ❌ 直接 GraphQL API：同樣失敗
- ❌ 非官方 Railway MCP：使用相同 API，無法解決

**問題分析**

| 問題 | 根因 | 解決方案 |
|------|------|----------|
| Token 認證失敗 | Railway 的已知 Bug，非我們的問題 | 切換到 Render |

**決策**
- 放棄 Railway，改用 Render
- Render 有穩定的 REST API
- 支援靜態網站 + 後端 + 資料庫

**下一步**
- 申請 Render API Key
- 建立 Render 整合
- 測試完整部署流程

---

### Iteration #3 - （待執行）

**專案資訊**
- 名稱：
- 素材來源：
- 目標平台：Render

**執行結果**
- [ ] Google Drive 下載：
- [ ] 網站建立：
- [ ] GitHub 推送：
- [ ] Render 部署：
- [ ] LINE 通知：

**問題分析**


**改進措施**


---

## 成功指標

| 指標 | 目標 | 當前 |
|------|------|------|
| 端到端成功率 | 100% | 80% (4/5) |
| Railway 部署成功率 | 100% | 0% |
| 平均執行時間 | < 10 分鐘 | ~9 分鐘 |
| LINE 通知成功率 | 100% | 50% |

---

## 累積學習

### 有效的做法
1. 在 prompt 中提供具體配置範本（如 railway.json）
2. 使用結構化輸出格式（---RESULT---）方便解析
3. 分階段執行並記錄進度

### 無效的做法
1. 只說「部署到 Railway」不夠具體
2. 沒有禁止清單，AI 會選擇它認為最簡單的方案

### 待驗證的假設
1. 提供 Railway CLI 指令是否比 MCP 更可靠？
2. 是否需要先在 Railway 建好專案再連接 GitHub？

---

## 模板更新日誌

| 日期 | 版本 | 變更內容 |
|------|------|----------|
| 2026-02-03 | v1.0 | 初始版本 |
| 2026-02-03 | v1.1 | 加入禁止清單、Railway 配置範本 |
