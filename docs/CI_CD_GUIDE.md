# CI/CD 配置指南

## 📋 概述

本文档描述了 Mini-Agent 项目的持续集成和持续部署（CI/CD）配置，包括自动化测试、代码质量检查和 PyPI 包发布流程。

---

## 🔄 持续集成（CI）

### 触发条件

CI 工作流会在以下情况下自动触发：

| 触发条件 | 描述 |
|---------|------|
| `push` 到 `main` 或 `develop` 分支 | 代码提交后自动运行测试 |
| `pull_request` 到 `main` 或 `develop` 分支 | PR 提交后自动运行测试 |
| 排除 `docs/**` 和 `**.md` 文件变更 | 文档变更不触发 CI |

### CI 工作流组成

#### 1. 代码检查（Lint & Type Check）

```yaml
jobs:
  lint:
    name: Lint & Type Check
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'

      - name: Install linting tools
        run: |
          pip install ruff mypy

      - name: Run Ruff linter
        run: ruff check .

      - name: Run type checking
        run: mypy mini_agent/ --ignore-missing-imports
```

**检查内容**：
- ✅ Ruff 代码风格检查
- ✅ MyPy 类型检查
- ✅ 导入排序检查
- ✅ 代码复杂度检查

#### 2. 多版本测试（Test Matrix）

```yaml
jobs:
  test:
    name: Test (Python ${{ matrix.python-version }})
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']
```

**测试矩阵**：

| Python 版本 | 覆盖率报告 | 备注 |
|------------|-----------|------|
| 3.10 | ❌ | 兼容性测试 |
| 3.11 | ❌ | 标准测试 |
| 3.12 | ✅ | 主版本，覆盖率报告 |

#### 3. 多代理协调系统测试

```yaml
jobs:
  test-orchestration:
    name: Test Orchestration
    steps:
      - name: Run orchestration tests
        run: pytest tests/orchestration/ -v
```

**测试范围**：
- ✅ 协调器功能测试
- ✅ 执行器优化测试
- ✅ 任务路由测试
- ✅ 结果聚合测试

#### 4. 安全审计（Security Audit）

```yaml
jobs:
  audit:
    name: Security Audit
    steps:
      - name: Install safety
        run: pip install safety

      - name: Run security audit
        run: safety check -r pyproject.toml
```

**审计内容**：
- ✅ 依赖漏洞扫描
- ✅ 已知安全问题检查
- ✅ 安全建议生成

#### 5. 集成检查（Integration Check）

```yaml
jobs:
  integration-check:
    name: Integration Check
    steps:
      - name: Check module imports
        run: |
          python -c "import mini_agent"
          python -c "from mini_agent.orchestration import MultiAgentOrchestrator"
```

**检查内容**：
- ✅ 模块导入测试
- ✅ 示例脚本验证
- ✅ 端到端流程测试

### CI 通过条件

所有作业必须成功完成：

```
✅ Lint & Type Check → 通过
✅ Test (3.10) → 通过
✅ Test (3.11) → 通过
✅ Test (3.12) → 通过 + 覆盖率报告
✅ Test Orchestration → 通过
✅ Security Audit → 通过
✅ Integration Check → 通过
✅ Coverage Aggregate → 通过 (覆盖率 ≥ 80%)
```

---

## 🚀 持续部署（CD）

### 触发条件

CD 工作流仅在创建 **GitHub Release** 时触发：

```yaml
on:
  release:
    types: [created]
```

### CD 工作流组成

#### 1. 构建和测试（Build & Test）

```yaml
jobs:
  build:
    name: Build & Test
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Build package
        run: python -m build

      - name: Verify package
        run: |
          pip install dist/*.whl
          python -c "import mini_agent; print(mini_agent.__version__)"
```

#### 2. TestPyPI 发布测试

```yaml
jobs:
  test-pypi:
    name: Test on TestPyPI
    environment:
      name: testpypi
      url: https://test.pypi.org/pypi mini-agent
    permissions:
      id-token: write
    steps:
      - name: Publish to TestPyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          repository-url: https://test.pypi.org/legacy/
```

