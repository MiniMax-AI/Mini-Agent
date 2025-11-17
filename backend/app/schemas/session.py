"""会话相关 Schema"""
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


class SessionListResponse(BaseModel):
    """会话列表响应"""

    sessions: list[SessionResponse]
    total: int
