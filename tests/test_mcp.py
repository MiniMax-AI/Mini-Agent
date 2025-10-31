"""Test cases for MCP tool loading."""

import asyncio

import pytest

from mini_agent.tools.mcp_loader import load_mcp_tools_async


@pytest.mark.asyncio
async def test_mcp_tools_loading():
    """Test loading MCP tools from mcp.json."""
    print("\n=== Testing MCP Tool Loading ===")

    # Load MCP tools
    tools = await load_mcp_tools_async("mcp.json")

    print(f"Loaded {len(tools)} MCP tools")

    # Display loaded tools
    if tools:
        for tool in tools:
            desc = (
                tool.description[:60]
                if len(tool.description) > 60
                else tool.description
            )
            print(f"  - {tool.name}: {desc}")

    # Test should pass even if no tools loaded (e.g., no mcp.json or no Node.js)
    assert isinstance(tools, list), "Should return a list of tools"
    print("✅ MCP tools loading test passed")


@pytest.mark.asyncio
async def test_mcp_tool_execution():
    """Test executing an MCP tool if available."""
    print("\n=== Testing MCP Tool Execution ===")

    tools = await load_mcp_tools_async("mcp.json")

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


async def main():
    """Run all MCP tests."""
    print("=" * 80)
    print("Running MCP Integration Tests")
    print("=" * 80)
    print(
        "\nNote: These tests require Node.js and will use MCP servers defined in mcp.json"
    )
    print("Tests will pass even if MCP is not configured.\n")

    await test_mcp_tools_loading()
    await test_mcp_tool_execution()

    print("\n" + "=" * 80)
    print("MCP tests completed! ✅")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
