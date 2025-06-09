
# utils/performance.py
"""
性能优化工具
"""

import asyncio
import time
import functools
from typing import Dict, Any, Callable, Optional
from collections import defaultdict
from datetime import datetime, timedelta
from loguru import logger


class PerformanceOptimizer:
    """性能优化器"""

    def __init__(self):
        self.cache = {}
        self.call_stats = defaultdict(list)
        self.slow_queries = []

    def cache_result(self, ttl: int = 300):
        """结果缓存装饰器"""

        def decorator(func: Callable):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                # 生成缓存键
                cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"

                # 检查缓存
                if cache_key in self.cache:
                    result, timestamp = self.cache[cache_key]
                    if time.time() - timestamp < ttl:
                        logger.debug(f"缓存命中: {func.__name__}")
                        return result

                # 执行函数
                start_time = time.time()
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time

                # 缓存结果
                self.cache[cache_key] = (result, time.time())

                # 记录性能
                self.call_stats[func.__name__].append(execution_time)

                if execution_time > 5.0:  # 超过5秒的慢查询
                    self.slow_queries.append({
                        'function': func.__name__,
                        'args': str(args)[:100],
                        'execution_time': execution_time,
                        'timestamp': datetime.now()
                    })
                    logger.warning(f"慢查询检测: {func.__name__} 耗时 {execution_time:.2f}s")

                return result

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                # 同步版本的缓存装饰器
                cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"

                if cache_key in self.cache:
                    result, timestamp = self.cache[cache_key]
                    if time.time() - timestamp < ttl:
                        return result

                start_time = time.time()
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time

                self.cache[cache_key] = (result, time.time())
                self.call_stats[func.__name__].append(execution_time)

                return result

            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

        return decorator

    def batch_process(self, batch_size: int = 10):
        """批处理装饰器"""

        def decorator(func: Callable):
            @functools.wraps(func)
            async def wrapper(items: list, *args, **kwargs):
                results = []

                for i in range(0, len(items), batch_size):
                    batch = items[i:i + batch_size]
                    batch_results = await func(batch, *args, **kwargs)
                    results.extend(batch_results)

                    # 小延迟避免过载
                    await asyncio.sleep(0.01)

                return results

            return wrapper

        return decorator

    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        stats = {}

        for func_name, times in self.call_stats.items():
            if times:
                stats[func_name] = {
                    'call_count': len(times),
                    'avg_time': sum(times) / len(times),
                    'max_time': max(times),
                    'min_time': min(times),
                    'total_time': sum(times)
                }

        return {
            'function_stats': stats,
            'slow_queries': self.slow_queries[-10:],  # 最近10个慢查询
            'cache_size': len(self.cache)
        }

    def clear_cache(self):
        """清理缓存"""
        old_size = len(self.cache)
        self.cache.clear()
        logger.info(f"缓存已清理，释放 {old_size} 个条目")

    def cleanup_old_cache(self, max_age: int = 3600):
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = []

        for key, (result, timestamp) in self.cache.items():
            if current_time - timestamp > max_age:
                expired_keys.append(key)

        for key in expired_keys:
            del self.cache[key]

        if expired_keys:
            logger.info(f"清理过期缓存 {len(expired_keys)} 个条目")


# 全局性能优化器
performance_optimizer = PerformanceOptimizer()


def get_performance_optimizer() -> PerformanceOptimizer:
    """获取性能优化器"""
    return performance_optimizer


# 装饰器快捷方式
cache_result = performance_optimizer.cache_result
batch_process = performance_optimizer.batch_process