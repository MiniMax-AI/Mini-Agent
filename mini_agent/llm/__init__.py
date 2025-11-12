"""Provider factory for LLMs and backwards-compatible client wrapper.

To address maintainability, providers are implemented separately under
mini_agent.llm.providers.* and this module exposes a thin LLMClient that
constructs the right provider based on configuration.
"""

from typing import Any

from ..retry import RetryConfig as RetryConfigBase
from ..schema import LLMResponse, Message


class LLMClient:
    """Backwards-compatible facade that dispatches to a provider instance."""

    def __init__(
        self,
        api_key: str,
        api_base: str = "https://api.minimax.io/anthropic",
        model: str = "MiniMax-M2",
        provider: str = "anthropic",
        retry_config: RetryConfigBase | None = None,
    ):
        self.provider_name = (provider or "anthropic").lower()
        self.retry_config = retry_config

        # Lazy import to avoid circulars
        if self.provider_name == "anthropic":
            from .providers.anthropic import AnthropicLLM

            self._impl = AnthropicLLM(api_key, api_base, model, retry_config)
        else:
            from .providers.openai_compat import OpenAILLM

            self._impl = OpenAILLM(api_key, api_base, model, retry_config)

        # Expose a retry callback passthrough for CLI printing
        self.retry_callback = None
        if hasattr(self._impl, "set_retry_callback"):
            self._impl.set_retry_callback(lambda exc, attempt: self.retry_callback and self.retry_callback(exc, attempt))

    async def generate(self, messages: list[Message], tools: list[dict[str, Any]] | None = None) -> LLMResponse:
        return await self._impl.generate(messages, tools)

