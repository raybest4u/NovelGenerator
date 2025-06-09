
# tests/test_plot.py
"""
情节规划模块测试
"""

import pytest
from unittest.mock import AsyncMock, patch
from modules.plot.story_planner import StoryPlanner, StoryPlannerTool
from modules.plot.conflict_generator import ConflictGenerator, ConflictGeneratorTool


class TestStoryPlanner:
    """故事规划器测试"""

    @pytest.mark.asyncio
    async def test_create_story_outline(self, mock_llm_service, sample_character,
                                        sample_world_setting):
        """测试创建故事大纲"""
        with patch('modules.plot.story_planner.get_llm_service', return_value=mock_llm_service):
            planner = StoryPlanner()

            outline = await planner.create_story_outline(
                "测试小说", "玄幻", 10, "三幕式", "成长",
                [sample_character], sample_world_setting
            )

            assert outline.title == "测试小说"
            assert outline.genre == "玄幻"
            assert len(outline.chapters) == 10

    @pytest.mark.asyncio
    async def test_story_planner_tool(self, tool_registry, mock_llm_service):
        """测试故事规划工具"""
        with patch('modules.plot.story_planner.get_llm_service', return_value=mock_llm_service):
            tool = StoryPlannerTool()
            tool_registry.register(tool)

            from core.base_tools import ToolCall
            call = ToolCall(
                id="test_story",
                name="story_planner",
                parameters={
                    "title": "测试小说",
                    "genre": "玄幻",
                    "chapter_count": 5
                }
            )

            response = await tool_registry.execute_tool(call)

            assert response.success
            assert "story_outline" in response.result


class TestConflictGenerator:
    """冲突生成器测试"""

    @pytest.mark.asyncio
    async def test_generate_central_conflict(self, mock_llm_service):
        """测试生成核心冲突"""
        with patch('modules.plot.conflict_generator.get_llm_service',
                   return_value=mock_llm_service):
            generator = ConflictGenerator()

            conflict = await generator.generate_central_conflict(
                "李逍遥", "魔教教主", "玄幻", "正义"
            )

            assert conflict.name is not None
            assert conflict.protagonist == "李逍遥"
            assert conflict.antagonist == "魔教教主"

