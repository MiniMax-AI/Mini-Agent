#!/usr/bin/env python3
"""
GitHub 配置测试脚本
测试 GitHub Token 和 MCP 的配置是否正确
"""

import os
import sys
import json
import asyncio
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))


def test_github_api_connection():
    """测试 GitHub API 连接"""
    print("\n" + "=" * 60)
    print("🧪 测试 1: GitHub API 连接")
    print("=" * 60)

    token = os.environ.get("GITHUB_TOKEN")

    if not token:
        print("❌ GITHUB_TOKEN 未设置")
        print("💡 提示: 请确保已在 GitHub Secrets 中配置 GITHUB_TOKEN")
        return False

    print(f"✅ GITHUB_TOKEN 已检测到 (前缀: {token[:7]}...)")

    # 测试 API 连接
    import urllib.request
    import ssl

    # 创建 SSL 上下文
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    try:
        # 测试用户信息
        url = "https://api.github.com/user"
        request = urllib.request.Request(url)
        request.add_header("Authorization", f"Bearer {token}")
        request.add_header("Accept", "application/vnd.github.v3+json")

        with urllib.request.urlopen(request, timeout=10, context=ssl_context) as response:
            data = json.loads(response.read().decode())
            print(f"✅ API 连接成功!")
            print(f"   用户名: {data.get('login', 'Unknown')}")
            print(f"   邮箱: {data.get('email', 'Not public')}")
            print(f"   公司: {data.get('company', 'Not specified')}")
            print(f"   公开仓库数: {data.get('public_repos', 0)}")
            print(f"   私有仓库数: {data.get('total_private_repos', 0)}")

        return True

    except Exception as e:
        print(f"❌ API 连接失败: {e}")
        return False


def test_repository_access():
    """测试仓库访问权限"""
    print("\n" + "=" * 60)
    print("🧪 测试 2: 仓库访问权限")
    print("=" * 60)

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("❌ GITHUB_TOKEN 未设置")
        return False

    try:
        import urllib.request
        import json

        # 测试访问 Mini-Agent 仓库
        urls = [
            ("https://api.github.com/repos/zhaofei0923/Mini-Agent", "用户仓库"),
            ("https://api.github.com/repos/MiniMax-AI/Mini-Agent", "上游仓库"),
        ]

        results = []
        for url, name in urls:
            try:
                request = urllib.request.Request(url)
                request.add_header("Authorization", f"Bearer {token}")
                request.add_header("Accept", "application/vnd.github.v3+json")

                with urllib.request.urlopen(request, timeout=10) as response:
                    data = json.loads(response.read().decode())
                    print(f"✅ {name} 访问成功")
                    print(f"   仓库: {data['full_name']}")
                    print(f"   Stars: {data['stargazers_count']}")
                    print(f"   Forks: {data['forks_count']}")
                    print(f"   可见性: {'Private' if data['private'] else 'Public'}")
                    results.append(True)
            except Exception as e:
                print(f"❌ {name} 访问失败: {e}")
                results.append(False)

        return all(results)

    except Exception as e:
        print(f"❌ 仓库访问测试失败: {e}")
        return False


def test_mcp_configuration():
    """测试 MCP 配置"""
    print("\n" + "=" * 60)
    print("🧪 测试 3: MCP 配置")
    print("=" * 60)

    try:
        # 读取 MCP 配置文件
        mcp_path = Path(__file__).parent / "mini_agent" / "config" / "mcp.json"
        
        if not mcp_path.exists():
            print(f"❌ MCP 配置文件不存在: {mcp_path}")
            return False

        with open(mcp_path, 'r', encoding='utf-8') as f:
            mcp_config = json.load(f)

        print("✅ MCP 配置文件读取成功")

        # 检查 GitHub MCP 服务器配置
        if "mcpServers" not in mcp_config:
            print("❌ mcpServers 配置不存在")
            return False

        servers = mcp_config["mcpServers"]
        
        if "github" not in servers:
            print("❌ GitHub MCP 服务器未配置")
            return False

        github_config = servers["github"]
        print(f"✅ GitHub MCP 服务器已配置")

        # 检查配置项
        required_fields = ["command", "disabled", "env"]
        for field in required_fields:
            if field not in github_config:
                print(f"❌ GitHub MCP 缺少必要配置: {field}")
                return False
            print(f"   {field}: {github_config[field]}")

        # 检查是否启用
        if github_config.get("disabled", False):
            print("⚠️ GitHub MCP 已禁用")
            return False
        else:
            print("✅ GitHub MCP 已启用")

        return True

    except Exception as e:
        print(f"❌ MCP 配置测试失败: {e}")
        return False


