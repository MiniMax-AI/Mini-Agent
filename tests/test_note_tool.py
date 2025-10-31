"""Test cases for Session Note Tool."""

import tempfile
from pathlib import Path

import pytest

from mini_agent.tools.note_tool import SessionNoteTool, RecallNoteTool


@pytest.mark.asyncio
async def test_record_and_recall_notes():
    """Test recording and recalling notes."""
    print("\n=== Testing Note Record and Recall ===")

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        note_file = f.name

    try:
        # Create tools
        record_tool = SessionNoteTool(memory_file=note_file)
        recall_tool = RecallNoteTool(memory_file=note_file)

        # Record a note
        result = await record_tool.execute(
            content="User prefers concise responses",
            category="user_preference",
        )
        assert result.success
        print(f"Record result: {result.content}")

        # Record another note
        result = await record_tool.execute(
            content="Project uses Python 3.12",
            category="project_info",
        )
        assert result.success
        print(f"Record result: {result.content}")

        # Recall all notes
        result = await recall_tool.execute()
        assert result.success
        assert "User prefers concise responses" in result.content
        assert "Python 3.12" in result.content
        print(f"\nAll notes:\n{result.content}")

        # Recall filtered by category
        result = await recall_tool.execute(category="user_preference")
        assert result.success
        assert "User prefers concise responses" in result.content
        assert "Python 3.12" not in result.content
        print(f"\nFiltered notes:\n{result.content}")

        print("✅ Note record and recall test passed")

    finally:
        Path(note_file).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_empty_notes():
    """Test recalling empty notes."""
    print("\n=== Testing Empty Notes ===")

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        note_file = f.name

    # Delete the file to test empty state
    Path(note_file).unlink()

    try:
        recall_tool = RecallNoteTool(memory_file=note_file)

        # Recall empty notes
        result = await recall_tool.execute()
        assert result.success
        assert "No notes recorded yet" in result.content
        print(f"Empty notes result: {result.content}")

        print("✅ Empty notes test passed")

    finally:
        Path(note_file).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_note_persistence():
    """Test that notes persist across tool instances."""
    print("\n=== Testing Note Persistence ===")

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        note_file = f.name

    try:
        # First instance - record note
        record_tool1 = SessionNoteTool(memory_file=note_file)
        result = await record_tool1.execute(
            content="Important fact to remember",
            category="test",
        )
        assert result.success

        # Second instance - recall note (simulates new session)
        recall_tool2 = RecallNoteTool(memory_file=note_file)
        result = await recall_tool2.execute()
        assert result.success
        assert "Important fact to remember" in result.content
        print(f"Persisted note: {result.content}")

        print("✅ Note persistence test passed")

    finally:
        Path(note_file).unlink(missing_ok=True)


async def main():
    """Run all session note tool tests."""
    print("=" * 80)
    print("Running Session Note Tool Tests")
    print("=" * 80)

    await test_record_and_recall_notes()
    await test_empty_notes()
    await test_note_persistence()

    print("\n" + "=" * 80)
    print("All Session Note Tool tests passed! ✅")
    print("=" * 80)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
