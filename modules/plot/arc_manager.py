
# modules/plot/arc_manager.py
"""
故事弧线管理器
管理整体故事弧线和各条支线
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from core.base_tools import AsyncTool, ToolDefinition, ToolParameter
from core.llm_client import get_llm_service
from modules.plot import StoryPlannerTool, ConflictGeneratorTool


@dataclass
class StoryArc:
    """故事弧线"""
    id: str
    name: str
    type: str  # 主线/支线
    priority: int  # 优先级 1-10

    # 弧线结构
    setup: str  # 铺垫
    development: str  # 发展
    climax: str  # 高潮
    resolution: str  # 解决

    # 涉及元素
    characters: List[str]  # 相关角色
    conflicts: List[str]  # 相关冲突
    themes: List[str]  # 相关主题

    # 章节分布
    chapter_distribution: Dict[str, List[int]]  # 各阶段对应的章节

    # 与其他弧线的关系
    dependencies: List[str]  # 依赖的弧线
    intersections: List[Dict[str, str]]  # 交叉点


class ArcManager:
    """弧线管理器"""

    def __init__(self):
        self.llm_service = get_llm_service()
        self.arcs: Dict[str, StoryArc] = {}

    async def create_main_arc(
        self,
        story_outline: Dict[str, Any]
    ) -> StoryArc:
        """创建主线弧线"""

        main_arc = StoryArc(
            id="main_arc",
            name="主线剧情",
            type="主线",
            priority=10,
            setup=story_outline.get("beginning", ""),
            development=story_outline.get("middle", ""),
            climax=story_outline.get("climax", ""),
            resolution=story_outline.get("resolution", ""),
            characters=[story_outline.get("protagonist", ""), story_outline.get("antagonist", "")],
            conflicts=[story_outline.get("central_conflict", "")],
            themes=story_outline.get("themes", []),
            chapter_distribution=self._distribute_main_arc_chapters(
                len(story_outline.get("chapters", []))
            ),
            dependencies=[],
            intersections=[]
        )

        self.arcs[main_arc.id] = main_arc
        return main_arc

    async def create_subplot_arcs(
        self,
        subplots: List[Dict[str, str]],
        total_chapters: int
    ) -> List[StoryArc]:
        """创建支线弧线"""

        subplot_arcs = []

        for i, subplot in enumerate(subplots):
            arc = StoryArc(
                id=f"subplot_{i + 1}",
                name=subplot.get("name", f"支线{i + 1}"),
                type="支线",
                priority=self._calculate_subplot_priority(subplot),
                setup=f"{subplot.get('name', '')}的开始",
                development=f"{subplot.get('name', '')}的发展",
                climax=f"{subplot.get('name', '')}的高潮",
                resolution=f"{subplot.get('name', '')}的结局",
                characters=subplot.get("characters", "").split("+"),
                conflicts=[],
                themes=[],
                chapter_distribution=self._distribute_subplot_chapters(total_chapters, i),
                dependencies=["main_arc"] if i == 0 else [f"subplot_{i}"],
                intersections=[]
            )

            subplot_arcs.append(arc)
            self.arcs[arc.id] = arc

        return subplot_arcs

    def _distribute_main_arc_chapters(self, total_chapters: int) -> Dict[str, List[int]]:
        """分配主线章节"""

        act1_end = total_chapters // 4
        act2_end = total_chapters * 3 // 4

        return {
            "setup": list(range(1, act1_end + 1)),
            "development": list(range(act1_end + 1, act2_end + 1)),
            "climax": list(range(act2_end + 1, total_chapters)),
            "resolution": [total_chapters]
        }

    def _distribute_subplot_chapters(self, total_chapters: int, subplot_index: int) -> Dict[
        str, List[int]]:
        """分配支线章节"""

        # 错开不同支线的重点章节
        start_offset = (subplot_index * 3) % 10

        setup_start = 3 + start_offset
        development_start = setup_start + 5
        climax_start = total_chapters - 8 + (subplot_index * 2)

        return {
            "setup": [setup_start, setup_start + 1],
            "development": list(range(development_start, climax_start)),
            "climax": [climax_start, climax_start + 1],
            "resolution": [total_chapters - 2 + subplot_index]
        }

    def _calculate_subplot_priority(self, subplot: Dict[str, str]) -> int:
        """计算支线优先级"""
        importance = subplot.get("importance", "中")

        priority_map = {
            "高": 8,
            "中": 6,
            "低": 4
        }

        return priority_map.get(importance, 6)

    async def analyze_arc_intersections(self) -> List[Dict[str, Any]]:
        """分析弧线交叉点"""

        intersections = []

        arc_list = list(self.arcs.values())

        for i, arc1 in enumerate(arc_list):
            for arc2 in arc_list[i + 1:]:
                intersection = self._find_arc_intersection(arc1, arc2)
                if intersection:
                    intersections.append(intersection)

        return intersections

    def _find_arc_intersection(self, arc1: StoryArc, arc2: StoryArc) -> Optional[Dict[str, Any]]:
        """寻找两条弧线的交叉点"""

        # 检查角色重叠
        common_characters = set(arc1.characters) & set(arc2.characters)

        # 检查章节重叠
        arc1_chapters = set()
        arc2_chapters = set()

        for chapters in arc1.chapter_distribution.values():
            arc1_chapters.update(chapters)

        for chapters in arc2.chapter_distribution.values():
            arc2_chapters.update(chapters)

        common_chapters = arc1_chapters & arc2_chapters

        if common_characters and common_chapters:
            return {
                "arc1": arc1.id,
                "arc2": arc2.id,
                "type": "角色交叉",
                "common_characters": list(common_characters),
                "common_chapters": sorted(list(common_chapters)),
                "description": f"{arc1.name}和{arc2.name}在第{min(common_chapters)}章开始交叉"
            }

        return None


class ArcManagerTool(AsyncTool):
    """弧线管理工具"""

    def __init__(self):
        super().__init__()
        self.manager = ArcManager()

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="arc_manager",
            description="管理故事弧线，创建主线和支线，分析弧线关系",
            category="plot",
            parameters=[
                ToolParameter(
                    name="action",
                    type="string",
                    description="操作类型：create_main/create_subplots/analyze",
                    required=True
                ),
                ToolParameter(
                    name="story_outline",
                    type="object",
                    description="故事大纲",
                    required=False
                ),
                ToolParameter(
                    name="subplots",
                    type="array",
                    description="支线列表",
                    required=False
                ),
                ToolParameter(
                    name="total_chapters",
                    type="integer",
                    description="总章节数",
                    required=False,
                    default=20
                )
            ]
        )

    async def execute(self, parameters: Dict[str, Any],
                      context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行弧线管理操作"""

        action = parameters.get("action")

        if action == "create_main":
            story_outline = parameters.get("story_outline", {})
            main_arc = await self.manager.create_main_arc(story_outline)
            return {"main_arc": asdict(main_arc)}

        elif action == "create_subplots":
            subplots = parameters.get("subplots", [])
            total_chapters = parameters.get("total_chapters", 20)
            subplot_arcs = await self.manager.create_subplot_arcs(subplots, total_chapters)
            return {"subplot_arcs": [asdict(arc) for arc in subplot_arcs]}

        elif action == "analyze":
            intersections = await self.manager.analyze_arc_intersections()
            return {
                "arcs": {arc_id: asdict(arc) for arc_id, arc in self.manager.arcs.items()},
                "intersections": intersections
            }

        else:
            return {"error": "不支持的操作类型"}


# 注册所有情节工具
def register_plot_tools():
    """注册情节规划工具"""
    from core.base_tools import get_tool_registry

    registry = get_tool_registry()

    registry.register(StoryPlannerTool())
    registry.register(ConflictGeneratorTool())
    registry.register(ArcManagerTool())


if __name__ == "__main__":
    register_plot_tools()
    print("情节规划工具已注册")
