# generation_config.py
"""
小说生成配置示例
展示如何自定义各种生成参数
"""

# 预设配置模板
GENERATION_PRESETS = {
    "快速测试": {
        "chapter_count": 3,
        "word_count_per_chapter": 1500,
        "randomization_level": 0.6,
        "themes": ["修仙", "都市"]
    },

    "标准小说": {
        "chapter_count": 15,
        "word_count_per_chapter": 2500,
        "randomization_level": 0.8,
        "themes": ["修仙", "玄幻", "都市异能", "科幻"]
    },

    "长篇小说": {
        "chapter_count": 30,
        "word_count_per_chapter": 3000,
        "randomization_level": 0.9,
        "themes": ["史诗玄幻", "修仙世界", "异界重生"]
    },

    "实验性": {
        "chapter_count": 8,
        "word_count_per_chapter": 2000,
        "randomization_level": 1.0,  # 最高随机化
        "themes": ["蒸汽朋克", "赛博朋克", "时空穿越", "维度战争"]
    }
}

# 主题扩展库
EXTENDED_THEMES = {
    "修仙类": ["修仙", "仙侠", "修真", "洪荒", "封神"],
    "玄幻类": ["玄幻", "异界", "魔法", "斗气", "魂师"],
    "都市类": ["都市异能", "现代修仙", "都市重生", "商战", "医生"],
    "科幻类": ["星际", "机甲", "末世", "进化", "虚拟现实"],
    "武侠类": ["武侠", "江湖", "侠客", "门派", "武林"],
    "历史类": ["穿越", "重生", "架空历史", "古代", "宫廷"],
    "奇幻类": ["西幻", "魔法", "精灵", "龙族", "异世界"],
    "悬疑类": ["推理", "悬疑", "恐怖", "灵异", "超自然"]
}

# 生成批次配置
BATCH_CONFIGS = {
    "多样性测试": {
        "themes": ["修仙", "都市异能", "科幻", "武侠", "玄幻"],
        "count_per_theme": 1,
        "chapter_count": 5,
        "word_count_per_chapter": 2000,
        "randomization_levels": [0.6, 0.7, 0.8, 0.9, 1.0]  # 每个主题使用不同随机度
    },

    "同主题变化": {
        "themes": ["修仙"],
        "count_per_theme": 5,
        "chapter_count": 10,
        "word_count_per_chapter": 2500,
        "randomization_levels": [0.5, 0.6, 0.7, 0.8, 0.9]
    },

    "快速原型": {
        "themes": ["修仙", "玄幻", "都市"],
        "count_per_theme": 2,
        "chapter_count": 3,
        "word_count_per_chapter": 1000,
        "randomization_levels": [0.8, 0.9]
    }
}


async def generate_with_preset(generator, preset_name: str):
    """使用预设配置生成小说"""
    if preset_name not in GENERATION_PRESETS:
        raise ValueError(f"未知预设: {preset_name}")

    config = GENERATION_PRESETS[preset_name]
    themes = config["themes"]

    print(f"📋 使用预设: {preset_name}")
    print(f"📝 将生成 {len(themes)} 个主题的小说")

    results = []
    for theme in themes:
        result = await generator.generate_novel_auto(
            theme=theme,
            chapter_count=config["chapter_count"],
            word_count_per_chapter=config["word_count_per_chapter"],
            randomization_level=config["randomization_level"],
            title=f"{theme}_{preset_name}"
        )
        results.append(result)

    return results


async def generate_themed_batch(generator, theme_category: str):
    """生成指定类别的主题批次"""
    if theme_category not in EXTENDED_THEMES:
        raise ValueError(f"未知主题类别: {theme_category}")

    themes = EXTENDED_THEMES[theme_category]

    print(f"🎭 生成 {theme_category} 主题批次")
    print(f"📚 包含主题: {', '.join(themes)}")

    results = await generator.generate_multiple_novels(
        themes=themes,
        count_per_theme=1,
        chapter_count=8,
        word_count_per_chapter=2000,
        randomization_level=0.8
    )

    return results


async def generate_batch_config(generator, config_name: str):
    """使用批次配置生成"""
    if config_name not in BATCH_CONFIGS:
        raise ValueError(f"未知批次配置: {config_name}")

    config = BATCH_CONFIGS[config_name]
    themes = config["themes"]
    randomization_levels = config.get("randomization_levels", [0.8])

    print(f"🚀 执行批次配置: {config_name}")

    all_results = []

    for i, theme in enumerate(themes):
        # 循环使用随机化级别
        random_level = randomization_levels[i % len(randomization_levels)]

        for j in range(config["count_per_theme"]):
            result = await generator.generate_novel_auto(
                theme=theme,
                chapter_count=config["chapter_count"],
                word_count_per_chapter=config["word_count_per_chapter"],
                randomization_level=random_level,
                title=f"{theme}_批次{j + 1}"
            )
            all_results.append({
                "theme": theme,
                "batch_index": j + 1,
                "randomization_level": random_level,
                "result": result
            })

    return all_results


# 使用示例
if __name__ == "__main__":
    import asyncio
    from main_novel_generator import AutoNovelGenerator


    async def example_usage():
        generator = AutoNovelGenerator()

        # 示例1: 使用预设配置
        print("=== 预设配置示例 ===")
        results = await generate_with_preset(generator, "快速测试")
        print(f"预设生成完成，共 {len(results)} 部小说")

        # 示例2: 主题类别批次
        print("\n=== 主题类别批次示例 ===")
        themed_results = await generate_themed_batch(generator, "修仙类")
        print(f"主题批次生成完成，共 {len(themed_results)} 部小说")

        # 示例3: 自定义批次配置
        print("\n=== 自定义批次配置示例 ===")
        batch_results = await generate_batch_config(generator, "多样性测试")
        print(f"批次配置生成完成，共 {len(batch_results)} 部小说")


    # 运行示例
    asyncio.run(example_usage())
