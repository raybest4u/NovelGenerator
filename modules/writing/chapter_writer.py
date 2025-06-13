# modules/writing/chapter_writer.py - 修复版本
"""
章节写作器
负责生成完整的章节内容
"""

import re
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from core.base_tools import AsyncTool, ToolDefinition, ToolParameter
from core.llm_client import get_llm_service
from config.settings import get_prompt_manager
import asyncio
import hashlib
import time


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
        # 简单的内存缓存
        self._cache = {}
        self._cache_expire_time = 3600  # 1小时

    def _get_cache_key(self, *args, **kwargs) -> str:
        """生成缓存键"""
        cache_data = {
            'args': args,
            'kwargs': kwargs
        }
        cache_str = json.dumps(cache_data, sort_keys=True, default=str)
        return hashlib.md5(cache_str.encode()).hexdigest()

    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """从缓存获取数据"""
        if cache_key in self._cache:
            result, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self._cache_expire_time:
                return result
            else:
                # 删除过期缓存
                del self._cache[cache_key]
        return None

    def _set_cache(self, cache_key: str, result: Any):
        """设置缓存"""
        self._cache[cache_key] = (result, time.time())

    async def write_chapter(
        self,
        chapter_info: Dict[str, Any],
        story_context: Dict[str, Any],
        writing_style: str = "traditional",
        target_word_count: int = 3000
    ) -> ChapterContent:
        """写作章节"""

        # 生成缓存键
        cache_key = self._get_cache_key(
            chapter_info, story_context, writing_style, target_word_count
        )

        # 检查缓存
        cached_result = self._get_from_cache(cache_key)
        if cached_result is not None:
            return cached_result

        # 规划章节结构
        scene_plan = await self._plan_chapter_scenes(
            chapter_info, story_context, target_word_count
        )

        # 生成各个场景
        scenes = []
        for scene_info in scene_plan:
            scene = await self._write_scene(
                scene_info, story_context, writing_style, chapter_info
            )
            scenes.append(scene)

        # 连接场景并润色
        chapter_content = await self._assemble_chapter(
            chapter_info, scenes, story_context
        )

        # 缓存结果
        self._set_cache(cache_key, chapter_content)

        return chapter_content

    async def _plan_chapter_scenes(
        self,
        chapter_info: Dict[str, Any],
        story_context: Dict[str, Any],
        target_word_count: int
    ) -> List[Dict[str, Any]]:
        """规划章节场景"""

        # 获取详细的章节信息
        chapter_scenes = chapter_info.get("scenes", [])
        chapter_summary = chapter_info.get("detailed_summary", chapter_info.get("summary", ""))
        key_events = chapter_info.get("key_events", [])
        core_conflict = chapter_info.get("core_conflict", "")

        if chapter_scenes:
            # 如果有预定义的场景，使用它们
            scene_plan = []
            words_per_scene = target_word_count // max(len(chapter_scenes), 1)

            for i, scene_data in enumerate(chapter_scenes):
                scene_plan.append({
                    "id": f"scene_{i + 1}",
                    "title": f"场景{i + 1}",
                    "purpose": scene_data.get("purpose", "推进情节"),
                    "location": scene_data.get("location", "未指定地点"),
                    "characters": scene_data.get("characters",
                                                 chapter_info.get("character_focus", ["主角"])),
                    "events": scene_data.get("events", []),
                    "mood": scene_data.get("mood", chapter_info.get("mood", "中性")),
                    "target_word_count": words_per_scene,
                    "pacing": "medium"
                })

            return scene_plan
        else:
            # 使用LLM规划场景
            prompt = f"""
            请为第{chapter_info.get('number', 1)}章规划3-4个场景：

            章节信息：
            - 标题：{chapter_info.get('title', '')}
            - 摘要：{chapter_summary}
            - 关键事件：{key_events}
            - 核心冲突：{core_conflict}
            - 主要角色：{chapter_info.get('character_focus', [])}
            - 目标字数：{target_word_count}

            故事背景：
            - 世界设定：{story_context.get('world_setting', {}).get('name', '未知世界')}
            - 主要角色：{[char.get('name', '未知') for char in story_context.get('characters', [])]}

            请规划3-4个场景，每个场景包含：
            1. 场景标题
            2. 场景地点
            3. 参与角色
            4. 主要事件
            5. 场景目的
            6. 情绪氛围
            7. 预期字数

            请以JSON格式返回场景列表：
            [
                {{
                    "title": "场景标题",
                    "location": "地点",
                    "characters": ["角色1", "角色2"],
                    "events": ["事件1", "事件2"],
                    "purpose": "场景目的",
                    "mood": "情绪氛围",
                    "word_count": 800
                }}
            ]
            """

            response = await self.llm_service.generate_text(prompt, temperature=0.7)
            return self._parse_scene_plan_from_llm(response.content, target_word_count)

    def _parse_scene_plan_from_llm(self, response: str, target_word_count: int) -> List[
        Dict[str, Any]]:
        """从LLM响应解析场景规划"""
        try:
            # 尝试提取JSON
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                scenes_data = json.loads(json_match.group())

                scene_plan = []
                for i, scene_data in enumerate(scenes_data):
                    scene_plan.append({
                        "id": f"scene_{i + 1}",
                        "title": scene_data.get("title", f"场景{i + 1}"),
                        "purpose": scene_data.get("purpose", "推进情节"),
                        "location": scene_data.get("location", "未指定地点"),
                        "characters": scene_data.get("characters", ["主角"]),
                        "events": scene_data.get("events", []),
                        "mood": scene_data.get("mood", "中性"),
                        "target_word_count": scene_data.get("word_count",
                                                            target_word_count // len(scenes_data)),
                        "pacing": "medium"
                    })

                return scene_plan
        except:
            pass

        # 如果解析失败，生成默认场景
        return self._generate_default_scenes(target_word_count)

    def _generate_default_scenes(self, target_word_count: int) -> List[Dict[str, Any]]:
        """生成默认场景"""
        scene_count = 3 if target_word_count < 2500 else 4
        words_per_scene = target_word_count // scene_count

        scenes = []
        purposes = ["开场铺垫", "情节发展", "冲突高潮", "收尾过渡"]

        for i in range(scene_count):
            scenes.append({
                "id": f"scene_{i + 1}",
                "title": f"场景{i + 1}",
                "purpose": purposes[i % len(purposes)],
                "target_word_count": words_per_scene,
                "characters": ["主角"],
                "location": "未指定地点",
                "mood": "中性",
                "pacing": "medium",
                "events": [f"第{i + 1}个场景的事件"]
            })

        return scenes

    async def _write_scene(
        self,
        scene_info: Dict[str, Any],
        story_context: Dict[str, Any],
        writing_style: str,
        chapter_info: Dict[str, Any]
    ) -> Scene:
        """写作场景"""

        # 获取写作风格设定
        style_config = self.writing_styles.get(writing_style, {})

        # 构建场景的具体信息
        scene_events = scene_info.get("events", [])
        scene_characters = scene_info.get("characters", [])
        scene_location = scene_info.get("location", "未指定地点")
        scene_purpose = scene_info.get("purpose", "推进情节")
        scene_mood = scene_info.get("mood", "中性")

        # 获取角色详细信息
        character_details = {}
        for char in story_context.get("characters", []):
            char_name = char.get("name", "")
            if char_name in scene_characters:
                character_details[char_name] = char

        prompt = f"""
        请写作一个具体的小说场景：

        场景信息：
        - 场景标题：{scene_info.get('title', '')}
        - 场景地点：{scene_location}
        - 场景目的：{scene_purpose}
        - 主要事件：{scene_events}
        - 参与角色：{scene_characters}
        - 情绪氛围：{scene_mood}
        - 目标字数：{scene_info.get('target_word_count', 800)}

        章节背景：
        - 章节标题：{chapter_info.get('title', '')}
        - 章节摘要：{chapter_info.get('detailed_summary', '')}
        - 核心冲突：{chapter_info.get('core_conflict', '')}

        角色信息：
        {json.dumps(character_details, ensure_ascii=False, indent=2)}

        世界设定：
        - 世界名称：{story_context.get('world_setting', {}).get('name', '未知世界')}
        - 世界类型：{story_context.get('world_setting', {}).get('type', '未知')}
        - 文化背景：{story_context.get('world_setting', {}).get('culture_notes', '')}

        写作要求：
        1. 严格按照场景信息写作
        2. 确保事件按顺序发生：{' -> '.join(scene_events) if scene_events else '自然发展'}
        3. 角色行为符合其性格设定
        4. 场景描写生动有画面感
        5. 对话自然符合角色特点
        6. 体现{scene_mood}的情绪氛围
        7. 实现{scene_purpose}的目的
        8. 语言风格：{style_config.get('tone', '自然流畅')}
        9. 字数控制在{scene_info.get('target_word_count', 800)}字左右

        请直接开始写作场景内容，不要添加解释或说明：
        """

        response = await self.llm_service.generate_text(
            prompt,
            temperature=0.8,  # 提高创造性
            max_tokens=int(scene_info.get("target_word_count", 800) * 1.5)
        )

        scene_content = response.content.strip()

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
        action_ratio = max(0, 1.0 - dialogue_ratio - description_ratio)

        # 分析情感弧线
        emotional_arc = await self._analyze_emotional_arc(scenes)

        return ChapterContent(
            chapter_number=chapter_info.get("number", 1),
            title=chapter_info.get("title", f"第{chapter_info.get('number', 1)}章"),
            summary=chapter_info.get("detailed_summary", chapter_info.get("summary", "")),
            scenes=scenes,
            total_word_count=sum(scene.word_count for scene in scenes),
            key_events=chapter_info.get("key_events", []),
            character_focus=chapter_info.get("character_focus", []),
            plot_advancement=chapter_info.get("plot_advancement", ""),
            emotional_arc=emotional_arc,
            dialogue_ratio=dialogue_ratio,
            description_ratio=description_ratio,
            action_ratio=action_ratio,
            previous_chapter_connection=chapter_info.get("chapter_ending", ""),
            next_chapter_setup=""
        )

    def _calculate_dialogue_ratio(self, content: str) -> float:
        """计算对话占比"""
        # 统计引号内容
        dialogue_chars = 0
        in_dialogue = False

        for char in content:
            if char in ['"', '"', '"', '「', '」', '『', '』']:
                in_dialogue = not in_dialogue
            elif in_dialogue:
                dialogue_chars += 1

        return min(dialogue_chars / max(len(content), 1), 1.0)

    def _calculate_description_ratio(self, content: str) -> float:
        """计算描述占比"""
        # 统计描述性词汇
        description_keywords = [
            "美丽", "壮观", "幽暗", "金色", "高大", "细腻", "华丽", "雄伟",
            "清澈", "朦胧", "绚烂", "苍凉", "宁静", "热闹", "神秘", "古老"
        ]
        description_chars = 0

        sentences = content.split("。")
        for sentence in sentences:
            if any(keyword in sentence for keyword in description_keywords):
                description_chars += len(sentence)

        return min(description_chars / max(len(content), 1), 1.0)

    async def _analyze_emotional_arc(self, scenes: List[Scene]) -> str:
        """分析情感弧线 - 支持情感发展变化"""
        if not scenes:
            return "情感发展：平静"

        # 定义情感强度映射
        emotion_intensity = {
            "平静": 1, "宁静": 1, "安详": 1,
            "好奇": 2, "期待": 2, "兴奋": 2,
            "担忧": 3, "紧张": 3, "不安": 3,
            "猜疑与试探的紧绷感": 4, "焦虑": 4, "恐惧": 4,
            "愤怒": 5, "绝望": 5, "狂怒": 5,
            "悲伤": 3, "沮丧": 3, "失落": 3,
            "坚定": 4, "决心": 4, "勇敢": 4,
            "希望": 3, "感动": 3, "温暖": 2,
            "震惊": 4, "惊讶": 3, "困惑": 2
        }

        # 定义情感发展模式
        emotion_patterns = {
            "上升": ["平静", "期待", "兴奋", "高潮"],
            "下降": ["兴奋", "担忧", "沮丧", "绝望"],
            "波动": ["平静", "紧张", "缓解", "再度紧张"],
            "转折": ["绝望", "反思", "觉醒", "坚定"],
            "渐进": ["好奇", "探索", "发现", "理解"]
        }

        # 如果所有场景情感相同，需要创建变化
        moods = [scene.mood for scene in scenes]
        unique_moods = set(moods)

        if len(unique_moods) == 1:
            # 所有情感相同，需要创建发展弧线
            base_emotion = moods[0]
            base_intensity = emotion_intensity.get(base_emotion, 3)

            # 根据场景数量和基础情感创建弧线
            scene_count = len(scenes)

            if scene_count <= 2:
                # 短章节：简单发展
                if base_intensity <= 2:
                    return f"情感发展：{base_emotion} -> 深入思考 -> 有所领悟"
                else:
                    return f"情感发展：{base_emotion} -> 情感加深 -> 某种释然"

            elif scene_count <= 4:
                # 中等章节：三段式发展
                if "紧绷" in base_emotion or "猜疑" in base_emotion:
                    return f"情感发展：{base_emotion} -> 试探与观察 -> 真相逐渐明晰 -> 紧张缓解或加剧"
                elif base_intensity >= 4:
                    return f"情感发展：{base_emotion} -> 情感波动 -> 内心挣扎 -> 情感转化"
                else:
                    return f"情感发展：{base_emotion} -> 情感深化 -> 新的认知 -> 心境变化"

            else:
                # 长章节：多层次发展
                if "紧绷" in base_emotion:
                    return f"情感发展：{base_emotion} -> 谨慎试探 -> 逐步深入 -> 关键发现 -> 情感转折"
                else:
                    return f"情感发展：{base_emotion} -> 情感酝酿 -> 逐步加深 -> 达到高潮 -> 回归平静"

        else:
            # 情感有变化，分析发展趋势
            emotion_values = [emotion_intensity.get(mood, 3) for mood in moods]

            # 计算趋势
            if emotion_values[-1] > emotion_values[0] + 1:
                trend = "递增"
            elif emotion_values[-1] < emotion_values[0] - 1:
                trend = "递减"
            else:
                trend = "波动"

            # 简化重复的情感
            simplified_moods = []
            for i, mood in enumerate(moods):
                if i == 0 or mood != moods[i - 1]:
                    simplified_moods.append(mood)

            return f"情感发展：{' -> '.join(simplified_moods)}"

    async def _create_varied_scene_moods(self, chapter_info: Dict[str, Any], scene_count: int) -> \
    List[str]:
        """为场景创建多样化的情感"""
        base_mood = chapter_info.get("mood", "平静")
        chapter_purpose = chapter_info.get("purpose", "")

        # 根据章节目的和基础情感创建情感发展
        if "猜疑" in base_mood or "试探" in base_mood:
            if scene_count <= 2:
                return ["谨慎观察", "试探与发现"]
            elif scene_count <= 4:
                return ["初始警觉", "谨慎试探", "发现线索", "真相显现"]
            else:
                return ["表面平静", "暗中观察", "小心试探", "发现异常", "真相逼近"]

        elif "紧张" in base_mood:
            return self._create_tension_progression(scene_count)

        elif "平静" in base_mood:
            return self._create_calm_progression(scene_count, chapter_purpose)

        else:
            # 默认情感发展
            return self._create_default_progression(base_mood, scene_count)

    def _create_tension_progression(self, scene_count: int) -> List[str]:
        """创建紧张情感发展"""
        progressions = {
            2: ["暗流涌动", "紧张爆发"],
            3: ["不安预感", "紧张升级", "关键时刻"],
            4: ["细微异常", "警觉提升", "紧张对峙", "结果揭晓"],
            5: ["平静表象", "异常发现", "紧张升级", "高度警觉", "真相大白"]
        }

        return progressions.get(scene_count, progressions[3])

    def _create_calm_progression(self, scene_count: int, purpose: str) -> List[str]:
        """创建平静情感发展"""
        if "对话" in purpose or "交流" in purpose:
            progressions = {
                2: ["轻松开始", "深入交流"],
                3: ["友好寒暄", "深度对话", "心灵共鸣"],
                4: ["自然相遇", "逐渐熟悉", "深入了解", "情感升华"]
            }
        else:
            progressions = {
                2: ["宁静致远", "内心感悟"],
                3: ["平静开始", "逐渐深入", "有所领悟"],
                4: ["安详环境", "细致观察", "深度思考", "心境升华"]
            }

        return progressions.get(scene_count, progressions.get(3, ["平静", "思考", "领悟"]))

    def _create_default_progression(self, base_mood: str, scene_count: int) -> List[str]:
        """创建默认情感发展"""
        # 基于基础情感创建合理的发展
        if scene_count == 1:
            return [base_mood]
        elif scene_count == 2:
            return [base_mood, f"{base_mood}的深化"]
        else:
            # 创建从基础情感出发的发展弧线
            return [base_mood] + [f"{base_mood}发展{i}" for i in range(1, scene_count)]

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
