"""Abstract base class for LLM providers (Strategy pattern)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ...retry import RetryConfig as RetryConfigBase
from ...schema import LLMResponse, Message


class BaseLLM(ABC):
    def __init__(
        self,
        api_key: str,
        api_base: str,
        model: str,
        retry_config: RetryConfigBase | None = None,
    ) -> None:
        self.api_key = api_key
        self.api_base = api_base
        self.model = model
        self.retry_config = retry_config
        self._retry_callback = None

    def set_retry_callback(self, cb):
        self._retry_callback = cb

    @abstractmethod
    async def generate(self, messages: list[Message], tools: list[dict[str, Any]] | None = None) -> LLMResponse:
        raise NotImplementedError

