"""File operation tools."""

import os
from pathlib import Path
from typing import Any, Dict

from .base import Tool, ToolResult


class ReadTool(Tool):
    """Read file content."""

    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return "Read the contents of a file."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to read",
                }
            },
            "required": ["file_path"],
        }

    async def execute(self, file_path: str) -> ToolResult:
        """Execute read file."""
        try:
            path = Path(file_path)
            if not path.exists():
                return ToolResult(
                    success=False,
                    content="",
                    error=f"File not found: {file_path}",
                )

            content = path.read_text(encoding="utf-8")
            return ToolResult(success=True, content=content)
        except Exception as e:
            return ToolResult(success=False, content="", error=str(e))


class WriteTool(Tool):
    """Write content to a file."""

    @property
    def name(self) -> str:
        return "write_file"

    @property
    def description(self) -> str:
        return "Write content to a file. Creates the file if it doesn't exist."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to write",
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file",
                },
            },
            "required": ["file_path", "content"],
        }

    async def execute(self, file_path: str, content: str) -> ToolResult:
        """Execute write file."""
        try:
            path = Path(file_path)
            # Create parent directories if they don't exist
            path.parent.mkdir(parents=True, exist_ok=True)

            path.write_text(content, encoding="utf-8")
            return ToolResult(
                success=True, content=f"Successfully wrote to {file_path}"
            )
        except Exception as e:
            return ToolResult(success=False, content="", error=str(e))


class EditTool(Tool):
    """Edit file by replacing text."""

    @property
    def name(self) -> str:
        return "edit_file"

    @property
    def description(self) -> str:
        return "Edit a file by replacing old_text with new_text."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to edit",
                },
                "old_text": {
                    "type": "string",
                    "description": "Text to replace",
                },
                "new_text": {
                    "type": "string",
                    "description": "Text to replace with",
                },
            },
            "required": ["file_path", "old_text", "new_text"],
        }

    async def execute(self, file_path: str, old_text: str, new_text: str) -> ToolResult:
        """Execute edit file."""
        try:
            path = Path(file_path)
            if not path.exists():
                return ToolResult(
                    success=False,
                    content="",
                    error=f"File not found: {file_path}",
                )

            content = path.read_text(encoding="utf-8")

            if old_text not in content:
                return ToolResult(
                    success=False,
                    content="",
                    error=f"Text not found in file: {old_text}",
                )

            new_content = content.replace(old_text, new_text)
            path.write_text(new_content, encoding="utf-8")

            return ToolResult(
                success=True, content=f"Successfully edited {file_path}"
            )
        except Exception as e:
            return ToolResult(success=False, content="", error=str(e))
