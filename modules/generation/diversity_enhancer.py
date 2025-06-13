# modules/generation/diversity_enhancer.py
"""
多样性增强模块
通过多种策略确保生成内容的差异化
"""

import random
import hashlib
import json
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from core.base_tools import AsyncTool, ToolDefinition, ToolParameter
from core.llm_client import get_llm_service
from config.settings import get_prompt_manager


@dataclass
class DiversityConstraints:
    """多样性约束"""
    avoid_characters: Set[str] = None  # 避免的角色名
    avoid_plots: Set[str] = None  # 避免的情节
    avoid_settings: Set[str] = None  # 避免的设定
    avoid_structures: Set[str] = None  # 避免的结构
    required_uniqueness: float = 0.7  # 要求的独特性(0-1)
    theme_constraints: Dict[str, Any] = None  # 主题约束


@dataclass
class GenerationVariant:
    """生成变体"""
    variant_id: str
    title: str
    description: str
    story_structure: str
    character_archetype: str
    world_flavor: str
    conflict_type: str
    tone: str
    pacing: str
    unique_elements: List[str]


class DiversityEnhancer:
    """多样性增强器"""

    def __init__(self):
        self.llm_service = get_llm_service()
        self.prompt_manager = get_prompt_manager()

        # 历史记录
        self.generation_history: List[Dict[str, Any]] = []
        self.character_history: Set[str] = set()
        self.plot_history: Set[str] = set()
        self.setting_history: Set[str] = set()

        # 变体库
        self.story_structures = self._load_story_structures()
        self.character_archetypes = self._load_character_archetypes()
        self.world_flavors = self._load_world_flavors()
        self.conflict_types = self._load_conflict_types()
        self.tones = self._load_tones()
        self.unique_elements = self._load_unique_elements()

    def _load_story_structures(self) -> Dict[str, Dict[str, Any]]:
        """加载多样化的故事结构"""
        return {
            "英雄之旅": {
                "acts": ["启程", "历险", "归来"],
                "key_points": ["召唤", "拒绝", "导师", "跨越门槛", "试炼", "启示", "变革", "回归"],
                "character_arc": "从平凡到英雄",
                "pacing": "渐进式",
                "themes": ["成长", "勇气", "自我发现"]
            },
            "多线并行": {
                "acts": ["建立", "交织", "汇聚"],
                "key_points": ["角色介绍", "情节分支", "交叉点", "冲突升级", "全面爆发",
                               "共同目标"],
                "character_arc": "群像式发展",
                "pacing": "交替推进",
                "themes": ["命运", "羁绊", "团结"]
            },
            "时间循环": {
                "acts": ["困境", "探索", "突破"],
                "key_points": ["初次循环", "发现规律", "尝试改变", "关键领悟", "最终突破"],
                "character_arc": "在重复中成长",
                "pacing": "螺旋上升",
                "themes": ["宿命", "改变", "顿悟"]
            },
            "双重身份": {
                "acts": ["伪装", "暴露", "统一"],
                "key_points": ["身份建立", "危机出现", "身份冲突", "真相揭示", "身份整合"],
                "character_arc": "寻找真我",
                "pacing": "悬疑推进",
                "themes": ["身份", "真实", "自我接纳"]
            },
            "逆转重构": {
                "acts": ["表象", "质疑", "真相"],
                "key_points": ["初始印象", "异常发现", "深入调查", "真相震惊", "重新认知"],
                "character_arc": "认知颠覆",
                "pacing": "层层剥离",
                "themes": ["真相", "欺骗", "认知"]
            },
            "spiral_ascension": {
                "acts": ["起点", "螺旋", "超越"],
                "key_points": ["基础建立", "重复挑战", "每次提升", "质变时刻", "新境界"],
                "character_arc": "螺旋式上升",
                "pacing": "递增强化",
                "themes": ["修炼", "突破", "超越"]
            }
        }

    def _load_character_archetypes(self) -> Dict[str, Dict[str, Any]]:
        """加载角色原型"""
        return {
            "不羁浪子": {
                "personality": ["自由", "叛逆", "魅力", "不拘小节"],
                "background": "游侠出身",
                "motivation": "追求自由",
                "conflict": "责任与自由",
                "growth": "学会承担"
            },
            "天才少年": {
                "personality": ["聪明", "骄傲", "孤独", "完美主义"],
                "background": "名门之后",
                "motivation": "证明自己",
                "conflict": "天赋与努力",
                "growth": "理解合作"
            },
            "复仇使者": {
                "personality": ["坚韧", "执着", "冷酷", "隐忍"],
                "background": "家族毁灭",
                "motivation": "复仇雪恨",
                "conflict": "复仇与救赎",
                "growth": "放下仇恨"
            },
            "迷茫探索者": {
                "personality": ["好奇", "迷惘", "勇敢", "善良"],
                "background": "普通出身",
                "motivation": "寻找意义",
                "conflict": "梦想与现实",
                "growth": "找到使命"
            },
            "隐世高人": {
                "personality": ["淡泊", "睿智", "神秘", "慈悲"],
                "background": "修炼有成",
                "motivation": "守护世界",
                "conflict": "介入与超脱",
                "growth": "传承使命"
            },
            "堕落天才": {
                "personality": ["扭曲", "聪明", "偏执", "悲观"],
                "background": "曾经光明",
                "motivation": "毁灭重建",
                "conflict": "救赎与沉沦",
                "growth": "重拾希望"
            }
        }

    def _load_world_flavors(self) -> Dict[str, Dict[str, Any]]:
        """加载世界风味"""
        return {
            "古典仙侠": {
                "setting": "古代中国风",
                "magic_system": "修仙体系",
                "aesthetics": "诗意优雅",
                "conflicts": "门派恩怨",
                "themes": ["修道", "长生", "超脱"]
            },
            "现代都市": {
                "setting": "现代城市",
                "magic_system": "异能觉醒",
                "aesthetics": "科技与神秘",
                "conflicts": "隐秘组织",
                "themes": ["觉醒", "秩序", "隐藏"]
            },
            "蒸汽朋克": {
                "setting": "工业革命时代",
                "magic_system": "机械与魔法",
                "aesthetics": "齿轮与蒸汽",
                "conflicts": "技术革命",
                "themes": ["进步", "传统", "革新"]
            },
            "末世废土": {
                "setting": "后末日世界",
                "magic_system": "变异与科技",
                "aesthetics": "荒凉绝望",
                "conflicts": "资源争夺",
                "themes": ["生存", "希望", "重建"]
            },
            "奇幻大陆": {
                "setting": "多种族大陆",
                "magic_system": "元素魔法",
                "aesthetics": "多元文化",
                "conflicts": "种族矛盾",
                "themes": ["和谐", "偏见", "团结"]
            }
        }

    def _load_conflict_types(self) -> Dict[str, Dict[str, Any]]:
        """加载冲突类型"""
        return {
            "权力斗争": {
                "nature": "政治冲突",
                "scale": "大规模",
                "duration": "长期",
                "resolution": "权力重新分配"
            },
            "生存危机": {
                "nature": "环境威胁",
                "scale": "全球性",
                "duration": "急迫",
                "resolution": "团结应对"
            },
            "身份认同": {
                "nature": "内心冲突",
                "scale": "个人",
                "duration": "持续",
                "resolution": "自我接纳"
            },
            "道德选择": {
                "nature": "价值观冲突",
                "scale": "中等",
                "duration": "关键时刻",
                "resolution": "价值确立"
            },
            "时间悖论": {
                "nature": "逻辑冲突",
                "scale": "概念性",
                "duration": "复杂",
                "resolution": "智慧解决"
            }
        }

    def _load_tones(self) -> List[str]:
        """加载叙述基调"""
        return [
            "轻松幽默", "严肃深沉", "神秘悬疑", "热血激昂",
            "温馨治愈", "黑暗沉重", "诗意浪漫", "紧张刺激",
            "哲思探索", "讽刺批判", "史诗宏大", "日常温馨"
        ]

    def _load_unique_elements(self) -> Dict[str, List[str]]:
        """加载独特元素"""
        return {
            "特殊设定": [
                "时间操控", "记忆交换", "梦境世界", "平行时空",
                "意识传输", "概率操控", "情感具象化", "思维共鸣"
            ],
            "特殊道具": [
                "时光沙漏", "记忆水晶", "命运罗盘", "心灵镜子",
                "愿望之书", "真实之眼", "灵魂天平", "因果链条"
            ],
            "特殊地点": [
                "倒流瀑布", "镜像森林", "重力异常区", "时间裂缝",
                "梦境交汇点", "记忆图书馆", "愿望许愿池", "命运交叉口"
            ],
            "特殊生物": [
                "时间龙", "梦境狐", "记忆鸟", "命运蝶",
                "愿望精灵", "真相之蛇", "预言猫头鹰", "因果乌鸦"
            ]
        }

    async def generate_diverse_variant(
        self,
        theme: str,
        constraints: DiversityConstraints = None
    ) -> GenerationVariant:
        """生成多样化变体"""

        constraints = constraints or DiversityConstraints()

        # 避免重复选择
        available_structures = [s for s in self.story_structures.keys()
                                if s not in (constraints.avoid_structures or set())]
        available_archetypes = [a for a in self.character_archetypes.keys()
                                if a not in (constraints.avoid_characters or set())]
        available_flavors = [f for f in self.world_flavors.keys()
                             if f not in (constraints.avoid_settings or set())]

        # 随机选择核心元素
        structure = random.choice(available_structures)
        archetype = random.choice(available_archetypes)
        flavor = random.choice(available_flavors)
        conflict = random.choice(list(self.conflict_types.keys()))
        tone = random.choice(self.tones)

        # 选择独特元素
        unique_elements = []
        for category, elements in self.unique_elements.items():
            unique_elements.append(random.choice(elements))

        # 生成变体标识
        variant_id = self._generate_variant_id(structure, archetype, flavor)

        # 生成描述性标题
        title = await self._generate_variant_title(theme, structure, archetype, flavor)

        # 生成详细描述
        description = await self._generate_variant_description(
            theme, structure, archetype, flavor, conflict, unique_elements
        )

        variant = GenerationVariant(
            variant_id=variant_id,
            title=title,
            description=description,
            story_structure=structure,
            character_archetype=archetype,
            world_flavor=flavor,
            conflict_type=conflict,
            tone=tone,
            pacing=self.story_structures[structure]["pacing"],
            unique_elements=unique_elements
        )

        # 记录生成历史
        self._record_generation(variant)

        return variant

    def _generate_variant_id(self, structure: str, archetype: str, flavor: str) -> str:
        """生成变体ID"""
        content = f"{structure}_{archetype}_{flavor}_{datetime.now().isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    async def _generate_variant_title(
        self,
        theme: str,
        structure: str,
        archetype: str,
        flavor: str
    ) -> str:
        """生成变体标题"""

        prompt = f"""
        基于以下元素创造一个独特的小说标题：

        主题：{theme}
        故事结构：{structure}
        角色原型：{archetype}
        世界风味：{flavor}

        要求：
        1. 标题要体现主题特色
        2. 暗示故事的独特性
        3. 具有吸引力和记忆点
        4. 4-8个字最佳

        请直接返回一个标题：
        """

        response = await self.llm_service.generate_text(prompt, temperature=0.8)
        return response.content.strip().replace('"', '').replace('《', '').replace('》', '')

    async def _generate_variant_description(
        self,
        theme: str,
        structure: str,
        archetype: str,
        flavor: str,
        conflict: str,
        unique_elements: List[str]
    ) -> str:
        """生成变体描述"""

        prompt = f"""
        基于以下元素创造一个独特的故事概念：

        主题：{theme}
        故事结构：{structure} - {self.story_structures[structure]}
        角色原型：{archetype} - {self.character_archetypes[archetype]}
        世界风味：{flavor} - {self.world_flavors[flavor]}
        主要冲突：{conflict} - {self.conflict_types[conflict]}
        独特元素：{unique_elements}

        请创造一个200字左右的故事概念描述，要求：
        1. 融合所有给定元素
        2. 展现独特性和创新性
        3. 具有吸引力和可读性
        4. 暗示主要情节走向

        请直接返回描述内容：
        """

        response = await self.llm_service.generate_text(prompt, temperature=0.9)
        return response.content.strip()

    def _record_generation(self, variant: GenerationVariant):
        """记录生成历史"""
        self.generation_history.append({
            "timestamp": datetime.now(),
            "variant_id": variant.variant_id,
            "elements": {
                "structure": variant.story_structure,
                "archetype": variant.character_archetype,
                "flavor": variant.world_flavor,
                "conflict": variant.conflict_type
            }
        })

        # 限制历史记录数量
        if len(self.generation_history) > 100:
            self.generation_history = self.generation_history[-50:]

    def analyze_diversity(self, recent_count: int = 10) -> Dict[str, Any]:
        """分析最近生成内容的多样性"""
        if len(self.generation_history) < recent_count:
            recent_count = len(self.generation_history)

        recent_generations = self.generation_history[-recent_count:]

        # 统计各元素的使用频率
        structure_freq = {}
        archetype_freq = {}
        flavor_freq = {}
        conflict_freq = {}

        for gen in recent_generations:
            elements = gen["elements"]
            structure_freq[elements["structure"]] = structure_freq.get(elements["structure"], 0) + 1
            archetype_freq[elements["archetype"]] = archetype_freq.get(elements["archetype"], 0) + 1
            flavor_freq[elements["flavor"]] = flavor_freq.get(elements["flavor"], 0) + 1
            conflict_freq[elements["conflict"]] = conflict_freq.get(elements["conflict"], 0) + 1

        # 计算多样性得分
        diversity_score = self._calculate_diversity_score([
            structure_freq, archetype_freq, flavor_freq, conflict_freq
        ])

        return {
            "diversity_score": diversity_score,
            "recent_count": recent_count,
            "frequency_analysis": {
                "structures": structure_freq,
                "archetypes": archetype_freq,
                "flavors": flavor_freq,
                "conflicts": conflict_freq
            },
            "recommendations": self._generate_diversity_recommendations(
                structure_freq, archetype_freq, flavor_freq, conflict_freq
            )
        }

    def _calculate_diversity_score(self, frequency_dicts: List[Dict[str, int]]) -> float:
        """计算多样性得分"""
        total_score = 0
        for freq_dict in frequency_dicts:
            if not freq_dict:
                continue

            total_uses = sum(freq_dict.values())
            unique_elements = len(freq_dict)

            # 计算熵值作为多样性指标
            entropy = 0
            for count in freq_dict.values():
                if count > 0:
                    p = count / total_uses
                    entropy -= p * (p.bit_length() - 1) if p > 0 else 0

            # 归一化到0-1
            max_entropy = (unique_elements.bit_length() - 1) if unique_elements > 1 else 0
            normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
            total_score += normalized_entropy

        return total_score / len(frequency_dicts)

    def _generate_diversity_recommendations(
        self,
        structure_freq: Dict[str, int],
        archetype_freq: Dict[str, int],
        flavor_freq: Dict[str, int],
        conflict_freq: Dict[str, int]
    ) -> List[str]:
        """生成多样性建议"""
        recommendations = []

        # 检查使用频率过高的元素
        all_freqs = {
            "故事结构": structure_freq,
            "角色原型": archetype_freq,
            "世界风味": flavor_freq,
            "冲突类型": conflict_freq
        }

        for category, freq_dict in all_freqs.items():
            if freq_dict:
                max_freq = max(freq_dict.values())
                total_uses = sum(freq_dict.values())

                if max_freq / total_uses > 0.5:  # 超过50%使用同一元素
                    overused = [k for k, v in freq_dict.items() if v == max_freq][0]
                    recommendations.append(f"建议减少使用{category}中的'{overused}'，尝试其他选项")

        # 检查未使用的元素
        all_structures = set(self.story_structures.keys())
        used_structures = set(structure_freq.keys())
        unused_structures = all_structures - used_structures

        if unused_structures:
            recommendations.append(
                f"建议尝试这些未使用的故事结构：{', '.join(list(unused_structures)[:3])}")

        return recommendations

    def get_avoidance_constraints(self, recent_count: int = 5) -> DiversityConstraints:
        """获取避免重复的约束条件"""
        if len(self.generation_history) < recent_count:
            recent_count = len(self.generation_history)

        recent_generations = self.generation_history[-recent_count:]

        avoid_structures = set()
        avoid_archetypes = set()
        avoid_flavors = set()
        avoid_conflicts = set()

        for gen in recent_generations:
            elements = gen["elements"]
            avoid_structures.add(elements["structure"])
            avoid_archetypes.add(elements["archetype"])
            avoid_flavors.add(elements["flavor"])
            avoid_conflicts.add(elements["conflict"])

        return DiversityConstraints(
            avoid_characters=avoid_archetypes,
            avoid_plots=avoid_conflicts,
            avoid_settings=avoid_flavors,
            avoid_structures=avoid_structures,
            required_uniqueness=0.8
        )


