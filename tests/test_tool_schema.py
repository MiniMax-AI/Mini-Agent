"""Test cases for Tool schema methods."""

from typing import Any

import pytest

from ye_linghua.tools.base import Tool, ToolResult


class MockWeatherTool(Tool):
    """Mock weather tool for testing."""

    @property
    def name(self) -> str:
        return "get_weather"

    @property
    def description(self) -> str:
        return "Get weather information"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "Location name",
                },
            },
            "required": ["location"],
        }

    async def execute(self, **kwargs) -> ToolResult:
        return ToolResult(success=True, content="Weather data")


class MockCalculatorTool(Tool):
    """Mock calculator tool for testing."""

    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return "Perform calculations"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Math expression",
                },
            },
            "required": ["expression"],
        }

    async def execute(self, **kwargs) -> ToolResult:
        return ToolResult(success=True, content="42")


class MockSearchTool(Tool):
    """Mock search tool with complex schema."""

    @property
    def name(self) -> str:
        return "search_database"

    @property
    def description(self) -> str:
        return "Search the database"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query",
                },
                "filters": {
                    "type": "object",
                    "properties": {
                        "category": {"type": "string"},
                        "min_price": {"type": "number"},
                        "max_price": {"type": "number"},
                    },
                },
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100,
                    "default": 10,
                },
            },
            "required": ["query"],
        }

    async def execute(self, **kwargs) -> ToolResult:
        return ToolResult(success=True, content="Search results")


class MockEnumTool(Tool):
    """Mock tool with enum parameter."""

    @property
    def name(self) -> str:
        return "set_status"

    @property
    def description(self) -> str:
        return "Set status"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["active", "inactive", "pending"],
                    "description": "Status value",
                }
            },
            "required": ["status"],
        }

    async def execute(self, **kwargs) -> ToolResult:
        return ToolResult(success=True, content="Status set")


def test_tool_to_schema():
    """Test Tool.to_schema() method."""
    tool = MockWeatherTool()
    schema = tool.to_schema()

    assert isinstance(schema, dict)
    assert schema["name"] == "get_weather"
    assert schema["description"] == "Get weather information"
    assert "input_schema" in schema
    assert schema["input_schema"]["type"] == "object"
    assert "location" in schema["input_schema"]["properties"]
    assert schema["input_schema"]["required"] == ["location"]


def test_tool_to_openai_schema():
    """Test Tool.to_openai_schema() method."""
    tool = MockWeatherTool()
    schema = tool.to_openai_schema()

    assert isinstance(schema, dict)
    assert schema["type"] == "function"
    assert "function" in schema
    assert schema["function"]["name"] == "get_weather"
    assert schema["function"]["description"] == "Get weather information"
    assert "parameters" in schema["function"]
    assert schema["function"]["parameters"]["type"] == "object"
    assert "location" in schema["function"]["parameters"]["properties"]


def test_tool_schema_complex():
    """Test tool with complex input schema."""
    tool = MockSearchTool()
    schema = tool.to_schema()

    assert schema["name"] == "search_database"
    assert "query" in schema["input_schema"]["properties"]
    assert "filters" in schema["input_schema"]["properties"]
    assert "limit" in schema["input_schema"]["properties"]
    assert schema["input_schema"]["required"] == ["query"]


def test_tool_openai_schema_complex():
    """Test OpenAI schema conversion for complex tool."""
    tool = MockSearchTool()
    schema = tool.to_openai_schema()

    assert schema["type"] == "function"
    params = schema["function"]["parameters"]
    assert "query" in params["properties"]
    assert "filters" in params["properties"]
    assert "limit" in params["properties"]
    assert params["required"] == ["query"]


def test_multiple_tools():
    """Test creating multiple tool instances."""
    tool1 = MockWeatherTool()
    tool2 = MockCalculatorTool()

    tools = [tool1, tool2]
    assert len(tools) == 2
    assert tools[0].name == "get_weather"
    assert tools[1].name == "calculator"

    # Convert all to Anthropic schemas
    anthropic_schemas = [t.to_schema() for t in tools]
    assert len(anthropic_schemas) == 2
    assert all(isinstance(s, dict) for s in anthropic_schemas)
    assert all("name" in s and "description" in s and "input_schema" in s for s in anthropic_schemas)

    # Convert all to OpenAI schemas
    openai_schemas = [t.to_openai_schema() for t in tools]
    assert len(openai_schemas) == 2
    assert all(isinstance(s, dict) for s in openai_schemas)
    assert all(s["type"] == "function" for s in openai_schemas)


def test_tool_with_enum():
    """Test tool with enum parameter."""
    tool = MockEnumTool()
    schema = tool.to_schema()

    status_prop = schema["input_schema"]["properties"]["status"]
    assert "enum" in status_prop
    assert status_prop["enum"] == ["active", "inactive", "pending"]

    # Test OpenAI schema too
    openai_schema = tool.to_openai_schema()
    status_prop_openai = openai_schema["function"]["parameters"]["properties"]["status"]
    assert "enum" in status_prop_openai
    assert status_prop_openai["enum"] == ["active", "inactive", "pending"]


def test_tool_schema_consistency():
    """Test that both schema methods produce consistent data."""
    tool = MockCalculatorTool()

    anthropic_schema = tool.to_schema()
    openai_schema = tool.to_openai_schema()

    # Names should match
    assert anthropic_schema["name"] == openai_schema["function"]["name"]
    # Descriptions should match
    assert anthropic_schema["description"] == openai_schema["function"]["description"]
    # Parameters should match (just different nesting)
    assert anthropic_schema["input_schema"] == openai_schema["function"]["parameters"]


@pytest.mark.asyncio
async def test_tool_execute():
    """Test that tools can be executed."""
    tool = MockWeatherTool()
    result = await tool.execute(location="Tokyo")

    assert isinstance(result, ToolResult)
    assert result.success is True
    assert result.content == "Weather data"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
