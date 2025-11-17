# 后端安装指南（推荐方式）

## 🎯 推荐：使用 pip install -e .

### 为什么这样更好？

相比当前的 `sys.path` 方式：

| 方式 | 优点 | 缺点 |
|------|------|------|
| **sys.path（当前）** | 无需安装 | ❌ 不标准<br>❌ IDE 不友好<br>❌ 依赖需要同步 |
| **pip install -e .（推荐）** | ✅ 标准流程<br>✅ IDE 支持好<br>✅ 统一管理依赖 | 需要一条安装命令 |

---

## 🚀 快速开始

### 方法 1：使用 pip

```bash
cd Mini-Agent

# 1. 安装 mini_agent（可编辑模式）
pip install -e .

# 2. 配置环境变量
cd backend
cp .env.example .env
# 编辑 .env，填入你的 API Keys

# 3. 运行后端
uvicorn app.main:app --reload
```

### 方法 2：使用 uv（推荐，更快）

```bash
cd Mini-Agent

# 1. 安装 mini_agent
uv pip install -e .

# 2. 配置环境变量
cd backend
cp .env.example .env
# 编辑 .env

# 3. 运行后端
uvicorn app.main:app --reload
```

---

## 📝 修改后端代码（可选）

如果使用 `pip install -e .`，可以简化 `agent_service.py`：

### 当前代码（复杂）

```python
# backend/app/services/agent_service.py
import sys
from pathlib import Path

# 添加 mini_agent 到 Python 路径
mini_agent_path = Path(__file__).parent.parent.parent.parent / "mini_agent"
if str(mini_agent_path) not in sys.path:
    sys.path.insert(0, str(mini_agent_path.parent))

from mini_agent.agent import Agent
```

### 简化后（推荐）

```python
# backend/app/services/agent_service.py
# 直接导入！不需要 sys.path 操作
from mini_agent.agent import Agent
from mini_agent.llm import LLMClient
from mini_agent.schema import LLMProvider, Message as AgentMessage
```

**注意**：如果使用 `pip install -e .`，agent_service.py 中的 sys.path 操作就是多余的了，可以删掉！

---

## 🔄 迁移步骤

### 从当前方式迁移到 pip install -e .

```bash
# 1. 确保在项目根目录
cd Mini-Agent

# 2. 安装 mini_agent（可编辑模式）
pip install -e .

# 3. （可选）简化 agent_service.py
# 删除 sys.path 相关代码（6-9 行）

# 4. 测试
cd backend
python diagnose.py  # 运行诊断脚本
uvicorn app.main:app --reload
```

---

## 🎯 两种模式对比

### 当前模式（sys.path）

```bash
cd backend
uvicorn app.main:app --reload
```

**工作原理**：
- 运行时动态添加 mini_agent 到 sys.path
- 不需要预先安装

**问题**：
- IDE 无法识别 mini_agent 模块
- 自动补全不工作
- 需要维护两份依赖文件

### 推荐模式（pip install -e .）

```bash
# 先安装
pip install -e .

# 再运行
cd backend
uvicorn app.main:app --reload
```

**工作原理**：
- mini_agent 安装在 site-packages（以链接方式）
- Python 可以正常导入

**优势**：
- ✅ IDE 完全支持
- ✅ 自动补全工作
- ✅ 只需要维护 pyproject.toml

---

## 📦 依赖管理

### 当前方式（不推荐）

```
pyproject.toml        ← mini_agent 的依赖
backend/requirements.txt  ← 后端的依赖（需要包含 mini_agent 的依赖）
```

⚠️ **问题**：两处依赖需要手动同步！

### 推荐方式

只维护一个地方：

```toml
# pyproject.toml
[project]
dependencies = [
    "anthropic>=0.39.0",
    "openai>=1.57.4",
    "tiktoken>=0.5.0",
    "zhipuai>=2.0.0",
    # ... mini_agent 核心依赖
]

[project.optional-dependencies]
backend = [
    "fastapi>=0.104.1",
    "uvicorn[standard]>=0.24.0",
    "sqlalchemy>=2.0.23",
    # ... 后端专用依赖
]
```

安装：
```bash
# 安装 mini_agent + 后端依赖
pip install -e ".[backend]"
```

---

## 🐳 Docker 部署

### 使用 pip install -e .

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# 复制项目文件
COPY . /app

# 安装 mini_agent（可编辑模式）
RUN pip install -e .

# 安装后端依赖（如果分开的话）
# RUN pip install -r backend/requirements.txt

# 运行后端
WORKDIR /app/backend
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## ✨ 总结

| 操作 | 当前方式 | 推荐方式 |
|------|---------|---------|
| **安装** | 无需安装 | `pip install -e .` |
| **运行** | `uvicorn app.main:app` | `uvicorn app.main:app` |
| **IDE 支持** | ❌ 差 | ✅ 完美 |
| **依赖管理** | 两份文件 | 一份文件 |
| **标准性** | ❌ 不标准 | ✅ Python 标准 |

**建议**：切换到 `pip install -e .` 方式！

---

## 🛠️ 快速切换命令

```bash
# 1. 安装 mini_agent
cd Mini-Agent
pip install -e .

# 2. （可选）简化 agent_service.py
# 删除第 6-9 行的 sys.path 操作

# 3. 运行后端
cd backend
uvicorn app.main:app --reload
```

**就这么简单！** 😊

---

**最后更新**: 2025-11-17
**推荐指数**: ⭐⭐⭐⭐⭐
