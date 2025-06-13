# modules/generation/enhanced_story_generator.py
"""
增强版故事生成器 - 集成配置管理版本
整合多样性增强功能，确保每次生成都有显著差异
与config_manager集成，使用全局配置
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
from config.config_manager import get_novel_config, get_enhanced_config  # 新增：获取全局配置
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

    # 新增：从全局配置继承的字段
    word_count_per_chapter: int = 2000  # 每章字数
    enable_plot_twists: bool = True  # 启用情节转折
    narrative_complexity: str = "medium"  # 叙述复杂度


class EnhancedStoryGenerator:
    """增强版故事生成器"""

    def __init__(self):
        self.llm_service = get_llm_service()
        self.prompt_manager = get_prompt_manager()
        self.diversity_enhancer = DiversityEnhancer()

        # 获取全局配置
        self.novel_config = get_novel_config()
        self.enhanced_config = get_enhanced_config()

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
                "implementation": ["角色轮换", "观点冲突", "信息互补"],
                "effect": "丰富故事层次"
            },
            "元叙事": {
                "description": "故事中的故事，自我指涉的叙述结构",
                "implementation": ["书中书", "戏中戏", "梦境嵌套", "虚实交错"],
                "effect": "增加哲学深度"
            },
            "意识流": {
                "description": "直接展现角色的内心活动和思维过程",
                "implementation": ["内心独白", "联想跳跃", "时空交错", "感官融合"],
                "effect": "深入心理描写"
            },
            "寓言化": {
                "description": "通过象征和隐喻表达深层含义",
                "implementation": ["象征物", "隐喻场景", "寓言情节", "哲理对话"],
                "effect": "提升思想内涵"
            }
        }

    def _load_character_innovations(self) -> Dict[str, Dict[str, Any]]:
        """加载角色创新设定"""
        return {
            "双重人格": {
                "description": "角色具有两种截然不同的人格",
                "variations": ["善恶对立", "理性感性", "过去现在"],
                "narrative_impact": "内心冲突戏剧化"
            },
            "时间旅行者": {
                "description": "来自不同时代的角色",
                "variations": ["未来预知", "历史重现", "时空错位"],
                "narrative_impact": "时间悖论和因果关系"
            },
            "情感操控": {
                "description": "能够感知或操控他人情感",
                "variations": ["共情能力", "情绪传染", "心理暗示"],
                "narrative_impact": "人际关系复杂化"
            },
            "逆向成长": {
                "description": "角色经历与常规相反的发展轨迹",
                "variations": ["强变弱", "智变愚", "善变恶"],
                "narrative_impact": "颠覆传统成长模式"
            }
        }

    def _load_plot_twists(self) -> Dict[str, Dict[str, Any]]:
        """加载情节转折技巧"""
        return {
            "身份揭秘": {
                "types": ["真实身份", "隐藏关系", "双重间谍"],
                "timing": ["中期转折", "高潮前", "结尾反转"],
                "impact": ["重新定义角色", "改变阵营", "颠覆认知"]
            },
            "真相反转": {
                "types": ["假象真相", "局中局", "记忆错误"],
                "timing": ["逐步揭示", "突然爆发", "最后一刻"],
                "impact": ["质疑一切", "重新解读", "价值观冲击"]
            },
            "时空扭曲": {
                "types": ["时间循环", "平行世界", "因果倒置"],
                "timing": ["开篇设定", "中期揭示", "结局解释"],
                "impact": ["现实感模糊", "逻辑重构", "哲学思考"]
            },
            "能力觉醒": {
                "types": ["隐藏天赋", "血脉觉醒", "器物共鸣"],
                "timing": ["危机时刻", "情感激发", "特殊环境"],
                "impact": ["力量平衡改变", "自我认知更新", "责任感升级"]
            }
        }

    def _load_world_innovations(self) -> Dict[str, Dict[str, Any]]:
        """加载世界创新设定"""
        return {
            "重力可控": {
                "description": "重力成为可操控的力量",
                "applications": ["建筑悬浮", "战斗技巧", "交通革命"],
                "conflicts": ["重力垄断", "失重灾难", "引力武器"]
            },
            "思想战争": {
                "description": "思想和观念的直接对抗",
                "applications": ["概念武器", "信念护盾", "记忆战场"],
                "conflicts": ["认知侵略", "思维病毒", "意识形态战"]
            },
            "记忆货币": {
                "description": "记忆成为交易媒介",
                "applications": ["经验买卖", "技能传承", "情感交易"],
                "conflicts": ["记忆贫富差距", "身份失真", "历史篡改"]
            },
            "维度文明": {
                "description": "不同维度的文明交汇",
                "applications": ["维度旅行", "跨次元贸易", "多重现实"],
                "conflicts": ["维度战争", "现实污染", "存在危机"]
            }
        }

    async def generate_enhanced_story_config(
        self,
        base_theme: str,
        randomization_level: float = None,
        avoid_recent: bool = None
    ) -> EnhancedStoryConfig:
        """生成增强故事配置 - 集成全局配置版本"""

        # 从全局配置获取默认值（方案3：配置继承机制）
        if randomization_level is None:
            randomization_level = self.enhanced_config.default_randomization_level

        if avoid_recent is None:
            avoid_recent = self.enhanced_config.avoid_recent_elements

        # 检查多样性开关
        if not self.enhanced_config.enable_diversity:
            randomization_level = 0.0
            avoid_recent = False
            logger.info("多样性增强已通过配置禁用")

        # 限制主题选择
        if base_theme in self.enhanced_config.forbidden_themes:
            logger.warning(f"主题 '{base_theme}' 在配置中被禁用，使用默认主题")
            base_theme = self.enhanced_config.preferred_themes[
                0] if self.enhanced_config.preferred_themes else "修仙"

        # 应用主题偏好
        if (self.enhanced_config.preferred_themes and
            base_theme not in self.enhanced_config.preferred_themes and
            randomization_level > 0.5):
            # 高随机化时可能调整到偏好主题
            if random.random() < 0.3:
                base_theme = random.choice(self.enhanced_config.preferred_themes)
                logger.info(f"根据配置偏好调整主题为: {base_theme}")

        # 获取避免约束
        constraints = None
        if avoid_recent:
            constraints = self.diversity_enhancer.get_avoidance_constraints(recent_count=5)

        # 生成多样性变体（使用正确的方法名）
        variant = await self.diversity_enhancer.generate_diverse_variant(base_theme, constraints)

        # 选择创新因子（考虑配置）
        available_factors = self.enhanced_config.default_innovation_factors.copy()

        # 根据创新强度调整因子数量
        intensity_map = {"low": 1, "medium": 2, "high": 3}
        factor_count = intensity_map.get(self.enhanced_config.innovation_intensity, 2)
        factor_count = min(factor_count + int(randomization_level * 2), len(available_factors))

        innovation_factors = random.sample(available_factors, factor_count)

        return EnhancedStoryConfig(
            base_theme=base_theme,
            variant=variant,
            randomization_level=randomization_level,
            innovation_factors=innovation_factors,
            constraint_adherence=self.enhanced_config.constraint_adherence,
            # 从全局配置继承
            word_count_per_chapter=self.novel_config.default_word_count,
            enable_plot_twists=self.enhanced_config.enable_plot_twists,
            narrative_complexity=self.enhanced_config.narrative_complexity
        )

    async def generate_enhanced_character(self, config: EnhancedStoryConfig,
                                          role: str = "protagonist") -> Dict[str, Any]:
        """生成增强角色"""
        character_prompt = f"""
        基于以下创新设定创造一个独特的{role}角色：

        故事背景：
        - 主题：{config.base_theme}
        - 世界风味：{config.variant.world_flavor}
        - 角色原型：{config.variant.character_archetype}

        创新要求：
        - 融入创新因子：{config.innovation_factors}
        - 独特元素：{config.variant.unique_elements}
        - 避免常见俗套：{self.enhanced_config.avoid_cliches}

        请创造一个具有以下特点的角色：
        1. 符合{config.variant.character_archetype}原型但有独特变化
        2. 巧妙融入{random.choice(config.innovation_factors)}的创新元素
        3. 适合{config.variant.world_flavor}的世界设定
        4. 具有内在冲突和成长空间
        5. 名字具有{config.variant.world_flavor}特色

        返回格式：
        名字：
        年龄：
        外貌：
        性格：
        背景：
        能力：
        目标：
        弱点：
        创新特色：
        """

        response = await self.llm_service.generate_text(character_prompt, temperature=0.8)

        # 解析角色信息
        character_info = self._parse_character_response(response.content)

        # 确保名字唯一性
        if not character_info.get("name") or character_info["name"] in self.used_names:
            character_info["name"] = self._generate_composite_name(config, role)
        else:
            self.used_names.add(character_info["name"])

        character_info["role"] = role
        character_info["config_used"] = {
            "theme": config.base_theme,
            "archetype": config.variant.character_archetype,
            "world_flavor": config.variant.world_flavor,
            "innovations": config.innovation_factors
        }

        return character_info

    def _parse_character_response(self, response: str) -> Dict[str, Any]:
        """解析角色响应"""
        character = {}

        lines = response.split('\n')
        current_field = None
        current_content = []

        field_map = {
            "名字": "name", "年龄": "age", "外貌": "appearance",
            "性格": "personality", "背景": "background", "能力": "abilities",
            "目标": "goals", "弱点": "weaknesses", "创新特色": "innovations"
        }

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 检查是否是字段标题
            for chinese_field, english_field in field_map.items():
                if line.startswith(f"{chinese_field}：") or line.startswith(f"{chinese_field}:"):
                    # 保存之前的字段
                    if current_field and current_content:
                        character[current_field] = '\n'.join(current_content).strip()

                    # 开始新字段
                    current_field = english_field
                    current_content = [line.split('：', 1)[-1].split(':', 1)[-1].strip()]
                    break
            else:
                # 继续当前字段的内容
                if current_field:
                    current_content.append(line)

        # 保存最后一个字段
        if current_field and current_content:
            character[current_field] = '\n'.join(current_content).strip()

        # 提取名字（如果格式不规范）
        if not character.get("name"):
            character["name"] = self._extract_name_from_response(response)

        return character

    def _extract_name_from_response(self, response: str) -> str:
        """从响应中提取名字"""
        # 简单的名字提取逻辑
        cleaned = re.sub(r'[^\u4e00-\u9fff\w\s]', '', response)
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
        chapter_count: int = None
    ) -> Dict[str, Any]:
        """生成增强的情节大纲 - 修复版本"""

        # 使用全局配置的默认章节数
        if chapter_count is None:
            chapter_count = self.novel_config.default_chapter_count

        # 安全获取故事结构信息
        try:
            structure_info = self.diversity_enhancer.story_structures.get(
                config.variant.story_structure,
                "传统三段式结构"
            )
        except (AttributeError, KeyError):
            structure_info = "传统三段式结构"

        # 选择适用的转折技巧（考虑配置）
        applicable_twists = []
        if config.enable_plot_twists:
            applicable_twists = self._select_plot_twists(config.randomization_level)

        # 修复：安全选择叙述技法
        narrative_technique = self._select_narrative_technique_safely(config)

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
        - 叙述复杂度：{config.narrative_complexity}

        章节数量：{chapter_count}
        每章字数：约{config.word_count_per_chapter}字

        请创造一个{chapter_count}章的详细大纲，要求：
        1. 严格按照{config.variant.story_structure}结构展开
        2. 巧妙融入所有创新元素
        3. 在关键节点安排情节转折
        4. 运用{narrative_technique}的叙述技法
        5. 确保每章都有明确目标和独特看点
        6. 避免常见俗套情节
        7. 符合{config.narrative_complexity}复杂度要求

        请按章节序号列出大纲，每章包含：
        - 章节标题
        - 主要事件
        - 角色发展
        - 创新展现
        - 情感基调
        """

        try:
            outline_response = await self.llm_service.generate_text(outline_prompt, temperature=0.8)

            return {
                "story_structure": config.variant.story_structure,
                "narrative_technique": narrative_technique,
                "plot_twists": applicable_twists,
                "chapter_count": chapter_count,
                "detailed_outline": outline_response.content,
                "innovation_integration": config.innovation_factors,
                "word_count_target": config.word_count_per_chapter * chapter_count,
                "complexity_level": config.narrative_complexity
            }
        except Exception as e:
            logger.error(f"生成情节大纲时出错: {e}")
            # 返回错误恢复版本
            return {
                "story_structure": config.variant.story_structure,
                "narrative_technique": narrative_technique,
                "plot_twists": [],
                "chapter_count": chapter_count,
                "detailed_outline": f"第1章到第{chapter_count}章的基础大纲框架",
                "innovation_integration": config.innovation_factors,
                "word_count_target": config.word_count_per_chapter * chapter_count,
                "complexity_level": config.narrative_complexity,
                "error": str(e)
            }

    def _select_narrative_technique_safely(self, config: EnhancedStoryConfig) -> str:
        """安全选择叙述技法"""
        try:
            # 确保 narrative_techniques 已初始化
            if not hasattr(self, 'narrative_techniques') or not self.narrative_techniques:
                self.narrative_techniques = self._load_narrative_techniques()

            # 确保 innovation_factors 存在且不为空
            if not config.innovation_factors:
                logger.warning("创新因子列表为空，使用默认叙述技法")
                return "传统叙述"

            # 查找匹配的叙述技法
            matching_techniques = [t for t in config.innovation_factors
                                   if t in self.narrative_techniques]

            if matching_techniques:
                return random.choice(matching_techniques)
            else:
                # 如果没有匹配的，从 narrative_techniques 中随机选择一个
                logger.warning("创新因子中没有匹配的叙述技法，随机选择一个")
                available_techniques = list(self.narrative_techniques.keys())
                if available_techniques:
                    return random.choice(available_techniques)
                else:
                    # 如果连 narrative_techniques 都是空的，返回默认值
                    logger.error("叙述技法库为空，使用默认技法")
                    return "传统叙述"

        except Exception as e:
            logger.error(f"选择叙述技法时出错: {e}")
            return "传统叙述"

    def _select_plot_twists(self, randomization_level: float) -> List[Dict[str, Any]]:
        """选择情节转折 - 安全版本"""
        try:
            # 确保 plot_twists 已初始化
            if not hasattr(self, 'plot_twists') or not self.plot_twists:
                self.plot_twists = self._load_plot_twists()

            if not self.plot_twists:
                logger.warning("情节转折库为空")
                return []

            twist_count = max(1, int(1 + randomization_level * 3))  # 1-4个转折

            selected_twists = []
            available_twists = list(self.plot_twists.keys())

            for _ in range(min(twist_count, len(available_twists))):
                twist_type = random.choice(available_twists)
                twist_info = self.plot_twists[twist_type]

                selected_twists.append({
                    "type": twist_type,
                    "variation": random.choice(twist_info.get("types", ["基础变化"])),
                    "timing": random.choice(twist_info.get("timing", ["中期"])),
                    "expected_impact": random.choice(twist_info.get("impact", ["情节推进"]))
                })

            return selected_twists

        except Exception as e:
            logger.error(f"选择情节转折时出错: {e}")
            return []

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
        - 复杂度要求：{config.narrative_complexity}

        写作要求：
        1. 字数：{config.word_count_per_chapter}字左右
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
            max_tokens=int(config.word_count_per_chapter * 1.5)  # 基于配置调整token数
        )

        return {
            "chapter_number": chapter_number,
            "title": chapter_title,
            "content": chapter_response.content,
            "word_count": len(chapter_response.content),
            "target_word_count": config.word_count_per_chapter,
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
    """增强版故事生成工具 - 集成配置管理版本"""

    def __init__(self):
        super().__init__()
        self.generator = EnhancedStoryGenerator()

        # 方案1：获取全局配置
        self.novel_config = get_novel_config()
        self.enhanced_config = get_enhanced_config()

        logger.info(f"增强故事生成器初始化完成，配置加载:")
        logger.info(f"- 默认章节数: {self.novel_config.default_chapter_count}")
        logger.info(f"- 默认字数: {self.novel_config.default_word_count}")
        logger.info(f"- 多样性增强: {self.enhanced_config.enable_diversity}")
        logger.info(f"- 随机化程度: {self.enhanced_config.default_randomization_level}")

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="enhanced_story_generator",
            description="生成高度差异化的故事内容，确保每次生成都有显著不同，集成全局配置管理",
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
                    required=False
                ),
                ToolParameter(
                    name="chapter_count",
                    type="integer",
                    description=f"章节数量（默认：{get_novel_config().default_chapter_count}）",
                    required=False
                ),
                ToolParameter(
                    name="randomization_level",
                    type="number",
                    description=f"随机化程度0-1（默认：{get_enhanced_config().default_randomization_level}）",
                    required=False
                ),
                ToolParameter(
                    name="avoid_recent",
                    type="boolean",
                    description=f"避免最近使用的元素（默认：{get_enhanced_config().avoid_recent_elements}）",
                    required=False
                ),
                ToolParameter(
                    name="word_count",
                    type="integer",
                    description=f"每章字数（默认：{get_novel_config().default_word_count}）",
                    required=False
                )
            ]
        )

    async def execute(self, parameters: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> \
    Dict[str, Any]:
        """执行增强版故事生成 - 加强错误处理"""
        action = parameters.get("action", "config")

        try:
            base_theme = parameters.get("base_theme", self.enhanced_config.preferred_themes[
                0] if self.enhanced_config.preferred_themes else "修仙")
            randomization_level = parameters.get("randomization_level",
                                                 self.enhanced_config.default_randomization_level)
            avoid_recent = parameters.get("avoid_recent",
                                          self.enhanced_config.avoid_recent_elements)
            chapter_count = parameters.get("chapter_count", self.novel_config.default_chapter_count)
            word_count = parameters.get("word_count", self.novel_config.default_word_count)

            if action == "full_story":
                # 生成完整故事 - 增强错误处理版本
                logger.info(f"开始生成完整故事: 主题={base_theme}, 章节数={chapter_count}")

                try:
                    # 1. 生成配置
                    config = await self.generator.generate_enhanced_story_config(
                        base_theme, randomization_level, avoid_recent
                    )
                    config.word_count_per_chapter = word_count
                    logger.info("✅ 故事配置生成完成")

                except Exception as e:
                    logger.error(f"配置生成失败: {e}")
                    return {"error": f"配置生成失败: {str(e)}"}

                try:
                    # 2. 生成主要角色
                    logger.info("开始生成角色...")
                    characters = []

                    protagonist = await self.generator.generate_enhanced_character(config,
                                                                                   "protagonist")
                    if protagonist:
                        characters.append(protagonist)
                        logger.info("✅ 主角生成完成")

                    antagonist = await self.generator.generate_enhanced_character(config,
                                                                                  "antagonist")
                    if antagonist:
                        characters.append(antagonist)
                        logger.info("✅ 反派生成完成")

                    supporting = await self.generator.generate_enhanced_character(config,
                                                                                  "supporting")
                    if supporting:
                        characters.append(supporting)
                        logger.info("✅ 配角生成完成")

                    if not characters:
                        logger.warning("未生成任何角色，使用默认角色")
                        characters = [
                            {"name": "主角", "role": "protagonist", "description": "待完善"}]

                except Exception as e:
                    logger.error(f"角色生成失败: {e}")
                    characters = [
                        {"name": "主角", "role": "protagonist", "description": "生成失败"}]

                try:
                    # 3. 生成情节大纲
                    logger.info("开始生成情节大纲...")
                    plot_outline = await self.generator.generate_enhanced_plot_outline(config,
                                                                                       chapter_count)
                    logger.info("✅ 情节大纲生成完成")

                except Exception as e:
                    logger.error(f"情节大纲生成失败: {e}")
                    plot_outline = {"error": f"大纲生成失败: {str(e)}"}

                try:
                    # 4. 生成章节内容
                    logger.info(f"开始生成 {chapter_count} 章内容...")
                    chapters = []

                    for i in range(1, chapter_count + 1):
                        try:
                            chapter_info = {
                                "number": i,
                                "title": f"第{i}章",
                                "plot_summary": f"第{i}章的情节发展"
                            }

                            logger.info(f"生成第 {i} 章...")
                            chapter = await self.generator.generate_enhanced_chapter(
                                config, chapter_info, characters, plot_outline
                            )

                            if chapter:
                                chapters.append(chapter)
                                logger.info(f"✅ 第 {i} 章生成完成")
                            else:
                                logger.warning(f"第 {i} 章生成失败，跳过")

                        except Exception as e:
                            logger.error(f"第 {i} 章生成失败: {e}")
                            # 添加错误章节占位符
                            chapters.append({
                                "number": i,
                                "title": f"第{i}章",
                                "content": "章节生成失败",
                                "word_count": 0,
                                "error": str(e)
                            })

                    if not chapters:
                        logger.warning("未生成任何章节")
                        chapters = [
                            {"title": "未生成章节", "content": "章节生成失败", "word_count": 0}]

                    total_word_count = sum(ch.get("word_count", 0) for ch in chapters)
                    logger.info(f"完整故事生成完成，总字数: {total_word_count}")

                except Exception as e:
                    logger.error(f"章节生成过程失败: {e}")
                    chapters = [{"title": "生成失败", "content": "未能生成章节", "word_count": 0}]
                    total_word_count = 0

                # 安全构建返回结果
                try:
                    variant_dict = asdict(config.variant) if hasattr(config,
                                                                     'variant') and config.variant else {}
                    config_dict = asdict(config) if config else {}

                    return {
                        "story_package": {
                            "title": variant_dict.get("title", f"{base_theme}小说"),
                            "genre": base_theme,
                            "theme": base_theme,
                            "config": config_dict,
                            "characters": characters,
                            "plot_outline": plot_outline,
                            "chapters": chapters,
                            "generation_info": {
                                "base_theme": base_theme,
                                "chapter_count": len(chapters),
                                "actual_chapter_count": chapter_count,
                                "randomization_level": randomization_level,
                                "variant_id": variant_dict.get("variant_id", "unknown"),
                                "total_word_count": total_word_count,
                                "target_word_count": word_count * chapter_count,
                                "used_global_config": True,
                                "generation_success": len(chapters) > 0,
                                "config_source": {
                                    "novel_config": {
                                        "default_chapter_count": self.novel_config.default_chapter_count,
                                        "default_word_count": self.novel_config.default_word_count,
                                        "enable_diversity": self.enhanced_config.enable_diversity
                                    }
                                }
                            }
                        }
                    }

                except Exception as e:
                    logger.error(f"构建返回结果失败: {e}")
                    return {
                        "error": f"构建返回结果失败: {str(e)}",
                        "story_package": {
                            "title": f"{base_theme}小说",
                            "genre": base_theme,
                            "theme": base_theme,
                            "chapters": chapters or [],
                            "characters": characters or [],
                            "generation_info": {"error": str(e)}
                        }
                    }

            else:
                return {"error": f"不支持的操作类型: {action}"}

        except Exception as e:
            logger.error(f"execute 方法执行失败: {e}")
            import traceback
            logger.error(f"完整错误堆栈: {traceback.format_exc()}")
            return {
                "error": f"执行失败: {str(e)}",
                "story_package": {
                    "title": "生成失败",
                    "chapters": [],
                    "characters": [],
                    "generation_info": {"error": str(e)}
                }
            }


# 使用示例
if __name__ == "__main__":
    import asyncio


    async def test_enhanced_generation():
        tool = EnhancedStoryGeneratorTool()

        # 测试配置集成
        print("=== 测试配置集成 ===")
        print(f"默认章节数: {tool.novel_config.default_chapter_count}")
        print(f"默认字数: {tool.novel_config.default_word_count}")
        print(f"多样性开关: {tool.enhanced_config.enable_diversity}")
        print(f"默认创新因子: {tool.enhanced_config.default_innovation_factors}")

        # 生成故事（使用配置默认值）
        result = await tool.execute({
            "action": "full_story",
            "base_theme": "科幻"  # 只指定主题，其他使用配置默认值
        })

        if result.get("story_package"):
            story = result["story_package"]
            generation_info = story["generation_info"]

            print(f"\n=== 生成结果 ===")
            print(f"标题: {story.get('title')}")
            print(f"章节数: {len(story.get('chapters', []))}")
            print(f"总字数: {generation_info.get('total_word_count')}")
            print(f"使用全局配置: {generation_info.get('used_global_config')}")
            print(f"配置来源: {generation_info.get('config_source')}")


    asyncio.run(test_enhanced_generation())
