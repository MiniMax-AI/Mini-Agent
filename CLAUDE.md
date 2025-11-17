# CLAUDE.md - Mini Agent 的 AI 助手指南

本文档为使用 Mini Agent 代码库的 AI 助手（如 Claude）提供全面指导。涵盖项目结构、开发工作流程、关键约定和最佳实践。始终使用中文回复用户。

## 项目概述

**Mini Agent** 是一个简洁而专业的演示项目，展示了使用 MiniMax M2 模型构建智能体的最佳实践。它使用兼容 Anthropic 的 API，并完全支持交错思维（interleaved thinking）来处理复杂的长时间运行任务。

### 核心特性

- 完整的智能体执行循环，带有基础文件系统和 shell 操作工具
- 通过会话笔记工具实现持久化记忆
- 智能上下文管理，支持自动对话摘要
- Claude Skills 集成（15 个专业技能，涵盖文档、设计、测试、开发）
- MCP（模型上下文协议）工具集成
- 用于调试的全面日志记录
- 多提供商 LLM 支持（Anthropic 和 OpenAI 协议）

### 技术栈

- **语言**: Python 3.10+
- **包管理器**: uv（现代 Python 包管理器）
- **测试**: pytest 配合 asyncio 支持
- **依赖**: httpx, pydantic, pyyaml, tiktoken, prompt-toolkit, mcp, anthropic, openai
- **构建系统**: setuptools

## 仓库结构

```
Mini-Agent/
├── mini_agent/                 # 核心源代码
│   ├── __init__.py
│   ├── agent.py                # 主智能体执行循环
│   ├── cli.py                  # 使用 prompt_toolkit 的命令行界面
│   ├── config.py               # 配置加载逻辑
│   ├── logger.py               # 全面的日志系统
│   ├── retry.py                # 指数退避的重试机制
│   ├── llm/                    # LLM 客户端抽象
│   │   ├── base.py             # LLM 客户端的抽象基类
│   │   ├── anthropic_client.py # Anthropic API 实现
│   │   ├── openai_client.py    # OpenAI API 实现
│   │   └── llm_wrapper.py      # LLMClient 工厂
│   ├── schema/                 # 数据模型
│   │   └── schema.py           # 消息、响应等的 Pydantic 模型
│   ├── tools/                  # 工具实现
│   │   ├── base.py             # 基础 Tool 类和 ToolResult
│   │   ├── file_tools.py       # ReadTool, WriteTool, EditTool
│   │   ├── bash_tool.py        # BashTool, BashOutputTool, BashKillTool
│   │   ├── note_tool.py        # 用于持久化记忆的 SessionNoteTool
│   │   ├── skill_tool.py       # Skill 工具 (get_skill)
│   │   ├── skill_loader.py     # 从子模块加载 Claude Skills
│   │   └── mcp_loader.py       # MCP 服务器集成
│   ├── skills/                 # Claude Skills（git 子模块）
│   ├── utils/                  # 工具函数
│   │   └── terminal_utils.py   # 终端显示宽度计算
│   └── config/                 # 配置文件
│       ├── config-example.yaml # 配置模板
│       ├── system_prompt.md    # 智能体的系统提示
│       └── mcp.json            # MCP 服务器配置
├── tests/                      # 测试套件
│   ├── test_agent.py           # 智能体集成测试
│   ├── test_llm.py             # LLM 客户端测试
│   ├── test_note_tool.py       # 会话笔记工具测试
│   ├── test_skill_tool.py      # Skill 工具测试
│   ├── test_mcp.py             # MCP 加载测试
│   └── ...
├── docs/                       # 文档
│   ├── DEVELOPMENT_GUIDE.md    # 详细开发指南
│   └── PRODUCTION_GUIDE.md     # 生产部署指南
├── scripts/                    # 设置和工具脚本
├── examples/                   # 使用示例
├── workspace/                  # 默认工作空间目录（已忽略）
├── pyproject.toml             # 项目配置和依赖
├── uv.lock                    # 锁定的依赖
├── README.md                  # 主文档
└── CONTRIBUTING.md            # 贡献指南
```

## 核心架构

### 1. 智能体执行循环

**文件**: `mini_agent/agent.py`

`Agent` 类实现了核心执行循环：

