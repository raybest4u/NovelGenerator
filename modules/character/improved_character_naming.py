# improved_character_naming.py
"""
改进的角色名称生成器 - 解决名字重复问题
"""

import random
import re
import json
import hashlib
import time
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from core.llm_client import get_llm_service


@dataclass
class NameConfig:
    """名称配置"""
    gender: str = "any"
    cultural_style: str = "中式古典"
    character_type: str = "主角"
    world_flavor: str = "古典仙侠"
    avoid_names: Set[str] = None
    character_traits: List[str] = None


class ImprovedNameGenerator:
    """改进的名称生成器"""

    def __init__(self):
        self.llm_service = get_llm_service()
        self.used_names: Set[str] = set()  # 已使用的名字
        self.name_patterns = self._load_name_patterns()
        self.syllable_banks = self._load_syllable_banks()

    def _load_name_patterns(self) -> Dict[str, Dict]:
        """加载姓名模式"""
        return {
            "中式古典": {
                "surnames": [
                    "李", "王", "张", "刘", "陈", "杨", "赵", "黄", "周", "吴",
                    "徐", "孙", "胡", "朱", "高", "林", "何", "郭", "马", "罗",
                    "梁", "宋", "郑", "谢", "韩", "唐", "冯", "于", "董", "萧",
                    "程", "曹", "袁", "邓", "许", "傅", "沈", "曾", "彭", "吕",
                    "苏", "卢", "蒋", "蔡", "贾", "丁", "魏", "薛", "叶", "阎",
                    "慕容", "欧阳", "上官", "司徒", "诸葛", "司马", "独孤", "南宫"
                ],
                "male_names": [
                    # 单字名
                    "轩", "辰", "宇", "晨", "阳", "昊", "睿", "泽", "浩", "瑜",
                    "煜", "炎", "焱", "烨", "炜", "琛", "瑾", "瑄", "璟", "曜",
                    "羽", "翔", "鹏", "鸿", "雁", "鹤", "凤", "龙", "麟", "腾",
                    # 双字名组合词
                    "逍遥", "无极", "天行", "星河", "风云", "雷霆", "烈火", "寒冰",
                    "破军", "贪狼", "七杀", "紫微", "天府", "太阴", "巨门", "天相"
                ],
                "female_names": [
                    # 单字名
                    "雪", "霜", "月", "星", "云", "烟", "露", "霞", "虹", "彩",
                    "琴", "瑟", "筝", "萧", "箫", "笛", "琵", "琶", "瑶", "瑾",
                    "莲", "荷", "兰", "菊", "梅", "竹", "桃", "杏", "樱", "蕊",
                    # 双字名组合词
                    "若水", "如梦", "似雪", "凌波", "惊鸿", "飞燕", "紫烟", "青莲"
                ]
            },
            "现代风格": {
                "surnames": ["李", "王", "张", "刘", "陈", "杨", "赵", "黄", "周", "吴"],
                "male_names": ["伟", "强", "军", "明", "华", "建", "文", "德", "志", "勇"],
                "female_names": ["丽", "静", "敏", "慧", "娟", "英", "华", "芳", "琳", "红"]
            },
            "西式幻想": {
                "surnames": ["Von", "De", "Le", "Mac", "O'"],
                "male_names": ["Aiden", "Blake", "Cole", "Drake", "Ethan", "Felix"],
                "female_names": ["Aria", "Belle", "Cora", "Diana", "Elena", "Fiona"]
            }
        }

    def _load_syllable_banks(self) -> Dict[str, List[str]]:
        """加载音节库"""
        return {
            "优雅": ["雅", "韵", "诗", "画", "琴", "瑟", "兰", "菊", "梅", "竹"],
            "力量": ["霸", "威", "震", "雷", "炎", "龙", "虎", "狼", "鹰", "豹"],
            "智慧": ["睿", "哲", "慧", "明", "聪", "颖", "博", "学", "文", "墨"],
            "神秘": ["玄", "冥", "幽", "暗", "影", "魅", "魔", "妖", "鬼", "神"],
            "自然": ["风", "云", "雨", "雷", "山", "水", "火", "土", "木", "金"]
        }

    async def generate_character_name(self, config: NameConfig) -> str:
        """生成角色名称"""
        max_attempts = 10

        for attempt in range(max_attempts):
            # 尝试不同的生成策略
            if attempt < 3:
                name = await self._generate_with_llm(config, attempt)
            elif attempt < 6:
                name = self._generate_with_patterns(config)
            else:
                name = self._generate_with_syllables(config)

            if name and name not in self.used_names:
                self.used_names.add(name)
                return name

        # 如果都失败了，生成一个独特的后缀名字
        base_name = await self._generate_with_llm(config, 0)
        unique_name = f"{base_name}{random.randint(100, 999)}"
        self.used_names.add(unique_name)
        return unique_name

    async def _generate_with_llm(self, config: NameConfig, seed: int) -> str:
        """使用LLM生成名字"""

        # 增加随机性的提示词
        creativity_prompts = [
            "请创造一个前所未有的独特名字",
            "请生成一个充满想象力的原创名字",
            "请设计一个别具一格的新颖名字"
        ]

        creativity_prompt = creativity_prompts[seed % len(creativity_prompts)]

        # 添加时间戳和随机数增加唯一性
        timestamp = int(time.time() * 1000) % 10000
        random_num = random.randint(1000, 9999)

        prompt = f"""
        {creativity_prompt}，要求：

        角色设定：
        - 性别：{config.gender}
        - 角色类型：{config.character_type}
        - 文化风格：{config.cultural_style}
        - 世界背景：{config.world_flavor}
        - 性格特征：{config.character_traits or []}

        创意要求：
        1. 绝对不能使用这些已有名字：{list(config.avoid_names or []) + list(self.used_names)}
        2. 名字要体现{config.character_type}的特质
        3. 符合{config.cultural_style}的命名传统
        4. 音韵优美，朗朗上口
        5. 有独特的含义和寓意
        6. 避免常见俗套名字

        创意种子：{timestamp + random_num}

        请只返回一个名字，不要任何解释：
        """

        response = await self.llm_service.generate_text(
            prompt,
            temperature=0.9,  # 提高随机性
            max_tokens=50
        )

        return self._extract_name_from_response(response.content)

    def _generate_with_patterns(self, config: NameConfig) -> str:
        """使用预定义模式生成名字"""

        patterns = self.name_patterns.get(config.cultural_style,
                                          self.name_patterns["中式古典"])

        surname = random.choice(patterns["surnames"])

        if config.gender == "male":
            given_names = patterns["male_names"]
        elif config.gender == "female":
            given_names = patterns["female_names"]
        else:
            given_names = patterns["male_names"] + patterns["female_names"]

        # 随机选择单字名或双字名
        if random.random() < 0.7:  # 70%概率生成双字名
            if random.random() < 0.3:  # 30%概率使用预定义组合
                given_name = random.choice([name for name in given_names if len(name) > 1])
            else:  # 70%概率随机组合
                char1 = random.choice([name for name in given_names if len(name) == 1])
                char2 = random.choice([name for name in given_names if len(name) == 1])
                given_name = char1 + char2
        else:  # 30%概率生成单字名
            given_name = random.choice([name for name in given_names if len(name) == 1])

        return surname + given_name

    def _generate_with_syllables(self, config: NameConfig) -> str:
        """使用音节库生成名字"""

        patterns = self.name_patterns.get(config.cultural_style,
                                          self.name_patterns["中式古典"])
        surname = random.choice(patterns["surnames"])

        # 根据角色特征选择音节
        trait_categories = []
        if config.character_traits:
            for trait in config.character_traits:
                if "优雅" in trait or "美丽" in trait:
                    trait_categories.append("优雅")
                elif "强大" in trait or "勇敢" in trait:
                    trait_categories.append("力量")
                elif "聪明" in trait or "智慧" in trait:
                    trait_categories.append("智慧")
                elif "神秘" in trait or "冷酷" in trait:
                    trait_categories.append("神秘")

        if not trait_categories:
            trait_categories = ["自然", "优雅"]

        # 随机选择音节组合
        category = random.choice(trait_categories)
        syllables = self.syllable_banks[category]

        if random.random() < 0.6:  # 60%概率双字名
            given_name = random.choice(syllables) + random.choice(syllables)
        else:  # 40%概率单字名
            given_name = random.choice(syllables)

        return surname + given_name

    def _extract_name_from_response(self, response: str) -> str:
        """从LLM响应中提取名字"""

        # 清理响应文本
        cleaned = response.strip()

        # 移除常见的前缀和后缀
        prefixes_to_remove = [
            "名字：", "姓名：", "角色名：", "建议：", "推荐：",
            "Name:", "Character:", "建议名字：", "推荐名字："
        ]

        for prefix in prefixes_to_remove:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()

        # 移除引号和标点
        cleaned = re.sub(r'["""''`()（）【】\[\]<>《》]', '', cleaned)
        cleaned = re.sub(r'[，。！？；：,!?;:].*', '', cleaned)  # 移除标点后的内容

        # 提取第一个看起来像名字的部分
        words = cleaned.split()
        if words:
            potential_name = words[0]

            # 验证名字格式（中文名字通常2-4个字符）
            if 2 <= len(potential_name) <= 6 and all(
                '\u4e00' <= c <= '\u9fff' for c in potential_name):
                return potential_name

        # 如果提取失败，生成一个随机名字
        return self._generate_fallback_name()

    def _generate_fallback_name(self) -> str:
        """生成备用名字"""
        surnames = ["李", "王", "张", "刘", "陈", "杨", "赵", "黄"]
        chars = ["轩", "宇", "辰", "阳", "睿", "瑜", "煜", "炎", "羽", "翔"]

        surname = random.choice(surnames)
        given = random.choice(chars) + random.choice(chars)
        return surname + given

    def clear_used_names(self):
        """清空已使用的名字记录"""
        self.used_names.clear()

    def add_used_name(self, name: str):
        """添加已使用的名字"""
        self.used_names.add(name)


