"""工作空间管理服务"""
from pathlib import Path
import shutil
from typing import List
from datetime import datetime
from app.config import get_settings

settings = get_settings()


class WorkspaceService:
    """工作空间管理服务"""

    def __init__(self):
        self.base_path = settings.workspace_base
        self.base_path.mkdir(parents=True, exist_ok=True)

    def create_session_workspace(self, user_id: str, session_id: str) -> Path:
        """创建会话工作空间"""
        session_dir = self._get_session_dir(user_id, session_id)

        # 创建目录结构
        session_dir.mkdir(parents=True, exist_ok=True)
        (session_dir / "files").mkdir(exist_ok=True)
        (session_dir / "logs").mkdir(exist_ok=True)

        # 创建符号链接到 shared_files
        shared_dir = self._get_user_shared_dir(user_id)
        shared_dir.mkdir(parents=True, exist_ok=True)

        shared_link = session_dir / "shared"
        if not shared_link.exists():
            try:
                shared_link.symlink_to(shared_dir, target_is_directory=True)
            except Exception:
                # Windows 可能不支持符号链接，跳过
                pass

        return session_dir

    def cleanup_session(
        self, user_id: str, session_id: str, preserve_files: bool = True
    ) -> List[str]:
        """清理会话工作空间"""
        session_dir = self._get_session_dir(user_id, session_id)
        preserved_files = []

        if preserve_files:
            # 保留特定格式的文件
            files_dir = session_dir / "files"
            if files_dir.exists():
                for file in files_dir.iterdir():
                    if (
                        file.is_file()
                        and file.suffix.lower() in settings.preserve_file_extensions
                    ):
                        # 移动到 shared_files/outputs
                        dest_dir = self._get_user_shared_dir(user_id) / "outputs"
                        dest_dir.mkdir(parents=True, exist_ok=True)

                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        dest_file = dest_dir / f"{timestamp}_{file.name}"
                        shutil.copy2(file, dest_file)
                        preserved_files.append(str(dest_file.relative_to(self.base_path)))

        # 删除会话目录
        if session_dir.exists():
            shutil.rmtree(session_dir, ignore_errors=True)

        return preserved_files

    def get_session_files(self, user_id: str, session_id: str) -> List[Path]:
        """获取会话的所有文件"""
        files_dir = self._get_session_dir(user_id, session_id) / "files"
        if not files_dir.exists():
            return []
        return [f for f in files_dir.iterdir() if f.is_file()]

    def _get_session_dir(self, user_id: str, session_id: str) -> Path:
        """获取会话目录路径"""
        return self.base_path / f"user_{user_id}" / "sessions" / session_id

    def _get_user_shared_dir(self, user_id: str) -> Path:
        """获取用户共享目录路径"""
        return self.base_path / f"user_{user_id}" / "shared_files"
