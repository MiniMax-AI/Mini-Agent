"""
Multi-Agent Orchestrator - 多代理协调器

允许一个 Agent 作为"大脑"协调多个专业子代理完成任务。
该模块提供了完整的层级式多代理协作架构，支持任务分解、
并行执行和结果整合。

主要功能：
- 主代理协调多个专业子代理
- 智能任务分配和路由
- 支持并行和顺序执行模式
- 完善的协调工具集
- 上下文共享和状态同步

作者：Mini-Agent Team
版本：0.6.0
"""

from typing import Optional, Dict, List, Any, Union
from pathlib import Path
import asyncio
import logging

from ..agent import Agent
from ..llm import LLMClient
from .executor import OptimizedExecutor, Task
from .task_router import TaskRouter
from .result_aggregator import ResultAggregator
from .prompts import get_coordinator_prompt

logger = logging.getLogger(__name__)


class MultiAgentOrchestrator:
    """
    多代理协调器 - 主代理的增强版本
    
    该类是整个多代理系统的核心入口，负责管理主代理和所有
    子代理的生命周期，协调任务的分配和执行，以及结果的整合。
    
    核心职责：
    1. 管理子代理的创建、配置和生命周期
    2. 提供任务执行接口，支持单任务和批量任务
    3. 协调器工具的注册和使用
    4. 共享上下文和任务历史的管理
    5. 执行结果的收集和聚合
    
    使用示例：
        orchestrator = MultiAgentOrchestrator(
            main_llm_client=llm_client,
            sub_agent_configs=sub_configs,
            workspace_dir="./workspace",
            max_steps=50
        )
        
        # 执行单个复杂任务
        result = await orchestrator.execute_task(
            task="开发一个Web应用",
            context={"需求文档": "..."}
        )
        
        # 并行执行多个独立任务
        results = await orchestrator.execute_parallel_tasks(tasks)
    
    Attributes:
        main_agent: 主代理实例，负责全局协调
        sub_agents: 子代理字典，键为代理名称
        executor: 优化执行器，负责任务的实际执行
        task_router: 任务路由器，负责任务分配
        result_aggregator: 结果聚合器，负责结果整合
        shared_context: 共享上下文，跨代理共享信息
        task_history: 任务历史，记录所有执行的任务
    """
    
    def __init__(
        self,
        main_llm_client: LLMClient,
        sub_agent_configs: List[Dict[str, Any]],
        workspace_dir: str = "./workspace",
        max_steps: int = 50,
        default_timeout: int = 300,
        enable_logging: bool = True
    ):
        """
        初始化多代理协调器
        
        Args:
            main_llm_client: 主代理使用的 LLM 客户端
            sub_agent_configs: 子代理配置列表，每个配置包含：
                - name: 子代理名称（唯一标识）
                - system_prompt: 系统提示词
                - tools: 可选，工具列表
                - workspace: 可选，工作目录
                - max_steps: 可选，最大步数
            workspace_dir: 主工作目录
            max_steps: 主代理最大步数
            default_timeout: 默认任务超时时间（秒）
            enable_logging: 是否启用日志记录
        """
        self.main_llm_client = main_llm_client
        self.sub_agent_configs = sub_agent_configs
        self.default_timeout = default_timeout
        self.enable_logging = enable_logging
        
        # 初始化日志
        if enable_logging:
            self._setup_logging()
        
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
        
        logger.info(f"多代理协调器初始化完成，子代理数量: {len(self.sub_agents)}")
    
    def _setup_logging(self):
        """配置日志记录"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('MultiAgentOrchestrator')
    
    def _create_sub_agents(self, base_workspace: str):
        """
        创建所有配置的子代理
        
        该方法根据配置列表创建对应的子代理实例，每个子代理
        拥有独立的工作目录和工具集。
        
        Args:
            base_workspace: 基础工作目录路径
        """
        for config in self.sub_agent_configs:
            name = config["name"]
            
            # 获取或创建工作目录
            workspace = Path(base_workspace) / name
            workspace.mkdir(parents=True, exist_ok=True)
            
            # 获取工具列表
            tools = config.get("tools", [])
            
            # 创建子代理
            agent = Agent(
                llm_client=self.main_llm_client,
                system_prompt=config["system_prompt"],
                tools=tools,
                max_steps=config.get("max_steps", 30),
                workspace_dir=str(workspace),
            )
            
            self.sub_agents[name] = agent
            logger.debug(f"子代理 '{name}' 创建成功")
    
    def _create_main_agent(self, workspace_dir: str, max_steps: int) -> Agent:
        """
        创建主代理（协调器）
        
        主代理负责全局规划和协调，拥有完整的协调工具集。
        
        Args:
            workspace_dir: 工作目录
            max_steps: 最大步数
        
        Returns:
            Agent: 主代理实例
        """
        workspace = Path(workspace_dir) / "coordinator"
        workspace.mkdir(parents=True, exist_ok=True)
        
        # 生成协调器提示词
        coordinator_prompt = get_coordinator_prompt(
            agent_names=list(self.sub_agents.keys()),
            agent_descriptions=self._generate_agent_descriptions(),
        )
        
        # 创建协调工具
        coordination_tools = self._create_coordination_tools()
        
        agent = Agent(
            llm_client=self.main_llm_client,
            system_prompt=coordinator_prompt,
            tools=coordination_tools,
            max_steps=max_steps,
            workspace_dir=str(workspace),
        )
        
        logger.info("主代理创建成功")
        return agent
    
    def _generate_agent_descriptions(self) -> str:
        """
        生成子代理描述文本
        
        从每个子代理的系统提示中提取描述信息，生成
        供协调器使用的代理描述列表。
        
        Returns:
            str: 格式化的代理描述文本
        """
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
        """
        创建协调工具列表
        
        初始化所有用于代理间协调的工具实例。
        
        Returns:
            List: 协调工具实例列表
        """
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
        
        tools = [
            DelegateToAgentTool(agents=self.sub_agents),
            BatchDelegateTool(orchestrator=self),
            RequestStatusTool(agents=self.sub_agents),
            GatherResultsTool(agents=self.sub_agents),
            ShareContextTool(orchestrator=self),
            BroadcastMessageTool(agents=self.sub_agents),
        ]
        
        logger.debug(f"协调工具创建完成，共 {len(tools)} 个工具")
        return tools
    
    def add_sub_agent(self, name: str, config: Dict[str, Any]):
        """
        动态添加子代理
        
        支持在运行时动态添加新的子代理，系统会自动
        更新相关的执行器和路由器配置。
        
        Args:
            name: 子代理名称
            config: 子代理配置字典
        
        Raises:
            ValueError: 如果代理名称已存在
        """
        if name in self.sub_agents:
            raise ValueError(f"子代理 '{name}' 已存在")
        
        # 获取或创建工作目录
        workspace = Path(config.get("workspace", f"./workspace/{name}"))
        workspace.mkdir(parents=True, exist_ok=True)
        
        # 创建子代理
        agent = Agent(
            llm_client=self.main_llm_client,
            system_prompt=config["system_prompt"],
            tools=config.get("tools", []),
            max_steps=config.get("max_steps", 30),
            workspace_dir=str(workspace),
        )
        
        self.sub_agents[name] = agent
        # 重新初始化执行器
        self.executor = OptimizedExecutor(self.sub_agents)
        
        logger.info(f"子代理 '{name}' 添加成功")
    
    def remove_sub_agent(self, name: str):
        """
        移除子代理
        
        从系统中移除指定名称的子代理，释放相关资源。
        
        Args:
            name: 要移除的子代理名称
        
        Raises:
            KeyError: 如果代理名称不存在
        """
        if name not in self.sub_agents:
            raise KeyError(f"子代理 '{name}' 不存在")
        
        del self.sub_agents[name]
        # 重新初始化执行器
        self.executor = OptimizedExecutor(self.sub_agents)
        
        logger.info(f"子代理 '{name}' 移除成功")
    
    def get_sub_agent(self, name: str) -> Agent:
        """
        获取子代理实例
        
        Args:
            name: 子代理名称
        
        Returns:
            Agent: 子代理实例
        
        Raises:
            KeyError: 如果代理名称不存在
        """
        if name not in self.sub_agents:
            raise KeyError(f"子代理 '{name}' 不存在")
        
        return self.sub_agents[name]
    
    async def execute_task(
        self,
        task: str,
        context: Dict[str, Any] = None,
        mode: str = "auto"
    ) -> Dict[str, Any]:
        """
        执行单个复杂任务
        
        这是协调器的主要接口之一，用户通过此方法提交复杂任务，
        协调器会分析任务并协调子代理完成。
        
        Args:
            task: 任务描述
            context: 可选上下文信息
            mode: 执行模式（auto/parallel/sequential/thread）
        
        Returns:
            Dict[str, Any]: 执行结果，包含：
                - success: 是否成功
                - result: 执行结果
                - task_history: 任务历史
                - metadata: 元数据
        """
        logger.info(f"开始执行任务: {task[:100]}...")
        
        # 更新共享上下文
        if context:
            self.shared_context.update(context)
        
        # 添加上下文到主代理
        if context:
            context_msg = self._format_context(context)
            self.main_agent.add_user_message(context_msg)
        
        # 添加任务
        self.main_agent.add_user_message(task)
        
        # 执行主代理循环
        try:
            result = await self.main_agent.run()
            
            # 更新任务历史
            self.task_history.append({
                "task": task,
                "context": context,
                "success": True,
            })
            
            logger.info("任务执行成功")
            
            return {
                "success": True,
                "result": result,
                "task_history": self.task_history[-1],
                "metadata": {
                    "mode": mode,
                    "sub_agents_used": self._detect_used_agents(),
                }
            }
            
        except Exception as e:
            logger.error(f"任务执行失败: {str(e)}")
            
            self.task_history.append({
                "task": task,
                "context": context,
                "success": False,
                "error": str(e),
            })
            
            return {
                "success": False,
                "result": None,
                "task_history": self.task_history[-1],
                "error": str(e),
            }
    
    async def execute_parallel_tasks(
        self,
        tasks: List[Dict[str, Any]],
        mode: str = "auto"
    ) -> Dict[str, Any]:
        """
        并行执行多个独立任务
        
        适用于任务之间没有依赖关系，可以并行处理的场景。
        系统会自动选择最优的执行模式。
        
        Args:
            tasks: 任务列表，每个任务包含：
                - agent: 指定执行的子代理名称
                - task: 任务描述
                - context: 可选上下文
                - priority: 可选优先级
            mode: 执行模式
        
        Returns:
            Dict[str, Any]: 聚合后的执行结果
        """
        logger.info(f"开始并行执行 {len(tasks)} 个任务")
        
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
        
        # 转换为字典格式返回
        result_dict = {
            "overall_status": aggregated.overall_status.value,
            "total": aggregated.total_count,
            "success": aggregated.success_count,
            "failed": aggregated.failed_count,
            "results": aggregated.results,
            "summary": aggregated.summary,
            "task_breakdown": aggregated.metadata.get("task_breakdown", {}),
        }
        
        logger.info(f"并行任务执行成功: {aggregated.success_count}/{aggregated.total_count}")
        
        return result_dict
    
    async def delegate_task(
        self,
        agent_name: str,
        task: str,
        context: Dict[str, Any] = None,
        timeout: int = None
    ) -> Dict[str, Any]:
        """
        直接委托任务给指定子代理
        
        这是一个简化接口，适用于需要直接控制任务分配的场景。
        
        Args:
            agent_name: 子代理名称
            task: 任务描述
            context: 可选上下文
            timeout: 可选超时时间
        
        Returns:
            Dict[str, Any]: 执行结果
        """
        agent = self.get_sub_agent(agent_name)
        
        # 添加上下文
        if context:
            context_msg = self._format_context(context)
            agent.add_user_message(context_msg)
        
        # 添加任务
        agent.add_user_message(task)
        
        # 执行
        try:
            timeout = timeout or self.default_timeout
            result = await asyncio.wait_for(
                agent.run(),
                timeout=timeout,
            )
            
            return {
                "success": True,
                "agent": agent_name,
                "result": result,
            }
            
        except asyncio.TimeoutError:
            return {
                "success": False,
                "agent": agent_name,
                "error": f"Task timed out after {timeout}s",
            }
        except Exception as e:
            return {
                "success": False,
                "agent": agent_name,
                "error": str(e),
            }
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """
        格式化上下文信息
        
        将字典格式的上下文转换为可读文本。
        
        Args:
            context: 上下文字典
        
        Returns:
            str: 格式化后的文本
        """
        lines = ["[Shared Context]"]
        for key, value in context.items():
            lines.append(f"- {key}: {value}")
        return "\n".join(lines)
    
    def _detect_used_agents(self) -> List[str]:
        """
        检测本次执行中使用了哪些子代理
        
        通过分析主代理的消息历史来确定子代理的使用情况。
        
        Returns:
            List[str]: 使用的子代理名称列表
        """
        used_agents = []
        
        for msg in self.main_agent.messages:
            if hasattr(msg, 'content') and isinstance(msg.content, str):
                # 检测是否调用了子代理
                for agent_name in self.sub_agents.keys():
                    if agent_name in msg.content.lower():
                        if agent_name not in used_agents:
                            used_agents.append(agent_name)
        
        return used_agents
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取协调器当前状态
        
        返回系统的整体状态信息，用于监控和调试。
        
        Returns:
            Dict[str, Any]: 状态信息字典
        """
        return {
            "sub_agent_count": len(self.sub_agents),
            "sub_agent_names": list(self.sub_agents.keys()),
            "task_history_count": len(self.task_history),
            "shared_context_keys": list(self.shared_context.keys()),
            "main_agent_messages": len(self.main_agent.messages),
        }
    
    def get_sub_agent_status(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有子代理的状态
        
        Returns:
            Dict[str, Dict]: 各子代理的状态信息
        """
        status = {}
        for name, agent in self.sub_agents.items():
            status[name] = {
                "message_count": len(agent.messages),
                "workspace": str(agent.workspace_dir),
                "token_usage": getattr(agent, 'api_total_tokens', 0),
            }
        return status
    
    def clear_context(self):
        """清空共享上下文"""
        self.shared_context.clear()
        logger.info("共享上下文已清空")
    
    def clear_history(self):
        """清空任务历史"""
        self.task_history.clear()
        logger.info("任务历史已清空")


def create_orchestrator(
    main_llm_client: LLMClient,
    sub_agent_configs: List[Dict[str, Any]],
    workspace_dir: str = "./workspace",
    max_steps: int = 50,
) -> MultiAgentOrchestrator:
    """
    创建多代理协调系统的便捷函数
    
    这是一个工厂函数，简化协调器的创建过程。
    
    Args:
        main_llm_client: 主代理使用的 LLM 客户端
        sub_agent_configs: 子代理配置列表
        workspace_dir: 工作目录
        max_steps: 最大步数
    
    Returns:
        MultiAgentOrchestrator: 协调器实例
    
    Example:
        orchestrator = create_orchestrator(
            main_llm_client=llm,
            sub_agent_configs=[
                {"name": "coder", "system_prompt": CODER_PROMPT},
                {"name": "designer", "system_prompt": DESIGNER_PROMPT},
            ]
        )
    """
    return MultiAgentOrchestrator(
        main_llm_client=main_llm_client,
        sub_agent_configs=sub_agent_configs,
        workspace_dir=workspace_dir,
        max_steps=max_steps,
    )
