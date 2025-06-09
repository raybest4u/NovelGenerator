
# utils/monitoring.py
"""
监控和指标收集
"""

import time
import psutil
import asyncio
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict, deque
from loguru import logger


@dataclass
class SystemMetrics:
    """系统指标"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_sent: int
    network_recv: int
    process_count: int
    load_average: float


@dataclass
class APIMetrics:
    """API指标"""
    endpoint: str
    method: str
    status_code: int
    response_time: float
    timestamp: datetime
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None


class MetricsCollector:
    """指标收集器"""

    def __init__(self, history_size: int = 1000):
        self.history_size = history_size
        self.system_metrics = deque(maxlen=history_size)
        self.api_metrics = deque(maxlen=history_size)
        self.error_counts = defaultdict(int)
        self.endpoint_stats = defaultdict(lambda: {
            'count': 0,
            'total_time': 0,
            'errors': 0
        })

        # 启动系统监控
        self._monitoring_task = None
        self.start_monitoring()

    def start_monitoring(self):
        """启动监控"""
        if self._monitoring_task is None:
            self._monitoring_task = asyncio.create_task(self._collect_system_metrics())

    def stop_monitoring(self):
        """停止监控"""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            self._monitoring_task = None

    async def _collect_system_metrics(self):
        """收集系统指标"""
        while True:
            try:
                metrics = SystemMetrics(
                    timestamp=datetime.now(),
                    cpu_percent=psutil.cpu_percent(interval=1),
                    memory_percent=psutil.virtual_memory().percent,
                    disk_percent=psutil.disk_usage('/').percent,
                    network_sent=psutil.net_io_counters().bytes_sent,
                    network_recv=psutil.net_io_counters().bytes_recv,
                    process_count=len(psutil.pids()),
                    load_average=psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0.0
                )

                self.system_metrics.append(metrics)

                # 记录性能日志
                logger.bind(type="performance").info(
                    f"CPU: {metrics.cpu_percent:.1f}% | "
                    f"Memory: {metrics.memory_percent:.1f}% | "
                    f"Disk: {metrics.disk_percent:.1f}%"
                )

                await asyncio.sleep(60)  # 每分钟收集一次

            except Exception as e:
                logger.error(f"系统指标收集失败: {e}")
                await asyncio.sleep(60)

    def record_api_call(self, endpoint: str, method: str, status_code: int,
                        response_time: float, **kwargs):
        """记录API调用"""

        metrics = APIMetrics(
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time=response_time,
            timestamp=datetime.now(),
            **kwargs
        )

        self.api_metrics.append(metrics)

        # 更新统计
        key = f"{method} {endpoint}"
        stats = self.endpoint_stats[key]
        stats['count'] += 1
        stats['total_time'] += response_time

        if status_code >= 400:
            stats['errors'] += 1
            self.error_counts[status_code] += 1

        # 记录访问日志
        logger.bind(type="access").info(
            f"{method} {endpoint} {status_code} {response_time:.3f}s"
        )

    def get_system_stats(self, minutes: int = 60) -> Dict[str, Any]:
        """获取系统统计"""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        recent_metrics = [m for m in self.system_metrics if m.timestamp > cutoff]

        if not recent_metrics:
            return {}

        return {
            "cpu_avg": sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics),
            "memory_avg": sum(m.memory_percent for m in recent_metrics) / len(recent_metrics),
            "disk_usage": recent_metrics[-1].disk_percent,
            "process_count": recent_metrics[-1].process_count,
            "sample_count": len(recent_metrics)
        }

    def get_api_stats(self, minutes: int = 60) -> Dict[str, Any]:
        """获取API统计"""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        recent_calls = [m for m in self.api_metrics if m.timestamp > cutoff]

        if not recent_calls:
            return {}

        total_calls = len(recent_calls)
        error_calls = sum(1 for m in recent_calls if m.status_code >= 400)
        avg_response_time = sum(m.response_time for m in recent_calls) / total_calls

        # 端点统计
        endpoint_counts = defaultdict(int)
        for call in recent_calls:
            endpoint_counts[f"{call.method} {call.endpoint}"] += 1

        return {
            "total_calls": total_calls,
            "error_rate": error_calls / total_calls if total_calls > 0 else 0,
            "avg_response_time": avg_response_time,
            "top_endpoints": dict(sorted(endpoint_counts.items(),
                                         key=lambda x: x[1], reverse=True)[:5])
        }

    def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        system_stats = self.get_system_stats(5)  # 最近5分钟
        api_stats = self.get_api_stats(5)

        status = "healthy"
        issues = []

        # 检查系统指标
        if system_stats:
            if system_stats["cpu_avg"] > 80:
                status = "warning"
                issues.append("CPU使用率过高")

            if system_stats["memory_avg"] > 90:
                status = "critical"
                issues.append("内存使用率过高")

            if system_stats["disk_usage"] > 85:
                status = "warning"
                issues.append("磁盘空间不足")

        # 检查API指标
        if api_stats:
            if api_stats["error_rate"] > 0.1:  # 错误率超过10%
                status = "warning" if status == "healthy" else status
                issues.append("API错误率过高")

            if api_stats["avg_response_time"] > 5.0:  # 平均响应时间超过5秒
                status = "warning" if status == "healthy" else status
                issues.append("API响应时间过长")

        return {
            "status": status,
            "issues": issues,
            "system_stats": system_stats,
            "api_stats": api_stats,
            "timestamp": datetime.now().isoformat()
        }


# 全局监控实例
metrics_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """获取指标收集器"""
    return metrics_collector

