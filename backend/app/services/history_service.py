"""对话历史服务"""
from sqlalchemy.orm import Session as DBSession
from app.models.message import Message
from app.models.session import Session
from typing import List, Dict, Optional
import json
import uuid


class HistoryService:
    """对话历史服务"""

    def __init__(self, db: DBSession):
        self.db = db

    def save_message(
        self,
        session_id: str,
        role: str,
        content: Optional[str] = None,
        thinking: Optional[str] = None,
        tool_calls: Optional[List[Dict]] = None,
        tool_call_id: Optional[str] = None,
    ) -> Message:
        """保存消息到数据库"""
        message = Message(
            id=str(uuid.uuid4()),  # 生成 UUID
            session_id=session_id,
            role=role,
            content=content,
            thinking=thinking,
            tool_calls=json.dumps(tool_calls, ensure_ascii=False)
            if tool_calls
            else None,
            tool_call_id=tool_call_id,
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)

        return message

    def load_session_history(self, session_id: str) -> List[Dict]:
        """加载会话历史"""
        messages = (
            self.db.query(Message)
            .filter(Message.session_id == session_id)
            .order_by(Message.created_at)
            .all()
        )

        return [
            {
                "role": msg.role,
                "content": msg.content,
                "thinking": msg.thinking,
                "tool_calls": json.loads(msg.tool_calls) if msg.tool_calls else None,
                "tool_call_id": msg.tool_call_id,
                "created_at": msg.created_at.isoformat(),
            }
            for msg in messages
        ]

    def get_message_count(self, session_id: str) -> int:
        """获取消息数量"""
        return self.db.query(Message).filter(Message.session_id == session_id).count()
