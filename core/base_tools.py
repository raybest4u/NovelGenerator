# core/base_tools.py - 重构版本
"""
统一的工具基类定义 - 消除重复代码
"""
import asyncio
import functools
import hashlib
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from functools import wraps
from typing import Any, Dict, List, Optional, Type, Callable
from pydantic import BaseModel, Field
from loguru import logger


@dataclass
class ToolCall:
    """工具调用信息"""
    id: str
    name: str
    parameters: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ToolResponse:
    """工具响应信息"""
    id: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class ToolParameter(BaseModel):
    """工具参数定义"""
    name: str = Field(..., description="参数名称")
    type: str = Field(..., description="参数类型")
    description: str = Field(..., description="参数描述")
    required: bool = Field(True, description="是否必需")
    default: Any = Field(None, description="默认值")
    enum: Optional[List[Any]] = Field(None, description="枚举值")


class ToolDefinition(BaseModel):
    """工具定义"""
    name: str = Field(..., description="工具名称")
    description: str = Field(..., description="工具描述")
    category: str = Field("general", description="工具类别")
    version: str = Field("1.0.0", description="工具版本")
    parameters: List[ToolParameter] = Field(default_factory=list, description="参数列表")
    examples: List[Dict[str, Any]] = Field(default_factory=list, description="使用示例")
    tags: List[str] = Field(default_factory=list, description="标签")


class BaseTool(ABC):
    """统一的工具基类"""

    def __init__(self):
        self._definition: Optional[ToolDefinition] = None
        self._context: Dict[str, Any] = {}

    @property
    @abstractmethod
    def definition(self) -> ToolDefinition:
        """工具定义"""
        pass

    @abstractmethod
    async def execute(self, parameters: Dict[str, Any],
                      context: Optional[Dict[str, Any]] = None) -> Any:
        """执行工具"""
        pass

    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """验证参数"""
        required_params = [p.name for p in self.definition.parameters if p.required]
        missing_params = [p for p in required_params if p not in parameters]

        if missing_params:
            raise ValueError(f"缺少必需参数: {missing_params}")

        return True

    def set_context(self, context: Dict[str, Any]):
        """设置上下文"""
        self._context.update(context or {})

    def get_context(self, key: str = None) -> Any:
        """获取上下文"""
        if key:
            return self._context.get(key)
        return self._context.copy()

    async def pre_execute(self, parameters: Dict[str, Any],
                          context: Optional[Dict[str, Any]] = None):
        """执行前的准备工作"""
        self.validate_parameters(parameters)
        if context:
            self.set_context(context)

    async def post_execute(self, result: Any, parameters: Dict[str, Any]) -> Any:
        """执行后的处理工作"""
        return result

    async def on_error(self, error: Exception, parameters: Dict[str, Any]) -> Optional[Any]:
        """错误处理"""
        logger.error(f"工具 {self.definition.name} 执行失败: {error}")
        return None

    async def safe_execute(self, parameters: Dict[str, Any],
                           context: Optional[Dict[str, Any]] = None) -> ToolResponse:
        """安全执行工具"""
        call_id = f"{self.definition.name}_{int(time.time() * 1000)}"
        start_time = time.time()

        try:
            await self.pre_execute(parameters, context)
            result = await self.execute(parameters, context)
            result = await self.post_execute(result, parameters)

            execution_time = time.time() - start_time

            return ToolResponse(
                id=call_id,
                success=True,
                result=result,
                execution_time=execution_time
            )

        except Exception as e:
            logger.error(f"工具执行失败: {self.definition.name} - {e}")

            # 尝试错误处理
            error_result = await self.on_error(e, parameters)

            execution_time = time.time() - start_time

            return ToolResponse(
                id=call_id,
                success=False,
                error=str(e),
                result=error_result,
                execution_time=execution_time
            )


class AsyncTool(BaseTool):
    """异步工具基类 - 现在继承自统一的BaseTool"""
    pass  # 所有功能已在BaseTool中实现


# 工具构建器 - 保留一个版本
class ToolBuilder:
    """工具构建器"""

    def __init__(self):
        self.definition = ToolDefinition(name="", description="")
        self.execute_func = None

    def name(self, name: str):
        """设置名称"""
        self.definition.name = name
        return self

    def description(self, description: str):
        """设置描述"""
        self.definition.description = description
        return self

    def category(self, category: str):
        """设置类别"""
        self.definition.category = category
        return self

    def parameter(self, name: str, type: str, description: str, required: bool = True,
                  default: Any = None):
        """添加参数"""
        param = ToolParameter(
            name=name,
            type=type,
            description=description,
            required=required,
            default=default
        )
        self.definition.parameters.append(param)
        return self

    def example(self, parameters: Dict[str, Any], result: Any):
        """添加示例"""
        self.definition.examples.append({
            "parameters": parameters,
            "result": result
        })
        return self

    def tag(self, *tags: str):
        """添加标签"""
        self.definition.tags.extend(tags)
        return self

    def execute(self, func: callable):
        """设置执行函数"""
        self.execute_func = func
        return self

    def build(self) -> BaseTool:
        """构建工具"""
        if not self.definition.name:
            raise ValueError("工具名称不能为空")

        if not self.execute_func:
            raise ValueError("必须设置执行函数")

        class DynamicTool(AsyncTool):
            def __init__(self, definition, execute_func):
                super().__init__()
                self._definition = definition
                self._execute_func = execute_func

            @property
            def definition(self) -> ToolDefinition:
                return self._definition

            async def execute(self, parameters: Dict[str, Any],
                              context: Optional[Dict[str, Any]] = None) -> Any:
                if asyncio.iscoroutinefunction(self._execute_func):
                    return await self._execute_func(parameters, context)
                else:
                    return self._execute_func(parameters, context)

        return DynamicTool(self.definition, self.execute_func)


def build_tool() -> ToolBuilder:
    """创建工具构建器"""
    return ToolBuilder()


# 重试装饰器 - 统一版本
def retry(max_attempts: int = 3, delay: float = 1.0):
    """重试装饰器"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(f"操作失败，正在重试 ({attempt + 1}/{max_attempts}): {e}")
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"操作彻底失败，已重试 {max_attempts} 次: {e}")
                        raise last_exception

            return None

        return wrapper

    return decorator


class MethodCache:
    """方法缓存装饰器"""

    def __init__(self, maxsize: int = 128, ttl: Optional[int] = None):
        self.maxsize = maxsize
        self.ttl = ttl
        self.cache: Dict[str, Any] = {}

    def __call__(self, func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = self._make_key(func.__name__, args, kwargs)

            # 检查缓存
            if cache_key in self.cache:
                return self.cache[cache_key]

            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            self.cache[cache_key] = result

            # 如果超过最大缓存大小，清理旧条目
            if len(self.cache) > self.maxsize:
                # 简单的 FIFO 策略
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]

            return result

        return wrapper

    def _make_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """生成缓存键"""
        key_parts = [func_name]
        key_parts.extend(str(arg) for arg in args)
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        return "|".join(key_parts)


# 简化版本的 method_cache 函数
def method_cache(maxsize: int = 128, ttl: Optional[int] = None):
    """方法缓存装饰器工厂函数"""
    return MethodCache(maxsize=maxsize, ttl=ttl)
