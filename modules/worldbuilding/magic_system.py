
# modules/worldbuilding/magic_system.py
"""
魔法体系生成器
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from core.base_tools import AsyncTool, ToolDefinition, ToolParameter
from core.llm_client import get_llm_service
from config.settings import get_prompt_manager


@dataclass
class MagicSystem:
    """魔法体系"""
    name: str  # 体系名称
    source: str  # 力量源泉
    classification: List[str]  # 分类方式
    power_levels: List[str]  # 实力等级
    cultivation_method: str  # 修炼方法
    restrictions: List[str]  # 限制条件
    side_effects: List[str]  # 副作用
    artifacts: List[Dict[str, str]]  # 法器/道具
    techniques: List[Dict[str, str]]  # 技能/法术
    organizations: List[Dict[str, str]]  # 相关组织
    legends: List[str]  # 传说故事


class MagicSystemGenerator:
    """魔法体系生成器"""

    def __init__(self):
        self.llm_service = get_llm_service()
        self.prompt_manager = get_prompt_manager()

    async def generate_magic_system(self, world_type: str = "修仙",
                                  complexity: str = "medium") -> MagicSystem:
        """生成魔法体系"""

        prompt = self.prompt_manager.get_prompt(
            "worldbuilding",
            "magic_system",
            world_type=world_type,
            complexity=complexity
        )

        response = await self.llm_service.generate_text(prompt)
        magic_data = await self._parse_magic_response(response.content)

        return MagicSystem(**magic_data)

    async def _parse_magic_response(self, response: str) -> Dict[str, Any]:
        """解析魔法体系响应"""
        # 默认修仙体系
        return {
            "name": "仙道体系",
            "source": "天地灵气",
            "classification": ["金", "木", "水", "火", "土"],
            "power_levels": ["炼气", "筑基", "金丹", "元婴", "化神", "炼虚", "合体", "大乘", "渡劫"],
            "cultivation_method": "吸纳天地灵气，淬炼己身",
            "restrictions": ["天赋限制", "资源稀缺", "心魔影响"],
            "side_effects": ["走火入魔", "境界不稳", "寿元消耗"],
            "artifacts": [
                {"name": "飞剑", "description": "御剑飞行的法宝"},
                {"name": "丹炉", "description": "炼制丹药的器具"}
            ],
            "techniques": [
                {"name": "御剑术", "description": "操控飞剑的技能"},
                {"name": "炼丹术", "description": "炼制丹药的技能"}
            ],
            "organizations": [
                {"name": "仙门", "description": "修仙者的组织"},
                {"name": "魔教", "description": "邪恶修炼者的组织"}
            ],
            "legends": ["仙界传说", "上古大能的故事"]
        }


class MagicSystemTool(AsyncTool):
    """魔法体系工具"""

    def __init__(self):
        super().__init__()
        self.generator = MagicSystemGenerator()

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="magic_system_generator",
            description="生成玄幻小说的魔法体系，包括修炼等级、技能法术、法宝道具等",
            category="worldbuilding",
            parameters=[
                ToolParameter(
                    name="world_type",
                    type="string",
                    description="世界类型：修仙/西幻/都市/科幻",
                    required=False,
                    default="修仙"
                ),
                ToolParameter(
                    name="complexity",
                    type="string",
                    description="复杂程度：simple/medium/complex",
                    required=False,
                    default="medium"
                )
            ]
        )

    async def execute(self, parameters: Dict[str, Any],
                     context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行魔法体系生成"""

        world_type = parameters.get("world_type", "修仙")
        complexity = parameters.get("complexity", "medium")

        magic_system = await self.generator.generate_magic_system(world_type, complexity)

        return {
            "magic_system": asdict(magic_system),
            "generation_info": {
                "world_type": world_type,
                "complexity": complexity
            }
        }

