# 保存小说内容为txt文件的完整实现
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from loguru import logger


class NovelTextFormatter:
    """小说文本格式化器"""

    def __init__(self):
        self.line_separator = "\n" + "=" * 60 + "\n"
        self.chapter_separator = "\n" + "-" * 40 + "\n"
        self.section_separator = "\n" + "·" * 30 + "\n"

    def format_novel_content(self, story_package: Dict[str, Any]) -> str:
        """格式化完整小说内容"""
        content_parts = []

        # 1. 标题页
        title_section = self._format_title_section(story_package)
        content_parts.append(title_section)

        # 2. 作品信息
        info_section = self._format_info_section(story_package)
        content_parts.append(info_section)

        # 3. 内容简介
        description_section = self._format_description_section(story_package)
        if description_section:
            content_parts.append(description_section)

        # 4. 角色介绍
        characters_section = self._format_characters_section(story_package)
        if characters_section:
            content_parts.append(characters_section)

        # 5. 故事大纲（可选）
        outline_section = self._format_outline_section(story_package)
        if outline_section:
            content_parts.append(outline_section)

        # 6. 正文内容
        main_content = self._format_main_content(story_package)
        content_parts.append(main_content)

        # 7. 生成信息（技术信息）
        generation_info = self._format_generation_info(story_package)
        if generation_info:
            content_parts.append(generation_info)

        return self.line_separator.join(content_parts)

    def _format_title_section(self, story_package: Dict[str, Any]) -> str:
        """格式化标题部分"""
        title = story_package.get('title', '未命名小说')
        genre = story_package.get('genre', '')
        theme = story_package.get('theme', '')

        lines = []
        lines.append("█" * 20 + " 小说作品 " + "█" * 20)
        lines.append("")
        lines.append(f"【 {title} 】".center(50))
        lines.append("")

        if genre or theme:
            subtitle_parts = []
            if genre:
                subtitle_parts.append(f"{genre}小说")
            if theme and theme != genre:
                subtitle_parts.append(f"{theme}题材")

            subtitle = " · ".join(subtitle_parts)
            lines.append(f"—— {subtitle} ——".center(50))
            lines.append("")

        lines.append(f"生成时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M')}")
        lines.append("")

        return "\n".join(lines)

    def _format_info_section(self, story_package: Dict[str, Any]) -> str:
        """格式化作品信息"""
        lines = []
        lines.append("📋 作品信息")
        lines.append("")

        # 基本信息
        title = story_package.get('title', '未命名')
        genre = story_package.get('genre', '未知')
        theme = story_package.get('theme', '未知')

        lines.append(f"作品名称：{title}")
        lines.append(f"作品类型：{genre}")
        lines.append(f"主要题材：{theme}")

        # 章节统计
        chapters = story_package.get('chapters', [])
        characters = story_package.get('characters', [])

        lines.append(f"章节数量：{len(chapters)} 章")
        lines.append(f"角色数量：{len(characters)} 个")

        # 字数统计
        total_words = sum(ch.get('word_count', len(ch.get('content', ''))) for ch in chapters)
        lines.append(f"总计字数：约 {total_words:,} 字")

        # 生成配置信息
        config = story_package.get('config', {})
        variant = config.get('variant', {})
        if variant:
            lines.append("")
            lines.append("📖 创作设定：")
            if variant.get('story_structure'):
                lines.append(f"  故事结构：{variant['story_structure']}")
            if variant.get('world_flavor'):
                lines.append(f"  世界设定：{variant['world_flavor']}")
            if variant.get('character_archetype'):
                lines.append(f"  角色原型：{variant['character_archetype']}")
            if variant.get('tone'):
                lines.append(f"  整体基调：{variant['tone']}")

        return "\n".join(lines)

    def _format_description_section(self, story_package: Dict[str, Any]) -> Optional[str]:
        """格式化作品简介"""
        # 尝试从多个字段获取描述
        description_sources = [
            story_package.get('description', ''),
            story_package.get('premise', ''),
            story_package.get('summary', '')
        ]

        # 尝试从plot_outline中获取描述
        plot_outline = story_package.get('plot_outline', {})
        if plot_outline:
            description_sources.extend([
                plot_outline.get('premise', ''),
                plot_outline.get('detailed_outline', '')[:300] + '...' if plot_outline.get(
                    'detailed_outline') else ''
            ])

        # 选择最长的非空描述
        description = max([desc for desc in description_sources if desc], key=len, default='')

        if not description:
            return None

        lines = []
        lines.append("📖 内容简介")
        lines.append("")

        # 格式化描述内容
        formatted_desc = self._format_paragraph(description)
        lines.append(formatted_desc)

        return "\n".join(lines)

    def _format_characters_section(self, story_package: Dict[str, Any]) -> Optional[str]:
        """格式化角色介绍"""
        characters = story_package.get('characters', [])
        if not characters:
            return None

        lines = []
        lines.append("👥 主要角色")
        lines.append("")

        for i, character in enumerate(characters, 1):
            name = character.get('name', f'角色{i}')
            role = character.get('role', '未知角色')

            lines.append(f"{i}. 【{name}】")

            # 角色类型
            role_map = {
                'protagonist': '主角',
                'antagonist': '反派',
                'deuteragonist': '重要配角',
                'supporting': '配角',
                'minor': '次要角色'
            }
            role_chinese = role_map.get(role, role)
            lines.append(f"   角色定位：{role_chinese}")

            # 角色描述
            description = character.get('description', '')
            appearance = character.get('appearance', '')
            personality = character.get('personality', '')
            background = character.get('background', '')

            # 合并描述信息
            char_info = []
            if description:
                char_info.append(description)
            if appearance:
                char_info.append(f"外貌：{self._truncate_text(appearance, 100)}")
            if personality:
                char_info.append(f"性格：{self._truncate_text(personality, 100)}")
            if background:
                char_info.append(f"背景：{self._truncate_text(background, 100)}")

            for info in char_info[:3]:  # 最多显示3个方面
                lines.append(f"   {info}")

            lines.append("")

        return "\n".join(lines)

    def _format_outline_section(self, story_package: Dict[str, Any]) -> Optional[str]:
        """格式化故事大纲"""
        plot_outline = story_package.get('plot_outline', {})
        if not plot_outline:
            return None

        lines = []
        lines.append("📋 故事大纲")
        lines.append("")

        # 故事结构
        structure = plot_outline.get('story_structure', '')
        if structure:
            lines.append(f"叙事结构：{structure}")
            lines.append("")

        # 详细大纲
        detailed_outline = plot_outline.get('detailed_outline', '')
        if detailed_outline:
            lines.append("情节概要：")
            formatted_outline = self._format_paragraph(detailed_outline)
            lines.append(formatted_outline)
            lines.append("")

        # 创新元素
        innovation_factors = plot_outline.get('innovation_integration', [])
        if innovation_factors:
            lines.append(f"创新元素：{', '.join(innovation_factors)}")
            lines.append("")

        return "\n".join(lines)

    def _format_main_content(self, story_package: Dict[str, Any]) -> str:
        """格式化正文内容"""
        chapters = story_package.get('chapters', [])

        if not chapters:
            return "📚 正文内容\n\n暂无章节内容。"

        lines = []
        lines.append("📚 正文内容")
        lines.append("")

        for i, chapter in enumerate(chapters, 1):
            # 章节标题
            chapter_title = chapter.get('title', f'第{i}章')
            lines.append(f"第{i}章  {chapter_title}")
            lines.append("")

            # 章节摘要（如果有）
            summary = chapter.get('summary', '')
            if summary:
                lines.append(f"【本章概要】{summary}")
                lines.append("")

            # 章节正文
            content = chapter.get('content', '')
            if content:
                formatted_content = self._format_chapter_content(content)
                lines.append(formatted_content)
            else:
                lines.append("（本章内容暂未生成）")

            lines.append("")

            # 章节分隔符
            if i < len(chapters):
                lines.append(self.chapter_separator)

        return "\n".join(lines)

    def _format_generation_info(self, story_package: Dict[str, Any]) -> Optional[str]:
        """格式化生成信息"""
        generation_info = story_package.get('generation_info', {})
        config = story_package.get('config', {})

        if not generation_info and not config:
            return None

        lines = []
        lines.append("🔧 生成信息")
        lines.append("")

        # 生成参数
        if generation_info:
            lines.append("生成参数：")
            randomization_level = generation_info.get('randomization_level', 0)
            lines.append(f"  随机化程度：{randomization_level:.1f}")

            chapter_count = generation_info.get('chapter_count', 0)
            if chapter_count:
                lines.append(f"  目标章节数：{chapter_count}")

            total_word_count = generation_info.get('total_word_count', 0)
            if total_word_count:
                lines.append(f"  目标字数：{total_word_count:,}")

        # 技术信息
        variant = config.get('variant', {})
        if variant:
            lines.append("")
            lines.append("技术细节：")
            if variant.get('variant_id'):
                lines.append(f"  变体ID：{variant['variant_id']}")
            if variant.get('conflict_type'):
                lines.append(f"  冲突类型：{variant['conflict_type']}")

        lines.append("")
        lines.append(f"本文件生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return "\n".join(lines)

    def _format_paragraph(self, text: str, line_length: int = 80) -> str:
        """格式化段落，自动换行"""
        if not text:
            return ""

        # 清理文本
        text = re.sub(r'\s+', ' ', text.strip())

        # 简单的换行处理
        words = text.split(' ')
        lines = []
        current_line = ""

        for word in words:
            if len(current_line + word) <= line_length:
                current_line += word + " "
            else:
                if current_line:
                    lines.append(current_line.strip())
                current_line = word + " "

        if current_line:
            lines.append(current_line.strip())

        return "\n".join(lines)

    def _format_chapter_content(self, content: str) -> str:
        """格式化章节内容"""
        if not content:
            return ""

        # 分段处理
        paragraphs = content.split('\n')
        formatted_paragraphs = []

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if paragraph:
                # 添加适当的缩进
                formatted_paragraph = "    " + paragraph
                formatted_paragraphs.append(formatted_paragraph)

        return "\n\n".join(formatted_paragraphs)

    def _truncate_text(self, text: str, max_length: int) -> str:
        """截断文本"""
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."


async def save_novel_as_txt(story_package: Dict[str, Any], output_dir: str = "generated_novels") -> \
Dict[str, Any]:
    """保存小说为txt文件"""
    try:
        # 创建输出目录
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # 生成文件名
        title = story_package.get('title', '未命名小说')
        # 清理文件名中的特殊字符
        safe_title = re.sub(r'[<>:"/\\|?*]', '', title)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_title}_{timestamp}.txt"
        filepath = output_path / filename

        # 格式化小说内容
        formatter = NovelTextFormatter()
        formatted_content = formatter.format_novel_content(story_package)

        # 保存文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(formatted_content)

        # 计算文件统计
        file_size = filepath.stat().st_size
        lines_count = formatted_content.count('\n') + 1
        words_count = len(formatted_content.split())

        logger.info(f"✅ 小说txt文件保存成功: {filepath}")

        return {
            "success": True,
            "filepath": str(filepath),
            "filename": filename,
            "title": title,
            "file_size": file_size,
            "lines_count": lines_count,
            "words_count": words_count,
            "chapters_count": len(story_package.get('chapters', [])),
            "characters_count": len(story_package.get('characters', []))
        }

    except Exception as e:
        logger.error(f"保存txt文件失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "filepath": None
        }


