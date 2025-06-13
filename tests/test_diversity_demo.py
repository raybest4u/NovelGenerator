# test_diversity_demo.py
"""
多样性增强功能测试演示
展示如何生成差异化的小说内容
"""

import asyncio
import json
from datetime import datetime
from modules.generation.diversity_enhancer import DiversityEnhancer, DiversityEnhancerTool
from modules.generation.enhanced_story_generator import EnhancedStoryGeneratorTool


async def demo_diversity_enhancement():
    """演示多样性增强功能"""

    print("=" * 60)
    print("多样性增强功能演示")
    print("=" * 60)

    # 创建工具实例
    diversity_tool = DiversityEnhancerTool()
    enhanced_generator = EnhancedStoryGeneratorTool()

    # 1. 生成多个不同的故事变体
    print("\n1. 生成多个不同的故事变体")
    print("-" * 40)

    variants = []
    for i in range(5):
        print(f"\n生成第 {i + 1} 个变体...")

        # 生成变体
        variant_result = await diversity_tool.execute({
            "action": "generate_variant",
            "theme": "修仙",
            "avoid_elements": {}  # 第一次不避免任何元素
        })

        variant = variant_result["variant"]
        variants.append(variant)

        print(f"  标题: {variant['title']}")
        print(f"  结构: {variant['story_structure']}")
        print(f"  角色: {variant['character_archetype']}")
        print(f"  世界: {variant['world_flavor']}")
        print(f"  冲突: {variant['conflict_type']}")
        print(f"  基调: {variant['tone']}")
        print(f"  独特元素: {', '.join(variant['unique_elements'][:2])}")
        print(f"  描述: {variant['description'][:100]}...")

    # 2. 分析多样性
    print(f"\n\n2. 分析生成内容的多样性")
    print("-" * 40)

    diversity_analysis = await diversity_tool.execute({
        "action": "analyze_diversity",
        "recent_count": 5
    })

    analysis = diversity_analysis["diversity_analysis"]
    print(f"多样性得分: {analysis['diversity_score']:.2f}")
    print(f"最近生成数量: {analysis['recent_count']}")

    print("\n频率分析:")
    for category, freq in analysis['frequency_analysis'].items():
        print(f"  {category}: {freq}")

    if analysis['recommendations']:
        print("\n改进建议:")
        for rec in analysis['recommendations']:
            print(f"  • {rec}")

    # 3. 使用增强生成器创建完整故事
    print(f"\n\n3. 使用增强生成器创建完整故事")
    print("-" * 40)

    # 生成两个高度差异化的故事
    for story_num in range(2):
        print(f"\n生成故事 {story_num + 1}:")

        story_result = await enhanced_generator.execute({
            "action": "full_story",
            "base_theme": "修仙",
            "randomization_level": 0.8 + story_num * 0.1,  # 递增随机化程度
            "avoid_recent": True,
            "chapter_count": 15
        })

        story_package = story_result["story_package"]
        config = story_package["config"]
        characters = story_package["characters"]
        plot_outline = story_package["plot_outline"]

        print(f"  故事配置:")
        print(f"    主题: {config['base_theme']}")
        print(f"    变体ID: {config['variant']['variant_id']}")
        print(f"    故事标题: {config['variant']['title']}")
        print(f"    故事结构: {config['variant']['story_structure']}")
        print(f"    世界风味: {config['variant']['world_flavor']}")
        print(f"    叙述基调: {config['variant']['tone']}")
        print(f"    随机化程度: {config['randomization_level']}")
        print(f"    创新因子: {', '.join(config['innovation_factors'][:3])}")

        print(f"  主要角色:")
        for char in characters:
            print(f"    {char['name']} ({char['role']}) - {char['archetype']}")

        print(f"  情节特色:")
        print(f"    叙述技法: {plot_outline['narrative_technique']}")
        print(f"    情节转折: {len(plot_outline['plot_twists'])} 个")

    # 4. 演示章节生成的差异
    print(f"\n\n4. 演示章节生成的差异")
    print("-" * 40)

    # 使用第一个故事的配置生成开篇章节
    first_story = story_result["story_package"]

    chapter_result = await enhanced_generator.execute({
        "action": "chapter",
        "config": first_story["config"],
        "characters": first_story["characters"],
        "plot_outline": first_story["plot_outline"],
        "chapter_info": {
            "number": 1,
            "title": "奇遇初始",
            "plot_summary": "主角的平凡生活被突如其来的奇遇打破"
        }
    })

    chapter = chapter_result["chapter"]
    print(f"章节标题: {chapter['title']}")
    print(f"字数: {chapter['word_count']}")
    print(f"使用的创新元素: {', '.join(chapter['innovations_used'])}")
    print(f"叙述技法: {chapter['narrative_technique']}")
    print(f"技法应用: {chapter['technique_application']}")
    print(f"\n章节内容预览:")
    print(f"{chapter['content'][:300]}...")

    # 5. 对比传统生成方式
    print(f"\n\n5. 传统 vs 增强生成对比")
    print("-" * 40)

    print("传统生成特征:")
    print("  • 角色名称重复（李逍遥、赵灵儿等）")
    print("  • 情节套路化（废柴逆袭、打脸升级）")
    print("  • 世界观单一（传统修仙大陆）")
    print("  • 结构固化（三段式起承转合）")

    print("\n增强生成特征:")
    print("  • 角色设定独特（时间操控者、梦境编织师）")
    print("  • 情节创新性强（身份认同、概念冲突）")
    print("  • 世界观多样（蒸汽朋克、现代都市异能）")
    print("  • 结构灵活（时间循环、多线并行）")

    # 6. 获取避免约束建议
    print(f"\n\n6. 获取下次生成的避免约束")
    print("-" * 40)

    constraints_result = await diversity_tool.execute({
        "action": "get_constraints",
        "recent_count": 3
    })

    constraints = constraints_result["avoidance_constraints"]
    print("建议在下次生成时避免使用:")
    for constraint_type, items in constraints.items():
        if items:
            print(f"  {constraint_type}: {', '.join(items)}")

    print(f"\n\n演示完成！")
    print("=" * 60)


