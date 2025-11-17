"""会话相关 Schema"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class SessionCreate(BaseModel):
    """创建会话请求"""

    title: Optional[str] = None


class CreateSessionResponse(BaseModel):
    """创建会话响应"""

    session_id: str
    message: str = "会话创建成功"


class SessionResponse(BaseModel):
    """会话响应"""

    id: str
    user_id: str
    status: str
    created_at: datetime
    updated_at: datetime  # 前端期望 updated_at 而不是 last_active
    title: Optional[str] = None

    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    """会话列表响应"""

    sessions: list[SessionResponse]