# 在main.py中集成使用的方法
async def _save_story_enhanced(self, story: dict):
    """增强版保存故事方法 - 支持多种格式"""
    try:
        print("\n💾 选择保存格式:")
        print("1. 数据库 + JSON备份 (推荐)")
        print("2. 仅保存txt小说文件")
        print("3. 同时保存数据库和txt文件")
        print("4. 仅保存JSON文件")

        choice = input("请选择保存方式 (1-4): ").strip()

        results = []

        if choice in ['1', '3']:
            # 保存到数据库
            print("\n📚 保存到数据库...")
            try:
                from enhanced_save_story import save_story_enhanced
                db_result = await save_story_enhanced(story)
                if db_result['success']:
                    print(f"✅ 数据库保存成功 (ID: {db_result['novel_id']})")
                    results.append(f"数据库: 成功 (ID: {db_result['novel_id']})")
                else:
                    print(f"❌ 数据库保存失败: {db_result['error']}")
                    results.append(f"数据库: 失败 ({db_result['error']})")
            except ImportError:
                print("⚠️ 数据库模块不可用，跳过数据库保存")
                results.append("数据库: 跳过 (模块不可用)")

        if choice in ['2', '3']:
            # 保存为txt文件
            print("\n📄 保存为txt文件...")
            txt_result = await save_novel_as_txt(story)
            if txt_result['success']:
                print(f"✅ txt文件保存成功: {txt_result['filename']}")
                print(f"📊 文件信息: {txt_result['words_count']} 字, {txt_result['lines_count']} 行")
                results.append(f"txt文件: {txt_result['filename']}")
            else:
                print(f"❌ txt文件保存失败: {txt_result['error']}")
                results.append(f"txt文件: 失败 ({txt_result['error']})")

        if choice == '4':
            # 仅保存JSON
            print("\n📋 保存为JSON文件...")
            await self._save_story_json_backup(story)
            results.append("JSON文件: 保存完成")

        # 显示保存结果汇总
        print(f"\n📁 保存结果汇总:")
        for result in results:
            print(f"  • {result}")

        print(f"\n📂 文件位置: generated_novels/")

    except Exception as e:
        logger.error(f"保存过程出错: {e}")
        print(f"❌ 保存失败: {e}")

        # 紧急备份
        emergency = input("是否创建紧急JSON备份? (y/n): ").strip().lower()
        if emergency == 'y':
            await self._save_story_json_backup(story)