def test_github_operations():
    """测试 GitHub 操作功能"""
    print("\n" + "=" * 60)
    print("🧪 测试 4: GitHub 操作功能")
    print("=" * 60)

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("❌ GITHUB_TOKEN 未设置，跳过操作测试")
        return None  # 跳过，不算失败

    try:
        import urllib.request
        import json
        from datetime import datetime, timedelta

        operations = []

        # 测试 1: 列出用户的仓库
        print("\n📋 测试列出用户仓库...")
        url = "https://api.github.com/user/repos?per_page=5&sort=updated"
        request = urllib.request.Request(url)
        request.add_header("Authorization", f"Bearer {token}")
        request.add_header("Accept", "application/vnd.github.v3+json")

        with urllib.request.urlopen(request, timeout=10) as response:
            repos = json.loads(response.read().decode())
            print(f"✅ 成功列出 {len(repos)} 个仓库")
            for repo in repos[:3]:
                print(f"   - {repo['full_name']} (⭐{repo['stargazers_count']})")
            operations.append(("列出仓库", True))

        # 测试 2: 列出 Issues
        print("\n📝 测试列出 Issues...")
        url = "https://api.github.com/repos/zhaofei0923/Mini-Agent/issues?state=all&per_page=5"
        request = urllib.request.Request(url)
        request.add_header("Authorization", f"Bearer {token}")
        request.add_header("Accept", "application/vnd.github.v3+json")

        with urllib.request.urlopen(request, timeout=10) as response:
            issues = json.loads(response.read().decode())
            print(f"✅ 成功列出 {len(issues)} 个 Issues")
            operations.append(("列出 Issues", True))

        # 测试 3: 列出 Pull Requests
        print("\n🔀 测试列出 Pull Requests...")
        url = "https://api.github.com/repos/zhaofei0923/Mini-Agent/pulls?state=all&per_page=5"
        request = urllib.request.Request(url)
        request.add_header("Authorization", f"Bearer {token}")
        request.add_header("Accept", "application/vnd.github.v3+json")

        with urllib.request.urlopen(request, timeout=10) as response:
            prs = json.loads(response.read().decode())
            print(f"✅ 成功列出 {len(prs)} 个 Pull Requests")
            if prs:
                print(f"   最新 PR: #{prs[0]['number']} - {prs[0]['title']}")
            operations.append(("列出 PRs", True))

        # 测试 4: 获取工作流运行状态
        print("\n⚙️ 测试获取 Actions 工作流...")
        url = "https://api.github.com/repos/zhaofei0923/Mini-Agent/actions/runs?per_page=3"
        request = urllib.request.Request(url)
        request.add_header("Authorization", f"Bearer {token}")
        request.add_header("Accept", "application/vnd.github.v3+json")

        with urllib.request.urlopen(request, timeout=10) as response:
            runs = json.loads(response.read().decode())
            print(f"✅ 成功获取工作流运行记录")
            if runs.get('workflow_runs'):
                latest = runs['workflow_runs'][0]
                print(f"   最新运行: {latest['name']} - {latest['status']}")
            operations.append(("获取工作流", True))

        return all(result for _, result in operations)

    except Exception as e:
        print(f"❌ GitHub 操作测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mcp_tool_loading():
    """测试 MCP 工具加载"""
    print("\n" + "=" * 60)
    print("🧪 测试 5: MCP 工具加载")
    print("=" * 60)

    try:
        # 尝试导入 MCP 加载器
        from mini_agent.tools.mcp_loader import load_mcp_tools

        print("✅ MCP 加载器导入成功")

        # 注意：由于 GitHub MCP 需要 npx 和网络连接，
        # 我们在这里只验证配置，不实际加载
        print("💡 提示: MCP 工具将在 agent 运行时自动加载")
        print("   需要确保:")
        print("   1. npx 已安装 (npm install -g npx)")
        print("   2. GITHUB_TOKEN 已配置在 GitHub Secrets 中")
        print("   3. GitHub Actions 环境变量已设置")

        return True

    except ImportError as e:
        print(f"❌ MCP 加载器导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ MCP 工具测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("\n🚀 GitHub 配置综合测试")
    print("=" * 60)

    results = {}

    # 测试 1: API 连接
    results["API 连接"] = test_github_api_connection()

    # 测试 2: 仓库访问
    results["仓库访问"] = test_repository_access()

    # 测试 3: MCP 配置
    results["MCP 配置"] = test_mcp_configuration()

    # 测试 4: GitHub 操作
    results["GitHub 操作"] = test_github_operations()

    # 测试 5: MCP 工具加载
    results["MCP 工具加载"] = test_mcp_tool_loading()

    # 总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)

    passed = 0
    failed = 0
    skipped = 0

    for test_name, result in results.items():
        if result is None:
            status = "⏭️ 跳过"
            skipped += 1
        elif result:
            status = "✅ 通过"
            passed += 1
        else:
            status = "❌ 失败"
            failed += 1

        print(f"{test_name}: {status}")

    print("\n" + "-" * 60)
    print(f"总计: {passed} 通过, {failed} 失败, {skipped} 跳过")

    if failed == 0:
        print("\n🎉 所有测试通过！GitHub 配置正确。")
        print("\n💡 下一步:")
        print("   1. 在 GitHub Actions 中运行工作流以测试 CI/CD")
        print("   2. 尝试让 agent 操作 GitHub 仓库")
        print("   3. 查看 MCP 工具是否正常工作")
        return 0
    else:
        print(f"\n⚠️ 有 {failed} 个测试失败，请检查配置。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
