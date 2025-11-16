"""Ye Linghua (叶灵华) - AI助手，一个热爱编程的少女"""

from .agent import Agent
from .llm import LLMClient
from .schema import FunctionCall, LLMProvider, LLMResponse, Message, ToolCall

# YeLinghua is an alias for Agent - representing the programming-loving AI girl persona
YeLinghua = Agent

__version__ = "0.1.0"

__all__ = [
    "Agent",
    "YeLinghua",  # Alias for Agent
    "LLMClient",
    "LLMProvider",
    "Message",
    "LLMResponse",
    "ToolCall",
    "FunctionCall",
]
