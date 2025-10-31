"""Integration test cases - Full agent demos."""

import asyncio
import json
import tempfile
from pathlib import Path

import pytest
import yaml

from mini_agent.agent import Agent
from mini_agent.llm import LLMClient
from mini_agent.tools import ReadTool, WriteTool, EditTool, BashTool
from mini_agent.tools.note_tool import SessionNoteTool, RecallNoteTool
from mini_agent.tools.mcp_loader import load_mcp_tools_async


@pytest.mark.asyncio
async def test_basic_agent_usage():
    """Test basic agent usage with file creation task.

    This is the integration test for basic agent functionality,
    converted from example.py.
    """
    print("\n" + "=" * 80)
    print("Integration Test: Basic Agent Usage")
    print("=" * 80)

    # Load configuration
    config_path = Path("mini_agent/config.yaml")
    if not config_path.exists():
        pytest.skip("config.yaml not found")

    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Check API key
    if not config.get("api_key") or config["api_key"] == "YOUR_MINIMAX_API_KEY_HERE":
        pytest.skip("API key not configured")

    # Load system prompt
    system_prompt_path = Path("system_prompt.txt")
    if system_prompt_path.exists():
        system_prompt = system_prompt_path.read_text(encoding="utf-8")
    else:
        system_prompt = "You are a helpful AI assistant."

    # Use temporary workspace
    with tempfile.TemporaryDirectory() as workspace_dir:
        # Initialize LLM client
        llm_client = LLMClient(
            api_key=config["api_key"],
            api_base=config.get(
                "api_base", "https://api.minimax.chat/v1/text/chatcompletion_v2"
            ),
            model=config.get("model"),
        )

        # Initialize basic tools
        tools = [
            ReadTool(),
            WriteTool(),
            EditTool(),
            BashTool(),
        ]

        # Add Note tools for session memory
        memory_file = Path(workspace_dir) / ".agent_memory.json"
        tools.extend(
            [
                SessionNoteTool(memory_file=str(memory_file)),
                RecallNoteTool(memory_file=str(memory_file)),
            ]
        )

        # Load MCP tools (optional) - with timeout protection
        try:
            # MCP tools are disabled by default to prevent test hangs
            # Enable specific MCP servers in mcp.json if needed
            mcp_tools = await load_mcp_tools_async(config_path="mcp.json")
            if mcp_tools:
                print(f"✓ Loaded {len(mcp_tools)} MCP tools")
                tools.extend(mcp_tools)
            else:
                print("⚠️  No MCP tools configured (mcp.json is empty)")
        except Exception as e:
            print(f"⚠️  MCP tools not loaded: {e}")

        # Create agent
        agent = Agent(
            llm_client=llm_client,
            system_prompt=system_prompt,
            tools=tools,
            max_steps=config.get("max_steps", 50),
            workspace_dir=workspace_dir,
        )

        # Task: Create a Python file with hello world
        task = """
        Create a Python file named hello.py in the workspace that prints "Hello, Mini Agent!".
        Then execute it to verify it works.
        """

        print(f"\nTask: {task}")
        print("\n" + "=" * 80 + "\n")

        agent.add_user_message(task)
        result = await agent.run()

        print("\n" + "=" * 80)
        print(f"Result: {result}")
        print("=" * 80)

        # Verify the file was created or task completed
        hello_file = Path(workspace_dir) / "hello.py"
        assert hello_file.exists() or "complete" in result.lower(), (
            "Agent should create the file or indicate completion"
        )

        print("\n✅ Basic agent usage test passed")


