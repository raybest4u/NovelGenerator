# main.py
"""
玄幻小说自动生成MCP工程 - 主入口文件
提供命令行界面和服务启动功能
"""

import asyncio
import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from loguru import logger
from pygments.lexer import default

from config.settings import get_settings, validate_config
from core.mcp_server import get_mcp_server
from core.llm_client import get_llm_service
from core.base_tools import get_tool_registry

from modules.character.development import register_character_tools
from modules.plot.arc_manager import register_plot_tools
from modules.tools.consistency_checker import register_tools
from modules.worldbuilding.geography import register_worldbuilding_tools
from modules.writing.description_writer import register_writing_tools


# 注册所有工具
# from modules.worldbuilding import register_worldbuilding_tools
# from modules.character import register_character_tools
# from modules.plot import register_plot_tools
# from modules.writing import register_writing_tools
# from modules.tools import register_tools


class NovelGenerator:
    """小说生成器主类"""

    def __init__(self):
        self.settings = get_settings()
        self.llm_service = get_llm_service()
        self.tool_registry = get_tool_registry()
        self.mcp_server = get_mcp_server()

        # 注册所有工具
        self._register_all_tools()

    def _register_all_tools(self):
        """注册所有工具"""
        logger.info("正在注册工具...")

        register_worldbuilding_tools()
        register_character_tools()
        register_plot_tools()
        register_writing_tools()
        register_tools()

        tool_count = len(self.tool_registry.tools)
        logger.info(f"已注册 {tool_count} 个工具")

    async def generate_novel_complete(
        self,
        title: str,
        genre: str = "玄幻",
        chapter_count: int = 10,
        theme: str = "成长",
        auto_save: bool = True
    ) -> Dict[str, Any]:
        """完整生成一部小说"""

        logger.info(f"开始生成小说《{title}》...")

        try:
            # 1. 生成世界观
            logger.info("第1步：生成世界观设定")
            world_result = await self.tool_registry.execute_tool(
                type("ToolCall", (), {
                    "id": "world_gen",
                    "name": "world_builder",
                    "parameters": {
                        "genre": genre,
                        "theme": theme,
                        "detail_level": "detailed"
                    }
                })()
            )

            if not world_result.success:
                raise Exception(f"世界观生成失败: {world_result.error}")

            world_setting = world_result.result["world_setting"]
            logger.info("✓ 世界观设定生成完成")

            # 2. 生成角色
            logger.info("第2步：生成主要角色")
            character_result = await self.tool_registry.execute_tool(
                type("ToolCall", (), {
                    "id": "char_gen",
                    "name": "character_creator",
                    "parameters": {
                        "character_type": "主角",
                        "genre": genre,
                        "count": 3,
                        "world_setting": world_setting
                    }
                })()
            )

            if not character_result.success:
                raise Exception(f"角色生成失败: {character_result.error}")

            characters = character_result.result["characters"]
            logger.info(f"✓ 生成了 {len(characters)} 个角色")

            # 3. 生成故事大纲
            logger.info("第3步：生成故事大纲")
            story_result = await self.tool_registry.execute_tool(
                type("ToolCall", (), {
                    "id": "story_gen",
                    "name": "story_planner",
                    "parameters": {
                        "title": title,
                        "genre": genre,
                        "chapter_count": chapter_count,
                        "theme": theme,
                        "characters": characters,
                        "world_setting": world_setting
                    }
                })()
            )

            if not story_result.success:
                raise Exception(f"故事大纲生成失败: {story_result.error}")

            story_outline = story_result.result["story_outline"]
            logger.info("✓ 故事大纲生成完成")

            # 4. 生成章节内容
            logger.info("第4步：生成章节内容")
            chapters = []

            for i in range(1, chapter_count + 1):
                logger.info(f"  生成第{i}章...")

                chapter_info = {
                    "number": i,
                    "title": f"第{i}章",
                    "summary": f"第{i}章的内容",
                    "key_events": [f"第{i}章事件"],
                    "character_focus": [characters[0]["name"]] if characters else ["主角"]
                }

                story_context = {
                    "world_setting": world_setting,
                    "characters": characters,
                    "story_outline": story_outline,
                    "previous_chapters": chapters
                }

                chapter_result = await self.tool_registry.execute_tool(
                    type("ToolCall", (), {
                        "id": f"chapter_{i}",
                        "name": "chapter_writer",
                        "parameters": {
                            "chapter_info": chapter_info,
                            "story_context": story_context,
                            "writing_style": "traditional",
                            "target_word_count": 3000
                        }
                    })()
                )

                if chapter_result.success:
                    chapters.append(chapter_result.result["chapter"])
                    logger.info(
                        f"  ✓ 第{i}章生成完成 ({chapter_result.result['chapter']['total_word_count']}字)")
                else:
                    logger.error(f"  ✗ 第{i}章生成失败: {chapter_result.error}")

            # 5. 组装完整小说
            novel_data = {
                "title": title,
                "genre": genre,
                "theme": theme,
                "world_setting": world_setting,
                "characters": characters,
                "story_outline": story_outline,
                "chapters": chapters,
                "total_word_count": sum(ch.get("total_word_count", 0) for ch in chapters),
                "generation_info": {
                    "generated_at": str(asyncio.get_event_loop().time()),
                    "chapter_count": len(chapters),
                    "character_count": len(characters),
                    "settings": {
                        "genre": genre,
                        "theme": theme,
                        "target_chapters": chapter_count
                    }
                }
            }

            # 6. 保存小说
            if auto_save:
                await self._save_novel(novel_data)

            logger.info(f"✓ 小说《{title}》生成完成！总字数：{novel_data['total_word_count']}")
            return novel_data

        except Exception as e:
            logger.error(f"小说生成失败: {e}")
            raise e

    async def _save_novel(self, novel_data: Dict[str, Any]):
        """保存小说到文件"""

        output_dir = self.settings.generated_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        title = novel_data["title"]
        safe_title = "".join(c for c in title if c.isalnum() or c in "._- ")

        # 保存JSON格式的完整数据
        json_file = output_dir / f"{safe_title}_complete.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(novel_data, f, ensure_ascii=False, indent=2)

        # 保存TXT格式的小说正文
        txt_file = output_dir / f"{safe_title}.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(f"《{novel_data['title']}》\n")
            f.write(f"类型：{novel_data['genre']}\n")
            f.write(f"主题：{novel_data['theme']}\n")
            f.write(f"总字数：{novel_data['total_word_count']}\n")
            f.write("=" * 50 + "\n\n")

            for chapter in novel_data["chapters"]:
                f.write(f"{chapter['title']}\n")
                f.write("-" * 30 + "\n")

                for scene in chapter.get("scenes", []):
                    f.write(scene["content"])
                    f.write("\n\n")

                f.write("\n")

        logger.info(f"小说已保存到：{txt_file}")

    async def generate_world_only(self, genre: str = "玄幻", theme: str = "修仙") -> Dict[str, Any]:
        """仅生成世界观设定"""

        logger.info("生成世界观设定...")

        result = await self.tool_registry.execute_tool(
            type("ToolCall", (), {
                "id": "world_only",
                "name": "world_builder",
                "parameters": {
                    "genre": genre,
                    "theme": theme,
                    "detail_level": "detailed"
                }
            })()
        )

        if result.success:
            logger.info("✓ 世界观生成完成")
            return result.result
        else:
            logger.error(f"世界观生成失败: {result.error}")
            raise Exception(result.error)

    async def generate_characters_only(
        self,
        count: int = 5,
        genre: str = "玄幻",
        world_setting: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """仅生成角色"""

        logger.info(f"生成 {count} 个角色...")

        character_types = ["主角", "重要配角", "反派", "导师", "爱情线角色"]
        characters = []

        for i in range(count):
            char_type = character_types[i % len(character_types)]

            result = await self.tool_registry.execute_tool(
                type("ToolCall", (), {
                    "id": f"char_{i}",
                    "name": "character_creator",
                    "parameters": {
                        "character_type": char_type,
                        "genre": genre,
                        "world_setting": world_setting
                    }
                })()
            )

            if result.success:
                characters.append(result.result["character"])
                logger.info(f"✓ 生成角色: {result.result['character']['name']} ({char_type})")
            else:
                logger.error(f"角色生成失败: {result.error}")

        return {"characters": characters}

    def start_server(self, host: str = None, port: int = None, debug: bool = None):
        """启动MCP服务器"""

        logger.info("启动MCP服务器...")
        self.mcp_server.run(host, port, debug)

    def list_tools(self):
        """列出所有可用工具"""

        tools = self.tool_registry.list_tools()
        categories = {}

        for tool in tools:
            category = tool.category
            if category not in categories:
                categories[category] = []
            categories[category].append(tool)

        print("可用工具列表：")
        print("=" * 50)

        for category, tool_list in categories.items():
            print(f"\n【{category}】")
            for tool in tool_list:
                print(f"  - {tool.name}: {tool.description}")

        print(f"\n总计：{len(tools)} 个工具")


async def main():
    """主函数"""

    parser = argparse.ArgumentParser(description="玄幻小说自动生成MCP工程")
    subparsers = parser.add_subparsers(dest="command",  help="可用命令")

    # 生成完整小说
    gen_parser = subparsers.add_parser("generate", help="生成完整小说")
    gen_parser.add_argument("--title", default='仙路征途',  help="小说标题")
    gen_parser.add_argument("--genre", default="玄幻", help="小说类型")
    gen_parser.add_argument("--chapters", type=int, default=10, help="章节数量")
    gen_parser.add_argument("--theme", default="修仙", help="主题")
    gen_parser.add_argument("--no-save", action="store_true", help="不保存文件")

    # 仅生成世界观
    world_parser = subparsers.add_parser("world", help="仅生成世界观")
    world_parser.add_argument("--genre", default="玄幻", help="小说类型")
    world_parser.add_argument("--theme", default="修仙", help="主题")

    # 仅生成角色
    char_parser = subparsers.add_parser("characters", help="仅生成角色")
    char_parser.add_argument("--count", type=int, default=5, help="角色数量")
    char_parser.add_argument("--genre", default="玄幻", help="小说类型")

    # 启动服务器
    server_parser = subparsers.add_parser("server", help="启动MCP服务器")
    server_parser.add_argument("--host", default=None, help="服务器地址")
    server_parser.add_argument("--port", type=int, default=None, help="服务器端口")
    server_parser.add_argument("--debug", action="store_true", help="调试模式")

    # 列出工具
    subparsers.add_parser("tools", help="列出所有工具")

    # 配置验证
    subparsers.add_parser("config", help="验证配置")

    args = parser.parse_args()
    args.command = 'generate'
    logger.info(f"--->{args.command}")
    if not args.command:
        parser.print_help()
        return

    # 验证配置
    try:
        validate_config()
    except Exception as e:
        logger.error(f"配置验证失败: {e}")
        sys.exit(1)

    generator = NovelGenerator()

    try:
        if args.command == "generate":
            args = gen_parser.parse_args()
            result = await generator.generate_novel_complete(
                title=args.title,
                genre=args.genre,
                chapter_count=args.chapters,
                theme=args.theme,
                auto_save=not args.no_save
            )

            print(f"\n生成结果：")
            print(f"标题：{result['title']}")
            print(f"总字数：{result['total_word_count']}")
            print(f"章节数：{len(result['chapters'])}")
            print(f"角色数：{len(result['characters'])}")

        elif args.command == "world":
            result = await generator.generate_world_only(args.genre, args.theme)
            print(json.dumps(result, ensure_ascii=False, indent=2))

        elif args.command == "characters":
            result = await generator.generate_characters_only(args.count, args.genre)
            print(json.dumps(result, ensure_ascii=False, indent=2))

        elif args.command == "server":
            generator.start_server(args.host, args.port, args.debug)

        elif args.command == "tools":
            generator.list_tools()

        elif args.command == "config":
            print("配置验证通过！")
            settings = get_settings()
            print(f"应用名称: {settings.app_name}")
            print(f"版本: {settings.version}")
            print(f"LLM模型: {settings.llm.model_name}")
            print(f"数据目录: {settings.data_dir}")

    except KeyboardInterrupt:
        logger.info("用户中断操作")
    except Exception as e:
        logger.error(f"执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # 配置日志
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )

    # 运行主函数
    asyncio.run(main())
