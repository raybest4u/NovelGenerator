
# tests/test_tools.py
"""
工具模块测试
"""

import pytest
from unittest.mock import AsyncMock, patch
from modules.tools.name_generator import NameGenerator, NameGeneratorTool
from modules.tools.timeline_manager import TimelineManager, TimelineManagerTool
from modules.tools.consistency_checker import ConsistencyChecker, ConsistencyCheckerTool


class TestNameGenerator:
    """名称生成器测试"""

    @pytest.mark.asyncio
    async def test_generate_character_names(self, mock_llm_service):
        """测试角色名称生成"""
        with patch('modules.tools.name_generator.get_llm_service', return_value=mock_llm_service):
            generator = NameGenerator()

            names = await generator.generate_character_names(3, "male", "中式古典")

            assert len(names) > 0
            assert all(name.type == "character" for name in names)

    def test_generate_random_name(self):
        """测试随机名称生成"""
        generator = NameGenerator()

        name = generator.generate_random_name("character", "中式古典")

        assert name.name is not None
        assert name.type == "character"


class TestTimelineManager:
    """时间线管理器测试"""

    @pytest.mark.asyncio
    async def test_create_main_timeline(self, mock_llm_service, sample_story_outline):
        """测试创建主时间线"""
        with patch('modules.tools.timeline_manager.get_llm_service', return_value=mock_llm_service):
            manager = TimelineManager()

            timeline = await manager.create_main_timeline(
                sample_story_outline, "1 year", "春季"
            )

            assert timeline.name == "主线时间线"
            assert len(timeline.events) > 0


class TestConsistencyChecker:
    """一致性检查器测试"""

    @pytest.mark.asyncio
    async def test_check_character_consistency(self, mock_llm_service, sample_character):
        """测试角色一致性检查"""
        with patch('modules.tools.consistency_checker.get_llm_service',
                   return_value=mock_llm_service):
            checker = ConsistencyChecker()

            issues = await checker.check_character_consistency([sample_character])

            assert isinstance(issues, list)
