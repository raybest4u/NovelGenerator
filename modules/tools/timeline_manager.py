
# modules/tools/timeline_manager.py
"""
时间线管理器
管理小说中的时间线和事件序列
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from core.base_tools import AsyncTool, ToolDefinition, ToolParameter
from core.llm_client import get_llm_service


@dataclass
class TimelineEvent:
    """时间线事件"""
    id: str
    name: str
    description: str
    timestamp: str  # 故事内时间
    chapter: Optional[int]  # 对应章节
    characters_involved: List[str]
    location: str
    event_type: str  # plot/character/world/background
    importance: int  # 1-10
    consequences: List[str]
    prerequisites: List[str]  # 前置事件ID


@dataclass
class Timeline:
    """时间线"""
    id: str
    name: str
    description: str
    time_scale: str  # years/months/days/hours
    events: List[TimelineEvent]
    start_time: str
    end_time: str


class TimelineManager:
    """时间线管理器"""

    def __init__(self):
        self.llm_service = get_llm_service()
        self.timelines: Dict[str, Timeline] = {}
        self.global_timeline: Optional[Timeline] = None

    async def create_main_timeline(
        self,
        story_outline: Dict[str, Any],
        time_span: str = "2 years",
        starting_point: str = "春季"
    ) -> Timeline:
        """创建主时间线"""

        events = await self._extract_events_from_outline(story_outline)

        timeline = Timeline(
            id="main_timeline",
            name="主线时间线",
            description="小说主要故事线的时间线",
            time_scale="months",
            events=events,
            start_time=starting_point,
            end_time=self._calculate_end_time(starting_point, time_span)
        )

        self.global_timeline = timeline
        self.timelines[timeline.id] = timeline

        return timeline

    async def create_character_timeline(
        self,
        character: Dict[str, Any],
        main_timeline: Timeline
    ) -> Timeline:
        """创建角色时间线"""

        character_events = await self._generate_character_events(character, main_timeline)

        timeline = Timeline(
            id=f"char_{character.get('name', 'unknown')}_timeline",
            name=f"{character.get('name', '角色')}的时间线",
            description=f"{character.get('name', '角色')}的个人发展时间线",
            time_scale="days",
            events=character_events,
            start_time=main_timeline.start_time,
            end_time=main_timeline.end_time
        )

        self.timelines[timeline.id] = timeline
        return timeline

    async def create_world_timeline(
        self,
        world_setting: Dict[str, Any],
        historical_depth: str = "1000 years"
    ) -> Timeline:
        """创建世界历史时间线"""

        historical_events = await self._generate_world_history(world_setting, historical_depth)

        timeline = Timeline(
            id="world_timeline",
            name="世界历史时间线",
            description="世界的历史背景时间线",
            time_scale="years",
            events=historical_events,
            start_time=f"{historical_depth}前",
            end_time="当前"
        )

        self.timelines[timeline.id] = timeline
        return timeline

    def add_event(
        self,
        timeline_id: str,
        event: TimelineEvent
    ) -> bool:
        """添加事件到时间线"""

        if timeline_id not in self.timelines:
            return False

        timeline = self.timelines[timeline_id]

        # 检查事件冲突
        if self._check_event_conflicts(event, timeline.events):
            return False

        # 插入事件（按时间排序）
        timeline.events.append(event)
        timeline.events.sort(key=lambda e: self._parse_timestamp(e.timestamp))

        return True

    def get_events_in_chapter(
        self,
        chapter_number: int,
        timeline_id: str = "main_timeline"
    ) -> List[TimelineEvent]:
        """获取指定章节的事件"""

        if timeline_id not in self.timelines:
            return []

        timeline = self.timelines[timeline_id]
        return [event for event in timeline.events if event.chapter == chapter_number]

    def get_events_by_character(
        self,
        character_name: str,
        timeline_id: str = "main_timeline"
    ) -> List[TimelineEvent]:
        """获取指定角色相关的事件"""

        if timeline_id not in self.timelines:
            return []

        timeline = self.timelines[timeline_id]
        return [
            event for event in timeline.events
            if character_name in event.characters_involved
        ]

    async def detect_timeline_conflicts(
        self,
        timeline_id: str = None
    ) -> List[Dict[str, Any]]:
        """检测时间线冲突"""

        conflicts = []

        if timeline_id:
            timelines_to_check = [
                self.timelines[timeline_id]] if timeline_id in self.timelines else []
        else:
            timelines_to_check = list(self.timelines.values())

        for timeline in timelines_to_check:
            timeline_conflicts = self._find_internal_conflicts(timeline)
            conflicts.extend(timeline_conflicts)

        # 检查时间线之间的冲突
        if len(self.timelines) > 1:
            cross_conflicts = self._find_cross_timeline_conflicts()
            conflicts.extend(cross_conflicts)

        return conflicts

    async def _extract_events_from_outline(
        self,
        story_outline: Dict[str, Any]
    ) -> List[TimelineEvent]:
        """从故事大纲提取事件"""

        events = []
        plot_points = story_outline.get("plot_points", [])
        chapters = story_outline.get("chapters", [])

        for i, plot_point in enumerate(plot_points):
            event = TimelineEvent(
                id=f"plot_{i}",
                name=plot_point.get("name", f"情节点{i}"),
                description=plot_point.get("description", ""),
                timestamp=f"第{i + 1}个月",
                chapter=self._map_plot_to_chapter(plot_point, chapters),
                characters_involved=plot_point.get("characters_involved", []),
                location="未指定",
                event_type="plot",
                importance=plot_point.get("importance", 5),
                consequences=plot_point.get("outcomes", []),
                prerequisites=[]
            )
            events.append(event)

        return events

    def _map_plot_to_chapter(
        self,
        plot_point: Dict[str, Any],
        chapters: List[Dict[str, Any]]
    ) -> Optional[int]:
        """映射情节点到章节"""

        chapter_range = plot_point.get("chapter_range", "")

        if "-" in chapter_range:
            start_chapter = int(chapter_range.split("-")[0])
            return start_chapter
        elif chapter_range.isdigit():
            return int(chapter_range)

        return None

    async def _generate_character_events(
        self,
        character: Dict[str, Any],
        main_timeline: Timeline
    ) -> List[TimelineEvent]:
        """生成角色相关事件"""

        events = []

        # 从主时间线筛选角色相关事件
        character_name = character.get("name", "")
        main_events = [
            event for event in main_timeline.events
            if character_name in event.characters_involved
        ]

        # 添加角色特有事件
        character_specific_events = [
            TimelineEvent(
                id=f"{character_name}_background",
                name=f"{character_name}的背景事件",
                description="角色的重要背景经历",
                timestamp="故事开始前",
                chapter=None,
                characters_involved=[character_name],
                location=character.get("birthplace", "未知"),
                event_type="character",
                importance=6,
                consequences=["塑造角色性格"],
                prerequisites=[]
            )
        ]

        events.extend(main_events)
        events.extend(character_specific_events)

        return events

    async def _generate_world_history(
        self,
        world_setting: Dict[str, Any],
        time_span: str
    ) -> List[TimelineEvent]:
        """生成世界历史事件"""

        history_events = []

        # 生成几个重要的历史事件
        historical_periods = [
            ("远古时代", "世界创造"),
            ("上古时期", "神魔大战"),
            ("中古时期", "王朝建立"),
            ("近古时期", "门派兴起"),
            ("当代", "故事背景")
        ]

        for i, (period, description) in enumerate(historical_periods):
            event = TimelineEvent(
                id=f"history_{i}",
                name=period,
                description=description,
                timestamp=f"{len(historical_periods) - i}000年前",
                chapter=None,
                characters_involved=[],
                location="整个世界",
                event_type="world",
                importance=8,
                consequences=[f"影响{period}的发展"],
                prerequisites=[]
            )
            history_events.append(event)

        return history_events

    def _calculate_end_time(self, start_time: str, time_span: str) -> str:
        """计算结束时间"""

        # 简单计算，实际可以更复杂
        if "year" in time_span.lower():
            years = int(time_span.split()[0])
            return f"{start_time}后{years}年"
        elif "month" in time_span.lower():
            months = int(time_span.split()[0])
            return f"{start_time}后{months}月"
        else:
            return f"{start_time}之后"

    def _parse_timestamp(self, timestamp: str) -> int:
        """解析时间戳为可排序的数值"""

        # 简单解析，实际可以更复杂
        if "年前" in timestamp:
            return -int(timestamp.replace("年前", ""))
        elif "月" in timestamp:
            return int(timestamp.replace("第", "").replace("个月", ""))
        elif "章" in timestamp:
            return int(timestamp.replace("第", "").replace("章", "")) * 30  # 假设每章30天
        else:
            return 0

    def _check_event_conflicts(
        self,
        new_event: TimelineEvent,
        existing_events: List[TimelineEvent]
    ) -> bool:
        """检查事件冲突"""

        # 检查同一角色在同一时间的冲突
        for event in existing_events:
            if (event.timestamp == new_event.timestamp and
                any(char in event.characters_involved for char in new_event.characters_involved)):
                return True

        return False

    def _find_internal_conflicts(self, timeline: Timeline) -> List[Dict[str, Any]]:
        """查找时间线内部冲突"""

        conflicts = []

        for i, event1 in enumerate(timeline.events):
            for event2 in timeline.events[i + 1:]:
                if self._check_event_conflicts(event1, [event2]):
                    conflicts.append({
                        "type": "内部冲突",
                        "timeline": timeline.id,
                        "event1": event1.id,
                        "event2": event2.id,
                        "description": f"{event1.name}与{event2.name}时间冲突"
                    })

        return conflicts

    def _find_cross_timeline_conflicts(self) -> List[Dict[str, Any]]:
        """查找跨时间线冲突"""

        conflicts = []

        timeline_list = list(self.timelines.values())

        for i, timeline1 in enumerate(timeline_list):
            for timeline2 in timeline_list[i + 1:]:
                # 检查交叉事件冲突
                for event1 in timeline1.events:
                    for event2 in timeline2.events:
                        if self._check_event_conflicts(event1, [event2]):
                            conflicts.append({
                                "type": "跨时间线冲突",
                                "timeline1": timeline1.id,
                                "timeline2": timeline2.id,
                                "event1": event1.id,
                                "event2": event2.id,
                                "description": f"不同时间线中的事件冲突"
                            })

        return conflicts


class TimelineManagerTool(AsyncTool):
    """时间线管理工具"""

    def __init__(self):
        super().__init__()
        self.manager = TimelineManager()

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="timeline_manager",
            description="管理小说时间线，创建主线、角色线、世界历史线，检测时间冲突",
            category="tools",
            parameters=[
                ToolParameter(
                    name="action",
                    type="string",
                    description="操作类型：create_main/create_character/create_world/add_event/get_events/detect_conflicts",
                    required=True
                ),
                ToolParameter(
                    name="story_outline",
                    type="object",
                    description="故事大纲（创建主线用）",
                    required=False
                ),
                ToolParameter(
                    name="time_span",
                    type="string",
                    description="时间跨度",
                    required=False,
                    default="2 years"
                ),
                ToolParameter(
                    name="starting_point",
                    type="string",
                    description="起始时间点",
                    required=False,
                    default="春季"
                ),
                ToolParameter(
                    name="character",
                    type="object",
                    description="角色信息（创建角色线用）",
                    required=False
                ),
                ToolParameter(
                    name="world_setting",
                    type="object",
                    description="世界设定（创建世界线用）",
                    required=False
                ),
                ToolParameter(
                    name="timeline_id",
                    type="string",
                    description="时间线ID",
                    required=False,
                    default="main_timeline"
                ),
                ToolParameter(
                    name="event",
                    type="object",
                    description="事件信息（添加事件用）",
                    required=False
                ),
                ToolParameter(
                    name="chapter_number",
                    type="integer",
                    description="章节号（获取事件用）",
                    required=False
                ),
                ToolParameter(
                    name="character_name",
                    type="string",
                    description="角色名（获取事件用）",
                    required=False
                )
            ]
        )

    async def execute(self, parameters: Dict[str, Any],
                      context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行时间线管理操作"""

        action = parameters.get("action")

        if action == "create_main":
            timeline = await self.manager.create_main_timeline(
                parameters.get("story_outline", {}),
                parameters.get("time_span", "2 years"),
                parameters.get("starting_point", "春季")
            )
            return {"timeline": asdict(timeline)}

        elif action == "create_character":
            main_timeline = self.manager.global_timeline
            if not main_timeline:
                return {"error": "请先创建主时间线"}

            timeline = await self.manager.create_character_timeline(
                parameters.get("character", {}),
                main_timeline
            )
            return {"timeline": asdict(timeline)}

        elif action == "create_world":
            timeline = await self.manager.create_world_timeline(
                parameters.get("world_setting", {}),
                parameters.get("time_span", "1000 years")
            )
            return {"timeline": asdict(timeline)}

        elif action == "add_event":
            event_data = parameters.get("event", {})
            event = TimelineEvent(**event_data)
            success = self.manager.add_event(
                parameters.get("timeline_id", "main_timeline"),
                event
            )
            return {"success": success}

        elif action == "get_events":
            if parameters.get("chapter_number"):
                events = self.manager.get_events_in_chapter(
                    parameters["chapter_number"],
                    parameters.get("timeline_id", "main_timeline")
                )
            elif parameters.get("character_name"):
                events = self.manager.get_events_by_character(
                    parameters["character_name"],
                    parameters.get("timeline_id", "main_timeline")
                )
            else:
                timeline_id = parameters.get("timeline_id", "main_timeline")
                if timeline_id in self.manager.timelines:
                    events = self.manager.timelines[timeline_id].events
                else:
                    events = []

            return {"events": [asdict(event) for event in events]}

        elif action == "detect_conflicts":
            conflicts = await self.manager.detect_timeline_conflicts(
                parameters.get("timeline_id")
            )
            return {"conflicts": conflicts}

        else:
            return {"error": "不支持的操作类型"}
