# Mini-Agent Backend Windows 环境问题排查指南

## 问题概述

根据日志分析，发现了以下几个问题：

### 1. BashTool 执行失败，错误信息为空

**症状**：
```
🔧 Tool Call: bash
   Arguments:
   {
     "command": "ls -la"
   }
✗ Error:
```

**可能原因**：
1. **PowerShell 编码问题** - Windows PowerShell 的输出编码可能与 UTF-8 不兼容
2. **工作空间路径过长** - Windows 路径长度限制可能导致问题
3. **PowerShell 执行策略** - 可能需要调整 PowerShell 的执行策略
4. **权限问题** - 工作空间目录可能没有执行权限

**解决方案**：

#### 方案 1: 添加详细的错误日志

修改 `mini_agent/tools/bash_tool.py`，在 `execute` 方法中添加更详细的日志：

```python
async def execute(
    self,
    command: str,
    timeout: int = 120,
    run_in_background: bool = False,
) -> ToolResult:
    """Execute shell command with optional background execution."""

    try:
        # 添加调试日志
        print(f"[DEBUG] Executing command: {command}")
        print(f"[DEBUG] Is Windows: {self.is_windows}")
        print(f"[DEBUG] Workspace dir: {self.workspace_dir}")

        # ... 其余代码保持不变 ...

        # 在解码输出后添加日志
        stdout_text = stdout.decode("utf-8", errors="replace")
        stderr_text = stderr.decode("utf-8", errors="replace")

        print(f"[DEBUG] Exit code: {process.returncode}")
        print(f"[DEBUG] Stdout length: {len(stdout_text)}")
        print(f"[DEBUG] Stderr length: {len(stderr_text)}")

        # ... 其余代码保持不变 ...
```

#### 方案 2: 修改 PowerShell 编码设置

在 `bash_tool.py` 的 Windows 命令构建部分添加编码参数：

```python
if self.is_windows:
    # Windows: Use PowerShell with UTF-8 encoding
    shell_cmd = [
        "powershell.exe",
        "-NoProfile",
        "-OutputEncoding", "UTF8",
        "-InputFormat", "Text",
        "-Command",
        command
    ]
```

#### 方案 3: 简化工作空间路径

如果当前工作空间路径过长，考虑使用更短的路径。在 `.env` 文件中修改：

```env
WORKSPACE_BASE="C:/mini-agent-data"
```

### 2. ReadTool 权限错误

**症状**：
```
🔧 Tool Call: read_file
   Arguments:
   {
     "path": "."
   }
✗ Error: [Errno 13] Permission denied: 'C:\\Users\\...'
```

**原因**：
Agent 尝试读取目录 "." 而不是文件。ReadTool 只能读取文件，不能读取目录。

**解决方案**：

这是 Agent 的行为问题，而不是代码问题。可以通过以下方式改进：

1. **在 system prompt 中明确说明**：在 `mini_agent/config/system_prompt.md` 中添加：

```markdown
## 文件操作注意事项

1. **read_file** 工具只能读取文件，不能读取目录
2. 如果需要列出目录内容，使用 bash 工具：
   - Windows: `dir` 或 `Get-ChildItem`
   - Unix: `ls -la`
3. 不要尝试直接读取 "." 或 ".."
```

2. **改进 ReadTool 的错误提示**：修改 `mini_agent/tools/file_tools.py`：

```python
async def execute(self, path: str, offset: int | None = None, limit: int | None = None) -> ToolResult:
    """Execute read file."""
    try:
        file_path = Path(path)
        # Resolve relative paths relative to workspace_dir
        if not file_path.is_absolute():
            file_path = self.workspace_dir / file_path

        # 添加目录检查
        if file_path.is_dir():
            return ToolResult(
                success=False,
                content="",
                error=f"Cannot read directory: {path}. Use bash tool to list directory contents instead.",
            )

        if not file_path.exists():
            return ToolResult(
                success=False,
                content="",
                error=f"File not found: {path}",
            )

        # ... 其余代码保持不变 ...
```

### 3. API 内容过滤错误

**症状**：
```
Error code: 400 - {'contentFilter': [{'level': 1, 'role': 'assistant'}],
'error': {'code': '1301', 'message': '系统检测到输入或生成内容可能包含不安全或敏感内容'}}
```

**原因**：
用户查询 "昆仑万维有啥利好" 触发了 MiniMax API 的内容安全过滤。这是因为涉及股票投资建议等敏感内容。

**解决方案**：

1. **修改查询方式** - 避免直接询问投资相关问题
2. **调整 system prompt** - 在 prompt 中说明不提供投资建议
3. **添加重试逻辑** - 当遇到内容过滤错误时，自动重新表述问题

在 `mini_agent/llm/anthropic_client.py` 或 `mini_agent/llm/openai_client.py` 中添加特殊处理：

```python
# 检查是否是内容过滤错误
if "contentFilter" in error_response or "1301" in str(error_response):
    # 返回一个友好的错误信息
    raise Exception(
        "检测到敏感内容。请尝试重新表述您的问题，避免涉及投资建议、敏感话题等内容。"
    )
```

### 4. ZHIPU_API_KEY 未配置

**症状**：
```
   ℹ️  未配置 ZHIPU_API_KEY，跳过搜索工具
```

**说明**：
这不是错误，只是一个信息提示。如果需要使用智谱 AI 的搜索工具，需要配置此 API Key。

**解决方案**：

如果需要使用搜索功能：

1. **获取智谱 AI API Key**：
   - 访问 https://open.bigmodel.cn/
   - 注册账号并获取 API Key

2. **配置环境变量**：
   在 `backend/.env` 文件中添加：
   ```env
   ZHIPU_API_KEY="your-zhipuai-api-key-here"
   ```

