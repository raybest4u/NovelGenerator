# modules/writing/chapter_writer.py - 修复版本
"""
章节写作器
负责生成完整的章节内容
"""

import re
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

from loguru import logger

from core.abstract_tools import ContentGeneratorTool
from core.base_tools import AsyncTool, ToolDefinition, ToolParameter
from core.cache_manager import cached
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
        scene_count: int = 4
    ) -> List[Dict[str, Any]]:
        """规划章节场景结构"""
        try:
            # 从缓存检查
            cache_key = self._get_cache_key("plan_scenes", chapter_info, scene_count)
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                logger.info("从缓存获取场景规划")
                return cached_result

            logger.info(f"开始规划 {scene_count} 个场景")

            # 生成场景规划提示
            prompt = self.prompt_manager.get_prompt(
                "writing",
                "scene_planning",
                chapter_info=chapter_info,
                story_context=story_context,
                scene_count=scene_count
            ) or f"""
            请为以下章节规划 {scene_count} 个场景：

            章节信息：
            - 章节号：第{chapter_info.get('number', 1)}章
            - 标题：{chapter_info.get('title', '未命名')}
            - 大纲：{chapter_info.get('summary', '')}
            - 关键事件：{chapter_info.get('key_events', [])}
            - 重点角色：{chapter_info.get('character_focus', [])}

            故事背景：
            {story_context.get('world_setting', '标准设定')}

            请按照以下JSON格式返回场景规划：
            [
                {{
                    "id": "scene_001",
                    "title": "场景标题",
                    "summary": "场景概要",
                    "location": "场景地点",
                    "characters": ["参与角色1", "角色2"],
                    "purpose": "场景目的（推进情节/角色发展/营造氛围等）",
                    "key_events": ["主要事件1", "事件2"],
                    "mood": "情绪氛围",
                    "pacing": "节奏（slow/medium/fast）",
                    "target_word_count": 800,
                    "transitions": {{
                        "from_previous": "与上个场景的连接",
                        "to_next": "为下个场景的铺垫"
                    }}
                }}
            ]

            要求：
            1. 场景之间要有逻辑连接
            2. 情绪起伏要有变化
            3. 每个场景都要推进剧情或发展角色
            4. 总字数控制在{chapter_info.get('target_word_count', 3000)}字左右
            """

            response = await self.llm_service.generate_text(
                prompt,
                temperature=0.7,
                max_tokens=1500
            )

            # 解析JSON响应
            scenes_data = await self._parse_json_response(response.content)

            # 验证和完善场景数据
            scenes_plan = []
            for i, scene_data in enumerate(scenes_data):
                scene_plan = {
                    "id": scene_data.get("id", f"scene_{i+1:03d}"),
                    "title": scene_data.get("title", f"场景{i+1}"),
                    "summary": scene_data.get("summary", ""),
                    "location": scene_data.get("location", "未指定地点"),
                    "characters": scene_data.get("characters", []),
                    "purpose": scene_data.get("purpose", "推进剧情"),
                    "key_events": scene_data.get("key_events", []),
                    "mood": scene_data.get("mood", "平稳"),
                    "pacing": scene_data.get("pacing", "medium"),
                    "target_word_count": scene_data.get("target_word_count",
                                                       chapter_info.get('target_word_count', 3000) // scene_count),
                    "transitions": scene_data.get("transitions", {
                        "from_previous": "自然过渡",
                        "to_next": "为下一场景做准备"
                    })
                }
                scenes_plan.append(scene_plan)

            # 存入缓存
            self._set_cache(cache_key, scenes_plan)

            logger.info(f"场景规划完成：{len(scenes_plan)}个场景")
            return scenes_plan

        except Exception as e:
            logger.error(f"场景规划失败: {e}")
            # 返回默认场景规划
            return self._create_default_scenes(scene_count, chapter_info)

    def _create_default_scenes(self, scene_count: int, chapter_info: Dict[str, Any]) -> List[
        Dict[str, Any]]:
        """创建默认场景规划"""
        default_scenes = []
        chapter_num = chapter_info.get('number', 1)
        target_words = chapter_info.get('target_word_count', 3000)
        words_per_scene = target_words // scene_count

        scene_templates = [
            {"title": "开场", "purpose": "设定场景", "mood": "平稳", "pacing": "slow"},
            {"title": "发展", "purpose": "推进情节", "mood": "紧张", "pacing": "medium"},
            {"title": "冲突", "purpose": "制造冲突", "mood": "激烈", "pacing": "fast"},
            {"title": "高潮", "purpose": "达到高潮", "mood": "紧张", "pacing": "fast"},
            {"title": "结尾", "purpose": "收尾", "mood": "平静", "pacing": "slow"}
        ]

        for i in range(scene_count):
            template = scene_templates[min(i, len(scene_templates) - 1)]
            scene = {
                "id": f"scene_{i + 1:03d}",
                "title": f"第{chapter_num}章 - {template['title']}",
                "summary": f"章节的{template['title']}部分",
                "location": "待定",
                "characters": chapter_info.get('character_focus', []),
                "purpose": template['purpose'],
                "key_events": [],
                "mood": template['mood'],
                "pacing": template['pacing'],
                "target_word_count": words_per_scene,
                "transitions": {
                    "from_previous": "承接上文",
                    "to_next": "引出下文"
                }
            }
            default_scenes.append(scene)

        return default_scenes


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
        style: str,
        chapter_info: Dict[str, Any]
    ) -> Scene:
        """写作单个场景"""
        try:
            # 缓存检查
            cache_key = self._get_cache_key("write_scene", scene_info, style)
            cached_scene = self._get_from_cache(cache_key)
            if cached_scene:
                logger.info(f"从缓存获取场景: {scene_info.get('title', 'unknown')}")
                return Scene(**cached_scene)

            logger.info(f"开始写作场景: {scene_info.get('title', 'unknown')}")

            # 获取写作风格配置
            style_config = self.writing_styles.get(style, self.writing_styles["modern"])

            # 构建场景写作提示
            scene_prompt = self._build_scene_prompt(scene_info, story_context, style_config)

            # 生成场景内容
            response = await self.llm_service.generate_text(
                scene_prompt,
                temperature=0.8,
                max_tokens=int(scene_info.get("target_word_count", 800) * 1.5)
            )

            scene_content = response.content.strip()

            # 创建场景对象
            scene = Scene(
                id=scene_info.get("id", "scene_unknown"),
                title=scene_info.get("title", ""),
                content=scene_content,
                word_count=len(scene_content),
                characters=scene_info.get("characters", []),
                location=scene_info.get("location", ""),
                purpose=scene_info.get("purpose", ""),
                mood=scene_info.get("mood", ""),
                pacing=scene_info.get("pacing", "medium")
            )

            # 存入缓存
            self._set_cache(cache_key, asdict(scene))

            logger.info(f"场景写作完成: {scene.word_count}字")
            return scene

        except Exception as e:
            logger.error(f"场景写作失败: {e}")
            # 返回基础场景
            return Scene(
                id=scene_info.get("id", "scene_error"),
                title=scene_info.get("title", "场景生成失败"),
                content=f"场景内容生成失败: {str(e)}",
                word_count=0,
                characters=scene_info.get("characters", []),
                location=scene_info.get("location", ""),
                purpose=scene_info.get("purpose", ""),
                mood=scene_info.get("mood", ""),
                pacing=scene_info.get("pacing", "medium")
            )

    def _build_scene_prompt(self, scene_info: Dict[str, Any],
                            story_context: Dict[str, Any],
                            style_config: Dict[str, Any]) -> str:
        """构建场景写作提示"""

        characters_info = story_context.get('characters', [])
        world_setting = story_context.get('world_setting', {})

        # 格式化角色信息
        char_descriptions = []
        scene_characters = scene_info.get('characters', [])
        for char_name in scene_characters:
            char_info = next((c for c in characters_info if c.get('name') == char_name), None)
            if char_info:
                char_descriptions.append(
                    f"- {char_name}: {char_info.get('description', '角色描述')}")
            else:
                char_descriptions.append(f"- {char_name}: 待描述角色")

        prompt = f"""
        请写作以下场景内容：

        【场景信息】
        - 标题：{scene_info.get('title', '未命名场景')}
        - 地点：{scene_info.get('location', '未指定')}
        - 目的：{scene_info.get('purpose', '推进剧情')}
        - 氛围：{scene_info.get('mood', '平稳')}
        - 节奏：{scene_info.get('pacing', 'medium')}
        - 目标字数：{scene_info.get('target_word_count', 800)}字

        【场景概要】
        {scene_info.get('summary', '场景发展概要')}

        【关键事件】
        {chr(10).join(f"- {event}" for event in scene_info.get('key_events', ['无特殊事件']))}

        【参与角色】
        {chr(10).join(char_descriptions) if char_descriptions else '- 无明确角色'}

        【世界背景】
        {world_setting.get('description', '标准奇幻世界设定')}

        【写作风格要求】
        - 语调：{style_config.get('tone', '自然流畅')}
        - 句子长度：{style_config.get('sentence_length', '中等')}
        - 词汇风格：{style_config.get('vocabulary', '现代白话')}
        - 描述密度：{style_config.get('description_density', '适中')}

        【写作要求】
        1. 严格按照场景目的和关键事件写作
        2. 保持{scene_info.get('mood', '平稳')}的情绪氛围
        3. 体现{scene_info.get('pacing', 'medium')}的节奏感
        4. 角色对话要符合其性格特点
        5. 场景描写要生动有画面感
        6. 字数控制在{scene_info.get('target_word_count', 800)}字左右
        7. 与前后场景自然过渡

        【过渡要求】
        - 承接：{scene_info.get('transitions', {}).get('from_previous', '自然承接')}
        - 铺垫：{scene_info.get('transitions', {}).get('to_next', '为下文做准备')}

        请直接开始写作场景内容，不要添加任何解释或说明：
        """

        return prompt

    def _set_cache(self, cache_key: str, data: Any):
        """设置缓存"""
        self._cache[cache_key] = {
            'data': data,
            'timestamp': time.time()
        }



    async def _parse_json_response(self, response_content: str) -> List[Dict[str, Any]]:
        """解析JSON响应"""
        try:
            # 清理响应内容
            cleaned_content = response_content.strip()

            # 尝试找到JSON部分
            if '```json' in cleaned_content:
                json_start = cleaned_content.find('```json') + 7
                json_end = cleaned_content.find('```', json_start)
                cleaned_content = cleaned_content[json_start:json_end].strip()
            elif '[' in cleaned_content and ']' in cleaned_content:
                json_start = cleaned_content.find('[')
                json_end = cleaned_content.rfind(']') + 1
                cleaned_content = cleaned_content[json_start:json_end]

            # 解析JSON
            parsed_data = json.loads(cleaned_content)

            # 确保返回列表
            if isinstance(parsed_data, dict):
                return [parsed_data]
            elif isinstance(parsed_data, list):
                return parsed_data
            else:
                logger.warning(f"意外的JSON数据类型: {type(parsed_data)}")
                return []

        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            logger.error(f"原始内容: {response_content[:500]}...")
            return []
        except Exception as e:
            logger.error(f"响应解析异常: {e}")
            return []

    def _calculate_dialogue_ratio(self, content: str) -> float:
        """计算对话占比"""
        lines = content.split('\n')
        dialogue_lines = 0
        total_lines = len([line for line in lines if line.strip()])

        for line in lines:
            line = line.strip()
            # 简单判断对话（以引号开始或包含引号）
            if line and (line.startswith('"') or line.startswith('"') or
                         line.startswith("'") or '"' in line or '"' in line):
                dialogue_lines += 1

        return dialogue_lines / max(total_lines, 1)

    def _calculate_description_ratio(self, content: str) -> float:
        """计算描述占比"""
        # 简化计算：非对话且包含描述性词汇的内容
        descriptive_keywords = ['看见', '感觉', '显得', '似乎', '仿佛', '宛如', '犹如', '色彩',
                                '光线', '空气']

        lines = content.split('\n')
        description_lines = 0
        total_lines = len([line for line in lines if line.strip()])

        for line in lines:
            line = line.strip()
            if line and not (line.startswith('"') or line.startswith('"') or '"' in line):
                # 不是对话，检查是否包含描述性内容
                if any(keyword in line for keyword in descriptive_keywords):
                    description_lines += 1

        return description_lines / max(total_lines, 1)

    async def _analyze_emotional_arc(self, scenes: List[Scene]) -> str:
        """分析章节情感弧线"""
        if not scenes:
            return "无情感弧线"

        moods = [scene.mood for scene in scenes]

        # 简化的情感弧线分析
        if len(moods) <= 1:
            return moods[0] if moods else "平稳"

        # 检查情感变化模式
        emotional_progression = " → ".join(moods)

        # 分析情感强度变化
        mood_intensity = {
            "平稳": 1, "轻松": 2, "紧张": 4, "激烈": 5,
            "悲伤": 3, "愤怒": 4, "喜悦": 3, "恐惧": 4,
            "平静": 1, "兴奋": 4, "焦虑": 3
        }

        intensities = [mood_intensity.get(mood, 2) for mood in moods]

        if intensities:
            avg_intensity = sum(intensities) / len(intensities)
            max_intensity = max(intensities)
            min_intensity = min(intensities)

            if max_intensity - min_intensity >= 3:
                return f"情感起伏剧烈：{emotional_progression}"
            elif avg_intensity >= 3.5:
                return f"高强度情感：{emotional_progression}"
            else:
                return f"情感渐进发展：{emotional_progression}"

        return emotional_progression

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


