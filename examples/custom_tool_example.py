
# examples/custom_tool_example.py
"""
自定义工具示例
展示如何创建和注册自定义工具
"""

import asyncio
from typing import Dict, Any, Optional
from core.base_tools import AsyncTool, ToolDefinition, ToolParameter, get_tool_registry


class PoemGeneratorTool(AsyncTool):
    """诗词生成工具示例"""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="poem_generator",
            description="生成符合主题的古典诗词",
            category="creative",
            parameters=[
                ToolParameter(
                    name="theme",
                    type="string",
                    description="诗词主题",
                    required=True
                ),
                ToolParameter(
                    name="style",
                    type="string",
                    description="诗词风格：五言绝句/七言律诗/词牌",
                    required=False,
                    default="七言律诗"
                ),
                ToolParameter(
                    name="mood",
                    type="string",
                    description="情感基调",
                    required=False,
                    default="豪迈"
                )
            ],
            examples=[
                {
                    "parameters": {
                        "theme": "剑侠",
                        "style": "七言律诗",
                        "mood": "豪迈"
                    },
                    "result": "一首关于剑侠的七言律诗"
                }
            ],
            tags=["poetry", "creative", "classical"]
        )

    async def execute(self, parameters: Dict[str, Any],
                      context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行诗词生成"""

        theme = parameters.get("theme", "山水")
        style = parameters.get("style", "七言律诗")
        mood = parameters.get("mood", "豪迈")

        # 这里可以调用LLM生成诗词
        # 为演示简化，返回模板诗词

        poem_templates = {
            "剑侠": {
                "七言律诗": {
                    "豪迈": """
                    十年磨剑霜雪寒，一朝出鞘天地宽。
                    仗剑天涯除恶霸，快意恩仇在江湖。
                    """
                }
            }
        }

        poem = poem_templates.get(theme, {}).get(style, {}).get(mood, "")
        if not poem:
            poem = f"关于{theme}的{style}（{mood}风格）"

        return {
            "poem": poem.strip(),
            "theme": theme,
            "style": style,
            "mood": mood,
            "analysis": f"这是一首以{theme}为主题的{style}，体现了{mood}的情感基调"
        }


class BookmarkTool(AsyncTool):
    """书签管理工具示例"""

    def __init__(self):
        super().__init__()
        self.bookmarks = []  # 简单的内存存储

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="bookmark_manager",
            description="管理小说创作过程中的书签和标记",
            category="utility",
            parameters=[
                ToolParameter(
                    name="action",
                    type="string",
                    description="操作类型：add/list/remove/search",
                    required=True
                ),
                ToolParameter(
                    name="title",
                    type="string",
                    description="书签标题",
                    required=False
                ),
                ToolParameter(
                    name="content",
                    type="string",
                    description="书签内容",
                    required=False
                ),
                ToolParameter(
                    name="tags",
                    type="array",
                    description="标签列表",
                    required=False
                ),
                ToolParameter(
                    name="query",
                    type="string",
                    description="搜索关键词",
                    required=False
                )
            ]
        )

    async def execute(self, parameters: Dict[str, Any],
                      context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行书签管理操作"""

        action = parameters.get("action")

        if action == "add":
            bookmark = {
                "id": len(self.bookmarks) + 1,
                "title": parameters.get("title", "未命名书签"),
                "content": parameters.get("content", ""),
                "tags": parameters.get("tags", []),
                "created_at": "2024-01-01"  # 简化时间
            }
            self.bookmarks.append(bookmark)
            return {"message": "书签已添加", "bookmark": bookmark}

        elif action == "list":
            return {"bookmarks": self.bookmarks, "count": len(self.bookmarks)}

        elif action == "search":
            query = parameters.get("query", "").lower()
            results = [
                bm for bm in self.bookmarks
                if query in bm["title"].lower() or query in bm["content"].lower()
            ]
            return {"results": results, "count": len(results)}

        elif action == "remove":
            title = parameters.get("title", "")
            removed = [bm for bm in self.bookmarks if bm["title"] == title]
            self.bookmarks = [bm for bm in self.bookmarks if bm["title"] != title]
            return {"message": f"已删除 {len(removed)} 个书签"}

        else:
            return {"error": "不支持的操作类型"}


async def example_custom_tools():
    """自定义工具使用示例"""
    print("自定义工具示例")
    print("=" * 50)

    # 获取工具注册表
    registry = get_tool_registry()

    # 注册自定义工具
    print("1. 注册自定义工具...")
    registry.register(PoemGeneratorTool())
    registry.register(BookmarkTool())

    print("✅ 自定义工具注册完成")

    # 测试诗词生成工具
    print("\n2. 测试诗词生成工具...")
    from core.base_tools import ToolCall

    poem_call = ToolCall(
        id="poem_test",
        name="poem_generator",
        parameters={
            "theme": "剑侠",
            "style": "七言律诗",
            "mood": "豪迈"
        }
    )

    poem_response = await registry.execute_tool(poem_call)
    if poem_response.success:
        result = poem_response.result
        print(f"主题: {result['theme']}")
        print(f"风格: {result['style']}")
        print(f"诗词:\n{result['poem']}")
        print(f"分析: {result['analysis']}")

    # 测试书签管理工具
    print("\n3. 测试书签管理工具...")

    # 添加书签
    add_call = ToolCall(
        id="bookmark_add",
        name="bookmark_manager",
        parameters={
            "action": "add",
            "title": "角色设定灵感",
            "content": "主角可以是一个失忆的剑仙",
            "tags": ["角色", "设定", "剑仙"]
        }
    )

    add_response = await registry.execute_tool(add_call)
    if add_response.success:
        print(f"添加书签: {add_response.result['message']}")

    # 列出书签
    list_call = ToolCall(
        id="bookmark_list",
        name="bookmark_manager",
        parameters={"action": "list"}
    )

    list_response = await registry.execute_tool(list_call)
    if list_response.success:
        bookmarks = list_response.result['bookmarks']
        print(f"当前书签数量: {len(bookmarks)}")
        for bm in bookmarks:
            print(f"  - {bm['title']}: {bm['content']}")

    # 搜索书签
    search_call = ToolCall(
        id="bookmark_search",
        name="bookmark_manager",
        parameters={
            "action": "search",
            "query": "剑仙"
        }
    )

    search_response = await registry.execute_tool(search_call)
    if search_response.success:
        results = search_response.result['results']
        print(f"搜索'剑仙'找到 {len(results)} 个结果")

    print("\n✅ 自定义工具测试完成")


if __name__ == "__main__":
    asyncio.run(example_custom_tools())
