
# modules/tools/consistency_checker.py
"""
一致性检查器
检查小说中的各种一致性问题
"""

from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, asdict
from core.base_tools import AsyncTool, ToolDefinition, ToolParameter
from core.llm_client import get_llm_service
from modules.tools import NameGeneratorTool, TimelineManagerTool


@dataclass
class ConsistencyIssue:
    """一致性问题"""
    id: str
    type: str  # character/plot/world/timeline/logic
    severity: str  # low/medium/high/critical
    description: str
    location: str  # 位置描述
    suggestions: List[str]  # 修复建议
    related_elements: List[str]  # 相关元素


@dataclass
class ConsistencyReport:
    """一致性报告"""
    overall_score: float  # 总体一致性评分 0-100
    issue_count: int
    issues_by_type: Dict[str, int]
    issues_by_severity: Dict[str, int]
    issues: List[ConsistencyIssue]
    recommendations: List[str]


class ConsistencyChecker:
    """一致性检查器"""

    def __init__(self):
        self.llm_service = get_llm_service()
        self.character_registry: Dict[str, Dict] = {}
        self.world_facts: Dict[str, Any] = {}
        self.timeline_events: List[Dict] = []

    async def check_full_consistency(
        self,
        story_data: Dict[str, Any]
    ) -> ConsistencyReport:
        """进行全面一致性检查"""

        issues = []

        # 提取数据
        self._extract_story_elements(story_data)

        # 各类检查
        character_issues = await self._check_character_consistency()
        plot_issues = await self._check_plot_consistency(story_data)
        world_issues = await self._check_world_consistency()
        timeline_issues = await self._check_timeline_consistency()
        logic_issues = await self._check_logic_consistency(story_data)

        issues.extend(character_issues)
        issues.extend(plot_issues)
        issues.extend(world_issues)
        issues.extend(timeline_issues)
        issues.extend(logic_issues)

        return self._generate_report(issues)

    async def check_character_consistency(
        self,
        characters: List[Dict[str, Any]]
    ) -> List[ConsistencyIssue]:
        """检查角色一致性"""

        issues = []

        for character in characters:
            self.character_registry[character.get("name", "")] = character

        return await self._check_character_consistency()

    async def check_world_consistency(
        self,
        world_setting: Dict[str, Any]
    ) -> List[ConsistencyIssue]:
        """检查世界观一致性"""

        self.world_facts = world_setting
        return await self._check_world_consistency()

    async def check_chapter_consistency(
        self,
        chapter: Dict[str, Any],
        story_context: Dict[str, Any]
    ) -> List[ConsistencyIssue]:
        """检查单章一致性"""

        issues = []

        # 检查角色表现一致性
        characters_in_chapter = chapter.get("character_focus", [])
        for char_name in characters_in_chapter:
            if char_name in self.character_registry:
                char_issues = await self._check_character_in_chapter(
                    char_name, chapter, story_context
                )
                issues.extend(char_issues)

        # 检查情节逻辑
        plot_issues = await self._check_chapter_plot_logic(chapter, story_context)
        issues.extend(plot_issues)

        return issues

    def _extract_story_elements(self, story_data: Dict[str, Any]):
        """提取故事元素"""

        # 提取角色信息
        characters = story_data.get("characters", [])
        for char in characters:
            if isinstance(char, dict):
                self.character_registry[char.get("name", "")] = char

        # 提取世界设定
        self.world_facts = story_data.get("world_setting", {})

        # 提取时间线事件
        timelines = story_data.get("timelines", {})
        for timeline in timelines.values():
            if isinstance(timeline, dict):
                self.timeline_events.extend(timeline.get("events", []))

    async def _check_character_consistency(self) -> List[ConsistencyIssue]:
        """检查角色一致性"""

        issues = []

        for char_name, character in self.character_registry.items():
            # 检查角色信息完整性
            required_fields = ["name", "appearance", "personality", "background", "abilities"]
            missing_fields = [field for field in required_fields
                              if field not in character or not character[field]]

            if missing_fields:
                issues.append(ConsistencyIssue(
                    id=f"char_incomplete_{char_name}",
                    type="character",
                    severity="medium",
                    description=f"角色{char_name}缺少必要信息：{', '.join(missing_fields)}",
                    location=f"角色定义",
                    suggestions=[f"补充{char_name}的{field}信息" for field in missing_fields],
                    related_elements=[char_name]
                ))

            # 检查角色能力与设定的一致性
            abilities = character.get("abilities", {})
            power_level = abilities.get("power_level", "")

            if power_level and not self._validate_power_level(power_level):
                issues.append(ConsistencyIssue(
                    id=f"char_power_{char_name}",
                    type="character",
                    severity="high",
                    description=f"角色{char_name}的实力等级{power_level}不符合体系设定",
                    location=f"角色能力定义",
                    suggestions=[f"调整{char_name}的实力等级"],
                    related_elements=[char_name, "power_system"]
                ))

        return issues

    async def _check_plot_consistency(self, story_data: Dict[str, Any]) -> List[ConsistencyIssue]:
        """检查情节一致性"""

        issues = []

        outline = story_data.get("story_outline", {})
        plot_points = outline.get("plot_points", [])

        # 检查情节点逻辑顺序
        for i, plot_point in enumerate(plot_points[:-1]):
            current_outcomes = plot_point.get("outcomes", [])
            next_prerequisites = plot_points[i + 1].get("prerequisites", [])

            # 检查前后情节点的逻辑连接
            if not self._check_plot_connection(current_outcomes, next_prerequisites):
                issues.append(ConsistencyIssue(
                    id=f"plot_connection_{i}",
                    type="plot",
                    severity="high",
                    description=f"情节点{plot_point.get('name', '')}与下一个情节点缺乏逻辑连接",
                    location=f"情节点{i}-{i + 1}",
                    suggestions=["添加过渡情节", "调整情节顺序"],
                    related_elements=[plot_point.get("id", ""), plot_points[i + 1].get("id", "")]
                ))

        return issues

    async def _check_world_consistency(self) -> List[ConsistencyIssue]:
        """检查世界观一致性"""

        issues = []

        # 检查魔法体系一致性
        magic_system = self.world_facts.get("magic_system", {})
        if magic_system:
            magic_issues = await self._check_magic_system_consistency(magic_system)
            issues.extend(magic_issues)

        # 检查地理一致性
        geography = self.world_facts.get("geography", {})
        if geography:
            geo_issues = await self._check_geography_consistency(geography)
            issues.extend(geo_issues)

        return issues

    async def _check_timeline_consistency(self) -> List[ConsistencyIssue]:
        """检查时间线一致性"""

        issues = []

        # 检查事件时间冲突
        for i, event1 in enumerate(self.timeline_events):
            for event2 in self.timeline_events[i + 1:]:
                if self._has_timeline_conflict(event1, event2):
                    issues.append(ConsistencyIssue(
                        id=f"timeline_conflict_{event1.get('id', '')}_{event2.get('id', '')}",
                        type="timeline",
                        severity="critical",
                        description=f"事件{event1.get('name', '')}与{event2.get('name', '')}存在时间冲突",
                        location="时间线",
                        suggestions=["调整事件时间", "分离冲突角色"],
                        related_elements=[event1.get("id", ""), event2.get("id", "")]
                    ))

        return issues

    async def _check_logic_consistency(self, story_data: Dict[str, Any]) -> List[ConsistencyIssue]:
        """检查逻辑一致性"""

        issues = []

        # 使用LLM检查复杂逻辑问题
        prompt = f"""
        请分析以下小说设定的逻辑一致性，找出可能的问题：

        故事大纲：{story_data.get('story_outline', {})}
        角色设定：{list(self.character_registry.keys())}
        世界设定：{self.world_facts}

        请识别以下类型的逻辑问题：
        1. 角色动机与行为不符
        2. 情节发展不合理
        3. 世界规则矛盾
        4. 因果关系错误

        请以简洁的格式列出发现的问题。
        """

        response = await self.llm_service.generate_text(prompt, temperature=0.3)

        # 解析LLM响应中的逻辑问题
        logic_issues = self._parse_logic_issues(response.content)
        issues.extend(logic_issues)

        return issues

    async def _check_character_in_chapter(
        self,
        char_name: str,
        chapter: Dict[str, Any],
        story_context: Dict[str, Any]
    ) -> List[ConsistencyIssue]:
        """检查角色在章节中的一致性"""

        issues = []

        character = self.character_registry.get(char_name, {})
        if not character:
            return issues

        # 检查角色行为是否符合性格
        personality = character.get("personality", {})
        core_traits = personality.get("core_traits", [])

        # 这里可以添加更复杂的行为分析逻辑

        return issues

    async def _check_chapter_plot_logic(
        self,
        chapter: Dict[str, Any],
        story_context: Dict[str, Any]
    ) -> List[ConsistencyIssue]:
        """检查章节情节逻辑"""

        issues = []

        # 检查章节内事件的因果关系
        key_events = chapter.get("key_events", [])

        # 这里可以添加更多的情节逻辑检查

        return issues

    async def _check_magic_system_consistency(self, magic_system: Dict[str, Any]) -> List[
        ConsistencyIssue]:
        """检查魔法体系一致性"""

        issues = []

        power_levels = magic_system.get("power_levels", [])
        if len(power_levels) < 3:
            issues.append(ConsistencyIssue(
                id="magic_levels_insufficient",
                type="world",
                severity="medium",
                description="魔法体系的实力等级层次不够丰富",
                location="魔法体系定义",
                suggestions=["增加更多实力等级", "细化等级差异"],
                related_elements=["magic_system"]
            ))

        return issues

    async def _check_geography_consistency(self, geography: Dict[str, Any]) -> List[
        ConsistencyIssue]:
        """检查地理一致性"""

        issues = []

        # 检查地理要素的逻辑性
        continents = geography.get("continents", [])
        climate_zones = geography.get("climate_zones", [])

        if len(continents) > 0 and len(climate_zones) == 0:
            issues.append(ConsistencyIssue(
                id="geography_climate_missing",
                type="world",
                severity="low",
                description="定义了大陆但缺少气候带信息",
                location="地理设定",
                suggestions=["添加气候带描述"],
                related_elements=["geography"]
            ))

        return issues

    def _validate_power_level(self, power_level: str) -> bool:
        """验证实力等级是否合法"""

        valid_levels = [
            "凡人", "炼气期", "筑基期", "金丹期", "元婴期",
            "化神期", "炼虚期", "合体期", "大乘期", "渡劫期", "仙人"
        ]

        return power_level in valid_levels

    def _check_plot_connection(self, outcomes: List[str], prerequisites: List[str]) -> bool:
        """检查情节点连接"""

        # 简单检查：如果有共同元素则认为有连接
        return len(set(outcomes) & set(prerequisites)) > 0

    def _has_timeline_conflict(self, event1: Dict[str, Any], event2: Dict[str, Any]) -> bool:
        """检查时间线冲突"""

        # 检查同一角色在同一时间的冲突
        chars1 = set(event1.get("characters_involved", []))
        chars2 = set(event2.get("characters_involved", []))

        if chars1 & chars2:  # 有共同角色
            time1 = event1.get("timestamp", "")
            time2 = event2.get("timestamp", "")
            if time1 == time2:  # 同一时间
                return True

        return False

    def _parse_logic_issues(self, llm_response: str) -> List[ConsistencyIssue]:
        """解析LLM响应中的逻辑问题"""

        issues = []
        lines = llm_response.strip().split('\n')

        for i, line in enumerate(lines):
            if line.strip() and ('问题' in line or '矛盾' in line or '不合理' in line):
                issues.append(ConsistencyIssue(
                    id=f"logic_issue_{i}",
                    type="logic",
                    severity="medium",
                    description=line.strip(),
                    location="故事逻辑",
                    suggestions=["重新审视相关设定", "调整情节逻辑"],
                    related_elements=["story_logic"]
                ))

        return issues

    def _generate_report(self, issues: List[ConsistencyIssue]) -> ConsistencyReport:
        """生成一致性报告"""

        # 计算总体评分
        total_severity_score = sum(self._severity_to_score(issue.severity) for issue in issues)
        max_possible_score = len(issues) * 10 if issues else 1
        overall_score = max(0, 100 - (total_severity_score / max_possible_score) * 100)

        # 统计问题类型
        issues_by_type = {}
        issues_by_severity = {}

        for issue in issues:
            issues_by_type[issue.type] = issues_by_type.get(issue.type, 0) + 1
            issues_by_severity[issue.severity] = issues_by_severity.get(issue.severity, 0) + 1

        # 生成建议
        recommendations = self._generate_recommendations(issues)

        return ConsistencyReport(
            overall_score=overall_score,
            issue_count=len(issues),
            issues_by_type=issues_by_type,
            issues_by_severity=issues_by_severity,
            issues=issues,
            recommendations=recommendations
        )

    def _severity_to_score(self, severity: str) -> int:
        """严重程度转分数"""
        severity_map = {
            "low": 2,
            "medium": 5,
            "high": 8,
            "critical": 10
        }
        return severity_map.get(severity, 5)

    def _generate_recommendations(self, issues: List[ConsistencyIssue]) -> List[str]:
        """生成修复建议"""

        recommendations = []

        # 根据问题类型生成建议
        if any(issue.type == "character" for issue in issues):
            recommendations.append("完善角色设定，确保信息完整性")

        if any(issue.type == "plot" for issue in issues):
            recommendations.append("检查情节逻辑，加强前后连接")

        if any(issue.type == "world" for issue in issues):
            recommendations.append("统一世界观设定，避免内部矛盾")

        if any(issue.type == "timeline" for issue in issues):
            recommendations.append("整理时间线，解决时间冲突")

        if any(issue.severity == "critical" for issue in issues):
            recommendations.append("优先处理严重问题，确保故事可读性")

        return recommendations


