"""
Multi-Agent Orchestration Module - 多代理协调模块

该模块提供了 Mini-Agent 的多代理协调能力，支持层级式和协作式的
多代理协作架构。主要组件包括协调器、执行器、任务路由器和结果聚合器。

核心组件：
- MultiAgentOrchestrator：多代理协调器主类
- OptimizedExecutor：智能混合执行器
- TaskRouter：任务路由器
- ResultAggregator：结果聚合器
- Task：任务定义数据类

版本：0.6.0
"""

from .orchestrator import (
    MultiAgentOrchestrator,
    create_orchestrator,
)

from .executor import (
    OptimizedExecutor,
    create_executor,
    Task,
    UbuntuConfig,
)

from .task_router import (
    TaskRouter,
    create_task_router,
    TaskPriority,
    RouterConfig,
    RouteResult,
)

from .result_aggregator import (
    ResultAggregator,
    create_result_aggregator,
    ResultStatus,
    AggregatedResult,
)

from .prompts import (
    get_coordinator_prompt,
    COORDINATOR_SYSTEM_PROMPT,
    CODER_PROMPT,
    DESIGNER_PROMPT,
    RESEARCHER_PROMPT,
    TESTER_PROMPT,
    DEPLOYER_PROMPT,
    ANALYST_PROMPT,
    DOCUMENTER_PROMPT,
    get_agent_prompt,
    create_agent_config,
)


__version__ = "0.6.0"

__all__ = [
    # 协调器
    "MultiAgentOrchestrator",
    "create_orchestrator",
    
    # 执行器
    "OptimizedExecutor",
    "create_executor",
    "Task",
    "UbuntuConfig",
    
    # 路由器
    "TaskRouter",
    "create_task_router",
    "TaskPriority",
    "RouterConfig",
    "RouteResult",
    
    # 聚合器
    "ResultAggregator",
    "create_result_aggregator",
    "ResultStatus",
    "AggregatedResult",
    
    # 提示词
    "get_coordinator_prompt",
    "COORDINATOR_SYSTEM_PROMPT",
    "CODER_PROMPT",
    "DESIGNER_PROMPT",
    "RESEARCHER_PROMPT",
    "TESTER_PROMPT",
    "DEPLOYER_PROMPT",
    "ANALYST_PROMPT",
    "DOCUMENTER_PROMPT",
    "get_agent_prompt",
    "create_agent_config",
]
