# 工具优化指南

## 当前工具使用情况分析

### 问题现象

用户询问"昆仑万维有啥利好"，Agent 尝试使用 bash 工具执行网络搜索，但失败了：
```
🔧 Tool Call: bash
   Arguments: { "command": "curl -s \"https://www.baidu.com/s?wd=昆仑万维利好消息\" ..." }
✗ Error:
```

### 根本原因

1. **缺少专业的网络搜索工具**
   - 当前只有 7 个基础工具（文件操作、bash、会话笔记）
   - 没有网络搜索能力
   - Agent 只能用 bash + curl "凑合"，但在 Windows 上很容易失败

2. **MCP 搜索工具未启用**
   - `mini_agent/config/mcp.json` 中有 `minimax_search` 工具
   - 但设置为 `disabled: true`
   - 后端代码中有 `TODO: 添加 MCP tools`

3. **工具集不匹配使用场景**
   - 现有工具主要用于**编程任务**（读写代码、执行命令）
   - 缺少**信息检索**能力（网络搜索、知识查询）

---

## 当前已启用的工具

### ✅ 有用的工具

| 工具 | 用途 | 适用场景 |
|------|------|----------|
| **ReadTool** | 读取文件 | 查看代码、配置文件、文档 |
| **WriteTool** | 写入文件 | 生成代码、创建文档 |
| **EditTool** | 编辑文件 | 修改现有代码 |
| **SessionNoteTool** | 会话记忆 | 跨对话记住重要信息 |
| **BashOutputTool** | 后台进程输出 | 长时间运行的任务（如训练模型） |
| **BashKillTool** | 终止进程 | 停止后台任务 |

### ⚠️ 有限制的工具

| 工具 | 当前限制 | 改进建议 |
|------|---------|----------|
| **BashTool** | Windows 环境下 curl/wget 可能不可用 | 添加专门的网络搜索工具 |

---

## 优化方案

### 方案 1：限制 Bash 工具使用（临时方案）

在 system prompt 中明确告知 Agent 不要用 bash 做网络搜索：

**修改位置**：`mini_agent/config/system_prompt.md`

```markdown
### Bash Commands
- **DO NOT** use bash/curl/wget for web searches or API calls
- If you need web search, tell the user you don't have this capability yet
- Focus on file operations, git, and local command execution
```

**优点**：快速实施，避免无效的工具调用
**缺点**：Agent 失去网络搜索能力

### 方案 2：添加简单的网络搜索工具（快速方案）

创建一个基于 HTTP 请求的简单搜索工具：

**文件**：`backend/app/tools/web_search_tool.py`

```python
from mini_agent.tools.base import Tool, ToolResult
import requests
from typing import Dict, Any

class WebSearchTool(Tool):
    """网络搜索工具（使用 Serper API 或其他搜索 API）"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://google.serper.dev/search"

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return "在互联网上搜索信息。输入搜索关键词，返回相关的搜索结果。"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词"
                },
                "num_results": {
                    "type": "integer",
                    "description": "返回结果数量（默认 5）",
                    "default": 5
                }
            },
            "required": ["query"]
        }

    async def execute(self, query: str, num_results: int = 5) -> ToolResult:
        """执行搜索"""
        try:
            headers = {
                "X-API-KEY": self.api_key,
                "Content-Type": "application/json"
            }

            payload = {
                "q": query,
                "num": num_results
            }

            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=10
            )

            if response.status_code != 200:
                return ToolResult(
                    success=False,
                    error=f"搜索失败: HTTP {response.status_code}"
                )

            data = response.json()

            # 格式化结果
            results = []
            for item in data.get("organic", [])[:num_results]:
                results.append(
                    f"**{item['title']}**\n{item['snippet']}\n链接: {item['link']}\n"
                )

            content = "\n".join(results)

            return ToolResult(
                success=True,
                content=f"搜索结果（共 {len(results)} 条）：\n\n{content}"
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"搜索出错: {str(e)}"
            )
```

**集成到后端**：修改 `backend/app/services/agent_service.py:84-104`

```python
def _create_tools(self) -> List:
    """创建工具列表"""
    tools = [
        # 文件工具
        ReadTool(workspace_dir=str(self.workspace_dir)),
        WriteTool(workspace_dir=str(self.workspace_dir)),
        EditTool(workspace_dir=str(self.workspace_dir)),
        # Bash 工具
        BashTool(workspace_dir=str(self.workspace_dir)),
        BashOutputTool(),
        BashKillTool(),
        # 会话笔记工具
        SessionNoteTool(
            memory_file=str(self.workspace_dir / ".agent_memory.json")
        ),
    ]

    # 添加网络搜索工具（如果配置了 API Key）
    if hasattr(settings, 'serper_api_key') and settings.serper_api_key:
        from backend.app.tools.web_search_tool import WebSearchTool
        tools.append(WebSearchTool(api_key=settings.serper_api_key))

    return tools
```

