# modules/character/character_creator.py
"""
角色创建器
负责生成各种类型的角色
"""
import asyncio
import json
import random
import re
from dataclasses import dataclass
from datetime import time
from enum import Enum
from typing import Dict, Any, List, Optional, Set

from loguru import logger

from config.settings import get_prompt_manager
from core.llm_client import get_llm_service


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
    growth_potential: str = ""


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


def _load_name_banks() -> Dict[str, List[str]]:
    """加载名称库"""
    return {
        "surnames": [
            "李", "王", "张", "刘", "陈", "杨", "赵", "黄", "周", "吴",
            "徐", "孙", "胡", "朱", "高", "林", "何", "郭", "马", "罗",
            "慕容", "欧阳", "上官", "司徒", "诸葛", "司马", "独孤", "南宫"
        ],
        "male_given": [
            "轩", "辰", "宇", "晨", "阳", "昊", "睿", "泽", "浩", "瑜",
            "煜", "炎", "焱", "烨", "炜", "琛", "瑾", "瑄", "璟", "曜",
            "逍遥", "无极", "天行", "星河", "风云", "雷霆", "破军", "贪狼"
        ],
        "female_given": [
            "雪", "霜", "月", "星", "云", "烟", "露", "霞", "虹", "彩",
            "琴", "瑟", "筝", "萧", "瑶", "瑾", "莲", "荷", "兰", "菊",
            "若水", "如梦", "似雪", "凌波", "惊鸿", "飞燕", "紫烟", "青莲"
        ]
    }


