# modules/plot/tools.py
"""
情节规划工具注册模块
"""

from core.tool_registry import ToolRegistry
from .story_planner import StoryPlannerTool


def register_plot_tools(registry: ToolRegistry):
    """注册情节规划相关工具"""

    # 注册故事规划工具
    registry.register(StoryPlannerTool())

    # 注册其他情节工具（如果存在）
    try:
        from .conflict_generator import ConflictGeneratorTool
        registry.register(ConflictGeneratorTool())
    except (ImportError, NameError):
        pass

    try:
        from .arc_manager import ArcManagerTool
        registry.register(ArcManagerTool())
    except (ImportError, NameError):
        pass
