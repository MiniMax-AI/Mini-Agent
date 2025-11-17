# Mini-Agent 后端 Workspace 设计方案

## 核心问题
Workspace 应该如何组织？
- 跟着用户走？
- 跟着 session 走？
- 统一环境？

---

## 方案对比

### 📊 方案1: Workspace 跟用户走

```
/data/workspaces/
  ├─ user_12345/
  │   ├─ .venv/              ← 用户的 Python 环境
  │   ├─ files/              ← 用户所有文件
  │   ├─ .agent_memory.json  ← 持久化记忆
  │   └─ sessions/
  │       ├─ session_abc/    ← 会话日志
  │       └─ session_def/
  └─ user_67890/
      ├─ .venv/
      ├─ files/
      └─ ...
```

**优点**:
- ✅ 用户文件持久化（可以跨会话访问）
- ✅ 包只需装一次（reportlab 装一次，所有会话都能用）
- ✅ 有"个人工作空间"的感觉

**缺点**:
- ❌ 不同任务的包可能冲突（A任务装 pandas 1.0，B任务需要 2.0）
- ❌ 用户可能装一堆包，占用大量空间
- ❌ 安全隔离不够强（一个会话的恶意代码影响整个用户空间）
- ❌ 需要配额和清理策略

**适用场景**:
- 个人使用
- 需要长期保存文件的场景
- 用户数量少

---

### 📊 方案2: Workspace 跟 Session 走

```
/data/workspaces/
  ├─ session_abc123/
  │   ├─ .venv/       ← 这个会话的环境
  │   ├─ files/       ← 这个会话的文件
  │   ├─ user_id.txt  ← 记录归属
  │   └─ .agent_memory.json
  ├─ session_def456/
  │   ├─ .venv/
  │   └─ files/
  └─ session_ghi789/
      └─ ...

会话结束 → 自动删除或归档
```

**优点**:
- ✅ 完全隔离（每个会话独立环境）
- ✅ 会话结束直接删除，不占空间
- ✅ 不会互相污染
- ✅ 安全性最高

**缺点**:
- ❌ 无法跨会话访问文件
- ❌ 每次都要重新装包（慢！）
- ❌ 资源浪费（每个会话都装一遍 pandas）
- ❌ 用户体验差（上次生成的文件这次看不到）

**适用场景**:
- 一次性任务
- 安全要求极高
- 不需要文件持久化

---

### 📊 方案3: 统一环境 + 用户文件隔离 ⭐ 推荐

```
/data/
  ├─ shared_env/
  │   ├─ base.venv/          ← 预装常用包的基础环境
  │   │   ├─ pandas
  │   │   ├─ numpy
  │   │   ├─ reportlab
  │   │   ├─ python-pptx
  │   │   └─ openpyxl
  │   └─ allowed_packages.txt ← 白名单
  │
  └─ workspaces/
      ├─ user_12345/
      │   ├─ sessions/
      │   │   ├─ session_abc/
      │   │   │   ├─ files/    ← 会话文件
      │   │   │   └─ logs/
      │   │   └─ session_def/
      │   │       └─ files/
      │   └─ shared_files/     ← 跨会话共享文件
      └─ user_67890/
          └─ ...
```

**工作流程**:
```python
# 1. 创建会话时
workspace = f"/data/workspaces/user_{user_id}/sessions/session_{session_id}"
os.makedirs(workspace)

# 2. 使用共享环境（只读）
shared_venv = "/data/shared_env/base.venv"

# 3. 如果需要额外的包
if package in allowed_packages:
    # 在用户空间临时安装
    uv pip install --prefix {workspace}/.local {package}
else:
    raise PermissionError("Package not allowed")

# 4. 会话结束
# - 保留文件到 shared_files/
# - 删除临时数据
```

**优点**:
- ✅ 常用包预装，启动快
- ✅ 用户之间完全隔离
- ✅ 会话之间可以共享文件（shared_files）
- ✅ 可以限制允许安装的包
- ✅ 资源占用适中

