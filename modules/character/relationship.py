# modules/character/relationship.py
"""
角色关系管理器
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from core.base_tools import AsyncTool, ToolDefinition, ToolParameter
from core.llm_client import get_llm_service


class RelationshipType(Enum):
    """关系类型"""
    FAMILY = "家庭关系"
    ROMANTIC = "爱情关系"
    FRIENDSHIP = "友谊关系"
    MENTORSHIP = "师徒关系"
    RIVALRY = "敌对关系"
    ALLIANCE = "盟友关系"
    BUSINESS = "商业关系"
    POLITICAL = "政治关系"


@dataclass
class Relationship:
    """角色关系"""
    id: str
    character1_id: str
    character2_id: str
    relationship_type: str
    intensity: int  # 关系强度 1-10
    status: str  # 当前状态：良好/紧张/恶化/发展中
    history: List[Dict[str, str]]  # 关系历史
    current_dynamic: str  # 当前动态
    future_potential: str  # 未来可能性
    conflict_sources: List[str]  # 冲突来源
    bonding_factors: List[str]  # 联结因素


class RelationshipManager:
    """关系管理器"""

    def __init__(self):
        self.llm_service = get_llm_service()
        self.relationships: Dict[str, Relationship] = {}

    async def create_relationship(
        self,
        char1: Dict[str, Any],
        char2: Dict[str, Any],
        relationship_type: str = None
    ) -> Relationship:
        """创建角色关系"""

        if not relationship_type:
            relationship_type = await self._determine_relationship_type(char1, char2)

        relationship_data = await self._generate_relationship_details(
            char1, char2, relationship_type
        )

        relationship = Relationship(
            id=f"rel_{char1['id']}_{char2['id']}",
            character1_id=char1['id'],
            character2_id=char2['id'],
            **relationship_data
        )

        self.relationships[relationship.id] = relationship
        return relationship

    async def _determine_relationship_type(self, char1: Dict, char2: Dict) -> str:
        """确定关系类型"""
        # 基于角色特征自动确定关系类型
        prompt = f"""
        基于以下两个角色的信息，判断他们最可能的关系类型：

        角色1: {char1.get('name', '')} - {char1.get('character_type', '')}
        角色2: {char2.get('name', '')} - {char2.get('character_type', '')}

        可选关系类型: 家庭关系、爱情关系、友谊关系、师徒关系、敌对关系、盟友关系

        请直接返回最合适的关系类型：
        """

        response = await self.llm_service.generate_text(prompt)
        return response.content.strip()

    async def _generate_relationship_details(
        self,
        char1: Dict,
        char2: Dict,
        relationship_type: str
    ) -> Dict[str, Any]:
        """生成关系详情"""

        return {
            "relationship_type": relationship_type,
            "intensity": 7,
            "status": "发展中",
            "history": [
                {"事件": "初次相遇", "描述": "在某个重要场合相遇"}
            ],
            "current_dynamic": "相互了解阶段",
            "future_potential": "关系可能进一步发展",
            "conflict_sources": ["价值观不同", "利益冲突"],
            "bonding_factors": ["共同目标", "相互欣赏"]
        }


class RelationshipTool(AsyncTool):
    """关系管理工具"""

    def __init__(self):
        super().__init__()
        self.manager = RelationshipManager()

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="relationship_manager",
            description="管理角色之间的关系，创建和维护角色关系网络",
            category="character",
            parameters=[
                ToolParameter(
                    name="action",
                    type="string",
                    description="操作类型：create/update/analyze",
                    required=True
                ),
                ToolParameter(
                    name="character1",
                    type="object",
                    description="第一个角色信息",
                    required=False
                ),
                ToolParameter(
                    name="character2",
                    type="object",
                    description="第二个角色信息",
                    required=False
                ),
                ToolParameter(
                    name="relationship_type",
                    type="string",
                    description="关系类型",
                    required=False
                )
            ]
        )

    async def execute(self, parameters: Dict[str, Any],
                      context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行关系管理操作"""

        action = parameters.get("action")

        if action == "create":
            char1 = parameters.get("character1", {})
            char2 = parameters.get("character2", {})
            rel_type = parameters.get("relationship_type")

            relationship = await self.manager.create_relationship(char1, char2, rel_type)

            return {
                "relationship": asdict(relationship),
                "action": "create"
            }

        return {"error": "不支持的操作类型"}

