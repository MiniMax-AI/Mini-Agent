import pytest

from mini_agent.llm.providers.openai_compat import OpenAILLM
from mini_agent.schema import Message, ToolCall, FunctionCall


def make_openai_llm():
    # Dummy credentials/base; will not be used for network in these tests
    return OpenAILLM(api_key="test", api_base="http://localhost:1234/v1", model="test-model", retry_config=None)


def test_tool_schema_conversion():
    llm = make_openai_llm()
    tools = [
        {
            "name": "calculator",
            "description": "calc",
            "input_schema": {
                "type": "object",
                "properties": {"a": {"type": "number"}},
            },
        }
    ]
    converted = llm._convert_tools(tools)
    assert converted and converted[0]["type"] == "function"
    assert converted[0]["function"]["name"] == "calculator"


def test_reasoning_from_reasoning_content():
    llm = make_openai_llm()
    result = {
        "choices": [
            {
                "finish_reason": "stop",
                "message": {
                    "content": "final answer",
                    "reasoning_content": "hidden thoughts",
                    "tool_calls": [],
                },
            }
        ]
    }
    resp = llm._parse_response(result)
    assert resp.content == "final answer"
    assert resp.thinking == "hidden thoughts"


def test_reasoning_from_think_tags():
    llm = make_openai_llm()
    result = {
        "choices": [
            {
                "finish_reason": "stop",
                "message": {"content": "<think>t1</think> visible", "tool_calls": []},
            }
        ]
    }
    resp = llm._parse_response(result)
    assert resp.content == "visible"
    assert resp.thinking == "t1"


def test_tool_calls_parse():
    llm = make_openai_llm()
    result = {
        "choices": [
            {
                "finish_reason": "tool_calls",
                "message": {
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "type": "function",
                            "function": {"name": "calc", "arguments": "{\"a\":1}"},
                        }
                    ],
                },
            }
        ]
    }
    resp = llm._parse_response(result)
    assert resp.tool_calls and resp.tool_calls[0].function.name == "calc"
    assert resp.tool_calls[0].function.arguments == {"a": 1}


def test_message_conversion_basic():
    llm = make_openai_llm()
    msgs = [
        Message(role="system", content="sys"),
        Message(role="user", content="u1"),
        Message(role="assistant", content="a1"),
    ]
    converted = llm._convert_messages(msgs)
    assert [m["role"] for m in converted] == ["system", "user", "assistant"]

