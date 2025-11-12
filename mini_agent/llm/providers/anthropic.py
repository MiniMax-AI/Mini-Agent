"""Anthropic-compatible (MiniMax M2) provider implementation."""

from __future__ import annotations

from typing import Any

import httpx

from ...retry import async_retry, RetryConfig as RetryConfigBase
from ...schema import FunctionCall, LLMResponse, Message, ToolCall
from .base import BaseLLM


class AnthropicLLM(BaseLLM):
    async def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
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
            return response.json()

    def _parse_response(self, result: dict[str, Any]) -> LLMResponse:
        # Check for errors (Anthropic format)
        if result.get("type") == "error":
            error_info = result.get("error", {})
            error_msg = f"API Error ({error_info.get('type')}): {error_info.get('message')}"
            raise Exception(error_msg)

        # Check for MiniMax base_resp errors
        if "base_resp" in result:
            base_resp = result["base_resp"]
            status_code = base_resp.get("status_code")
            status_msg = base_resp.get("status_msg")
            if status_code not in [0, 1000, None]:
                error_msg = f"MiniMax API Error (code {status_code}): {status_msg}"
                if status_code == 1008:
                    error_msg += "\n\n⚠️  Insufficient account balance, please recharge on MiniMax platform"
                elif status_code == 2013:
                    error_msg += f"\n\n⚠️  Model '{self.model}' is not supported"
                raise Exception(error_msg)

        content_blocks = result.get("content", [])
        stop_reason = result.get("stop_reason", "stop")

        text_content = ""
        thinking_content = ""
        tool_calls: list[ToolCall] = []
        for block in content_blocks:
            if block.get("type") == "text":
                text_content += block.get("text", "")
            elif block.get("type") == "thinking":
                thinking_content += block.get("thinking", "")
            elif block.get("type") == "tool_use":
                tool_calls.append(
                    ToolCall(
                        id=block.get("id"),
                        type="function",
                        function=FunctionCall(
                            name=block.get("name"),
                            arguments=block.get("input", {}),
                        ),
                    )
                )

        return LLMResponse(
            content=text_content,
            thinking=thinking_content if thinking_content else None,
            tool_calls=tool_calls if tool_calls else None,
            finish_reason=stop_reason,
        )

    async def generate(self, messages: list[Message], tools: list[dict[str, Any]] | None = None) -> LLMResponse:
        # Extract system message separately
        system_message = None
        api_messages: list[dict[str, Any]] = []
        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
                continue
            if msg.role in ["user", "assistant"]:
                if msg.role == "assistant" and (msg.thinking or msg.tool_calls):
                    content_blocks = []
                    if msg.thinking:
                        content_blocks.append({"type": "thinking", "thinking": msg.thinking})
                    if msg.content:
                        content_blocks.append({"type": "text", "text": msg.content})
                    if msg.tool_calls:
                        for tool_call in msg.tool_calls:
                            content_blocks.append(
                                {
                                    "type": "tool_use",
                                    "id": tool_call.id,
                                    "name": tool_call.function.name,
                                    "input": tool_call.function.arguments,
                                }
                            )
                    api_messages.append({"role": "assistant", "content": content_blocks})
                else:
                    api_messages.append({"role": msg.role, "content": msg.content})
            elif msg.role == "tool":
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

        payload = {
            "model": self.model,
            "messages": api_messages,
            "max_tokens": 16384,
        }
        if system_message:
            payload["system"] = system_message
        if tools:
            payload["tools"] = tools

        # Retry wrapper
        if self.retry_config and self.retry_config.enabled:
            retry_decorator = async_retry(config=self.retry_config, on_retry=self._retry_callback)
            api_call = retry_decorator(self._post)
            result = await api_call(payload)
        else:
            result = await self._post(payload)

        return self._parse_response(result)

