# modules/character/enhanced_character_creator.py
"""
增强版角色创建器
提供高质量的角色生成和自动质量检查
"""

import asyncio
import json
import random
import re
from dataclasses import asdict
from typing import Dict, Any, List, Optional

from loguru import logger

from modules.character.character_creator import CharacterCreator, Character
from modules.character.character_creator import (
    CharacterAppearance, CharacterPersonality,
    CharacterBackground, CharacterAbilities
)
from config.settings import get_settings


class CharacterQualityChecker:
    """角色质量检查器"""

    def __init__(self, config: dict):
        self.config = config
        self.required_fields = config.get("required_fields", [])
        self.min_lengths = config.get("min_field_length", {})
        self.quality_threshold = config.get("quality_threshold", 0.8)

    def check_character_quality(self, character: Character) -> Dict[str, Any]:
        """检查角色质量"""
        issues = []
        quality_score = 1.0
        field_scores = {}

        # 检查必要字段
        for field in self.required_fields:
            if not hasattr(character, field):
                issues.append(f"缺少必要字段: {field}")
                quality_score -= 0.2
                field_scores[field] = 0.0
                continue

            field_data = getattr(character, field)
            field_score = self._evaluate_field_quality(field, field_data)
            field_scores[field] = field_score

            if field_score < 0.3:
                issues.append(f"字段 {field} 内容质量过低")
                quality_score -= 0.15
            elif field_score < 0.3:
                issues.append(f"字段 {field} 内容需要改进")
                quality_score -= 0.1

        # 检查描述长度
        for field, min_length in self.min_lengths.items():
            if hasattr(character, field):
                field_data = getattr(character, field)
                content_length = self._calculate_content_length(field_data)
                if content_length < min_length:
                    issues.append(f"字段 {field} 内容长度不足 ({content_length} < {min_length})")
                    quality_score -= 0.05

        return {
            "quality_score": max(0, quality_score),
            "field_scores": field_scores,
            "issues": issues,
            "passed": quality_score >= self.quality_threshold
        }

    def _evaluate_field_quality(self, field_name: str, field_data) -> float:
        """评估字段质量得分 (0-1)"""
        if self._is_field_empty(field_data):
            return 0.0

        if self._is_field_too_simple(field_name, field_data):
            return 0.4

        # 检查内容丰富度
        richness_score = self._calculate_richness_score(field_data)

        # 检查内容相关性
        relevance_score = self._calculate_relevance_score(field_name, field_data)

        return min(1.0, (richness_score + relevance_score) / 2)

    def _is_field_empty(self, field_data) -> bool:
        """检查字段是否为空"""
        if field_data is None:
            return True
        if isinstance(field_data, str) and not field_data.strip():
            return True
        if isinstance(field_data, list) and not field_data:
            return True
        if isinstance(field_data, dict) and not field_data:
            return True
        return False

    def _is_field_too_simple(self, field_name: str, field_data) -> bool:
        """检查字段内容是否过于简单"""
        simple_indicators = [
            "待完善", "暂无", "无", "普通", "一般", "标准",
            "默认", "基础", "简单", "常见", "平凡", "待补充",
            "未知", "不详", "略", "省略", "..."
        ]

        content_str = str(field_data).lower()
        return any(indicator in content_str for indicator in simple_indicators)

    def _calculate_richness_score(self, field_data) -> float:
        """计算内容丰富度得分"""
        content_str = str(field_data)

        # 长度评分
        length_score = min(1.0, len(content_str) / 200)

        # 词汇多样性评分
        words = re.findall(r'\w+', content_str)
        unique_words = set(words)
        diversity_score = min(1.0, len(unique_words) / max(1, len(words))) if words else 0

        # 结构化信息评分
        structure_score = 0.5
        if isinstance(field_data, dict):
            structure_score = min(1.0, len(field_data) / 5)
        elif isinstance(field_data, list):
            structure_score = min(1.0, len(field_data) / 3)

        return (length_score + diversity_score + structure_score) / 3

    def _calculate_relevance_score(self, field_name: str, field_data) -> float:
        """计算内容相关性得分"""
        content_str = str(field_data).lower()

        # 根据字段类型定义相关关键词
        relevant_keywords = {
            "appearance": ["外貌", "长相", "身高", "体型", "发型", "眼睛", "服装", "气质"],
            "personality": ["性格", "特点", "习惯", "脾气", "态度", "价值观", "品格"],
            "background": ["出身", "家庭", "经历", "过去", "成长", "教育", "事件"],
            "abilities": ["能力", "技能", "修为", "实力", "天赋", "法术", "武功"]
        }

        keywords = relevant_keywords.get(field_name, [])
        if not keywords:
            return 0.8  # 默认相关性

        found_keywords = sum(1 for keyword in keywords if keyword in content_str)
        return min(1.0, found_keywords / len(keywords) + 0.3)

    def _calculate_content_length(self, field_data) -> int:
        """计算内容长度"""
        if isinstance(field_data, str):
            return len(field_data)
        elif isinstance(field_data, (list, dict)):
            return len(str(field_data))
        else:
            return len(str(field_data))


