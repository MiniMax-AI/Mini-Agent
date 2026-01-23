"""
Task Router - 任务路由器

智能分析任务内容并将任务路由到最合适的子代理。
该模块负责任务分析、代理匹配和负载均衡等核心功能。

核心功能：
- 任务内容分析
- 子代理能力匹配
- 负载均衡策略
- 动态路由配置
- 路由历史记录

作者：Mini-Agent Team
版本：0.6.0
"""

from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re
import logging

from ..agent import Agent

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """
    任务优先级枚举
    
    定义任务的优先级级别，用于任务调度和资源分配。
    """
    LOW = 0      # 低优先级
    NORMAL = 1   # 普通优先级
    HIGH = 2     # 高优先级
    URGENT = 3   # 紧急优先级


@dataclass
class RouterConfig:
    """
    路由器配置类
    
    控制路由器行为的各种配置参数。
    
    Attributes:
        enable_load_balancing: 是否启用负载均衡
        max_retries: 最大重试次数
        timeout: 默认超时时间
        enable_caching: 是否启用路由缓存
        cache_ttl: 缓存过期时间（秒）
    """
    enable_load_balancing: bool = True
    max_retries: int = 3
    timeout: int = 300
    enable_caching: bool = True
    cache_ttl: int = 3600


@dataclass
class RouteResult:
    """
    路由结果类
    
    记录一次路由决策的完整信息。
    
    Attributes:
        agent_name: 选择的代理名称
        confidence: 置信度（0-1）
        reasoning: 路由决策的理由
        alternatives: 备选代理列表
    """
    agent_name: str
    confidence: float
    reasoning: str
    alternatives: List[Tuple[str, float]] = field(default_factory=list)


