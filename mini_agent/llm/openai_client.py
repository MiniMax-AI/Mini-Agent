"""OpenAI LLM client implementation."""

import json
import logging
from typing import Any

from openai import AsyncOpenAI

from ..retry import RetryConfig, async_retry
from ..schema import FunctionCall, LLMResponse, Message, ToolCall
from .base import LLMClientBase

logger = logging.getLogger(__name__)


class OpenAIClient(LLMClientBase):
    """LLM client using OpenAI's protocol.

    This client uses the official OpenAI SDK and supports:
    - Reasoning content (via reasoning_split=True)
    - Tool calling
    - Retry logic
    """

    def __init__(
        self,
        api_key: str,
        api_base: str = "https://api.minimaxi.com/v1",
        model: str = "MiniMax-M2",
        retry_config: RetryConfig | None = None,
        enable_reasoning_split: bool = True,
    ):
        """Initialize OpenAI client.

        Args:
            api_key: API key for authentication
            api_base: Base URL for the API (default: MiniMax OpenAI endpoint)
            model: Model name to use (default: MiniMax-M2)
            retry_config: Optional retry configuration
            enable_reasoning_split: Enable reasoning_split parameter (default: True for MiniMax)
        """
        super().__init__(api_key, api_base, model, retry_config)

        # Initialize OpenAI client
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=api_base,
        )

        # Store whether to use reasoning_split
        self.enable_reasoning_split = enable_reasoning_split

        # Auto-detect reasoning format based on model name
        # GLM uses "reasoning_content" (string), MiniMax uses "reasoning_details" (list)
        self.reasoning_format = "none"
        if model.lower().startswith("glm"):
            self.reasoning_format = "glm"  # GLM format: reasoning_content
            logger.info("Using GLM reasoning format (reasoning_content)")
        elif model.startswith("MiniMax"):
            self.reasoning_format = "minimax"  # MiniMax format: reasoning_details
            logger.info("Using MiniMax reasoning format (reasoning_details)")

    async def _make_api_request(
        self,
        api_messages: list[dict[str, Any]],
        tools: list[Any] | None = None,
    ) -> Any:
        """Execute API request (core method that can be retried).

        Args:
            api_messages: List of messages in OpenAI format
            tools: Optional list of tools

        Returns:
            OpenAI ChatCompletion message

        Raises:
            Exception: API call failed
        """
        params = {
            "model": self.model,
            "messages": api_messages,
        }

        # Only add reasoning_split if enabled (MiniMax-specific feature)
        if self.enable_reasoning_split:
            params["extra_body"] = {"reasoning_split": True}

        if tools:
            params["tools"] = self._convert_tools(tools)

        # Use OpenAI SDK's chat.completions.create
        response = await self.client.chat.completions.create(**params)

        # Add null checks and better error handling
        if response is None:
            logger.error("API returned None response")
            raise ValueError("API returned None response")

        if not hasattr(response, 'choices') or response.choices is None:
            logger.error(f"API response missing choices field. Response: {response}")
            raise ValueError(f"API response missing choices field. Response type: {type(response)}")

        if len(response.choices) == 0:
            logger.error(f"API response has empty choices array. Response: {response}")
            raise ValueError("API response has empty choices array")

        return response.choices[0].message

    def _convert_tools(self, tools: list[Any]) -> list[dict[str, Any]]:
        """Convert tools to OpenAI format.

        Args:
            tools: List of Tool objects or dicts

        Returns:
            List of tools in OpenAI dict format
        """
        result = []
        for tool in tools:
            if isinstance(tool, dict):
                # If already a dict, check if it's in OpenAI format
                if "type" in tool and tool["type"] == "function":
                    result.append(tool)
                else:
                    # Assume it's in Anthropic format, convert to OpenAI
                    result.append(
                        {
                            "type": "function",
                            "function": {
                                "name": tool["name"],
                                "description": tool["description"],
                                "parameters": tool["input_schema"],
                            },
                        }
                    )
            elif hasattr(tool, "to_openai_schema"):
                # Tool object with to_openai_schema method
                result.append(tool.to_openai_schema())
            else:
                raise TypeError(f"Unsupported tool type: {type(tool)}")
        return result

    def _convert_messages(self, messages: list[Message]) -> tuple[str | None, list[dict[str, Any]]]:
        """Convert internal messages to OpenAI format.

        Args:
            messages: List of internal Message objects

        Returns:
            Tuple of (system_message, api_messages)
            Note: OpenAI includes system message in the messages array
        """
        api_messages = []

        for msg in messages:
            if msg.role == "system":
                # OpenAI includes system message in messages array
                api_messages.append({"role": "system", "content": msg.content})
                continue

            # For user messages
            if msg.role == "user":
                api_messages.append({"role": "user", "content": msg.content})

            # For assistant messages
            elif msg.role == "assistant":
                assistant_msg = {"role": "assistant"}

                # Add content if present
                if msg.content:
                    assistant_msg["content"] = msg.content

                # Add tool calls if present
                if msg.tool_calls:
                    tool_calls_list = []
                    for tool_call in msg.tool_calls:
                        tool_calls_list.append(
                            {
                                "id": tool_call.id,
                                "type": "function",
                                "function": {
                                    "name": tool_call.function.name,
                                    "arguments": json.dumps(tool_call.function.arguments),
                                },
                            }
                        )
                    assistant_msg["tool_calls"] = tool_calls_list

                # IMPORTANT: Add reasoning content if thinking is present
                # This is CRITICAL for Interleaved Thinking to work properly!
                # The complete response_message (including reasoning content) must be
                # preserved in Message History and passed back to the model in the next turn.
                # This ensures the model's chain of thought is not interrupted.
                if msg.thinking:
                    if self.reasoning_format == "glm":
                        # GLM format: reasoning_content (string)
                        assistant_msg["reasoning_content"] = msg.thinking
                    elif self.reasoning_format == "minimax":
                        # MiniMax format: reasoning_details (list)
                        assistant_msg["reasoning_details"] = [{"text": msg.thinking}]

                api_messages.append(assistant_msg)

            # For tool result messages
            elif msg.role == "tool":
                api_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": msg.tool_call_id,
                        "content": msg.content,
                    }
                )

        return None, api_messages

    def _prepare_request(
        self,
        messages: list[Message],
        tools: list[Any] | None = None,
    ) -> dict[str, Any]:
        """Prepare the request for OpenAI API.

        Args:
            messages: List of conversation messages
            tools: Optional list of available tools

        Returns:
            Dictionary containing request parameters
        """
        _, api_messages = self._convert_messages(messages)

        return {
            "api_messages": api_messages,
            "tools": tools,
        }

    def _parse_response(self, response: Any) -> LLMResponse:
        """Parse OpenAI response into LLMResponse.

        Args:
            response: OpenAI ChatCompletionMessage response

        Returns:
            LLMResponse object
        """
        # Extract text content
        text_content = response.content or ""

        # Extract thinking content - support both MiniMax and GLM formats
        thinking_content = ""

        # Method 1: GLM format - reasoning_content (string)
        if hasattr(response, "reasoning_content") and response.reasoning_content:
            thinking_content = response.reasoning_content
            logger.debug("Extracted reasoning from reasoning_content (GLM format)")

        # Method 2: MiniMax format - reasoning_details (list)
        elif hasattr(response, "reasoning_details") and response.reasoning_details:
            for detail in response.reasoning_details:
                if hasattr(detail, "text"):
                    thinking_content += detail.text
            logger.debug("Extracted reasoning from reasoning_details (MiniMax format)")

        # Extract tool calls
        tool_calls = []
        if response.tool_calls:
            for tool_call in response.tool_calls:
                # Parse arguments from JSON string
                arguments = json.loads(tool_call.function.arguments)

                tool_calls.append(
                    ToolCall(
                        id=tool_call.id,
                        type="function",
                        function=FunctionCall(
                            name=tool_call.function.name,
                            arguments=arguments,
                        ),
                    )
                )

        return LLMResponse(
            content=text_content,
            thinking=thinking_content if thinking_content else None,
            tool_calls=tool_calls if tool_calls else None,
            finish_reason="stop",  # OpenAI doesn't provide finish_reason in the message
        )

    async def generate(
        self,
        messages: list[Message],
        tools: list[Any] | None = None,
    ) -> LLMResponse:
        """Generate response from OpenAI LLM.

        Args:
            messages: List of conversation messages
            tools: Optional list of available tools

        Returns:
            LLMResponse containing the generated content
        """
        # Prepare request
        request_params = self._prepare_request(messages, tools)

        # Make API request with retry logic
        if self.retry_config.enabled:
            # Apply retry logic
            retry_decorator = async_retry(config=self.retry_config, on_retry=self.retry_callback)
            api_call = retry_decorator(self._make_api_request)
            response = await api_call(
                request_params["api_messages"],
                request_params["tools"],
            )
        else:
            # Don't use retry
            response = await self._make_api_request(
                request_params["api_messages"],
                request_params["tools"],
            )

        # Parse and return response
        return self._parse_response(response)
