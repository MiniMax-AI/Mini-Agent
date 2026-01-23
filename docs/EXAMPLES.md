# Mini-Agent 多代理协调系统使用示例指南

本文档提供 Mini-Agent v0.6.0 多代理协调系统的完整使用示例，涵盖从基础配置到高级场景的各种用例。通过这些示例，开发者可以快速上手并掌握多代理系统的使用方法。

## 目录

1. [快速开始](#快速开始)
2. [基础配置](#基础配置)
3. [单代理使用](#单代理使用)
4. [多代理协调](#多代理协调)
5. [高级场景](#高级场景)
6. [最佳实践](#最佳实践)

---

## 快速开始

### 环境准备

在开始使用多代理协调系统之前，请确保已正确安装所有依赖。推荐使用 uv 包管理器进行安装：

```bash
# 安装项目依赖
uv pip install -e .

# 验证 psutil 已安装（多代理系统必需）
uv pip show psutil
```

安装完成后，可以通过以下方式导入和使用多代理系统模块：

```python
# 导入核心组件
from mini_agent.orchestration import (
    MultiAgentOrchestrator,
    OptimizedExecutor,
    TaskRouter,
    ResultAggregator
)

# 导入提示模板
from mini_agent.orchestration.prompts import (
    get_coordinator_prompt,
    get_agent_prompt,
    create_agent_config
)

# 导入协调工具
from mini_agent.tools.orchestration import (
    DelegateToAgentTool,
    BatchDelegateTool,
    RequestStatusTool,
    GatherResultsTool
)

# 导入通信工具
from mini_agent.tools.communication import (
    ShareContextTool,
    BroadcastMessageTool
)

print("✅ Mini-Agent 多代理协调系统已就绪")
```

### 基础配置

创建配置文件 `config/multi_agent.yaml` 来配置多代理系统：

```yaml
# 多代理协调系统配置
orchestration:
  # 执行器配置
  executor:
    # 默认执行模式: "auto" | "parallel" | "sequential" | "thread"
    default_mode: "auto"
    # 异步并发数
    async_concurrency: 200
    # 线程池大小
    thread_pool_size: 16
    # 超时时间（秒）
    timeout: 300
    # 重试次数
    max_retries: 3

  # 任务路由器配置
  router:
    # 路由策略: "keyword" | "load_balancing" | "hybrid"
    strategy: "hybrid"
    # 关键词匹配阈值
    keyword_threshold: 0.7

  # 结果聚合器配置
  aggregator:
    # 结果验证启用
    validation_enabled: true
    # 质量评估启用
    quality_assessment_enabled: true
    # 默认质量阈值
    default_quality_threshold: 0.6

# 可用代理配置
agents:
  coder:
    name: "专业编码助手"
    capabilities:
      - "代码生成"
      - "代码审查"
      - "调试分析"
      - "重构优化"
    model: "claude-sonnet-4-20250514"
    temperature: 0.3

  designer:
    name: "UI/UX 设计师"
    capabilities:
      - "界面设计"
      - "交互设计"
      - "视觉设计"
      - "设计系统"
    model: "claude-sonnet-4-20250514"
    temperature: 0.7

  researcher:
    name: "研究分析师"
    capabilities:
      - "技术研究"
      - "竞品分析"
      - "趋势分析"
      - "文档编写"
    model: "claude-sonnet-4-20250514"
    temperature: 0.5

  tester:
    name: "质量保证工程师"
    capabilities:
      - "测试设计"
      - "自动化测试"
      - "性能测试"
      - "安全测试"
    model: "claude-sonnet-4-20250514"
    temperature: 0.2

  deployer:
    name: "DevOps 工程师"
    capabilities:
      - "容器化"
      - "CI/CD"
      - "云部署"
      - "监控配置"
    model: "claude-sonnet-4-20250514"
    temperature: 0.3

# Ubuntu 系统优化
ubuntu:
  # CPU 核心数
  cpu_count: 16
  # 内存使用率限制
  memory_limit: 0.8
  # SSD 优化
  ssd_optimization: true
```

---

## 基础配置

### 创建主代理

主代理是整个协调系统的核心，负责接收用户请求、分析任务、并协调各个专业代理完成任务。以下是创建主代理的详细步骤：

```python
import os
from mini_agent import Agent
from mini_agent.orchestration import (
    MultiAgentOrchestrator,
    OptimizedExecutor,
    TaskRouter,
    ResultAggregator
)
from mini_agent.orchestration.prompts import get_coordinator_prompt

# 设置 API 密钥
os.environ["ANTHROPIC_API_KEY"] = "your-api-key-here"

# 创建主代理（协调者）
main_agent = Agent(
    name="MainCoordinator",
    model="claude-sonnet-4-20250514",
    system_prompt=get_coordinator_prompt(),
    max_steps=100,
    workspace_dir="./workspace",
    tools=["bash", "file_tools", "DelegateToAgentTool", "GatherResultsTool"]
)

print("✅ 主代理创建成功")
```

### 配置执行器

执行器负责管理任务执行的并发策略和资源分配。OptimizedExecutor 支持多种执行模式，可根据任务类型自动选择最优执行策略：

```python
from mini_agent.orchestration import OptimizedExecutor
from mini_agent.orchestration.executor import UbuntuConfig

# 创建 Ubuntu 系统配置
ubuntu_config = UbuntuConfig.create()

# 创建优化执行器
executor = OptimizedExecutor(
    config=ubuntu_config,
    default_mode="auto",  # 自动选择最优执行模式
    max_concurrent_tasks=100,
    timeout_per_task=300,
    retry_on_failure=True,
    max_retries=3
)

# 自定义配置
executor = OptimizedExecutor(
    default_mode="parallel",
    async_concurrency=200,
    thread_pool_size=16,
    cpu_intensive_workers=8,
    timeout_per_task=600,
    retry_on_failure=True,
    max_retries=3
)

print("✅ 执行器配置完成")
print(f"   - 异步并发数: {executor.async_concurrency}")
print(f"   - 线程池大小: {executor.thread_pool_size}")
print(f"   - CPU 密集型工作线程: {executor.cpu_intensive_workers}")
```

### 配置任务路由器

任务路由器负责分析输入任务并将它们路由到最合适的专业代理：

```python
from mini_agent.orchestration import TaskRouter

# 创建任务路由器
router = TaskRouter(
    strategy="hybrid",  # 混合策略，结合关键词匹配和负载均衡
    keyword_threshold=0.7,  # 关键词匹配阈值
    default_agent="coder"  # 默认代理
)

# 注册代理能力
router.register_agent_capabilities(
    agent_id="coder",
    keywords=["代码", "编程", "开发", "Python", "JavaScript", "调试", "重构"],
    description="专业编码助手，负责代码生成、审查、调试和重构"
)

router.register_agent_capabilities(
    agent_id="designer",
    keywords=["设计", "UI", "UX", "界面", "组件", "样式", "动画"],
    description="UI/UX 设计师，负责界面设计和交互设计"
)

router.register_agent_capabilities(
    agent_id="researcher",
    keywords=["研究", "分析", "调研", "文档", "报告", "趋势"],
    description="研究分析师，负责技术研究和文档编写"
)

router.register_agent_capabilities(
    agent_id="tester",
    keywords=["测试", "验证", "Bug", "质量", "自动化"],
    description="质量保证工程师，负责测试设计"
)

router.register_agent_capabilities(
    agent_id="deployer",
    keywords=["部署", "Docker", "CI/CD", "云", "服务器"],
    description="DevOps 工程师，负责部署和运维"
)

print("✅ 任务路由器配置完成")
```

---

## 单代理使用

### 基本使用模式

在某些场景下，您可能只需要使用单个专业代理来完成任务。以下是几种常见的单代理使用模式：

```python
from mini_agent import Agent
from mini_agent.orchestration.prompts import get_agent_prompt

# 创建编码代理
coder_agent = Agent(
    name="CoderAgent",
    model="claude-sonnet-4-20250514",
    system_prompt=get_agent_prompt("coder"),
    max_steps=50,
    workspace_dir="./workspace/coder",
    tools=["bash", "file_tools"]
)

# 执行简单任务
async def basic_usage_example():
    """基本使用示例"""
    
    # 任务 1: 代码生成
    task1 = "用 Python 实现一个快速排序算法，要求包含详细的注释"
    result1 = await coder_agent.run(task1)
    print(f"任务 1 完成: {result1['success']}")
    
    # 任务 2: 代码审查
    task2 = """
    请审查以下代码并提出改进建议：
    
    def calculate_average(numbers):
        total = 0
        count = 0
        for num in numbers:
            total += num
            count += 1
        return total / count if count > 0 else 0
    """
    result2 = await coder_agent.run(task2)
    print(f"任务 2 完成: {result2['success']}")

# 运行示例
import asyncio
asyncio.run(basic_usage_example())
```

### 专业代理配置

每种专业代理都有其独特的系统提示和工具配置，以适应不同的任务需求：

```python
from mini_agent.orchestration.prompts import (
    get_agent_prompt,
    create_agent_config,
    CODER_SYSTEM_PROMPT,
    DESIGNER_SYSTEM_PROMPT,
    RESEARCHER_SYSTEM_PROMPT,
    TESTER_SYSTEM_PROMPT,
    DEPLOYER_SYSTEM_PROMPT
)

# 方式 1: 使用预定义的代理提示
coder_prompt = get_agent_prompt("coder")
designer_prompt = get_agent_prompt("designer")
researcher_prompt = get_agent_prompt("researcher")

# 方式 2: 自定义代理配置
config = create_agent_config(
    agent_type="coder",
    custom_instructions="特别关注代码性能优化和安全性",
    additional_capabilities=["性能分析", "安全审计"]
)

# 方式 3: 直接使用系统提示模板
agent = Agent(
    name="CustomAgent",
    model="claude-sonnet-4-20250514",
    system_prompt=CODER_SYSTEM_PROMPT + "\n\n特别注意：优先考虑算法效率",
    max_steps=50,
    tools=["bash", "file_tools", "DelegateToAgentTool"]
)
```

### 工具使用

专业代理可以根据其配置使用不同的工具。以下是各类型代理的工具配置示例：

```python
from mini_agent.tools.file_tools import FileTools
from mini_agent.tools.bash import BashTools

# 编码代理工具配置
coder_tools = [
    "bash",  # 执行 Shell 命令
    "file_tools",  # 文件操作
    "code_analysis",  # 代码分析
    "debug_tools"  # 调试工具
]

# 设计代理工具配置
designer_tools = [
    "bash",
    "file_tools",
    "canvas_design",  # 画布设计
    "image_tools"  # 图片处理
]

# 研究代理工具配置
researcher_tools = [
    "bash",
    "file_tools",
    "web_search",  # 网络搜索
    "document_parser"  # 文档解析
]

# 测试代理工具配置
tester_tools = [
    "bash",
    "file_tools",
    "test_runner",  # 测试运行
    "coverage_analysis"  # 覆盖率分析
]

# 部署代理工具配置
deployer_tools = [
    "bash",
    "file_tools",
    "docker_tools",  # Docker 工具
    "kubernetes_tools"  # Kubernetes 工具
]
```

---

## 多代理协调

### 创建协调器

MultiAgentOrchestrator 是多代理系统的核心组件，负责管理所有专业代理的生命周期和任务分配：

```python
from mini_agent import Agent
from mini_agent.orchestration import (
    MultiAgentOrchestrator,
    OptimizedExecutor,
    TaskRouter,
    ResultAggregator
)
from mini_agent.orchestration.prompts import (
    get_coordinator_prompt,
    get_agent_prompt
)

# 创建专业代理
def create_specialized_agents():
    """创建所有专业代理"""
    
    agents = {}
    
    # 编码代理
    agents["coder"] = Agent(
        name="CoderAgent",
        model="claude-sonnet-4-20250514",
        system_prompt=get_agent_prompt("coder"),
        max_steps=50,
        workspace_dir="./workspace/coder",
        tools=["bash", "file_tools"]
    )
    
    # 设计代理
    agents["designer"] = Agent(
        name="DesignerAgent",
        model="claude-sonnet-4-20250514",
        system_prompt=get_agent_prompt("designer"),
        max_steps=50,
        workspace_dir="./workspace/designer",
        tools=["bash", "file_tools", "canvas_design"]
    )
    
    # 研究代理
    agents["researcher"] = Agent(
        name="ResearcherAgent",
        model="claude-sonnet-4-20250514",
        system_prompt=get_agent_prompt("researcher"),
        max_steps=50,
        workspace_dir="./workspace/researcher",
        tools=["bash", "file_tools", "web_search"]
    )
    
    # 测试代理
    agents["tester"] = Agent(
        name="TesterAgent",
        model="claude-sonnet-4-20250514",
        system_prompt=get_agent_prompt("tester"),
        max_steps=50,
        workspace_dir="./workspace/tester",
        tools=["bash", "file_tools"]
    )
    
    # 部署代理
    agents["deployer"] = Agent(
        name="DeployerAgent",
        model="claude-sonnet-4-20250514",
        system_prompt=get_agent_prompt("deployer"),
        max_steps=50,
        workspace_dir="./workspace/deployer",
        tools=["bash", "file_tools", "docker_tools"]
    )
    
    return agents

# 创建协调器
def create_orchestrator():
    """创建多代理协调器"""
    
    # 创建专业代理
    agents = create_specialized_agents()
    
    # 创建协调器
    orchestrator = MultiAgentOrchestrator(
        main_agent_name="MainCoordinator",
        sub_agents=agents,
        coordinator_model="claude-sonnet-4-20250514",
        coordinator_system_prompt=get_coordinator_prompt(),
        enable_parallel_execution=True,
        max_concurrent_agents=5,
        default_timeout=300
    )
    
    return orchestrator

# 初始化协调器
orchestrator = create_orchestrator()
print("✅ 多代理协调器创建成功")
```

### 任务委派

协调器支持多种任务委派方式，包括直接委派和批量委派：

```python
from mini_agent.tools.orchestration import (
    DelegateToAgentTool,
    BatchDelegateTool,
    RequestStatusTool,
    GatherResultsTool
)

# 方式 1: 通过协调器方法委派任务
async def delegation_examples():
    """任务委派示例"""
    
    orchestrator = create_orchestrator()
    
    # 直接委派任务给特定代理
    result1 = await orchestrator.delegate_task(
        agent_id="coder",
        task="实现一个 RESTful API，用户管理功能",
        context={"project": "user-service"},
        timeout=120
    )
    
    # 委派任务并等待结果
    result2 = await orchestrator.delegate_with_result(
        agent_id="designer",
        task="设计一个用户登录界面的原型",
        timeout=180
    )
    
    return result1, result2

# 方式 2: 使用委派工具
async def tool_delegation_example():
    """使用工具委派任务"""
    
    # 创建委派工具
    delegate_tool = DelegateToAgentTool(orchestrator=orchestrator)
    
    # 执行委派
    result = await delegate_tool.execute(
        agent_id="coder",
        task="编写单元测试",
        priority="high",
        timeout=300
    )
    
    return result

# 方式 3: 批量委派任务
async def batch_delegation_example():
    """批量任务委派示例"""
    
    # 创建批量委派工具
    batch_delegate = BatchDelegateTool(orchestrator=orchestrator)
    
    # 定义批量任务
    tasks = [
        {
            "agent_id": "coder",
            "task": "实现用户认证模块",
            "priority": "high"
        },
        {
            "agent_id": "coder",
            "task": "实现用户数据 CRUD",
            "priority": "high"
        },
        {
            "agent_id": "designer",
            "task": "设计用户界面",
            "priority": "medium"
        },
        {
            "agent_id": "tester",
            "task": "编写集成测试",
            "priority": "medium"
        }
    ]
    
    # 并行执行所有任务
    results = await batch_delegate.execute(
        tasks=tasks,
        parallel=True,
        timeout_per_task=300
    )
    
    return results
```

### 状态查询与结果收集

协调器提供了丰富的状态查询和结果收集功能：

```python
from mini_agent.tools.orchestration import (
    RequestStatusTool,
    GatherResultsTool
)
from mini_agent.tools.communication import ShareContextTool

# 查询代理状态
async def status_query_example():
    """状态查询示例"""
    
    status_tool = RequestStatusTool(orchestrator=orchestrator)
    
    # 获取所有代理状态
    all_status = await status_tool.execute(agent_id="all")
    print(f"所有代理状态: {all_status}")
    
    # 获取特定代理状态
    coder_status = await status_tool.execute(agent_id="coder")
    print(f"编码代理状态: {coder_status}")
    
    # 获取运行任务数量
    running_count = status_tool.get_running_task_count("coder")
    print(f"编码代理运行中任务数: {running_count}")

# 收集结果
async def result_collection_example():
    """结果收集示例"""
    
    gather_tool = GatherResultsTool(orchestrator=orchestrator)
    
    # 收集所有已完成的结果
    all_results = await gather_tool.execute(
        agent_id="all",
        status="completed",
        timeout=60
    )
    
    # 收集特定代理的结果
    coder_results = await gather_tool.execute(
        agent_id="coder",
        status="completed",
        timeout=30
    )
    
    # 收集所有结果（包含失败）
    all_results_with_failures = await gather_tool.execute(
        agent_id="all",
        status="all",
        include_errors=True
    )
    
    return all_results, coder_results

# 上下文共享
async def context_sharing_example():
    """上下文共享示例"""
    
    share_tool = ShareContextTool(orchestrator=orchestrator)
    
    # 共享上下文
    await share_tool.execute(
        from_agent="coder",
        to_agents=["tester", "deployer"],
        context={
            "project_structure": {...},
            "api_endpoints": [...],
            "deployment_config": {...}
        }
    )
    
    # 获取共享上下文
    context = share_tool.get_shared_context(agent_id="tester")
    print(f"收到的上下文: {context}")
```

### 完整工作流程示例

以下是一个完整的软件开发工作流程示例：

```python
import asyncio
from mini_agent import Agent
from mini_agent.orchestration import (
    MultiAgentOrchestrator,
    OptimizedExecutor
)
from mini_agent.orchestration.prompts import (
    get_coordinator_prompt,
    get_agent_prompt
)

async def full_development_workflow():
    """
    完整的软件开发工作流程示例
    
    这个示例展示了一个典型的 Web 应用开发流程：
    1. 需求分析（研究员）
    2. 系统设计（设计师）
    3. 代码实现（编码员）
    4. 测试验证（测试员）
    5. 部署上线（部署员）
    """
    
    print("🚀 启动完整开发工作流程")
    
    # 创建执行器
    executor = OptimizedExecutor(
        default_mode="auto",
        max_concurrent_tasks=10
    )
    
    # 创建代理
    agents = {
        "researcher": Agent(
            name="Researcher",
            model="claude-sonnet-4-20250514",
            system_prompt=get_agent_prompt("researcher"),
            max_steps=30,
            workspace_dir="./workspace/researcher"
        ),
        "designer": Agent(
            name="Designer",
            model="claude-sonnet-4-20250514",
            system_prompt=get_agent_prompt("designer"),
            max_steps=30,
            workspace_dir="./workspace/designer"
        ),
        "coder": Agent(
            name="Coder",
            model="claude-sonnet-4-20250514",
            system_prompt=get_agent_prompt("coder"),
            max_steps=50,
            workspace_dir="./workspace/coder"
        ),
        "tester": Agent(
            name="Tester",
            model="claude-sonnet-4-20250514",
            system_prompt=get_agent_prompt("tester"),
            max_steps=30,
            workspace_dir="./workspace/tester"
        ),
        "deployer": Agent(
            name="Deployer",
            model="claude-sonnet-4-20250514",
            system_prompt=get_agent_prompt("deployer"),
            max_steps=30,
            workspace_dir="./workspace/deployer"
        )
    }
    
    # 创建协调器
    orchestrator = MultiAgentOrchestrator(
        main_agent_name="ProjectManager",
        sub_agents=agents,
        coordinator_model="claude-sonnet-4-20250514",
        coordinator_system_prompt=get_coordinator_prompt()
    )
    
    # 阶段 1: 需求分析
    print("\n📋 阶段 1: 需求分析")
    requirements = await orchestrator.delegate_with_result(
        agent_id="researcher",
        task="""
        分析以下需求并生成详细的技术需求文档：
        
        项目名称：任务管理应用
        功能需求：
        - 用户注册和登录
        - 创建、编辑、删除任务
        - 任务分类和标签
        - 任务搜索和过滤
        - 团队协作功能
        
        请生成包含功能规格、技术选型建议、开发计划的文档。
        """
    )
    print(f"✅ 需求分析完成: {requirements.success}")
    
    # 阶段 2: 系统设计
    print("\n🎨 阶段 2: 系统设计")
    design = await orchestrator.delegate_with_result(
        agent_id="designer",
        task="""
        基于需求文档，设计任务管理应用的系统架构和界面：
        
        1. 系统架构设计（前端、后端、数据库）
        2. 数据库schema设计
        3. API 接口设计
        4. UI/UX 设计原型
        5. 技术选型建议
        
        提供详细的设计文档和架构图。
        """
    )
    print(f"✅ 系统设计完成: {design.success}")
    
    # 阶段 3: 代码实现
    print("\n💻 阶段 3: 代码实现")
    implementation = await orchestrator.delegate_with_result(
        agent_id="coder",
        task="""
        实现任务管理应用的核心功能：
        
        1. 用户认证模块（JWT）
        2. 任务 CRUD API
        3. 任务分类和标签功能
        4. 搜索和过滤功能
        
        代码要求：
        - 使用 Python Flask 框架
        - 使用 SQLite 数据库
        - 遵循 PEP 8 规范
        - 包含单元测试
        """
    )
    print(f"✅ 代码实现完成: {implementation.success}")
    
    # 阶段 4: 测试验证
    print("\n🧪 阶段 4: 测试验证")
    testing = await orchestrator.delegate_with_result(
        agent_id="tester",
        task="""
        对任务管理应用进行全面的测试：
        
        1. 单元测试（覆盖核心功能）
        2. 集成测试（API 接口测试）
        3. 端到端测试（用户流程测试）
        4. 性能测试（并发请求测试）
        
        生成测试报告，包含测试覆盖率、发现的问题和建议。
        """
    )
    print(f"✅ 测试验证完成: {testing.success}")
    
    # 阶段 5: 部署上线
    print("\n🚀 阶段 5: 部署上线")
    deployment = await orchestrator.delegate_with_result(
        agent_id="deployer",
        task="""
        部署任务管理应用到生产环境：
        
        1. 编写 Dockerfile 和 docker-compose.yml
        2. 配置 CI/CD 流水线
        3. 部署到云服务器
        4. 配置域名和 SSL 证书
        5. 设置监控和日志
        
        提供部署文档和运维手册。
        """
    )
    print(f"✅ 部署上线完成: {deployment.success}")
    
    # 收集所有结果
    print("\n📊 工作流程总结")
    results = await orchestrator.gather_all_results(timeout=60)
    
    print(f"总任务数: {results.total_count}")
    print(f"成功: {results.success_count}")
    print(f"失败: {results.failure_count}")
    print(f"成功率: {results.success_rate:.2%}")
    
    return results

# 运行完整工作流程
if __name__ == "__main__":
    results = asyncio.run(full_development_workflow())
```

---

## 高级场景

### 并行执行模式

当多个任务之间没有依赖关系时，可以并行执行以提高效率：

```python
from mini_agent.orchestration import OptimizedExecutor

async def parallel_execution_example():
    """并行执行示例"""
    
    # 创建执行器
    executor = OptimizedExecutor(
        default_mode="parallel",
        async_concurrency=50,
        timeout_per_task=300,
        retry_on_failure=True,
        max_retries=3
    )
    
    # 定义独立任务
    async def task1():
        # 获取最新技术新闻
        return {"source": "tech_news", "data": [...]}
    
    async def task2():
        # 获取股票数据
        return {"source": "stock_data", "data": [...]}
    
    async def task3():
        # 发送邮件通知
        return {"source": "email", "status": "sent"}
    
    # 并行执行
    results = await executor.execute_parallel(
        tasks=[task1, task2, task3],
        wait_for_all=True,
        timeout=120
    )
    
    print(f"成功: {len(results.successful)}")
    print(f"失败: {len(results.failed)}")
    
    return results

async def batch_parallel_example():
    """批量并行执行示例"""
    
    executor = OptimizedExecutor(
        default_mode="parallel",
        async_concurrency=100,
        timeout_per_task=60
    )
    
    # 批量任务列表
    tasks = [
        {"type": "code_review", "file": "src/app.py"},
        {"type": "code_review", "file": "src/utils.py"},
        {"type": "code_review", "file": "src/models.py"},
        {"type": "documentation", "file": "README.md"},
        {"type": "documentation", "file": "docs/API.md"}
    ]
    
    # 并行执行所有任务
    results = await executor.execute_batch(
        tasks=tasks,
        task_processor=process_task,
        max_concurrent=20
    )
    
    return results

async def process_task(task):
    """任务处理函数"""
    # 模拟任务处理
    await asyncio.sleep(1)
    return {"result": f"Processed {task}"}
```

### 混合执行模式

混合执行模式可以根据任务类型自动选择最优的执行策略：

```python
from mini_agent.orchestration import OptimizedExecutor

async def hybrid_execution_example():
    """混合执行模式示例"""
    
    executor = OptimizedExecutor(
        default_mode="auto",  # 自动选择执行模式
        async_concurrency=200,
        thread_pool_size=16,
        cpu_intensive_workers=8,
        timeout_per_task=300
    )
    
    # I/O 密集型任务（自动使用异步）
    async def io_task_1():
        # API 调用
        await asyncio.sleep(2)
        return {"type": "io", "result": "API response"}
    
    async def io_task_2():
        # 文件读取
        await asyncio.sleep(1)
        return {"type": "io", "result": "File content"}
    
    # CPU 密集型任务（自动使用线程池）
    def cpu_task_1():
        # 数据处理
        import time
        time.sleep(2)
        return {"type": "cpu", "result": "Computed"}
    
    def cpu_task_2():
        # 算法计算
        import time
        time.sleep(3)
        return {"type": "cpu", "result": "Calculated"}
    
    # 混合任务执行
    results = await executor.execute_hybrid(
        async_tasks=[io_task_1, io_task_2],
        cpu_tasks=[cpu_task_1, cpu_task_2],
        timeout=120
    )
    
    print(f"异步任务结果: {len(results.async_results)}")
    print(f"CPU 任务结果: {len(results.cpu_results)}")
    
    return results
```

### 流水线执行模式

流水线模式适用于多阶段数据处理场景：

```python
from mini_agent.orchestration import OptimizedExecutor

async def pipeline_example():
    """流水线执行示例"""
    
    executor = OptimizedExecutor(
        default_mode="auto",
        timeout_per_task=300
    )
    
    # 定义流水线阶段
    async def extract(data):
        """提取阶段：从源数据中提取信息"""
        await asyncio.sleep(1)
        return {"extracted": [item for item in data if item]}
    
    async def transform(data):
        """转换阶段：数据清洗和转换"""
        await asyncio.sleep(2)
        return {"transformed": [item.upper() for item in data.get("extracted", [])]}
    
    async def load(data):
        """加载阶段：保存处理后的数据"""
        await asyncio.sleep(1)
        return {"loaded": len(data.get("transformed", [])), "items": data.get("transformed", [])}
    
    async def analyze(data):
        """分析阶段：数据分析"""
        await asyncio.sleep(2)
        return {"analyzed": len(data.get("loaded", [])), "unique_items": set(data.get("loaded", []).get("items", []))}
    
    # 执行流水线
    result = await executor.execute_pipeline(
        data=["apple", "banana", "cherry", "", "date", "elderberry"],
        stages=[extract, transform, load, analyze],
        checkpoint_interval=1
    )
    
    print(f"最终结果: {result}")
    
    return result

# ETL 流水线示例
async def etl_pipeline_example():
    """ETL 数据处理流水线"""
    
    executor = OptimizedExecutor(
        default_mode="auto",
        timeout_per_task=600
    )
    
    # ETL 阶段
    stages = [
        # Extract - 从数据库提取数据
        lambda ctx: extract_from_database(ctx),
        # Transform - 数据清洗和转换
        lambda ctx: transform_data(ctx),
        # Load - 加载到数据仓库
        lambda ctx: load_to_warehouse(ctx),
        # Validate - 数据验证
        lambda ctx: validate_data(ctx),
        # Report - 生成报告
        lambda ctx: generate_report(ctx)
    ]
    
    result = await executor.execute_pipeline(
        data={"source": "production_db", "date_range": "2024-01"},
        stages=stages,
        checkpoint_interval=1
    )
    
    return result
```

### 多代理协作示例

以下是一个复杂的多代理协作场景：

```python
import asyncio
from mini_agent import Agent
from mini_agent.orchestration import (
    MultiAgentOrchestrator,
    OptimizedExecutor
)
from mini_agent.orchestration.prompts import (
    get_coordinator_prompt,
    get_agent_prompt
)
from mini_agent.tools.communication import (
    ShareContextTool,
    BroadcastMessageTool
)

async def complex_collaboration_example():
    """
    复杂的多代理协作示例
    
    场景：一个数据分析项目，需要多个代理协作完成数据收集、分析和可视化。
    """
    
    print("🔬 启动复杂协作场景：数据分析项目")
    
    # 创建执行器
    executor = OptimizedExecutor(
        default_mode="auto",
        max_concurrent_tasks=20
    )
    
    # 创建专业代理
    agents = {
        "researcher": Agent(
            name="DataResearcher",
            model="claude-sonnet-4-20250514",
            system_prompt=get_agent_prompt("researcher"),
            max_steps=30
        ),
        "coder": Agent(
            name="DataEngineer",
            model="claude-sonnet-4-20250514",
            system_prompt=get_agent_prompt("coder"),
            max_steps=50
        ),
        "designer": Agent(
            name="VisualizationDesigner",
            model="claude-sonnet-4-20250514",
            system_prompt=get_agent_prompt("designer"),
            max_steps=30
        )
    }
    
    # 创建协调器
    orchestrator = MultiAgentOrchestrator(
        main_agent_name="ProjectLead",
        sub_agents=agents,
        coordinator_model="claude-sonnet-4-20250514",
        coordinator_system_prompt=get_coordinator_prompt()
    )
    
    # 创建通信工具
    share_tool = ShareContextTool(orchestrator=orchestrator)
    broadcast_tool = BroadcastMessageTool(orchestrator=orchestrator)
    
    # 阶段 1: 并行数据收集
    print("\n📊 阶段 1: 并行数据收集")
    
    data_sources = [
        {"source": "API", "endpoint": "/users", "count": 1000},
        {"source": "API", "endpoint": "/transactions", "count": 10000},
        {"source": "Database", "query": "SELECT * FROM events", "count": 5000}
    ]
    
    # 并行收集数据
    data_results = await orchestrator.delegate_parallel(
        agent_id="researcher",
        tasks=[
            {"task": f"从 {ds['source']} 收集数据: {ds['endpoint']}", "context": ds}
            for ds in data_sources
        ],
        timeout=300
    )
    
    # 共享收集的数据
    await share_tool.execute(
        from_agent="researcher",
        to_agents=["coder"],
        context={"collected_data": data_results}
    )
    
    # 阶段 2: 数据处理（编码代理）
    print("\n🔧 阶段 2: 数据处理")
    
    processing_result = await orchestrator.delegate_with_result(
        agent_id="coder",
        task="""
        处理收集的数据：
        
        1. 数据清洗（去除重复、缺失值处理）
        2. 数据转换（格式统一、类型转换）
        3. 特征工程（提取有用特征）
        4. 数据聚合（按维度汇总）
        
        输出处理后的数据集和分析代码。
        """
    )
    
    # 共享处理结果
    await share_tool.execute(
        from_agent="coder",
        to_agents=["designer"],
        context={"processed_data": processing_result}
    )
    
    # 阶段 3: 可视化设计（设计代理）
    print("\n🎨 阶段 3: 可视化设计")
    
    viz_result = await orchestrator.delegate_with_result(
        agent_id="designer",
        task="""
        为处理后的数据设计可视化方案：
        
        1. 用户增长趋势图
        2. 交易分布热力图
        3. 事件漏斗分析图
        4. 交互式仪表板设计
        
        使用 Python (Matplotlib/Plotly) 实现可视化代码。
        """
    )
    
    # 广播完成消息
    await broadcast_tool.execute(
        message="数据分析项目完成！所有数据已处理，可视化已生成。",
        recipients=["all"]
    )
    
    # 收集最终结果
    final_results = await orchestrator.gather_all_results(timeout=60)
    
    print(f"\n📈 项目完成总结")
    print(f"   总任务数: {final_results.total_count}")
    print(f"   成功率: {final_results.success_rate:.2%}")
    
    return final_results
```

### 错误处理与重试

多代理系统提供了完善的错误处理和重试机制：

```python
from mini_agent.orchestration import OptimizedExecutor

async def error_handling_example():
    """错误处理示例"""
    
    executor = OptimizedExecutor(
        default_mode="auto",
        retry_on_failure=True,
        max_retries=3,
        timeout_per_task=60
    )
    
    # 可能失败的任务
    async def unreliable_task(task_id):
        """模拟可能失败的任务"""
        import random
        if random.random() < 0.3:  # 30% 失败率
            raise Exception(f"Task {task_id} failed temporarily")
        return {"task_id": task_id, "status": "success"}
    
    # 执行带重试的任务
    result = await executor.execute_with_retry(
        task=unreliable_task,
        args=(1,),
        max_retries=3,
        backoff_factor=2,
        retry_on=(ConnectionError, TimeoutError)
    )
    
    print(f"任务结果: {result.success}")
    print(f"重试次数: {result.retry_count}")
    
    # 批量执行带错误处理
    tasks = [
        {"task": unreliable_task, "args": (i,), "priority": i % 3}
        for i in range(10)
    ]
    
    batch_results = await executor.execute_batch_with_fallback(
        tasks=tasks,
        fallback_strategy="retry_important_first",
        max_total_retries=20
    )
    
    print(f"成功: {batch_results.success_count}")
    print(f"失败: {batch_results.failure_count}")
    print(f"使用重试: {batch_results.retry_count}")
    
    return batch_results
```

---

## 最佳实践

### 1. 代理设计原则

在设计多代理系统时，应遵循以下原则：

**单一职责原则**：每个专业代理应该只负责一种类型的任务。例如，编码代理专注于代码编写，不应该处理设计或部署任务。这种分离使得系统更易于维护和扩展。当某个代理出现问题时，可以快速定位和修复，而不会影响其他代理的正常运行。

**能力注册**：在启动系统之前，应该清楚地定义每个代理的能力范围。这包括它们擅长的任务类型、可以使用的工具、以及任何特定的限制条件。清晰的能力定义有助于任务路由器做出正确的路由决策，提高整个系统的效率。

**上下文隔离**：不同的代理应该有独立的工作空间，避免相互干扰。每个代理的 workspace_dir 应该设置在不同的目录下，这样可以防止文件冲突，同时也便于跟踪和管理各个代理的工作成果。

```python
# 推荐的代理配置方式
AGENT_CONFIGS = {
    "coder": {
        "name": "专业编码助手",
        "workspace_dir": "./workspace/coder",
        "capabilities": ["代码生成", "代码审查", "调试"],
        "tools": ["bash", "file_tools"],
        "model": "claude-sonnet-4-20250514",
        "temperature": 0.3
    },
    "designer": {
        "name": "UI/UX 设计师",
        "workspace_dir": "./workspace/designer",
        "capabilities": ["界面设计", "交互设计"],
        "tools": ["bash", "file_tools", "canvas_design"],
        "model": "claude-sonnet-4-20250514",
        "temperature": 0.7
    }
}
```

### 2. 任务分配策略

任务分配是影响系统性能的关键因素。以下是一些最佳实践：

**智能路由**：使用混合路由策略，结合关键词匹配和负载均衡。关键词匹配可以确保任务被分配给最适合的代理，而负载均衡则可以避免某个代理过载。这种组合可以在任务匹配度和系统效率之间取得平衡。

**优先级处理**：为不同类型的任务设置优先级，确保关键任务得到优先处理。在资源有限的情况下，高优先级任务应该被优先调度。这可以通过任务队列和优先级调度器来实现。

**批量优化**：当有多个相似任务时，使用批量处理可以显著提高效率。批量处理可以减少代理切换的开销，同时允许代理复用上下文信息，提高处理速度。

```python
from mini_agent.orchestration import TaskRouter

# 配置智能路由
router = TaskRouter(
    strategy="hybrid",
    keyword_threshold=0.7,
    load_balancing_window=10,
    enable_priority=True
)

# 注册代理能力（带权重）
router.register_agent_capabilities(
    agent_id="coder",
    keywords=["代码", "开发", "API"],
    weight=1.0  # 权重越高，分配优先级越高
)

router.register_agent_capabilities(
    agent_id="tester",
    keywords=["测试", "验证", "Bug"],
    weight=0.8
)
```

### 3. 资源管理

有效的资源管理对于系统的稳定性和性能至关重要：

**并发控制**：不要同时运行太多的并发任务。过多的并发会导致系统资源耗尽，反而降低整体效率。建议根据系统能力设置合理的并发上限，并使用信号量来控制同时执行的任务数量。

**超时设置**：为每个任务设置合理的超时时间。长时间运行的任务可能会占用资源，影响其他任务的执行。超时机制可以确保系统能够及时释放资源，处理后续任务。

**内存管理**：定期清理不再需要的数据和上下文信息。长时间运行的系统可能会积累大量中间数据，导致内存占用过高。通过定期清理，可以保持系统的稳定性和响应速度。

```python
from mini_agent.orchestration import OptimizedExecutor

# 优化的执行器配置
executor = OptimizedExecutor(
    default_mode="auto",
    async_concurrency=100,  # 异步并发数
    thread_pool_size=16,    # 线程池大小
    cpu_intensive_workers=8, # CPU 密集型工作线程
    timeout_per_task=300,    # 单任务超时
    max_concurrent_tasks=50, # 最大并发任务数
    memory_limit_mb=4096,   # 内存限制
    retry_on_failure=True,
    max_retries=3
)
```

### 4. 错误恢复

健壮的错误处理机制是生产系统的重要组成部分：

**重试策略**：对于临时性错误（如网络问题、服务暂时不可用等），应该实现自动重试机制。重试策略应该包括指数退避，避免对目标服务造成过大压力。

**降级处理**：当某个代理不可用时，系统应该能够将任务路由到其他可用的代理，或者暂时将任务放入队列等待。降级处理可以提高系统的可用性和容错能力。

**监控告警**：实现完善的监控和告警机制，及时发现和处理异常情况。监控指标应该包括任务成功率、响应时间、资源使用情况等关键指标。

```python
from mini_agent.orchestration import MultiAgentOrchestrator
from mini_agent.tools.orchestration import RequestStatusTool

# 创建带错误处理的协调器
orchestrator = MultiAgentOrchestrator(
    main_agent_name="MainCoordinator",
    sub_agents=sub_agents,
    coordinator_model="claude-sonnet-4-20250514",
    coordinator_system_prompt=get_coordinator_prompt(),
    enable_fallback=True,  # 启用降级处理
    health_check_interval=60  # 健康检查间隔
)

# 定期检查代理状态
async def monitor_agents():
    """监控代理健康状态"""
    status_tool = RequestStatusTool(orchestrator=orchestrator)
    
    while True:
        all_status = await status_tool.execute(agent_id="all")
        
        for agent_id, status in all_status.items():
            if status.health_score < 0.5:  # 健康分数低于 0.5
                print(f"⚠️ 警告: {agent_id} 健康状态异常: {status.health_score}")
                # 触发告警或降级处理
        
        await asyncio.sleep(60)  # 每分钟检查一次
```

### 5. 性能优化

以下是一些性能优化的技巧：

**连接池复用**：对于需要频繁访问外部服务（如数据库、API 等）的代理，应该使用连接池复用连接，避免频繁创建和销毁连接的开销。这可以显著减少网络延迟和资源消耗。

**缓存策略**：对于不经常变化的数据，可以实现缓存机制来减少重复计算和请求。缓存可以显著提高系统响应速度，特别是对于频繁访问的元数据和配置信息。

**批量操作**：尽可能使用批量操作代替单个操作。例如，批量写入数据库、批量发送请求等。批量操作可以减少网络往返次数，提高吞吐量。

```python
from functools import lru_cache
import asyncio

# 缓存配置信息
@lru_cache(maxsize=128)
def get_agent_config(agent_id: str) -> dict:
    """获取代理配置（带缓存）"""
    # 模拟从配置文件读取
    return load_config_from_file(f"config/agents/{agent_id}.yaml")

# 批量操作示例
async def batch_file_operations():
    """批量文件操作示例"""
    
    # 批量读取
    async def batch_read(file_paths):
        results = await asyncio.gather(
            *[read_file(path) for path in file_paths],
            return_exceptions=True
        )
        return results
    
    # 批量写入
    async def batch_write(file_data_map):
        tasks = [
            write_file(path, data)
            for path, data in file_data_map.items()
        ]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    # 使用示例
    files = ["file1.txt", "file2.txt", "file3.txt"]
    contents = await batch_read(files)
    
    processed = {f: content.upper() for f, content in zip(files, contents)}
    await batch_write(processed)
```

### 6. 安全考虑

在设计多代理系统时，安全性是至关重要的：

**输入验证**：对所有输入进行验证和清理，防止注入攻击和恶意输入。每个代理在处理任务之前都应该验证输入的有效性和安全性。

**权限控制**：实施最小权限原则，每个代理只应该拥有完成其任务所必需的最小权限。这可以限制潜在损害的范围，防止单个代理被 compromise 后影响整个系统。

**审计日志**：记录所有重要操作和决策，便于追踪和审计。审计日志应该包括任务提交、代理调用、敏感操作等信息。

```python
import hashlib
import json
from datetime import datetime

class SecurityManager:
    """安全管理器"""
    
    def __init__(self):
        self.audit_log = []
    
    def validate_input(self, task: str) -> bool:
        """验证输入安全性"""
        dangerous_patterns = [
            "rm -rf", "delete *", "format disk",
            "sudo", "chmod 777", "eval("
        ]
        
        for pattern in dangerous_patterns:
            if pattern.lower() in task.lower():
                raise SecurityError(f"检测到危险指令: {pattern}")
        
        return True
    
    def log_operation(self, agent_id: str, operation: str, details: dict):
        """记录操作审计日志"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id,
            "operation": operation,
            "details_hash": hashlib.sha256(
                json.dumps(details).encode()
            ).hexdigest()[:16]
        }
        self.audit_log.append(log_entry)
    
    def get_audit_log(self, agent_id: str = None):
        """获取审计日志"""
        if agent_id:
            return [log for log in self.audit_log if log["agent_id"] == agent_id]
        return self.audit_log

# 使用安全管理器
security = SecurityManager()

async def secure_task_execution(orchestrator, task: str, agent_id: str):
    """安全地执行任务"""
    
    # 验证输入
    security.validate_input(task)
    
    # 执行任务
    result = await orchestrator.delegate_with_result(
        agent_id=agent_id,
        task=task
    )
    
    # 记录审计日志
    security.log_operation(
        agent_id=agent_id,
        operation="task_execution",
        details={"task_hash": hashlib.sha256(task.encode()).hexdigest()[:16]}
    )
    
    return result
```

---

## 总结

本文档涵盖了 Mini-Agent 多代理协调系统的完整使用指南，从基础配置到高级场景，提供了丰富的示例代码和最佳实践建议。通过遵循这些指南，开发者可以快速构建高效、可靠的多代理系统。

**核心要点回顾**：

- 使用 OptimizedExecutor 的自动模式可以获得最佳性能
- 合理配置任务路由器可以提高任务分配准确性
- 利用并行执行可以显著提升处理效率
- 完善的错误处理和监控机制是生产系统的必要保障
- 安全性设计应该贯穿整个系统的设计和实现

如需更多帮助，请参考其他文档或提交 Issue。

---

**文档版本**: 0.6.0  
**最后更新**: 2024  
**维护者**: Mini-Agent Team
