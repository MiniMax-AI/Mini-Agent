# Mini-Agent 项目提升改进完整方案

## 一、项目背景与现状分析

### 1.1 当前项目架构概述

Mini-Agent 是一个功能完备的 Python 代理框架，经过前期的项目结构分析，我们对其有了全面的了解。该项目采用模块化设计，核心组件包括 Agent 类、LLM 客户端、多样化的工具系统以及 Skills 生态系统。从技术架构来看，项目支持异步执行模式，具备消息历史管理、Token 自动摘要、完善的取消机制以及丰富的日志记录功能。然而，当前实现本质上是一个单代理系统，这在处理复杂多任务场景时存在一定的局限性。

当前架构的主要优势体现在以下几个方面：首先是模块化程度高，各组件职责清晰，便于维护和扩展；其次是异步设计完善，能够高效处理 I/O 密集型任务；第三是工具系统灵活，支持动态加载和自定义扩展。然而，随着项目应用场景的复杂化，单代理架构逐渐暴露出一些固有缺陷，这些问题在处理大规模、多领域协作任务时尤为突出。

### 1.2 单代理架构的局限性分析

通过对现有架构的深入分析，我们识别出单代理系统存在的四个核心局限性。

**工具爆炸问题**是首要挑战。随着功能需求的增加，单一代理需要不断加载更多工具，这导致系统提示词急剧膨胀，Token 消耗大幅上升，同时工具之间可能产生相互干扰或冲突。例如，当一个代理同时具备代码编写、图像生成、文档处理、测试验证等多维度能力时，每次 API 调用都需要传递完整的工具描述，这不仅增加了上下文长度，还可能影响模型的选择准确性。

**专业能力折中**是第二个关键问题。一个代理难以在所有领域都达到专家水平，为了保持通用性往往需要牺牲深度专业能力。比如，一个兼顾 Web 开发、数据分析和 UI 设计的代理，在每个领域的专业深度都可能不如专门针对该领域优化的代理。这种设计虽然灵活，但在处理高难度专业任务时可能力不从心。

**执行效率问题**体现在复杂任务需要长序列的思考-行动循环。错误会在长链条中累积放大，导致最终结果的质量难以保证。同时，单代理串行处理任务的模式无法充分利用现代多核 CPU 的并行计算能力，造成资源浪费。

**可扩展性差**是第四个问题。新功能只能通过添加工具实现，这种线性扩展模式在面对高度异构的任务需求时显得力不从心。当需要支持全新的任务类型时，可能需要重新设计整个工具系统，而非简单地添加新组件。

### 1.3 改进目标与预期价值

基于上述分析，本改进方案的核心目标是将 Mini-Agent 从单代理架构升级为多代理协调架构，使系统具备层级式和协作式的多代理协作能力。通过引入主代理（大脑）协调多个专业子代理的机制，实现任务的智能分解、并行执行和结果整合。

预期实现的价值包括：**专业化分工**使每个子代理专注于特定领域，工具和提示词可以高度优化，避免能力折中；**可扩展性提升**使系统能够轻松添加新的专业代理，模块化设计易于维护，支持动态扩展；**执行效率提高**通过并行执行独立任务，优化 Token 使用，减少长链条推理的错误；**可靠性增强**实现错误隔离，单个代理失败不影响全局，支持重试和恢复；**灵活性增强**支持多种协作模式，动态任务分配，适应不同复杂度的任务。

---

## 二、技术架构设计

### 2.1 总体架构设计

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         多代理协调系统架构                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│                         ┌─────────────────────┐                         │
│                         │     主代理（大脑）    │                         │
│                         │                     │                         │
│                         │  • 全局规划与分解    │                         │
│                         │  • 子代理协调调度    │                         │
│                         │  • 结果质量控制      │                         │
│                         │  • 资源分配优化      │                         │
│                         └──────────┬──────────┘                         │
│                                    │                                     │
│              ┌─────────────────────┼─────────────────────┐              │
│              │                     │                     │              │
│              ▼                     ▼                     ▼              │
│    ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐    │
│    │   专业子代理 1   │   │   专业子代理 2   │   │   专业子代理 3   │    │
│    │   (代码专家)    │   │   (设计专家)    │   │   (测试专家)    │    │
│    │                 │   │                 │   │                 │    │
│    │  • 代码编写     │   │  • 视觉设计     │   │  • 自动化测试   │    │
│    │  • 代码审查     │   │  • 文档生成     │   │  • 质量验证     │    │
│    │  • 调试分析     │   │  • 演示制作     │   │  • 部署验证     │    │
│    └─────────────────┘   └─────────────────┘   └─────────────────┘    │
│                                                                         │
│                         ┌─────────────────────┐                         │
│                         │   共享资源层         │                         │
│                         │                     │                         │
│                         │  • 执行结果缓存      │                         │
│                         │  • 上下文共享机制    │                         │
│                         │  • 消息通信总线      │                         │
│                         │  • 状态同步服务      │                         │
│                         └─────────────────────┘                         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 执行模式设计

基于 Ubuntu 系统的技术特性和开发场景的任务特征，本方案采用**智能混合执行框架**，根据任务性质动态选择最优执行模式。

**异步并行模式**作为首选模式，适用于 60-70% 的开发任务，包括 LLM API 调用、文件 I/O 操作、网络请求等 I/O 密集型任务。在 Ubuntu 系统上，asyncio 结合 epoll 事件循环机制可以高效处理大量并发 I/O 操作，内存占用低，上下文切换快，能够支持数百甚至上千个并发任务。

**线程池模式**适用于 CPU 密集型但不适合多进程的场景，如中等规模的数据处理、格式转换等操作。通过 ThreadPoolExecutor 实现，可以利用多核 CPU 的并行能力，同时避免多进程间通信的高开销。

**顺序执行模式**适用于有严格依赖关系的任务链、需要保持上下文连贯性的场景，以及任务数量较少（少于 3 个）的情况。顺序模式简单可靠，错误处理和恢复机制容易实现。

### 2.3 核心组件设计

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          核心组件关系图                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    MultiAgentOrchestrator                        │   │
│  │  • 协调器入口类                                                   │   │
│  │  • 管理所有子代理                                                 │   │
│  │  • 提供统一执行接口                                               │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                    │                                     │
│                    ┌───────────────┼───────────────┐                    │
│                    │               │               │                    │
│                    ▼               ▼               ▼                    │
│           ┌────────────┐   ┌────────────┐   ┌────────────┐             │
│           │ TaskRouter │   │ Executor   │   │ Result     │             │
│           │            │   │ Manager    │   │ Aggregator │             │
│           │ • 任务分析  │   │ • 模式选择  │   │ • 结果收集  │             │
│           │ • 类型识别  │   │ • 并发控制  │   │ • 质量验证  │             │
│           │ • 路由分发  │   │ • 资源管理  │   │ • 格式整合  │             │
│           └────────────┘   └────────────┘   └────────────┘             │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                       Tool Registry                              │   │
│  │                                                                  │   │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐     │   │
│  │  │ Orchestration  │  │ Coordination   │  │ Communication  │     │   │
│  │  │    Tools       │  │    Tools       │  │    Tools       │     │   │
│  │  │                │  │                │  │                │     │   │
│  │  │ • delegate     │  │ • status       │  │ • share        │     │   │
│  │  │ • batch        │  │ • gather       │  │ • sync         │     │   │
│  │  │ • parallel     │  │ • monitor      │  │ • broadcast    │     │   │
│  │  └────────────────┘  └────────────────┘  └────────────────┘     │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 三、详细实现方案

