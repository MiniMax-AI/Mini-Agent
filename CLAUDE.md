# CLAUDE.md - AI Assistant Guide for Mini Agent

This document provides comprehensive guidance for AI assistants (like Claude) working with the Mini Agent codebase. It covers the project structure, development workflows, key conventions, and best practices.

## Project Overview

**Mini Agent** is a minimal yet professional demo project showcasing best practices for building agents with the MiniMax M2 model. It uses an Anthropic-compatible API and fully supports interleaved thinking for complex, long-running tasks.

### Key Features

- Full agent execution loop with basic file system and shell operation tools
- Persistent memory via Session Note Tool
- Intelligent context management with automatic conversation summarization
- Claude Skills integration (15 professional skills for documents, design, testing, development)
- MCP (Model Context Protocol) tool integration
- Comprehensive logging for debugging
- Multi-provider LLM support (Anthropic and OpenAI protocols)

### Technology Stack

- **Language**: Python 3.10+
- **Package Manager**: uv (modern Python package manager)
- **Testing**: pytest with asyncio support
- **Dependencies**: httpx, pydantic, pyyaml, tiktoken, prompt-toolkit, mcp, anthropic, openai
- **Build System**: setuptools

## Repository Structure

```
Mini-Agent/
├── mini_agent/                 # Core source code
│   ├── __init__.py
│   ├── agent.py                # Main agent execution loop
│   ├── cli.py                  # Command-line interface with prompt_toolkit
│   ├── config.py               # Configuration loading logic
│   ├── logger.py               # Comprehensive logging system
│   ├── retry.py                # Retry mechanism with exponential backoff
│   ├── llm/                    # LLM client abstraction
│   │   ├── base.py             # Abstract base class for LLM clients
│   │   ├── anthropic_client.py # Anthropic API implementation
│   │   ├── openai_client.py    # OpenAI API implementation
│   │   └── llm_wrapper.py      # LLMClient factory
│   ├── schema/                 # Data models
│   │   └── schema.py           # Pydantic models for messages, responses, etc.
│   ├── tools/                  # Tool implementations
│   │   ├── base.py             # Base Tool class and ToolResult
│   │   ├── file_tools.py       # ReadTool, WriteTool, EditTool
│   │   ├── bash_tool.py        # BashTool, BashOutputTool, BashKillTool
│   │   ├── note_tool.py        # SessionNoteTool for persistent memory
│   │   ├── skill_tool.py       # Skill tools (get_skill)
│   │   ├── skill_loader.py     # Loads Claude Skills from submodule
│   │   └── mcp_loader.py       # MCP server integration
│   ├── skills/                 # Claude Skills (git submodule)
│   ├── utils/                  # Utility functions
│   │   └── terminal_utils.py   # Terminal display width calculations
│   └── config/                 # Configuration files
│       ├── config-example.yaml # Configuration template
│       ├── system_prompt.md    # System prompt for the agent
│       └── mcp.json            # MCP server configuration
├── tests/                      # Test suite
│   ├── test_agent.py           # Agent integration tests
│   ├── test_llm.py             # LLM client tests
│   ├── test_note_tool.py       # Session Note Tool tests
│   ├── test_skill_tool.py      # Skill tool tests
│   ├── test_mcp.py             # MCP loading tests
│   └── ...
├── docs/                       # Documentation
│   ├── DEVELOPMENT_GUIDE.md    # Detailed development guide
│   └── PRODUCTION_GUIDE.md     # Production deployment guide
├── scripts/                    # Setup and utility scripts
├── examples/                   # Example usage
├── workspace/                  # Default workspace directory (gitignored)
├── pyproject.toml             # Project configuration and dependencies
├── uv.lock                    # Locked dependencies
├── README.md                  # Main documentation
└── CONTRIBUTING.md            # Contribution guidelines
```

## Core Architecture

### 1. Agent Execution Loop

**File**: `mini_agent/agent.py`

The `Agent` class implements the core execution loop:

