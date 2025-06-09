
# tests/test_integration.py
"""
集成测试
"""

import pytest
from unittest.mock import AsyncMock, patch
from main import NovelGenerator


class TestNovelGeneration:
    """小说生成集成测试"""

    @pytest.mark.asyncio
    async def test_generate_world_only(self, mock_llm_service):
        """测试仅生成世界观"""
        with patch('main.get_llm_service', return_value=mock_llm_service):
            generator = NovelGenerator()

            result = await generator.generate_world_only("玄幻", "修仙")

            assert "world_setting" in result

    @pytest.mark.asyncio
    async def test_generate_characters_only(self, mock_llm_service):
        """测试仅生成角色"""
        with patch('main.get_llm_service', return_value=mock_llm_service):
            generator = NovelGenerator()

            result = await generator.generate_characters_only(3, "玄幻")

            assert "characters" in result
            assert len(result["characters"]) > 0

    def test_list_tools(self):
        """测试列出工具"""
        generator = NovelGenerator()

        # 这个测试主要确保不会出错
        generator.list_tools()