async def _save_story_json_backup(self, story: dict):
    """JSON备份保存方法"""
    try:
        import json
        from datetime import datetime

        # 创建保存目录
        save_dir = Path("generated_novels")
        save_dir.mkdir(exist_ok=True)

        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        title = story.get('title', '未命名')
        safe_title = re.sub(r'[<>:"/\\|?*]', '', title)
        filename = f"{safe_title}_backup_{timestamp}.json"
        filepath = save_dir / filename

        # 保存文件
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(story, f, ensure_ascii=False, indent=2)

        print(f"📁 JSON备份已保存: {filepath}")

    except Exception as e:
        logger.error(f"JSON备份失败: {e}")
        print(f"❌ JSON备份失败: {e}")


# 快速测试保存功能
async def test_save_txt():
    """测试txt保存功能"""
    # 模拟故事包数据
    test_story = {
        "title": "测试小说",
        "genre": "玄幻",
        "theme": "修仙",
        "description": "这是一个测试小说的描述，用来验证txt保存功能是否正常工作。",
        "chapters": [
            {
                "number": 1,
                "title": "开篇",
                "content": "这是第一章的内容。\n\n李逍遥站在山巅，望着远方的云海，心中涌起一阵豪情。\n\n'总有一天，我要踏破这片天空！'他暗自发誓。",
                "word_count": 50,
                "summary": "主角初次登场，立下豪言壮志"
            },
            {
                "number": 2,
                "title": "修炼",
                "content": "经过一夜的修炼，李逍遥感觉体内真气有所增长。\n\n师父曾说过，修仙之路艰难险阻，唯有持之以恒方能成功。",
                "word_count": 40,
                "summary": "主角开始修炼，师父传授心法"
            }
        ],
        "characters": [
            {
                "name": "李逍遥",
                "role": "protagonist",
                "description": "年轻有为的修仙者",
                "appearance": "剑眉星目，气质不凡",
                "personality": "坚毅果敢，心地善良"
            }
        ],
        "config": {
            "variant": {
                "story_structure": "英雄之旅",
                "world_flavor": "古典仙侠",
                "character_archetype": "不羁浪子",
                "tone": "热血励志"
            }
        },
        "generation_info": {
            "randomization_level": 0.8,
            "chapter_count": 2,
            "total_word_count": 90
        }
    }

    result = await save_novel_as_txt(test_story)
    print(f"测试结果: {result}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_save_txt())
