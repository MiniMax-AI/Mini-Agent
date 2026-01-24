# API 参考文档

本文档详细描述了 Mini-Agent 多代理协调系统的所有 API 接口、类和方法。

## 目录

- [核心类](#核心类)
- [协调器](#协调器)
- [执行器](#执行器)
- [路由器](#路由器)
- [聚合器](#聚合器)
- [工具](#工具)
- [提示词模板](#提示词模板)
- [数据类型](#数据类型)

---

## 核心类

### Agent

基础的单一代理类，用于创建和执行单个代理任务。

```python
from mini_agent import Agent

agent = Agent(
    llm_client: LLMClient,
    system_prompt: str,
    tools: List[Tool] = None,
    max_steps: int = 50,
    workspace_dir: str = "./workspace",
)
```

**参数：**

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `llm_client` | `LLMClient` | 必填 | LLM 客户端实例 |
| `system_prompt` | `str` | 必填 | 系统提示词 |
| `tools` | `List[Tool]` | `None` | 可用工具列表 |
| `max_steps` | `int` | `50` | 最大执行步数 |
| `workspace_dir` | `str` | `"./workspace"` | 工作目录 |

**方法：**

#### `add_user_message(message: str)`

添加用户消息到消息历史。

```python
agent.add_user_message("请帮我编写一个 Python 函数")
```

#### `async run() -> str`

执行代理任务。

```python
result = await agent.run()
print(result)
```

---

## 协调器

### MultiAgentOrchestrator

**位置：** `mini_agent.orchestration.orchestrator`

多代理协调器主类，管理主代理和所有子代理的协调执行。

```python
from mini_agent.orchestration import MultiAgentOrchestrator

orchestrator = MultiAgentOrchestrator(
    main_llm_client: LLMClient,
    sub_agent_configs: List[Dict[str, Any]],
    workspace_dir: str = "./workspace",
    max_steps: int = 50,
    default_timeout: int = 300,
    enable_logging: bool = True,
)
```

**参数：**

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `main_llm_client` | `LLMClient` | 必填 | 主代理使用的 LLM 客户端 |
| `sub_agent_configs` | `List[Dict]` | 必填 | 子代理配置列表 |
| `workspace_dir` | `str` | `"./workspace"` | 主工作目录 |
| `max_steps` | `int` | `50` | 主代理最大步数 |
| `default_timeout` | `int` | `300` | 默认任务超时时间（秒） |
| `enable_logging` | `bool` | `True` | 是否启用日志记录 |

**子代理配置格式：**

```python
sub_agent_configs = [
    {
        "name": "coder",
        "system_prompt": CODER_PROMPT,
        "tools": [BashTool(), FileTool()],
        "max_steps": 30,
        "workspace": "./workspace/coder",
    },
    {
        "name": "designer",
        "system_prompt": DESIGNER_PROMPT,
        "tools": [FileTool()],
        "max_steps": 20,
        "workspace": "./workspace/designer",
    },
]
```

**属性：**

| 属性 | 类型 | 描述 |
|------|------|------|
| `main_agent` | `Agent` | 主代理实例 |
| `sub_agents` | `Dict[str, Agent]` | 子代理字典 |
| `executor` | `OptimizedExecutor` | 执行器实例 |
| `task_router` | `TaskRouter` | 任务路由器 |
| `result_aggregator` | `ResultAggregator` | 结果聚合器 |
| `shared_context` | `Dict[str, Any]` | 共享上下文 |
| `task_history` | `List[Dict]` | 任务历史 |

**方法：**

#### `async execute_task(task: str, context: Dict = None, mode: str = "auto") -> Dict[str, Any]`

执行单个复杂任务。

```python
result = await orchestrator.execute_task(
    task="请完成一个完整的项目，包括代码编写和文档",
    context={"project": "my_project"},
    mode="auto"
)
```

**返回值：**

```python
{
    "success": True,
    "result": "...",           # 执行结果
    "task_history": [...],     # 任务历史
}
```

#### `async execute_parallel_tasks(tasks: List[Dict], mode: str = "auto") -> Dict[str, Any]`

并行执行多个独立任务。

```python
result = await orchestrator.execute_parallel_tasks(
    tasks=[
        {
            "agent": "coder",
            "task": "编写登录模块",
            "context": {"project": "webapp"},
            "priority": 1,
        },
        {
            "agent": "designer",
            "task": "设计登录页面",
            "context": {"project": "webapp"},
            "priority": 1,
        },
    ],
    mode="parallel"
)
```

**返回值：**

```python
{
    "overall_status": "success",    # 总体状态
    "total": 2,                      # 总任务数
    "success": 2,                    # 成功数
    "failed": 0,                     # 失败数
    "results": [...],                # 详细结果
    "summary": "...",                # 结果摘要
    "task_breakdown": {              # 任务类型分布
        "cpu_bound": 0,
        "io_bound": 2,
    },
}
```

#### `async delegate_task(agent_name: str, task: str, context: Dict = None, timeout: int = None) -> Dict[str, Any]`

直接委托任务给指定子代理。

```python
result = await orchestrator.delegate_task(
    agent_name="coder",
    task="编写计算器程序",
    context={"type": "cli"},
    timeout=600,
)
```

#### `get_status() -> Dict[str, Any]`

获取协调器状态。

```python
status = orchestrator.get_status()
# {
#     "sub_agent_count": 3,
#     "sub_agent_names": ["coder", "designer", "researcher"],
#     "task_history_count": 10,
#     "shared_context_keys": ["project", "user"],
# }
```

#### `get_sub_agent_status() -> Dict[str, Dict]`

获取所有子代理的状态。

```python
status = orchestrator.get_sub_agent_status()
# {
#     "coder": {"message_count": 50, "step": 50, "token_usage": 12000},
#     "designer": {"message_count": 30, "step": 30, "token_usage": 8000},
# }
```

#### `add_sub_agent(name: str, config: Dict[str, Any])`

动态添加子代理。

```python
orchestrator.add_sub_agent(
    name="tester",
    config={
        "system_prompt": TESTER_PROMPT,
        "tools": [BashTool()],
        "max_steps": 20,
        "workspace": "./workspace/tester",
    },
)
```

#### `remove_sub_agent(name: str)`

移除子代理。

```python
orchestrator.remove_sub_agent("tester")
```

#### `clear_context()`

清空共享上下文。

```python
orchestrator.clear_context()
```

#### `clear_history()`

清空任务历史。

```python
orchestrator.clear_history()
```

---

### create_orchestrator

便捷创建函数。

```python
from mini_agent.orchestration import create_orchestrator

orchestrator = create_orchestrator(
    main_llm_client=llm_client,
    sub_agent_configs=[...],
    workspace_dir="./workspace",
    max_steps=50,
)
```

---

## 执行器

### OptimizedExecutor

**位置：** `mini_agent.orchestration.executor`

智能混合执行器，针对 Ubuntu 系统优化。

```python
from mini_agent.orchestration import OptimizedExecutor

executor = OptimizedExecutor(
    agents: Dict[str, Agent],
)
```

**属性：**

| 属性 | 类型 | 描述 |
|------|------|------|
| `config` | `UbuntuConfig` | Ubuntu 系统配置 |
| `semaphore` | `asyncio.Semaphore` | 异步并发控制信号量 |
| `thread_pool` | `ThreadPoolExecutor` | 线程池 |

**方法：**

#### `async execute_task(task: Task) -> Dict[str, Any]`

执行单个任务（带并发控制）。

```python
task = Task(
    agent_name="coder",
    task="编写代码",
    context={"project": "demo"},
    timeout=300,
    priority=1,
)
result = await executor.execute_task(task)
```

#### `async execute_parallel(tasks: List[Task]) -> List[Dict[str, Any]]`

并行执行任务列表。

```python
tasks = [
    Task(agent_name="coder", task="Task 1"),
    Task(agent_name="designer", task="Task 2"),
]
results = await executor.execute_parallel(tasks)
```

#### `execute_sequential(tasks: List[Task]) -> List[Dict[str, Any]]`

顺序执行任务列表（使用线程池）。

```python
results = executor.execute_sequential(tasks)
```

#### `async execute(tasks: List[Task], mode: str = "auto") -> Dict[str, Any]`

智能执行任务。

```python
result = await executor.execute(tasks, mode="auto")
# mode: "auto" | "parallel" | "sequential" | "thread"
```

#### `analyze_task_type(task: Task) -> str`

分析任务类型。

```python
task_type = executor.analyze_task_type(Task(agent_name="coder", task="计算数据分析"))
# 返回: "cpu_bound" 或 "io_bound"
```

#### `get_config() -> Dict[str, Any]`

获取执行器配置。

```python
config = executor.get_config()
# {
#     "cpu_count": 8,
#     "max_async_concurrent": 200,
#     "thread_pool_size": 16,
# }
```

#### `shutdown()`

关闭执行器。

```python
executor.shutdown()
```

---

### Task

任务定义数据类。

```python
from mini_agent.orchestration import Task

task = Task(
    agent_name: str,          # 必填，代理名称
    task: str,                # 必填，任务描述
    context: Dict = None,     # 可选，上下文
    timeout: int = 300,       # 可选，超时时间（秒）
    priority: int = 0,        # 可选，优先级
    task_type: str = "io_bound",  # 可选，任务类型
)
```

**属性：**

| 属性 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `agent_name` | `str` | 必填 | 子代理名称 |
| `task` | `str` | 必填 | 任务描述 |
| `context` | `Dict` | `None` | 上下文信息 |
| `timeout` | `int` | `300` | 超时时间（秒） |
| `priority` | `int` | `0` | 优先级（数值越大优先级越高） |
| `task_type` | `str` | `"io_bound"` | 任务类型（`"io_bound"` 或 `"cpu_bound"`） |

---

### UbuntuConfig

Ubuntu 系统优化配置类。

```python
from mini_agent.orchestration import UbuntuConfig

config = UbuntuConfig()
```

**属性：**

| 属性 | 值 | 描述 |
|------|------|------|
| `CPU_COUNT` | `os.cpu_count()` | CPU 核心数 |
| `MAX_ASYNC_CONCURRENT` | `min(200, 32 * CPU_COUNT)` | 最大异步并发数 |
| `THREAD_POOL_SIZE` | `CPU_COUNT * 2` | 线程池大小 |
| `PROCESS_POOL_SIZE` | `max(1, CPU_COUNT - 1)` | 进程池大小 |
| `MEMORY_LIMIT` | `总内存 * 0.5` | 内存限制（GB） |

---

## 路由器

### TaskRouter

**位置：** `mini_agent.orchestration.task_router`

任务路由器，智能路由任务到合适的代理。

```python
from mini_agent.orchestration import TaskRouter

router = TaskRouter(
    agents: Dict[str, Agent],
    config: RouterConfig = None,
)
```

**方法：**

#### `route(task: str, preferred_agent: str = None) -> RouteResult`

路由单个任务。

```python
result = router.route(
    task="编写 Python 代码实现登录功能",
    preferred_agent="coder"  # 可选的首选代理
)
```

**返回值：**

```python
RouteResult(
    agent_name="coder",       # 路由到的代理名称
    confidence=0.85,          # 置信度 0-1
    reasoning="根据关键词'编写'和'代码'匹配到 coder 代理",  # 路由理由
    alternative=None,         # 备选代理
)
```

#### `route_batch(tasks: List[Dict], preferred_agents: Dict = None) -> List[RouteResult]`

批量路由任务。

```python
results = router.route_batch(
    tasks=[
        {"task": "编写代码"},
        {"task": "设计界面"},
    ],
    preferred_agents={"task_1": "coder"},
)
```

#### `get_load_status() -> Dict[str, Any]`

获取代理负载状态。

```python
status = router.get_load_status()
# {
#     "agent_loads": {"coder": 5, "designer": 2},
#     "total_load": 7,
#     "average_load": 3.5,
# }
```

#### `get_statistics() -> Dict[str, Any]`

获取路由统计信息。

```python
stats = router.get_statistics()
# {
#     "total_routes": 100,
#     "agent_selection_count": {"coder": 60, "designer": 40},
#     "average_confidence": 0.82,
# }
```

---

### RouterConfig

路由器配置。

```python
from mini_agent.orchestration import RouterConfig

config = RouterConfig(
    enable_load_balancing=True,    # 启用负载均衡
    enable_caching=True,           # 启用路由缓存
    cache_ttl=300,                 # 缓存 TTL（秒）
    min_confidence=0.3,            # 最小置信度阈值
)
```

---

### RouteResult

路由结果。

```python
from mini_agent.orchestration import RouteResult

result = RouteResult(
    agent_name="coder",
    confidence=0.85,
    reasoning="...",
    alternative=None,
)
```

---

### TaskPriority

任务优先级枚举。

```python
from mini_agent.orchestration import TaskPriority

TaskPriority.LOW      # 优先级 0
TaskPriority.NORMAL   # 优先级 1
TaskPriority.HIGH     # 优先级 2
TaskPriority.CRITICAL # 优先级 3
```

---

## 聚合器

### ResultAggregator

**位置：** `mini_agent.orchestration.result_aggregator`

结果聚合器，收集、验证和整合执行结果。

```python
from mini_agent.orchestration import ResultAggregator

aggregator = ResultAggregator(
    enable_deduplication: bool = True,
    quality_threshold: float = 0.6,
)
```

**方法：**

#### `aggregate(execution_result: Dict[str, Any]) -> AggregatedResult`

聚合执行结果。

```python
execution_result = {
    "mode": "parallel",
    "total": 5,
    "success": 4,
    "failed": 1,
    "results": [...],
    "task_breakdown": {"cpu_bound": 1, "io_bound": 4},
}

result = aggregator.aggregate(execution_result)
```

#### `merge_results(results: List[Dict[str, Any]]) -> Dict[str, Any]`

合并多个执行结果。

```python
merged = aggregator.merge_results(results)
```

#### `format_for_output(result: AggregatedResult, format: str = "markdown") -> Union[str, Dict]`

格式化输出结果。

```python
# Markdown 格式
md_output = aggregator.format_for_output(result, "markdown")

# JSON 格式
json_output = aggregator.format_for_output(result, "json")
```

---

### AggregatedResult

聚合结果数据类。

```python
from mini_agent.orchestration import AggregatedResult

result = AggregatedResult(
    overall_status=ResultStatus.SUCCESS,
    total_count=5,
    success_count=4,
    failed_count=1,
    results=[...],
    summary="执行完成，4/5 成功",
    errors=["任务3超时"],
    metadata={...},
)
```

---

### ResultStatus

结果状态枚举。

```python
from mini_agent.orchestration import ResultStatus

ResultStatus.SUCCESS  # 全部成功
ResultStatus.PARTIAL  # 部分成功
ResultStatus.FAILED   # 大部分失败
ResultStatus.TIMEOUT  # 超时
ResultStatus.ERROR    # 错误
```

---

## 工具

### 协调工具

#### DelegateToAgentTool

将任务委托给指定子代理的工具。

```python
from mini_agent.tools import DelegateToAgentTool

tool = DelegateToAgentTool(agents=sub_agents)

result = await tool.execute(
    agent_name="coder",
    task="编写登录功能",
    context={"type": "web"},
    timeout=300,
)
```

**参数：**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `agent_name` | `str` | 是 | 子代理名称 |
| `task` | `str` | 是 | 任务描述 |
| `context` | `Dict` | 否 | 上下文信息 |
| `timeout` | `int` | 否 | 超时时间（秒） |

**返回值：**

```python
ToolResult(
    success=True,
    content="登录功能已编写完成",
    metadata={
        "agent_name": "coder",
        "result_preview": "登录功能已编写完成...",
    },
)
```

---

#### BatchDelegateTool

批量委托任务给多个子代理的工具。

```python
from mini_agent.tools import BatchDelegateTool

tool = BatchDelegateTool(orchestrator=orchestrator)

result = await tool.execute(
    tasks=[
        {"agent_name": "coder", "task": "编写代码"},
        {"agent_name": "designer", "task": "设计界面"},
    ],
    parallel=True,
)
```

---

#### RequestStatusTool

查询子代理状态的工具。

```python
from mini_agent.tools import RequestStatusTool

tool = RequestStatusTool(agents=sub_agents)

result = await tool.execute(agent_name="coder")
```

---

#### GatherResultsTool

收集所有子代理结果的工具。

```python
from mini_agent.tools import GatherResultsTool

tool = GatherResultsTool(agents=sub_agents)

result = await tool.execute(agent_names=["coder", "designer"])
```

---

### 通信工具

#### ShareContextTool

上下文共享工具。

```python
from mini_agent.tools import ShareContextTool

tool = ShareContextTool(orchestrator=orchestrator)

result = await tool.execute(
    key="user_info",
    value={"name": "张三", "role": "admin"},
    target_agents=["coder", "designer"],
    ttl=3600,
)
```

---

#### BroadcastMessageTool

消息广播工具。

```python
from mini_agent.tools import BroadcastMessageTool

tool = BroadcastMessageTool(agents=sub_agents)

result = await tool.execute(
    message="请停止当前任务，开始新任务",
    target_agents=["coder", "designer"],
    priority="urgent",
)
```

---

#### SyncStateTool

状态同步工具。

```python
from mini_agent.tools import SyncStateTool

tool = SyncStateTool(agents=sub_agents)

result = await tool.execute(
    agent_names=["coder", "designer"],
    include_details=True,
)
```

---

## 提示词模板

### 协调器提示词

#### get_coordinator_prompt

生成协调器系统提示词。

```python
from mini_agent.orchestration.prompts import get_coordinator_prompt

prompt = get_coordinator_prompt(
    agent_names=["coder", "designer"],
    agent_descriptions=None,  # 自动生成
    prompt_type="standard",    # standard | short | urgent | research
)
```

#### COORDINATOR_SYSTEM_PROMPT

标准版协调器提示词。

---

### 专业代理提示词

| 提示词 | 描述 | 适用场景 |
|--------|------|----------|
| `CODER_PROMPT` | 代码编写专家 | 编写、调试、重构代码 |
| `DESIGNER_PROMPT` | 视觉设计专家 | 海报、PPT、UI 设计 |
| `RESEARCHER_PROMPT` | 研究分析专家 | 信息收集、数据分析 |
| `TESTER_PROMPT` | 测试质量专家 | 自动化测试、质量验证 |
| `DEPLOYER_PROMPT` | 部署运维专家 | CI/CD、容器化、监控 |
| `ANALYST_PROMPT` | 数据分析专家 | 统计分析、洞察生成 |
| `DOCUMENTER_PROMPT` | 文档编写专家 | 技术文档、用户手册 |
| `REVIEWER_PROMPT` | 代码审查专家 | 代码审查、最佳实践 |
| `ARCHITECT_PROMPT` | 架构设计专家 | 系统设计、技术选型 |
| `DEBUGGER_PROMPT` | 调试分析专家 | 问题诊断、性能优化 |

#### get_agent_prompt

获取代理提示词。

```python
from mini_agent.orchestration.prompts import get_agent_prompt

prompt = get_agent_prompt("coder")
```

#### create_agent_config

创建代理配置。

```python
from mini_agent.orchestration.prompts import create_agent_config

config = create_agent_config(
    agent_type="coder",
    name="my_coder",
    tools=["tool1", "tool2"],
    max_steps=20,
)
```

---

## 数据类型

### LLMClient

LLM 客户端基类。

```python
from mini_agent.llm import LLMClient

client = LLMClient(api_key="...", model="claude-3-5-sonnet-20241022")
```

### Message

消息数据类。

```python
from mini_agent.schema import Message

message = Message(
    role="user",           # "user" | "assistant" | "system"
    content="请帮我编写代码",
)
```

### ToolResult

工具执行结果。

```python
from mini_agent.tools import ToolResult

result = ToolResult(
    success=True,
    content="执行结果",
    error=None,
    metadata={},
)
```

---

## 便捷创建函数

| 函数 | 描述 |
|------|------|
| `create_orchestrator()` | 创建协调器 |
| `create_executor()` | 创建执行器 |
| `create_task_router()` | 创建任务路由器 |
| `create_result_aggregator()` | 创建结果聚合器 |

---

**文档版本:** 0.6.0  
**最后更新:** 2024年  
**状态:** 正式发布
