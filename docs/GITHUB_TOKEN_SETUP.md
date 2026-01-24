# GitHub Token 配置指南

本指南将帮助您配置 GitHub Personal Access Token，使 Mini-Agent 能够操作 GitHub 仓库和使用 GitHub MCP 工具。

## 目录
1. [创建 GitHub Personal Access Token](#1-创建-github-personal-access-token)
2. [配置 GitHub Secrets](#2-配置-github-secrets)
3. [配置 GitHub MCP](#3-配置-github-mcp)
4. [验证配置](#4-验证配置)
5. [常见问题](#5-常见问题)

---

## 1. 创建 GitHub Personal Access Token

### 步骤 1: 访问 GitHub 设置
1. 登录 GitHub 账号
2. 点击右上角头像 → **Settings**
3. 在左侧菜单中找到 **Developer settings**
4. 选择 **Personal access tokens** → **Tokens (classic)**
5. 点击 **Generate new token (classic)**

### 步骤 2: 设置 Token 权限
- **Note**: 输入描述，例如 "Mini-Agent GitHub Operations"
- **Expiration**: 建议选择 "No expiration"（永不过期）或 90 天
- **Select scopes**: 勾选以下权限

#### 必需权限
```markdown
✅ repo - Full control of private repositories
   ├── repo:status - Access commit statuses
   ├── repo_deployment - Access deployments
   ├── public_repo - Limit to public repositories
   └── repo_invite - Access repository invitations

✅ workflow - Update GitHub Actions workflows
✅ delete_repo - Delete repositories

✅ read:user - Read user profile data
✅ user:email - Read user email addresses
```

#### 可选权限（根据需求选择）
```markdown
✅ read:org - Read org and team membership
✅ read:project - Read organization projects
```

### 步骤 3: 生成并保存 Token
1. 点击 **Generate token**
2. **重要**：复制生成的 Token（格式：`ghp_xxxxxxxxxxxxxxxxxxxx`）
3. Token 只显示一次，请立即保存到安全的地方

---

## 2. 配置 GitHub Secrets

### 步骤 1: 访问仓库 Secrets
1. 打开您的 Mini-Agent fork 仓库：https://github.com/zhaofei0923/Mini-Agent
2. 点击 **Settings** 标签
3. 在左侧菜单中找到 **Secrets and variables** → **Actions**

### 步骤 2: 添加 GITHUB_TOKEN
1. 点击 **New repository secret**
2. Name: `GITHUB_TOKEN`
3. Secret: 粘贴您刚刚创建的 GitHub Personal Access Token
4. 点击 **Add secret**

### 步骤 3: 验证 Secrets 列表
确认以下 Secrets 已配置：
- ✅ `PYPI_API_TOKEN` - 用于 PyPI 发布
- ✅ `TEST_PYPI_API_TOKEN` - 用于 TestPyPI 测试发布
- ✅ `GITHUB_TOKEN` - 用于 GitHub 仓库操作

---

## 3. 配置 GitHub MCP

GitHub MCP 提供原生的 GitHub API 集成，使 agent 能够直接与 GitHub 交互。

### 方法一：使用官方 GitHub MCP 服务器

编辑 `mini_agent/config/mcp.json`：

```json
{
  "mcpServers": {
    "github": {
      "command": ["npx", "-y", "@modelcontextprotocol/server-github"],
      "disabled": false,
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    "minimax_search": {
      "command": ["python", "-m", "mini_agent.tools.mcp_loader"],
      "disabled": true,
      "env": {}
    },
    "memory": {
      "command": ["python", "-m", "mini_agent.tools.mcp_loader"],
      "disabled": true,
      "env": {}
    }
  }
}
```

### 方法二：使用 GitHub Actions 验证 Token

在 GitHub Actions workflow 中，Token 会自动作为 `GITHUB_TOKEN` 环境变量提供。

```yaml
# .github/workflows/github-ops.yml
name: GitHub Operations Demo

on:
  push:
    branches: [main, develop]

jobs:
  github-api-demo:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: List PRs using GitHub Token
        run: |
          # GITHUB_TOKEN 自动可用
          gh pr list --state all --json number,title,author
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## 4. 验证配置

### 4.1 测试 GitHub Token 权限

运行以下命令验证 Token 是否正确配置：

```bash
# 方法 1: 使用 GitHub CLI（如果已安装）
gh auth status

# 方法 2: 使用 curl 直接测试
curl -H "Authorization: Bearer YOUR_GITHUB_TOKEN" \
     https://api.github.com/user

# 方法 3: 测试 API 速率限制
curl -H "Authorization: Bearer YOUR_GITHUB_TOKEN" \
     https://api.github.com/rate_limit
```

### 4.2 测试 GitHub MCP 连接

创建一个测试脚本：

```python
# test_github_mcp.py
import asyncio
import os
from mini_agent.tools.mcp_loader import load_mcp_tools

async def test_github_mcp():
    """测试 GitHub MCP 连接"""
    # 确保 GITHUB_TOKEN 已设置
    if not os.environ.get("GITHUB_TOKEN"):
        print("❌ GITHUB_TOKEN 未设置")
        return

    try:
        # 加载 GitHub MCP 工具
        tools = await load_mcp_tools("github")
        print(f"✅ GitHub MCP 工具加载成功: {len(tools)} 个工具")

        # 列出可用工具
        for tool in tools[:5]:  # 只显示前 5 个
            print(f"  - {tool.name}")

    except Exception as e:
        print(f"❌ GitHub MCP 连接失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_github_mcp())
```

### 4.3 测试仓库操作功能

```python
# test_github_ops.py
from github import Github
import os

def test_github_operations():
    """测试 GitHub 仓库操作"""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("❌ GITHUB_TOKEN 未设置")
        return

    g = Github(token)
    user = g.get_user()
    print(f"✅ 登录用户: {user.login}")

    # 列出仓库
    repos = list(user.get_repos()[:3])
    print(f"✅ 找到 {len(repos)} 个仓库:")
    for repo in repos:
        print(f"  - {repo.full_name}")

    # 测试创建 issue
    try:
        # 这是测试，实际使用需要指定具体仓库
        print("✅ GitHub API 连接正常")
    except Exception as e:
        print(f"❌ API 调用失败: {e}")

if __name__ == "__main__":
    test_github_operations()
```

---

## 5. 常见问题

### Q1: Token 权限不足

**错误**: `401 Unauthorized` 或 `Resource not accessible`

**解决**:
1. 检查 Token 权限是否包含 `repo`
2. 如果是组织仓库，确认 Token 有组织访问权限
3. 重新生成 Token 并勾选所需权限

### Q2: MCP 服务器连接失败

**错误**: `Connection refused` 或超时

**解决**:
1. 确认 npx 已安装：`npm install -g npx`
2. 检查网络连接
3. 查看日志获取详细错误信息

### Q3: GitHub Actions 中 GITHUB_TOKEN 不可用

**错误**: `GITHUB_TOKEN not found in environment`

**解决**:
1. 确认已在仓库 Secrets 中配置 `GITHUB_TOKEN`
2. 确认 workflow 文件语法正确
3. 等待几分钟后重试

### Q4: 速率限制错误

**错误**: `403 Rate limit exceeded`

**解决**:
1. GitHub API 速率限制：每小时 5000 次请求（认证后）
2. 等待一小时后重试
3. 使用 `gh auth refresh` 刷新 Token

### Q5: MCP 工具未加载

**错误**: `No tools found` 或空工具列表

**解决**:
1. 确认 `mcp.json` 语法正确
2. 检查 MCP 服务器是否启动成功
3. 查看 agent 日志获取详细错误

---

## 6. 安全建议

### 6.1 Token 安全
- ✅ 不要将 Token 硬编码在代码中
- ✅ 使用 GitHub Secrets 存储 Token
- ✅ 定期轮换 Token（建议每 90 天）
- ✅ 立即撤销并重新创建意外泄露的 Token

### 6.2 最小权限原则
- 只授予必要的权限
- 使用细粒度 Token（Fine-grained Personal Access Tokens）以获得更精细的控制
- 为不同用途创建不同的 Token

### 6.3 监控和审计
- 定期检查 Token 使用情况
- 查看 GitHub审计日志
- 设置安全警报

---

## 7. 支持的功能

配置完成后，agent 将能够：

### 仓库操作
- ✅ 创建和管理 Pull Requests
- ✅ 创建和管理 Issues
- ✅ 提交代码到仓库
- ✅ 管理分支（创建、删除、列出）
- ✅ 查看和管理文件

### 工作流程
- ✅ 触发和管理 GitHub Actions
- ✅ 查看工作流运行状态
- ✅ 管理 Secrets 和 Variables

### 搜索和查询
- ✅ 搜索仓库、代码、Issues、PRs
- ✅ 获取用户和组织信息
- ✅ 查看和管理项目

### MCP 工具集成
- ✅ 使用 GitHub MCP 原生工具
- ✅ 与其他 MCP 服务器集成
- ✅ 自定义 MCP 服务器配置

---

## 8. 故障排除流程图

```
开始
  ↓
Token 是否已创建？
  ├─ 否 → 步骤 1: 创建 Token
  └─ 是 → 下一步
  ↓
Token 是否配置在 Secrets 中？
  ├─ 否 → 步骤 2: 配置 Secrets
  └─ 是 → 下一步
  ↓
mcp.json 是否已配置？
  ├─ 否 → 步骤 3: 配置 MCP
  └─ 是 → 下一步
  ↓
测试 GitHub API 连接
  ├─ 成功 → ✅ 配置完成！
  └─ 失败 → 查看第 5 节常见问题
```

---

## 9. 相关文档

- [GitHub Personal Access Tokens 文档](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
- [GitHub REST API 文档](https://docs.github.com/en/rest)
- [GitHub MCP 服务器](https://github.com/modelcontextprotocol/servers/tree/main/src/github)
- [Mini-Agent 项目文档](../README.md)

---

**最后更新**: 2024-01-23
**维护者**: Mini-Agent Team
