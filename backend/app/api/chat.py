"""对话 API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as DBSession
from app.models.database import get_db
from app.models.session import Session
from app.schemas.chat import ChatRequest, ChatResponse, HistoryResponse, MessageHistory
from app.services.agent_service import AgentService
from app.services.history_service import HistoryService
from app.services.workspace_service import WorkspaceService
from datetime import datetime

router = APIRouter()

# 内存中的 Agent 实例缓存
_agent_cache: dict[str, AgentService] = {}


@router.post("/{session_id}", response_model=ChatResponse)
async def chat(
    session_id: str,
    request: ChatRequest,
    user_id: str = Query(..., description="用户ID"),
    db: DBSession = Depends(get_db),
):
    """发送消息并获取响应"""
    # 验证会话
    session = (
        db.query(Session)
        .filter(Session.id == session_id, Session.user_id == user_id)
        .first()
    )

    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    if session.status != "active":
        raise HTTPException(status_code=410, detail="会话已关闭")

    # 获取或创建 Agent Service
    if session_id not in _agent_cache:
        workspace_service = WorkspaceService()
        workspace_dir = workspace_service._get_session_dir(user_id, session_id)

        history_service = HistoryService(db)
        agent_service = AgentService(workspace_dir, history_service, session_id)

        # 初始化 Agent
        agent_service.initialize_agent()

        _agent_cache[session_id] = agent_service
    else:
        agent_service = _agent_cache[session_id]

    # 执行对话
    try:
        result = await agent_service.chat(request.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent 执行失败: {str(e)}")

    # 更新会话活跃时间
    session.last_active = datetime.utcnow()
    db.commit()

    # 获取生成的文件
    workspace_service = WorkspaceService()
    files = workspace_service.get_session_files(user_id, session_id)

    return ChatResponse(
        session_id=session_id,
        message=result["response"],
        files=[f.name for f in files],
        turn=session.turn_count,
        message_count=result["message_count"],
    )


@router.get("/{session_id}/history", response_model=HistoryResponse)
async def get_history(
    session_id: str,
    user_id: str = Query(..., description="用户ID"),
    db: DBSession = Depends(get_db),
):
    """获取会话的对话历史"""
    # 验证会话
    session = (
        db.query(Session)
        .filter(Session.id == session_id, Session.user_id == user_id)
        .first()
    )

    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    # 加载历史
    history_service = HistoryService(db)
    history = history_service.load_session_history(session_id)

    # 转换为响应格式
    messages = [
        MessageHistory(
            role=msg["role"],
            content=msg["content"],
            thinking=msg.get("thinking"),
            created_at=msg["created_at"],
        )
        for msg in history
        if msg["role"] in ["user", "assistant"]  # 只返回用户和助手消息
    ]

    return HistoryResponse(session_id=session_id, messages=messages, total=len(messages))