# 修改 CharacterCreator 类中的相关方法
class ImprovedCharacterCreator:
    """改进的角色创建器"""

    def __init__(self):
        self.llm_service = get_llm_service()
        self.name_generator = ImprovedNameGenerator()
        # 其他初始化代码...

    async def _generate_basic_info(self, character_type: str, genre: str,
                                   requirements: Optional[Dict] = None) -> Dict[str, Any]:
        """生成基础信息 - 改进版"""

        # 配置名称生成
        name_config = NameConfig(
            gender=requirements.get("gender", "any") if requirements else "any",
            cultural_style="中式古典",  # 可以根据genre调整
            character_type=character_type,
            world_flavor=genre,
            character_traits=requirements.get("traits", []) if requirements else []
        )

        # 生成独特名字
        character_name = await self.name_generator.generate_character_name(name_config)

        # 生成绰号（可选）
        nickname = await self._generate_nickname(character_name, character_type, genre)

        return {
            "name": character_name,
            "nickname": nickname,
            "importance": self._calculate_importance(character_type),
            "story_role": f"{character_type}在故事中的作用",
            "character_arc": f"{character_name}的成长历程"
        }

    async def _generate_nickname(self, name: str, character_type: str, genre: str) -> Optional[str]:
        """生成角色绰号"""

        if random.random() < 0.3:  # 30%概率有绰号
            prompt = f"""
            为角色{name}（{character_type}）生成一个合适的绰号：

            要求：
            1. 体现角色特色或能力
            2. 符合{genre}世界观
            3. 简洁有力，朗朗上口
            4. 避免俗套

            请只返回绰号，不要解释：
            """

            response = await self.llm_service.generate_text(prompt, temperature=0.8)
            nickname = response.content.strip().replace('"', '').replace('"', '')

            if len(nickname) <= 6:  # 绰号不要太长
                return nickname

        return None


# 使用示例
async def test_improved_naming():
    """测试改进的命名系统"""

    name_gen = ImprovedNameGenerator()

    # 生成不同类型的角色名字
    configs = [
        NameConfig(gender="male", character_type="主角", cultural_style="中式古典",
                   character_traits=["勇敢", "正义"]),
        NameConfig(gender="female", character_type="重要配角", cultural_style="中式古典",
                   character_traits=["聪明", "美丽"]),
        NameConfig(gender="male", character_type="反派", cultural_style="中式古典",
                   character_traits=["强大", "冷酷"]),
        NameConfig(gender="female", character_type="导师", cultural_style="中式古典",
                   character_traits=["智慧", "神秘"]),
        NameConfig(gender="any", character_type="配角", cultural_style="中式古典",
                   character_traits=["幽默", "忠诚"])
    ]

    print("生成的角色名字：")
    for i, config in enumerate(configs):
        name = await name_gen.generate_character_name(config)
        print(f"{i + 1}. {config.character_type}：{name} ({config.gender})")

    print(f"\n已使用的名字：{list(name_gen.used_names)}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_improved_naming())
