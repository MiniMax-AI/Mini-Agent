"""会话管理 API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as DBSession
from app.models.database import get_db
from app.models.session import Session
from app.schemas.session import SessionCreate, SessionResponse, SessionListResponse
from app.services.workspace_service import WorkspaceService
from datetime import datetime
import uuid

router = APIRouter()


@router.post("", response_model=SessionResponse)
async def create_session(
    request: SessionCreate,
    user_id: str = Query(..., description="用户ID"),
    db: DBSession = Depends(get_db),
):
    """创建新会话"""
    # 创建会话
    session_id = str(uuid.uuid4())
    session = Session(
        id=session_id, user_id=user_id, title=request.title or "新会话"
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # 创建工作空间
    workspace_service = WorkspaceService()
    workspace_service.create_session_workspace(user_id, session_id)

    return session


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    user_id: str = Query(..., description="用户ID"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: DBSession = Depends(get_db),
):
    """获取用户的会话列表"""
    sessions = (
        db.query(Session)
        .filter(Session.user_id == user_id)
        .order_by(Session.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    total = db.query(Session).filter(Session.user_id == user_id).count()

    return SessionListResponse(sessions=sessions, total=total)


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    user_id: str = Query(..., description="用户ID"),
    db: DBSession = Depends(get_db),
):
    """获取会话详情"""
    session = (
        db.query(Session)
        .filter(Session.id == session_id, Session.user_id == user_id)
        .first()
    )

    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    return session


@router.delete("/{session_id}")
async def close_session(
    session_id: str,
    user_id: str = Query(..., description="用户ID"),
    preserve_files: bool = Query(True, description="是否保留文件"),
    db: DBSession = Depends(get_db),
):
    """关闭会话"""
    session = (
        db.query(Session)
        .filter(Session.id == session_id, Session.user_id == user_id)
        .first()
    )

    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    # 清理工作空间
    workspace_service = WorkspaceService()
    preserved = workspace_service.cleanup_session(
        user_id, session_id, preserve_files=preserve_files
    )

    # 更新数据库
    session.status = "closed"
    session.closed_at = datetime.utcnow()
    db.commit()

    return {"status": "closed", "preserved_files": preserved}
