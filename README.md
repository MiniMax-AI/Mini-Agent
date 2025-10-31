# Mini Agent

English | [中文](./README_CN.md)

A **minimal yet professional** single agent demo project that showcases the core execution pipeline and production-grade features of agents.

## Quick Start

### 1. Install Dependencies (using uv)

Recommended to use [uv](https://github.com/astral-sh/uv) as the package manager:

```bash
# Install uv (if you haven't)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies
uv sync
```

Or use the traditional method:

```bash
pip install -e .
```

### 2. Get MiniMax API Key

Visit [MiniMax Open Platform](https://platform.minimaxi.com) to register an account.

Get your API Key:
1. After login, go to **Account Management > API Keys**
2. Click **"Create New Key"**
3. Copy and save it securely (key is only shown once)

### 3. Configure API Key

```bash
# Copy the configuration template
cp mini_agent/config-example.yaml mini_agent/config.yaml

# Edit the config file and fill in your API Key
vim mini_agent/config.yaml
```

Configuration example:

```yaml
api_key: "YOUR_API_KEY_HERE"
api_base: "https://api.minimax.io/anthropic"
model: "MiniMax-M2"
max_steps: 50
workspace_dir: "./workspace"
```

> 📖 Full configuration guide: See [config-example.yaml](mini_agent/config-example.yaml)

### 4. Initialize Claude Skills (Recommended) ⭐

This project integrates Claude's official skills repository via git submodule. Initialize it after first clone:

```bash
# Initialize submodule
git submodule update --init --recursive
```

**Skills provide 20+ professional capabilities**, making the Agent work like a professional:
- 📄 **Document Processing**: Create and edit PDF, DOCX, XLSX, PPTX
- 🎨 **Design Creation**: Generate artwork, posters, GIF animations
- 🧪 **Development & Testing**: Web automation testing (Playwright), MCP server development
- 🏢 **Enterprise Applications**: Internal communication, brand guidelines, theme customization

**✨ This is one of the core highlights of this project**. For details, see the "Configure Skills" section below.

More information:
- [Claude Skills Official Documentation](https://github.com/anthropics/skills)
- [Anthropic Blog: Equipping agents for the real world](https://anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)

### 5. Configure Skills (Optional) ⭐

**Claude Skills** enable the Agent to work like a professional, providing 20+ professional skill packages:

**Core Capabilities:**
- 📄 **Document Processing** - PDF, Word, Excel, PowerPoint
- 🎨 **Design Creation** - Posters, GIF animations, theme design
- 🧪 **Development & Testing** - Playwright testing, MCP server development
- 🏢 **Enterprise Applications** - Brand guidelines, internal communication, theme customization

**Quick Enable:**

```bash
# Initialize Skills (first time)
git submodule update --init --recursive
```

Skills will be automatically loaded, and the Agent will intelligently select appropriate skills based on tasks.

> 📖 Complete Skills list and usage guide: [skills/README.md](./skills/README.md)
> 📚 Official Documentation: https://github.com/anthropics/skills

---

### 6. Configure MCP Tools (Optional)

The project integrates **2 core MCP tools**, configured in `mcp.json`:

#### 🧠 Memory - Knowledge Graph Memory System
- **Function**: Provides long-term memory storage and retrieval based on graph database
- **Status**: Enabled by default (`disabled: false`)
- **Configuration**: No API Key required, works out of the box

#### 🔍 MiniMax Search - Web Search and Browse ⭐
- **Function**: Provides three tools: `search` (search), `parallel_search` (parallel search), `browse` (intelligent browsing)
- **Status**: Disabled by default, needs configuration to enable
- **Configuration Steps**:
  1. Configure environment variables in `mcp.json` under `minimax_search`:
     - `JINA_API_KEY`: For web reading (apply at: https://jina.ai)
     - `SERPER_API_KEY`: For Google search (apply at: https://serpapi.com)
     - `BRAVE_API_KEY`: For Brave search, optional (apply at: https://brave.com/search/api/)
     - `MINIMAX_TOKEN` / `BILLING_TOKEN`: For LLM calls in browsing function
  2. Change `disabled` to `false`

**Local Development**: To use a local version of MiniMax Search, modify `args` to:
```json
["--from", "/path/to/local/minimax-search", "minimax-search"]
```

> 🔗 More MCP Tools: https://github.com/modelcontextprotocol/servers

### 7. Run Examples

**Interactive Mode**

```bash
uv run python main.py
```

Features: Colorful output, multi-turn conversations, session statistics

Common commands: `/help`, `/clear`, `/history`, `/stats`, `/exit`

## Features

### Core Functions
- ✅ **Agent Multi-round Execution Loop**: Complete tool calling pipeline
- ✅ **Basic Tool Set**: Read / Write / Edit files + Bash commands
- ✅ **Session Note Tool**: Agent actively records and retrieves session highlights ⭐
- ✅ **Claude Skills Integration**: 20+ professional skills (documentation, design, testing, development) ⭐💡 🆕
- ✅ **MCP Tool Integration**: Memory (knowledge graph) + MiniMax Search (web search) ⭐ 🆕
- ✅ **MiniMax M2 Model**: Through Anthropic-compatible endpoint

### Advanced Features ⭐
- ✅ **Persistent Notes**: Agent maintains context across sessions and execution chains
- ✅ **Intelligent Recording**: Agent autonomously determines what information needs to be recorded
- ✅ **Multi-round Sessions**: Supports session management, history clearing, statistics, etc. 🆕
- ✅ **Beautiful Interaction**: Colorful terminal output, clear session interface 🆕
- ✅ **Simple yet Complete**: Showcases core functionality, avoids excessive complexity

## Project Structure

```
mini-agent/
├── README.md              # This document
├── mcp.json              # MCP tools configuration (points to external MCP servers) ⭐
├── system_prompt.txt     # System prompt
├── pyproject.toml        # Python project configuration
├── skills/               # Claude Skills (git submodule) 🆕
│   ├── example-skills/   # Official example skills
│   ├── document-skills/  # Document processing skills
│   └── ...
├── mini_agent/
│   ├── config-example.yaml # API configuration example
│   ├── agent.py          # Core Agent
│   ├── llm.py            # LLM Client (Anthropic compatible)
│   ├── config.py         # Configuration loader 🆕
│   └── tools/
│       ├── base.py       # Tool base class
│       ├── file_tools.py # File tools
│       ├── bash_tool.py  # Bash tool
│       ├── note_tool.py  # Session Note tool ⭐
│       ├── mcp_loader.py # MCP loader (supports external servers) ⭐
│       ├── skill_loader.py # Skill loader 🆕
│       └── skill_tool.py # Skill tool 🆕
├── tests/
│   ├── test_agent.py     # Agent integration tests
│   ├── test_llm.py       # LLM tests
│   ├── test_note_tool.py # Session Note Tool tests ⭐
│   ├── test_tools.py     # Tool unit tests
│   ├── test_integration.py # Integration tests
│   ├── test_mcp.py       # MCP tests
│   ├── test_git_mcp.py   # Git MCP loading tests ⭐
│   ├── test_skill_loader.py # Skill Loader tests 🆕
│   ├── test_skill_tool.py   # Skill Tool tests 🆕
│   └── test_session_integration.py # Session integration tests 🆕
├── docs/
│   ├── M2_Agent_Best_Practices_CN.md # M2 Best Practices (Chinese)
│   └── M2_Agent_Best_Practices_EN.md # M2 Best Practices (English)
└── main.py              # Interactive entry point

External MCP Servers:
../minimax-search/        # MiniMax Search MCP Server (independent project) ⭐
├── server.py             # MCP Server entry
├── utils/                # Search and browse implementation
├── pyproject.toml        # Independent project configuration
└── README.md             # Independent documentation
```

## Core Implementation

### 1. Agent Execution Flow

```python
# Simplified core loop (from agent.py)
async def run(self) -> str:
    step = 0
    while step < self.max_steps:
        # 1. Call LLM
        response = await self.llm.generate(messages, tools)

        # 2. If no tool calls, task complete
        if not response.tool_calls:
            return response.content

        # 3. Execute tool calls
        for tool_call in response.tool_calls:
            result = await tool.execute(**arguments)
            self.messages.append(tool_result_message)

        step += 1
```

### 2. Session Note Tool - Session Note Recording ⭐

This is one of the **core highlights** of this demo, showcasing a simple and efficient session memory management approach.

#### Core Concept

Unlike traditional message history management, **Session Note Tool lets the Agent actively decide what needs to be recorded**:

- ❌ **Traditional Method**: Passively saves all conversations, easily exceeds token limits
- ✅ **Session Note Tool**: Agent actively records key points, persistent storage

#### Tool Description

Session Note Tool provides two core functions:

1. **Record Note** (`record_note`): Save important information to persistent storage
   - Supports category tags (e.g., user_preference, project_info)
   - Auto-adds timestamp
   - JSON format storage

2. **Recall Notes** (`recall_notes`): Retrieve previously recorded information
   - Supports filtering by category
   - Returns formatted note list
   - Cross-session access

#### Usage Example

**Agent actively records notes**:

```
User: I'm a Python developer, the project uses Python 3.12, and I prefer clean code

Agent: (actively calls record_note)
→ record_note(
    content="Project uses Python 3.12, prefers clean code style",
    category="user_preference"
  )
```

**Agent recalls notes**:

```
User: (new session) Do you remember my project information?

Agent: (actively calls recall_notes)
→ recall_notes()
→ Gets: "Project uses Python 3.12, prefers clean code style"
→ Answers: "I remember! Your project uses Python 3.12..."
```

#### Note File Format

Notes are stored in JSON format at `workspace/.agent_memory.json`:

```json
[
  {
    "timestamp": "2025-10-24T17:20:50.340607",
    "category": "project_info",
    "content": "project_name=mini-agent, technology=Python 3.12, async/await"
  },
  {
    "timestamp": "2025-10-24T17:21:30.123456",
    "category": "user_preference",
    "content": "Prefers clean code style"
  }
]
```

### 3. MiniMax Search - Web Search and Browse ⭐

This is an **independent MCP Server** integrated into the Agent via `mcp.json`.

**Repository URL**: `https://github.com/MiniMax-AI/minimax_search`

#### Core Functions

**MiniMax Search provides three tools**:

1. **search** - Web search
   - Supports multiple search engines (Google, Bing, Jina, Brave, Sogou)
   - Supports Google advanced search syntax
   - Auto retry and engine switching

2. **parallel_search** - Parallel search
   - Search multiple queries simultaneously
   - Improve search efficiency

3. **browse** - Intelligent web browsing
   - Use Jina Reader to read web content
   - Use LLM to understand and answer questions
   - Auto generate web summaries

#### Usage Example

**Simple Search**:
```
User: Help me search for Python asyncio tutorials

Agent: (calls search tool)
→ Returns: Related tutorial links and summaries
```

**Parallel Search**:
```
User: Search for "Python asyncio" and "Python threading" simultaneously

Agent: (calls parallel_search tool)
→ Returns: Search results for both queries
```

**Web Browse**:
```
User: Visit https://docs.python.org and summarize asyncio features

Agent: (calls browse tool)
→ Returns: LLM-generated web summary
```

#### Technical Implementation

- **Configurable API Keys**: Read from config.yaml, supports flexible configuration
- **Multi-engine Support**: 5 search engines, automatic fallback
- **Chinese/English Optimization**: Auto-detect and select appropriate search engine
- **MCP Protocol**: Standard MCP Server implementation

---

### 4. Tool Definition

Each tool inherits from the `Tool` base class:

```python
class ReadTool(Tool):
    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return "Read the contents of a file."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to file"}
            },
            "required": ["file_path"]
        }

    async def execute(self, file_path: str) -> ToolResult:
        content = Path(file_path).read_text()
        return ToolResult(success=True, content=content)
```

Tool schemas are automatically converted to OpenAI function calling format via `to_schema()`, then converted to Anthropic format in the LLM client.

## 🏭 Production Environment Deployment

This project is an educational demo showcasing core concepts. Production environments require more considerations:

- 🧠 **Advanced Memory Management** - Vector databases, semantic search
- 🔄 **Model Fallback** - Multi-model pool, intelligent degradation
- 🛡️ **Reflection System** - Prevent model hallucinations and erroneous operations
- 📊 **Monitoring & Alerting** - Complete observability solution

> 📖 Complete Guide: [Production Deployment Guide](docs/PRODUCTION_GUIDE.md)

---

## 🧪 Testing

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

> 📖 Detailed testing guide: [Development Documentation](docs/DEVELOPMENT.md#testing-guide)

---

## Summary

This project is an **educational-friendly** yet **technically complete** Agent implementation:

✅ **Simple Enough**: Minimal code, easy to understand
✅ **Complete Enough**: Includes core functionality and Session Note Tool
✅ **Shows the Gap**: Clearly contrasts the huge difference between Demo and production

Suitable for:
- 🎓 Learning Agent architecture and working principles
- 🧪 Rapid experimentation and prototype validation
- 📚 Understanding production environment complexity

**Not suitable** for direct production use.

## 📚 Related Documentation

- [Production Deployment Guide](docs/PRODUCTION_GUIDE.md) - Complete guide from Demo to production
- [Development Documentation](docs/DEVELOPMENT.md) - Development, testing, and extension guide
- [M2 Agent Best Practices (Chinese)](docs/M2_Agent_Best_Practices_CN.md)
- [M2 Agent Best Practices (English)](docs/M2_Agent_Best_Practices_EN.md)

## 🤝 Contributing

Issues and Pull Requests are welcome!

- [Contributing Guide](CONTRIBUTING.md) - How to contribute
- [Code of Conduct](CODE_OF_CONDUCT.md) - Community guidelines

## 📄 License

This project is licensed under the [MIT License](LICENSE).

## 🔗 References

- MiniMax API: https://platform.minimaxi.com/document
- MiniMax-M2: https://github.com/MiniMax-AI/MiniMax-M2
- Anthropic API: https://docs.anthropic.com/claude/reference
- Claude Skills: https://github.com/anthropics/skills
- MCP Servers: https://github.com/modelcontextprotocol/servers

---

**⭐ If this project helps you, please give it a Star!**
