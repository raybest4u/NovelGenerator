
# modules/plot/story_planner.py
"""
故事规划器
负责生成故事大纲和章节规划
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
from core.base_tools import AsyncTool, ToolDefinition, ToolParameter
from core.llm_client import get_llm_service
from config.settings import get_prompt_manager


class PlotStructure(Enum):
    """情节结构"""
    THREE_ACT = "三幕式"
    HERO_JOURNEY = "英雄之旅"
    SEVEN_POINT = "七点式"
    FREYTAG_PYRAMID = "弗莱塔格金字塔"
    CHINESE_CLASSICAL = "中式传统"


class StoryTone(Enum):
    """故事基调"""
    LIGHT_HEARTED = "轻松愉快"
    SERIOUS = "严肃正剧"
    DARK = "黑暗沉重"
    EPIC = "宏大史诗"
    ROMANTIC = "浪漫温馨"
    ADVENTURE = "冒险刺激"


@dataclass
class PlotPoint:
    """情节点"""
    id: str
    name: str
    description: str
    chapter_range: str  # 章节范围
    importance: int  # 重要性 1-10
    plot_function: str  # 情节功能
    characters_involved: List[str]  # 涉及角色
    conflicts: List[str]  # 相关冲突
    outcomes: List[str]  # 结果影响


@dataclass
class Chapter:
    """章节"""
    number: int
    title: str
    summary: str
    word_count_target: int
    key_events: List[str]
    character_focus: List[str]
    plot_advancement: str
    tension_level: int  # 紧张程度 1-10
    pacing: str  # 节奏：slow/medium/fast
    mood: str  # 氛围


@dataclass
class StoryOutline:
    """故事大纲"""
    title: str
    genre: str
    theme: str
    premise: str  # 故事前提
    structure: str  # 情节结构
    tone: str  # 故事基调

    # 核心元素
    protagonist: str  # 主角
    antagonist: str  # 反派
    central_conflict: str  # 核心冲突
    stakes: str  # 赌注

    # 情节点
    plot_points: List[PlotPoint]

    # 章节规划
    chapters: List[Chapter]

    # 故事弧线
    beginning: str  # 开端
    middle: str  # 发展
    climax: str  # 高潮
    resolution: str  # 结局

    # 子情节
    subplots: List[Dict[str, str]]

    # 主题元素
    themes: List[str]
    symbols: List[str]
    motifs: List[str]


class StoryPlanner:
    """故事规划器"""

    def __init__(self):
        self.llm_service = get_llm_service()
        self.prompt_manager = get_prompt_manager()

    async def create_story_outline(
        self,
        title: str,
        genre: str = "玄幻",
        chapter_count: int = 20,
        structure: str = "三幕式",
        theme: str = None,
        characters: List[Dict] = None,
        world_setting: Dict = None
    ) -> StoryOutline:
        """创建故事大纲"""

        # 生成基础故事信息
        basic_info = await self._generate_basic_story_info(
            title, genre, theme, characters, world_setting
        )

        # 生成情节结构
        plot_points = await self._generate_plot_points(
            basic_info, structure, chapter_count
        )

        # 生成章节规划
        chapters = await self._generate_chapter_plan(
            basic_info, plot_points, chapter_count
        )

        # 生成子情节
        subplots = await self._generate_subplots(
            basic_info, characters
        )

        outline = StoryOutline(
            title=title,
            genre=genre,
            theme=basic_info.get("theme", "成长与冒险"),
            premise=basic_info.get("premise", ""),
            structure=structure,
            tone=basic_info.get("tone", "冒险刺激"),
            protagonist=basic_info.get("protagonist", "主角"),
            antagonist=basic_info.get("antagonist", "反派"),
            central_conflict=basic_info.get("central_conflict", ""),
            stakes=basic_info.get("stakes", ""),
            plot_points=plot_points,
            chapters=chapters,
            beginning=basic_info.get("beginning", ""),
            middle=basic_info.get("middle", ""),
            climax=basic_info.get("climax", ""),
            resolution=basic_info.get("resolution", ""),
            subplots=subplots,
            themes=basic_info.get("themes", []),
            symbols=basic_info.get("symbols", []),
            motifs=basic_info.get("motifs", [])
        )

        return outline

    async def _generate_basic_story_info(
        self,
        title: str,
        genre: str,
        theme: str,
        characters: List[Dict],
        world_setting: Dict
    ) -> Dict[str, Any]:
        """生成基础故事信息"""

        prompt = self.prompt_manager.get_prompt(
            "plot",
            "basic_story",
            title=title,
            genre=genre,
            theme=theme or "成长",
            characters=characters or [],
            world_setting=world_setting or {}
        )

        response = await self.llm_service.generate_text(prompt)

        # 解析响应，返回结构化数据
        return {
            "theme": theme or "成长与冒险",
            "premise": f"在{genre}世界中，主角展开冒险旅程",
            "tone": "冒险刺激",
            "protagonist": "主角",
            "antagonist": "反派",
            "central_conflict": "正义与邪恶的对抗",
            "stakes": "世界的命运",
            "beginning": "平凡世界被打破",
            "middle": "冒险与成长",
            "climax": "最终决战",
            "resolution": "新的平衡",
            "themes": ["成长", "友谊", "正义"],
            "symbols": ["剑", "光明", "希望"],
            "motifs": ["旅程", "试炼", "觉醒"]
        }

    async def _generate_plot_points(
        self,
        basic_info: Dict,
        structure: str,
        chapter_count: int
    ) -> List[PlotPoint]:
        """生成情节点"""

        if structure == "三幕式":
            return await self._generate_three_act_points(basic_info, chapter_count)
        elif structure == "英雄之旅":
            return await self._generate_hero_journey_points(basic_info, chapter_count)
        else:
            return await self._generate_default_points(basic_info, chapter_count)

    async def _generate_three_act_points(self, basic_info: Dict, chapter_count: int) -> List[
        PlotPoint]:
        """生成三幕式情节点"""

        act1_end = chapter_count // 4
        act2_mid = chapter_count // 2
        act3_start = chapter_count * 3 // 4

        return [
            PlotPoint(
                id="opening",
                name="开场",
                description="介绍主角和日常世界",
                chapter_range=f"1-2",
                importance=8,
                plot_function="世界构建",
                characters_involved=["主角"],
                conflicts=[],
                outcomes=["建立背景"]
            ),
            PlotPoint(
                id="inciting_incident",
                name="启动事件",
                description="打破日常，开始冒险",
                chapter_range=f"3-{act1_end}",
                importance=9,
                plot_function="情节启动",
                characters_involved=["主角"],
                conflicts=["初始冲突"],
                outcomes=["踏上旅程"]
            ),
            PlotPoint(
                id="midpoint",
                name="中点",
                description="重大转折或启示",
                chapter_range=f"{act2_mid}",
                importance=8,
                plot_function="转折点",
                characters_involved=["主角", "导师"],
                conflicts=["认知冲突"],
                outcomes=["角色成长"]
            ),
            PlotPoint(
                id="climax",
                name="高潮",
                description="最终对决",
                chapter_range=f"{act3_start}-{chapter_count - 1}",
                importance=10,
                plot_function="最终冲突",
                characters_involved=["主角", "反派"],
                conflicts=["核心冲突"],
                outcomes=["决定结局"]
            ),
            PlotPoint(
                id="resolution",
                name="结局",
                description="新的平衡",
                chapter_range=f"{chapter_count}",
                importance=7,
                plot_function="收尾",
                characters_involved=["主角"],
                conflicts=[],
                outcomes=["故事完结"]
            )
        ]

    async def _generate_hero_journey_points(self, basic_info: Dict, chapter_count: int) -> List[
        PlotPoint]:
        """生成英雄之旅情节点"""

        # 简化版英雄之旅结构
        points_per_stage = max(1, chapter_count // 12)

        return [
            PlotPoint(
                id="ordinary_world",
                name="日常世界",
                description="主角的平凡生活",
                chapter_range="1-2",
                importance=6,
                plot_function="建立基线",
                characters_involved=["主角"],
                conflicts=[],
                outcomes=["背景设定"]
            ),
            PlotPoint(
                id="call_to_adventure",
                name="冒险召唤",
                description="收到冒险的邀请或挑战",
                chapter_range="3-4",
                importance=8,
                plot_function="情节触发",
                characters_involved=["主角", "信使"],
                conflicts=["选择冲突"],
                outcomes=["接受使命"]
            ),
            PlotPoint(
                id="mentor",
                name="导师出现",
                description="遇到指导者",
                chapter_range="5-6",
                importance=7,
                plot_function="能力获得",
                characters_involved=["主角", "导师"],
                conflicts=[],
                outcomes=["获得帮助"]
            ),
            PlotPoint(
                id="threshold",
                name="跨越门槛",
                description="正式踏入冒险世界",
                chapter_range=f"7-{chapter_count // 3}",
                importance=8,
                plot_function="世界转换",
                characters_involved=["主角"],
                conflicts=["适应冲突"],
                outcomes=["进入新世界"]
            ),
            PlotPoint(
                id="trials",
                name="试炼考验",
                description="面临各种挑战",
                chapter_range=f"{chapter_count // 3 + 1}-{chapter_count * 2 // 3}",
                importance=9,
                plot_function="角色锻炼",
                characters_involved=["主角", "盟友", "敌人"],
                conflicts=["成长冲突"],
                outcomes=["获得成长"]
            ),
            PlotPoint(
                id="ordeal",
                name="最大考验",
                description="面临最大的恐惧和挑战",
                chapter_range=f"{chapter_count * 2 // 3 + 1}-{chapter_count - 2}",
                importance=10,
                plot_function="最终考验",
                characters_involved=["主角", "反派"],
                conflicts=["生死冲突"],
                outcomes=["获得宝物"]
            ),
            PlotPoint(
                id="return",
                name="归来",
                description="带着收获回到日常世界",
                chapter_range=f"{chapter_count - 1}-{chapter_count}",
                importance=7,
                plot_function="收尾整合",
                characters_involved=["主角"],
                conflicts=[],
                outcomes=["新的开始"]
            )
        ]

    async def _generate_default_points(self, basic_info: Dict, chapter_count: int) -> List[
        PlotPoint]:
        """生成默认情节点"""
        return await self._generate_three_act_points(basic_info, chapter_count)

    async def _generate_chapter_plan(
        self,
        basic_info: Dict,
        plot_points: List[PlotPoint],
        chapter_count: int
    ) -> List[Chapter]:
        """生成章节规划"""

        chapters = []

        for i in range(1, chapter_count + 1):
            # 确定当前章节涉及的情节点
            relevant_points = [
                point for point in plot_points
                if self._is_chapter_in_range(i, point.chapter_range)
            ]

            # 计算紧张程度（开头低，中间高，结尾递减）
            tension = self._calculate_tension_level(i, chapter_count)

            # 确定节奏
            pacing = self._determine_pacing(i, chapter_count, relevant_points)

            chapter = Chapter(
                number=i,
                title=f"第{i}章",
                summary=f"第{i}章的主要内容",
                word_count_target=3000,
                key_events=[point.name for point in relevant_points],
                character_focus=["主角"],
                plot_advancement=f"推进{relevant_points[0].plot_function if relevant_points else '故事发展'}",
                tension_level=tension,
                pacing=pacing,
                mood=self._determine_mood(relevant_points, tension)
            )

            chapters.append(chapter)

        return chapters

    def _is_chapter_in_range(self, chapter: int, range_str: str) -> bool:
        """判断章节是否在范围内"""
        try:
            if '-' in range_str:
                start, end = map(int, range_str.split('-'))
                return start <= chapter <= end
            else:
                return chapter == int(range_str)
        except:
            return False

    def _calculate_tension_level(self, chapter: int, total_chapters: int) -> int:
        """计算紧张程度"""
        position = chapter / total_chapters

        if position < 0.25:  # 第一幕
            return min(3 + int(position * 12), 5)
        elif position < 0.75:  # 第二幕
            return min(5 + int((position - 0.25) * 16), 9)
        else:  # 第三幕
            return max(9 - int((position - 0.75) * 12), 6)

    def _determine_pacing(self, chapter: int, total_chapters: int,
                          plot_points: List[PlotPoint]) -> str:
        """确定节奏"""
        position = chapter / total_chapters
        has_major_events = any(point.importance >= 8 for point in plot_points)

        if has_major_events:
            return "fast"
        elif position < 0.3 or position > 0.8:
            return "medium"
        else:
            return "medium"

    def _determine_mood(self, plot_points: List[PlotPoint], tension: int) -> str:
        """确定氛围"""
        if tension >= 8:
            return "紧张刺激"
        elif tension >= 6:
            return "严肃专注"
        elif tension >= 4:
            return "轻松活泼"
        else:
            return "平静祥和"

    async def _generate_subplots(self, basic_info: Dict, characters: List[Dict]) -> List[
        Dict[str, str]]:
        """生成子情节"""

        subplots = [
            {
                "name": "成长线",
                "description": "主角的个人成长历程",
                "characters": "主角",
                "importance": "高"
            },
            {
                "name": "友谊线",
                "description": "与伙伴的友谊发展",
                "characters": "主角+伙伴",
                "importance": "中"
            }
        ]

        if characters and len(characters) > 1:
            subplots.append({
                "name": "爱情线",
                "description": "浪漫关系的发展",
                "characters": "主角+爱情对象",
                "importance": "中"
            })

        return subplots


class StoryPlannerTool(AsyncTool):
    """故事规划工具"""

    def __init__(self):
        super().__init__()
        self.planner = StoryPlanner()

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="story_planner",
            description="创建完整的故事大纲，包括情节结构、章节规划、主题设定等",
            category="plot",
            parameters=[
                ToolParameter(
                    name="title",
                    type="string",
                    description="故事标题",
                    required=True
                ),
                ToolParameter(
                    name="genre",
                    type="string",
                    description="故事类型",
                    required=False,
                    default="玄幻"
                ),
                ToolParameter(
                    name="chapter_count",
                    type="integer",
                    description="章节数量",
                    required=False,
                    default=20
                ),
                ToolParameter(
                    name="structure",
                    type="string",
                    description="情节结构：三幕式/英雄之旅/七点式等",
                    required=False,
                    default="三幕式"
                ),
                ToolParameter(
                    name="theme",
                    type="string",
                    description="主题",
                    required=False
                ),
                ToolParameter(
                    name="characters",
                    type="array",
                    description="角色列表",
                    required=False
                ),
                ToolParameter(
                    name="world_setting",
                    type="object",
                    description="世界设定",
                    required=False
                )
            ],
            examples=[
                {
                    "parameters": {
                        "title": "仙路征途",
                        "genre": "玄幻",
                        "chapter_count": 30,
                        "structure": "英雄之旅"
                    },
                    "result": "完整的故事大纲和章节规划"
                }
            ],
            tags=["plot", "outline", "structure"]
        )

    async def execute(self, parameters: Dict[str, Any],
                      context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行故事规划"""

        title = parameters.get("title", "无题")
        genre = parameters.get("genre", "玄幻")
        chapter_count = parameters.get("chapter_count", 20)
        structure = parameters.get("structure", "三幕式")
        theme = parameters.get("theme")
        characters = parameters.get("characters", [])
        world_setting = parameters.get("world_setting", {})

        outline = await self.planner.create_story_outline(
            title, genre, chapter_count, structure, theme, characters, world_setting
        )

        return {
            "story_outline": asdict(outline),
            "generation_info": {
                "title": title,
                "genre": genre,
                "chapter_count": chapter_count,
                "structure": structure
            }
        }

