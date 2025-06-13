# core/base_tools.py
"""
基础工具类定义
为所有工具提供统一的接口和基础功能
"""
import hashlib
from abc import ABC, abstractmethod
from functools import wraps
from typing import Dict, Any, Optional, List, Type
from dataclasses import dataclass, field
from datetime import datetime
import time
import asyncio
import json
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
    """工具基类"""

    def __init__(self):
        self._definition: Optional[ToolDefinition] = None
        self._context: Dict[str, Any] = {}

    @property
    @abstractmethod
    def definition(self) -> ToolDefinition:
        """工具定义"""
        pass

    @abstractmethod
    async def execute(self, parameters: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Any:
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

    async def pre_execute(self, parameters: Dict[str, Any], context: Optional[Dict[str, Any]] = None):
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


class AsyncTool(BaseTool):
    """异步工具基类"""

    async def safe_execute(self, parameters: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> ToolResponse:
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
                execution_time=execution_time,
                metadata={"tool_name": self.definition.name}
            )

        except Exception as e:
            execution_time = time.time() - start_time
            error_result = await self.on_error(e, parameters)

            return ToolResponse(
                id=call_id,
                success=False,
                result=error_result,
                error=str(e),
                execution_time=execution_time,
                metadata={"tool_name": self.definition.name}
            )


class ToolRegistry:
    """工具注册表"""

    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self.categories: Dict[str, List[str]] = {}
        self.hooks: Dict[str, List[callable]] = {
            "before_execute": [],
            "after_execute": [],
            "on_error": []
        }

    def register(self, tool: BaseTool):
        """注册工具"""
        definition = tool.definition

        if definition.name in self.tools:
            logger.warning(f"工具 {definition.name} 已存在，将被覆盖")

        self.tools[definition.name] = tool

        # 更新分类
        if definition.category not in self.categories:
            self.categories[definition.category] = []

        if definition.name not in self.categories[definition.category]:
            self.categories[definition.category].append(definition.name)

        logger.info(f"工具已注册: {definition.name} ({definition.category})")

    def unregister(self, tool_name: str):
        """注销工具"""
        if tool_name in self.tools:
            tool = self.tools[tool_name]
            category = tool.definition.category

            del self.tools[tool_name]

            if category in self.categories and tool_name in self.categories[category]:
                self.categories[category].remove(tool_name)
                if not self.categories[category]:
                    del self.categories[category]

            logger.info(f"工具已注销: {tool_name}")
        else:
            logger.warning(f"工具不存在: {tool_name}")

    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """获取工具"""
        return self.tools.get(tool_name)

    def list_tools(self, category: str = None) -> List[ToolDefinition]:
        """列出工具"""
        if category:
            tool_names = self.categories.get(category, [])
            return [self.tools[name].definition for name in tool_names]
        else:
            return [tool.definition for tool in self.tools.values()]

    def list_categories(self) -> List[str]:
        """列出所有类别"""
        return list(self.categories.keys())

    async def execute_tool(self, tool_call: ToolCall, context: Optional[Dict[str, Any]] = None) -> ToolResponse:
        """执行工具"""
        tool = self.get_tool(tool_call.name)

        if not tool:
            return ToolResponse(
                id=tool_call.id,
                success=False,
                error=f"工具不存在: {tool_call.name}"
            )

        # 执行前钩子
        for hook in self.hooks["before_execute"]:
            try:
                await hook(tool_call, context)
            except Exception as e:
                logger.error(f"执行前钩子失败: {e}")

        # 执行工具
        if isinstance(tool, AsyncTool):
            response = await tool.safe_execute(tool_call.parameters, context)
        else:
            # 同步工具的异步包装
            try:
                result = tool.execute(tool_call.parameters, context)
                response = ToolResponse(
                    id=tool_call.id,
                    success=True,
                    result=result
                )
            except Exception as e:
                response = ToolResponse(
                    id=tool_call.id,
                    success=False,
                    error=str(e)
                )

        # 执行后钩子
        hook_type = "after_execute" if response.success else "on_error"
        for hook in self.hooks[hook_type]:
            try:
                await hook(tool_call, response, context)
            except Exception as e:
                logger.error(f"执行后钩子失败: {e}")

        return response

    def add_hook(self, event: str, hook: callable):
        """添加钩子"""
        if event in self.hooks:
            self.hooks[event].append(hook)
        else:
            raise ValueError(f"不支持的钩子事件: {event}")

    def remove_hook(self, event: str, hook: callable):
        """移除钩子"""
        if event in self.hooks and hook in self.hooks[event]:
            self.hooks[event].remove(hook)


class ToolDecorator:
    @staticmethod
    def cached(expire_seconds: int = 300, key_func: callable = None):
        """缓存装饰器 - 支持任意方法签名"""
        cache = {}

        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # 生成缓存键
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    # 默认的缓存键生成策略
                    cache_data = {
                        'func_name': func.__name__,
                        'args': args[1:],  # 跳过 self
                        'kwargs': kwargs
                    }
                    cache_str = json.dumps(cache_data, sort_keys=True, default=str)
                    cache_key = hashlib.md5(cache_str.encode()).hexdigest()

                current_time = time.time()

                # 检查缓存
                if cache_key in cache:
                    cached_result, timestamp = cache[cache_key]
                    if current_time - timestamp < expire_seconds:
                        if hasattr(args[0], 'definition'):
                            print(f"使用缓存结果: {args[0].definition.name}.{func.__name__}")
                        return cached_result

                # 执行并缓存
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                cache[cache_key] = (result, current_time)

                # 清理过期缓存
                expired_keys = [k for k, (_, ts) in cache.items() if current_time - ts >= expire_seconds]
                for k in expired_keys:
                    del cache[k]

                return result

            return wrapper
        return decorator

    @staticmethod
    def cached_for_tool_execute(expire_seconds: int = 300):
        """专门为工具execute方法设计的缓存装饰器"""
        cache = {}

        def decorator(func):
            @wraps(func)
            async def wrapper(self, parameters: Dict[str, Any], context: Optional[Dict[str, Any]] = None):
                # 生成缓存键
                cache_key = json.dumps(parameters, sort_keys=True)
                current_time = time.time()

                # 检查缓存
                if cache_key in cache:
                    cached_result, timestamp = cache[cache_key]
                    if current_time - timestamp < expire_seconds:
                        print(f"使用缓存结果: {self.definition.name}")
                        return cached_result

                # 执行并缓存
                result = await func(self, parameters, context)
                cache[cache_key] = (result, current_time)

                # 清理过期缓存
                expired_keys = [k for k, (_, ts) in cache.items() if current_time - ts >= expire_seconds]
                for k in expired_keys:
                    del cache[k]

                return result

            return wrapper
        return decorator

    @staticmethod
    def retry(max_attempts: int = 3, delay: float = 1.0):
        """重试装饰器 - 支持任意方法签名"""
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
                            if hasattr(args[0], 'definition'):
                                print(f"工具 {args[0].definition.name}.{func.__name__} 第{attempt + 1}次执行失败，{delay}秒后重试: {e}")
                            else:
                                print(f"方法 {func.__name__} 第{attempt + 1}次执行失败，{delay}秒后重试: {e}")
                            await asyncio.sleep(delay)
                        else:
                            if hasattr(args[0], 'definition'):
                                print(f"工具 {args[0].definition.name}.{func.__name__} 重试{max_attempts}次后仍然失败: {e}")
                            else:
                                print(f"方法 {func.__name__} 重试{max_attempts}次后仍然失败: {e}")

                raise last_exception

            return wrapper
        return decorator

    @staticmethod
    def rate_limit(calls_per_minute: int = 60):
        """速率限制装饰器 - 支持任意方法签名"""
        call_times = []

        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                current_time = time.time()

                # 清理过期的调用记录
                call_times[:] = [t for t in call_times if current_time - t < 60]

                # 检查速率限制
                if len(call_times) >= calls_per_minute:
                    if hasattr(args[0], 'definition'):
                        raise Exception(f"工具 {args[0].definition.name}.{func.__name__} 超出速率限制: {calls_per_minute}次/分钟")
                    else:
                        raise Exception(f"方法 {func.__name__} 超出速率限制: {calls_per_minute}次/分钟")

                call_times.append(current_time)

                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)

            return wrapper
        return decorator


