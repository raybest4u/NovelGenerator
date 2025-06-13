# modules/plot/tools.py
"""
情节规划工具注册模块
"""
from loguru import logger

from core.tool_registry import ToolRegistry
from .story_planner import StoryPlannerTool


def register_plot_tools(registry: ToolRegistry):
    """注册情节规划相关工具"""

    # 注册故事规划工具
    try:
        registry.register(StoryPlannerTool())
        logger.debug("故事规划工具注册成功")
    except Exception as e:
        logger.error(f"故事规划工具注册失败: {e}")

    # 安全地尝试注册其他工具
    _safe_register_tool(registry, "conflict_generator", "ConflictGeneratorTool")
    _safe_register_tool(registry, "arc_manager", "ArcManagerTool")


def _safe_register_tool(registry: ToolRegistry, module_name: str, class_name: str):
    """安全注册工具，避免导入错误"""
    try:
        module = __import__(f"modules.plot.{module_name}", fromlist=[class_name])
        tool_class = getattr(module, class_name)
        registry.register(tool_class())
        logger.debug(f"{class_name} 注册成功")
    except (ImportError, AttributeError) as e:
        logger.warning(f"{class_name} 注册跳过 - 模块不存在: {e}")
