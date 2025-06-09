# modules/writing/__init__.py
"""
写作模块
负责实际的小说内容生成，包括章节、场景、对话、描述等
"""

from .chapter_writer import ChapterWriter, ChapterWriterTool
from .scene_generator import SceneGenerator, SceneGeneratorTool
from .dialogue_writer import DialogueWriter, DialogueWriterTool
from .description_writer import DescriptionWriter, DescriptionWriterTool

__all__ = [
    'ChapterWriter', 'ChapterWriterTool',
    'SceneGenerator', 'SceneGeneratorTool',
    'DialogueWriter', 'DialogueWriterTool',
    'DescriptionWriter', 'DescriptionWriterTool'
]

