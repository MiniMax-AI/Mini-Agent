"""
Mini Agent - 交互式运行示例

运行方式：
    uv run python main.py
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import List

from mini_agent.agent import Agent
from mini_agent.config import Config
from mini_agent.llm import LLMClient
from mini_agent.tools.base import Tool
from mini_agent.tools.bash_tool import BashTool
from mini_agent.tools.file_tools import EditTool, ReadTool, WriteTool
from mini_agent.tools.mcp_loader import cleanup_mcp_connections, load_mcp_tools_async
from mini_agent.tools.note_tool import SessionNoteTool
from mini_agent.tools.skill_tool import create_skill_tools


# ANSI 颜色代码
class Colors:
    """终端颜色定义"""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # 前景色
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # 亮色
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # 背景色
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"


def print_banner():
    """打印欢迎横幅"""
    print()
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}╔{'═' * 58}╗{Colors.RESET}")
    print(
        f"{Colors.BOLD}{Colors.BRIGHT_CYAN}║{Colors.RESET}  {Colors.BOLD}🤖 Mini Agent - 多轮交互式会话{Colors.RESET}                    {Colors.BOLD}{Colors.BRIGHT_CYAN}║{Colors.RESET}"
    )
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}╚{'═' * 58}╝{Colors.RESET}")
    print()


def print_help():
    """打印帮助信息"""
    help_text = f"""
{Colors.BOLD}{Colors.BRIGHT_YELLOW}可用命令:{Colors.RESET}
  {Colors.BRIGHT_GREEN}/help{Colors.RESET}      - 显示此帮助信息
  {Colors.BRIGHT_GREEN}/clear{Colors.RESET}     - 清除会话历史（保留 system prompt）
  {Colors.BRIGHT_GREEN}/history{Colors.RESET}   - 显示当前会话消息数量
  {Colors.BRIGHT_GREEN}/stats{Colors.RESET}     - 显示会话统计信息
  {Colors.BRIGHT_GREEN}/exit{Colors.RESET}      - 退出程序（也可用 exit, quit, q）

{Colors.BOLD}{Colors.BRIGHT_YELLOW}使用说明:{Colors.RESET}
  - 直接输入你的任务，Agent 会帮你完成
  - Agent 会记住本次会话的所有对话内容
  - 使用 {Colors.BRIGHT_GREEN}/clear{Colors.RESET} 可以开始新的会话