**缺点**:
- ⚠️ 需要维护共享环境
- ⚠️ 白名单管理有成本

**适用场景**: ⭐ **生产环境推荐**
- 多用户 SaaS
- 需要性能和安全平衡
- 有运维能力

---

### 📊 方案4: Docker 容器隔离（最安全）

```
每个会话一个容器:

docker run --rm \
  --name "session_abc123" \
  -v /data/workspaces/user_12345/session_abc:/workspace \
  --cpus=0.5 \
  --memory=512m \
  --pids-limit=50 \
  --network=agent-net \  # 受限网络
  --read-only \          # 只读根文件系统
  --tmpfs /tmp:size=100m \
  mini-agent:latest
```

**镜像构建**:
```dockerfile
FROM python:3.11-slim
RUN uv venv /opt/venv && \
    /opt/venv/bin/pip install pandas numpy reportlab python-pptx openpyxl
COPY mini_agent /app/mini_agent
WORKDIR /workspace
CMD ["python", "-m", "mini_agent.agent_server"]
```

**优点**:
- ✅ 完全隔离（进程、网络、文件系统）
- ✅ 资源限制（CPU、内存、进程数）
- ✅ 安全性最高
- ✅ 可以预装环境
- ✅ 崩溃不影响宿主机

**缺点**:
- ❌ 需要 Docker 环境
- ❌ 启动稍慢（1-2秒）
- ❌ 运维复杂度高

**适用场景**: ⭐ **大规模生产环境**
- 安全要求极高
- 用户量大
- 有 DevOps 团队

---

## 🎯 推荐方案组合

### 开发/小规模（< 1000 用户）
**方案 3: 统一环境 + 用户隔离**

```python
# FastAPI 后端结构
/backend/
  ├─ app/
  │   ├─ main.py
  │   ├─ routers/
  │   │   ├─ chat.py       # 聊天 API
  │   │   └─ files.py      # 文件管理 API
  │   ├─ services/
  │   │   ├─ agent_service.py
  │   │   └─ workspace_service.py
  │   └─ models/
  │       ├─ user.py
  │       └─ session.py
  └─ config/
      ├─ allowed_packages.txt
      └─ resource_limits.yaml
```

### 生产/大规模（> 1000 用户）
**方案 4: Docker 容器**

```python
# 使用 Kubernetes/Docker Swarm
apiVersion: v1
kind: Pod
metadata:
  name: agent-session-{{ session_id }}
spec:
  containers:
  - name: mini-agent
    image: mini-agent:latest
    resources:
      limits:
        cpu: 500m
        memory: 512Mi
    volumeMounts:
    - name: workspace
      mountPath: /workspace
```

---

## 🔧 实现细节

### 方案3 详细设计

#### 1. 目录结构
```
/data/
  ├─ shared_env/
  │   ├─ base.venv/
  │   ├─ allowed_packages.txt
  │   └─ package_cache/     # 预下载的包
  │
  └─ workspaces/
      ├─ user_12345/
      │   ├─ quota.json      # 配额信息
      │   ├─ shared_files/   # 跨会话文件
      │   │   ├─ data/
      │   │   └─ outputs/
      │   └─ sessions/
      │       ├─ session_abc/
      │       │   ├─ files/
      │       │   ├─ logs/
      │       │   └─ .local/  # 会话特定的包
      │       └─ session_def/
      └─ user_67890/
```

#### 2. 配额管理
```yaml
# quota.json
{
  "user_id": "12345",
  "limits": {
    "max_workspace_size_mb": 1024,      # 1GB
    "max_sessions": 10,
    "max_session_duration_hours": 24,
    "max_files_per_session": 100
  },
  "current": {
    "workspace_size_mb": 345,
    "active_sessions": 2
  }
}
```

