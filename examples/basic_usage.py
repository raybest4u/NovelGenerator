# examples/basic_usage.py
"""
基本使用示例
展示如何使用Fantasy Novel MCP的主要功能
"""

import asyncio
import json
from pathlib import Path
import sys

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

from main import NovelGenerator
from core.base_tools import ToolCall, get_tool_registry
from config.settings import get_settings


async def example_generate_world():
    """示例：生成世界观"""
    print("=" * 50)
    print("示例1：生成世界观设定")
    print("=" * 50)

    generator = NovelGenerator()

    try:
        result = await generator.generate_world_only("玄幻", "修仙")

        world_setting = result["world_setting"]
        print(f"世界名称: {world_setting['name']}")
        print(f"世界类型: {world_setting['type']}")
        print(f"主要种族: {', '.join(world_setting['major_races'])}")
        print(f"独特元素: {', '.join(world_setting['unique_elements'])}")

        # 保存结果
        with open("example_world.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print("\n✅ 世界观生成完成，已保存到 example_world.json")
        return world_setting

    except Exception as e:
        print(f"❌ 世界观生成失败: {e}")
        return None


async def example_generate_characters():
    """示例：生成角色"""
    print("\n" + "=" * 50)
    print("示例2：生成角色")
    print("=" * 50)

    generator = NovelGenerator()

    try:
        result = await generator.generate_characters_only(3, "玄幻")

        characters = result["characters"]
        for i, char in enumerate(characters, 1):
            print(f"\n角色{i}:")
            print(f"  姓名: {char['name']}")
            print(f"  类型: {char['character_type']}")
            print(f"  性别: {char['appearance']['gender']}")
            print(f"  年龄: {char['appearance']['age']}")
            print(f"  重要性: {char['importance']}/10")

        # 保存结果
        with open("example_characters.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print("\n✅ 角色生成完成，已保存到 example_characters.json")
        return characters

    except Exception as e:
        print(f"❌ 角色生成失败: {e}")
        return []


async def example_generate_story_outline():
    """示例：生成故事大纲"""
    print("\n" + "=" * 50)
    print("示例3：生成故事大纲")
    print("=" * 50)

    registry = get_tool_registry()

    try:
        # 调用故事规划工具
        call = ToolCall(
            id="outline_example",
            name="story_planner",
            parameters={
                "title": "仙路征途",
                "genre": "玄幻",
                "chapter_count": 10,
                "structure": "三幕式",
                "theme": "成长"
            }
        )

        response = await registry.execute_tool(call)

        if response.success:
            outline = response.result["story_outline"]
            print(f"故事标题: {outline['title']}")
            print(f"故事类型: {outline['genre']}")
            print(f"主要主题: {outline['theme']}")
            print(f"情节结构: {outline['structure']}")
            print(f"章节数量: {len(outline['chapters'])}")

            print("\n主要情节点:")
            for point in outline['plot_points'][:3]:  # 显示前3个
                print(f"  - {point['name']}: {point['description']}")

            # 保存结果
            with open("example_outline.json", "w", encoding="utf-8") as f:
                json.dump(response.result, f, ensure_ascii=False, indent=2)

            print("\n✅ 故事大纲生成完成，已保存到 example_outline.json")
            return outline
        else:
            print(f"❌ 故事大纲生成失败: {response.error}")
            return None

    except Exception as e:
        print(f"❌ 故事大纲生成失败: {e}")
        return None


async def example_write_chapter():
    """示例：写作章节"""
    print("\n" + "=" * 50)
    print("示例4：写作章节")
    print("=" * 50)

    registry = get_tool_registry()

    try:
        # 章节信息
        chapter_info = {
            "number": 1,
            "title": "初入江湖",
            "summary": "主角李逍遥离开余杭镇，开始修仙之路",
            "key_events": ["离别家乡", "遇到仙人", "获得传承"],
            "character_focus": ["李逍遥"]
        }

        # 故事背景
        story_context = {
            "world_setting": {
                "name": "修仙大陆",
                "magic_system": "仙道体系",
                "power_levels": ["炼气", "筑基", "金丹", "元婴"]
            },
            "characters": [
                {
                    "name": "李逍遥",
                    "character_type": "主角",
                    "personality": {"core_traits": ["勇敢", "善良"]}
                }
            ]
        }

        # 调用章节写作工具
        call = ToolCall(
            id="chapter_example",
            name="chapter_writer",
            parameters={
                "chapter_info": chapter_info,
                "story_context": story_context,
                "writing_style": "traditional",
                "target_word_count": 2000
            }
        )

        response = await registry.execute_tool(call)

        if response.success:
            chapter = response.result["chapter"]
            print(f"章节标题: {chapter['title']}")
            print(f"实际字数: {chapter['total_word_count']}")
            print(f"场景数量: {len(chapter['scenes'])}")
            print(f"对话占比: {chapter['dialogue_ratio']:.1%}")
            print(f"描述占比: {chapter['description_ratio']:.1%}")

            # 显示部分内容
            if chapter['scenes']:
                first_scene = chapter['scenes'][0]
                content_preview = first_scene['content'][:200] + "..."
                print(f"\n内容预览:\n{content_preview}")

            # 保存结果
            with open("example_chapter.json", "w", encoding="utf-8") as f:
                json.dump(response.result, f, ensure_ascii=False, indent=2)

            # 保存纯文本
            with open("example_chapter.txt", "w", encoding="utf-8") as f:
                f.write(f"{chapter['title']}\n")
                f.write("=" * 30 + "\n\n")
                for scene in chapter['scenes']:
                    f.write(scene['content'])
                    f.write("\n\n")

            print("\n✅ 章节写作完成，已保存到 example_chapter.txt")
            return chapter
        else:
            print(f"❌ 章节写作失败: {response.error}")
            return None

    except Exception as e:
        print(f"❌ 章节写作失败: {e}")
        return None


async def example_generate_names():
    """示例：生成名称"""
    print("\n" + "=" * 50)
    print("示例5：生成各种名称")
    print("=" * 50)

    registry = get_tool_registry()

    name_types = [
        ("character", "角色名称", {"gender": "male", "count": 3}),
        ("place", "地点名称", {"place_type": "city", "count": 3}),
        ("technique", "功法名称", {"technique_type": "martial_art", "count": 3}),
        ("artifact", "法宝名称", {"artifact_type": "weapon", "count": 3})
    ]

    for name_type, description, extra_params in name_types:
        try:
            call = ToolCall(
                id=f"name_{name_type}",
                name="name_generator",
                parameters={
                    "name_type": name_type,
                    "cultural_style": "中式古典",
                    **extra_params
                }
            )

            response = await registry.execute_tool(call)

            if response.success:
                names = response.result["names"]
                print(f"\n{description}:")
                for name_info in names:
                    print(f"  - {name_info['name']}: {name_info['meaning']}")
            else:
                print(f"❌ {description}生成失败: {response.error}")

        except Exception as e:
            print(f"❌ {description}生成失败: {e}")

    print("\n✅ 名称生成完成")


async def example_consistency_check():
    """示例：一致性检查"""
    print("\n" + "=" * 50)
    print("示例6：一致性检查")
    print("=" * 50)

    registry = get_tool_registry()

    try:
        # 准备测试数据
        story_data = {
            "characters": [
                {
                    "name": "李逍遥",
                    "character_type": "主角",
                    "abilities": {"power_level": "炼气期"},
                    "personality": {"core_traits": ["勇敢"]}
                }
            ],
            "world_setting": {
                "magic_system": {
                    "power_levels": ["炼气期", "筑基期", "金丹期"]
                }
            },
            "story_outline": {
                "title": "测试小说",
                "genre": "玄幻"
            }
        }

        # 调用一致性检查工具
        call = ToolCall(
            id="consistency_example",
            name="consistency_checker",
            parameters={
                "check_type": "full",
                "story_data": story_data
            }
        )

        response = await registry.execute_tool(call)

        if response.success:
            report = response.result["consistency_report"]
            print(f"总体评分: {report['overall_score']:.1f}/100")
            print(f"问题总数: {report['issue_count']}")

            if report['issues']:
                print("\n发现的问题:")
                for issue in report['issues'][:3]:  # 显示前3个问题
                    print(f"  - [{issue['severity'].upper()}] {issue['description']}")
                    if issue['suggestions']:
                        print(f"    建议: {issue['suggestions'][0]}")

            if report['recommendations']:
                print("\n总体建议:")
                for rec in report['recommendations'][:3]:
                    print(f"  - {rec}")

            print("\n✅ 一致性检查完成")
        else:
            print(f"❌ 一致性检查失败: {response.error}")

    except Exception as e:
        print(f"❌ 一致性检查失败: {e}")


async def example_complete_novel():
    """示例：生成完整小说"""
    print("\n" + "=" * 50)
    print("示例7：生成完整小说（简化版）")
    print("=" * 50)

    generator = NovelGenerator()

    try:
        print("开始生成完整小说，这可能需要几分钟...")

        novel = await generator.generate_novel_complete(
            title="仙路征途",
            genre="玄幻",
            chapter_count=3,  # 为演示减少章节数
            theme="修仙",
            auto_save=True
        )

        print(f"\n✅ 小说生成完成！")
        print(f"标题: {novel['title']}")
        print(f"类型: {novel['genre']}")
        print(f"主题: {novel['theme']}")
        print(f"总字数: {novel['total_word_count']}")
        print(f"章节数: {len(novel['chapters'])}")
        print(f"角色数: {len(novel['characters'])}")

        print("\n角色列表:")
        for char in novel['characters']:
            print(f"  - {char['name']} ({char['character_type']})")

        print("\n章节列表:")
        for chapter in novel['chapters']:
            print(f"  - {chapter['title']} ({chapter['total_word_count']}字)")

        print("\n小说文件已保存到 data/generated/ 目录")

    except Exception as e:
        print(f"❌ 完整小说生成失败: {e}")


async def main():
    """主函数 - 运行所有示例"""
    print("Fantasy Novel MCP 使用示例")
    print("=" * 50)

    # 检查配置
    settings = get_settings()
    if settings.llm.api_key == "your-api-key":
        print("⚠️  警告: 请先在.env文件中配置您的LLM API密钥")
        print("复制.env.example为.env并修改相关配置")
        return

    print(f"当前LLM配置: {settings.llm.model_name}")
    print(f"API地址: {settings.llm.api_base}")

    # 运行示例（按顺序）
    examples = [
        ("生成世界观", example_generate_world),
        ("生成角色", example_generate_characters),
        ("生成故事大纲", example_generate_story_outline),
        ("写作章节", example_write_chapter),
        ("生成名称", example_generate_names),
        ("一致性检查", example_consistency_check),
        ("生成完整小说", example_complete_novel)
    ]

    for name, func in examples:
        try:
            print(f"\n🚀 开始执行: {name}")
            await func()
            print(f"✅ {name} 完成")
        except Exception as e:
            print(f"❌ {name} 失败: {e}")

        # 短暂延迟
        await asyncio.sleep(1)

    print("\n" + "=" * 50)
    print("🎉 所有示例执行完成！")
    print("生成的文件:")
    example_files = [
        "example_world.json",
        "example_characters.json",
        "example_outline.json",
        "example_chapter.json",
        "example_chapter.txt"
    ]

    for filename in example_files:
        if Path(filename).exists():
            print(f"  - {filename}")


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())