- **Message Management**: Maintains conversation history with automatic token counting
- **Context Summarization**: Automatically summarizes history when token limit is exceeded (default: 80,000 tokens)
- **Tool Execution**: Manages tool calls and results
- **Step Limiting**: Prevents infinite loops with configurable max_steps (default: 100)
- **Workspace Management**: Handles workspace directory and path resolution

**Key Methods**:
- `run(task: str)`: Main execution loop for a task
- `add_user_message(content: str)`: Add user message to history
- `_estimate_tokens()`: Accurate token counting using tiktoken
- `_summarize_history()`: Intelligent context compression

### 2. LLM Client Abstraction

**Files**: `mini_agent/llm/`

The LLM layer has been abstracted to support multiple providers:

- **`base.py`**: Defines `LLMClientBase` abstract interface
- **`anthropic_client.py`**: Anthropic Messages API implementation
- **`openai_client.py`**: OpenAI Chat Completions API implementation
- **`llm_wrapper.py`**: Factory that creates appropriate client based on configuration

**Key Features**:
- Provider-agnostic interface
- Automatic API endpoint construction (appends `/anthropic` or `/v1`)
- Retry mechanism with exponential backoff
- Thinking block support (for models that support it)
- Tool calling standardization

**Configuration**:
```yaml
provider: "anthropic"  # or "openai"
api_key: "YOUR_API_KEY"
api_base: "https://api.minimax.io"
model: "MiniMax-M2"
```

### 3. Tools System

**Files**: `mini_agent/tools/`

All tools inherit from the `Tool` base class in `base.py`:

**Tool Interface**:
```python
class Tool:
    @property
    def name(self) -> str: ...

    @property
    def description(self) -> str: ...

    @property
    def parameters(self) -> dict[str, Any]: ...

    async def execute(self, *args, **kwargs) -> ToolResult: ...

    def to_schema(self) -> dict: ...  # Anthropic format
    def to_openai_schema(self) -> dict: ...  # OpenAI format
```

**Built-in Tools**:
- **ReadTool**: Read file contents with optional line range
- **WriteTool**: Create or overwrite files
- **EditTool**: Edit existing files using old/new string replacement
- **BashTool**: Execute bash commands with timeout
- **BashOutputTool**: Read output from background bash processes
- **BashKillTool**: Kill background bash processes
- **SessionNoteTool**: Persistent note-taking for session memory
- **get_skill**: Load Claude Skills dynamically

### 4. Configuration System

**File**: `mini_agent/config.py`

Configuration is loaded from YAML files in priority order:
1. `mini_agent/config/config.yaml` (development mode)
2. `~/.mini-agent/config/config.yaml` (user config)
3. Package installation directory config

**Key Configuration Options**:
- `api_key`: MiniMax API key
- `api_base`: API endpoint URL
- `model`: Model name (e.g., "MiniMax-M2")
- `provider`: LLM provider ("anthropic" or "openai")
- `max_steps`: Maximum execution steps (default: 100)
- `workspace_dir`: Working directory path
- `system_prompt_path`: Path to system prompt file
- `tools.*`: Tool enable/disable switches
- `retry.*`: Retry configuration

### 5. Skills System

**Files**: `mini_agent/tools/skill_tool.py`, `mini_agent/tools/skill_loader.py`

Claude Skills are loaded from the `skills/` git submodule using **progressive disclosure**:
- **Level 1**: Metadata (name, description) shown at startup
- **Level 2**: Full content loaded via `get_skill(skill_name)`
- **Level 3+**: Additional resources and scripts as needed

**Skills include**: PDF, PPTX, DOCX, XLSX, canvas-design, algorithmic-art, testing, MCP-builder, skill-creator, and more.

### 6. MCP Integration

**File**: `mini_agent/tools/mcp_loader.py`

Model Context Protocol (MCP) servers are configured in `mcp.json` and loaded dynamically. Pre-configured servers include:
- **memory**: Knowledge graph memory system
- **minimax_search**: Web search and browse capabilities

## Development Workflows

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/MiniMax-AI/Mini-Agent.git
cd Mini-Agent

# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies
uv sync

# Initialize Claude Skills (optional)
git submodule update --init --recursive

