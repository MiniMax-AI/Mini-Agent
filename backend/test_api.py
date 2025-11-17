"""FastAPI 后端测试脚本"""
import requests
import json

BASE_URL = "http://localhost:8000/api"


def test_login():
    """测试登录"""
    print("\n=== 测试登录 ===")
    response = requests.post(
        f"{BASE_URL}/auth/login", json={"username": "demo", "password": "demo123"}
    )
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    return response.json()["user_id"]


def test_create_session(user_id):
    """测试创建会话"""
    print("\n=== 测试创建会话 ===")
    response = requests.post(
        f"{BASE_URL}/sessions?user_id={user_id}",
        json={"title": "测试会话"},
    )
    print(f"状态码: {response.status_code}")
    data = response.json()
    print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
    return data["id"]


def test_chat(user_id, session_id):
    """测试对话"""
    print("\n=== 测试对话 ===")
    response = requests.post(
        f"{BASE_URL}/chat/{session_id}?user_id={user_id}",
        json={"message": "你好，介绍一下你自己"},
    )
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")


def test_get_history(user_id, session_id):
    """测试获取历史"""
    print("\n=== 测试获取历史 ===")
    response = requests.get(f"{BASE_URL}/chat/{session_id}/history?user_id={user_id}")
    print(f"状态码: {response.status_code}")
    data = response.json()
    print(f"消息数量: {data['total']}")
    for msg in data["messages"]:
        print(f"  - {msg['role']}: {msg['content'][:50]}...")


def test_list_sessions(user_id):
    """测试会话列表"""
    print("\n=== 测试会话列表 ===")
    response = requests.get(f"{BASE_URL}/sessions?user_id={user_id}")
    print(f"状态码: {response.status_code}")
    data = response.json()
    print(f"总会话数: {data['total']}")
    for session in data["sessions"]:
        print(f"  - {session['title']} ({session['id'][:8]}...)")


def test_close_session(user_id, session_id):
    """测试关闭会话"""
    print("\n=== 测试关闭会话 ===")
    response = requests.delete(
        f"{BASE_URL}/sessions/{session_id}?user_id={user_id}&preserve_files=true"
    )
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")


if __name__ == "__main__":
    print("开始测试 Mini-Agent FastAPI 后端...")

    try:
        # 1. 登录
        user_id = test_login()

        # 2. 创建会话
        session_id = test_create_session(user_id)

        # 3. 发送消息
        test_chat(user_id, session_id)

        # 4. 获取历史
        test_get_history(user_id, session_id)

        # 5. 列出会话
        test_list_sessions(user_id)

        # 6. 关闭会话
        test_close_session(user_id, session_id)

        print("\n✅ 所有测试完成！")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
