"""
Result Aggregator - 结果聚合器

收集、验证和整合来自多个子代理的执行结果。
该模块负责结果的标准化、质量检查和格式转换。

核心功能：
- 多源结果收集
- 结果验证和去重
- 质量评分计算
- 格式整合输出
- 错误汇总处理

作者：Mini-Agent Team
版本：0.6.0
"""

from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging
import hashlib
import json

logger = logging.getLogger(__name__)


class ResultStatus(Enum):
    """
    结果状态枚举
    
    描述单个结果的状态类型。
    """
    SUCCESS = "success"      # 成功
    PARTIAL = "partial"      # 部分成功
    FAILED = "failed"        # 失败
    TIMEOUT = "timeout"      # 超时
    ERROR = "error"          # 错误


@dataclass
class AggregatedResult:
    """
    聚合结果类
    
    包含聚合后的完整结果信息。
    
    Attributes:
        overall_status: 总体状态
        total_count: 总任务数
        success_count: 成功数
        failed_count: 失败数
        results: 详细结果列表
        summary: 结果摘要
        errors: 错误列表
        metadata: 元数据
    """
    overall_status: ResultStatus
    total_count: int
    success_count: int
    failed_count: int
    results: List[Dict[str, Any]] = field(default_factory=list)
    summary: str = ""
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ResultAggregator:
    """
    结果聚合器
    
    负责收集和整合多个子代理的执行结果。
    提供结果验证、质量评估和格式转换等功能。
    
    聚合策略：
    1. 按状态分类结果
    2. 移除重复结果
    3. 计算质量分数
    4. 生成摘要报告
    5. 统一输出格式
    
    Example:
        aggregator = ResultAggregator()
        
        # 聚合执行结果
        result = aggregator.aggregate(execution_results)
        
        # 检查总体状态
        print(f"成功: {result.success_count}/{result.total_count}")
        
        # 获取摘要
        print(result.summary)
    """
    
    def __init__(
        self,
        enable_deduplication: bool = True,
        quality_threshold: float = 0.6
    ):
        """
        初始化结果聚合器
        
        Args:
            enable_deduplication: 是否启用去重
            quality_threshold: 质量分数阈值
        """
        self.enable_deduplication = enable_deduplication
        self.quality_threshold = quality_threshold
        
        # 去重哈希记录
        self.result_hashes: set = set()
        
        # 聚合历史
        self.aggregation_history: List[Dict] = []
        
        logger.info("结果聚合器初始化完成")
    
    def aggregate(
        self,
        execution_result: Dict[str, Any]
    ) -> AggregatedResult:
        """
        聚合执行结果
        
        这是聚合器的主要接口，将执行结果转换为标准化的聚合结果。
        
        Args:
            execution_result: 执行结果字典，包含：
                - results: 详细结果列表
                - mode: 执行模式
                - total: 总任务数
                - success: 成功数
                - failed: 失败数
        
        Returns:
            AggregatedResult: 聚合后的结果
        """
        results = execution_result.get("results", [])
        
        # 分类结果
        successful_results = []
        failed_results = []
        
        for result in results:
            if self.enable_deduplication:
                # 去重检查
                result_hash = self._hash_result(result)
                if result_hash in self.result_hashes:
                    logger.debug(f"跳过重复结果: {result_hash}")
                    continue
                self.result_hashes.add(result_hash)
            
            if result.get("success"):
                successful_results.append(result)
            else:
                failed_results.append(result)
        
        # 计算状态
        overall_status = self._determine_overall_status(
            successful_results, failed_results, len(results)
        )
        
        # 收集错误
        errors = self._collect_errors(failed_results)
        
        # 生成摘要
        summary = self._generate_summary(
            overall_status,
            successful_results,
            failed_results,
            execution_result.get("mode", "unknown")
        )
        
        # 创建聚合结果
        aggregated = AggregatedResult(
            overall_status=overall_status,
            total_count=len(results),
            success_count=len(successful_results),
            failed_count=len(failed_results),
            results=results,
            summary=summary,
            errors=errors,
            metadata={
                "mode": execution_result.get("mode"),
                "task_breakdown": execution_result.get("task_breakdown"),
                "cpu_utilization": execution_result.get("cpu_utilization"),
                "timestamp": datetime.now().isoformat(),
            }
        )
        
        # 记录历史
        self.aggregation_history.append({
            "timestamp": datetime.now(),
            "result": aggregated,
        })
        
        logger.info(
            f"结果聚合完成: 成功 {aggregated.success_count}/{aggregated.total_count}"
        )
        
        return aggregated
    
    def _hash_result(self, result: Dict[str, Any]) -> str:
        """
        计算结果哈希值
        
        用于去重检测。
        
        Args:
            result: 结果字典
        
        Returns:
            str: 哈希字符串
        """
        # 提取关键字段
        key_fields = {
            "agent": result.get("agent"),
            "task_type": result.get("task_type"),
            "success": result.get("success"),
        }
        
        # 生成哈希
        content = json.dumps(key_fields, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()
    
    def _determine_overall_status(
        self,
        successful: List[Dict],
        failed: List[Dict],
        total: int
    ) -> ResultStatus:
        """
        确定总体状态
        
        Args:
            successful: 成功的结果列表
            failed: 失败的结果列表
            total: 总数
        
        Returns:
            ResultStatus: 总体状态
        """
        if total == 0:
            return ResultStatus.SUCCESS
        
        success_rate = len(successful) / total
        
        if success_rate == 1.0:
            return ResultStatus.SUCCESS
        elif success_rate >= self.quality_threshold:
            return ResultStatus.PARTIAL
        elif len(failed) == 0:
            return ResultStatus.SUCCESS
        else:
            return ResultStatus.FAILED
    
    def _collect_errors(self, failed_results: List[Dict]) -> List[str]:
        """
        收集错误信息
        
        Args:
            failed_results: 失败的结果列表
        
        Returns:
            List[str]: 错误信息列表
        """
        errors = []
        
        for result in failed_results:
            agent = result.get("agent", "unknown")
            error = result.get("error", "未知错误")
            errors.append(f"[{agent}] {error}")
        
        return errors
    
    def _generate_summary(
        self,
        status: ResultStatus,
        successful: List[Dict],
        failed: List[Dict],
        mode: str
    ) -> str:
        """
        生成结果摘要
        
        Args:
            status: 总体状态
            successful: 成功的结果列表
            failed: 失败的结果列表
            mode: 执行模式
        
        Returns:
            str: 摘要文本
        """
        total = len(successful) + len(failed)
        
        status_desc = {
            ResultStatus.SUCCESS: "全部成功",
            ResultStatus.PARTIAL: "部分成功",
            ResultStatus.FAILED: "大部分失败",
            ResultStatus.TIMEOUT: "存在超时",
            ResultStatus.ERROR: "存在错误",
        }.get(status, "未知状态")
        
        # 统计各代理的成功情况
        agent_stats: Dict[str, Dict] = {}
        for result in successful + failed:
            agent = result.get("agent", "unknown")
            if agent not in agent_stats:
                agent_stats[agent] = {"success": 0, "failed": 0}
            
            if result.get("success"):
                agent_stats[agent]["success"] += 1
            else:
                agent_stats[agent]["failed"] += 1
        
        # 生成摘要
        lines = [
            f"执行模式: {mode}",
            f"总体状态: {status_desc}",
            f"成功: {len(successful)}/{total}",
        ]
        
        # 添加各代理统计
        for agent, stats in agent_stats.items():
            lines.append(f"  - {agent}: {stats['success']} 成功, {stats['failed']} 失败")
        
        # 添加失败信息
        if failed:
            lines.append(f"失败任务数: {len(failed)}")
        
        return "\n".join(lines)
    
    def merge_results(
        self,
        results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        合并多个结果字典
        
        将多个结果合并为一个统一的结果。
        
        Args:
            results: 结果字典列表
        
        Returns:
            Dict[str, Any]: 合并后的结果
        """
        merged = {
            "mode": "merged",
            "total": 0,
            "success": 0,
            "failed": 0,
            "results": [],
            "merged_from": len(results),
        }
        
        for result in results:
            if isinstance(result, dict):
                merged["total"] += result.get("total", 0)
                merged["success"] += result.get("success", 0)
                merged["failed"] += result.get("failed", 0)
                merged["results"].extend(result.get("results", []))
        
        # 计算任务分布
        task_breakdown = {"cpu_bound": 0, "io_bound": 0}
        for result in results:
            breakdown = result.get("task_breakdown", {})
            task_breakdown["cpu_bound"] += breakdown.get("cpu_bound", 0)
            task_breakdown["io_bound"] += breakdown.get("io_bound", 0)
        
        merged["task_breakdown"] = task_breakdown
        
        return merged
    
    def extract_key_outputs(
        self,
        result: AggregatedResult
    ) -> Dict[str, Any]:
        """
        提取关键输出
        
        从聚合结果中提取关键输出信息。
        
        Args:
            result: 聚合结果
        
        Returns:
            Dict: 关键输出字典
        """
        outputs = {
            "status": result.overall_status.value,
            "summary": result.summary,
            "errors": result.errors,
            "agent_outputs": {},
        }
        
        # 提取各代理的输出
        for item in result.results:
            agent = item.get("agent", "unknown")
            if agent not in outputs["agent_outputs"]:
                outputs["agent_outputs"][agent] = []
            
            if item.get("success"):
                outputs["agent_outputs"][agent].append({
                    "success": True,
                    "output": item.get("result"),
                })
            else:
                outputs["agent_outputs"][agent].append({
                    "success": False,
                    "error": item.get("error"),
                })
        
        return outputs
    
    def validate_results(
        self,
        result: AggregatedResult,
        required_agents: List[str] = None
    ) -> Dict[str, Any]:
        """
        验证结果完整性
        
        检查是否包含所有必需代理的结果。
        
        Args:
            result: 聚合结果
            required_agents: 必需包含的代理列表
        
        Returns:
            Dict: 验证结果
        """
        validation = {
            "is_valid": True,
            "missing_agents": [],
            "warnings": [],
            "errors": [],
        }
        
        if not required_agents:
            return validation
        
        # 获取实际执行的代理
        executed_agents = set(item.get("agent") for item in result.results)
        
        # 检查必需代理
        for agent in required_agents:
            if agent not in executed_agents:
                validation["missing_agents"].append(agent)
                validation["is_valid"] = False
        
        # 检查失败率
        if result.failed_count > 0:
            failure_rate = result.failed_count / result.total_count
            if failure_rate > 0.5:
                validation["warnings"].append(
                    f"失败率较高: {failure_rate:.1%}"
                )
        
        # 生成错误信息
        if validation["missing_agents"]:
            validation["errors"].append(
                f"缺少必需代理的结果: {', '.join(validation['missing_agents'])}"
            )
        
        return validation
    
    def format_for_output(
        self,
        result: AggregatedResult,
        format: str = "text"
    ) -> Union[str, Dict]:
        """
        格式化输出
        
        将结果格式化为指定的输出格式。
        
        Args:
            result: 聚合结果
            format: 输出格式（text/json/markdown）
        
        Returns:
            Union[str, Dict]: 格式化后的结果
        """
        if format == "json":
            return {
                "status": result.overall_status.value,
                "total": result.total_count,
                "success": result.success_count,
                "failed": result.failed_count,
                "summary": result.summary,
                "errors": result.errors,
                "metadata": result.metadata,
            }
        
        elif format == "markdown":
            lines = [
                "## 执行结果\n",
                f"**状态**: {result.overall_status.value}",
                f"**总计**: {result.total_count}",
                f"**成功**: {result.success_count}",
                f"**失败**: {result.failed_count}",
                "",
                "### 摘要\n",
                result.summary,
                "",
            ]
            
            if result.errors:
                lines.append("### 错误\n")
                for error in result.errors:
                    lines.append(f"- {error}")
                lines.append("")
            
            return "\n".join(lines)
        
        else:  # text
            return result.summary
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取聚合统计信息
        
        Returns:
            Dict: 统计信息
        """
        return {
            "total_aggregations": len(self.aggregation_history),
            "deduplication_hashes": len(self.result_hashes),
            "config": {
                "enable_deduplication": self.enable_deduplication,
                "quality_threshold": self.quality_threshold,
            },
        }
    
    def clear(self):
        """清空聚合器状态"""
        self.result_hashes.clear()
        self.aggregation_history.clear()
        logger.info("聚合器状态已清空")


def create_result_aggregator(
    enable_deduplication: bool = True,
    quality_threshold: float = 0.6
) -> ResultAggregator:
    """
    创建结果聚合器
    
    工厂函数，简化聚合器的创建过程。
    
    Args:
        enable_deduplication: 是否启用去重
        quality_threshold: 质量分数阈值
    
    Returns:
        ResultAggregator: 聚合器实例
    """
    return ResultAggregator(
        enable_deduplication=enable_deduplication,
        quality_threshold=quality_threshold,
    )
