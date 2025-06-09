
# tests/test_writing.py
"""
写作模块测试
"""

import pytest
from unittest.mock import AsyncMock, patch
from modules.writing.chapter_writer import ChapterWriter, ChapterWriterTool
from modules.writing.scene_generator import SceneGenerator, SceneGeneratorTool


class TestChapterWriter:
    """章节写作器测试"""

    @pytest.mark.asyncio
    async def test_write_chapter(self, mock_llm_service, sample_story_outline):
        """测试章节写作"""
        with patch('modules.writing.chapter_writer.get_llm_service', return_value=mock_llm_service):
            writer = ChapterWriter()

            chapter_info = {
                "number": 1,
                "title": "第一章",
                "summary": "开始的故事",
                "key_events": ["初遇"]
            }

            chapter = await writer.write_chapter(
                chapter_info, sample_story_outline, "traditional", 3000
            )

            assert chapter.chapter_number == 1
            assert chapter.title == "第一章"
            assert len(chapter.scenes) > 0

    @pytest.mark.asyncio
    async def test_chapter_writer_tool(self, tool_registry, mock_llm_service):
        """测试章节写作工具"""
        with patch('modules.writing.chapter_writer.get_llm_service', return_value=mock_llm_service):
            tool = ChapterWriterTool()
            tool_registry.register(tool)

            from core.base_tools import ToolCall
            call = ToolCall(
                id="test_chapter",
                name="chapter_writer",
                parameters={
                    "chapter_info": {
                        "number": 1,
                        "title": "第一章"
                    },
                    "story_context": {},
                    "target_word_count": 2000
                }
            )

            response = await tool_registry.execute_tool(call)

            assert response.success
            assert "chapter" in response.result


class TestSceneGenerator:
    """场景生成器测试"""

    @pytest.mark.asyncio
    async def test_generate_scene(self, mock_llm_service):
        """测试场景生成"""
        with patch('modules.writing.scene_generator.get_llm_service',
                   return_value=mock_llm_service):
            generator = SceneGenerator()

            scene_content = await generator.generate_scene(
                "对话", "客栈", ["李逍遥", "赵灵儿"], "初次相遇"
            )

            assert len(scene_content) > 0

