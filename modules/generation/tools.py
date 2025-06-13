# ============================================================================
# modules/generation/tools.py - 示例模块注册
# ============================================================================

# modules/generation/tools.py
"""
生成增强模块工具注册
"""
from core.tool_registry import ToolRegistry
from .diversity_enhancer import DiversityEnhancerTool
from .enhanced_story_generator import EnhancedStoryGeneratorTool


def register_generation_tools(registry: ToolRegistry):
    """注册生成增强相关工具"""

    # 注册多样性增强工具
    try:
        from .diversity_enhancer import DiversityEnhancerTool
        registry.register(DiversityEnhancerTool())
    except (ImportError, NameError):
        pass

    # 注册增强故事生成工具
    try:
        from .enhanced_story_generator import EnhancedStoryGeneratorTool
        registry.register(EnhancedStoryGeneratorTool())
    except (ImportError, NameError):
        pass



