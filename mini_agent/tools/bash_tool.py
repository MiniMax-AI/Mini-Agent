"""Bash command execution tool."""

import asyncio
import subprocess
from typing import Any, Dict

from .base import Tool, ToolResult


class BashTool(Tool):
    """Execute bash commands."""

    @property
    def name(self) -> str:
        return "bash"

    @property
    def description(self) -> str:
        return "Execute a bash command and return the output."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The bash command to execute",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds (default: 60)",
                    "default": 60,
                },
            },
            "required": ["command"],
        }

    async def execute(self, command: str, timeout: int = 60) -> ToolResult:
        """Execute bash command."""
        try:
            # Run command with timeout
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                return ToolResult(
                    success=False,
                    content="",
                    error=f"Command timed out after {timeout} seconds",
                )

            # Decode output
            stdout_text = stdout.decode("utf-8", errors="replace")
            stderr_text = stderr.decode("utf-8", errors="replace")

            # Combine stdout and stderr
            output = stdout_text
            if stderr_text:
                output += f"\n[stderr]:\n{stderr_text}"

            # Check return code
            if process.returncode == 0:
                return ToolResult(success=True, content=output or "(no output)")
            else:
                return ToolResult(
                    success=False,
                    content=output,
                    error=f"Command failed with exit code {process.returncode}",
                )

        except Exception as e:
            return ToolResult(success=False, content="", error=str(e))
