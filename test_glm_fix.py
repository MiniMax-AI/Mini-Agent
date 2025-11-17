"""Test GLM support after fixes."""

import asyncio
from pathlib import Path
import yaml

from mini_agent.llm import LLMClient
from mini_agent.schema import LLMProvider, Message


async def test_glm_with_llm_client():
    """Test GLM using LLMClient wrapper."""
    print("\n" + "="*80)
    print("Testing GLM with LLMClient (Fixed Version)")
    print("="*80)

    # Load config
    config_path = Path("mini_agent/config/config.yaml")
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Create client with OpenAI provider (GLM)
    client = LLMClient(
        api_key=config["api_key"],
        provider=LLMProvider.OPENAI,
        api_base=config["api_base"],
        model=config["model"],
    )

    print(f"Provider: {client.provider}")
    print(f"Model: {client.model}")
    print(f"API Base: {client.api_base}")

    # Simple test
    messages = [
        Message(role="system", content="You are a helpful assistant."),
        Message(role="user", content="Say 'Hello, GLM!' and nothing else."),
    ]

    try:
        print("\n📤 Sending request...")
        response = await client.generate(messages=messages)

        print("\n✅ Request successful!")
        print(f"\n📝 Content: {response.content}")
        print(f"\n🤔 Thinking (first 200 chars): {response.thinking[:200] if response.thinking else 'None'}...")
        print(f"\n🏁 Finish reason: {response.finish_reason}")

        # Verify response
        if response.content and ("Hello" in response.content or "hello" in response.content):
            print("\n✅ TEST PASSED: Response contains expected content")
            return True
        else:
            print(f"\n❌ TEST FAILED: Response doesn't contain 'Hello': {response.content}")
            return False

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run test."""
    success = await test_glm_with_llm_client()

    print("\n" + "="*80)
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Tests failed")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
