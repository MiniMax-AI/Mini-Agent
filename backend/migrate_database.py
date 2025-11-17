#!/usr/bin/env python3
"""数据库迁移脚本

将旧的整数 ID 迁移到 UUID 字符串格式。
尝试保留现有数据。
"""
import sys
from pathlib import Path
import sqlite3
import uuid

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

def migrate_database():
    """迁移数据库"""
    print("🔄 Mini-Agent 数据库迁移工具\n")
    print("=" * 60)

    db_file = Path("./data/database/mini_agent.db")
    if not db_file.exists():
        print("❌ 数据库文件不存在")
        print("   如果是首次运行，请直接启动后端服务，系统会自动初始化数据库。")
        return False

    print("\n1️⃣  检查数据库...")

    try:
        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()

        # 检查 messages 表结构
        cursor.execute("PRAGMA table_info(messages)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        print(f"   ✅ 找到 messages 表，包含字段: {', '.join(column_names)}")

        # 检查是否有整数 ID
        cursor.execute("SELECT id, typeof(id) FROM messages LIMIT 5")
        sample_rows = cursor.fetchall()

        if not sample_rows:
            print("   ℹ️  messages 表为空，无需迁移")
            conn.close()
            return True

        has_integer_ids = any(row[1] == 'integer' for row in sample_rows)

        if not has_integer_ids:
            print("   ℹ️  所有 ID 已经是字符串格式，无需迁移")
            conn.close()
            return True

        print(f"   ⚠️  检测到整数 ID，需要迁移")

        # 确认操作
        print("\n⚠️  警告：此操作会修改数据库结构")
        print("   建议先备份数据库文件！")
        response = input("\n确定要继续吗？(输入 'yes' 确认): ")
        if response.lower() != "yes":
            print("❌ 操作已取消")
            conn.close()
            return False

        # 2. 创建新表
        print("\n2️⃣  创建新表结构...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages_new (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT,
                thinking TEXT,
                tool_calls TEXT,
                tool_call_id TEXT,
                created_at TIMESTAMP NOT NULL
            )
        """)
        print("   ✅ 新表创建成功")

        # 3. 迁移数据
        print("\n3️⃣  迁移数据...")
        cursor.execute("SELECT * FROM messages")
        old_rows = cursor.fetchall()

        id_mapping = {}  # 旧 ID -> 新 UUID 的映射
        migrated_count = 0

        for row in old_rows:
            old_id = row[0]

            # 如果是整数，生成新的 UUID
            if isinstance(old_id, int):
                new_id = str(uuid.uuid4())
                id_mapping[old_id] = new_id
            else:
                new_id = str(old_id)

            # 插入到新表
            cursor.execute("""
                INSERT INTO messages_new (id, session_id, role, content, thinking, tool_calls, tool_call_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (new_id, row[1], row[2], row[3], row[4], row[5], row[6], row[7]))

            migrated_count += 1

        print(f"   ✅ 成功迁移 {migrated_count} 条消息记录")

        # 4. 替换旧表
        print("\n4️⃣  替换旧表...")
        cursor.execute("DROP TABLE messages")
        cursor.execute("ALTER TABLE messages_new RENAME TO messages")
        print("   ✅ 表替换完成")

        # 5. 创建索引
        print("\n5️⃣  创建索引...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at)")
        print("   ✅ 索引创建完成")

        # 提交更改
        conn.commit()
        conn.close()

        # 6. 完成
        print("\n" + "=" * 60)
        print("✅ 数据库迁移完成！")
        print(f"\n迁移统计:")
        print(f"   - 总消息数: {migrated_count}")
        print(f"   - ID 映射数: {len(id_mapping)}")
        print("\n可以重新启动后端服务:")
        print("   uvicorn app.main:app --reload")
        return True

    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        import traceback
        print(f"\n详细错误:\n{traceback.format_exc()}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False


if __name__ == "__main__":
    success = migrate_database()
    sys.exit(0 if success else 1)