class EnhancedCharacterCreator(CharacterCreator):
    """增强版角色创建器"""

    def __init__(self):
        super().__init__()

        # 获取质量检查配置
        settings = get_settings()
        self.quality_config = settings.novel.character_quality
        self.quality_checker = CharacterQualityChecker(self.quality_config)
        self.max_retry_attempts = self.quality_config.get("max_retry_attempts", 3)
        self.auto_enhance = self.quality_config.get("auto_enhance", True)

        logger.info("增强版角色创建器初始化完成")

    async def create_character(
        self,
        character_type: str = "主角",
        genre: str = "玄幻",
        world_setting: Optional[Dict] = None,
        requirements: Optional[Dict] = None
    ) -> Character:
        """创建高质量角色"""

        logger.info(f"开始创建{character_type}角色，类型：{genre}")

        best_character = None
        best_score = 0.0

        for attempt in range(self.max_retry_attempts):
            logger.info(f"第 {attempt + 1} 次尝试创建角色")

            try:
                # 使用增强的生成方法创建角色
                character = await self._create_character_enhanced(
                    character_type, genre, world_setting, requirements, attempt
                )

                # 检查角色质量
                quality_result = self.quality_checker.check_character_quality(character)
                current_score = quality_result["quality_score"]

                logger.info(f"角色质量得分: {current_score:.2f}")

                # 记录最佳角色
                if current_score > best_score:
                    best_character = character
                    best_score = current_score

                # 如果质量通过，直接返回
                if quality_result["passed"]:
                    logger.info(f"角色创建成功，质量得分: {current_score:.2f}")
                    return character
                else:
                    logger.warning(f"角色质量不足，得分: {current_score:.2f}")
                    logger.warning(f"问题: {quality_result['issues']}")

                    # 尝试增强现有角色
                    if self.auto_enhance and attempt < self.max_retry_attempts - 1:
                        logger.info("尝试增强角色质量")
                        enhanced_character = await self._enhance_character_quality(
                            character, quality_result
                        )

                        # 再次检查增强后的角色
                        enhanced_quality = self.quality_checker.check_character_quality(
                            enhanced_character)
                        enhanced_score = enhanced_quality["quality_score"]

                        logger.info(f"增强后质量得分: {enhanced_score:.2f}")

                        if enhanced_score > current_score:
                            character = enhanced_character
                            current_score = enhanced_score

                            if enhanced_score > best_score:
                                best_character = character
                                best_score = enhanced_score

                        if enhanced_quality["passed"]:
                            logger.info(f"角色增强成功，质量得分: {enhanced_score:.2f}")
                            return enhanced_character

            except Exception as e:
                logger.error(f"第{attempt + 1}次角色创建失败: {e}")
                if attempt == self.max_retry_attempts - 1:
                    raise

        # 返回最佳角色，即使质量不够理想
        if best_character:
            logger.warning(f"返回最佳角色，质量得分: {best_score:.2f}")
            return best_character
        else:
            logger.error("角色创建完全失败，返回基础角色")
            return await super().create_character(character_type, genre, world_setting,
                                                  requirements)

    async def _create_character_enhanced(
        self,
        character_type: str,
        genre: str,
        world_setting: Optional[Dict],
        requirements: Optional[Dict],
        attempt: int
    ) -> Character:
        """增强版角色创建内部方法"""

        # 根据尝试次数调整参数
        temperature = 0.8 + (attempt * 0.05)  # 逐渐增加随机性
        max_tokens_bonus = attempt * 200  # 逐渐增加token限制

        logger.info(f"使用参数: temperature={temperature}, bonus_tokens={max_tokens_bonus}")

        # 生成基础信息
        basic_info = await self._generate_basic_info_enhanced(
            character_type, genre, requirements, temperature, max_tokens_bonus
        )
        logger.info(f"生成基础信息: {basic_info.get('name', 'Unknown')}")

        # 生成详细信息
        appearance = await self._generate_appearance_enhanced(
            basic_info, world_setting, temperature, max_tokens_bonus
        )

        personality = await self._generate_personality_enhanced(
            basic_info, character_type, temperature, max_tokens_bonus
        )

        background = await self._generate_background_enhanced(
            basic_info, world_setting, temperature, max_tokens_bonus
        )

        abilities = await self._generate_abilities_enhanced(
            basic_info, genre, world_setting, temperature, max_tokens_bonus
        )

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
            creation_notes=f"增强生成，尝试{attempt + 1}次",
            inspiration=""
        )

        return character

    async def _generate_basic_info_enhanced(
        self, character_type: str, genre: str, requirements: Optional[Dict],
        temperature: float, max_tokens_bonus: int
    ) -> Dict[str, Any]:
        """增强版基础信息生成"""

        prompt = self.prompt_manager.get_prompt(
            "character",
            "basic_info",
            character_type=character_type,
            genre=genre,
            requirements=requirements or {}
        )

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
            "key_relationships": ["与其他角色的关系1", "关系2"],
            "core_motivation": "角色的核心动机",
            "unique_trait": "最突出的个人特质"
        }}

        要求：
        - 姓名要有深意，符合{genre}世界观
        - 角色要有鲜明特色，避免平庸
        - 为后续发展留下充足空间
        - 每个字段都要具体详细
        - 注意返回 JSON 格式正确，避免字符串中使用符号影响 JSON 解析
        """

        response_text = await self._generate_with_retry_enhanced(
            prompt, temperature, 600 + max_tokens_bonus
        )
        basic_info = await self._parse_json_response_enhanced(response_text)

        # 确保基础信息完整
        validate_user = await self._ensure_complete_basic_info(basic_info, character_type, genre)

        return basic_info

    async def _generate_appearance_enhanced(
        self, basic_info: Dict, world_setting: Optional[Dict],
        temperature: float, max_tokens_bonus: int
    ) -> CharacterAppearance:
        """增强版外貌生成"""

        prompt = self.prompt_manager.get_prompt(
            "character",
            "appearance",
            name=basic_info["name"],
            world_setting=world_setting or "标准玄幻世界"
        )

        prompt += """

        请以完整的JSON格式返回，包含以下所有字段：
        {
            "gender": "性别",
            "age": 年龄数字,
            "height": "详细身高描述（包含具体数值和比例）",
            "build": "详细体型描述（肌肉线条、身材比例等）",
            "hair_color": "具体发色和发型（质感、长度、造型）",
            "eye_color": "具体眼色和眼神（形状、光芒、表情）",
            "skin_tone": "肌肤特点（颜色、质感、特殊标记）",
            "distinctive_features": ["独特特征1", "独特特征2", "独特特征3", "独特特征4"],
            "clothing_style": "详细穿衣风格描述（喜好、品味、常见搭配）",
            "accessories": ["配饰1", "配饰2", "配饰3"]
        }

        要求：
        - 每个字段都要具体详细，避免模糊描述
        - 外貌要与角色身份和性格相符
        - 特征要生动具体，便于想象
        - 至少包含4个独特特征
        - 注意返回 JSON 格式正确，避免字符串中使用符号影响 JSON 解析
        """

        response_text = await self._generate_with_retry_enhanced(
            prompt, temperature, 800 + max_tokens_bonus
        )
        appearance_data = await self._parse_json_response_enhanced(response_text)
        appearance_data = self._ensure_complete_appearance(appearance_data, basic_info)

        return CharacterAppearance(**appearance_data)

    async def _generate_personality_enhanced(
        self, basic_info: Dict, character_type: str,
        temperature: float, max_tokens_bonus: int
    ) -> CharacterPersonality:
        """增强版性格生成"""

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

        要求：
        - 性格要有层次感和复杂性
        - 优缺点要具体且平衡
        - 每个特质都要详细描述
        - 体现角色的独特性
        - 注意返回 JSON 格式正确，避免字符串中使用符号影响 JSON 解析
        """

        response_text = await self._generate_with_retry_enhanced(
            prompt, temperature, 1000 + max_tokens_bonus
        )
        personality_data = await self._parse_json_response_enhanced(response_text)
        personality_data = self._ensure_complete_personality(personality_data, character_type)

        return CharacterPersonality(**personality_data)

    async def _generate_background_enhanced(
        self, basic_info: Dict, world_setting: Optional[Dict],
        temperature: float, max_tokens_bonus: int
    ) -> CharacterBackground:
        """增强版背景生成"""

        prompt = self.prompt_manager.get_prompt(
            "character",
            "background",
            name=basic_info["name"],
            world_setting=world_setting or "标准玄幻世界"
        )

        prompt += """

        请以完整的JSON格式返回：
        {
            "birthplace": "具体出生地描述（地理位置、环境特色）",
            "family": {
                "father": "父亲详细信息（职业、性格、关系）",
                "mother": "母亲详细信息（职业、性格、关系）",
                "siblings": "兄弟姐妹信息",
                "others": "其他重要亲属"
            },
            "childhood": "详细童年经历描述（至少150字，包含重要事件）",
            "education": ["教育经历1", "教育经历2", "师承关系"],
            "major_events": [
                {"event": "重大事件1", "age": "发生年龄", "impact": "对角色的深远影响"},
                {"event": "重大事件2", "age": "发生年龄", "impact": "对角色的深远影响"},
                {"event": "重大事件3", "age": "发生年龄", "impact": "对角色的深远影响"}
            ],
            "relationships": [
                {"relation": "关系类型", "name": "人物姓名", "description": "详细关系描述"},
                {"relation": "关系类型", "name": "人物姓名", "description": "详细关系描述"}
            ],
            "secrets": ["个人秘密1", "个人秘密2"],
            "goals": ["人生目标1", "人生目标2", "当前目标"]
        }

        要求：
        - 背景要丰富详细，有层次感
        - 重大事件要有前因后果
        - 为角色行为提供充分动机
        - 与世界观设定保持一致
        - 注意返回 JSON 格式正确，避免字符串中使用符号影响 JSON 解析
        """

        response_text = await self._generate_with_retry_enhanced(
            prompt, temperature, 1200 + max_tokens_bonus
        )
        background_data = await self._parse_json_response_enhanced(response_text)
        background_data = self._ensure_complete_background(background_data)

        return CharacterBackground(**background_data)

    async def _generate_abilities_enhanced(
        self, basic_info: Dict, genre: str, world_setting: Optional[Dict],
        temperature: float, max_tokens_bonus: int
    ) -> CharacterAbilities:
        """增强版能力生成"""

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

        要求：
        - 能力体系要完整详细
        - 符合世界观的力量体系
        - 实力与角色设定匹配
        - 留有合理的成长空间
        - 注意返回 JSON 格式正确，避免字符串中使用符号影响 JSON 解析
        """

        response_text = await self._generate_with_retry_enhanced(
            prompt, temperature, 1200 + max_tokens_bonus
        )
        abilities_data = await self._parse_json_response_enhanced(response_text)
        abilities_data = self._ensure_complete_abilities(abilities_data, genre)

        return CharacterAbilities(**abilities_data)

    async def _generate_with_retry_enhanced(
        self, prompt: str, temperature: float, max_tokens: int, max_retries: int = 3
    ) -> str:
        """增强版带重试的生成"""

        for attempt in range(max_retries):
            try:
                response = await self.llm_service.generate_text(
                    prompt,
                    temperature=temperature,
                    max_tokens=max_tokens
                )

                # 验证响应质量
                if len(response.content.strip()) > 100:  # 基本长度检查
                    return response.content
                else:
                    logger.warning(f"第{attempt + 1}次生成内容过短，重试")

            except Exception as e:
                logger.error(f"第{attempt + 1}次生成失败: {e}")

            if attempt < max_retries - 1:
                await asyncio.sleep(1)  # 短暂等待后重试

        raise Exception("生成失败，已达到最大重试次数")

    async def _parse_json_response_enhanced(self, response: str) -> Dict[str, Any]:
        """增强版JSON解析"""
        logger.debug(f"开始解析响应，长度: {len(response)}")

        # 使用原有的解析方法
        try:
            return await self._parse_json_response(response)
        except Exception as e:
            logger.error(f"JSON解析失败: {e}")
            # 返回空字典，让后续的完整性检查处理
            return {}

    async def _enhance_character_quality(
        self, character: Character, quality_result: Dict[str, Any]
    ) -> Character:
        """增强角色质量"""

        issues = quality_result.get("issues", [])
        field_scores = quality_result.get("field_scores", {})

        # 根据字段得分确定需要增强的部分
        for field, score in field_scores.items():
            if score < 0.6:  # 得分较低的字段需要增强
                logger.info(f"增强字段: {field} (当前得分: {score:.2f})")

                if field == "appearance":
                    character.appearance = await self._enhance_appearance(character)
                elif field == "personality":
                    character.personality = await self._enhance_personality(character)
                elif field == "background":
                    character.background = await self._enhance_background(character)
                elif field == "abilities":
                    character.abilities = await self._enhance_abilities(character)

        return character

    async def _enhance_appearance(self, character: Character) -> CharacterAppearance:
        """增强外貌描述"""

        current_appearance = asdict(character.appearance)

        prompt = f"""
        角色 {character.name} 的外貌描述需要更加丰富详细。

        当前外貌信息：{current_appearance}

        请创建一个更加详细生动的外貌描述，要求：
        1. 保留现有的合理信息
        2. 补充缺失或简单的描述
        3. 增加更多独特的外貌特征
        4. 让外貌更加立体生动
        5. 与角色身份和性格相符
        - 注意返回 JSON 格式正确，避免字符串中使用符号影响 JSON 解析

        返回完整的JSON格式，每个字段都要具体详细：
        {{
            "gender": "性别",
            "age": 年龄,
            "height": "详细身高描述",
            "build": "详细体型描述",
            "hair_color": "详细发型发色",
            "eye_color": "详细眼睛描述",
            "skin_tone": "详细肌肤描述",
            "distinctive_features": ["特征1", "特征2", "特征3", "特征4"],
            "clothing_style": "详细服饰风格",
            "accessories": ["配饰1", "配饰2", "配饰3"]
        }}
        """

        response = await self.llm_service.generate_text(
            prompt, temperature=0.9, max_tokens=800
        )

        enhanced_data = await self._parse_json_response_enhanced(response.content)

        # 合并原有数据和增强数据
        for key, value in enhanced_data.items():
            if key in current_appearance:
                # 如果新数据更详细，使用新数据
                if (isinstance(value, str) and len(value) > len(str(current_appearance[key]))) or \
                    (isinstance(value, list) and len(value) > len(current_appearance[key])):
                    current_appearance[key] = value

        return CharacterAppearance(**current_appearance)

    async def _enhance_personality(self, character: Character) -> CharacterPersonality:
        """增强性格描述"""

        current_personality = asdict(character.personality)

        prompt = f"""
        角色 {character.name} 的性格描述需要更加丰富详细。

        当前性格信息：{current_personality}