- **消息管理**: 维护对话历史记录并自动计算 token
- **上下文摘要**: 当超过 token 限制时自动摘要历史记录（默认：80,000 tokens）
- **工具执行**: 管理工具调用和结果
- **步骤限制**: 通过可配置的 max_steps 防止无限循环（默认：100）
- **工作空间管理**: 处理工作空间目录和路径解析

**关键方法**:
- `run(task: str)`: 任务的主执行循环
- `add_user_message(content: str)`: 向历史记录添加用户消息
- `_estimate_tokens()`: 使用 tiktoken 精确计算 token
- `_summarize_history()`: 智能上下文压缩

### 2. LLM 客户端抽象

**文件**: `mini_agent/llm/`

LLM 层已被抽象化以支持多个提供商：

- **`base.py`**: 定义 `LLMClientBase` 抽象接口
- **`anthropic_client.py`**: Anthropic Messages API 实现
- **`openai_client.py`**: OpenAI Chat Completions API 实现
- **`llm_wrapper.py`**: 根据配置创建适当客户端的工厂

**关键特性**:
- 与提供商无关的接口
- 自动 API 端点构建（附加 `/anthropic` 或 `/v1`）
- 指数退避的重试机制
- 思维块支持（针对支持它的模型）
- 工具调用标准化

**配置**:
```yaml
provider: "anthropic"  # 或 "openai"
api_key: "YOUR_API_KEY"
api_base: "https://api.minimax.io"
model: "MiniMax-M2"
```

### 3. 工具系统

**文件**: `mini_agent/tools/`

所有工具都继承自 `base.py` 中的 `Tool` 基类：

**工具接口**:
```python
class Tool:
    @property
    def name(self) -> str: ...

    @property
    def description(self) -> str: ...

    @property
    def parameters(self) -> dict[str, Any]: ...

    async def execute(self, *args, **kwargs) -> ToolResult: ...

    def to_schema(self) -> dict: ...  # Anthropic 格式
    def to_openai_schema(self) -> dict: ...  # OpenAI 格式
```

**内置工具**:
- **ReadTool**: 读取文件内容，支持可选的行范围
- **WriteTool**: 创建或覆盖文件
- **EditTool**: 使用旧/新字符串替换编辑现有文件
- **BashTool**: 执行带超时的 bash 命令
- **BashOutputTool**: 读取后台 bash 进程的输出
- **BashKillTool**: 终止后台 bash 进程
- **SessionNoteTool**: 用于会话记忆的持久化笔记
- **get_skill**: 动态加载 Claude Skills

### 4. 配置系统

**文件**: `mini_agent/config.py`

配置按优先级从 YAML 文件加载：
1. `mini_agent/config/config.yaml`（开发模式）
2. `~/.mini-agent/config/config.yaml`（用户配置）
3. 包安装目录配置

**关键配置选项**:
- `api_key`: MiniMax API 密钥
- `api_base`: API 端点 URL
- `model`: 模型名称（如 "MiniMax-M2"）
- `provider`: LLM 提供商（"anthropic" 或 "openai"）
- `max_steps`: 最大执行步数（默认：100）
- `workspace_dir`: 工作目录路径
- `system_prompt_path`: 系统提示文件路径
- `tools.*`: 工具启用/禁用开关
- `retry.*`: 重试配置

### 5. Skills 系统

**文件**: `mini_agent/tools/skill_tool.py`, `mini_agent/tools/skill_loader.py`

Claude Skills 使用**渐进式披露**从 `skills/` git 子模块加载：
- **第 1 级**: 启动时显示元数据（名称、描述）
- **第 2 级**: 通过 `get_skill(skill_name)` 加载完整内容
- **第 3 级及以上**: 根据需要加载额外的资源和脚本

**Skills 包括**: PDF、PPTX、DOCX、XLSX、canvas-design、algorithmic-art、testing、MCP-builder、skill-creator 等。

### 6. MCP 集成

**文件**: `mini_agent/tools/mcp_loader.py`

模型上下文协议（MCP）服务器在 `mcp.json` 中配置并动态加载。预配置的服务器包括：
- **memory**: 知识图谱记忆系统
- **minimax_search**: 网页搜索和浏览功能

## 开发工作流程

### 设置开发环境

```bash
# 克隆仓库
git clone https://github.com/MiniMax-AI/Mini-Agent.git
cd Mini-Agent

# 安装 uv（如果尚未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 同步依赖
uv sync

# 初始化 Claude Skills（可选）
git submodule update --init --recursive

# 复制配置模板
cp mini_agent/config/config-example.yaml mini_agent/config/config.yaml

# 使用你的 API 密钥编辑 config.yaml
# vim mini_agent/config/config.yaml
```

