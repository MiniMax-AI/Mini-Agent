# CI/CD 错误排查与触发指南

## 目录
1. [检查CI状态](#检查ci状态)
2. [常见错误及解决方案](#常见错误及解决方案)
3. [推送后触发CI](#推送后触发ci)
4. [手动触发工作流](#手动触发工作流)
5. [调试技巧](#调试技巧)

---

## 检查CI状态

### 方法1: GitHub Web界面
1. 访问你的仓库: `https://github.com/zhaofei0923/Mini-Agent`
2. 点击 **Actions** 标签页
3. 查看所有工作流运行状态：
   - ✅ 绿色勾: 通过
   - ❌ 红色X: 失败
   - ⏳ 黄色圆圈: 运行中
   - ⚪ 灰色: 已取消

### 方法2: 使用GitHub CLI
```bash
# 查看最近的工作流运行
gh run list --limit 10

# 查看特定工作流的详细状态
gh run list --workflow=ci.yml --limit 5
```

### 方法3: 检查本地测试
```bash
# 运行完整测试套件
python -m pytest tests/ -v --tb=short

# 运行Linting检查
uv run ruff check .

# 运行类型检查
uv run mypy mini_agent/
```

---

## 常见错误及解决方案

### 1. 测试失败 (Test Failures)

**错误标志**: 
```
FAILED tests/test_xxx.py::TestClass::test_method
Error: Process completed with exit code 1.
```

**排查步骤**:

1. **查看详细错误信息**:
```bash
python -m pytest tests/ -v --tb=long 2>&1 | tail -100
```

2. **常见原因**:
   - 测试环境配置问题
   - API密钥缺失
   - 依赖版本不兼容
   - 测试数据问题

3. **解决方案**:
```bash
# 重新同步依赖
uv sync

# 清理缓存后重新测试
python -m pytest tests/ --cache-clear -v

# 检查环境变量
echo $ANTHROPIC_API_KEY
echo $OPENAI_API_KEY
```

**示例修复**:
```bash
# 如果是API密钥问题，设置测试密钥
export ANTHROPIC_API_KEY="test-key"
export OPENAI_API_KEY="test-key"

# 再次运行测试
python -m pytest tests/orchestration/ -v
```

### 2. Linting错误

**错误标志**:
```
F401 [*] `module` imported but unused
E722 Do not use bare `except`
Found N errors.
Error: Process completed with exit code 1.
```

**排查步骤**:

1. **查看所有错误**:
```bash
uv run ruff check . --show-source
```

2. **自动修复大部分错误**:
```bash
uv run ruff check . --fix
```

3. **需要手动修复的错误**:
```bash
# 查看需要手动处理的错误
uv run ruff check . --fix --unsafe-fixes
```

4. **常见Linting错误修复**:

**F401 - 未使用的导入**:
```python
# 错误
from typing import Optional

# 修复 - 删除未使用的导入
```

**F541 - f-string没有占位符**:
```python
# 错误
print(f"Hello World")  # 没有变量

# 修复
print("Hello World")
```

**E722 - 裸except**:
```python
# 错误
except:

# 修复
except (OSError, ValueError):
```

### 3. 类型检查错误

**错误标志**:
```
error: Argument "xxx" has incompatible type "yyy"
Found N errors in N files
Error: Process completed with exit code 1.
```

**排查步骤**:

1. **查看详细类型错误**:
```bash
uv run mypy mini_agent/ --show-error-codes
```

2. **常见原因和修复**:
```bash
# 修复缺失的类型注解
uv run mypy mini_agent/orchestration/ --ignore-missing-imports

# 或添加类型注解
def process_data(data: Dict[str, Any]) -> Any:
    pass
```

### 4. 依赖问题

**错误标志**:
```
ModuleNotFoundError: No module named 'module_name'
Error: Process completed with exit code 1.
```

**排查步骤**:

1. **检查依赖文件**:
```bash
cat pyproject.toml | grep -A 20 "\[project\]"
cat pyproject.toml | grep -A 10 "\[tool.uv\]"
```

2. **重新安装依赖**:
```bash
uv sync --clean
```

3. **添加缺失的依赖**:
```bash
# 编辑pyproject.toml添加
[project.dependencies]
psutil = ">=5.9.0"
```

### 5. 权限错误

**错误标志**:
```
remote: Permission to user/repo denied to user/other.
Error: Process completed with exit code 1.
```

**解决方案**:
```bash
# 检查当前远程URL
git remote -v

# 如果需要，更新为正确的仓库URL
git remote set-url origin https://github.com/zhaofei0923/Mini-Agent.git

# 或使用SSH
git remote set-url origin git@github.com:zhaofei0923/Mini-Agent.git
```

---

## 推送后触发CI

### 自动触发

CI/CD工作流会在以下情况自动触发：

1. **推送到main分支**:
```bash
git checkout main
git merge feature/multi-agent-orchestration
git push origin main
# ✅ 自动触发CI和CD工作流
```

2. **推送到其他分支**:
```bash
git checkout feature/new-feature
git push origin feature/new-feature
# ✅ 触发CI工作流（不触发CD）
```

3. **创建Pull Request**:
   - 访问 `https://github.com/zhaofei0923/Mini-Agent/compare/main...feature:branch`
   - 创建PR
   - ✅ 自动触发CI检查

### 触发条件详情

```
✅ CI工作流 (.github/workflows/ci.yml):
   - 推送到任何分支
   - 打开/更新Pull Request
   - 手动触发

✅ CD工作流 (.github/workflows/cd.yml):
   - 仅main分支的推送
   - 创建版本标签 (v*.*.*)
   - 手动触发
```

---

## 手动触发工作流

### 方法1: GitHub Web界面

1. 访问 `https://github.com/zhaofei0923/Mini-Agent/actions`
2. 选择工作流 (ci.yml 或 cd.yml)
3. 点击 **"Run workflow"** 按钮
4. 选择分支和输入参数
5. 点击 **"Run workflow"**

### 方法2: GitHub CLI

```bash
# 触发CI工作流
gh workflow run ci.yml --ref main -f python_version="3.12"

# 触发CD工作流
gh workflow run cd.yml --ref main

# 查看工作流运行状态
gh run watch
```

### 方法3: 创建标签触发CD

```bash
# 创建版本标签
git tag -a v0.6.0 -m "Release v0.6.0"

# 推送标签
git push origin v0.6.0

# ✅ 自动触发CD工作流 → 发布到PyPI
```

---

## 调试技巧

### 1. 本地模拟CI环境

```bash
# 使用Docker容器测试（如果配置了的话）
docker build -t mini-agent-ci .

# 或使用GitHub Actions本地运行
# 安装 act: https://github.com/nektos/act
act push --workflows .github/workflows/ci.yml
```

### 2. 查看CI运行日志

```bash
# 使用GitHub CLI下载日志
gh run download <run-id>

# 或在GitHub Actions页面点击具体的job查看日志
```

### 3. 隔离问题

```bash
# 只运行失败的测试
python -m pytest tests/orchestration/test_orchestrator.py::test_specific_method -v

# 只运行特定测试文件
python -m pytest tests/test_agent.py -v

# 只检查特定目录
uv run ruff check mini_agent/orchestration/
```

### 4. 快速修复流程

```bash
# 1. 查看错误
uv run ruff check .

# 2. 自动修复
uv run ruff check . --fix

# 3. 运行测试
python -m pytest tests/orchestration/ -v

# 4. 提交修复
git add .
git commit -m "fix: 修复CI错误"
git push origin feature/multi-agent-orchestration
```

---

## 当前仓库状态检查

让我为你的仓库进行快速诊断：

```bash
# 检查测试状态
cd /home/kevin0923/workspace/Mini-Agent
python -m pytest tests/orchestration/ -v --tb=short

# 检查Linting状态
uv run ruff check .

# 检查最近Git状态
git log --oneline -3
git status
```

### 预期结果

✅ **正常状态**:
- 所有测试通过 (162/162)
- 0 Ruff错误
- 所有工作流通过

❌ **需要关注**:
- 如果测试失败: 查看具体错误信息
- 如果Linting错误: 运行 `uv run ruff check . --fix`
- 如果工作流失败: 在GitHub Actions页面查看详细日志

---

## 下一步操作

### 如果你发现了CI错误：

1. **记录错误信息**:
   - 截图或复制完整的错误信息
   - 记录失败的工作流名称和运行ID

2. **尝试本地修复**:
   ```bash
   # 运行测试
   python -m pytest tests/ -v
   
   # 修复Linting
   uv run ruff check . --fix
   ```

3. **提交修复**:
   ```bash
   git add .
   git commit -m "fix: 修复CI错误"
   git push origin feature/multi-agent-orchestration
   ```

4. **查看自动重试结果**:
   - CI会自动在新的推送上运行
   - 检查GitHub Actions页面看是否通过

### 如果你需要我帮忙检查：

请提供以下信息之一：

1. **GitHub Actions页面截图**:
   - 访问 https://github.com/zhaofei0923/Mini-Agent/actions
   - 截图显示失败的工作流

2. **错误信息**:
   - 复制完整的错误输出
   - 包括 "Error:" 开头的行

3. **或者我可以直接检查**:
   - 我可以帮你查看GitHub Actions状态
   - 帮你分析具体的错误原因

---

## 常用命令速查表

```bash
# 🧪 测试相关
python -m pytest tests/ -v                    # 运行所有测试
python -m pytest tests/orchestration/ -v      # 只运行编排测试
python -m pytest tests/ -k "test_name"        # 运行特定测试
python -m pytest tests/ --cache-clear         # 清理缓存后测试

# 🎨 Linting相关
uv run ruff check .                           # 检查代码
uv run ruff check . --fix                     # 自动修复
uv run ruff check . --show-source             # 显示错误详情

# 📝 类型检查
uv run mypy mini_agent/                       # 类型检查
uv run mypy mini_agent/orchestration/         # 检查特定目录

# 🔧 依赖管理
uv sync                                       # 同步依赖
uv sync --clean                               # 清理后同步
uv pip install <package>                      # 添加依赖

# 📊 GitHub Actions
gh run list --limit 10                        # 查看最近运行
gh workflow run ci.yml --ref main             # 手动触发CI
gh run watch                                  # 实时监控运行状态
```

---

## 总结

**检查CI错误的完整流程**:

1. ✅ 访问 GitHub Actions 页面
2. ✅ 查看失败工作流的详细日志
3. ✅ 在本地运行相同测试
4. ✅ 修复发现的问题
5. ✅ 提交并推送修复
6. ✅ 验证CI自动重试通过

**记住**:
- CI错误是正常的开发过程的一部分
- 重要的是快速定位和修复问题
- 使用 `uv run ruff check . --fix` 可以解决大部分Linting问题
- 测试通过后再推送可以减少CI失败次数

如果你发现任何具体的CI错误，请告诉我，我可以帮你详细分析和修复！