**配置**：在 `.env` 中添加：
```env
# 搜索 API（可选）
SERPER_API_KEY="your-serper-api-key"  # 从 https://serper.dev 获取
```

**优点**：
- 快速实施，无需复杂的 MCP 配置
- 直接集成到后端服务
- 提供真正的网络搜索能力

**缺点**：
- 需要第三方 API Key
- 功能相对简单

### 方案 3：启用 MCP 搜索工具（完整方案）

启用已配置的 `minimax_search` MCP 工具：

**步骤 1**：修改 `mini_agent/config/mcp.json`

```json
{
  "mcpServers": {
    "minimax_search": {
      "description": "MiniMax Search - Powerful web search and intelligent browsing ⭐",
      "type": "stdio",
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/MiniMax-AI/minimax_search",
        "minimax-search"
      ],
      "env": {
        "JINA_API_KEY": "your-jina-api-key",
        "SERPER_API_KEY": "your-serper-api-key",
        "MINIMAX_API_KEY": "your-minimax-api-key"
      },
      "disabled": false  // 改为 false
    }
  }
}
```

**步骤 2**：在后端集成 MCP 工具

修改 `backend/app/services/agent_service.py:84-104`，实现 MCP 工具加载：

```python
def _create_tools(self) -> List:
    """创建工具列表"""
    tools = [
        # ... 现有工具 ...
    ]

    # 加载 MCP 工具
    from mini_agent.tools.mcp_loader import load_mcp_tools
    mcp_config_path = Path(__file__).parent.parent.parent.parent / "mini_agent" / "config" / "mcp.json"

    if mcp_config_path.exists():
        try:
            mcp_tools = load_mcp_tools(str(mcp_config_path))
            tools.extend(mcp_tools)
            print(f"   ✅ 加载了 {len(mcp_tools)} 个 MCP 工具")
        except Exception as e:
            print(f"   ⚠️  MCP 工具加载失败: {e}")

    return tools
```

**优点**：
- 功能最完整（搜索 + 智能浏览）
- 与 CLI 版本保持一致
- 支持多种搜索引擎

**缺点**：
- 配置相对复杂
- 需要多个 API Key
- 需要 Node.js/Python 环境支持

---

## 推荐方案

### 对于您的情况

**推荐：方案 2（添加简单的网络搜索工具）**

理由：
1. ✅ 快速实施（30 分钟内完成）
2. ✅ 满足基本需求（搜索最新信息）
3. ✅ 不需要复杂的 MCP 配置
4. ✅ 成本低（Serper API 免费额度：2500 次/月）

### 实施步骤

1. **获取 Serper API Key**
   - 访问 https://serper.dev
   - 注册并获取免费 API Key

2. **创建搜索工具**
   - 参考上面的 `WebSearchTool` 代码
   - 保存到 `backend/app/tools/web_search_tool.py`

3. **集成到服务**
   - 修改 `agent_service.py`
   - 添加到 `.env` 配置

4. **重启服务**
   - 重启后端
   - 测试搜索功能

---

## 其他工具优化建议

### 1. Skills 集成

目前 Skills 也未启用（`TODO: 添加 Skills`）。考虑启用：
- **pdf**: PDF 处理
- **pptx**: PPT 生成
- **docx**: Word 文档
- **xlsx**: Excel 处理

### 2. 工具使用监控

添加工具使用统计，了解哪些工具最常用：
```python
# 在 agent_service.py 中添加
self.tool_usage_stats = {}

def _track_tool_usage(self, tool_name: str):
    self.tool_usage_stats[tool_name] = self.tool_usage_stats.get(tool_name, 0) + 1
```

---

## 总结

**当前工具都是有用的**，但针对您的使用场景（信息检索），缺少关键的**网络搜索能力**。

建议：
1. 立即实施**方案 2**，添加基础网络搜索
2. 长期考虑**方案 3**，启用完整的 MCP 工具集
3. 根据实际使用情况，启用 Skills

这样 Agent 就能真正回答"昆仑万维有啥利好"这类需要实时信息的问题了！
