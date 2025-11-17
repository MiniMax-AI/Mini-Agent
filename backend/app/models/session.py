"""会话数据模型"""
from sqlalchemy import Column, String, Integer, DateTime
from datetime import datetime
from .database import Base


class Session(Base):
    """会话表"""

    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(100), nullable=False, index=True)  # 简化为username
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    last_active = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="active", index=True)  # active, closed, expired
    title = Column(String(255), nullable=True)

    # 统计字段
    message_count = Column(Integer, default=0)
    turn_count = Column(Integer, default=0)