#### 3. 正式 PyPI 发布

```yaml
jobs:
  pypi:
    name: Publish to PyPI
    needs: test-pypi
    environment:
      name: pypi
      url: pypi.org/pypi mini-agent
    permissions:
      id-token: write
    steps:
      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
```

### CD 发布流程

```
1. 创建 GitHub Release
   ↓
2. CI 构建和测试
   ↓
3. 发布到 TestPyPI
   ↓
4. 从 TestPyPI 安装验证
   ↓
5. 发布到正式 PyPI
   ↓
6. 验证 PyPI 安装
   ↓
7. 发布完成通知
```

---

## ⚙️ PyPI 发布配置

### 必需的环境变量/密钥

#### 1. PyPI 发布令牌

**TestPyPI**（测试发布）：
- 设置位置：GitHub Repository → Settings → Secrets and variables → Actions
- 密钥名称：`TEST_PYPI_API_TOKEN`
- 获取地址：https://test.pypi.org/manage/account/

**正式 PyPI**（生产发布）：
- 设置位置：GitHub Repository → Settings → Secrets and variables → Actions
- 密钥名称：`PYPI_API_TOKEN`
- 获取地址：https://pypi.org/manage/account/

#### 2. 配置步骤

**步骤 1：获取 PyPI API Token**

1. 访问 https://pypi.org/manage/account/
2. 点击 "Add API token"
3. 填写令牌名称（如 "github-actions"）
4. 设置范围：选择 "Entire account" 或特定项目 "mini-agent"
5. 复制令牌

**步骤 2：添加到 GitHub Secrets**

1. 访问 https://github.com/zhaofei0923/Mini-Agent/settings/secrets/actions
2. 点击 "New repository secret"
3. 名称：`PYPI_API_TOKEN`
4. 值：粘贴令牌
5. 点击 "Add secret"

**步骤 3：配置 TestPyPI（可选）**

1. 访问 https://test.pypi.org/manage/account/
2. 创建 API token
3. 添加到 GitHub Secrets，名称：`TEST_PYPI_API_TOKEN`

### 验证 PyPI 配置

```bash
# 测试安装
pip install --index-url https://test.pypi.org/simple/ mini-agent

# 验证安装
python -c "import mini_agent; print(mini_agent.__version__)"
```

---

## 📊 工作流状态徽章

### 添加状态徽章

在 `README.md` 中添加 CI 状态徽章：

```markdown
![CI](https://github.com/zhaofei0923/Mini-Agent/actions/workflows/ci.yml/badge.svg)
![CD](https://github.com/zhaofei0923/Mini-Agent/actions/workflows/cd.yml/badge.svg)
![PyPI Version](https://img.shields.io/pypi/v/mini-agent)
![Python Versions](https://img.shields.io/pypi/pyversions/mini-agent)
```

### 徽章效果

