"""OpenAI-compatible provider (LM Studio, etc.)."""

from __future__ import annotations

import json
import re
from typing import Any

import httpx

from ...retry import async_retry, RetryConfig as RetryConfigBase
from ...schema import FunctionCall, LLMResponse, Message, ToolCall
from .base import BaseLLM


class OpenAILLM(BaseLLM):
    async def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )

            status = response.status_code
            try:
                result = response.json()
            except Exception:
                result = {"raw": response.text}

            if status >= 400:
                err = None
                if isinstance(result, dict):
                    if "error" in result:
                        err = result.get("error")
                        if isinstance(err, dict):
                            err = err.get("message") or err.get("type")
                    if not err and "message" in result:
                        err = result.get("message")
                if not err:
                    err = response.text
                raise Exception(f"OpenAI-compatible API Error {status}: {err}")

            return result

    def _convert_messages(self, messages: list[Message]) -> list[dict[str, Any]]:
        oa_messages: list[dict[str, Any]] = []
        for msg in messages:
            if msg.role == "system":
                oa_messages.append({"role": "system", "content": msg.content})
            elif msg.role == "user":
                oa_messages.append({"role": "user", "content": msg.content})
            elif msg.role == "assistant":
                entry: dict[str, Any] = {"role": "assistant"}
                entry["content"] = msg.content or ""
                if msg.tool_calls:
                    tool_calls = []
                    for tc in msg.tool_calls:
                        func_args = tc.function.arguments
                        if isinstance(func_args, str):
                            args_str = func_args
                        else:
                            args_str = json.dumps(func_args, ensure_ascii=False)
                        tool_calls.append(
                            {
                                "id": tc.id,
                                "type": tc.type,
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": args_str,
                                },
                            }
                        )
                    entry["tool_calls"] = tool_calls
                oa_messages.append(entry)
            elif msg.role == "tool":
                entry = {
                    "role": "tool",
                    "tool_call_id": msg.tool_call_id,
                    "content": msg.content,
                }
                if msg.name:
                    entry["name"] = msg.name
                oa_messages.append(entry)
        return oa_messages

    def _convert_tools(self, tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        converted: list[dict[str, Any]] = []
        for t in tools:
            name = t.get("name")
            desc = t.get("description")
            params = t.get("input_schema") or {}
            converted.append(
                {
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": desc,
                        "parameters": params,
                    },
                }
            )
        return converted

    def _parse_response(self, result: dict[str, Any]) -> LLMResponse:
        choices = result.get("choices", [])
        if not choices:
            raise Exception("OpenAI-compatible response missing 'choices'")

        choice = choices[0]
        msg = choice.get("message", {})
        finish_reason = choice.get("finish_reason", "stop")

        text_content = msg.get("content") or ""
        reasoning_content = msg.get("reasoning_content")

        tool_calls_raw = msg.get("tool_calls") or []
        tool_calls: list[ToolCall] = []
        for tc in tool_calls_raw:
            func = tc.get("function", {})
            args_raw = func.get("arguments")
            try:
                args_parsed = json.loads(args_raw) if isinstance(args_raw, str) else (args_raw or {})
            except Exception:
                args_parsed = {"_raw": args_raw}

            tool_calls.append(
                ToolCall(
                    id=tc.get("id"),
                    type=tc.get("type", "function"),
                    function=FunctionCall(
                        name=func.get("name"),
                        arguments=args_parsed,
                    ),
                )
            )

        extracted_thinking = None
        if not reasoning_content and text_content:
            pattern = r"<think>([\s\S]*?)</think>"
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                extracted_thinking = match.group(1).strip()
                text_content = re.sub(pattern, "", text_content, flags=re.IGNORECASE).strip()

        return LLMResponse(
            content=text_content,
            thinking=(reasoning_content or extracted_thinking),
            tool_calls=tool_calls if tool_calls else None,
            finish_reason=finish_reason,
        )

    async def generate(self, messages: list[Message], tools: list[dict[str, Any]] | None = None) -> LLMResponse:
        oa_messages = self._convert_messages(messages)
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": oa_messages,
            "max_tokens": 2048,
        }
        if tools:
            payload["tools"] = self._convert_tools(tools)
            payload["tool_choice"] = "auto"

        if self.retry_config and self.retry_config.enabled:
            retry_decorator = async_retry(config=self.retry_config, on_retry=self._retry_callback)
            api_call = retry_decorator(self._post)
            result = await api_call(payload)
        else:
            result = await self._post(payload)

        return self._parse_response(result)

