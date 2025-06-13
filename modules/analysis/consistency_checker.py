# modules/analysis/consistency_checker.py
"""
一致性检查器
检查小说中的各种一致性问题
"""

from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, asdict
from core.base_tools import AsyncTool, ToolDefinition, ToolParameter
from core.llm_client import get_llm_service


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
            required_fields = ["name", "appearance", "personality", "background"]
            missing_fields = [field for field in required_fields if not character.get(field)]

            if missing_fields:
                issues.append(ConsistencyIssue(
                    id=f"char_{char_name}_missing",
                    type="character",
                    severity="medium",
                    description=f"角色{char_name}缺少必要信息",
                    location=f"角色设定-{char_name}",
                    suggestions=[f"补充{field}信息" for field in missing_fields],
                    related_elements=[char_name]
                ))

            # 检查角色名称重复
            similar_names = self._find_similar_names(char_name)
            if similar_names:
                issues.append(ConsistencyIssue(
                    id=f"char_{char_name}_similar",
                    type="character",
                    severity="low",
                    description=f"角色{char_name}与其他角色名称相似",
                    location=f"角色设定-{char_name}",
                    suggestions=["考虑重新命名以避免混淆"],
                    related_elements=[char_name] + similar_names
                ))

        return issues

    async def _check_plot_consistency(self, story_data: Dict[str, Any]) -> List[ConsistencyIssue]:
        """检查情节一致性"""

        issues = []

        # 检查故事大纲
        outline = story_data.get("outline", {})
        if not outline:
            issues.append(ConsistencyIssue(
                id="plot_no_outline",
                type="plot",
                severity="high",
                description="缺少故事大纲",
                location="故事结构",
                suggestions=["创建详细的故事大纲"],
                related_elements=["story_structure"]
            ))

        # 检查章节连贯性
        chapters = story_data.get("chapters", [])
        if len(chapters) > 1:
            plot_issues = await self._check_chapter_connections(chapters)
            issues.extend(plot_issues)

        return issues

    async def _check_world_consistency(self) -> List[ConsistencyIssue]:
        """检查世界观一致性"""
        issues = []

        # 检查世界设定完整性
        required_world_elements = ["geography", "culture", "power_system", "history"]
        missing_elements = [elem for elem in required_world_elements if
                            not self.world_facts.get(elem)]

        if missing_elements:
            issues.append(ConsistencyIssue(
                id="world_incomplete",
                type="world",
                severity="medium",
                description="世界设定不完整",
                location="世界观设定",
                suggestions=[f"补充{elem}相关设定" for elem in missing_elements],
                related_elements=missing_elements
            ))

        # 检查世界设定内部一致性
        power_system = self.world_facts.get("power_system", {})
        if power_system:
            # 检查力量体系的逻辑一致性
            levels = power_system.get("levels", [])
            if len(levels) < 3:
                issues.append(ConsistencyIssue(
                    id="power_system_simple",
                    type="world",
                    severity="low",
                    description="力量体系层级过于简单",
                    location="力量体系设定",
                    suggestions=["增加更多力量层级和详细描述"],
                    related_elements=["power_system"]
                ))

        return issues

    async def _check_timeline_consistency(self) -> List[ConsistencyIssue]:
        """检查时间线一致性"""
        issues = []

        if not self.timeline_events:
            return issues

        # 按时间排序事件
        sorted_events = sorted(self.timeline_events,
                              key=lambda x: x.get("timestamp", 0))

        # 检查事件逻辑顺序
        for i in range(1, len(sorted_events)):
            current_event = sorted_events[i]
            previous_event = sorted_events[i-1]

            # 检查是否有时间冲突
            if current_event.get("timestamp", 0) <= previous_event.get("timestamp", 0):
                issues.append(ConsistencyIssue(
                    id=f"timeline_conflict_{i}",
                    type="timeline",
                    severity="high",
                    description=f"时间线冲突：{current_event.get('name')} 与 {previous_event.get('name')}",
                    location="故事时间线",
                    suggestions=["调整事件时间顺序"],
                    related_elements=[current_event.get("name", ""), previous_event.get("name", "")]
                ))

        return issues


    async def _check_logic_consistency(self, story_data: Dict[str, Any]) -> List[ConsistencyIssue]:
        """检查逻辑一致性"""
        issues = []

        # 检查角色能力与情节的匹配度
        characters = story_data.get("characters", [])
        chapters = story_data.get("chapters", [])

        for char in characters:
            char_name = char.get("name", "")
            abilities = char.get("abilities", [])

            # 简单的逻辑检查：角色使用了未设定的能力
            for chapter in chapters:
                content = chapter.get("content", "") + chapter.get("summary", "")
                if char_name in content:
                    # 这里可以添加更复杂的能力使用检查逻辑
                    pass

        return issues

    def _find_similar_names(self, name: str) -> List[str]:
        """查找相似名称"""
        similar = []
        for other_name in self.character_registry.keys():
            if other_name != name and self._names_similar(name, other_name):
                similar.append(other_name)
        return similar

    def _names_similar(self, name1: str, name2: str) -> bool:
        """判断名称是否相似"""
        # 简单的相似度判断
        if len(name1) != len(name2):
            return False

        different_chars = sum(c1 != c2 for c1, c2 in zip(name1, name2))
        return different_chars <= 1

    async def _check_character_in_chapter(
        self, char_name: str, chapter: Dict[str, Any], story_context: Dict[str, Any]
    ) -> List[ConsistencyIssue]:
        """检查角色在章节中的一致性"""
        issues = []

        # 这里可以添加更复杂的角色一致性检查逻辑
        # 比如检查角色的行为是否符合其性格设定等

        return issues

    async def _check_chapter_plot_logic(
        self, chapter: Dict[str, Any], story_context: Dict[str, Any]
    ) -> List[ConsistencyIssue]:
        """检查章节情节逻辑"""
        issues = []

        # 这里可以添加情节逻辑检查
        # 比如检查前后章节的情节连贯性等

        return issues

    async def _check_chapter_connections(self, chapters: List[Dict[str, Any]]) -> List[
        ConsistencyIssue]:
        """检查章节连接"""
        issues = []

        for i in range(1, len(chapters)):
            current_chapter = chapters[i]
            previous_chapter = chapters[i - 1]

            # 检查章节之间的连贯性
            # 这里可以添加更复杂的连贯性检查逻辑

        return issues

    def _find_timeline_conflicts(self) -> List[Dict[str, Any]]:
        """查找时间线冲突"""
        conflicts = []

        # 这里可以添加时间线冲突检测逻辑

        return conflicts

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
        issue_types = set(issue.type for issue in issues)
        if "character" in issue_types:
            recommendations.append("完善角色设定，补充缺失的基本信息")

        if "plot" in issue_types:
            recommendations.append("梳理故事情节逻辑，确保前后呼应")

        if "world" in issue_types:
            recommendations.append("丰富世界观设定，建立完整的背景体系")

        if "timeline" in issue_types:
            recommendations.append("整理故事时间线，消除时间冲突")

        if "logic" in issue_types:
            recommendations.append("检查故事逻辑，确保角色行为合理")

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
            category="analysis",
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
