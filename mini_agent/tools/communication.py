"""
Communication Tools - 通信工具集

提供代理之间共享信息和同步状态的工具。
这些工具支持代理间的上下文共享、消息广播和状态同步。

可用工具：
- ShareContextTool：上下文共享工具
- BroadcastMessageTool：消息广播工具
- SyncStateTool：状态同步工具

版本：0.6.0
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
import logging

from .base import Tool, ToolResult

logger = logging.getLogger(__name__)


@dataclass
class SharedContext:
    """
    共享上下文条目
    
    Attributes:
        key: 上下文键名
        value: 上下文值
        source: 来源代理
        timestamp: 创建时间
        ttl: 存活时间（秒）
    """
    key: str
    value: Any
    source: str
    timestamp: datetime = field(default_factory=datetime.now)
    ttl: int = 3600  # 默认1小时过期


class ShareContextTool(Tool):
    """在代理之间共享上下文的工具"""
    
    name = "share_context"
    description = """在代理之间共享上下文信息。

这是实现多代理协作的关键工具，允许代理之间传递：
- 中间结果
- 共享数据
- 处理状态
- 重要发现

使用场景：
- 传递中间处理结果
- 共享配置文件或数据
- 传递处理状态信息
- 跨代理知识传递

参数：
- key: 上下文键名
- value: 要共享的值
- target_agents: 目标代理列表（可选，默认所有代理）
- ttl: 存活时间（秒），默认 3600

重要说明：
1. 使用描述性的键名
2. 控制共享数据的大小
3. 设置合理的 TTL
4. 及时清理不再需要的上下文"""

    def __init__(self, orchestrator: "MultiAgentOrchestrator"):
        """
        初始化上下文共享工具
        
        Args:
            orchestrator: 协调器实例
        """
        self.orchestrator = orchestrator
        self._context_store: Dict[str, SharedContext] = {}
    
    @property
    def parameters(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "上下文键名",
                },
                "value": {
                    "type": "any",
                    "description": "要共享的值",
                },
                "target_agents": {
                    "type": "array",
                    "description": "目标代理列表（可选）",
                    "items": {"type": "string"},
                },
                "ttl": {
                    "type": "integer",
                    "description": "存活时间（秒）",
                    "default": 3600,
                },
            },
            "required": ["key", "value"],
        }
    
    def execute(
        self,
        key: str,
        value: Any,
        target_agents: Optional[List[str]] = None,
        ttl: int = 3600,
    ) -> ToolResult:
        """
        共享上下文
        
        Args:
            key: 上下文键名
            value: 要共享的值
            target_agents: 目标代理列表
            ttl: 存活时间
        
        Returns:
            ToolResult: 执行结果
        """
        try:
            # 序列化复杂对象
            if not isinstance(value, (str, int, float, bool, list, dict)):
                value = self._serialize_value(value)
            
            # 创建共享上下文
            context = SharedContext(
                key=key,
                value=value,
                source="coordinator",
                ttl=ttl,
            )
            
            # 存储上下文
            self._context_store[key] = context
            
            # 更新协调器的共享上下文
            self.orchestrator.shared_context[key] = value
            
            # 记录日志
            target_str = ", ".join(target_agents) if target_agents else "所有代理"
            logger.info(f"上下文已共享: {key} -> {target_str}")
            
            return ToolResult(
                success=True,
                content=f"上下文 '{key}' 已共享给 {target_str}",
                metadata={
                    "key": key,
                    "target_agents": target_agents,
                    "ttl": ttl,
                },
            )
            
        except Exception as e:
            logger.error(f"共享上下文失败: {str(e)}")
            return ToolResult(
                success=False,
                content="",
                error=f"共享上下文失败: {str(e)}",
            )
    
    def get_context(self, key: str) -> Any:
        """
        获取上下文值
        
        Args:
            key: 上下文键名
        
        Returns:
            Any: 上下文值，不存在返回 None
        """
        if key in self._context_store:
            context = self._context_store[key]
            if self._is_valid(context):
                return context.value
            else:
                # 清理过期上下文
                del self._context_store[key]
        return None
    
    def get_all_contexts(self, agent_name: str = None) -> Dict[str, Any]:
        """
        获取所有有效的上下文
        
        Args:
            agent_name: 只返回发给特定代理的上下文
        
        Returns:
            Dict: 上下文字典
        """
        result = {}
        for key, context in self._context_store.items():
            if self._is_valid(context):
                result[key] = context.value
        return result
    
    def remove_context(self, key: str) -> bool:
        """
        移除上下文
        
        Args:
            key: 上下文键名
        
        Returns:
            bool: 是否成功移除
        """
        if key in self._context_store:
            del self._context_store[key]
            if key in self.orchestrator.shared_context:
                del self.orchestrator.shared_context[key]
            return True
        return False
    
    def clear_expired(self):
        """清理所有过期的上下文"""
        expired_keys = [
            key for key, context in self._context_store.items()
            if not self._is_valid(context)
        ]
        for key in expired_keys:
            del self._context_store[key]
        logger.info(f"清理了 {len(expired_keys)} 个过期上下文")
    
    def _is_valid(self, context: SharedContext) -> bool:
        """
        检查上下文是否有效
        
        Args:
            context: 共享上下文
        
        Returns:
            bool: 是否有效
        """
        from datetime import timedelta
        age = datetime.now() - context.timestamp
        return age.total_seconds() < context.ttl
    
    def _serialize_value(self, value: Any) -> str:
        """
        序列化复杂对象
        
        Args:
            value: 要序列化的值
        
        Returns:
            str: 序列化后的字符串
        """
        try:
            return json.dumps(value, ensure_ascii=False, default=str)
        except (TypeError, ValueError):
            return str(value)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            Dict: 统计信息
        """
        valid_count = sum(
            1 for c in self._context_store.values()
            if self._is_valid(c)
        )
        return {
            "total_contexts": len(self._context_store),
            "valid_contexts": valid_count,
            "expired_contexts": len(self._context_store) - valid_count,
        }