# 简单的方法级缓存装饰器
def method_cache(expire_seconds: int = 300):
    """方法级缓存装饰器 - 更简单的使用方式"""

    def decorator(func):
        cache = {}

        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_data = {
                'args': args[1:],  # 跳过 self
                'kwargs': kwargs
            }
            cache_str = json.dumps(cache_data, sort_keys=True, default=str)
            cache_key = hashlib.md5(cache_str.encode()).hexdigest()

            current_time = time.time()

            # 检查缓存
            if cache_key in cache:
                result, timestamp = cache[cache_key]
                if current_time - timestamp < expire_seconds:
                    return result

            # 执行方法
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # 缓存结果
            cache[cache_key] = (result, current_time)

            # 清理过期缓存
            expired_keys = [k for k, (_, ts) in cache.items() if
                            current_time - ts >= expire_seconds]
            for k in expired_keys:
                del cache[k]

            return result

        return wrapper

    return decorator


# 使用示例
class ExampleTool(AsyncTool):
    """示例工具，展示装饰器的正确用法"""

    def __init__(self):
        super().__init__()

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="example_tool",
            description="示例工具"
        )

    # 对于tool的execute方法，使用专门的装饰器
    @ToolDecorator.cached_for_tool_execute(expire_seconds=300)
    async def execute(self, parameters: Dict[str, Any],
                      context: Optional[Dict[str, Any]] = None) -> Any:
        return await self.do_work(parameters)

    # 对于普通方法，使用通用的缓存装饰器或简单的方法缓存
    @method_cache(expire_seconds=600)
    async def do_work(self, parameters: Dict[str, Any]) -> str:
        """执行实际工作"""
        # 模拟耗时操作
        await asyncio.sleep(1)
        return f"工作完成: {parameters}"

    # 使用重试装饰器
    @ToolDecorator.retry(max_attempts=3, delay=1.0)
    async def unreliable_operation(self, data: str) -> str:
        """可能失败的操作"""
        import random
        if random.random() < 0.5:
            raise Exception("随机失败")
        return f"成功处理: {data}"