async def compare_generation_methods():
    """对比传统生成和增强生成的差异"""

    print("\n" + "=" * 60)
    print("传统生成 vs 增强生成对比测试")
    print("=" * 60)

    enhanced_generator = EnhancedStoryGeneratorTool()

    # 生成3个不同随机化程度的故事
    randomization_levels = [0.3, 0.6, 0.9]
    level_names = ["保守模式", "平衡模式", "激进模式"]

    for i, (level, name) in enumerate(zip(randomization_levels, level_names)):
        print(f"\n{i + 1}. {name} (随机化程度: {level})")
        print("-" * 40)

        config_result = await enhanced_generator.execute({
            "action": "config",
            "base_theme": "修仙",
            "randomization_level": level,
            "avoid_recent": True
        })

        config = config_result["config"]
        variant = config["variant"]

        print(f"故事标题: {variant['title']}")
        print(f"故事结构: {variant['story_structure']}")
        print(f"角色原型: {variant['character_archetype']}")
        print(f"世界风味: {variant['world_flavor']}")
        print(f"主要冲突: {variant['conflict_type']}")
        print(f"叙述基调: {variant['tone']}")
        print(f"创新因子数量: {len(config['innovation_factors'])}")
        print(f"独特元素: {', '.join(variant['unique_elements'])}")
        print(f"故事描述: {variant['description'][:150]}...")

        # 生成主角
        char_result = await enhanced_generator.execute({
            "action": "character",
            "config": config
        })

        character = char_result["character"]
        print(f"\n主角信息:")
        print(f"  姓名: {character['name']}")
        print(f"  原型: {character['archetype']}")
        print(f"  创新元素: {', '.join(character['innovation_elements'][:2])}")


async def main():
    """主函数"""
    await demo_diversity_enhancement()
    await compare_generation_methods()


if __name__ == "__main__":
    # 运行演示
    asyncio.run(main())
