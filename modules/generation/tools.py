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
    """注册生成增强工具"""

    # 注册多样性增强工具
    registry.register(DiversityEnhancerTool())

    # 注册增强版故事生成器
    registry.register(EnhancedStoryGeneratorTool())

    # 可以添加更多生成相关工具...



