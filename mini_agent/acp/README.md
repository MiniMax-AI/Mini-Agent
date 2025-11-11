# ACP (Agent Client Protocol) Support for Mini-Agent

This module provides ACP support for Mini-Agent, allowing it to communicate with ACP-compatible clients (like Zed) over stdin/stdout using JSON-RPC.

## Overview

The ACP integration is designed to be:
- **Modular**: Separate from core agent logic, easy to maintain
- **Minimal**: Uses the official `agent-client-protocol` Python SDK
- **Simple**: Clean abstractions with clear separation of concerns

## Architecture

```
mini_agent/acp/
├── __init__.py      # Module exports
├── agent.py         # ACP Agent implementation
├── session.py       # Session management
├── converter.py     # Message format conversion
├── server.py        # ACP server entry point
└── README.md        # This file
```

### Components

#### agent.py - MiniMaxACPAgent
Implements the ACP `Agent` protocol, bridging between ACP clients and Mini-Agent's internal implementation.

**Features:**
- Multiple concurrent sessions support
- Real-time streaming updates via `sessionUpdate` notifications
- Tool execution with progress tracking
- MiniMax-specific features (thinking blocks)
- Graceful error handling

**Key Methods:**
- `initialize()` - Protocol handshake and capability negotiation
- `newSession()` - Create new conversation session
- `prompt()` - Process user input and generate responses
- `cancel()` - Cancel ongoing operations

#### session.py - SessionManager
Manages multiple concurrent ACP sessions, each with its own:
- Message history
- Working directory
- Agent instance
- MCP server configuration
- Cancellation event

#### converter.py - Message Format Conversion
Handles conversion between ACP content blocks and Mini-Agent's message format:
- ACP content blocks (text, image, resource) → Mini-Agent messages
- Mini-Agent messages → ACP content blocks
- Tool calls format conversion

#### server.py - Entry Point
Main entry point for running Mini-Agent as an ACP server:
- Configuration loading
- Tool initialization
- ACP connection setup over stdin/stdout
- Event loop management

## Usage

### As a Standalone Server

```bash
# Install Mini-Agent with ACP support
pip install mini-agent

# Run the ACP server
mini-agent-acp
```

The server will:
1. Load configuration from `~/.mini-agent/config/config.yaml`
2. Initialize tools and LLM client
3. Wait for ACP client connections on stdin/stdout

### With Zed Editor

Zed speaks ACP over stdio. Point Zed directly at your Mini‑Agent executable (ideally the virtualenv path) to ensure it runs the same version you installed locally.

Steps:
- Open the Agent Panel (cmd-?) → New External Agent → ACP.
- Command: `/absolute/path/to/venv/bin/mini-agent-acp`
- Optional: set Working Directory to your project path.
- Start a thread. You should see streaming updates for thoughts, messages, and tools.

Verifying the version Zed runs:
- Use a small wrapper to print version + module path, then exec Mini‑Agent:
  - Command: `/bin/bash`
  - Args: `-lc`, `echo 'mini-agent:' $(python -c 'import importlib.metadata as m; print(m.version("mini-agent"))') 'at' $(python -c 'import mini_agent; print(mini_agent.__file__)') >&2; exec /absolute/path/to/venv/bin/mini-agent-acp`

Configuration locations (searched in order):
1) `mini_agent/config/config.yaml` (development)
2) `~/.mini-agent/config/config.yaml` (recommended for API keys)
3) Installed package config

Security: never commit secrets. Keep keys in `~/.mini-agent/config/config.yaml`. The repository ignores `config.yaml` by default.

### Programmatically

```python
import asyncio
from mini_agent.acp import run_acp_server
from mini_agent.config import Config

# Run with custom config
config = Config.load()
asyncio.run(run_acp_server(config))
```

## Features

### Streaming Updates
The agent sends real-time updates during execution:
- **User messages**: Echo user input
- **Agent thoughts**: MiniMax thinking blocks (internal reasoning)
- **Agent messages**: Assistant responses
- **Tool calls**: Tool execution progress (pending → in_progress → completed/failed)

### Tool Execution
Tools are executed with streaming updates:
1. Start notification with tool name and arguments
2. Progress updates during execution
3. Completion notification with results or errors

### Concurrent Sessions
Multiple sessions can run concurrently, each with:
- Isolated message history
- Separate working directory
- Independent agent instance
- Session-specific MCP servers

### Error Handling
Graceful error handling:
- Tool execution errors are caught and reported
- LLM errors are handled with appropriate notifications
- Session cancellation is supported
- Connection errors are logged

## MiniMax Integration

The ACP implementation handles MiniMax's unique features:

### Interleaved Thinking
MiniMax returns thinking blocks interleaved with content:
```python
{
  "type": "thinking",
  "thinking": "Internal reasoning..."
}
```
These are streamed to the client as `update_agent_thought` notifications.

### Tool Call Format
MiniMax uses Anthropic-compatible tool calls:
```python
{
  "id": "call_123",
  "type": "function",
  "function": {
    "name": "read_file",
    "arguments": {"path": "file.txt"}
  }
}
```

## Configuration

ACP server uses the standard Mini-Agent configuration:

```yaml
# ~/.mini-agent/config/config.yaml
llm:
  api_key: "your-api-key"
  api_base: "https://api.minimax.io/anthropic"
  model: "MiniMax-M2"

agent:
  max_steps: 10
  workspace_dir: "."
  system_prompt_path: "~/.mini-agent/config/system_prompt.md"

tools:
  enable_file_tools: true
  enable_bash: true
  enable_mcp: true
  mcp_config_path: "~/.mini-agent/config/mcp.json"
```

## Development

### Testing
```bash
# Install in development mode
pip install -e .

# Run tests
pytest tests/

# Test with a simple ACP client
python -m acp.examples.client mini-agent-acp
```

### Debugging
Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

The agent logs:
- Session creation and management
- Message conversions
- Tool execution
- Errors and warnings

## Protocol Compliance

This implementation follows the [Agent Client Protocol](https://agentclientprotocol.com/) specification:

- ✅ JSON-RPC 2.0 over stdin/stdout
- ✅ Initialize handshake
- ✅ Session management (create, prompt, cancel)
- ✅ Real-time streaming via `sessionUpdate` notifications
- ✅ Tool execution with progress tracking
- ✅ Stop reasons map to ACP enum values (`end_turn`, `max_tokens`, `max_turn_requests`, `refusal`, `cancelled`)
- ✅ Bidirectional requests (agent → client)
- ⚠️ Session persistence (not yet implemented)
- ⚠️ Mode switching (not yet implemented)
- ⚠️ Permission requests (planned)

## Future Enhancements

Planned features:
- [ ] Session persistence (`loadSession` support)
- [ ] Mode switching (code, chat, plan modes)
- [ ] Permission requests for tool execution
- [ ] File I/O via ACP file methods (`fs/read_text_file`, `fs/write_text_file`)
- [ ] Terminal integration (`terminal/create`, `terminal/output`)
- [ ] MCP server forwarding from client
- [ ] Multi-model support

## Resources

- [Agent Client Protocol](https://agentclientprotocol.com/)
- [ACP Python SDK](https://github.com/agentclientprotocol/python-sdk)
- [Mini-Agent Documentation](../../README.md)

## License

MIT License - see project root for details.
