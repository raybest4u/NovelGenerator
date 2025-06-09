# modules/writing/scene_generator.py
"""
场景生成器
负责生成具体的场景内容
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from core.base_tools import AsyncTool, ToolDefinition, ToolParameter
from core.llm_client import get_llm_service
from config.settings import get_prompt_manager


@dataclass
class SceneElement:
    """场景元素"""
    type: str  # environment/character/object/atmosphere
    name: str
    description: str
    importance: int  # 1-10
    sensory_details: Dict[str, str]  # 感官细节


@dataclass
class SceneStructure:
    """场景结构"""
    opening: str  # 开场
    development: str  # 发展
    climax: str  # 高潮
    transition: str  # 过渡


class SceneGenerator:
    """场景生成器"""

    def __init__(self):
        self.llm_service = get_llm_service()
        self.prompt_manager = get_prompt_manager()

    async def generate_scene(
        self,
        scene_type: str,
        location: str,
        characters: List[str],
        purpose: str,
        mood: str = "neutral",
        word_count: int = 800
    ) -> str:
        """生成场景内容"""

        # 生成场景元素
        elements = await self._generate_scene_elements(
            location, characters, mood
        )

        # 规划场景结构
        structure = await self._plan_scene_structure(
            scene_type, purpose, characters
        )

        # 写作场景内容
        scene_content = await self._write_scene_content(
            elements, structure, scene_type, word_count
        )

        return scene_content

    async def generate_action_scene(
        self,
        conflict_type: str,
        participants: List[str],
        location: str,
        stakes: str,
        word_count: int = 1000
    ) -> str:
        """生成动作场景"""

        prompt = self.prompt_manager.get_prompt(
            "writing",
            "action_scene",
            conflict_type=conflict_type,
            participants=participants,
            location=location,
            stakes=stakes,
            word_count=word_count
        )

        response = await self.llm_service.generate_text(
            prompt,
            temperature=0.7,
            max_tokens=int(word_count * 1.5)
        )

        return response.content

    async def generate_dialogue_scene(
        self,
        characters: List[str],
        topic: str,
        relationship_dynamics: Dict[str, str],
        emotional_undertone: str,
        word_count: int = 600
    ) -> str:
        """生成对话场景"""

        prompt = self.prompt_manager.get_prompt(
            "writing",
            "dialogue_scene",
            characters=characters,
            topic=topic,
            relationships=relationship_dynamics,
            emotion=emotional_undertone,
            word_count=word_count
        )

        response = await self.llm_service.generate_text(
            prompt,
            temperature=0.8,
            max_tokens=int(word_count * 1.5)
        )

        return response.content

    async def generate_description_scene(
        self,
        subject: str,
        descriptive_focus: List[str],
        sensory_emphasis: str,
        mood: str,
        word_count: int = 500
    ) -> str:
        """生成描述场景"""

        prompt = self.prompt_manager.get_prompt(
            "writing",
            "description_scene",
            subject=subject,
            focus_areas=descriptive_focus,
            sensory_type=sensory_emphasis,
            mood=mood,
            word_count=word_count
        )

        response = await self.llm_service.generate_text(
            prompt,
            temperature=0.6,
            max_tokens=int(word_count * 1.5)
        )

        return response.content

    async def _generate_scene_elements(
        self,
        location: str,
        characters: List[str],
        mood: str
    ) -> List[SceneElement]:
        """生成场景元素"""

        elements = []

        # 环境元素
        elements.append(SceneElement(
            type="environment",
            name=location,
            description=f"{location}的环境描述",
            importance=8,
            sensory_details={
                "visual": "视觉细节",
                "auditory": "听觉细节",
                "tactile": "触觉细节"
            }
        ))

        # 角色元素
        for char in characters:
            elements.append(SceneElement(
                type="character",
                name=char,
                description=f"{char}在此场景中的表现",
                importance=9,
                sensory_details={
                    "visual": "外观描述",
                    "behavioral": "行为特征"
                }
            ))

        return elements

    async def _plan_scene_structure(
        self,
        scene_type: str,
        purpose: str,
        characters: List[str]
    ) -> SceneStructure:
        """规划场景结构"""

        return SceneStructure(
            opening=f"场景开始，引入{scene_type}",
            development=f"发展{purpose}相关的情节",
            climax=f"达到{purpose}的关键点",
            transition="为下个场景做铺垫"
        )

    async def _write_scene_content(
        self,
        elements: List[SceneElement],
        structure: SceneStructure,
        scene_type: str,
        word_count: int
    ) -> str:
        """写作场景内容"""

        prompt = f"""
        请基于以下信息写作一个{scene_type}场景：

        场景元素：
        {[element.name for element in elements]}

        场景结构：
        - 开场：{structure.opening}
        - 发展：{structure.development}
        - 高潮：{structure.climax}
        - 过渡：{structure.transition}

        目标字数：{word_count}字

        请写作生动、有画面感的场景内容：
        """

        response = await self.llm_service.generate_text(
            prompt,
            temperature=0.7,
            max_tokens=int(word_count * 1.5)
        )

        return response.content


class SceneGeneratorTool(AsyncTool):
    """场景生成工具"""

    def __init__(self):
        super().__init__()
        self.generator = SceneGenerator()

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="scene_generator",
            description="生成具体的场景内容，支持动作、对话、描述等不同类型场景",
            category="writing",
            parameters=[
                ToolParameter(
                    name="scene_type",
                    type="string",
                    description="场景类型：action/dialogue/description/general",
                    required=True
                ),
                ToolParameter(
                    name="location",
                    type="string",
                    description="场景地点",
                    required=False,
                    default="未指定"
                ),
                ToolParameter(
                    name="characters",
                    type="array",
                    description="参与角色",
                    required=False
                ),
                ToolParameter(
                    name="purpose",
                    type="string",
                    description="场景目的",
                    required=False,
                    default="推进情节"
                ),
                ToolParameter(
                    name="mood",
                    type="string",
                    description="场景氛围",
                    required=False,
                    default="neutral"
                ),
                ToolParameter(
                    name="word_count",
                    type="integer",
                    description="目标字数",
                    required=False,
                    default=800
                ),
                # 动作场景专用参数
                ToolParameter(
                    name="conflict_type",
                    type="string",
                    description="冲突类型（动作场景用）",
                    required=False
                ),
                ToolParameter(
                    name="stakes",
                    type="string",
                    description="赌注（动作场景用）",
                    required=False
                ),
                # 对话场景专用参数
                ToolParameter(
                    name="topic",
                    type="string",
                    description="对话主题（对话场景用）",
                    required=False
                ),
                ToolParameter(
                    name="relationship_dynamics",
                    type="object",
                    description="角色关系动态（对话场景用）",
                    required=False
                ),
                # 描述场景专用参数
                ToolParameter(
                    name="subject",
                    type="string",
                    description="描述对象（描述场景用）",
                    required=False
                ),
                ToolParameter(
                    name="descriptive_focus",
                    type="array",
                    description="描述重点（描述场景用）",
                    required=False
                )
            ]
        )

    async def execute(self, parameters: Dict[str, Any],
                      context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行场景生成"""

        scene_type = parameters.get("scene_type", "general")

        if scene_type == "action":
            content = await self.generator.generate_action_scene(
                parameters.get("conflict_type", "武力冲突"),
                parameters.get("characters", ["主角"]),
                parameters.get("location", "未指定"),
                parameters.get("stakes", "重要事物"),
                parameters.get("word_count", 1000)
            )

        elif scene_type == "dialogue":
            content = await self.generator.generate_dialogue_scene(
                parameters.get("characters", ["主角", "配角"]),
                parameters.get("topic", "重要话题"),
                parameters.get("relationship_dynamics", {}),
                parameters.get("mood", "neutral"),
                parameters.get("word_count", 600)
            )

        elif scene_type == "description":
            content = await self.generator.generate_description_scene(
                parameters.get("subject", "场景"),
                parameters.get("descriptive_focus", ["环境", "氛围"]),
                "visual",
                parameters.get("mood", "neutral"),
                parameters.get("word_count", 500)
            )

        else:  # general
            content = await self.generator.generate_scene(
                scene_type,
                parameters.get("location", "未指定"),
                parameters.get("characters", ["主角"]),
                parameters.get("purpose", "推进情节"),
                parameters.get("mood", "neutral"),
                parameters.get("word_count", 800)
            )

        return {
            "scene_content": content,
            "generation_info": {
                "scene_type": scene_type,
                "word_count": len(content),
                "target_word_count": parameters.get("word_count", 800)
            }
        }

