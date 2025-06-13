# modules/writing/dialogue_writer.py
"""
对话写作器
专门处理角色对话的生成和优化
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from core.base_tools import AsyncTool, ToolDefinition, ToolParameter
from core.llm_client import get_llm_service
from config.settings import get_prompt_manager


@dataclass
class DialogueLine:
    """对话行"""
    speaker: str
    content: str
    emotion: str
    action: Optional[str] = None  # 伴随动作
    internal_thought: Optional[str] = None  # 内心想法
    subtext: Optional[str] = None  # 潜台词


@dataclass
class DialogueExchange:
    """对话交换"""
    participants: List[str]
    topic: str
    context: str
    emotional_arc: str
    lines: List[DialogueLine]
    word_count: int


class DialogueWriter:
    """对话写作器"""

    # 情感图定义（有向图）
    EMOTION_GRAPH: Dict[str, List[str]] = {
        # 核心节点
        "neutral": ["担忧", "平静", "悲伤", "期待", "困惑"],
        "平静": ["不安", "中性", "满足", "期待"],
        "不安": ["紧张", "平静", "恐惧"],
        "紧张": ["愤怒", "不安", "焦虑"],
        "愤怒": ["中性", "懊悔", "疲惫", "满足"],
        "悲伤": ["反思", "中性", "忧郁", "怀旧"],
        "反思": ["醒悟", "悲伤", "困惑"],
        "醒悟": ["坚定", "反思", "希望"],
        "坚定": ["希望", "中性", "满足"],

        # 特殊情感路径
        "担忧": ["沉重", "困惑"],
        "沉重": ["悲壮与决绝", "决心"],
        "悲壮与决绝": ["坚定", "释然"],
        "期待": ["兴奋", "焦虑"],
        "困惑": ["好奇", "醒悟"],
        "怀旧": ["感伤", "温暖"],
        "感伤": ["释然", "忧郁"],

        # 终端节点
        "满足": [],
        "希望": [],
        "释然": [],
        "恐惧": [],
        "疲惫": [],
        "忧郁": [],
        "温暖": [],
        "决心": [],
        "兴奋": [],
        "焦虑": [],
        "好奇": [],
        "懊悔": []
    }

    def __init__(self):
        self.llm_service = get_llm_service()
        self.prompt_manager = get_prompt_manager()
        self.character_voices = {}  # 角色语音风格缓存

    async def write_dialogue_exchange(
        self,
        participants: List[str],
        topic: str,
        context: str,
        character_info: Dict[str, Dict],
        emotional_goal: str = "neutral",
        length: str = "medium"
    ) -> DialogueExchange:
        """写作对话交换"""

        # 分析角色声音
        for participant in participants:
            if participant not in self.character_voices:
                self.character_voices[participant] = await self._analyze_character_voice(
                    participant, character_info.get(participant, {})
                )

        # 规划对话结构
        dialogue_plan = await self._plan_dialogue_structure(
            participants, topic, emotional_goal, length
        )

        # 生成对话内容
        dialogue_lines = await self._generate_dialogue_lines(
            dialogue_plan, context, character_info
        )

        # 润色和优化
        refined_lines = await self._refine_dialogue(dialogue_lines)

        return DialogueExchange(
            participants=participants,
            topic=topic,
            context=context,
            emotional_arc=emotional_goal,
            lines=refined_lines,
            word_count=sum(len(line.content) for line in refined_lines)
        )

    async def write_character_monologue(
        self,
        character: str,
        internal_state: str,
        trigger_event: str,
        character_info: Dict[str, Any],
        word_count: int = 200
    ) -> str:
        """写作角色独白"""

        prompt = self.prompt_manager.get_prompt(
            "writing",
            "monologue",
            character=character,
            internal_state=internal_state,
            trigger=trigger_event,
            character_traits=character_info.get("personality", {}),
            word_count=word_count
        )

        response = await self.llm_service.generate_text(
            prompt,
            temperature=0.8,
            max_tokens=int(word_count * 1.5)
        )

        return response.content

    async def write_exposition_dialogue(
        self,
        info_to_convey: str,
        speaker: str,
        listener: str,
        relationship: str,
        natural_context: str
    ) -> List[DialogueLine]:
        """写作说明性对话（自然地传递信息）"""

        prompt = self.prompt_manager.get_prompt(
            "writing",
            "exposition_dialogue",
            information=info_to_convey,
            speaker=speaker,
            listener=listener,
            relationship=relationship,
            context=natural_context
        )

        response = await self.llm_service.generate_text(prompt, temperature=0.7)

        return self._parse_dialogue_response(response.content)

    async def _analyze_character_voice(
        self,
        character: str,
        character_info: Dict[str, Any]
    ) -> Dict[str, str]:
        """分析角色说话风格"""

        personality = character_info.get("personality", {})
        background = character_info.get("background", {})

        # 基于角色信息确定说话风格
        voice_style = {
            "formality": "formal" if "正式" in str(personality) else "informal",
            "vocabulary": "advanced" if "博学" in str(background) else "simple",
            "sentence_length": "long" if "文雅" in str(personality) else "short",
            "emotional_expression": "restrained" if "内敛" in str(personality) else "open",
            "speech_patterns": ["习惯用语", "口头禅"],
            "cultural_background": background.get("culture", "通用")
        }

        return voice_style

    def _create_emotional_progression(self, start_emotion: str, target_emotion: str) -> List[str]:
        """创建情感发展弧线，使用图搜索算法寻找合理路径"""

        # 特殊情况处理
        if start_emotion == target_emotion:
            return [start_emotion]

        # 检查情感是否在图中
        all_emotions = set(self.EMOTION_GRAPH.keys())
        for e in (start_emotion, target_emotion):
            if e not in all_emotions:
                # 尝试标准化处理
                normalized = self._normalize_emotion(e)
                if normalized != e:
                    return self._create_emotional_progression(normalized, target_emotion)
                return [start_emotion, target_emotion]

        # BFS搜索最短路径
        path = self._bfs_search(start_emotion, target_emotion)
        if path:
            return path

        # 尝试通过中性节点过渡
        if "neutral" in all_emotions:
            path_via_neutral = (
                self._bfs_search(start_emotion, "neutral") +
                self._bfs_search("neutral", target_emotion)[1:]
            )
            if (len(path_via_neutral) > 1 and
                path_via_neutral[0] == start_emotion and
                path_via_neutral[-1] == target_emotion):
                return path_via_neutral

        # 添加通用过渡状态作为兜底方案
        return self._fallback_path(start_emotion, target_emotion)

    def _bfs_search(self, start: str, end: str) -> List[str]:
        """使用BFS算法寻找最短情感路径"""
        from collections import deque
        queue = deque([[start]])
        visited = {start}

        while queue:
            path = queue.popleft()
            current = path[-1]

            if current == end:
                return path

            for neighbor in self.EMOTION_GRAPH.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    new_path = path + [neighbor]
                    queue.append(new_path)

        return []

    def _normalize_emotion(self, emotion: str) -> str:
        """情感名称标准化处理"""
        aliases = {
            "neutral": ["中性", "平常", "自然"],
            "sad": ["悲伤", "伤心", "悲哀"],
            "angry": ["愤怒", "生气", "怒火"],
            "joy": ["快乐", "开心", "喜悦"]
        }

        for std_emotion, variants in aliases.items():
            if emotion in variants:
                return std_emotion
        return emotion

    def _fallback_path(self, start: str, end: str) -> List[str]:
        """生成默认过渡路径"""
        common_transitions = {
            ("positive", "negative"): [start, "反思", "neutral", end],
            ("negative", "positive"): [start, "neutral", "希望", end],
            ("intense", "calm"): [start, "疲惫", "平静", end],
            ("calm", "intense"): [start, "不安", "紧张", end]
        }

        # 情感分类逻辑（简化版）
        emotion_types = {
            "positive": ["joy", "满足", "希望", "温暖", "兴奋"],
            "negative": ["sad", "愤怒", "恐惧", "忧郁", "懊悔"],
            "intense": ["愤怒", "紧张", "兴奋", "焦虑"],
            "calm": ["平静", "满足", "neutral", "释然"]
        }

        # 检测情感类型
        start_type = next((t for t, ems in emotion_types.items() if start in ems), "")
        end_type = next((t for t, ems in emotion_types.items() if end in ems), "")

        return common_transitions.get(
            (start_type, end_type),
            [start, "neutral", end] if "neutral" in self.EMOTION_GRAPH else [start, end]
        )

    def add_custom_path(self, path: List[str]):
        """添加自定义情感路径到图中"""
        for i in range(len(path) - 1):
            current = path[i]
            next_emo = path[i + 1]

            if current not in self.EMOTION_GRAPH:
                self.EMOTION_GRAPH[current] = []

            if next_emo not in self.EMOTION_GRAPH[current]:
                self.EMOTION_GRAPH[current].append(next_emo)

            # 确保终点也在图中
            if next_emo not in self.EMOTION_GRAPH:
                self.EMOTION_GRAPH[next_emo] = []

    async def _plan_dialogue_structure(
        self,
        participants: List[str],
        topic: str,
        emotional_goal: str,
        length: str
    ) -> Dict[str, Any]:
        """规划对话结构"""

        line_count_map = {
            "short": 4,
            "medium": 8,
            "long": 15
        }

        line_count = line_count_map.get(length, 8)
        # 🔥 在这里调用 _create_emotional_progression
        emotional_progression = self._create_emotional_progression(
            start_emotion="neutral",  # 或者根据context动态确定
            target_emotion=emotional_goal
        )
        return {
            "total_lines": line_count,
            "structure": "opening-development-resolution",
            "emotional_progression": emotional_progression,
            "information_flow": "gradual",
            "turn_taking": "balanced"
        }

    async def _generate_dialogue_lines(
        self,
        plan: Dict[str, Any],
        context: str,
        character_info: Dict[str, Dict]
    ) -> List[DialogueLine]:
        """生成对话行"""

        lines = []
        total_lines = plan["total_lines"]
        participants = list(character_info.keys())

        for i in range(total_lines):
            speaker = participants[i % len(participants)]

            # 确定当前情绪状态
            progress = i / total_lines
            if progress < 0.3:
                emotion = "neutral"
            elif progress < 0.7:
                emotion = plan["emotional_progression"][1]
            else:
                emotion = plan["emotional_progression"][2]

            # 生成对话内容
            prompt = f"""
            请为角色{speaker}写一句对话，要求：
            - 符合其说话风格：{self.character_voices.get(speaker, {})}
            - 当前情绪：{emotion}
            - 对话进度：{progress:.1%}
            - 上下文：{context}

            只返回对话内容，不要其他解释：
            """

            response = await self.llm_service.generate_text(
                prompt, temperature=0.8, max_tokens=100
            )

            line = DialogueLine(
                speaker=speaker,
                content=response.content.strip(),
                emotion=emotion,
                action=self._generate_action_tag(emotion) if i % 3 == 0 else None
            )

            lines.append(line)

        return lines

    def _generate_action_tag(self, emotion: str) -> str:
        """生成动作标签"""
        action_map = {
            "angry": "皱眉",
            "sad": "叹气",
            "happy": "微笑",
            "surprised": "瞪大眼睛",
            "fear": "后退一步",
            "neutral": "点头"
        }

        return action_map.get(emotion, "停顿")

    async def _refine_dialogue(self, lines: List[DialogueLine]) -> List[DialogueLine]:
        """润色对话"""

        # 检查重复用词
        # 平衡对话长度
        # 增强角色声音差异

        return lines  # 暂时直接返回

    def _parse_dialogue_response(self, response: str) -> List[DialogueLine]:
        """解析对话响应"""

        # 简单解析，实际可以更复杂
        lines = []
        sentences = response.split("\n")

        for i, sentence in enumerate(sentences):
            if sentence.strip():
                lines.append(DialogueLine(
                    speaker=f"角色{i % 2 + 1}",
                    content=sentence.strip(),
                    emotion="neutral"
                ))

        return lines


class DialogueWriterTool(AsyncTool):
    """对话写作工具"""

    def __init__(self):
        super().__init__()
        self.writer = DialogueWriter()

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="dialogue_writer",
            description="专业的对话写作工具，生成自然、符合角色特点的对话",
            category="writing",
            parameters=[
                ToolParameter(
                    name="dialogue_type",
                    type="string",
                    description="对话类型：exchange/monologue/exposition",
                    required=True
                ),
                ToolParameter(
                    name="participants",
                    type="array",
                    description="对话参与者",
                    required=False
                ),
                ToolParameter(
                    name="topic",
                    type="string",
                    description="对话主题",
                    required=False
                ),
                ToolParameter(
                    name="context",
                    type="string",
                    description="对话背景",
                    required=False
                ),
                ToolParameter(
                    name="character_info",
                    type="object",
                    description="角色信息",
                    required=False
                ),
                ToolParameter(
                    name="emotional_goal",
                    type="string",
                    description="情感目标",
                    required=False,
                    default="neutral"
                ),
                ToolParameter(
                    name="length",
                    type="string",
                    description="对话长度：short/medium/long",
                    required=False,
                    default="medium"
                )
            ]
        )

    async def execute(self, parameters: Dict[str, Any],
                      context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行对话写作"""

        dialogue_type = parameters.get("dialogue_type")

        if dialogue_type == "exchange":
            exchange = await self.writer.write_dialogue_exchange(
                parameters.get("participants", ["角色1", "角色2"]),
                parameters.get("topic", "对话主题"),
                parameters.get("context", "对话背景"),
                parameters.get("character_info", {}),
                parameters.get("emotional_goal", "neutral"),
                parameters.get("length", "medium")
            )
            return {"dialogue_exchange": asdict(exchange)}

        elif dialogue_type == "monologue":
            monologue = await self.writer.write_character_monologue(
                parameters.get("character", "角色"),
                parameters.get("internal_state", "思考状态"),
                parameters.get("trigger_event", "触发事件"),
                parameters.get("character_info", {}),
                parameters.get("word_count", 200)
            )
            return {"monologue": monologue}

        else:
            return {"error": "不支持的对话类型"}