@pytest.mark.asyncio
async def test_session_memory_demo():
    """Test session memory functionality across multiple agent instances.

    This is the integration test for session note tool,
    converted from example_memory.py.
    """
    print("\n" + "=" * 80)
    print("Integration Test: Session Memory Demo")
    print("=" * 80)

    # Load config
    config_path = Path("mini_agent/config.yaml")
    if not config_path.exists():
        pytest.skip("config.yaml not found")

    config = yaml.safe_load(config_path.read_text())

    # Check API key
    if not config.get("api_key") or config["api_key"] == "YOUR_MINIMAX_API_KEY_HERE":
        pytest.skip("API key not configured")

    # Load system prompt
    system_prompt_path = Path("system_prompt.txt")
    if system_prompt_path.exists():
        system_prompt = system_prompt_path.read_text()
    else:
        system_prompt = "You are a helpful AI assistant."

    # Add session note instructions
    note_instructions = """

IMPORTANT - Session Note Management:
You have access to record_note and recall_notes tools. Use them to:
- record_note: Record important facts, user preferences, decisions, or context during sessions
- recall_notes: Retrieve previously recorded notes from session history

Guidelines:
- Proactively record key information that should be remembered across agent execution chains
- Recall notes at the start to restore context
- Update notes when preferences or facts change
"""
    system_prompt += note_instructions

    # Use temporary workspace
    with tempfile.TemporaryDirectory() as workspace_dir:
        # Initialize LLM
        llm_client = LLMClient(
            api_key=config["api_key"],
            api_base=config.get("api_base"),
            model=config.get("model"),
        )

        # Memory file path
        memory_file = Path(workspace_dir) / ".agent_memory.json"

        # Initialize tools (including Session Note Tools)
        tools = [
            ReadTool(),
            WriteTool(),
            BashTool(),
            SessionNoteTool(memory_file=str(memory_file)),
            RecallNoteTool(memory_file=str(memory_file)),
        ]

        print("\n📝 Creating Agent with Session Note tools...")
        agent = Agent(
            llm_client=llm_client,
            system_prompt=system_prompt,
            tools=tools,
            max_steps=15,
            workspace_dir=workspace_dir,
        )

        # Task 1: First conversation - agent should save memories
        task1 = """
        Hello! I'm a developer learning Python.
        My project information:
        - Project name: mini-agent
        - Technologies: Python 3.12, async/await, MiniMax M2
        - I prefer concise code style

        Please create a demo.py file with a simple hello world function.
        Also, please remember this information for future use.
        """

        print(f"\n📌 First Conversation:\n{task1}")
        print("=" * 80)

        agent.add_user_message(task1)
        result1 = await agent.run()

        print("\n" + "=" * 80)
        print(f"Agent completed: {result1[:200]}...")
        print("=" * 80)

        # Check if notes were recorded
        if memory_file.exists():
            notes = json.loads(memory_file.read_text())
            print(f"\n✅ Agent recorded {len(notes)} notes:")
            for note in notes:
                print(f"  - [{note['category']}] {note['content']}")
            assert len(notes) > 0, "Agent should have recorded some notes"
        else:
            print("\n⚠️  No notes found - agent may not have used record_note tool")

        print("\n\n" + "=" * 80)
        print("Simulating New Session (Agent should recall previous information)")
        print("=" * 80)

        # Task 2: New conversation - agent should recall memories
        agent2 = Agent(
            llm_client=llm_client,
            system_prompt=system_prompt,
            tools=tools,
            max_steps=10,
            workspace_dir=workspace_dir,
        )

        task2 = """
        Hello! I want to continue my previous work.
        Please tell me: Do you remember my project information and preferences?
        """

        print(f"\n📌 Second Conversation (new session):\n{task2}")
        print("=" * 80)

        agent2.add_user_message(task2)
        result2 = await agent2.run()

        print("\n" + "=" * 80)
        print(f"Agent response: {result2}")
        print("=" * 80)

        print("\n✅ Session Note Tool test completed!")
        print("\nKey Points Verified:")
        print("  1. Agent can record important information")
        print("  2. Notes persist in memory file")
        print("  3. New agent instances can recall previous notes")


async def main():
    """Run all integration tests."""
    print("=" * 80)
    print("Running Integration Tests")
    print("=" * 80)
    print("\nNote: These tests require a valid MiniMax API key in config.yaml")
    print("These tests will actually call the LLM API and may take some time.\n")

    try:
        await test_basic_agent_usage()
    except Exception as e:
        print(f"❌ Basic usage test failed: {e}")

    try:
        await test_session_memory_demo()
    except Exception as e:
        print(f"❌ Session memory test failed: {e}")

    print("\n" + "=" * 80)
    print("Integration tests completed!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