### 3.1 目录结构规划

```
mini_agent/
├── __init__.py                          # 导出新增组件
├── agent.py                             # 现有核心（保持不变）
├── cli.py                               # 添加多代理 CLI 命令
│
├── orchestration/                       # ⭐ 新增：多代理协调模块
│   ├── __init__.py                      # 模块导出
│   ├── orchestrator.py                  # 协调器主类
│   ├── executor.py                      # 执行器核心（智能混合执行）
│   ├── task_router.py                   # 任务路由器
│   └── result_aggregator.py             # 结果聚合器
│
├── prompts/                             # ⭐ 新增：提示词模板
│   ├── __init__.py                      # 模块导出
│   ├── coordinator_prompts.py           # 协调器提示词
│   └── agent_prompts.py                 # 专业代理提示词模板
│
├── tools/                               # 现有工具目录
│   ├── __init__.py                      # 添加导出
│   ├── base.py                          # 现有（保持不变）
│   ├── orchestration.py                 # ⭐ 新增：协调工具
│   │   ├── DelegateToAgentTool          # 任务委托工具
│   │   ├── BatchDelegateTool            # 批量委托工具
│   │   ├── RequestStatusTool            # 状态查询工具
│   │   └── GatherResultsTool            # 结果收集工具
│   │
│   ├── communication.py                 # ⭐ 新增：通信工具
│   │   ├── ShareContextTool             # 上下文共享工具
│   │   ├── BroadcastMessageTool         # 消息广播工具
│   │   └── SyncStateTool                # 状态同步工具
│   │
│   ├── bash.py                          # 现有（保持不变）
│   ├── file_tools.py                    # 现有（保持不变）
│   └── mcp_loader.py                    # 现有（保持不变）
│
├── llm/                                 # 现有（保持不变）
├── skills/                              # 现有（保持不变）
├── acp/                                 # 现有（保持不变）
├── config/                              # 现有（保持不变）
│
├── examples/                            # 示例目录
│   ├── multi_agent_demo.py              # ⭐ 新增：基础演示
│   ├── complex_task_example.py          # ⭐ 新增：复杂任务示例
│   └── parallel_execution_demo.py       # ⭐ 新增：并行执行示例
│
├── tests/                               # 测试目录
│   ├── test_orchestration/              # ⭐ 新增：协调模块测试
│   │   ├── test_orchestrator.py         # 协调器测试
│   │   ├── test_executor.py             # 执行器测试
│   │   ├── test_coordination_tools.py   # 协调工具测试
│   │   └── test_communication.py        # 通信工具测试
│   │
│   ├── test_agent.py                    # 现有（保持不变）
│   ├── test_tools.py                    # 现有（保持不变）
│   └── ...
│
└── docs/                                # 文档目录
    ├── PROJECT_IMPROVEMENT_PLAN.md       # 本方案文档
    ├── ARCHITECTURE.md                   # 架构设计文档
    ├── API_REFERENCE.md                  # API 参考文档
    └── EXAMPLES.md                       # 使用示例文档
```

### 3.2 核心代码实现

#### 3.2.1 协调器主类

