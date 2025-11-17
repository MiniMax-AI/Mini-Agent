# Mini-Agent FastAPI 后端

基于讨论的架构设计实现的 FastAPI 后端服务。

## 特性

- ✅ 简单认证（用户名/密码）
- ✅ 会话管理（创建、列表、详情、关闭）
- ✅ 多轮对话（支持上下文记忆）
- ✅ 对话历史持久化（SQLite）
- ✅ 文件管理（自动保留特定格式）
- ✅ 工作空间隔离
- ✅ 包白名单控制

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 LLM API Key（支持 MiniMax、GLM、OpenAI 等）
# 详见 CONFIG_SECURITY.md
```

### 3. 启动服务

```bash
# 开发模式
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或者直接运行
python -m app.main
```

### 4. 访问 API 文档

打开浏览器访问：
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## API 使用示例

### 1. 登录

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "demo",
    "password": "demo123"
  }'
```

返回：
```json
{
  "user_id": "demo",
  "username": "demo",
  "message": "登录成功"
}
```

### 2. 创建会话

```bash
curl -X POST "http://localhost:8000/api/sessions?user_id=demo" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "我的第一个会话"
  }'
```

返回：
```json
{
  "id": "uuid-here",
  "user_id": "demo",
  "created_at": "2025-11-17T10:00:00",
  "status": "active",
  ...
}
```

### 3. 发送消息

```bash
curl -X POST "http://localhost:8000/api/chat/{session_id}?user_id=demo" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "帮我生成一个 PDF 文件，内容是 Hello World"
  }'
```

### 4. 获取对话历史

```bash
curl "http://localhost:8000/api/chat/{session_id}/history?user_id=demo"
```

### 5. 关闭会话

```bash
curl -X DELETE "http://localhost:8000/api/sessions/{session_id}?user_id=demo&preserve_files=true"
```

## 项目结构

```
backend/
├── app/
│   ├── main.py                    # 应用入口
│   ├── config.py                  # 配置管理
│   ├── api/                       # API 路由
│   │   ├── auth.py                # 认证
│   │   ├── sessions.py            # 会话管理
│   │   └── chat.py                # 对话
│   ├── models/                    # 数据模型
│   │   ├── database.py
│   │   ├── session.py
│   │   └── message.py
│   ├── schemas/                   # Pydantic 模式
│   │   ├── auth.py
│   │   ├── session.py
│   │   └── chat.py
│   └── services/                  # 业务逻辑
│       ├── workspace_service.py
│       ├── history_service.py
│       └── agent_service.py
├── data/
│   ├── database/                  # SQLite 数据库
│   ├── shared_env/                # 共享 Python 环境
│   └── workspaces/                # 用户工作空间
├── requirements.txt
├── .env.example
└── README.md
```

## 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `MINIMAX_API_KEY` | MiniMax API 密钥 | 必填 |
| `SIMPLE_AUTH_USERS` | 用户列表 | `demo:demo123` |
| `CORS_ORIGINS` | 允许的跨域来源 | `["http://localhost:3000"]` |
| `AGENT_MAX_STEPS` | Agent 最大执行步数 | `100` |
| `SESSION_INACTIVE_TIMEOUT_HOURS` | 会话超时时间 | `1` |

### 包白名单

编辑 `data/shared_env/allowed_packages.txt` 添加允许安装的包。

## 开发指南

### 添加新的 API 接口

1. 在 `app/api/` 创建新的路由文件
2. 在 `app/main.py` 中注册路由
3. 如需数据库，在 `app/models/` 添加模型
4. 业务逻辑放在 `app/services/`

### 数据库迁移

```bash
# 生成迁移
alembic revision --autogenerate -m "描述"

# 执行迁移
alembic upgrade head
```

## 部署

### 生产环境

```bash
# 使用 gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker 部署

（待实现）

## 故障排除

### 1. 找不到 mini_agent 模块

确保 `mini_agent/` 目录在正确的位置，或者修改 `app/services/agent_service.py` 中的路径。

### 2. 数据库权限错误

确保 `data/database/` 目录存在且有写权限。

### 3. CORS 错误

检查 `.env` 中的 `CORS_ORIGINS` 配置是否包含前端地址。

## 许可证

MIT
