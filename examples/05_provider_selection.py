"""Example: Using LLMClient with different providers.

This example demonstrates how to use the LLMClient wrapper with different
LLM providers (Anthropic or OpenAI) through the provider parameter.
"""

import asyncio
from pathlib import Path

import yaml

from mini_agent import LLMClient, LLMProvider, Message


async def demo_anthropic_provider():
    """Demo using LLMClient with Anthropic provider."""
    print("\n" + "=" * 60)
    print("DEMO: LLMClient with Anthropic Provider")
    print("=" * 60)

    # Load config
    config_path = Path("mini_agent/config/config.yaml")
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Initialize client with Anthropic provider
    client = LLMClient(
        api_key=config["api_key"],
        provider=LLMProvider.ANTHROPIC,  # Specify Anthropic provider
        model=config.get("model", "MiniMax-M2.1"),
    )

    print(f"Provider: {client.provider}")
    print(f"API Base: {client.api_base}")

    # Simple question
    messages = [Message(role="user", content="Say 'Hello from Anthropic!'")]
    print(f"\n👤 User: {messages[0].content}")

    try:
        response = await client.generate(messages)
        if response.thinking:
            print(f"💭 Thinking: {response.thinking}")
        print(f"💬 Model: {response.content}")
        print("✅ Anthropic provider demo completed")
    except Exception as e:
        print(f"❌ Error: {e}")


async def demo_openai_provider():
    """Demo using LLMClient with OpenAI provider."""
    print("\n" + "=" * 60)
    print("DEMO: LLMClient with OpenAI Provider")
    print("=" * 60)

    # Load config
    config_path = Path("mini_agent/config/config.yaml")
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Initialize client with OpenAI provider
    client = LLMClient(
        api_key=config["api_key"],
        provider=LLMProvider.OPENAI,  # Specify OpenAI provider
        model=config.get("model", "MiniMax-M2.1"),
    )

    print(f"Provider: {client.provider}")
    print(f"API Base: {client.api_base}")

    # Simple question
    messages = [Message(role="user", content="Say 'Hello from OpenAI!'")]
    print(f"\n👤 User: {messages[0].content}")

    try:
        response = await client.generate(messages)
        if response.thinking:
            print(f"💭 Thinking: {response.thinking}")
        print(f"💬 Model: {response.content}")
        print("✅ OpenAI provider demo completed")
    except Exception as e:
        print(f"❌ Error: {e}")


async def demo_default_provider():
    """Demo using LLMClient with default provider."""
    print("\n" + "=" * 60)
    print("DEMO: LLMClient with Default Provider (Anthropic)")
    print("=" * 60)

    # Load config
    config_path = Path("mini_agent/config/config.yaml")
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Initialize client without specifying provider (defaults to Anthropic)
    client = LLMClient(
        api_key=config["api_key"],
        model=config.get("model", "MiniMax-M2.1"),
    )

    print(f"Provider (default): {client.provider}")
    print(f"API Base: {client.api_base}")

    # Simple question
    messages = [Message(role="user", content="Say 'Hello with default provider!'")]
    print(f"\n👤 User: {messages[0].content}")

    try:
        response = await client.generate(messages)
        print(f"💬 Model: {response.content}")
        print("✅ Default provider demo completed")
    except Exception as e:
        print(f"❌ Error: {e}")


async def demo_provider_comparison():
    """Compare responses from both providers."""
    print("\n" + "=" * 60)
    print("DEMO: Provider Comparison")
    print("=" * 60)

    # Load config
    config_path = Path("mini_agent/config/config.yaml")
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Create clients for both providers
    anthropic_client = LLMClient(
        api_key=config["api_key"],
        provider=LLMProvider.ANTHROPIC,
        model=config.get("model", "MiniMax-M2.1"),
    )

    openai_client = LLMClient(
        api_key=config["api_key"],
        provider=LLMProvider.OPENAI,
        model=config.get("model", "MiniMax-M2.1"),
    )

    # Same question for both
    messages = [Message(role="user", content="What is 2+2?")]
    print(f"\n👤 Question: {messages[0].content}\n")

    try:
        # Get response from Anthropic
        anthropic_response = await anthropic_client.generate(messages)
        print(f"🔵 Anthropic: {anthropic_response.content}")

        # Get response from OpenAI
        openai_response = await openai_client.generate(messages)
        print(f"🟢 OpenAI: {openai_response.content}")

        print("\n✅ Provider comparison completed")
    except Exception as e:
        print(f"❌ Error: {e}")


async def main():
    """Run all demos."""
    print("\n🚀 LLM Provider Selection Demo")
    print("This demo shows how to use LLMClient with different providers.")
    print("Make sure you have configured API key in config.yaml.")

    try:
        # Demo default provider
        await demo_default_provider()

        # Demo Anthropic provider
        await demo_anthropic_provider()

        # Demo OpenAI provider
        await demo_openai_provider()

        # Demo provider comparison
        await demo_provider_comparison()

        print("\n✅ All demos completed successfully!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