```python
# 文件：mini_agent/orchestration/orchestrator.py

"""
Multi-Agent Orchestrator - 多代理协调器

允许一个 Agent 作为"大脑"协调多个专业子代理完成任务。
"""

from typing import Optional, Dict, List, Any
from pathlib import Path
import asyncio

from ..agent import Agent
from ..llm import LLMClient
from .executor import OptimizedExecutor, Task
from .task_router import TaskRouter
from .result_aggregator import ResultAggregator
from .prompts import get_coordinator_prompt


class MultiAgentOrchestrator:
    """多代理协调器 - 主代理的增强版本"""
    
    def __init__(
        self,
        main_llm_client: LLMClient,
        sub_agent_configs: List[Dict[str, Any]],
        workspace_dir: str = "./workspace",
        max_steps: int = 50,
        default_timeout: int = 300,
    ):
        """
        Args:
            main_llm_client: 主代理使用的 LLM 客户端
            sub_agent_configs: 子代理配置列表
                [{
                    "name": "coder",
                    "system_prompt": "...",
                    "tools": [...],
                    "workspace": "./workspace/coder",
                    "max_steps": 30,
                }]
            workspace_dir: 主工作目录
            max_steps: 主代理最大步数
            default_timeout: 默认任务超时时间（秒）
        """
        self.main_llm_client = main_llm_client
        self.sub_agent_configs = sub_agent_configs
        self.default_timeout = default_timeout
        
        # 创建子代理
        self.sub_agents: Dict[str, Agent] = {}
        self._create_sub_agents(workspace_dir)
        
        # 初始化执行器
        self.executor = OptimizedExecutor(self.sub_agents)
        
        # 初始化任务路由器
        self.task_router = TaskRouter(self.sub_agents)
        
        # 初始化结果聚合器
        self.result_aggregator = ResultAggregator()
        
        # 创建主代理
        self.main_agent = self._create_main_agent(workspace_dir, max_steps)
        
        # 共享上下文
        self.shared_context: Dict[str, Any] = {}
        
        # 任务历史
        self.task_history: List[Dict] = []
    
    def _create_sub_agents(self, base_workspace: str):
        """创建所有子代理"""
        for config in self.sub_agent_configs:
            name = config["name"]
            workspace = Path(base_workspace) / name
            workspace.mkdir(parents=True, exist_ok=True)
            
            agent = Agent(
                llm_client=self.main_llm_client,  # 共享 LLM 客户端
                system_prompt=config["system_prompt"],
                tools=config.get("tools", []),
                max_steps=config.get("max_steps", 30),
                workspace_dir=str(workspace),
            )
            
            self.sub_agents[name] = agent
    
    def _create_main_agent(self, workspace_dir: str, max_steps: int) -> Agent:
        """创建主代理（协调器）"""
        workspace = Path(workspace_dir) / "coordinator"
        workspace.mkdir(parents=True, exist_ok=True)
        
        # 生成协调器提示词
        coordinator_prompt = get_coordinator_prompt(
            agent_names=list(self.sub_agents.keys()),
            agent_descriptions=self._generate_agent_descriptions(),
        )
        
        # 初始化工工具列表（稍后添加协调工具）
        coordination_tools = self._create_coordination_tools()
        
        agent = Agent(
            llm_client=self.main_llm_client,
            system_prompt=coordinator_prompt,
            tools=coordination_tools,
            max_steps=max_steps,
            workspace_dir=str(workspace),
        )
        
        return agent
    
    def _generate_agent_descriptions(self) -> str:
        """生成子代理描述"""
        descriptions = []
        for name, agent in self.sub_agents.items():
            # 从系统提示中提取简短描述
            prompt = agent.system_prompt
            # 取第一行作为描述
            lines = prompt.strip().split("\n")
            description = lines[0][:100] if lines else name
            descriptions.append(f"- **{name}**: {description}")
        return "\n".join(descriptions)
    
    def _create_coordination_tools(self) -> List:
        """创建协调工具"""
        from ..tools.orchestration import (
            DelegateToAgentTool,
            BatchDelegateTool,
            RequestStatusTool,
            GatherResultsTool,
        )
        from ..tools.communication import (
            ShareContextTool,
            BroadcastMessageTool,
        )
        
        return [
            DelegateToAgentTool(agents=self.sub_agents),
            BatchDelegateTool(orchestrator=self),
            RequestStatusTool(agents=self.sub_agents),
            GatherResultsTool(agents=self.sub_agents),
            ShareContextTool(orchestrator=self),
            BroadcastMessageTool(agents=self.sub_agents),
        ]
    
    def add_sub_agent(self, name: str, config: Dict[str, Any]):
        """动态添加子代理"""
        workspace = Path(config.get("workspace", f"./workspace/{name}"))
        workspace.mkdir(parents=True, exist_ok=True)
        
        agent = Agent(
            llm_client=self.main_llm_client,
            system_prompt=config["system_prompt"],
            tools=config.get("tools", []),
            max_steps=config.get("max_steps", 30),
            workspace_dir=str(workspace),
        )
        
        self.sub_agents[name] = agent
        self.executor = OptimizedExecutor(self.sub_agents)  # 重新初始化执行器
    
    def remove_sub_agent(self, name: str):
        """移除子代理"""
        if name in self.sub_agents:
            del self.sub_agents[name]
            self.executor = OptimizedExecutor(self.sub_agents)
    
    async def execute_task(
        self,
        task: str,
        context: Dict[str, Any] = None,
        mode: str = "auto"
    ) -> Dict[str, Any]:
        """执行单个复杂任务
        
        Args:
            task: 任务描述
            context: 可选上下文
            mode: 执行模式（auto/parallel/sequential/thread）
        
        Returns:
            执行结果
        """
        # 更新共享上下文
        if context:
            self.shared_context.update(context)
        
        # 添加到主代理
        if context:
            context_msg = self._format_context(context)
            self.main_agent.add_user_message(context_msg)
        
        self.main_agent.add_user_message(task)
        
        # 执行主代理循环
        result = await self.main_agent.run()
        
        return {
            "success": True,
            "result": result,
            "task_history": self.task_history,
        }
    
    async def execute_parallel_tasks(
        self,
        tasks: List[Dict[str, Any]],
        mode: str = "auto"
    ) -> Dict[str, Any]:
        """并行执行多个独立任务
        
        Args:
            tasks: 任务列表
                [{
                    "agent": "coder",
                    "task": "...",
                    "context": {...},
                    "priority": 1,
                }]
            mode: 执行模式
        
        Returns:
            聚合结果
        """
        # 转换为 Task 对象
        task_objects = [
            Task(
                agent_name=task["agent"],
                task=task["task"],
                context=task.get("context"),
                priority=task.get("priority", 0),
            )
            for task in tasks
        ]
        
        # 执行
        execution_result = await self.executor.execute(task_objects, mode)
        
        # 聚合结果
        aggregated = self.result_aggregator.aggregate(execution_result)
        
        # 更新任务历史
        self.task_history.extend(tasks)
        
        return aggregated
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """格式化上下文信息"""
        lines = ["[Shared Context]"]
        for key, value in context.items():
            lines.append(f"- {key}: {value}")
        return "\n".join(lines)
    
    def get_status(self) -> Dict[str, Any]:
        """获取协调器状态"""
        return {
            "sub_agent_count": len(self.sub_agents),
            "sub_agent_names": list(self.sub_agents.keys()),
            "task_history_count": len(self.task_history),
            "shared_context_keys": list(self.shared_context.keys()),
        }


# 便捷创建函数
def create_orchestrator(
    main_llm_client: LLMClient,
    sub_agent_configs: List[Dict[str, Any]],
    workspace_dir: str = "./workspace",
    max_steps: int = 50,
) -> MultiAgentOrchestrator:
    """创建多代理协调系统的便捷函数"""
    return MultiAgentOrchestrator(
        main_llm_client=main_llm_client,
        sub_agent_configs=sub_agent_configs,
        workspace_dir=workspace_dir,
        max_steps=max_steps,
    )
```

#### 3.2.2 智能混合执行器

