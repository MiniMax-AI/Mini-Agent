"""认证相关 Schema"""
from pydantic import BaseModel


class LoginRequest(BaseModel):
    """登录请求"""

    username: str
    password: str


class LoginResponse(BaseModel):
    """登录响应"""

    user_id: str
    username: str
    message: str = "登录成功"
