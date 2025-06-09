
# tests/test_worldbuilding.py
"""
世界观构建模块测试
"""

import pytest
from unittest.mock import AsyncMock, patch
from modules.worldbuilding.world_generator import WorldGenerator, WorldBuilderTool
from modules.worldbuilding.magic_system import MagicSystemGenerator, MagicSystemTool
from modules.worldbuilding.geography import GeographyGenerator, GeographyTool


class TestWorldGenerator:
    """世界生成器测试"""

    @pytest.mark.asyncio
    async def test_generate_basic_world(self, mock_llm_service):
        """测试基础世界生成"""
        with patch('modules.worldbuilding.world_generator.get_llm_service',
                   return_value=mock_llm_service):
            generator = WorldGenerator()

            world = await generator.generate_basic_world("玄幻", "修仙", "大陆")

            assert world.name is not None
            assert world.type == "大陆"
            assert len(world.major_races) > 0

    @pytest.mark.asyncio
    async def test_world_builder_tool(self, tool_registry, mock_llm_service):
        """测试世界构建工具"""
        with patch('modules.worldbuilding.world_generator.get_llm_service',
                   return_value=mock_llm_service):
            tool = WorldBuilderTool()
            tool_registry.register(tool)

            from core.base_tools import ToolCall
            call = ToolCall(
                id="test_world",
                name="world_builder",
                parameters={
                    "genre": "玄幻",
                    "theme": "修仙",
                    "detail_level": "basic"
                }
            )

            response = await tool_registry.execute_tool(call)

            assert response.success
            assert "world_setting" in response.result


class TestMagicSystemGenerator:
    """魔法体系生成器测试"""

    @pytest.mark.asyncio
    async def test_generate_magic_system(self, mock_llm_service):
        """测试魔法体系生成"""
        with patch('modules.worldbuilding.magic_system.get_llm_service',
                   return_value=mock_llm_service):
            generator = MagicSystemGenerator()

            magic_system = await generator.generate_magic_system("修仙", "medium")

            assert magic_system.name is not None
            assert len(magic_system.power_levels) > 0

    @pytest.mark.asyncio
    async def test_magic_system_tool(self, tool_registry, mock_llm_service):
        """测试魔法体系工具"""
        with patch('modules.worldbuilding.magic_system.get_llm_service',
                   return_value=mock_llm_service):
            tool = MagicSystemTool()
            tool_registry.register(tool)

            from core.base_tools import ToolCall
            call = ToolCall(
                id="test_magic",
                name="magic_system_generator",
                parameters={
                    "world_type": "修仙",
                    "complexity": "medium"
                }
            )

            response = await tool_registry.execute_tool(call)

            assert response.success
            assert "magic_system" in response.result

