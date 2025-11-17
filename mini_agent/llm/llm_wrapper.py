"""LLM client wrapper that supports multiple providers.

This module provides a unified interface for different LLM providers
(Anthropic and OpenAI) through a single LLMClient class.
"""

import logging

from ..retry import RetryConfig
from ..schema import LLMProvider, LLMResponse, Message
from .anthropic_client import AnthropicClient
from .base import LLMClientBase
from .openai_client import OpenAIClient

logger = logging.getLogger(__name__)


class LLMClient:
    """LLM Client wrapper supporting multiple providers.

    This class provides a unified interface for different LLM providers.
    It automatically instantiates the correct underlying client based on
    the provider parameter and appends the appropriate API endpoint suffix.

    Supported providers:
    - anthropic: Appends /anthropic to api_base
    - openai: Appends /v1 to api_base
    """

    def __init__(
        self,
        api_key: str,
        provider: LLMProvider = LLMProvider.ANTHROPIC,
        api_base: str = "https://api.minimaxi.com",
        model: str = "MiniMax-M2",
        retry_config: RetryConfig | None = None,
    ):
        """Initialize LLM client with specified provider.

        Args:
            api_key: API key for authentication
            provider: LLM provider (anthropic or openai)
            api_base: Base URL for the API (default: https://api.minimaxi.com)
                     Will be automatically suffixed with /anthropic or /v1 based on provider
            model: Model name to use
            retry_config: Optional retry configuration
        """
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self.retry_config = retry_config or RetryConfig()

        # for backward compatibility
        api_base = api_base.replace("/anthropic", "")

        # Append provider-specific suffix to api_base
        if provider == LLMProvider.ANTHROPIC:
            full_api_base = f"{api_base.rstrip('/')}/anthropic"
        elif provider == LLMProvider.OPENAI:
            full_api_base = f"{api_base.rstrip('/')}/v1"
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        self.api_base = full_api_base

        # Instantiate the appropriate client
        self._client: LLMClientBase
        if provider == LLMProvider.ANTHROPIC:
            self._client = AnthropicClient(
                api_key=api_key,
                api_base=full_api_base,
                model=model,
                retry_config=retry_config,
            )
        elif provider == LLMProvider.OPENAI:
            # Auto-detect if we should enable reasoning_split
            # Enable for MiniMax and GLM models (both support interleaved thinking)
            # Disable for standard GPT models
            enable_reasoning_split = (
                model.startswith("MiniMax") or model.lower().startswith("glm")
            )

            self._client = OpenAIClient(
                api_key=api_key,
                api_base=full_api_base,
                model=model,
                retry_config=retry_config,
                enable_reasoning_split=enable_reasoning_split,
            )
            logger.info("OpenAI client reasoning_split: %s (model: %s)", enable_reasoning_split, model)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        logger.info("Initialized LLM client with provider: %s, api_base: %s", provider, full_api_base)

    @property
    def retry_callback(self):
        """Get retry callback."""
        return self._client.retry_callback

    @retry_callback.setter
    def retry_callback(self, value):
        """Set retry callback."""
        self._client.retry_callback = value

    async def generate(
        self,
        messages: list[Message],
        tools: list | None = None,
    ) -> LLMResponse:
        """Generate response from LLM.

        Args:
            messages: List of conversation messages
            tools: Optional list of Tool objects or dicts

        Returns:
            LLMResponse containing the generated content
        """
        return await self._client.generate(messages, tools)
