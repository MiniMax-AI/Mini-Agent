# 后端架构说明 - 为什么不需要安装 mini_agent

## 🤔 问题

用户疑惑：后端代码中直接 `from mini_agent.agent import Agent`，但没有安装 mini_agent 包，为什么能运行？

```python
# backend/app/services/agent_service.py
from mini_agent.agent import Agent  # ← 这里没有安装 mini_agent，为什么能导入？
```

## 📐 项目结构

```
Mini-Agent/
├── mini_agent/              # 核心源码包（未安装）
│   ├── __init__.py
│   ├── cli.py               # CLI 入口
│   ├── agent.py             # Agent 核心
│   ├── llm/                 # LLM 客户端
│   ├── tools/               # 工具集
│   └── skills/              # Skills (git 子模块)
│
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── main.py
│   │   └── services/
│   │       └── agent_service.py  # ← 这里引用 mini_agent
│   ├── requirements.txt     # 后端依赖
│   └── .env
│
├── pyproject.toml           # mini_agent 包定义（用于 CLI）
├── uv.lock                  # CLI 依赖锁定
└── README.md
```

## 💡 答案：通过 sys.path 引用源码

### 关键代码（backend/app/services/agent_service.py:6-9）

```python
# 添加 mini_agent 到 Python 路径
mini_agent_path = Path(__file__).parent.parent.parent.parent / "mini_agent"
if str(mini_agent_path) not in sys.path:
    sys.path.insert(0, str(mini_agent_path.parent))

# 现在可以直接导入了！
from mini_agent.agent import Agent
from mini_agent.llm import LLMClient
```

**工作原理**：

1. **计算路径**：`Path(__file__).parent.parent.parent.parent`
   ```
   agent_service.py 的位置：
   backend/app/services/agent_service.py

   .parent → backend/app/services/
   .parent → backend/app/
   .parent → backend/
   .parent → Mini-Agent/  ← 项目根目录

   mini_agent_path = Mini-Agent/mini_agent/
   ```

2. **添加到 Python 路径**：
   ```python
   sys.path.insert(0, "Mini-Agent/")  # 把项目根目录添加到 sys.path
   ```

3. **Python 查找模块时**：
   ```python
   from mini_agent.agent import Agent
   # Python 在 sys.path 中查找 "mini_agent" 目录
   # 找到：Mini-Agent/mini_agent/agent.py ✅
   ```

---

## 🎭 两种使用方式对比

### 方式 1：CLI（安装包模式）

**使用场景**：命令行工具

```bash
# 安装包
uv tool install -e .

# 或者直接运行
uv run python -m mini_agent.cli --workspace /path/to/workspace
```

**工作原理**：
- `pyproject.toml` 定义了 `mini-agent` 包
- 安装后创建命令：`mini-agent = "mini_agent.cli:main"`
- Python 从 site-packages 中导入

**依赖管理**：
- 在 `pyproject.toml` 中定义
- 使用 `uv.lock` 锁定版本

### 方式 2：后端（源码引用模式）

**使用场景**：FastAPI Web 服务

```bash
# 不需要安装 mini_agent
cd backend
uvicorn app.main:app --reload
```

**工作原理**：
- 通过 `sys.path.insert()` 引用源码
- Python 直接从源码目录导入

**依赖管理**：
- 在 `backend/requirements.txt` 中定义
- **需要手动同步** mini_agent 的依赖

---

## ✅ 这种设计的优点

### 1. **开发便利性**

修改 mini_agent 源码后：
- ✅ CLI：无需重新安装（使用 `-e` 可编辑模式）
- ✅ 后端：直接生效，只需重启服务
- ✅ 共享同一份源码，避免不一致

### 2. **灵活部署**

可以根据需求选择部署方式：
- **开发环境**：源码模式（当前方式）
- **生产环境**：可以打包安装 mini_agent

### 3. **降低复杂度**

不需要：
- ❌ 每次修改后重新构建包
- ❌ 维护两个版本的 mini_agent
- ❌ 处理包安装路径问题

---

## ⚠️ 这种设计的注意事项

### 1. **依赖需要手动同步**

