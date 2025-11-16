"""Test cases for MCP tool loading and Git-based MCP servers."""

import asyncio
import json
from pathlib import Path

import pytest

from ye_linghua.tools.mcp_loader import cleanup_mcp_connections, load_mcp_tools_async


@pytest.fixture(scope="module")
def mcp_config():
    """Read MCP configuration."""
    mcp_config_path = Path("mini_agent/config/mcp.json")
    with open(mcp_config_path, encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.asyncio
async def test_mcp_tools_loading():
    """Test loading MCP tools from mcp.json."""
    print("\n=== Testing MCP Tool Loading ===")

    try:
        # Load MCP tools
        tools = await load_mcp_tools_async("mini_agent/config/mcp.json")

        print(f"Loaded {len(tools)} MCP tools")

        # Display loaded tools
        if tools:
            for tool in tools:
                desc = tool.description[:60] if len(tool.description) > 60 else tool.description
                print(f"  - {tool.name}: {desc}")

        # Test should pass even if no tools loaded (e.g., no mcp.json or no Node.js)
        assert isinstance(tools, list), "Should return a list of tools"
        print("✅ MCP tools loading test passed")

    finally:
        # Cleanup MCP connections
        await cleanup_mcp_connections()


@pytest.mark.asyncio
async def test_git_mcp_loading(mcp_config):
    """Test loading MCP Server from Git repository (minimax_search)."""
    print("\n" + "=" * 70)
    print("Testing: Loading MiniMax Search MCP Server from Git repository")
    print("=" * 70)

    git_url = mcp_config["mcpServers"]["minimax_search"]["args"][1]
    print(f"\n📍 Git repository: {git_url}")
    print("⏳ Cloning and installing...\n")

    try:
        # Load MCP tools
        tools = await load_mcp_tools_async("mini_agent/config/mcp.json")

        print("\n✅ Loaded successfully!")
        print("\n📊 Statistics:")
        print(f"  • Total tools loaded: {len(tools)}")

        # Verify tools list is not empty
        assert isinstance(tools, list), "Should return a list of tools"

        if tools:
            print("\n🔧 Available tools:")
            for tool in tools:
                desc = tool.description[:80] + "..." if len(tool.description) > 80 else tool.description
                print(f"  • {tool.name}")
                print(f"    {desc}")

        # Verify expected tools from minimax_search
        expected_tools = ["search", "parallel_search", "browse"]
        loaded_tool_names = [t.name for t in tools]

        print("\n🔍 Function verification:")
        found_count = 0
        for expected in expected_tools:
            if expected in loaded_tool_names:
                print(f"  ✅ {expected} - OK")
                found_count += 1
            else:
                print(f"  ❌ {expected} - Missing")

        # If no expected tools found, minimax_search connection failed
        if found_count == 0:
            print("\n⚠️  Warning: minimax_search MCP Server connection failed")
            print("This may be due to SSH key authentication requirements or network issues")
            pytest.skip("minimax_search MCP Server connection failed, skipping test")

        # Assert all expected tools exist
        missing_tools = [t for t in expected_tools if t not in loaded_tool_names]
        assert len(missing_tools) == 0, f"Missing tools: {missing_tools}"

        print("\n" + "=" * 70)
        print("✅ All tests passed! MCP Server loaded from Git repository successfully!")
        print("=" * 70)

    finally:
        # Cleanup MCP connections
        print("\n🧹 Cleaning up MCP connections...")
        await cleanup_mcp_connections()


@pytest.mark.asyncio
async def test_git_mcp_tool_availability():
    """Test Git MCP tool availability."""
    print("\n=== Testing Git MCP Tool Availability ===")

    try:
        tools = await load_mcp_tools_async("mini_agent/config/mcp.json")

        if not tools:
            pytest.skip("No MCP tools loaded")
            return

        # Find search tool
        search_tool = None
        for tool in tools:
            if "search" in tool.name.lower():
                search_tool = tool
                break

        assert search_tool is not None, "Should contain search-related tools"
        print(f"✅ Found search tool: {search_tool.name}")

    finally:
        await cleanup_mcp_connections()


@pytest.mark.asyncio
async def test_mcp_tool_execution():
    """Test executing an MCP tool if available (memory server)."""
    print("\n=== Testing MCP Tool Execution ===")

    try:
        tools = await load_mcp_tools_async("mini_agent/config/mcp.json")

        if not tools:
            print("⚠️  No MCP tools loaded, skipping execution test")
            pytest.skip("No MCP tools available")
            return

        # Try to find and test create_entities (from memory server)
        create_tool = None
        for tool in tools:
            if tool.name == "create_entities":
                create_tool = tool
                break

        if create_tool:
            print(f"Testing: {create_tool.name}")
            try:
                result = await create_tool.execute(
                    entities=[
                        {
                            "name": "test_entity",
                            "entityType": "test",
                            "observations": ["Test observation for pytest"],
                        }
                    ]
                )
                assert result.success, f"Tool execution should succeed: {result.error}"
                print(f"✅ Tool execution successful: {result.content[:100]}")
            except Exception as e:
                pytest.fail(f"Tool execution failed: {e}")
        else:
            print("⚠️  create_entities tool not found, skipping execution test")
            pytest.skip("create_entities tool not available")

    finally:
        await cleanup_mcp_connections()


async def main():
    """Run all MCP tests."""
    print("=" * 80)
    print("Running MCP Integration Tests")
    print("=" * 80)
    print("\nNote: These tests require Node.js and will use MCP servers defined in mcp.json")
    print("Tests will pass even if MCP is not configured.\n")

    await test_mcp_tools_loading()
    await test_mcp_tool_execution()

    print("\n" + "=" * 80)
    print("MCP tests completed! ✅")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