class CharacterCreator:
    """角色创建器"""

    def __init__(self):
        self.llm_service = get_llm_service()
        self.prompt_manager = get_prompt_manager()
        self.character_templates = self._load_character_templates()

        # 添加名称管理
        self.used_names: Set[str] = set()
        self.name_banks = _load_name_banks()

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
        """生成基础信息 - 修复版"""

        # # 生成独特名字
        # character_name = await self._generate_unique_name(
        #     character_type, genre, requirements
        # )
        #
        # # 生成绰号
        # nickname = await self._generate_nickname(character_name, character_type)
        #
        # return {
        #     "name": character_name,
        #     "nickname": nickname,
        #     "importance": self._calculate_importance(character_type),
        #     "story_role": f"{character_type}角色",
        #     "character_arc": self._generate_character_arc_description(character_type)
        # }

        # 使用详细的基础信息模板
        prompt = self.prompt_manager.get_prompt(
            "character",
            "basic_info",
            character_type=character_type,
            genre=genre,
            requirements=requirements or {}
        )

        # 添加更详细的要求
        prompt += f"""

            请以JSON格式返回完整的基础信息：
            {{
                "name": "富有含义的角色姓名",
                "gender": "性别",
                "age": 具体年龄数字,
                "nickname": "有特色的绰号（可选）",
                "importance": {self._calculate_importance(character_type)},
                "story_role": "在故事中的具体作用和地位",
                "character_arc": "角色发展弧线描述",
                "brief_description": "角色一句话概括",
                "key_relationships": ["与其他角色的关系1", "关系2"]
            }}

            要求：
            - 姓名要有深意，符合{genre}世界观
            - 角色要有鲜明特色，避免平庸
            - 为后续发展留下充足空间
            """

        response_text = await self._generate_with_retry(prompt)
        basic_info = await self._parse_json_response(response_text)

        # 确保基础信息完整
        basic_info = self._ensure_complete_basic_info(basic_info, character_type, genre,requirements)

        logger.info(f"生成的基础信息: {basic_info}")
        return basic_info

    async def _ensure_complete_basic_info(self, data: Dict, character_type: str, genre: str,requirements: Optional[Dict] = None) -> Dict:
        """确保基础信息完整"""

        # 如果没有姓名，生成一个
        if not data.get("name"):
            # 生成独特名字
            character_name = await self._generate_unique_name(
                character_type, genre, requirements
            )

            # 生成绰号
            nickname = await self._generate_nickname(character_name, character_type)
            data["name"] = character_name#self._generate_random_name(character_type)
            data['nickname']=nickname

        defaults = {
            "gender": "男" if character_type in ["主角", "反派"] else random.choice(["男", "女"]),
            "age": random.randint(16, 30) if character_type == "主角" else random.randint(20, 50),
            "importance": self._calculate_importance(character_type),
            "story_role": f"{character_type}角色，推动故事发展",
            "character_arc": self._generate_character_arc_description(character_type),
            "brief_description": f"一个{character_type}角色",
            "key_relationships": []
        }

        for key, default_value in defaults.items():
            if key not in data or not data[key]:
                data[key] = default_value

        return data

    async def _generate_unique_name(self, character_type: str, genre: str,
                                    requirements: Optional[Dict] = None) -> str:
        """生成独特的角色名字"""

        max_attempts = 10

        for attempt in range(max_attempts):
            if attempt < 5:
                # 前5次尝试使用LLM生成
                name = await self._generate_name_with_llm(character_type, genre, requirements,
                                                          attempt)
            else:
                # 后5次使用规则生成
                name = self._generate_name_with_rules(character_type, requirements)

            if name and name not in self.used_names:
                self.used_names.add(name)
                return name

        # 如果都失败了，生成带数字后缀的名字
        base_name = self._generate_name_with_rules(character_type, requirements)
        unique_name = f"{base_name}{random.randint(10, 99)}"
        self.used_names.add(unique_name)
        return unique_name

    async def _generate_name_with_llm(self, character_type: str, genre: str,
                                      requirements: Optional[Dict], seed: int) -> str:
        """使用LLM生成名字"""

        # 增加创意种子
        creativity_seeds = [
            "古风雅韵", "仙侠风范", "英雄气概", "神秘莫测", "温文儒雅"
        ]

        creativity_hint = creativity_seeds[seed % len(creativity_seeds)]

        gender = requirements.get("gender", "any") if requirements else "any"
        traits = requirements.get("traits", []) if requirements else []

        prompt = f"""
        为{genre}小说创造一个独特的{character_type}角色名字：

        要求：
        - 性别：{gender}
        - 性格特征：{traits}
        - 风格：{creativity_hint}
        - 绝对避免使用：{list(self.used_names)}
        - 要求原创性，不能是常见的网络小说角色名
        - 名字要有文化内涵和美感
        - 符合{genre}世界观

        创意编号：{seed + int(time.time()) % 1000}

        请只返回一个名字：
        """

        response = await self.llm_service.generate_text(
            prompt,
            temperature=0.85 + (seed * 0.02),  # 每次尝试增加随机性
            max_tokens=30
        )

        return self._extract_name_from_response(response.content)

    def _generate_name_with_rules(self, character_type: str,
                                  requirements: Optional[Dict] = None) -> str:
        """使用规则生成名字"""

        gender = requirements.get("gender", "any") if requirements else "any"

        # 选择姓氏
        surname = random.choice(self.name_banks["surnames"])

        # 根据性别选择名字
        if gender == "male":
            given_pool = self.name_banks["male_given"]
        elif gender == "female":
            given_pool = self.name_banks["female_given"]
        else:
            given_pool = self.name_banks["male_given"] + self.name_banks["female_given"]

        # 生成名字
        if random.random() < 0.6:  # 60%概率双字名
            if random.random() < 0.3:  # 30%概率用预定义组合
                given_name = random.choice([n for n in given_pool if len(n) > 1])
            else:  # 70%概率随机组合单字
                single_chars = [n for n in given_pool if len(n) == 1]
                given_name = random.choice(single_chars) + random.choice(single_chars)
        else:  # 40%概率单字名
            given_name = random.choice([n for n in given_pool if len(n) == 1])

        return surname + given_name

    def _extract_name_from_response(self, response: str) -> str:
        """从响应中提取姓名 - 修复版"""

        # 清理响应
        cleaned = response.strip()

        # 移除常见前缀
        prefixes = ["名字：", "姓名：", "角色名：", "建议：", "推荐："]
        for prefix in prefixes:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()

        # 移除引号和标点
        cleaned = re.sub(r'["""''`()（）【】\[\]<>《》]', '', cleaned)
        cleaned = re.sub(r'[，。！？；：,!?;:].*', '', cleaned)

        # 提取第一个词
        words = cleaned.split()
        if words:
            potential_name = words[0]
            # 验证是中文名字（2-4个字符）
            if 2 <= len(potential_name) <= 4 and all(
                '\u4e00' <= c <= '\u9fff' for c in potential_name):
                return potential_name

        # 提取失败，生成随机名字
        return self._generate_name_with_rules("主角")

    async def _generate_nickname(self, name: str, character_type: str) -> Optional[str]:
        """生成绰号"""

        if random.random() < 0.3:  # 30%概率有绰号
            prompt = f"""
            为{character_type}角色{name}生成一个武侠风格的绰号：

            要求：
            1. 体现角色特色
            2. 简洁有力
            3. 避免俗套
            4. 2-4个字

            只返回绰号：
            """

            response = await self.llm_service.generate_text(prompt, temperature=0.8)
            nickname = response.content.strip().replace('"', '')

            if len(nickname) <= 6:
                return nickname

        return None

    def _generate_character_arc_description(self, character_type: str) -> str:
        """生成角色弧线描述"""
        arc_templates = {
            "主角": "从平凡到非凡的成长历程",
            "重要配角": "与主角并肩成长的伙伴之路",
            "反派": "从对立到可能的救赎",
            "导师": "传承智慧与最终的告别",
            "爱情线角色": "情感的萌芽与深化"
        }
        return arc_templates.get(character_type, "角色的发展轨迹")

    async def _generate_appearance(self, basic_info: Dict,
                                   world_setting: Optional[Dict]) -> CharacterAppearance:
        """生成外貌"""

        # 使用 character.yaml 中的详细模板
        prompt = self.prompt_manager.get_prompt(
            "character",
            "appearance",
            name=basic_info["name"],
            world_setting=world_setting or "标准玄幻世界"
        )

        # 添加JSON格式要求
        prompt += """
            请以完整的JSON格式返回，包含以下所有字段：
            {
                "gender": "性别",
                "age": 年龄数字,
                "height": "详细身高描述",
                "build": "详细体型描述",
                "hair_color": "具体发色和发型",
                "eye_color": "具体眼色和眼神",
                "skin_tone": "肤色和肌肤特点",
                "distinctive_features": ["独特特征1", "独特特征2", "独特特征3"],
                "clothing_style": "详细穿衣风格描述",
                "accessories": ["配饰1", "配饰2", "配饰3"]
            }

            要求每个字段都要具体详细，体现角色个性！
            """

        response = await self.llm_service.generate_text(
            prompt,
            temperature=0.8,  # 提高随机性
            max_tokens=800    # 增加token限制
        )
        appearance_data = await self._parse_json_response(response.content)
        # 确保所有字段都有值
        appearance_data = self._ensure_complete_appearance(appearance_data, basic_info)

        return CharacterAppearance(**appearance_data)

    async def _generate_personality(self, basic_info: Dict,
                                    character_type: str) -> CharacterPersonality:
        """生成性格"""

        # 使用详细模板
        prompt = self.prompt_manager.get_prompt(
            "character",
            "personality",
            name=basic_info["name"],
            character_type=character_type
        )

        prompt += """
请以完整的JSON格式返回：
{
    "core_traits": ["核心特质1", "核心特质2", "核心特质3", "核心特质4", "核心特质5"],
    "strengths": ["具体优点1", "具体优点2", "具体优点3"],
    "weaknesses": ["具体缺点1", "具体缺点2", "具体缺点3"],
    "fears": ["恐惧1", "恐惧2"],
    "desires": ["欲望1", "欲望2", "欲望3"],
    "habits": ["行为习惯1", "行为习惯2", "口头禅"],
    "speech_pattern": "详细的说话方式和语言特色描述",
    "moral_alignment": "具体的道德取向描述"
}

每个字段都要详细具体，体现角色的立体感！
            """

        response = await self.llm_service.generate_text(
            prompt,
            temperature=0.8,
            max_tokens=1000
        )

        personality_data = await self._parse_json_response(response.content)
        personality_data = self._ensure_complete_personality(personality_data, character_type)

        return CharacterPersonality(**personality_data)

    async def _generate_background(self, basic_info: Dict,
                                   world_setting: Optional[Dict]) -> CharacterBackground:
        """生成背景"""

        prompt = self.prompt_manager.get_prompt(
            "character",
            "background",
            name=basic_info["name"],
            world_setting=world_setting or "标准玄幻世界"
        )

        prompt += """
请以完整的JSON格式返回：
{
    "birthplace": "具体出生地描述",
    "family": {
        "father": "父亲详细信息",
        "mother": "母亲详细信息",
        "siblings": "兄弟姐妹信息",
        "others": "其他重要亲属"
    },
    "childhood": "详细童年经历描述（至少100字）",
    "education": ["教育经历1", "教育经历2", "师承关系"],
    "major_events": [
        {"event": "重大事件1", "age": "发生年龄", "impact": "对角色的影响"},
        {"event": "重大事件2", "age": "发生年龄", "impact": "对角色的影响"},
        {"event": "重大事件3", "age": "发生年龄", "impact": "对角色的影响"}
    ],
    "relationships": [
        {"relation": "关系类型", "name": "人物姓名", "description": "关系描述"},
        {"relation": "关系类型", "name": "人物姓名", "description": "关系描述"}
    ],
    "secrets": ["个人秘密1", "个人秘密2"],
    "goals": ["人生目标1", "人生目标2", "当前目标"]
}

背景要丰富详细，为角色行为提供充分动机！
            """

        response = await self.llm_service.generate_text(
            prompt,
            temperature=0.8,
            max_tokens=1200
        )

        background_data = await self._parse_json_response(response.content)
        background_data = self._ensure_complete_background(background_data)

        return CharacterBackground(**background_data)

    async def _generate_abilities(self, basic_info: Dict, genre: str,
                                  world_setting: Optional[Dict]) -> CharacterAbilities:
        """生成能力"""

        prompt = self.prompt_manager.get_prompt(
            "character",
            "abilities",
            name=basic_info["name"],
            genre=genre,
            world_setting=world_setting or "标准玄幻世界"
        )

        prompt += """
请以完整的JSON格式返回：
{
    "power_level": "详细实力等级描述",
    "cultivation_method": "具体修炼功法名称和特点",
    "special_abilities": [
        {"name": "特殊能力1", "description": "详细能力描述", "level": "熟练程度"},
        {"name": "特殊能力2", "description": "详细能力描述", "level": "熟练程度"},
        {"name": "特殊能力3", "description": "详细能力描述", "level": "熟练程度"}
    ],
    "combat_skills": ["战斗技能1", "战斗技能2", "战斗技能3", "招式名称"],
    "non_combat_skills": ["非战斗技能1", "非战斗技能2", "生活技能"],
    "artifacts": [
        {"name": "法宝名称", "grade": "品级", "description": "详细描述", "abilities": "法宝能力"},
        {"name": "装备名称", "grade": "品级", "description": "详细描述", "abilities": "装备效果"}
    ],
    "spiritual_root": "灵根属性和天赋描述",
    "talent_level": "天赋等级和具体表现",
    "growth_potential": "成长潜力和未来发展方向"
}

能力体系要完整详细，符合世界观设定！
            """

        response = await self.llm_service.generate_text(
            prompt,
            temperature=0.8,
            max_tokens=1200
        )

        abilities_data = await self._parse_json_response(response.content)
        abilities_data = self._ensure_complete_abilities(abilities_data, genre)

        return CharacterAbilities(**abilities_data)

    async def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """解析JSON响应 - 增强版"""
        import json
        import re

        logger.info(f"原始响应: {response}")

        try:
            # 方法1: 直接解析
            if response.strip().startswith('{') and response.strip().endswith('}'):
                result = json.loads(response.strip())
                logger.info("直接JSON解析成功")
                return result

        except json.JSONDecodeError as e:
            logger.warning(f"直接JSON解析失败: {e}")

        try:
            # 方法2: 提取JSON块
            json_pattern = r'\{(?:[^{}]|{[^{}]*})*\}'
            json_matches = re.findall(json_pattern, response, re.DOTALL)

            if json_matches:
                # 尝试最大的JSON块
                largest_json = max(json_matches, key=len)
                result = json.loads(largest_json)
                logger.info("JSON块提取解析成功")
                return result

        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"JSON块提取解析失败: {e}")

        try:
            # 方法3: 清理后解析
            cleaned = response.strip()
            # 移除markdown代码块标记
            cleaned = re.sub(r'```(?:json)?\s*', '', cleaned)
            cleaned = re.sub(r'```\s*$', '', cleaned)
            # 移除多余的文本
            start_idx = cleaned.find('{')
            end_idx = cleaned.rfind('}') + 1

            if start_idx != -1 and end_idx > start_idx:
                json_str = cleaned[start_idx:end_idx]
                result = json.loads(json_str)
                logger.info("清理后JSON解析成功")
                return result

        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"清理后JSON解析失败: {e}")

        try:
            # 方法4: 尝试修复常见JSON错误
            fixed_response = self._fix_common_json_errors(response)
            result = json.loads(fixed_response)
            logger.info("修复后JSON解析成功")
            return result

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"所有JSON解析方法都失败: {e}")

        # 方法5: 如果所有方法都失败，尝试从文本中提取信息
        logger.warning("JSON解析完全失败，尝试文本解析")
        return self._parse_text_response(response)

    def _fix_common_json_errors(self, text: str) -> str:
        """修复常见的JSON错误"""
        # 移除注释
        text = re.sub(r'//.*?\n', '\n', text)
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)

        # 修复单引号
        text = re.sub(r"'([^']*)':", r'"\1":', text)
        text = re.sub(r": '([^']*)'", r': "\1"', text)

        # 修复缺失的引号
        text = re.sub(r'(\w+):', r'"\1":', text)

        # 修复尾部逗号
        text = re.sub(r',(\s*[}\]])', r'\1', text)

        return text

    def _parse_text_response(self, response: str) -> Dict[str, Any]:
        """从文本中解析信息"""
        result = {}

        # 基本模式匹配
        patterns = {
            'name': r'(?:姓名|名字|name)[：:]\s*([^\n,，]+)',
            'gender': r'(?:性别|gender)[：:]\s*([^\n,，]+)',
            'age': r'(?:年龄|age)[：:]\s*(\d+)',
            'height': r'(?:身高|height)[：:]\s*([^\n,，]+)',
            'personality': r'(?:性格|特质|personality)[：:]\s*([^\n]+)',
            'background': r'(?:背景|出身|background)[：:]\s*([^\n]+)',
            'abilities': r'(?:能力|技能|abilities)[：:]\s*([^\n]+)'
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                result[key] = match.group(1).strip()

        logger.info(f"文本解析结果: {result}")
        return result

    # 添加重试机制
    async def _generate_with_retry(self, prompt: str, max_retries: int = 3) -> str:
        """带重试的生成"""

        for attempt in range(max_retries):
            try:
                response = await self.llm_service.generate_text(
                    prompt,
                    temperature=0.8 + (attempt * 0.1),  # 逐渐增加随机性
                    max_tokens=1000 + (attempt * 200)  # 逐渐增加token限制
                )

                # 验证响应质量
                if len(response.content.strip()) > 50:  # 基本长度检查
                    return response.content
                else:
                    logger.warning(f"第{attempt + 1}次生成内容过短，重试")

            except Exception as e:
                logger.error(f"第{attempt + 1}次生成失败: {e}")

            if attempt < max_retries - 1:
                await asyncio.sleep(1)  # 短暂等待后重试

        raise Exception("生成失败，已达到最大重试次数")

    # 添加完整性检查方法
    def _ensure_complete_appearance(self, data: Dict, basic_info: Dict) -> Dict:
        """确保外貌信息完整"""
        defaults = {
            "gender": basic_info.get("gender", "男"),
            "age": 20,
            "height": "中等身材",
            "build": "匀称健康",
            "hair_color": "黑色长发",
            "eye_color": "深邃黑眸",
            "skin_tone": "健康肤色",
            "distinctive_features": ["剑眉星目", "气质出众"],
            "clothing_style": "简洁大方",
            "accessories": ["无特殊配饰"]
        }

        for key, default_value in defaults.items():
            if key not in data or not data[key]:
                data[key] = default_value

        # Filter to only include valid CharacterAppearance fields
        valid_fields = {
            'gender', 'age', 'height', 'build', 'hair_color', 'eye_color',
            'skin_tone', 'distinctive_features', 'clothing_style', 'accessories'
        }

        filtered_data = {k: v for k, v in data.items() if k in valid_fields}

        return filtered_data

    def _ensure_complete_personality(self, data: Dict, character_type: str) -> Dict:
        """确保性格信息完整"""
        type_traits = {
            "主角": ["勇敢", "坚毅", "正义", "责任心强", "不服输"],
            "反派": ["野心勃勃", "狡诈", "强势", "目标明确", "手段多样"],
            "配角": ["忠诚", "可靠", "有特色", "支持主角", "各有所长"]
        }

        defaults = {
            "core_traits": type_traits.get(character_type,
                                           ["平衡", "理性", "适应力强", "有原则", "善于学习"]),
            "strengths": ["聪明机智", "意志坚定"],
            "weaknesses": ["过于执着", "有时冲动"],
            "fears": ["失去重要的人", "实力不足"],
            "desires": ["变得更强", "保护他人"],
            "habits": ["深思熟虑", "言而有信"],
            "speech_pattern": "语言简洁有力，逻辑清晰",
            "moral_alignment": "善良正义，有底线原则"
        }

        for key, default_value in defaults.items():
            if key not in data or not data[key]:
                data[key] = default_value

        # Filter to only include valid CharacterAppearance fields
        valid_fields = {
            'core_traits', 'strengths', 'weaknesses', 'fears', 'desires', 'habits',
            'speech_pattern', 'moral_alignment'
        }

        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return filtered_data

    def _ensure_complete_background(self, data: Dict) -> Dict:
        """确保背景信息完整"""
        defaults = {
            "birthplace": "某个偏远村庄",
            "family": {"father": "普通村民", "mother": "温柔善良"},
            "childhood": "在平凡的环境中成长，从小展现出与众不同的特质",
            "education": ["基础启蒙教育"],
            "major_events": [{"event": "踏上修行路", "age": "16", "impact": "改变人生轨迹"}],
            "relationships": [{"relation": "师父", "name": "引路人", "description": "人生导师"}],
            "secrets": ["身世之谜"],
            "goals": ["提升实力", "找寻真相"]
        }

        for key, default_value in defaults.items():
            if key not in data or not data[key]:
                data[key] = default_value
        # Filter to only include valid CharacterAppearance fields
        valid_fields = {
            'birthplace', 'family', 'childhood', 'education', 'major_events', 'relationships',
            'secrets', 'goals'
        }

        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return filtered_data

    def _ensure_complete_abilities(self, data: Dict, genre: str) -> Dict:
        """确保能力信息完整"""
        defaults = {
            "power_level": "初入门径",
            "cultivation_method": "基础心法",
            "special_abilities": [
                {"name": "灵力感知", "description": "能够感知周围的灵力波动", "level": "初级"}],
            "combat_skills": ["基础剑法", "徒手搏击"],
            "non_combat_skills": ["医术基础", "炼丹入门"],
            "artifacts": [{"name": "普通长剑", "grade": "凡器", "description": "锋利的铁剑",
                           "abilities": "无特殊能力"}],
            "spiritual_root": "混合灵根",
            "talent_level": "中等资质",
            "growth_potential": "潜力无限，后期发力"
        }

        for key, default_value in defaults.items():
            if key not in data or not data[key]:
                data[key] = default_value

        # Filter to only include valid CharacterAppearance fields
        valid_fields = {
            'power_level', 'cultivation_method', 'special_abilities', 'combat_skills', 'non_combat_skills', 'artifacts',
            'spiritual_root', 'talent_level','growth_potential'
        }

        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return filtered_data

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



