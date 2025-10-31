# 使用 MiniMax M2 构建 Agent 的最佳实践

> 本文档基于 mini-agent 项目的实战经验，提供构建生产级 Agent 系统的完整指南

## 目录

- [1. 快速开始](#1-快速开始)
- [2. 核心最佳实践](#2-核心最佳实践)
- [3. 进阶特性](#3-进阶特性)
- [4. 生产环境考虑](#4-生产环境考虑)
- [5. 常见问题](#5-常见问题)

---

## 1. 快速开始

### 1.1 克隆项目并安装依赖

首先克隆 mini-agent 示例项目：

```bash
# 克隆项目
git clone https://github.com/MiniMax-AI/Mini-Agent mini-agent
cd mini-agent

# 安装 uv（如果还没有）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 同步依赖
uv sync
```

### 1.2 获取 MiniMax API Key

#### 注册 MiniMax 账号

**个人用户**：

直接访问 [MiniMax 开放平台](https://platform.minimaxi.com) 进行注册。

**企业团队用户**（推荐使用主账号+子账号管理）：

1. 在 [MiniMax 开放平台](https://platform.minimaxi.com) 注册主账号
   - 注册时填写的姓名与手机号将成为企业账号的管理员信息
2. 登录主账号后，在 **账户管理 > 子账号** 创建所需数量的子账户
3. 为企业人员分配不同的子账户进行使用

**主账号与子账号的关系**：
- 子账号和主账号享用相同的使用权益与速率限制
- 子账号和主账号的 API 消耗可以共享，最后统一结算
- 子账号限制：无法查看和管理"支付"页面，也无法管理子账号和接口密钥

#### 获取 API Key

登录 MiniMax 账号后，按以下步骤获取 API Key：

1. **获取 Group ID**（可选）：
   - 进入 **账户管理 > 账户信息 > 基本信息**
   - 复制 `group_id`（某些场景下可能需要）

2. **获取 API Key**：
   - 进入 **账户管理 > 接口密钥**
   - 点击 **"创建新的密钥"**
   - 在弹窗中输入密钥名称（如：`mini-agent-key`）
   - 创建成功后，系统将展示 API Key
   - ⚠️ **请务必复制并妥善保存**，该密钥**只会显示一次**，无法再次查看

### 1.3 配置 API Key

复制配置文件模板并填入你的 API Key：

```bash
# 复制配置文件模板
cp mini_agent/config-example.yaml mini_agent/config.yaml
```

然后编辑 `config.yaml`，填入你在上一步获取的 MiniMax API Key：

```yaml
api_key: "YOUR_API_KEY_HERE"
api_base: "https://api.minimax.io/anthropic"
model: "MiniMax-M2"
max_steps: 50
workspace_dir: "./workspace"
```

### 1.4 运行示例

```bash
# 运行交互式 Agent
uv run python main.py
```

启动后，你可以输入任务让 Agent 帮你完成：

```
🤖 Mini Agent - 交互式模式
============================================================

提示:
  - 输入你的任务，Agent 会帮你完成
  - 输入 'exit' 或 'quit' 退出
  - 工作目录: /path/to/workspace

------------------------------------------------------------

👤 你: 创建一个 hello.py 文件，内容是打印 "Hello, M2!"

🤖 Agent: 好的，我来帮你创建这个文件...
```

**其他运行方式**：

```bash
# 运行测试查看功能演示
uv run pytest tests/test_agent.py -v -s

# 运行所有测试
uv run pytest tests
```

### 1.5 基础 Agent 架构

```python
class Agent:
    """最小化但完整的 Agent 实现"""

    def __init__(self, llm_client, tools, system_prompt):
        self.llm = llm_client
        self.tools = {tool.name: tool for tool in tools}
        self.messages = [{"role": "system", "content": system_prompt}]

    async def run(self, task: str) -> str:
        """执行任务的核心循环"""
        self.messages.append({"role": "user", "content": task})

        for step in range(50):  # 最多 50 步
            # 1. 调用 LLM
            response = await self.llm.generate(
                messages=self.messages,
                tools=self.get_tool_schemas()
            )

            # 2. 如果没有工具调用，任务完成
            if not response.tool_calls:
                return response.content

            # 3. 执行工具调用
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

        return "达到最大步数限制"
```

---

## 2. 核心最佳实践

### 2.1 工具定义 - 清晰准确

**❌ 不好的工具定义**:
```python
{
    "name": "read",
    "description": "读取文件",  # 太简略
    "parameters": {
        "file": {"type": "string"}  # 参数名模糊
    }
}
```

**✅ 好的工具定义**:
```python
{
    "name": "read_file",
    "description": "读取指定路径的文件内容。支持文本文件（.txt, .py, .md 等）。如果文件不存在会返回错误。",
    "parameters": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "文件的绝对路径或相对于工作目录的路径"
            }
        },
        "required": ["file_path"]
    }
}
```

**关键原则**：
- 描述应包含功能说明、使用限制、错误场景
- 参数命名应清晰明确（如 `file_path` 优于 `file`）
- 必须明确指定 `required` 字段

### 2.2 System Prompt - 明确角色和规则

```python
SYSTEM_PROMPT = """你是一个自动化助手，专注于帮助用户完成文件处理和编程任务。

你的能力：
- 读取、写入、编辑文件
- 执行 bash 命令
- 主动记录和检索重要信息（使用 Note Tool）

工作流程：
1. 理解用户任务，分解为具体步骤
2. 使用工具逐步完成任务
3. 遇到错误时分析原因并重试
4. 完成后向用户确认结果

约束条件：
- 执行危险命令（rm -rf, dd）前必须向用户确认
- 修改重要文件前先备份
- 遇到不确定的情况，向用户询问而不是猜测
"""
```

**关键原则**：
- 明确定义 Agent 的能力边界
- 提供清晰的工作流程指引
- 设置必要的安全约束条件
- 鼓励 Agent 主动与用户沟通

### 2.3 错误处理 - 优雅降级

```python
async def execute_tool(self, tool_call):
    """执行工具调用，带完善的错误处理"""
    try:
        tool = self.tools[tool_call.name]
        result = await tool.execute(**tool_call.arguments)
        return ToolResult(success=True, content=result)

    except FileNotFoundError as e:
        # 文件不存在 - 提供清晰的错误信息
        return ToolResult(
            success=False,
            error=f"文件不存在: {e.filename}。请检查路径是否正确。"
        )

    except PermissionError as e:
        # 权限错误 - 引导用户解决
        return ToolResult(
            success=False,
            error=f"权限不足: {e}。可能需要 sudo 或检查文件权限。"
        )

    except Exception as e:
        # 未知错误 - 记录详细信息
        logger.error(f"Tool {tool_call.name} failed: {e}", exc_info=True)
        return ToolResult(
            success=False,
            error=f"执行失败: {type(e).__name__}: {str(e)}"
        )
```

**关键原则**：
- 区分错误类型，提供针对性的错误提示
- 错误信息应对 LLM 友好（表述明确、可操作）
- 记录详细日志以便后续调试分析
- 采用优雅降级策略，避免单个错误导致系统崩溃

### 2.4 消息格式 - 符合 Anthropic 规范

**重要**: M2 使用 Anthropic API 格式时，消息格式要严格遵循规范：

```python
# ✅ 正确的工具调用格式
messages = [
    {
        "role": "user",
        "content": "请读取 config.yaml 文件"
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

# ❌ 错误：混用 OpenAI 格式
messages = [
    {
        "role": "assistant",
        "function_call": {"name": "read_file", ...}  # 这是 OpenAI 格式！
    }
]
```

### 2.5 工具结果 - 结构化输出

```python
@dataclass
class ToolResult:
    """标准化的工具执行结果"""
    success: bool
    content: str = ""
    error: str = ""
    metadata: Dict[str, Any] = None

    def to_message_content(self) -> str:
        """转换为对 LLM 友好的格式"""
        if self.success:
            return f"✅ 执行成功\\n\\n{self.content}"
        else:
            return f"❌ 执行失败\\n\\n错误: {self.error}"
```

**结构化输出的优势**：
- 便于 LLM 解析和理解执行结果
- 简化后续处理流程和日志记录
- 统一错误处理逻辑，提升代码可维护性

---

## 3. 进阶特性

### 3.1 Skills - 专业任务指导系统 ⭐

Skills 是 mini-agent 项目的核心特性之一，为 Agent 提供专业领域知识，使其能够高质量地完成复杂任务。

#### 什么是 Skills？

Skills 是一套预定义的专业指导文档，通过 `SKILL.md` 文件为 Agent 提供：
- 📋 **详细的执行步骤**：告诉 Agent 如何一步步完成复杂任务
- 💡 **最佳实践**：经过验证的专业方法和技巧
- ⚠️ **注意事项**：常见陷阱和错误的避免方法
- 📝 **示例模板**：可复用的代码、脚本和资源文件

#### 内置 Skills 能力

mini-agent 通过 git submodule 集成了 20+ 专业 skills：

**📄 文档处理 Skills**

```bash
# 创建 Word 文档
用户: 使用 docx skill 创建一个技术文档，包含表格和图片
Agent: (加载 docx skill)
     → 了解 OOXML 格式规范
     → 创建文档结构
     → 添加格式化内容
     → 保存为 .docx 文件

# 生成 PDF 报告
用户: 使用 pdf skill 创建一个带图表的项目报告
Agent: (加载 pdf skill)
     → 规划文档布局
     → 添加图表和表格
     → 设置页眉页脚
     → 生成专业 PDF
```

**🎨 设计创作 Skills**

```bash
# 设计海报
用户: 使用 canvas-design skill 创建一个科技风格的海报
Agent: (加载 canvas-design skill)
     → 应用设计哲学（平衡、对比、留白）
     → 选择合适的字体和配色
     → 生成 PNG/PDF 格式输出

# 创建动画 GIF
用户: 使用 slack-gif-creator 创建一个欢迎动画
Agent: (加载 slack-gif-creator skill)
     → 选择动画模板（13种：zoom/fade/bounce/spin等）
     → 优化文件大小（符合 Slack 限制）
     → 生成高质量 GIF
```

**🧪 开发测试 Skills**

```bash
# 测试 Web 应用
用户: 使用 webapp-testing skill 测试我的网站 localhost:3000
Agent: (加载 webapp-testing skill)
     → 启动 Playwright 浏览器
     → 自动化 UI 交互测试
     → 截图和结果验证
     → 生成测试报告

# 开发 MCP Server
用户: 使用 mcp-builder skill 创建一个天气查询 MCP Server
Agent: (加载 mcp-builder skill)
     → 了解 MCP 协议规范
     → 生成 server.py 代码
     → 配置工具定义
     → 提供测试示例
```

#### Skills 技术实现

**1. Skill 文件结构**

```
skills/
├── document-skills/
│   ├── pdf/
│   │   ├── SKILL.md          # 主要指导文件
│   │   ├── reference.md      # PDF 格式参考
│   │   ├── forms.md          # 表单处理指南
│   │   └── scripts/          # Python 辅助脚本
│   │       ├── fill_pdf_form.py
│   │       ├── extract_form_info.py
│   │       └── ...
│   └── ...
├── canvas-design/
│   ├── SKILL.md
│   └── canvas-fonts/         # 字体资源
│       ├── WorkSans-Regular.ttf
│       └── ...
└── ...
```

**2. SKILL.md 格式**

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

**3. Skill 加载机制**

在 mini-agent 中，Skills 通过 `SkillLoader` 和 `SkillTool` 集成：

```python
# mini_agent/tools/skill_loader.py
class SkillLoader:
    """加载和管理 Claude Skills"""

    def load_skills(self, skills_dir: Path) -> List[Dict]:
        """扫描 skills 目录，加载所有 SKILL.md"""
        skills = []
        for skill_dir in skills_dir.iterdir():
            skill_md = skill_dir / "SKILL.md"
            if skill_md.exists():
                # 解析 YAML frontmatter
                skill_data = self.parse_skill_md(skill_md)
                # 加载相关资源文件
                skill_data["resources"] = self.load_resources(skill_dir)
                skills.append(skill_data)
        return skills

# mini_agent/tools/skill_tool.py
class SkillTool(Tool):
    """动态加载并使用 Skills"""

    async def execute(self, skill_name: str, context: str):
        """加载指定 skill 并注入到 Agent 上下文"""
        skill = self.loader.get_skill(skill_name)

        # 将 skill 内容注入到 system prompt
        enhanced_prompt = f"""
{self.base_prompt}

You now have access to the {skill["name"]} skill.

{skill["content"]}
"""

        return enhanced_prompt
```

**4. Agent 使用 Skills 的流程**

```python
# 用户请求时自动加载
用户: "创建一个 PDF 报告"

# Agent 推理过程:
Agent:
  1. 识别任务类型 → "PDF 创建"
  2. 查找相关 skill → 找到 "pdf" skill
  3. 调用 load_skill("pdf")
  4. 获取 PDF 创建指导:
     - 格式规范
     - 常用库 (reportlab, PyPDF2)
     - 代码模板
     - 最佳实践
  5. 按照 skill 指导生成代码
  6. 执行并验证结果
```

#### Skills 的优势

**相比传统 System Prompt**:

| 维度         | 传统 System Prompt | Skills 系统        |
| ------------ | ------------------ | ------------------ |
| **内容量**   | 有限（~2K tokens） | 无限（按需加载）   |
| **专业性**   | 通用指导           | 深度专业知识       |
| **可维护**   | 难以更新           | 独立文件，易于维护 |
| **可扩展**   | 固定能力           | 动态加载新 skills  |
| **复用性**   | 不可复用           | 跨项目共享         |
| **版本控制** | 不便追踪           | Git 管理，版本清晰 |

**实际效果对比**:

```bash
# 不使用 Skills
用户: 创建一个包含表格的 PDF
Agent: 我会尝试...（可能出现格式错误、布局问题）

# 使用 PDF Skill
用户: 创建一个包含表格的 PDF
Agent: (加载 pdf skill)
     → 按照标准流程
     → 使用推荐的库
     → 应用最佳实践
     → 生成专业 PDF（格式正确、布局美观）
```

#### 创建自定义 Skills

可以使用 `skill-creator` skill 来创建自己的专业 skills：

**步骤 1: 规划 Skill**

```bash
用户: 使用 skill-creator 帮我创建一个数据可视化的 skill

Agent: (加载 skill-creator)
     → 引导问题:
       1. Skill 的主要功能是什么？
       2. 目标用户是谁？
       3. 需要哪些依赖？
       4. 常见使用场景？
```

**步骤 2: 生成 SKILL.md**

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

**步骤 3: 添加资源文件**

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

**步骤 4: 测试和优化**

```bash
# 测试 skill
用户: 使用 data-visualization skill 创建一个销售数据的柱状图

Agent: (加载新 skill)
     → 检查数据格式
     → 选择合适的模板
     → 应用配置
     → 生成图表
```

#### Skills 最佳实践

**1. 什么时候创建新 Skill？**

✅ **适合创建 Skill**:
- 复杂的多步骤任务（> 5 步）
- 需要专业知识的领域
- 频繁重复的工作流程
- 有明确的最佳实践

❌ **不适合创建 Skill**:
- 简单的一次性任务
- 过于通用的指导
- 频繁变化的需求

**2. Skill 设计原则**

```markdown
# 好的 Skill 设计
---
name: my-skill
description: 详细描述功能、适用场景、前置条件
---

## 目标
明确说明这个 skill 要解决什么问题

## 前置条件
列出所需的依赖、工具、环境

## 步骤
1. 第一步（具体、可操作）
2. 第二步（附带代码示例）
3. ...

## 示例
提供完整的使用示例

## 最佳实践
列出经验总结和技巧

## 常见问题
预防性地列出可能遇到的问题和解决方案
```

**3. Skill 维护**

```bash
# 定期更新 skill
1. 收集用户反馈
2. 记录常见错误
3. 更新最佳实践
4. 添加新的示例
5. 提交到版本控制

# 版本管理
git commit -m "feat(pdf-skill): Add form filling examples"
git commit -m "fix(canvas-design): Update font loading path"
git commit -m "docs(mcp-builder): Clarify error handling"
```

#### Skills 生态系统

**官方 Skills（已集成）**:
- ✅ 20+ 专业 skills
- ✅ 持续更新和维护
- ✅ 社区验证

**自定义 Skills**:
- ✅ 根据团队需求定制
- ✅ 内部知识库和流程
- ✅ 专有工具集成

**共享 Skills**:
- ✅ 发布到 GitHub
- ✅ 与社区分享
- ✅ 收集反馈改进

#### 小结

Skills 系统是 mini-agent 项目的创新特性之一，具有以下核心优势：

- **知识共享**：将专业知识标准化、结构化
- **持续演进**：便于更新迭代和长期维护
- **快速扩展**：通过添加新 Skills 快速获得新能力
- **精准执行**：提供具体可操作的指导

通过 Skills 机制，Agent 能够从通用助手提升为特定领域的专业系统。

---

### 3.2 Note Tool - 跨对话记忆 ⭐

这是区分 Demo 和生产级 Agent 的关键特性之一。

#### 核心理念

**传统方式** (❌ 不推荐):
```python
# 保存所有对话历史
messages = [msg1, msg2, msg3, ..., msg100]  # 会超出 context window!
```

**Note Tool 方式** (✅ 推荐):
```python
# Agent 主动决定什么需要记住
# 用户说："我喜欢简洁的代码风格，项目使用 Python 3.12"
# Agent 调用:
save_note(
    content="用户偏好：简洁代码风格；项目：Python 3.12",
    category="user_preference"
)

# 新对话中，Agent 需要时主动检索:
notes = read_note(category="user_preference")
# 返回: "用户偏好：简洁代码风格；项目：Python 3.12"
```

#### 实现示例

```python
class NoteTool(Tool):
    """持久化笔记工具"""

    @property
    def name(self) -> str:
        return "save_note"

    @property
    def description(self) -> str:
        return (
            "保存重要信息到持久化存储，用于跨对话记忆。"
            "适合保存：用户偏好、项目信息、重要决策、上下文关键点。"
            "每条笔记会自动添加时间戳。"
        )

    @property
    def parameters(self):
        return {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "要记住的信息（简洁但具体）"
                },
                "category": {
                    "type": "string",
                    "description": "分类标签",
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
        return f"✅ 已记录: {content}"
```

#### 使用效果

```
第一次对话:
用户: 我是 Python 开发者，项目使用 Python 3.12，喜欢类型提示
Agent: (主动调用 save_note)
      → 保存："项目=Python 3.12，偏好=类型提示"

---新会话---

第二次对话:
用户: 帮我写一个读取 JSON 文件的函数
Agent: (主动调用 read_note)
      → 想起："项目=Python 3.12，偏好=类型提示"
      → 生成带类型提示的代码:

      from pathlib import Path
      import json
      from typing import Dict, Any

      def read_json(file_path: str) -> Dict[str, Any]:
          return json.loads(Path(file_path).read_text())
```

#### 最佳实践

1. **什么时候保存笔记**:
   - ✅ 用户明确表达偏好时
   - ✅ 项目关键信息首次出现时
   - ✅ 用户纠正你的错误时
   - ❌ 不要保存每一句对话

2. **如何组织笔记**:
   - 使用清晰的分类 (category)
   - 内容要简洁但信息完整
   - 避免重复保存相似信息

3. **何时检索笔记**:
   - 新对话开始时主动检索
   - 用户询问"你记得..."时
   - 需要个性化响应时

### 3.3 上下文管理 - 防止超限

即使有 Note Tool，也需要管理对话历史：

```python
class MessageManager:
    """简单但有效的消息管理"""

    def __init__(self, max_messages: int = 20):
        self.max_messages = max_messages
        self.messages = []

    def add_message(self, message: Dict):
        """添加消息，自动截断"""
        self.messages.append(message)

        # 保留 system prompt + 最近 N 条消息
        if len(self.messages) > self.max_messages:
            self.messages = [
                self.messages[0],  # system prompt
                *self.messages[-(self.max_messages-1):]  # 最近的消息
            ]

    def get_messages(self) -> List[Dict]:
        return self.messages
```

**进阶版（生产环境）**:
- 使用 tiktoken 精确计算 token 数
- 根据消息重要性智能截断
- 工具调用结果自动摘要

### 3.4 流式输出 - 提升用户体验

```python
async def run_streaming(self, task: str):
    """流式返回结果，提升响应速度感知"""
    self.messages.append({"role": "user", "content": task})

    async with self.llm.stream(
        messages=self.messages,
        tools=self.get_tool_schemas()
    ) as stream:
        async for chunk in stream:
            if chunk.type == "content_block_delta":
                # 实时输出文本
                print(chunk.delta.text, end="", flush=True)

            elif chunk.type == "tool_use":
                # 执行工具调用
                result = await self.execute_tool(chunk)
                # ... 继续流式处理
```

**适用场景**:
- Web 应用中实时显示 Agent 思考过程
- 长时间运行的任务
- 需要用户交互确认的场景

---

## 4. 生产环境考虑

### 4.1 从 Demo 到生产的差距

基于 mini-agent 项目经验，以下是关键差异：

#### 开发时间对比
```
Demo:    2-3 天
生产:    3-6 个月
差距:    30-60x
```

### 4.2 生产级必备功能

#### 1. 高级笔记管理

**Demo 方案**:
- JSON 文件存储
- 简单的分类检索

**生产方案**:
- 向量数据库 (Milvus/Pinecone)
- 语义搜索（而非关键词匹配）
- 笔记去重和合并
- 重要性评分和自动过期
- 多级笔记架构（短期/长期/工作记忆）

**价值提升**：支持更复杂的长期对话场景，通过语义搜索智能检索相关记忆

#### 2. 模型 Fallback 机制

**Demo 方案**:
- 单一模型 (M2)
- 失败直接报错

**生产方案**:
- 多模型池管理
  - 主力: M2、Claude-3.5-Sonnet
  - 备用: GPT-4、Claude-Opus
  - 降级: Claude-Haiku、GPT-3.5
- 根据任务复杂度自动选择模型
- 失败时自动降级
- 成本优化（优先使用便宜模型）
- 健康检测和配额管理

**价值提升**：实现 99.9% 系统可用性，成本优化 30-50%

#### 3. 反思系统 (Reflection)

**Demo 方案**:
- 直接信任模型输出

**生产方案**:
- 工具调用前验证（参数、路径、命令安全性）
- 执行前预测："这个操作会做什么？"
- 执行后验证：对比结果与预期
- 自我反思：要求解释推理过程
- 多模型交叉验证

**价值提升**：减少 80% 以上的错误操作

#### 4. 监控和可观测性

**生产必备**:
```python
# 结构化日志
logger.info("tool_execution", extra={
    "tool_name": tool.name,
    "arguments": arguments,
    "duration_ms": duration,
    "success": result.success,
    "user_id": user_id,
    "session_id": session_id
})

# 指标收集
metrics.increment("agent.tool_calls", tags={
    "tool": tool.name,
    "status": "success" if result.success else "error"
})

# 链路追踪
with trace_span("agent.run", task=task):
    result = await self.run(task)
```

**价值提升**：快速定位问题根因，持续优化系统性能

### 4.3 安全性考虑

```python
class SecurityValidator:
    """工具调用安全性检查"""

    DANGEROUS_PATTERNS = [
        "rm -rf",
        "dd if=",
        "mkfs",
        "> /dev/",
        "chmod 777",
        "curl | bash"
    ]

    def validate_bash_command(self, command: str) -> bool:
        """验证 bash 命令安全性"""
        # 1. 危险命令检测
        if any(pattern in command for pattern in self.DANGEROUS_PATTERNS):
            logger.warning(f"Dangerous command blocked: {command}")
            return False

        # 2. 路径遍历检测
        if ".." in command or command.startswith("/etc"):
            logger.warning(f"Path traversal detected: {command}")
            return False

        # 3. 命令注入检测
        if ";" in command or "|" in command or "&&" in command:
            # 需要额外验证
            pass

        return True
```

### 4.4 性能优化

#### 并发执行工具调用

```python
async def execute_tools_parallel(self, tool_calls):
    """并发执行多个独立的工具调用"""
    tasks = [
        self.execute_tool(tc)
        for tc in tool_calls
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

**性能提升**：多工具调用场景下性能提升 3-5 倍

#### 结果缓存

```python
from functools import lru_cache

class CachedTool(Tool):
    @lru_cache(maxsize=100)
    async def execute(self, **kwargs):
        # 缓存相同参数的结果
        return await self._execute_impl(**kwargs)
```

**适用场景**：读取类工具（如 read_file、fetch_url 等）

---

## 5. 常见问题

### Q1: M2 和 Claude/GPT-4 相比如何选择？

**选择 M2 当**:
- 成本敏感的场景
- Agent 工作流（工具调用密集）
- 中文任务为主
- 需要快速响应

**选择 Claude/GPT-4 当**:
- 需要最强推理能力
- 创意性内容生成
- 复杂的代码理解和生成
- 预算充足

**推荐策略**：混合使用多模型
- M2 作为主力模型（处理 80% 任务）
- 复杂任务自动切换到 Claude/GPT-4
- 配置完善的 Fallback 机制

### Q2: 如何调试 Agent 的错误行为？

**三步调试法**:

1. **记录详细日志**
```python
logger.info(f"Step {step}: LLM Response", extra={
    "content": response.content,
    "tool_calls": response.tool_calls,
    "stop_reason": response.stop_reason
})
```

2. **可视化执行流程**
```
[用户] 创建一个 Python 文件
  ↓
[Agent] 调用 write_file(path="demo.py", content="...")
  ↓
[Tool] ✅ 文件创建成功
  ↓
[Agent] 调用 read_file(path="demo.py")
  ↓
[Tool] ✅ 返回文件内容
  ↓
[Agent] "文件已创建，内容如下..."
```

3. **回放和分析**
```python
# 保存每一步的状态
session.save_step({
    "messages": self.messages.copy(),
    "tool_call": tool_call,
    "result": result
})

# 后续可以回放整个执行过程
session.replay(from_step=5)
```

### Q3: Agent 经常执行错误的工具调用怎么办？

**可能原因和解决方案**:

1. **工具描述不清晰**
   - ❌ "读取文件"
   - ✅ "读取指定路径的文本文件内容。支持 .txt/.py/.md 等格式"

2. **缺少使用示例**
```python
description = """
读取文件内容。

示例:
- read_file(file_path="config.yaml")  # 读取配置文件
- read_file(file_path="./data/users.json")  # 读取数据文件
"""
```

3. **System Prompt 约束不足**
```python
system_prompt = """
工具使用规则：
1. 执行文件操作前，先用 bash("ls") 确认路径存在
2. 写入文件前，先用 read_file 检查是否会覆盖重要内容
3. 不确定时，询问用户而不是猜测
"""
```

### Q4: 如何处理 Agent 陷入循环？

**检测循环**:
```python
class LoopDetector:
    def __init__(self, window_size=5):
        self.recent_actions = deque(maxlen=window_size)

    def detect_loop(self, action: str) -> bool:
        """检测是否陷入循环"""
        self.recent_actions.append(action)

        # 如果最近 5 次操作都相同
        if len(self.recent_actions) == self.window_size:
            if len(set(self.recent_actions)) == 1:
                return True

        return False

# 使用
if loop_detector.detect_loop(f"{tool_name}:{arguments}"):
    # 打断循环，向 LLM 提示
    self.messages.append({
        "role": "user",
        "content": "检测到重复操作，请尝试不同的方法。"
    })
```

---

## 总结

### 关键要点

1. **工具定义要清晰**: 这是 Agent 能力的基础
2. **System Prompt 要明确**: 定义行为边界和工作流程
3. **Note Tool 是关键**: 区分 Demo 和生产的核心特性之一
4. **错误处理要完善**: 优雅降级比完美执行更重要
5. **安全性优先**: 验证所有用户输入和工具调用

### 参考资源

- **MiniMax 官方文档**：https://platform.minimaxi.com/docs
- **Mini Agent 项目**：https://github.com/MiniMax-AI/Mini-Agent
- **技术支持**：通过 MiniMax 开放平台获取

---

## 附录：完整示例代码

参见 [mini-agent](https://github.com/MiniMax-AI/Mini-Agent) 项目，包含：

- ✅ 基础 Agent 实现
- ✅ Note Tool 完整实现
- ✅ 4 个核心工具 (Read/Write/Edit/Bash)
- ✅ 完整的测试用例
- ✅ 详细的文档和注释

**快速上手**:
```bash
# 克隆项目
git clone https://github.com/MiniMax-AI/Mini-Agent mini-agent
cd mini-agent

# 安装依赖
uv sync

# 配置 API Key
cp config-example.yaml config.yaml
# 然后编辑 config.yaml 填入你的 API Key

# 运行交互式 Agent
uv run python main.py
```

---

**文档版本**：v1.2
**最后更新**：2025-10-27
**适用模型**：MiniMax M2 系列
**基于项目**：mini-agent

**版权声明**：© 2025 MiniMax. All rights reserved.