class TaskRouter:
    """
    任务路由器
    
    负责分析任务内容并选择最合适的子代理来执行任务。
    路由器采用多种策略来做出最优决策：
    
    1. 关键词匹配：分析任务描述中的关键词
    2. 能力评估：评估各代理的能力匹配度
    3. 负载均衡：考虑各代理的当前负载
    4. 历史学习：参考历史路由决策
    
    Example:
        router = TaskRouter(agents)
        
        # 路由单个任务
        result = router.route("编写一个Python函数")
        print(f"选择的代理: {result.agent_name}")
        print(f"置信度: {result.confidence}")
        
        # 批量路由
        results = router.route_batch(tasks)
    """
    
    # 任务类型关键词映射
    TASK_KEYWORDS = {
        "coder": [
            "代码", "编程", "开发", "函数", "类", "接口", "调试",
            "code", "program", "develop", "function", "class", "debug",
            "bug", "refactor", "algorithm", "api", "backend", "frontend"
        ],
        "designer": [
            "设计", "海报", "演示", "文档", "视觉", "UI", "UX",
            "design", "poster", "presentation", "document", "visual",
            "canvas", "slide", "layout", "color", "typography"
        ],
        "researcher": [
            "研究", "分析", "调查", "报告", "趋势", "市场", "技术",
            "research", "analyze", "investigate", "report", "trend",
            "market", "technology", "survey", "data", "information"
        ],
        "tester": [
            "测试", "验证", "质量", "检查", "单元测试", "集成测试",
            "test", "verify", "quality", "check", "unit test", "integration",
            "automation", "coverage", "bug", "issue", "validation"
        ],
        "deployer": [
            "部署", "发布", "运维", "容器", "云", "CI/CD", "服务器",
            "deploy", "release", "operation", "container", "cloud",
            "docker", "kubernetes", "k8s", "infrastructure", "server"
        ],
        "analyst": [
            "分析", "数据", "统计", "图表", "报表", "洞察",
            "analyze", "data", "statistics", "chart", "report",
            "insight", "metric", "dashboard", "visualization"
        ],
        "documenter": [
            "文档", "注释", "说明", "手册", "教程", "README",
            "document", "comment", "documentation", "manual",
            "tutorial", "specification", "guide"
        ],
    }
    
    def __init__(
        self,
        agents: Dict[str, Agent],
        config: RouterConfig = None
    ):
        """
        初始化任务路由器
        
        Args:
            agents: 子代理字典
            config: 路由器配置
        """
        self.agents = agents
        self.config = config or RouterConfig()
        
        # 代理负载记录
        self.agent_load: Dict[str, int] = {
            name: 0 for name in agents.keys()
        }
        
        # 路由缓存
        self.route_cache: Dict[str, RouteResult] = {}
        
        # 路由历史
        self.route_history: List[Dict] = []
        
        logger.info(f"任务路由器初始化完成，代理数量: {len(agents)}")
    
    def _preprocess_task(self, task: str) -> str:
        """
        预处理任务文本
        
        统一文本格式，便于后续分析。
        
        Args:
            task: 原始任务描述
        
        Returns:
            str: 预处理后的文本
        """
        # 转换为小写
        task = task.lower()
        
        # 移除多余的空白字符
        task = re.sub(r'\s+', ' ', task)
        
        return task
    
    def _analyze_task_type(self, task: str) -> Dict[str, float]:
        """
        分析任务类型
        
        通过关键词匹配计算各代理类型的能力匹配分数。
        
        Args:
            task: 任务描述
        
        Returns:
            Dict[str, float]: 各代理类型的匹配分数
        """
        task = self._preprocess_task(task)
        scores = {}
        
        for agent_type, keywords in self.TASK_KEYWORDS.items():
            score = 0
            matched_keywords = []
            
            for keyword in keywords:
                if keyword.lower() in task:
                    score += 1
                    matched_keywords.append(keyword)
            
            # 正则匹配额外加分
            for keyword in keywords:
                if re.search(r'\b' + re.escape(keyword.lower()) + r'\b', task):
                    score += 0.5
            
            # 归一化分数
            if keywords:
                scores[agent_type] = min(1.0, score / (len(keywords) * 0.3))
            else:
                scores[agent_type] = 0
        
        return scores
    
    def _get_agent_load(self, agent_name: str) -> int:
        """
        获取代理当前负载
        
        Args:
            agent_name: 代理名称
        
        Returns:
            int: 当前负载（正在执行的任务数）
        """
        return self.agent_load.get(agent_name, 0)
    
    def _calculate_final_score(
        self,
        type_scores: Dict[str, float],
        agent_name: str
    ) -> float:
        """
        计算最终分数
        
        综合考虑类型匹配分数和负载情况。
        
        Args:
            type_scores: 类型匹配分数
            agent_name: 代理名称
        
        Returns:
            float: 最终分数
        """
        # 基础类型匹配分数
        base_score = type_scores.get(agent_name, 0)
        
        # 负载均衡调整
        if self.config.enable_load_balancing:
            load = self._get_agent_load(agent_name)
            # 负载越高，分数越低
            load_penalty = min(0.3, load * 0.05)
            final_score = base_score * (1 - load_penalty)
        else:
            final_score = base_score
        
        return final_score
    
    def _select_best_agent(
        self,
        type_scores: Dict[str, float],
        available_agents: List[str]
    ) -> Tuple[str, float, List[Tuple[str, float]]]:
        """
        选择最佳代理
        
        根据分数选择最佳代理，并返回备选列表。
        
        Args:
            type_scores: 各类型分数
            available_agents: 可用代理列表
        
        Returns:
            Tuple: (最佳代理, 置信度, 备选列表)
        """
        agent_scores = []
        
        for agent_name in available_agents:
            score = self._calculate_final_score(type_scores, agent_name)
            agent_scores.append((agent_name, score))
        
        # 按分数排序
        agent_scores.sort(key=lambda x: -x[1])
        
        if not agent_scores:
            return "default", 0.0, []
        
        best_agent, best_score = agent_scores[0]
        alternatives = agent_scores[1:6]  # 前5个备选
        
        return best_agent, best_score, alternatives
    
    def _build_reasoning(
        self,
        agent_name: str,
        confidence: float,
        matched_keywords: List[str]
    ) -> str:
        """
        构建路由决策理由
        
        Args:
            agent_name: 选择的代理
            confidence: 置信度
            matched_keywords: 匹配的关键词
        
        Returns:
            str: 决策理由文本
        """
        if confidence >= 0.8:
            confidence_desc = "高置信度"
        elif confidence >= 0.5:
            confidence_desc = "中等置信度"
        else:
            confidence_desc = "低置信度"
        
        keywords_str = ", ".join(matched_keywords[:5])
        
        return f"{confidence_desc}（{confidence:.2f}），匹配关键词：{keywords_str}"
    
    def route(
        self,
        task: str,
        preferred_agent: str = None,
        context: Dict[str, Any] = None
    ) -> RouteResult:
        """
        路由单个任务
        
        这是路由器的主要接口，分析任务并选择最佳代理。
        
        Args:
            task: 任务描述
            preferred_agent: 首选代理（可选）
            context: 上下文信息（可选）
        
        Returns:
            RouteResult: 路由结果
        """
        # 检查缓存
        cache_key = f"{task[:100]}:{preferred_agent}"
        if self.config.enable_caching and cache_key in self.route_cache:
            cached = self.route_cache[cache_key]
            # 检查缓存是否过期
            # 这里简化处理，实际应该检查时间戳
            return cached
        
        # 预处理任务
        task = self._preprocess_task(task)
        
        # 分析任务类型
        type_scores = self._analyze_task_type(task)
        
        # 获取可用代理
        available_agents = list(self.agents.keys())
        
        # 如果指定了首选代理，优先考虑
        if preferred_agent and preferred_agent in available_agents:
            # 将首选代理的分数提高
            type_scores[preferred_agent] = type_scores.get(preferred_agent, 0) + 0.3
        
        # 选择最佳代理
        best_agent, confidence, alternatives = self._select_best_agent(
            type_scores, available_agents
        )
        
        # 获取匹配的关键词
        matched_keywords = []
        for keyword in self.TASK_KEYWORDS.get(best_agent, []):
            if keyword.lower() in task.lower():
                matched_keywords.append(keyword)
        
        # 构建决策理由
        reasoning = self._build_reasoning(best_agent, confidence, matched_keywords)
        
        # 创建路由结果
        result = RouteResult(
            agent_name=best_agent,
            confidence=confidence,
            reasoning=reasoning,
            alternatives=[(name, score) for name, score in alternatives]
        )
        
        # 更新缓存
        if self.config.enable_caching:
            self.route_cache[cache_key] = result
        
        # 记录路由历史
        self.route_history.append({
            "task": task,
            "result": result,
            "context": context,
        })
        
        logger.info(f"路由决策: {best_agent} (置信度: {confidence:.2f})")
        
        return result
    
    def route_batch(
        self,
        tasks: List[Dict[str, Any]],
        context: Dict[str, Any] = None
    ) -> List[RouteResult]:
        """
        批量路由任务
        
        一次性路由多个任务，优化整体决策。
        
        Args:
            tasks: 任务列表，每个任务包含 task 和可选的 preferred_agent
            context: 全局上下文
        
        Returns:
            List[RouteResult]: 路由结果列表
        """
        results = []
        
        for task_info in tasks:
            task = task_info.get("task", "")
            preferred = task_info.get("preferred_agent")
            
            result = self.route(task, preferred, context)
            results.append(result)
        
        # 应用负载均衡
        if self.config.enable_load_balancing:
            self._apply_load_balancing(results)
        
        return results
    
    def _apply_load_balancing(self, results: List[RouteResult]):
        """
        应用负载均衡
        
        调整路由结果以平衡各代理的负载。
        
        Args:
            results: 路由结果列表
        """
        # 统计各代理的任务数量
        agent_task_counts: Dict[str, int] = {}
        for result in results:
            agent_name = result.agent_name
            agent_task_counts[agent_name] = agent_task_counts.get(agent_name, 0) + 1
        
        # 如果某个代理任务过多，考虑重新分配
        for result in results:
            agent_name = result.agent_name
            count = agent_task_counts.get(agent_name, 0)
            
            # 如果任务数超过平均水平的 2 倍，尝试重新路由
            avg_count = len(results) / len(self.agents)
            if count > avg_count * 2 and result.alternatives:
                # 选择备选代理中负载较轻的
                for alt_name, alt_score in result.alternatives:
                    alt_count = agent_task_counts.get(alt_name, 0)
                    if alt_count < count - 1:
                        # 重新路由到备选代理
                        new_result = self.route(
                            f"备用路由: {result.reasoning}",
                            preferred_agent=alt_name
                        )
                        result.agent_name = new_result.agent_name
                        result.confidence = new_result.confidence * 0.9  # 降低置信度
                        agent_task_counts[agent_name] -= 1
                        agent_task_counts[alt_name] = agent_task_counts.get(alt_name, 0) + 1
                        break
    
    def add_agent_load(self, agent_name: str):
        """
        增加代理负载计数
        
        Args:
            agent_name: 代理名称
        """
        if agent_name in self.agent_load:
            self.agent_load[agent_name] += 1
    
    def remove_agent_load(self, agent_name: str):
        """
        减少代理负载计数
        
        Args:
            agent_name: 代理名称
        """
        if agent_name in self.agent_load and self.agent_load[agent_name] > 0:
            self.agent_load[agent_name] -= 1
    
    def get_load_status(self) -> Dict[str, Any]:
        """
        获取负载状态
        
        Returns:
            Dict: 负载状态信息
        """
        total_load = sum(self.agent_load.values())
        avg_load = total_load / len(self.agent_load) if self.agent_load else 0
        
        return {
            "agent_loads": self.agent_load,
            "total_load": total_load,
            "average_load": avg_load,
            "overloaded_agents": [
                name for name, load in self.agent_load.items()
                if load > avg_load * 2
            ],
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取路由统计信息
        
        Returns:
            Dict: 统计信息
        """
        # 统计各代理被选择的次数
        agent_selection_count: Dict[str, int] = {}
        total_confidence = 0
        
        for entry in self.route_history:
            result = entry["result"]
            agent_name = result.agent_name
            agent_selection_count[agent_name] = agent_selection_count.get(agent_name, 0) + 1
            total_confidence += result.confidence
        
        return {
            "total_routes": len(self.route_history),
            "agent_selection_count": agent_selection_count,
            "average_confidence": total_confidence / len(self.route_history) if self.route_history else 0,
            "cache_size": len(self.route_cache),
            "current_load": self.get_load_status(),
        }
    
    def clear_cache(self):
        """清空路由缓存"""
        self.route_cache.clear()
        logger.info("路由缓存已清空")
    
    def clear_history(self):
        """清空路由历史"""
        self.route_history.clear()
        logger.info("路由历史已清空")


def create_task_router(
    agents: Dict[str, Agent],
    enable_load_balancing: bool = True
) -> TaskRouter:
    """
    创建任务路由器
    
    工厂函数，简化路由器的创建过程。
    
    Args:
        agents: 子代理字典
        enable_load_balancing: 是否启用负载均衡
    
    Returns:
        TaskRouter: 路由器实例
    """
    config = RouterConfig(enable_load_balancing=enable_load_balancing)
    return TaskRouter(agents, config)
