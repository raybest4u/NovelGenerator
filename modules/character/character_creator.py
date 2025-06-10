# modules/character/character_creator.py
"""
角色创建器
负责生成各种类型的角色
"""

from typing import Dict, Any, List, Optional, Literal
from dataclasses import dataclass, asdict
from enum import Enum
from core.base_tools import AsyncTool, ToolDefinition, ToolParameter
from core.llm_client import get_llm_service
from config.settings import get_prompt_manager
import random
import json
import re
from loguru import logger


class CharacterType(Enum):
    """角色类型"""
    PROTAGONIST = "主角"
    DEUTERAGONIST = "重要配角"
    SUPPORTING = "一般配角"
    ANTAGONIST = "反派"
    MENTOR = "导师"
    LOVE_INTEREST = "爱情线角色"
    COMIC_RELIEF = "搞笑角色"
    BACKGROUND = "背景角色"


class PowerLevel(Enum):
    """实力等级"""
    MORTAL = "凡人"
    QI_REFINING = "炼气期"
    FOUNDATION = "筑基期"
    GOLDEN_CORE = "金丹期"
    NASCENT_SOUL = "元婴期"
    SOUL_FORMATION = "化神期"
    VOID_REFINEMENT = "炼虚期"
    BODY_INTEGRATION = "合体期"
    GREAT_ASCENSION = "大乘期"
    TRIBULATION = "渡劫期"
    IMMORTAL = "仙人"


@dataclass
class CharacterAppearance:
    """角色外貌"""
    gender: str  # 性别
    age: int  # 年龄
    height: str  # 身高
    build: str  # 体型
    hair_color: str  # 发色
    eye_color: str  # 眼色
    skin_tone: str  # 肤色
    distinctive_features: List[str]  # 特征
    clothing_style: str  # 穿衣风格
    accessories: List[str]  # 配饰


@dataclass
class CharacterPersonality:
    """角色性格"""
    core_traits: List[str]  # 核心特质
    strengths: List[str]  # 优点
    weaknesses: List[str]  # 缺点
    fears: List[str]  # 恐惧
    desires: List[str]  # 欲望
    habits: List[str]  # 习惯
    speech_pattern: str  # 说话方式
    moral_alignment: str  # 道德取向


@dataclass
class CharacterBackground:
    """角色背景"""
    birthplace: str  # 出生地
    family: Dict[str, str]  # 家庭成员
    childhood: str  # 童年经历
    education: List[str]  # 教育经历
    major_events: List[Dict[str, str]]  # 重大事件
    relationships: List[Dict[str, str]]  # 人际关系
    secrets: List[str]  # 秘密
    goals: List[str]  # 目标


@dataclass
class CharacterAbilities:
    """角色能力"""
    power_level: str  # 实力等级
    cultivation_method: str  # 修炼功法
    special_abilities: List[Dict[str, str]]  # 特殊能力
    combat_skills: List[str]  # 战斗技能
    non_combat_skills: List[str]  # 非战斗技能
    artifacts: List[Dict[str, str]]  # 法宝/装备
    spiritual_root: str  # 灵根属性
    talent_level: str  # 天赋等级


@dataclass
class Character:
    """完整角色"""
    id: str  # 角色ID
    name: str  # 姓名
    nickname: Optional[str]  # 绰号
    character_type: str  # 角色类型
    importance: int  # 重要性评分(1-10)

    # 详细信息
    appearance: CharacterAppearance
    personality: CharacterPersonality
    background: CharacterBackground
    abilities: CharacterAbilities

    # 故事相关
    story_role: str  # 故事作用
    character_arc: str  # 角色弧线
    relationships: List[str]  # 关系列表

    # 元数据
    creation_notes: str  # 创作笔记
    inspiration: str  # 灵感来源


