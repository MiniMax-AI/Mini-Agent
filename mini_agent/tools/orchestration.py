"""
Orchestration Tools - 协调工具集

提供主代理协调子代理执行所需的工具。
这些工具是主代理（大脑）与子代理之间通信的基础设施。

可用工具：
- DelegateToAgentTool：任务委托工具
- BatchDelegateTool：批量委托工具
- RequestStatusTool：状态查询工具
- GatherResultsTool：结果收集工具

版本：0.6.0
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import asyncio
import logging

from .base import Tool, ToolResult

logger = logging.getLogger(__name__)


@dataclass
class DelegationContext:
    """
    委托上下文
    
    记录一次任务委托的完整信息。
    
    Attributes:
        task_id: 任务唯一标识
        agent_name: 目标代理名称
        task_description: 任务描述
        context: 上下文信息
        status: 当前状态
        result: 执行结果
    """
    task_id: str
    agent_name: str
    task_description: str
    context: Optional[Dict] = None
    status: str = "pending"
    result: Any = None


class DelegateToAgentTool(Tool):
    """将任务委托给指定子代理的工具"""
    
    name = "delegate_to_agent"
    description = """将任务委托给指定的子代理执行。

这是多代理系统中最核心的工具，允许主代理将任务分配给最适合的专业子代理。

使用场景：
- 需要特定领域的专业知识时
- 任务可以分解为独立子任务时
- 需要并行处理多个任务时（结合 batch_delegate）

重要说明：
1. 提供清晰具体的任务描述
2. 包含必要的上下文信息
3. 设置合理的超时时间
4. 等待结果返回后继续

参数：
- agent_name: 子代理名称（必须在可用代理列表中）
- task: 要执行的具体任务描述
- context: 可选的上下文信息
- timeout: 可选的超时时间（秒），默认 300 秒"""

    def __init__(self, agents: Dict[str, "Agent"]):
        """
        初始化委托工具
        
        Args:
            agents: 可用的子代理字典
        """
        self.agents = agents
        self.delegation_history: List[DelegationContext] = []
        self._task_counter = 0
    
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
                    "default": 300,
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
        """
        执行任务委托
        
        Args:
            agent_name: 目标子代理名称
            task: 任务描述
            context: 上下文信息
            timeout: 超时时间
        
        Returns:
            ToolResult: 执行结果
        """
        # 验证代理存在
        if agent_name not in self.agents:
            return ToolResult(
                success=False,
                content="",
                error=f"未知代理: {agent_name}。可用代理: {list(self.agents.keys())}",
            )
        
        agent = self.agents[agent_name]
        
        # 生成任务 ID
        self._task_counter += 1
        task_id = f"task_{self._task_counter}_{agent_name}"
        
        # 创建委托上下文
        delegation = DelegationContext(
            task_id=task_id,
            agent_name=agent_name,
            task_description=task,
            context=context,
            status="running",
        )
        self.delegation_history.append(delegation)
        
        logger.info(f"开始委托任务到 {agent_name}: {task[:100]}...")
        
        # 添加上下文
        if context:
            context_msg = self._format_context(context)
            agent.add_user_message(context_msg)
        
        # 添加任务
        agent.add_user_message(task)
        
        # 执行任务
        timeout = timeout or 300
        try:
            result = await asyncio.wait_for(
                agent.run(),
                timeout=timeout,
            )
            
            # 更新委托状态
            delegation.status = "completed"
            delegation.result = result
            
            # 提取结果预览
            history = getattr(agent, 'messages', [])
            result_preview = self._extract_result_preview(history)
            
            logger.info(f"任务 {task_id} 执行成功")
            
            return ToolResult(
                success=True,
                content=result,
                metadata={
                    "task_id": task_id,
                    "agent_name": agent_name,
                    "result_preview": result_preview,
                    "status": "completed",
                },
            )
            
        except asyncio.TimeoutError:
            delegation.status = "timeout"
            logger.warning(f"任务 {task_id} 超时")
            
            return ToolResult(
                success=False,
                content="",
                error=f"任务在 {timeout} 秒后超时",
                metadata={
                    "task_id": task_id,
                    "agent_name": agent_name,
                    "status": "timeout",
                },
            )
        except Exception as e:
            delegation.status = "error"
            delegation.result = str(e)
            logger.error(f"任务 {task_id} 执行错误: {str(e)}")
            
            return ToolResult(
                success=False,
                content="",
                error=f"代理执行失败: {str(e)}",
                metadata={
                    "task_id": task_id,
                    "agent_name": agent_name,
                    "status": "error",
                    "error_type": type(e).__name__,
                },
            )
    
    def _format_context(self, context: Dict) -> str:
        """
        格式化上下文信息
        
        Args:
            context: 上下文字典
        
        Returns:
            str: 格式化后的文本
        """
        lines = ["[Shared Context]"]
        for key, value in context.items():
            lines.append(f"- {key}: {value}")
        return "\n".join(lines)
    
    def _extract_result_preview(self, history: List) -> str:
        """
        从历史中提取结果预览
        
        Args:
            history: 消息历史
        
        Returns:
            str: 结果预览文本
        """
        if not history:
            return ""
        
        for msg in reversed(history):
            if hasattr(msg, 'role') and msg.role in ("assistant", "user"):
                content = msg.content
                if isinstance(content, str) and content:
                    return content[:200] + "..." if len(content) > 200 else content
        
        return ""
    
    def get_delegation_history(self) -> List[Dict]:
        """
        获取委托历史
        
        Returns:
            List: 委托历史列表
        """
        return [
            {
                "task_id": d.task_id,
                "agent_name": d.agent_name,
                "task_description": d.task_description,
                "status": d.status,
            }
            for d in self.delegation_history
        ]


class BatchDelegateTool(Tool):
    """批量委托任务给多个子代理的工具"""
    
    name = "batch_delegate"
    description = """批量委托任务给多个子代理并行执行。

