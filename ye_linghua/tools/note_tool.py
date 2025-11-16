"""Session Note Tool - Let agent record and recall important information.

This tool allows the agent to:
- Record key points and important information during sessions
- Recall previously recorded notes
- Maintain context across agent execution chains
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .base import Tool, ToolResult


class SessionNoteTool(Tool):
    """Tool for recording and recalling session notes.

    The agent can use this tool to:
    - Record important facts, decisions, or context during sessions
    - Recall information from previous sessions
    - Build up knowledge over time

    Example usage by agent:
    - record_note("User prefers concise responses")
    - record_note("Project uses Python 3.12 and async/await")
    - recall_notes() -> retrieves all recorded notes
    """

    def __init__(self, memory_file: str = "./workspace/.agent_memory.json"):
        """Initialize session note tool.

        Args:
            memory_file: Path to the note storage file
        """
        self.memory_file = Path(memory_file)
        # Lazy loading: file and directory are only created when first note is recorded

    @property
    def name(self) -> str:
        return "record_note"

    @property
    def description(self) -> str:
        return (
            "Record important information as session notes for future reference. "
            "Use this to record key facts, user preferences, decisions, or context "
            "that should be recalled later in the agent execution chain. Each note is timestamped."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "The information to record as a note. Be concise but specific.",
                },
                "category": {
                    "type": "string",
                    "description": "Optional category/tag for this note (e.g., 'user_preference', 'project_info', 'decision')",
                },
            },
            "required": ["content"],
        }

    def _load_from_file(self) -> list:
        """Load notes from file.
        
        Returns empty list if file doesn't exist (lazy loading).
        """
        if not self.memory_file.exists():
            return []
        
        try:
            return json.loads(self.memory_file.read_text())
        except Exception:
            return []

    def _save_to_file(self, notes: list):
        """Save notes to file.
        
        Creates parent directory and file if they don't exist (lazy initialization).
        """
        # Ensure parent directory exists when actually saving
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        self.memory_file.write_text(json.dumps(notes, indent=2, ensure_ascii=False))

    async def execute(self, content: str, category: str = "general") -> ToolResult:
        """Record a session note.

        Args:
            content: The information to record
            category: Category/tag for this note

        Returns:
            ToolResult with success status
        """
        try:
            # Load existing notes
            notes = self._load_from_file()

            # Add new note with timestamp
            note = {
                "timestamp": datetime.now().isoformat(),
                "category": category,
                "content": content,
            }
            notes.append(note)

            # Save back to file
            self._save_to_file(notes)

            return ToolResult(
                success=True,
                content=f"Recorded note: {content} (category: {category})",
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=f"Failed to record note: {str(e)}",
            )


class RecallNoteTool(Tool):
    """Tool for recalling recorded session notes."""

    def __init__(self, memory_file: str = "./workspace/.agent_memory.json"):
        """Initialize recall note tool.

        Args:
            memory_file: Path to the note storage file
        """
        self.memory_file = Path(memory_file)

    @property
    def name(self) -> str:
        return "recall_notes"

    @property
    def description(self) -> str:
        return (
            "Recall all previously recorded session notes. "
            "Use this to retrieve important information, context, or decisions "
            "from earlier in the session or previous agent execution chains."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Optional: filter notes by category",
                },
            },
        }

    async def execute(self, category: str = None) -> ToolResult:
        """Recall session notes.

        Args:
            category: Optional category filter

        Returns:
            ToolResult with notes content
        """
        try:
            if not self.memory_file.exists():
                return ToolResult(
                    success=True,
                    content="No notes recorded yet.",
                )

            notes = json.loads(self.memory_file.read_text())

            if not notes:
                return ToolResult(
                    success=True,
                    content="No notes recorded yet.",
                )

            # Filter by category if specified
            if category:
                notes = [n for n in notes if n.get("category") == category]
                if not notes:
                    return ToolResult(
                        success=True,
                        content=f"No notes found in category: {category}",
                    )

            # Format notes for display
            formatted = []
            for idx, note in enumerate(notes, 1):
                timestamp = note.get("timestamp", "unknown time")
                cat = note.get("category", "general")
                content = note.get("content", "")
                formatted.append(f"{idx}. [{cat}] {content}\n   (recorded at {timestamp})")

            result = "Recorded Notes:\n" + "\n".join(formatted)

            return ToolResult(success=True, content=result)

        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=f"Failed to recall notes: {str(e)}",
            )
