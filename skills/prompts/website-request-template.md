# 網站建立請求模板

> 用於發送到 LINE 的標準化提示詞格式

---

## 模板格式

```
請幫我建立「{專案名稱}」網站：

## 素材來源
Google Drive：{Google Drive 連結}

## 網站規格
- 類型：{靜態網站 / 動態網站}
- 風格：{設計風格描述}
- 頁面：{頁面列表}
- 特殊需求：{其他要求}

## 部署要求
- 平台：Render（禁止使用 GitHub Pages）
- GitHub Repo 名稱：{repo-name}

## 完成後回傳
- Render 網址（xxx.onrender.com）
- Notion 記錄連結
```

---

## 範例：太空貓咖啡館 V3

```
請幫我建立「太空貓咖啡館 V3」網站：

## 素材來源
Google Drive：https://drive.google.com/drive/folders/1PISNnkQ9zxE9xZk-Eg1zwmWoUaC7hm1n?usp=sharing

## 網站規格
- 類型：靜態網站（HTML + CSS + JS）
- 風格：深藍太空主題、可愛貓咪元素、現代簡約
- 頁面：
  - 首頁（Hero 區塊 + 特色介紹）
  - 關於我們（品牌故事）
  - 菜單（咖啡、甜點、輕食）
  - 聯絡資訊（地址、營業時間、地圖）
- 特殊需求：
  - 響應式設計（手機、平板、桌面）
  - 缺少的文案用 AI 生成
  - 使用 Google Drive 中的 Logo 和圖片

## 部署要求
- 平台：Render（禁止使用 GitHub Pages、Vercel、Netlify）
- GitHub Repo 名稱：space-cat-cafe-v3

## 完成後回傳
- Render 網址（xxx.onrender.com）
- Notion 記錄連結
```

---

## 可複製的 LINE 訊息

### 太空貓咖啡館 V3（完整版）

```
請幫我建立「太空貓咖啡館 V3」網站：

素材：https://drive.google.com/drive/folders/1PISNnkQ9zxE9xZk-Eg1zwmWoUaC7hm1n?usp=sharing

規格：
- 靜態網站（HTML + CSS + JS）
- 深藍太空主題 + 可愛貓咪
- 頁面：首頁、關於我們、菜單、聯絡資訊
- 響應式設計
- 缺少的文案用 AI 生成

部署到 Render，完成後給我網址和 Notion 連結
```

### 太空貓咖啡館 V3（簡短版）

```
建立「太空貓咖啡館 V3」網站

素材：https://drive.google.com/drive/folders/1PISNnkQ9zxE9xZk-Eg1zwmWoUaC7hm1n?usp=sharing

深藍太空主題、響應式設計
頁面：首頁、關於、菜單、聯絡
部署到 Render
```

---

## 其他類型網站範例

### 電商網站模板

```
請幫我建立「{店名}」電商網站：

素材：{Google Drive 連結}

規格：
- 動態網站（需要後端）
- 頁面：首頁、產品列表、產品詳情、購物車、結帳
- 風格：{描述}

部署到 Render，完成後給我網址
```

### 作品集網站模板

```
請幫我建立「{名字}」作品集網站：

素材：{Google Drive 連結}

規格：
- 靜態網站
- 頁面：首頁、作品展示、關於我、聯絡
- 風格：{描述}

部署到 Render，完成後給我網址
```

### 公司官網模板

```
請幫我建立「{公司名}」官方網站：

素材：{Google Drive 連結}

規格：
- 靜態網站
- 頁面：首頁、服務項目、關於我們、團隊介紹、聯絡我們
- 風格：{描述}

部署到 Render，完成後給我網址
```

---

## 參數說明

| 參數 | 必填 | 說明 | 範例 |
|------|------|------|------|
| 專案名稱 | ✅ | 網站/品牌名稱 | 太空貓咖啡館 |
| Google Drive 連結 | ✅ | 素材資料夾（需公開） | https://drive.google.com/... |
| 類型 | ❌ | 靜態/動態，預設靜態 | 靜態網站 |
| 風格 | ❌ | 設計風格描述 | 深藍太空主題 |
| 頁面 | ❌ | 需要的頁面，預設自動判斷 | 首頁、關於、聯絡 |
| Repo 名稱 | ❌ | GitHub repo 名稱，預設自動生成 | space-cat-cafe |

---

## 注意事項

1. **Google Drive 連結必須是公開的**
   - 右鍵 → 分享 → 「知道連結的人都可以檢視」

2. **部署平台固定為 Render**
   - 不接受 GitHub Pages（只能靜態）
   - 不接受 Vercel、Netlify（為了統一管理）

3. **素材建議包含**
   - Logo（PNG/SVG）
   - 主視覺圖片
   - 產品/服務照片
   - 品牌色彩（如有）

---

*建立日期：2026-02-03*
*最後更新：2026-02-03*
