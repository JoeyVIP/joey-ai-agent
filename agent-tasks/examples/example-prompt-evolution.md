# 進化任務：優化系統提示詞的回應格式

## 安全等級
Level: 2

## 目標
改善 Claude 的 JSON 回應格式，讓 line_message 欄位更簡潔友好。

## 修改範圍
- [ ] src/prompts/system_prompt.md

## 執行步驟
1. 讀取現有的 system_prompt.md
2. 在 line_message 格式說明區塊加入「保持簡潔，不超過 200 字」的指引
3. 更新範例，展示更簡潔的 line_message 格式

## 驗證方式
- [ ] /health 回應 healthy
- [ ] system_prompt.md 檔案語法正確
- [ ] 新增的指引文字存在於檔案中

## 回滾條件
- 如果 /health 檢查失敗則自動回滾
- 如果檔案損壞（無法被 Claude 解析）則回滾

## 備註
這是一個 Level 2 的安全進化，會自動建立 Git 快照。
