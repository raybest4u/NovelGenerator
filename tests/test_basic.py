"""
基础测试
"""

import pytest
import asyncio
from main import NovelGenerator


@pytest.mark.asyncio
async def test_world_generation():
    """测试世界观生成"""
    generator = NovelGenerator()
    result = await generator.generate_world_only("玄幻", "修仙")

    assert "world_setting" in result
    assert result["world_setting"]["name"] is not None


@pytest.mark.asyncio  
async def test_character_generation():
    """测试角色生成"""
    generator = NovelGenerator()
    result = await generator.generate_character_only("主角", "玄幻")

    assert "character" in result
    assert result["character"]["name"] is not None


def test_tool_registry():
    """测试工具注册"""
    generator = NovelGenerator()
    tools = generator.tool_registry.list_tools()

    assert len(tools) > 0
    tool_names = [tool.name for tool in tools]
    assert "world_builder" in tool_names
    assert "character_creator" in tool_names
