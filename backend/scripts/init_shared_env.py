#!/usr/bin/env python3
"""初始化共享环境脚本（跨平台）"""
import os
import sys
import subprocess
import venv
from pathlib import Path


def main():
    print("🚀 开始初始化 Mini-Agent 共享环境...")

    # 确定后端目录
    backend_dir = Path(__file__).parent.parent
    os.chdir(backend_dir)

    # 创建目录
    print("📁 创建目录结构...")
    data_dir = Path("data")
    (data_dir / "shared_env").mkdir(parents=True, exist_ok=True)
    (data_dir / "workspaces").mkdir(parents=True, exist_ok=True)
    (data_dir / "database").mkdir(parents=True, exist_ok=True)

    # 创建虚拟环境
    venv_dir = data_dir / "shared_env" / "base.venv"
    if venv_dir.exists():
        print(f"⚠️  虚拟环境已存在: {venv_dir}")
        print("   跳过创建...")
    else:
        print(f"🔨 创建虚拟环境: {venv_dir}")
        try:
            venv.create(venv_dir, with_pip=True)
            print("✅ 虚拟环境创建成功")
        except Exception as e:
            print(f"❌ 创建虚拟环境失败: {e}")
            return 1

    # 确定 pip 路径
    if sys.platform == "win32":
        pip_path = venv_dir / "Scripts" / "pip.exe"
        python_path = venv_dir / "Scripts" / "python.exe"
    else:
        pip_path = venv_dir / "bin" / "pip"
        python_path = venv_dir / "bin" / "python"

    if not pip_path.exists():
        print(f"❌ 找不到 pip: {pip_path}")
        return 1

    # 升级 pip
    print("📦 升级 pip...")
    try:
        subprocess.run([str(python_path), "-m", "pip", "install", "--upgrade", "pip"],
                      check=True, capture_output=True)
        print("✅ pip 升级成功")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  pip 升级失败: {e}")

    # 读取并安装允许的包
    packages_file = data_dir / "shared_env" / "allowed_packages.txt"
    if not packages_file.exists():
        print(f"⚠️  找不到 {packages_file}")
        print("   跳过包安装")
    else:
        print(f"📚 从 {packages_file} 安装包...")
        with open(packages_file, "r", encoding="utf-8") as f:
            packages = [
                line.strip()
                for line in f
                if line.strip() and not line.strip().startswith("#")
            ]

        if not packages:
            print("⚠️  包列表为空")
        else:
            print(f"   共 {len(packages)} 个包需要安装")
            failed = []
            for i, package in enumerate(packages, 1):
                print(f"   [{i}/{len(packages)}] 安装: {package}")
                try:
                    subprocess.run(
                        [str(pip_path), "install", package],
                        check=True,
                        capture_output=True,
                        timeout=300  # 5分钟超时
                    )
                    print(f"      ✅ {package} 安装成功")
                except subprocess.TimeoutExpired:
                    print(f"      ⚠️  {package} 安装超时，跳过")
                    failed.append(package)
                except subprocess.CalledProcessError as e:
                    print(f"      ⚠️  {package} 安装失败")
                    failed.append(package)

            if failed:
                print(f"\n⚠️  以下包安装失败:")
                for pkg in failed:
                    print(f"   - {pkg}")

    print("\n" + "="*60)
    print("✅ 共享环境初始化完成！")
    print(f"📍 虚拟环境路径: {venv_dir.absolute()}")
    print(f"🐍 Python: {python_path}")
    print(f"📦 Pip: {pip_path}")
    print("="*60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