```python
# 文件：mini_agent/orchestration/executor.py

"""
Optimized Executor - Ubuntu 优化的智能混合执行器

根据任务性质自动选择最优执行模式。
"""

import asyncio
import os
from typing import List, Dict, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import re

from ..agent import Agent
from ..tools.base import ToolResult


# Ubuntu 系统优化配置
class UbuntuConfig:
    """Ubuntu 系统优化配置"""
    
    CPU_COUNT = os.cpu_count() or 4
    
    # Async 并发数
    MAX_ASYNC_CONCURRENT = min(200, 32 * CPU_COUNT)
    
    # 线程池大小
    THREAD_POOL_SIZE = CPU_COUNT * 2
    
    # 进程池大小
    PROCESS_POOL_SIZE = max(1, CPU_COUNT - 1)
    
    # 内存限制
    import psutil
    MEMORY_TOTAL = psutil.virtual_memory().total / (1024**3)
    MEMORY_LIMIT = int(MEMORY_TOTAL * 0.5)


@dataclass
class Task:
    """任务定义"""
    agent_name: str
    task: str
    context: Dict[str, Any] = None
    timeout: int = 300
    priority: int = 0
    task_type: str = "io_bound"  # io_bound / cpu_bound


class OptimizedExecutor:
    """Ubuntu 优化的多代理执行器"""
    
    def __init__(self, agents: Dict[str, Agent]):
        self.agents = agents
        self.config = UbuntuConfig()
        self.semaphore = asyncio.Semaphore(self.config.MAX_ASYNC_CONCURRENT)
        self.thread_pool = ThreadPoolExecutor(
            max_workers=self.config.THREAD_POOL_SIZE,
            thread_name_prefix="AgentWorker"
        )
        
        # CPU 密集型任务关键词
        self.cpu_keywords = [
            "计算", "分析", "处理", "转换", "统计", "批量",
            "calculate", "analyze", "process", "transform", "stat",
            "batch", "generate", "render", "compile"
        ]
    
    def analyze_task_type(self, task: Task) -> str:
        """分析任务类型（I/O 密集型 vs CPU 密集型）"""
        task_text = task.task.lower()
        
        # 检查是否包含 CPU 密集型关键词
        if any(keyword.lower() in task_text for keyword in self.cpu_keywords):
            return "cpu_bound"
        
        return "io_bound"
    
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """执行单个任务（带并发控制）"""
        async with self.semaphore:
            agent = self.agents.get(task.agent_name)
            
            if not agent:
                return {
                    "agent": task.agent_name,
                    "success": False,
                    "error": f"Unknown agent: {task.agent_name}",
                    "task_type": "unknown",
                }
            
            # 自动分析任务类型
            task.task_type = self.analyze_task_type(task)
            
            # 添加上下文
            if task.context:
                context_str = self._format_context(task.context)
                agent.add_user_message(context_str)
            
            # 添加任务
            agent.add_user_message(task.task)
            
            try:
                result = await asyncio.wait_for(
                    agent.run(),
                    timeout=task.timeout,
                )
                
                return {
                    "agent": task.agent_name,
                    "success": True,
                    "result": result,
                    "task_type": task.task_type,
                }
                
            except asyncio.TimeoutError:
                return {
                    "agent": task.agent_name,
                    "success": False,
                    "error": f"Task timed out after {task.timeout}s",
                    "task_type": task.task_type,
                }
            except Exception as e:
                return {
                    "agent": task.agent_name,
                    "success": False,
                    "error": str(e),
                    "task_type": task.task_type,
                }
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """格式化上下文信息"""
        lines = ["[Context]"]
        for key, value in context.items():
            lines.append(f"- {key}: {value}")
        return "\n".join(lines)
    
    async def execute_parallel(self, tasks: List[Task]) -> List[Dict[str, Any]]:
        """并行执行任务列表"""
        # 按优先级排序
        sorted_tasks = sorted(tasks, key=lambda t: -t.priority)
        
        # 并发执行
        coroutines = [self.execute_task(task) for task in sorted_tasks]
        results = await asyncio.gather(*coroutines, return_exceptions=True)
        
        # 处理异常
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append({
                    "success": False,
                    "error": str(result),
                    "task_type": "unknown",
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    def execute_sequential(self, tasks: List[Task]) -> List[Dict[str, Any]]:
        """顺序执行任务列表（使用线程池）"""
        results = []
        for task in tasks:
            future = self.thread_pool.submit(
                asyncio.run,
                self.execute_task(task)
            )
            results.append(future.result())
        
        return results
    
    async def execute(
        self,
        tasks: List[Task],
        mode: str = "auto"
    ) -> Dict[str, Any]:
        """智能执行任务
        
        Args:
            tasks: 任务列表
            mode: 执行模式
                - "auto": 自动选择（推荐）
                - "parallel": 强制并行
                - "sequential": 强制顺序
                - "thread": 使用线程池
        """
        # 分析任务类型
        task_types = [self.analyze_task_type(t) for t in tasks]
        cpu_bound_count = task_types.count("cpu_bound")
        total_count = len(tasks)
        
        # 智能选择模式
        if mode == "auto":
            if cpu_bound_count / total_count > 0.5:
                mode = "thread"
            elif len(tasks) <= 2:
                mode = "sequential"
            else:
                mode = "parallel"
        
        # 执行
        if mode == "parallel":
            results = await self.execute_parallel(tasks)
        elif mode == "thread":
            results = self.execute_sequential(tasks)
        else:
            results = await self.execute_parallel(tasks)
        
        # 生成摘要
        success_count = sum(1 for r in results if r.get("success"))
        
        return {
            "mode": mode,
            "total": len(tasks),
            "success": success_count,
            "failed": len(tasks) - success_count,
            "results": results,
            "task_breakdown": {
                "cpu_bound": cpu_bound_count,
                "io_bound": total_count - cpu_bound_count,
            },
            "cpu_utilization": self._estimate_cpu_usage(results),
        }
    
    def _estimate_cpu_usage(self, results: List[Dict]) -> str:
        """估算 CPU 使用情况"""
        cpu_tasks = sum(1 for r in results if r.get("task_type") == "cpu_bound")
        if cpu_tasks == 0:
            return "low"
        elif cpu_tasks < len(results) / 2:
            return "medium"
        else:
            return "high"
    
    def shutdown(self):
        """关闭执行器"""
        self.thread_pool.shutdown(wait=True)


def create_executor(agents: Dict[str, Agent]) -> OptimizedExecutor:
    """创建优化的执行器"""
    return OptimizedExecutor(agents)
```

#### 3.2.3 协调工具实现

