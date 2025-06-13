from typing import Dict, Any, Optional
from dataclasses import asdict
from typing import Dict, Any, Optional

from loguru import logger

from core.base_tools import AsyncTool, ToolDefinition, ToolParameter
from modules.character.enhanced_character_creator import EnhancedCharacterCreator


class CharacterCreatorTool(AsyncTool):
    """角色创建工具"""

    def __init__(self):
        super().__init__()
        self.creator = EnhancedCharacterCreator()
        # self.creator = CharacterCreator()

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="character_creator",
            description="创建玄幻小说角色，包括外貌、性格、背景、能力等完整信息",
            category="character",
            parameters=[
                ToolParameter(
                    name="character_type",
                    type="string",
                    description="角色类型：主角/重要配角/一般配角/反派/导师等",
                    required=False,
                    default="主角"
                ),
                ToolParameter(
                    name="genre",
                    type="string",
                    description="小说类型",
                    required=False,
                    default="玄幻"
                ),
                ToolParameter(
                    name="count",
                    type="integer",
                    description="创建角色数量",
                    required=False,
                    default=1
                ),
                ToolParameter(
                    name="world_setting",
                    type="object",
                    description="世界设定信息",
                    required=False
                ),
                ToolParameter(
                    name="requirements",
                    type="object",
                    description="特殊要求",
                    required=False
                )
            ],
            examples=[
                {
                    "parameters": {
                        "character_type": "主角",
                        "genre": "玄幻",
                        "count": 1
                    },
                    "result": "完整的主角角色信息"
                }
            ],
            tags=["character", "creation", "protagonist"]
        )

    async def execute(self, parameters: Dict[str, Any],
                      context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行角色创建"""

        character_type = parameters.get("character_type", "主角")
        genre = parameters.get("genre", "玄幻")
        count = parameters.get("count", 1)
        world_setting = parameters.get("world_setting")
        requirements = parameters.get("requirements")
        logger.info(f"==========>执行角色创建 {count}")
        if count == 1:
            character = await self.creator.create_character(
                character_type, genre, world_setting, requirements
            )
            return {
                "character": asdict(character),
                "generation_info": {
                    "character_type": character_type,
                    "genre": genre
                }
            }
        else:
            characters = await self.creator.create_character_batch(
                count, [character_type], genre, world_setting
            )
            return {
                "characters": [asdict(char) for char in characters],
                "generation_info": {
                    "count": count,
                    "character_type": character_type,
                    "genre": genre
                }
            }
