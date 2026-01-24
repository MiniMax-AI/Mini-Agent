"""
Optimized Executor - Ubuntu 优化的智能混合执行器

根据任务性质自动选择最优执行模式的执行器。
该模块针对 Ubuntu 系统进行了深度优化，充分利用系统资源
实现高效的并行任务执行。

核心特性：
- 智能任务类型检测（I/O 密集型 vs CPU 密集型）
- 多种执行模式支持（异步并行、线程池、顺序执行）
- Ubuntu 系统资源优化配置
- 动态并发控制
- 完善的错误处理和超时机制

作者：Mini-Agent Team
版本：0.6.0
"""

import asyncio
import os
import psutil
from typing import List, Dict, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, Future
import logging

from ..agent import Agent

logger = logging.getLogger(__name__)


# Ubuntu 系统优化配置类
class UbuntuConfig:
    """
    Ubuntu 系统优化配置
    
    根据 Ubuntu 系统的硬件资源自动配置最优执行参数。
    该类会检测 CPU 核心数、内存大小等系统资源，
    并据此设置线程池大小、并发限制等参数。
    
    默认配置策略：
    - 异步并发数：基于 CPU 核心数的动态计算
    - 线程池大小：CPU 核心数的 2 倍
    - 进程池大小：CPU 核心数减 1
    - 内存限制：可用内存的 50%
    
    Example:
        config = UbuntuConfig()
        print(f"CPU 核心数: {config.CPU_COUNT}")
        print(f"最大异步并发: {config.MAX_ASYNC_CONCURRENT}")
        print(f"线程池大小: {config.THREAD_POOL_SIZE}")
    """
    
    # CPU 核心数
    CPU_COUNT = os.cpu_count() or 4
    
    # 内存信息（GB）
    _MEMORY_INFO = psutil.virtual_memory()
    MEMORY_TOTAL = _MEMORY_INFO.total / (1024 ** 3)
    MEMORY_AVAILABLE = _MEMORY_INFO.available / (1024 ** 3)
    
    # Async 并发数：最小 50，最大 200，或基于 CPU 核心数计算
    MAX_ASYNC_CONCURRENT = min(200, max(50, 32 * CPU_COUNT))
    
    # 线程池大小：CPU 核心数的 2 倍
    THREAD_POOL_SIZE = CPU_COUNT * 2
    
    # 进程池大小：CPU 核心数减 1（保留一个核心给系统）
    PROCESS_POOL_SIZE = max(1, CPU_COUNT - 1)
    
    # 内存限制：可用内存的 50%
    MEMORY_LIMIT = int(MEMORY_AVAILABLE * 0.5)
    
    # 默认任务超时时间（秒）
    DEFAULT_TIMEOUT = 300
    
    # 批量任务最大数量
    BATCH_MAX_SIZE = 100


@dataclass
class Task:
    """
    任务定义数据类
    
    用于描述一个待执行的任务，包含任务类型、执行代理、
    超时设置等所有必要信息。
    
    Attributes:
        agent_name: 执行任务的子代理名称
        task: 任务描述文本
        context: 可选的上下文信息字典
        timeout: 超时时间（秒），默认 300 秒
        priority: 任务优先级，数值越大优先级越高
        task_type: 任务类型（io_bound/cpu_bound），自动检测
    
    Example:
        task = Task(
            agent_name="coder",
            task="编写一个 Python 函数",
            context={"项目": "demo"},
            priority=1,
            timeout=600
        )
    """
    agent_name: str
    task: str
    context: Dict[str, Any] = None
    timeout: int = 300
    priority: int = 0
    task_type: str = "io_bound"


