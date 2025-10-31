

# Mini Agent

[English](./README.md) | 中文

一个**最小化但有水平**的 single agent 演示项目，展示了 agent 的核心执行链路和生产级特性。

## 快速开始

### 1. 安装依赖（使用 uv）

推荐使用 [uv](https://github.com/astral-sh/uv) 作为包管理器：

```bash
# 安装 uv（如果还没有）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 同步依赖
uv sync
```

或者使用传统方式：

```bash
pip install -e .
```

### 2. 获取 MiniMax API Key

访问 [MiniMax 开放平台](https://platform.minimaxi.com) 注册账号。

获取 API Key：
1. 登录后进入 **账户管理 > 接口密钥**
2. 点击 **"创建新的密钥"**
3. 复制并妥善保存（密钥只显示一次）

### 3. 配置 API Key

```bash
# 复制配置模板
cp mini_agent/config-example.yaml mini_agent/config.yaml

# 编辑配置文件，填入你的 API Key
vim mini_agent/config.yaml
```

配置示例：

```yaml
api_key: "YOUR_API_KEY_HERE"
api_base: "https://api.minimax.io/anthropic"
model: "MiniMax-M2"
max_steps: 50
workspace_dir: "./workspace"
```

> 📖 完整配置说明：查看 [config-example.yaml](mini_agent/config-example.yaml)

### 4. 初始化 Claude Skills（推荐）⭐

本项目通过 git submodule 集成了 Claude 官方的 skills 仓库。首次克隆后需要初始化：

```bash
# 初始化 submodule
git submodule update --init --recursive
```

**Skills 提供了 20+ 专业能力**，让 Agent 像专业人士一样工作：
- 📄 **文档处理**：创建和编辑 PDF、DOCX、XLSX、PPTX
- 🎨 **设计创作**：生成艺术作品、海报、GIF 动画
- 🧪 **开发测试**：网页自动化测试（Playwright）、MCP 服务器开发
- 🏢 **企业应用**：内部沟通、品牌规范、主题定制

**✨ 这是本项目的核心亮点之一**，详细说明请查看下方 "配置 Skills" 章节。

更多信息请参考：
- [Claude Skills 官方文档](https://github.com/anthropics/skills)
- [Anthropic 博客：Equipping agents for the real world](https://anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)

### 5. 配置 Skills（可选）⭐

**Claude Skills** 让 Agent 像专业人士一样工作，提供 20+ 专业技能包：

**核心能力：**
- 📄 **文档处理** - PDF、Word、Excel、PowerPoint
- 🎨 **设计创作** - 海报、GIF 动画、主题设计
- 🧪 **开发测试** - Playwright 测试、MCP 服务器开发
- 🏢 **企业应用** - 品牌指南、内部沟通、主题定制

**快速启用：**

```bash
# 初始化 Skills（首次使用）
git submodule update --init --recursive
```

Skills 会被自动加载，Agent 根据任务智能选择合适的 skill。

> 📖 完整 Skills 列表和使用指南：[skills/README.md](./skills/README.md)
> 📚 官方文档：https://github.com/anthropics/skills

---

### 6. 配置 MCP 工具（可选）

项目集成了 **2 个核心 MCP 工具**，配置在 `mcp.json` 中：

#### 🧠 Memory - 知识图谱记忆系统
- **功能**：提供基于图数据库的长期记忆存储和检索
- **状态**：默认启用（`disabled: false`）
- **配置**：无需 API Key，开箱即用

#### 🔍 MiniMax Search - 网页搜索和浏览 ⭐
- **功能**：提供 `search`（搜索）、`parallel_search`（并行搜索）、`browse`（智能浏览）三个工具
- **状态**：默认禁用，需要配置后启用
- **配置步骤**：
  1. 在 `mcp.json` 的 `minimax_search` 下配置环境变量：
     - `JINA_API_KEY`: 用于网页读取（申请：https://jina.ai）
     - `SERPER_API_KEY`: 用于 Google 搜索（申请：https://serpapi.com）
     - `BRAVE_API_KEY`: 用于 Brave 搜索，可选（申请：https://brave.com/search/api/）
     - `MINIMAX_TOKEN` / `BILLING_TOKEN`: 用于浏览功能的 LLM 调用
  2. 将 `disabled` 改为 `false`

**本地开发**：如需使用本地版本的 MiniMax Search，修改 `args` 为：
```json
["--from", "/path/to/local/minimax-search", "minimax-search"]
```

> 🔗 更多 MCP 工具：https://github.com/modelcontextprotocol/servers

### 7. 运行示例

**交互式运行**

```bash
uv run python main.py
```

特性：彩色输出、多轮对话、会话统计

常用命令：`/help`, `/clear`, `/history`, `/stats`, `/exit`

## 特性

### 核心功能
- ✅ **Agent 多轮执行循环**: 完整的工具调用链路
- ✅ **基础工具集**: Read / Write / Edit 文件 + Bash 命令
- ✅ **Session Note Tool**: Agent 主动记录和检索会话要点 ⭐
- ✅ **Claude Skills 集成**: 20+ 专业技能（文档、设计、测试、开发）⭐💡 🆕
- ✅ **MCP 工具集成**: Memory（知识图谱）+ MiniMax Search（网页搜索）⭐ 🆕
- ✅ **MiniMax M2 模型**: 通过 Anthropic 兼容端点

### 进阶特性 ⭐
- ✅ **持久化笔记**: Agent 跨会话和执行链路保持上下文
- ✅ **智能记录**: Agent 自主判断什么信息需要记录
- ✅ **多轮会话**: 支持会话管理、历史清除、统计等功能 🆕
- ✅ **美化交互**: 彩色终端输出，清晰的会话界面 🆕
- ✅ **简洁但完整**: 展示核心功能，避免过度复杂

## 项目结构

```
mini-agent/
├── README.md              # 本文档
├── mcp.json              # MCP 工具配置（指向外部 MCP 服务器）⭐
├── system_prompt.txt     # System prompt
├── pyproject.toml        # Python 项目配置
├── skills/               # Claude Skills (git submodule) 🆕
│   ├── example-skills/   # 官方示例 skills
│   ├── document-skills/  # 文档处理 skills
│   └── ...
├── mini_agent/
│   ├── config-example.yaml # API 配置示例
│   ├── agent.py          # 核心 Agent
│   ├── llm.py            # LLM 客户端 (Anthropic 兼容)
│   ├── config.py         # 配置加载器 🆕
│   └── tools/
│       ├── base.py       # 工具基类
│       ├── file_tools.py # 文件工具
│       ├── bash_tool.py  # Bash 工具
│       ├── note_tool.py  # Session Note 工具 ⭐
│       ├── mcp_loader.py # MCP 加载器（支持外部服务器）⭐
│       ├── skill_loader.py # Skill 加载器 🆕
│       └── skill_tool.py # Skill 工具 🆕
├── tests/
│   ├── test_agent.py     # Agent 集成测试
│   ├── test_llm.py       # LLM 测试
│   ├── test_note_tool.py # Session Note Tool 测试 ⭐
│   ├── test_tools.py     # 工具单元测试
│   ├── test_integration.py # 集成测试
│   ├── test_mcp.py       # MCP 测试
│   ├── test_git_mcp.py   # Git MCP 加载测试 ⭐
│   ├── test_skill_loader.py # Skill Loader 测试 🆕
│   ├── test_skill_tool.py   # Skill Tool 测试 🆕
│   └── test_session_integration.py # 会话集成测试 🆕
├── docs/
│   ├── M2_Agent_Best_Practices_CN.md # M2 最佳实践（中文）
│   └── M2_Agent_Best_Practices_EN.md # M2 最佳实践（英文）
└── main.py              # 交互式运行入口

外部 MCP 服务器:
../minimax-search/        # MiniMax Search MCP Server（独立项目）⭐
├── server.py             # MCP Server 入口
├── utils/                # 搜索和浏览实现
├── pyproject.toml        # 独立项目配置
└── README.md             # 独立文档
```

## 核心实现

### 1. Agent 执行流程

```python
# 简化的核心循环（来自 agent.py）
async def run(self) -> str:
    step = 0
    while step < self.max_steps:
        # 1. 调用 LLM
        response = await self.llm.generate(messages, tools)

        # 2. 如果没有工具调用，任务完成
        if not response.tool_calls:
            return response.content

        # 3. 执行工具调用
        for tool_call in response.tool_calls:
            result = await tool.execute(**arguments)
            self.messages.append(tool_result_message)

        step += 1
```

### 2. Session Note Tool - 会话笔记记录 ⭐

这是本 demo 的**核心亮点**之一，展示了一种简洁高效的会话记忆管理方式。

#### 核心概念

与传统的消息历史管理不同，**Session Note Tool 让 Agent 主动决定什么需要记录**：

- ❌ **传统方式**：被动保存所有对话，容易超出 token 限制
- ✅ **Session Note Tool**：Agent 主动记录关键要点，持久化存储

#### 工具说明

Session Note Tool 提供了两个核心功能：

1. **记录笔记** (`record_note`)：将重要信息保存到持久化存储
   - 支持分类标签（如 user_preference, project_info）
   - 自动添加时间戳
   - JSON 格式存储

2. **回忆笔记** (`recall_notes`)：检索之前记录的信息
   - 支持按类别过滤
   - 返回格式化的笔记列表
   - 跨会话访问

#### 使用示例

**Agent 主动记录笔记**:

```
用户: 我是一个 Python 开发者，项目使用 Python 3.12，喜欢简洁的代码

Agent: (主动调用 record_note)
→ record_note(
    content="项目使用 Python 3.12，喜欢简洁代码风格",
    category="user_preference"
  )
```

**Agent 回忆笔记**:

```
用户: (新会话) 你还记得我的项目信息吗？

Agent: (主动调用 recall_notes)
→ recall_notes()
→ 获取: "项目使用 Python 3.12，喜欢简洁代码风格"
→ 回答: "我记得！你的项目使用 Python 3.12..."
```

#### 笔记文件格式

笔记以 JSON 格式存储在 `workspace/.agent_memory.json`:

```json
[
  {
    "timestamp": "2025-10-24T17:20:50.340607",
    "category": "project_info",
    "content": "项目名称=mini-agent，使用技术=Python 3.12, async/await"
  },
  {
    "timestamp": "2025-10-24T17:21:30.123456",
    "category": "user_preference",
    "content": "喜欢简洁的代码风格"
  }
]
```

### 3. MiniMax Search - 网页搜索和浏览 ⭐

这是一个**独立的 MCP Server**，通过 `mcp.json` 集成到 Agent 中。

**仓库地址**: `https://github.com/MiniMax-AI/minimax_search`

#### 核心功能

**MiniMax Search 提供三个工具**：

1. **search** - 网页搜索
   - 支持多个搜索引擎 (Google, Bing, Jina, Brave, Sougo)
   - 支持 Google 高级搜索语法
   - 自动重试和引擎切换

2. **parallel_search** - 并行搜索
   - 同时搜索多个查询
   - 提高搜索效率

3. **browse** - 智能网页浏览
   - 使用 Jina Reader 读取网页内容
   - 使用 LLM 理解和回答问题
   - 自动生成网页摘要

#### 使用示例

**简单搜索**:
```
用户: 帮我搜索 Python asyncio 教程

Agent: (调用 search 工具)
→ 返回: 相关教程链接和摘要
```

**并行搜索**:
```
用户: 同时搜索 "Python asyncio" 和 "Python threading"

Agent: (调用 parallel_search 工具)
→ 返回: 两个查询的搜索结果
```

**网页浏览**:
```
用户: 访问 https://docs.python.org 并总结 asyncio 功能

Agent: (调用 browse 工具)
→ 返回: LLM 生成的网页摘要
```

#### 技术实现

- **配置化 API Keys**: 从 config.yaml 读取，支持灵活配置
- **多引擎支持**: 5 个搜索引擎，自动回退
- **中英文优化**: 自动识别并选择合适的搜索引擎
- **MCP 协议**: 标准 MCP Server 实现


---

### 4. 工具定义

每个工具继承自 `Tool` 基类：

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

工具的 schema 通过 `to_schema()` 自动转换为 OpenAI function calling 格式，然后在 LLM 客户端转换为 Anthropic 格式。

## 🏭 生产环境部署

本项目是教学级 Demo，展示核心概念。生产环境需要更多考虑：

- 🧠 **高级记忆管理** - 向量数据库、语义搜索
- 🔄 **模型 Fallback** - 多模型池、智能降级
- 🛡️ **反思系统** - 防止模型幻觉和错误操作
- 📊 **监控告警** - 完整的可观测性方案

> 📖 完整指南：[生产环境部署指南](docs/PRODUCTION_GUIDE.md)

---

## 🧪 测试

项目包含完整的测试用例，覆盖单元测试、功能测试和集成测试。

### 快速运行

```bash
# 运行所有测试
pytest tests/ -v

# 运行核心功能测试
pytest tests/test_agent.py tests/test_note_tool.py -v
```

### 测试覆盖

- ✅ **单元测试** - 工具类、LLM 客户端
- ✅ **功能测试** - Session Note Tool、MCP 加载
- ✅ **集成测试** - Agent 端到端执行
- ✅ **外部服务** - Git MCP Server 加载

> 📖 详细测试指南：[开发文档](docs/DEVELOPMENT.md#测试指南)

---

## 总结

本项目是一个**教学友好**但**技术完整**的 Agent 实现：

✅ **足够简单**: 代码量少，易于理解
✅ **足够完整**: 包含核心功能和 Session Note Tool
✅ **展示鸿沟**: 清晰对比 Demo 和生产环境的巨大差异

适合用于：
- 🎓 学习 Agent 架构和工作原理
- 🧪 快速实验和原型验证
- 📚 理解生产环境的复杂性

**不适合**直接用于生产环境。

## 📚 相关文档

- [生产环境部署指南](docs/PRODUCTION_GUIDE.md) - 从 Demo 到生产的完整指南
- [开发文档](docs/DEVELOPMENT.md) - 开发、测试和扩展指南
- [M2 Agent 最佳实践（中文）](docs/M2_Agent_Best_Practices_CN.md)
- [M2 Agent Best Practices (English)](docs/M2_Agent_Best_Practices_EN.md)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

- [贡献指南](CONTRIBUTING.md) - 如何参与贡献
- [行为准则](CODE_OF_CONDUCT.md) - 社区准则

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源许可证。

## 🔗 参考资源

- MiniMax API: https://platform.minimaxi.com/document
- MiniMax-M2: https://github.com/MiniMax-AI/MiniMax-M2
- Anthropic API: https://docs.anthropic.com/claude/reference
- Claude Skills: https://github.com/anthropics/skills
- MCP Servers: https://github.com/modelcontextprotocol/servers

---

**⭐ 如果这个项目对你有帮助，欢迎给个 Star！**
