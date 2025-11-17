"""对话 API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as DBSession
from app.models.database import get_db
from app.models.session import Session
from app.schemas.chat import SendMessageRequest, SendMessageResponse
from app.services.agent_service import AgentService
from app.services.history_service import HistoryService
from app.services.workspace_service import WorkspaceService
from datetime import datetime

router = APIRouter()

# 内存中的 Agent 实例缓存
_agent_cache: dict[str, AgentService] = {}


@router.post("/{chat_session_id}/message", response_model=SendMessageResponse)
async def send_message(
    chat_session_id: str,
    request: SendMessageRequest,
    session_id: str = Query(..., description="Session ID (user_id)"),
    db: DBSession = Depends(get_db),
):
    """发送消息并获取响应"""
    # 验证会话
    session = (
        db.query(Session)
        .filter(Session.id == chat_session_id, Session.user_id == session_id)
        .first()
    )

    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    if session.status == "completed":
        raise HTTPException(status_code=410, detail="会话已完成")

    # 获取或创建 Agent Service
    if chat_session_id not in _agent_cache:
        workspace_service = WorkspaceService()
        workspace_dir = workspace_service._get_session_dir(session_id, chat_session_id)

        history_service = HistoryService(db)
        agent_service = AgentService(workspace_dir, history_service, chat_session_id)

        # 初始化 Agent
        agent_service.initialize_agent()

        _agent_cache[chat_session_id] = agent_service
    else:
        agent_service = _agent_cache[chat_session_id]

    # 执行对话
    try:
        result = await agent_service.chat(request.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent 执行失败: {str(e)}")

    # 更新会话活跃时间
    session.updated_at = datetime.utcnow()
    db.commit()

    return SendMessageResponse(
        message=request.message,
        response=result["response"],
    )