"""
    print(help_text)


def print_session_info(agent: Agent, workspace_dir: Path, model: str):
    """打印会话信息"""
    print(f"{Colors.DIM}┌{'─' * 58}┐{Colors.RESET}")
    print(
        f"{Colors.DIM}│{Colors.RESET} {Colors.BRIGHT_CYAN}会话信息{Colors.RESET}                                             {Colors.DIM}│{Colors.RESET}"
    )
    print(f"{Colors.DIM}├{'─' * 58}┤{Colors.RESET}")
    print(
        f"{Colors.DIM}│{Colors.RESET} 模型: {Colors.BRIGHT_WHITE}{model}{Colors.RESET:<48} {Colors.DIM}│{Colors.RESET}"
    )
    print(
        f"{Colors.DIM}│{Colors.RESET} 工作目录: {Colors.BRIGHT_WHITE}{workspace_dir}{Colors.RESET:<43} {Colors.DIM}│{Colors.RESET}"
    )
    print(
        f"{Colors.DIM}│{Colors.RESET} 消息历史: {Colors.BRIGHT_WHITE}{len(agent.messages)} 条{Colors.RESET:<45} {Colors.DIM}│{Colors.RESET}"
    )
    print(
        f"{Colors.DIM}│{Colors.RESET} 可用工具: {Colors.BRIGHT_WHITE}{len(agent.tools)} 个{Colors.RESET:<45} {Colors.DIM}│{Colors.RESET}"
    )
    print(f"{Colors.DIM}└{'─' * 58}┘{Colors.RESET}")
    print()
    print(
        f"{Colors.DIM}输入 {Colors.BRIGHT_GREEN}/help{Colors.DIM} 查看帮助，输入 {Colors.BRIGHT_GREEN}/exit{Colors.DIM} 退出{Colors.RESET}"
    )
    print()


def print_stats(agent: Agent, session_start: datetime):
    """打印会话统计"""
    duration = datetime.now() - session_start
    hours, remainder = divmod(int(duration.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)

    # 统计不同类型的消息
    user_msgs = sum(1 for m in agent.messages if m.role == "user")
    assistant_msgs = sum(1 for m in agent.messages if m.role == "assistant")
    tool_msgs = sum(1 for m in agent.messages if m.role == "tool")

    print(f"\n{Colors.BOLD}{Colors.BRIGHT_CYAN}会话统计:{Colors.RESET}")
    print(f"{Colors.DIM}{'─' * 40}{Colors.RESET}")
    print(
        f"  会话时长: {Colors.BRIGHT_WHITE}{hours:02d}:{minutes:02d}:{seconds:02d}{Colors.RESET}"
    )
    print(f"  消息总数: {Colors.BRIGHT_WHITE}{len(agent.messages)}{Colors.RESET}")
    print(f"    - 用户消息: {Colors.BRIGHT_GREEN}{user_msgs}{Colors.RESET}")
    print(f"    - 助手回复: {Colors.BRIGHT_BLUE}{assistant_msgs}{Colors.RESET}")
    print(f"    - 工具调用: {Colors.BRIGHT_YELLOW}{tool_msgs}{Colors.RESET}")
    print(f"  可用工具: {Colors.BRIGHT_WHITE}{len(agent.tools)}{Colors.RESET}")
    print(f"{Colors.DIM}{'─' * 40}{Colors.RESET}\n")


async def initialize_tools(config: Config) -> List[Tool]:
    """根据配置初始化工具

    Args:
        config: 配置对象

    Returns:
        工具列表
    """
    tools = []
    workspace_dir = Path(config.agent.workspace_dir)
    workspace_dir.mkdir(exist_ok=True)

    # 1. 基础文件工具
    if config.tools.enable_file_tools:
        tools.extend(
            [
                ReadTool(),
                WriteTool(),
                EditTool(),
            ]
        )
        print(f"{Colors.GREEN}✅ 已加载文件操作工具{Colors.RESET}")

    # 2. Bash 工具
    if config.tools.enable_bash:
        tools.append(BashTool())
        print(f"{Colors.GREEN}✅ 已加载 Bash 工具{Colors.RESET}")

    # 3. 会话笔记工具
    if config.tools.enable_note:
        tools.append(
            SessionNoteTool(memory_file=str(workspace_dir / ".agent_memory.json"))
        )
        print(f"{Colors.GREEN}✅ 已加载会话笔记工具{Colors.RESET}")

    # 4. Claude Skills
    if config.tools.enable_skills:
        print(f"{Colors.BRIGHT_CYAN}正在加载 Claude Skills...{Colors.RESET}")
        try:
            skill_tools = create_skill_tools(config.tools.skills_dir)
            if skill_tools:
                tools.extend(skill_tools)
                print(
                    f"{Colors.GREEN}✅ 已加载 {len(skill_tools)} 个 Skill 工具{Colors.RESET}"
                )
            else:
                print(f"{Colors.YELLOW}⚠️  未找到可用的 Skills{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.YELLOW}⚠️  加载 Skills 失败: {e}{Colors.RESET}")

    # 5. MCP 工具
    if config.tools.enable_mcp:
        print(f"{Colors.BRIGHT_CYAN}正在加载 MCP 工具...{Colors.RESET}")
        try:
            mcp_tools = await load_mcp_tools_async(config.tools.mcp_config_path)
            if mcp_tools:
                tools.extend(mcp_tools)
                print(
                    f"{Colors.GREEN}✅ 已加载 {len(mcp_tools)} 个 MCP 工具{Colors.RESET}"
                )
            else:
                print(f"{Colors.YELLOW}⚠️  未找到可用的 MCP 工具{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.YELLOW}⚠️  加载 MCP 工具失败: {e}{Colors.RESET}")

    print()  # 空行分隔
    return tools


async def main():
    """运行交互式 Agent"""
    session_start = datetime.now()

    # 1. 加载配置
    config_path = Path("mini_agent/config.yaml")

    if not config_path.exists():
        print(f"{Colors.RED}❌ 错误: 配置文件不存在{Colors.RESET}")
        print(
            f"{Colors.YELLOW}请先运行: {Colors.BRIGHT_WHITE}cp mini_agent/config-example.yaml mini_agent/config.yaml{Colors.RESET}"
        )
        print(f"{Colors.YELLOW}然后编辑配置文件填入你的 API Key{Colors.RESET}")
        return

    try:
        config = Config.from_yaml(config_path)
    except FileNotFoundError:
        print(f"{Colors.RED}❌ 错误: 配置文件不存在: {config_path}{Colors.RESET}")
        return
    except ValueError as e:
        print(f"{Colors.RED}❌ 错误: {e}{Colors.RESET}")
        print(f"{Colors.YELLOW}请检查配置文件格式{Colors.RESET}")
        return
    except Exception as e:
        print(f"{Colors.RED}❌ 错误: 加载配置文件失败: {e}{Colors.RESET}")
        return

    # 2. 初始化 LLM 客户端
    from mini_agent.retry import RetryConfig as RetryConfigBase

    # 转换配置格式
    retry_config = RetryConfigBase(
        enabled=config.llm.retry.enabled,
        max_retries=config.llm.retry.max_retries,
        initial_delay=config.llm.retry.initial_delay,
        max_delay=config.llm.retry.max_delay,
        exponential_base=config.llm.retry.exponential_base,
        retryable_exceptions=(Exception,),
    )

    # 创建重试回调函数，用于在终端显示重试信息
    def on_retry(exception: Exception, attempt: int):
        """重试回调函数，显示重试信息"""
        print(
            f"\n{Colors.BRIGHT_YELLOW}⚠️  LLM 调用失败 (第 {attempt} 次): {str(exception)}{Colors.RESET}"
        )
        next_delay = retry_config.calculate_delay(attempt - 1)
        print(
            f"{Colors.DIM}   {next_delay:.1f}秒后进行第 {attempt + 1} 次重试...{Colors.RESET}"
        )

    llm_client = LLMClient(
        api_key=config.llm.api_key,
        api_base=config.llm.api_base,
        model=config.llm.model,
        retry_config=retry_config if config.llm.retry.enabled else None,
    )

    # 设置重试回调
    if config.llm.retry.enabled:
        llm_client.retry_callback = on_retry
        print(
            f"{Colors.GREEN}✅ 已启用 LLM 重试机制 (最多重试 {config.llm.retry.max_retries} 次){Colors.RESET}"
        )

    # 3. 初始化工具
    tools = await initialize_tools(config)

    # 4. 加载 System Prompt
    system_prompt = config.get_system_prompt()

    # 5. 创建 Agent
    workspace_dir = Path(config.agent.workspace_dir)
    agent = Agent(
        llm_client=llm_client,
        system_prompt=system_prompt,
        tools=tools,
        max_steps=config.agent.max_steps,
        workspace_dir=str(workspace_dir),
    )

    # 7. 显示欢迎信息
    print_banner()
    print_session_info(agent, workspace_dir, config.llm.model)

    # 8. 交互循环
    while True:
        try:
            # 获取用户输入
            prompt = (
                f"{Colors.BRIGHT_GREEN}You{Colors.RESET} {Colors.DIM}›{Colors.RESET} "
            )
            user_input = input(prompt).strip()

            if not user_input:
                continue

            # 处理命令
            if user_input.startswith("/"):
                command = user_input.lower()

                if command in ["/exit", "/quit", "/q"]:
                    print(
                        f"\n{Colors.BRIGHT_YELLOW}👋 再见！感谢使用 Mini Agent{Colors.RESET}\n"
                    )
                    print_stats(agent, session_start)
                    break

                elif command == "/help":
                    print_help()
                    continue

                elif command == "/clear":
                    # 清除消息历史，但保留 system prompt
                    old_count = len(agent.messages)
                    agent.messages = [agent.messages[0]]  # 只保留 system message
                    print(
                        f"{Colors.GREEN}✅ 已清除 {old_count - 1} 条消息，开始新会话{Colors.RESET}\n"
                    )
                    continue

                elif command == "/history":
                    print(
                        f"\n{Colors.BRIGHT_CYAN}当前会话消息数: {Colors.BRIGHT_WHITE}{len(agent.messages)}{Colors.RESET}\n"
                    )
                    continue

                elif command == "/stats":
                    print_stats(agent, session_start)
                    continue

                else:
                    print(f"{Colors.RED}❌ 未知命令: {user_input}{Colors.RESET}")
                    print(f"{Colors.DIM}输入 /help 查看可用命令{Colors.RESET}\n")
                    continue

            # 普通对话 - 退出判断
            if user_input.lower() in ["exit", "quit", "q"]:
                print(
                    f"\n{Colors.BRIGHT_YELLOW}👋 再见！感谢使用 Mini Agent{Colors.RESET}\n"
                )
                print_stats(agent, session_start)
                break

            # 运行 Agent
            print(
                f"\n{Colors.BRIGHT_BLUE}Agent{Colors.RESET} {Colors.DIM}›{Colors.RESET} {Colors.DIM}思考中...{Colors.RESET}\n"
            )
            agent.add_user_message(user_input)
            _ = await agent.run()
            print(f"\n{Colors.DIM}{'─' * 60}{Colors.RESET}\n")

        except KeyboardInterrupt:
            print(
                f"\n\n{Colors.BRIGHT_YELLOW}👋 检测到中断信号，正在退出...{Colors.RESET}\n"
            )
            print_stats(agent, session_start)
            break

        except Exception as e:
            print(f"\n{Colors.RED}❌ 错误: {e}{Colors.RESET}")
            print(f"{Colors.DIM}{'─' * 60}{Colors.RESET}\n")

    # 9. 清理 MCP 连接
    try:
        print(f"{Colors.BRIGHT_CYAN}正在清理 MCP 连接...{Colors.RESET}")
        await cleanup_mcp_connections()
        print(f"{Colors.GREEN}✅ 清理完成{Colors.RESET}\n")
    except Exception as e:
        print(f"{Colors.YELLOW}清理时出现错误（可忽略）: {e}{Colors.RESET}\n")


if __name__ == "__main__":
    asyncio.run(main())
