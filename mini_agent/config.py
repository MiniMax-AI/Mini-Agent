"""配置管理模块

提供统一的配置加载和管理功能
"""

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class RetryConfig:
    """重试配置"""

    enabled: bool = True
    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0


@dataclass
class LLMConfig:
    """LLM 配置"""

    api_key: str
    api_base: str = "https://api.minimax.io/anthropic"
    model: str = "MiniMax-M2"
    retry: RetryConfig = None

    def __post_init__(self):
        """初始化后处理"""
        if self.retry is None:
            self.retry = RetryConfig()


@dataclass
class AgentConfig:
    """Agent 配置"""

    max_steps: int = 50
    workspace_dir: str = "./workspace"
    system_prompt_path: str = "system_prompt.txt"


@dataclass
class ToolsConfig:
    """工具配置"""

    # 基础工具（文件操作、bash）
    enable_file_tools: bool = True
    enable_bash: bool = True
    enable_note: bool = True

    # Skills
    enable_skills: bool = True
    skills_dir: str = "./skills"

    # MCP 工具
    enable_mcp: bool = True
    mcp_config_path: str = "mcp.json"


@dataclass
class Config:
    """主配置类"""

    llm: LLMConfig
    agent: AgentConfig
    tools: ToolsConfig

    @classmethod
    def from_yaml(cls, config_path: str | Path) -> "Config":
        """从 YAML 文件加载配置

        Args:
            config_path: 配置文件路径

        Returns:
            Config 实例

        Raises:
            FileNotFoundError: 配置文件不存在
            ValueError: 配置格式错误或缺少必要字段
        """
        config_path = Path(config_path)

        if not config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data:
            raise ValueError("配置文件为空")

        # 解析 LLM 配置
        if "api_key" not in data:
            raise ValueError("配置文件缺少必要字段: api_key")

        if not data["api_key"] or data["api_key"] == "YOUR_API_KEY_HERE":
            raise ValueError("请配置有效的 API Key")

        # 解析重试配置
        retry_data = data.get("retry", {})
        retry_config = RetryConfig(
            enabled=retry_data.get("enabled", True),
            max_retries=retry_data.get("max_retries", 3),
            initial_delay=retry_data.get("initial_delay", 1.0),
            max_delay=retry_data.get("max_delay", 60.0),
            exponential_base=retry_data.get("exponential_base", 2.0),
        )

        llm_config = LLMConfig(
            api_key=data["api_key"],
            api_base=data.get("api_base", "https://api.minimax.io/anthropic"),
            model=data.get("model", "MiniMax-M2"),
            retry=retry_config,
        )

        # 解析 Agent 配置
        agent_config = AgentConfig(
            max_steps=data.get("max_steps", 50),
            workspace_dir=data.get("workspace_dir", "./workspace"),
            system_prompt_path=data.get("system_prompt_path", "system_prompt.txt"),
        )

        # 解析工具配置
        tools_data = data.get("tools", {})
        tools_config = ToolsConfig(
            enable_file_tools=tools_data.get("enable_file_tools", True),
            enable_bash=tools_data.get("enable_bash", True),
            enable_note=tools_data.get("enable_note", True),
            enable_skills=tools_data.get("enable_skills", True),
            skills_dir=tools_data.get("skills_dir", "./skills"),
            enable_mcp=tools_data.get("enable_mcp", True),
            mcp_config_path=tools_data.get("mcp_config_path", "mcp.json"),
        )

        return cls(
            llm=llm_config,
            agent=agent_config,
            tools=tools_config,
        )

    def get_system_prompt(self) -> str:
        """获取 system prompt

        Returns:
            system prompt 内容，如果文件不存在则返回默认值
        """
        prompt_path = Path(self.agent.system_prompt_path)

        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8")

        return "你是一个智能助手，可以帮助用户完成各种任务。"