# Copy config template
cp mini_agent/config/config-example.yaml mini_agent/config/config.yaml

# Edit config.yaml with your API key
# vim mini_agent/config/config.yaml
```

### Running the Agent

```bash
# Method 1: Run as module (good for debugging)
uv run python -m mini_agent.cli

# Method 2: Install in editable mode (recommended)
uv tool install -e .
mini-agent
mini-agent --workspace /path/to/project

# Specify workspace directory
mini-agent --workspace /path/to/your/project
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_agent.py -v

# Run with coverage
pytest tests/ -v --cov=mini_agent

# Run core functionality tests
pytest tests/test_agent.py tests/test_note_tool.py -v
```

### Code Style and Conventions

**Commit Message Format**:
```
<type>(<scope>): <description>

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation changes
- style: Code style (formatting, no logic change)
- refactor: Code refactoring
- test: Test changes
- chore: Build/tooling changes

Examples:
- feat(tools): Add new file search tool
- fix(agent): Fix error handling for tool calls
- refactor(llm): Abstract LLM client for multiple providers
```

**Python Conventions**:
- Type hints for all function parameters and return values
- Docstrings for all classes and public methods
- Use Pydantic for data validation
- Async/await for I/O operations
- pathlib.Path for file paths

### Adding a New Tool

1. Create a new file in `mini_agent/tools/`:
```python
from mini_agent.tools.base import Tool, ToolResult
from typing import Dict, Any

class MyTool(Tool):
    @property
    def name(self) -> str:
        return "my_tool"

    @property
    def description(self) -> str:
        return "Description of what this tool does"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "param1": {
                    "type": "string",
                    "description": "First parameter"
                }
            },
            "required": ["param1"]
        }

    async def execute(self, param1: str) -> ToolResult:
        try:
            # Tool logic here
            return ToolResult(success=True, content="Result")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
```

2. Register the tool in `mini_agent/cli.py`:
```python
from mini_agent.tools.my_tool import MyTool

