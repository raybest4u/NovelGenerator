
# modules/tools/name_generator.py
"""
名称生成器
为角色、地点、功法、法宝等生成合适的名称
"""

import random
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from core.base_tools import AsyncTool, ToolDefinition, ToolParameter
from core.llm_client import get_llm_service
from config.settings import get_prompt_manager


@dataclass
class NameEntry:
    """名称条目"""
    name: str
    type: str  # character/place/technique/artifact/organization
    meaning: str  # 含义
    cultural_origin: str  # 文化来源
    sound_pattern: str  # 音韵特点
    alternative_forms: List[str]  # 变体形式


class NameGenerator:
    """名称生成器"""

    def __init__(self):
        self.llm_service = get_llm_service()
        self.prompt_manager = get_prompt_manager()
        self.name_databases = self._load_name_databases()

    async def generate_character_names(
        self,
        count: int = 5,
        gender: str = "any",
        cultural_style: str = "中式古典",
        character_traits: List[str] = None,
        avoid_names: List[str] = None
    ) -> List[NameEntry]:
        """生成角色名称"""

        prompt = self.prompt_manager.get_prompt(
            "tools",
            "character_names",
            count=count,
            gender=gender,
            style=cultural_style,
            traits=character_traits or [],
            avoid_list=avoid_names or []
        )

        response = await self.llm_service.generate_text(prompt)

        return self._parse_names_response(response.content, "character")

    async def generate_place_names(
        self,
        count: int = 5,
        place_type: str = "city",
        geographical_features: List[str] = None,
        cultural_style: str = "中式古典"
    ) -> List[NameEntry]:
        """生成地名"""

        prompt = self.prompt_manager.get_prompt(
            "tools",
            "place_names",
            count=count,
            place_type=place_type,
            features=geographical_features or [],
            style=cultural_style
        )

        response = await self.llm_service.generate_text(prompt)

        return self._parse_names_response(response.content, "place")

    async def generate_technique_names(
        self,
        count: int = 5,
        technique_type: str = "martial_art",
        power_level: str = "medium",
        element_affinity: str = "none"
    ) -> List[NameEntry]:
        """生成功法/技能名称"""

        prompt = self.prompt_manager.get_prompt(
            "tools",
            "technique_names",
            count=count,
            type=technique_type,
            level=power_level,
            element=element_affinity
        )

        response = await self.llm_service.generate_text(prompt)

        return self._parse_names_response(response.content, "technique")

    async def generate_artifact_names(
        self,
        count: int = 5,
        artifact_type: str = "weapon",
        rarity: str = "rare",
        material: str = "metal"
    ) -> List[NameEntry]:
        """生成法宝/装备名称"""

        prompt = self.prompt_manager.get_prompt(
            "tools",
            "artifact_names",
            count=count,
            type=artifact_type,
            rarity=rarity,
            material=material
        )

        response = await self.llm_service.generate_text(prompt)

        return self._parse_names_response(response.content, "artifact")

    async def generate_organization_names(
        self,
        count: int = 5,
        organization_type: str = "sect",
        alignment: str = "neutral",
        specialization: str = "general"
    ) -> List[NameEntry]:
        """生成组织/门派名称"""

        prompt = self.prompt_manager.get_prompt(
            "tools",
            "organization_names",
            count=count,
            type=organization_type,
            alignment=alignment,
            specialty=specialization
        )

        response = await self.llm_service.generate_text(prompt)

        return self._parse_names_response(response.content, "organization")

    def generate_random_name(
        self,
        name_type: str,
        style: str = "中式古典"
    ) -> NameEntry:
        """生成随机名称"""

        database = self.name_databases.get(name_type, {})
        style_names = database.get(style, [])

        if not style_names:
            # 使用默认名称
            default_names = {
                "character": ["李逍遥", "赵灵儿", "王小虎"],
                "place": ["青云城", "天山", "幽冥谷"],
                "technique": ["九阳神功", "凌波微步", "降龙十八掌"],
                "artifact": ["倚天剑", "屠龙刀", "玄铁重剑"],
                "organization": ["青云门", "天音寺", "鬼王宗"]
            }
            style_names = default_names.get(name_type, ["未命名"])

        selected_name = random.choice(style_names)

        return NameEntry(
            name=selected_name,
            type=name_type,
            meaning="待定义",
            cultural_origin=style,
            sound_pattern="双音节",
            alternative_forms=[]
        )

    def _parse_names_response(self, response: str, name_type: str) -> List[NameEntry]:
        """解析名称生成响应"""

        # 简单解析，实际项目中可以更复杂
        lines = [line.strip() for line in response.split('\n') if line.strip()]
        names = []

        for i, line in enumerate(lines[:5]):  # 最多取5个
            # 提取名称（去除序号和说明）
            name = line.split('.', 1)[-1].split('：', 1)[0].split('-', 1)[0].strip()

            names.append(NameEntry(
                name=name,
                type=name_type,
                meaning="由LLM生成",
                cultural_origin="中式古典",
                sound_pattern="双音节",
                alternative_forms=[]
            ))

        return names if names else [self.generate_random_name(name_type)]

    def _load_name_databases(self) -> Dict[str, Dict[str, List[str]]]:
        """加载名称数据库"""

        return {
            "character": {
                "中式古典": [
                    "李逍遥", "赵灵儿", "林月如", "王小虎", "苏媚",
                    "张无忌", "赵敏", "周芷若", "小昭", "殷离",
                    "萧峰", "段誉", "虚竹", "王语嫣", "阿朱",
                    "令狐冲", "任盈盈", "岳灵珊", "林平之", "东方不败"
                ],
                "现代风格": [
                    "陈浩", "李雪", "王强", "刘明", "张伟",
                    "赵丽", "孙涛", "周杰", "吴敏", "钱进"
                ]
            },
            "place": {
                "中式古典": [
                    "青云城", "天山派", "华山", "峨眉山", "武当山",
                    "少林寺", "神雕谷", "桃花岛", "光明顶", "黑木崖",
                    "蝴蝶谷", "绝情谷", "冰火岛", "灵鹫宫", "星宿海"
                ]
            },
            "technique": {
                "中式古典": [
                    "九阳神功", "乾坤大挪移", "太极拳", "降龙十八掌",
                    "凌波微步", "六脉神剑", "斗转星移", "化骨绵掌",
                    "九阴真经", "易筋经", "金钟罩", "铁布衫"
                ]
            },
            "artifact": {
                "中式古典": [
                    "倚天剑", "屠龙刀", "玄铁重剑", "君子剑", "淑女剑",
                    "碧血剑", "金蛇剑", "鸳鸯刀", "紫薇软剑", "木剑"
                ]
            },
            "organization": {
                "中式古典": [
                    "青云门", "天音寺", "鬼王宗", "合欢派", "焚香谷",
                    "华山派", "峨眉派", "武当派", "少林派", "丐帮"
                ]
            }
        }


