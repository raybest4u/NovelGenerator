# modules/analysis/quality_analyzer.py
"""
质量分析器
分析小说的整体质量，包括文笔、情节、人物塑造等方面
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from core.base_tools import AsyncTool, ToolDefinition, ToolParameter
from core.llm_client import get_llm_service


@dataclass
class QualityMetric:
    """质量指标"""
    name: str
    score: float  # 0-100分
    description: str
    suggestions: List[str]


@dataclass
class QualityReport:
    """质量报告"""
    overall_score: float  # 总体质量得分
    metrics: List[QualityMetric]
    strengths: List[str]  # 优势
    weaknesses: List[str]  # 不足
    recommendations: List[str]  # 改进建议


class QualityAnalyzer:
    """质量分析器"""

    def __init__(self):
        self.llm_service = get_llm_service()

    async def analyze_novel_quality(
        self,
        novel_data: Dict[str, Any]
    ) -> QualityReport:
        """分析小说整体质量"""

        metrics = []

        # 分析各个维度
        plot_score = await self._analyze_plot_quality(novel_data)
        metrics.append(plot_score)

        character_score = await self._analyze_character_quality(novel_data)
        metrics.append(character_score)

        writing_score = await self._analyze_writing_quality(novel_data)
        metrics.append(writing_score)

        world_score = await self._analyze_world_building_quality(novel_data)
        metrics.append(world_score)

        pacing_score = await self._analyze_pacing_quality(novel_data)
        metrics.append(pacing_score)

        # 计算总体得分
        overall_score = sum(metric.score for metric in metrics) / len(metrics)

        # 生成报告
        return self._generate_quality_report(overall_score, metrics)

    async def _analyze_plot_quality(self, novel_data: Dict[str, Any]) -> QualityMetric:
        """分析情节质量"""

        # 检查情节要素
        outline = novel_data.get("outline", {})
        chapters = novel_data.get("chapters", [])

        score = 70  # 基础分数
        suggestions = []

        # 检查故事结构
        if not outline.get("central_conflict"):
            score -= 15
            suggestions.append("需要明确的中心冲突")

        if not outline.get("climax"):
            score -= 10
            suggestions.append("需要设置高潮部分")

        # 检查章节连贯性
        if len(chapters) > 1:
            # 简单的连贯性检查
            if any(not chapter.get("plot_advancement") for chapter in chapters):
                score -= 10
                suggestions.append("确保每章都推进情节发展")

        if not suggestions:
            suggestions.append("情节结构良好，继续保持")

        return QualityMetric(
            name="情节质量",
            score=max(0, min(100, score)),
            description="故事情节的完整性、连贯性和吸引力",
            suggestions=suggestions
        )

    async def _analyze_character_quality(self, novel_data: Dict[str, Any]) -> QualityMetric:
        """分析角色质量"""

        characters = novel_data.get("characters", [])

        score = 75
        suggestions = []

        if not characters:
            score = 30
            suggestions.append("需要创建角色")
        else:
            # 检查主角
            protagonist = next((c for c in characters if c.get("type") == "主角"), None)
            if not protagonist:
                score -= 20
                suggestions.append("需要明确的主角")

            # 检查角色完整性
            incomplete_chars = [c for c in characters if not all([
                c.get("name"), c.get("personality"), c.get("background")
            ])]

            if incomplete_chars:
                score -= len(incomplete_chars) * 5
                suggestions.append("完善角色设定信息")

        if not suggestions:
            suggestions.append("角色设定完整，继续深化")

        return QualityMetric(
            name="角色质量",
            score=max(0, min(100, score)),
            description="角色的丰满程度、个性特征和发展弧线",
            suggestions=suggestions
        )

    async def _analyze_writing_quality(self, novel_data: Dict[str, Any]) -> QualityMetric:
        """分析文笔质量"""

        chapters = novel_data.get("chapters", [])

        score = 80  # 假设基础文笔良好
        suggestions = []

        if not chapters:
            score = 40
            suggestions.append("需要实际的文字内容进行分析")
        else:
            # 简单的文本质量检查
            total_words = sum(chapter.get("word_count_target", 0) for chapter in chapters)

            if total_words < 10000:
                suggestions.append("增加内容丰富度")

            # 检查描述丰富度
            chapters_with_descriptions = [c for c in chapters if c.get("detailed_summary")]
            if len(chapters_with_descriptions) < len(chapters) * 0.8:
                score -= 10
                suggestions.append("增加场景和情感描述")

        if not suggestions:
            suggestions.append("文笔流畅，继续保持")

        return QualityMetric(
            name="文笔质量",
            score=max(0, min(100, score)),
            description="语言表达、描写技巧和文字的感染力",
            suggestions=suggestions
        )

    async def _analyze_world_building_quality(self, novel_data: Dict[str, Any]) -> QualityMetric:
        """分析世界构建质量"""

        world_setting = novel_data.get("world_setting", {})

        score = 70
        suggestions = []

        # 检查世界设定要素
        required_elements = ["geography", "culture", "power_system", "history"]
        missing_elements = [elem for elem in required_elements if not world_setting.get(elem)]

        score -= len(missing_elements) * 10

        if missing_elements:
            suggestions.append(f"补充世界设定：{', '.join(missing_elements)}")

        # 检查设定详细程度
        detailed_elements = [elem for elem in world_setting.values() if
                             isinstance(elem, dict) and len(elem) > 3]
        if len(detailed_elements) < len(world_setting) * 0.5:
            score -= 10
            suggestions.append("丰富世界设定的细节")

        if not suggestions:
            suggestions.append("世界设定完善，具有独特性")

        return QualityMetric(
            name="世界构建",
            score=max(0, min(100, score)),
            description="世界观的完整性、独特性和内在逻辑",
            suggestions=suggestions
        )

    async def _analyze_pacing_quality(self, novel_data: Dict[str, Any]) -> QualityMetric:
        """分析节奏质量"""

        chapters = novel_data.get("chapters", [])

        score = 75
        suggestions = []

        if not chapters:
            score = 50
            suggestions.append("需要章节内容进行节奏分析")
        else:
            # 检查节奏变化
            pacing_levels = [chapter.get("tension_level", 5) for chapter in chapters]

            # 检查是否有节奏变化
            if len(set(pacing_levels)) < 3:
                score -= 15
                suggestions.append("增加节奏变化，避免单调")

            # 检查高潮设置
            max_tension = max(pacing_levels) if pacing_levels else 0
            if max_tension < 8:
                score -= 10
                suggestions.append("设置更强烈的高潮部分")

        if not suggestions:
            suggestions.append("节奏控制良好，张弛有度")

        return QualityMetric(
            name="节奏控制",
            score=max(0, min(100, score)),
            description="故事节奏的变化和张弛有度",
            suggestions=suggestions
        )

    def _generate_quality_report(
        self, overall_score: float, metrics: List[QualityMetric]
    ) -> QualityReport:
        """生成质量报告"""

        # 识别优势和不足
        strengths = []
        weaknesses = []
        recommendations = []

        for metric in metrics:
            if metric.score >= 80:
                strengths.append(f"{metric.name}表现优秀")
            elif metric.score < 60:
                weaknesses.append(f"{metric.name}需要改进")

            recommendations.extend(metric.suggestions)

        # 生成总体建议
        if overall_score >= 85:
            recommendations.append("整体质量优秀，可以考虑投稿发表")
        elif overall_score >= 70:
            recommendations.append("质量良好，继续完善细节")
        elif overall_score >= 50:
            recommendations.append("有一定基础，需要重点改进薄弱环节")
        else:
            recommendations.append("需要全面提升，建议重新规划")

        return QualityReport(
            overall_score=overall_score,
            metrics=metrics,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=list(set(recommendations))  # 去重
        )


class QualityAnalyzerTool(AsyncTool):
    """质量分析工具"""

    def __init__(self):
        super().__init__()
        self.analyzer = QualityAnalyzer()

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="quality_analyzer",
            description="分析小说的整体质量，提供详细的质量报告和改进建议",
            category="analysis",
            parameters=[
                ToolParameter(
                    name="novel_data",
                    type="object",
                    description="小说数据，包括角色、情节、世界设定等",
                    required=True
                ),
                ToolParameter(
                    name="focus_areas",
                    type="array",
                    description="重点分析领域：plot/character/writing/world/pacing",
                    required=False
                )
            ],
            examples=[
                {
                    "parameters": {
                        "novel_data": {
                            "characters": [],
                            "chapters": [],
                            "world_setting": {},
                            "outline": {}
                        }
                    },
                    "result": "详细的质量分析报告"
                }
            ],
            tags=["quality", "analysis", "evaluation"]
        )

    async def execute(self, parameters: Dict[str, Any],
                      context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行质量分析"""

        novel_data = parameters.get("novel_data", {})
        focus_areas = parameters.get("focus_areas", [])

        # 执行分析
        quality_report = await self.analyzer.analyze_novel_quality(novel_data)

        # 如果指定了重点分析领域，过滤结果
        if focus_areas:
            filtered_metrics = [
                metric for metric in quality_report.metrics
                if any(area in metric.name.lower() for area in focus_areas)
            ]
            quality_report.metrics = filtered_metrics

        return {"quality_report": asdict(quality_report)}