```python
# 文件：mini_agent/tools/orchestration.py

"""
Orchestration Tools - 协调工具集

提供主代理协调子代理执行所需的工具。
"""

from typing import Optional, Dict, Any, List
import asyncio

from .base import Tool, ToolResult


class DelegateToAgentTool(Tool):
    """将任务委托给指定子代理的工具"""
    
    name = "delegate_to_agent"
    description = """将任务委托给指定的子代理执行。

使用场景：
- 需要特定领域的专业知识时
- 任务可以分解为独立子任务时
- 需要并行处理多个任务时（结合 batch_delegate）

参数：
- agent_name: 子代理名称（必须在可用代理列表中）
- task: 要执行的具体任务描述
- context: 可选的上下文信息
- timeout: 可选的超时时间（秒），默认 300 秒"""
    
    def __init__(self, agents: Dict[str, "Agent"]):
        self.agents = agents
    
    @property
    def parameters(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "agent_name": {
                    "type": "string",
                    "description": f"子代理名称，可用选项: {list(self.agents.keys())}",
                },
                "task": {
                    "type": "string",
                    "description": "要执行的具体任务描述",
                },
                "context": {
                    "type": "object",
                    "description": "可选的上下文信息",
                },
                "timeout": {
                    "type": "integer",
                    "description": "超时时间（秒）",
                },
            },
            "required": ["agent_name", "task"],
        }
    
    async def execute(
        self,
        agent_name: str,
        task: str,
        context: Optional[Dict] = None,
        timeout: Optional[int] = None,
    ) -> ToolResult:
        """执行任务委托"""
        if agent_name not in self.agents:
            return ToolResult(
                success=False,
                content="",
                error=f"Unknown agent: {agent_name}. Available: {list(self.agents.keys())}",
            )
        
        agent = self.agents[agent_name]
        
        # 添加上下文
        if context:
            context_msg = self._format_context(context)
            agent.add_user_message(context_msg)
        
        # 添加任务
        agent.add_user_message(task)
        
        # 执行任务
        try:
            if timeout:
                result = await asyncio.wait_for(
                    agent.run(),
                    timeout=timeout,
                )
            else:
                result = await agent.run()
        except asyncio.TimeoutError:
            return ToolResult(
                success=False,
                content="",
                error=f"Task timed out after {timeout or 300}s",
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=f"Agent execution failed: {str(e)}",
            )
        
        # 提取结果摘要
        history = agent.get_history()
        result_preview = self._extract_result_preview(history)
        
        return ToolResult(
            success=True,
            content=result,
            metadata={
                "agent_name": agent_name,
                "result_preview": result_preview,
            },
        )
    
    def _format_context(self, context: Dict) -> str:
        """格式化上下文信息"""
        lines = ["[Shared Context]"]
        for key, value in context.items():
            lines.append(f"- {key}: {value}")
        return "\n".join(lines)
    
    def _extract_result_preview(self, history: List) -> str:
        """从历史中提取结果预览"""
        if not history:
            return ""
        
        for msg in reversed(history):
            if msg.role in ("assistant", "user"):
                content = msg.content
                if isinstance(content, str) and content:
                    return content[:200] + "..." if len(content) > 200 else content
        
        return ""


class BatchDelegateTool(Tool):
    """批量委托任务给多个子代理的工具"""
    
    name = "batch_delegate"
    description = """批量委托任务给多个子代理并行执行。

使用场景：
- 有多个独立任务需要同时处理
- 任务之间没有依赖关系
- 需要最大化并行效率

参数：
- tasks: 任务列表，每个任务包含 agent_name 和 task
- parallel: 是否并行执行（默认 true）"""
    
    def __init__(self, orchestrator: "MultiAgentOrchestrator"):
        self.orchestrator = orchestrator
    
    @property
    def parameters(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "tasks": {
                    "type": "array",
                    "description": "任务列表",
                    "items": {
                        "type": "object",
                        "properties": {
                            "agent_name": {"type": "string"},
                            "task": {"type": "string"},
                            "context": {"type": "object"},
                        },
                        "required": ["agent_name", "task"],
                    },
                },
                "parallel": {
                    "type": "boolean",
                    "description": "是否并行执行",
                    "default": True,
                },
            },
            "required": ["tasks"],
        }
    
    async def execute(
        self,
        tasks: List[Dict[str, Any]],
        parallel: bool = True,
    ) -> ToolResult:
        """执行批量委托"""
        # 转换任务格式
        from .executor import Task
        
        task_objects = [
            Task(
                agent_name=t["agent_name"],
                task=t["task"],
                context=t.get("context"),
            )
            for t in tasks
        ]
        
        # 执行
        mode = "parallel" if parallel else "sequential"
        result = await self.orchestrator.executor.execute(task_objects, mode)
        
        return ToolResult(
            success=result["success"] > 0,
            content=str(result),
            metadata=result,
        )


class RequestStatusTool(Tool):
    """查询子代理状态的工具"""
    
    name = "request_agent_status"
    description = "查询指定子代理的当前状态和进度"
    
    def __init__(self, agents: Dict[str, "Agent"]):
        self.agents = agents
    
    @property
    def parameters(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "agent_name": {
                    "type": "string",
                    "description": f"子代理名称，可用选项: {list(self.agents.keys())}",
                },
            },
            "required": ["agent_name"],
        }
    
    async def execute(self, agent_name: str) -> ToolResult:
        """查询状态"""
        if agent_name not in self.agents:
            return ToolResult(success=False, error=f"Unknown agent: {agent_name}")
        
        agent = self.agents[agent_name]
        status = {
            "agent_name": agent_name,
            "message_count": len(agent.messages),
            "step": len(agent.messages),
            "workspace": str(agent.workspace_dir),
            "token_usage": agent.api_total_tokens,
        }
        
        return ToolResult(success=True, content=str(status))


class GatherResultsTool(Tool):
    """收集所有子代理结果的工具"""
    
    name = "gather_results"
    description = "收集所有子代理的执行结果进行汇总"
    
    def __init__(self, agents: Dict[str, "Agent"]):
        self.agents = agents
    
    @property
    def parameters(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "agent_names": {
                    "type": "array",
                    "description": "要收集结果的代理名称列表",
                    "items": {"type": "string"},
                },
            },
            "required": ["agent_names"],
        }
    
    async def execute(self, agent_names: List[str]) -> ToolResult:
        """收集结果"""
        results = {}
        for name in agent_names:
            if name in self.agents:
                agent = self.agents[name]
                if agent.messages:
                    last_msg = agent.messages[-1]
                    results[name] = {
                        "role": last_msg.role,
                        "content": last_msg.content if isinstance(last_msg.content, str) 
                                  else str(last_msg.content),
                    }
        
        return ToolResult(
            success=True,
            content=f"Collected results from {len(results)} agents:\n\n{results}",
        )
```

### 3.3 提示词模板

```python
# 文件：mini_agent/orchestration/prompts/__init__.py

"""
Prompt Templates - 提示词模板模块
"""

from .coordinator_prompts import (
    get_coordinator_prompt,
    COORDINATOR_SYSTEM_PROMPT,
)
from .agent_prompts import (
    CODER_PROMPT,
    DESIGNER_PROMPT,
    RESEARCHER_PROMPT,
    TESTER_PROMPT,
    DEPLOYER_PROMPT,
)

__all__ = [
    "get_coordinator_prompt",
    "COORDINATOR_SYSTEM_PROMPT",
    "CODER_PROMPT",
    "DESIGNER_PROMPT",
    "RESEARCHER_PROMPT",
    "TESTER_PROMPT",
    "DEPLOYER_PROMPT",
]
```

```python
# 文件：mini_agent/orchestration/prompts/coordinator_prompts.py

"""
Coordinator Prompts - 协调器提示词模板
"""

COORDINATOR_SYSTEM_PROMPT = """You are an expert Multi-Agent Coordinator. Your role is to orchestrate a team of specialized agents to complete complex tasks efficiently.

## Your Team

You have access to the following specialized agents:

{agent_descriptions}

## Coordination Strategy

1. **Task Analysis**: Break down the user's request into independent sub-tasks
2. **Agent Selection**: Choose the most appropriate agent for each sub-task
3. **Parallelization**: Identify tasks that can run concurrently
4. **Result Integration**: Combine results from multiple agents into a coherent response
5. **Quality Assurance**: Verify results meet requirements before finalizing

## Guidelines

- Prefer delegating tasks over attempting everything yourself
- Consider dependencies between sub-tasks when ordering
- Communicate clearly with each agent about expectations
- Handle partial failures gracefully
- Provide enough context to each agent for them to work independently

## Available Tools

You have access to the following coordination tools:

1. **delegate_to_agent**: Delegate a specific task to a specialized agent
2. **batch_delegate**: Delegate multiple tasks to multiple agents (parallel or sequential)
3. **request_agent_status**: Check the status of a specific agent
4. **gather_results**: Collect results from multiple agents
5. **share_context**: Share information between agents

## Communication Pattern

When delegating:
1. Provide clear, specific task descriptions
2. Include necessary context from the original request
3. Set clear success criteria
4. Specify any constraints or preferences

## Workspace Management

Each agent has its own workspace:
- Results from one agent are NOT automatically visible to another
- Use the `share_context` tool to pass information between agents
- Final integration should happen here, in the coordinator

Remember: Your goal is to orchestrate, not to do. Delegate wisely!"""


def get_coordinator_prompt(
    agent_names: list,
    agent_descriptions: str = None,
) -> str:
    """生成协调器系统提示词
    
    Args:
        agent_names: 子代理名称列表
        agent_descriptions: 子代理描述（可选，自动生成）
    
    Returns:
        完整的系统提示词
    """
    if agent_descriptions is None:
        # 自动生成描述
        descriptions = []
        for name in agent_names:
            # 基于名称生成简单描述
            desc_map = {
                "coder": "Coding and software development specialist",
                "designer": "Visual design and creative specialist",
                "researcher": "Research and analysis specialist",
                "tester": "Testing and quality assurance specialist",
                "deployer": "DevOps and deployment specialist",
                "analyst": "Data analysis and insights specialist",
                "documenter": "Documentation and technical writing specialist",
            }
            description = desc_map.get(name, f"{name.replace('_', ' ').title()} specialist")
            descriptions.append(f"- **{name}**: {description}")
        agent_descriptions = "\n".join(descriptions)
    
    return COORDINATOR_SYSTEM_PROMPT.format(
        agent_descriptions=agent_descriptions
    )
```