#### 3. 包白名单
```
# allowed_packages.txt
pandas>=2.0.0,<3.0.0
numpy>=1.24.0,<2.0.0
reportlab>=4.0.0
python-pptx>=0.6.0
openpyxl>=3.1.0
matplotlib>=3.7.0
requests>=2.31.0
# 不允许危险包
# NOT: os-sys, subprocess32, etc.
```

#### 4. Workspace Service
```python
# services/workspace_service.py
import os
import shutil
from pathlib import Path
from typing import Optional

class WorkspaceService:
    def __init__(self, base_path: str = "/data/workspaces"):
        self.base_path = Path(base_path)
        self.shared_env = Path("/data/shared_env/base.venv")

    def create_session_workspace(
        self,
        user_id: str,
        session_id: str
    ) -> Path:
        """创建会话工作空间"""
        user_dir = self.base_path / f"user_{user_id}"
        session_dir = user_dir / "sessions" / session_id

        # 检查配额
        if not self._check_quota(user_id):
            raise QuotaExceededError("User quota exceeded")

        # 创建目录
        session_dir.mkdir(parents=True, exist_ok=True)
        (session_dir / "files").mkdir(exist_ok=True)
        (session_dir / "logs").mkdir(exist_ok=True)

        # 创建符号链接到共享文件
        shared_link = session_dir / "shared"
        shared_files = user_dir / "shared_files"
        shared_files.mkdir(exist_ok=True)
        if not shared_link.exists():
            shared_link.symlink_to(shared_files)

        return session_dir

    def cleanup_session(
        self,
        user_id: str,
        session_id: str,
        keep_files: bool = True
    ):
        """清理会话"""
        session_dir = (
            self.base_path /
            f"user_{user_id}" /
            "sessions" /
            session_id
        )

        if keep_files:
            # 移动重要文件到 shared_files
            files_dir = session_dir / "files"
            if files_dir.exists():
                for file in files_dir.iterdir():
                    if file.suffix in ['.pdf', '.xlsx', '.pptx', '.docx']:
                        dest = (
                            self.base_path /
                            f"user_{user_id}" /
                            "shared_files" /
                            "outputs" /
                            file.name
                        )
                        shutil.move(str(file), str(dest))

        # 删除会话目录
        shutil.rmtree(session_dir, ignore_errors=True)

    def _check_quota(self, user_id: str) -> bool:
        """检查用户配额"""
        user_dir = self.base_path / f"user_{user_id}"
        quota_file = user_dir / "quota.json"

        if not quota_file.exists():
            return True

        import json
        with open(quota_file) as f:
            quota = json.load(f)

        # 检查空间
        current_size = self._get_dir_size(user_dir)
        if current_size > quota['limits']['max_workspace_size_mb'] * 1024 * 1024:
            return False

        # 检查会话数
        sessions = list((user_dir / "sessions").iterdir())
        if len(sessions) >= quota['limits']['max_sessions']:
            return False

        return True

    def _get_dir_size(self, path: Path) -> int:
        """获取目录大小（字节）"""
        total = 0
        for entry in path.rglob('*'):
            if entry.is_file():
                total += entry.stat().st_size
        return total
```

