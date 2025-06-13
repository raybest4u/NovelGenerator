# modules/worldbuilding/world_generator.py
"""
世界生成器
创建完整的玄幻世界设定
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

from loguru import logger

from core.base_tools import AsyncTool, ToolDefinition, ToolParameter
from core.llm_client import get_llm_service, PromptTemplate
from config.settings import get_prompt_manager
import json


@dataclass
class WorldSetting:
    """世界设定"""
    name: str  # 世界名称
    type: str  # 世界类型：大陆、星球、异界等
    time_period: str  # 时代背景
    technology_level: str  # 科技水平
    magic_prevalence: str  # 魔法普及程度
    political_system: str  # 政治体系
    major_races: List[str]  # 主要种族
    major_kingdoms: List[Dict[str, str]]  # 主要王国/势力
    natural_features: List[str]  # 自然特征
    unique_elements: List[str]  # 独特元素
    history_timeline: List[Dict[str, str]]  # 历史时间线
    culture_notes: str  # 文化特色
    economy_system: str  # 经济体系
    languages: List[str]  # 语言系统

    # 添加详细信息字段
    detailed_politics: Optional[str] = None  # 详细政治信息
    detailed_economy: Optional[str] = None  # 详细经济信息
    detailed_culture: Optional[str] = None  # 详细文化信息
    detailed_history: Optional[str] = None  # 详细历史信息


class WorldGenerator:
    """世界生成器"""

    def __init__(self):
        self.llm_service = get_llm_service()
        self.prompt_manager = get_prompt_manager()

    async def generate_basic_world(self, genre: str = "玄幻", theme: str = "修仙",
                                   scale: str = "大陆") -> WorldSetting:
        """生成基础世界设定"""

        prompt = self.prompt_manager.get_prompt(
            "worldbuilding",
            "basic_world",
            genre=genre,
            theme=theme,
            scale=scale
        )
        logger.info(f">>生成基础世界设定{prompt}")
        response = await self.llm_service.generate_text(prompt)

        # 解析LLM响应为结构化数据
        world_data = await self._parse_world_response(response.content)

        return WorldSetting(**world_data)

    async def generate_detailed_world(self, basic_world: WorldSetting,
                                      focus_areas: List[str] = None) -> WorldSetting:
        """生成详细世界设定"""
        logger.info(f">>生成详细世界设定{basic_world}")
        focus_areas = focus_areas or ["politics", "economy", "culture", "history"]

        # 添加中英文映射字典
        area_mapping = {
            "政治": "politics",
            "经济": "economy",
            "文化": "culture",
            "历史": "history",
            "politics": "politics",
            "economy": "economy",
            "culture": "culture",
            "history": "history"
        }

        updated_world = basic_world

        for area in focus_areas:
            # 使用映射转换
            english_area = area_mapping.get(area, area)

            prompt = self.prompt_manager.get_prompt(
                "worldbuilding",
                f"detailed_{english_area}",
                world_name=basic_world.name,
                world_type=basic_world.type,
                existing_info=asdict(basic_world)
            )

            response = await self.llm_service.generate_text(prompt)

            # 更新世界设定
            updated_data = await self._parse_detail_response(response.content, english_area)
            updated_world = self._merge_world_data(updated_world, updated_data)

        return updated_world

    async def generate_world_conflicts(self, world: WorldSetting) -> List[Dict[str, Any]]:
        """生成世界冲突和矛盾"""

        prompt = self.prompt_manager.get_prompt(
            "worldbuilding",
            "world_conflicts",
            kingdoms=world.major_kingdoms,
            races=world.major_races,
            political_system=world.political_system
        )
        logger.info(f">>生成世界冲突和矛盾{prompt}")
        response = await self.llm_service.generate_text(prompt)

        return await self._parse_conflicts_response(response.content)

    async def generate_world_mysteries(self, world: WorldSetting) -> List[Dict[str, str]]:
        """生成世界谜团和秘密"""

        prompt = self.prompt_manager.get_prompt(
            "worldbuilding",
            "world_mysteries",
            world_name=world.name,
            unique_elements=world.unique_elements,
            history=world.history_timeline
        )
        logger.info(f">>生成世界谜团和秘密{prompt}")
        response = await self.llm_service.generate_text(prompt)

        return await self._parse_mysteries_response(response.content)

    async def _parse_world_response(self, response: str) -> Dict[str, Any]:
        """解析世界生成响应"""
        try:
            # 使用LLM来结构化响应
            structure_prompt = f"""
            请将以下世界设定描述转换为JSON格式，包含以下字段：
            name, type, time_period, technology_level, magic_prevalence,
            political_system, major_races, major_kingdoms, natural_features,
            unique_elements, history_timeline, culture_notes, economy_system, languages

            原始描述：
            {response}

            请返回标准JSON格式：
            """

            structure_response = await self.llm_service.generate_text(structure_prompt)

            # 尝试解析JSON
            try:
                logger.info(f"parse_llm_response==>{structure_response.content}")
                # 尝试提取JSON部分
                response_content = structure_response.content
                json_start = response_content.find("{")
                json_end = response_content.rfind("}") + 1

                if json_start == -1 or json_end == 0:
                    raise ValueError("响应中未找到JSON格式")

                json_str = response_content[json_start:json_end]
                parsed_data = json.loads(json_str)

                # 确保所有必需字段都存在，添加默认值
                default_world_data = {
                    "name": "未命名世界",
                    "type": "大陆",
                    "time_period": "古代",
                    "technology_level": "中世纪",
                    "magic_prevalence": "高",
                    "political_system": "封建制",
                    "major_races": ["人族", "妖族"],
                    "major_kingdoms": [{"name": "东方王国", "description": "强大的人族王国"}],
                    "natural_features": ["高山", "森林", "河流"],
                    "unique_elements": ["灵气", "仙境"],
                    "history_timeline": [{"period": "远古时代", "event": "世界诞生"}],
                    "culture_notes": "修仙文化盛行",
                    "economy_system": "以物易物和货币并存",
                    "languages": ["通用语", "古语"]
                }

                # 用解析的数据更新默认数据
                default_world_data.update(parsed_data)
                return default_world_data

            except json.JSONDecodeError as e:
                logger.warning(f"JSON解析失败: {e}，使用默认值")
                # 如果解析失败，使用默认值
                return {
                    "name": "未命名世界",
                    "type": "大陆",
                    "time_period": "古代",
                    "technology_level": "中世纪",
                    "magic_prevalence": "高",
                    "political_system": "封建制",
                    "major_races": ["人族", "妖族"],
                    "major_kingdoms": [{"name": "东方王国", "description": "强大的人族王国"}],
                    "natural_features": ["高山", "森林", "河流"],
                    "unique_elements": ["灵气", "仙境"],
                    "history_timeline": [{"period": "远古时代", "event": "世界诞生"}],
                    "culture_notes": "修仙文化盛行",
                    "economy_system": "以物易物和货币并存",
                    "languages": ["通用语", "古语"]
                }

        except Exception as e:
            logger.error(f"解析世界响应失败: {e}")
            raise Exception(f"解析世界响应失败: {e}")

    async def _parse_detail_response(self, response: str, area: str) -> Dict[str, Any]:
        """解析详细信息响应"""
        # 根据不同区域将详细信息映射到正确的字段
        logger.info(f">>解析详细信息响应_parse_detail_response:{response[:500]}")
        if area == "politics":
            return {"detailed_politics": response}
        elif area == "economy":
            return {"detailed_economy": response}
        elif area == "culture":
            return {"detailed_culture": response}
        elif area == "history":
            return {"detailed_history": response}
        else:
            # 对于未知区域，返回空字典
            logger.warning(f"未知的详细信息区域: {area}")
            return {}

    def _merge_world_data(self, world: WorldSetting, new_data: Dict[str, Any]) -> WorldSetting:
        """合并世界数据"""
        world_dict = asdict(world)

        # 只更新存在的字段，避免引入不支持的字段
        for key, value in new_data.items():
            if hasattr(WorldSetting, key):
                world_dict[key] = value
            else:
                logger.warning(f"忽略不支持的字段: {key}")

        return WorldSetting(**world_dict)

    async def _parse_conflicts_response(self, response: str) -> List[Dict[str, Any]]:
        """解析冲突响应"""
        # 简单解析冲突列表，实际项目中可以更复杂
        conflicts = []

        # 尝试从响应中提取冲突信息
        lines = response.strip().split('\n')
        for i, line in enumerate(lines):
            if line.strip() and ('冲突' in line or '矛盾' in line or '争夺' in line):
                conflicts.append({
                    "id": f"conflict_{i}",
                    "type": "世界冲突",
                    "description": line.strip(),
                    "severity": "中等",
                    "involved_parties": [],
                    "location": "未指定"
                })

        # 如果没有找到冲突，返回默认冲突
        if not conflicts:
            conflicts = [{
                "id": "default_conflict",
                "type": "政治冲突",
                "description": "王国间的领土争夺",
                "severity": "高",
                "involved_parties": ["东方王国", "西方联盟"],
                "location": "边境地区"
            }]

        return conflicts

    async def _parse_mysteries_response(self, response: str) -> List[Dict[str, str]]:
        """解析谜团响应"""
        mysteries = []

        # 尝试从响应中提取谜团信息
        lines = response.strip().split('\n')
        for i, line in enumerate(lines):
            if line.strip() and (
                '谜' in line or '秘密' in line or '传说' in line or '遗迹' in line):
                mysteries.append({
                    "id": f"mystery_{i}",
                    "title": f"谜团{i + 1}",
                    "description": line.strip(),
                    "difficulty": "中等",
                    "category": "世界秘密"
                })

        # 如果没有找到谜团，返回默认谜团
        if not mysteries:
            mysteries = [{
                "id": "default_mystery",
                "title": "古老遗迹",
                "description": "大陆深处隐藏着上古文明的遗迹，蕴含着强大的力量",
                "difficulty": "高",
                "category": "历史秘密"
            }]

        return mysteries


class WorldBuilderTool(AsyncTool):
    """世界构建工具"""

    def __init__(self):
        super().__init__()
        self.generator = WorldGenerator()

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="world_builder",
            description="构建玄幻小说的世界观设定，包括世界背景、种族、王国、文化等",
            category="worldbuilding",
            parameters=[
                ToolParameter(
                    name="genre",
                    type="string",
                    description="小说类型",
                    required=False,
                    default="玄幻"
                ),
                ToolParameter(
                    name="theme",
                    type="string",
                    description="主题风格",
                    required=False,
                    default="修仙"
                ),
                ToolParameter(
                    name="scale",
                    type="string",
                    description="世界规模",
                    required=False,
                    default="大陆"
                ),
                ToolParameter(
                    name="detail_level",
                    type="string",
                    description="详细程度：basic/detailed",
                    required=False,
                    default="basic"
                ),
                ToolParameter(
                    name="focus_areas",
                    type="array",
                    description="重点关注的领域",
                    required=False
                )
            ],
            examples=[
                {
                    "parameters": {
                        "genre": "玄幻",
                        "theme": "修仙",
                        "scale": "大陆",
                        "detail_level": "detailed"
                    },
                    "result": "完整的修仙大陆世界设定"
                }
            ],
            tags=["worldbuilding", "setting", "background"]
        )

    async def execute(self, parameters: Dict[str, Any],
                      context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行世界构建"""

        try:
            genre = parameters.get("genre", "玄幻")
            theme = parameters.get("theme", "修仙")
            scale = parameters.get("scale", "大陆")
            detail_level = parameters.get("detail_level", "basic")
            focus_areas = parameters.get("focus_areas", [])

            # 生成基础世界
            basic_world = await self.generator.generate_basic_world(genre, theme, scale)
            logger.info(f"生成基础世界  -->{basic_world}")
            if detail_level == "detailed":
                # 生成详细世界
                detailed_world = await self.generator.generate_detailed_world(basic_world,
                                                                              focus_areas)
                logger.info(f"生成详细世界  -->{detailed_world}")
                # 生成冲突和谜团
                conflicts = await self.generator.generate_world_conflicts(detailed_world)
                mysteries = await self.generator.generate_world_mysteries(detailed_world)
                logger.info(f"生成冲突和谜团 conflicts -->{conflicts}")
                logger.info(f"生成冲突和谜团 mysteries -->{mysteries}")
                return {
                    "world_setting": asdict(detailed_world),
                    "conflicts": conflicts,
                    "mysteries": mysteries,
                    "generation_info": {
                        "genre": genre,
                        "theme": theme,
                        "scale": scale,
                        "detail_level": detail_level
                    }
                }
            else:
                return {
                    "world_setting": asdict(basic_world),
                    "generation_info": {
                        "genre": genre,
                        "theme": theme,
                        "scale": scale,
                        "detail_level": detail_level
                    }
                }

        except Exception as e:
            logger.error(f"世界构建执行失败: {e}")
            raise Exception(f"世界构建执行失败: {e}")
