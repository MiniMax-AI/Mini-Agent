"""应用配置"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path
from typing import List


class Settings(BaseSettings):
    """应用配置"""

    # 应用配置
    app_name: str = "Mini-Agent Backend"
    app_version: str = "0.1.0"
    debug: bool = False

    # API 配置
    api_prefix: str = "/api"
    cors_origins: List[str] = ["http://localhost:3000"]

    # 简单认证（临时方案，格式：username:password,username2:password2）
    simple_auth_users: str = "demo:demo123"

    # 数据库配置
    database_url: str = "sqlite:///./data/database/mini_agent.db"

    # LLM API 配置（支持 MiniMax、GLM、OpenAI 等）
    llm_api_key: str  # API 密钥
    llm_api_base: str = "https://api.minimax.chat"  # API 基础地址
    llm_model: str = "MiniMax-Text-01"  # 模型名称
    llm_provider: str = "anthropic"  # 提供商：anthropic 或 openai

    # 工作空间配置
    workspace_base: Path = Path("./data/workspaces")
    shared_env_path: Path = Path("./data/shared_env/base.venv")
    allowed_packages_file: Path = Path("./data/shared_env/allowed_packages.txt")

    # Agent 配置
    agent_max_steps: int = 100
    agent_token_limit: int = 80000

    # 会话配置
    session_inactive_timeout_hours: int = 1
    session_max_duration_hours: int = 24
    session_max_turns: int = 50

    # 文件保留配置
    preserve_file_extensions: List[str] = [
        ".pdf",
        ".xlsx",
        ".pptx",
        ".docx",
        ".png",
        ".jpg",
        ".jpeg",
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def get_auth_users(self) -> dict[str, str]:
        """解析简单认证用户列表"""
        users = {}
        for user_pair in self.simple_auth_users.split(","):
            if ":" in user_pair:
                username, password = user_pair.split(":", 1)
                users[username.strip()] = password.strip()
        return users


@lru_cache()
def get_settings() -> Settings:
    """获取配置（单例）"""
    return Settings()