# 工具构建器
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

    def parameter(self, name: str, type: str, description: str, required: bool = True, default: Any = None):
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

            async def execute(self, parameters: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Any:
                if asyncio.iscoroutinefunction(self._execute_func):
                    return await self._execute_func(parameters, context)
                else:
                    return self._execute_func(parameters, context)

        return DynamicTool(self.definition, self.execute_func)


# 全局工具注册表
tool_registry = ToolRegistry()


def get_tool_registry() -> ToolRegistry:
    """获取工具注册表"""
    return tool_registry


def register_tool(tool: BaseTool):
    """注册工具"""
    tool_registry.register(tool)


def build_tool() -> ToolBuilder:
    """创建工具构建器"""
    return ToolBuilder()


if __name__ == "__main__":
    # 示例：创建一个简单的工具
    async def hello_world(parameters: Dict[str, Any], context: Optional[Dict[str, Any]] = None):
        name = parameters.get("name", "World")
        return f"Hello, {name}!"

    # 使用构建器创建工具
    hello_tool = (build_tool()
                  .name("hello")
                  .description("打招呼工具")
                  .category("demo")
                  .parameter("name", "string", "姓名", required=False, default="World")
                  .example({"name": "Alice"}, "Hello, Alice!")
                  .tag("demo", "greeting")
                  .execute(hello_world)
                  .build())

    # 注册工具
    register_tool(hello_tool)

    # 测试工具
    async def test():
        registry = get_tool_registry()

        # 列出工具
        tools = registry.list_tools()
        print(f"已注册工具: {[t.name for t in tools]}")

        # 执行工具
        call = ToolCall(
            id="test_1",
            name="hello",
            parameters={"name": "MCP"}
        )

        response = await registry.execute_tool(call)
        print(f"执行结果: {response.result}")

    asyncio.run(test())