class BroadcastMessageTool(Tool):
    """向多个代理广播消息的工具"""
    
    name = "broadcast_message"
    description = """向多个代理同时发送消息。

用于向所有或部分子代理发送通知或指令。

使用场景：
- 发送全局通知
- 同步开始/停止信号
- 传递紧急指令
- 协调并行任务启动

参数：
- message: 要广播的消息内容
- target_agents: 目标代理列表（可选，默认所有）
- priority: 消息优先级（normal/urgent）

注意：
- 广播是单向的，不等待响应
- 大量广播可能影响性能
- 紧急消息会标记为高优先级"""

    def __init__(self, agents: Dict[str, "Agent"]):
        """
        初始化消息广播工具
        
        Args:
            agents: 可用的子代理字典
        """
        self.agents = agents
        self._broadcast_history: List[Dict] = []
    
    @property
    def parameters(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "要广播的消息内容",
                },
                "target_agents": {
                    "type": "array",
                    "description": "目标代理列表（可选，默认所有）",
                    "items": {"type": "string"},
                },
                "priority": {
                    "type": "string",
                    "description": "消息优先级",
                    "enum": ["normal", "urgent"],
                    "default": "normal",
                },
            },
            "required": ["message"],
        }
    
    def execute(
        self,
        message: str,
        target_agents: Optional[List[str]] = None,
        priority: str = "normal",
    ) -> ToolResult:
        """
        广播消息
        
        Args:
            message: 消息内容
            target_agents: 目标代理列表
            priority: 优先级
        
        Returns:
            ToolResult: 执行结果
        """
        # 确定目标代理
        if target_agents is None:
            target_agents = list(self.agents.keys())
        
        # 过滤不存在的代理
        valid_targets = [a for a in target_agents if a in self.agents]
        
        if not valid_targets:
            return ToolResult(
                success=False,
                content="",
                error="没有有效的目标代理",
            )
        
        # 格式化消息
        formatted_message = self._format_message(message, priority)
        
        # 发送消息给所有目标代理
        success_count = 0
        for agent_name in valid_targets:
            agent = self.agents[agent_name]
            agent.add_user_message(formatted_message)
            success_count += 1
        
        # 记录历史
        self._broadcast_history.append({
            "message": message,
            "targets": valid_targets,
            "priority": priority,
            "success_count": success_count,
            "timestamp": datetime.now().isoformat(),
        })
        
        logger.info(
            f"广播消息已发送: {len(valid_targets)} 个代理，优先级: {priority}"
        )
        
        return ToolResult(
            success=True,
            content=f"消息已广播给 {len(valid_targets)} 个代理",
            metadata={
                "targets": valid_targets,
                "priority": priority,
                "success_count": success_count,
            },
        )
    
    def _format_message(self, message: str, priority: str) -> str:
        """
        格式化广播消息
        
        Args:
            message: 原始消息
            priority: 优先级
        
        Returns:
            str: 格式化后的消息
        """
        if priority == "urgent":
            prefix = "【紧急通知】"
        else:
            prefix = "【广播通知】"
        
        return f"{prefix}\n{message}"
    
    def get_broadcast_history(self) -> List[Dict]:
        """
        获取广播历史
        
        Returns:
            List: 广播历史列表
        """
        return self._broadcast_history


