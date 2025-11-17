"""简单认证 API"""
from fastapi import APIRouter, HTTPException, Form
from app.schemas.auth import LoginResponse
from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.post("/login", response_model=LoginResponse)
async def login(username: str = Form(...), password: str = Form(...)):
    """
    简单登录接口

    返回用户信息（username 作为 user_id）
    """
    # 获取配置的用户列表
    auth_users = settings.get_auth_users()

    # 验证用户名和密码
    if username not in auth_users:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    if auth_users[username] != password:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 登录成功，返回用户信息
    # 使用 username 作为 session_id（简化方案）
    return LoginResponse(
        session_id=username,
        message="登录成功",
    )


@router.get("/me")
async def get_current_user(user_id: str):
    """
    获取当前用户信息（简化版）

    前端需要在查询参数中传递 user_id
    """
    auth_users = settings.get_auth_users()

    if user_id not in auth_users:
        raise HTTPException(status_code=404, detail="用户不存在")

    return {"user_id": user_id, "username": user_id}
