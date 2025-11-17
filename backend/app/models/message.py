"""消息数据模型"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from datetime import datetime
from .database import Base


class Message(Base):
    """消息表"""

    __tablename__ = "messages"

    id = Column(String(36), primary_key=True)  # 改为 String UUID
    session_id = Column(
        String(36),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role = Column(String(20), nullable=False)  # system, user, assistant, tool
    content = Column(Text, nullable=True)
    thinking = Column(Text, nullable=True)
    tool_calls = Column(Text, nullable=True)  # JSON string
    tool_call_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
