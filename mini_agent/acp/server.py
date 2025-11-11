"""ACP server entry point for Mini-Agent.

This module provides the main entry point for running Mini-Agent
as an ACP server, communicating over stdin/stdout with ACP clients.
"""

import asyncio
import logging
from pathlib import Path

from acp import AgentSideConnection, stdio_streams

from mini_agent.acp.agent import MiniMaxACPAgent
from mini_agent.config import Config
from mini_agent.llm import LLMClient
from mini_agent.tools.bash_tool import BashTool, BashOutputTool, BashKillTool
from mini_agent.tools.file_tools import ReadTool, WriteTool, EditTool
from mini_agent.tools.mcp_loader import load_mcp_tools_async
from mini_agent.tools.skill_tool import create_skill_tools
from mini_agent.acp import schema_fix  # noqa: F401 - ensure monkeypatch is applied on import

logger = logging.getLogger(__name__)


def load_system_prompt(config: Config) -> str:
    """Load system prompt from file.

    Args:
        config: Configuration object

    Returns:
        System prompt text
    """
    try:
        with open(config.agent.system_prompt_path, encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.warning("Failed to load system prompt: %s", e)
        return "You are a helpful AI assistant."


def initialize_tools(config: Config, workspace_dir: Path) -> list:
    """Initialize all available tools.

    Args:
        config: Configuration object
        workspace_dir: Default workspace directory

    Returns:
        List of initialized tools
    """
    tools = []

    # Bash tools
    if config.tools.enable_bash:
        tools.extend([BashTool(), BashOutputTool(), BashKillTool()])
        logger.info("Loaded bash tools")

    # File tools
    if config.tools.enable_file_tools:
        tools.extend([
            ReadTool(workspace_dir),
            WriteTool(workspace_dir),
            EditTool(workspace_dir),
        ])
        logger.info("Loaded file tools")

    # MCP tools (async, will need to be awaited separately)
    # Note: For now, skipping MCP tools in ACP mode
    # TODO: Properly integrate async MCP loading
    if config.tools.enable_mcp:
        logger.info("MCP tools loading not yet implemented in ACP mode")

    # Skills
    if config.tools.enable_skills:
        try:
            # create_skill_tools returns (tools: list[Tool], loader: Optional[SkillLoader])
            skill_tools, _ = create_skill_tools(config.tools.skills_dir)
            tools.extend(skill_tools)
            logger.info("Loaded %d skills", len(skill_tools))
        except Exception as e:
            logger.warning("Failed to load skills: %s", e)

    return tools


async def run_acp_server(config: Config | None = None) -> None:
    """Run Mini-Agent as an ACP server.

    This is the main entry point for ACP mode. It:
    1. Loads configuration
    2. Initializes LLM client and tools
    3. Creates ACP connection over stdin/stdout
    4. Runs the agent loop

    Args:
        config: Optional configuration (will load from files if not provided)
    """
    # Load config if not provided
    if config is None:
        config = Config.load()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    logger.info("Starting Mini-Agent ACP server")
    logger.info("API Base: %s", config.llm.api_base)
    logger.info("Model: %s", config.llm.model)

    # Initialize LLM client
    llm_client = LLMClient(
        api_key=config.llm.api_key,
        api_base=config.llm.api_base,
        model=config.llm.model,
        retry_config=config.llm.retry,
    )

    # Initialize tools
    workspace_dir = Path(config.agent.workspace_dir).expanduser()
    tools = initialize_tools(config, workspace_dir)
    logger.info("Initialized %d tools", len(tools))

    # Load system prompt
    system_prompt = load_system_prompt(config)

    # Create ACP connection
    logger.info("Waiting for ACP client connection...")
    reader, writer = await stdio_streams()

    # Create agent connection
    AgentSideConnection(
        lambda conn: MiniMaxACPAgent(conn, llm_client, tools, system_prompt),
        writer,
        reader,
    )

    logger.info("ACP server running, waiting for requests...")

    # Keep server running
    await asyncio.Event().wait()


def main() -> None:
    """Main entry point for ACP server CLI."""
    asyncio.run(run_acp_server())


if __name__ == "__main__":
    main()
