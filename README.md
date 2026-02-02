# 财经资讯聚合平台

每小时自动收集财经新闻、AI 去噪过滤、实时展示的平台。

## 功能特性

- **多源采集**：东方财富、财联社、Google News
- **智能去重**：URL + 内容指纹 + 语义相似度三层去重
- **AI 过滤**：GLM-4 自动评分、分类、提取关键词（可选）
- **定时任务**：每小时自动采集
- **实时推送**：SSE 实时新闻流
- **响应式前端**：支持搜索、筛选、收藏

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.11 + FastAPI + SQLAlchemy |
| 数据库 | PostgreSQL 16 |
| 任务调度 | APScheduler |
| 前端 | React 18 + Vite + TailwindCSS |
| AI | GLM-4 API（可选） |

## 快速开始

### 前置条件

- Docker 和 Docker Compose
- 或者：Python 3.11+、Node.js 20+、PostgreSQL 16+

### 方式一：Docker 开发环境（推荐）

```bash
# 1. 克隆项目
cd E:\project\news

# 2. 启动开发环境
docker-compose -f docker-compose.dev.yml up -d

# 3. 运行数据库迁移
docker-compose -f docker-compose.dev.yml exec backend alembic upgrade head

# 4. 访问
# 前端: http://localhost:5173
# 后端 API: http://localhost:8000
# API 文档: http://localhost:8000/docs
```

### 方式二：本地开发

```bash
# 1. 启动 PostgreSQL（确保运行在 localhost:5432）

# 2. 创建数据库
psql -U postgres -c "CREATE DATABASE news_db;"

# 3. 后端
cd backend
python -m venv venv
.\venv\Scripts\activate  # Windows
pip install -r requirements.txt
cp .env.example .env     # 编辑配置
alembic upgrade head     # 数据库迁移
uvicorn app.main:app --reload

# 4. 前端（新终端）
cd frontend
npm install
npm run dev
```

## 生产部署

### 1. 准备环境变量

```bash
# 复制示例配置
cp .env.example .env

# 编辑 .env 文件，设置安全密码
```

**.env 必填项：**

```env
# 数据库（必须修改！）
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=news_db

# AI 过滤（可选，不配置则禁用 AI 功能）
GLM_API_KEY=your_glm_api_key
```

### 2. 启动服务

```bash
# 构建并启动
docker-compose up -d --build

# 运行数据库迁移
docker-compose exec backend alembic upgrade head

# 查看日志
docker-compose logs -f
```

### 3. 访问地址

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost:3000 |
| 后端 API | http://localhost:8000 |
| API 文档 | http://localhost:8000/docs |

### 4. 反向代理（可选）

使用 Nginx 反向代理示例：

```nginx
server {
    listen 80;
    server_name news.example.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';

        # SSE 支持
        proxy_buffering off;
        proxy_read_timeout 86400s;
    }
}
```

## 配置说明

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `DATABASE_URL` | - | PostgreSQL 连接 URL |
| `GLM_API_KEY` | - | 智谱 AI API Key（可选） |
| `HTTPS_PROXY` 或 `HTTP_PROXY` | - | 代理服务器（Google News 采集必需） |
| `COLLECTION_INTERVAL_HOURS` | 1 | 采集间隔（小时） |
| `AI_QUALITY_THRESHOLD` | 0.3 | AI 质量过滤阈值 |
| `DEFAULT_PAGE_SIZE` | 20 | 默认分页大小 |
| `DEBUG` | false | 调试模式 |

### Google News 采集器配置

本项目已集成 [GNews](https://github.com/ranahaani/GNews) 库用于采集 Google News 财经新闻。

**重要提示：**
- Google News 需要配置代理才能正常访问（设置 `HTTPS_PROXY` 或 `HTTP_PROXY` 环境变量）
- 如果不配置代理，GNews 采集器将自动跳过，不影响其他采集器
- GNews 库位于 `backend/app/utils/gnews`，已作为内置模块集成

**.env 示例配置：**
```env
# 代理配置（用于 Google News）
HTTPS_PROXY=http://your-proxy-server:port
# 或
HTTP_PROXY=http://your-proxy-server:port
```

**支持的新闻源：**
- 东方财富（无需代理）
- 财联社 AKShare（无需代理）
- Google News（需要代理）

## API 接口

### 新闻列表

```
GET /api/news?page=1&per_page=20&source=eastmoney&category=宏观经济&search=关键词
```

### 实时推送

```
GET /api/news/stream  (SSE)
```

### 手动触发采集

```
POST /api/collect
POST /api/collect?source=akshare_eastmoney
```

### 统计信息

```
GET /api/stats
GET /api/sources
GET /api/categories
```

完整 API 文档：http://localhost:8000/docs

## 项目结构

```
news/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口
│   │   ├── config.py            # 配置管理
│   │   ├── database.py          # 数据库连接
│   │   ├── models/              # SQLAlchemy 模型
│   │   ├── schemas/             # Pydantic 模型
│   │   ├── api/                 # API 路由
│   │   ├── collectors/          # 新闻采集器
│   │   ├── services/            # 业务服务
│   │   └── utils/               # 工具函数
│   ├── alembic/                 # 数据库迁移
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/          # React 组件
│   │   ├── hooks/               # 自定义 Hooks
│   │   └── pages/               # 页面
│   └── package.json
├── docker-compose.yml           # 生产环境
├── docker-compose.dev.yml       # 开发环境
└── .env.example                 # 环境变量示例
```

## 常用命令

```bash
# 开发环境
docker-compose -f docker-compose.dev.yml up -d
docker-compose -f docker-compose.dev.yml logs -f backend
docker-compose -f docker-compose.dev.yml down

# 生产环境
docker-compose up -d --build
docker-compose logs -f
docker-compose down

# 数据库迁移
docker-compose exec backend alembic upgrade head
docker-compose exec backend alembic revision --autogenerate -m "description"

# 手动触发采集
curl -X POST http://localhost:8000/api/collect
```

## 故障排查

### 数据库连接失败

```bash
# 检查 PostgreSQL 是否运行
docker-compose ps

# 查看数据库日志
docker-compose logs db
```

### 采集无数据

```bash
# 查看后端日志
docker-compose logs backend

# 手动触发采集并查看结果
curl -X POST http://localhost:8000/api/collect
```

### AI 过滤未生效

检查 `.env` 中是否配置了 `GLM_API_KEY`。未配置时 AI 功能自动禁用，新闻仍可正常采集和展示。

## 许可证

MIT
