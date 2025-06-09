# modules/worldbuilding/geography.py
"""
地理环境生成器
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from core.base_tools import AsyncTool, ToolDefinition, ToolParameter
from core.llm_client import get_llm_service
from config.settings import get_prompt_manager
from modules.worldbuilding import WorldBuilderTool, MagicSystemTool


@dataclass
class GeographyInfo:
    """地理信息"""
    continents: List[Dict[str, str]]  # 大陆
    kingdoms: List[Dict[str, str]]  # 王国/势力
    cities: List[Dict[str, str]]  # 城市
    natural_features: List[Dict[str, str]]  # 自然地貌
    dangerous_zones: List[Dict[str, str]]  # 危险区域
    resource_locations: List[Dict[str, str]]  # 资源分布
    trade_routes: List[Dict[str, str]]  # 贸易路线
    climate_zones: List[Dict[str, str]]  # 气候带
    special_locations: List[Dict[str, str]]  # 特殊地点


class GeographyGenerator:
    """地理生成器"""

    def __init__(self):
        self.llm_service = get_llm_service()
        self.prompt_manager = get_prompt_manager()

    async def generate_geography(self, world_name: str, world_scale: str = "大陆") -> GeographyInfo:
        """生成地理信息"""

        prompt = self.prompt_manager.get_prompt(
            "worldbuilding",
            "geography",
            world_name=world_name,
            world_scale=world_scale
        )

        response = await self.llm_service.generate_text(prompt)
        geo_data = await self._parse_geography_response(response.content)

        return GeographyInfo(**geo_data)

    async def _parse_geography_response(self, response: str) -> Dict[str, Any]:
        """解析地理响应"""
        # 默认地理信息
        return {
            "continents": [
                {"name": "东荒大陆", "description": "东方的广阔大陆"},
                {"name": "西域", "description": "西方的沙漠区域"}
            ],
            "kingdoms": [
                {"name": "大周王朝", "description": "东荒大陆的主要王朝"},
                {"name": "北蛮部落", "description": "北方的游牧部落"}
            ],
            "cities": [
                {"name": "京都", "description": "大周王朝的都城"},
                {"name": "雪城", "description": "北方的要塞城市"}
            ],
            "natural_features": [
                {"name": "万里长江", "description": "贯穿大陆的大河"},
                {"name": "昆仑山脉", "description": "连绵的高山"}
            ],
            "dangerous_zones": [
                {"name": "死亡沙漠", "description": "西域的死亡禁地"},
                {"name": "迷魂森林", "description": "充满危险的原始森林"}
            ],
            "resource_locations": [
                {"name": "灵石矿", "description": "蕴含灵气的矿脉"},
                {"name": "药草谷", "description": "珍贵药材的产地"}
            ],
            "trade_routes": [
                {"name": "丝绸之路", "description": "连接东西的商路"},
                {"name": "内河航线", "description": "沿江的水路运输"}
            ],
            "climate_zones": [
                {"name": "温带", "description": "四季分明的宜居区域"},
                {"name": "寒带", "description": "终年严寒的北方"}
            ],
            "special_locations": [
                {"name": "仙人洞府", "description": "传说中仙人的居所"},
                {"name": "古战场", "description": "上古大战的遗迹"}
            ]
        }


class GeographyTool(AsyncTool):
    """地理工具"""

    def __init__(self):
        super().__init__()
        self.generator = GeographyGenerator()

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="geography_generator",
            description="生成世界地理环境，包括大陆、王国、城市、自然地貌等",
            category="worldbuilding",
            parameters=[
                ToolParameter(
                    name="world_name",
                    type="string",
                    description="世界名称",
                    required=True
                ),
                ToolParameter(
                    name="world_scale",
                    type="string",
                    description="世界规模",
                    required=False,
                    default="大陆"
                )
            ]
        )

    async def execute(self, parameters: Dict[str, Any],
                      context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行地理生成"""

        world_name = parameters.get("world_name", "未命名世界")
        world_scale = parameters.get("world_scale", "大陆")

        geography = await self.generator.generate_geography(world_name, world_scale)

        return {
            "geography": asdict(geography),
            "generation_info": {
                "world_name": world_name,
                "world_scale": world_scale
            }
        }


# 注册所有工具
def register_worldbuilding_tools():
    """注册世界观构建工具"""
    from core.base_tools import get_tool_registry

    registry = get_tool_registry()

    registry.register(WorldBuilderTool())
    registry.register(MagicSystemTool())
    registry.register(GeographyTool())


if __name__ == "__main__":
    register_worldbuilding_tools()
    print("世界观构建工具已注册")