```python
# 文件：mini_agent/orchestration/prompts/agent_prompts.py

"""
Agent Prompts - 专业代理提示词模板
"""

CODER_PROMPT = """You are a specialized Coding Agent. Your focus is on writing, debugging, and refactoring code.

## Your Expertise

- Writing clean, efficient code in multiple languages
- Debugging complex issues with detailed analysis
- Code review and optimization suggestions
- Writing tests and documentation
- Working with version control systems

## Working Style

- Analyze the requirements carefully before coding
- Write modular, maintainable code
- Add comments for complex logic
- Test your changes when possible
- Consider edge cases and error handling

## Output Format

When completing a task, provide:
1. A summary of what was accomplished
2. Key files created or modified
3. Any issues encountered and how they were resolved
4. Recommendations for follow-up if needed

You work in your dedicated workspace. Return your results to the coordinator for integration."""


DESIGNER_PROMPT = """You are a specialized Design Agent. Your focus is on visual design, UI/UX, and creative tasks.

## Your Expertise

- Creating visual designs (posters, presentations, documents)
- Design principles and best practices
- Brand guidelines application
- Creative concept development
- User interface and experience design

## Working Style

- Understand the core message before designing
- Apply design principles systematically
- Consider accessibility and usability
- Iterate based on feedback

## Tools Available

- Canvas design for PNG/PDF outputs
- Document creation tools
- Presentation tools

## Output Format

When completing a task, provide:
1. Design summary and approach
2. Files created
3. Key design decisions
4. Suggestions for improvements

Return your design results to the coordinator for integration."""


RESEARCHER_PROMPT = """You are a specialized Research Agent. Your focus is on gathering information, analyzing data, and providing insights.

## Your Expertise

- Web research and information gathering
- Data analysis and interpretation
- Technical documentation review
- Competitive analysis
- Trend identification

## Working Style

- Systematically gather information from multiple sources
- Verify information accuracy
- Organize findings clearly
- Provide actionable insights

## Tools Available

- Web search and browsing
- File reading and analysis
- Data processing tools

## Output Format

When completing a task, provide:
1. Research summary
2. Key findings
3. Sources referenced
4. Recommendations or insights

Return your research results to the coordinator for integration."""


TESTER_PROMPT = """You are a specialized Testing Agent. Your focus is on quality assurance, testing, and verification.

## Your Expertise

- Writing and executing test cases
- Automated testing frameworks
- Performance testing and optimization
- Security testing
- Code review and quality gates

## Working Style

- Create comprehensive test coverage
- Test edge cases and error conditions
- Document test results clearly
- Provide actionable feedback

## Tools Available

- Test execution frameworks
- Code analysis tools
- Performance monitoring tools

## Output Format

When completing a task, provide:
1. Test summary
2. Test coverage report
3. Issues found and severity
4. Recommendations for fixes

Return your test results to the coordinator for integration."""


DEPLOYER_PROMPT = """You are a specialized DevOps Agent. Your focus is on deployment, infrastructure, and operations.

## Your Expertise

- CI/CD pipeline management
- Container orchestration (Docker, Kubernetes)
- Cloud infrastructure management
- Monitoring and logging
- Security and compliance

## Working Style

- Follow infrastructure as code practices
- Ensure security and compliance
- Implement proper monitoring
- Plan for rollbacks and disaster recovery

## Tools Available

- Container tools
- Cloud provider interfaces
- CI/CD systems
- Monitoring tools

## Output Format

When completing a task, provide:
1. Deployment summary
2. Changes made
3. Verification steps
4. Rollback plan

Return your deployment results to the coordinator for integration."""
```

### 3.4 使用示例

```python
# 文件：examples/multi_agent_demo.py

"""
Multi-Agent Orchestration Demo - 多代理协调演示

展示如何使用多代理系统完成复杂开发任务。
"""

import asyncio
from pathlib import Path

from mini_agent import Agent
from mini_agent.llm import create_llm_client
from mini_agent.tools import BashTool, FileTool
from mini_agent.orchestration import create_orchestrator
from mini_agent.orchestration.prompts import (
    get_coordinator_prompt,
    CODER_PROMPT,
    DESIGNER_PROMPT,
    RESEARCHER_PROMPT,
)


async def demo_complex_task():
    """演示复杂任务的处理流程"""
    
    print("=" * 70)
    print("🚀 启动多代理协作系统")
    print("=" * 70)
    
    # 1. 创建 LLM 客户端
    llm = create_llm_client("anthropic")
    
    # 2. 定义子代理配置
    sub_agent_configs = [
        {
            "name": "coder",
            "system_prompt": CODER_PROMPT,
            "tools": [
                BashTool(),
                FileTool(),
            ],
            "max_steps": 30,
            "workspace": "./workspace/coder",
        },
        {
            "name": "designer",
            "system_prompt": DESIGNER_PROMPT,
            "tools": [
                FileTool(),
            ],
            "max_steps": 20,
            "workspace": "./workspace/designer",
        },
        {
            "name": "researcher",
            "system_prompt": RESEARCHER_PROMPT,
            "tools": [
                BashTool(),
                FileTool(),
            ],
            "max_steps": 20,
            "workspace": "./workspace/researcher",
        },
    ]
    
    # 3. 创建协调系统
    orchestrator = create_orchestrator(
        main_llm_client=llm,
        sub_agent_configs=sub_agent_configs,
        workspace_dir="./workspace/multi_agent",
        max_steps=50,
    )
    
    # 4. 提交复杂任务
    task = """
    请帮我完成一个完整的项目：
    
    1. 研究当前 AI Agent 技术的发展趋势，整理成报告
    2. 设计一个产品发布会的宣传海报
    3. 编写一个简单的 Agent 演示程序，包含文档
    
    请协调各个专业代理完成这些任务。
    """
    
    # 5. 执行任务
    result = await orchestrator.execute_task(task)
    
    print("\n" + "=" * 70)
    print("✅ 多代理协作完成")
    print("=" * 70)
    print(f"\n最终结果:\n{result['result']}")
    
    # 6. 查看状态
    status = orchestrator.get_status()
    print(f"\n系统状态: {status}")
    
    return result


async def demo_parallel_tasks():
    """演示并行任务执行"""
    
    print("=" * 70)
    print("🚀 启动并行任务执行演示")
    print("=" * 70)
    
    # 创建 LLM 客户端
    llm = create_llm_client("anthropic")
    
    # 定义子代理
    sub_agent_configs = [
        {
            "name": "coder",
            "system_prompt": CODER_PROMPT,
            "tools": [BashTool(), FileTool()],
            "max_steps": 20,
            "workspace": "./workspace/demo/coder",
        },
        {
            "name": "researcher",
            "system_prompt": RESEARCHER_PROMPT,
            "tools": [BashTool(), FileTool()],
            "max_steps": 20,
            "workspace": "./workspace/demo/researcher",
        },
    ]
    
    orchestrator = create_orchestrator(
        main_llm_client=llm,
        sub_agent_configs=sub_agent_configs,
        workspace_dir="./workspace/demo",
        max_steps=30,
    )
    
    # 定义并行任务
    tasks = [
        {
            "agent": "coder",
            "task": "创建一个 Python 计算器程序，包含加减乘除功能，保存到 calculator.py",
            "context": {"project": "calculator_demo"},
        },
        {
            "agent": "researcher",
            "task": "研究 Python 最好的代码规范指南，总结关键点保存到 coding_standards.md",
            "context": {"project": "calculator_demo"},
        },
    ]
    
    # 并行执行
    result = await orchestrator.execute_parallel_tasks(tasks, mode="parallel")
    
    print("\n" + "=" * 70)
    print("✅ 并行任务完成")
    print("=" * 70)
    print(f"\n执行模式: {result['mode']}")
    print(f"成功: {result['success']}/{result['total']}")
    print(f"任务类型分布: {result['task_breakdown']}")
    
    return result


if __name__ == "__main__":
    # 运行演示
    asyncio.run(demo_complex_task())
    print("\n" + "=" * 70)
    asyncio.run(demo_parallel_tasks())
```

