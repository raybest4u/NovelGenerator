# main_enhanced_improved.py
"""
改进版玄幻小说自动生成器 - 修复完整性和人物丰富度问题
"""

import asyncio
import argparse
import json
import re
import sys
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List, Set

from loguru import logger

from config.settings import get_settings, validate_config
from core.mcp_server import get_mcp_server
from core.llm_client import get_llm_service
from core.base_tools import get_tool_registry

from modules.character.development import register_character_tools
from modules.plot.arc_manager import register_plot_tools
from modules.tools.consistency_checker import register_tools
from modules.worldbuilding.geography import register_worldbuilding_tools
from modules.writing.description_writer import register_writing_tools

from modules.generation.diversity_enhancer import DiversityEnhancerTool
from modules.generation.enhanced_story_generator import EnhancedStoryGeneratorTool
import random
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio


class StoryGenre(Enum):
    """故事类型枚举"""
    FANTASY = "fantasy"
    ROMANCE = "romance"
    MYSTERY = "mystery"
    THRILLER = "thriller"
    SCIENCE_FICTION = "sci-fi"
    HISTORICAL = "historical"
    CONTEMPORARY = "contemporary"
    ADVENTURE = "adventure"


class CharacterArchetype(Enum):
    """角色原型枚举"""
    HERO = "hero"
    MENTOR = "mentor"
    THRESHOLD_GUARDIAN = "threshold_guardian"
    HERALD = "herald"
    SHAPESHIFTER = "shapeshifter"
    SHADOW = "shadow"
    ALLY = "ally"
    TRICKSTER = "trickster"


@dataclass
class CharacterProfile:
    """角色档案"""
    name: str
    role: str
    archetype: CharacterArchetype
    personality_traits: List[str]
    background: str
    motivations: List[str]
    goals: List[str]
    conflicts: List[str]
    relationships: Dict[str, str]
    character_arc: Dict[str, str]
    dialogue_style: str
    physical_description: str
    skills_abilities: List[str]
    weaknesses: List[str]
    secrets: List[str]
    importance_level: int  # 1-10, 10为最重要


class CharacterRelationship:
    """角色关系类"""

    def __init__(self, char1: str, char2: str, relationship_type: str,
                 intensity: int, description: str):
        self.char1 = char1
        self.char2 = char2
        self.relationship_type = relationship_type
        self.intensity = intensity  # 1-10
        self.description = description

