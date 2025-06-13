# main_novel_generator.py
"""
自动小说生成主程序
整合现有工具系统，实现一键式小说生成
"""

import asyncio
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from loguru import logger

# 导入现有组件
from core.tool_registry import get_tool_registry
from core.base_tools import ToolCall
from modules.generation.enhanced_story_generator import EnhancedStoryGeneratorTool
from modules.writing.chapter_writer import ChapterWriterTool
from modules.save_txt import NovelTextFormatter
from config.config_manager import get_novel_config, get_enhanced_config
from config.settings import get_settings
from config.logger import setup_logging


class AutoNovelGenerator:
    """自动小说生成器主程序"""

    def __init__(self):
        """初始化生成器"""
        setup_logging()
        self.settings = get_settings()
        self.novel_config = get_novel_config()
        self.enhanced_config = get_enhanced_config()

        # 初始化工具注册表
        self.tool_registry = get_tool_registry()
        self._register_tools()

        # 文件保存配置
        self.output_dir = Path("generated_novels")
        self.output_dir.mkdir(exist_ok=True)

        # 初始化格式化器
        self.formatter = NovelTextFormatter()

        logger.info("自动小说生成器初始化完成")

    def _register_tools(self):
        """注册所有必要的工具"""
        try:
            # 注册增强故事生成器
            if not self.tool_registry.get_tool("enhanced_story_generator"):
                self.tool_registry.register(EnhancedStoryGeneratorTool())
                logger.info("✅ 注册增强故事生成器")

            # 注册章节写作器
            if not self.tool_registry.get_tool("chapter_writer"):
                self.tool_registry.register(ChapterWriterTool())
                logger.info("✅ 注册章节写作器")

        except Exception as e:
            logger.error(f"工具注册失败: {e}")
            raise

    async def generate_novel_auto(
        self,
        theme: str = "修仙",
        chapter_count: int = None,
        word_count_per_chapter: int = None,
        randomization_level: float = None,
        title: str = None,
        auto_save: bool = True
    ) -> Dict[str, Any]:
        """
        自动生成完整小说

        Args:
            theme: 小说主题
            chapter_count: 章节数量（默认使用配置）
            word_count_per_chapter: 每章字数（默认使用配置）
            randomization_level: 随机化程度（默认使用配置）
            title: 自定义标题
            auto_save: 是否自动保存
        """
        start_time = time.time()

        # 使用配置默认值
        chapter_count = chapter_count or self.novel_config.default_chapter_count
        word_count_per_chapter = word_count_per_chapter or self.novel_config.default_word_count
        randomization_level = randomization_level or self.enhanced_config.default_randomization_level

        logger.info(
            f"开始自动生成小说：{theme} | {chapter_count}章 | 每章{word_count_per_chapter}字")

        try:
            # 第一步：生成完整故事包（使用现有工具）
            story_package = await self._generate_story_package(
                theme, chapter_count, word_count_per_chapter, randomization_level
            )

            if not story_package.get("success", True):
                raise Exception(f"故事包生成失败: {story_package.get('error', '未知错误')}")

            # 第二步：生成具体章节内容
            chapters = await self._generate_chapters(
                story_package, chapter_count, word_count_per_chapter
            )

            # 第三步：组装最终小说
            final_novel = await self._assemble_novel(
                story_package, chapters, title or f"{theme}小说"
            )

            # 第四步：保存文件（如果启用自动保存）
            if auto_save:
                saved_path = await self._save_novel(final_novel)
                final_novel["saved_path"] = saved_path

            generation_time = time.time() - start_time
            final_novel["generation_time"] = generation_time

            logger.info(f"✅ 小说生成完成！用时 {generation_time:.2f} 秒")
            logger.info(
                f"📊 生成统计: {len(chapters)}章，总计约{sum(c.get('word_count', 0) for c in chapters):,}字")

            return final_novel

        except Exception as e:
            logger.error(f"小说生成失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "generation_time": time.time() - start_time
            }

    async def _generate_story_package(
        self, theme: str, chapter_count: int, word_count: int, randomization_level: float
    ) -> Dict[str, Any]:
        """生成故事包（配置、角色、大纲）"""
        logger.info("🎲 生成故事配置包...")

        # 调用现有的增强故事生成器
        tool_call = ToolCall(
            id=f"story_package_{int(time.time())}",
            name="enhanced_story_generator",
            parameters={
                "action": "full_story",
                "base_theme": theme,
                "chapter_count": chapter_count,
                "word_count": word_count,
                "randomization_level": randomization_level,
                "avoid_recent": True,
                "character_count": 5,
                "generate_relationships": True
            }
        )

        response = await self.tool_registry.execute_tool(tool_call)

        if not response.success:
            logger.error(f"故事包生成失败: {response.error}")
            return {"success": False, "error": response.error}

        logger.info("✅ 故事配置包生成完成")
        return response.result

    async def _generate_chapters(
        self, story_package: Dict[str, Any], chapter_count: int, word_count: int
    ) -> List[Dict[str, Any]]:
        """生成所有章节内容"""
        logger.info(f"📝 开始生成 {chapter_count} 个章节...")

        chapters = []
        story_context = {
            "characters": story_package.get("characters", []),
            "world_setting": story_package.get("plot_outline", {}),
            "story_config": story_package.get("config", {})
        }

        # 并发生成前几章，然后串行生成后续章节（保持连贯性）
        batch_size = min(3, chapter_count)  # 前3章并发生成

        # 第一批：并发生成
        first_batch_tasks = []
        for i in range(min(batch_size, chapter_count)):
            task = self._generate_single_chapter(
                i + 1, story_context, word_count, story_package
            )
            first_batch_tasks.append(task)

        first_batch = await asyncio.gather(*first_batch_tasks, return_exceptions=True)

        # 处理第一批结果
        for i, result in enumerate(first_batch):
            if isinstance(result, Exception):
                logger.error(f"第{i + 1}章生成失败: {result}")
                chapters.append(self._create_fallback_chapter(i + 1, word_count))
            else:
                chapters.append(result)
                logger.info(f"✅ 第{i + 1}章生成完成")

        # 剩余章节：串行生成（基于前面章节的内容）
        for i in range(batch_size, chapter_count):
            try:
                # 更新故事上下文，包含已生成的章节
                updated_context = story_context.copy()
                updated_context["previous_chapters"] = chapters[-3:]  # 最近3章

                chapter = await self._generate_single_chapter(
                    i + 1, updated_context, word_count, story_package
                )
                chapters.append(chapter)
                logger.info(f"✅ 第{i + 1}章生成完成")

                # 短暂延迟，避免API限流
                await asyncio.sleep(0.5)

            except Exception as e:
                logger.error(f"第{i + 1}章生成失败: {e}")
                chapters.append(self._create_fallback_chapter(i + 1, word_count))

        logger.info(f"✅ 所有章节生成完成，共 {len(chapters)} 章")
        return chapters

    async def _generate_single_chapter(
        self, chapter_num: int, story_context: Dict, word_count: int, story_package: Dict
    ) -> Dict[str, Any]:
        """生成单个章节"""

        # 根据章节位置确定章节标题和摘要
        if chapter_num == 1:
            title = "初入江湖"
            summary = "故事开始，主角首次登场"
        elif chapter_num <= 3:
            title = f"第{chapter_num}章"
            summary = "情节发展，角色建立"
        elif chapter_num >= story_package.get("chapter_count", 20) - 2:
            title = "终章"
            summary = "故事高潮与结局"
        else:
            title = f"第{chapter_num}章"
            summary = "故事发展"

        # 调用现有的章节写作器
        tool_call = ToolCall(
            id=f"chapter_{chapter_num}_{int(time.time())}",
            name="chapter_writer",
            parameters={
                "content_type": "traditional",
                "chapter_info": {"title":"test"},
                "story_context": story_context,
                "writing_style": "traditional",
                "target_word_count": 3000
            }
        )

        response = await self.tool_registry.execute_tool(tool_call)

        if response.success:
            return response.result
        else:
            logger.warning(f"章节生成器失败，使用备用方案: {response.error}")
            return self._create_fallback_chapter(chapter_num, word_count)

    def _create_fallback_chapter(self, chapter_num: int, word_count: int) -> Dict[str, Any]:
        """创建备用章节（当生成失败时）"""
        return {
            "chapter_number": chapter_num,
            "title": f"第{chapter_num}章",
            "content": f"（第{chapter_num}章内容生成中...）\n\n" + "故事正在发展中。" * (
                    word_count // 10),
            "word_count": word_count,
            "is_fallback": True
        }

    async def _assemble_novel(
        self, story_package: Dict, chapters: List[Dict], title: str
    ) -> Dict[str, Any]:
        """组装最终小说"""
        logger.info("📚 组装最终小说...")

        # 计算统计信息
        total_words = sum(c.get("word_count", 0) for c in chapters)
        successful_chapters = len([c for c in chapters if not c.get("is_fallback", False)])

        # 准备完整的小说数据包
        novel_data = {
            "title": title,
            "genre": story_package.get("config", {}).get("variant", {}).get("world_flavor", "玄幻"),
            "theme": story_package.get("base_theme", "修仙"),
            "characters": story_package.get("characters", []),
            "plot_outline": story_package.get("plot_outline", {}),
            "chapters": chapters,
            "config": story_package.get("config", {}),
            "generation_info": {
                "total_chapters": len(chapters),
                "successful_chapters": successful_chapters,
                "total_word_count": total_words,
                "generation_time": datetime.now().isoformat(),
                "randomization_level": story_package.get("config", {}).get("randomization_level",
                                                                           0.8)
            }
        }

        logger.info("✅ 小说组装完成")
        return {
            "success": True,
            "novel_data": novel_data,
            "statistics": {
                "total_chapters": len(chapters),
                "total_words": total_words,
                "successful_chapters": successful_chapters,
                "average_words_per_chapter": total_words // len(chapters) if chapters else 0
            }
        }

    async def _save_novel(self, novel_result: Dict[str, Any]) -> str:
        """保存小说到文件"""
        if not novel_result.get("success"):
            raise Exception("无法保存失败的小说生成结果")

        novel_data = novel_result["novel_data"]

        # 生成文件名
        title = novel_data["title"]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{title}_{timestamp}.txt"
        filepath = self.output_dir / filename

        # 使用现有的格式化器
        formatted_content = self.formatter.format_novel_content(novel_data)

        # 保存文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(formatted_content)

        logger.info(f"📁 小说已保存: {filepath}")
        return str(filepath)

    async def generate_multiple_novels(
        self,
        themes: List[str],
        count_per_theme: int = 1,
        **generation_params
    ) -> List[Dict[str, Any]]:
        """批量生成多部小说"""
        logger.info(f"🚀 开始批量生成小说: {len(themes)}个主题，每个主题{count_per_theme}部")

        all_results = []

        for theme in themes:
            for i in range(count_per_theme):
                logger.info(f"正在生成: {theme} 第{i + 1}部")

                # 为每部小说设置不同的随机化程度
                params = generation_params.copy()
                params["randomization_level"] = params.get("randomization_level", 0.8) + (i * 0.1)
                params["randomization_level"] = min(params["randomization_level"], 1.0)

                result = await self.generate_novel_auto(
                    theme=theme,
                    title=f"{theme}小说_{i + 1}",
                    **params
                )

                all_results.append({
                    "theme": theme,
                    "index": i + 1,
                    "result": result
                })

                # 批量生成时的延迟
                await asyncio.sleep(2)

        logger.info(f"✅ 批量生成完成，共生成 {len(all_results)} 部小说")
        return all_results


async def main():
    """主函数 - 使用示例"""
    generator = AutoNovelGenerator()

    print("🎯 自动小说生成器启动")
    print("=" * 50)

    # 示例1: 生成单部小说
    print("\n📖 生成示例小说...")
    result = await generator.generate_novel_auto(
        theme="仙侠修真",
        chapter_count=10,
        word_count_per_chapter=2500,
        randomization_level=0.85,
        title="天道轮回录"
    )

    if result.get("success"):
        stats = result["statistics"]
        print(f"✅ 生成成功!")
        print(f"   📊 {stats['total_chapters']}章，共{stats['total_words']:,}字")
        print(f"   💾 保存位置: {result.get('saved_path', 'N/A')}")
        print(f"   ⏱️  耗时: {result['generation_time']:.2f}秒")
    else:
        print(f"❌ 生成失败: {result.get('error')}")

    # 示例2: 批量生成（可选）
    # print("\n🎭 批量生成示例...")
    # batch_results = await generator.generate_multiple_novels(
    #     themes=["都市异能", "科幻", "奇幻"],
    #     count_per_theme=1,
    #     chapter_count=5,
    #     word_count_per_chapter=2000
    # )
    # print(f"✅ 批量生成完成，共{len(batch_results)}部小说")


if __name__ == "__main__":
    # 运行主程序
    asyncio.run(main())
