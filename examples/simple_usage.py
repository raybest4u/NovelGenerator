"""
简单使用示例
"""

import asyncio
from main import NovelGenerator


async def main():
    generator = NovelGenerator()

    # 生成世界观
    print("=== 生成世界观 ===")
    world = await generator.generate_world_only("玄幻", "修仙")
    print(f"世界名称: {world['world_setting']['name']}")

    # 生成角色
    print("\n=== 生成角色 ===")
    character = await generator.generate_character_only("主角", "玄幻")
    print(f"角色姓名: {character['character']['name']}")

    # 生成小说
    print("\n=== 生成小说 ===")
    novel = await generator.generate_simple_novel("测试小说", "玄幻", 2)
    print(f"小说标题: {novel['title']}")
    print(f"总字数: {novel['total_words']}")


if __name__ == "__main__":
    asyncio.run(main())
