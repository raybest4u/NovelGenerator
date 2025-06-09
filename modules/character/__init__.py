# modules/character/__init__.py
"""
角色管理模块
负责创建和管理小说中的角色，包括主角、配角、反派等
"""

from .character_creator import CharacterCreator, CharacterCreatorTool
from .relationship import RelationshipManager, RelationshipTool
from .development import CharacterDevelopment, CharacterDevelopmentTool

__all__ = [
    'CharacterCreator', 'CharacterCreatorTool',
    'RelationshipManager', 'RelationshipTool',
    'CharacterDevelopment', 'CharacterDevelopmentTool'
]

