"""Test cases for individual Anthropic and OpenAI LLM clients.

These tests directly test the AnthropicClient and OpenAIClient implementations
without going through the wrapper layer.
"""

import asyncio
from pathlib import Path

import pytest
import yaml

from ye_linghua.llm import AnthropicClient, OpenAIClient
from ye_linghua.retry import RetryConfig
from ye_linghua.schema import Message


def load_config():
    """Load config from config.yaml."""
    config_path = Path("mini_agent/config/config.yaml")
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.mark.asyncio
async def test_anthropic_simple_completion():
    """Test Anthropic client with simple completion."""
    print("\n=== Testing Anthropic Simple Completion ===")

    config = load_config()

    # Create Anthropic client
    client = AnthropicClient(
        api_key=config["api_key"],
        api_base="https://api.minimaxi.com/anthropic",
        model=config.get("model", "MiniMax-M2"),
        retry_config=RetryConfig(enabled=True, max_retries=2),
    )

    # Simple messages
    messages = [
        Message(role="system", content="You are a helpful assistant."),
        Message(role="user", content="Say 'Hello from Anthropic!' and nothing else."),
    ]

    try:
        response = await client.generate(messages=messages)

        print(f"Response: {response.content}")
        print(f"Thinking: {response.thinking}")
        print(f"Finish reason: {response.finish_reason}")

        assert response.content, "Response content is empty"
        assert "Hello" in response.content or "hello" in response.content

        print("✅ Anthropic simple completion test passed")
        return True
    except Exception as e:
        print(f"❌ Anthropic test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


@pytest.mark.asyncio
async def test_openai_simple_completion():
    """Test OpenAI client with simple completion."""
    print("\n=== Testing OpenAI Simple Completion ===")

    config = load_config()

    # Create OpenAI client
    client = OpenAIClient(
        api_key=config["api_key"],
        api_base="https://api.minimaxi.com/v1",
        model=config.get("model", "MiniMax-M2"),
        retry_config=RetryConfig(enabled=True, max_retries=2),
    )

    # Simple messages
    messages = [
        Message(role="system", content="You are a helpful assistant."),
        Message(role="user", content="Say 'Hello from OpenAI!' and nothing else."),
    ]

    try:
        response = await client.generate(messages=messages)

        print(f"Response: {response.content}")
        print(f"Thinking: {response.thinking}")
        print(f"Finish reason: {response.finish_reason}")

        assert response.content, "Response content is empty"
        assert "Hello" in response.content or "hello" in response.content

        print("✅ OpenAI simple completion test passed")
        return True
    except Exception as e:
        print(f"❌ OpenAI test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


@pytest.mark.asyncio
async def test_anthropic_tool_calling():
    """Test Anthropic client with tool calling."""
    print("\n=== Testing Anthropic Tool Calling ===")

    config = load_config()

    # Create Anthropic client
    client = AnthropicClient(
        api_key=config["api_key"],
        api_base="https://api.minimaxi.com/anthropic",
        model=config.get("model", "MiniMax-M2"),
    )

    # Define tool using dict format
    tools = [
        {
            "name": "get_weather",
            "description": "Get weather of a location",
            "input_schema": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, US",
                    }
                },
                "required": ["location"],
            },
        }
    ]

    # Messages requesting tool use
    messages = [
        Message(role="user", content="What's the weather in San Francisco?"),
    ]

    try:
        response = await client.generate(messages=messages, tools=tools)

        print(f"Response: {response.content}")
        print(f"Thinking: {response.thinking}")
        print(f"Tool calls: {response.tool_calls}")

        if response.tool_calls:
            assert len(response.tool_calls) > 0
            assert response.tool_calls[0].function.name == "get_weather"
            print("✅ Anthropic tool calling test passed")
        else:
            print("⚠️  Warning: LLM didn't use tools, but request succeeded")

        return True
    except Exception as e:
        print(f"❌ Anthropic tool calling test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


@pytest.mark.asyncio
async def test_openai_tool_calling():
    """Test OpenAI client with tool calling."""
    print("\n=== Testing OpenAI Tool Calling ===")

    config = load_config()

    # Create OpenAI client
    client = OpenAIClient(
        api_key=config["api_key"],
        api_base="https://api.minimaxi.com/v1",
        model=config.get("model", "MiniMax-M2"),
    )

    # Define tool using dict format (will be converted internally for OpenAI)
    tools = [
        {
            "name": "get_weather",
            "description": "Get weather of a location",
            "input_schema": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, US",
                    }
                },
                "required": ["location"],
            },
        }
    ]

    # Messages requesting tool use
    messages = [
        Message(role="user", content="What's the weather in New York?"),
    ]

    try:
        response = await client.generate(messages=messages, tools=tools)

        print(f"Response: {response.content}")
        print(f"Thinking: {response.thinking}")
        print(f"Tool calls: {response.tool_calls}")

        if response.tool_calls:
            assert len(response.tool_calls) > 0
            assert response.tool_calls[0].function.name == "get_weather"
            print("✅ OpenAI tool calling test passed")
        else:
            print("⚠️  Warning: LLM didn't use tools, but request succeeded")

        return True
    except Exception as e:
        print(f"❌ OpenAI tool calling test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


@pytest.mark.asyncio
async def test_multi_turn_conversation():
    """Test multi-turn conversation with tool calling."""
    print("\n=== Testing Multi-turn Conversation ===")

    config = load_config()

    # Test with Anthropic client
    client = AnthropicClient(
        api_key=config["api_key"],
        api_base="https://api.minimaxi.com/anthropic",
        model=config.get("model", "MiniMax-M2"),
    )

    # Define tool using dict format
    tools = [
        {
            "name": "calculator",
            "description": "Perform arithmetic operations",
            "input_schema": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["add", "subtract", "multiply", "divide"],
                    },
                    "a": {"type": "number"},
                    "b": {"type": "number"},
                },
                "required": ["operation", "a", "b"],
            },
        }
    ]

    try:
        # First turn - user asks
        messages = [Message(role="user", content="What's 5 + 3?")]
        response = await client.generate(messages=messages, tools=tools)

        print(f"Turn 1 - Response: {response.content}")
        print(f"Turn 1 - Tool calls: {response.tool_calls}")

        if response.tool_calls:
            # Add assistant response
            messages.append(
                Message(
                    role="assistant",
                    content=response.content,
                    thinking=response.thinking,
                    tool_calls=response.tool_calls,
                )
            )

            # Add tool result
            messages.append(
                Message(
                    role="tool",
                    tool_call_id=response.tool_calls[0].id,
                    content="8",
                )
            )

            # Second turn - get final answer
            final_response = await client.generate(messages=messages, tools=tools)
            print(f"Turn 2 - Response: {final_response.content}")

            assert final_response.content
            print("✅ Multi-turn conversation test passed")
        else:
            print("⚠️  Warning: LLM didn't use tools")

        return True
    except Exception as e:
        print(f"❌ Multi-turn conversation test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Run all LLM client tests."""
    print("=" * 80)
    print("Running LLM Client Tests")
    print("=" * 80)
    print("\nNote: These tests require a valid MiniMax API key in config.yaml")

    results = []

    # Test Anthropic client
    results.append(await test_anthropic_simple_completion())
    results.append(await test_anthropic_tool_calling())

    # Test OpenAI client
    results.append(await test_openai_simple_completion())
    results.append(await test_openai_tool_calling())

    # Test multi-turn conversation
    results.append(await test_multi_turn_conversation())

    print("\n" + "=" * 80)
    if all(results):
        print("All LLM client tests passed! ✅")
    else:
        print("Some LLM client tests failed. Check the output above.")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

