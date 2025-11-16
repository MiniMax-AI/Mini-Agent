"""Example 1: Basic Tools Usage

This example demonstrates how to use the basic tools:
- ReadTool: Read file contents
- WriteTool: Create new files
- EditTool: Edit existing files
- BashTool: Execute bash commands

Based on: tests/test_tools.py
"""

import asyncio
import tempfile
from pathlib import Path

from ye_linghua.tools import BashTool, EditTool, ReadTool, WriteTool


async def demo_write_tool():
    """Demo: Write a new file."""
    print("\n" + "=" * 60)
    print("Demo 1: WriteTool - Create a new file")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "hello.txt"

        tool = WriteTool()
        result = await tool.execute(
            path=str(file_path), content="Hello, Mini Agent!\nThis is a test file."
        )

        if result.success:
            print(f"✅ File created: {file_path}")
            print(f"Content:\n{file_path.read_text()}")
        else:
            print(f"❌ Failed: {result.error}")


async def demo_read_tool():
    """Demo: Read a file."""
    print("\n" + "=" * 60)
    print("Demo 2: ReadTool - Read file contents")
    print("=" * 60)

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("Line 1: Hello\nLine 2: World\nLine 3: Mini Agent")
        temp_path = f.name

    try:
        tool = ReadTool()
        result = await tool.execute(path=temp_path)

        if result.success:
            print(f"✅ File read successfully")
            print(f"Content:\n{result.content}")
        else:
            print(f"❌ Failed: {result.error}")
    finally:
        Path(temp_path).unlink()


async def demo_edit_tool():
    """Demo: Edit an existing file."""
    print("\n" + "=" * 60)
    print("Demo 3: EditTool - Edit file content")
    print("=" * 60)

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("Python is great!\nI love Python programming.")
        temp_path = f.name

    try:
        print(f"Original content:\n{Path(temp_path).read_text()}\n")

        tool = EditTool()
        result = await tool.execute(
            path=temp_path, old_str="Python", new_str="Agent"
        )

        if result.success:
            print(f"✅ File edited successfully")
            print(f"New content:\n{Path(temp_path).read_text()}")
        else:
            print(f"❌ Failed: {result.error}")
    finally:
        Path(temp_path).unlink()


async def demo_bash_tool():
    """Demo: Execute bash commands."""
    print("\n" + "=" * 60)
    print("Demo 4: BashTool - Execute bash commands")
    print("=" * 60)

    tool = BashTool()

    # Example 1: List files
    print("\nCommand: ls -la")
    result = await tool.execute(command="ls -la")
    if result.success:
        print(f"✅ Command executed successfully")
        print(f"Output:\n{result.content[:200]}...")

    # Example 2: Get current directory
    print("\nCommand: pwd")
    result = await tool.execute(command="pwd")
    if result.success:
        print(f"✅ Current directory: {result.content.strip()}")

    # Example 3: Echo
    print("\nCommand: echo 'Hello from BashTool!'")
    result = await tool.execute(command="echo 'Hello from BashTool!'")
    if result.success:
        print(f"✅ Output: {result.content.strip()}")


async def main():
    """Run all demos."""
    print("=" * 60)
    print("Basic Tools Usage Examples")
    print("=" * 60)
    print("\nThese examples show how to use the core tools directly.")
    print("In a real agent scenario, the LLM decides which tools to use.\n")

    await demo_write_tool()
    await demo_read_tool()
    await demo_edit_tool()
    await demo_bash_tool()

    print("\n" + "=" * 60)
    print("All demos completed! ✅")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
