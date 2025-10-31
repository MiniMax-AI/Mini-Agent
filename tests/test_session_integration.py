"""
会话集成测试 - 测试多轮对话和会话管理功能
"""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mini_agent.agent import Agent
from mini_agent.llm import LLMClient, LLMResponse, Message
from mini_agent.tools.bash_tool import BashTool
from mini_agent.tools.file_tools import ReadTool, WriteTool
from mini_agent.tools.note_tool import RecallNoteTool, SessionNoteTool


@pytest.fixture
def mock_llm_client():
    """创建 mock LLM 客户端"""
    client = MagicMock(spec=LLMClient)
    return client


@pytest.fixture
def temp_workspace():
    """创建临时工作目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


def test_multi_turn_conversation(mock_llm_client, temp_workspace):
    """测试多轮对话，验证上下文共享"""
    # 准备测试数据
    system_prompt = "你是一个智能助手"
    tools = [ReadTool(), WriteTool(), SessionNoteTool()]

    # 创建 agent
    agent = Agent(
        llm_client=mock_llm_client,
        system_prompt=system_prompt,
        tools=tools,
        workspace_dir=temp_workspace,
    )

    # 验证初始状态
    assert len(agent.messages) == 1  # 只有 system prompt
    assert agent.messages[0].role == "system"
    assert agent.messages[0].content == system_prompt

    # 添加第一条用户消息
    agent.add_user_message("你好")
    assert len(agent.messages) == 2
    assert agent.messages[1].role == "user"
    assert agent.messages[1].content == "你好"

    # 添加第二条用户消息
    agent.add_user_message("帮我创建一个文件")
    assert len(agent.messages) == 3
    assert agent.messages[2].role == "user"

    # 验证所有消息都保留在历史中
    user_messages = [m for m in agent.messages if m.role == "user"]
    assert len(user_messages) == 2
    assert user_messages[0].content == "你好"
    assert user_messages[1].content == "帮我创建一个文件"


def test_session_history_management(mock_llm_client, temp_workspace):
    """测试会话历史管理"""
    agent = Agent(
        llm_client=mock_llm_client,
        system_prompt="System prompt",
        tools=[],
        workspace_dir=temp_workspace,
    )

    # 添加多条消息
    for i in range(5):
        agent.add_user_message(f"Message {i}")

    # 验证消息数量（1 system + 5 user）
    assert len(agent.messages) == 6

    # 清除历史（保留 system prompt）
    agent.messages = [agent.messages[0]]

    # 验证清除后只剩 system prompt
    assert len(agent.messages) == 1
    assert agent.messages[0].role == "system"


def test_get_history(mock_llm_client, temp_workspace):
    """测试获取会话历史"""
    agent = Agent(
        llm_client=mock_llm_client,
        system_prompt="System",
        tools=[],
        workspace_dir=temp_workspace,
    )

    # 添加消息
    agent.add_user_message("Test message")

    # 获取历史
    history = agent.get_history()

    # 验证历史是副本（不影响原始消息）
    assert len(history) == len(agent.messages)
    assert history is not agent.messages

    # 修改副本不应影响原始消息
    history.append(Message(role="user", content="New message"))
    assert len(agent.messages) == 2  # 原始消息未改变
    assert len(history) == 3  # 副本已改变


@pytest.mark.asyncio
async def test_session_note_persistence(temp_workspace):
    """测试 SessionNoteTool 的持久化功能"""
    memory_file = Path(temp_workspace) / "memory.json"

    # 创建第一个 tool 实例并记录笔记
    record_tool = SessionNoteTool(memory_file=str(memory_file))
    result1 = await record_tool.execute(content="Test note", category="test")
    assert result1.success

    # 创建第二个 tool 实例（模拟新会话）
    recall_tool = RecallNoteTool(memory_file=str(memory_file))

    # 验证能够读取之前的笔记
    result2 = await recall_tool.execute()
    assert result2.success
    assert "Test note" in result2.content


def test_message_statistics(mock_llm_client, temp_workspace):
    """测试消息统计功能"""
    agent = Agent(
        llm_client=mock_llm_client,
        system_prompt="System",
        tools=[],
        workspace_dir=temp_workspace,
    )

    # 添加不同类型的消息
    agent.add_user_message("User message 1")
    agent.messages.append(Message(role="assistant", content="Assistant response 1"))
    agent.add_user_message("User message 2")
    agent.messages.append(
        Message(
            role="tool", content="Tool result", tool_call_id="123", name="test_tool"
        )
    )

    # 统计不同类型的消息
    user_msgs = sum(1 for m in agent.messages if m.role == "user")
    assistant_msgs = sum(1 for m in agent.messages if m.role == "assistant")
    tool_msgs = sum(1 for m in agent.messages if m.role == "tool")

    assert user_msgs == 2
    assert assistant_msgs == 1
    assert tool_msgs == 1
    assert len(agent.messages) == 5  # 1 system + 2 user + 1 assistant + 1 tool
