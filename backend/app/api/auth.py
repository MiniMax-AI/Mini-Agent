"""简单认证 API"""
from fastapi import APIRouter, HTTPException
from app.schemas.auth import LoginRequest, LoginResponse
from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    简单登录接口

    返回用户信息（username 作为 user_id）
    """
    # 获取配置的用户列表
    auth_users = settings.get_auth_users()

    # 验证用户名和密码
    if request.username not in auth_users:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    if auth_users[request.username] != request.password:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 登录成功，返回用户信息
    return LoginResponse(
        user_id=request.username,  # 简化：直接使用 username 作为 user_id
        username=request.username,
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