3. **安装依赖**（如果还没有安装）：
   ```bash
   pip install zhipuai
   ```

4. **重启服务**：
   ```bash
   uvicorn app.main:app --reload
   ```

如果不需要搜索功能，可以忽略这个提示。

## 完整诊断脚本

创建一个 Windows 专用的诊断脚本 `backend/diagnose_windows.py`：

```python
#!/usr/bin/env python3
"""Windows 环境专用诊断脚本"""
import sys
import os
import platform
from pathlib import Path
import asyncio

print("🔍 Mini-Agent Windows 环境诊断\n")
print("=" * 60)

# 1. 检查操作系统
print("\n1️⃣  检查操作系统")
print(f"   系统: {platform.system()}")
print(f"   版本: {platform.version()}")
print(f"   架构: {platform.machine()}")

if platform.system() != "Windows":
    print("   ⚠️  此脚本专为 Windows 设计")
else:
    print("   ✅ Windows 环境")

# 2. 检查 PowerShell
print("\n2️⃣  检查 PowerShell")
try:
    import subprocess
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command", "echo 'Test'"],
        capture_output=True,
        text=True,
        timeout=5
    )
    if result.returncode == 0:
        print("   ✅ PowerShell 可用")
        print(f"   输出: {result.stdout.strip()}")
    else:
        print(f"   ❌ PowerShell 执行失败: {result.stderr}")
except Exception as e:
    print(f"   ❌ PowerShell 测试失败: {e}")

# 3. 检查工作空间路径
print("\n3️⃣  检查工作空间配置")
try:
    from app.config import get_settings
    settings = get_settings()
    workspace_base = Path(settings.workspace_base)
    print(f"   工作空间基础路径: {workspace_base}")
    print(f"   路径长度: {len(str(workspace_base.absolute()))} 字符")

    if len(str(workspace_base.absolute())) > 200:
        print("   ⚠️  路径过长，可能导致问题")
    else:
        print("   ✅ 路径长度正常")

    if workspace_base.exists():
        print("   ✅ 工作空间目录存在")
    else:
        print("   ⚠️  工作空间目录不存在，将自动创建")
        workspace_base.mkdir(parents=True, exist_ok=True)
except Exception as e:
    print(f"   ❌ 工作空间检查失败: {e}")

# 4. 测试 BashTool
print("\n4️⃣  测试 BashTool")
try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from mini_agent.tools.bash_tool import BashTool

    bash_tool = BashTool(workspace_dir=str(workspace_base))
    print(f"   使用 Shell: {bash_tool.shell_name}")
    print(f"   是否 Windows: {bash_tool.is_windows}")

    # 测试简单命令
    async def test_bash():
        result = await bash_tool.execute("echo 'Hello'", timeout=10)
        return result

    result = asyncio.run(test_bash())
    if result.success:
        print("   ✅ BashTool 测试成功")
        print(f"   输出: {result.stdout[:100]}")
    else:
        print(f"   ❌ BashTool 测试失败")
        print(f"   错误: {result.error}")
        print(f"   Stdout: {result.stdout}")
        print(f"   Stderr: {result.stderr}")
        print(f"   Exit code: {result.exit_code}")
except Exception as e:
    print(f"   ❌ BashTool 测试失败: {e}")
    import traceback
    traceback.print_exc()

# 5. 检查环境变量
print("\n5️⃣  检查环境变量")
env_vars = ["LLM_API_KEY", "LLM_API_BASE", "LLM_MODEL", "ZHIPU_API_KEY"]
for var in env_vars:
    value = os.getenv(var)
    if value:
        if "KEY" in var:
            masked = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
            print(f"   ✅ {var}: {masked}")
        else:
            print(f"   ✅ {var}: {value}")
    else:
        if var == "ZHIPU_API_KEY":
            print(f"   ℹ️  {var}: 未配置（可选）")
        else:
            print(f"   ❌ {var}: 未配置")

print("\n" + "=" * 60)
print("✅ 诊断完成！")
```

## 快速修复步骤

1. **创建诊断脚本**：
   ```bash
   # 将上面的脚本保存为 backend/diagnose_windows.py
   python backend/diagnose_windows.py
   ```

2. **根据诊断结果修复问题**：
   - 如果 PowerShell 不可用，检查系统环境变量
   - 如果路径过长，修改 `.env` 中的 `WORKSPACE_BASE`
   - 如果 BashTool 失败，查看详细错误信息

3. **添加调试日志**：
   在测试期间，建议在 `bash_tool.py` 中添加详细的调试输出

4. **配置 ZHIPU_API_KEY**（可选）：
   如果需要搜索功能，在 `.env` 中添加智谱 AI 的 API Key

5. **重启服务并测试**：
   ```bash
   uvicorn app.main:app --reload
   ```

## 常见问题

### Q1: 为什么所有 bash 命令都失败？
A: 可能是以下原因之一：
- PowerShell 执行策略限制
- 工作空间路径权限问题
- 编码问题导致输出无法正确解析

### Q2: 如何避免内容过滤错误？
A:
- 避免询问投资建议、政治敏感话题
- 重新表述问题，使用更中性的语言
- 在 system prompt 中明确说明不提供敏感内容

### Q3: 是否必须配置 ZHIPU_API_KEY？
A: 不是必须的。这是可选功能，只有需要使用智谱 AI 搜索工具时才需要配置。

## 后续改进建议

1. **添加 Windows 特定的测试用例**
2. **改进错误处理和日志记录**
3. **在 system prompt 中添加更详细的工具使用指南**
4. **考虑添加配置验证工具**
5. **为常见错误添加自动恢复机制**

---

**最后更新**: 2025-01-17
