"""LLM client for MiniMax M2 via Anthropic-compatible API."""

import json
import logging
from typing import Any, Dict, List

import httpx
from pydantic import BaseModel

from .retry import RetryConfig as RetryConfigBase
from .retry import async_retry

logger = logging.getLogger(__name__)


class Message(BaseModel):
    """Chat message."""

    role: str  # "system", "user", "assistant", "tool"
    content: str | List[Dict[str, Any]]  # Can be string or list of content blocks
    tool_calls: List[Dict[str, Any]] | None = None
    tool_call_id: str | None = None
    name: str | None = None  # For tool role


class LLMResponse(BaseModel):
    """LLM response."""

    content: str
    thinking: str | None = None  # Extended thinking blocks
    tool_calls: List[Dict[str, Any]] | None = None
    finish_reason: str


class LLMClient:
    """MiniMax M2 LLM Client via Anthropic-compatible endpoint.

    Supported models:
    - MiniMax-M2
    """

    def __init__(
        self,
        api_key: str,
        api_base: str = "https://api.minimax.io/anthropic",
        model: str = "MiniMax-M2",
        retry_config: RetryConfigBase | None = None,
    ):
        self.api_key = api_key
        self.api_base = api_base
        self.model = model
        self.retry_config = retry_config or RetryConfigBase()

        # 用于追踪重试次数的回调
        self.retry_callback = None

    def _convert_tool_to_anthropic_format(self, tool: Dict[str, Any]) -> Dict[str, Any]:
        """Convert OpenAI tool format to Anthropic format."""
        function = tool.get("function", {})
        return {
            "name": function.get("name"),
            "description": function.get("description"),
            "input_schema": function.get("parameters", {}),
        }

    async def _make_api_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """执行 API 请求（可重试的核心方法）

        Args:
            payload: 请求负载

        Returns:
            API 响应结果

        Raises:
            Exception: API 调用失败
        """
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.api_base}/v1/messages",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01",
                },
                json=payload,
            )

            result = response.json()

        # Check for errors (Anthropic format)
        if result.get("type") == "error":
            error_info = result.get("error", {})
            error_msg = (
                f"API Error ({error_info.get('type')}): {error_info.get('message')}"
            )
            raise Exception(error_msg)

        # Check for MiniMax base_resp errors
        if "base_resp" in result:
            base_resp = result["base_resp"]
            status_code = base_resp.get("status_code")
            status_msg = base_resp.get("status_msg")

            if status_code not in [0, 1000, None]:
                error_msg = f"MiniMax API Error (code {status_code}): {status_msg}"
                if status_code == 1008:
                    error_msg += "\n\n⚠️  账户余额不足，请前往 MiniMax 平台充值"
                elif status_code == 2013:
                    error_msg += f"\n\n⚠️  模型 '{self.model}' 不支持"
                raise Exception(error_msg)

        return result

    async def generate(
        self,
        messages: List[Message],
        tools: List[Dict[str, Any]] | None = None,
    ) -> LLMResponse:
        """Generate response from LLM."""
        # Extract system message (Anthropic requires it separately)
        system_message = None
        api_messages = []

        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
                continue

            # For user and assistant messages
            if msg.role in ["user", "assistant"]:
                # Handle tool results embedded in assistant messages
                if msg.role == "assistant" and msg.tool_calls:
                    # Build content blocks for assistant with tool calls
                    content_blocks = []
                    if msg.content:
                        content_blocks.append({"type": "text", "text": msg.content})

                    # Add tool use blocks
                    for tool_call in msg.tool_calls:
                        content_blocks.append(
                            {
                                "type": "tool_use",
                                "id": tool_call["id"],
                                "name": tool_call["function"]["name"],
                                "input": json.loads(tool_call["function"]["arguments"]),
                            }
                        )

                    api_messages.append(
                        {"role": "assistant", "content": content_blocks}
                    )
                else:
                    api_messages.append({"role": msg.role, "content": msg.content})

            # For tool result messages
            elif msg.role == "tool":
                # Anthropic uses user role with tool_result content blocks
                api_messages.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": msg.tool_call_id,
                                "content": msg.content,
                            }
                        ],
                    }
                )

        # Build request payload
        payload = {
            "model": self.model,
            "messages": api_messages,
            "max_tokens": 4096,
        }

        # Add system message if present
        if system_message:
            payload["system"] = system_message

        # Add tools if provided (convert to Anthropic format)
        if tools:
            payload["tools"] = [
                self._convert_tool_to_anthropic_format(t) for t in tools
            ]

        # Make API request with retry logic
        if self.retry_config.enabled:
            # 应用重试逻辑
            retry_decorator = async_retry(
                config=self.retry_config, on_retry=self.retry_callback
            )
            api_call = retry_decorator(self._make_api_request)
            result = await api_call(payload)
        else:
            # 不使用重试
            result = await self._make_api_request(payload)

        # Parse Anthropic response format
        content_blocks = result.get("content", [])
        stop_reason = result.get("stop_reason", "stop")

        # Extract text content, thinking, and tool calls
        text_content = ""
        thinking_content = ""
        tool_calls = []

        for block in content_blocks:
            if block.get("type") == "text":
                text_content += block.get("text", "")
            elif block.get("type") == "thinking":
                thinking_content += block.get("thinking", "")
            elif block.get("type") == "tool_use":
                # Convert to OpenAI tool call format for compatibility
                tool_calls.append(
                    {
                        "id": block.get("id"),
                        "type": "function",
                        "function": {
                            "name": block.get("name"),
                            "arguments": json.dumps(block.get("input", {})),
                        },
                    }
                )

        return LLMResponse(
            content=text_content,
            thinking=thinking_content if thinking_content else None,
            tool_calls=tool_calls if tool_calls else None,
            finish_reason=stop_reason,
        )
