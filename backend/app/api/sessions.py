"""会话管理 API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as DBSession
from app.models.database import get_db
from app.models.session import Session
from app.models.message import Message
from app.schemas.session import CreateSessionResponse, SessionResponse, SessionListResponse
from app.schemas.message import MessageHistoryResponse
from app.services.workspace_service import WorkspaceService
from datetime import datetime
import uuid

router = APIRouter()


@router.post("/create", response_model=CreateSessionResponse)
async def create_session(
    session_id: str = Query(..., description="Session ID (user_id)"),
    db: DBSession = Depends(get_db),
):
    """创建新会话"""
    # 创建会话
    chat_session_id = str(uuid.uuid4())
    session = Session(
        id=chat_session_id, user_id=session_id, title="新会话"
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # 创建工作空间
    workspace_service = WorkspaceService()
    workspace_service.create_session_workspace(session_id, chat_session_id)

    return CreateSessionResponse(
        session_id=chat_session_id,
        message="会话创建成功"
    )


@router.get("/list", response_model=SessionListResponse)
async def list_sessions(
    session_id: str = Query(..., description="Session ID (user_id)"),
    db: DBSession = Depends(get_db),
):
    """获取用户的会话列表"""
    sessions = (
        db.query(Session)
        .filter(Session.user_id == session_id)
        .order_by(Session.updated_at.desc())
        .all()
    )

    return SessionListResponse(sessions=sessions)


@router.get("/{chat_session_id}/history", response_model=MessageHistoryResponse)
async def get_session_history(
    chat_session_id: str,
    session_id: str = Query(..., description="Session ID (user_id)"),
    db: DBSession = Depends(get_db),
):
    """获取会话的消息历史"""
    # 验证会话属于该用户
    session = (
        db.query(Session)
        .filter(Session.id == chat_session_id, Session.user_id == session_id)
        .first()
    )

    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    # 获取消息历史
    messages = (
        db.query(Message)
        .filter(Message.session_id == chat_session_id)
        .order_by(Message.created_at.asc())
        .all()
    )

    return MessageHistoryResponse(messages=messages)


@router.delete("/{chat_session_id}")
async def delete_session(
    chat_session_id: str,
    session_id: str = Query(..., description="Session ID (user_id)"),
    db: DBSession = Depends(get_db),
):
    """删除会话"""
    # 验证会话属于该用户
    session = (
        db.query(Session)
        .filter(Session.id == chat_session_id, Session.user_id == session_id)
        .first()
    )

    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    # 删除消息
    db.query(Message).filter(Message.session_id == chat_session_id).delete()

    # 删除会话
    db.delete(session)
    db.commit()

    # 清理工作空间
    workspace_service = WorkspaceService()
    workspace_service.cleanup_session(session_id, chat_session_id, preserve_files=False)

    return {"message": "会话已删除"}
