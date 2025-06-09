
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

        # 生成外貌
        appearance = await self._generate_appearance(basic_info, world_setting)

        # 生成性格
        personality = await self._generate_personality(basic_info, character_type)

        # 生成背景
        background = await self._generate_background(basic_info, world_setting)

        # 生成能力
        abilities = await self._generate_abilities(basic_info, genre, world_setting)

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

        prompt = self.prompt_manager.get_prompt(
            "character",
            "basic_info",
            character_type=character_type,
            genre=genre,
            requirements=requirements or {}
        )

        response = await self.llm_service.generate_text(prompt)

        # 解析响应
        return {
            "name": self._extract_name_from_response(response.content),
            "nickname": self._extract_nickname_from_response(response.content),
            "importance": self._calculate_importance(character_type),
            "story_role": self._extract_story_role(response.content),
            "character_arc": self._extract_character_arc(response.content)
        }

    async def _generate_appearance(self, basic_info: Dict, world_setting: Optional[Dict]) -> CharacterAppearance:
        """生成外貌"""

        prompt = self.prompt_manager.get_prompt(
            "character",
            "appearance",
            name=basic_info["name"],
            world_setting=world_setting or {}
        )

        response = await self.llm_service.generate_text(prompt)

        return CharacterAppearance(
            gender=self._extract_gender(response.content),
            age=self._extract_age(response.content),
            height=self._extract_height(response.content),
            build=self._extract_build(response.content),
            hair_color=self._extract_hair_color(response.content),
            eye_color=self._extract_eye_color(response.content),
            skin_tone=self._extract_skin_tone(response.content),
            distinctive_features=self._extract_features(response.content),
            clothing_style=self._extract_clothing(response.content),
            accessories=self._extract_accessories(response.content)
        )

    async def _generate_personality(self, basic_info: Dict, character_type: str) -> CharacterPersonality:
        """生成性格"""

        prompt = self.prompt_manager.get_prompt(
            "character",
            "personality",
            name=basic_info["name"],
            character_type=character_type
        )

        response = await self.llm_service.generate_text(prompt)

        return CharacterPersonality(
            core_traits=["勇敢", "坚韧"],
            strengths=["意志坚强", "正义感"],
            weaknesses=["过于冲动", "容易信任他人"],
            fears=["失去亲人", "力量不足"],
            desires=["变强", "保护重要的人"],
            habits=["晨练", "独自思考"],
            speech_pattern="直接坦率",
            moral_alignment="守序善良"
        )

    async def _generate_background(self, basic_info: Dict, world_setting: Optional[Dict]) -> CharacterBackground:
        """生成背景"""

        prompt = self.prompt_manager.get_prompt(
            "character",
            "background",
            name=basic_info["name"],
            world_setting=world_setting or {}
        )

        response = await self.llm_service.generate_text(prompt)

        return CharacterBackground(
            birthplace="小山村",
            family={"父亲": "村民", "母亲": "村民"},
            childhood="普通的村庄生活",
            education=["私塾", "武馆"],
            major_events=[{"事件": "家族遭难", "影响": "踏上修仙路"}],
            relationships=[{"关系": "师父", "描述": "引路人"}],
            secrets=["身世之谜"],
            goals=["复仇", "变强", "保护家园"]
        )

    async def _generate_abilities(self, basic_info: Dict, genre: str,
                                world_setting: Optional[Dict]) -> CharacterAbilities:
        """生成能力"""

        prompt = self.prompt_manager.get_prompt(
            "character",
            "abilities",
            name=basic_info["name"],
            genre=genre,
            world_setting=world_setting or {}
        )

        response = await self.llm_service.generate_text(prompt)

        return CharacterAbilities(
            power_level="炼气期",
            cultivation_method="基础功法",
            special_abilities=[{"名称": "灵力感知", "描述": "感知周围灵力"}],
            combat_skills=["剑法", "身法"],
            non_combat_skills=["炼丹", "阵法"],
            artifacts=[{"名称": "飞剑", "品级": "法器"}],
            spiritual_root="金属性",
            talent_level="中等"
        )

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

    # 辅助方法
    def _extract_name_from_response(self, response: str) -> str:
        """从响应中提取姓名"""
        # 简单实现，实际可以用正则或NLP
        return "李逍遥"

    def _extract_nickname_from_response(self, response: str) -> Optional[str]:
        """提取绰号"""
        return "剑仙"

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

    def _extract_story_role(self, response: str) -> str:
        """提取故事作用"""
        return "推动情节发展"

    def _extract_character_arc(self, response: str) -> str:
        """提取角色弧线"""
        return "从弱小到强大"

    def _extract_gender(self, response: str) -> str:
        """提取性别"""
        return "男"

    def _extract_age(self, response: str) -> int:
        """提取年龄"""
        return 18

    def _extract_height(self, response: str) -> str:
        """提取身高"""
        return "中等"

    def _extract_build(self, response: str) -> str:
        """提取体型"""
        return "匀称"

    def _extract_hair_color(self, response: str) -> str:
        """提取发色"""
        return "黑色"

    def _extract_eye_color(self, response: str) -> str:
        """提取眼色"""
        return "黑色"

    def _extract_skin_tone(self, response: str) -> str:
        """提取肤色"""
        return "正常"

    def _extract_features(self, response: str) -> List[str]:
        """提取特征"""
        return ["剑眉星目", "气质不凡"]

    def _extract_clothing(self, response: str) -> str:
        """提取穿衣风格"""
        return "青衫布衣"

    def _extract_accessories(self, response: str) -> List[str]:
        """提取配饰"""
        return ["玉佩", "长剑"]


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

