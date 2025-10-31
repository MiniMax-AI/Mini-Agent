"""Core Agent implementation."""

import json
from pathlib import Path
from typing import Dict, List

from .llm import LLMClient, LLMResponse, Message
from .tools.base import Tool, ToolResult


# ANSI 颜色代码
class Colors:
    """终端颜色定义"""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # 前景色
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"

    # 亮色
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"


class Agent:
    """Single agent with basic tools and MCP support."""

    def __init__(
        self,
        llm_client: LLMClient,
        system_prompt: str,
        tools: List[Tool],
        max_steps: int = 50,
        workspace_dir: str = "./workspace",
        max_messages: int = 20,  # 最大消息数，防止 context 超限
    ):
        self.llm = llm_client
        self.system_prompt = system_prompt
        self.tools = {tool.name: tool for tool in tools}
        self.max_steps = max_steps
        self.max_messages = max_messages
        self.workspace_dir = Path(workspace_dir)

        # Ensure workspace exists
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

        # Initialize message history
        self.messages: List[Message] = [Message(role="system", content=system_prompt)]

    def add_user_message(self, content: str):
        """Add a user message to history."""
        self.messages.append(Message(role="user", content=content))

    def _truncate_messages(self):
        """简单的消息截断：保留 system prompt + 最近的消息

        策略：
        - 永远保留第一条 system prompt
        - 保留最近的 (max_messages - 1) 条消息
        - 当消息数超过 max_messages 时触发截断
        """
        if len(self.messages) > self.max_messages:
            self.messages = [
                self.messages[0],  # system prompt
                *self.messages[-(self.max_messages - 1) :],  # 最近的消息
            ]

    async def run(self) -> str:
        """Execute agent loop until task is complete or max steps reached."""
        step = 0

        while step < self.max_steps:
            # 截断消息历史，防止 context 超限
            self._truncate_messages()

            # 步骤标题
            print(f"\n{Colors.DIM}╭{'─' * 58}╮{Colors.RESET}")
            print(
                f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}{Colors.BRIGHT_CYAN}💭 Step {step + 1}/{self.max_steps}{Colors.RESET}{' ' * (49 - len(f'Step {step + 1}/{self.max_steps}'))}{Colors.DIM}│{Colors.RESET}"
            )
            print(f"{Colors.DIM}╰{'─' * 58}╯{Colors.RESET}")

            # Get tool schemas
            tool_schemas = [tool.to_schema() for tool in self.tools.values()]

            # Call LLM
            try:
                response = await self.llm.generate(
                    messages=self.messages, tools=tool_schemas
                )
            except Exception as e:
                # 检查是否是重试耗尽错误
                from .retry import RetryExhaustedError

                if isinstance(e, RetryExhaustedError):
                    error_msg = (
                        f"LLM 调用失败，已重试 {e.attempts} 次\n"
                        f"最后的错误: {str(e.last_exception)}"
                    )
                    print(
                        f"\n{Colors.BRIGHT_RED}❌ 重试失败:{Colors.RESET} {error_msg}"
                    )
                else:
                    error_msg = f"LLM call failed: {str(e)}"
                    print(f"\n{Colors.BRIGHT_RED}❌ Error:{Colors.RESET} {error_msg}")
                return error_msg

            # Add assistant message
            assistant_msg = Message(
                role="assistant",
                content=response.content,
                tool_calls=response.tool_calls,
            )
            self.messages.append(assistant_msg)

            # Print thinking if present
            if response.thinking:
                print(f"\n{Colors.BOLD}{Colors.MAGENTA}🧠 Thinking:{Colors.RESET}")
                print(f"{Colors.DIM}{response.thinking}{Colors.RESET}")

            # Print assistant response
            if response.content:
                print(f"\n{Colors.BOLD}{Colors.BRIGHT_BLUE}🤖 Assistant:{Colors.RESET}")
                print(f"{Colors.BRIGHT_WHITE}{response.content}{Colors.RESET}")

            # Check if task is complete (no tool calls)
            if not response.tool_calls:
                print(f"\n{Colors.BOLD}{Colors.BRIGHT_GREEN}{'─' * 60}{Colors.RESET}")
                print(
                    f"{Colors.BOLD}{Colors.BRIGHT_GREEN}✨ Task Complete!{Colors.RESET}"
                )
                print(f"{Colors.BOLD}{Colors.BRIGHT_GREEN}{'─' * 60}{Colors.RESET}")
                return response.content

            # Execute tool calls
            for tool_call in response.tool_calls:
                tool_call_id = tool_call["id"]
                function_name = tool_call["function"]["name"]
                arguments = json.loads(tool_call["function"]["arguments"])

                # Tool call header
                print(
                    f"\n{Colors.BRIGHT_YELLOW}🔧 Tool Call:{Colors.RESET} {Colors.BOLD}{Colors.CYAN}{function_name}{Colors.RESET}"
                )

                # Arguments (格式化显示)
                print(f"{Colors.DIM}   Arguments:{Colors.RESET}")
                args_json = json.dumps(arguments, indent=2, ensure_ascii=False)
                for line in args_json.split("\n"):
                    print(f"   {Colors.DIM}{line}{Colors.RESET}")

                # Execute tool
                if function_name not in self.tools:
                    result = ToolResult(
                        success=False,
                        content="",
                        error=f"Unknown tool: {function_name}",
                    )
                else:
                    tool = self.tools[function_name]
                    result = await tool.execute(**arguments)

                # Print result
                if result.success:
                    result_text = result.content
                    if len(result_text) > 300:
                        result_text = (
                            result_text[:300] + f"{Colors.DIM}...{Colors.RESET}"
                        )
                    print(f"{Colors.BRIGHT_GREEN}✓ Result:{Colors.RESET} {result_text}")
                else:
                    print(
                        f"{Colors.BRIGHT_RED}✗ Error:{Colors.RESET} {Colors.RED}{result.error}{Colors.RESET}"
                    )

                # Add tool result message
                tool_msg = Message(
                    role="tool",
                    content=result.content
                    if result.success
                    else f"Error: {result.error}",
                    tool_call_id=tool_call_id,
                    name=function_name,
                )
                self.messages.append(tool_msg)

            step += 1

        # Max steps reached
        error_msg = f"Task couldn't be completed after {self.max_steps} steps."
        print(f"\n{Colors.BRIGHT_YELLOW}⚠️  {error_msg}{Colors.RESET}")
        return error_msg

    def get_history(self) -> List[Message]:
        """Get message history."""
        return self.messages.copy()
