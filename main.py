# main.py - 重构后的简化主程序
"""
小说生成器主程序 - 重构版本
消除重复代码，统一模块管理
"""
import asyncio
import argparse
import json
import time
from datetime import datetime
from pathlib import Path
from loguru import logger

from config.settings import get_settings, validate_config
from core.tool_registry import get_tool_registry
from core.mcp_server import get_mcp_server
from core.cache_manager import get_cache_manager

# 统一的模块注册
from modules import register_all_tools
from modules.save_story import save_story_enhanced
from modules.save_txt import save_novel_as_txt


class NovelGenerator:
    """小说生成器主类 - 简化版本"""

    def __init__(self):
        self.settings = get_settings()
        self.tool_registry = get_tool_registry()
        self.mcp_server = get_mcp_server()
        self.cache_manager = get_cache_manager()

        self._initialized = False

    async def initialize(self):
        """初始化系统"""
        if self._initialized:
            return

        logger.info("🚀 初始化小说生成器...")

        # 验证配置
        validate_config()

        # 注册所有工具模块
        register_all_tools(self.tool_registry)

        # 检查必需工具
        if not self._check_required_tools():
            logger.error("工具检查失败，部分功能可能无法使用")

        # 显示注册信息
        stats = self.cache_manager.get_stats()
        tools_count = len(self.tool_registry.tools)

        logger.info(f"✅ 初始化完成")
        logger.info(f"📦 已注册工具: {tools_count} 个")
        logger.info(f"💾 缓存命名空间: {stats['namespaces']} 个")

        self._initialized = True

    def _check_required_tools(self) -> bool:
        """检查必需工具是否已注册"""
        required_tools = [
            "enhanced_story_generator",
            "character_creator",
            "story_planner"
        ]

        missing_tools = []
        for tool_name in required_tools:
            if not self.tool_registry.get_tool(tool_name):
                missing_tools.append(tool_name)

        if missing_tools:
            logger.error(f"缺少必需工具: {missing_tools}")
            print(f"❌ 缺少必需工具: {', '.join(missing_tools)}")
            print("请检查工具注册是否正确")
            return False

        return True

    async def run_server(self, host: str = None, port: int = None):
        """运行MCP服务器"""
        await self.initialize()

        host = host or self.settings.mcp.host
        port = port or self.settings.mcp.port

        logger.info(f"🌐 启动MCP服务器: http://{host}:{port}")
        self.mcp_server.run(host=host, port=port)

    async def run_cli(self):
        """运行命令行接口"""
        await self.initialize()

        logger.info("💻 启动命令行接口")

        while True:
            try:
                # 简单的命令行交互
                user_input = input("\n请输入命令 (help/generate/stats/quit): ").strip().lower()

                if user_input == "quit":
                    break
                elif user_input == "help":
                    self._show_help()
                elif user_input == "generate":
                    await self._interactive_generate()
                elif user_input == "stats":
                    self._show_stats()
                else:
                    print("未知命令，输入 'help' 查看帮助")

            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"命令执行失败: {e}")

        logger.info("👋 再见！")

    def _show_help(self):
        """显示帮助信息"""
        print("""
🎯 可用命令:
  help     - 显示此帮助信息
  generate - 交互式生成小说
  stats    - 显示系统状态
  quit     - 退出程序

🔧 可用工具类别:
""")
        for category in self.tool_registry.categories:
            tools = self.tool_registry.list_tools(category,True)
            print(f"  {category}: {len(tools)} 个工具")

    def _show_stats(self):
        """显示系统统计"""
        cache_stats = self.cache_manager.get_stats()

        print(f"""
        📊 系统状态:
          已注册工具: {len(self.tool_registry.tools)} 个
          工具类别: {len(self.tool_registry.categories)} 个
          缓存命名空间: {cache_stats.get('namespaces', 0)} 个
          缓存项目数: {cache_stats.get('total_items', 0)} 个
          系统运行时间: {time.time() - self.tool_registry.start_time:.1f} 秒
        """)

        for category, count in cache_stats.get('namespace_details', {}).items():
            print(f"  {category}: {count} 项")

    async def _interactive_generate(self):
        """交互式生成 - 修复版本"""
        print("\n🎨 小说生成向导")

        try:
            # 获取用户输入
            theme = input("请输入小说主题 (如: 修仙, 都市, 科幻): ").strip()
            if not theme:
                theme = "修仙"

            # 使用增强版故事生成器
            enhanced_tool = self.tool_registry.get_tool("enhanced_story_generator")
            if not enhanced_tool:
                print("❌ 增强版故事生成器未找到")
                return

            print(f"🎯 开始生成 '{theme}' 主题小说...")

            # 生成故事包
            result = await enhanced_tool.execute({
                "action": "generate_full_story",
                "base_theme": theme,
                "chapter_count": 5,  # 简化为5章
                "randomization_level": 0.8
            })

            if result and result.get("story_package"):
                story = result["story_package"]

                # 安全获取数据，避免索引错误
                title = story.get('title', '未命名')
                genre = story.get('genre', '未知')
                theme_actual = story.get('theme', '未知')
                chapters = story.get('chapters', [])
                characters = story.get('characters', [])
                config = story.get('config', {})

                # 安全获取配置信息
                variant_info = config.get('variant', {})
                structure = variant_info.get('structure', '标准结构') if variant_info else '标准结构'

                print(f"""
✅ 生成完成！

📖 故事信息:
  标题: {title}
  类型: {genre}
  主题: {theme_actual}
  章节数: {len(chapters)}

🎭 主要角色: {len(characters)} 个
📋 生成配置: {structure}
""")

                # 显示章节预览（如果有章节）
                if chapters:
                    print("\n📚 章节预览:")
                    for i, chapter in enumerate(chapters[:3], 1):  # 只显示前3章
                        chapter_title = chapter.get('title', f'第{i}章')
                        chapter_summary = chapter.get('summary', '暂无摘要')
                        word_count = chapter.get('word_count', 0)
                        print(f"  {i}. {chapter_title} ({word_count}字)")
                        print(f"     {chapter_summary[:50]}...")

                    if len(chapters) > 3:
                        print(f"  ... 还有 {len(chapters) - 3} 章")
                else:
                    print("\n⚠️ 未生成章节内容")

                # 显示角色信息（如果有角色）
                if characters:
                    print("\n👥 主要角色:")
                    for i, char in enumerate(characters[:3], 1):  # 只显示前3个角色
                        char_name = char.get('name', f'角色{i}')
                        char_role = char.get('role', '未知角色')
                        print(f"  {i}. {char_name} - {char_role}")

                    if len(characters) > 3:
                        print(f"  ... 还有 {len(characters) - 3} 个角色")
                else:
                    print("\n⚠️ 未生成角色信息")

                # 询问是否保存
                save = input("\n是否保存生成结果? (y/n): ").strip().lower()
                if save == 'y':
                    await self._save_story(story)
            else:
                print("❌ 生成失败 - 未返回有效的故事包")
                # 显示错误详情
                if result:
                    error_msg = result.get('error', '未知错误')
                    print(f"错误详情: {error_msg}")

        except Exception as e:
            import traceback
            logger.error(f"生成过程出错: {e}")
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            print(f"❌ 生成失败: {e}")
            print("请检查工具是否正确注册和配置")

    async def _save_story(self, story: dict):
        """保存故事"""
        try:
            result = await save_novel_as_txt(story)
            await self._interactive_save_story(story)

        except Exception as e:
            logger.error(f"保存失败: {e}")
            print(f"❌ 保存失败: {e}")

    async def _interactive_save_story(self, story: dict):
        """交互式保存故事 - 集成版本"""
        try:
            print("\n💾 开始保存故事...")

            # 使用增强版保存方法
            result = await save_story_enhanced(story)

            if result['success']:
                print(f"""
    ✅ 故事保存成功！

    📖 保存信息:
      小说ID: {result['novel_id']}
      标题: {result['title']}
      章节数: {result['chapters_saved']}
      角色数: {result['characters_saved']}
      总字数: {result['total_word_count']}
      保存时间: {result['saved_at']}

    📁 数据库位置: fantasy_novel.db
    📁 JSON备份: generated_novels/backups/
    """)
            else:
                print(f"❌ 保存失败: {result['error']}")

                # 提供JSON备份选项
                fallback = input("是否保存为JSON文件作为备份? (y/n): ").strip().lower()
                if fallback == 'y':
                    await self._save_story_json_fallback(story)

        except Exception as e:
            logger.error(f"保存过程出错: {e}")
            print(f"❌ 保存失败: {e}")

            # 提供紧急备份
            emergency = input("是否创建紧急JSON备份? (y/n): ").strip().lower()
            if emergency == 'y':
                await self._save_story_json_fallback(story)

    async def _save_story_json_fallback(self, story: dict):
        """JSON备份保存方法"""
        try:
            from pathlib import Path

            # 创建保存目录
            save_dir = Path("generated_novels")
            save_dir.mkdir(exist_ok=True)

            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"novel_backup_{timestamp}.json"
            filepath = save_dir / filename

            # 保存文件
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(story, f, ensure_ascii=False, indent=2)

            print(f"📁 紧急备份已保存: {filepath}")

        except Exception as e:
            logger.error(f"紧急备份失败: {e}")
            print(f"❌ 紧急备份失败: {e}")