class CharacterCreator:
    """角色创建器"""

    def __init__(self):
        self.llm_service = get_llm_service()
        self.prompt_manager = get_prompt_manager()
        self.character_templates = self._load_character_templates()

    async def create_character(
        self,
        character_type: str = "主角",
        genre: str = "玄幻",
        world_setting: Optional[Dict] = None,
        requirements: Optional[Dict] = None
    ) -> Character:
        """创建角色"""

        # 生成基础信息
        basic_info = await self._generate_basic_info(character_type, genre, requirements)
        logger.info(f"生成基础信息-->{basic_info}")
        # 生成外貌
        appearance = await self._generate_appearance(basic_info, world_setting)
        logger.info(f"生成外貌-->{appearance}")
        # 生成性格
        personality = await self._generate_personality(basic_info, character_type)
        logger.info(f"生成性格-->{personality}")
        # 生成背景
        background = await self._generate_background(basic_info, world_setting)
        logger.info(f"生成背景-->{background}")
        # 生成能力
        abilities = await self._generate_abilities(basic_info, genre, world_setting)
        logger.info(f"生成能力-->{abilities}")
        # 组装角色
        character = Character(
            id=f"char_{random.randint(1000, 9999)}",
            name=basic_info["name"],
            nickname=basic_info.get("nickname"),
            character_type=character_type,
            importance=basic_info.get("importance", 5),
            appearance=appearance,
            personality=personality,
            background=background,
            abilities=abilities,
            story_role=basic_info.get("story_role", ""),
            character_arc=basic_info.get("character_arc", ""),
            relationships=[],
            creation_notes="",
            inspiration=""
        )

        return character

    async def create_character_batch(
        self,
        count: int,
        character_types: List[str] = None,
        genre: str = "玄幻",
        world_setting: Optional[Dict] = None
    ) -> List[Character]:
        """批量创建角色"""

        if not character_types:
            character_types = ["主角", "重要配角", "一般配角", "反派"]

        characters = []

        for i in range(count):
            char_type = character_types[i % len(character_types)]
            character = await self.create_character(char_type, genre, world_setting)
            characters.append(character)

        return characters

    async def _generate_basic_info(self, character_type: str, genre: str,
                                   requirements: Optional[Dict] = None) -> Dict[str, Any]:
        """生成基础信息"""

        prompt = f"""
        为{genre}小说创建一个{character_type}角色的基本信息。

        特殊要求：{requirements or '无'}

        请以JSON格式返回以下信息：
        {{
            "name": "角色姓名",
            "nickname": "绰号（可为空）",
            "story_role": "在故事中的作用",
            "character_arc": "角色发展弧线描述"
        }}

        要求：
        1. 姓名要符合{genre}小说的风格
        2. 符合{character_type}的特征
        3. 为后续发展留下空间
        """

        response = await self.llm_service.generate_text(prompt)
        parsed_info = await self._parse_json_response(response.content)

        # 添加重要性评分
        parsed_info["importance"] = self._calculate_importance(character_type)

        return parsed_info

    async def _generate_appearance(self, basic_info: Dict,
                                   world_setting: Optional[Dict]) -> CharacterAppearance:
        """生成外貌"""

        prompt = f"""
        为角色{basic_info["name"]}设计外貌特征。

        世界设定：{world_setting or '标准玄幻世界'}

        请以JSON格式返回：
        {{
            "gender": "性别",
            "age": 年龄数字,
            "height": "身高描述",
            "build": "体型描述",
            "hair_color": "发色",
            "eye_color": "眼色",
            "skin_tone": "肤色",
            "distinctive_features": ["特征1", "特征2"],
            "clothing_style": "穿衣风格",
            "accessories": ["配饰1", "配饰2"]
        }}

        要求：
        - 外貌要与角色身份相符
        - 便于读者记忆
        - 体现角色特色
        """

        response = await self.llm_service.generate_text(prompt)
        appearance_data = await self._parse_json_response(response.content)

        return CharacterAppearance(**appearance_data)

    async def _generate_personality(self, basic_info: Dict,
                                    character_type: str) -> CharacterPersonality:
        """生成性格"""

        prompt = f"""
        为角色{basic_info["name"]}（{character_type}）设计性格特征。

        请以JSON格式返回：
        {{
            "core_traits": ["核心特质1", "核心特质2", "核心特质3"],
            "strengths": ["优点1", "优点2"],
            "weaknesses": ["缺点1", "缺点2"],
            "fears": ["恐惧1", "恐惧2"],
            "desires": ["欲望1", "欲望2"],
            "habits": ["习惯1", "习惯2"],
            "speech_pattern": "说话方式描述",
            "moral_alignment": "道德取向"
        }}

        要求：
        - 性格要有层次感
        - 优缺点要平衡
        - 符合{character_type}的定位
        """

        response = await self.llm_service.generate_text(prompt)
        personality_data = await self._parse_json_response(response.content)

        return CharacterPersonality(**personality_data)

    async def _generate_background(self, basic_info: Dict,
                                   world_setting: Optional[Dict]) -> CharacterBackground:
        """生成背景"""

        prompt = f"""
        为角色{basic_info["name"]}创建详细背景。

        世界设定：{world_setting or '标准玄幻世界'}

        请以JSON格式返回：
        {{
            "birthplace": "出生地",
            "family": {{"父亲": "描述", "母亲": "描述"}},
            "childhood": "童年经历描述",
            "education": ["教育1", "教育2"],
            "major_events": [{{"事件": "描述", "影响": "对角色的影响"}}],
            "relationships": [{{"关系": "师父", "描述": "关系描述"}}],
            "secrets": ["秘密1", "秘密2"],
            "goals": ["目标1", "目标2"]
        }}

        要求：
        - 背景要与世界观一致
        - 为角色行为提供动机
        """

        response = await self.llm_service.generate_text(prompt)
        background_data = await self._parse_json_response(response.content)

        return CharacterBackground(**background_data)

    async def _generate_abilities(self, basic_info: Dict, genre: str,
                                  world_setting: Optional[Dict]) -> CharacterAbilities:
        """生成能力"""

        prompt = f"""
        为角色{basic_info["name"]}设计能力体系。

        小说类型：{genre}
        世界设定：{world_setting or '标准玄幻世界'}

        请以JSON格式返回：
        {{
            "power_level": "实力等级",
            "cultivation_method": "修炼功法",
            "special_abilities": [{{"名称": "能力名", "描述": "能力描述"}}],
            "combat_skills": ["战斗技能1", "战斗技能2"],
            "non_combat_skills": ["非战斗技能1", "非战斗技能2"],
            "artifacts": [{{"名称": "法宝名", "品级": "品级", "描述": "描述"}}],
            "spiritual_root": "灵根属性",
            "talent_level": "天赋等级"
        }}

        要求：
        - 符合世界的力量体系
        - 实力与角色设定匹配
        - 留有成长空间
        """

        response = await self.llm_service.generate_text(prompt)
        abilities_data = await self._parse_json_response(response.content)

        return CharacterAbilities(**abilities_data)

    async def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """解析JSON响应"""
        try:
            # 尝试直接解析JSON
            json_start = response.find("{")
            json_end = response.rfind("}") + 1

            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            else:
                # 如果找不到JSON，使用LLM重新结构化
                return await self._structure_response_with_llm(response)

        except json.JSONDecodeError as e:
            logger.warning(f"JSON解析失败: {e}，尝试用LLM重新结构化")
            return await self._structure_response_with_llm(response)

    async def _structure_response_with_llm(self, response: str) -> Dict[str, Any]:
        """使用LLM重新结构化响应"""

        structure_prompt = f"""
        请将以下文本转换为标准JSON格式：

        原文：
        {response}

        请返回有效的JSON格式，只返回JSON，不要其他解释。
        """

        structure_response = await self.llm_service.generate_text(structure_prompt)

        try:
            json_start = structure_response.content.find("{")
            json_end = structure_response.content.rfind("}") + 1

            if json_start != -1 and json_end > json_start:
                json_str = structure_response.content[json_start:json_end]
                return json.loads(json_str)
            else:
                # 如果还是失败，返回默认值
                logger.error("LLM结构化也失败，使用默认值")
                return self._get_default_values()

        except json.JSONDecodeError:
            logger.error("LLM结构化解析失败，使用默认值")
            return self._get_default_values()

    def _get_default_values(self) -> Dict[str, Any]:
        """获取默认值"""
        return {
            "name": f"角色{random.randint(1, 999)}",
            "nickname": "暂无",
            "story_role": "推动情节发展",
            "character_arc": "从弱小到强大",
            "gender": "男",
            "age": 18,
            "height": "中等",
            "build": "匀称",
            "hair_color": "黑色",
            "eye_color": "黑色",
            "skin_tone": "正常",
            "distinctive_features": ["气质不凡"],
            "clothing_style": "简朴",
            "accessories": ["随身佩剑"],
            "core_traits": ["坚韧", "正义"],
            "strengths": ["意志坚强"],
            "weaknesses": ["过于冲动"],
            "fears": ["失去亲人"],
            "desires": ["变强"],
            "habits": ["勤奋修炼"],
            "speech_pattern": "直接",
            "moral_alignment": "善良",
            "birthplace": "小山村",
            "family": {"父亲": "普通村民", "母亲": "普通村民"},
            "childhood": "平凡的村庄生活",
            "education": ["私塾"],
            "major_events": [{"事件": "踏上修仙路", "影响": "改变人生"}],
            "relationships": [{"关系": "师父", "描述": "引路人"}],
            "secrets": ["身世之谜"],
            "goals": ["变强", "保护家人"],
            "power_level": "炼气期",
            "cultivation_method": "基础功法",
            "special_abilities": [{"名称": "灵力感知", "描述": "感知周围灵力"}],
            "combat_skills": ["剑法"],
            "non_combat_skills": ["炼丹"],
            "artifacts": [{"名称": "飞剑", "品级": "法器", "描述": "普通飞剑"}],
            "spiritual_root": "金属性",
            "talent_level": "中等"
        }

    def _load_character_templates(self) -> Dict[str, Dict]:
        """加载角色模板"""
        return {
            "主角": {
                "importance": 10,
                "typical_traits": ["勇敢", "坚韧", "正义"],
                "typical_background": "平凡出身",
                "power_progression": "快速成长"
            },
            "反派": {
                "importance": 8,
                "typical_traits": ["野心", "狡诈", "强大"],
                "typical_background": "显赫出身",
                "power_progression": "已经强大"
            }
        }

    def _calculate_importance(self, character_type: str) -> int:
        """计算重要性"""
        importance_map = {
            "主角": 10,
            "重要配角": 8,
            "一般配角": 5,
            "反派": 9,
            "导师": 7,
            "爱情线角色": 6,
            "搞笑角色": 4,
            "背景角色": 2
        }
        return importance_map.get(character_type, 5)


class CharacterCreatorTool(AsyncTool):
    """角色创建工具"""

    def __init__(self):
        super().__init__()
        self.creator = CharacterCreator()

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
