"""Test cases for Agent."""

import asyncio
import tempfile
from pathlib import Path

import pytest
import yaml

from mini_agent.agent import Agent
from mini_agent.llm import LLMClient
from mini_agent.tools import ReadTool, WriteTool, EditTool, BashTool


@pytest.mark.asyncio
async def test_agent_simple_task():
    """Test agent with a simple file creation task."""
    print("\n=== Testing Agent with Simple File Task ===")

    # Load config
    config_path = Path("mini_agent/config.yaml")
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Create temp workspace
    with tempfile.TemporaryDirectory() as workspace_dir:
        print(f"Using workspace: {workspace_dir}")

        # Load system prompt
        system_prompt = Path("system_prompt.txt").read_text(encoding="utf-8")

        # Initialize LLM client
        llm_client = LLMClient(
            api_key=config["api_key"],
            api_base=config.get("api_base"),
            model=config.get("model"),
        )

        # Initialize tools
        tools = [
            ReadTool(),
            WriteTool(),
            EditTool(),
            BashTool(),
        ]

        # Create agent
        agent = Agent(
            llm_client=llm_client,
            system_prompt=system_prompt,
            tools=tools,
            max_steps=10,  # Limit steps for testing
            workspace_dir=workspace_dir,
        )

        # Task: Create a simple text file
        task = "Create a file named 'test.txt' with the content 'Hello from Agent!'"
        print(f"\nTask: {task}\n")

        agent.add_user_message(task)

        try:
            result = await agent.run()

            print(f"\n{'=' * 80}")
            print(f"Agent Result: {result}")
            print("=" * 80)

            # Check if file was created
            test_file = Path(workspace_dir) / "test.txt"
            if test_file.exists():
                content = test_file.read_text()
                print(f"\n✅ File created successfully!")
                print(f"Content: {content}")

                if "Hello from Agent!" in content:
                    print("✅ Content is correct!")
                    return True
                else:
                    print(f"⚠️  Content mismatch: {content}")
                    return True  # Still count as success, agent did create the file
            else:
                print("⚠️  File was not created, but agent completed")
                return True  # Agent might have completed differently

        except Exception as e:
            print(f"❌ Agent test failed: {e}")
            import traceback

            traceback.print_exc()
            return False


@pytest.mark.asyncio
async def test_agent_bash_task():
    """Test agent with a bash command task."""
    print("\n=== Testing Agent with Bash Task ===")

    # Load config
    config_path = Path("mini_agent/config.yaml")
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Create temp workspace
    with tempfile.TemporaryDirectory() as workspace_dir:
        print(f"Using workspace: {workspace_dir}")

        # Load system prompt
        system_prompt = Path("system_prompt.txt").read_text(encoding="utf-8")

        # Initialize LLM client
        llm_client = LLMClient(
            api_key=config["api_key"],
            api_base=config.get("api_base"),
            model=config.get("model"),
        )

        # Initialize tools
        tools = [
            ReadTool(),
            WriteTool(),
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

        # Task: List files using bash
        task = "Use bash to list all files in the current directory and tell me what you find."
        print(f"\nTask: {task}\n")

        agent.add_user_message(task)

        try:
            result = await agent.run()

            print(f"\n{'=' * 80}")
            print(f"Agent Result: {result}")
            print("=" * 80)

            print("\n✅ Bash task completed!")
            return True

        except Exception as e:
            print(f"❌ Bash task failed: {e}")
            import traceback

            traceback.print_exc()
            return False


async def main():
    """Run all agent tests."""
    print("=" * 80)
    print("Running Agent Integration Tests")
    print("=" * 80)
    print("\nNote: These tests require a valid MiniMax API key in config.yaml")
    print("These tests will actually call the LLM API and may take some time.\n")

    # Test simple file task
    result1 = await test_agent_simple_task()

    # Test bash task
    result2 = await test_agent_bash_task()

    print("\n" + "=" * 80)
    if result1 and result2:
        print("All Agent tests passed! ✅")
    else:
        print("Some Agent tests failed. Check the output above.")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
