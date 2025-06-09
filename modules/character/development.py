# modules/character/development.py
"""
角色发展管理器
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from core.base_tools import AsyncTool, ToolDefinition, ToolParameter
from core.llm_client import get_llm_service
from modules.character import CharacterCreatorTool, RelationshipTool


@dataclass
class CharacterArc:
    """角色弧线"""
    character_id: str
    stages: List[Dict[str, str]]  # 发展阶段
    key_events: List[Dict[str, str]]  # 关键事件
    growth_areas: List[str]  # 成长领域
    conflicts: List[str]  # 内在冲突
    resolution: str  # 最终解决


@dataclass
class PowerProgression:
    """实力发展"""
    character_id: str
    starting_level: str
    target_level: str
    progression_path: List[Dict[str, str]]  # 发展路径
    breakthrough_events: List[Dict[str, str]]  # 突破事件
    training_methods: List[str]  # 训练方法
    obstacles: List[str]  # 阻碍因素


class CharacterDevelopment:
    """角色发展管理器"""

    def __init__(self):
        self.llm_service = get_llm_service()
        self.character_arcs: Dict[str, CharacterArc] = {}
        self.power_progressions: Dict[str, PowerProgression] = {}

    async def create_character_arc(
        self,
        character: Dict[str, Any],
        story_length: int = 10
    ) -> CharacterArc:
        """创建角色弧线"""

        arc_data = await self._generate_character_arc(character, story_length)

        arc = CharacterArc(
            character_id=character['id'],
            **arc_data
        )

        self.character_arcs[character['id']] = arc
        return arc

    async def create_power_progression(
        self,
        character: Dict[str, Any],
        target_level: str = "元婴期"
    ) -> PowerProgression:
        """创建实力发展路线"""

        progression_data = await self._generate_power_progression(character, target_level)

        progression = PowerProgression(
            character_id=character['id'],
            **progression_data
        )

        self.power_progressions[character['id']] = progression
        return progression

    async def _generate_character_arc(self, character: Dict, story_length: int) -> Dict[str, Any]:
        """生成角色弧线"""

        return {
            "stages": [
                {"阶段": "起始", "描述": "角色初始状态"},
                {"阶段": "发展", "描述": "角色遇到挑战"},
                {"阶段": "高潮", "描述": "角色面临最大考验"},
                {"阶段": "结局", "描述": "角色完成成长"}
            ],
            "key_events": [
                {"事件": "启程", "影响": "踏上冒险之路"},
                {"事件": "试炼", "影响": "获得成长"}
            ],
            "growth_areas": ["实力", "心境", "人际关系"],
            "conflicts": ["内心恐惧", "道德选择"],
            "resolution": "成为更强的自己"
        }

    async def _generate_power_progression(self, character: Dict, target_level: str) -> Dict[
        str, Any]:
        """生成实力发展"""

        return {
            "starting_level": "炼气期",
            "target_level": target_level,
            "progression_path": [
                {"等级": "炼气期", "方法": "基础修炼"},
                {"等级": "筑基期", "方法": "筑基丹辅助"},
                {"等级": "金丹期", "方法": "结丹突破"}
            ],
            "breakthrough_events": [
                {"事件": "雷劫", "描述": "突破时的天劫考验"}
            ],
            "training_methods": ["打坐修炼", "实战历练", "丹药辅助"],
            "obstacles": ["资源稀缺", "强敌阻挠", "瓶颈难破"]
        }


class CharacterDevelopmentTool(AsyncTool):
    """角色发展工具"""

    def __init__(self):
        super().__init__()
        self.development = CharacterDevelopment()

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="character_development",
            description="规划角色发展弧线和实力成长路径",
            category="character",
            parameters=[
                ToolParameter(
                    name="development_type",
                    type="string",
                    description="发展类型：arc/power/both",
                    required=True
                ),
                ToolParameter(
                    name="character",
                    type="object",
                    description="角色信息",
                    required=True
                ),
                ToolParameter(
                    name="story_length",
                    type="integer",
                    description="故事长度（章节数）",
                    required=False,
                    default=10
                ),
                ToolParameter(
                    name="target_level",
                    type="string",
                    description="目标实力等级",
                    required=False,
                    default="元婴期"
                )
            ]
        )

    async def execute(self, parameters: Dict[str, Any],
                      context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行角色发展规划"""

        dev_type = parameters.get("development_type")
        character = parameters.get("character", {})
        story_length = parameters.get("story_length", 10)
        target_level = parameters.get("target_level", "元婴期")

        result = {}

        if dev_type in ["arc", "both"]:
            arc = await self.development.create_character_arc(character, story_length)
            result["character_arc"] = asdict(arc)

        if dev_type in ["power", "both"]:
            progression = await self.development.create_power_progression(character, target_level)
            result["power_progression"] = asdict(progression)

        result["generation_info"] = {
            "development_type": dev_type,
            "story_length": story_length,
            "target_level": target_level
        }

        return result


# 注册所有角色工具
def register_character_tools():
    """注册角色管理工具"""
    from core.base_tools import get_tool_registry

    registry = get_tool_registry()

    registry.register(CharacterCreatorTool())
    registry.register(RelationshipTool())
    registry.register(CharacterDevelopmentTool())


if __name__ == "__main__":
    register_character_tools()
    print("角色管理工具已注册")
