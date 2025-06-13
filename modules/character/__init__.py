# modules/character/__init__.py
"""
角色管理模块
负责创建和管理小说中的角色，包括主角、配角、反派等
"""

from .character_creator import CharacterCreator
from .character_creator_tool import CharacterCreatorTool
from .enhanced_character_creator import EnhancedCharacterCreator
from .relationship import RelationshipManager, RelationshipTool
from .development import CharacterDevelopment, CharacterDevelopmentTool

__all__ = [
    'CharacterCreator', 'EnhancedCharacterCreator','CharacterCreatorTool',
    'RelationshipManager', 'RelationshipTool',
    'CharacterDevelopment', 'CharacterDevelopmentTool'
]

