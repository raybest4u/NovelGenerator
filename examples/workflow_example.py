
# examples/workflow_example.py
"""
工作流示例
展示完整的小说创作工作流程
"""

import asyncio
from typing import Dict, Any, List
from core.base_tools import ToolCall, get_tool_registry


class NovelWorkflow:
    """小说创作工作流"""

    def __init__(self):
        self.registry = get_tool_registry()
        self.context = {}

    async def run_workflow(self, title: str, genre: str = "玄幻",
                           chapter_count: int = 5) -> Dict[str, Any]:
        """运行完整工作流"""

        print(f"开始创作小说《{title}》...")
        print(f"类型: {genre}, 章节数: {chapter_count}")

        # 第1步：世界观构建
        print("\n📍 第1步：构建世界观")
        world_setting = await self._build_world(genre)
        self.context["world_setting"] = world_setting

        # 第2步：角色创建
        print("\n📍 第2步：创建角色")
        characters = await self._create_characters(genre, world_setting)
        self.context["characters"] = characters

        # 第3步：故事规划
        print("\n📍 第3步：规划故事")
        story_outline = await self._plan_story(title, genre, chapter_count, characters)
        self.context["story_outline"] = story_outline

        # 第4步：角色关系
        print("\n📍 第4步：建立角色关系")
        relationships = await self._build_relationships(characters)
        self.context["relationships"] = relationships

        # 第5步：生成章节
        print("\n📍 第5步：生成章节内容")
        chapters = await self._generate_chapters(story_outline, chapter_count)
        self.context["chapters"] = chapters

        # 第6步：一致性检查
        print("\n📍 第6步：一致性检查")
        consistency_report = await self._check_consistency()
        self.context["consistency_report"] = consistency_report

        # 组装最终结果
        novel_data = {
            "title": title,
            "genre": genre,
            "world_setting": world_setting,
            "characters": characters,
            "story_outline": story_outline,
            "relationships": relationships,
            "chapters": chapters,
            "consistency_report": consistency_report,
            "metadata": {
                "total_word_count": sum(ch.get("total_word_count", 0) for ch in chapters),
                "character_count": len(characters),
                "chapter_count": len(chapters)
            }
        }

        print(f"\n🎉 小说《{title}》创作完成！")
        return novel_data

    async def _build_world(self, genre: str) -> Dict[str, Any]:
        """构建世界观"""
        call = ToolCall(
            id="world_build",
            name="world_builder",
            parameters={
                "genre": genre,
                "theme": "修仙" if genre == "玄幻" else "冒险",
                "detail_level": "detailed"
            }
        )

        response = await self.registry.execute_tool(call)
        if response.success:
            world = response.result["world_setting"]
            print(f"✅ 创建世界: {world['name']}")
            return world
        else:
            print(f"❌ 世界观创建失败: {response.error}")
            return {}

    async def _create_characters(self, genre: str, world_setting: Dict) -> List[Dict[str, Any]]:
        """创建角色"""
        characters = []
        character_types = ["主角", "重要配角", "反派", "导师"]

        for char_type in character_types:
            call = ToolCall(
                id=f"char_{char_type}",
                name="character_creator",
                parameters={
                    "character_type": char_type,
                    "genre": genre,
                    "world_setting": world_setting
                }
            )

            response = await self.registry.execute_tool(call)
            if response.success:
                character = response.result["character"]
                characters.append(character)
                print(f"✅ 创建角色: {character['name']} ({char_type})")
            else:
                print(f"❌ {char_type}创建失败: {response.error}")

        return characters

    async def _plan_story(self, title: str, genre: str, chapter_count: int,
                          characters: List[Dict]) -> Dict[str, Any]:
        """规划故事"""
        call = ToolCall(
            id="story_plan",
            name="story_planner",
            parameters={
                "title": title,
                "genre": genre,
                "chapter_count": chapter_count,
                "characters": characters,
                "world_setting": self.context.get("world_setting", {})
            }
        )

        response = await self.registry.execute_tool(call)
        if response.success:
            outline = response.result["story_outline"]
            print(f"✅ 故事规划完成: {len(outline['plot_points'])}个情节点")
            return outline
        else:
            print(f"❌ 故事规划失败: {response.error}")
            return {}

    async def _build_relationships(self, characters: List[Dict]) -> List[Dict[str, Any]]:
        """建立角色关系"""
        relationships = []

        # 为前几个主要角色建立关系
        for i in range(min(3, len(characters))):
            for j in range(i + 1, min(3, len(characters))):
                char1 = characters[i]
                char2 = characters[j]

                call = ToolCall(
                    id=f"rel_{i}_{j}",
                    name="relationship_manager",
                    parameters={
                        "action": "create",
                        "character1": char1,
                        "character2": char2
                    }
                )

                response = await self.registry.execute_tool(call)
                if response.success:
                    relationship = response.result["relationship"]
                    relationships.append(relationship)
                    print(f"✅ 建立关系: {char1['name']} - {char2['name']}")

        return relationships

    async def _generate_chapters(self, story_outline: Dict, chapter_count: int) -> List[
        Dict[str, Any]]:
        """生成章节"""
        chapters = []

        for i in range(min(chapter_count, 3)):  # 为演示限制章节数
            chapter_info = {
                "number": i + 1,
                "title": f"第{i + 1}章",
                "summary": f"第{i + 1}章的内容",
                "key_events": [f"第{i + 1}章事件"]
            }

            call = ToolCall(
                id=f"chapter_{i + 1}",
                name="chapter_writer",
                parameters={
                    "chapter_info": chapter_info,
                    "story_context": self.context,
                    "target_word_count": 1500  # 为演示减少字数
                }
            )

            response = await self.registry.execute_tool(call)
            if response.success:
                chapter = response.result["chapter"]
                chapters.append(chapter)
                print(f"✅ 生成章节: {chapter['title']} ({chapter['total_word_count']}字)")
            else:
                print(f"❌ 第{i + 1}章生成失败: {response.error}")

        return chapters

    async def _check_consistency(self) -> Dict[str, Any]:
        """检查一致性"""
        call = ToolCall(
            id="consistency_check",
            name="consistency_checker",
            parameters={
                "check_type": "full",
                "story_data": self.context
            }
        )

        response = await self.registry.execute_tool(call)
        if response.success:
            report = response.result["consistency_report"]
            print(f"✅ 一致性检查完成: 评分 {report['overall_score']:.1f}/100")
            return report
        else:
            print(f"❌ 一致性检查失败: {response.error}")
            return {}


