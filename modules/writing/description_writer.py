# modules/writing/description_writer.py
"""
描述写作器
专门处理环境、人物、物品等描述性文本
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from core.base_tools import AsyncTool, ToolDefinition, ToolParameter
from core.llm_client import get_llm_service
from config.settings import get_prompt_manager
from modules.writing import ChapterWriterTool, DialogueWriterTool, SceneGeneratorTool


@dataclass
class Description:
    """描述文本"""
    subject: str  # 描述对象
    content: str  # 描述内容
    word_count: int
    sensory_details: Dict[str, List[str]]  # 感官细节
    mood: str  # 营造的氛围
    perspective: str  # 视角
    literary_devices: List[str]  # 使用的修辞手法


class DescriptionWriter:
    """描述写作器"""

    def __init__(self):
        self.llm_service = get_llm_service()
        self.prompt_manager = get_prompt_manager()

    async def write_character_description(
        self,
        character: str,
        focus_aspects: List[str],
        perspective: str = "third_person",
        mood: str = "neutral",
        word_count: int = 300
    ) -> Description:
        """写作人物描述"""

        prompt = self.prompt_manager.get_prompt(
            "writing",
            "character_description",
            character=character,
            aspects=focus_aspects,
            perspective=perspective,
            mood=mood,
            word_count=word_count
        )

        response = await self.llm_service.generate_text(
            prompt,
            temperature=0.6,
            max_tokens=int(word_count * 1.5)
        )

        return Description(
            subject=character,
            content=response.content,
            word_count=len(response.content),
            sensory_details=self._extract_sensory_details(response.content),
            mood=mood,
            perspective=perspective,
            literary_devices=self._identify_literary_devices(response.content)
        )

    async def write_environment_description(
        self,
        location: str,
        time_of_day: str,
        weather: str,
        atmosphere: str,
        sensory_focus: str = "visual",
        word_count: int = 400
    ) -> Description:
        """写作环境描述"""

        prompt = self.prompt_manager.get_prompt(
            "writing",
            "environment_description",
            location=location,
            time=time_of_day,
            weather=weather,
            atmosphere=atmosphere,
            sensory=sensory_focus,
            word_count=word_count
        )

        response = await self.llm_service.generate_text(
            prompt,
            temperature=0.7,
            max_tokens=int(word_count * 1.5)
        )

        return Description(
            subject=location,
            content=response.content,
            word_count=len(response.content),
            sensory_details=self._extract_sensory_details(response.content),
            mood=atmosphere,
            perspective="third_person",
            literary_devices=self._identify_literary_devices(response.content)
        )

    async def write_action_description(
        self,
        action: str,
        actor: str,
        setting: str,
        intensity: str = "medium",
        focus: str = "visual",
        word_count: int = 250
    ) -> Description:
        """写作动作描述"""

        prompt = self.prompt_manager.get_prompt(
            "writing",
            "action_description",
            action=action,
            actor=actor,
            setting=setting,
            intensity=intensity,
            focus=focus,
            word_count=word_count
        )

        response = await self.llm_service.generate_text(
            prompt,
            temperature=0.8,
            max_tokens=int(word_count * 1.5)
        )

        return Description(
            subject=f"{actor}的{action}",
            content=response.content,
            word_count=len(response.content),
            sensory_details=self._extract_sensory_details(response.content),
            mood=intensity,
            perspective="third_person",
            literary_devices=self._identify_literary_devices(response.content)
        )

    async def write_object_description(
        self,
        object_name: str,
        significance: str,
        physical_details: List[str],
        symbolic_meaning: str = None,
        word_count: int = 200
    ) -> Description:
        """写作物品描述"""

        prompt = self.prompt_manager.get_prompt(
            "writing",
            "object_description",
            object=object_name,
            significance=significance,
            details=physical_details,
            symbolism=symbolic_meaning,
            word_count=word_count
        )

        response = await self.llm_service.generate_text(
            prompt,
            temperature=0.6,
            max_tokens=int(word_count * 1.5)
        )

        return Description(
            subject=object_name,
            content=response.content,
            word_count=len(response.content),
            sensory_details=self._extract_sensory_details(response.content),
            mood="neutral",
            perspective="third_person",
            literary_devices=self._identify_literary_devices(response.content)
        )

    def _extract_sensory_details(self, content: str) -> Dict[str, List[str]]:
        """提取感官细节"""

        sensory_keywords = {
            "visual": ["看到", "色彩", "光", "影", "形状", "美丽", "明亮", "黑暗"],
            "auditory": ["听到", "声音", "响", "静", "音", "嗡嗡", "叮当"],
            "tactile": ["触", "摸", "软", "硬", "冷", "热", "粗糙", "光滑"],
            "olfactory": ["闻", "香", "臭", "味道", "芳香", "刺鼻"],
            "gustatory": ["尝", "甜", "苦", "酸", "辣", "咸"]
        }

        detected_details = {}

        for sense, keywords in sensory_keywords.items():
            details = []
            for keyword in keywords:
                if keyword in content:
                    # 找到包含关键词的句子
                    sentences = content.split("。")
                    for sentence in sentences:
                        if keyword in sentence:
                            details.append(sentence.strip())
                            break

            if details:
                detected_details[sense] = details[:3]  # 最多保留3个

        return detected_details

    def _identify_literary_devices(self, content: str) -> List[str]:
        """识别修辞手法"""

        devices = []

        # 简单检测一些修辞手法
        if "如" in content or "像" in content or "似" in content:
            devices.append("比喻")

        if "的" in content and content.count("的") > len(content) // 20:
            devices.append("排比")

        if any(char in content for char in "，、；"):
            devices.append("并列")

        return devices


class DescriptionWriterTool(AsyncTool):
    """描述写作工具"""

    def __init__(self):
        super().__init__()
        self.writer = DescriptionWriter()

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="description_writer",
            description="专业的描述写作工具，生成生动的人物、环境、动作、物品描述",
            category="writing",
            parameters=[
                ToolParameter(
                    name="description_type",
                    type="string",
                    description="描述类型：character/environment/action/object",
                    required=True
                ),
                ToolParameter(
                    name="subject",
                    type="string",
                    description="描述对象",
                    required=True
                ),
                ToolParameter(
                    name="word_count",
                    type="integer",
                    description="目标字数",
                    required=False,
                    default=300
                ),
                # 人物描述参数
                ToolParameter(
                    name="focus_aspects",
                    type="array",
                    description="关注方面（人物描述用）",
                    required=False
                ),
                # 环境描述参数
                ToolParameter(
                    name="time_of_day",
                    type="string",
                    description="时间（环境描述用）",
                    required=False,
                    default="白天"
                ),
                ToolParameter(
                    name="weather",
                    type="string",
                    description="天气（环境描述用）",
                    required=False,
                    default="晴朗"
                ),
                ToolParameter(
                    name="atmosphere",
                    type="string",
                    description="氛围",
                    required=False,
                    default="平静"
                ),
                # 动作描述参数
                ToolParameter(
                    name="action",
                    type="string",
                    description="动作内容（动作描述用）",
                    required=False
                ),
                ToolParameter(
                    name="actor",
                    type="string",
                    description="执行者（动作描述用）",
                    required=False
                ),
                ToolParameter(
                    name="intensity",
                    type="string",
                    description="强度（动作描述用）",
                    required=False,
                    default="medium"
                ),
                # 物品描述参数
                ToolParameter(
                    name="significance",
                    type="string",
                    description="重要性（物品描述用）",
                    required=False
                ),
                ToolParameter(
                    name="physical_details",
                    type="array",
                    description="物理细节（物品描述用）",
                    required=False
                ),
                # 通用参数
                ToolParameter(
                    name="sensory_focus",
                    type="string",
                    description="感官重点：visual/auditory/tactile/olfactory/gustatory",
                    required=False,
                    default="visual"
                ),
                ToolParameter(
                    name="perspective",
                    type="string",
                    description="视角：first_person/third_person",
                    required=False,
                    default="third_person"
                )
            ]
        )

    async def execute(self, parameters: Dict[str, Any],
                      context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行描述写作"""

        description_type = parameters.get("description_type")
        subject = parameters.get("subject", "")
        word_count = parameters.get("word_count", 300)

        if description_type == "character":
            description = await self.writer.write_character_description(
                subject,
                parameters.get("focus_aspects", ["外貌", "气质"]),
                parameters.get("perspective", "third_person"),
                parameters.get("atmosphere", "neutral"),
                word_count
            )

        elif description_type == "environment":
            description = await self.writer.write_environment_description(
                subject,
                parameters.get("time_of_day", "白天"),
                parameters.get("weather", "晴朗"),
                parameters.get("atmosphere", "平静"),
                parameters.get("sensory_focus", "visual"),
                word_count
            )

        elif description_type == "action":
            description = await self.writer.write_action_description(
                parameters.get("action", "行动"),
                parameters.get("actor", subject),
                parameters.get("setting", "场景"),
                parameters.get("intensity", "medium"),
                parameters.get("sensory_focus", "visual"),
                word_count
            )

        elif description_type == "object":
            description = await self.writer.write_object_description(
                subject,
                parameters.get("significance", "重要物品"),
                parameters.get("physical_details", ["外观特征"]),
                parameters.get("symbolic_meaning"),
                word_count
            )

        else:
            return {"error": "不支持的描述类型"}

        return {
            "description": asdict(description),
            "generation_info": {
                "description_type": description_type,
                "target_word_count": word_count,
                "actual_word_count": description.word_count
            }
        }


# 注册所有写作工具
def register_writing_tools():
    """注册写作工具"""
    from core.base_tools import get_tool_registry

    registry = get_tool_registry()

    registry.register(ChapterWriterTool())
    registry.register(SceneGeneratorTool())
    registry.register(DialogueWriterTool())
    registry.register(DescriptionWriterTool())


if __name__ == "__main__":
    register_writing_tools()
    print("写作工具已注册")
