
# modules/plot/conflict_generator.py
"""
冲突生成器
生成各种类型的故事冲突
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
from core.base_tools import AsyncTool, ToolDefinition, ToolParameter
from core.llm_client import get_llm_service


class ConflictType(Enum):
    """冲突类型"""
    CHARACTER_VS_CHARACTER = "人物vs人物"
    CHARACTER_VS_SELF = "人物vs自我"
    CHARACTER_VS_SOCIETY = "人物vs社会"
    CHARACTER_VS_NATURE = "人物vs自然"
    CHARACTER_VS_TECHNOLOGY = "人物vs科技"
    CHARACTER_VS_SUPERNATURAL = "人物vs超自然"
    CHARACTER_VS_FATE = "人物vs命运"


@dataclass
class Conflict:
    """冲突"""
    id: str
    name: str
    type: str
    description: str
    severity: int  # 严重程度 1-10
    scope: str  # 范围：个人/局部/全局
    duration: str  # 持续时间：短期/中期/长期

    # 冲突要素
    protagonist: str  # 主要角色
    antagonist: str  # 对立面
    stakes: str  # 赌注
    obstacles: List[str]  # 障碍

    # 发展过程
    trigger: str  # 触发事件
    escalation: List[str]  # 升级过程
    climax: str  # 冲突高潮
    resolution_options: List[str]  # 解决方案

    # 影响
    character_impact: Dict[str, str]  # 对角色的影响
    plot_impact: str  # 对情节的影响
    theme_connection: List[str]  # 主题连接


class ConflictGenerator:
    """冲突生成器"""

    def __init__(self):
        self.llm_service = get_llm_service()

    async def generate_central_conflict(
        self,
        protagonist: str,
        antagonist: str,
        genre: str = "玄幻",
        theme: str = "成长"
    ) -> Conflict:
        """生成核心冲突"""

        conflict_data = await self._generate_conflict_data(
            "核心冲突", ConflictType.CHARACTER_VS_CHARACTER.value,
            protagonist, antagonist, genre, theme, severity=10
        )

        return Conflict(**conflict_data)

    async def generate_internal_conflict(
        self,
        character: str,
        personality_traits: List[str],
        background: Dict[str, Any]
    ) -> Conflict:
        """生成内心冲突"""

        conflict_data = await self._generate_conflict_data(
            "内心冲突", ConflictType.CHARACTER_VS_SELF.value,
            character, "内心的恐惧与欲望", "心理", "成长", severity=7
        )

        return Conflict(**conflict_data)

    async def generate_social_conflict(
        self,
        character: str,
        society_setting: Dict[str, Any],
        character_goals: List[str]
    ) -> Conflict:
        """生成社会冲突"""

        conflict_data = await self._generate_conflict_data(
            "社会冲突", ConflictType.CHARACTER_VS_SOCIETY.value,
            character, "社会制度", "社会", "正义", severity=8
        )

        return Conflict(**conflict_data)

    async def generate_conflicts_batch(
        self,
        story_outline: Dict[str, Any],
        count: int = 5
    ) -> List[Conflict]:
        """批量生成冲突"""

        conflicts = []

        # 生成核心冲突
        if story_outline.get("protagonist") and story_outline.get("antagonist"):
            central = await self.generate_central_conflict(
                story_outline["protagonist"],
                story_outline["antagonist"],
                story_outline.get("genre", "玄幻"),
                story_outline.get("theme", "成长")
            )
            conflicts.append(central)

        # 生成其他类型的冲突
        remaining_count = count - len(conflicts)
        for i in range(remaining_count):
            conflict_type = list(ConflictType)[i % len(ConflictType)]

            conflict_data = await self._generate_conflict_data(
                f"冲突{i + 1}", conflict_type.value,
                story_outline.get("protagonist", "主角"),
                f"对立面{i + 1}",
                story_outline.get("genre", "玄幻"),
                story_outline.get("theme", "成长"),
                severity=5 + (i % 5)
            )

            conflicts.append(Conflict(**conflict_data))

        return conflicts

    async def _generate_conflict_data(
        self,
        name: str,
        conflict_type: str,
        protagonist: str,
        antagonist: str,
        genre: str,
        theme: str,
        severity: int = 5
    ) -> Dict[str, Any]:
        """生成冲突数据"""

        return {
            "id": f"conflict_{name.lower().replace(' ', '_')}",
            "name": name,
            "type": conflict_type,
            "description": f"{protagonist}与{antagonist}之间的{conflict_type}",
            "severity": severity,
            "scope": "全局" if severity >= 8 else "局部",
            "duration": "长期" if severity >= 7 else "中期",
            "protagonist": protagonist,
            "antagonist": antagonist,
            "stakes": "重要的人或事物",
            "obstacles": ["实力差距", "信息不对称", "资源限制"],
            "trigger": "初次相遇或冲突事件",
            "escalation": ["小摩擦", "正面冲突", "全面对抗"],
            "climax": "决定性对决",
            "resolution_options": ["武力解决", "智慧化解", "牺牲妥协"],
            "character_impact": {
                protagonist: "获得成长",
                antagonist: "失败或转变"
            },
            "plot_impact": "推动故事发展",
            "theme_connection": [theme, "冲突与成长"]
        }


class ConflictGeneratorTool(AsyncTool):
    """冲突生成工具"""

    def __init__(self):
        super().__init__()
        self.generator = ConflictGenerator()

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="conflict_generator",
            description="生成故事冲突，包括核心冲突、内心冲突、社会冲突等",
            category="plot",
            parameters=[
                ToolParameter(
                    name="conflict_type",
                    type="string",
                    description="冲突类型：central/internal/social/batch",
                    required=True
                ),
                ToolParameter(
                    name="protagonist",
                    type="string",
                    description="主要角色",
                    required=False
                ),
                ToolParameter(
                    name="antagonist",
                    type="string",
                    description="对立角色",
                    required=False
                ),
                ToolParameter(
                    name="genre",
                    type="string",
                    description="故事类型",
                    required=False,
                    default="玄幻"
                ),
                ToolParameter(
                    name="theme",
                    type="string",
                    description="主题",
                    required=False,
                    default="成长"
                ),
                ToolParameter(
                    name="story_outline",
                    type="object",
                    description="故事大纲（用于批量生成）",
                    required=False
                ),
                ToolParameter(
                    name="count",
                    type="integer",
                    description="生成数量（批量模式）",
                    required=False,
                    default=5
                )
            ]
        )

    async def execute(self, parameters: Dict[str, Any],
                      context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行冲突生成"""

        conflict_type = parameters.get("conflict_type")

        if conflict_type == "central":
            conflict = await self.generator.generate_central_conflict(
                parameters.get("protagonist", "主角"),
                parameters.get("antagonist", "反派"),
                parameters.get("genre", "玄幻"),
                parameters.get("theme", "成长")
            )
            return {"conflict": asdict(conflict)}

        elif conflict_type == "batch":
            conflicts = await self.generator.generate_conflicts_batch(
                parameters.get("story_outline", {}),
                parameters.get("count", 5)
            )
            return {"conflicts": [asdict(c) for c in conflicts]}

        else:
            return {"error": "不支持的冲突类型"}