async def _interactive_generate(self):
    """交互式生成 - 优化版本"""
    print("\n🎨 小说生成向导")

    try:
        # 获取用户输入
        theme = input("请输入小说主题 (如: 修仙, 都市, 科幻): ").strip()
        if not theme:
            theme = "修仙"

        # 新增：询问角色数量
        char_count_input = input("请输入希望生成的角色数量 (默认5个): ").strip()
        try:
            char_count = int(char_count_input) if char_count_input else 5
            char_count = max(3, min(char_count, 15))  # 限制在3-15个之间
        except ValueError:
            char_count = 5

        # 新增：询问是否生成角色关系
        generate_relationships = input("是否生成角色关系网络? (y/n, 默认y): ").strip().lower()
        if generate_relationships in ['', 'y', 'yes']:
            generate_relationships = True
        else:
            generate_relationships = False

        print(f"\n🎯 生成参数:")
        print(f"  主题: {theme}")
        print(f"  角色数量: {char_count}")
        print(f"  生成关系: {'是' if generate_relationships else '否'}")

        # 使用增强版故事生成器
        enhanced_tool = self.tool_registry.get_tool("enhanced_story_generator")
        if not enhanced_tool:
            print("❌ 增强版故事生成器未找到")
            return

        print("\n🚀 开始生成故事...")

        # 生成故事包
        result = await enhanced_tool.execute({
            "action": "generate_full_story",
            "theme": theme,
            "character_count": char_count,  # 新增参数
            "generate_relationships": generate_relationships,  # 新增参数
            "chapter_count": 10,
            "word_count": 3000
        })

        if result and "story_package" in result:
            story = result["story_package"]

            print("\n✅ 故事生成完成！")
            print(f"📖 标题: {story.get('title', '未命名')}")
            print(f"📝 类型: {story.get('genre', '未知')}")
            print(f"📊 章节数: {len(story.get('chapters', []))}")

            # 显示角色信息
            characters = story.get("characters", [])
            if characters:
                print(f"\n👥 生成了 {len(characters)} 个角色:")
                for i, char in enumerate(characters[:5]):  # 显示前5个
                    char_name = char.get('name', f'角色{i + 1}')
                    char_role = char.get('story_role', '未知角色')
                    print(f"  {i + 1}. {char_name} - {char_role}")

                if len(characters) > 5:
                    print(f"  ... 还有 {len(characters) - 5} 个角色")

                # 新增：显示关系信息
                if generate_relationships:
                    relationships = story.get("relationships", [])
                    if relationships:
                        print(f"\n🔗 生成了 {len(relationships)} 个角色关系:")
                        for i, rel in enumerate(relationships[:3]):  # 显示前3个关系
                            char1_name = self._get_character_name_by_id(characters,
                                                                        rel.get('character1_id'))
                            char2_name = self._get_character_name_by_id(characters,
                                                                        rel.get('character2_id'))
                            rel_type = rel.get('relationship_type', '未知关系')
                            print(f"  {i + 1}. {char1_name} ↔ {char2_name} ({rel_type})")

                        if len(relationships) > 3:
                            print(f"  ... 还有 {len(relationships) - 3} 个关系")
                    else:
                        print("\n⚠️ 未生成角色关系")
            else:
                print("\n⚠️ 未生成角色信息")

            # 询问是否保存
            save = input("\n是否保存生成结果? (y/n): ").strip().lower()
            if save == 'y':
                await self._save_story(story)
        else:
            print("❌ 生成失败 - 未返回有效的故事包")
            if result:
                error_msg = result.get('error', '未知错误')
                print(f"错误详情: {error_msg}")

    except Exception as e:
        import traceback
        logger.error(f"生成过程出错: {e}")
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        print(f"❌ 生成失败: {e}")
        print("请检查工具是否正确注册和配置")


def _get_character_name_by_id(self, characters: list, char_id: str) -> str:
    """根据ID获取角色名称"""
    for char in characters:
        if char.get('id') == char_id:
            return char.get('name', '未知角色')
    return '未知角色'


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="玄幻小说自动生成器")
    parser.add_argument("--mode", choices=["server", "cli"], default="cli",
                        help="运行模式 (server/cli)")
    parser.add_argument("--host", default="localhost", help="服务器地址")
    parser.add_argument("--port", type=int, default=8080, help="服务器端口")
    parser.add_argument("--debug", action="store_true", help="调试模式")

    args = parser.parse_args()

    # 设置日志级别
    if args.debug:
        logger.remove()
        logger.add(lambda msg: print(msg, end=""), level="DEBUG")

    # 创建生成器
    generator = NovelGenerator()

    try:
        if args.mode == "server":
            await generator.run_server(args.host, args.port)
        else:
            await generator.run_cli()
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序异常退出: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
