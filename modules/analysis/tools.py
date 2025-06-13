# modules/analysis/tools.py
"""
分析工具注册模块
"""
from loguru import logger

from core.tool_registry import ToolRegistry
from .consistency_checker import ConsistencyCheckerTool


def register_analysis_tools(registry: ToolRegistry):
    """注册分析相关工具"""

    try:
        from .consistency_checker import ConsistencyCheckerTool
        registry.register(ConsistencyCheckerTool())
        logger.debug("一致性检查工具注册成功")
    except (ImportError, AttributeError) as e:
        logger.warning(f"一致性检查工具注册失败: {e}")

    try:
        from .quality_analyzer import QualityAnalyzerTool
        registry.register(QualityAnalyzerTool())
        logger.debug("质量分析工具注册成功")
    except (ImportError, AttributeError) as e:
        logger.warning(f"质量分析工具注册失败: {e}")
