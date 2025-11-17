"""消息相关 Schema"""
from pydantic import BaseModel
from datetime import datetime
from typing import List


class MessageResponse(BaseModel):
    """消息响应"""

    id: str
    session_id: str
    role: str  # "user" | "assistant" | "system"
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class MessageHistoryResponse(BaseModel):
    """消息历史响应"""

    messages: List[MessageResponse]
