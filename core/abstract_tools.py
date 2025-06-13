# core/abstract_tools.py
"""
抽象工具基类，为常见工具类型提供模板
减少重复代码，统一接口
"""
from abc import abstractmethod
from typing import Dict, Any, Optional, List
from core.base_tools import AsyncTool, ToolDefinition, ToolParameter
from core.cache_manager import cached


class ContentGeneratorTool(AsyncTool):
    """内容生成工具基类"""

    @property
    def common_parameters(self) -> List[ToolParameter]:
        """通用参数定义"""
        return [
            ToolParameter(
                name="content_type",
                type="string",
                description="内容类型",
                required=True
            ),
            ToolParameter(
                name="context",
                type="object",
                description="生成上下文",
                required=False,
                default={}
            ),
            ToolParameter(
                name="style",
                type="string",
                description="生成风格",
                required=False,
                default="default"
            ),
            ToolParameter(
                name="word_count",
                type="integer",
                description="目标字数",
                required=False,
                default=1000
            )
        ]

    @abstractmethod
    async def generate_content(self, content_type: str, context: Dict[str, Any],
                               style: str, word_count: int) -> Any:
        """生成内容的核心方法 - 子类必须实现"""
        pass

    async def execute(self, parameters: Dict[str, Any],
                      context: Optional[Dict[str, Any]] = None) -> Any:
        """统一的执行逻辑"""
        content_type = parameters.get("content_type")
        gen_context = parameters.get("context", {})
        style = parameters.get("style", "default")
        word_count = parameters.get("word_count", 1000)

        # 合并外部上下文
        if context:
            gen_context.update(context)

        return await self.generate_content(content_type, gen_context, style, word_count)


class AnalyzerTool(AsyncTool):
    """分析工具基类"""

    @property
    def common_parameters(self) -> List[ToolParameter]:
        """通用参数定义"""
        return [
            ToolParameter(
                name="data",
                type="any",
                description="要分析的数据",
                required=True
            ),
            ToolParameter(
                name="analysis_type",
                type="string",
                description="分析类型",
                required=True
            ),
            ToolParameter(
                name="detailed",
                type="boolean",
                description="是否返回详细分析",
                required=False,
                default=False
            )
        ]

    @abstractmethod
    async def analyze_data(self, data: Any, analysis_type: str, detailed: bool = False) -> Dict[
        str, Any]:
        """分析数据的核心方法 - 子类必须实现"""
        pass

    async def execute(self, parameters: Dict[str, Any],
                      context: Optional[Dict[str, Any]] = None) -> Any:
        """统一的执行逻辑"""
        data = parameters.get("data")
        analysis_type = parameters.get("analysis_type")
        detailed = parameters.get("detailed", False)

        return await self.analyze_data(data, analysis_type, detailed)


class ManagerTool(AsyncTool):
    """管理工具基类"""

    @property
    def common_parameters(self) -> List[ToolParameter]:
        """通用参数定义"""
        return [
            ToolParameter(
                name="action",
                type="string",
                description="操作类型 (create/read/update/delete/list)",
                required=True,
                enum=["create", "read", "update", "delete", "list"]
            ),
            ToolParameter(
                name="resource_id",
                type="string",
                description="资源ID",
                required=False
            ),
            ToolParameter(
                name="resource_data",
                type="object",
                description="资源数据",
                required=False,
                default={}
            )
        ]

    @abstractmethod
    async def manage_resource(self, action: str, resource_id: Optional[str] = None,
                              resource_data: Dict[str, Any] = None) -> Any:
        """资源管理的核心方法 - 子类必须实现"""
        pass

    async def execute(self, parameters: Dict[str, Any],
                      context: Optional[Dict[str, Any]] = None) -> Any:
        """统一的执行逻辑"""
        action = parameters.get("action")
        resource_id = parameters.get("resource_id")
        resource_data = parameters.get("resource_data", {})

        return await self.manage_resource(action, resource_id, resource_data)
