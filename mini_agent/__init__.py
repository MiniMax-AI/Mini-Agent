"""Mini Agent - Minimal single agent with basic tools and MCP support."""

from .agent import Agent
from .llm import LLMClient
from .schema import FunctionCall, LLMProvider, LLMResponse, Message, ToolCall

# 多代理协调模块导出
from .orchestration import (
    MultiAgentOrchestrator,
    create_orchestrator,
    OptimizedExecutor,
    create_executor,
    TaskRouter,
    create_task_router,
    ResultAggregator,
    create_result_aggregator,
    Task,
)

__version__ = "0.6.0"

__all__ = [
    # 核心组件
    "Agent",
    "LLMClient",
    
    # 枚举和模式
    "LLMProvider",
    "Message",
    "LLMResponse",
    "ToolCall",
    "FunctionCall",
    
    # 多代理协调模块
    "MultiAgentOrchestrator",
    "create_orchestrator",
    "OptimizedExecutor",
    "create_executor",
    "TaskRouter",
    "create_task_router",
    "ResultAggregator",
    "create_result_aggregator",
    "Task",
]
