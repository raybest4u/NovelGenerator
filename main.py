# main.py - 重构后的简化主程序
"""
小说生成器主程序 - 重构版本
消除重复代码，统一模块管理
"""
import asyncio
import argparse
from pathlib import Path
from loguru import logger

from config.settings import get_settings, validate_config
from core.tool_registry import get_tool_registry
from core.mcp_server import get_mcp_server
from core.cache_manager import get_cache_manager

# 统一的模块注册
from modules import register_all_tools


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

        # 显示注册信息
        stats = self.cache_manager.get_stats()
        tools_count = len(self.tool_registry.tools)

        logger.info(f"✅ 初始化完成")
        logger.info(f"📦 已注册工具: {tools_count} 个")
        logger.info(f"💾 缓存命名空间: {stats['namespaces']} 个")

        self._initialized = True

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
  缓存命名空间: {cache_stats['namespaces']} 个
  缓存项总数: {cache_stats['total_items']} 个

🗂️ 工具分布:""")

        for category, count in cache_stats.get('namespace_details', {}).items():
            print(f"  {category}: {count} 项")

    async def _interactive_generate(self):
        """交互式生成"""
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
                "action": "full_story",
                "base_theme": theme,
                "chapter_count": 5,  # 简化为5章
                "randomization_level": 0.8
            })

            if result and result.get("story_package"):
                story = result["story_package"]
                print(f"""
✅ 生成完成！

📖 故事信息:
  标题: {story.get('title', '未命名')}
  类型: {story.get('genre', '未知')}
  主题: {story.get('theme', '未知')}
  章节数: {len(story.get('chapters', []))}

🎭 主要角色: {len(story.get('characters', []))} 个
📋 生成配置: {story.get('config', {}).get('variant', {}).get('structure', '未知')}
""")

                # 询问是否保存
                save = input("是否保存生成结果? (y/n): ").strip().lower()
                if save == 'y':
                    await self._save_story(story)
            else:
                print("❌ 生成失败")

        except Exception as e:
            logger.error(f"生成过程出错: {e}")
            print(f"❌ 生成失败: {e}")

    async def _save_story(self, story: dict):
        """保存故事"""
        try:
            import json
            from datetime import datetime

            # 创建保存目录
            save_dir = Path("generated_novels")
            save_dir.mkdir(exist_ok=True)

            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"novel_{timestamp}.json"
            filepath = save_dir / filename

            # 保存文件
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(story, f, ensure_ascii=False, indent=2)

            print(f"✅ 故事已保存到: {filepath}")

        except Exception as e:
            logger.error(f"保存失败: {e}")
            print(f"❌ 保存失败: {e}")


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
