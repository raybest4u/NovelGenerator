
# scripts/migrate.py
# !/usr/bin/env python3
"""
数据库迁移脚本
"""

import sys
import argparse
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

from data.models import (
    init_database, drop_database, create_database_engine,
    NovelDAO, CharacterDAO
)
from sqlalchemy import text
from loguru import logger


def create_tables():
    """创建所有表"""
    try:
        init_database()
        logger.info("✅ 数据库表创建成功")
    except Exception as e:
        logger.error(f"❌ 数据库表创建失败: {e}")
        sys.exit(1)


def drop_tables():
    """删除所有表"""
    try:
        drop_database()
        logger.info("✅ 数据库表删除成功")
    except Exception as e:
        logger.error(f"❌ 数据库表删除失败: {e}")
        sys.exit(1)


def reset_database():
    """重置数据库"""
    logger.info("重置数据库...")
    drop_tables()
    create_tables()
    logger.info("✅ 数据库重置完成")


def seed_data():
    """填充示例数据"""
    try:
        logger.info("填充示例数据...")

        novel_dao = NovelDAO()

        # 创建示例小说
        sample_novel = novel_dao.create_novel({
            "title": "仙路征途",
            "genre": "玄幻",
            "theme": "修仙",
            "description": "一个平凡少年的修仙之路",
            "target_word_count": 200000,
            "generation_config": {
                "writing_style": "traditional",
                "chapter_count": 50,
                "auto_generate": True
            }
        })

        logger.info(f"创建示例小说: {sample_novel.title} (ID: {sample_novel.id})")

        # 创建示例角色
        char_dao = CharacterDAO()

        sample_characters = [
            {
                "novel_id": sample_novel.id,
                "name": "李逍遥",
                "character_type": "主角",
                "importance": 10,
                "appearance": {"gender": "男", "age": 18},
                "personality": {"core_traits": ["勇敢", "正义"]},
                "background": {"birthplace": "余杭镇"},
                "abilities": {"power_level": "炼气期"}
            },
            {
                "novel_id": sample_novel.id,
                "name": "赵灵儿",
                "character_type": "女主角",
                "importance": 9,
                "appearance": {"gender": "女", "age": 16},
                "personality": {"core_traits": ["善良", "温柔"]},
                "background": {"birthplace": "仙灵岛"},
                "abilities": {"power_level": "筑基期"}
            }
        ]

        for char_data in sample_characters:
            character = char_dao.create_character(char_data)
            logger.info(f"创建示例角色: {character.name}")

        logger.info("✅ 示例数据填充完成")

    except Exception as e:
        logger.error(f"❌ 示例数据填充失败: {e}")
        sys.exit(1)


def check_database():
    """检查数据库状态"""
    try:
        engine = create_database_engine()

        with engine.connect() as conn:
            # 检查表是否存在
            result = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table';"
            ))
            tables = [row[0] for row in result]

            logger.info(f"数据库表数量: {len(tables)}")
            for table in tables:
                logger.info(f"  - {table}")

            # 检查数据
            if 'novels' in tables:
                result = conn.execute(text("SELECT COUNT(*) FROM novels"))
                novel_count = result.scalar()
                logger.info(f"小说数量: {novel_count}")

            if 'characters' in tables:
                result = conn.execute(text("SELECT COUNT(*) FROM characters"))
                char_count = result.scalar()
                logger.info(f"角色数量: {char_count}")

        logger.info("✅ 数据库检查完成")

    except Exception as e:
        logger.error(f"❌ 数据库检查失败: {e}")
        sys.exit(1)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="数据库迁移工具")

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # 创建表
    subparsers.add_parser("create", help="创建数据库表")

    # 删除表
    subparsers.add_parser("drop", help="删除数据库表")

    # 重置数据库
    subparsers.add_parser("reset", help="重置数据库")

    # 填充示例数据
    subparsers.add_parser("seed", help="填充示例数据")

    # 检查数据库
    subparsers.add_parser("check", help="检查数据库状态")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "create":
        create_tables()
    elif args.command == "drop":
        drop_tables()
    elif args.command == "reset":
        reset_database()
    elif args.command == "seed":
        seed_data()
    elif args.command == "check":
        check_database()


if __name__ == "__main__":
    main()