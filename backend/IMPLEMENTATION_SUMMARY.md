# FastAPI 后端实现总结

## ✅ 已完成功能

### 1. 核心架构

```
backend/
├── app/
│   ├── main.py                    # ✅ FastAPI 应用入口
│   ├── config.py                  # ✅ 配置管理
│   ├── api/                       # ✅ API 路由层
│   │   ├── auth.py                #    - 简单登录
│   │   ├── sessions.py            #    - 会话CRUD
│   │   └── chat.py                #    - 对话+历史
│   ├── models/                    # ✅ 数据模型
│   │   ├── database.py            #    - SQLite配置
│   │   ├── session.py             #    - 会话表
│   │   └── message.py             #    - 消息表
│   ├── schemas/                   # ✅ Pydantic模式
│   │   ├── auth.py
│   │   ├── session.py
│   │   └── chat.py
│   └── services/                  # ✅ 业务逻辑层
│       ├── workspace_service.py   #    - 工作空间管理
│       ├── history_service.py     #    - 对话历史
│       └── agent_service.py       #    - Agent集成
└── data/
    ├── shared_env/
    │   └── allowed_packages.txt   # ✅ 包白名单
    ├── database/                  # ✅ SQLite数据库
    └── workspaces/                # ✅ 用户工作空间
```

### 2. API 接口

#### 认证 API
- ✅ `POST /api/auth/login` - 简单登录（用户名/密码）
- ✅ `GET /api/auth/me` - 获取当前用户信息

#### 会话管理 API
- ✅ `POST /api/sessions` - 创建会话
- ✅ `GET /api/sessions` - 获取会话列表
- ✅ `GET /api/sessions/{id}` - 获取会话详情
- ✅ `DELETE /api/sessions/{id}` - 关闭会话（可选保留文件）

#### 对话 API
- ✅ `POST /api/chat/{session_id}` - 发送消息
- ✅ `GET /api/chat/{session_id}/history` - 获取对话历史

### 3. 核心特性

- ✅ **简单认证** - 基于用户名/密码（配置在 .env）
- ✅ **会话管理** - 多轮对话，手动创建/关闭
- ✅ **对话持久化** - SQLite 存储完整历史
- ✅ **工作空间隔离** - 每个用户独立目录
- ✅ **文件自动保留** - .pdf/.xlsx/.pptx/.docx 等
- ✅ **Agent 集成** - 连接 Mini-Agent 核心
- ✅ **包白名单** - 基于 Skills 需求的安全包列表

### 4. 安全机制

- ✅ **包白名单**：`data/shared_env/allowed_packages.txt`
  - 包含 20+ 个基于 Skills 需求的包
  - pypdf, reportlab, python-pptx, openpyxl, pandas, Pillow 等

- ✅ **工作空间隔离**：每个用户独立目录
  ```
  workspaces/
  ├── user_demo/
  │   ├── shared_files/    # 持久化文件
  │   └── sessions/        # 会话临时文件
  └── user_test/
      └── ...
  ```

- ✅ **会话超时**：可配置的超时和最大时长
  - SESSION_INACTIVE_TIMEOUT_HOURS=1
  - SESSION_MAX_DURATION_HOURS=24

## 📦 包白名单详情

基于你的 Skills 分析，已包含：

### 文档处理 (Document Skills)
- pypdf, pdfplumber, reportlab (PDF)
- python-pptx (PowerPoint)
- python-docx (Word)
- openpyxl, xlrd, xlsxwriter (Excel)

### 数据处理
- pandas, numpy

### 图像处理 (Canvas Design, GIF Creator)
- Pillow

### 可视化
- matplotlib, seaborn

### 工具库
- requests, httpx, pyyaml, jinja2, scipy

## 🚀 快速启动

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入 MINIMAX_API_KEY
```

### 3. 启动服务

```bash
# 方式1：使用 uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 方式2：直接运行
python -m app.main
```

### 4. 测试 API

```bash
# 运行测试脚本
python test_api.py

# 或访问 API 文档
open http://localhost:8000/api/docs
```

## 📝 使用示例

### 完整流程

```bash
# 1. 登录
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"demo123"}'
# 返回: {"user_id": "demo", ...}

# 2. 创建会话
curl -X POST "http://localhost:8000/api/sessions?user_id=demo" \
  -H "Content-Type: application/json" \
  -d '{"title":"我的会话"}'
# 返回: {"id": "uuid-xxx", ...}

# 3. 发送消息
curl -X POST "http://localhost:8000/api/chat/uuid-xxx?user_id=demo" \
  -H "Content-Type: application/json" \
  -d '{"message":"帮我生成一个PDF"}'
