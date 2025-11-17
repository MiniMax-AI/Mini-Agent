# 后端安装说明

## 🎯 您说得对！使用 pip install -e . 更简单！

### 一条命令安装所有依赖

```bash
cd Mini-Agent
pip install -e ".[backend]"
```

**就这么简单！** 现在可以直接运行后端了。

---

## 🚀 快速开始（推荐方式）

### 方法 1：一键安装脚本

**Linux/Mac**：
```bash
cd Mini-Agent/backend
./setup-backend.sh
```

**Windows**：
```cmd
cd Mini-Agent\backend
setup-backend.bat
```

脚本会自动：
1. ✅ 安装 mini_agent（可编辑模式）
2. ✅ 安装所有后端依赖
3. ✅ 创建 .env 配置文件

### 方法 2：手动安装

```bash
# 1. 安装 mini_agent + 后端依赖
cd Mini-Agent
pip install -e ".[backend]"

# 2. 配置环境变量
cd backend
cp .env.example .env
# 编辑 .env，填入你的 API Keys

# 3. 运行诊断
python diagnose.py

# 4. 启动后端
uvicorn app.main:app --reload
```

---

## 📦 安装了什么？

### mini_agent 核心依赖（必需）
- anthropic>=0.39.0
- openai>=1.57.4
- tiktoken>=0.5.0
- zhipuai>=2.0.0
- pydantic>=2.0.0
- httpx>=0.27.0
- ...

### 后端额外依赖（backend 组）
- fastapi>=0.104.1
- uvicorn[standard]>=0.24.0
- sqlalchemy>=2.0.23
- pydantic-settings>=2.1.0
- python-dotenv>=1.0.0
- ...

**一条命令全搞定**：`pip install -e ".[backend]"`

---

## 🆚 与旧方式的对比

### ❌ 旧方式（不推荐）

```bash
# 需要手动同步依赖
pip install -r backend/requirements.txt

# 然后在代码中用 sys.path hack
sys.path.insert(0, str(mini_agent_path.parent))
from mini_agent.agent import Agent
```

**问题**：
- ❌ 需要维护两份依赖文件
- ❌ IDE 无法识别 mini_agent 模块
- ❌ 自动补全不工作
- ❌ 不是 Python 标准做法

### ✅ 新方式（推荐）

```bash
# 一条命令
pip install -e ".[backend]"

# 代码中直接导入
from mini_agent.agent import Agent
```

**优势**：
- ✅ Python 标准做法
- ✅ 只维护一份依赖（pyproject.toml）
- ✅ IDE 完全支持
- ✅ 自动补全工作

---

## 🔄 从旧方式迁移

如果您之前使用 sys.path 方式：

```bash
# 1. 卸载旧依赖（可选）
pip uninstall -r backend/requirements.txt -y

# 2. 使用新方式安装
cd Mini-Agent
pip install -e ".[backend]"

# 3. （可选）简化代码
# 编辑 backend/app/services/agent_service.py
# 删除 6-9 行的 sys.path 操作

# 4. 测试
cd backend
python diagnose.py
uvicorn app.main:app --reload
```

---

## 🎓 技术细节

### pip install -e . 做了什么？

1. **创建链接**：在 site-packages 中创建指向源码的链接
   ```
   site-packages/mini_agent.egg-link → /path/to/Mini-Agent
   ```

2. **添加到 sys.path**：自动添加到 Python 路径
   ```python
   # 不需要手动操作，pip 已经帮你做了！
   import mini_agent  # ✅ 直接可用
   ```

3. **可编辑模式**：修改源码立即生效，无需重新安装

### [backend] 是什么？

这是 `pyproject.toml` 中定义的"可选依赖组"：

```toml
[project.optional-dependencies]
backend = [
    "fastapi>=0.104.1",
    "uvicorn[standard]>=0.24.0",
    # ... 后端专用依赖
]
```

`pip install -e ".[backend]"` 会安装：
- mini_agent 核心依赖
- **+** backend 组的额外依赖

---

## 🐳 Docker 部署

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# 复制项目
COPY . /app

# 安装所有依赖（一条命令）
RUN pip install -e ".[backend]"

# 配置
ENV PYTHONUNBUFFERED=1

# 运行
WORKDIR /app/backend
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## ✅ 验证安装

```bash
# 1. 检查 mini_agent 是否可导入
python -c "import mini_agent; print('✅ mini_agent 已安装')"

# 2. 检查后端依赖
python -c "import fastapi; print('✅ FastAPI 已安装')"

# 3. 运行诊断脚本
cd backend
python diagnose.py

# 4. 启动后端测试
uvicorn app.main:app --reload
```

---

## 🎯 总结

| 操作 | 旧方式 | **新方式（推荐）** |
|------|--------|--------------------|
| **安装** | `pip install -r requirements.txt` | `pip install -e ".[backend]"` ✅ |
| **依赖管理** | 两个文件 | 一个文件 ✅ |
| **代码** | 需要 sys.path | 直接导入 ✅ |
| **IDE 支持** | ❌ 不好 | ✅ 完美 |
| **标准性** | ❌ Hack | ✅ Python 标准 |

**强烈推荐使用新方式！** 🚀

---

## 📚 相关文档

- `INSTALL_GUIDE.md` - 详细安装指南
- `ARCHITECTURE.md` - 架构说明（解释了旧方式）
- `diagnose.py` - 诊断脚本

**最后更新**: 2025-11-17
