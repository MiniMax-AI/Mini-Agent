"""Test cases for MCP tool loading and Git-based MCP servers."""

import asyncio
import json
import tempfile
from pathlib import Path

import pytest

from mini_agent.tools.mcp_loader import (
    MCPServerConnection,
    MCPTimeoutConfig,
    _determine_connection_type,
    cleanup_mcp_connections,
    get_mcp_timeout_config,
    load_mcp_tools_async,
    set_mcp_timeout_config,
)


@pytest.fixture(scope="module")
def mcp_config():
    """Read MCP configuration."""
    mcp_config_path = Path("mini_agent/config/mcp-example.json")
    with open(mcp_config_path, encoding="utf-8") as f:
        return json.load(f)


# =============================================================================
# Connection Type Detection Tests
# =============================================================================


class TestDetermineConnectionType:
    """Tests for _determine_connection_type function."""

    def test_stdio_with_command_only(self):
        """STDIO is default when only command is specified."""
        config = {"command": "npx", "args": ["-y", "some-server"]}
        assert _determine_connection_type(config) == "stdio"

    def test_stdio_explicit_type(self):
        """Explicit type=stdio should return stdio."""
        config = {"command": "npx", "type": "stdio"}
        assert _determine_connection_type(config) == "stdio"

    def test_url_defaults_to_streamable_http(self):
        """URL without explicit type should default to streamable_http."""
        config = {"url": "https://mcp.example.com/mcp"}
        assert _determine_connection_type(config) == "streamable_http"

    def test_sse_explicit_type(self):
        """Explicit type=sse should return sse."""
        config = {"url": "https://mcp.example.com/sse", "type": "sse"}
        assert _determine_connection_type(config) == "sse"

    def test_http_explicit_type(self):
        """Explicit type=http should return http."""
        config = {"url": "https://mcp.example.com/http", "type": "http"}
        assert _determine_connection_type(config) == "http"

    def test_streamable_http_explicit_type(self):
        """Explicit type=streamable_http should return streamable_http."""
        config = {"url": "https://mcp.example.com/mcp", "type": "streamable_http"}
        assert _determine_connection_type(config) == "streamable_http"

    def test_case_insensitive_type(self):
        """Type should be case insensitive."""
        config = {"url": "https://mcp.example.com/sse", "type": "SSE"}
        assert _determine_connection_type(config) == "sse"

    def test_empty_config_defaults_to_stdio(self):
        """Empty config should default to stdio."""
        config = {}
        assert _determine_connection_type(config) == "stdio"

    def test_unknown_type_with_url_defaults_to_streamable_http(self):
        """Unknown type with URL should default to streamable_http."""
        config = {"url": "https://mcp.example.com/mcp", "type": "unknown"}
        assert _determine_connection_type(config) == "streamable_http"


# =============================================================================
# MCPServerConnection Initialization Tests
# =============================================================================


class TestMCPServerConnectionInit:
    """Tests for MCPServerConnection initialization."""

    def test_stdio_connection_init(self):
        """Test STDIO connection initialization."""
        conn = MCPServerConnection(
            name="test-stdio",
            connection_type="stdio",
            command="npx",
            args=["-y", "test-server"],
            env={"API_KEY": "test"},
        )
        assert conn.name == "test-stdio"
        assert conn.connection_type == "stdio"
        assert conn.command == "npx"
        assert conn.args == ["-y", "test-server"]
        assert conn.env == {"API_KEY": "test"}
        assert conn.url is None

    def test_url_connection_init(self):
        """Test URL-based connection initialization."""
        conn = MCPServerConnection(
            name="test-url",
            connection_type="streamable_http",
            url="https://mcp.example.com/mcp",
            headers={"Authorization": "Bearer token"},
        )
        assert conn.name == "test-url"
        assert conn.connection_type == "streamable_http"
        assert conn.url == "https://mcp.example.com/mcp"
        assert conn.headers == {"Authorization": "Bearer token"}
        assert conn.command is None

    def test_sse_connection_init(self):
        """Test SSE connection initialization."""
        conn = MCPServerConnection(
            name="test-sse",
            connection_type="sse",
            url="https://mcp.example.com/sse",
        )
        assert conn.name == "test-sse"
        assert conn.connection_type == "sse"
        assert conn.url == "https://mcp.example.com/sse"

    def test_default_values(self):
        """Test default values for optional parameters."""
        conn = MCPServerConnection(name="test-default")
        assert conn.connection_type == "stdio"
        assert conn.args == []
        assert conn.env == {}
        assert conn.headers == {}

    def test_timeout_overrides(self):
        """Test per-server timeout override initialization."""
        conn = MCPServerConnection(
            name="test-timeout",
            connection_type="sse",
            url="https://mcp.example.com/sse",
            connect_timeout=15.0,
            execute_timeout=90.0,
            sse_read_timeout=180.0,
        )
        assert conn.connect_timeout == 15.0
        assert conn.execute_timeout == 90.0
        assert conn.sse_read_timeout == 180.0


