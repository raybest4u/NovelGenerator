# modules/generation/enhanced_story_generator.py
"""
增强版故事生成器
整合多样性增强功能，确保每次生成都有显著差异
"""

import random
import json
import re
import time
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, asdict

from loguru import logger

from core.base_tools import AsyncTool, ToolDefinition, ToolParameter, method_cache
from core.llm_client import get_llm_service
from config.settings import get_prompt_manager
from modules.character import CharacterCreator, CharacterCreatorTool
from modules.generation.diversity_enhancer import DiversityEnhancer, GenerationVariant


@dataclass
class EnhancedStoryConfig:
    """增强的故事配置"""
    base_theme: str  # 基础主题
    variant: GenerationVariant  # 多样性变体
    randomization_level: float  # 随机化程度 0-1
    innovation_factors: List[str]  # 创新因子
    constraint_adherence: float  # 约束遵循度 0-1


class EnhancedStoryGenerator:
    """增强版故事生成器"""

    def __init__(self):
        self.llm_service = get_llm_service()
        self.prompt_manager = get_prompt_manager()
        self.diversity_enhancer = DiversityEnhancer()

        # 创新技法库
        self.narrative_techniques = self._load_narrative_techniques()
        self.character_innovations = self._load_character_innovations()
        self.plot_twists = self._load_plot_twists()
        self.world_building_innovations = self._load_world_innovations()

        # 添加名称管理
        self.used_names: Set[str] = set()
        self.name_patterns = self._load_name_patterns()

        # 集成角色创建器
        self.character_creator = CharacterCreator()
        self.character_creator_tool = CharacterCreatorTool()

    def _load_name_patterns(self) -> Dict[str, List[str]]:
        """加载名称模式"""
        return {
            "prefix_modifiers": ["风", "云", "雷", "火", "冰", "雪", "星", "月"],
            "suffix_modifiers": ["轩", "宇", "辰", "阳", "煜", "瑜", "琛", "璟"]
        }

    def _load_narrative_techniques(self) -> Dict[str, Dict[str, Any]]:
        """加载叙述技法"""
        return {
            "非线性叙述": {
                "description": "打乱时间顺序，通过闪回、预告等手法讲述故事",
                "implementation": ["倒叙开场", "交叉剪辑", "时间跳跃", "记忆碎片"],
                "effect": "增强悬疑感和阅读体验"
            },
            "多重视角": {
                "description": "从不同角色的视角讲述同一个故事",
                "implementation": ["角色轮换", "观点冲突", "信息互补", "真相拼图"],
                "effect": "丰富故事层次和人物塑造"
            },
            "元叙事": {
                "description": "故事中的故事，突破第四面墙",
                "implementation": ["书中书", "戏中戏", "角色自省", "作者介入"],
                "effect": "增加故事的哲学深度"
            },
            "意识流": {
                "description": "直接展现角色的内心世界和思维过程",
                "implementation": ["内心独白", "联想跳跃", "感觉描写", "潜意识表达"],
                "effect": "深入人物内心，增强共鸣"
            },
            "寓言化": {
                "description": "用象征和隐喻表达深层主题",
                "implementation": ["象征符号", "隐喻结构", "寓意情节", "哲理对话"],
                "effect": "提升作品的思想高度"
            }
        }

    def _load_character_innovations(self) -> Dict[str, List[str]]:
        """加载角色创新要素"""
        return {
            "身份设定": [
                "双重人格", "失忆者", "预言者", "时间旅行者",
                "灵魂互换", "虚拟存在", "概念化身", "命运编织者"
            ],
            "能力体系": [
                "情感操控", "概率改写", "记忆编辑", "时间暂停",
                "维度穿越", "因果逆转", "真实扭曲", "意识分离"
            ],
            "成长轨迹": [
                "逆向成长", "循环重置", "分身发展", "融合进化",
                "维度提升", "概念超越", "存在升华", "意识觉醒"
            ],
            "关系动态": [
                "敌友转换", "师徒颠倒", "时空错位", "身份互换",
                "记忆共享", "命运绑定", "灵魂共鸣", "意识融合"
            ]
        }

    def _load_plot_twists(self) -> Dict[str, Dict[str, Any]]:
        """加载情节转折"""
        return {
            "身份揭秘": {
                "types": ["真实身份", "隐藏关系", "伪装暴露", "血缘之谜"],
                "timing": ["开篇", "中段", "高潮", "结尾"],
                "impact": ["震惊", "恍然", "愤怒", "感动"]
            },
            "真相反转": {
                "types": ["善恶颠倒", "动机误判", "事实错觉", "记忆造假"],
                "timing": ["铺垫后", "冲突中", "揭示时", "回顾时"],
                "impact": ["困惑", "醒悟", "重新审视", "价值重塑"]
            },
            "时空扭曲": {
                "types": ["时间循环", "平行世界", "梦境现实", "虚拟真实"],
                "timing": ["关键节点", "转折处", "高潮时", "收尾前"],
                "impact": ["颠覆认知", "重新定位", "存在质疑", "哲学思考"]
            },
            "能力觉醒": {
                "types": ["潜能爆发", "血脉觉醒", "器物认主", "天赋显现"],
                "timing": ["绝境时", "感悟后", "传承中", "突破后"],
                "impact": ["力量提升", "自信增强", "责任加重", "使命明确"]
            }
        }

    def _load_world_innovations(self) -> Dict[str, List[str]]:
        """加载世界构建创新"""
        return {
            "物理法则": [
                "重力可控", "时间流速不同", "空间折叠", "维度重叠",
                "意识物质化", "情感能量", "记忆具象", "梦境现实"
            ],
            "社会结构": [
                "记忆等级制", "情感货币", "思想共享", "意识民主",
                "能力分工", "时间分配", "空间所有权", "虚拟身份"
            ],
            "文明形态": [
                "思维文明", "能量文明", "信息文明", "维度文明",
                "概念文明", "意识文明", "时间文明", "因果文明"
            ],
            "冲突机制": [
                "思想战争", "记忆争夺", "时间竞赛", "维度侵袭",
                "概念污染", "意识病毒", "因果破坏", "现实扭曲"
            ]
        }

    async def generate_enhanced_story_config(
        self,
        base_theme: str,
        randomization_level: float = 0.8,
        avoid_recent: bool = True
    ) -> EnhancedStoryConfig:
        """生成增强的故事配置"""

        # 获取避免约束
        constraints = None
        if avoid_recent:
            constraints = self.diversity_enhancer.get_avoidance_constraints(recent_count=5)

        # 生成多样性变体
        variant = await self.diversity_enhancer.generate_diverse_variant(base_theme, constraints)

        # 选择创新因子
        innovation_factors = self._select_innovation_factors(randomization_level)

        return EnhancedStoryConfig(
            base_theme=base_theme,
            variant=variant,
            randomization_level=randomization_level,
            innovation_factors=innovation_factors,
            constraint_adherence=0.7 + randomization_level * 0.3
        )

    def _select_innovation_factors(self, randomization_level: float) -> List[str]:
        """选择创新因子"""
        base_count = int(2 + randomization_level * 4)  # 2-6个因子

        all_factors = []

        # 从各个创新库中选择
        all_factors.extend(random.sample(list(self.narrative_techniques.keys()),
                                         min(2, len(self.narrative_techniques))))

        char_innovations = []
        for category, items in self.character_innovations.items():
            char_innovations.extend(random.sample(items, min(1, len(items))))
        all_factors.extend(random.sample(char_innovations, min(2, len(char_innovations))))

        world_innovations = []
        for category, items in self.world_building_innovations.items():
            world_innovations.extend(random.sample(items, min(1, len(items))))
        all_factors.extend(random.sample(world_innovations, min(2, len(world_innovations))))

        # 随机选择最终的因子
        return random.sample(all_factors, min(base_count, len(all_factors)))

    async def generate_enhanced_character(
        self,
        config: EnhancedStoryConfig,
        character_role: str = "protagonist"
    ) -> Dict[str, Any]:
        """生成增强的角色 - 集成 CharacterCreator"""

        logger.info(f"开始生成增强角色: {character_role}")

        # 映射角色类型
        character_type_mapping = {
            "protagonist": "主角",
            "antagonist": "反派",
            "supporting": "重要配角",
            "mentor": "导师",
            "love_interest": "爱情线角色",
            "comic_relief": "搞笑角色"
        }

        character_type = character_type_mapping.get(character_role, "主角")

        # 构建世界设定信息
        world_setting = {
            "genre": config.base_theme,
            "world_type": config.variant.world_flavor,
            "story_structure": config.variant.story_structure,
            "tone": config.variant.tone,
            "unique_elements": config.variant.unique_elements,
            "conflict_type": config.variant.conflict_type
        }

        # 获取原型信息
        archetype_info = self.diversity_enhancer.character_archetypes.get(
            config.variant.character_archetype, {}
        )

        # 应用创新因子
        innovations = [factor for factor in config.innovation_factors
                       if factor in sum(self.character_innovations.values(), [])]

        # 构建特殊要求
        requirements = {
            "character_archetype": config.variant.character_archetype,
            "archetype_info": archetype_info,
            "innovation_elements": innovations,
            "conflict_type": config.variant.conflict_type,
            "randomization_level": config.randomization_level,
            "avoid_names": list(self.used_names),
            "enhanced_mode": True,
            "narrative_techniques": [f for f in config.innovation_factors
                                     if f in self.narrative_techniques],
            "world_innovations": [f for f in config.innovation_factors
                                  if f in sum(self.world_building_innovations.values(), [])]
        }

        logger.info(f"角色创建参数: character_type={character_type}, requirements={requirements}")

        try:
            # 调用 CharacterCreatorTool 创建完整角色
            result = await self.character_creator_tool.execute({
                "character_type": character_type,
                "genre": config.base_theme,
                "world_setting": world_setting,
                "requirements": requirements
            })

            character = result["character"]

            # 记录使用的名称
            self.used_names.add(character["name"])
            if character.get("nickname"):
                self.used_names.add(character["nickname"])

            # 添加增强信息
            character.update({
                "role": character_role,
                "archetype": config.variant.character_archetype,
                "innovation_elements": innovations,
                "world_context": config.variant.world_flavor,
                "enhanced_generation": True,
                "config_variant_id": config.variant.variant_id,
                "generation_timestamp": int(time.time())
            })

            logger.info(f"成功生成增强角色: {character['name']}")
            return character

        except Exception as e:
            logger.error(f"角色生成失败: {e}")

            # 备用方案：使用简化生成
            return await self.generate_llm_character(
                config, character_role
            )

    async def generate_llm_character(
        self,
        config: EnhancedStoryConfig,
        character_role: str = "protagonist"
    ) -> Dict[str, Any]:
        """生成增强的角色"""

        # 基础角色信息
        archetype_info = self.diversity_enhancer.character_archetypes[
            config.variant.character_archetype]

        # 应用创新因子
        innovations = [factor for factor in config.innovation_factors
                       if factor in sum(self.character_innovations.values(), [])]

        # 生成独特名称
        character_name = await self._generate_unique_character_name(
            config, character_role, innovations
        )

        # 生成详细角色信息
        character_prompt = f"""
        基于以下信息创造一个独特的角色：

        角色名称：{character_name}
        角色类型：{character_role}
        原型特征：{archetype_info}
        世界背景：{config.variant.world_flavor}
        故事主题：{config.base_theme}
        创新元素：{innovations}
        独特要素：{config.variant.unique_elements}

        请生成详细的角色信息，包括：
        1. 外貌特征（独特而有辨识度）
        2. 性格特质（复杂而立体）
        3. 背景故事（与众不同的经历）
        4. 能力体系（创新的力量设定）
        5. 内心动机（深层的驱动力）
        6. 人际关系（特殊的连接方式）
        7. 成长目标（独特的发展方向）

        要求角色设定要新颖、避免俗套，充分体现创新元素。
        """

        character_response = await self.llm_service.generate_text(character_prompt, temperature=0.8)

        return {
            "name": character_name,
            "role": character_role,
            "archetype": config.variant.character_archetype,
            "detailed_info": character_response.content,
            "innovation_elements": innovations,
            "world_context": config.variant.world_flavor
        }

    async def _generate_unique_character_name(
        self,
        config: EnhancedStoryConfig,
        character_role: str,
        innovations: List[str]
    ) -> str:
        """生成独特的角色名称"""

        max_attempts = 8

        for attempt in range(max_attempts):
            # 构建更具变化性的提示词
            variant_hints = [
                f"融合{config.variant.world_flavor}特色",
                f"体现{config.variant.character_archetype}精神",
                f"展现{innovations[0] if innovations else '独特'}特质",
                f"彰显角色的{character_role}身份"
            ]

            hint = variant_hints[attempt % len(variant_hints)]

            name_prompt = f"""
            为{config.variant.world_flavor}世界的{config.variant.character_archetype}角色创造独特名字：

            角色身份：{character_role}
            创意方向：{hint}
            创新元素：{innovations[:2] if innovations else []}
            时间戳：{int(time.time() * 1000) % 10000}
            尝试序号：{attempt + 1}

            严格要求：
            1. 绝对不能使用：{list(self.used_names)}
            2. 必须原创，避免网文常见名
            3. 体现{config.variant.character_archetype}特质
            4. 符合{config.variant.world_flavor}风格
            5. 音韵优美，有文化内涵

            只返回一个名字：
            """

            response = await self.llm_service.generate_text(
                name_prompt,
                temperature=0.8 + (attempt * 0.02),  # 递增随机性
                max_tokens=20
            )

            name = self._clean_name(response.content)

            if name and name not in self.used_names and len(name) >= 2:
                self.used_names.add(name)
                return name

        # 备用方案：组合生成
        return self._generate_composite_name(config, character_role)

    def _clean_name(self, raw_name: str) -> str:
        """清理名称"""
        cleaned = raw_name.strip()
        cleaned = re.sub(r'["""''`()（）【】\[\]<>《》：:]', '', cleaned)
        cleaned = re.sub(r'[，。！？；,!?;].*', '', cleaned)

        words = cleaned.split()
        if words:
            name = words[0]
            if 2 <= len(name) <= 5 and all('\u4e00' <= c <= '\u9fff' for c in name):
                return name
        return ""

    def _generate_composite_name(self, config: EnhancedStoryConfig, role: str) -> str:
        """组合生成名称"""
        surnames = ["慕容", "欧阳", "司徒", "独孤", "李", "王", "赵", "林"]
        prefixes = self.name_patterns["prefix_modifiers"]
        suffixes = self.name_patterns["suffix_modifiers"]

        surname = random.choice(surnames)
        given = random.choice(prefixes) + random.choice(suffixes)

        composite_name = surname + given

        # 确保唯一性
        counter = 1
        original_name = composite_name
        while composite_name in self.used_names:
            composite_name = f"{original_name}{counter}"
            counter += 1

        self.used_names.add(composite_name)
        return composite_name


    async def generate_enhanced_plot_outline(
        self,
        config: EnhancedStoryConfig,
        chapter_count: int = 20
    ) -> Dict[str, Any]:
        """生成增强的情节大纲"""

        structure_info = self.diversity_enhancer.story_structures[config.variant.story_structure]

        # 选择适用的转折技巧
        applicable_twists = self._select_plot_twists(config.randomization_level)

        # 选择叙述技法
        narrative_technique = random.choice([t for t in config.innovation_factors
                                             if t in self.narrative_techniques])

        outline_prompt = f"""
        基于以下创新设定创造一个独特的故事大纲：

        故事配置：
        - 主题：{config.base_theme}
        - 结构：{config.variant.story_structure} - {structure_info}
        - 角色原型：{config.variant.character_archetype}
        - 世界风味：{config.variant.world_flavor}
        - 主要冲突：{config.variant.conflict_type}
        - 独特元素：{config.variant.unique_elements}

        创新技法：
        - 叙述方式：{narrative_technique} - {self.narrative_techniques.get(narrative_technique, {})}
        - 情节转折：{applicable_twists}
        - 创新因子：{config.innovation_factors}

        章节数量：{chapter_count}

        请创造一个{chapter_count}章的详细大纲，要求：
        1. 严格按照{config.variant.story_structure}结构展开
        2. 巧妙融入所有创新元素
        3. 在关键节点安排情节转折
        4. 运用{narrative_technique}的叙述技法
        5. 确保每章都有明确目标和独特看点
        6. 避免常见俗套情节

        请按章节序号列出大纲，每章包含：
        - 章节标题
        - 主要事件
        - 角色发展
        - 创新展现
        - 情感基调
        """

        outline_response = await self.llm_service.generate_text(outline_prompt, temperature=0.8)

        return {
            "story_structure": config.variant.story_structure,
            "narrative_technique": narrative_technique,
            "plot_twists": applicable_twists,
            "chapter_count": chapter_count,
            "detailed_outline": outline_response.content,
            "innovation_integration": config.innovation_factors
        }

    def _select_plot_twists(self, randomization_level: float) -> List[Dict[str, Any]]:
        """选择情节转折"""
        twist_count = int(1 + randomization_level * 3)  # 1-4个转折

        selected_twists = []
        for _ in range(twist_count):
            twist_type = random.choice(list(self.plot_twists.keys()))
            twist_info = self.plot_twists[twist_type]

            selected_twists.append({
                "type": twist_type,
                "variation": random.choice(twist_info["types"]),
                "timing": random.choice(twist_info["timing"]),
                "expected_impact": random.choice(twist_info["impact"])
            })

        return selected_twists

    async def generate_enhanced_chapter(
        self,
        config: EnhancedStoryConfig,
        chapter_info: Dict[str, Any],
        characters: List[Dict[str, Any]],
        plot_outline: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成增强的章节内容"""

        chapter_number = chapter_info.get("number", 1)
        chapter_title = chapter_info.get("title", f"第{chapter_number}章")

        # 确定本章的创新展现
        chapter_innovations = random.sample(config.innovation_factors,
                                            min(2, len(config.innovation_factors)))

        # 确定叙述技法的具体应用
        narrative_technique = plot_outline.get("narrative_technique")
        technique_application = self._get_technique_application(narrative_technique, chapter_number)

        chapter_prompt = f"""
        写作小说第{chapter_number}章：{chapter_title}

        故事背景：
        - 主题：{config.base_theme}
        - 世界：{config.variant.world_flavor}
        - 基调：{config.variant.tone}
        - 冲突：{config.variant.conflict_type}

        角色信息：
        {json.dumps([char.get("name", "未知") + ": " + char.get("role", "") for char in characters], ensure_ascii=False)}

        情节大纲：{chapter_info.get("plot_summary", "")}

        创新要求：
        - 本章重点展现：{chapter_innovations}
        - 叙述技法：{narrative_technique}
        - 技法应用：{technique_application}
        - 独特元素融入：{random.choice(config.variant.unique_elements)}

        写作要求：
        1. 字数：3000-4000字
        2. 严格按照情节大纲发展
        3. 巧妙融入创新元素，不要生硬
        4. 运用指定的叙述技法
        5. 角色行为符合其设定
        6. 语言风格符合{config.variant.world_flavor}
        7. 场景描写生动有画面感
        8. 对话自然符合角色性格
        9. 情节推进自然流畅
        10. 避免常见俗套写法

        请直接开始写作正文：
        """

        chapter_response = await self.llm_service.generate_text(
            chapter_prompt,
            temperature=0.7 + config.randomization_level * 0.2,
            max_tokens=6000
        )

        return {
            "chapter_number": chapter_number,
            "title": chapter_title,
            "content": chapter_response.content,
            "word_count": len(chapter_response.content),
            "innovations_used": chapter_innovations,
            "narrative_technique": narrative_technique,
            "technique_application": technique_application,
            "config_used": asdict(config)
        }

    def _get_technique_application(self, technique: str, chapter_number: int) -> str:
        """获取叙述技法的具体应用"""
        if not technique or technique not in self.narrative_techniques:
            return "常规叙述"

        implementations = self.narrative_techniques[technique]["implementation"]

        # 根据章节位置选择合适的应用方式
        if chapter_number <= 3:  # 开篇
            suitable = [impl for impl in implementations if "开场" in impl or "介绍" in impl]
        elif chapter_number >= 15:  # 结尾
            suitable = [impl for impl in implementations if "结尾" in impl or "总结" in impl]
        else:  # 中间
            suitable = implementations

        return random.choice(suitable if suitable else implementations)


class EnhancedStoryGeneratorTool(AsyncTool):
    """增强版故事生成工具"""

    def __init__(self):
        super().__init__()
        self.generator = EnhancedStoryGenerator()

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="enhanced_story_generator",
            description="生成高度差异化的故事内容，确保每次生成都有显著不同",
            category="generation",
            parameters=[
                ToolParameter(
                    name="action",
                    type="string",
                    description="操作类型：config/character/outline/chapter/full_story",
                    required=True
                ),
                ToolParameter(
                    name="base_theme",
                    type="string",
                    description="基础主题",
                    required=False,
                    default="修仙"
                ),
                ToolParameter(
                    name="randomization_level",
                    type="number",
                    description="随机化程度 0-1",
                    required=False,
                    default=0.8
                ),
                ToolParameter(
                    name="avoid_recent",
                    type="boolean",
                    description="是否避免最近使用的元素",
                    required=False,
                    default=True
                ),
                ToolParameter(
                    name="chapter_count",
                    type="integer",
                    description="章节数量",
                    required=False,
                    default=20
                ),
                ToolParameter(
                    name="config",
                    type="object",
                    description="故事配置（用于后续生成）",
                    required=False
                ),
                ToolParameter(
                    name="characters",
                    type="array",
                    description="角色列表（用于章节生成）",
                    required=False
                ),
                ToolParameter(
                    name="plot_outline",
                    type="object",
                    description="情节大纲（用于章节生成）",
                    required=False
                ),
                ToolParameter(
                    name="chapter_info",
                    type="object",
                    description="章节信息（用于章节生成）",
                    required=False
                )
            ]
        )

    async def execute(self, parameters: Dict[str, Any],
                      context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行增强版故事生成"""

        action = parameters.get("action")
        base_theme = parameters.get("base_theme", "修仙")
        randomization_level = parameters.get("randomization_level", 0.8)
        avoid_recent = parameters.get("avoid_recent", True)

        if action == "config":
            # 生成故事配置
            config = await self.generator.generate_enhanced_story_config(
                base_theme, randomization_level, avoid_recent
            )

            return {
                "config": asdict(config),
                "generation_info": {
                    "base_theme": base_theme,
                    "randomization_level": randomization_level,
                    "variant_id": config.variant.variant_id
                }
            }

        elif action == "character":
            # 生成角色
            config_data = parameters.get("config", {})
            if not config_data:
                return {"error": "需要提供故事配置"}

            # 重建配置对象
            variant_data = config_data.get("variant", {})
            variant = GenerationVariant(**variant_data)
            config = EnhancedStoryConfig(
                base_theme=config_data.get("base_theme", base_theme),
                variant=variant,
                randomization_level=config_data.get("randomization_level", randomization_level),
                innovation_factors=config_data.get("innovation_factors", []),
                constraint_adherence=config_data.get("constraint_adherence", 0.7)
            )

            character = await self.generator.generate_enhanced_character(config)

            return {
                "character": character,
                "config_used": asdict(config)
            }

        elif action == "outline":
            # 生成情节大纲
            config_data = parameters.get("config", {})
            chapter_count = parameters.get("chapter_count", 20)

            if not config_data:
                return {"error": "需要提供故事配置"}

            # 重建配置对象
            variant_data = config_data.get("variant", {})
            variant = GenerationVariant(**variant_data)
            config = EnhancedStoryConfig(
                base_theme=config_data.get("base_theme", base_theme),
                variant=variant,
                randomization_level=config_data.get("randomization_level", randomization_level),
                innovation_factors=config_data.get("innovation_factors", []),
                constraint_adherence=config_data.get("constraint_adherence", 0.7)
            )

            outline = await self.generator.generate_enhanced_plot_outline(config, chapter_count)

            return {
                "plot_outline": outline,
                "config_used": asdict(config)
            }

        elif action == "chapter":
            # 生成章节
            config_data = parameters.get("config", {})
            characters = parameters.get("characters", [])
            plot_outline = parameters.get("plot_outline", {})
            chapter_info = parameters.get("chapter_info", {})

            if not all([config_data, characters, plot_outline, chapter_info]):
                return {"error": "需要提供完整的生成参数"}

            # 重建配置对象
            variant_data = config_data.get("variant", {})
            variant = GenerationVariant(**variant_data)
            config = EnhancedStoryConfig(
                base_theme=config_data.get("base_theme", base_theme),
                variant=variant,
                randomization_level=config_data.get("randomization_level", randomization_level),
                innovation_factors=config_data.get("innovation_factors", []),
                constraint_adherence=config_data.get("constraint_adherence", 0.7)
            )

            chapter = await self.generator.generate_enhanced_chapter(
                config, chapter_info, characters, plot_outline
            )

            return {
                "chapter": chapter
            }

        elif action == "full_story":
            # 生成完整故事
            chapter_count = parameters.get("chapter_count", 20)

            # 1. 生成配置
            config = await self.generator.generate_enhanced_story_config(
                base_theme, randomization_level, avoid_recent
            )

            # 2. 生成主要角色
            protagonist = await self.generator.generate_enhanced_character(config, "protagonist")
            antagonist = await self.generator.generate_enhanced_character(config, "antagonist")
            supporting = await self.generator.generate_enhanced_character(config, "supporting")

            characters = [protagonist, antagonist, supporting]

            # 3. 生成情节大纲
            plot_outline = await self.generator.generate_enhanced_plot_outline(config,
                                                                               chapter_count)

            return {
                "story_package": {
                    "config": asdict(config),
                    "characters": characters,
                    "plot_outline": plot_outline,
                    "generation_info": {
                        "base_theme": base_theme,
                        "chapter_count": chapter_count,
                        "randomization_level": randomization_level,
                        "variant_id": config.variant.variant_id
                    }
                }
            }

        else:
            return {"error": "不支持的操作类型"}


# 使用示例
if __name__ == "__main__":
    import asyncio


    async def test_enhanced_generation():
        tool = EnhancedStoryGeneratorTool()

        # 生成多个不同的故事配置
        for i in range(3):
            print(f"\n=== 故事变体 {i + 1} ===")

            # 生成配置
            config_result = await tool.execute({
                "action": "config",
                "base_theme": "修仙",
                "randomization_level": 0.8,
                "avoid_recent": True
            })

            config = config_result["config"]
            variant = config["variant"]

            print(f"标题: {variant['title']}")
            print(f"结构: {variant['story_structure']}")
            print(f"原型: {variant['character_archetype']}")
            print(f"风味: {variant['world_flavor']}")
            print(f"冲突: {variant['conflict_type']}")
            print(f"基调: {variant['tone']}")
            print(f"创新因子: {config['innovation_factors']}")
            print(f"描述: {variant['description'][:150]}...")


    asyncio.run(test_enhanced_generation())