# 返回: {"message": "已生成PDF...", "files": ["report.pdf"], ...}

# 4. 获取历史
curl "http://localhost:8000/api/chat/uuid-xxx/history?user_id=demo"
# 返回: {"messages": [...], "total": 5}

# 5. 关闭会话
curl -X DELETE "http://localhost:8000/api/sessions/uuid-xxx?user_id=demo"
# 返回: {"status": "closed", "preserved_files": ["outputs/20251117_100000_report.pdf"]}
```

## 🎯 工作流程

```
用户登录
  ↓
创建会话 → 生成 workspace/user_xxx/sessions/session_xxx/
  ↓
发送消息 → Agent 执行 → 生成文件到 files/
  ↓
继续对话 → Agent 有上下文记忆
  ↓
关闭会话 → 保留 .pdf/.xlsx等 到 shared_files/outputs/
  ↓
删除临时文件
```

## ⚙️ 配置说明

### 默认用户

编辑 `.env` 中的 `SIMPLE_AUTH_USERS`：
```env
SIMPLE_AUTH_USERS="demo:demo123,test:test123,alice:alice456"
```

格式：`username:password,username2:password2`

### 会话超时

```env
SESSION_INACTIVE_TIMEOUT_HOURS=1    # 1小时无活动关闭
SESSION_MAX_DURATION_HOURS=24        # 24小时最大生命周期
SESSION_MAX_TURNS=50                 # 50轮对话限制
```

### 文件保留

```env
PRESERVE_FILE_EXTENSIONS=[".pdf",".xlsx",".pptx",".docx",".png"]
```

会话关闭时，只保留这些格式的文件到 `shared_files/outputs/`

## 🔧 开发建议

### 添加新的工具

编辑 `app/services/agent_service.py` 的 `_create_tools()` 方法：

```python
def _create_tools(self) -> List:
    tools = [
        # 现有工具...

        # 添加新工具
        YourNewTool(workspace_dir=str(self.workspace_dir)),
    ]
    return tools
```

### 添加 Skills 支持

在 `agent_service.py` 中添加：

```python
from mini_agent.tools.skill_tool import create_skill_tools

# 在 _create_tools() 中
skill_tools, skill_loader = create_skill_tools(skills_dir)
tools.extend(skill_tools)
```

### 添加 MCP Tools

在 `agent_service.py` 中添加：

```python
from mini_agent.tools.mcp_loader import load_mcp_tools_async

# 在 initialize_agent() 中
mcp_tools = await load_mcp_tools_async(mcp_config_path)
tools.extend(mcp_tools)
```

## ⚠️ 注意事项

### 1. 生产环境部署

- ❌ **不要**使用 `SIMPLE_AUTH_USERS`（不安全）
- ✅ **应该**实现 JWT 认证和用户数据库
- ✅ **应该**升级到 PostgreSQL
- ✅ **应该**添加速率限制
- ✅ **应该**添加日志和监控

### 2. 数据库

当前使用 SQLite，适合开发和小规模使用。

生产环境建议：
```env
DATABASE_URL="postgresql://user:pass@localhost/mini_agent"
```

### 3. Mini-Agent 路径

`agent_service.py` 中硬编码了 `mini_agent` 的路径：
```python
mini_agent_path = Path(__file__).parent.parent.parent.parent / "mini_agent"
```

如果目录结构不同，需要调整此路径。

## 📊 数据库结构

### sessions 表
- id (主键)
- user_id (用户名)
- created_at, last_active, closed_at
- status (active/closed/expired)
- title
- message_count, turn_count

### messages 表
- id (自增主键)
- session_id (外键)
- role (system/user/assistant/tool)
- content, thinking, tool_calls
- created_at

## 🐛 故障排除

### 找不到 mini_agent 模块

确保目录结构：
```
/
├── backend/
│   └── app/
└── mini_agent/
```

或修改 `agent_service.py` 中的路径。

### SQLite 权限错误

```bash
mkdir -p backend/data/database
chmod 755 backend/data/database
```

### CORS 错误

检查 `.env` 中的 `CORS_ORIGINS` 包含前端地址。

## 🎉 下一步

1. **前端集成**
   - 创建 React/Vue 前端
   - 使用 WebSocket 实现实时对话

2. **完善认证**
   - 实现 JWT 认证
   - 添加用户注册
   - 实现权限管理

3. **添加功能**
   - 文件上传/下载 API
   - 会话分享功能
   - 对话导出（PDF/Markdown）

4. **性能优化**
   - 添加 Redis 缓存
   - 使用 Celery 异步任务
   - 添加 CDN 服务文件

5. **安全增强**
   - 实现 SafeBashTool
   - 添加速率限制
   - 实现审计日志
