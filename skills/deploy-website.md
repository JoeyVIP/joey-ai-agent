# Skill: 網站建立與部署

## 概述

從素材到部署的完整網站建立流程。將 Google Drive 素材轉換為完整網站，部署到 Render 並回傳公開網址。

> **注意**：2026-02-03 起改用 Render（原 Railway 有認證問題）

---

## 輸入參數

| 參數 | 必填 | 說明 |
|------|------|------|
| project_name | ✅ | 專案名稱（例：太空貓咖啡館）|
| drive_url | ✅ | Google Drive 素材資料夾連結 |
| site_type | ❌ | 網站類型：static / dynamic（預設 static）|
| style | ❌ | 設計風格描述 |
| repo_name | ❌ | GitHub repo 名稱（預設自動生成）|

---

## 執行步驟

### Step 1: 下載素材
```
使用 Google Drive MCP 從指定連結下載所有素材到 ./assets/ 資料夾
- 圖片放到 ./assets/images/
- 文件放到 ./assets/docs/
```

### Step 2: 分析素材
```
分析下載的素材：
- 識別 Logo、主視覺、產品圖等
- 提取文案內容（如有）
- 決定配色方案
```

### Step 3: 建立網站（含響應式設計）
```
根據 site_type 建立網站：

【Static 靜態網站】
- 建立 index.html, styles.css, script.js
- **Mobile-First 響應式設計（嚴格要求）**
- 所有缺少的內容用 AI 生成假資料填充

【Dynamic 動態網站】
- 使用 Node.js + Express 或 Python + FastAPI
- 建立基本路由和頁面
- 包含 package.json 或 requirements.txt
```

### Step 3.5: 響應式設計規範（必須遵守）

**HTML head 必須包含：**
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0">
```

**CSS Mobile-First 基礎：**
```css
* { box-sizing: border-box; }
body { margin: 0; padding: 0; font-size: 16px; }
img { max-width: 100%; height: auto; }
.container { width: 100%; max-width: 1200px; margin: 0 auto; padding: 0 20px; }
```

**響應式斷點：**
```css
/* 手機優先 (預設) */

/* 平板 768px+ */
@media (min-width: 768px) { }

/* 桌面 1024px+ */
@media (min-width: 1024px) { }
```

**導航列響應式：**
- 手機版：漢堡選單 ☰
- 桌面版：水平導航列

**字體響應式：**
```css
h1 { font-size: clamp(1.5rem, 4vw, 2.5rem); }
```

**Grid 響應式佈局：**
```css
.grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
}
@media (min-width: 768px) {
  .grid { grid-template-columns: repeat(2, 1fr); }
}
@media (min-width: 1024px) {
  .grid { grid-template-columns: repeat(3, 1fr); }
}
```

**禁止事項：**
- ❌ 固定寬度（如 width: 800px）
- ❌ 水平滾動條
- ❌ 文字小於 14px
- ❌ 按鈕小於 44x44px

### Step 4: Render 部署配置

**重要：必須使用 Render 部署，禁止使用 GitHub Pages**

**⚠️ render.yaml 正確格式（必須完全照抄）：**
```yaml
services:
  - type: web
    name: project-name
    env: static
    buildCommand: echo "Build complete"
    staticPublishPath: .