---

## 四、实施路线图

### 4.1 分阶段实施计划

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         实施阶段总览                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Phase 1: 基础框架（Week 1）                                             │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Day 1-2: 创建项目结构和基础组件                                 │   │
│  │  • 创建 orchestration 和 prompts 目录                            │   │
│  │  • 实现协调器主类（orchestrator.py）                             │   │
│  │  • 实现基本的 Task 和 Executor 类                                │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Day 3-4: 实现协调工具                                           │   │
│  │  • 实现 DelegateToAgentTool                                      │   │
│  │  • 实现 BatchDelegateTool                                        │   │
│  │  • 实现 RequestStatusTool 和 GatherResultsTool                   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Day 5: 基础测试和示例                                           │   │
│  │  • 编写单元测试                                                   │   │
│  │  • 创建基础演示示例                                               │   │
│  │  • 代码审查和合并                                                 │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  Phase 2: 高级特性（Week 2）                                             │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Day 1-2: 智能混合执行器                                         │   │
│  │  • 实现 OptimizedExecutor                                        │   │
│  │  • 实现任务类型自动检测                                           │   │
│  │  • 实现智能模式选择                                               │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Day 3-4: 通信工具和状态管理                                     │   │
│  │  • 实现 ShareContextTool                                         │   │
│  │  • 实现 BroadcastMessageTool                                     │   │
│  │  • 实现状态同步机制                                               │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Day 5: 集成测试和优化                                           │   │
│  │  • 集成测试                                                       │   │
│  │  • 性能优化                                                       │   │
│  │  • 文档完善                                                       │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  Phase 3: 测试和完善（Week 3）                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Day 1-2: 完整测试套件                                           │   │
│  │  • 单元测试                                                       │   │
│  │  • 集成测试                                                       │   │
│  │  • E2E 测试                                                       │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Day 3-4: 文档和示例                                             │   │
│  │  • API 文档                                                       │   │
│  │  • 使用示例                                                       │   │
│  │  • 架构文档                                                       │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Day 5: 发布准备                                                 │   │
│  │  • 代码审查                                                       │   │
│  │  • 版本发布                                                       │   │
│  │  • 更新日志                                                       │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  总计: 3 周（15 个工作日）                                               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.2 详细里程碑

```
里程碑 1：基础框架完成（M1）
──────────────
完成时间：第 1 周周五

交付物：
├── orchestration/orchestrator.py ✅
├── orchestration/executor.py ✅
├── prompts/coordinator_prompts.py ✅
├── prompts/agent_prompts.py ✅
├── tests/orchestration/test_orchestrator.py ✅
└── examples/multi_agent_demo.py ✅

验收标准：
├── 所有现有测试继续通过
├── 新增单元测试覆盖率达到 80%
├── 基础演示运行成功

里程碑 2：高级特性完成（M2）
──────────────
完成时间：第 2 周周五

交付物：
├── tools/orchestration.py ✅
├── tools/communication.py ✅
├── orchestration/task_router.py ✅
├── orchestration/result_aggregator.py ✅
└── tests/orchestration/test_advanced.py ✅

验收标准：
├── 协调工具功能完整
├── 任务类型自动检测准确率 > 90%
├── 性能提升 3-5 倍

里程碑 3：发布准备完成（M3）
──────────────
完成时间：第 3 周周五

交付物：
├── 完整测试套件 ✅
├── API 文档 ✅
├── 用户指南 ✅
├── CHANGELOG.md ✅
└── 版本发布 ✅

验收标准：
├── 测试覆盖率 > 85%
├── 无严重 bug
├── 文档完整
└── 用户可以顺利使用新功能
```

### 4.3 工作量估算

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         工作量详细估算                                   │
├────────────────────────────────┬────────────────────────────────────────┤
│           任务                  │            时间估算                    │
├────────────────────────────────┼────────────────────────────────────────┤
│ Phase 1: 基础框架              │ 5 天                                   │
│  ├── 目录结构创建              │ 0.5 天                                 │
│  ├── 协调器主类实现            │ 1 天                                   │
│  ├── 执行器核心实现            │ 1 天                                   │
│  ├── 协调工具实现              │ 1.5 天                                 │
│  └── 测试和示例                │ 1 天                                   │
├────────────────────────────────┼────────────────────────────────────────┤
│ Phase 2: 高级特性              │ 5 天                                   │
│  ├── 智能混合执行器            │ 1.5 天                                 │
│  ├── 通信工具实现              │ 1 天                                   │
│  ├── 状态管理机制              │ 1 天                                   │
│  └── 集成和优化                │ 1.5 天                                 │
├────────────────────────────────┼────────────────────────────────────────┤
│ Phase 3: 测试和完善            │ 5 天                                   │
│  ├── 单元测试                  │ 1.5 天                                 │
│  ├── 集成测试                  │ 1.5 天                                 │
│  ├── 文档编写                  │ 1 天                                   │
│  └── 发布准备                  │ 1 天                                   │
├────────────────────────────────┼────────────────────────────────────────┤
│ 总计                           │ 15 天（3 周）                          │
├────────────────────────────────┴────────────────────────────────────────┤
│ 缓冲时间（20%）                │ +3 天                                   │
├────────────────────────────────┴────────────────────────────────────────┤
│ 实际工期                       │ 18 天（~4 周）                         │
└────────────────────────────────┴────────────────────────────────────────┘
```

---

## 五、风险管理与缓解策略

### 5.1 风险识别与评估

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         风险评估矩阵                                     │
├────────────────────────────────┬────────┬────────┬──────────────────────┤
│           风险                  │ 影响   │ 概率   │              等级    │
├────────────────────────────────┼────────┼────────┼──────────────────────┤
│ 改造影响现有功能               │  高    │  低    │ 🟡 中等              │
│ 性能下降                       │  高    │  低    │ 🟡 中等              │
│ 实现复杂度超预期               │  中    │  中    │ 🟡 中等              │
│ 学习曲线陡峭                   │  低    │  高    │ 🟡 中等              │
│ 集成测试困难                   │  中    │  中    │ 🟢 低                │
│ 资源竞争问题                   │  中    │  低    │ 🟢 低                │
│ 依赖兼容性问题                 │  高    │  低    │ 🟡 中等              │
└────────────────────────────────┴────────┴────────┴──────────────────────┘
```

