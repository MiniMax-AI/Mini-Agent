"""Agent 服务 - 连接 Mini-Agent 核心"""
import sys
from pathlib import Path

# 添加 mini_agent 到 Python 路径
mini_agent_path = Path(__file__).parent.parent.parent.parent / "mini_agent"
if str(mini_agent_path) not in sys.path:
    sys.path.insert(0, str(mini_agent_path.parent))

from mini_agent.agent import Agent
from mini_agent.llm import LLMClient
from mini_agent.schema import LLMProvider, Message as AgentMessage
from mini_agent.tools.file_tools import ReadTool, WriteTool, EditTool
from mini_agent.tools.bash_tool import BashTool, BashOutputTool, BashKillTool
from mini_agent.tools.note_tool import SessionNoteTool

from app.services.history_service import HistoryService
from app.config import get_settings
from typing import List, Dict
from pathlib import Path as PathlibPath

settings = get_settings()


class AgentService:
    """Agent 服务"""

    def __init__(
        self, workspace_dir: PathlibPath, history_service: HistoryService, session_id: str
    ):
        self.workspace_dir = workspace_dir
        self.history_service = history_service
        self.session_id = session_id
        self.agent: Agent | None = None
        self._last_saved_index = 0

    def initialize_agent(self):
        """初始化 Agent"""
        # 根据配置确定 provider
        if settings.llm_provider.lower() == "openai":
            provider = LLMProvider.OPENAI
        else:
            provider = LLMProvider.ANTHROPIC

        # 创建 LLM 客户端
        llm_client = LLMClient(
            api_key=settings.llm_api_key,
            api_base=settings.llm_api_base,
            provider=provider,
            model=settings.llm_model,
        )

        # 加载 system prompt
        system_prompt = self._load_system_prompt()

        # 创建工具列表
        tools = self._create_tools()

        # 创建 Agent
        self.agent = Agent(
            llm_client=llm_client,
            system_prompt=system_prompt,
            tools=tools,
            max_steps=settings.agent_max_steps,
            workspace_dir=str(self.workspace_dir),
            token_limit=settings.agent_token_limit,
        )

        # 从数据库恢复历史
        self._restore_history()

    def _load_system_prompt(self) -> str:
        """加载 system prompt"""
        prompt_file = (
            Path(__file__).parent.parent.parent.parent
            / "mini_agent"
            / "config"
            / "system_prompt.md"
        )
        if prompt_file.exists():
            return prompt_file.read_text(encoding="utf-8")
        return "You are Mini-Agent, an AI assistant."

    def _create_tools(self) -> List:
        """创建工具列表"""
        tools = [
            # 文件工具
            ReadTool(workspace_dir=str(self.workspace_dir)),
            WriteTool(workspace_dir=str(self.workspace_dir)),
            EditTool(workspace_dir=str(self.workspace_dir)),
            # Bash 工具
            BashTool(workspace_dir=str(self.workspace_dir)),
            BashOutputTool(),
            BashKillTool(),
            # 会话笔记工具
            SessionNoteTool(
                memory_file=str(self.workspace_dir / ".agent_memory.json")
            ),
        ]

        # TODO: 添加 Skills
        # TODO: 添加 MCP tools

        return tools

    def _restore_history(self):
        """从数据库恢复对话历史"""
        if not self.agent:
            return

        history = self.history_service.load_session_history(self.session_id)

        # 跳过 system message（index 0）
        for msg_data in history:
            if msg_data["role"] == "user":
                self.agent.messages.append(
                    AgentMessage(role="user", content=msg_data["content"])
                )
            elif msg_data["role"] == "assistant":
                self.agent.messages.append(
                    AgentMessage(
                        role="assistant",
                        content=msg_data["content"],
                        thinking=msg_data.get("thinking"),
                        tool_calls=msg_data.get("tool_calls"),
                    )
                )
            elif msg_data["role"] == "tool":
                self.agent.messages.append(
                    AgentMessage(
                        role="tool",
                        content=msg_data["content"],
                        tool_call_id=msg_data.get("tool_call_id"),
                    )
                )

        self._last_saved_index = len(self.agent.messages)

    async def chat(self, user_message: str) -> Dict:
        """执行对话"""
        if not self.agent:
            raise RuntimeError("Agent not initialized")

        # 保存用户消息
        self.history_service.save_message(
            session_id=self.session_id, role="user", content=user_message
        )

        # 添加到 agent
        self.agent.add_user_message(user_message)

        # 执行 agent
        response = await self.agent.run()

        # 保存 agent 生成的消息
        self._save_new_messages()

        return {"response": response, "message_count": len(self.agent.messages)}

    def _save_new_messages(self):
        """保存新增的消息到数据库"""
        if not self.agent:
            return

        for msg in self.agent.messages[self._last_saved_index :]:
            if msg.role == "assistant":
                self.history_service.save_message(
                    session_id=self.session_id,
                    role="assistant",
                    content=msg.content,
                    thinking=msg.thinking,
                    tool_calls=[tc.dict() for tc in msg.tool_calls]
                    if msg.tool_calls
                    else None,
                )
            elif msg.role == "tool":
                self.history_service.save_message(
                    session_id=self.session_id,
                    role="tool",
                    content=msg.content,
                    tool_call_id=msg.tool_call_id,
                )

        self._last_saved_index = len(self.agent.messages)
