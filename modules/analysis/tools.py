# modules/analysis/tools.py
"""
分析工具注册模块
"""

from core.tool_registry import ToolRegistry
from .consistency_checker import ConsistencyCheckerTool


def register_analysis_tools(registry: ToolRegistry):
    """注册分析相关工具"""

    # 注册一致性检查工具
    registry.register(ConsistencyCheckerTool())

    # 注册其他分析工具（如果存在）
    try:
        from .quality_analyzer import QualityAnalyzerTool
        registry.register(QualityAnalyzerTool())
    except (ImportError, NameError):
        pass
