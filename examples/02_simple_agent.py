"""Example 2: Simple Agent Usage

This example demonstrates how to create and run a basic agent
to perform simple file operations.

Based on: tests/test_agent.py
"""

import asyncio
import tempfile
from pathlib import Path

from ye_linghua import LLMClient
from ye_linghua.agent import Agent
from ye_linghua.config import Config
from ye_linghua.tools import BashTool, EditTool, ReadTool, WriteTool


async def demo_file_creation():
    """Demo: Agent creates a file based on user request."""
    print("\n" + "=" * 60)
    print("Demo: Agent-Driven File Creation")
    print("=" * 60)

    # Load configuration
    config_path = Path("mini_agent/config/config.yaml")
    if not config_path.exists():
        print("❌ config.yaml not found. Please set up your API key first.")
        print("   Run: cp mini_agent/config/config-example.yaml mini_agent/config/config.yaml")
        return

    config = Config.from_yaml(config_path)

    # Check API key
    if not config.llm.api_key or config.llm.api_key.startswith("YOUR_"):
        print("❌ API key not configured in config.yaml")
        return

    # Create temporary workspace
    with tempfile.TemporaryDirectory() as workspace_dir:
        print(f"📁 Workspace: {workspace_dir}\n")

        # Load system prompt (Agent will auto-inject workspace info)
        system_prompt_path = Path("mini_agent/config/system_prompt.md")
        if system_prompt_path.exists():
            system_prompt = system_prompt_path.read_text(encoding="utf-8")
        else:
            system_prompt = "You are a helpful AI assistant that can use tools."

        # Initialize LLM client
        llm_client = LLMClient(
            api_key=config.llm.api_key,
            api_base=config.llm.api_base,
            model=config.llm.model,
        )

        # Initialize tools
        tools = [
            ReadTool(workspace_dir=workspace_dir),
            WriteTool(workspace_dir=workspace_dir),
            EditTool(workspace_dir=workspace_dir),
            BashTool(),
        ]

        # Create agent
        agent = Agent(
            llm_client=llm_client,
            system_prompt=system_prompt,
            tools=tools,
            max_steps=10,
            workspace_dir=workspace_dir,
        )

        # Task: Create a Python hello world file
        task = """
        Create a Python file named 'hello.py' that:
        1. Defines a function called greet(name)
        2. The function prints "Hello, {name}!"
        3. Calls the function with name="Mini Agent"
        """

        print("📝 Task:")
        print(task)
        print("\n" + "=" * 60)
        print("🤖 Agent is working...\n")

        agent.add_user_message(task)

        try:
            result = await agent.run()

            print("\n" + "=" * 60)
            print("✅ Agent completed the task!")
            print("=" * 60)
            print(f"\nAgent's response:\n{result}\n")

            # Check if file was created
            hello_file = Path(workspace_dir) / "hello.py"
            if hello_file.exists():
                print("=" * 60)
                print("📄 Created file content:")
                print("=" * 60)
                print(hello_file.read_text())
                print("=" * 60)
            else:
                print("⚠️  File was not created (but agent may have completed differently)")

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback

            traceback.print_exc()


async def demo_bash_task():
    """Demo: Agent executes bash commands."""
    print("\n" + "=" * 60)
    print("Demo: Agent-Driven Bash Commands")
    print("=" * 60)

    # Load configuration
    config_path = Path("mini_agent/config/config.yaml")
    if not config_path.exists():
        print("❌ config.yaml not found")
        return

    config = Config.from_yaml(config_path)

    if not config.llm.api_key or config.llm.api_key.startswith("YOUR_"):
        print("❌ API key not configured")
        return

    with tempfile.TemporaryDirectory() as workspace_dir:
        print(f"📁 Workspace: {workspace_dir}\n")

        # Load system prompt (Agent will auto-inject workspace info)
        system_prompt_path = Path("mini_agent/config/system_prompt.md")
        if system_prompt_path.exists():
            system_prompt = system_prompt_path.read_text(encoding="utf-8")
        else:
            system_prompt = "You are a helpful AI assistant that can use tools."

        # Initialize LLM
        llm_client = LLMClient(
            api_key=config.llm.api_key,
            api_base=config.llm.api_base,
            model=config.llm.model,
        )

        # Tools
        tools = [
            ReadTool(workspace_dir=workspace_dir),
            WriteTool(workspace_dir=workspace_dir),
            BashTool(),
        ]

        # Create agent
        agent = Agent(
            llm_client=llm_client,
            system_prompt=system_prompt,
            tools=tools,
            max_steps=10,
            workspace_dir=workspace_dir,
        )

        # Task: Use bash to get system info
        task = """
        Use bash commands to:
        1. Show the current date and time
        2. List all Python files in the current directory
        3. Count how many Python files exist
        """

        print("📝 Task:")
        print(task)
        print("\n" + "=" * 60)
        print("🤖 Agent is working...\n")

        agent.add_user_message(task)

        try:
            result = await agent.run()

            print("\n" + "=" * 60)
            print("✅ Agent completed!")
            print("=" * 60)
            print(f"\nAgent's response:\n{result}\n")

        except Exception as e:
            print(f"❌ Error: {e}")


async def main():
    """Run all demos."""
    print("=" * 60)
    print("Simple Agent Usage Examples")
    print("=" * 60)
    print("\nThese examples show how to create an agent and give it tasks.")
    print("The agent uses LLM to decide which tools to call.\n")

    # Run demos
    await demo_file_creation()
    print("\n" * 2)
    await demo_bash_task()

    print("\n" + "=" * 60)
    print("All demos completed! ✅")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