| 徽章 | 含义 |
|------|------|
| ![CI](https://github.com/zhaofei0923/Mini-Agent/actions/workflows/ci.yml/badge.svg) | CI 状态 |
| ![CD](https://github.com/zhaofei0923/Mini-Agent/actions/workflows/cd.yml/badge.svg) | CD 状态 |
| ![PyPI Version](https://img.shields.io/pypi/v/mini-agent) | 最新版本 |
| ![Python Versions](https://img.shields.io/pypi/pyversions/mini-agent) | 支持的 Python 版本 |

---

## 🧪 测试指南

### 本地运行测试

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/orchestration/test_orchestrator.py -v

# 运行带覆盖率的测试
pytest tests/ --cov=mini_agent --cov-report=html

# 并行测试
pytest tests/ -n auto
```

### 本地运行 CI 检查

```bash
# 代码风格检查
ruff check .

# 类型检查
mypy mini_agent/ --ignore-missing-imports

# 安全审计
safety check -r pyproject.toml
```

---

## 📝 发布流程

### 完整发布步骤

#### 步骤 1：准备发布

```bash
# 1. 确保所有测试通过
pytest tests/ -v

# 2. 更新版本号（在 pyproject.toml 中）
# version = "0.6.0"

# 3. 更新 CHANGELOG.md
```

#### 步骤 2：创建 GitHub Release

1. 访问 https://github.com/zhaofei0923/Mini-Agent/releases
2. 点击 "Draft a new release"
3. 选择标签版本（如 v0.6.0）
4. 填写发布标题和描述
5. 点击 "Publish release"

#### 步骤 3：自动触发 CD

创建 Release 后，CD 工作流会自动：

```
✅ 构建包
✅ 运行测试
✅ 发布到 TestPyPI
✅ 验证安装
✅ 发布到 PyPI
✅ 发送完成通知
```

---

## 🔧 故障排除

### 问题 1：CI 失败 - 测试不通过

**错误信息**：
```
FAILED tests/orchestration/test_orchestrator.py::test_function
```

**解决方法**：
1. 查看详细的测试输出
2. 在本地运行失败的测试
3. 修复代码问题
4. 提交修复到分支

```bash
# 本地调试
pytest tests/orchestration/test_orchestrator.py::test_function -v -s
```

### 问题 2：CI 失败 - 覆盖率不足

**错误信息**：
```
Coverage failure: required coverage (80%) not met (75%)
```

**解决方法**：
1. 分析覆盖率报告
2. 添加缺失的测试用例
3. 确保核心功能 100% 覆盖

```bash
# 生成覆盖率报告
pytest tests/ --cov=mini_agent --cov-report=term-missing
```

### 问题 3：CD 失败 - PyPI 发布

**错误信息**：
```
HTTPError: 403 Forbidden - User '<bot>' does not have 'pypi' permission
```

**解决方法**：
1. 检查 PyPI API Token 权限
2. 确认令牌已添加到 GitHub Secrets
3. 验证令牌未过期

```bash
# 测试令牌是否有效
pip install twine
twine check dist/*
```

### 问题 4：CI 失败 - 权限错误

**错误信息**：
```
Error: Resource not accessible by integration
```

**解决方法**：
1. 检查 GitHub Actions 权限设置
2. 确保工作流有必要的权限

```yaml
# 在工作流中添加权限
permissions:
  contents: read
  checks: write
  actions: read
  pull-requests: write
```

---

## 📈 优化建议

### 1. 缓存优化

```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: '3.12'
    cache: 'pip'  # 启用 pip 缓存
```

### 2. 并行作业

```yaml
jobs:
  lint: ...
  test: ...
  audit: ...
  # 所有作业并行运行
```

### 3. 条件执行

```yaml
- name: Run tests
  if: matrix.python-version == '3.12'
  # 仅特定条件运行
```

---

## 📚 相关资源

### 官方文档
- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [PyPI 发布指南](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)
- [pypa/gh-action-pypi-publish](https://github.com/pypa/gh-action-pypi-publish)

### 相关文件
- `.github/workflows/ci.yml` - CI 配置文件
- `.github/workflows/cd.yml` - CD 配置文件
- `pyproject.toml` - 项目配置
- `docs/CHANGELOG.md` - 版本更新日志

### 获取帮助
- GitHub Issues: https://github.com/zhaofei0923/Mini-Agent/issues
- GitHub Discussions: https://github.com/zhaofei0923/Mini-Agent/discussions

---

## ✅ 快速检查清单

### 发布前检查
- [ ] 所有测试通过
- [ ] 代码覆盖率 ≥ 80%
- [ ] 安全审计通过
- [ ] 版本号已更新
- [ ] CHANGELOG.md 已更新

### PyPI 配置检查
- [ ] PYPI_API_TOKEN 已添加
- [ ] TEST_PYPI_API_TOKEN 已添加（可选）
- [ ] 令牌权限正确
- [ ] 令牌未过期

### 发布后检查
- [ ] GitHub Release 已创建
- [ ] CI/CD 工作流成功完成
- [ ] 包可从 PyPI 安装
- [ ] 安装版本号正确
