# quick_start.py
"""
快速启动脚本 - 一键生成小说
"""

import asyncio
import sys
import argparse
from pathlib import Path

# 确保可以导入主程序
sys.path.append(str(Path(__file__).parent))

from main_novel_generator import AutoNovelGenerator


async def quick_generate():
    """快速生成小说"""
    parser = argparse.ArgumentParser(description='一键生成小说')
    parser.add_argument('--theme', '-t', default='修仙', help='小说主题（默认：修仙）')
    parser.add_argument('--title', '-n', default=None, help='小说标题（默认自动生成）')
    parser.add_argument('--chapters', '-c', type=int, default=10, help='章节数（默认：10）')
    parser.add_argument('--words', '-w', type=int, default=2500, help='每章字数（默认：2500）')
    parser.add_argument('--random', '-r', type=float, default=0.8, help='随机程度0-1（默认：0.8）')
    parser.add_argument('--batch', '-b', action='store_true', help='批量生成模式')

    args = parser.parse_args()

    print("🎯 自动小说生成器")
    print("=" * 40)
    print(f"主题: {args.theme}")
    print(f"章节: {args.chapters}章")
    print(f"字数: {args.words}字/章")
    print(f"随机度: {args.random}")
    print("=" * 40)

    generator = AutoNovelGenerator()

    if args.batch:
        # 批量生成模式
        themes = ["修仙", "都市异能", "科幻", "玄幻", "武侠"]
        print(f"🚀 批量生成模式，将生成 {len(themes)} 部小说...")

        results = await generator.generate_multiple_novels(
            themes=themes,
            count_per_theme=1,
            chapter_count=args.chapters,
            word_count_per_chapter=args.words,
            randomization_level=args.random
        )

        print(f"✅ 批量生成完成！共生成 {len(results)} 部小说")

    else:
        # 单部小说生成
        print("📝 开始生成小说...")

        result = await generator.generate_novel_auto(
            theme=args.theme,
            title=args.title,
            chapter_count=args.chapters,
            word_count_per_chapter=args.words,
            randomization_level=args.random
        )

        if result.get("success"):
            stats = result["statistics"]
            print("\n🎉 生成成功！")
            print(f"📖 标题: {result['novel_data']['title']}")
            print(f"📊 统计: {stats['total_chapters']}章，{stats['total_words']:,}字")
            print(f"💾 文件: {result.get('saved_path', 'N/A')}")
            print(f"⏱️  耗时: {result['generation_time']:.1f}秒")
        else:
            print(f"❌ 生成失败: {result.get('error')}")


def main():
    """命令行入口"""
    try:
        asyncio.run(quick_generate())
    except KeyboardInterrupt:
        print("\n👋 用户取消生成")
    except Exception as e:
        print(f"❌ 程序出错: {e}")


if __name__ == "__main__":
    main()