```

**🚫 禁止設定（會導致 CSS/JS MIME type 錯誤）：**
```yaml
# ❌ 絕對不要加這個！
routes:
  - type: rewrite
    source: /*
    destination: /index.html
```

**為什麼？**
- rewrite 規則會把 CSS/JS 請求導向 index.html
- 導致瀏覽器收到 HTML 內容但預期 CSS/JS
- 出現 "MIME type text/plain is not supported" 錯誤

**Render 設定說明**：
- 靜態網站選擇 `env: static`
- `staticPublishPath: .` 指向根目錄
- 不需要 routes 設定，Render 會自動處理靜態檔案

### Step 5: 推送到 GitHub
```
使用 gh CLI：
1. gh repo create {repo_name} --public --source=. --remote=origin
2. git add -A
3. git commit -m "Initial commit: {project_name}"
4. git push -u origin main
```

### Step 6: 部署到 Render

**使用 Render API 或 Dashboard**

```
方法 1：Render Dashboard（手動）
1. 登入 Render Dashboard
2. 點擊 "New" → "Static Site"
3. 連接 GitHub Repository
4. 設定 Build Command 和 Publish Directory
5. 部署並獲取網址

方法 2：Render API（自動化）
1. 使用 API Key 認證
2. POST /services 建立新服務
3. 連接 GitHub Repo
4. 觸發部署
5. 獲取 .onrender.com 網址

API 範例：
curl -X POST https://api.render.com/v1/services \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "static_site",
    "name": "project-name",
    "repo": "https://github.com/user/repo",
    "branch": "main"
  }'
```

### Step 7: 驗證部署（使用 Playwright MCP - 桌面版 + 手機版）

**重要：必須使用 Playwright MCP 進行桌面版和手機版雙重視覺驗證**

```
1. 等待部署完成（約 1-3 分鐘）
2. 獲取 Render 網址（格式：xxx.onrender.com）

3. 桌面版驗證：
   a. browser_navigate 到部署網址
   b. browser_console_messages 檢查是否有 CSS/JS 錯誤
   c. browser_take_screenshot 截圖首頁（desktop-home.png）
   d. browser_press_key "End" 滾動到底部
   e. browser_take_screenshot 截圖底部（desktop-footer.png）

4. 手機版驗證：
   a. browser_resize 設定 width: 375, height: 667（iPhone SE）
   b. browser_navigate 重新載入頁面
   c. browser_take_screenshot 截圖手機版首頁（mobile-home.png）
   d. browser_press_key "End" 滾動到底部
   e. browser_take_screenshot 截圖手機版底部（mobile-footer.png）

5. 驗證標準：

   【桌面版】
   - ✅ 無 CSS MIME type 錯誤
   - ✅ 無 404 錯誤（除 favicon 外）
   - ✅ 導航列水平排列
   - ✅ 多欄佈局正確顯示
   - ✅ 無水平滾動條

   【手機版】
   - ✅ 導航列變成漢堡選單或垂直排列
   - ✅ 單欄佈局，內容不超出螢幕
   - ✅ 字體清晰可讀（≥14px）
   - ✅ 按鈕夠大，方便觸控（≥44x44px）
   - ✅ 圖片自適應寬度

6. 如果驗證失敗：
   - 修復響應式 CSS
   - 檢查 viewport meta tag
   - 確認無固定寬度元素
   - 重新部署並再次驗證
```

**Playwright MCP 驗證範例**：
```javascript
// === 桌面版驗證 ===
browser_navigate({ url: "https://xxx.onrender.com" })
browser_console_messages({ level: "error" })
browser_take_screenshot({ type: "png", filename: "desktop-home.png" })
browser_press_key({ key: "End" })
browser_take_screenshot({ type: "png", filename: "desktop-footer.png" })

// === 手機版驗證 ===
browser_resize({ width: 375, height: 667 })
browser_navigate({ url: "https://xxx.onrender.com" })
browser_take_screenshot({ type: "png", filename: "mobile-home.png" })
browser_press_key({ key: "End" })
browser_take_screenshot({ type: "png", filename: "mobile-footer.png" })
```

---

## 輸出格式

任務完成後，必須以此格式輸出結果：

```
---RESULT---
PROJECT_NAME: {專案名稱}
GITHUB_URL: https://github.com/{user}/{repo}
DEPLOY_URL: https://{project}.onrender.com
DEPLOY_PLATFORM: Render
STATUS: SUCCESS
---END---
```

**注意**：DEPLOY_URL 必須是 Render 網址（xxx.onrender.com），不接受 GitHub Pages 網址。

**STATUS 選項**：
- `SUCCESS`：部署完成，網址可訪問
- `PARTIAL`：GitHub 已推送，等待手動在 Render Dashboard 完成部署
- `FAILED`：執行失敗

---

## 錯誤處理

| 錯誤 | 解決方案 |
|------|----------|
| Google Drive 下載失敗 | 檢查連結是否公開，重試 |
| Render 部署失敗 | 檢查 render.yaml 配置，查看 build logs |
| Render API 無法使用 | 改用手動方式在 Dashboard 部署，回報 PARTIAL 狀態 |
| GitHub push 失敗 | 確認 gh auth 狀態，檢查 repo 名稱衝突 |

---

## 版本歷史

### v1.1 (2026-02-03)
- 從 Railway 切換到 Render
- Railway Token 認證有已知 Bug，無法自動化
- Render API 更穩定

### v1.0 (2026-02-03)
- 初始版本
- 支援靜態網站建立與部署
- 原使用 Railway（已棄用）

### 待改進項目
- [ ] 支援動態網站（Node.js/Python 後端）
- [ ] 自動偵測最佳框架
- [ ] 支援自訂域名綁定（Phase 2: Cloudflare）
- [ ] 支援資料庫整合
- [ ] 多語言支援
- [ ] SEO 優化自動化

---

## 學習紀錄

### 2026-02-03 - 太空貓咖啡館 V1
**問題**：Claude Code 選擇了 GitHub Pages 而非 Railway
**原因**：提示詞沒有強制指定部署平台
**解決**：在 Skill 中明確禁止 GitHub Pages

### 2026-02-03 - 太空貓咖啡館 V2
**問題**：Railway Token 認證失敗（Unauthorized）
**原因**：Railway API 的已知 Bug，非程式問題
**解決**：切換到 Render，API 更穩定

### 模板
```
【日期】- 專案名稱
**問題**：
**原因**：
**解決**：
```