这是实现真正并行的关键工具，允许同时将多个独立任务分配给不同的子代理。

使用场景：
- 有多个独立任务需要同时处理
- 任务之间没有依赖关系
- 需要最大化并行效率
- 批量数据处理

执行策略：
- parallel=true：所有任务同时开始（推荐用于独立任务）
- parallel=false：任务按顺序执行（用于有依赖的任务）

参数：
- tasks: 任务列表，每个任务包含 agent_name 和 task
- parallel: 是否并行执行（默认 true）

重要提示：
- 确保任务之间没有依赖关系
- 考虑系统资源限制
- 设置合理的超时时间"""

    def __init__(self, orchestrator: "MultiAgentOrchestrator"):
        """
        初始化批量委托工具
        
        Args:
            orchestrator: 协调器实例
        """
        self.orchestrator = orchestrator
        self.batch_history: List[Dict] = []
        self._batch_counter = 0
    
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
                            "agent_name": {
                                "type": "string",
                                "description": "子代理名称",
                            },
                            "task": {
                                "type": "string",
                                "description": "任务描述",
                            },
                            "context": {
                                "type": "object",
                                "description": "上下文信息",
                            },
                            "priority": {
                                "type": "integer",
                                "description": "任务优先级",
                                "default": 0,
                            },
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
        """
        执行批量委托
        
        Args:
            tasks: 任务列表
            parallel: 是否并行执行
        
        Returns:
            ToolResult: 执行结果
        """
        # 生成批次 ID
        self._batch_counter += 1
        batch_id = f"batch_{self._batch_counter}"
        
        logger.info(f"开始批量委托，批次 {batch_id}，任务数: {len(tasks)}")
        
        # 转换任务格式
        from ..orchestration.executor import Task
        
        task_objects = [
            Task(
                agent_name=t["agent_name"],
                task=t["task"],
                context=t.get("context"),
                priority=t.get("priority", 0),
            )
            for t in tasks
        ]
        
        # 选择执行模式
        mode = "parallel" if parallel else "sequential"
        
        # 执行
        try:
            result = await self.orchestrator.executor.execute(task_objects, mode)
            
            # 记录批次历史
            self.batch_history.append({
                "batch_id": batch_id,
                "task_count": len(tasks),
                "mode": mode,
                "success": result.get("success", 0),
                "failed": result.get("failed", 0),
            })
            
            logger.info(
                f"批次 {batch_id} 完成，成功: {result.get('success')}/{result.get('total')}"
            )
            
            return ToolResult(
                success=result.get("success", 0) > 0,
                content=str(result),
                metadata={
                    "batch_id": batch_id,
                    "mode": mode,
                    "total": result.get("total"),
                    "success": result.get("success"),
                    "failed": result.get("failed"),
                    "task_breakdown": result.get("task_breakdown"),
                },
            )
            
        except Exception as e:
            logger.error(f"批次 {batch_id} 执行错误: {str(e)}")
            
            return ToolResult(
                success=False,
                content="",
                error=f"批量执行失败: {str(e)}",
                metadata={
                    "batch_id": batch_id,
                    "error_type": type(e).__name__,
                },
            )


class RequestStatusTool(Tool):
    """查询子代理状态的工具"""
    
    name = "request_agent_status"
    description = """查询指定子代理的当前状态和进度。

