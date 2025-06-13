# modules/plot/story_planner.py - 修复版本
"""
故事规划器
负责生成故事大纲和章节规划
"""

import re
import json
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

    # 新增详细信息
    detailed_summary: str = ""  # 详细摘要
    scenes: List[Dict[str, Any]] = None  # 场景信息
    core_conflict: str = ""  # 核心冲突
    character_development: Dict[str, str] = None  # 角色发展
    foreshadowing: List[str] = None  # 伏笔


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

        # 生成详细章节规划
        chapters = await self._generate_detailed_chapter_plan(
            basic_info, plot_points, chapter_count, characters, world_setting
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

        # 获取角色名称
        character_names = [char.get("name", "未知角色") for char in (characters or [])]
        protagonist_name = character_names[0] if character_names else "主角"
        antagonist_name = character_names[1] if len(character_names) > 1 else "反派"

        # 获取世界信息
        world_name = world_setting.get("name", "未知世界") if world_setting else "未知世界"
        world_type = world_setting.get("type", "大陆") if world_setting else "大陆"

        prompt = f"""
        为小说《{title}》创建基础故事信息：

        基本设定：
        - 类型：{genre}
        - 主题：{theme or "成长"}
        - 世界：{world_name}（{world_type}）
        - 主角：{protagonist_name}
        - 反派：{antagonist_name}

        世界背景：{world_setting.get('culture_notes', '') if world_setting else ''}
        角色信息：{json.dumps(characters, ensure_ascii=False) if characters else '[]'}

        请生成以JSON格式返回以下信息：
        {{
            "premise": "故事前提（一句话概括故事核心）",
            "theme": "主要主题",
            "tone": "故事基调",
            "protagonist": "主角名称",
            "antagonist": "反派名称",
            "central_conflict": "核心冲突描述",
            "stakes": "故事赌注（失败的后果）",
            "beginning": "开端概述",
            "middle": "发展概述",
            "climax": "高潮概述",
            "resolution": "结局概述",
            "themes": ["主题1", "主题2", "主题3"],
            "symbols": ["象征1", "象征2"],
            "motifs": ["意象1", "意象2"]
        }}
        """

        response = await self.llm_service.generate_text(prompt, temperature=0.7)

        try:
            # 提取JSON部分
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                parsed_info = json.loads(json_match.group())
                return parsed_info
        except:
            pass

        # 如果解析失败，返回默认值
        return {
            "theme": theme or "成长与冒险",
            "premise": f"在{world_name}中，{protagonist_name}展开冒险旅程",
            "tone": "冒险刺激",
            "protagonist": protagonist_name,
            "antagonist": antagonist_name,
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
                description=f"介绍{basic_info['protagonist']}和日常世界",
                chapter_range=f"1-2",
                importance=8,
                plot_function="世界构建",
                characters_involved=[basic_info['protagonist']],
                conflicts=[],
                outcomes=["建立背景", "角色介绍"]
            ),
            PlotPoint(
                id="inciting_incident",
                name="启动事件",
                description=f"打破{basic_info['protagonist']}的日常，开始冒险",
                chapter_range=f"3-{act1_end}",
                importance=9,
                plot_function="情节启动",
                characters_involved=[basic_info['protagonist']],
                conflicts=["初始冲突"],
                outcomes=["踏上旅程", "离开舒适区"]
            ),
            PlotPoint(
                id="midpoint",
                name="中点转折",
                description="重大转折或启示，改变故事方向",
                chapter_range=f"{act2_mid}",
                importance=8,
                plot_function="转折点",
                characters_involved=[basic_info['protagonist'], "导师"],
                conflicts=["认知冲突"],
                outcomes=["角色成长", "真相揭示"]
            ),
            PlotPoint(
                id="climax",
                name="最终对决",
                description=f"{basic_info['protagonist']}与{basic_info['antagonist']}的最终对决",
                chapter_range=f"{act3_start}-{chapter_count - 1}",
                importance=10,
                plot_function="最终冲突",
                characters_involved=[basic_info['protagonist'], basic_info['antagonist']],
                conflicts=[basic_info['central_conflict']],
                outcomes=["决定结局", "解决冲突"]
            ),
            PlotPoint(
                id="resolution",
                name="结局",
                description="新的平衡，故事收尾",
                chapter_range=f"{chapter_count}",
                importance=7,
                plot_function="收尾",
                characters_involved=[basic_info['protagonist']],
                conflicts=[],
                outcomes=["故事完结", "新的开始"]
            )
        ]

    async def _generate_hero_journey_points(self, basic_info: Dict, chapter_count: int) -> List[
        PlotPoint]:
        """生成英雄之旅情节点"""

        return [
            PlotPoint(
                id="ordinary_world",
                name="日常世界",
                description=f"{basic_info['protagonist']}的平凡生活",
                chapter_range="1-2",
                importance=6,
                plot_function="建立基线",
                characters_involved=[basic_info['protagonist']],
                conflicts=[],
                outcomes=["背景设定", "角色建立"]
            ),
            PlotPoint(
                id="call_to_adventure",
                name="冒险召唤",
                description="收到冒险的邀请或挑战",
                chapter_range="3-4",
                importance=8,
                plot_function="情节触发",
                characters_involved=[basic_info['protagonist'], "信使"],
                conflicts=["选择冲突"],
                outcomes=["接受使命", "开始旅程"]
            ),
            PlotPoint(
                id="mentor",
                name="导师出现",
                description="遇到指导者，获得帮助",
                chapter_range="5-6",
                importance=7,
                plot_function="能力获得",
                characters_involved=[basic_info['protagonist'], "导师"],
                conflicts=[],
                outcomes=["获得帮助", "能力提升"]
            ),
            PlotPoint(
                id="threshold",
                name="跨越门槛",
                description="正式踏入冒险世界",
                chapter_range=f"7-{chapter_count // 3}",
                importance=8,
                plot_function="世界转换",
                characters_involved=[basic_info['protagonist']],
                conflicts=["适应冲突"],
                outcomes=["进入新世界", "面临挑战"]
            ),
            PlotPoint(
                id="trials",
                name="试炼考验",
                description="面临各种挑战和考验",
                chapter_range=f"{chapter_count // 3 + 1}-{chapter_count * 2 // 3}",
                importance=9,
                plot_function="角色锻炼",
                characters_involved=[basic_info['protagonist'], "盟友", "敌人"],
                conflicts=["成长冲突", "外部威胁"],
                outcomes=["获得成长", "结交盟友"]
            ),
            PlotPoint(
                id="ordeal",
                name="最大考验",
                description="面临最大的恐惧和挑战",
                chapter_range=f"{chapter_count * 2 // 3 + 1}-{chapter_count - 2}",
                importance=10,
                plot_function="最终考验",
                characters_involved=[basic_info['protagonist'], basic_info['antagonist']],
                conflicts=[basic_info['central_conflict']],
                outcomes=["获得宝物", "战胜恐惧"]
            ),
            PlotPoint(
                id="return",
                name="英雄归来",
                description="带着收获回到日常世界",
                chapter_range=f"{chapter_count - 1}-{chapter_count}",
                importance=7,
                plot_function="收尾整合",
                characters_involved=[basic_info['protagonist']],
                conflicts=[],
                outcomes=["新的开始", "智慧分享"]
            )
        ]

    async def _generate_default_points(self, basic_info: Dict, chapter_count: int) -> List[
        PlotPoint]:
        """生成默认情节点"""
        return await self._generate_three_act_points(basic_info, chapter_count)

    async def _generate_detailed_chapter_plan(
        self,
        basic_info: Dict,
        plot_points: List[PlotPoint],
        chapter_count: int,
        characters: List[Dict] = None,
        world_setting: Dict = None
    ) -> List[Chapter]:
        """生成详细章节规划"""

        # 使用LLM生成详细的章节规划
        prompt = f"""
        基于故事信息和情节点，为{chapter_count}章小说生成详细的章节规划：

        故事信息：
        - 标题：{basic_info.get('premise', '')}
        - 主角：{basic_info.get('protagonist', '')}
        - 反派：{basic_info.get('antagonist', '')}
        - 核心冲突：{basic_info.get('central_conflict', '')}

        情节点：
        {json.dumps([{"name": p.name, "description": p.description, "chapter_range": p.chapter_range} for p in plot_points], ensure_ascii=False, indent=2)}

        角色信息：
        {json.dumps([{"name": char.get("name", ""), "role": char.get("character_type", "")} for char in (characters or [])], ensure_ascii=False, indent=2)}

        请为每一章生成详细信息，返回JSON格式：
        [
            {{
                "number": 1,
                "title": "章节标题",
                "summary": "章节摘要（50字左右）",
                "detailed_summary": "详细摘要（100字左右）",
                "key_events": ["事件1", "事件2"],
                "character_focus": ["主要角色1", "主要角色2"],
                "plot_advancement": "本章如何推进情节",
                "tension_level": 5,
                "mood": "情绪氛围",
                "pacing": "节奏快慢",
                "core_conflict": "本章核心冲突",
                "scenes": [
                    {{
                        "location": "场景地点",
                        "characters": ["参与角色"],
                        "events": ["场景事件"],
                        "purpose": "场景目的",
                        "mood": "场景氛围"
                    }}
                ]
            }}
        ]

        要求：
        1. 每章都要有明确的目标和进展
        2. 章节之间要有逻辑连贯性
        3. 适当分配角色戏份
        4. 控制节奏起伏
        5. 确保情节点在相应章节体现
        """

        response = await self.llm_service.generate_text(prompt, temperature=0.7, max_tokens=8000)

        # 解析响应
        chapters = self._parse_chapters_from_llm(response.content, chapter_count, plot_points)

        return chapters

    def _parse_chapters_from_llm(self, response: str, chapter_count: int,
                                 plot_points: List[PlotPoint]) -> List[Chapter]:
        """从LLM响应解析章节信息"""
        try:
            # 尝试提取JSON
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                chapters_data = json.loads(json_match.group())

                chapters = []
                for i, chapter_data in enumerate(chapters_data):
                    if i >= chapter_count:
                        break

                    chapter = Chapter(
                        number=chapter_data.get("number", i + 1),
                        title=chapter_data.get("title", f"第{i + 1}章"),
                        summary=chapter_data.get("summary", f"第{i + 1}章的内容"),
                        word_count_target=3000,
                        key_events=chapter_data.get("key_events", []),
                        character_focus=chapter_data.get("character_focus", ["主角"]),
                        plot_advancement=chapter_data.get("plot_advancement", "推进故事发展"),
                        tension_level=chapter_data.get("tension_level", 5),
                        pacing=chapter_data.get("pacing", "medium"),
                        mood=chapter_data.get("mood", "中性"),
                        detailed_summary=chapter_data.get("detailed_summary",
                                                          chapter_data.get("summary", "")),
                        scenes=chapter_data.get("scenes", []),
                        core_conflict=chapter_data.get("core_conflict", ""),
                        character_development=chapter_data.get("character_development", {}),
                        foreshadowing=chapter_data.get("foreshadowing", [])
                    )
                    chapters.append(chapter)

                # 确保章节数量足够
                while len(chapters) < chapter_count:
                    chapters.append(self._create_default_chapter(len(chapters) + 1, plot_points))

                return chapters[:chapter_count]
        except Exception as e:
            print(f"解析章节失败: {e}")

        # 如果解析失败，生成默认章节
        return [self._create_default_chapter(i + 1, plot_points) for i in range(chapter_count)]

    def _create_default_chapter(self, chapter_number: int, plot_points: List[PlotPoint]) -> Chapter:
        """创建默认章节"""

        # 找到对应的情节点
        relevant_points = [
            point for point in plot_points
            if self._is_chapter_in_range(chapter_number, point.chapter_range)
        ]

        if relevant_points:
            main_point = relevant_points[0]
            title = f"第{chapter_number}章 {main_point.name}"
            summary = main_point.description
            key_events = main_point.outcomes
            character_focus = main_point.characters_involved
            plot_advancement = main_point.plot_function
            tension_level = main_point.importance
        else:
            title = f"第{chapter_number}章"
            summary = f"第{chapter_number}章的主要内容"
            key_events = [f"第{chapter_number}章的重要事件"]
            character_focus = ["主角"]
            plot_advancement = "推进故事发展"
            tension_level = self._calculate_tension_level(chapter_number, 20)

        return Chapter(
            number=chapter_number,
            title=title,
            summary=summary,
            word_count_target=3000,
            key_events=key_events,
            character_focus=character_focus,
            plot_advancement=plot_advancement,
            tension_level=tension_level,
            pacing=self._determine_pacing(chapter_number, 20, relevant_points),
            mood=self._determine_mood(relevant_points, tension_level),
            detailed_summary=summary,
            scenes=[],
            core_conflict="",
            character_development={},
            foreshadowing=[]
        )

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
                "description": f"{basic_info['protagonist']}的个人成长历程",
                "characters": basic_info['protagonist'],
                "importance": "高"
            },
            {
                "name": "友谊线",
                "description": "与伙伴的友谊发展",
                "characters": f"{basic_info['protagonist']}+伙伴",
                "importance": "中"
            }
        ]

        if characters and len(characters) > 1:
            subplots.append({
                "name": "爱情线",
                "description": "浪漫关系的发展",
                "characters": f"{basic_info['protagonist']}+爱情对象",
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
