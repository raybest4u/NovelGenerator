

# modules/writing/chapter_writer.py
"""
章节写作器
负责生成完整的章节内容
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from core.base_tools import AsyncTool, ToolDefinition, ToolParameter, ToolDecorator
from core.llm_client import get_llm_service
from config.settings import get_prompt_manager
import asyncio


@dataclass
class Scene:
    """场景"""
    id: str
    title: str
    content: str
    word_count: int
    characters: List[str]
    location: str
    purpose: str  # 场景目的
    mood: str
    pacing: str


@dataclass
class ChapterContent:
    """章节内容"""
    chapter_number: int
    title: str
    summary: str
    scenes: List[Scene]
    total_word_count: int

    # 章节元数据
    key_events: List[str]
    character_focus: List[str]
    plot_advancement: str
    emotional_arc: str

    # 写作质量指标
    dialogue_ratio: float  # 对话占比
    description_ratio: float  # 描述占比
    action_ratio: float  # 动作占比

    # 连接信息
    previous_chapter_connection: str
    next_chapter_setup: str


class ChapterWriter:
    """章节写作器"""

    def __init__(self):
        self.llm_service = get_llm_service()
        self.prompt_manager = get_prompt_manager()
        self.writing_styles = self._load_writing_styles()

    @ToolDecorator.cached(expire_seconds=3600)
    async def write_chapter(
        self,
        chapter_info: Dict[str, Any],
        story_context: Dict[str, Any],
        writing_style: str = "traditional",
        target_word_count: int = 3000
    ) -> ChapterContent:
        """写作章节"""

        # 规划章节结构
        scene_plan = await self._plan_chapter_scenes(
            chapter_info, story_context, target_word_count
        )

        # 生成各个场景
        scenes = []
        for scene_info in scene_plan:
            scene = await self._write_scene(
                scene_info, story_context, writing_style
            )
            scenes.append(scene)

        # 连接场景并润色
        chapter_content = await self._assemble_chapter(
            chapter_info, scenes, story_context
        )

        return chapter_content

    async def _plan_chapter_scenes(
        self,
        chapter_info: Dict[str, Any],
        story_context: Dict[str, Any],
        target_word_count: int
    ) -> List[Dict[str, Any]]:
        """规划章节场景"""

        prompt = self.prompt_manager.get_prompt(
            "writing",
            "scene_planning",
            chapter_number=chapter_info.get("number", 1),
            chapter_summary=chapter_info.get("summary", ""),
            key_events=chapter_info.get("key_events", []),
            target_word_count=target_word_count,
            story_context=story_context
        )

        response = await self.llm_service.generate_text(prompt)

        # 解析场景规划
        return self._parse_scene_plan(response.content, target_word_count)

    def _parse_scene_plan(self, response: str, target_word_count: int) -> List[Dict[str, Any]]:
        """解析场景规划"""

        # 默认分为3-4个场景
        scene_count = 3 if target_word_count < 2500 else 4
        words_per_scene = target_word_count // scene_count

        scenes = []
        for i in range(scene_count):
            scenes.append({
                "id": f"scene_{i+1}",
                "title": f"场景{i+1}",
                "purpose": ["开场", "发展", "转折", "结尾"][i % 4],
                "target_word_count": words_per_scene,
                "characters": ["主角"],
                "location": "未指定地点",
                "mood": "中性",
                "pacing": "medium"
            })

        return scenes

    async def _write_scene(
        self,
        scene_info: Dict[str, Any],
        story_context: Dict[str, Any],
        writing_style: str
    ) -> Scene:
        """写作场景"""

        # 获取写作风格设定
        style_config = self.writing_styles.get(writing_style, {})

        prompt = self.prompt_manager.get_prompt(
            "writing",
            "scene_writing",
            scene_purpose=scene_info.get("purpose", ""),
            characters=scene_info.get("characters", []),
            location=scene_info.get("location", ""),
            mood=scene_info.get("mood", ""),
            target_word_count=scene_info.get("target_word_count", 800),
            writing_style=style_config,
            story_context=story_context
        )

        response = await self.llm_service.generate_text(
            prompt,
            temperature=0.8,  # 提高创造性
            max_tokens=int(scene_info.get("target_word_count", 800) * 1.5)
        )

        scene_content = response.content

        return Scene(
            id=scene_info["id"],
            title=scene_info.get("title", ""),
            content=scene_content,
            word_count=len(scene_content),
            characters=scene_info.get("characters", []),
            location=scene_info.get("location", ""),
            purpose=scene_info.get("purpose", ""),
            mood=scene_info.get("mood", ""),
            pacing=scene_info.get("pacing", "medium")
        )

    async def _assemble_chapter(
        self,
        chapter_info: Dict[str, Any],
        scenes: List[Scene],
        story_context: Dict[str, Any]
    ) -> ChapterContent:
        """组装章节"""

        # 连接场景内容
        full_content = "\n\n".join([scene.content for scene in scenes])

        # 计算各种比例
        dialogue_ratio = self._calculate_dialogue_ratio(full_content)
        description_ratio = self._calculate_description_ratio(full_content)
        action_ratio = 1.0 - dialogue_ratio - description_ratio

        # 分析情感弧线
        emotional_arc = await self._analyze_emotional_arc(scenes)

        return ChapterContent(
            chapter_number=chapter_info.get("number", 1),
            title=chapter_info.get("title", f"第{chapter_info.get('number', 1)}章"),
            summary=chapter_info.get("summary", ""),
            scenes=scenes,
            total_word_count=sum(scene.word_count for scene in scenes),
            key_events=chapter_info.get("key_events", []),
            character_focus=chapter_info.get("character_focus", []),
            plot_advancement=chapter_info.get("plot_advancement", ""),
            emotional_arc=emotional_arc,
            dialogue_ratio=dialogue_ratio,
            description_ratio=description_ratio,
            action_ratio=action_ratio,
            previous_chapter_connection="",
            next_chapter_setup=""
        )

    def _calculate_dialogue_ratio(self, content: str) -> float:
        """计算对话占比"""
        # 简单统计引号内容
        dialogue_chars = 0
        in_dialogue = False

        for char in content:
            if char in ['"', '"', '"', '「', '」']:
                in_dialogue = not in_dialogue
            elif in_dialogue:
                dialogue_chars += 1

        return min(dialogue_chars / max(len(content), 1), 1.0)

    def _calculate_description_ratio(self, content: str) -> float:
        """计算描述占比"""
        # 简单估算：非对话且包含描述性词汇的部分
        description_keywords = ["美丽", "壮观", "幽暗", "金色", "高大", "细腻", "华丽"]
        description_chars = 0

        sentences = content.split("。")
        for sentence in sentences:
            if any(keyword in sentence for keyword in description_keywords):
                description_chars += len(sentence)

        return min(description_chars / max(len(content), 1), 1.0)

    async def _analyze_emotional_arc(self, scenes: List[Scene]) -> str:
        """分析情感弧线"""
        mood_progression = [scene.mood for scene in scenes]
        return f"情感发展：{' -> '.join(mood_progression)}"

    def _load_writing_styles(self) -> Dict[str, Dict[str, Any]]:
        """加载写作风格配置"""
        return {
            "traditional": {
                "tone": "古典优雅",
                "sentence_length": "medium",
                "vocabulary": "文言色彩",
                "description_density": "high"
            },
            "modern": {
                "tone": "现代直白",
                "sentence_length": "short",
                "vocabulary": "现代白话",
                "description_density": "medium"
            },
            "poetic": {
                "tone": "诗意浪漫",
                "sentence_length": "varied",
                "vocabulary": "诗性语言",
                "description_density": "very_high"
            },
            "action": {
                "tone": "紧张刺激",
                "sentence_length": "short",
                "vocabulary": "动感强烈",
                "description_density": "low"
            }
        }


class ChapterWriterTool(AsyncTool):
    """章节写作工具"""

    def __init__(self):
        super().__init__()
        self.writer = ChapterWriter()

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="chapter_writer",
            description="写作完整的小说章节，包括场景规划、内容生成、质量控制",
            category="writing",
            parameters=[
                ToolParameter(
                    name="chapter_info",
                    type="object",
                    description="章节信息（编号、标题、摘要等）",
                    required=True
                ),
                ToolParameter(
                    name="story_context",
                    type="object",
                    description="故事上下文（角色、世界观、前情等）",
                    required=True
                ),
                ToolParameter(
                    name="writing_style",
                    type="string",
                    description="写作风格：traditional/modern/poetic/action",
                    required=False,
                    default="traditional"
                ),
                ToolParameter(
                    name="target_word_count",
                    type="integer",
                    description="目标字数",
                    required=False,
                    default=3000
                )
            ],
            examples=[
                {
                    "parameters": {
                        "chapter_info": {
                            "number": 1,
                            "title": "初入江湖",
                            "summary": "主角离开家乡，开始修仙之路"
                        },
                        "story_context": {
                            "protagonist": "林风",
                            "world": "修仙大陆"
                        },
                        "writing_style": "traditional",
                        "target_word_count": 3000
                    },
                    "result": "完整的章节内容"
                }
            ],
            tags=["writing", "chapter", "content"]
        )

    async def execute(self, parameters: Dict[str, Any],
                     context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行章节写作"""

        chapter_info = parameters.get("chapter_info", {})
        story_context = parameters.get("story_context", {})
        writing_style = parameters.get("writing_style", "traditional")
        target_word_count = parameters.get("target_word_count", 3000)

        chapter_content = await self.writer.write_chapter(
            chapter_info, story_context, writing_style, target_word_count
        )

        return {
            "chapter": asdict(chapter_content),
            "generation_info": {
                "writing_style": writing_style,
                "target_word_count": target_word_count,
                "actual_word_count": chapter_content.total_word_count
            }
        }
