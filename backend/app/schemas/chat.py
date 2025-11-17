"""对话相关 Schema"""
from pydantic import BaseModel, Field
from typing import Optional, List


class ChatRequest(BaseModel):
    """对话请求"""

    message: str = Field(..., min_length=1, max_length=10000, description="用户消息")


class SendMessageRequest(BaseModel):
    """发送消息请求（前端期望的格式）"""

    message: str = Field(..., min_length=1, max_length=10000, description="用户消息")


class SendMessageResponse(BaseModel):
    """发送消息响应（前端期望的格式）"""

    message: str  # 用户发送的消息
    response: str  # AI 的响应


class ChatResponse(BaseModel):
    """对话响应"""

    session_id: str
    message: str
    thinking: Optional[str] = None
    files: List[str] = []
    turn: int
    message_count: int


class MessageHistory(BaseModel):
    """消息历史"""

    role: str
    content: Optional[str]
    thinking: Optional[str] = None
    created_at: str


class HistoryResponse(BaseModel):
    """历史记录响应"""

    session_id: str
    messages: List[MessageHistory]
    total: int
