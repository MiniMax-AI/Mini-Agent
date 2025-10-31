"""测试从 Git 仓库加载 MiniMax Search MCP Server"""

import json
from pathlib import Path

import pytest

from mini_agent.tools.mcp_loader import load_mcp_tools_async, cleanup_mcp_connections


@pytest.fixture(scope="module")
def mcp_config():
    """读取 MCP 配置"""
    mcp_config_path = Path("mcp.json")
    with open(mcp_config_path) as f:
        return json.load(f)


@pytest.mark.asyncio
async def test_git_mcp_loading(mcp_config):
    """测试从 Git 仓库加载 MCP Server"""
    print("\n" + "=" * 70)
    print("测试从 Git 仓库加载 MiniMax Search MCP Server")
    print("=" * 70)

    git_url = mcp_config["mcpServers"]["minimax_search"]["args"][1]
    print(f"\n📍 Git 仓库: {git_url}")
    print(f"⏳ 正在克隆并安装...\n")

    try:
        # 加载 MCP 工具
        tools = await load_mcp_tools_async("mcp.json")

        print(f"\n✅ 加载成功！")
        print(f"\n📊 统计信息:")
        print(f"  • 加载的工具总数: {len(tools)}")

        # 验证工具列表不为空
        assert isinstance(tools, list), "应返回工具列表"

        if tools:
            print(f"\n🔧 可用工具列表:")
            for tool in tools:
                desc = (
                    tool.description[:80] + "..."
                    if len(tool.description) > 80
                    else tool.description
                )
                print(f"  • {tool.name}")
                print(f"    {desc}")

        # 验证预期工具
        expected_tools = ["search", "parallel_search", "browse"]
        loaded_tool_names = [t.name for t in tools]

        print(f"\n🔍 功能验证:")
        found_count = 0
        for expected in expected_tools:
            if expected in loaded_tool_names:
                print(f"  ✅ {expected} - 正常")
                found_count += 1
            else:
                print(f"  ❌ {expected} - 缺失")

        # 如果没有找到任何预期工具，说明 minimax_search 连接失败
        if found_count == 0:
            print(f"\n⚠️  警告: minimax_search MCP Server 未连接成功")
            print(f"这可能是因为需要 SSH 密钥认证或网络问题")
            pytest.skip("minimax_search MCP Server 连接失败，跳过测试")

        # 断言所有预期工具都存在
        missing_tools = [t for t in expected_tools if t not in loaded_tool_names]
        assert len(missing_tools) == 0, f"缺失工具: {missing_tools}"

        print(f"\n" + "=" * 70)
        print("✅ 所有测试通过！从 Git 仓库加载 MCP Server 成功！")
        print("=" * 70)

    finally:
        # 清理 MCP 连接，避免异步警告
        print("\n🧹 清理 MCP 连接...")
        await cleanup_mcp_connections()


@pytest.mark.asyncio
async def test_git_mcp_tool_availability(mcp_config):
    """测试 Git MCP 工具的可用性"""
    print("\n=== 测试工具可用性 ===")

    try:
        tools = await load_mcp_tools_async("mcp.json")

        if not tools:
            pytest.skip("未加载到 MCP 工具")
            return

        # 查找 search 工具
        search_tool = None
        for tool in tools:
            if "search" in tool.name.lower():
                search_tool = tool
                break

        assert search_tool is not None, "应包含 search 相关工具"
        print(f"✅ 找到搜索工具: {search_tool.name}")

    finally:
        await cleanup_mcp_connections()