`pyproject.toml` 和 `backend/requirements.txt` 中的依赖需要保持一致：

**pyproject.toml**（CLI 的依赖）：
```toml
dependencies = [
    "anthropic>=0.39.0",
    "openai>=1.57.4",
    "tiktoken>=0.5.0",
    "zhipuai>=2.0.0",
    # ...
]
```

**backend/requirements.txt**（后端的依赖）：
```txt
# ========== Mini-Agent 核心依赖 ==========
anthropic>=0.39.0
openai>=1.57.4
tiktoken>=0.5.0
zhipuai>=2.0.0
# ...
```

⚠️ **如果 mini_agent 添加了新依赖，需要同时更新两处！**

### 2. **路径依赖**

后端必须在正确的目录结构下运行：
```
Mini-Agent/
├── mini_agent/     ← 必须存在
└── backend/        ← 从这里运行
```

如果移动了目录，路径计算会出错。

### 3. **Skills 子模块**

Skills 是 git 子模块，需要初始化：
```bash
git submodule update --init --recursive
```

否则 `mini_agent/skills/` 目录为空。

---

## 🔄 迁移到生产环境

如果需要在生产环境部署，可以考虑：

### 选项 1：继续使用源码模式（推荐）

```dockerfile
# Dockerfile
FROM python:3.10

WORKDIR /app

# 复制整个项目
COPY . /app

# 安装后端依赖
RUN pip install -r backend/requirements.txt

# 运行后端
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0"]
```

### 选项 2：安装 mini_agent 包

```bash
# 1. 先安装 mini_agent
pip install -e .

# 2. 再安装后端依赖
pip install -r backend/requirements.txt

# 3. 修改 agent_service.py，移除 sys.path 操作
# 因为 mini_agent 已经安装在 site-packages 中了
```

---

## 📊 依赖同步检查清单

当您修改 mini_agent 依赖时，确保更新：

- [ ] `pyproject.toml` - CLI 的依赖
- [ ] `backend/requirements.txt` - 后端的依赖
- [ ] 如果添加了新的工具，更新 `agent_service.py`

---

## 🛠️ 常见问题

### Q1：为什么不直接安装 mini_agent？

**A**：开发阶段使用源码模式更方便：
- 修改代码立即生效
- 不需要反复安装
- CLI 和后端共享源码

### Q2：如何验证 sys.path 是否正确？

**A**：在后端启动时添加调试：

```python
print(f"✅ mini_agent 路径: {mini_agent_path}")
print(f"✅ sys.path 包含: {mini_agent_path.parent in sys.path}")
```

### Q3：如果 mini_agent 在其他位置怎么办？

**A**：修改路径计算或使用环境变量：

```python
import os

# 方式 1：环境变量
mini_agent_path = os.getenv("MINI_AGENT_PATH", "default/path")

# 方式 2：修改计算逻辑
mini_agent_path = Path("/absolute/path/to/mini_agent")
```

### Q4：后端依赖和 CLI 依赖不一致会怎样？

**A**：可能导致：
- 后端启动失败（缺少依赖）
- 功能异常（版本不兼容）
- 工具加载失败

**解决方案**：定期同步两个依赖文件。

---

## 📝 总结

### 当前架构

```
不安装 mini_agent → 通过 sys.path 引用源码 → 直接导入模块 ✅
```

### 关键实现

```python
# backend/app/services/agent_service.py:6-9
sys.path.insert(0, str(mini_agent_path.parent))
from mini_agent.agent import Agent
```

### 核心优势

- ✅ 开发便利（修改立即生效）
- ✅ 代码共享（CLI 和后端使用同一份）
- ✅ 部署灵活（可选安装或源码模式）

### 需要注意

- ⚠️ 依赖需要手动同步
- ⚠️ 路径结构不能随意改变
- ⚠️ git 子模块需要正确初始化

---

**最后更新**: 2025-11-17
**相关文件**:
- `backend/app/services/agent_service.py:6-9` - sys.path 操作
- `pyproject.toml` - CLI 包定义
- `backend/requirements.txt` - 后端依赖