- 注意返回 JSON 格式正确，避免字符串中使用符号影响 JSON 解析
        请创建更加详细的性格描述，补充和完善现有信息：

        返回完整的JSON格式：
        {{
            "core_traits": ["特质1", "特质2", "特质3", "特质4", "特质5"],
            "strengths": ["优点1", "优点2", "优点3"],
            "weaknesses": ["缺点1", "缺点2", "缺点3"],
            "fears": ["恐惧1", "恐惧2"],
            "desires": ["欲望1", "欲望2", "欲望3"],
            "habits": ["习惯1", "习惯2", "习惯3"],
            "speech_pattern": "详细说话方式描述",
            "moral_alignment": "详细道德取向描述"
        }}
        """

        response = await self.llm_service.generate_text(
            prompt, temperature=0.9, max_tokens=1000
        )

        enhanced_data = await self._parse_json_response_enhanced(response.content)

        # 合并数据
        for key, value in enhanced_data.items():
            if key in current_personality and value:
                current_personality[key] = value

        return CharacterPersonality(**current_personality)

    async def _enhance_background(self, character: Character) -> CharacterBackground:
        """增强背景描述"""

        current_background = asdict(character.background)

        prompt = f"""
        角色 {character.name} 的背景描述需要更加丰富详细。

        当前背景信息：{current_background}

        请创建更加详细的背景描述，特别是：
        1. 详细的童年经历（至少200字）
        2. 具体的重大事件和影响
        3. 丰富的人际关系网络
        4. 个人秘密和动机

        返回完整的JSON格式。
        """

        response = await self.llm_service.generate_text(
            prompt, temperature=0.9, max_tokens=1200
        )

        enhanced_data = await self._parse_json_response_enhanced(response.content)

        # 合并数据，优先使用更详细的信息
        for key, value in enhanced_data.items():
            if key in current_background and value:
                if isinstance(value, str) and len(value) > len(str(current_background[key])):
                    current_background[key] = value
                elif isinstance(value, (list, dict)) and len(value) > len(current_background[key]):
                    current_background[key] = value

        return CharacterBackground(**current_background)

    async def _enhance_abilities(self, character: Character) -> CharacterAbilities:
        """增强能力描述"""

        current_abilities = asdict(character.abilities)

        prompt = f"""
        角色 {character.name} 的能力描述需要更加丰富详细。

        当前能力信息：{current_abilities}

        请创建更加详细的能力体系，包括：
        1. 具体的修炼功法和特点
        2. 详细的特殊能力描述
        3. 丰富的技能列表
        4. 具体的法宝装备
        5. 成长潜力分析

        返回完整的JSON格式。
        """

        response = await self.llm_service.generate_text(
            prompt, temperature=0.9, max_tokens=1200
        )

        enhanced_data = await self._parse_json_response_enhanced(response.content)

        # 合并数据
        for key, value in enhanced_data.items():
            if key in current_abilities and value:
                current_abilities[key] = value

        return CharacterAbilities(**current_abilities)
