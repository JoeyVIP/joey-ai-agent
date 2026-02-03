[AUTOMATED EXECUTION MODE - WEB FRONTEND PROJECT]

建立「Joey AI Agent Web Frontend」完整專案。

工作目錄：/Users/JoeyLiao/Joey's AI Agent /joey-ai-agent

## 執行順序

1. 後端擴充（在 joey-ai-agent 內）
   - 新增 src/database/ 模組（models.py, session.py）
   - 新增 src/api/auth.py（GitHub OAuth）
   - 新增 src/api/projects.py（CRUD + SSE）
   - 新增 src/api/uploads.py（檔案上傳）
   - 新增 src/schemas/project.py
   - 新增 src/services/web_task_processor.py
   - 修改 src/config.py（新增 DB、OAuth 設定）
   - 修改 src/main.py（註冊新路由）

2. 前端建立
   - 在 joey-ai-agent 同層目錄建立 web-frontend/
   - 路徑：/Users/JoeyLiao/Joey's AI Agent /web-frontend/
   - 初始化 Next.js 14 專案
   - 安裝：tailwindcss, shadcn/ui, zustand, next-auth
   - 建立所有頁面和元件

3. 部署設定
   - 建立 render.yaml（後端 + 前端）
   - 推送到 GitHub
   - 部署到 Render

## 資料庫 Schema

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    github_id VARCHAR(255) UNIQUE NOT NULL,
    github_username VARCHAR(255),
    email VARCHAR(255),
    avatar_url TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE projects (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    site_type VARCHAR(50) DEFAULT 'static',
    style_description TEXT,
    color_scheme JSONB,
    font_selection JSONB,
    backend_type VARCHAR(50) DEFAULT 'none',
    pages JSONB,
    google_drive_url TEXT,
    seo_title VARCHAR(255),
    seo_description TEXT,
    seo_keywords TEXT[],
    og_image TEXT,
    ga4_id VARCHAR(50),
    fb_pixel_id VARCHAR(50),
    gtm_id VARCHAR(50),
    status VARCHAR(50) DEFAULT 'pending',
    current_step VARCHAR(50),
    github_url TEXT,
    deploy_url TEXT,
    notion_url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

CREATE TABLE project_progress (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(id),
    step VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    message TEXT,
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE uploads (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(id),
    file_type VARCHAR(50),
    file_name VARCHAR(255),
    file_path TEXT,
    file_size INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 前端頁面結構

```
web-frontend/src/app/
├── page.tsx                    # 首頁/登入
├── dashboard/page.tsx          # 儀表板
├── projects/
│   ├── new/page.tsx            # 新建專案（5 步驟表單）
│   └── [id]/
│       ├── page.tsx            # 專案詳情
│       └── progress/page.tsx   # 即時進度監控
└── settings/page.tsx           # 設定
```

## 進度監控步驟

```python
PROGRESS_STEPS = [
    ("task_received", "任務已接收", "📝"),
    ("analyzing", "分析需求中", "🔍"),
    ("downloading_assets", "下載素材中", "📥"),
    ("creating_structure", "建立專案結構", "📁"),
    ("building_pages", "建立頁面中", "🏗️"),
    ("styling", "套用樣式中", "🎨"),
    ("adding_scripts", "加入互動功能", "⚡"),
    ("pushing_github", "推送到 GitHub", "📤"),
    ("deploying_render", "部署到 Render", "🚀"),
    ("verifying", "驗證部署中", "✅"),
    ("completed", "完成", "🎉"),
]
```

## 關鍵要求

- 使用 TypeScript
- 繁體中文介面
- 響應式設計（Mobile-First）
- 真實進度監控（SSE）
- GitHub SSO 登入
- 部署到 Render

## 完成後輸出

---RESULT---
PROJECT_NAME: joey-ai-frontend
GITHUB_URL: https://github.com/...
DEPLOY_URL: https://....onrender.com
STATUS: SUCCESS
---END---
