# 進化任務：提取 Magic Numbers 為命名常數

## 安全等級
Level: 2

## 目標
使用 code-simplifier 將 magic numbers 提取為命名常數，提升程式碼可讀性。

## 修改範圍
- [x] src/constants.py（新建）
- [x] src/services/notion_service.py（20+ 處 `[:2000]`）
- [x] src/services/claude_service.py（1 處 `4096`）

## 執行步驟
1. 建立 src/constants.py 定義以下常數：
   - NOTION_MAX_TEXT_LENGTH = 2000
   - CLAUDE_MAX_TOKENS = 4096
   - LINE_MESSAGE_PREVIEW_LENGTH = 200
   - 其他相關常數
2. 更新 notion_service.py 匯入並使用 NOTION_MAX_TEXT_LENGTH
3. 更新 claude_service.py 匯入並使用 CLAUDE_MAX_TOKENS

## 驗證方式
- [x] python3 -m py_compile src/constants.py
- [x] python3 -m py_compile src/services/notion_service.py
- [x] python3 -m py_compile src/services/claude_service.py
- [ ] curl /health 回應 healthy（部署後驗證）

## 回滾條件
- 如果任何驗證失敗則自動回滾

## 完成狀態
- 狀態：已完成（本地）
- 完成時間：2026-02-03
- 待執行：部署到 Mac mini 並驗證服務
