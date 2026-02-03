# 進化任務：新增前端深色模式

## 安全等級
Level: 3

## 目標
為 web-frontend 新增深色模式切換功能。

## 修改範圍
- [ ] web-frontend/src/styles/theme.css
- [ ] web-frontend/src/components/ThemeToggle.tsx

## 執行步驟
1. 建立 theme.css 定義淺色和深色主題變數
2. 建立 ThemeToggle 元件
3. 在主要 layout 中整合主題切換按鈕

## 驗證方式
- [ ] /health 回應 healthy
- [ ] 新增的檔案存在且語法正確
- [ ] npm run build 成功（如果有設定）

## 回滾條件
- 如果 /health 檢查失敗則自動回滾

## 備註
這是一個 Level 3 的自由進化，影響範圍僅限於前端程式碼。