用于监控子代理的执行状态，包括：
- 消息数量
- 工作空间位置
- Token 使用情况
- 当前任务状态

使用场景：
- 需要了解某个代理是否正在忙
- 检查任务执行进度
- 调试协作问题
- 资源管理决策"""

    def __init__(self, agents: Dict[str, "Agent"]):
        """
        初始化状态查询工具
        
        Args:
            agents: 可用的子代理字典
        """
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
        """
        查询代理状态
        
        Args:
            agent_name: 代理名称
        
        Returns:
            ToolResult: 状态信息
        """
        if agent_name not in self.agents:
            return ToolResult(success=False, error=f"未知代理: {agent_name}")
        
        agent = self.agents[agent_name]
        
        # 获取状态信息
        status = {
            "agent_name": agent_name,
            "message_count": len(getattr(agent, 'messages', [])),
            "step": len(getattr(agent, 'messages', [])),
            "workspace": str(getattr(agent, 'workspace_dir', 'unknown')),
            "token_usage": getattr(agent, 'api_total_tokens', 0),
        }
        
        # 判断当前状态
        if status["message_count"] > 10:
            current_state = "active"
        elif status["message_count"] > 0:
            current_state = "idle"
        else:
            current_state = "ready"
        
        status["current_state"] = current_state
        
        return ToolResult(
            success=True,
            content=str(status),
            metadata=status,
        )


class GatherResultsTool(Tool):
    """收集所有子代理结果的工具"""
    
    name = "gather_results"
    description = """收集指定子代理的执行结果进行汇总。

用于在批量任务执行完成后，收集和整合多个代理的结果。

使用场景：
- 批量任务完成后收集结果
- 跨代理结果整合
- 生成执行报告
- 错误检查和验证

注意：
- 只收集成功执行的任务结果
- 可以指定特定的代理列表"""

    def __init__(self, agents: Dict[str, "Agent"]):
        """
        初始化结果收集工具
        
        Args:
            agents: 可用的子代理字典
        """
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
                    "default": list(agents.keys()),
                },
                "include_errors": {
                    "type": "boolean",
                    "description": "是否包含错误结果",
                    "default": False,
                },
            },
            "required": ["agent_names"],
        }
    
    async def execute(
        self,
        agent_names: List[str],
        include_errors: bool = False,
    ) -> ToolResult:
        """
        收集结果
        
        Args:
            agent_names: 要收集的代理名称列表
            include_errors: 是否包含错误结果
        
        Returns:
            ToolResult: 收集的结果
        """
        results = {}
        errors = []
        success_count = 0
        total_count = 0
        
        for name in agent_names:
            if name not in self.agents:
                errors.append(f"未知代理: {name}")
                continue
            
            agent = self.agents[name]
            messages = getattr(agent, 'messages', [])
            total_count += 1
            
            if messages:
                last_msg = messages[-1]
                content = last_msg.content
                
                if isinstance(content, str):
                    result_content = content
                else:
                    result_content = str(content)
                
                results[name] = {
                    "success": True,
                    "content": result_content,
                    "message_count": len(messages),
                }
                
                success_count += 1
            elif include_errors:
                errors.append(f"{name}: 无执行结果")
        
        # 生成汇总信息
        summary_lines = [
            f"收集到 {success_count}/{total_count} 个代理的结果",
            "",
        ]
        
        if results:
            summary_lines.append("结果概览：")
            for name, result in results.items():
                content_preview = result["content"][:100] + "..." if len(result["content"]) > 100 else result["content"]
                summary_lines.append(f"- {name}: {content_preview}")
        
        if errors:
            summary_lines.append("")
            summary_lines.append("错误信息：")
            for error in errors:
                summary_lines.append(f"- {error}")
        
        summary = "\n".join(summary_lines)
        
        return ToolResult(
            success=success_count > 0,
            content=summary,
            metadata={
                "results": results,
                "success_count": success_count,
                "total_count": total_count,
                "errors": errors,
            },
        )
