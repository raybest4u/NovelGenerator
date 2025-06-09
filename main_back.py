#!/usr/bin/env python3
"""
Fantasy Novel MCP 主程序
"""

import asyncio
import argparse
import json
from pathlib import Path

from loguru import logger
from config.settings import get_settings
from core.mcp_server import get_mcp_server
from core.llm_client import get_llm_service
from core.base_tools import get_tool_registry, ToolCall

# 注册工具
from modules.worldbuilding import register_worldbuilding_tools
from modules.character import register_character_tools
from modules.writing import register_writing_tools


class NovelGenerator:
    def __init__(self):
        self.settings = get_settings()
        self.llm_service = get_llm_service()
        self.tool_registry = get_tool_registry()
        self.mcp_server = get_mcp_server()

        # 注册工具
        self._register_tools()

    def _register_tools(self):
        logger.info("注册工具...")
        register_worldbuilding_tools()
        register_character_tools()
        register_writing_tools()
        logger.info(f"已注册 {len(self.tool_registry.tools)} 个工具")

    async def generate_world_only(self, genre: str = "玄幻", theme: str = "修仙"):
        """生成世界观"""
        call = ToolCall(
            id="world_gen",
            name="world_builder",
            parameters={"genre": genre, "theme": theme}
        )

        response = await self.tool_registry.execute_tool(call)
        if response.success:
            return response.result
        else:
            raise Exception(f"世界观生成失败: {response.error}")

    async def generate_character_only(self, character_type: str = "主角", genre: str = "玄幻"):
        """生成角色"""
        call = ToolCall(
            id="char_gen",
            name="character_creator",
            parameters={"character_type": character_type, "genre": genre}
        )

        response = await self.tool_registry.execute_tool(call)
        if response.success:
            return response.result
        else:
            raise Exception(f"角色生成失败: {response.error}")

    async def generate_simple_novel(self, title: str, genre: str = "玄幻", chapters: int = 3):
        """生成简单小说"""
        logger.info(f"开始生成小说《{title}》...")

        # 1. 生成世界观
        logger.info("生成世界观...")
        world_result = await self.generate_world_only(genre)

        # 2. 生成主角
        logger.info("生成主角...")
        char_result = await self.generate_character_only("主角", genre)

        # 3. 生成章节
        logger.info("生成章节...")
        chapter_contents = []

        for i in range(1, chapters + 1):
            chapter_info = {
                "number": i,
                "title": f"第{i}章",
                "summary": f"第{i}章的精彩内容"
            }

            call = ToolCall(
                id=f"chapter_{i}",
                name="chapter_writer", 
                parameters={
                    "chapter_info": chapter_info,
                    "target_word_count": 1500
                }
            )

            response = await self.tool_registry.execute_tool(call)
            if response.success:
                chapter_contents.append(response.result["chapter"])
                logger.info(f"完成第{i}章")
            else:
                logger.error(f"第{i}章生成失败: {response.error}")

        # 组装结果
        novel_data = {
            "title": title,
            "genre": genre,
            "world_setting": world_result["world_setting"],
            "main_character": char_result["character"],
            "chapters": chapter_contents,
            "total_words": sum(ch["word_count"] for ch in chapter_contents)
        }

        # 保存文件
        output_dir = Path("data/generated")
        output_dir.mkdir(parents=True, exist_ok=True)

        # JSON格式
        with open(output_dir / f"{title}.json", "w", encoding="utf-8") as f:
            json.dump(novel_data, f, ensure_ascii=False, indent=2)

        # TXT格式
        with open(output_dir / f"{title}.txt", "w", encoding="utf-8") as f:
            f.write(f"《{title}》\n")
            f.write(f"类型：{genre}\n")
            f.write(f"总字数：{novel_data['total_words']}\n")
            f.write("="*50 + "\n\n")

            for chapter in chapter_contents:
                f.write(f"{chapter['title']}\n")
                f.write("-"*30 + "\n")
                f.write(chapter['content'])
                f.write("\n\n")

        logger.info(f"小说生成完成！文件保存在: {output_dir}")
        return novel_data

    def start_server(self, host: str = None, port: int = None, debug: bool = None):
        """启动服务器"""
        logger.info("启动MCP服务器...")
        self.mcp_server.run(host, port, debug)

    def list_tools(self):
        """列出工具"""
        tools = self.tool_registry.list_tools()
        print("可用工具:")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")


async def main():
    parser = argparse.ArgumentParser(description="Fantasy Novel MCP")
    subparsers = parser.add_subparsers(dest="command")

    # 生成小说
    gen_parser = subparsers.add_parser("generate", help="生成小说")
    gen_parser.add_argument("--title", required=True, help="小说标题")
    gen_parser.add_argument("--genre", default="玄幻", help="小说类型")
    gen_parser.add_argument("--chapters", type=int, default=3, help="章节数")

    # 生成世界观
    world_parser = subparsers.add_parser("world", help="生成世界观")
    world_parser.add_argument("--genre", default="玄幻", help="类型")
    world_parser.add_argument("--theme", default="修仙", help="主题")

    # 生成角色
    char_parser = subparsers.add_parser("character", help="生成角色")
    char_parser.add_argument("--type", default="主角", help="角色类型")
    char_parser.add_argument("--genre", default="玄幻", help="小说类型")

    # 启动服务器
    server_parser = subparsers.add_parser("server", help="启动服务器")
    server_parser.add_argument("--host", default=None)
    server_parser.add_argument("--port", type=int, default=None)
    server_parser.add_argument("--debug", action="store_true")

    # 列出工具
    subparsers.add_parser("tools", help="列出工具")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    generator = NovelGenerator()

    try:
        if args.command == "generate":
            novel = await generator.generate_simple_novel(
                args.title, args.genre, args.chapters
            )
            print(f"✅ 小说《{novel['title']}》生成完成！")
            print(f"   总字数: {novel['total_words']}")
            print(f"   章节数: {len(novel['chapters'])}")

        elif args.command == "world":
            result = await generator.generate_world_only(args.genre, args.theme)
            print(json.dumps(result, ensure_ascii=False, indent=2))

        elif args.command == "character":
            result = await generator.generate_character_only(args.type, args.genre)
            print(json.dumps(result, ensure_ascii=False, indent=2))

        elif args.command == "server":
            generator.start_server(args.host, args.port, args.debug)

        elif args.command == "tools":
            generator.list_tools()

    except Exception as e:
        logger.error(f"执行失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())