class NameGeneratorTool(AsyncTool):
    """名称生成工具"""

    def __init__(self):
        super().__init__()
        self.generator = NameGenerator()

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="name_generator",
            description="为小说中的角色、地点、功法、法宝、组织等生成合适的名称",
            category="tools",
            parameters=[
                ToolParameter(
                    name="name_type",
                    type="string",
                    description="名称类型：character/place/technique/artifact/organization/random",
                    required=True
                ),
                ToolParameter(
                    name="count",
                    type="integer",
                    description="生成数量",
                    required=False,
                    default=5
                ),
                ToolParameter(
                    name="cultural_style",
                    type="string",
                    description="文化风格：中式古典/现代风格/西式幻想",
                    required=False,
                    default="中式古典"
                ),
                # 角色名称专用参数
                ToolParameter(
                    name="gender",
                    type="string",
                    description="性别：male/female/any",
                    required=False,
                    default="any"
                ),
                ToolParameter(
                    name="character_traits",
                    type="array",
                    description="角色特质",
                    required=False
                ),
                # 地名专用参数
                ToolParameter(
                    name="place_type",
                    type="string",
                    description="地点类型：city/mountain/sect/valley等",
                    required=False,
                    default="city"
                ),
                ToolParameter(
                    name="geographical_features",
                    type="array",
                    description="地理特征",
                    required=False
                ),
                # 功法名称专用参数
                ToolParameter(
                    name="technique_type",
                    type="string",
                    description="技能类型：martial_art/magic/cultivation",
                    required=False,
                    default="martial_art"
                ),
                ToolParameter(
                    name="power_level",
                    type="string",
                    description="威力等级：low/medium/high/legendary",
                    required=False,
                    default="medium"
                ),
                ToolParameter(
                    name="element_affinity",
                    type="string",
                    description="元素属性：fire/water/earth/air/none",
                    required=False,
                    default="none"
                ),
                # 法宝名称专用参数
                ToolParameter(
                    name="artifact_type",
                    type="string",
                    description="法宝类型：weapon/armor/accessory/pill",
                    required=False,
                    default="weapon"
                ),
                ToolParameter(
                    name="rarity",
                    type="string",
                    description="稀有度：common/rare/epic/legendary",
                    required=False,
                    default="rare"
                ),
                # 组织名称专用参数
                ToolParameter(
                    name="organization_type",
                    type="string",
                    description="组织类型：sect/guild/academy/empire",
                    required=False,
                    default="sect"
                ),
                ToolParameter(
                    name="alignment",
                    type="string",
                    description="阵营：good/neutral/evil",
                    required=False,
                    default="neutral"
                ),
                # 通用参数
                ToolParameter(
                    name="avoid_names",
                    type="array",
                    description="要避免的名称列表",
                    required=False
                )
            ],
            examples=[
                {
                    "parameters": {
                        "name_type": "character",
                        "count": 3,
                        "gender": "male",
                        "cultural_style": "中式古典"
                    },
                    "result": "生成3个男性角色名称"
                }
            ],
            tags=["name", "generation", "creative"]
        )

    async def execute(self, parameters: Dict[str, Any],
                      context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行名称生成"""

        name_type = parameters.get("name_type")
        count = parameters.get("count", 5)

        if name_type == "character":
            names = await self.generator.generate_character_names(
                count=count,
                gender=parameters.get("gender", "any"),
                cultural_style=parameters.get("cultural_style", "中式古典"),
                character_traits=parameters.get("character_traits"),
                avoid_names=parameters.get("avoid_names")
            )

        elif name_type == "place":
            names = await self.generator.generate_place_names(
                count=count,
                place_type=parameters.get("place_type", "city"),
                geographical_features=parameters.get("geographical_features"),
                cultural_style=parameters.get("cultural_style", "中式古典")
            )

        elif name_type == "technique":
            names = await self.generator.generate_technique_names(
                count=count,
                technique_type=parameters.get("technique_type", "martial_art"),
                power_level=parameters.get("power_level", "medium"),
                element_affinity=parameters.get("element_affinity", "none")
            )

        elif name_type == "artifact":
            names = await self.generator.generate_artifact_names(
                count=count,
                artifact_type=parameters.get("artifact_type", "weapon"),
                rarity=parameters.get("rarity", "rare"),
                material=parameters.get("material", "metal")
            )

        elif name_type == "organization":
            names = await self.generator.generate_organization_names(
                count=count,
                organization_type=parameters.get("organization_type", "sect"),
                alignment=parameters.get("alignment", "neutral"),
                specialization=parameters.get("specialization", "general")
            )

        elif name_type == "random":
            # 随机选择一个类型
            random_type = random.choice(
                ["character", "place", "technique", "artifact", "organization"])
            name = self.generator.generate_random_name(
                random_type,
                parameters.get("cultural_style", "中式古典")
            )
            names = [name]

        else:
            return {"error": "不支持的名称类型"}

        return {
            "names": [
                {
                    "name": name.name,
                    "type": name.type,
                    "meaning": name.meaning,
                    "cultural_origin": name.cultural_origin,
                    "sound_pattern": name.sound_pattern,
                    "alternative_forms": name.alternative_forms
                }
                for name in names
            ],
            "generation_info": {
                "name_type": name_type,
                "count": len(names),
                "cultural_style": parameters.get("cultural_style", "中式古典")
            }
        }

