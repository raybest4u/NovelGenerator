# core/cache_manager.py
"""
统一的缓存管理系统
替换项目中分散的缓存实现
"""
import time
import json
import hashlib
import asyncio
from typing import Any, Dict, Optional, Callable, Union
from functools import wraps
from loguru import logger
from threading import Lock


class CacheManager:
    """统一缓存管理器"""

    def __init__(self):
        self._caches: Dict[str, Dict[str, tuple]] = {}
        self._locks: Dict[str, Lock] = {}
        self._default_expire = 3600  # 1小时
        self._cleanup_interval = 600  # 10分钟清理一次
        self._last_cleanup = time.time()

    def _get_lock(self, namespace: str) -> Lock:
        """获取命名空间锁"""
        if namespace not in self._locks:
            self._locks[namespace] = Lock()
        return self._locks[namespace]

    def get_cache(self, namespace: str) -> Dict[str, tuple]:
        """获取命名空间缓存"""
        if namespace not in self._caches:
            self._caches[namespace] = {}
        return self._caches[namespace]

    def generate_cache_key(self, *args, **kwargs) -> str:
        """生成缓存键"""
        try:
            cache_data = {'args': args, 'kwargs': kwargs}
            cache_str = json.dumps(cache_data, sort_keys=True, default=str)
            return hashlib.md5(cache_str.encode()).hexdigest()
        except Exception as e:
            # 如果序列化失败，使用字符串表示
            logger.warning(f"缓存键生成失败，使用fallback: {e}")
            return hashlib.md5(str(cache_data).encode()).hexdigest()

    def get(self, namespace: str, key: str, expire_time: int = None) -> Optional[Any]:
        """获取缓存值"""
        with self._get_lock(namespace):
            cache = self.get_cache(namespace)
            if key in cache:
                value, timestamp = cache[key]
                expire_time = expire_time or self._default_expire
                if time.time() - timestamp < expire_time:
                    logger.debug(f"缓存命中: {namespace}.{key[:8]}")
                    return value
                else:
                    # 缓存已过期
                    del cache[key]
                    logger.debug(f"缓存过期删除: {namespace}.{key[:8]}")
        return None

    def set(self, namespace: str, key: str, value: Any):
        """设置缓存值"""
        with self._get_lock(namespace):
            cache = self.get_cache(namespace)
            cache[key] = (value, time.time())
            logger.debug(f"缓存设置: {namespace}.{key[:8]}")

    def delete(self, namespace: str, key: str = None):
        """删除缓存"""
        with self._get_lock(namespace):
            cache = self.get_cache(namespace)
            if key is None:
                # 清空整个命名空间
                cache.clear()
                logger.info(f"清空缓存命名空间: {namespace}")
            elif key in cache:
                del cache[key]
                logger.debug(f"删除缓存项: {namespace}.{key[:8]}")

    def clear_expired(self, namespace: str = None, expire_time: int = None):
        """清理过期缓存"""
        expire_time = expire_time or self._default_expire
        current_time = time.time()

        if namespace:
            namespaces = [namespace]
        else:
            namespaces = list(self._caches.keys())

        total_cleared = 0
        for ns in namespaces:
            with self._get_lock(ns):
                cache = self.get_cache(ns)
                expired_keys = [k for k, (_, ts) in cache.items() if
                                current_time - ts >= expire_time]
                for k in expired_keys:
                    del cache[k]
                total_cleared += len(expired_keys)

        if total_cleared > 0:
            logger.info(f"清理过期缓存项: {total_cleared} 个")

    def auto_cleanup(self):
        """自动清理（在需要时调用）"""
        current_time = time.time()
        if current_time - self._last_cleanup > self._cleanup_interval:
            self.clear_expired()
            self._last_cleanup = current_time

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        stats = {
            "namespaces": len(self._caches),
            "total_items": sum(len(cache) for cache in self._caches.values()),
            "namespace_details": {}
        }

        for namespace, cache in self._caches.items():
            stats["namespace_details"][namespace] = len(cache)

        return stats


# 全局缓存管理器实例
_cache_manager = CacheManager()


def get_cache_manager() -> CacheManager:
    """获取全局缓存管理器"""
    return _cache_manager


def cached(namespace: str = "default", expire_seconds: int = 3600, key_func: Callable = None):
    """统一缓存装饰器

    Args:
        namespace: 缓存命名空间
        expire_seconds: 过期时间（秒）
        key_func: 自定义键生成函数
    """

    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache_manager = get_cache_manager()

            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = cache_manager.generate_cache_key(*args, **kwargs)

            # 自动清理过期缓存
            cache_manager.auto_cleanup()

            # 尝试从缓存获取
            cached_result = cache_manager.get(namespace, cache_key, expire_seconds)
            if cached_result is not None:
                return cached_result

            # 执行函数
            result = await func(*args, **kwargs)

            # 存入缓存
            cache_manager.set(namespace, cache_key, result)

            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache_manager = get_cache_manager()

            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = cache_manager.generate_cache_key(*args, **kwargs)

            # 自动清理过期缓存
            cache_manager.auto_cleanup()

            # 尝试从缓存获取
            cached_result = cache_manager.get(namespace, cache_key, expire_seconds)
            if cached_result is not None:
                return cached_result

            # 执行函数
            result = func(*args, **kwargs)

            # 存入缓存
            cache_manager.set(namespace, cache_key, result)

            return result

        # 根据函数类型返回对应的包装器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def cache_result(namespace: str = "default", expire_seconds: int = 3600):
    """简化的缓存装饰器（向后兼容）"""
    return cached(namespace, expire_seconds)


def method_cache(expire_seconds: int = 3600):
    """方法缓存装饰器（向后兼容）"""

    def decorator(func):
        # 使用方法所属类名作为命名空间
        namespace = f"method_{func.__qualname__}"
        return cached(namespace, expire_seconds)(func)

    return decorator


# 清理接口
def clear_cache(namespace: str = None):
    """清理缓存"""
    cache_manager = get_cache_manager()
    if namespace:
        cache_manager.delete(namespace)
    else:
        for ns in list(cache_manager._caches.keys()):
            cache_manager.delete(ns)


def get_cache_stats() -> Dict[str, Any]:
    """获取缓存统计"""
    return get_cache_manager().get_stats()
