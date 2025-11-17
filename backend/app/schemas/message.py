"""消息相关 Schema"""
from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import List, Union


class MessageResponse(BaseModel):
    """消息响应"""

    id: str
    session_id: str
    role: str  # "user" | "assistant" | "system"
    content: str
    created_at: datetime

    @field_validator('id', 'session_id', mode='before')
    @classmethod
    def convert_to_string(cls, v: Union[str, int]) -> str:
        """将 id 转换为字符串（兼容旧的整数 ID）"""
        return str(v)

    class Config:
        from_attributes = True


class MessageHistoryResponse(BaseModel):
    """消息历史响应"""

    messages: List[MessageResponse]
