# Mini Agent

English | [中文](./README_CN.md)

**Mini Agent** is a minimal yet professional demo project that showcases the best practices for building agents with the MiniMax M2 model. Leveraging an Anthropic-compatible API, it fully supports interleaved thinking to unlock M2's powerful reasoning capabilities for long, complex tasks.

This project comes packed with features designed for a robust and intelligent agent development experience:

*   ✅ **Full Agent Execution Loop**: A complete and reliable foundation with a basic toolset for file system and shell operations.
*   ✅ **Persistent Memory**: An active **Session Note Tool** ensures the agent retains key information across multiple sessions.
*   ✅ **Intelligent Context Management**: Automatically summarizes conversation history to handle contexts up to a configurable token limit, enabling infinitely long tasks.
*   ✅ **Claude Skills Integration**: Comes with 15 professional skills for documents, design, testing, and development.
*   ✅ **MCP Tool Integration**: Natively supports MCP for tools like knowledge graph access and web search.
*   ✅ **ACP Support**: Native support for [Agent Client Protocol](https://agentclientprotocol.com/) for integration with ACP-compatible clients like Zed.
*   ✅ **Comprehensive Logging**: Detailed logs for every request, response, and tool execution for easy debugging.
*   ✅ **Clean & Simple Design**: A beautiful CLI and a codebase that is easy to understand, making it the perfect starting point for building advanced agents.

## Table of Contents

- [Mini Agent](#mini-agent)
  - [Table of Contents](#table-of-contents)
  - [Quick Start](#quick-start)
    - [1. Get API Key](#1-get-api-key)
    - [2. Choose Your Usage Mode](#2-choose-your-usage-mode)
      - [🚀 Quick Start Mode (Recommended for Beginners)](#-quick-start-mode-recommended-for-beginners)
      - [🔧 Development Mode](#-development-mode)
  - [Usage Examples](#usage-examples)
    - [Task Execution](#task-execution)
    - [Using a Claude Skill (e.g., PDF Generation)](#using-a-claude-skill-eg-pdf-generation)
    - [Web Search \& Summarization (MCP Tool)](#web-search--summarization-mcp-tool)
  - [Testing](#testing)
    - [Quick Run](#quick-run)
    - [Test Coverage](#test-coverage)
  - [ACP (Agent Client Protocol) Support](#acp-agent-client-protocol-support)
    - [Features](#features)
    - [Quick Start](#quick-start-1)
    - [Integration with Zed](#integration-with-zed)
  - [Related Documentation](#related-documentation)
  - [Contributing](#contributing)
  - [License](#license)
  - [References](#references)

## Quick Start

### 1. Get API Key

MiniMax provides both global and China platforms. Choose based on your network environment:

| Version    | Platform                                                       | API Base                             |
| ---------- | -------------------------------------------------------------- | ------------------------------------ |
| **Global** | [https://platform.minimax.io](https://platform.minimax.io)     | `https://api.minimax.io/anthropic`   |
| **China**  | [https://platform.minimaxi.com](https://platform.minimaxi.com) | `https://api.minimaxi.com/anthropic` |

**Steps to get API Key:**
1. Visit the corresponding platform to register and login
2. Go to **Account Management > API Keys**
3. Click **"Create New Key"**
4. Copy and save it securely (key is only shown once)

> 💡 **Tip**: Remember the API Base address corresponding to your chosen platform, you'll need it for configuration

### 2. Choose Your Usage Mode

**Prerequisites: Install pipx**

Both usage modes require pipx. If you don't have it installed:

```bash
# macOS
brew install pipx
pipx ensurepath

# Linux
sudo apt install pipx  # Debian/Ubuntu
pipx ensurepath

# After installation, restart your terminal or run:
source ~/.bashrc  # or ~/.zshrc
```

We offer two usage modes - choose based on your needs:

#### 🚀 Quick Start Mode (Recommended for Beginners)

Perfect for users who want to quickly try Mini Agent without cloning the repository or modifying code.

**Installation:**

```bash
# 1. Install directly from GitHub
pipx install git+https://github.com/MiniMax-AI/Mini-Agent.git

# 2. Run setup script (automatically creates config files)
curl -fsSL https://raw.githubusercontent.com/MiniMax-AI/Mini-Agent/main/scripts/setup-config.sh | bash
```

> 💡 **Tip**: If you want to develop locally or modify code, use "Development Mode" below

**Configuration:**

The setup script creates config files in `~/.mini-agent/config/`. Edit the config file:

```bash
# Edit config file
nano ~/.mini-agent/config/config.yaml
```

Fill in your API Key and corresponding API Base:

```yaml
api_key: "YOUR_API_KEY_HERE"          # API Key from step 1
api_base: "https://api.minimax.io/anthropic"  # Global
# api_base: "https://api.minimaxi.com/anthropic"  # China
model: "MiniMax-M2"
```

**Start Using:**

```bash
mini-agent                                    # Use current directory as workspace
mini-agent --workspace /path/to/your/project  # Specify workspace directory
mini-agent --version                          # Check version
```

#### 🔧 Development Mode

For developers who need to modify code, add features, or debug.

**Installation & Configuration:**

```bash
# 1. Clone the repository
git clone https://github.com/MiniMax-AI/Mini-Agent.git
cd Mini-Agent

# 2. Install uv (if you haven't)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Sync dependencies
uv sync

# 4. Initialize Claude Skills (Optional)
git submodule update --init --recursive

# 5. Copy config template
cp mini_agent/config/config-example.yaml mini_agent/config/config.yaml

# 6. Edit config file
vim mini_agent/config/config.yaml  # Or use your preferred editor
```

Fill in your API Key and corresponding API Base:

```yaml
api_key: "YOUR_API_KEY_HERE"          # API Key from step 1
api_base: "https://api.minimax.io/anthropic"  # Global
# api_base: "https://api.minimaxi.com/anthropic"  # China
model: "MiniMax-M2"
max_steps: 100
workspace_dir: "./workspace"
```

> 📖 Full configuration guide: See [config-example.yaml](mini_agent/config/config-example.yaml)

**Run Methods:**

Choose your preferred run method:

```bash
# Method 1: Run as module directly (good for debugging)
uv run python -m mini_agent.cli

# Method 2: Install in editable mode (recommended)
pipx install -e .
# After installation, run from anywhere and code changes take effect immediately
mini-agent
mini-agent --workspace /path/to/your/project
```

> 📖 For more development guidance, see [Development Guide](docs/DEVELOPMENT_GUIDE.md)

> 📖 For more production deployment guidance, see [Production Guide](docs/PRODUCTION_GUIDE.md)

## Usage Examples

Here are a few examples of what Mini Agent can do.

### Task Execution

*In this demo, the agent is asked to create a simple, beautiful webpage and display it in the browser, showcasing the basic tool-use loop.*

![Demo GIF 1: Basic Task Execution](docs/assets/demo1-task-execution.gif "Basic Task Execution Demo")

### Using a Claude Skill (e.g., PDF Generation)

*Here, the agent leverages a Claude Skill to create a professional document (like a PDF or DOCX) based on the user's request, demonstrating its advanced capabilities.*

![Demo GIF 2: Claude Skill Usage](docs/assets/demo2-claude-skill.gif "Claude Skill Usage Demo")

### Web Search & Summarization (MCP Tool)

*This demo shows the agent using its web search tool to find up-to-date information online and summarize it for the user.*

![Demo GIF 3: Web Search](docs/assets/demo3-web-search.gif "Web Search Demo")

## Testing

The project includes comprehensive test cases covering unit tests, functional tests, and integration tests.

### Quick Run

```bash
# Run all tests
pytest tests/ -v

# Run core functionality tests
pytest tests/test_agent.py tests/test_note_tool.py -v
```

### Test Coverage

- ✅ **Unit Tests** - Tool classes, LLM client
- ✅ **Functional Tests** - Session Note Tool, MCP loading
- ✅ **Integration Tests** - Agent end-to-end execution
- ✅ **External Services** - Git MCP Server loading


## ACP (Agent Client Protocol) Support

Mini-Agent supports the [Agent Client Protocol](https://agentclientprotocol.com/), allowing it to integrate seamlessly with ACP-compatible clients like Zed.

### Features

- ✅ **Multiple Concurrent Sessions**: Run multiple conversations simultaneously
- ✅ **Real-time Streaming**: Stream agent thoughts, messages, and tool execution in real-time
- ✅ **Tool Execution**: Execute tools with progress tracking and error handling
- ✅ **MiniMax Integration**: Full support for MiniMax's thinking blocks and unique tool format

### Quick Start

```bash
# Install with ACP support
pip install mini-agent

# Run as ACP server
mini-agent-acp
```

### Integration with Zed

Zed communicates with external agents over ACP via stdio. To use Mini‑Agent in Zed, point Zed to the exact executable you installed (ideally the venv binary):

1) Open the Agent Panel (cmd-?) and create a New External Agent → ACP.
2) Set Command to your venv path, for example:
   - `/Users/sero/projects/Mini-Agent/.venv/bin/mini-agent-acp`
3) Optionally set the working directory to your project path.
4) Start a thread and talk to the agent. Tool progress and results stream in real time.

Tips for consistent versions:
- Prefer the absolute venv path over relying on PATH.
- If needed, wrap the command to print the installed version before exec:
  - Command: `/bin/bash`
  - Args: `-lc`, `echo 'mini-agent:' $(python -c 'import importlib.metadata as m; print(m.version("mini-agent"))') 'at' $(python -c 'import mini_agent; print(mini_agent.__file__)') >&2; exec /Users/sero/projects/Mini-Agent/.venv/bin/mini-agent-acp`

Configuration search order:
- `mini_agent/config/config.yaml` (dev checkout)
- `~/.mini-agent/config/config.yaml` (recommended for keys)
- `<site-packages>/mini_agent/config/config.yaml`

Security: never commit API keys. Use `~/.mini-agent/config/config.yaml` and keep `config.yaml` out of version control (already ignored).

For detailed ACP documentation, see [mini_agent/acp/README.md](mini_agent/acp/README.md).

## Related Documentation

- [Development Guide](docs/DEVELOPMENT_GUIDE.md) - Detailed development and configuration guidance
- [Production Guide](docs/PRODUCTION_GUIDE.md) - Best practices for production deployment
- [ACP Integration](mini_agent/acp/README.md) - Agent Client Protocol implementation details

## Contributing

Issues and Pull Requests are welcome!

- [Contributing Guide](CONTRIBUTING.md) - How to contribute
- [Code of Conduct](CODE_OF_CONDUCT.md) - Community guidelines

## License

This project is licensed under the [MIT License](LICENSE).

## References

- MiniMax API: https://platform.minimaxi.com/document
- MiniMax-M2: https://github.com/MiniMax-AI/MiniMax-M2
- Anthropic API: https://docs.anthropic.com/claude/reference
- Claude Skills: https://github.com/anthropics/skills
- MCP Servers: https://github.com/modelcontextprotocol/servers

---

**⭐ If this project helps you, please give it a Star!**