async def example_workflow():
    """工作流示例"""
    print("Fantasy Novel MCP 工作流示例")
    print("=" * 50)

    workflow = NovelWorkflow()

    try:
        # 运行完整工作流
        novel = await workflow.run_workflow(
            title="工作流测试小说",
            genre="玄幻",
            chapter_count=3
        )

        # 输出结果摘要
        print("\n" + "=" * 50)
        print("创作结果摘要:")
        print("=" * 50)

        metadata = novel["metadata"]
        print(f"📖 小说标题: {novel['title']}")
        print(f"🌍 世界名称: {novel['world_setting'].get('name', '未知')}")
        print(f"👥 角色数量: {metadata['character_count']}")
        print(f"📄 章节数量: {metadata['chapter_count']}")
        print(f"📝 总字数: {metadata['total_word_count']}")

        if novel["consistency_report"]:
            score = novel["consistency_report"]["overall_score"]
            print(f"✅ 一致性评分: {score:.1f}/100")

        print("\n角色列表:")
        for char in novel["characters"]:
            print(f"  - {char['name']} ({char['character_type']})")

        print("\n章节列表:")
        for chapter in novel["chapters"]:
            print(f"  - {chapter['title']} ({chapter['total_word_count']}字)")

        # 保存结果
        import json
        with open("workflow_result.json", "w", encoding="utf-8") as f:
            json.dump(novel, f, ensure_ascii=False, indent=2)

        print("\n💾 完整结果已保存到 workflow_result.json")

    except Exception as e:
        print(f"❌ 工作流执行失败: {e}")


if __name__ == "__main__":
    asyncio.run(example_workflow())