# =============================================================================
# Timeout Configuration Tests
# =============================================================================


class TestMCPTimeoutConfig:
    """Tests for MCP timeout configuration."""

    def test_default_timeout_config(self):
        """Test default timeout configuration values."""
        config = MCPTimeoutConfig()
        assert config.connect_timeout == 10.0
        assert config.execute_timeout == 60.0
        assert config.sse_read_timeout == 120.0

    def test_custom_timeout_config(self):
        """Test custom timeout configuration values."""
        config = MCPTimeoutConfig(
            connect_timeout=5.0,
            execute_timeout=30.0,
            sse_read_timeout=60.0,
        )
        assert config.connect_timeout == 5.0
        assert config.execute_timeout == 30.0
        assert config.sse_read_timeout == 60.0

    def test_set_global_timeout_config(self):
        """Test setting global timeout configuration."""
        # Save original config
        original = get_mcp_timeout_config()
        original_connect = original.connect_timeout
        original_execute = original.execute_timeout

        try:
            # Set new values
            set_mcp_timeout_config(connect_timeout=20.0, execute_timeout=120.0)
            config = get_mcp_timeout_config()
            assert config.connect_timeout == 20.0
            assert config.execute_timeout == 120.0
        finally:
            # Restore original values
            set_mcp_timeout_config(
                connect_timeout=original_connect,
                execute_timeout=original_execute,
            )

    def test_partial_timeout_config_update(self):
        """Test partial update of timeout configuration."""
        original = get_mcp_timeout_config()
        original_connect = original.connect_timeout
        original_execute = original.execute_timeout
        original_sse = original.sse_read_timeout

        try:
            # Only update connect_timeout
            set_mcp_timeout_config(connect_timeout=25.0)
            config = get_mcp_timeout_config()
            assert config.connect_timeout == 25.0
            # Other values should remain unchanged from previous test state
        finally:
            set_mcp_timeout_config(
                connect_timeout=original_connect,
                execute_timeout=original_execute,
                sse_read_timeout=original_sse,
            )


class TestMCPServerConnectionTimeout:
    """Tests for MCPServerConnection timeout behavior."""

    def test_get_effective_connect_timeout_with_override(self):
        """Test getting effective connect timeout with per-server override."""
        conn = MCPServerConnection(
            name="test",
            connection_type="sse",
            url="https://example.com",
            connect_timeout=20.0,
        )
        assert conn._get_connect_timeout() == 20.0

    def test_get_effective_connect_timeout_without_override(self):
        """Test getting effective connect timeout using global default."""
        conn = MCPServerConnection(
            name="test",
            connection_type="sse",
            url="https://example.com",
        )
        # Should use global default
        global_config = get_mcp_timeout_config()
        assert conn._get_connect_timeout() == global_config.connect_timeout

    def test_get_effective_execute_timeout_with_override(self):
        """Test getting effective execute timeout with per-server override."""
        conn = MCPServerConnection(
            name="test",
            connection_type="sse",
            url="https://example.com",
            execute_timeout=180.0,
        )
        assert conn._get_execute_timeout() == 180.0


# =============================================================================
# URL-based Config Loading Tests
# =============================================================================


@pytest.mark.asyncio
async def test_url_config_validation():
    """Test that URL-based config without url is rejected."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        config = {
            "mcpServers": {
                "broken-sse": {
                    "type": "sse",
                    # Missing "url" field
                }
            }
        }
        json.dump(config, f)
        f.flush()

        try:
            tools = await load_mcp_tools_async(f.name)
            # Should return empty list (server skipped due to missing url)
            assert tools == []
        finally:
            await cleanup_mcp_connections()
            Path(f.name).unlink()


@pytest.mark.asyncio
async def test_stdio_config_validation():
    """Test that STDIO config without command is rejected."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        config = {
            "mcpServers": {
                "broken-stdio": {
                    "type": "stdio",
                    # Missing "command" field
                }
            }
        }
        json.dump(config, f)
        f.flush()

        try:
            tools = await load_mcp_tools_async(f.name)
            # Should return empty list (server skipped due to missing command)
            assert tools == []
        finally:
            await cleanup_mcp_connections()
            Path(f.name).unlink()