class DiversityEnhancerTool(AsyncTool):
    """多样性增强工具"""

    def __init__(self):
        super().__init__()
        self.enhancer = DiversityEnhancer()

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="diversity_enhancer",
            description="增强生成内容的多样性，避免重复和相似",
            category="generation",
            parameters=[
                ToolParameter(
                    name="action",
                    type="string",
                    description="操作类型：generate_variant/analyze_diversity/get_constraints",
                    required=True
                ),
                ToolParameter(
                    name="theme",
                    type="string",
                    description="故事主题",
                    required=False
                ),
                ToolParameter(
                    name="avoid_elements",
                    type="object",
                    description="要避免的元素",
                    required=False
                ),
                ToolParameter(
                    name="recent_count",
                    type="integer",
                    description="分析最近的生成数量",
                    required=False,
                    default=10
                )
            ]
        )

    async def execute(self, parameters: Dict[str, Any],
                      context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行多样性增强"""

        action = parameters.get("action")

        if action == "generate_variant":
            theme = parameters.get("theme", "修仙")
            avoid_elements = parameters.get("avoid_elements", {})

            constraints = DiversityConstraints(
                avoid_structures=set(avoid_elements.get("structures", [])),
                avoid_characters=set(avoid_elements.get("archetypes", [])),
                avoid_settings=set(avoid_elements.get("flavors", [])),
                avoid_plots=set(avoid_elements.get("conflicts", []))
            )

            variant = await self.enhancer.generate_diverse_variant(theme, constraints)

            return {
                "variant": asdict(variant),
                "generation_info": {
                    "theme": theme,
                    "constraints_applied": bool(avoid_elements)
                }
            }

        elif action == "analyze_diversity":
            recent_count = parameters.get("recent_count", 10)
            analysis = self.enhancer.analyze_diversity(recent_count)

            return {
                "diversity_analysis": analysis
            }

        elif action == "get_constraints":
            recent_count = parameters.get("recent_count", 5)
            constraints = self.enhancer.get_avoidance_constraints(recent_count)

            return {
                "avoidance_constraints": {
                    "avoid_structures": list(constraints.avoid_structures or []),
                    "avoid_archetypes": list(constraints.avoid_characters or []),
                    "avoid_flavors": list(constraints.avoid_settings or []),
                    "avoid_conflicts": list(constraints.avoid_plots or [])
                }
            }

        else:
            return {"error": "不支持的操作类型"}


# 示例使用
if __name__ == "__main__":
    import asyncio


    async def test_diversity():
        enhancer = DiversityEnhancer()

        # 生成多个变体
        variants = []
        for i in range(5):
            # 获取避免约束
            constraints = enhancer.get_avoidance_constraints(recent_count=3)

            # 生成新变体
            variant = await enhancer.generate_diverse_variant("修仙", constraints)
            variants.append(variant)

            print(f"变体 {i + 1}:")
            print(f"  标题: {variant.title}")
            print(f"  结构: {variant.story_structure}")
            print(f"  原型: {variant.character_archetype}")
            print(f"  风味: {variant.world_flavor}")
            print(f"  描述: {variant.description[:100]}...")
            print()

        # 分析多样性
        analysis = enhancer.analyze_diversity()
        print(f"多样性得分: {analysis['diversity_score']:.2f}")
        print("建议:", analysis['recommendations'])


    asyncio.run(test_diversity())