#### 5. 安全的 Bash Tool
```python
# tools/safe_bash_tool.py
import subprocess
from pathlib import Path
from typing import List

FORBIDDEN_COMMANDS = [
    'rm', 'rmdir', 'dd', 'mkfs',  # 删除/格式化
    'curl', 'wget', 'nc', 'telnet',  # 网络（除非白名单）
    'sudo', 'su', 'chmod', 'chown',  # 权限
    'kill', 'killall', 'pkill',  # 进程管理
]

ALLOWED_COMMANDS = [
    'python', 'uv', 'pip',  # Python
    'ls', 'cat', 'echo', 'cd', 'pwd',  # 基础命令
    'mkdir', 'touch',  # 安全的文件操作
]

class SafeBashTool(BashTool):
    def __init__(self, workspace_dir: str, allowed_packages: List[str]):
        super().__init__(workspace_dir)
        self.allowed_packages = allowed_packages

    async def execute(self, command: str, **kwargs) -> ToolResult:
        # 解析命令
        cmd_parts = command.split()
        if not cmd_parts:
            return ToolResult(success=False, error="Empty command")

        base_cmd = cmd_parts[0]

        # 检查黑名单
        if base_cmd in FORBIDDEN_COMMANDS:
            return ToolResult(
                success=False,
                error=f"Command '{base_cmd}' is not allowed"
            )

        # 检查白名单
        if base_cmd not in ALLOWED_COMMANDS:
            return ToolResult(
                success=False,
                error=f"Command '{base_cmd}' is not in whitelist"
            )

        # 检查 pip install
        if 'pip install' in command or 'uv pip install' in command:
            packages = self._extract_packages(command)
            for pkg in packages:
                if pkg not in self.allowed_packages:
                    return ToolResult(
                        success=False,
                        error=f"Package '{pkg}' is not allowed"
                    )

        # 执行命令（带超时）
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.workspace_dir,
                capture_output=True,
                text=True,
                timeout=30,  # 30秒超时
                env={
                    **os.environ,
                    'PYTHONPATH': str(self.workspace_dir),
                }
            )

            return ToolResult(
                success=result.returncode == 0,
                content=result.stdout,
                error=result.stderr if result.returncode != 0 else None
            )

        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                error="Command execution timeout (30s)"
            )

    def _extract_packages(self, command: str) -> List[str]:
        """从 pip install 命令提取包名"""
        # 简化实现
        parts = command.split()
        if 'install' in parts:
            idx = parts.index('install')
            return [p for p in parts[idx+1:] if not p.startswith('-')]
        return []
```

#### 6. FastAPI 集成
```python
# app/main.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncio
import uuid

app = FastAPI(title="Mini-Agent API")

# 服务初始化
workspace_service = WorkspaceService()

class ChatRequest(BaseModel):
    user_id: str
    session_id: str | None = None
    message: str

class ChatResponse(BaseModel):
    session_id: str
    message: str
    files: list[str] = []

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """聊天接口"""
    # 创建或获取会话
    session_id = request.session_id or str(uuid.uuid4())

    try:
        # 创建工作空间
        workspace = workspace_service.create_session_workspace(
            request.user_id,
            session_id
        )

        # 创建 Agent
        agent = create_agent(
            workspace_dir=str(workspace),
            user_id=request.user_id
        )

        # 执行任务
        agent.add_user_message(request.message)
        response = await agent.run()

        # 获取生成的文件
        files = list((workspace / "files").glob("*"))

        return ChatResponse(
            session_id=session_id,
            message=response,
            files=[f.name for f in files]
        )

    except QuotaExceededError:
        raise HTTPException(status_code=429, detail="Quota exceeded")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/files/{user_id}/{filename}")
async def download_file(user_id: str, filename: str):
    """下载文件"""
    file_path = (
        Path("/data/workspaces") /
        f"user_{user_id}" /
        "shared_files" /
        "outputs" /
        filename
    )

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path)

@app.delete("/api/sessions/{user_id}/{session_id}")
async def cleanup_session(user_id: str, session_id: str):
    """清理会话"""
    workspace_service.cleanup_session(user_id, session_id)
    return {"status": "success"}
```

---

## 📝 总结

### 推荐选择:

1. **快速原型/个人使用**: 方案3（统一环境 + 用户隔离）
2. **生产环境**: 方案4（Docker 容器）+ 方案3 的文件组织

### 关键考虑点:

| 维度 | 方案3 | 方案4 |
|------|-------|-------|
| 安全性 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 性能 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 运维复杂度 | ⭐⭐⭐ | ⭐⭐ |
| 资源效率 | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| 扩展性 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

### 实施路径:

```
阶段1: 本地开发
└─ 使用方案3，单机部署

阶段2: 小规模生产
└─ 方案3 + Nginx + Redis（会话缓存）

阶段3: 大规模生产
└─ 迁移到方案4（Docker/K8s）+ 分布式存储
```