class EnhancedNovelGenerator:
    """改进版小说生成器"""

    def __init__(self):
        self.settings = get_settings()
        self.llm_service = get_llm_service()
        self.tool_registry = get_tool_registry()
        self.mcp_server = get_mcp_server()

        self._register_all_tools()
        self.diversity_tool = DiversityEnhancerTool()
        self.enhanced_generator = EnhancedStoryGeneratorTool()
        # 初始化全局名称管理器
        self.global_name_tracker: Set[str] = set()

    def _register_all_tools(self):
        """注册所有工具"""
        logger.info("正在注册工具...")

        register_worldbuilding_tools()
        register_character_tools()
        register_plot_tools()
        register_writing_tools()
        register_tools()

        self.tool_registry.register(DiversityEnhancerTool())
        self.tool_registry.register(EnhancedStoryGeneratorTool())

        tool_count = len(self.tool_registry.tools)
        logger.info(f"已注册 {tool_count} 个工具")

    async def generate_novel_enhanced_improved(
        self,
        title: str,
        genre: str = "玄幻",
        chapter_count: int = 10,
        theme: str = "成长",
        randomization_level: float = 0.8,
        auto_save: bool = True,
        force_diversity: bool = False
    ) -> Dict[str, Any]:
        """改进版增强小说生成"""

        logger.info(f"开始使用改进版增强模式生成小说《{title}》...")

        try:
            # 1. 检查多样性状况
            diversity_check = await self._check_diversity_status()

            if diversity_check["diversity_score"] < 0.6 or force_diversity:
                logger.info(f"多样性得分: {diversity_check['diversity_score']:.2f}, 启用增强模式")

                # 2. 生成增强的故事框架
                story_framework = await self._generate_enhanced_story_framework(
                    title, theme, chapter_count, randomization_level
                )
                logger.info(f"生成增强的故事框架:{json.dumps(story_framework, ensure_ascii=False, indent=2)}")
                # 3. 生成丰富的角色体系
                character_system = await self._generate_rich_character_system(
                    story_framework, chapter_count
                )
                logger.info(
                    f"生成丰富的角色体系:{character_system}")
                # 4. 生成详细的章节规划
                detailed_chapters = await self._generate_detailed_chapter_planning(
                    story_framework, character_system, chapter_count
                )
                logger.info(
                    f"生成详细的章节规划:{json.dumps(detailed_chapters, ensure_ascii=False, indent=2)}")
                # 5. 生成高质量章节内容
                final_chapters = await self._generate_quality_chapters(
                    detailed_chapters, story_framework, character_system
                )
                # logger.info(f"生成高质量章节内容:{final_chapters}")
                # 6. 进行一致性检查和修正
                validated_content = await self._validate_and_fix_consistency(
                    final_chapters, story_framework, character_system
                )

                # 7. 组装完整小说
                novel_data = await self._assemble_complete_novel(
                    title, genre, theme, story_framework, character_system,
                    validated_content, randomization_level
                )

            else:
                logger.info(f"多样性得分: {diversity_check['diversity_score']:.2f}, 使用标准模式")
                novel_data = await self._generate_fallback_novel(
                    title, genre, chapter_count, theme
                )
                novel_data["enhanced"] = False

            # 8. 保存小说
            if auto_save:
                await self._save_novel_improved(novel_data)

            logger.info(f"✓ 小说《{title}》生成完成！总字数：{novel_data['total_word_count']}")
            return novel_data

        except Exception as e:
            logger.error(f"改进版增强小说生成失败: {e}")
            raise e

    async def _generate_enhanced_story_framework(
        self, title: str, theme: str, chapter_count: int, randomization_level: float
    ) -> Dict[str, Any]:
        """生成增强的故事框架"""

        logger.info("生成故事框架...")

        # 生成基础配置
        config_result = await self.enhanced_generator.execute({
            "action": "config",
            "base_theme": theme,
            "randomization_level": randomization_level,
            "avoid_recent": True
        })

        config = config_result["config"]

        # 生成详细大纲
        outline_result = await self.enhanced_generator.execute({
            "action": "outline",
            "config": config,
            "chapter_count": chapter_count
        })

        plot_outline = outline_result["plot_outline"]

        return {
            "title": title,
            "config": config,
            "plot_outline": plot_outline,
            "variant": config["variant"],
            "innovation_factors": config["innovation_factors"]
        }

    async def back_generate_rich_character_system(
        self, story_framework: Dict[str, Any], chapter_count: int
    ) -> Dict[str, Any]:
        """生成丰富的角色体系"""

        logger.info("生成丰富角色体系...")

        config = story_framework["config"]

        # 清理名称缓存，开始新故事
        self.global_name_tracker.clear()

        # 生成主要角色
        main_characters = []
        character_roles = [
            ("protagonist", "主角"),
            ("antagonist", "反派"),
            ("deuteragonist", "重要配角"),
            ("mentor", "导师"),
            ("love_interest", "爱情线角色")
        ]

        for role_key, role_name in character_roles:
            # 确保传递名称避免列表
            enhanced_config = config.copy()
            enhanced_config["avoid_names"] = list(self.global_name_tracker)

            char_result = await self.enhanced_generator.execute({
                "action": "character",
                "config": enhanced_config
            })

            character = char_result["character"]
            character["id"] = str(uuid.uuid4())
            character["role_type"] = role_key
            character["role_name"] = role_name
            # 记录名称
            char_name = character.get("name", "")
            if char_name:
                self.global_name_tracker.add(char_name)
            main_characters.append(character)
            logger.info(
                f"✓ 生成{role_name}-->{character['name']}: {json.dumps(character, ensure_ascii=False, indent=2)}")

        # 生成角色关系网络
        relationships = await self._generate_character_relationships(main_characters)
        logger.info(
            f"✓ 生成角色关系网络: {json.dumps(relationships, ensure_ascii=False, indent=2)}")

        # 生成角色发展轨迹
        character_arcs = await self._generate_character_development_arcs(
            main_characters, chapter_count
        )
        logger.info(
            f"✓ 生成角色发展轨迹: {json.dumps(character_arcs, ensure_ascii=False, indent=2)}")

        return {
            "main_characters": main_characters,
            "relationships": relationships,
            "character_arcs": character_arcs,
            "character_count": len(main_characters)
        }

    async def _generate_rich_character_system(
        self, story_framework: Dict[str, Any], chapter_count: int
    ) -> Dict[str, Any]:
        """生成丰富的角色体系"""

        logger.info("开始生成丰富角色体系...")

        config = story_framework["config"]
        story_theme = config.get("theme", "")
        story_genre = StoryGenre(config.get("genre", "contemporary"))
        story_setting = config.get("setting", "")
        target_audience = config.get("target_audience", "general")

        # 清理名称缓存
        self.global_name_tracker.clear()

        # 根据故事类型和章节数智能确定角色配置
        character_config = await self._determine_character_configuration(
            story_genre, chapter_count, story_theme
        )

        # 生成核心角色群
        main_characters = await self._generate_core_characters(
            character_config, config, story_framework
        )
        logger.info(f"生成核心角色群===>{len(main_characters)}")

        # 生成支持角色
        supporting_characters = await self._generate_supporting_characters(
            character_config, config, story_framework, main_characters
        )
        logger.info(f"生成支持角色===>{len(supporting_characters)}")
        # 建立角色关系网络
        character_relationships = await self._build_character_relationships(
            main_characters + supporting_characters, story_framework
        )
        logger.info(f"建立角色关系网络===>{character_relationships}")
        # 分配角色在各章节中的作用
        character_chapter_roles = await self._assign_chapter_roles(
            main_characters + supporting_characters, chapter_count, story_framework
        )
        logger.info(f"分配角色在各章节中的作用===>{character_chapter_roles}")
        # 生成角色发展弧线
        character_arcs = await self._generate_character_arcs(
            main_characters, chapter_count, story_framework
        )
        logger.info(f"生成角色发展弧线===>{character_arcs}")
        return {
            "main_characters": main_characters,
            "supporting_characters": supporting_characters,
            "character_relationships": character_relationships,
            "character_chapter_roles": character_chapter_roles,
            "character_arcs": character_arcs,
            "character_config": character_config
        }

    async def _determine_character_configuration(
        self, genre: StoryGenre, chapter_count: int, theme: str
    ) -> Dict[str, Any]:
        """根据故事类型智能确定角色配置"""

        # 基础配置
        base_config = {
            "core_characters": 5,  # 最少核心角色数
            "max_core_characters": 8,  # 最多核心角色数
            "supporting_characters": 13,
            "max_total_characters": 25
        }

        # 根据类型调整
        genre_adjustments = {
            StoryGenre.FANTASY: {
                "core_characters": 3,
                "max_core_characters": 6,
                "supporting_characters": 5,
                "archetype_preferences": [
                    CharacterArchetype.HERO,
                    CharacterArchetype.MENTOR,
                    CharacterArchetype.SHADOW,
                    CharacterArchetype.ALLY,
                    CharacterArchetype.SHAPESHIFTER
                ]
            },
            StoryGenre.ROMANCE: {
                "core_characters": 2,
                "max_core_characters": 4,
                "supporting_characters": 3,
                "archetype_preferences": [
                    CharacterArchetype.HERO,
                    CharacterArchetype.ALLY,
                    CharacterArchetype.THRESHOLD_GUARDIAN,
                    CharacterArchetype.TRICKSTER
                ]
            },
            StoryGenre.MYSTERY: {
                "core_characters": 2,
                "max_core_characters": 4,
                "supporting_characters": 4,
                "archetype_preferences": [
                    CharacterArchetype.HERO,
                    CharacterArchetype.SHADOW,
                    CharacterArchetype.HERALD,
                    CharacterArchetype.THRESHOLD_GUARDIAN
                ]
            }
        }

        # 根据章节数调整
        if chapter_count > 20:
            base_config["max_core_characters"] += 3
            base_config["supporting_characters"] += 5
            if chapter_count > 40:
                base_config["max_core_characters"] += 10
                base_config["supporting_characters"] += 25
        elif chapter_count < 10:
            base_config["max_core_characters"] -= 1
            base_config["supporting_characters"] -= 1

        # 应用类型特定调整
        if genre in genre_adjustments:
            base_config.update(genre_adjustments[genre])

        return base_config

    async def _generate_core_characters(
        self, character_config: Dict[str, Any], config: Dict[str, Any],
        story_framework: Dict[str, Any]
    ) -> List[CharacterProfile]:
        """生成核心角色"""

        core_characters = []
        archetype_preferences = character_config.get("archetype_preferences",
                                                     list(CharacterArchetype))

        # 确保有主角
        protagonist = await self._create_character(
            role="主角",
            archetype=CharacterArchetype.HERO,
            importance_level=10,
            config=config,
            story_framework=story_framework
        )
        core_characters.append(protagonist)

        # 生成其他核心角色
        remaining_slots = character_config["max_core_characters"] - 1
        used_archetypes = {CharacterArchetype.HERO}

        for i in range(remaining_slots):
            # 选择合适的原型
            available_archetypes = [a for a in archetype_preferences
                                    if a not in used_archetypes]
            if not available_archetypes:
                available_archetypes = archetype_preferences

            archetype = random.choice(available_archetypes)
            used_archetypes.add(archetype)

            # 确定角色类型
            role = await self._determine_character_role(archetype, core_characters)

            character = await self._create_character(
                role=role,
                archetype=archetype,
                importance_level=8 - i,  # 重要性递减
                config=config,
                story_framework=story_framework,
                existing_characters=core_characters
            )

            core_characters.append(character)

        return core_characters

    async def _create_character(
        self, role: str, archetype: CharacterArchetype, importance_level: int,
        config: Dict[str, Any], story_framework: Dict[str, Any],
        existing_characters: List[CharacterProfile] = None
    ) -> CharacterProfile:
        """创建单个角色"""

        existing_characters = existing_characters or []

        # 生成基础信息
        enhanced_config = config.copy()
        enhanced_config["avoid_names"] = list(self.global_name_tracker)
        enhanced_config["role"] = role
        enhanced_config["archetype"] = archetype.value
        enhanced_config["importance_level"] = importance_level

        # 调用原有的角色生成逻辑
        # enhanced_config = config.copy()
        # enhanced_config["avoid_names"] = list(self.global_name_tracker)

        basic_character = await self.enhanced_generator.execute({
            "action": "character",
            "config": enhanced_config
        })
        character_base = basic_character['character']
        # 增强角色信息
        character_profile = CharacterProfile(
            name=character_base["name"],
            role=role,
            archetype=archetype,
            personality_traits=await self._generate_personality_traits(archetype, role),
            background=await self._generate_rich_background(character_base, story_framework),
            motivations=await self._generate_motivations(archetype, role, story_framework),
            goals=await self._generate_character_goals(archetype, role),
            conflicts=await self._generate_internal_conflicts(archetype, role),
            relationships={},  # 稍后填充
            character_arc={},  # 稍后填充
            dialogue_style=await self._generate_dialogue_style(archetype, character_base),
            physical_description=character_base.get("appearance", ""),
            skills_abilities=await self._generate_skills_abilities(archetype, role),
            weaknesses=await self._generate_weaknesses(archetype, role),
            secrets=await self._generate_secrets(archetype, role),
            importance_level=importance_level
        )

        # 添加到名称跟踪器
        self.global_name_tracker.add(character_profile.name)

        return character_profile

    async def _generate_personality_traits(
        self, archetype: CharacterArchetype, role: str
    ) -> List[str]:
        """生成角色性格特征"""

        archetype_traits = {
            CharacterArchetype.HERO: [
                "勇敢", "决心坚定", "富有正义感", "愿意牺牲", "有责任感"
            ],
            CharacterArchetype.MENTOR: [
                "智慧", "经验丰富", "耐心", "神秘", "保护欲强"
            ],
            CharacterArchetype.SHADOW: [
                "狡猾", "野心勃勃", "复杂", "魅力四射", "不择手段"
            ],
            CharacterArchetype.ALLY: [
                "忠诚", "可靠", "支持性", "幽默", "适应性强"
            ],
            CharacterArchetype.SHAPESHIFTER: [
                "神秘", "不可预测", "魅力四射", "复杂", "双面性"
            ]
        }

        base_traits = archetype_traits.get(archetype, ["复杂", "多面性"])

        # 添加一些随机特征增加独特性
        additional_traits = [
            "幽默感", "完美主义", "冲动", "深思熟虑", "创造力",
            "保守", "冒险精神", "同情心", "独立", "合作精神"
        ]

        selected_traits = base_traits + random.sample(additional_traits, 2)
        return selected_traits[:6]  # 限制特征数量

    async def _build_character_relationships(
        self, all_characters: List[CharacterProfile], story_framework: Dict[str, Any]
    ) -> List[CharacterRelationship]:
        """建立角色关系网络"""

        relationships = []

        for i, char1 in enumerate(all_characters):
            for j, char2 in enumerate(all_characters[i + 1:], i + 1):
                # 基于原型确定关系类型
                relationship_type, intensity, description = await self._determine_relationship(
                    char1, char2, story_framework
                )

                if relationship_type:  # 如果有关系
                    relationship = CharacterRelationship(
                        char1.name, char2.name, relationship_type, intensity, description
                    )
                    relationships.append(relationship)

                    # 更新角色的关系信息
                    char1.relationships[char2.name] = relationship_type
                    char2.relationships[char1.name] = relationship_type

        return relationships

    async def _determine_relationship(
        self, char1: CharacterProfile, char2: CharacterProfile,
        story_framework: Dict[str, Any]
    ) -> Tuple[Optional[str], int, str]:
        """确定两个角色之间的关系"""

        # 基于原型的关系矩阵
        archetype_relationships = {
            (CharacterArchetype.HERO, CharacterArchetype.MENTOR): (
            "师生关系", 8, "导师指导主角成长"),
            (CharacterArchetype.HERO, CharacterArchetype.SHADOW): ("对立关系", 9, "主要冲突对手"),
            (CharacterArchetype.HERO, CharacterArchetype.ALLY): (
            "同盟关系", 7, "忠实的伙伴和支持者"),
            (CharacterArchetype.HERO, CharacterArchetype.SHAPESHIFTER): (
            "复杂关系", 6, "亦敌亦友的复杂关系"),
            (CharacterArchetype.MENTOR, CharacterArchetype.SHADOW): (
            "对立关系", 5, "理念和方法的冲突"),
            (CharacterArchetype.ALLY, CharacterArchetype.ALLY): ("友谊关系", 6, "战友情谊"),
        }

        # 尝试正向和反向匹配
        key1 = (char1.archetype, char2.archetype)
        key2 = (char2.archetype, char1.archetype)

        if key1 in archetype_relationships:
            return archetype_relationships[key1]
        elif key2 in archetype_relationships:
            rel_type, intensity, desc = archetype_relationships[key2]
            return rel_type, intensity, desc

        # 如果没有预定义关系，根据重要性决定是否建立关系
        if char1.importance_level + char2.importance_level > 12:
            return ("普通关系", 3, "剧情中的一般互动")

        return None, 0, ""

    # 添加更多辅助方法...
    async def _generate_character_arcs(
        self, main_characters: List[CharacterProfile], chapter_count: int,
        story_framework: Dict[str, Any]
    ) -> Dict[str, Dict[str, str]]:
        """生成角色发展弧线"""

        character_arcs = {}

        for character in main_characters:
            arc_points = {
                "起点": await self._generate_arc_point("starting_point", character,
                                                       story_framework),
                "冲突点": await self._generate_arc_point("conflict_point", character,
                                                         story_framework),
                "转折点": await self._generate_arc_point("turning_point", character,
                                                         story_framework),
                "高潮": await self._generate_arc_point("climax", character, story_framework),
                "结局": await self._generate_arc_point("resolution", character, story_framework)
            }

            character_arcs[character.name] = arc_points

        return character_arcs

    async def _generate_rich_background(
        self, basic_character: Dict[str, Any], story_framework: Dict[str, Any]
    ) -> str:
        """生成丰富的角色背景"""

        config = story_framework["config"]
        setting = config.get("setting", "现代都市")
        theme = config.get("theme", "")

        background_templates = {
            "childhood": [
                "在{setting}的一个普通家庭中长大",
                "自幼失去父母，由{relative}抚养长大",
                "出生在富裕/贫困家庭，经历了{experience}",
                "童年时期经历了{trauma}，塑造了坚韧的性格"
            ],
            "education": [
                "在{institution}接受教育，主修{subject}",
                "自学成才，对{field}有独特见解",
                "师从{mentor}，掌握了{skill}"
            ],
            "career": [
                "曾经是{profession}，后来转向{new_field}",
                "一直从事{occupation}工作，积累了丰富经验",
                "年轻时就显示出{talent}天赋"
            ],
            "defining_moment": [
                "在{age}岁时经历了{event}，改变了人生轨迹",
                "目睹了{incident}，从此立志{goal}",
                "遇到了{person}，获得了人生指导"
            ]
        }

        # 随机选择背景元素
        background_parts = []
        for category, templates in background_templates.items():
            template = random.choice(templates)
            # 填充模板变量
            filled_template = await self._fill_background_template(template, basic_character,
                                                                   config)
            background_parts.append(filled_template)

        background = "。".join(background_parts) + "。"
        return background

    async def _fill_background_template(
        self, template: str, character: Dict[str, Any], config: Dict[str, Any]
    ) -> str:
        """填充背景模板中的变量"""

        # 定义替换变量
        replacements = {
            "setting": config.get("setting", "未知地方"),
            "relative": random.choice(["祖父母", "叔叔", "阿姨", "兄长", "姐姐"]),
            "experience": random.choice(["巨大的变故", "家族的兴衰", "意外的机遇", "重大的挫折"]),
            "trauma": random.choice(["家庭变故", "意外事故", "战争", "天灾", "疾病"]),
            "institution": random.choice(["知名学府", "军事学院", "艺术学校", "普通学校"]),
            "subject": random.choice(["文学", "历史", "自然科学", "艺术", "武艺", "医学"]),
            "field": random.choice(["艺术", "科学", "哲学", "武学", "商业", "政治"]),
            "mentor": random.choice(["一位智者", "神秘老人", "家族长辈", "偶遇的高人"]),
            "skill": random.choice(["独特技能", "古老知识", "特殊能力", "深刻智慧"]),
            "profession": random.choice(["商人", "学者", "军人", "艺人", "工匠", "农夫"]),
            "new_field": random.choice(["冒险", "研究", "创作", "教学", "服务"]),
            "occupation": random.choice(["学术研究", "商业贸易", "艺术创作", "社会服务"]),
            "talent": random.choice(["领导", "创造", "分析", "表演", "战斗", "治疗"]),
            "age": str(random.randint(15, 25)),
            "event": random.choice(["重大决定", "意外发现", "关键选择", "命运转折"]),
            "incident": random.choice(["不公正事件", "英勇行为", "悲剧发生", "奇迹出现"]),
            "goal": random.choice(["追求正义", "保护他人", "寻求真理", "改变世界"]),
            "person": random.choice(["智慧长者", "神秘人物", "重要朋友", "精神导师"])
        }

        # 替换模板中的变量
        result = template
        for key, value in replacements.items():
            result = result.replace(f"{{{key}}}", value)

        return result

    async def _generate_motivations(
        self, archetype: CharacterArchetype, role: str, story_framework: Dict[str, Any]
    ) -> List[str]:
        """生成角色动机"""

        theme = story_framework["config"].get("theme", "")

        archetype_motivations = {
            CharacterArchetype.HERO: [
                "保护重要的人或事物",
                "寻求真相和正义",
                "证明自己的价值",
                "实现童年的梦想",
                "为过去的错误赎罪"
            ],
            CharacterArchetype.MENTOR: [
                "传承知识和智慧",
                "保护和指导年轻一代",
                "弥补过去的遗憾",
                "完成未竟的使命",
                "维护重要的传统"
            ],
            CharacterArchetype.SHADOW: [
                "获得权力和控制",
                "报复过去的伤害",
                "证明自己的理念正确",
                "摧毁现有秩序",
                "追求完美的世界"
            ],
            CharacterArchetype.ALLY: [
                "支持朋友和盟友",
                "寻求归属感",
                "证明自己的忠诚",
                "保护共同的理想",
                "弥补过去的背叛"
            ],
            CharacterArchetype.SHAPESHIFTER: [
                "寻找真实的自我",
                "在不同身份间寻求平衡",
                "保护重要的秘密",
                "追求自由和独立",
                "探索可能性的边界"
            ]
        }

        base_motivations = archetype_motivations.get(archetype, ["寻求自我实现"])

        # 根据主题添加特定动机
        theme_motivations = {
            "爱情": ["寻找真爱", "保护爱人", "克服感情障碍"],
            "友谊": ["维护友谊", "证明忠诚", "共同成长"],
            "成长": ["自我提升", "克服弱点", "获得成熟"],
            "正义": ["维护公平", "惩罚邪恶", "保护无辜"],
            "冒险": ["探索未知", "寻求刺激", "证明勇气"]
        }

        for theme_key, theme_motivs in theme_motivations.items():
            if theme_key in theme:
                base_motivations.extend(random.sample(theme_motivs, min(2, len(theme_motivs))))

        return random.sample(base_motivations, min(4, len(base_motivations)))

    async def _generate_character_goals(
        self, archetype: CharacterArchetype, role: str
    ) -> List[str]:
        """生成角色目标"""

        archetype_goals = {
            CharacterArchetype.HERO: [
                "完成重要任务或使命",
                "拯救重要的人",
                "获得某种力量或能力",
                "揭露真相",
                "恢复失去的东西"
            ],
            CharacterArchetype.MENTOR: [
                "培养出色的继承者",
                "传授重要的知识",
                "保护古老的秘密",
                "维护重要的平衡",
                "完成最后的责任"
            ],
            CharacterArchetype.SHADOW: [
                "获得至高权力",
                "摧毁敌人",
                "实现野心计划",
                "证明自己的优越性",
                "重塑世界秩序"
            ],
            CharacterArchetype.ALLY: [
                "帮助朋友成功",
                "维护团队团结",
                "证明自己的价值",
                "保护共同利益",
                "获得认可和尊重"
            ],
            CharacterArchetype.SHAPESHIFTER: [
                "保持神秘身份",
                "平衡多重关系",
                "寻找归属",
                "探索自我边界",
                "维护微妙平衡"
            ]
        }

        goals = archetype_goals.get(archetype, ["追求个人成长"])
        return random.sample(goals, min(3, len(goals)))

    async def _generate_internal_conflicts(
        self, archetype: CharacterArchetype, role: str
    ) -> List[str]:
        """生成内在冲突"""

        common_conflicts = [
            "理想与现实的冲突",
            "个人利益与集体利益的矛盾",
            "过去与现在的纠葛",
            "恐惧与勇气的斗争",
            "爱与责任的选择"
        ]

        archetype_conflicts = {
            CharacterArchetype.HERO: [
                "自信与自卑的交替",
                "独立与依赖的矛盾",
                "完美主义与现实的冲突"
            ],
            CharacterArchetype.MENTOR: [
                "过度保护与放手的矛盾",
                "智慧与错误的反思",
                "年龄与活力的落差"
            ],
            CharacterArchetype.SHADOW: [
                "善恶本性的斗争",
                "孤独与渴望理解的冲突",
                "控制欲与真情的矛盾"
            ]
        }

        specific_conflicts = archetype_conflicts.get(archetype, [])
        all_conflicts = common_conflicts + specific_conflicts

        return random.sample(all_conflicts, min(3, len(all_conflicts)))

    async def _generate_dialogue_style(
        self, archetype: CharacterArchetype, character: Dict[str, Any]
    ) -> str:
        """生成对话风格"""

        archetype_styles = {
            CharacterArchetype.HERO: [
                "直接坦率，充满正义感",
                "热情激昂，鼓舞人心",
                "简洁有力，言出必行"
            ],
            CharacterArchetype.MENTOR: [
                "深沉智慧，富含哲理",
                "温和耐心，循循善诱",
                "简练精辟，意味深长"
            ],
            CharacterArchetype.SHADOW: [
                "犀利尖锐，充满威胁",
                "优雅冷酷，暗藏杀机",
                "讽刺挖苦，居高临下"
            ],
            CharacterArchetype.ALLY: [
                "轻松幽默，化解紧张",
                "支持鼓励，温暖人心",
                "实用直接，解决问题"
            ],
            CharacterArchetype.SHAPESHIFTER: [
                "神秘莫测，模棱两可",
                "多变灵活，适应环境",
                "暗示隐喻，意在言外"
            ]
        }

        styles = archetype_styles.get(archetype, ["平实自然，真诚可信"])
        return random.choice(styles)

    async def _generate_skills_abilities(
        self, archetype: CharacterArchetype, role: str
    ) -> List[str]:
        """生成技能能力"""

        common_skills = [
            "观察力敏锐", "记忆力出众", "学习能力强", "适应性好",
            "沟通能力佳", "分析能力强", "创造力丰富", "执行力强"
        ]

        archetype_skills = {
            CharacterArchetype.HERO: [
                "领导能力", "战斗技巧", "意志力坚强", "直觉敏锐", "激励他人"
            ],
            CharacterArchetype.MENTOR: [
                "知识渊博", "教学能力", "预见未来", "治疗能力", "精神指导"
            ],
            CharacterArchetype.SHADOW: [
                "策略规划", "操控他人", "隐藏真意", "资源整合", "权力游戏"
            ],
            CharacterArchetype.ALLY: [
                "团队合作", "后勤支援", "情报收集", "技术专长", "调解冲突"
            ],
            CharacterArchetype.SHAPESHIFTER: [
                "伪装能力", "适应环境", "信息获取", "多重身份", "平衡关系"
            ]
        }

        specific_skills = archetype_skills.get(archetype, [])
        all_skills = common_skills + specific_skills

        return random.sample(all_skills, min(5, len(all_skills)))

    async def _generate_weaknesses(
        self, archetype: CharacterArchetype, role: str
    ) -> List[str]:
        """生成角色弱点"""

        common_weaknesses = [
            "过于信任他人", "固执己见", "情绪化", "完美主义",
            "缺乏耐心", "过度自信", "害怕失败", "逃避责任"
        ]

        archetype_weaknesses = {
            CharacterArchetype.HERO: [
                "冲动鲁莽", "背负过重责任", "难以拒绝求助", "过度牺牲自我"
            ],
            CharacterArchetype.MENTOR: [
                "过度保护", "固守传统", "难以接受变化", "承担太多责任"
            ],
            CharacterArchetype.SHADOW: [
                "孤独感深重", "难以信任他人", "控制欲过强", "缺乏同理心"
            ],
            CharacterArchetype.ALLY: [
                "过于依赖他人", "缺乏主见", "害怕冲突", "自我价值感低"
            ],
            CharacterArchetype.SHAPESHIFTER: [
                "身份认同混乱", "难以建立深度关系", "缺乏一致性", "内心矛盾"
            ]
        }

        specific_weaknesses = archetype_weaknesses.get(archetype, [])
        all_weaknesses = common_weaknesses + specific_weaknesses

        return random.sample(all_weaknesses, min(3, len(all_weaknesses)))

    async def _generate_secrets(
        self, archetype: CharacterArchetype, role: str
    ) -> List[str]:
        """生成角色秘密"""

        secret_templates = [
            "隐藏的真实身份：{identity}",
            "过去的重大错误：{mistake}",
            "未公开的关系：{relationship}",
            "秘密的能力：{ability}",
            "内心的恐惧：{fear}",
            "未实现的愿望：{wish}",
            "隐瞒的事实：{fact}"
        ]

        # 为不同原型定制秘密内容
        archetype_secret_content = {
            CharacterArchetype.HERO: {
                "identity": "并非天生英雄，曾经是普通人",
                "mistake": "曾经因犹豫而失去了重要的人",
                "fear": "害怕不能保护所有人",
                "ability": "拥有尚未完全觉醒的特殊力量"
            },
            CharacterArchetype.MENTOR: {
                "identity": "曾经也是需要指导的学生",
                "mistake": "年轻时的错误判断导致了悲剧",
                "relationship": "与反派有着复杂的过去",
                "fact": "知道关于主角身世的重要秘密"
            },
            CharacterArchetype.SHADOW: {
                "identity": "与主角有着意想不到的联系",
                "mistake": "曾经是正义的一方",
                "fear": "害怕被人真正了解",
                "wish": "内心深处渴望救赎"
            }
        }

        content = archetype_secret_content.get(archetype, {
            "identity": "有着不为人知的过去",
            "mistake": "犯过重大错误",
            "fear": "有着深层恐惧",
            "ability": "拥有隐藏能力"
        })

        # 生成3个秘密
        secrets = []
        selected_templates = random.sample(secret_templates, min(3, len(secret_templates)))

        for template in selected_templates:
            # 随机选择内容填充
            for key, value in content.items():
                if f"{{{key}}}" in template:
                    secret = template.replace(f"{{{key}}}", value)
                    secrets.append(secret)
                    break

        return secrets

    async def _determine_character_role(
        self, archetype: CharacterArchetype, existing_characters: List[CharacterProfile]
    ) -> str:
        """根据原型和现有角色确定角色定位"""

        existing_roles = [char.role for char in existing_characters]

        archetype_role_mapping = {
            CharacterArchetype.MENTOR: ["导师", "智者", "长辈", "指导者"],
            CharacterArchetype.SHADOW: ["反派", "对手", "敌人", "竞争者"],
            CharacterArchetype.ALLY: ["朋友", "伙伴", "同盟", "支持者"],
            CharacterArchetype.SHAPESHIFTER: ["神秘人", "双面角色", "变化者", "中间派"],
            CharacterArchetype.THRESHOLD_GUARDIAN: ["守护者", "考验者", "阻挡者"],
            CharacterArchetype.HERALD: ["信使", "预言者", "引导者"],
            CharacterArchetype.TRICKSTER: ["小丑", "智者", "调剂者"]
        }

        possible_roles = archetype_role_mapping.get(archetype, ["配角"])

        # 选择尚未使用的角色类型
        available_roles = [role for role in possible_roles if role not in existing_roles]

        if available_roles:
            return random.choice(available_roles)
        else:
            return random.choice(possible_roles)  # 如果都被使用了，随机选择

    async def _generate_supporting_characters(
        self, character_config: Dict[str, Any], config: Dict[str, Any],
        story_framework: Dict[str, Any], main_characters: List[CharacterProfile]
    ) -> List[CharacterProfile]:
        """生成支持角色"""

        supporting_characters = []
        support_count = character_config.get("supporting_characters", 3)

        # 支持角色的原型偏好
        support_archetypes = [
            CharacterArchetype.THRESHOLD_GUARDIAN,
            CharacterArchetype.HERALD,
            CharacterArchetype.TRICKSTER,
            CharacterArchetype.ALLY
        ]

        for i in range(support_count):
            archetype = random.choice(support_archetypes)
            role = await self._determine_character_role(archetype,
                                                        main_characters + supporting_characters)

            character = await self._create_character(
                role=role,
                archetype=archetype,
                importance_level=random.randint(3, 6),  # 支持角色重要性较低
                config=config,
                story_framework=story_framework,
                existing_characters=main_characters + supporting_characters
            )

            supporting_characters.append(character)

        return supporting_characters

    async def _assign_chapter_roles(
        self, all_characters: List[CharacterProfile], chapter_count: int,
        story_framework: Dict[str, Any]
    ) -> Dict[str, Dict[int, str]]:
        """分配角色在各章节中的作用"""

        character_chapter_roles = {}

        for character in all_characters:
            chapter_roles = {}

            # 根据角色重要性分配出场章节
            if character.importance_level >= 8:  # 主要角色
                # 几乎每章都出现，但作用不同
                for chapter in range(1, chapter_count + 1):
                    if chapter <= chapter_count // 3:
                        chapter_roles[chapter] = "建立角色"
                    elif chapter <= chapter_count * 2 // 3:
                        chapter_roles[chapter] = "发展冲突"
                    else:
                        chapter_roles[chapter] = "解决冲突"

            elif character.importance_level >= 5:  # 重要配角
                # 选择性出现
                appearance_chapters = random.sample(
                    range(1, chapter_count + 1),
                    min(chapter_count // 2, chapter_count)
                )
                for chapter in appearance_chapters:
                    chapter_roles[chapter] = random.choice([
                        "推动剧情", "提供信息", "制造冲突", "协助主角"
                    ])

            else:  # 次要角色
                # 偶尔出现
                appearance_chapters = random.sample(
                    range(1, chapter_count + 1),
                    min(3, chapter_count)
                )
                for chapter in appearance_chapters:
                    chapter_roles[chapter] = "背景补充"

            character_chapter_roles[character.name] = chapter_roles

        return character_chapter_roles

    async def _generate_arc_point(
        self, arc_stage: str, character: CharacterProfile, story_framework: Dict[str, Any]
    ) -> str:
        """生成角色弧线的特定节点"""

        stage_templates = {
            "starting_point": [
                f"{character.name}最初的状态和处境",
                f"展现{character.name}的初始性格特征",
                f"{character.name}面临的初始问题或困境"
            ],
            "conflict_point": [
                f"{character.name}遭遇主要挑战",
                f"{character.name}的弱点被暴露",
                f"{character.name}面临重要选择"
            ],
            "turning_point": [
                f"{character.name}获得新的认识或能力",
                f"{character.name}做出关键决定",
                f"{character.name}经历重大变化"
            ],
            "climax": [
                f"{character.name}面对最大考验",
                f"{character.name}展现成长后的能力",
                f"{character.name}做出最重要的选择"
            ],
            "resolution": [
                f"{character.name}完成角色成长",
                f"{character.name}达成目标或获得和解",
                f"{character.name}的新状态和未来"
            ]
        }

        templates = stage_templates.get(arc_stage, [f"{character.name}在此阶段的发展"])
        return random.choice(templates)


    async def _generate_character_relationships(
        self, characters: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """生成角色关系网络"""

        logger.info("生成角色关系网络...")

        relationships = []

        # 为每对角色生成关系
        for i, char1 in enumerate(characters):
            for char2 in characters[i + 1:]:
                rel_result = await self.tool_registry.execute_tool(
                    type("ToolCall", (), {
                        "id": f"rel_{char1['name']}_{char2['name']}",
                        "name": "relationship_manager",
                        "parameters": {
                            "action": "create",
                            "character1": char1,
                            "character2": char2
                        }
                    })()
                )

                if rel_result.success:
                    relationships.append(rel_result.result["relationship"])

        return relationships

    async def _generate_character_development_arcs(
        self, characters: List[Dict[str, Any]], chapter_count: int
    ) -> Dict[str, Any]:
        """生成角色发展轨迹"""

        logger.info("生成角色发展轨迹...")

        character_arcs = {}

        for character in characters:
            arc_result = await self.tool_registry.execute_tool(
                type("ToolCall", (), {
                    "id": f"arc_{character['name']}",
                    "name": "character_development",
                    "parameters": {
                        "development_type": "both",
                        "character": character,
                        "story_length": chapter_count
                    }
                })()
            )

            if arc_result.success:
                character_arcs[character['name']] = arc_result.result

        return character_arcs

    async def _generate_detailed_chapter_planning(
        self,
        story_framework: Dict[str, Any],
        character_system: Dict[str, Any],
        chapter_count: int
    ) -> List[Dict[str, Any]]:
        """生成详细的章节规划"""

        logger.info("生成详细章节规划...")

        plot_outline = story_framework["plot_outline"]
        detailed_outline = plot_outline.get("detailed_outline", "")
        main_characters = character_system["main_characters"]
        character_arcs = character_system["character_arcs"]

        # 解析大纲中的章节信息
        chapters_info = await self._parse_detailed_outline(detailed_outline, chapter_count)

        # 为每章分配具体内容
        detailed_chapters = []

        for i in range(chapter_count):
            chapter_num = i + 1
            base_info = chapters_info[i] if i < len(chapters_info) else {}

            # 确定本章重点角色
            chapter_characters = self._assign_chapter_characters(
                chapter_num, main_characters, character_arcs, chapter_count
            )

            # 生成详细章节信息
            detailed_info = await self._generate_detailed_chapter_info(
                chapter_num, base_info, story_framework, chapter_characters, character_arcs
            )

            detailed_chapters.append(detailed_info)
            logger.info(f"✓ 规划第{chapter_num}章: {detailed_info.get('title', '')}")

        return detailed_chapters

    async def _parse_detailed_outline(
        self, detailed_outline: str, chapter_count: int
    ) -> List[Dict[str, Any]]:
        """解析详细大纲"""

        # 使用LLM解析大纲
        prompt = f"""
        请解析以下故事大纲，提取每章的具体信息：

        大纲内容：
        {detailed_outline}

        目标章节数：{chapter_count}

        请为每章提取或生成以下信息，返回JSON格式：
        [
            {{
                "number": 1,
                "title": "章节标题",
                "summary": "章节摘要",
                "key_events": ["关键事件1", "关键事件2"],
                "plot_function": "情节功能",
                "tension_level": 5,
                "mood": "氛围",
                "focus_characters": ["重点角色"],
                "scene_locations": ["主要场景"]
            }}
        ]
        """

        response = await self.llm_service.generate_text(prompt, temperature=0.5)

        try:
            import re
            json_match = re.search(r'\[.*\]', response.content, re.DOTALL)
            if json_match:
                chapters_info = json.loads(json_match.group())

                # 确保有足够的章节信息
                while len(chapters_info) < chapter_count:
                    chapter_num = len(chapters_info) + 1
                    chapters_info.append({
                        "number": chapter_num,
                        "title": f"第{chapter_num}章",
                        "summary": f"第{chapter_num}章的内容",
                        "key_events": [f"第{chapter_num}章事件"],
                        "plot_function": "推进情节",
                        "tension_level": 5,
                        "mood": "中性",
                        "focus_characters": ["主角"],
                        "scene_locations": ["场景"]
                    })

                return chapters_info[:chapter_count]

        except Exception as e:
            logger.warning(f"解析大纲失败: {e}")

        # 返回默认章节信息
        return [
            {
                "number": i + 1,
                "title": f"第{i + 1}章",
                "summary": f"第{i + 1}章的内容",
                "key_events": [f"第{i + 1}章事件"],
                "plot_function": "推进情节",
                "tension_level": 5,
                "mood": "中性",
                "focus_characters": ["主角"],
                "scene_locations": ["场景"]
            }
            for i in range(chapter_count)
        ]

    def _assign_chapter_characters(
        self,
        chapter_num: int,
        main_characters: List[Dict[str, Any]],
        character_arcs: Dict[str, Any],
        total_chapters: int
    ) -> List[Dict[str, Any]]:
        """为章节分配角色"""

        # 根据故事进度分配角色
        progress = chapter_num / total_chapters

        assigned_characters = []

        # 主角几乎出现在所有章节
        protagonist = next((char for char in main_characters if char["role_type"] == "protagonist"),
                           None)
        if protagonist:
            assigned_characters.append(protagonist)

        # 根据进度分配其他角色
        for character in main_characters:
            if character["role_type"] == "protagonist":
                continue

            # 根据角色类型和故事进度决定是否出现
            should_appear = False

            if character["role_type"] == "mentor" and progress < 0.5:
                should_appear = True
            elif character["role_type"] == "antagonist" and progress > 0.3:
                should_appear = True
            elif character["role_type"] == "love_interest" and 0.2 < progress < 0.9:
                should_appear = True
            elif character["role_type"] == "deuteragonist":
                should_appear = True

            if should_appear:
                assigned_characters.append(character)

        return assigned_characters

    async def _generate_detailed_chapter_info(
        self,
        chapter_num: int,
        base_info: Dict[str, Any],
        story_framework: Dict[str, Any],
        chapter_characters: List[Dict[str, Any]],
        character_arcs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成详细的章节信息"""

        # 获取角色在本章的发展
        character_developments = {}
        for char in chapter_characters:
            char_name = char["name"]
            if char_name in character_arcs:
                arc_info = character_arcs[char_name]
                # 简化处理：假设角色发展均匀分布
                character_developments[char_name] = f"{char_name}在第{chapter_num}章的发展"

        # 生成场景规划
        scenes = await self._generate_chapter_scenes(
            chapter_num, base_info, chapter_characters, story_framework
        )

        detailed_info = {
            "number": chapter_num,
            "title": base_info.get("title", f"第{chapter_num}章"),
            "summary": base_info.get("summary", f"第{chapter_num}章的内容"),
            "detailed_summary": base_info.get("summary", f"第{chapter_num}章的详细内容"),
            "key_events": base_info.get("key_events", [f"第{chapter_num}章事件"]),
            "character_focus": [char["name"] for char in chapter_characters],
            "character_developments": character_developments,
            "plot_advancement": base_info.get("plot_function", "推进情节"),
            "tension_level": base_info.get("tension_level", 5),
            "mood": base_info.get("mood", "中性"),
            "pacing": "medium",
            "scenes": scenes,
            "core_conflict": base_info.get("core_conflict", "本章主要矛盾"),
            "foreshadowing": [],
            "chapter_ending": "为下章做铺垫"
        }

        return detailed_info

    async def _generate_chapter_scenes(
        self,
        chapter_num: int,
        base_info: Dict[str, Any],
        chapter_characters: List[Dict[str, Any]],
        story_framework: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """生成章节场景"""

        # 生成3-4个场景
        scene_count = 3 if chapter_num <= 3 or chapter_num >= 18 else 4
        scenes = []

        scene_purposes = ["开场", "发展", "转折", "收尾"]

        for i in range(scene_count):
            scene = {
                "scene_number": i + 1,
                "purpose": scene_purposes[i % len(scene_purposes)],
                "location": base_info.get("scene_locations", ["场景"])[0] if base_info.get(
                    "scene_locations") else "场景地点",
                "characters": [char["name"] for char in chapter_characters[:2]],  # 每场景最多2个主要角色
                "events": [f"场景{i + 1}的事件"],
                "mood": base_info.get("mood", "中性"),
                "word_count_target": 800
            }
            scenes.append(scene)

        return scenes

    async def _generate_quality_chapters(
        self,
        detailed_chapters: List[Dict[str, Any]],
        story_framework: Dict[str, Any],
        character_system: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """生成高质量章节内容"""

        logger.info("生成高质量章节内容...")

        final_chapters = []
        story_context = {
            "world_setting": {"name": story_framework["variant"]["world_flavor"]},
            "characters": character_system["main_characters"],
            "story_outline": story_framework["plot_outline"],
            "title": story_framework["title"]
        }

        for i, chapter_info in enumerate(detailed_chapters):
            logger.info(f"  生成第{chapter_info['number']}章...")

            # 更新故事上下文
            current_context = story_context.copy()
            current_context["previous_chapters"] = final_chapters
            current_context["chapter_progress"] = (i + 1) / len(detailed_chapters)

            # 生成章节内容
            chapter_result = await self.tool_registry.execute_tool(
                type("ToolCall", (), {
                    "id": f"chapter_{chapter_info['number']}",
                    "name": "chapter_writer",
                    "parameters": {
                        "chapter_info": chapter_info,
                        "story_context": current_context,
                        "writing_style": "traditional",
                        "target_word_count": 3000
                    }
                })()
            )

            if chapter_result.success:
                chapter_data = chapter_result.result["chapter"]

                # 质量检查
                quality_score = self._assess_chapter_quality(chapter_data)

                # 如果质量不足，尝试重新生成
                if quality_score < 0.6:
                    logger.warning(f"第{chapter_info['number']}章质量不足，重新生成...")
                    chapter_result = await self._regenerate_chapter_with_improvements(
                        chapter_info, current_context, chapter_data
                    )
                    if chapter_result:
                        chapter_data = chapter_result

                final_chapters.append(chapter_data)
                logger.info(
                    f"第{chapter_info['number']}章生成完成 \n:{json.dumps(chapter_data, ensure_ascii=False, indent=2)}")
                logger.info(
                    f"  ✓ 第{chapter_info['number']}章生成完成 ({chapter_data['total_word_count']}字)")


            else:
                logger.error(f"  ✗ 第{chapter_info['number']}章生成失败: {chapter_result.error}")
                # 创建占位符章节
                placeholder = self._create_placeholder_chapter(chapter_info)
                final_chapters.append(placeholder)

        return final_chapters

    def _assess_chapter_quality(self, chapter_data: Dict[str, Any]) -> float:
        """评估章节质量"""

        score = 0.0

        # 字数检查
        word_count = chapter_data.get("total_word_count", 0)
        if 2000 <= word_count <= 5000:
            score += 0.3
        elif word_count > 1000:
            score += 0.1

        # 对话比例检查
        dialogue_ratio = chapter_data.get("dialogue_ratio", 0)
        if 0.2 <= dialogue_ratio <= 0.5:
            score += 0.2

        # 描述比例检查
        description_ratio = chapter_data.get("description_ratio", 0)
        if 0.3 <= description_ratio <= 0.6:
            score += 0.2

        # 场景数量检查
        scenes = chapter_data.get("scenes", [])
        if 3 <= len(scenes) <= 5:
            score += 0.3

        return score

    async def _regenerate_chapter_with_improvements(
        self,
        chapter_info: Dict[str, Any],
        story_context: Dict[str, Any],
        failed_chapter: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """重新生成并改进章节"""

        # 分析失败原因并改进提示
        improved_chapter_info = chapter_info.copy()
        improved_chapter_info["improvement_notes"] = "增强对话和描写，确保场景丰富"

        chapter_result = await self.tool_registry.execute_tool(
            type("ToolCall", (), {
                "id": f"chapter_retry_{chapter_info['number']}",
                "name": "chapter_writer",
                "parameters": {
                    "chapter_info": improved_chapter_info,
                    "story_context": story_context,
                    "writing_style": "traditional",
                    "target_word_count": 3500  # 增加目标字数
                }
            })()
        )

        if chapter_result.success:
            return chapter_result.result["chapter"]

        return None

    def _create_placeholder_chapter(self, chapter_info: Dict[str, Any]) -> Dict[str, Any]:
        """创建占位符章节"""

        return {
            "chapter_number": chapter_info['number'],
            "title": chapter_info['title'],
            "summary": chapter_info['summary'],
            "scenes": [{
                "content": f"第{chapter_info['number']}章内容生成失败，需要重新生成。\n\n章节摘要：{chapter_info['summary']}"
            }],
            "total_word_count": 100,
            "key_events": chapter_info.get('key_events', []),
            "character_focus": chapter_info.get('character_focus', []),
            "plot_advancement": chapter_info.get('plot_advancement', ''),
            "emotional_arc": "需要重新生成",
            "dialogue_ratio": 0.0,
            "description_ratio": 0.0,
            "action_ratio": 0.0,
            "previous_chapter_connection": "",
            "next_chapter_setup": ""
        }

    async def _validate_and_fix_consistency(
        self,
        chapters: List[Dict[str, Any]],
        story_framework: Dict[str, Any],
        character_system: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """验证和修复一致性"""

        logger.info("进行一致性检查...")

        # 构建检查数据
        story_data = {
            "characters": character_system["main_characters"],
            "world_setting": {"name": story_framework["variant"]["world_flavor"]},
            "story_outline": story_framework["plot_outline"],
            "chapters": chapters
        }

        # 执行一致性检查
        consistency_result = await self.tool_registry.execute_tool(
            type("ToolCall", (), {
                "id": "consistency_check",
                "name": "consistency_checker",
                "parameters": {
                    "check_type": "full",
                    "story_data": story_data
                }
            })()
        )

        if consistency_result.success:
            report = consistency_result.result["consistency_report"]
            score = report.get("overall_score", 0)
            issues = report.get("issues", [])

            logger.info(f"一致性得分: {score:.1f}/100")

            if issues:
                logger.warning(f"发现 {len(issues)} 个一致性问题")
                for issue in issues[:3]:  # 只显示前3个
                    logger.warning(f"  - {issue.get('description', '未知问题')}")

            # 如果分数太低，记录问题但不中断生成
            if score < 60:
                logger.warning("一致性得分较低，建议检查生成内容")

        return chapters

    async def _assemble_complete_novel(
        self,
        title: str,
        genre: str,
        theme: str,
        story_framework: Dict[str, Any],
        character_system: Dict[str, Any],
        chapters: List[Dict[str, Any]],
        randomization_level: float
    ) -> Dict[str, Any]:
        """组装完整小说"""

        diversity_info = story_framework["config"]["variant"]

        novel_data = {
            "title": title,
            "genre": genre,
            "theme": theme,
            "enhanced": True,
            "diversity_info": {
                "variant_id": diversity_info["variant_id"],
                "story_structure": diversity_info["story_structure"],
                "character_archetype": diversity_info["character_archetype"],
                "world_flavor": diversity_info["world_flavor"],
                "innovation_factors": story_framework["config"]["innovation_factors"],
                "randomization_level": randomization_level
            },
            "characters": character_system["main_characters"],
            "character_relationships": character_system["relationships"],
            "character_arcs": character_system["character_arcs"],
            "plot_outline": story_framework["plot_outline"],
            "chapters": chapters,
            "total_word_count": sum(ch.get("total_word_count", 0) for ch in chapters),
            "generation_info": {
                "generated_at": str(asyncio.get_event_loop().time()),
                "chapter_count": len(chapters),
                "character_count": character_system["character_count"],
                "enhancement_used": True,
                "quality_checked": True
            },
            "quality_metrics": {
                "avg_chapter_length": sum(ch.get("total_word_count", 0) for ch in chapters) / len(
                    chapters) if chapters else 0,
                "dialogue_ratio": sum(ch.get("dialogue_ratio", 0) for ch in chapters) / len(
                    chapters) if chapters else 0,
                "description_ratio": sum(ch.get("description_ratio", 0) for ch in chapters) / len(
                    chapters) if chapters else 0
            }
        }

        return novel_data

    async def _generate_fallback_novel(
        self, title: str, genre: str, chapter_count: int, theme: str
    ) -> Dict[str, Any]:
        """生成备用小说（标准模式）"""
        # 这里可以调用原有的标准生成方法
        # 为简化，返回基本结构
        return {
            "title": title,
            "genre": genre,
            "theme": theme,
            "enhanced": False,
            "chapters": [],
            "total_word_count": 0,
            "generation_info": {
                "generated_at": str(asyncio.get_event_loop().time()),
                "fallback_used": True
            }
        }

    async def _save_novel_improved(self, novel_data: Dict[str, Any]):
        """改进版小说保存"""

        output_dir = self.settings.generated_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        title = novel_data["title"]
        safe_title = "".join(c for c in title if c.isalnum() or c in "._- ")

        # 保存JSON格式的完整数据
        suffix = "_enhanced_v2" if novel_data.get("enhanced") else "_standard"
        json_file = output_dir / f"{safe_title}{suffix}_complete.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(novel_data, f, ensure_ascii=False, indent=2)

        # 保存TXT格式的小说正文
        txt_file = output_dir / f"{safe_title}{suffix}.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            # 写入小说信息
            f.write(f"《{novel_data['title']}》\n")
            f.write(f"类型：{novel_data['genre']}\n")
            f.write(f"主题：{novel_data['theme']}\n")
            f.write(f"总字数：{novel_data['total_word_count']}\n")
            f.write(f"章节数：{len(novel_data['chapters'])}\n")

            # 增强版额外信息
            if novel_data.get("enhanced"):
                diversity_info = novel_data.get("diversity_info", {})
                f.write(f"生成模式：增强版 v2.0\n")
                f.write(f"故事结构：{diversity_info.get('story_structure', '未知')}\n")
                f.write(f"角色原型：{diversity_info.get('character_archetype', '未知')}\n")
                f.write(f"世界风味：{diversity_info.get('world_flavor', '未知')}\n")
                f.write(f"创新程度：{diversity_info.get('randomization_level', 0)}\n")

                # 质量指标
                quality_metrics = novel_data.get("quality_metrics", {})
                f.write(f"平均章节长度：{quality_metrics.get('avg_chapter_length', 0):.0f}字\n")
                f.write(f"对话比例：{quality_metrics.get('dialogue_ratio', 0):.1%}\n")
                f.write(f"描述比例：{quality_metrics.get('description_ratio', 0):.1%}\n")

            f.write("=" * 50 + "\n\n")

            # 角色介绍
            f.write("主要角色：\n")
            for character in novel_data.get("characters", []):
                f.write(
                    f"  {character.get('name', '未知')} - {character.get('role_name', '角色')}\n")
            f.write("\n")

            # 章节内容
            for chapter in novel_data["chapters"]:
                f.write(f"第{chapter.get('chapter_number', 0)}章 {chapter.get('title', '')}\n")
                f.write("-" * 30 + "\n")

                # 处理不同的章节结构
                if "scenes" in chapter and chapter["scenes"]:
                    for scene in chapter["scenes"]:
                        content = scene.get("content", "")
                        if content:
                            content = re.sub(r'场景\s*\d+\s*：', '', content)
                            f.write(content)
                            f.write("\n\n")
                elif "content" in chapter:
                    f.write(chapter["content"])
                    f.write("\n\n")
                else:
                    f.write("章节内容生成失败\n\n")

                f.write("\n")

        logger.info(f"小说已保存到：{txt_file}")

    async def _check_diversity_status(self) -> Dict[str, Any]:
        """检查当前生成内容的多样性状况"""
        try:
            analysis_result = await self.diversity_tool.execute({
                "action": "analyze_diversity",
                "recent_count": 10
            })

            diversity_analysis = analysis_result.get("diversity_analysis", {})

            return {
                "diversity_score": diversity_analysis.get("diversity_score", 1.0),
                "recent_count": diversity_analysis.get("recent_count", 0),
                "recommendations": diversity_analysis.get("recommendations", [])
            }
        except Exception as e:
            logger.warning(f"多样性检查失败: {e}")
            return {"diversity_score": 1.0, "recent_count": 0, "recommendations": []}

    async def generate_characters_only(self, story_framework, chapter_count):
        # 生成基础配置
        config_result = await self.enhanced_generator.execute({
            "action": "config",
            "base_theme": "玄幻",
            "randomization_level": 0.8,
            "avoid_recent": True
        })

        config = config_result["config"]
        story_framework = {'config':config}
        character_system = await self._generate_rich_character_system(
            story_framework, chapter_count
        )
        return character_system


# 示例用法
async def test_improved_generation():
    """测试改进版生成"""
    generator = EnhancedNovelGenerator()

    result = await generator.generate_novel_enhanced_improved(
        title="刀剑无影追天道",
        genre="玄幻",
        chapter_count=4,
        theme="修仙",
        randomization_level=0.8,
        force_diversity=True
    )
    # result = await generator.generate_characters_only("爱情动作玄幻",5,)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    print(f"生成完成：{result['title']}")
    print(f"总字数：{result['total_word_count']}")
    print(f"角色数：{len(result['characters'])}")
    print(f"增强模式：{result.get('enhanced', False)}")


if __name__ == "__main__":
    asyncio.run(test_improved_generation())