class ChapterWriterTool(ContentGeneratorTool):
    """章节写作工具 - 完整实现"""

    def __init__(self):
        super().__init__()
        self.writer = ChapterWriter()  # 使用已有的ChapterWriter实现
        self.llm_service = get_llm_service()
        self.prompt_manager = get_prompt_manager()

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="chapter_writer",
            description="生成完整的章节内容，包括场景规划、内容写作和质量分析",
            category="writing",
            parameters=self.common_parameters + [
                ToolParameter(
                    name="chapter_info",
                    type="object",
                    description="章节信息（章节号、标题、大纲等）",
                    required=True
                ),
                ToolParameter(
                    name="story_context",
                    type="object",
                    description="故事背景上下文（角色、世界观、前情等）",
                    required=False,
                    default={}
                ),
                ToolParameter(
                    name="scene_count",
                    type="integer",
                    description="场景数量（默认3-5个）",
                    required=False,
                    default=4
                ),
                ToolParameter(
                    name="writing_style",
                    type="string",
                    description="写作风格（traditional/modern/poetic/action）",
                    required=False,
                    default="modern",
                    enum=["traditional", "modern", "poetic", "action"]
                )
            ]
        )

    @cached("chapter_writer", expire_seconds=1800)
    async def generate_content(self, content_type: str, context: Dict[str, Any],
                               style: str = "modern", word_count: int = 3000) -> Any:
        """生成章节内容 - 完整实现"""
        try:
            # 从context中提取参数
            chapter_info = context.get("chapter_info", {})
            story_context = context.get("story_context", {})
            scene_count = context.get("scene_count", 4)
            writing_style = context.get("writing_style", style)

            # 验证必需参数
            if not chapter_info:
                return {
                    "success": False,
                    "error": "缺少章节信息参数",
                    "details": "需要提供chapter_info参数"
                }

            # 确保章节信息完整
            chapter_info = self._ensure_complete_chapter_info(chapter_info, word_count)

            logger.info(
                f"开始生成章节：第{chapter_info.get('number', '?')}章 - {chapter_info.get('title', '未命名')}")

            # 调用ChapterWriter进行实际生成
            chapter_content = await self.writer.write_chapter(
                chapter_info=chapter_info,
                story_context=story_context,
                style=writing_style,
                scene_count=scene_count
            )

            # 格式化返回结果
            result = {
                "success": True,
                "chapter_content": asdict(chapter_content),
                "generation_info": {
                    "content_type": content_type,
                    "target_word_count": word_count,
                    "actual_word_count": chapter_content.total_word_count,
                    "scene_count": len(chapter_content.scenes),
                    "writing_style": writing_style,
                    "quality_metrics": {
                        "dialogue_ratio": chapter_content.dialogue_ratio,
                        "description_ratio": chapter_content.description_ratio,
                        "action_ratio": chapter_content.action_ratio
                    }
                },
                "metadata": {
                    "chapter_number": chapter_content.chapter_number,
                    "chapter_title": chapter_content.title,
                    "key_events": chapter_content.key_events,
                    "character_focus": chapter_content.character_focus,
                    "emotional_arc": chapter_content.emotional_arc
                }
            }

            logger.info(
                f"章节生成完成：{chapter_content.total_word_count}字，{len(chapter_content.scenes)}个场景")
            return result

        except Exception as e:
            logger.error(f"章节生成失败: {e}")
            return {
                "success": False,
                "error": f"章节生成失败: {str(e)}",
                "details": {
                    "content_type": content_type,
                    "chapter_info": chapter_info if 'chapter_info' in locals() else "未获取",
                    "word_count": word_count
                }
            }

    async def execute(self, parameters: Dict[str, Any],
                      context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行章节写作任务 - 重写基类方法以支持更多操作"""

        # 检查是否是特殊操作
        action = parameters.get("action")
        if action:
            return await self._handle_special_action(action, parameters, context)

        # 标准内容生成流程
        content_type = parameters.get("content_type", "full_chapter")
        gen_context = parameters.get("context", {})
        style = parameters.get("style", "modern")
        word_count = parameters.get("word_count", 3000)

        # 合并参数到上下文
        gen_context.update({
            "chapter_info": parameters.get("chapter_info", {}),
            "story_context": parameters.get("story_context", {}),
            "scene_count": parameters.get("scene_count", 4),
            "writing_style": parameters.get("writing_style", style)
        })

        # 合并外部上下文
        if context:
            gen_context.update(context)

        return await self.generate_content(content_type, gen_context, style, word_count)

    async def _handle_special_action(self, action: str, parameters: Dict[str, Any],
                                     context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """处理特殊操作"""

        if action == "plan_scenes":
            # 只规划场景，不生成内容
            return await self._plan_scenes_only(parameters, context)

        elif action == "write_single_scene":
            # 只写一个场景
            return await self._write_single_scene(parameters, context)

        elif action == "analyze_chapter":
            # 分析已有章节
            return await self._analyze_existing_chapter(parameters, context)

        elif action == "revise_chapter":
            # 修订章节
            return await self._revise_chapter(parameters, context)

        else:
            return {
                "success": False,
                "error": f"不支持的操作类型: {action}",
                "supported_actions": ["plan_scenes", "write_single_scene", "analyze_chapter",
                                      "revise_chapter"]
            }

    async def _plan_scenes_only(self, parameters: Dict[str, Any],
                                context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """只规划场景结构"""
        try:
            chapter_info = parameters.get("chapter_info", {})
            story_context = parameters.get("story_context", {})
            scene_count = parameters.get("scene_count", 4)

            # 调用ChapterWriter的场景规划方法
            scenes_plan = await self.writer.plan_chapter_scenes(
                chapter_info, story_context, scene_count
            )

            return {
                "success": True,
                "scenes_plan": [asdict(scene) for scene in scenes_plan],
                "scene_count": len(scenes_plan),
                "action": "plan_scenes"
            }

        except Exception as e:
            logger.error(f"场景规划失败: {e}")
            return {
                "success": False,
                "error": f"场景规划失败: {str(e)}",
                "action": "plan_scenes"
            }

    async def _write_single_scene(self, parameters: Dict[str, Any],
                                  context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """写作单个场景"""
        try:
            scene_info = parameters.get("scene_info", {})
            story_context = parameters.get("story_context", {})
            style = parameters.get("writing_style", "modern")

            if not scene_info:
                return {
                    "success": False,
                    "error": "缺少场景信息参数",
                    "action": "write_single_scene"
                }

            # 调用ChapterWriter的场景写作方法
            scene = await self.writer.write_scene(scene_info, story_context, style)

            return {
                "success": True,
                "scene": asdict(scene),
                "word_count": scene.word_count,
                "action": "write_single_scene"
            }

        except Exception as e:
            logger.error(f"场景写作失败: {e}")
            return {
                "success": False,
                "error": f"场景写作失败: {str(e)}",
                "action": "write_single_scene"
            }

    async def _analyze_existing_chapter(self, parameters: Dict[str, Any],
                                        context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """分析已有章节"""
        try:
            chapter_content = parameters.get("chapter_content", "")

            if not chapter_content:
                return {
                    "success": False,
                    "error": "缺少章节内容",
                    "action": "analyze_chapter"
                }

            # 分析章节内容
            analysis = await self._perform_chapter_analysis(chapter_content)

            return {
                "success": True,
                "analysis": analysis,
                "action": "analyze_chapter"
            }

        except Exception as e:
            logger.error(f"章节分析失败: {e}")
            return {
                "success": False,
                "error": f"章节分析失败: {str(e)}",
                "action": "analyze_chapter"
            }

    async def _revise_chapter(self, parameters: Dict[str, Any],
                              context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """修订章节"""
        try:
            original_content = parameters.get("original_content", "")
            revision_notes = parameters.get("revision_notes", [])

            if not original_content:
                return {
                    "success": False,
                    "error": "缺少原始章节内容",
                    "action": "revise_chapter"
                }

            # 执行修订
            revised_content = await self._perform_revision(original_content, revision_notes)

            return {
                "success": True,
                "revised_content": revised_content,
                "revision_notes": revision_notes,
                "action": "revise_chapter"
            }

        except Exception as e:
            logger.error(f"章节修订失败: {e}")
            return {
                "success": False,
                "error": f"章节修订失败: {str(e)}",
                "action": "revise_chapter"
            }

    def _ensure_complete_chapter_info(self, chapter_info: Dict[str, Any],
                                      default_word_count: int) -> Dict[str, Any]:
        """确保章节信息完整"""
        complete_info = {
            "number": chapter_info.get("number", 1),
            "title": chapter_info.get("title", f"第{chapter_info.get('number', 1)}章"),
            "summary": chapter_info.get("summary", ""),
            "detailed_summary": chapter_info.get("detailed_summary", ""),
            "key_events": chapter_info.get("key_events", []),
            "character_focus": chapter_info.get("character_focus", []),
            "plot_advancement": chapter_info.get("plot_advancement", ""),
            "target_word_count": chapter_info.get("target_word_count", default_word_count),
            "mood": chapter_info.get("mood", "平稳"),
            "pacing": chapter_info.get("pacing", "medium"),
            "conflict_level": chapter_info.get("conflict_level", "medium")
        }

        # 如果没有详细大纲，基于简要大纲生成
        if not complete_info["detailed_summary"] and complete_info["summary"]:
            complete_info["detailed_summary"] = complete_info["summary"]

        return complete_info

    async def _perform_chapter_analysis(self, chapter_content: str) -> Dict[str, Any]:
        """执行章节分析"""
        # 基础统计
        word_count = len(chapter_content)
        paragraph_count = len([p for p in chapter_content.split('\n') if p.strip()])

        # 对话分析
        dialogue_ratio = self.writer._calculate_dialogue_ratio(chapter_content)
        description_ratio = self.writer._calculate_description_ratio(chapter_content)
        action_ratio = max(0.0, 1.0 - dialogue_ratio - description_ratio)

        # 情感分析（简化版）
        emotional_keywords = {
            "positive": ["喜悦", "高兴", "激动", "满足", "希望"],
            "negative": ["悲伤", "愤怒", "恐惧", "绝望", "痛苦"],
            "neutral": ["思考", "观察", "行走", "说话", "看见"]
        }

        emotion_scores = {}
        for emotion, keywords in emotional_keywords.items():
            score = sum(chapter_content.count(keyword) for keyword in keywords)
            emotion_scores[emotion] = score

        return {
            "basic_stats": {
                "word_count": word_count,
                "paragraph_count": paragraph_count,
                "estimated_reading_time": f"{word_count // 300}分钟"
            },
            "content_ratios": {
                "dialogue_ratio": round(dialogue_ratio, 2),
                "description_ratio": round(description_ratio, 2),
                "action_ratio": round(action_ratio, 2)
            },
            "emotional_analysis": emotion_scores,
            "suggestions": self._generate_improvement_suggestions(
                dialogue_ratio, description_ratio, action_ratio
            )
        }

    def _generate_improvement_suggestions(self, dialogue_ratio: float,
                                          description_ratio: float,
                                          action_ratio: float) -> List[str]:
        """生成改进建议"""
        suggestions = []

        if dialogue_ratio < 0.2:
            suggestions.append("建议增加对话，提升人物互动感")
        elif dialogue_ratio > 0.6:
            suggestions.append("对话偏多，可以增加一些描述或叙述")

        if description_ratio < 0.3:
            suggestions.append("建议增加环境和人物描述，丰富画面感")
        elif description_ratio > 0.7:
            suggestions.append("描述偏多，可以加快节奏，增加行动")

        if action_ratio < 0.1:
            suggestions.append("建议增加动作场面，提升故事动感")

        if not suggestions:
            suggestions.append("内容比例均衡，写作质量良好")

        return suggestions

    async def _perform_revision(self, original_content: str,
                                revision_notes: List[str]) -> str:
        """执行内容修订"""
        revision_prompt = f"""
        请根据以下修订意见对章节内容进行修改：

        原始内容：
        {original_content[:2000]}...

        修订要求：
        {chr(10).join(f"- {note}" for note in revision_notes)}

        请保持故事的连贯性和风格一致性，返回修订后的完整内容：
        """

        response = await self.llm_service.generate_text(
            revision_prompt,
            temperature=0.7,
            max_tokens=len(original_content) + 500
        )

        return response.content.strip()