tools.append(MyTool())
```

3. Add tests in `tests/test_my_tool.py`

### Adding MCP Tools

1. Edit `mini_agent/config/mcp.json`:
```json
{
  "mcpServers": {
    "my_mcp_server": {
      "disabled": false,
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-name"],
      "env": {
        "API_KEY": "your-api-key"
      }
    }
  }
}
```

2. The tools will be automatically loaded at startup if `enable_mcp: true` in config.yaml

## Key Conventions for AI Assistants

### When Working with This Codebase

1. **Always Use uv**: This project uses `uv` for dependency management, not pip
   ```bash
   # Install package
   uv pip install package-name

   # Run Python
   uv run python script.py

   # Sync dependencies
   uv sync
   ```

2. **Respect the Workspace**: All file operations should be relative to `workspace_dir` unless absolute paths are needed

3. **Follow the Tool Pattern**: New tools must inherit from `Tool` and implement all required properties

4. **Test Your Changes**: Always add tests for new features
   ```bash
   pytest tests/test_your_feature.py -v
   ```

5. **Use Type Hints**: All new code should include proper type annotations

6. **Handle Errors Gracefully**: Tools should return `ToolResult(success=False, error=...)` instead of raising exceptions

7. **Configuration Over Code**: Prefer configuration changes over code modifications when possible

8. **Document Your Work**: Update relevant documentation when adding features

### File Modifications

**Before editing files**:
- Always read the file first to understand current implementation
- Use EditTool for existing files, WriteTool only for new files
- Preserve existing style and formatting
- Keep changes minimal and focused

**Path handling**:
- Use `pathlib.Path` for all file operations
- Support both absolute and workspace-relative paths
- Create parent directories before writing files

### Testing Guidelines

**Test coverage areas**:
- Unit tests for individual tools
- Functional tests for tool interactions
- Integration tests for full agent execution
- Mock external API calls in tests

**Test file naming**:
- `test_<module_name>.py` for unit tests
- `test_<feature>_integration.py` for integration tests

### Logging and Debugging

**Log levels**:
- The project uses a custom `AgentLogger` class
- Logs are written to workspace directory
- Enable verbose logging for debugging

**Debugging tips**:
- Check `workspace/*.log` files for detailed execution logs
- Use `/stats` command in interactive mode to see execution statistics
- Enable thinking blocks to see model reasoning

### Common Pitfalls to Avoid

1. **Don't bypass the Tool interface**: All agent capabilities must go through tools
2. **Don't modify git submodules**: The skills directory is a submodule, don't edit it directly
3. **Don't commit config.yaml**: It contains API keys and is gitignored
4. **Don't use pip**: Always use `uv` for package management
5. **Don't skip tests**: Test failures indicate real issues
6. **Don't hard-code paths**: Use workspace_dir from config
7. **Don't ignore token limits**: Context summarization is critical for long tasks

### Working with Git

**Branch naming**:
- Feature branches: `feature/description`
- Bug fixes: `fix/description`
- Claude-specific: `claude/claude-md-<session-id>`

**Before committing**:
1. Run tests: `pytest tests/ -v`
2. Check git status: `git status`
3. Review changes: `git diff`
4. Use conventional commit messages

**Pushing changes**:
```bash
# Push to feature branch with retry
git push -u origin <branch-name>

# If push fails due to network, retry with exponential backoff
```

## Important Files and Their Purpose

| File | Purpose |
|------|---------|
| `mini_agent/agent.py` | Core agent execution loop and context management |
| `mini_agent/cli.py` | Interactive CLI with prompt_toolkit |
| `mini_agent/llm/llm_wrapper.py` | LLM client factory |
| `mini_agent/config.py` | Configuration loading logic |
| `mini_agent/tools/base.py` | Base Tool class - all tools inherit from this |
| `mini_agent/config/config-example.yaml` | Configuration template |
| `mini_agent/config/system_prompt.md` | System prompt for the agent |
| `pyproject.toml` | Project metadata and dependencies |
| `tests/test_agent.py` | Core agent functionality tests |

## API Documentation Links

- **MiniMax API**: https://platform.minimaxi.com/document
- **MiniMax-M2**: https://github.com/MiniMax-AI/MiniMax-M2
- **Anthropic API**: https://docs.anthropic.com/claude/reference
- **Claude Skills**: https://github.com/anthropics/skills
- **MCP Servers**: https://github.com/modelcontextprotocol/servers

## Troubleshooting

### SSL Certificate Errors
If encountering `[SSL: CERTIFICATE_VERIFY_FAILED]`:
- Quick fix for testing: Add `verify=False` to httpx.AsyncClient in `mini_agent/llm/`
- Production solution: `pip install --upgrade certifi`

### Module Not Found
Ensure you're running from the project directory:
```bash
cd Mini-Agent
uv run python -m mini_agent.cli
```

### MCP Tools Not Loading
- Check `mcp.json` configuration
- Ensure `enable_mcp: true` in config.yaml
- Check logs in workspace directory
- Verify MCP server dependencies are installed

### Token Limit Exceeded
- Context summarization should trigger automatically at 80,000 tokens
- Check `token_limit` in config.yaml
- Use `/clear` command to reset context in interactive mode

## Quick Reference for AI Assistants

**When asked to**:
- "Add a feature" → Create new tool in `mini_agent/tools/`, add tests, register in cli.py
- "Fix a bug" → Identify file, read it, make minimal changes, add test case
- "Run tests" → `pytest tests/ -v`
- "Deploy" → See `docs/PRODUCTION_GUIDE.md`
- "Add MCP tool" → Edit `mini_agent/config/mcp.json`
- "Change behavior" → Check if configurable in `config.yaml` first
- "Add skill" → Skills are in submodule, see `docs/DEVELOPMENT_GUIDE.md`

**Remember**:
- This is a Python project using `uv`, not npm/node
- All tools must be async and return ToolResult
- Configuration files are in `mini_agent/config/`
- Tests must pass before committing
- Follow conventional commit messages
- Respect the workspace directory pattern

---

**Last Updated**: 2025-01-17
**Project Version**: 0.1.0
**Maintained by**: Mini Agent Team