### 运行智能体

```bash
# 方法 1：作为模块运行（适合调试）
uv run python -m mini_agent.cli

# 方法 2：以可编辑模式安装（推荐）
uv tool install -e .
mini-agent
mini-agent --workspace /path/to/project

# 指定工作空间目录
mini-agent --workspace /path/to/your/project
```

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_agent.py -v

# 运行带覆盖率的测试
pytest tests/ -v --cov=mini_agent

# 运行核心功能测试
pytest tests/test_agent.py tests/test_note_tool.py -v
```

### 代码风格和约定

**提交信息格式**:
```
<类型>(<范围>): <描述>

类型:
- feat: 新功能
- fix: 错误修复
- docs: 文档更改
- style: 代码风格（格式化，无逻辑更改）
- refactor: 代码重构
- test: 测试更改
- chore: 构建/工具更改

示例:
- feat(tools): 添加新的文件搜索工具
- fix(agent): 修复工具调用的错误处理
- refactor(llm): 为多个提供商抽象 LLM 客户端
```

**Python 约定**:
- 所有函数参数和返回值都使用类型提示
- 所有类和公共方法都有文档字符串
- 使用 Pydantic 进行数据验证
- 使用 async/await 处理 I/O 操作
- 使用 pathlib.Path 处理文件路径

### 添加新工具

1. 在 `mini_agent/tools/` 中创建新文件：
```python
from mini_agent.tools.base import Tool, ToolResult
from typing import Dict, Any

class MyTool(Tool):
    @property
    def name(self) -> str:
        return "my_tool"

    @property
    def description(self) -> str:
        return "此工具的功能描述"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "param1": {
                    "type": "string",
                    "description": "第一个参数"
                }
            },
            "required": ["param1"]
        }

    async def execute(self, param1: str) -> ToolResult:
        try:
            # 工具逻辑在这里
            return ToolResult(success=True, content="结果")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
```

2. 在 `mini_agent/cli.py` 中注册工具：
```python
from mini_agent.tools.my_tool import MyTool

