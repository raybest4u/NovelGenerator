# core/tool_registry.py
"""
完整的工具注册中心实现
提供工具管理、执行、监控等功能
"""
import time
import asyncio
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict

from loguru import logger
from core.base_tools import BaseTool, ToolDefinition, ToolCall, ToolResponse


@dataclass
class ToolExecutionStats:
    """工具执行统计"""
    tool_name: str
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_execution_time: float = 0.0
    average_execution_time: float = 0.0
    last_called: Optional[datetime] = None
    error_messages: List[str] = field(default_factory=list)


@dataclass
class RegistryStats:
    """注册表统计"""
    total_tools: int
    categories: Dict[str, int]
    execution_stats: Dict[str, ToolExecutionStats]
    uptime: float

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "total_tools": self.total_tools,
            "categories": self.categories,
            "uptime_seconds": self.uptime,
            "execution_stats": {
                name: {
                    "total_calls": stats.total_calls,
                    "success_rate": (stats.successful_calls / max(stats.total_calls, 1)) * 100,
                    "avg_execution_time": stats.average_execution_time,
                    "last_called": stats.last_called.isoformat() if stats.last_called else None
                }
                for name, stats in self.execution_stats.items()
            }
        }


class ToolRegistry:
    """增强的工具注册中心"""

    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self.categories: Dict[str, List[str]] = defaultdict(list)
        self.aliases: Dict[str, str] = {}  # 工具别名
        self.execution_stats: Dict[str, ToolExecutionStats] = {}

        # 钩子函数
        self.hooks: Dict[str, List[Callable]] = {
            "before_register": [],
            "after_register": [],
            "before_execute": [],
            "after_execute": [],
            "on_error": []
        }

        # 启动时间
        self.start_time = time.time()

        # 工具依赖关系
        self.dependencies: Dict[str, List[str]] = {}

        logger.info("🔧 工具注册中心已初始化")

    def add_hook(self, hook_type: str, func: Callable):
        """添加钩子函数"""
        if hook_type in self.hooks:
            self.hooks[hook_type].append(func)
            logger.debug(f"添加钩子: {hook_type} -> {func.__name__}")
        else:
            logger.warning(f"未知钩子类型: {hook_type}")

    def register(self, tool: BaseTool, aliases: List[str] = None):
        """注册工具"""
        definition = tool.definition
        tool_name = definition.name

        # 执行注册前钩子
        for hook in self.hooks["before_register"]:
            try:
                hook(tool, definition)
            except Exception as e:
                logger.error(f"注册前钩子执行失败: {e}")

        # 检查工具名冲突
        if tool_name in self.tools:
            logger.warning(f"工具名冲突，将覆盖: {tool_name}")

        # 注册工具
        self.tools[tool_name] = tool

        # 按类别组织
        category = definition.category
        if tool_name not in self.categories[category]:
            self.categories[category].append(tool_name)

        # 注册别名
        if aliases:
            for alias in aliases:
                if alias in self.aliases:
                    logger.warning(f"别名冲突，将覆盖: {alias}")
                self.aliases[alias] = tool_name

        # 初始化统计
        self.execution_stats[tool_name] = ToolExecutionStats(tool_name=tool_name)

        # 执行注册后钩子
        for hook in self.hooks["after_register"]:
            try:
                hook(tool, definition)
            except Exception as e:
                logger.error(f"注册后钩子执行失败: {e}")

        logger.info(f"✅ 工具已注册: {tool_name} [{category}]")
        if aliases:
            logger.info(f"   别名: {', '.join(aliases)}")

    def unregister(self, tool_name: str):
        """注销工具"""
        if tool_name in self.tools:
            tool = self.tools[tool_name]
            category = tool.definition.category

            # 移除工具
            del self.tools[tool_name]

            # 移除分类信息
            if tool_name in self.categories[category]:
                self.categories[category].remove(tool_name)
                if not self.categories[category]:
                    del self.categories[category]

            # 移除别名
            aliases_to_remove = [alias for alias, name in self.aliases.items() if name == tool_name]
            for alias in aliases_to_remove:
                del self.aliases[alias]

            # 移除统计
            if tool_name in self.execution_stats:
                del self.execution_stats[tool_name]

            logger.info(f"❌ 工具已注销: {tool_name}")
        else:
            logger.warning(f"工具不存在: {tool_name}")

    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """获取工具（支持别名）"""
        # 直接查找
        if tool_name in self.tools:
            return self.tools[tool_name]

        # 通过别名查找
        if tool_name in self.aliases:
            real_name = self.aliases[tool_name]
            return self.tools.get(real_name)

        return None

    def list_tools(self, category: str = None, include_hidden: bool = False) -> List[
        ToolDefinition]:
        """列出工具"""
        if category:
            tool_names = self.categories.get(category, [])
            tools = [self.tools[name].definition for name in tool_names if name in self.tools]
        else:
            tools = [tool.definition for tool in self.tools.values()]

        # 过滤隐藏工具
        if not include_hidden:
            tools = [tool for tool in tools if not tool.name.startswith('_')]

        return sorted(tools, key=lambda t: t.name)

    def list_categories(self) -> List[str]:
        """列出所有类别"""
        return sorted(list(self.categories.keys()))

    def search_tools(self, query: str) -> List[ToolDefinition]:
        """搜索工具"""
        query = query.lower()
        results = []

        for tool in self.tools.values():
            definition = tool.definition

            # 搜索名称和描述
            if (query in definition.name.lower() or
                query in definition.description.lower() or
                any(query in tag.lower() for tag in definition.tags)):
                results.append(definition)

        return sorted(results, key=lambda t: t.name)

    def set_dependency(self, tool_name: str, dependencies: List[str]):
        """设置工具依赖"""
        self.dependencies[tool_name] = dependencies

    def check_dependencies(self, tool_name: str) -> bool:
        """检查工具依赖是否满足"""
        if tool_name not in self.dependencies:
            return True

        for dep in self.dependencies[tool_name]:
            if dep not in self.tools:
                logger.error(f"工具 {tool_name} 依赖 {dep} 未找到")
                return False

        return True

    async def execute_tool(self, tool_call: ToolCall,
                           context: Optional[Dict[str, Any]] = None) -> ToolResponse:
        """执行工具"""
        tool_name = tool_call.name
        tool = self.get_tool(tool_name)

        if not tool:
            return ToolResponse(
                id=tool_call.id,
                success=False,
                error=f"工具不存在: {tool_name}"
            )

        # 检查依赖
        if not self.check_dependencies(tool_name):
            return ToolResponse(
                id=tool_call.id,
                success=False,
                error=f"工具 {tool_name} 依赖检查失败"
            )

        # 获取统计对象
        stats = self.execution_stats.get(tool_name)
        if not stats:
            stats = ToolExecutionStats(tool_name=tool_name)
            self.execution_stats[tool_name] = stats

        # 更新调用计数
        stats.total_calls += 1
        stats.last_called = datetime.now()

        # 执行前钩子
        for hook in self.hooks["before_execute"]:
            try:
                await hook(tool_call, context) if asyncio.iscoroutinefunction(hook) else hook(
                    tool_call, context)
            except Exception as e:
                logger.error(f"执行前钩子失败: {e}")

        # 执行工具
        start_time = time.time()
        response = await tool.safe_execute(tool_call.parameters, context)
        execution_time = time.time() - start_time

        # 更新统计
        stats.total_execution_time += execution_time
        stats.average_execution_time = stats.total_execution_time / stats.total_calls

        if response.success:
            stats.successful_calls += 1
        else:
            stats.failed_calls += 1
            if response.error:
                stats.error_messages.append(response.error)
                # 只保留最近的10个错误消息
                if len(stats.error_messages) > 10:
                    stats.error_messages = stats.error_messages[-10:]

        # 执行后钩子
        for hook in self.hooks["after_execute"]:
            try:
                await hook(tool_call, response, context) if asyncio.iscoroutinefunction(
                    hook) else hook(tool_call, response, context)
            except Exception as e:
                logger.error(f"执行后钩子失败: {e}")

        # 错误钩子
        if not response.success:
            for hook in self.hooks["on_error"]:
                try:
                    await hook(tool_call, response, context) if asyncio.iscoroutinefunction(
                        hook) else hook(tool_call, response, context)
                except Exception as e:
                    logger.error(f"错误钩子失败: {e}")

        return response

    async def batch_execute(self, tool_calls: List[ToolCall],
                            context: Optional[Dict[str, Any]] = None) -> List[ToolResponse]:
        """批量执行工具"""
        tasks = []
        for tool_call in tool_calls:
            task = asyncio.create_task(self.execute_tool(tool_call, context))
            tasks.append(task)

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常
        results = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                results.append(ToolResponse(
                    id=tool_calls[i].id,
                    success=False,
                    error=f"批量执行异常: {str(response)}"
                ))
            else:
                results.append(response)

        return results

    def get_stats(self) -> RegistryStats:
        """获取注册表统计信息"""
        category_counts = {cat: len(tools) for cat, tools in self.categories.items()}
        uptime = time.time() - self.start_time

        return RegistryStats(
            total_tools=len(self.tools),
            categories=category_counts,
            execution_stats=self.execution_stats.copy(),
            uptime=uptime
        )

    def export_definitions(self) -> List[Dict[str, Any]]:
        """导出工具定义（用于API文档等）"""
        definitions = []
        for tool in self.tools.values():
            definition = tool.definition
            definitions.append({
                "name": definition.name,
                "description": definition.description,
                "category": definition.category,
                "version": definition.version,
                "parameters": [param.dict() for param in definition.parameters],
                "examples": definition.examples,
                "tags": definition.tags
            })

        return definitions

    def validate_all_tools(self) -> Dict[str, List[str]]:
        """验证所有工具"""
        validation_results = {}

        for tool_name, tool in self.tools.items():
            errors = []

            try:
                # 检查定义完整性
                definition = tool.definition
                if not definition.name:
                    errors.append("工具名称为空")
                if not definition.description:
                    errors.append("工具描述为空")

                # 检查参数定义
                for param in definition.parameters:
                    if not param.name:
                        errors.append(f"参数名称为空")
                    if not param.type:
                        errors.append(f"参数 {param.name} 类型为空")

                # 检查依赖
                if not self.check_dependencies(tool_name):
                    errors.append("依赖检查失败")

            except Exception as e:
                errors.append(f"验证异常: {str(e)}")

            if errors:
                validation_results[tool_name] = errors

        return validation_results