@pytest.mark.asyncio
async def test_mixed_config_loading():
    """Test loading config with both STDIO and URL-based servers."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        config = {
            "mcpServers": {
                "stdio-server": {"command": "npx", "args": ["-y", "nonexistent-server"], "disabled": True},
                "url-server": {"url": "https://mcp.nonexistent.example.com/mcp", "disabled": True},
                "sse-server": {"url": "https://sse.nonexistent.example.com/sse", "type": "sse", "disabled": True},
            }
        }
        json.dump(config, f)
        f.flush()

        try:
            # All servers are disabled, should return empty but not error
            tools = await load_mcp_tools_async(f.name)
            assert tools == []
        finally:
            await cleanup_mcp_connections()
            Path(f.name).unlink()


@pytest.mark.asyncio
async def test_mcp_tools_loading():
    """Test loading MCP tools from mcp.json."""
    print("\n=== Testing MCP Tool Loading ===")

    try:
        # Load MCP tools
        tools = await load_mcp_tools_async("mini_agent/config/mcp-example.json")

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
        tools = await load_mcp_tools_async("mini_agent/config/mcp-example.json")

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
        tools = await load_mcp_tools_async("mini_agent/config/mcp-example.json")

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
        tools = await load_mcp_tools_async("mini_agent/config/mcp-example.json")

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


@pytest.mark.asyncio
async def test_connection_timeout_on_unreachable_server():
    """Test that connection to unreachable server times out properly."""
    print("\n=== Testing Connection Timeout ===")

    # Set a short timeout for testing
    original = get_mcp_timeout_config()
    original_connect = original.connect_timeout

    try:
        set_mcp_timeout_config(connect_timeout=2.0)

        conn = MCPServerConnection(
            name="unreachable-test",
            connection_type="streamable_http",
            url="https://10.255.255.1:9999/mcp",  # Non-routable IP, will timeout
        )

        import time

        start = time.time()
        success = await conn.connect()
        elapsed = time.time() - start

        assert success is False, "Connection to unreachable server should fail"
        # Should timeout within reasonable time (connect_timeout + some overhead)
        assert elapsed < 10.0, f"Should timeout quickly, but took {elapsed:.1f}s"
        print(f"✅ Connection timed out as expected in {elapsed:.1f}s")

    finally:
        set_mcp_timeout_config(connect_timeout=original_connect)
        await cleanup_mcp_connections()


@pytest.mark.asyncio
async def test_per_server_timeout_override_in_config():
    """Test that per-server timeout overrides from config are respected."""
    print("\n=== Testing Per-Server Timeout Override ===")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        config = {
            "mcpServers": {
                "fast-server": {
                    "url": "https://10.255.255.1:9999/mcp",
                    "connect_timeout": 1.0,  # Very short timeout
                    "execute_timeout": 30.0,
                }
            }
        }
        json.dump(config, f)
        f.flush()

        try:
            import time

            start = time.time()
            tools = await load_mcp_tools_async(f.name)
            elapsed = time.time() - start

            # Should fail due to unreachable server
            assert tools == []
            # Should respect the short 1.0s connect_timeout
            assert elapsed < 5.0, f"Should use per-server timeout, but took {elapsed:.1f}s"
            print(f"✅ Per-server timeout override worked, failed in {elapsed:.1f}s")

        finally:
            await cleanup_mcp_connections()
            Path(f.name).unlink()


async def main():
    """Run all MCP tests."""
    print("=" * 80)
    print("Running MCP Integration Tests")
    print("=" * 80)
    print("\nNote: These tests require Node.js and will use MCP servers defined in mcp-example.json or your local mcp.json")
    print("Tests will pass even if MCP is not configured.\n")

    await test_mcp_tools_loading()
    await test_mcp_tool_execution()
    await test_connection_timeout_on_unreachable_server()

    print("\n" + "=" * 80)
    print("MCP tests completed! ✅")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