class OptimizedExecutor:
    """
    Ubuntu 优化的多代理执行器
    
    该执行器是整个多代理系统的核心执行引擎，负责实际执行
    分配给各子代理的任务。它采用智能混合执行策略，根据
    任务类型自动选择最优的执行模式。
    
    执行模式：
    1. auto（自动模式）：根据任务类型自动选择
    2. parallel（并行模式）：使用 asyncio 并行执行
    3. sequential（顺序模式）：使用线程池顺序执行
    4. thread（线程池模式）：强制使用线程池
    
    任务类型检测：
    - I/O 密集型：API 调用、文件操作、网络请求等
    - CPU 密集型：数据分析、格式转换、批量处理等
    
    Example:
        executor = OptimizedExecutor(agents)
        
        # 自动模式执行
        result = await executor.execute(tasks, mode="auto")
        
        # 强制并行执行
        result = await executor.execute(tasks, mode="parallel")
    """
    
    def __init__(self, agents: Dict[str, Agent]):
        """
        初始化执行器
        
        Args:
            agents: 子代理字典，键为代理名称
        """
        self.agents = agents
        self.config = UbuntuConfig()
        
        # 创建异步信号量（并发控制）
        self.semaphore = asyncio.Semaphore(self.config.MAX_ASYNC_CONCURRENT)
        
        # 创建线程池（用于 CPU 密集型任务）
        self.thread_pool = ThreadPoolExecutor(
            max_workers=self.config.THREAD_POOL_SIZE,
            thread_name_prefix="AgentWorker"
        )
        
        # CPU 密集型任务关键词列表
        self.cpu_keywords = [
            # 中文关键词
            "计算", "分析", "处理", "转换", "统计", "批量",
            "编译", "渲染", "生成", "加密", "解压", "压缩",
            # 英文关键词
            "calculate", "analyze", "process", "transform", "statistic",
            "batch", "generate", "render", "compile", "encrypt", "compress",
            "parse", "encode", "decode", "filter", "map", "reduce"
        ]
        
        logger.info(f"执行器初始化完成，线程池大小: {self.config.THREAD_POOL_SIZE}")

    def analyze_task_type(self, task: Task) -> str:
        """
        分析任务类型（I/O 密集型 vs CPU 密集型）
        
        通过分析任务描述中的关键词来判断任务类型。
        如果包含 CPU 密集型关键词，则认为是 CPU 密集型任务。
        
        Args:
            task: 任务对象
        
        Returns:
            str: 任务类型（"cpu_bound" 或 "io_bound"）
        """
        task_text = task.task.lower()
        
        # 检查是否包含 CPU 密集型关键词
        if any(keyword.lower() in task_text for keyword in self.cpu_keywords):
            return "cpu_bound"
        
        return "io_bound"

    def detect_task_types(self, tasks: List[Task]) -> Dict[str, List[Task]]:
        """
        批量检测任务类型
        
        Args:
            tasks: 任务列表
        
        Returns:
            Dict: 分类后的任务字典，包含 "cpu_bound" 和 "io_bound" 键
        """
        result = {
            "cpu_bound": [],
            "io_bound": []
        }
        
        for task in tasks:
            task.task_type = self.analyze_task_type(task)
            result[task.task_type].append(task)
        
        return result

    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """
        执行单个任务（带并发控制）
        
        使用信号量限制并发数量，防止系统过载。
        
        Args:
            task: 任务对象
        
        Returns:
            Dict[str, Any]: 执行结果
        """
        async with self.semaphore:
            agent = self.agents.get(task.agent_name)
            
            if not agent:
                return {
                    "agent": task.agent_name,
                    "success": False,
                    "error": f"未知代理: {task.agent_name}",
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
                    "token_usage": getattr(agent, 'api_total_tokens', 0),
                }
                
            except asyncio.TimeoutError:
                logger.warning(f"任务超时: {task.agent_name} - {task.task[:50]}...")
                return {
                    "agent": task.agent_name,
                    "success": False,
                    "error": f"任务在 {task.timeout} 秒后超时",
                    "task_type": task.task_type,
                }
            except Exception as e:
                logger.error(f"任务执行错误: {task.agent_name} - {str(e)}")
                return {
                    "agent": task.agent_name,
                    "success": False,
                    "error": str(e),
                    "task_type": task.task_type,
                }

    def _format_context(self, context: Dict[str, Any]) -> str:
        """
        格式化上下文信息
        
        Args:
            context: 上下文字典
        
        Returns:
            str: 格式化后的文本
        """
        lines = ["[Context]"]
        for key, value in context.items():
            lines.append(f"- {key}: {value}")
        return "\n".join(lines)

    async def execute_parallel(self, tasks: List[Task]) -> List[Dict[str, Any]]:
        """
        并行执行任务列表
        
        使用 asyncio.gather 实现真正的并行执行。
        
        Args:
            tasks: 任务列表
        
        Returns:
            List[Dict]: 执行结果列表
        """
        # 按优先级排序（高优先级先执行）
        sorted_tasks = sorted(tasks, key=lambda t: -t.priority)
        
        # 并发执行所有任务
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
        """
        顺序执行任务列表（使用线程池）
        
        适用于 CPU 密集型任务，避免 GIL 限制。
        
        Args:
            tasks: 任务列表
        
        Returns:
            List[Dict]: 执行结果列表
        """
        results = []
        
        for task in tasks:
            # 在线程池中执行异步任务
            future: Future = self.thread_pool.submit(
                asyncio.run,
                self.execute_task(task)
            )
            results.append(future.result())
        
        return results

    def execute_thread_pool(self, tasks: List[Task]) -> List[Dict[str, Any]]:
        """
        使用线程池执行任务（CPU 密集型任务优化）
        
        Args:
            tasks: 任务列表
        
        Returns:
            List[Dict]: 执行结果列表
        """
        results = []
        
        for task in tasks:
            task.task_type = "cpu_bound"
            future: Future = self.thread_pool.submit(
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
        """
        智能执行任务
        
        这是执行器的主要接口，根据指定或自动检测的模式
        执行任务列表。
        
        Args:
            tasks: 任务列表
            mode: 执行模式
                - "auto": 自动选择（推荐）
                - "parallel": 强制并行
                - "sequential": 强制顺序
                - "thread": 使用线程池
        
        Returns:
            Dict[str, Any]: 执行结果摘要，包含：
                - mode: 使用的执行模式
                - total: 任务总数
                - success: 成功数量
                - failed: 失败数量
                - results: 详细结果列表
                - task_breakdown: 任务类型分布
                - cpu_utilization: CPU 使用情况评估
        """
        if not tasks:
            return {
                "mode": mode,
                "total": 0,
                "success": 0,
                "failed": 0,
                "results": [],
                "task_breakdown": {"cpu_bound": 0, "io_bound": 0},
                "cpu_utilization": "low",
            }

        logger.info(f"开始执行 {len(tasks)} 个任务，模式: {mode}")
        
        # 分析任务类型
        task_types = [self.analyze_task_type(t) for t in tasks]
        cpu_bound_count = task_types.count("cpu_bound")
        io_bound_count = len(tasks) - cpu_bound_count
        total_count = len(tasks)
        
        # 智能选择执行模式
        selected_mode = mode
        if mode == "auto":
            # 如果 CPU 密集型任务超过 50%，使用线程池
            if cpu_bound_count / total_count > 0.5:
                selected_mode = "thread"
            # 如果任务数量少于等于 2，使用顺序执行
            elif len(tasks) <= 2:
                selected_mode = "sequential"
            # 否则使用并行执行
            else:
                selected_mode = "parallel"
        
        logger.info(f"实际执行模式: {selected_mode}, CPU任务: {cpu_bound_count}, IO任务: {io_bound_count}")
        
        # 根据模式执行
        if selected_mode == "parallel":
            results = await self.execute_parallel(tasks)
        elif selected_mode == "thread":
            results = self.execute_thread_pool(tasks)
        elif selected_mode == "sequential":
            results = self.execute_sequential(tasks)
        else:
            # 默认使用并行执行
            results = await self.execute_parallel(tasks)
        
        # 统计结果
        success_count = sum(1 for r in results if r.get("success"))
        failed_count = len(results) - success_count
        
        # 生成摘要
        return {
            "mode": selected_mode,
            "total": len(tasks),
            "success": success_count,
            "failed": failed_count,
            "results": results,
            "task_breakdown": {
                "cpu_bound": cpu_bound_count,
                "io_bound": io_bound_count,
            },
            "cpu_utilization": self._estimate_cpu_usage(cpu_bound_count, len(tasks)),
            "execution_time": self._measure_execution_time(results),
        }

    def _estimate_cpu_usage(self, cpu_tasks: int, total: int) -> str:
        """
        估算 CPU 使用情况
        
        Args:
            cpu_tasks: CPU 密集型任务数量
            total: 总任务数
        
        Returns:
            str: CPU 使用情况描述（low/medium/high）
        """
        if cpu_tasks == 0:
            return "low"
        elif cpu_tasks < total / 2:
            return "medium"
        else:
            return "high"

    def _measure_execution_time(self, results: List[Dict]) -> Dict[str, float]:
        """
        测量执行时间
        
        Args:
            results: 执行结果列表
        
        Returns:
            Dict: 时间统计信息
        """
        # 这里可以添加详细的执行时间测量逻辑
        # 目前返回基本统计
        return {
            "estimated_total": sum(
                r.get("duration", 0) for r in results if isinstance(r, dict)
            ),
            "avg_per_task": 0,
        }

    def shutdown(self):
        """
        关闭执行器
        
        释放线程池等资源。
        """
        self.thread_pool.shutdown(wait=True)
        logger.info("执行器已关闭")

    def get_config(self) -> Dict[str, Any]:
        """
        获取当前配置
        
        Returns:
            Dict: 配置信息字典
        """
        return {
            "cpu_count": self.config.CPU_COUNT,
            "max_async_concurrent": self.config.MAX_ASYNC_CONCURRENT,
            "thread_pool_size": self.config.THREAD_POOL_SIZE,
            "process_pool_size": self.config.PROCESS_POOL_SIZE,
            "memory_limit_gb": self.config.MEMORY_LIMIT,
        }


def create_executor(agents: Dict[str, Agent]) -> OptimizedExecutor:
    """
    创建优化的执行器
    
    工厂函数，简化执行器的创建过程。
    
    Args:
        agents: 子代理字典
    
    Returns:
        OptimizedExecutor: 执行器实例
    """
    return OptimizedExecutor(agents)


# 便捷执行函数
async def quick_execute(
    agents: Dict[str, Agent],
    agent_name: str,
    task: str,
    timeout: int = 300
) -> Dict[str, Any]:
    """
    快速执行单个任务
    
    简化接口，适用于快速测试和简单任务。
    
    Args:
        agents: 子代理字典
        agent_name: 代理名称
        task: 任务描述
        timeout: 超时时间
    
    Returns:
        Dict: 执行结果
    """
    executor = OptimizedExecutor(agents)
    
    task_obj = Task(
        agent_name=agent_name,
        task=task,
        timeout=timeout,
    )
    
    return await executor.execute_task(task_obj)
