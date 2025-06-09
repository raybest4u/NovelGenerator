
# examples/api_client_example.py
"""
API客户端使用示例
展示如何通过HTTP API调用系统功能
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any


class FantasyNovelAPIClient:
    """Fantasy Novel MCP API客户端"""

    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.session_id = "example_session"

    async def chat(self, message: str, use_tools: bool = True) -> Dict[str, Any]:
        """聊天接口"""
        async with aiohttp.ClientSession() as session:
            data = {
                "message": message,
                "session_id": self.session_id,
                "use_tools": use_tools
            }

            async with session.post(f"{self.base_url}/chat", json=data) as resp:
                return await resp.json()

    async def generate_novel(self, title: str, genre: str = "玄幻",
                             chapter_count: int = 5) -> Dict[str, Any]:
        """生成小说"""
        async with aiohttp.ClientSession() as session:
            data = {
                "title": title,
                "genre": genre,
                "chapter_count": chapter_count,
                "auto_generate": True
            }

            async with session.post(f"{self.base_url}/novel/generate", json=data) as resp:
                return await resp.json()

    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """调用工具"""
        async with aiohttp.ClientSession() as session:
            data = {
                "tool_name": tool_name,
                "parameters": parameters
            }

            async with session.post(f"{self.base_url}/tools/call", json=data) as resp:
                return await resp.json()

    async def get_novel_status(self, novel_id: str) -> Dict[str, Any]:
        """获取小说生成状态"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/novel/{novel_id}/status") as resp:
                return await resp.json()

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/health") as resp:
                return await resp.json()


async def example_api_usage():
    """API使用示例"""
    client = FantasyNovelAPIClient()

    print("Fantasy Novel MCP API 使用示例")
    print("=" * 50)

    try:
        # 1. 健康检查
        print("1. 健康检查...")
        health = await client.health_check()
        print(f"服务状态: {health.get('status', 'unknown')}")
        print(f"可用工具: {health.get('available_tools', 0)}")

        # 2. 聊天交互
        print("\n2. 聊天交互...")
        chat_response = await client.chat("请帮我创建一个玄幻世界的设定")
        print(f"AI回复: {chat_response.get('content', '')[:200]}...")

        # 3. 直接调用工具
        print("\n3. 调用世界构建工具...")
        world_response = await client.call_tool("world_builder", {
            "genre": "玄幻",
            "theme": "修仙",
            "detail_level": "basic"
        })

        if world_response.get("success"):
            world_name = world_response["result"]["world_setting"]["name"]
            print(f"生成的世界: {world_name}")

        # 4. 生成角色
        print("\n4. 生成角色...")
        character_response = await client.call_tool("character_creator", {
            "character_type": "主角",
            "genre": "玄幻",
            "count": 1
        })

        if character_response.get("success"):
            character = character_response["result"]["character"]
            print(f"生成的角色: {character['name']} ({character['character_type']})")

        # 5. 生成小说
        print("\n5. 开始生成小说...")
        novel_response = await client.generate_novel(
            title="API测试小说",
            genre="玄幻",
            chapter_count=3
        )

        if novel_response.get("success"):
            novel_id = novel_response["novel_id"]
            print(f"小说ID: {novel_id}")

            # 轮询状态
            print("轮询生成状态...")
            for i in range(10):  # 最多查询10次
                await asyncio.sleep(2)
                status = await client.get_novel_status(novel_id)

                if status.get("success"):
                    progress = status.get("progress", 0)
                    current_step = status.get("current_step", "")
                    print(f"进度: {progress:.1%} - {current_step}")

                    if status.get("status") == "completed":
                        print("✅ 小说生成完成！")
                        break
                    elif status.get("status") == "error":
                        print("❌ 小说生成失败")
                        break

        print("\n✅ API示例执行完成")

    except aiohttp.ClientError as e:
        print(f"❌ 网络错误: {e}")
        print("请确保服务器已启动: python main.py server")
    except Exception as e:
        print(f"❌ 其他错误: {e}")


if __name__ == "__main__":
    asyncio.run(example_api_usage())
