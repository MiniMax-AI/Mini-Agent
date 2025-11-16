"""
Session integration tests - Testing multi-turn conversations and session management
"""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ye_linghua import LLMClient
from ye_linghua.agent import Agent
from ye_linghua.schema import LLMResponse, Message
from ye_linghua.tools.bash_tool import BashTool
from ye_linghua.tools.file_tools import ReadTool, WriteTool
from ye_linghua.tools.note_tool import RecallNoteTool, SessionNoteTool


@pytest.fixture
def mock_llm_client():
    """Create mock LLM client"""
    client = MagicMock(spec=LLMClient)
    return client


@pytest.fixture
def temp_workspace():
    """Create temporary workspace directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


def test_multi_turn_conversation(mock_llm_client, temp_workspace):
    """Test multi-turn conversation and context sharing"""
    # Prepare test data
    system_prompt = "You are an intelligent assistant"
    tools = [
        ReadTool(workspace_dir=temp_workspace),
        WriteTool(workspace_dir=temp_workspace),
        SessionNoteTool(),
    ]

    # Create agent
    agent = Agent(
        llm_client=mock_llm_client,
        system_prompt=system_prompt,
        tools=tools,
        workspace_dir=temp_workspace,
    )

    # Verify initial state
    assert len(agent.messages) == 1  # Only system prompt
    assert agent.messages[0].role == "system"
    # Agent automatically adds workspace info to system prompt
    assert system_prompt in agent.messages[0].content
    assert "Current Workspace" in agent.messages[0].content

    # Add first user message
    agent.add_user_message("Hello")
    assert len(agent.messages) == 2
    assert agent.messages[1].role == "user"
    assert agent.messages[1].content == "Hello"

    # Add second user message
    agent.add_user_message("Help me create a file")
    assert len(agent.messages) == 3
    assert agent.messages[2].role == "user"

    # Verify all messages are retained in history
    user_messages = [m for m in agent.messages if m.role == "user"]
    assert len(user_messages) == 2
    assert user_messages[0].content == "Hello"
    assert user_messages[1].content == "Help me create a file"


def test_session_history_management(mock_llm_client, temp_workspace):
    """Test session history management"""
    agent = Agent(
        llm_client=mock_llm_client,
        system_prompt="System prompt",
        tools=[],
        workspace_dir=temp_workspace,
    )

    # Add multiple messages
    for i in range(5):
        agent.add_user_message(f"Message {i}")

    # Verify message count (1 system + 5 user)
    assert len(agent.messages) == 6

    # Clear history (keep system prompt)
    agent.messages = [agent.messages[0]]

    # Verify only system prompt remains after clearing
    assert len(agent.messages) == 1
    assert agent.messages[0].role == "system"


def test_get_history(mock_llm_client, temp_workspace):
    """Test getting session history"""
    agent = Agent(
        llm_client=mock_llm_client,
        system_prompt="System",
        tools=[],
        workspace_dir=temp_workspace,
    )

    # Add message
    agent.add_user_message("Test message")

    # Get history
    history = agent.get_history()

    # Verify history is a copy (doesn't affect original messages)
    assert len(history) == len(agent.messages)
    assert history is not agent.messages

    # Modifying copy should not affect original messages
    history.append(Message(role="user", content="New message"))
    assert len(agent.messages) == 2  # Original messages unchanged
    assert len(history) == 3  # Copy changed


@pytest.mark.asyncio
async def test_session_note_persistence(temp_workspace):
    """Test SessionNoteTool persistence functionality"""
    memory_file = Path(temp_workspace) / "memory.json"

    # Create first tool instance and record note
    record_tool = SessionNoteTool(memory_file=str(memory_file))
    result1 = await record_tool.execute(content="Test note", category="test")
    assert result1.success

    # Create second tool instance (simulating new session)
    recall_tool = RecallNoteTool(memory_file=str(memory_file))

    # Verify ability to read previous notes
    result2 = await recall_tool.execute()
    assert result2.success
    assert "Test note" in result2.content


def test_message_statistics(mock_llm_client, temp_workspace):
    """Test message statistics functionality"""
    agent = Agent(
        llm_client=mock_llm_client,
        system_prompt="System",
        tools=[],
        workspace_dir=temp_workspace,
    )

    # Add different types of messages
    agent.add_user_message("User message 1")
    agent.messages.append(Message(role="assistant", content="Assistant response 1"))
    agent.add_user_message("User message 2")
    agent.messages.append(
        Message(
            role="tool", content="Tool result", tool_call_id="123", name="test_tool"
        )
    )

    # Count different types of messages
    user_msgs = sum(1 for m in agent.messages if m.role == "user")
    assistant_msgs = sum(1 for m in agent.messages if m.role == "assistant")
    tool_msgs = sum(1 for m in agent.messages if m.role == "tool")

    assert user_msgs == 2
    assert assistant_msgs == 1
    assert tool_msgs == 1
    assert len(agent.messages) == 5  # 1 system + 2 user + 1 assistant + 1 tool
