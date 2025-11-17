"""Debug script to test GLM API response."""

import asyncio
from pathlib import Path
import yaml
from openai import AsyncOpenAI

async def test_glm_api():
    """Test GLM API directly to see the actual response."""
    # Load config
    config_path = Path("mini_agent/config/config.yaml")
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    print(f"API Base: {config['api_base']}")
    print(f"Model: {config['model']}")

    # Create client
    client = AsyncOpenAI(
        api_key=config["api_key"],
        base_url=config["api_base"],
    )

    # Test 1: Simple request without extra_body
    print("\n" + "="*80)
    print("Test 1: Simple request WITHOUT reasoning_split")
    print("="*80)
    try:
        response = await client.chat.completions.create(
            model=config["model"],
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello' and nothing else."},
            ],
        )
        print(f"Response type: {type(response)}")
        print(f"Response: {response}")
        print(f"Has choices: {hasattr(response, 'choices')}")
        if hasattr(response, 'choices'):
            print(f"Choices: {response.choices}")
            if response.choices:
                print(f"First choice: {response.choices[0]}")
                print(f"Message: {response.choices[0].message}")
                print(f"Content: {response.choices[0].message.content}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

    # Test 2: Request with reasoning_split
    print("\n" + "="*80)
    print("Test 2: Request WITH reasoning_split")
    print("="*80)
    try:
        response = await client.chat.completions.create(
            model=config["model"],
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello' and nothing else."},
            ],
            extra_body={"reasoning_split": True},
        )
        print(f"Response type: {type(response)}")
        print(f"Response: {response}")
        print(f"Has choices: {hasattr(response, 'choices')}")
        if hasattr(response, 'choices'):
            print(f"Choices: {response.choices}")
            if response.choices:
                print(f"First choice: {response.choices[0]}")
                print(f"Message: {response.choices[0].message}")
                print(f"Content: {response.choices[0].message.content}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_glm_api())
