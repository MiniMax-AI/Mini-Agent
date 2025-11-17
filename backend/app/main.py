"""FastAPI 主应用"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.api import auth, sessions, chat
from app.models.database import init_db
from app.utils.init_env import init_shared_env, check_shared_env
from pathlib import Path

settings = get_settings()

# 创建 FastAPI 应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url=f"{settings.api_prefix}/docs",
    redoc_url=f"{settings.api_prefix}/redoc",
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    # 初始化数据库
    init_db()
    print(f"✅ 数据库初始化完成")

    # 初始化共享环境
    shared_env_dir = Path(settings.workspace_base).parent / "shared_env"
    venv_dir = shared_env_dir / "base.venv"

    if not check_shared_env(venv_dir):
        print("🔨 首次启动，正在初始化共享环境...")
        print("   这可能需要几分钟时间（只会执行一次）")

        packages_file = shared_env_dir / "allowed_packages.txt"
        success = init_shared_env(
            base_dir=shared_env_dir,
            packages_file=packages_file if packages_file.exists() else None,
            force=False
        )

        if success:
            print("✅ 共享环境初始化完成")
        else:
            print("⚠️  共享环境初始化失败，部分功能可能不可用")
    else:
        print("✅ 共享环境已就绪")

    print(f"✅ {settings.app_name} v{settings.app_version} 启动成功")


# 路由
app.include_router(auth.router, prefix=f"{settings.api_prefix}/auth", tags=["认证"])
app.include_router(
    sessions.router, prefix=f"{settings.api_prefix}/sessions", tags=["会话管理"]
)
app.include_router(chat.router, prefix=f"{settings.api_prefix}/chat", tags=["对话"])


# 根路径
@app.get("/")
async def root():
    return {
        "message": "Mini-Agent API",
        "version": settings.app_version,
        "docs": f"{settings.api_prefix}/docs",
    }


# 健康检查
@app.get("/health")
async def health():
    return {"status": "healthy", "version": settings.app_version}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=settings.debug)
