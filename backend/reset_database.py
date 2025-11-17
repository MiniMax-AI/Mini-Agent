#!/usr/bin/env python3
"""数据库重置脚本

⚠️  警告：此脚本会删除所有会话数据和消息历史！

用于清理不兼容的旧数据库，重新初始化数据库表结构。
"""
import sys
from pathlib import Path
import shutil

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

def reset_database(clean_workspaces: bool = False):
    """重置数据库

    Args:
        clean_workspaces: 是否同时清理工作空间目录
    """
    print("🔄 Mini-Agent 数据库重置工具\n")
    print("=" * 60)

    # 1. 确认操作
    print("\n⚠️  警告：此操作将：")
    print("   - 删除所有会话记录")
    print("   - 删除所有消息历史")
    print("   - 重新创建数据库表结构")
    if clean_workspaces:
        print("   - 清理所有工作空间文件")
    print("\n此操作不可恢复！")

    response = input("\n确定要继续吗？(输入 'yes' 确认): ")
    if response.lower() != "yes":
        print("❌ 操作已取消")
        return False

    # 2. 删除数据库文件
    print("\n1️⃣  删除数据库文件...")
    db_file = Path("./data/database/mini_agent.db")
    if db_file.exists():
        try:
            db_file.unlink()
            print(f"   ✅ 已删除: {db_file}")
        except Exception as e:
            print(f"   ❌ 删除失败: {e}")
            return False
    else:
        print(f"   ℹ️  数据库文件不存在: {db_file}")

    # 3. 清理工作空间（可选）
    if clean_workspaces:
        print("\n2️⃣  清理工作空间...")
        workspace_dir = Path("./data/workspaces")
        if workspace_dir.exists():
            try:
                shutil.rmtree(workspace_dir)
                workspace_dir.mkdir(parents=True, exist_ok=True)
                print(f"   ✅ 已清理: {workspace_dir}")
            except Exception as e:
                print(f"   ❌ 清理失败: {e}")
                return False
        else:
            print(f"   ℹ️  工作空间目录不存在: {workspace_dir}")

    # 4. 重新初始化数据库
    print("\n3️⃣  重新初始化数据库...")
    try:
        from app.models.database import init_db
        from app.models.session import Session  # 导入模型以注册表
        from app.models.message import Message

        init_db()
        print("   ✅ 数据库表创建成功")
    except Exception as e:
        print(f"   ❌ 数据库初始化失败: {e}")
        import traceback
        print(f"\n详细错误:\n{traceback.format_exc()}")
        return False

    # 5. 完成
    print("\n" + "=" * 60)
    print("✅ 数据库重置完成！")
    print("\n可以重新启动后端服务:")
    print("   uvicorn app.main:app --reload")
    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="重置 Mini-Agent 数据库")
    parser.add_argument(
        "--clean-workspaces",
        action="store_true",
        help="同时清理所有工作空间文件"
    )

    args = parser.parse_args()

    success = reset_database(clean_workspaces=args.clean_workspaces)
    sys.exit(0 if success else 1)
