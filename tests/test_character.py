
# tests/test_character.py
"""
角色管理模块测试
"""

import pytest
from unittest.mock import AsyncMock, patch
from modules.character.character_creator import CharacterCreator, CharacterCreatorTool
from modules.character.relationship import RelationshipManager, RelationshipTool


class TestCharacterCreator:
    """角色创建器测试"""

    @pytest.mark.asyncio
    async def test_create_character(self, mock_llm_service, sample_world_setting):
        """测试角色创建"""
        with patch('modules.character.character_creator.get_llm_service',
                   return_value=mock_llm_service):
            creator = CharacterCreator()

            character = await creator.create_character(
                "主角", "玄幻", sample_world_setting
            )

            assert character.name is not None
            assert character.character_type == "主角"
            assert character.importance > 0

    @pytest.mark.asyncio
    async def test_character_creator_tool(self, tool_registry, mock_llm_service):
        """测试角色创建工具"""
        with patch('modules.character.character_creator.get_llm_service',
                   return_value=mock_llm_service):
            tool = CharacterCreatorTool()
            tool_registry.register(tool)

            from core.base_tools import ToolCall
            call = ToolCall(
                id="test_char",
                name="character_creator",
                parameters={
                    "character_type": "主角",
                    "genre": "玄幻",
                    "count": 1
                }
            )

            response = await tool_registry.execute_tool(call)

            assert response.success
            assert "character" in response.result


class TestRelationshipManager:
    """关系管理器测试"""

    @pytest.mark.asyncio
    async def test_create_relationship(self, mock_llm_service, sample_character):
        """测试创建角色关系"""
        with patch('modules.character.relationship.get_llm_service', return_value=mock_llm_service):
            manager = RelationshipManager()

            char2 = sample_character.copy()
            char2["name"] = "赵灵儿"
            char2["id"] = "char_2"

            relationship = await manager.create_relationship(
                sample_character, char2, "友谊关系"
            )

            assert relationship.relationship_type == "友谊关系"
            assert relationship.character1_id == sample_character["id"]
            assert relationship.character2_id == char2["id"]

