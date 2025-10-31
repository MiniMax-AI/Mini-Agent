"""Example 4: Full Agent with All Features

This example demonstrates a complete agent setup with:
- All basic tools (Read, Write, Edit, Bash)
- Session Note tools for memory
- MCP tools (Memory, Search, etc.)
- Skills integration

Based on: tests/test_integration.py
"""

import asyncio
import tempfile
from pathlib import Path

import yaml

from mini_agent.agent import Agent
from mini_agent.llm import LLMClient
from mini_agent.tools import ReadTool, WriteTool, EditTool, BashTool
from mini_agent.tools.note_tool import SessionNoteTool, RecallNoteTool
from mini_agent.tools.mcp_loader import load_mcp_tools_async


async def demo_full_agent():
    """Demo: Full-featured agent with all capabilities."""
    print("\n" + "=" * 60)
    print("Full Mini Agent - All Features Enabled")
    print("=" * 60)

    # Load configuration
    config_path = Path("mini_agent/config.yaml")
    if not config_path.exists():
        print("❌ config.yaml not found. Please run:")
        print("   cp mini_agent/config-example.yaml mini_agent/config.yaml")
        return

    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Check API key
    if not config.get("api_key") or config["api_key"].startswith("YOUR_"):
        print("❌ API key not configured in config.yaml")
        return

    # Create workspace
    with tempfile.TemporaryDirectory() as workspace_dir:
        print(f"📁 Workspace: {workspace_dir}")

        # Load system prompt
        system_prompt_path = Path("system_prompt.txt")
        if system_prompt_path.exists():
            system_prompt = system_prompt_path.read_text(encoding="utf-8")
        else:
            system_prompt = "You are a helpful AI assistant."

        # Add Session Note instructions
        note_instructions = """

IMPORTANT - Session Memory:
You have record_note and recall_notes tools. Use them to:
- Save important facts, decisions, and context
- Recall previous information across conversations
"""
        system_prompt += note_instructions

        # Initialize LLM
        llm_client = LLMClient(
            api_key=config["api_key"],
            api_base=config.get("api_base"),
            model=config.get("model"),
        )

        # Initialize basic tools
        tools = [
            ReadTool(),
            WriteTool(),
            EditTool(),
            BashTool(),
        ]
        print("✓ Loaded 4 basic tools")

        # Add Session Note tools
        memory_file = Path(workspace_dir) / ".agent_memory.json"
        tools.extend(
            [
                SessionNoteTool(memory_file=str(memory_file)),
                RecallNoteTool(memory_file=str(memory_file)),
            ]
        )
        print("✓ Loaded 2 Session Note tools")

        # Load MCP tools (if configured)
        try:
            mcp_tools = await load_mcp_tools_async(config_path="mcp.json")
            if mcp_tools:
                tools.extend(mcp_tools)
                print(f"✓ Loaded {len(mcp_tools)} MCP tools")
            else:
                print("⚠️  No MCP tools configured (mcp.json is empty or disabled)")
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

        print(f"\n🤖 Agent created with {len(tools)} total tools\n")

        # Task: Complex task that uses multiple tools
        task = """
        Please help me with the following tasks:

        1. Create a Python script called 'calculator.py' that:
           - Has functions for add, subtract, multiply, divide
           - Has a main() function that demonstrates usage
           - Includes proper docstrings and type hints

        2. Create a README.md file that:
           - Describes the calculator script
           - Shows how to run it
           - Lists the available functions

        3. Test the calculator by running it with bash

        4. Remember this project info:
           - Project: Simple Calculator
           - Language: Python
           - Purpose: Demonstration of agent capabilities
        """

        print("=" * 60)
        print("📝 Task:")
        print("=" * 60)
        print(task)
        print("\n" + "=" * 60)
        print("🤖 Agent is working...\n")

        agent.add_user_message(task)

        try:
            result = await agent.run()

            print("\n" + "=" * 60)
            print("✅ Agent completed!")
            print("=" * 60)
            print(f"\nAgent's final response:\n{result}\n")

            # Show created files
            print("=" * 60)
            print("📄 Created files in workspace:")
            print("=" * 60)

            workspace = Path(workspace_dir)
            for file in workspace.glob("*"):
                if file.is_file() and not file.name.startswith("."):
                    print(f"\n📄 {file.name}:")
                    print("-" * 60)
                    content = file.read_text()
                    # Show first 20 lines
                    lines = content.split("\n")[:20]
                    print("\n".join(lines))
                    if len(content.split("\n")) > 20:
                        print("... (truncated)")
                    print("-" * 60)

            # Show memory
            if memory_file.exists():
                import json

                notes = json.loads(memory_file.read_text())
                print(f"\n💾 Session notes recorded: {len(notes)}")
                for note in notes:
                    print(f"  - [{note['category']}] {note['content'][:60]}...")

        except Exception as e:
            print(f"❌ Error during agent execution: {e}")
            import traceback

            traceback.print_exc()


async def demo_interactive_mode():
    """Demo: Interactive conversation with agent."""
    print("\n" + "=" * 60)
    print("Interactive Mini Agent")
    print("=" * 60)
    print("\nThis demo shows multi-turn conversation.")
    print("(In production, use main.py for full interactive mode)")

    # Load config
    config_path = Path("mini_agent/config.yaml")
    if not config_path.exists():
        print("❌ config.yaml not found")
        return

    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if not config.get("api_key") or config["api_key"].startswith("YOUR_"):
        print("❌ API key not configured")
        return

    with tempfile.TemporaryDirectory() as workspace_dir:
        # Setup
        system_prompt = "You are a helpful assistant with access to tools."
        llm_client = LLMClient(
            api_key=config["api_key"],
            api_base=config.get("api_base"),
            model=config.get("model"),
        )

        tools = [WriteTool(), ReadTool(), BashTool()]

        agent = Agent(
            llm_client=llm_client,
            system_prompt=system_prompt,
            tools=tools,
            max_steps=20,
            workspace_dir=workspace_dir,
        )

        # Conversation turns
        conversations = [
            "Create a file called 'data.txt' with the numbers 1 to 5, one per line.",
            "Now read the file and tell me what's in it.",
            "Count how many lines are in the file using bash.",
        ]

        for i, message in enumerate(conversations, 1):
            print(f"\n{'=' * 60}")
            print(f"Turn {i}:")
            print(f"{'=' * 60}")
            print(f"User: {message}\n")

            agent.add_user_message(message)

            try:
                result = await agent.run()
                print(f"Agent: {result}\n")
            except Exception as e:
                print(f"Error: {e}")
                break


async def main():
    """Run all demos."""
    print("=" * 60)
    print("Full Agent Examples")
    print("=" * 60)
    print("\nThese examples demonstrate the complete agent capabilities:")
    print("- All basic tools (file operations, bash)")
    print("- Session memory (persistent notes)")
    print("- MCP tools (if configured)")
    print("- Multi-turn conversations\n")

    # Run demos
    await demo_full_agent()
    print("\n" * 2)
    await demo_interactive_mode()

    print("\n" + "=" * 60)
    print("All demos completed! ✅")
    print("=" * 60)
    print("\n💡 Next step: Try the interactive mode with:")
    print("   python main.py\n")


if __name__ == "__main__":
    asyncio.run(main())
