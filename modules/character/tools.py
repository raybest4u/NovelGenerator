# modules/character/tools.py
"""
角色管理工具注册模块
"""

from core.tool_registry import ToolRegistry
from .character_creator_tool import CharacterCreatorTool
from .relationship import RelationshipTool
from .development import CharacterDevelopmentTool


def register_character_tools(registry: ToolRegistry):
    """注册角色管理相关工具"""

    # 注册角色创建工具
    registry.register(CharacterCreatorTool())

    # 注册关系管理工具（如果存在）
    try:
        registry.register(RelationshipTool())
    except (ImportError, NameError):
        pass

    # 注册角色发展工具（如果存在）
    try:
        registry.register(CharacterDevelopmentTool())
    except (ImportError, NameError):
        pass