class SyncStateTool(Tool):
    """同步代理状态的工具"""
    
    name = "sync_state"
    description = """同步和比较多个代理的当前状态。

用于检查和协调多个代理的执行状态，确保协作正确进行。

使用场景：
- 检查所有代理是否就绪
- 同步任务开始状态
- 比较执行进度
- 检测卡住或异常的代理

参数：
- agent_names: 要同步的代理名称列表
- include_details: 是否包含详细信息

返回：
- 各代理的当前状态
- 异常代理列表
- 同步建议"""

    def __init__(self, agents: Dict[str, "Agent"]):
        """
        初始化状态同步工具
        
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
                    "description": "要同步的代理名称列表",
                    "items": {"type": "string"},
                },
                "include_details": {
                    "type": "boolean",
                    "description": "是否包含详细信息",
                    "default": False,
                },
            },
            "required": ["agent_names"],
        }
    
    def execute(
        self,
        agent_names: List[str],
        include_details: bool = False,
    ) -> ToolResult:
        """
        同步状态
        
        Args:
            agent_names: 代理名称列表
            include_details: 是否包含详细信息
        
        Returns:
            ToolResult: 同步结果
        """
        states = {}
        anomalies = []
        ready_count = 0
        busy_count = 0
        
        for name in agent_names:
            if name not in self.agents:
                anomalies.append({
                    "agent": name,
                    "issue": "未知代理",
                })
                continue
            
            agent = self.agents[name]
            messages = getattr(agent, 'messages', [])
            
            # 分析状态
            if messages:
                # 检查最后一条消息的角色
                last_msg = messages[-1]
                last_role = getattr(last_msg, 'role', None)
                
                if last_role == "assistant":
                    state = "completed"
                    ready_count += 1
                elif last_role == "user":
                    state = "pending"
                    busy_count += 1
                else:
                    state = "unknown"
            else:
                state = "ready"
                ready_count += 1
            
            agent_state = {
                "state": state,
                "message_count": len(messages),
                "workspace": str(getattr(agent, 'workspace_dir', 'unknown')),
            }
            
            if include_details:
                agent_state["last_message_role"] = getattr(
                    messages[-1], 'role', None
                ) if messages else None
            
            states[name] = agent_state
        
        # 生成同步建议
        suggestions = []
        if busy_count > 0:
            suggestions.append(f"{busy_count} 个代理正在等待输入")
        if anomalies:
            suggestions.append(f"{len(anomalies)} 个代理存在异常")
        if ready_count == len(agent_names) and not anomalies:
            suggestions.append("所有代理已就绪，可以开始新任务")
        
        # 总体状态
        if anomalies:
            overall_status = "anomaly"
        elif busy_count > 0:
            overall_status = "partial"
        elif ready_count == len(agent_names):
            overall_status = "ready"
        else:
            overall_status = "unknown"
        
        # 格式化结果
        result_lines = [
            f"状态同步完成",
            f"总代理数: {len(agent_names)}",
            f"就绪: {ready_count}",
            f"等待中: {busy_count}",
            f"异常: {len(anomalies)}",
            "",
        ]
        
        if suggestions:
            result_lines.append("建议:")
            for suggestion in suggestions:
                result_lines.append(f"- {suggestion}")
        
        result_content = "\n".join(result_lines)
        
        return ToolResult(
            success=len(anomalies) == 0,
            content=result_content,
            metadata={
                "overall_status": overall_status,
                "states": states,
                "anomalies": anomalies,
                "suggestions": suggestions,
                "ready_count": ready_count,
                "busy_count": busy_count,
            },
        )
    
    def sync_all(self) -> ToolResult:
        """
        同步所有代理状态
        
        Returns:
            ToolResult: 同步结果
        """
        return self.execute(
            agent_names=list(self.agents.keys()),
            include_details=True,
        )