# 全局工具注册表实例
_tool_registry = ToolRegistry()


def get_tool_registry() -> ToolRegistry:
    """获取全局工具注册表"""
    return _tool_registry


def register_tool(tool: BaseTool, aliases: List[str] = None):
    """注册工具到全局注册表"""
    _tool_registry.register(tool, aliases)


def get_tool(tool_name: str) -> Optional[BaseTool]:
    """从全局注册表获取工具"""
    return _tool_registry.get_tool(tool_name)


async def execute_tool(tool_name: str, parameters: Dict[str, Any],
                       context: Optional[Dict[str, Any]] = None) -> ToolResponse:
    """直接执行工具"""
    tool_call = ToolCall(
        id=f"{tool_name}_{int(time.time() * 1000)}",
        name=tool_name,
        parameters=parameters
    )

    return await _tool_registry.execute_tool(tool_call, context)


# ============================================================================
# 工具注册装饰器
# ============================================================================

def tool(name: str = None, category: str = "general", aliases: List[str] = None,
         description: str = "", version: str = "1.0.0", tags: List[str] = None):
    """工具注册装饰器"""

    def decorator(cls):
        # 如果没有指定名称，使用类名
        tool_name = name or cls.__name__.lower().replace('tool', '')

        # 创建工具实例并注册
        tool_instance = cls()

        # 设置基本信息（如果工具类没有定义）
        if hasattr(tool_instance, '_definition') and tool_instance._definition is None:
            from core.base_tools import ToolDefinition
            tool_instance._definition = ToolDefinition(
                name=tool_name,
                description=description or cls.__doc__ or "",
                category=category,
                version=version,
                tags=tags or []
            )

        # 注册工具
        register_tool(tool_instance, aliases)

        return cls

    return decorator


# ============================================================================
# 使用示例
# ============================================================================

if __name__ == "__main__":
    # 示例：使用装饰器注册工具

    @tool(name="example_calculator", category="math", aliases=["calc"], description="简单计算器")
    class CalculatorTool:
        async def execute(self, parameters, context=None):
            operation = parameters.get("operation")
            a = parameters.get("a", 0)
            b = parameters.get("b", 0)

            if operation == "add":
                return a + b
            elif operation == "multiply":
                return a * b
            else:
                raise ValueError(f"不支持的操作: {operation}")


    # 测试注册表
    async def test_registry():
        registry = get_tool_registry()

        # 查看统计信息
        stats = registry.get_stats()
        print(f"已注册工具: {stats.total_tools}")
        print(f"工具分类: {stats.categories}")

        # 搜索工具
        calc_tools = registry.search_tools("calc")
        print(f"计算相关工具: {[t.name for t in calc_tools]}")

        # 执行工具
        result = await execute_tool("example_calculator", {
            "operation": "add",
            "a": 5,
            "b": 3
        })

        print(f"计算结果: {result.result}")
        print(f"执行成功: {result.success}")


    asyncio.run(test_registry())
