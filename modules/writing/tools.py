# modules/writing/tools.py
"""
写作工具模块 - 使用新的抽象基类
"""
from core.tool_registry import ToolRegistry




# ============================================================================
# 工具注册函数
# ============================================================================

def register_writing_tools(registry: ToolRegistry):
    """注册写作相关工具"""


    # 注册章节写作工具
    try:
        from .chapter_writer import ChapterWriterTool
        registry.register(ChapterWriterTool())
    except (ImportError, NameError, AttributeError):
        pass

    # 注册其他写作工具（如果存在）
    try:
        from .scene_generator import SceneGeneratorTool
        registry.register(SceneGeneratorTool())
    except (ImportError, NameError):
        pass

    try:
        from .dialogue_writer import DialogueWriterTool
        registry.register(DialogueWriterTool())
    except (ImportError, NameError):
        pass

    try:
        from .description_writer import DescriptionWriterTool
        registry.register(DescriptionWriterTool())
    except (ImportError, NameError):
        pass


