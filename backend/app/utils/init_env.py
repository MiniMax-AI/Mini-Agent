"""共享环境初始化工具"""
import os
import sys
import subprocess
import venv
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def init_shared_env(
    base_dir: Path,
    packages_file: Path | None = None,
    force: bool = False
) -> bool:
    """
    初始化共享 Python 环境

    Args:
        base_dir: 基础目录（通常是 backend/data/shared_env）
        packages_file: 包列表文件路径
        force: 是否强制重新创建

    Returns:
        bool: 初始化是否成功
    """
    try:
        logger.info("🚀 开始初始化共享环境...")

        # 创建目录
        base_dir.mkdir(parents=True, exist_ok=True)

        # 虚拟环境路径
        venv_dir = base_dir / "base.venv"

        # 检查是否已存在
        if venv_dir.exists() and not force:
            logger.info(f"✅ 共享环境已存在: {venv_dir}")
            return True

        # 创建虚拟环境
        logger.info(f"🔨 创建虚拟环境: {venv_dir}")
        if venv_dir.exists():
            import shutil
            shutil.rmtree(venv_dir)

        venv.create(venv_dir, with_pip=True, clear=True)
        logger.info("✅ 虚拟环境创建成功")

        # 确定 pip 路径
        if sys.platform == "win32":
            pip_path = venv_dir / "Scripts" / "pip.exe"
            python_path = venv_dir / "Scripts" / "python.exe"
        else:
            pip_path = venv_dir / "bin" / "pip"
            python_path = venv_dir / "bin" / "python"

        if not pip_path.exists():
            logger.error(f"❌ 找不到 pip: {pip_path}")
            return False

        # 升级 pip（静默）
        logger.info("📦 升级 pip...")
        try:
            subprocess.run(
                [str(python_path), "-m", "pip", "install", "--upgrade", "pip", "--quiet"],
                check=True,
                capture_output=True,
                timeout=120
            )
        except Exception as e:
            logger.warning(f"⚠️  pip 升级失败: {e}")

        # 安装包
        if packages_file and packages_file.exists():
            logger.info(f"📚 安装包列表: {packages_file}")
            with open(packages_file, "r", encoding="utf-8") as f:
                packages = [
                    line.strip()
                    for line in f
                    if line.strip() and not line.strip().startswith("#")
                ]

            if packages:
                logger.info(f"   共 {len(packages)} 个包")
                # 批量安装（更快）
                try:
                    subprocess.run(
                        [str(pip_path), "install", "--quiet"] + packages,
                        check=True,
                        capture_output=True,
                        timeout=600  # 10分钟
                    )
                    logger.info(f"✅ 成功安装 {len(packages)} 个包")
                except subprocess.TimeoutExpired:
                    logger.error("❌ 包安装超时")
                    return False
                except subprocess.CalledProcessError as e:
                    logger.error(f"❌ 包安装失败: {e.stderr.decode() if e.stderr else str(e)}")
                    return False
        else:
            logger.warning("⚠️  未找到包列表文件，跳过包安装")

        logger.info("✅ 共享环境初始化完成")
        return True

    except Exception as e:
        logger.error(f"❌ 共享环境初始化失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def check_shared_env(venv_dir: Path) -> bool:
    """
    检查共享环境是否存在且可用

    Args:
        venv_dir: 虚拟环境目录

    Returns:
        bool: 环境是否可用
    """
    if not venv_dir.exists():
        return False

    # 检查 Python 可执行文件
    if sys.platform == "win32":
        python_path = venv_dir / "Scripts" / "python.exe"
    else:
        python_path = venv_dir / "bin" / "python"

    return python_path.exists()
