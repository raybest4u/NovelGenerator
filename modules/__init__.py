# ============================================================================
# modules/__init__.py - 统一模块注册
# ============================================================================

# modules/__init__.py
"""
模块工具统一注册系统
消除分散的注册代码
"""
from core.tool_registry import ToolRegistry
from loguru import logger


def register_all_tools(registry: ToolRegistry):
    """注册所有模块工具"""

    registered_count = 0

    try:
        # 角色管理模块
        from modules.character.character_creator_tool import register_character_tools
        register_character_tools(registry)
        registered_count += len([name for name in registry.tools.keys() if "character" in name])
        logger.debug("角色管理工具已注册")
    except ImportError as e:
        logger.warning(f"角色管理模块导入失败: {e}")

    try:
        # 情节规划模块
        from modules.plot.tools import register_plot_tools
        register_plot_tools(registry)
        registered_count += len(
            [name for name in registry.tools.keys() if "plot" in name or "story" in name])
        logger.debug("情节规划工具已注册")
    except ImportError as e:
        logger.warning(f"情节规划模块导入失败: {e}")

    try:
        # 写作模块
        from modules.writing.tools import register_writing_tools
        register_writing_tools(registry)
        registered_count += len(
            [name for name in registry.tools.keys() if "writing" in name or "chapter" in name])
        logger.debug("写作工具已注册")
    except ImportError as e:
        logger.warning(f"写作模块导入失败: {e}")

    try:
        # 分析工具模块
        from modules.analysis.tools import register_analysis_tools
        register_analysis_tools(registry)
        registered_count += len(
            [name for name in registry.tools.keys() if "analysis" in name or "consistency" in name])
        logger.debug("分析工具已注册")
    except ImportError as e:
        logger.warning(f"分析工具模块导入失败: {e}")

    try:
        # 生成增强模块
        from modules.generation.tools import register_generation_tools
        register_generation_tools(registry)
        registered_count += len(
            [name for name in registry.tools.keys() if "generation" in name or "diversity" in name])
        logger.debug("生成增强工具已注册")
    except ImportError as e:
        logger.warning(f"生成增强模块导入失败: {e}")

    logger.info(f"工具注册完成，共注册 {len(registry.tools)} 个工具")