### 5.2 缓解策略

```
风险 1：改造影响现有功能
───────────────────────
缓解策略：
├── 渐进式改造，不影响核心功能
├── 保持 API 向后兼容
├── 保留现有单代理模式
├── 充分的回归测试
└── 可随时回滚

风险 2：性能下降
───────────────────────
缓解策略：
├── 仅在启用多代理时增加开销
├── 优化协调提示词减少 Token
├── 默认单代理模式零额外开销
└── 性能基准测试

风险 3：实现复杂度超预期
───────────────────────
缓解策略：
├── 分阶段实现，可独立交付
├── 优先实现核心功能
├── 使用现有代码库模式
└── 预留缓冲时间

风险 4：学习曲线陡峭
───────────────────────
缓解策略：
├── 向后完全兼容
├── 提供渐进式文档
├── 保留简单使用方式
└── 丰富的示例代码

风险 5：集成测试困难
───────────────────────
缓解策略：
├── 建立完整的测试套件
├── 使用 CI/CD 自动化测试
├── 隔离测试环境
└── E2E 测试覆盖
```

### 5.3 回滚计划

```
回滚策略：

代码级别：
├── Git 分支管理，可随时回退
├── 功能开关控制，可禁用多代理功能
└── 保留完整历史记录

部署级别：
├── 保持单代理镜像兼容
├── 支持并行部署和切换
└── 蓝绿部署策略

数据级别：
├── 消息格式保持兼容
├── 配置格式支持版本迁移
└── 无数据迁移需求
```

---

## 六、预期效果与收益

### 6.1 性能提升预估

```
基于 Ubuntu 开发环境的性能预估：

配置示例：
- CPU: 8 核心 / 16 线程
- 内存: 32 GB
- 存储: NVMe SSD

场景 1：并行代码生成（10 个独立文件）
─────────────────────────────────────
改进前（顺序）：50 秒
改进后（并行）：5-6 秒
提升倍数：8-10 倍

场景 2：并行测试执行（20 个测试文件）
─────────────────────────────────────
改进前（顺序）：60 秒
改进后（并行）：6-8 秒
提升倍数：8-10 倍

场景 3：混合任务（5 API + 5 文件处理）
─────────────────────────────────────
改进前（顺序）：27.5 秒
改进后（混合）：5-6 秒
提升倍数：4-5 倍

场景 4：复杂项目开发
─────────────────────────────────────
改进前：需要手动协调多个任务
改进后：自动分解、并行执行、智能调度
预估效率提升：3-5 倍

总体平均提升：4-7 倍开发效率提升
```

### 6.2 功能增强

```
功能增强清单：

1. 专业化分工
   ├── 可配置的专业子代理
   ├── 独立的工具集和提示词
   └── 领域特定优化

2. 并行执行
   ├── 异步并行模式（I/O 密集型）
   ├── 线程池模式（CPU 密集型）
   ├── 顺序执行模式（依赖任务）
   └── 智能模式选择

3. 协调机制
   ├── 任务委托工具
   ├── 批量委托工具
   ├── 状态查询工具
   ├── 结果收集工具
   ├── 上下文共享工具
   └── 消息广播工具

4. 可扩展性
   ├── 动态添加/移除子代理
   ├── 自定义执行模式
   └── 插件式工具系统
```

### 6.3 长期价值

```
长期价值分析：

1. 技术债务减少
   ├── 模块化设计易于维护
   └── 清晰的职责分离

2. 扩展能力强
   ├── 新功能通过添加子代理实现
   └── 不影响现有功能

3. 生态系统完善
   ├── 可共享和复用子代理配置
   └── 可形成子代理市场

4. 团队效率提升
   ├── 自动化复杂任务协调
   └── 减少人工干预
```

---

## 七、总结与建议

### 7.1 方案总结

本改进方案提出了将 Mini-Agent 从单代理架构升级为多代理协调架构的完整技术方案。方案基于 Ubuntu 系统的技术特性和开发场景的任务特征，设计了智能混合执行框架，能够根据任务性质自动选择最优执行模式。实现分为三个阶段，总工期约 4 周，预期带来 4-7 倍的开发效率提升。

方案的核心优势包括：**渐进式改造**确保现有功能不受影响；**智能执行**最大化资源利用效率；**模块化设计**便于维护和扩展；**向后兼容**保证平滑升级。

### 7.2 下一步行动

```
立即开始：
─────────────
1. 创建特性分支
   git checkout -b feature/multi-agent-orchestration

2. 实现 Phase 1（基础框架）
   - 创建目录结构
   - 实现协调器主类
   - 实现基础执行器
   - 编写基础测试

3. 运行现有测试确保兼容

4. 提交代码进行审查

持续改进：
─────────────
5. 实现 Phase 2（高级特性）
6. 添加完整测试
7. 完善文档和示例
8. 发布 v0.6.0
```

### 7.3 成功标准

```
成功标准：

功能完整性：
├── 所有计划功能实现完成
├── 向后兼容 100%
└── 文档完整度 > 90%

性能指标：
├── 性能提升 3-5 倍（对比单代理）
├── 并行任务支持 10+ 并发
└── 内存增长 < 50%

质量标准：
├── 测试覆盖率 > 85%
├── 无严重 bug
└── 代码审查通过

用户体验：
├── 现有用户可平滑升级
├── 新用户可快速上手
└── 示例运行成功
```

---

## 附录

### A. 技术依赖

```
新增依赖：
├── 无新增核心依赖
└── 复用现有依赖（asyncio、concurrent.futures）

现有依赖：
├── Python 3.10+
├── asyncio
├── pydantic
├── tiktoken
└── pytest
```

### B. 兼容性保证

```
Python 版本：
├── 3.10+（完整功能）
├── 3.9+（基本功能）
└── 3.8-（不支持）

操作系统：
├── Ubuntu 20.04+（推荐）
├── macOS 10.15+
├── Windows 10+
└── 其他 Linux 发行版

LLM 兼容：
├── Anthropic Claude
├── OpenAI GPT-4
└── 其他兼容 OpenAI API 的模型
```

### C. 参考资料

```
相关文档：
├── 项目现有文档（docs/）
├── Python asyncio 官方文档
├── concurrent.futures 文档
└── 多代理系统研究论文
```

---

**文档版本**: 1.0  
**创建日期**: 2024 年  
**状态**: 待实施  
**下次评审**: 实现 Phase 1 后