class ConsistencyCheckerTool(AsyncTool):
    """一致性检查工具"""

    def __init__(self):
        super().__init__()
        self.checker = ConsistencyChecker()

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="consistency_checker",
            description="检查小说的各种一致性问题，包括角色、情节、世界观、时间线等",
            category="tools",
            parameters=[
                ToolParameter(
                    name="check_type",
                    type="string",
                    description="检查类型：full/character/world/chapter/plot/timeline",
                    required=True
                ),
                ToolParameter(
                    name="story_data",
                    type="object",
                    description="完整故事数据（全面检查用）",
                    required=False
                ),
                ToolParameter(
                    name="characters",
                    type="array",
                    description="角色列表（角色检查用）",
                    required=False
                ),
                ToolParameter(
                    name="world_setting",
                    type="object",
                    description="世界设定（世界观检查用）",
                    required=False
                ),
                ToolParameter(
                    name="chapter",
                    type="object",
                    description="章节信息（章节检查用）",
                    required=False
                ),
                ToolParameter(
                    name="story_context",
                    type="object",
                    description="故事上下文（章节检查用）",
                    required=False
                )
            ],
            examples=[
                {
                    "parameters": {
                        "check_type": "full",
                        "story_data": {
                            "characters": [],
                            "world_setting": {},
                            "story_outline": {}
                        }
                    },
                    "result": "完整的一致性检查报告"
                }
            ],
            tags=["consistency", "quality", "validation"]
        )

    async def execute(self, parameters: Dict[str, Any],
                      context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行一致性检查"""

        check_type = parameters.get("check_type")

        if check_type == "full":
            report = await self.checker.check_full_consistency(
                parameters.get("story_data", {})
            )
            return {"consistency_report": asdict(report)}

        elif check_type == "character":
            issues = await self.checker.check_character_consistency(
                parameters.get("characters", [])
            )
            return {"character_issues": [asdict(issue) for issue in issues]}

        elif check_type == "world":
            issues = await self.checker.check_world_consistency(
                parameters.get("world_setting", {})
            )
            return {"world_issues": [asdict(issue) for issue in issues]}

        elif check_type == "chapter":
            issues = await self.checker.check_chapter_consistency(
                parameters.get("chapter", {}),
                parameters.get("story_context", {})
            )
            return {"chapter_issues": [asdict(issue) for issue in issues]}

        else:
            return {"error": "不支持的检查类型"}


# 注册所有工具
def register_tools():
    """注册所有辅助工具"""
    from core.base_tools import get_tool_registry

    registry = get_tool_registry()

    registry.register(NameGeneratorTool())
    registry.register(TimelineManagerTool())
    registry.register(ConsistencyCheckerTool())


if __name__ == "__main__":
    register_tools()
    print("辅助工具已注册")
