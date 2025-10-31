# Building Agents with MiniMax M2: Best Practices

> This guide provides comprehensive best practices for building production-grade Agent systems, based on real-world experience with the mini-agent project

## Table of Contents

- [1. Quick Start](#1-quick-start)
- [2. Core Best Practices](#2-core-best-practices)
- [3. Advanced Features](#3-advanced-features)
- [4. Production Considerations](#4-production-considerations)
- [5. FAQ](#5-faq)

---

## 1. Quick Start

### 1.1 Clone Project and Install Dependencies

First, clone the mini-agent example project:

```bash
# Clone the project
git clone https://github.com/MiniMax-AI/Mini-Agent
cd mini-agent

# Install uv (if you haven't already)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies
uv sync
```

### 1.2 Get MiniMax API Key

#### Register MiniMax Account

**Individual Users**:

Visit [MiniMax Platform](https://platform.minimaxi.com) to register directly.

**Enterprise Team Users** (recommended to use main account + sub-accounts):

1. Register a main account at [MiniMax Platform](https://platform.minimaxi.com)
   - The name and phone number entered during registration will become the administrator information for the enterprise account
2. After logging in to the main account, create sub-accounts in **Account Management > Sub-accounts**
3. Assign different sub-accounts to enterprise personnel

**Relationship between Main and Sub-accounts**:
- Sub-accounts and main accounts share the same usage rights and rate limits
- API consumption by sub-accounts and main accounts can be shared and billed together
- Sub-account limitations: Cannot view and manage the "Payment" page, nor manage sub-accounts and API keys

#### Get API Key

After logging in to your MiniMax account, follow these steps to get the API Key:

1. **Get Group ID** (optional):
   - Go to **Account Management > Account Info > Basic Info**
   - Copy the `group_id` (may be needed in some scenarios)

2. **Get API Key**:
   - Go to **Account Management > API Keys**
   - Click **"Create New Key"**
   - Enter a key name in the popup (e.g., `mini-agent-key`)
   - After successful creation, the system will display the API Key
   - ⚠️ **Please copy and save it carefully**, the key **will only be displayed once** and cannot be viewed again

### 1.3 Configure API Key

Copy the configuration file template and fill in your API Key:

```bash
# Copy configuration file template
cp mini_agent/config-example.yaml mini_agent/config.yaml
```

Then edit `config.yaml` and fill in the MiniMax API Key you obtained in the previous step:

```yaml
api_key: "YOUR_API_KEY_HERE"
api_base: "https://api.minimax.io/anthropic"
model: "MiniMax-M2"
max_steps: 50
workspace_dir: "./workspace"
```

### 1.4 Run Examples

```bash
# Run interactive Agent
uv run python main.py
```

After starting, you can input tasks for the Agent to complete:

```
🤖 Mini Agent - Interactive Mode
============================================================

Tips:
  - Enter your task and the Agent will help you complete it
  - Enter 'exit' or 'quit' to exit
  - Workspace directory: /path/to/workspace

------------------------------------------------------------

👤 You: Create a hello.py file that prints "Hello, M2!"

🤖 Agent: Sure, I'll create this file for you...
```

**Alternative ways to run**:

```bash
# Run tests to see functionality demos
uv run pytest tests/test_agent.py -v -s

# Run all tests
uv run pytest tests
```

### 1.5 Basic Agent Architecture

```python
class Agent:
    """Minimal but complete Agent implementation"""

    def __init__(self, llm_client, tools, system_prompt):
        self.llm = llm_client
        self.tools = {tool.name: tool for tool in tools}
        self.messages = [{"role": "system", "content": system_prompt}]

    async def run(self, task: str) -> str:
        """Core execution loop"""
        self.messages.append({"role": "user", "content": task})

        for step in range(50):  # Maximum 50 steps
            # 1. Call LLM
            response = await self.llm.generate(
                messages=self.messages,
                tools=self.get_tool_schemas()
            )

            # 2. If no tool calls, task is complete
            if not response.tool_calls:
                return response.content

            # 3. Execute tool calls
            for tool_call in response.tool_calls:
                tool = self.tools[tool_call.name]
                result = await tool.execute(**tool_call.arguments)
                self.messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [tool_call]
                })
                self.messages.append({
                    "role": "user",
                    "content": [{"type": "tool_result", "content": result}]
                })

        return "Reached maximum step limit"
```

---

## 2. Core Best Practices

### 2.1 Tool Definition - Clear and Precise

**❌ Poor Tool Definition**:
```python
{
    "name": "read",
    "description": "Read file",  # Too brief
    "parameters": {
        "file": {"type": "string"}  # Vague parameter name
    }
}
```

**✅ Good Tool Definition**:
```python
{
    "name": "read_file",
    "description": "Read the contents of a file at the specified path. Supports text files (.txt, .py, .md, etc.). Returns an error if the file does not exist.",
    "parameters": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Absolute path to the file or path relative to the working directory"
            }
        },
        "required": ["file_path"]
    }
}
```

**Key Principles**:
- Descriptions should include functionality, constraints, and error scenarios
- Parameter naming should be clear and explicit (e.g., `file_path` is preferred over `file`)
- Always specify `required` fields explicitly

### 2.2 System Prompt - Define Role and Rules

```python
SYSTEM_PROMPT = """You are an automation assistant focused on helping users complete file processing and programming tasks.

Your capabilities:
- Read, write, and edit files
- Execute bash commands
- Proactively record and retrieve important information (using Note Tool)

Workflow:
1. Understand user tasks and break them into specific steps
2. Use tools to complete tasks step by step
3. Analyze errors and retry when encountered
4. Confirm results with the user upon completion

Constraints:
- Must confirm with user before executing dangerous commands (rm -rf, dd)
- Backup important files before modification
- Ask the user when uncertain rather than guessing
"""
```

**Key Principles**:
- Clearly define the Agent's capability boundaries
- Provide clear workflow guidelines
- Establish necessary safety constraints
- Encourage proactive communication with users

### 2.3 Error Handling - Graceful Degradation

```python
async def execute_tool(self, tool_call):
    """Execute tool call with comprehensive error handling"""
    try:
        tool = self.tools[tool_call.name]
        result = await tool.execute(**tool_call.arguments)
        return ToolResult(success=True, content=result)

    except FileNotFoundError as e:
        # File not found - provide clear error message
        return ToolResult(
            success=False,
            error=f"File not found: {e.filename}. Please check if the path is correct."
        )

    except PermissionError as e:
        # Permission error - guide user to resolution
        return ToolResult(
            success=False,
            error=f"Permission denied: {e}. May need sudo or check file permissions."
        )

    except Exception as e:
        # Unknown error - log detailed information
        logger.error(f"Tool {tool_call.name} failed: {e}", exc_info=True)
        return ToolResult(
            success=False,
            error=f"Execution failed: {type(e).__name__}: {str(e)}"
        )
```

**Key Principles**:
- Distinguish error types and provide targeted error messages
- Error messages should be LLM-friendly (clear and actionable)
- Log detailed information for subsequent debugging and analysis
- Implement graceful degradation to prevent single errors from crashing the system

### 2.4 Message Format - Follow Anthropic Specification

**Important**: When M2 uses Anthropic API format, message format must strictly follow the specification:

```python
# ✅ Correct tool call format
messages = [
    {
        "role": "user",
        "content": "Please read the config.yaml file"
    },
    {
        "role": "assistant",
        "content": [
            {
                "type": "tool_use",
                "id": "toolu_01A09q90qw90lq917835lq9",
                "name": "read_file",
                "input": {"file_path": "config.yaml"}
            }
        ]
    },
    {
        "role": "user",
        "content": [
            {
                "type": "tool_result",
                "tool_use_id": "toolu_01A09q90qw90lq917835lq9",
                "content": "api_key: xxx\\nmodel: MiniMax-M2"
            }
        ]
    }
]

# ❌ Wrong: mixing OpenAI format
messages = [
    {
        "role": "assistant",
        "function_call": {"name": "read_file", ...}  # This is OpenAI format!
    }
]
```

### 2.5 Tool Results - Structured Output

```python
@dataclass
class ToolResult:
    """Standardized tool execution result"""
    success: bool
    content: str = ""
    error: str = ""
    metadata: Dict[str, Any] = None

    def to_message_content(self) -> str:
        """Convert to LLM-friendly format"""
        if self.success:
            return f"✅ Execution successful\\n\\n{self.content}"
        else:
            return f"❌ Execution failed\\n\\nError: {self.error}"
```

**Benefits of Structured Output**:
- Facilitates LLM parsing and understanding of execution results
- Simplifies subsequent processing and logging
- Provides unified error handling logic, improving code maintainability

---

## 3. Advanced Features

### 3.1 Skills - Professional Task Guidance System ⭐

Skills are a core feature of the mini-agent project, providing Agents with domain-specific expertise to complete complex tasks with professional quality.

#### What are Skills?

Skills are pre-defined professional guidance documents that provide Agents with:
- 📋 **Detailed Execution Steps**: Tell the Agent how to complete complex tasks step by step
- 💡 **Best Practices**: Verified professional methods and techniques
- ⚠️ **Cautions**: How to avoid common pitfalls and errors
- 📝 **Example Templates**: Reusable code, scripts, and resource files

#### Built-in Skills Capabilities

mini-agent integrates 20+ professional skills via git submodule:

**📄 Document Processing Skills**

```bash
# Create Word Document
User: Use docx skill to create a technical document with tables and images
Agent: (Load docx skill)
     → Understand OOXML format specification
     → Create document structure
     → Add formatted content
     → Save as .docx file

# Generate PDF Report
User: Use pdf skill to create a project report with charts
Agent: (Load pdf skill)
     → Plan document layout
     → Add charts and tables
     → Set headers and footers
     → Generate professional PDF
```

**🎨 Design & Creation Skills**

```bash
# Design Poster
User: Use canvas-design skill to create a tech-style poster
Agent: (Load canvas-design skill)
     → Apply design philosophy (balance, contrast, whitespace)
     → Choose appropriate fonts and colors
     → Generate PNG/PDF format output

# Create Animated GIF
User: Use slack-gif-creator to create a welcome animation
Agent: (Load slack-gif-creator skill)
     → Select animation template (13 types: zoom/fade/bounce/spin, etc.)
     → Optimize file size (meet Slack limitations)
     → Generate high-quality GIF
```

**🧪 Development & Testing Skills**

```bash
# Test Web Application
User: Use webapp-testing skill to test my website localhost:3000
Agent: (Load webapp-testing skill)
     → Launch Playwright browser
     → Automated UI interaction testing
     → Screenshot and result verification
     → Generate test report

# Develop MCP Server
User: Use mcp-builder skill to create a weather query MCP Server
Agent: (Load mcp-builder skill)
     → Understand MCP protocol specification
     → Generate server.py code
     → Configure tool definitions
     → Provide test examples
```

#### Skills Technical Implementation

**1. Skill File Structure**

```
skills/
├── document-skills/
│   ├── pdf/
│   │   ├── SKILL.md          # Main guidance file
│   │   ├── reference.md      # PDF format reference
│   │   ├── forms.md          # Form handling guide
│   │   └── scripts/          # Python helper scripts
│   │       ├── fill_pdf_form.py
│   │       ├── extract_form_info.py
│   │       └── ...
│   └── ...
├── canvas-design/
│   ├── SKILL.md
│   └── canvas-fonts/         # Font resources
│       ├── WorkSans-Regular.ttf
│       └── ...
└── ...
```

**2. SKILL.md Format**

```markdown
---
name: pdf
description: Create, edit, and analyze PDF documents with forms support
---

# PDF Skill

This skill helps you work with PDF files...

## Capabilities
- Create new PDF documents
- Extract text and tables
- Fill PDF forms
- Merge/split PDFs

## Usage Examples

### Create a simple PDF
...

## Best Practices
1. Always use proper error handling
2. Test with different PDF versions
3. ...

## Common Pitfalls
- Avoid...
- Remember...
```

**3. Skill Loading Mechanism**

In mini-agent, Skills are integrated through `SkillLoader` and `SkillTool`:

```python
# mini_agent/tools/skill_loader.py
class SkillLoader:
    """Load and manage Claude Skills"""
    
    def load_skills(self, skills_dir: Path) -> List[Dict]:
        """Scan skills directory and load all SKILL.md files"""
        skills = []
        for skill_dir in skills_dir.iterdir():
            skill_md = skill_dir / "SKILL.md"
            if skill_md.exists():
                # Parse YAML frontmatter
                skill_data = self.parse_skill_md(skill_md)
                # Load related resource files
                skill_data["resources"] = self.load_resources(skill_dir)
                skills.append(skill_data)
        return skills

# mini_agent/tools/skill_tool.py
class SkillTool(Tool):
    """Dynamically load and use Skills"""
    
    async def execute(self, skill_name: str, context: str):
        """Load specified skill and inject into Agent context"""
        skill = self.loader.get_skill(skill_name)
        
        # Inject skill content into system prompt
        enhanced_prompt = f"""
{self.base_prompt}

You now have access to the {skill["name"]} skill.

{skill["content"]}
"""
        
        return enhanced_prompt
```

**4. Agent Using Skills Flow**

```python
# Auto-load on user request
User: "Create a PDF report"

# Agent reasoning process:
Agent:
  1. Identify task type → "PDF creation"
  2. Find related skill → Found "pdf" skill
  3. Call load_skill("pdf")
  4. Get PDF creation guidance:
     - Format specification
     - Common libraries (reportlab, PyPDF2)
     - Code templates
     - Best practices
  5. Generate code following skill guidance
  6. Execute and verify results
```

#### Skills Advantages

**Compared to Traditional System Prompt**:

| Dimension           | Traditional System Prompt | Skills System                       |
| ------------------- | ------------------------- | ----------------------------------- |
| **Content**         | Limited (~2K tokens)      | Unlimited (load on-demand)          |
| **Professionalism** | General guidance          | Deep specialized knowledge          |
| **Maintainability** | Hard to update            | Independent files, easy to maintain |
| **Extensibility**   | Fixed capabilities        | Dynamically load new skills         |
| **Reusability**     | Not reusable              | Share across projects               |
| **Version Control** | Hard to track             | Git managed, clear versions         |

**Real-world Comparison**:

```bash
# Without Skills
User: Create a PDF with tables
Agent: I'll try... (might have format errors, layout issues)

# With PDF Skill
User: Create a PDF with tables
Agent: (Load pdf skill)
     → Follow standard process
     → Use recommended libraries
     → Apply best practices
     → Generate professional PDF (correct format, beautiful layout)
```

#### Creating Custom Skills

Use the `skill-creator` skill to create your own professional skills:

**Step 1: Plan Skill**

```bash
User: Use skill-creator to help me create a data visualization skill

Agent: (Load skill-creator)
     → Guiding questions:
       1. What is the main functionality of the Skill?
       2. Who is the target user?
       3. What dependencies are needed?
       4. Common use cases?
```

**Step 2: Generate SKILL.md**

```markdown
---
name: data-visualization
description: Create professional data visualizations using matplotlib, seaborn, and plotly
---

# Data Visualization Skill

## Capabilities
- Create line, bar, scatter, and pie charts
- Generate heatmaps and correlation matrices
- Interactive visualizations with plotly
- Export to PNG, SVG, PDF formats

## Quick Start
```python
import matplotlib.pyplot as plt
import seaborn as sns

# Create a simple line chart
plt.figure(figsize=(10, 6))
plt.plot(x, y)
plt.title("My Chart")
plt.savefig("output.png")
```

## Best Practices
1. Choose the right chart type for your data
2. Use clear labels and titles
3. Apply appropriate color schemes
4. Optimize figure size for readability
```

**Step 3: Add Resource Files**

```
skills/data-visualization/
├── SKILL.md
├── templates/
│   ├── line_chart.py
│   ├── bar_chart.py
│   └── heatmap.py
├── examples/
│   ├── example1.png
│   └── example2.png
└── requirements.txt
```

**Step 4: Test and Optimize**

```bash
# Test skill
User: Use data-visualization skill to create a bar chart of sales data

Agent: (Load new skill)
     → Check data format
     → Select appropriate template
     → Apply configuration
     → Generate chart
```

#### Skills Best Practices

**1. When to Create New Skills?**

✅ **Suitable for Skills**:
- Complex multi-step tasks (> 5 steps)
- Domains requiring specialized knowledge
- Frequently repeated workflows
- Clear best practices available

❌ **Not Suitable for Skills**:
- Simple one-time tasks
- Overly general guidance
- Frequently changing requirements

**2. Skill Design Principles**

```markdown
# Good Skill Design
---
name: my-skill
description: Detailed description of functionality, use cases, prerequisites
---

## Objective
Clearly state what problem this skill solves

## Prerequisites
List required dependencies, tools, environment

## Steps
1. First step (specific, actionable)
2. Second step (with code examples)
3. ...

## Examples
Provide complete usage examples

## Best Practices
List experience summaries and tips

## Common Issues
Proactively list potential issues and solutions
```

**3. Skill Maintenance**

```bash
# Regular skill updates
1. Collect user feedback
2. Document common errors
3. Update best practices
4. Add new examples
5. Commit to version control

# Version management
git commit -m "feat(pdf-skill): Add form filling examples"
git commit -m "fix(canvas-design): Update font loading path"
git commit -m "docs(mcp-builder): Clarify error handling"
```

#### Skills Ecosystem

**Official Skills (Integrated)**:
- ✅ 20+ professional skills
- ✅ Continuously updated and maintained
- ✅ Community validated

**Custom Skills**:
- ✅ Customized for team needs
- ✅ Internal knowledge base and processes
- ✅ Proprietary tool integration

**Shared Skills**:
- ✅ Publish to GitHub
- ✅ Share with community
- ✅ Collect feedback for improvement

#### Summary

The Skills system is an innovative feature of the mini-agent project with the following core advantages:

- **Knowledge Sharing**: Standardizes and structures domain expertise
- **Continuous Evolution**: Facilitates iterative updates and long-term maintenance
- **Rapid Extension**: Quickly gain new capabilities by adding new Skills
- **Precise Execution**: Provides concrete, actionable guidance

Through the Skills mechanism, Agents can evolve from general assistants into specialized domain systems.

---

### 3.2 Note Tool - Cross-Conversation Memory ⭐

This is a key feature that distinguishes demo-level from production-grade Agents.

#### Core Philosophy

**Traditional Approach** (❌ Not Recommended):
```python
# Save all conversation history
messages = [msg1, msg2, msg3, ..., msg100]  # Will exceed context window!
```

**Note Tool Approach** (✅ Recommended):
```python
# Agent proactively decides what needs to be remembered
# User says: "I prefer concise code style, project uses Python 3.12"
# Agent calls:
save_note(
    content="User preference: concise code style; Project: Python 3.12",
    category="user_preference"
)

# In new conversation, Agent proactively retrieves when needed:
notes = read_note(category="user_preference")
# Returns: "User preference: concise code style; Project: Python 3.12"
```

#### Implementation Example

```python
class NoteTool(Tool):
    """Persistent note tool"""

    @property
    def name(self) -> str:
        return "save_note"

    @property
    def description(self) -> str:
        return (
            "Save important information to persistent storage for cross-conversation memory. "
            "Suitable for saving: user preferences, project information, important decisions, context key points. "
            "Each note is automatically timestamped."
        )

    @property
    def parameters(self):
        return {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "Information to remember (concise but specific)"
                },
                "category": {
                    "type": "string",
                    "description": "Category label",
                    "enum": ["user_preference", "project_info", "decision", "context"]
                }
            },
            "required": ["content", "category"]
        }

    async def execute(self, content: str, category: str):
        notes = self._load_from_file()
        notes.append({
            "timestamp": datetime.now().isoformat(),
            "category": category,
            "content": content
        })
        self._save_to_file(notes)
        return f"✅ Recorded: {content}"
```

#### Usage Effect

```
First Conversation:
User: I'm a Python developer, project uses Python 3.12, prefer type hints
Agent: (Proactively calls save_note)
      → Saves: "Project=Python 3.12, Preference=type hints"

---New Session---

Second Conversation:
User: Help me write a function to read JSON files
Agent: (Proactively calls read_note)
      → Recalls: "Project=Python 3.12, Preference=type hints"
      → Generates code with type hints:

      from pathlib import Path
      import json
      from typing import Dict, Any

      def read_json(file_path: str) -> Dict[str, Any]:
          return json.loads(Path(file_path).read_text())
```

#### Best Practices

1. **When to Save Notes**:
   - ✅ When user explicitly expresses preferences
   - ✅ When project key information first appears
   - ✅ When user corrects your mistakes
   - ❌ Don't save every conversation

2. **How to Organize Notes**:
   - Use clear categories
   - Content should be concise but information-complete
   - Avoid saving duplicate similar information

3. **When to Retrieve Notes**:
   - Proactively retrieve at start of new conversation
   - When user asks "Do you remember..."
   - When personalized response is needed

### 3.3 Context Management - Prevent Overflow

Even with Note Tool, conversation history still needs management:

```python
class MessageManager:
    """Simple but effective message management"""

    def __init__(self, max_messages: int = 20):
        self.max_messages = max_messages
        self.messages = []

    def add_message(self, message: Dict):
        """Add message with automatic truncation"""
        self.messages.append(message)

        # Keep system prompt + recent N messages
        if len(self.messages) > self.max_messages:
            self.messages = [
                self.messages[0],  # system prompt
                *self.messages[-(self.max_messages-1):]  # recent messages
            ]

    def get_messages(self) -> List[Dict]:
        return self.messages
```

**Advanced Version (Production)**:
- Use tiktoken for precise token counting
- Intelligently truncate based on message importance
- Automatically summarize tool call results

### 3.4 Streaming Output - Enhance User Experience

```python
async def run_streaming(self, task: str):
    """Stream results for improved responsiveness perception"""
    self.messages.append({"role": "user", "content": task})

    async with self.llm.stream(
        messages=self.messages,
        tools=self.get_tool_schemas()
    ) as stream:
        async for chunk in stream:
            if chunk.type == "content_block_delta":
                # Real-time text output
                print(chunk.delta.text, end="", flush=True)

            elif chunk.type == "tool_use":
                # Execute tool call
                result = await self.execute_tool(chunk)
                # ... continue streaming
```

**Use Cases**:
- Real-time display of Agent thinking process in web apps
- Long-running tasks
- Scenarios requiring user interaction confirmation

---

## 4. Production Considerations

### 4.1 The Gap from Demo to Production

Based on mini-agent project experience, here are the key differences:

#### Development Time Comparison
```
Demo:    2-3 days
Production:    3-6 months
Gap:    30-60x
```

### 4.2 Production-Grade Essential Features

#### 1. Advanced Note Management

**Demo Solution**:
- JSON file storage
- Simple category-based retrieval

**Production Solution**:
- Vector database (Milvus/Pinecone)
- Semantic search (not keyword matching)
- Note deduplication and merging
- Importance scoring and auto-expiration
- Multi-level note architecture (short-term/long-term/working memory)

**Value Proposition**: Supports more complex long-term conversation scenarios with intelligent semantic retrieval of relevant memories

#### 2. Model Fallback Mechanism

**Demo Solution**:
- Single model (M2)
- Direct error on failure

**Production Solution**:
- Multi-model pool management
  - Primary: M2, Claude-3.5-Sonnet
  - Backup: GPT-4, Claude-Opus
  - Fallback: Claude-Haiku, GPT-3.5
- Auto-select model based on task complexity
- Auto-fallback on failure
- Cost optimization (prefer cheaper models)
- Health monitoring and quota management

**Value Proposition**: Achieves 99.9% system availability with 30-50% cost reduction

#### 3. Reflection System

**Demo Solution**:
- Directly trust model output

**Production Solution**:
- Pre-validation of tool calls (parameters, paths, command safety)
- Pre-execution prediction: "What will this operation do?"
- Post-execution validation: Compare result with expectation
- Self-reflection: Require explanation of reasoning
- Multi-model cross-validation

**Value Proposition**: Reduces erroneous operations by over 80%

#### 4. Monitoring and Observability

**Production Essentials**:
```python
# Structured logging
logger.info("tool_execution", extra={
    "tool_name": tool.name,
    "arguments": arguments,
    "duration_ms": duration,
    "success": result.success,
    "user_id": user_id,
    "session_id": session_id
})

# Metrics collection
metrics.increment("agent.tool_calls", tags={
    "tool": tool.name,
    "status": "success" if result.success else "error"
})

# Distributed tracing
with trace_span("agent.run", task=task):
    result = await self.run(task)
```

**Value Proposition**: Rapidly identify root causes and continuously optimize system performance

### 4.3 Security Considerations

```python
class SecurityValidator:
    """Tool call security check"""

    DANGEROUS_PATTERNS = [
        "rm -rf",
        "dd if=",
        "mkfs",
        "> /dev/",
        "chmod 777",
        "curl | bash"
    ]

    def validate_bash_command(self, command: str) -> bool:
        """Validate bash command safety"""
        # 1. Dangerous command detection
        if any(pattern in command for pattern in self.DANGEROUS_PATTERNS):
            logger.warning(f"Dangerous command blocked: {command}")
            return False

        # 2. Path traversal detection
        if ".." in command or command.startswith("/etc"):
            logger.warning(f"Path traversal detected: {command}")
            return False

        # 3. Command injection detection
        if ";" in command or "|" in command or "&&" in command:
            # Need additional validation
            pass

        return True
```

### 4.4 Performance Optimization

#### Parallel Tool Execution

```python
async def execute_tools_parallel(self, tool_calls):
    """Execute multiple independent tool calls concurrently"""
    tasks = [
        self.execute_tool(tc)
        for tc in tool_calls
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

**Performance Gain**: 3-5x performance improvement in multi-tool call scenarios

#### Result Caching

```python
from functools import lru_cache

class CachedTool(Tool):
    @lru_cache(maxsize=100)
    async def execute(self, **kwargs):
        # Cache results for same parameters
        return await self._execute_impl(**kwargs)
```

**Applicable Scenarios**: Read-type tools (e.g., read_file, fetch_url)

---

## 5. FAQ

### Q1: How to choose between M2 and Claude/GPT-4?

**Choose M2 when**:
- Cost-sensitive scenarios
- Agent workflows (tool-calling intensive)
- Primarily Chinese tasks
- Need fast responses

**Choose Claude/GPT-4 when**:
- Need strongest reasoning capabilities
- Creative content generation
- Complex code understanding and generation
- Sufficient budget

**Recommended Strategy**: Multi-model hybrid approach
- M2 as primary model (handles 80% of tasks)
- Automatically switch to Claude/GPT-4 for complex tasks
- Configure comprehensive Fallback mechanisms

### Q2: How to debug Agent's erroneous behavior?

**Three-Step Debugging**:

1. **Detailed Logging**
```python
logger.info(f"Step {step}: LLM Response", extra={
    "content": response.content,
    "tool_calls": response.tool_calls,
    "stop_reason": response.stop_reason
})
```

2. **Visualize Execution Flow**
```
[User] Create a Python file
  ↓
[Agent] Call write_file(path="demo.py", content="...")
  ↓
[Tool] ✅ File created successfully
  ↓
[Agent] Call read_file(path="demo.py")
  ↓
[Tool] ✅ Return file content
  ↓
[Agent] "File created, content as follows..."
```

3. **Replay and Analysis**
```python
# Save state at each step
session.save_step({
    "messages": self.messages.copy(),
    "tool_call": tool_call,
    "result": result
})

# Can replay entire execution process later
session.replay(from_step=5)
```

### Q3: Agent frequently executes wrong tool calls?

**Possible Causes and Solutions**:

1. **Unclear Tool Description**
   - ❌ "Read file"
   - ✅ "Read text file content at specified path. Supports .txt/.py/.md formats"

2. **Missing Usage Examples**
```python
description = """
Read file content.

Examples:
- read_file(file_path="config.yaml")  # Read config file
- read_file(file_path="./data/users.json")  # Read data file
"""
```

3. **Insufficient System Prompt Constraints**
```python
system_prompt = """
Tool usage rules:
1. Before file operations, use bash("ls") to confirm path exists
2. Before writing file, use read_file to check if important content will be overwritten
3. When uncertain, ask user rather than guessing
"""
```

### Q4: How to handle Agent getting stuck in loops?

**Detect Loops**:
```python
class LoopDetector:
    def __init__(self, window_size=5):
        self.recent_actions = deque(maxlen=window_size)

    def detect_loop(self, action: str) -> bool:
        """Detect if stuck in a loop"""
        self.recent_actions.append(action)

        # If last 5 operations are all the same
        if len(self.recent_actions) == self.window_size:
            if len(set(self.recent_actions)) == 1:
                return True

        return False

# Usage
if loop_detector.detect_loop(f"{tool_name}:{arguments}"):
    # Break loop, prompt LLM
    self.messages.append({
        "role": "user",
        "content": "Repeated operations detected, please try a different approach."
    })
```

---

## Summary

### Key Takeaways

1. **Clear Tool Definitions**: Foundation of Agent capabilities
2. **Explicit System Prompts**: Define behavior boundaries and workflows
3. **Note Tool is Key**: One of the core features distinguishing demo from production
4. **Comprehensive Error Handling**: Graceful degradation more important than perfect execution
5. **Security First**: Validate all user inputs and tool calls

### Reference Resources

- **MiniMax Official Documentation**: https://platform.minimaxi.com/docs
- **Mini Agent Project**: https://github.com/MiniMax-AI/Mini-Agent
- **Technical Support**: Available through MiniMax Platform

---

## Appendix: Complete Example Code

See the [mini-agent](https://github.com/MiniMax-AI/Mini-Agent) project, which includes:

- ✅ Basic Agent implementation
- ✅ Complete Note Tool implementation
- ✅ 4 core tools (Read/Write/Edit/Bash)
- ✅ Complete test cases
- ✅ Detailed documentation and comments

**Quick Start**:
```bash
# Clone the project
git clone https://github.com/MiniMax-AI/Mini-Agent
cd mini-agent

# Install dependencies
uv sync

# Configure API Key
cp config-example.yaml config.yaml
# Then edit config.yaml and fill in your API Key

# Run interactive Agent
uv run python main.py
```

---

**Document Version**: v1.2  
**Last Updated**: 2025-10-27  
**Applicable Models**: MiniMax M2 Series  
**Based on Project**: mini-agent

**Copyright**: © 2025 MiniMax. All rights reserved.
