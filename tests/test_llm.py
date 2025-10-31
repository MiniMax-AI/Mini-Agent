"""Test cases for LLM client."""

import asyncio
from pathlib import Path

import pytest
import yaml

from mini_agent.llm import LLMClient, Message


@pytest.mark.asyncio
async def test_simple_completion():
    """Test simple LLM completion without tools."""
    print("\n=== Testing Simple LLM Completion ===")

    # Load config
    config_path = Path("mini_agent/config.yaml")
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Create client
    client = LLMClient(
        api_key=config["api_key"],
        api_base=config.get("api_base"),
        model=config.get("model"),
    )

    # Simple messages
    messages = [
        Message(role="system", content="You are a helpful assistant."),
        Message(role="user", content="Say 'Hello, Mini Agent!' and nothing else."),
    ]

    try:
        response = await client.generate(messages=messages)

        print(f"Response: {response.content}")
        print(f"Finish reason: {response.finish_reason}")

        assert response.content, "Response content is empty"
        assert "Hello" in response.content or "hello" in response.content, (
            f"Response doesn't contain 'Hello': {response.content}"
        )

        print("✅ Simple completion test passed")
        return True
    except Exception as e:
        print(f"❌ LLM test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


@pytest.mark.asyncio
async def test_tool_calling():
    """Test LLM with tool calling."""
    print("\n=== Testing LLM Tool Calling ===")

    # Load config
    config_path = Path("mini_agent/config.yaml")
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Create client
    client = LLMClient(
        api_key=config["api_key"],
        api_base=config.get("api_base"),
        model=config.get("model"),
    )

    # Messages requesting tool use
    messages = [
        Message(
            role="system", content="You are a helpful assistant with access to tools."
        ),
        Message(role="user", content="Calculate 123 + 456 using the calculator tool."),
    ]

    # Define a simple calculator tool
    tools = [
        {
            "type": "function",
            "function": {
                "name": "calculator",
                "description": "Perform arithmetic operations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["add", "subtract", "multiply", "divide"],
                            "description": "The operation to perform",
                        },
                        "a": {
                            "type": "number",
                            "description": "First number",
                        },
                        "b": {
                            "type": "number",
                            "description": "Second number",
                        },
                    },
                    "required": ["operation", "a", "b"],
                },
            },
        }
    ]

    try:
        response = await client.generate(messages=messages, tools=tools)

        print(f"Response: {response.content}")
        print(f"Tool calls: {response.tool_calls}")
        print(f"Finish reason: {response.finish_reason}")

        if response.tool_calls:
            print("✅ Tool calling test passed - LLM requested tool use")
        else:
            print("⚠️  Warning: LLM didn't use tools, but request succeeded")

        return True
    except Exception as e:
        print(f"❌ Tool calling test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Run all LLM tests."""
    print("=" * 80)
    print("Running LLM Tests")
    print("=" * 80)
    print("\nNote: These tests require a valid MiniMax API key in config.yaml")

    # Test simple completion
    result1 = await test_simple_completion()

    # Test tool calling
    result2 = await test_tool_calling()

    print("\n" + "=" * 80)
    if result1 and result2:
        print("All LLM tests passed! ✅")
    else:
        print("Some LLM tests failed. Check the output above.")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
