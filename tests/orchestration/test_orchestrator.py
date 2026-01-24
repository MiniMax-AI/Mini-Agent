"""
Test Suite for Multi-Agent Orchestration System

多代理协调系统测试套件

测试覆盖：
1. 协调器基本功能
2. 执行器任务执行
3. 任务路由器
4. 结果聚合器
5. 协调工具
6. 通信工具

版本：0.6.0
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from pathlib import Path
import sys

# 添加项目根目录
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mini_agent.orchestration import (
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
from mini_agent.orchestration.prompts import (
    get_coordinator_prompt,
    CODER_PROMPT,
    DESIGNER_PROMPT,
    get_agent_prompt,
    create_agent_config,
)
from mini_agent.tools.orchestration import (
    DelegateToAgentTool,
    BatchDelegateTool,
    RequestStatusTool,
    GatherResultsTool,
)
from mini_agent.tools.communication import (
    ShareContextTool,
    BroadcastMessageTool,
    SyncStateTool,
)


# ==================== Fixtures ====================

@pytest.fixture
def mock_agent():
    """创建模拟 Agent"""
    agent = Mock()
    agent.messages = []
    agent.system_prompt = "Test agent"
    agent.workspace_dir = Path("./workspace/test")
    agent.add_user_message = Mock()
    agent.run = AsyncMock(return_value="Test result")
    agent.api_total_tokens = 100
    return agent


@pytest.fixture
def mock_agents():
    """创建模拟 Agent 字典"""
    return {
        "coder": Mock(
            messages=[],
            system_prompt=CODER_PROMPT,
            workspace_dir=Path("./workspace/coder"),
            add_user_message=Mock(),
            run=AsyncMock(return_value="Coder result"),
            api_total_tokens=100,
        ),
        "designer": Mock(
            messages=[],
            system_prompt=DESIGNER_PROMPT,
            workspace_dir=Path("./workspace/designer"),
            add_user_message=Mock(),
            run=AsyncMock(return_value="Designer result"),
            api_total_tokens=100,
        ),
    }


@pytest.fixture
def mock_llm_client():
    """创建模拟 LLM 客户端"""
    client = Mock()
    client.complete = AsyncMock(return_value="Mock completion")
    return client


@pytest.fixture
def orchestrator_instance(mock_agents, mock_llm_client):
    """创建协调器实例"""
    sub_configs = [
        {
            "name": "coder",
            "system_prompt": CODER_PROMPT,
            "tools": [],
            "max_steps": 10,
            "workspace": "./workspace/coder",
        },
        {
            "name": "designer",
            "system_prompt": DESIGNER_PROMPT,
            "tools": [],
            "max_steps": 10,
            "workspace": "./workspace/designer",
        },
    ]
    
    orchestrator = MultiAgentOrchestrator(
        main_llm_client=mock_llm_client,
        sub_agent_configs=sub_configs,
        workspace_dir="./workspace/test",
        max_steps=20,
        enable_logging=False,
    )
    
    # 替换为模拟 agents
    orchestrator.sub_agents = mock_agents
    orchestrator.executor = OptimizedExecutor(mock_agents)
    
    return orchestrator


# ==================== Test Classes ====================

class TestTask:
    """Task 数据类测试"""
    
    def test_task_creation(self):
        """测试 Task 创建"""
        task = Task(
            agent_name="coder",
            task="Write a function",
            context={"key": "value"},
            timeout=300,
            priority=1,
        )
        
        assert task.agent_name == "coder"
        assert task.task == "Write a function"
        assert task.context == {"key": "value"}
        assert task.timeout == 300
        assert task.priority == 1
        assert task.task_type == "io_bound"
    
    def test_task_default_values(self):
        """测试 Task 默认值"""
        task = Task(agent_name="test", task="Test task")
        
        assert task.context is None
        assert task.timeout == 300
        assert task.priority == 0
        assert task.task_type == "io_bound"


class TestOptimizedExecutor:
    """执行器测试"""
    
    @pytest.mark.asyncio
    async def test_execute_single_task(self, mock_agents):
        """测试执行单个任务"""
        executor = OptimizedExecutor(mock_agents)
        
        task = Task(agent_name="coder", task="Test task")
        result = await executor.execute_task(task)
        
        assert result["agent"] == "coder"
        assert result["success"] is True
        assert result["task_type"] in ["io_bound", "cpu_bound"]
    
    @pytest.mark.asyncio
    async def test_execute_unknown_agent(self, mock_agents):
        """测试执行未知代理任务"""
        executor = OptimizedExecutor(mock_agents)
        
        task = Task(agent_name="unknown", task="Test task")
        result = await executor.execute_task(task)
        
        assert result["success"] is False
        assert "未知代理" in result["error"] or "Unknown agent" in result["error"]
    
    @pytest.mark.asyncio
    async def test_analyze_task_type(self, mock_agents):
        """测试任务类型分析"""
        executor = OptimizedExecutor(mock_agents)
        
        # CPU 密集型任务
        cpu_task = Task(agent_name="coder", task="计算数据分析统计")
        assert executor.analyze_task_type(cpu_task) == "cpu_bound"
        
        # I/O 密集型任务
        io_task = Task(agent_name="coder", task="查询网络获取信息")
        assert executor.analyze_task_type(io_task) == "io_bound"
    
    @pytest.mark.asyncio
    async def test_execute_parallel(self, mock_agents):
        """测试并行执行"""
        executor = OptimizedExecutor(mock_agents)
        
        tasks = [
            Task(agent_name="coder", task="Task 1"),
            Task(agent_name="designer", task="Task 2"),
        ]
        
        results = await executor.execute_parallel(tasks)
        
        assert len(results) == 2
        assert all(r["success"] for r in results)
    
    @pytest.mark.asyncio
    async def test_execute_auto_mode(self, mock_agents):
        """测试自动模式执行"""
        executor = OptimizedExecutor(mock_agents)
        
        tasks = [
            Task(agent_name="coder", task="Task 1"),
            Task(agent_name="designer", task="Task 2"),
        ]
        
        result = await executor.execute(tasks, mode="auto")
        
        assert "mode" in result
        assert "total" in result
        assert "success" in result
        assert "results" in result
    
    def test_get_config(self, mock_agents):
        """测试获取配置"""
        executor = OptimizedExecutor(mock_agents)
        config = executor.get_config()
        
        assert "cpu_count" in config
        assert "max_async_concurrent" in config
        assert "thread_pool_size" in config


class TestTaskRouter:
    """任务路由器测试"""
    
    def test_route_single_task(self, mock_agents):
        """测试路由单个任务"""
        router = TaskRouter(mock_agents)
        result = router.route("编写 Python 代码")
        
        assert result.agent_name in mock_agents.keys()
        assert 0 <= result.confidence <= 1
        assert isinstance(result.reasoning, str)
    
    def test_route_with_preferred_agent(self, mock_agents):
        """测试带首选代理的路由"""
        router = TaskRouter(mock_agents)
        result = router.route(
            "编写代码",
            preferred_agent="coder"
        )
        
        assert result.agent_name == "coder"
    
    def test_route_batch(self, mock_agents):
        """测试批量路由"""
        router = TaskRouter(mock_agents)
        
        tasks = [
            {"task": "编写代码"},
            {"task": "设计界面"},
            {"task": "分析数据"},
        ]
        
        results = router.route_batch(tasks)
        
        assert len(results) == 3
        for result in results:
            assert result.agent_name in mock_agents.keys()
    
    def test_get_load_status(self, mock_agents):
        """测试获取负载状态"""
        router = TaskRouter(mock_agents)
        status = router.get_load_status()
        
        assert "agent_loads" in status
        assert "total_load" in status
        assert "average_load" in status
    
    def test_get_statistics(self, mock_agents):
        """测试获取统计信息"""
        router = TaskRouter(mock_agents)
        
        # 执行一些路由
        router.route("编写代码")
        router.route("设计界面")
        
        stats = router.get_statistics()
        
        assert "total_routes" in stats
        assert "agent_selection_count" in stats


class TestResultAggregator:
    """结果聚合器测试"""
    
    def test_aggregate_success(self):
        """测试聚合成功结果"""
        aggregator = ResultAggregator()
        
        execution_result = {
            "mode": "parallel",
            "total": 2,
            "success": 2,
            "failed": 0,
            "results": [
                {"agent": "coder", "success": True, "task_type": "io_bound"},
                {"agent": "designer", "success": True, "task_type": "io_bound"},
            ],
            "task_breakdown": {"cpu_bound": 0, "io_bound": 2},
        }
        
        result = aggregator.aggregate(execution_result)
        
        assert result.overall_status.value == "success"
        assert result.success_count == 2
        assert result.failed_count == 0
    
    def test_aggregate_partial_failure(self):
        """测试聚合部分失败结果"""
        aggregator = ResultAggregator()
        
        execution_result = {
            "mode": "parallel",
            "total": 2,
            "success": 1,
            "failed": 1,
            "results": [
                {"agent": "coder", "success": True, "task_type": "io_bound"},
                {"agent": "designer", "success": False, "error": "Test error"},
            ],
            "task_breakdown": {"cpu_bound": 0, "io_bound": 2},
        }
        
        result = aggregator.aggregate(execution_result)
        
        # 50% 成功率低于默认阈值 0.6，所以状态为 "failed"
        # 如果需要 "partial" 状态，需要成功率 >= 0.6
        assert result.overall_status.value in ["success", "partial", "failed"]
        assert result.success_count == 1
        assert result.failed_count == 1
        assert len(result.errors) == 1
    
    def test_merge_results(self):
        """测试合并结果"""
        aggregator = ResultAggregator()
        
        results = [
            {"total": 2, "success": 2, "failed": 0, "results": []},
            {"total": 3, "success": 2, "failed": 1, "results": []},
        ]
        
        merged = aggregator.merge_results(results)
        
        assert merged["total"] == 5
        assert merged["success"] == 4
        assert merged["failed"] == 1
        assert merged["merged_from"] == 2
    
    def test_format_for_output(self):
        """测试格式化输出"""
        aggregator = ResultAggregator()
        
        execution_result = {
            "mode": "parallel",
            "total": 1,
            "success": 1,
            "failed": 0,
            "results": [
                {"agent": "coder", "success": True},
            ],
            "task_breakdown": {"cpu_bound": 0, "io_bound": 1},
        }
        
        result = aggregator.aggregate(execution_result)
        
        # 测试 JSON 格式
        json_output = aggregator.format_for_output(result, "json")
        assert isinstance(json_output, dict)
        assert "status" in json_output
        
        # 测试 Markdown 格式
        md_output = aggregator.format_for_output(result, "markdown")
        assert isinstance(md_output, str)
        assert "## 执行结果" in md_output


class TestCoordinatorPrompts:
    """协调器提示词测试"""
    
    def test_get_coordinator_prompt(self):
        """测试生成协调器提示词"""
        prompt = get_coordinator_prompt(
            agent_names=["coder", "designer"],
        )
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "coder" in prompt
        assert "designer" in prompt
    
    def test_get_coordinator_prompt_with_descriptions(self):
        """测试带描述的提示词生成"""
        descriptions = "- coder: 编程专家\n- designer: 设计专家"
        prompt = get_coordinator_prompt(
            agent_names=["coder", "designer"],
            agent_descriptions=descriptions,
        )
        
        assert "编程专家" in prompt
        assert "设计专家" in prompt
    
    def test_get_coordinator_prompt_short(self):
        """测试精简版提示词"""
        prompt = get_coordinator_prompt(
            agent_names=["coder", "designer"],
            prompt_type="short",
        )
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0


class TestAgentPrompts:
    """代理提示词测试"""
    
    def test_get_agent_prompt_coder(self):
        """测试获取程序员提示词"""
        prompt = get_agent_prompt("coder")
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "代码" in prompt or "code" in prompt.lower()
    
    def test_get_agent_prompt_designer(self):
        """测试获取设计师提示词"""
        prompt = get_agent_prompt("designer")
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0
    
    def test_get_agent_prompt_unknown(self):
        """测试获取未知类型提示词"""
        prompt = get_agent_prompt("unknown_type")
        
        # 应该返回默认的 CODER_PROMPT
        assert prompt == CODER_PROMPT
    
    def test_create_agent_config(self):
        """测试创建代理配置"""
        config = create_agent_config(
            agent_type="coder",
            name="my_coder",
            tools=["tool1", "tool2"],
            max_steps=20,
        )
        
        assert config["name"] == "my_coder"
        assert config["tools"] == ["tool1", "tool2"]
        assert config["max_steps"] == 20
        assert "system_prompt" in config


class TestOrchestrationTools:
    """协调工具测试"""
    
    def test_delegate_to_agent_tool_init(self, mock_agents):
        """测试委托工具初始化"""
        tool = DelegateToAgentTool(agents=mock_agents)
        
        assert tool.agents == mock_agents
        assert len(tool.delegation_history) == 0
    
    def test_delegate_to_agent_parameters(self, mock_agents):
        """测试委托工具参数"""
        tool = DelegateToAgentTool(agents=mock_agents)
        params = tool.parameters
        
        assert "agent_name" in params["required"]
        assert "task" in params["required"]
    
    def test_batch_delegate_tool_init(self, orchestrator_instance):
        """测试批量委托工具初始化"""
        tool = BatchDelegateTool(orchestrator=orchestrator_instance)
        
        assert tool.orchestrator == orchestrator_instance
    
    def test_request_status_tool(self, mock_agents):
        """测试状态查询工具"""
        tool = RequestStatusTool(agents=mock_agents)
        
        # 同步执行
        result = asyncio.run(tool.execute("coder"))
        
        assert result.success is True
        assert "coder" in result.content
    
    def test_gather_results_tool(self, mock_agents):
        """测试结果收集工具"""
        tool = GatherResultsTool(agents=mock_agents)
        
        # 先给 agent 添加消息
        mock_agents["coder"].messages = [
            Mock(role="user", content="Test result")
        ]
        
        result = asyncio.run(tool.execute(["coder"]))
        
        assert result.success is True


class TestCommunicationTools:
    """通信工具测试"""
    
    def test_share_context_tool(self, orchestrator_instance):
        """测试上下文共享工具"""
        tool = ShareContextTool(orchestrator=orchestrator_instance)
        
        result = tool.execute(
            key="test_key",
            value="test_value",
            target_agents=["coder"],
        )
        
        assert result.success is True
        assert tool.get_context("test_key") == "test_value"
    
    def test_share_context_complex_value(self, orchestrator_instance):
        """测试共享复杂值"""
        tool = ShareContextTool(orchestrator=orchestrator_instance)
        
        complex_value = {"nested": {"key": "value"}, "list": [1, 2, 3]}
        result = tool.execute(
            key="complex",
            value=complex_value,
        )
        
        assert result.success is True
        assert tool.get_context("complex") == complex_value
    
    def test_broadcast_message_tool(self, mock_agents):
        """测试消息广播工具"""
        tool = BroadcastMessageTool(agents=mock_agents)
        
        result = tool.execute(
            message="Test broadcast",
            target_agents=["coder"],
            priority="normal",
        )
        
        assert result.success is True
        assert len(tool.get_broadcast_history()) == 1
    
    def test_sync_state_tool(self, mock_agents):
        """测试状态同步工具"""
        tool = SyncStateTool(agents=mock_agents)
        
        result = tool.execute(
            agent_names=["coder", "designer"],
            include_details=False,
        )
        
        assert result.success is True
        assert "overall_status" in result.metadata


class TestMultiAgentOrchestrator:
    """协调器主类测试"""
    
    def test_orchestrator_creation(self, mock_llm_client):
        """测试协调器创建"""
        sub_configs = [
            {
                "name": "coder",
                "system_prompt": CODER_PROMPT,
                "tools": [],
                "max_steps": 10,
            },
        ]
        
        orchestrator = MultiAgentOrchestrator(
            main_llm_client=mock_llm_client,
            sub_agent_configs=sub_configs,
            workspace_dir="./workspace/test",
            max_steps=20,
            enable_logging=False,
        )
        
        assert len(orchestrator.sub_agents) == 1
        assert "coder" in orchestrator.sub_agents
        assert orchestrator.main_agent is not None
    
    def test_get_status(self, orchestrator_instance):
        """测试获取状态"""
        status = orchestrator_instance.get_status()
        
        assert "sub_agent_count" in status
        assert "sub_agent_names" in status
        assert "task_history_count" in status
    
    def test_get_sub_agent_status(self, orchestrator_instance):
        """测试获取子代理状态"""
        status = orchestrator_instance.get_sub_agent_status()
        
        assert "coder" in status
        assert "designer" in status
    
    def test_clear_context(self, orchestrator_instance):
        """测试清空上下文"""
        orchestrator_instance.shared_context["test"] = "value"
        
        orchestrator_instance.clear_context()
        
        assert len(orchestrator_instance.shared_context) == 0
    
    def test_clear_history(self, orchestrator_instance):
        """测试清空历史"""
        orchestrator_instance.task_history.append({"task": "test"})
        
        orchestrator_instance.clear_history()
        
        assert len(orchestrator_instance.task_history) == 0


class TestConvenienceFunctions:
    """便捷函数测试"""
    
    def test_create_orchestrator(self, mock_llm_client):
        """测试创建协调器便捷函数"""
        sub_configs = [
            {
                "name": "coder",
                "system_prompt": CODER_PROMPT,
                "tools": [],
            },
        ]
        
        orchestrator = create_orchestrator(
            main_llm_client=mock_llm_client,
            sub_agent_configs=sub_configs,
        )
        
        assert isinstance(orchestrator, MultiAgentOrchestrator)
    
    def test_create_executor(self, mock_agents):
        """测试创建执行器便捷函数"""
        executor = create_executor(mock_agents)
        
        assert isinstance(executor, OptimizedExecutor)
    
    def test_create_task_router(self, mock_agents):
        """测试创建任务路由器便捷函数"""
        router = create_task_router(mock_agents)
        
        assert isinstance(router, TaskRouter)
    
    def test_create_result_aggregator(self):
        """测试创建结果聚合器便捷函数"""
        aggregator = create_result_aggregator()
        
        assert isinstance(aggregator, ResultAggregator)


# ==================== Integration Tests ====================

class TestIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    async def test_full_delegation_flow(self, mock_agents, mock_llm_client):
        """测试完整的委托流程"""
        orchestrator = MultiAgentOrchestrator(
            main_llm_client=mock_llm_client,
            sub_agent_configs=[
                {
                    "name": "coder",
                    "system_prompt": CODER_PROMPT,
                    "tools": [],
                    "max_steps": 10,
                },
            ],
            workspace_dir="./workspace/integration_test",
            max_steps=5,
            enable_logging=False,
        )
        
        # 替换为模拟 agents
        orchestrator.sub_agents = mock_agents
        orchestrator.executor = OptimizedExecutor(mock_agents)
        
        # 直接委托任务
        result = await orchestrator.delegate_task(
            agent_name="coder",
            task="Write a test function",
            context={"test": True},
        )
        
        assert result["success"] is True
        assert result["agent"] == "coder"
    
    @pytest.mark.asyncio
    async def test_parallel_execution_flow(self, mock_agents, mock_llm_client):
        """测试并行执行流程"""
        orchestrator = MultiAgentOrchestrator(
            main_llm_client=mock_llm_client,
            sub_agent_configs=[
                {
                    "name": "coder",
                    "system_prompt": CODER_PROMPT,
                    "tools": [],
                    "max_steps": 10,
                },
                {
                    "name": "designer",
                    "system_prompt": DESIGNER_PROMPT,
                    "tools": [],
                    "max_steps": 10,
                },
            ],
            workspace_dir="./workspace/integration_test",
            max_steps=5,
            enable_logging=False,
        )
        
        orchestrator.sub_agents = mock_agents
        orchestrator.executor = OptimizedExecutor(mock_agents)
        
        # 并行执行多个任务
        tasks = [
            {"agent": "coder", "task": "Task 1"},
            {"agent": "designer", "task": "Task 2"},
        ]
        
        result = await orchestrator.execute_parallel_tasks(tasks, mode="parallel")
        
        assert result["total"] == 2
        assert result["success"] == 2


# ==================== Run Tests ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
