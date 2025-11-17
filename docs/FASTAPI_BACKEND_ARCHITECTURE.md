# Mini-Agent FastAPI 后端架构设计

> 基于讨论确定的方案：统一环境 + 用户文件隔离 + SQLite + 多轮对话

## 📋 目录
- [架构概览](#架构概览)
- [目录结构](#目录结构)
- [数据库设计](#数据库设计)
- [核心模块](#核心模块)
- [API 接口](#api-接口)
- [Workspace 管理](#workspace-管理)
- [安全机制](#安全机制)
- [部署配置](#部署配置)

---

## 架构概览

### 核心架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        前端 (React/Vue)                          │
│  • 会话列表  • 对话界面  • 文件管理  • 用户设置                  │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/WebSocket
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI 应用层                               │
├─────────────────────────────────────────────────────────────────┤
│  Routers:                                                        │
│  ├─ /api/auth        - 认证授权                                 │
│  ├─ /api/sessions    - 会话管理                                 │
│  ├─ /api/chat        - 对话接口                                 │
│  ├─ /api/files       - 文件管理                                 │
│  └─ /api/admin       - 管理接口                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     业务逻辑层 (Services)                        │
├─────────────────────────────────────────────────────────────────┤
│  • SessionService    - 会话管理                                 │
│  • AgentService      - Agent 执行                               │
│  • WorkspaceService  - 工作空间管理                             │
│  • HistoryService    - 对话历史                                 │
│  • FileService       - 文件管理                                 │
│  • QuotaService      - 配额管理                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
    │   SQLite    │  │  Workspace  │  │ Mini-Agent  │
    │   数据库     │  │  文件系统    │  │   Core      │
    └─────────────┘  └─────────────┘  └─────────────┘
```

### 技术栈

```yaml
后端框架: FastAPI 0.104+
数据库: SQLite 3.x (生产可升级 PostgreSQL)
ORM: SQLAlchemy 2.0+
认证: JWT (python-jose)
任务队列: asyncio (简单) / Celery (复杂)
缓存: 内存 dict (简单) / Redis (生产)
日志: loguru
配置: pydantic-settings
```

---

## 目录结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI 应用入口
│   ├── config.py                  # 配置管理
│   ├── dependencies.py            # 依赖注入
│   │
│   ├── api/                       # API 路由
│   │   ├── __init__.py
│   │   ├── auth.py                # 认证接口
│   │   ├── sessions.py            # 会话管理
│   │   ├── chat.py                # 对话接口
│   │   ├── files.py               # 文件管理
│   │   └── admin.py               # 管理接口
│   │
│   ├── services/                  # 业务逻辑
│   │   ├── __init__.py
│   │   ├── session_service.py     # 会话服务
│   │   ├── agent_service.py       # Agent 服务
│   │   ├── workspace_service.py   # 工作空间服务
│   │   ├── history_service.py     # 历史服务
│   │   ├── file_service.py        # 文件服务
│   │   └── quota_service.py       # 配额服务
│   │
│   ├── models/                    # 数据模型
│   │   ├── __init__.py
│   │   ├── database.py            # 数据库配置
│   │   ├── user.py                # 用户模型
│   │   ├── session.py             # 会话模型
│   │   ├── message.py             # 消息模型
│   │   └── file.py                # 文件模型
│   │
│   ├── schemas/                   # Pydantic 模式
│   │   ├── __init__.py
│   │   ├── auth.py                # 认证请求/响应
│   │   ├── session.py             # 会话请求/响应
│   │   ├── chat.py                # 对话请求/响应
│   │   └── file.py                # 文件请求/响应
│   │
│   ├── core/                      # 核心组件
│   │   ├── __init__.py
│   │   ├── security.py            # 安全相关
│   │   ├── agent_wrapper.py       # Agent 包装器
│   │   └── allowed_packages.py    # 包白名单
│   │
│   └── utils/                     # 工具函数
│       ├── __init__.py
│       ├── logger.py              # 日志配置
│       └── helpers.py             # 辅助函数
│
├── data/                          # 数据目录
│   ├── database/
│   │   └── mini_agent.db          # SQLite 数据库
│   ├── shared_env/                # 共享环境
│   │   ├── base.venv/             # 预装包的虚拟环境
│   │   └── allowed_packages.txt   # 包白名单
│   └── workspaces/                # 用户工作空间
│       ├── user_{user_id}/
│       │   ├── shared_files/      # 持久化文件
│       │   │   ├── outputs/       # 生成的文档
│       │   │   └── data/          # 数据文件
│       │   └── sessions/
│       │       └── {session_id}/
│       │           ├── files/     # 会话临时文件
│       │           └── logs/      # 会话日志
│       └── user_{another_id}/
│
├── tests/                         # 测试
│   ├── __init__.py
│   ├── test_api/
│   ├── test_services/
│   └── test_models/
│
├── scripts/                       # 脚本
│   ├── init_db.py                 # 初始化数据库
│   ├── setup_shared_env.py        # 设置共享环境
│   └── migrate.py                 # 数据迁移
│
├── requirements.txt               # 依赖
├── .env.example                   # 环境变量示例
├── alembic.ini                    # 数据库迁移配置
└── README.md
```

---

## 数据库设计

### ER 图

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│    users     │───┐   │   sessions   │───┐   │   messages   │
├──────────────┤   │   ├──────────────┤   │   ├──────────────┤
│ id (PK)      │   └──<│ user_id (FK) │   └──<│ session_id   │
│ username     │       │ id (PK)      │       │ id (PK)      │
│ email        │       │ created_at   │       │ role         │
│ hashed_pwd   │       │ last_active  │       │ content      │
│ created_at   │       │ closed_at    │       │ thinking     │
│ is_active    │       │ status       │       │ tool_calls   │
│ quota_*      │       │ title        │       │ created_at   │
└──────────────┘       └──────────────┘       └──────────────┘
                              │
                              │
                              ▼
                       ┌──────────────┐
                       │ session_files│
                       ├──────────────┤
                       │ id (PK)      │
                       │ session_id   │
                       │ filename     │
                       │ file_path    │
                       │ file_size    │
                       │ mime_type    │
                       │ created_at   │
                       └──────────────┘
```

### SQL Schema

```sql
-- 用户表
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,

    -- 配额字段
    quota_max_sessions INTEGER DEFAULT 10,
    quota_max_storage_mb INTEGER DEFAULT 1024,
    quota_max_session_duration_hours INTEGER DEFAULT 24,

    INDEX idx_username (username),
    INDEX idx_email (email)
);

-- 会话表
CREATE TABLE sessions (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP NULL,
    status VARCHAR(20) DEFAULT 'active',  -- active, closed, expired
    title VARCHAR(255) NULL,

    -- 统计字段
    message_count INTEGER DEFAULT 0,
    turn_count INTEGER DEFAULT 0,

    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 消息表
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR(36) NOT NULL,
    role VARCHAR(20) NOT NULL,  -- system, user, assistant, tool
    content TEXT,
    thinking TEXT,
    tool_calls TEXT,  -- JSON string
    tool_call_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_session_id (session_id),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

-- 会话文件表
CREATE TABLE session_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR(36) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER,
    mime_type VARCHAR(100),
    is_preserved BOOLEAN DEFAULT FALSE,  -- 是否已保存到 shared_files
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_session_id (session_id),
    INDEX idx_filename (filename),
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

-- 用户配额使用记录表
CREATE TABLE quota_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id VARCHAR(36) NOT NULL,
    date DATE NOT NULL,
    sessions_created INTEGER DEFAULT 0,
    storage_used_mb INTEGER DEFAULT 0,

    UNIQUE(user_id, date),
    INDEX idx_user_date (user_id, date),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

---

## 核心模块

### 1. 配置管理 (`app/config.py`)

```python
from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path

class Settings(BaseSettings):
    # 应用配置
    app_name: str = "Mini-Agent Backend"
    app_version: str = "0.1.0"
    debug: bool = False

    # API 配置
    api_prefix: str = "/api"
    cors_origins: list[str] = ["http://localhost:3000"]

    # 数据库配置
    database_url: str = "sqlite:///./data/database/mini_agent.db"

    # JWT 配置
    secret_key: str  # 必须设置
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 小时

    # MiniMax API 配置
    minimax_api_key: str
    minimax_api_base: str = "https://api.minimax.chat"
    minimax_model: str = "MiniMax-Text-01"

    # 工作空间配置
    workspace_base: Path = Path("./data/workspaces")
    shared_env_path: Path = Path("./data/shared_env/base.venv")
    allowed_packages_file: Path = Path("./data/shared_env/allowed_packages.txt")

    # 配额默认值
    default_max_sessions: int = 10
    default_max_storage_mb: int = 1024
    default_max_session_duration_hours: int = 24

    # Agent 配置
    agent_max_steps: int = 100
    agent_token_limit: int = 80000

    # 文件保留配置
    preserve_file_extensions: list[str] = [".pdf", ".xlsx", ".pptx", ".docx"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

### 2. 数据库模型 (`app/models/`)

#### `database.py`
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import get_settings

settings = get_settings()

# 创建引擎
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},  # SQLite 需要
    echo=settings.debug
)

# 会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 类
Base = declarative_base()

# 依赖注入：获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

#### `user.py`
```python
from sqlalchemy import Column, String, Boolean, Integer, DateTime
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # 配额
    quota_max_sessions = Column(Integer, default=10)
    quota_max_storage_mb = Column(Integer, default=1024)
    quota_max_session_duration_hours = Column(Integer, default=24)
```

#### `session.py`
```python
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from datetime import datetime
from .database import Base

class Session(Base):
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    last_active = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="active", index=True)
    title = Column(String(255), nullable=True)

    message_count = Column(Integer, default=0)
    turn_count = Column(Integer, default=0)
```

#### `message.py`
```python
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from datetime import datetime
from .database import Base

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=True)
    thinking = Column(Text, nullable=True)
    tool_calls = Column(Text, nullable=True)  # JSON string
    tool_call_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
```

### 3. Pydantic Schemas (`app/schemas/`)

#### `session.py`
```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class SessionCreate(BaseModel):
    """创建会话请求"""
    title: Optional[str] = None

class SessionResponse(BaseModel):
    """会话响应"""
    id: str
    user_id: str
    created_at: datetime
    last_active: datetime
    status: str
    title: Optional[str]
    message_count: int
    turn_count: int

    class Config:
        from_attributes = True

class SessionList(BaseModel):
    """会话列表响应"""
    sessions: list[SessionResponse]
    total: int
```

#### `chat.py`
```python
from pydantic import BaseModel, Field
from typing import Optional, List

class ChatRequest(BaseModel):
    """对话请求"""
    message: str = Field(..., min_length=1, max_length=10000)

class ChatResponse(BaseModel):
    """对话响应"""
    session_id: str
    message: str
    thinking: Optional[str] = None
    files: List[str] = []
    turn: int
    message_count: int
```

### 4. 业务服务 (`app/services/`)

#### `workspace_service.py`
```python
from pathlib import Path
import shutil
from typing import List
from app.config import get_settings

settings = get_settings()

class WorkspaceService:
    """工作空间管理服务"""

    def __init__(self):
        self.base_path = settings.workspace_base
        self.base_path.mkdir(parents=True, exist_ok=True)

    def create_session_workspace(self, user_id: str, session_id: str) -> Path:
        """创建会话工作空间"""
        session_dir = self._get_session_dir(user_id, session_id)

        # 创建目录结构
        session_dir.mkdir(parents=True, exist_ok=True)
        (session_dir / "files").mkdir(exist_ok=True)
        (session_dir / "logs").mkdir(exist_ok=True)

        # 创建符号链接到 shared_files
        shared_dir = self._get_user_shared_dir(user_id)
        shared_dir.mkdir(parents=True, exist_ok=True)

        shared_link = session_dir / "shared"
        if not shared_link.exists():
            shared_link.symlink_to(shared_dir, target_is_directory=True)

        return session_dir

    def cleanup_session(
        self,
        user_id: str,
        session_id: str,
        preserve_files: bool = True
    ) -> List[str]:
        """清理会话工作空间"""
        session_dir = self._get_session_dir(user_id, session_id)
        preserved_files = []

        if preserve_files:
            # 保留特定格式的文件
            files_dir = session_dir / "files"
            if files_dir.exists():
                for file in files_dir.iterdir():
                    if file.suffix.lower() in settings.preserve_file_extensions:
                        # 移动到 shared_files/outputs
                        dest_dir = self._get_user_shared_dir(user_id) / "outputs"
                        dest_dir.mkdir(parents=True, exist_ok=True)

                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        dest_file = dest_dir / f"{timestamp}_{file.name}"
                        shutil.copy2(file, dest_file)
                        preserved_files.append(str(dest_file))

        # 删除会话目录
        if session_dir.exists():
            shutil.rmtree(session_dir, ignore_errors=True)

        return preserved_files

    def _get_session_dir(self, user_id: str, session_id: str) -> Path:
        """获取会话目录路径"""
        return self.base_path / f"user_{user_id}" / "sessions" / session_id

    def _get_user_shared_dir(self, user_id: str) -> Path:
        """获取用户共享目录路径"""
        return self.base_path / f"user_{user_id}" / "shared_files"

    def get_session_files(self, user_id: str, session_id: str) -> List[Path]:
        """获取会话的所有文件"""
        files_dir = self._get_session_dir(user_id, session_id) / "files"
        if not files_dir.exists():
            return []
        return list(files_dir.iterdir())
```

#### `history_service.py`
```python
from sqlalchemy.orm import Session as DBSession
from app.models.message import Message
from app.models.session import Session
from typing import List, Dict
import json

class HistoryService:
    """对话历史服务"""

    def __init__(self, db: DBSession):
        self.db = db

    def save_message(
        self,
        session_id: str,
        role: str,
        content: str = None,
        thinking: str = None,
        tool_calls: List[Dict] = None,
        tool_call_id: str = None
    ) -> Message:
        """保存消息到数据库"""
        message = Message(
            session_id=session_id,
            role=role,
            content=content,
            thinking=thinking,
            tool_calls=json.dumps(tool_calls, ensure_ascii=False) if tool_calls else None,
            tool_call_id=tool_call_id
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)

        # 更新会话的消息计数
        session = self.db.query(Session).filter(Session.id == session_id).first()
        if session:
            session.message_count += 1
            if role == "user":
                session.turn_count += 1
            self.db.commit()

        return message

    def load_session_history(self, session_id: str) -> List[Dict]:
        """加载会话历史"""
        messages = self.db.query(Message)\
            .filter(Message.session_id == session_id)\
            .order_by(Message.created_at)\
            .all()

        return [
            {
                "role": msg.role,
                "content": msg.content,
                "thinking": msg.thinking,
                "tool_calls": json.loads(msg.tool_calls) if msg.tool_calls else None,
                "tool_call_id": msg.tool_call_id,
                "created_at": msg.created_at.isoformat()
            }
            for msg in messages
        ]

    def get_message_count(self, session_id: str) -> int:
        """获取消息数量"""
        return self.db.query(Message)\
            .filter(Message.session_id == session_id)\
            .count()
```

#### `agent_service.py`
```python
from mini_agent.agent import Agent
from mini_agent.llm import LLMClient
from mini_agent.schema import LLMProvider, Message as AgentMessage
from app.services.history_service import HistoryService
from app.core.agent_wrapper import create_safe_agent
from typing import List, Dict
from pathlib import Path

class AgentService:
    """Agent 服务"""

    def __init__(
        self,
        workspace_dir: Path,
        history_service: HistoryService,
        session_id: str
    ):
        self.workspace_dir = workspace_dir
        self.history_service = history_service
        self.session_id = session_id
        self.agent = None
        self._last_saved_index = 0

    def initialize_agent(self, system_prompt: str, tools: List):
        """初始化 Agent"""
        self.agent = create_safe_agent(
            workspace_dir=str(self.workspace_dir),
            system_prompt=system_prompt,
            tools=tools
        )

        # 从数据库恢复历史
        self._restore_history()

    def _restore_history(self):
        """从数据库恢复对话历史"""
        history = self.history_service.load_session_history(self.session_id)

        # 跳过 system message（index 0）
        for msg_data in history:
            if msg_data["role"] == "user":
                self.agent.messages.append(
                    AgentMessage(role="user", content=msg_data["content"])
                )
            elif msg_data["role"] == "assistant":
                self.agent.messages.append(
                    AgentMessage(
                        role="assistant",
                        content=msg_data["content"],
                        thinking=msg_data.get("thinking"),
                        tool_calls=msg_data.get("tool_calls")
                    )
                )
            elif msg_data["role"] == "tool":
                self.agent.messages.append(
                    AgentMessage(
                        role="tool",
                        content=msg_data["content"],
                        tool_call_id=msg_data.get("tool_call_id")
                    )
                )

        self._last_saved_index = len(self.agent.messages)

    async def chat(self, user_message: str) -> Dict:
        """执行对话"""
        # 保存用户消息
        self.history_service.save_message(
            session_id=self.session_id,
            role="user",
            content=user_message
        )

        # 添加到 agent
        self.agent.add_user_message(user_message)

        # 执行 agent
        response = await self.agent.run()

        # 保存 agent 生成的消息
        self._save_new_messages()

        return {
            "response": response,
            "message_count": len(self.agent.messages)
        }

    def _save_new_messages(self):
        """保存新增的消息到数据库"""
        for msg in self.agent.messages[self._last_saved_index:]:
            if msg.role == "assistant":
                self.history_service.save_message(
                    session_id=self.session_id,
                    role="assistant",
                    content=msg.content,
                    thinking=msg.thinking,
                    tool_calls=[tc.dict() for tc in msg.tool_calls] if msg.tool_calls else None
                )
            elif msg.role == "tool":
                self.history_service.save_message(
                    session_id=self.session_id,
                    role="tool",
                    content=msg.content,
                    tool_call_id=msg.tool_call_id
                )

        self._last_saved_index = len(self.agent.messages)
```

---

## API 接口

### 路由结构

```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.api import auth, sessions, chat, files, admin

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 路由
app.include_router(auth.router, prefix=f"{settings.api_prefix}/auth", tags=["认证"])
app.include_router(sessions.router, prefix=f"{settings.api_prefix}/sessions", tags=["会话"])
app.include_router(chat.router, prefix=f"{settings.api_prefix}/chat", tags=["对话"])
app.include_router(files.router, prefix=f"{settings.api_prefix}/files", tags=["文件"])
app.include_router(admin.router, prefix=f"{settings.api_prefix}/admin", tags=["管理"])

@app.get("/")
async def root():
    return {"message": "Mini-Agent API", "version": settings.app_version}

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

### 核心接口

#### 1. 会话管理 (`app/api/sessions.py`)

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from app.models.database import get_db
from app.models.session import Session
from app.models.user import User
from app.schemas.session import SessionCreate, SessionResponse, SessionList
from app.services.workspace_service import WorkspaceService
from app.core.security import get_current_user
from datetime import datetime
import uuid

router = APIRouter()

@router.post("", response_model=SessionResponse)
async def create_session(
    request: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """创建新会话"""
    # 检查配额
    active_sessions = db.query(Session).filter(
        Session.user_id == current_user.id,
        Session.status == "active"
    ).count()

    if active_sessions >= current_user.quota_max_sessions:
        raise HTTPException(
            status_code=429,
            detail=f"已达到最大会话数限制 ({current_user.quota_max_sessions})"
        )

    # 创建会话
    session_id = str(uuid.uuid4())
    session = Session(
        id=session_id,
        user_id=current_user.id,
        title=request.title
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # 创建工作空间
    workspace_service = WorkspaceService()
    workspace_service.create_session_workspace(current_user.id, session_id)

    return session

@router.get("", response_model=SessionList)
async def list_sessions(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """获取用户的会话列表"""
    sessions = db.query(Session)\
        .filter(Session.user_id == current_user.id)\
        .order_by(Session.created_at.desc())\
        .limit(limit)\
        .offset(offset)\
        .all()

    total = db.query(Session)\
        .filter(Session.user_id == current_user.id)\
        .count()

    return SessionList(sessions=sessions, total=total)

@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """获取会话详情"""
    session = db.query(Session).filter(
        Session.id == session_id,
        Session.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    return session

@router.delete("/{session_id}")
async def close_session(
    session_id: str,
    preserve_files: bool = True,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """关闭会话"""
    session = db.query(Session).filter(
        Session.id == session_id,
        Session.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    # 清理工作空间
    workspace_service = WorkspaceService()
    preserved = workspace_service.cleanup_session(
        current_user.id,
        session_id,
        preserve_files=preserve_files
    )

    # 更新数据库
    session.status = "closed"
    session.closed_at = datetime.utcnow()
    db.commit()

    return {
        "status": "closed",
        "preserved_files": preserved
    }
```

#### 2. 对话接口 (`app/api/chat.py`)

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from app.models.database import get_db
from app.models.session import Session
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.agent_service import AgentService
from app.services.history_service import HistoryService
from app.services.workspace_service import WorkspaceService
from app.core.security import get_current_user
from app.core.agent_wrapper import load_tools, load_system_prompt
from datetime import datetime

router = APIRouter()

# 内存中的 Agent 实例缓存
_agent_cache = {}

@router.post("/{session_id}", response_model=ChatResponse)
async def chat(
    session_id: str,
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """发送消息并获取响应"""
    # 验证会话
    session = db.query(Session).filter(
        Session.id == session_id,
        Session.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    if session.status != "active":
        raise HTTPException(status_code=410, detail="会话已关闭")

    # 检查会话是否过期
    if (datetime.utcnow() - session.created_at).total_seconds() > \
       current_user.quota_max_session_duration_hours * 3600:
        session.status = "expired"
        db.commit()
        raise HTTPException(status_code=410, detail="会话已过期")

    # 获取或创建 Agent Service
    if session_id not in _agent_cache:
        workspace_service = WorkspaceService()
        workspace_dir = workspace_service._get_session_dir(current_user.id, session_id)

        history_service = HistoryService(db)
        agent_service = AgentService(workspace_dir, history_service, session_id)

        # 初始化 Agent
        system_prompt = load_system_prompt()
        tools = load_tools(workspace_dir)
        agent_service.initialize_agent(system_prompt, tools)

        _agent_cache[session_id] = agent_service
    else:
        agent_service = _agent_cache[session_id]

    # 执行对话
    result = await agent_service.chat(request.message)

    # 更新会话活跃时间
    session.last_active = datetime.utcnow()
    db.commit()

    # 获取生成的文件
    workspace_service = WorkspaceService()
    files = workspace_service.get_session_files(current_user.id, session_id)

    return ChatResponse(
        session_id=session_id,
        message=result["response"],
        files=[f.name for f in files],
        turn=session.turn_count,
        message_count=result["message_count"]
    )
```

#### 3. 文件管理 (`app/api/files.py`)

```python
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session as DBSession
from app.models.database import get_db
from app.models.session import Session
from app.models.user import User
from app.services.workspace_service import WorkspaceService
from app.core.security import get_current_user
from typing import List

router = APIRouter()

@router.get("/{session_id}")
async def list_files(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """列出会话的所有文件"""
    # 验证会话归属
    session = db.query(Session).filter(
        Session.id == session_id,
        Session.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    workspace_service = WorkspaceService()
    files = workspace_service.get_session_files(current_user.id, session_id)

    return {
        "files": [
            {
                "name": f.name,
                "size": f.stat().st_size,
                "modified": f.stat().st_mtime
            }
            for f in files
        ]
    }

@router.get("/{session_id}/{filename}")
async def download_file(
    session_id: str,
    filename: str,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """下载文件"""
    session = db.query(Session).filter(
        Session.id == session_id,
        Session.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    workspace_service = WorkspaceService()
    file_path = workspace_service._get_session_dir(current_user.id, session_id) / "files" / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream"
    )
```

---

## 安全机制

### 1. 包白名单 (`data/shared_env/allowed_packages.txt`)

```
# 数据处理
pandas>=2.0.0,<3.0.0
numpy>=1.24.0,<2.0.0

# 文档生成
reportlab>=4.0.0,<5.0.0
python-pptx>=0.6.0,<1.0.0
python-docx>=1.0.0,<2.0.0
openpyxl>=3.1.0,<4.0.0

# 可视化
matplotlib>=3.7.0,<4.0.0
pillow>=10.0.0,<11.0.0

# 网络请求
requests>=2.31.0,<3.0.0
httpx>=0.25.0,<1.0.0

# 工具
pyyaml>=6.0,<7.0
jinja2>=3.1.0,<4.0.0

# 禁止的包（不在白名单）
# - os-sys
# - subprocess32
# - eval, exec 相关
```

### 2. 安全的 Agent 包装器 (`app/core/agent_wrapper.py`)

```python
from mini_agent.agent import Agent
from mini_agent.llm import LLMClient
from mini_agent.schema import LLMProvider
from mini_agent.tools.base import Tool
from mini_agent.tools.file_tools import ReadTool, WriteTool, EditTool
from mini_agent.tools.bash_tool import BashTool
from app.core.security import SafeBashTool
from app.config import get_settings
from pathlib import Path
from typing import List

settings = get_settings()

def create_safe_agent(
    workspace_dir: str,
    system_prompt: str,
    tools: List[Tool] = None
) -> Agent:
    """创建安全的 Agent 实例"""
    # 创建 LLM 客户端
    llm_client = LLMClient(
        api_key=settings.minimax_api_key,
        api_base=settings.minimax_api_base,
        provider=LLMProvider.ANTHROPIC,
        model=settings.minimax_model
    )

    # 加载工具（如果未提供）
    if tools is None:
        tools = load_tools(Path(workspace_dir))

    # 创建 Agent
    agent = Agent(
        llm_client=llm_client,
        system_prompt=system_prompt,
        tools=tools,
        max_steps=settings.agent_max_steps,
        workspace_dir=workspace_dir,
        token_limit=settings.agent_token_limit
    )

    return agent

def load_tools(workspace_dir: Path) -> List[Tool]:
    """加载受限的工具列表"""
    # 读取包白名单
    allowed_packages = []
    if settings.allowed_packages_file.exists():
        allowed_packages = settings.allowed_packages_file.read_text().strip().split('\n')
        allowed_packages = [p.split('>=')[0].split('==')[0] for p in allowed_packages if p and not p.startswith('#')]

    tools = [
        # 文件工具（限制在 workspace 内）
        ReadTool(workspace_dir=str(workspace_dir)),
        WriteTool(workspace_dir=str(workspace_dir)),
        EditTool(workspace_dir=str(workspace_dir)),

        # 安全的 Bash 工具
        SafeBashTool(
            workspace_dir=str(workspace_dir),
            allowed_packages=allowed_packages
        ),
    ]

    # TODO: 加载 Skills
    # TODO: 加载 MCP tools

    return tools

def load_system_prompt() -> str:
    """加载 system prompt"""
    # 读取基础 prompt
    prompt_file = Path("mini_agent/config/system_prompt.md")
    if prompt_file.exists():
        return prompt_file.read_text(encoding="utf-8")

    return "You are Mini-Agent, an AI assistant."
```

### 3. 安全的 Bash Tool (`app/core/security.py`)

```python
from mini_agent.tools.bash_tool import BashTool
from mini_agent.tools.base import ToolResult
import subprocess
from typing import List

# 命令黑名单
FORBIDDEN_COMMANDS = {
    'rm', 'rmdir', 'dd', 'mkfs',  # 删除/格式化
    'curl', 'wget', 'nc', 'telnet',  # 网络
    'sudo', 'su', 'chmod', 'chown',  # 权限
    'kill', 'killall', 'pkill',  # 进程
    'shutdown', 'reboot',  # 系统
}

# 命令白名单
ALLOWED_COMMANDS = {
    'python', 'python3', 'uv', 'pip',
    'ls', 'cat', 'echo', 'cd', 'pwd',
    'mkdir', 'touch', 'cp', 'mv',
    'grep', 'find', 'head', 'tail',
}

class SafeBashTool(BashTool):
    """安全的 Bash 工具"""

    def __init__(self, workspace_dir: str, allowed_packages: List[str]):
        super().__init__(workspace_dir)
        self.allowed_packages = allowed_packages

    async def execute(self, command: str, **kwargs) -> ToolResult:
        """执行命令（带安全检查）"""
        # 解析命令
        cmd_parts = command.split()
        if not cmd_parts:
            return ToolResult(success=False, error="空命令")

        base_cmd = cmd_parts[0]

        # 黑名单检查
        if base_cmd in FORBIDDEN_COMMANDS:
            return ToolResult(
                success=False,
                error=f"命令 '{base_cmd}' 不允许执行（安全限制）"
            )

        # 白名单检查
        if base_cmd not in ALLOWED_COMMANDS:
            return ToolResult(
                success=False,
                error=f"命令 '{base_cmd}' 不在允许列表中"
            )

        # pip install 检查
        if 'pip install' in command or 'uv pip install' in command:
            packages = self._extract_packages(command)
            for pkg in packages:
                if pkg not in self.allowed_packages:
                    return ToolResult(
                        success=False,
                        error=f"包 '{pkg}' 不在白名单中。允许的包：{', '.join(self.allowed_packages[:10])}..."
                    )

        # 执行命令（带超时）
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.workspace_dir,
                capture_output=True,
                text=True,
                timeout=60,  # 60秒超时
                env={
                    'HOME': self.workspace_dir,
                    'PATH': '/usr/local/bin:/usr/bin:/bin',
                }
            )

            return ToolResult(
                success=result.returncode == 0,
                content=result.stdout,
                error=result.stderr if result.returncode != 0 else None
            )

        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                error="命令执行超时（60秒）"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"执行失败: {str(e)}"
            )

    def _extract_packages(self, command: str) -> List[str]:
        """从 pip install 命令提取包名"""
        parts = command.split()
        if 'install' not in parts:
            return []

        idx = parts.index('install')
        packages = []
        for p in parts[idx + 1:]:
            if p.startswith('-'):
                break
            # 去除版本号
            pkg = p.split('==')[0].split('>=')[0].split('<=')[0]
            packages.append(pkg)

        return packages
```

---

## 部署配置

### 环境变量 (`.env`)

```bash
# 应用配置
APP_NAME="Mini-Agent Backend"
DEBUG=false

# JWT
SECRET_KEY="your-secret-key-change-in-production"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# MiniMax API
MINIMAX_API_KEY="your-minimax-api-key"
MINIMAX_API_BASE="https://api.minimax.chat"
MINIMAX_MODEL="MiniMax-Text-01"

# 数据库
DATABASE_URL="sqlite:///./data/database/mini_agent.db"

# CORS
CORS_ORIGINS=["http://localhost:3000","https://yourdomain.com"]

# 工作空间
WORKSPACE_BASE="./data/workspaces"
SHARED_ENV_PATH="./data/shared_env/base.venv"

# 配额
DEFAULT_MAX_SESSIONS=10
DEFAULT_MAX_STORAGE_MB=1024
DEFAULT_MAX_SESSION_DURATION_HOURS=24
```

### 初始化脚本 (`scripts/init_db.py`)

```python
"""初始化数据库"""
from app.models.database import Base, engine
from app.models.user import User
from app.models.session import Session
from app.models.message import Message

def init_db():
    """创建所有表"""
    print("创建数据库表...")
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库初始化完成")

if __name__ == "__main__":
    init_db()
```

### 设置共享环境 (`scripts/setup_shared_env.py`)

```python
"""设置共享 Python 环境"""
import subprocess
from pathlib import Path

def setup_shared_env():
    """创建并配置共享环境"""
    env_path = Path("./data/shared_env/base.venv")

    print("创建虚拟环境...")
    subprocess.run(["uv", "venv", str(env_path)], check=True)

    print("安装预设包...")
    packages = [
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "reportlab>=4.0.0",
        "python-pptx>=0.6.0",
        "openpyxl>=3.1.0",
        "matplotlib>=3.7.0",
    ]

    for pkg in packages:
        print(f"  安装 {pkg}...")
        subprocess.run(
            [str(env_path / "bin" / "pip"), "install", pkg],
            check=True
        )

    print("✅ 共享环境设置完成")

if __name__ == "__main__":
    setup_shared_env()
```

### 启动命令

```bash
# 开发模式
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

---

## 总结

### ✅ 核心特性

1. **多轮对话** - 支持连续对话和上下文记忆
2. **用户隔离** - 每个用户独立的工作空间和配额
3. **会话管理** - 手动创建/关闭，自动过期检测
4. **对话持久化** - SQLite 存储完整历史
5. **文件管理** - 自动保留重要文件到共享目录
6. **安全控制** - 命令白名单 + 包白名单
7. **配额管理** - 会话数、存储、时长限制

### 📊 技术指标

- **数据库**: SQLite (可升级 PostgreSQL)
- **并发**: 支持异步处理
- **性能**: Agent 实例缓存
- **安全**: 多层防护（命令/包/路径）
- **扩展性**: 模块化设计，易于扩展

### 🚀 下一步

1. 实现认证系统（JWT）
2. 添加 WebSocket 支持（实时对话）
3. 完善配额管理和监控
4. 添加文件预览功能
5. 实现对话导出（PDF/Markdown）
