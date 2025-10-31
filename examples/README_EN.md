# Mini Agent Examples

This directory contains a series of progressive examples to help you understand how to use the Mini Agent framework.

## 📚 Example List

### 01_basic_tools.py - Basic Tool Usage

**Difficulty**: ⭐ Beginner

**Content**:
- How to directly use ReadTool, WriteTool, EditTool, BashTool
- No Agent or LLM involved, pure tool call demonstrations
- Perfect for understanding each tool's basic functionality

**Run**:
```bash
python examples/01_basic_tools.py
```

**Key Learnings**:
- Tool input parameter formats
- ToolResult return structure
- Error handling approaches

---

### 02_simple_agent.py - Simple Agent Usage

**Difficulty**: ⭐⭐ Beginner-Intermediate

**Content**:
- Create the simplest Agent
- Have Agent perform file creation tasks
- Have Agent execute bash command tasks
- Understand Agent execution flow

**Run**:
```bash
# Requires API key configuration first
python examples/02_simple_agent.py
```

**Key Learnings**:
- Agent initialization process
- How to give tasks to Agent
- How Agent autonomously selects tools
- Task completion criteria

**Prerequisites**:
- API key configured in `mini_agent/config.yaml`

---

### 03_session_notes.py - Session Note Tool

**Difficulty**: ⭐⭐⭐ Intermediate

**Content**:
- Direct usage of Session Note tools (record_note, recall_notes)
- Agent using Session Notes to maintain cross-session memory
- Demonstrate how two Agent instances share memory

**Run**:
```bash
python examples/03_session_notes.py
```

**Key Learnings**:
- How Session Notes work
- Note categorization management (category)
- How to guide Agent to use notes in system prompt
- Cross-session memory implementation

**Highlight**:
This is one of the core features of this project! Shows a lightweight but effective session memory management solution.

---

### 04_full_agent.py - Full-Featured Agent

**Difficulty**: ⭐⭐⭐⭐ Advanced

**Content**:
- Complete Agent setup with all features
- Integration of basic tools + Session Notes + MCP tools
- Full execution flow for complex tasks
- Multi-turn conversation examples

**Run**:
```bash
python examples/04_full_agent.py
```

**Key Learnings**:
- How to combine multiple tools
- MCP tool loading and usage
- Complex task decomposition and execution
- Production environment Agent configuration

**Prerequisites**:
- API key configured
- (Optional) MCP tools configured

---

## 🚀 Quick Start

### 1. Configure API Key

```bash
# Copy configuration template
cp mini_agent/config-example.yaml mini_agent/config.yaml

# Edit config file and fill in your MiniMax API Key
vim mini_agent/config.yaml
```

### 2. Run Your First Example

```bash
# Example that doesn't need API key
python examples/01_basic_tools.py

# Example that needs API key
python examples/02_simple_agent.py
```

### 3. Progressive Learning

Recommended to learn in numerical order:
1. **01_basic_tools.py** - Understand tools
2. **02_simple_agent.py** - Understand Agent
3. **03_session_notes.py** - Understand memory management
4. **04_full_agent.py** - Understand complete system

---

## 📖 Relationship with Test Cases

These examples are all refined from test cases in the `tests/` directory:

| Example             | Based on Test                                        | Description                     |
| ------------------- | ---------------------------------------------------- | ------------------------------- |
| 01_basic_tools.py   | tests/test_tools.py                                  | Basic tool unit tests           |
| 02_simple_agent.py  | tests/test_agent.py                                  | Agent basic functionality tests |
| 03_session_notes.py | tests/test_note_tool.py<br>tests/test_integration.py | Session Note tool tests         |
| 04_full_agent.py    | tests/test_integration.py                            | Complete integration tests      |

---

## 💡 Recommended Learning Paths

### Path 1: Quick Start
1. Run `01_basic_tools.py` - Learn about tools
2. Run `02_simple_agent.py` - Run your first Agent
3. Go directly to interactive mode with `main.py`

### Path 2: Deep Understanding
1. Read and run all examples (01 → 04)
2. Read corresponding test cases (`tests/`)
3. Read core implementation code (`mini_agent/`)
4. Try modifying examples to implement your own features

### Path 3: Production Application
1. Understand all examples
2. Read [Production Deployment Guide](../docs/PRODUCTION_GUIDE.md)
3. Configure MCP tools and Skills
4. Extend tool set based on needs

---

## 🔧 Troubleshooting

### API Key Error
```
❌ API key not configured in config.yaml
```
**Solution**: Ensure you've configured a valid MiniMax API Key in `mini_agent/config.yaml`

### config.yaml Not Found
```
❌ config.yaml not found
```
**Solution**:
```bash
cp mini_agent/config-example.yaml mini_agent/config.yaml
```

### MCP Tools Loading Failed
```
⚠️ MCP tools not loaded: [error message]
```
**Solution**: MCP tools are optional and don't affect basic functionality. If you need them, refer to the MCP configuration section in the main README.

---

## 📚 More Resources

- [Main Project README](../README.md) - Complete project documentation
- [Test Cases](../tests/) - More usage examples
- [Core Implementation](../mini_agent/) - Source code
- [Production Guide](../docs/PRODUCTION_GUIDE.md) - Deployment guide

---

## 🤝 Contributing Examples

If you have good usage examples, PRs are welcome!

Suggested new example directions:
- Web search integration examples (using MiniMax Search MCP)
- Skills usage examples (document processing, design, etc.)
- Custom tool development examples
- Error handling and retry mechanism examples

---

**⭐ If these examples help you, please give the project a Star!**
