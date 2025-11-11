"""File operation tools."""

from pathlib import Path
from typing import Any

try:
    import tiktoken  # type: ignore
except Exception:  # pragma: no cover - optional dependency at runtime
    tiktoken = None  # Fallback when network or package data unavailable

from .base import Tool, ToolResult


def truncate_text_by_tokens(
    text: str,
    max_tokens: int,
) -> str:
    """Truncate text by token count if it exceeds the limit.

    When text exceeds the specified token limit, performs intelligent truncation
    by keeping the front and back parts while truncating the middle.

    Args:
        text: Text to be truncated
        max_tokens: Maximum token limit

    Returns:
        str: Truncated text if it exceeds the limit, otherwise the original text.

    Example:
        >>> text = "very long text..." * 10000
        >>> truncated = truncate_text_by_tokens(text, 64000)
        >>> print(truncated)
    """
    # Try accurate tokenization when available; otherwise fall back to chars
    try:
        if tiktoken is not None:
            encoding = tiktoken.get_encoding("cl100k_base")
            token_count = len(encoding.encode(text))
        else:
            raise RuntimeError("tiktoken not available")
    except Exception:
        # Fallback: approximate tokens by characters (4 chars ≈ 1 token)
        token_count = int(len(text) / 4)

    # Return original text if under limit
    if token_count <= max_tokens:
        return text

    # Calculate token/character ratio for approximation
    char_count = max(1, len(text))
    # Approximate ratio; when using fallback, inverse of 4 chars per token
    ratio = token_count / char_count if token_count else 1.0

    # Keep head and tail mode: allocate half space for each (with 5% safety margin)
    chars_per_half = int((max_tokens / 2) / ratio * 0.95)

    # Truncate front part: find nearest newline
    head_part = text[:chars_per_half]
    last_newline_head = head_part.rfind("\n")
    if last_newline_head > 0:
        head_part = head_part[:last_newline_head]

    # Truncate back part: find nearest newline
    tail_part = text[-chars_per_half:]
    first_newline_tail = tail_part.find("\n")
    if first_newline_tail > 0:
        tail_part = tail_part[first_newline_tail + 1 :]

    # Combine result
    truncation_note = f"\n\n... [Content truncated: {token_count} tokens -> ~{max_tokens} tokens limit] ...\n\n"
    return head_part + truncation_note + tail_part


class ReadTool(Tool):
    """Read file content."""

    def __init__(self, workspace_dir: str = "."):
        """Initialize ReadTool with workspace directory.

        Args:
            workspace_dir: Base directory for resolving relative paths
        """
        self.workspace_dir = Path(workspace_dir).absolute()

    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return (
            "Read file contents from the filesystem. Output always includes line numbers "
            "in format 'LINE_NUMBER|LINE_CONTENT' (1-indexed). Supports reading partial content "
            "by specifying line offset and limit for large files. "
            "You can call this tool multiple times in parallel to read different files simultaneously."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute or relative path to the file",
                },
                "offset": {
                    "type": "integer",
                    "description": "Starting line number (1-indexed). Use for large files to read from specific line",
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of lines to read. Use with offset for large files to read in chunks",
                },
            },
            "required": ["path"],
        }

    async def execute(self, path: str, offset: int | None = None, limit: int | None = None) -> ToolResult:
        """Execute read file."""
        try:
            file_path = Path(path)
            # Resolve relative paths relative to workspace_dir
            if not file_path.is_absolute():
                file_path = self.workspace_dir / file_path

            if not file_path.exists():
                return ToolResult(
                    success=False,
                    content="",
                    error=f"File not found: {path}",
                )

            # Read file content with line numbers
            with open(file_path, encoding="utf-8") as f:
                lines = f.readlines()

            # Apply offset and limit
            start = (offset - 1) if offset else 0
            end = (start + limit) if limit else len(lines)
            if start < 0:
                start = 0
            if end > len(lines):
                end = len(lines)

            selected_lines = lines[start:end]

            # Format with line numbers (1-indexed)
            numbered_lines = []
            for i, line in enumerate(selected_lines, start=start + 1):
                # Remove trailing newline for formatting
                line_content = line.rstrip("\n")
                numbered_lines.append(f"{i:6d}|{line_content}")

            content = "\n".join(numbered_lines)

            # Apply token truncation if needed
            max_tokens = 32000
            content = truncate_text_by_tokens(content, max_tokens)

            return ToolResult(success=True, content=content)
        except Exception as e:
            return ToolResult(success=False, content="", error=str(e))


class WriteTool(Tool):
    """Write content to a file."""

    def __init__(self, workspace_dir: str = "."):
        """Initialize WriteTool with workspace directory.

        Args:
            workspace_dir: Base directory for resolving relative paths
        """
        self.workspace_dir = Path(workspace_dir).absolute()

    @property
    def name(self) -> str:
        return "write_file"

    @property
    def description(self) -> str:
        return (
            "Write content to a file. Will overwrite existing files completely. "
            "For existing files, you should read the file first using read_file. "
            "Prefer editing existing files over creating new ones unless explicitly needed."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute or relative path to the file",
                },
                "content": {
                    "type": "string",
                    "description": "Complete content to write (will replace existing content)",
                },
            },
            "required": ["path", "content"],
        }

    async def execute(self, path: str, content: str) -> ToolResult:
        """Execute write file."""
        try:
            file_path = Path(path)
            # Resolve relative paths relative to workspace_dir
            if not file_path.is_absolute():
                file_path = self.workspace_dir / file_path

            # Create parent directories if they don't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)

            file_path.write_text(content, encoding="utf-8")
            return ToolResult(success=True, content=f"Successfully wrote to {file_path}")
        except Exception as e:
            return ToolResult(success=False, content="", error=str(e))


class EditTool(Tool):
    """Edit file by replacing text."""

    def __init__(self, workspace_dir: str = "."):
        """Initialize EditTool with workspace directory.

        Args:
            workspace_dir: Base directory for resolving relative paths
        """
        self.workspace_dir = Path(workspace_dir).absolute()

    @property
    def name(self) -> str:
        return "edit_file"

    @property
    def description(self) -> str:
        return (
            "Perform exact string replacement in a file. The old_str must match exactly "
            "and appear uniquely in the file, otherwise the operation will fail. "
            "You must read the file first before editing. Preserve exact indentation from the source."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute or relative path to the file",
                },
                "old_str": {
                    "type": "string",
                    "description": "Exact string to find and replace (must be unique in file)",
                },
                "new_str": {
                    "type": "string",
                    "description": "Replacement string (use for refactoring, renaming, etc.)",
                },
            },
            "required": ["path", "old_str", "new_str"],
        }

    async def execute(self, path: str, old_str: str, new_str: str) -> ToolResult:
        """Execute edit file."""
        try:
            file_path = Path(path)
            # Resolve relative paths relative to workspace_dir
            if not file_path.is_absolute():
                file_path = self.workspace_dir / file_path

            if not file_path.exists():
                return ToolResult(
                    success=False,
                    content="",
                    error=f"File not found: {path}",
                )

            content = file_path.read_text(encoding="utf-8")

            if old_str not in content:
                return ToolResult(
                    success=False,
                    content="",
                    error=f"Text not found in file: {old_str}",
                )

            new_content = content.replace(old_str, new_str)
            file_path.write_text(new_content, encoding="utf-8")

            return ToolResult(success=True, content=f"Successfully edited {file_path}")
        except Exception as e:
            return ToolResult(success=False, content="", error=str(e))
