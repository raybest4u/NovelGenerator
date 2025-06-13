# 增强版 save_story 方法
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from loguru import logger

from modules.models import (
    Novel, Chapter, Character, StoryOutline, WorldSetting,
    NovelDAO, CharacterDAO, get_db_session
)


class EnhancedStoryDAO:
    """增强版故事数据访问对象"""

    def __init__(self, db_session=None):
        self.db = db_session or get_db_session()
        self.novel_dao = NovelDAO(self.db)
        self.character_dao = CharacterDAO(self.db)

    def save_complete_story(self, story_package: Dict[str, Any]) -> Dict[str, Any]:
        """保存完整故事包到数据库"""
        try:
            # 开始事务
            self.db.begin()

            # 1. 解析和保存小说基本信息
            novel = self._save_novel_info(story_package)
            logger.info(f"✅ 小说基本信息已保存，ID: {novel.id}")

            # 2. 保存故事大纲
            outline = self._save_story_outline(novel.id, story_package)
            if outline:
                logger.info(f"✅ 故事大纲已保存，ID: {outline.id}")

            # 3. 保存角色信息
            characters = self._save_characters(novel.id, story_package)
            logger.info(f"✅ 已保存 {len(characters)} 个角色")

            # 4. 保存章节内容
            chapters = self._save_chapters(novel.id, story_package)
            logger.info(f"✅ 已保存 {len(chapters)} 个章节")

            # 5. 保存世界设定（如果有）
            world_setting = self._save_world_setting(novel.id, story_package)
            if world_setting:
                logger.info(f"✅ 世界设定已保存，ID: {world_setting.id}")

            # 6. 更新小说统计信息
            self._update_novel_statistics(novel, chapters)

            # 提交事务
            self.db.commit()

            return {
                "success": True,
                "novel_id": novel.id,
                "title": novel.title,
                "chapters_saved": len(chapters),
                "characters_saved": len(characters),
                "total_word_count": novel.actual_word_count,
                "saved_at": datetime.now().isoformat()
            }

        except Exception as e:
            # 回滚事务
            self.db.rollback()
            logger.error(f"保存故事失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "novel_id": None
            }

    def _save_novel_info(self, story_package: Dict[str, Any]) -> Novel:
        """保存小说基本信息"""
        try:
            # 从故事包中提取基本信息
            title = story_package.get('title', '未命名小说')
            genre = story_package.get('genre', '未知类型')
            theme = story_package.get('theme', '')
            description = self._generate_description(story_package)

            # 获取生成配置
            config = story_package.get('config', {})
            generation_info = story_package.get('generation_info', {})

            # 计算目标字数
            chapters = story_package.get('chapters', [])
            target_word_count = self._calculate_target_word_count(chapters, config)

            novel_data = {
                "title": title,
                "genre": genre,
                "theme": theme,
                "description": description,
                "target_word_count": target_word_count,
                "chapter_count": len(chapters),
                "status": "draft",
                "generation_config": {
                    **config,
                    "generation_info": generation_info,
                    "saved_at": datetime.now().isoformat()
                }
            }

            return self.novel_dao.create_novel(novel_data)

        except Exception as e:
            logger.error(f"保存小说基本信息失败: {e}")
            raise

    def _save_story_outline(self, novel_id: int, story_package: Dict[str, Any]) -> Optional[
        StoryOutline]:
        """保存故事大纲"""
        try:
            plot_outline = story_package.get('plot_outline', {})
            if not plot_outline:
                return None

            # 解析大纲信息
            premise = self._extract_premise(plot_outline)
            structure = plot_outline.get('story_structure', '传统三段式')
            central_conflict = self._extract_central_conflict(story_package)
            themes = self._extract_themes(story_package)

            outline = StoryOutline(
                novel_id=novel_id,
                premise=premise,
                structure=structure,
                tone=self._extract_tone(story_package),
                central_conflict=central_conflict,
                stakes=self._extract_stakes(plot_outline),
                themes=themes,
                plot_points=self._extract_plot_points(plot_outline),
                beginning=plot_outline.get('beginning', ''),
                middle=plot_outline.get('middle', ''),
                climax=plot_outline.get('climax', ''),
                resolution=plot_outline.get('resolution', ''),
                subplots=plot_outline.get('subplots', [])
            )

            self.db.add(outline)
            self.db.flush()  # 获取ID但不提交
            return outline

        except Exception as e:
            logger.error(f"保存故事大纲失败: {e}")
            return None

    def _save_characters(self, novel_id: int, story_package: Dict[str, Any]) -> List[Character]:
        """保存角色信息"""
        characters_data = story_package.get('characters', [])
        saved_characters = []

        for i, char_data in enumerate(characters_data):
            try:
                character = self._create_character_from_data(novel_id, char_data, i)
                self.db.add(character)
                self.db.flush()  # 获取ID但不提交
                saved_characters.append(character)

            except Exception as e:
                logger.error(f"保存角色 {char_data.get('name', f'角色{i}')} 失败: {e}")
                continue

        return saved_characters

    def _create_character_from_data(self, novel_id: int, char_data: Dict[str, Any],
                                    index: int) -> Character:
        """从角色数据创建角色对象"""
        name = char_data.get('name', f'角色{index + 1}')

        # 确定角色类型和重要性
        role = char_data.get('role', 'supporting')
        character_type, importance = self._determine_character_type_and_importance(role)

        # 解析角色各个方面的信息
        appearance = self._parse_character_appearance(char_data)
        personality = self._parse_character_personality(char_data)
        background = self._parse_character_background(char_data)
        abilities = self._parse_character_abilities(char_data)

        return Character(
            novel_id=novel_id,
            name=name,
            nickname=char_data.get('nickname', ''),
            character_type=character_type,
            importance=importance,
            appearance=appearance,
            personality=personality,
            background=background,
            abilities=abilities,
            story_role=char_data.get('description', ''),
            character_arc=char_data.get('character_arc', {}),
            development_plan=char_data.get('development_plan', {}),
            creation_notes=char_data.get('creation_notes', ''),
            inspiration=char_data.get('inspiration', '')
        )

    def _save_chapters(self, novel_id: int, story_package: Dict[str, Any]) -> List[Chapter]:
        """保存章节内容"""
        chapters_data = story_package.get('chapters', [])
        saved_chapters = []

        for chapter_data in chapters_data:
            try:
                chapter = self._create_chapter_from_data(novel_id, chapter_data)
                self.db.add(chapter)
                self.db.flush()  # 获取ID但不提交
                saved_chapters.append(chapter)

            except Exception as e:
                chapter_title = chapter_data.get('title', '未知章节')
                logger.error(f"保存章节 {chapter_title} 失败: {e}")
                continue

        return saved_chapters

    def _create_chapter_from_data(self, novel_id: int, chapter_data: Dict[str, Any]) -> Chapter:
        """从章节数据创建章节对象"""
        number = chapter_data.get('number', chapter_data.get('chapter_number', 1))
        title = chapter_data.get('title', f'第{number}章')
        content = chapter_data.get('content', '')
        word_count = chapter_data.get('word_count', len(content))

        return Chapter(
            novel_id=novel_id,
            number=number,
            title=title,
            summary=chapter_data.get('summary', ''),
            content=content,
            word_count=word_count,
            key_events=chapter_data.get('key_events', []),
            character_focus=chapter_data.get('character_focus', []),
            plot_advancement=chapter_data.get('plot_advancement', ''),
            emotional_arc=chapter_data.get('emotional_arc', ''),
            dialogue_ratio=chapter_data.get('dialogue_ratio', 0.0),
            description_ratio=chapter_data.get('description_ratio', 0.0),
            action_ratio=chapter_data.get('action_ratio', 0.0),
            status='draft',
            generation_config=chapter_data.get('config_used', {})
        )

    def _save_world_setting(self, novel_id: int, story_package: Dict[str, Any]) -> Optional[
        WorldSetting]:
        """保存世界设定"""
        try:
            config = story_package.get('config', {})
            variant = config.get('variant', {})

            if not variant:
                return None

            world_flavor = variant.get('world_flavor', '')
            if not world_flavor:
                return None

            world_setting = WorldSetting(
                novel_id=novel_id,
                name=f"{world_flavor}世界",
                world_type=self._determine_world_type(world_flavor),
                time_period=self._determine_time_period(world_flavor),
                technology_level=self._determine_tech_level(world_flavor),
                magic_system=self._extract_magic_system(variant),
                geography=self._extract_geography(variant),
                politics=self._extract_politics(variant),
                economy=self._extract_economy(variant),
                culture=self._extract_culture(variant),
                history=self._extract_history(variant),
                unique_elements=variant.get('unique_elements', []),
                mysteries=self._extract_mysteries(variant),
                conflicts=self._extract_world_conflicts(variant)
            )

            self.db.add(world_setting)
            self.db.flush()
            return world_setting

        except Exception as e:
            logger.error(f"保存世界设定失败: {e}")
            return None

    def _update_novel_statistics(self, novel: Novel, chapters: List[Chapter]):
        """更新小说统计信息"""
        try:
            # 计算实际字数
            actual_word_count = sum(chapter.word_count for chapter in chapters)

            # 更新小说信息
            novel.actual_word_count = actual_word_count
            novel.chapter_count = len(chapters)
            novel.updated_at = datetime.now()

            # 如果有章节内容，更新状态
            if chapters:
                novel.status = 'generating' if actual_word_count < novel.target_word_count else 'completed'

        except Exception as e:
            logger.error(f"更新小说统计信息失败: {e}")

    # 辅助方法
    def _generate_description(self, story_package: Dict[str, Any]) -> str:
        """生成小说描述"""
        try:
            theme = story_package.get('theme', '')
            genre = story_package.get('genre', '')
            config = story_package.get('config', {})
            variant = config.get('variant', {})

            description_parts = []

            if theme:
                description_parts.append(f"这是一部{theme}题材的小说")

            if variant.get('world_flavor'):
                description_parts.append(f"背景设定在{variant['world_flavor']}世界")

            if variant.get('character_archetype'):
                description_parts.append(f"主角是{variant['character_archetype']}类型")

            if variant.get('story_structure'):
                description_parts.append(f"采用{variant['story_structure']}的叙事结构")

            return "，".join(description_parts) + "。"

        except Exception:
            return "AI生成的小说作品。"

    def _calculate_target_word_count(self, chapters: List[Dict], config: Dict[str, Any]) -> int:
        """计算目标字数"""
        if chapters:
            # 基于现有章节计算
            avg_word_count = sum(ch.get('word_count', 0) for ch in chapters) / len(chapters)
            return int(avg_word_count * len(chapters) * 1.2)  # 预留20%增长
        else:
            # 基于配置计算
            chapter_count = config.get('chapter_count', 20)
            word_per_chapter = config.get('word_count_per_chapter', 2000)
            return chapter_count * word_per_chapter

    def _determine_character_type_and_importance(self, role: str) -> tuple:
        """确定角色类型和重要性"""
        role_mapping = {
            'protagonist': ('主角', 10),
            'antagonist': ('反派', 9),
            'deuteragonist': ('重要配角', 8),
            'supporting': ('配角', 6),
            'minor': ('次要角色', 4),
            'background': ('背景角色', 2)
        }
        return role_mapping.get(role, ('配角', 5))

    def _parse_character_appearance(self, char_data: Dict[str, Any]) -> Dict[str, Any]:
        """解析角色外貌信息"""
        appearance_text = char_data.get('appearance', '')
        if isinstance(appearance_text, str):
            return {
                "description": appearance_text,
                "height": "",
                "build": "",
                "hair": "",
                "eyes": "",
                "distinguishing_features": ""
            }
        return appearance_text if isinstance(appearance_text, dict) else {}

    def _parse_character_personality(self, char_data: Dict[str, Any]) -> Dict[str, Any]:
        """解析角色性格信息"""
        personality_text = char_data.get('personality', '')
        if isinstance(personality_text, str):
            return {
                "description": personality_text,
                "traits": [],
                "strengths": [],
                "weaknesses": [],
                "fears": [],
                "motivations": []
            }
        return personality_text if isinstance(personality_text, dict) else {}

    def _parse_character_background(self, char_data: Dict[str, Any]) -> Dict[str, Any]:
        """解析角色背景信息"""
        background_text = char_data.get('background', '')
        if isinstance(background_text, str):
            return {
                "description": background_text,
                "origin": "",
                "family": "",
                "education": "",
                "career": "",
                "significant_events": []
            }
        return background_text if isinstance(background_text, dict) else {}

    def _parse_character_abilities(self, char_data: Dict[str, Any]) -> Dict[str, Any]:
        """解析角色能力信息"""
        abilities_text = char_data.get('abilities', char_data.get('skills', ''))
        if isinstance(abilities_text, str):
            return {
                "description": abilities_text,
                "combat_skills": [],
                "special_abilities": [],
                "magic_level": "",
                "strengths": [],
                "limitations": []
            }
        return abilities_text if isinstance(abilities_text, dict) else {}

    def _extract_premise(self, plot_outline: Dict[str, Any]) -> str:
        """提取故事前提"""
        return plot_outline.get('premise', plot_outline.get('detailed_outline', '')[:200])

    def _extract_central_conflict(self, story_package: Dict[str, Any]) -> str:
        """提取中心冲突"""
        config = story_package.get('config', {})
        variant = config.get('variant', {})
        return variant.get('conflict_type', '未知冲突')

    def _extract_themes(self, story_package: Dict[str, Any]) -> List[str]:
        """提取主题"""
        themes = []
        theme = story_package.get('theme', '')
        if theme:
            themes.append(theme)

        config = story_package.get('config', {})
        base_theme = config.get('base_theme', '')
        if base_theme and base_theme not in themes:
            themes.append(base_theme)

        return themes

    def _extract_tone(self, story_package: Dict[str, Any]) -> str:
        """提取故事基调"""
        config = story_package.get('config', {})
        variant = config.get('variant', {})
        return variant.get('tone', '未知基调')

    def _extract_stakes(self, plot_outline: Dict[str, Any]) -> str:
        """提取故事赌注"""
        return plot_outline.get('stakes', '未知赌注')

    def _extract_plot_points(self, plot_outline: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取情节点"""
        return plot_outline.get('plot_points', [])

    def _determine_world_type(self, world_flavor: str) -> str:
        """确定世界类型"""
        type_mapping = {
            '古典仙侠': '修仙大陆',
            '现代都市': '现代地球',
            '蒸汽朋克': '蒸汽文明',
            '末世废土': '后末日世界',
            '奇幻大陆': '奇幻世界'
        }
        return type_mapping.get(world_flavor, '未知世界')

    def _determine_time_period(self, world_flavor: str) -> str:
        """确定时代背景"""
        period_mapping = {
            '古典仙侠': '古代/神话时代',
            '现代都市': '现代',
            '蒸汽朋克': '维多利亚时代风格',
            '末世废土': '后文明时代',
            '奇幻大陆': '中世纪风格'
        }
        return period_mapping.get(world_flavor, '未知时代')

    def _determine_tech_level(self, world_flavor: str) -> str:
        """确定科技水平"""
        tech_mapping = {
            '古典仙侠': '古代+修仙术法',
            '现代都市': '现代科技',
            '蒸汽朋克': '蒸汽机械科技',
            '末世废土': '退化科技',
            '奇幻大陆': '魔法替代科技'
        }
        return tech_mapping.get(world_flavor, '未知科技')

    def _extract_magic_system(self, variant: Dict[str, Any]) -> Dict[str, Any]:
        """提取魔法/修炼体系"""
        return {
            "type": variant.get('world_flavor', ''),
            "rules": [],
            "levels": [],
            "restrictions": []
        }

    def _extract_geography(self, variant: Dict[str, Any]) -> Dict[str, Any]:
        """提取地理信息"""
        return {
            "world_flavor": variant.get('world_flavor', ''),
            "regions": [],
            "landmarks": [],
            "climate": ""
        }

    def _extract_politics(self, variant: Dict[str, Any]) -> Dict[str, Any]:
        """提取政治体系"""
        return {
            "government_type": "",
            "power_structure": [],
            "major_factions": []
        }

    def _extract_economy(self, variant: Dict[str, Any]) -> Dict[str, Any]:
        """提取经济体系"""
        return {
            "currency": "",
            "trade": [],
            "resources": []
        }

    def _extract_culture(self, variant: Dict[str, Any]) -> Dict[str, Any]:
        """提取文化设定"""
        return {
            "traditions": [],
            "beliefs": [],
            "social_structure": []
        }

    def _extract_history(self, variant: Dict[str, Any]) -> Dict[str, Any]:
        """提取历史设定"""
        return {
            "major_events": [],
            "timeline": [],
            "legends": []
        }

    def _extract_mysteries(self, variant: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取世界谜团"""
        return []

    def _extract_world_conflicts(self, variant: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取世界冲突"""
        conflict_type = variant.get('conflict_type', '')
        if conflict_type:
            return [{"type": conflict_type, "description": ""}]
        return []


async def save_story_enhanced(story_package: Dict[str, Any]) -> Dict[str, Any]:
    """增强版保存故事方法"""
    try:
        # 数据验证
        if not story_package:
            raise ValueError("故事包不能为空")

        if not story_package.get('title'):
            logger.warning("故事包缺少标题，使用默认标题")
            story_package['title'] = f"未命名小说_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 保存到数据库
        dao = EnhancedStoryDAO()
        result = dao.save_complete_story(story_package)

        if result['success']:
            logger.info(f"✅ 故事保存成功: {result['title']} (ID: {result['novel_id']})")

            # 同时保存JSON备份文件
            await _save_json_backup(story_package, result['novel_id'])

            return result
        else:
            logger.error(f"❌ 故事保存失败: {result['error']}")
            return result

    except Exception as e:
        logger.error(f"保存故事时发生异常: {e}")
        return {
            "success": False,
            "error": str(e),
            "novel_id": None
        }


async def _save_json_backup(story_package: Dict[str, Any], novel_id: int):
    """保存JSON备份文件"""
    try:
        from pathlib import Path

        # 创建备份目录
        backup_dir = Path("generated_novels/backups")
        backup_dir.mkdir(parents=True, exist_ok=True)

        # 生成备份文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"novel_{novel_id}_{timestamp}.json"
        filepath = backup_dir / filename

        # 保存备份文件
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(story_package, f, ensure_ascii=False, indent=2)

        logger.info(f"📁 JSON备份已保存: {filepath}")

    except Exception as e:
        logger.warning(f"保存JSON备份失败: {e}")