tools.append(MyTool())
```

3. 在 `tests/test_my_tool.py` 中添加测试

### 添加 MCP 工具

1. 编辑 `mini_agent/config/mcp.json`：
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

2. 如果 config.yaml 中设置了 `enable_mcp: true`，工具将在启动时自动加载

## AI 助手的关键约定

### 使用此代码库时

1. **始终使用 uv**: 此项目使用 `uv` 进行依赖管理，而不是 pip
   ```bash
   # 安装包
   uv pip install package-name

   # 运行 Python
   uv run python script.py

   # 同步依赖
   uv sync
   ```

2. **尊重工作空间**: 除非需要绝对路径，否则所有文件操作都应相对于 `workspace_dir`

3. **遵循工具模式**: 新工具必须继承自 `Tool` 并实现所有必需的属性

4. **测试你的更改**: 始终为新功能添加测试
   ```bash
   pytest tests/test_your_feature.py -v
   ```

5. **使用类型提示**: 所有新代码都应包含适当的类型注解

6. **优雅地处理错误**: 工具应返回 `ToolResult(success=False, error=...)` 而不是抛出异常

7. **配置优于代码**: 尽可能优先选择配置更改而不是代码修改

8. **记录你的工作**: 添加功能时更新相关文档

### 文件修改

**编辑文件之前**:
- 始终先读取文件以了解当前实现
- 对现有文件使用 EditTool，仅对新文件使用 WriteTool
- 保持现有的风格和格式
- 保持更改最小化和集中

**路径处理**:
- 对所有文件操作使用 `pathlib.Path`
- 支持绝对路径和工作空间相对路径
- 写入文件之前创建父目录

### 测试指南

**测试覆盖范围**:
- 单个工具的单元测试
- 工具交互的功能测试
- 完整智能体执行的集成测试
- 在测试中模拟外部 API 调用

**测试文件命名**:
- `test_<模块名>.py` 用于单元测试
- `test_<功能>_integration.py` 用于集成测试

### 日志和调试

**日志级别**:
- 项目使用自定义的 `AgentLogger` 类
- 日志写入工作空间目录
- 启用详细日志记录以进行调试

**调试技巧**:
- 检查 `workspace/*.log` 文件以获取详细的执行日志
- 在交互模式下使用 `/stats` 命令查看执行统计信息
- 启用思维块以查看模型推理

### 要避免的常见陷阱

1. **不要绕过工具接口**: 所有智能体功能都必须通过工具
2. **不要修改 git 子模块**: skills 目录是子模块，不要直接编辑
3. **不要提交 config.yaml**: 它包含 API 密钥并已被忽略
4. **不要使用 pip**: 始终使用 `uv` 进行包管理
5. **不要跳过测试**: 测试失败表示真实的问题
6. **不要硬编码路径**: 使用配置中的 workspace_dir
7. **不要忽略 token 限制**: 上下文摘要对长任务至关重要

### 使用 Git

**分支命名**:
- 功能分支：`feature/description`
- 错误修复：`fix/description`
- Claude 特定：`claude/claude-md-<session-id>`

**提交之前**:
1. 运行测试：`pytest tests/ -v`
2. 检查 git 状态：`git status`
3. 审查更改：`git diff`
4. 使用常规提交消息

**推送更改**:
```bash
# 推送到功能分支并重试
git push -u origin <分支名>

# 如果由于网络推送失败，使用指数退避重试
```

## 重要文件及其用途

| 文件 | 用途 |
|------|---------|
| `mini_agent/agent.py` | 核心智能体执行循环和上下文管理 |
| `mini_agent/cli.py` | 使用 prompt_toolkit 的交互式 CLI |
| `mini_agent/llm/llm_wrapper.py` | LLM 客户端工厂 |
| `mini_agent/config.py` | 配置加载逻辑 |
| `mini_agent/tools/base.py` | 基础 Tool 类 - 所有工具都继承自此 |
| `mini_agent/config/config-example.yaml` | 配置模板 |
| `mini_agent/config/system_prompt.md` | 智能体的系统提示 |
| `pyproject.toml` | 项目元数据和依赖 |
| `tests/test_agent.py` | 核心智能体功能测试 |

## API 文档链接

- **MiniMax API**: https://platform.minimaxi.com/document
- **MiniMax-M2**: https://github.com/MiniMax-AI/MiniMax-M2
- **Anthropic API**: https://docs.anthropic.com/claude/reference
- **Claude Skills**: https://github.com/anthropics/skills
- **MCP Servers**: https://github.com/modelcontextprotocol/servers

## 故障排除

### SSL 证书错误
如果遇到 `[SSL: CERTIFICATE_VERIFY_FAILED]`：
- 测试的快速修复：在 `mini_agent/llm/` 中的 httpx.AsyncClient 添加 `verify=False`
- 生产解决方案：`pip install --upgrade certifi`

### 模块未找到
确保从项目目录运行：
```bash
cd Mini-Agent
uv run python -m mini_agent.cli
```

### MCP 工具未加载
- 检查 `mcp.json` 配置
- 确保 config.yaml 中 `enable_mcp: true`
- 检查工作空间目录中的日志
- 验证 MCP 服务器依赖已安装

### Token 限制超出
- 上下文摘要应在 80,000 tokens 时自动触发
- 检查 config.yaml 中的 `token_limit`
- 在交互模式下使用 `/clear` 命令重置上下文

## AI 助手快速参考

**当被要求**:
- "添加功能" → 在 `mini_agent/tools/` 中创建新工具，添加测试，在 cli.py 中注册
- "修复错误" → 识别文件，读取它，进行最小更改，添加测试用例
- "运行测试" → `pytest tests/ -v`
- "部署" → 参见 `docs/PRODUCTION_GUIDE.md`
- "添加 MCP 工具" → 编辑 `mini_agent/config/mcp.json`
- "更改行为" → 首先检查是否可以在 `config.yaml` 中配置
- "添加 skill" → Skills 在子模块中，参见 `docs/DEVELOPMENT_GUIDE.md`

**记住**:
- 这是使用 `uv` 的 Python 项目，不是 npm/node
- 所有工具必须是异步的并返回 ToolResult
- 配置文件在 `mini_agent/config/` 中
- 提交前测试必须通过
- 遵循常规提交消息
- 尊重工作空间目录模式

---

**最后更新**: 2025-01-17
**项目版本**: 0.1.0
**维护者**: Mini Agent 团队
