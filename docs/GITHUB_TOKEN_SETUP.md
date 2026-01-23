# GitHub Token 配置指南

## 概述

本文档介绍如何配置GitHub Token，使Mini-Agent能够：
- 操作GitHub仓库（创建PR、提交代码等）
- 使用GitHub MCP工具

## 步骤1：创建GitHub Personal Access Token

### 1.1 访问Token创建页面

打开浏览器，访问：
```
https://github.com/settings/tokens
```

### 1.2 生成新Token

1. 点击 **"Generate new token (classic)"**
2. 设置Token名称：
   - **Note**: `Mini-Agent GitHub Token`
   - **Expiration**: 建议选择 "90 days" 或 "No expiration"
3. 选择权限（Scopes）：
   - ✅ `repo` - 完全控制私有仓库（必需）
   - ✅ `workflow` - 更新GitHub Actions工作流
   - ✅ `delete_repo` - 删除仓库（可选）
   - ✅ `read:user` - 读取用户数据
   - ✅ `user` - 更新用户数据

### 1.3 生成并保存Token

1. 点击 **"Generate token"**
2. **重要**：复制生成的token（格式类似：`ghp_xxxxxxxxxxxxxxxxxxxx`）
3. 立即保存到安全的地方（关闭页面后无法再次查看）

## 步骤2：添加到GitHub Secrets

### 2.1 访问仓库Secrets设置

打开浏览器，访问：
```
https://github.com/zhaofei0923/Mini-Agent/settings/secrets
```

### 2.2 添加新Secret

1. 点击 **"New repository secret"**
2. 填写：
   - **Name**: `GITHUB_TOKEN`
   - **Secret**: 粘贴你刚才生成的token
3. 点击 **"Add secret"**

## 步骤3：配置GitHub MCP（可选）

### 3.1 编辑MCP配置文件

编辑 `mini_agent/config/mcp.json`：

```json
{
    "mcpServers": {
        "github": {
            "command": "uvx",
            "args": [
                "mcp-server-github"
            ],
            "env": {
                "GITHUB_TOKEN": "${GITHUB_TOKEN}"
            },
            "disabled": false
        }
    }
}
```

### 3.2 或使用官方GitHub MCP服务器

从官方MCP服务器安装：

```bash
# 安装官方GitHub MCP服务器
npm install @modelcontextprotocol/server-github
```

## 步骤4：验证配置

### 4.1 本地测试

```bash
# 设置环境变量
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"

# 测试GitHub API访问
gh auth login
gh repo view zhaofei0923/Mini-Agent
```

### 4.2 在Mini-Agent中使用

Mini-Agent现在可以：
- 创建Pull Request
- 提交代码
- 创建Issue
- 管理分支
- 使用GitHub搜索

示例：
```python
# 创建PR
await agent.run("请创建一个PR，将 feature/multi-agent-orchestration 合并到 main 分支")
```

## 可用功能

配置完成后，Mini-Agent可以执行以下GitHub操作：

### 仓库操作
- 📁 查看仓库信息
- 📂 浏览文件和目录
- 📄 读取文件内容

### PR操作
- 📋 列出PR
- 🔍 查看PR详情
- ✏️ 创建PR
- 💬 添加PR评论
- ✅ 合并PR

### Issue操作
- 📝 创建Issue
- 📖 查看Issue
- 💬 添加Issue评论
- 🏷️ 管理标签

### 工作流操作
- 🚀 查看Actions状态
- 📊 查看workflow运行
- ▶️ 触发workflow

## 故障排除

### 问题1：Token权限不足

**错误**：`401 Unauthorized`

**解决**：
1. 检查Token权限是否包含 `repo`
2. 确认Token未过期
3. 重新生成Token

### 问题2：无法访问私有仓库

**错误**：`404 Not Found`

**解决**：
1. 确认Token有访问该仓库的权限
2. 检查仓库设置中的访问控制

### 问题3：MCP服务器无法启动

**错误**：MCP连接失败

**解决**：
1. 确认已安装MCP服务器
2. 检查环境变量配置
3. 查看MCP服务器日志

## 安全建议

⚠️ **重要安全提醒**：

1. **不要在代码中硬编码Token**
2. **使用GitHub Secrets存储Token**
3. **定期轮换Token**（建议每90天）
4. **使用最小权限原则**（只授予必需的权限）
5. **监控Token使用情况**

## 相关链接

- [GitHub Personal Access Tokens](https://github.com/settings/tokens)
- [GitHub MCP Server](https://github.com/modelcontextprotocol/servers/tree/main/src/github)
- [Mini-Agent文档](../README.md)
