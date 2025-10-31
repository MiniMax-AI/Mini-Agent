# 开发指南

> Mini Agent 项目的开发、测试和扩展指南

## 目录

- [1. 开发环境配置](#1-开发环境配置)
- [2. 项目架构](#2-项目架构)
- [3. 测试指南](#3-测试指南)
- [4. 扩展开发](#4-扩展开发)
- [5. 代码规范](#5-代码规范)

---

## 1. 开发环境配置

### 1.1 环境要求

- Python 3.11+
- uv (包管理器)
- Git

### 1.2 克隆项目

```bash
git clone https://github.com/MiniMax-AI/Mini-Agent mini-agent
cd mini-agent

# 初始化 submodules（Skills）
git submodule update --init --recursive
```

### 1.3 安装依赖

```bash
# 使用 uv（推荐）
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync

# 或使用 pip
pip install -e .
```

### 1.4 配置开发环境

```bash
# 复制配置文件
cp mini_agent/config-example.yaml mini_agent/config.yaml

# 编辑配置文件，填入 API Keys
vim mini_agent/config.yaml
```

### 1.5 运行项目

```bash
# 交互式运行
uv run python main.py

# 或直接运行 Python
python main.py
```

---

## 2. 项目架构

### 2.1 目录结构

```
mini-agent/
├── mini_agent/              # 核心代码
│   ├── agent.py             # Agent 主循环
│   ├── llm.py               # LLM 客户端
│   ├── config.py            # 配置加载
│   └── tools/               # 工具实现
│       ├── base.py          # 工具基类
│       ├── file_tools.py    # 文件工具
│       ├── bash_tool.py     # Bash 工具
│       ├── note_tool.py     # Session Note Tool
│       ├── mcp_loader.py    # MCP 加载器
│       ├── skill_loader.py  # Skills 加载器
│       └── skill_tool.py    # Skills 工具
├── tests/                   # 测试代码
├── skills/                  # Claude Skills (submodule)
├── docs/                    # 文档
├── workspace/               # 工作目录
├── main.py                  # 交互式入口
└── pyproject.toml           # 项目配置
```

### 2.2 核心组件

#### Agent (agent.py)

Agent 是核心执行引擎，负责：
- 管理对话历史
- 调用 LLM 生成响应
- 执行工具调用
- 控制执行循环

```python
class Agent:
    async def run(self, user_input: str) -> str:
        """主执行循环"""
        step = 0
        while step < self.max_steps:
            # 1. 调用 LLM
            response = await self.llm.generate(...)
            
            # 2. 如果没有工具调用，返回结果
            if not response.tool_calls:
                return response.content
            
            # 3. 执行工具调用
            for tool_call in response.tool_calls:
                result = await tool.execute(...)
            
            step += 1
```

#### LLM Client (llm.py)

LLM 客户端封装了与 MiniMax M2 的交互：
- 兼容 Anthropic API 格式
- 支持流式输出
- 工具调用格式转换

```python
class LLMClient:
    async def generate(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        stream: bool = False
    ) -> LLMResponse:
        """生成响应"""
        # 转换为 Anthropic 格式
        # 调用 API
        # 解析响应
```

#### Tool System (tools/)

工具系统基于继承架构：
- `Tool` - 抽象基类
- 具体工具实现（ReadTool, WriteTool, BashTool 等）
- 工具管理器负责注册和调用

```python
class Tool(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称"""
    
    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述"""
    
    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """参数 schema"""
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """执行工具"""
```

---

## 3. 测试指南

### 3.1 测试架构

#### 测试分层

```
├── 单元测试 (Unit Tests)
│   ├── test_tools.py           # 文件工具、Bash 工具
│   └── test_llm.py             # LLM 客户端
│
├── 功能测试 (Feature Tests)
│   ├── test_note_tool.py       # Session Note Tool（记忆功能）⭐
│   └── test_mcp.py             # MCP 加载器
│
├── 集成测试 (Integration Tests)
│   ├── test_agent.py           # Agent 端到端执行
│   └── test_integration.py     # 完整系统集成
│
└── 外部服务测试 (External Service Tests)
    └── test_git_mcp.py         # Git 仓库 MCP Server 加载 ⭐
```

#### 测试覆盖率

| 层级         | 覆盖范围               | 测试文件数 | 关键特性   |
| ------------ | ---------------------- | ---------- | ---------- |
| 单元测试     | 工具类、LLM 客户端     | 2          | 快速反馈   |
| 功能测试     | Session Note、MCP 加载 | 2          | 关键功能 ⭐ |
| 集成测试     | Agent 执行链路         | 2          | 端到端     |
| 外部服务测试 | Git MCP Server         | 1          | 生产环境 ⭐ |
| **总计**     | **完整测试覆盖**       | **7**      | -          |

### 3.2 运行测试

#### 快速测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_agent.py -v

# 显示详细输出（包括 print）
pytest tests/ -v -s

# 只运行标记的测试
pytest tests/ -v -m "not slow"
```

#### 测试命令详解

```bash
# 单元测试（快速，无外部依赖）
pytest tests/test_tools.py tests/test_llm.py -v

# 功能测试（Session Note Tool 等）
pytest tests/test_note_tool.py tests/test_mcp.py -v

# 集成测试（端到端，需要 API Key）
pytest tests/test_agent.py tests/test_integration.py -v

# Git MCP Server 测试（需要网络和 Git 权限）
pytest tests/test_git_mcp.py -v
```

### 3.3 测试设计原则

1. **快速单元测试** - 毫秒级响应，无外部依赖
2. **隔离功能测试** - 测试单一功能，易于调试
3. **真实集成测试** - 使用真实 API，验证完整链路
4. **独立外部测试** - MCP Server 独立测试，不依赖 pytest

### 3.4 关键测试点

#### Session Note Tool 测试 (`test_note_tool.py`)

- ✅ 记录笔记功能 (`record_note`)
- ✅ 回忆笔记功能 (`recall_notes`)
- ✅ 笔记持久化（JSON 文件）
- ✅ 类别过滤 (`category`)
- ✅ 跨会话记忆

```python
# 示例测试
def test_session_note_tool():
    tool = SessionNoteTool()
    
    # 测试记录笔记
    result = await tool.execute(
        action="record",
        content="用户喜欢简洁代码",
        category="user_preference"
    )
    assert result.success
    
    # 测试回忆笔记
    result = await tool.execute(action="recall")
    assert "用户喜欢简洁代码" in result.content
```

#### Git MCP 加载测试 (`test_git_mcp.py`)

- ✅ Git 仓库克隆 (`uvx --from git+ssh://...`)
- ✅ 依赖安装和构建
- ✅ MCP Server 启动
- ✅ 工具加载验证（search, parallel_search, browse）
- ✅ 异步资源清理 (`AsyncExitStack`)

```python
@pytest.mark.asyncio
async def test_git_mcp_loading():
    """测试从 Git 仓库加载 MCP Server"""
    loader = MCPLoader(config_path="mcp.json")
    tools = await loader.load_tools()
    
    assert "search" in tools
    assert "parallel_search" in tools
    assert "browse" in tools
```

### 3.5 测试数据管理

测试数据存储在 `workspace/` 目录：

```
workspace/
├── .agent_memory.json       # Session Note Tool 测试数据
├── test_file.txt            # 文件工具测试数据
└── test_output.txt          # 工具执行结果
```

**注意**: 测试后自动清理，无需手动管理。

---

## 4. 扩展开发

### 4.1 添加新工具

#### 步骤

1. 在 `mini_agent/tools/` 下创建工具文件
2. 继承 `Tool` 基类
3. 实现必需的属性和方法
4. 在 Agent 初始化时注册工具

#### 示例：创建自定义工具

```python
# mini_agent/tools/my_tool.py
from mini_agent.tools.base import Tool, ToolResult
from typing import Dict, Any

class MyTool(Tool):
    @property
    def name(self) -> str:
        """工具名称（必须唯一）"""
        return "my_tool"
    
    @property
    def description(self) -> str:
        """工具描述（会显示给 LLM）"""
        return "My custom tool for doing something useful"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """参数 schema（OpenAI function calling 格式）"""
        return {
            "type": "object",
            "properties": {
                "param1": {
                    "type": "string",
                    "description": "First parameter"
                },
                "param2": {
                    "type": "integer",
                    "description": "Second parameter",
                    "default": 10
                }
            },
            "required": ["param1"]
        }
    
    async def execute(self, param1: str, param2: int = 10) -> ToolResult:
        """
        执行工具逻辑
        
        Args:
            param1: 第一个参数
            param2: 第二个参数（有默认值）
        
        Returns:
            ToolResult: 执行结果
        """
        try:
            # 实现你的逻辑
            result = f"Processed {param1} with param2={param2}"
            
            return ToolResult(
                success=True,
                content=result
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content=f"Error: {str(e)}"
            )
```

#### 注册工具

```python
# main.py 或 agent 初始化代码
from mini_agent.tools.my_tool import MyTool

# 在创建 Agent 时添加工具
tools = [
    ReadTool(workspace_dir),
    WriteTool(workspace_dir),
    MyTool(),  # 添加自定义工具
]

agent = Agent(
    llm=llm,
    tools=tools,
    max_steps=50
)
```

### 4.2 添加测试

为新工具创建测试文件：

```python
# tests/test_my_tool.py
import pytest
from mini_agent.tools.my_tool import MyTool

@pytest.mark.asyncio
async def test_my_tool():
    """测试自定义工具"""
    tool = MyTool()
    
    # 测试正常执行
    result = await tool.execute(param1="test", param2=20)
    assert result.success
    assert "test" in result.content
    
    # 测试默认参数
    result = await tool.execute(param1="test")
    assert result.success
    
    # 测试错误处理
    # ...
```

### 4.3 自定义笔记存储

如果需要替换 Session Note Tool 的存储后端：

```python
# 当前实现：JSON 文件
class SessionNoteTool:
    def __init__(self, memory_file: str = "./workspace/.agent_memory.json"):
        self.memory_file = Path(memory_file)
    
    async def _save_notes(self, notes: List[Dict]):
        with open(self.memory_file, 'w') as f:
            json.dump(notes, f, indent=2, ensure_ascii=False)

# 扩展为：PostgreSQL
class PostgresNoteTool(Tool):
    def __init__(self, db_url: str):
        self.db = PostgresDB(db_url)
    
    async def _save_notes(self, notes: List[Dict]):
        await self.db.execute(
            "INSERT INTO notes (content, category, timestamp) VALUES ($1, $2, $3)",
            notes
        )

# 扩展为：向量数据库
class MilvusNoteTool(Tool):
    def __init__(self, milvus_host: str):
        self.vector_db = MilvusClient(host=milvus_host)
    
    async def _save_notes(self, notes: List[Dict]):
        # 生成 embedding
        embeddings = await self.get_embeddings([n["content"] for n in notes])
        
        # 存储到向量数据库
        await self.vector_db.insert(
            collection="agent_notes",
            data=notes,
            embeddings=embeddings
        )
```

### 4.4 添加新的 MCP 工具

编辑 `mcp.json` 添加新的 MCP Server：

```json
{
  "mcpServers": {
    "my_custom_mcp": {
      "description": "My custom MCP server",
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@my-org/my-mcp-server"],
      "env": {
        "API_KEY": "your-api-key"
      },
      "disabled": false,
      "notes": {
        "说明": "这是自定义 MCP 服务器",
        "API Key 申请": "https://example.com/api-keys"
      }
    }
  }
}
```

### 4.5 添加新的 Skill

创建自定义 Skill：

```bash
# 在 skills/ 目录下创建新的 skill
mkdir skills/my-custom-skill
cd skills/my-custom-skill

# 创建 SKILL.md
cat > SKILL.md << 'EOF'
---
name: my-custom-skill
description: 我的自定义 skill，用于处理特定任务
---

# 能力说明

这个 skill 提供以下能力：
- 能力 1
- 能力 2

# 使用步骤

1. 第一步...
2. 第二步...

# 最佳实践

- 实践 1
- 实践 2

# 常见问题

Q: 问题 1
A: 答案 1
EOF
```

Skill 会被 Agent 自动加载和识别。

---

## 5. 代码规范

### 5.1 代码风格

遵循 PEP 8 和 Google Python Style Guide：

```python
# ✅ 好的示例
class MyClass:
    """类的简短描述。
    
    详细描述...
    
    Attributes:
        attr1: 属性1的描述
        attr2: 属性2的描述
    """
    
    def my_method(self, param1: str, param2: int = 10) -> str:
        """方法的简短描述。
        
        Args:
            param1: 参数1的描述
            param2: 参数2的描述
        
        Returns:
            返回值的描述
        
        Raises:
            ValueError: 错误情况的描述
        """
        pass

# ❌ 不好的示例
class myclass:  # 类名应该用 PascalCase
    def MyMethod(self,param1,param2=10):  # 方法名应该用 snake_case，参数间要有空格
        pass  # 缺少 docstring
```

### 5.2 类型注解

使用 Python 类型注解：

```python
from typing import List, Dict, Optional, Union

async def process_messages(
    messages: List[Dict[str, Any]],
    max_tokens: Optional[int] = None
) -> Union[str, List[str]]:
    """处理消息列表"""
    pass
```

### 5.3 错误处理

```python
# ✅ 好的错误处理
try:
    result = await tool.execute(**params)
except FileNotFoundError as e:
    logger.error(f"文件未找到: {e}")
    return ToolResult(success=False, content=f"File not found: {e}")
except Exception as e:
    logger.exception("意外错误")
    return ToolResult(success=False, content=f"Unexpected error: {e}")

# ❌ 不好的错误处理
try:
    result = await tool.execute(**params)
except:  # 不要使用裸 except
    pass  # 不要忽略错误
```

### 5.4 日志

使用结构化日志：

```python
import logging

logger = logging.getLogger(__name__)

# ✅ 好的日志
logger.info(f"开始执行工具: {tool_name}")
logger.debug(f"工具参数: {params}")
logger.error(f"工具执行失败: {error}", exc_info=True)

# ❌ 不好的日志
print("开始执行")  # 不要使用 print
logger.info("失败")  # 缺少上下文信息
```

### 5.5 异步编程

```python
# ✅ 好的异步代码
async def process_items(items: List[str]) -> List[str]:
    """并发处理多个项目"""
    tasks = [process_item(item) for item in items]
    results = await asyncio.gather(*tasks)
    return results

# ❌ 不好的异步代码
async def process_items(items: List[str]) -> List[str]:
    results = []
    for item in items:
        # 串行处理，没有利用异步优势
        result = await process_item(item)
        results.append(result)
    return results
```

---

## 6. 故障排查

### 6.1 常见问题

#### API Key 配置错误

```bash
# 错误信息
Error: Invalid API key

# 解决方案
1. 检查 config.yaml 中的 API Key 是否正确
2. 确保没有多余的空格或引号
3. 验证 API Key 是否过期
```

#### 依赖安装失败

```bash
# 错误信息
uv sync failed

# 解决方案
1. 更新 uv 到最新版本: uv self update
2. 清理缓存: uv cache clean
3. 重新同步: uv sync
```

#### MCP 工具加载失败

```bash
# 错误信息
Failed to load MCP server

# 解决方案
1. 检查 mcp.json 中的配置是否正确
2. 确保 Node.js 已安装（MCP 工具需要）
3. 检查 API Keys 是否配置
4. 查看详细日志: pytest tests/test_mcp.py -v -s
```

### 6.2 调试技巧

#### 启用详细日志

```python
# main.py 或测试文件开头
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

#### 使用 Python 调试器

```python
# 在代码中设置断点
import pdb; pdb.set_trace()

# 或使用 ipdb（更友好）
import ipdb; ipdb.set_trace()
```

#### 查看工具调用

```python
# 在 Agent 中添加日志
logger.debug(f"工具调用: {tool_call.name}")
logger.debug(f"工具参数: {tool_call.arguments}")
logger.debug(f"工具结果: {result.content[:200]}")
```

---

## 7. 贡献指南

### 7.1 提交代码

1. Fork 项目
2. 创建特性分支: `git checkout -b feature/my-feature`
3. 提交更改: `git commit -m 'Add some feature'`
4. 推送到分支: `git push origin feature/my-feature`
5. 创建 Pull Request

### 7.2 代码审查

所有 PR 需要经过代码审查：
- ✅ 遵循代码规范
- ✅ 包含测试
- ✅ 更新文档
- ✅ 通过所有测试

### 7.3 提交消息规范

```bash
# 格式
<type>(<scope>): <subject>

# 示例
feat(tools): 添加新的文件搜索工具
fix(agent): 修复工具调用错误处理
docs(readme): 更新快速开始指南
test(note_tool): 添加笔记持久化测试
```

---

## 相关文档

- [README](../README.md) - 项目简介和快速开始
- [生产环境指南](./PRODUCTION_GUIDE.md) - 从 Demo 到生产
- [M2 最佳实践](./M2_Agent_Best_Practices_CN.md) - MiniMax M2 使用技巧

