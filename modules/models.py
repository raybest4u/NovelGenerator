# data/models.py
"""
数据模型定义
用于数据库存储和数据持久化
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Dict, Any, List, Optional

Base = declarative_base()


class Novel(Base):
    """小说表"""
    __tablename__ = "novels"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    genre = Column(String(50), nullable=False)
    theme = Column(String(100))
    status = Column(String(20), default="draft")  # draft, generating, completed, published

    # 基本信息
    description = Column(Text)
    target_word_count = Column(Integer, default=100000)
    actual_word_count = Column(Integer, default=0)
    chapter_count = Column(Integer, default=0)

    # 时间信息
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime)

    # 生成参数
    generation_config = Column(JSON)  # 生成配置

    # 关联关系
    world_setting = relationship("WorldSetting", back_populates="novel", uselist=False)
    characters = relationship("Character", back_populates="novel")
    chapters = relationship("Chapter", back_populates="novel")
    outline = relationship("StoryOutline", back_populates="novel", uselist=False)


class WorldSetting(Base):
    """世界设定表"""
    __tablename__ = "world_settings"

    id = Column(Integer, primary_key=True, index=True)
    novel_id = Column(Integer, ForeignKey("novels.id"), nullable=False)

    # 基本信息
    name = Column(String(200), nullable=False)
    world_type = Column(String(50))  # 大陆、星球、异界等
    time_period = Column(String(100))
    technology_level = Column(String(100))

    # 详细设定
    magic_system = Column(JSON)  # 魔法/修炼体系
    geography = Column(JSON)  # 地理信息
    politics = Column(JSON)  # 政治体系
    economy = Column(JSON)  # 经济体系
    culture = Column(JSON)  # 文化设定
    history = Column(JSON)  # 历史时间线

    # 特殊元素
    unique_elements = Column(JSON)  # 独特元素
    mysteries = Column(JSON)  # 谜团和秘密
    conflicts = Column(JSON)  # 世界冲突

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关联关系
    novel = relationship("Novel", back_populates="world_setting")


class Character(Base):
    """角色表"""
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, index=True)
    novel_id = Column(Integer, ForeignKey("novels.id"), nullable=False)

    # 基本信息
    name = Column(String(100), nullable=False)
    nickname = Column(String(100))
    character_type = Column(String(50))  # 主角、配角、反派等
    importance = Column(Integer, default=5)  # 1-10

    # 外貌设定
    appearance = Column(JSON)

    # 性格设定
    personality = Column(JSON)

    # 背景设定
    background = Column(JSON)

    # 能力设定
    abilities = Column(JSON)

    # 故事相关
    story_role = Column(Text)  # 故事作用
    character_arc = Column(JSON)  # 角色弧线
    development_plan = Column(JSON)  # 发展计划

    # 元数据
    creation_notes = Column(Text)
    inspiration = Column(Text)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关联关系
    novel = relationship("Novel", back_populates="characters")
    relationships_as_char1 = relationship("CharacterRelationship",
                                          foreign_keys="CharacterRelationship.character1_id")
    relationships_as_char2 = relationship("CharacterRelationship",
                                          foreign_keys="CharacterRelationship.character2_id")


class CharacterRelationship(Base):
    """角色关系表"""
    __tablename__ = "character_relationships"

    id = Column(Integer, primary_key=True, index=True)
    character1_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    character2_id = Column(Integer, ForeignKey("characters.id"), nullable=False)

    # 关系信息
    relationship_type = Column(String(50))  # 家庭、爱情、友谊、敌对等
    intensity = Column(Integer, default=5)  # 关系强度 1-10
    status = Column(String(50))  # 当前状态

    # 详细信息
    history = Column(JSON)  # 关系历史
    current_dynamic = Column(Text)  # 当前动态
    future_potential = Column(Text)  # 未来可能性
    conflict_sources = Column(JSON)  # 冲突来源
    bonding_factors = Column(JSON)  # 联结因素

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关联关系
    character1 = relationship("Character", foreign_keys=[character1_id])
    character2 = relationship("Character", foreign_keys=[character2_id])


class StoryOutline(Base):
    """故事大纲表"""
    __tablename__ = "story_outlines"

    id = Column(Integer, primary_key=True, index=True)
    novel_id = Column(Integer, ForeignKey("novels.id"), nullable=False)

    # 基本信息
    premise = Column(Text)  # 故事前提
    structure = Column(String(50))  # 情节结构
    tone = Column(String(50))  # 故事基调

    # 核心元素
    central_conflict = Column(Text)
    stakes = Column(Text)  # 赌注
    themes = Column(JSON)  # 主题列表

    # 情节点
    plot_points = Column(JSON)

    # 故事弧线
    beginning = Column(Text)
    middle = Column(Text)
    climax = Column(Text)
    resolution = Column(Text)

    # 子情节
    subplots = Column(JSON)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关联关系
    novel = relationship("Novel", back_populates="outline")


class Chapter(Base):
    """章节表"""
    __tablename__ = "chapters"

    id = Column(Integer, primary_key=True, index=True)
    novel_id = Column(Integer, ForeignKey("novels.id"), nullable=False)

    # 基本信息
    number = Column(Integer, nullable=False)
    title = Column(String(200), nullable=False)
    summary = Column(Text)

    # 内容信息
    content = Column(Text)  # 章节正文
    word_count = Column(Integer, default=0)

    # 章节元数据
    key_events = Column(JSON)
    character_focus = Column(JSON)  # 重点角色
    plot_advancement = Column(Text)  # 情节推进
    emotional_arc = Column(String(100))  # 情感弧线

    # 写作质量指标
    dialogue_ratio = Column(Float, default=0.0)
    description_ratio = Column(Float, default=0.0)
    action_ratio = Column(Float, default=0.0)

    # 状态信息
    status = Column(String(20), default="draft")  # draft, writing, completed, reviewed
    generation_config = Column(JSON)  # 生成配置

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关联关系
    novel = relationship("Novel", back_populates="chapters")
    scenes = relationship("Scene", back_populates="chapter")


class Scene(Base):
    """场景表"""
    __tablename__ = "scenes"

    id = Column(Integer, primary_key=True, index=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=False)

    # 基本信息
    scene_number = Column(Integer, nullable=False)
    title = Column(String(200))
    content = Column(Text)
    word_count = Column(Integer, default=0)

    # 场景设定
    location = Column(String(200))
    characters = Column(JSON)  # 参与角色
    purpose = Column(String(100))  # 场景目的
    mood = Column(String(50))  # 氛围
    pacing = Column(String(50))  # 节奏

    # 场景类型
    scene_type = Column(String(50))  # action, dialogue, description, etc.

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关联关系
    chapter = relationship("Chapter", back_populates="scenes")


class Timeline(Base):
    """时间线表"""
    __tablename__ = "timelines"

    id = Column(Integer, primary_key=True, index=True)
    novel_id = Column(Integer, ForeignKey("novels.id"))

    # 基本信息
    name = Column(String(200), nullable=False)
    description = Column(Text)
    time_scale = Column(String(50))  # years, months, days, hours

    # 时间范围
    start_time = Column(String(100))
    end_time = Column(String(100))

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关联关系
    events = relationship("TimelineEvent", back_populates="timeline")


class TimelineEvent(Base):
    """时间线事件表"""
    __tablename__ = "timeline_events"

    id = Column(Integer, primary_key=True, index=True)
    timeline_id = Column(Integer, ForeignKey("timelines.id"), nullable=False)

    # 基本信息
    name = Column(String(200), nullable=False)
    description = Column(Text)
    timestamp = Column(String(100))  # 故事内时间

    # 关联信息
    chapter_id = Column(Integer, ForeignKey("chapters.id"))
    characters_involved = Column(JSON)
    location = Column(String(200))

    # 事件属性
    event_type = Column(String(50))  # plot, character, world, background
    importance = Column(Integer, default=5)  # 1-10
    consequences = Column(JSON)
    prerequisites = Column(JSON)  # 前置事件

    created_at = Column(DateTime, default=func.now())

    # 关联关系
    timeline = relationship("Timeline", back_populates="events")


class GenerationTask(Base):
    """生成任务表"""
    __tablename__ = "generation_tasks"

    id = Column(Integer, primary_key=True, index=True)
    novel_id = Column(Integer, ForeignKey("novels.id"))

    # 任务信息
    task_type = Column(String(50), nullable=False)  # novel, chapter, character, etc.
    status = Column(String(20), default="pending")  # pending, running, completed, failed

    # 配置和参数
    parameters = Column(JSON)
    config = Column(JSON)

    # 进度信息
    progress = Column(Float, default=0.0)
    current_step = Column(String(200))

    # 结果信息
    result = Column(JSON)
    error_message = Column(Text)

    # 时间信息
    created_at = Column(DateTime, default=func.now())
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # 元数据
    estimated_duration = Column(Integer)  # 预估时间（秒）
    actual_duration = Column(Integer)  # 实际时间（秒）


class ConsistencyCheck(Base):
    """一致性检查表"""
    __tablename__ = "consistency_checks"

    id = Column(Integer, primary_key=True, index=True)
    novel_id = Column(Integer, ForeignKey("novels.id"), nullable=False)

    # 检查信息
    check_type = Column(String(50))  # full, character, plot, world, etc.
    overall_score = Column(Float)  # 总体评分 0-100

    # 问题统计
    issue_count = Column(Integer, default=0)
    critical_issues = Column(Integer, default=0)
    high_issues = Column(Integer, default=0)
    medium_issues = Column(Integer, default=0)
    low_issues = Column(Integer, default=0)

    # 详细结果
    issues = Column(JSON)  # 问题列表
    recommendations = Column(JSON)  # 建议列表

    created_at = Column(DateTime, default=func.now())


class UserSession(Base):
    """用户会话表"""
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, nullable=False, index=True)

    # 会话信息
    user_id = Column(String(100))  # 用户标识
    current_novel_id = Column(Integer, ForeignKey("novels.id"))

    # 会话状态
    context = Column(JSON)  # 会话上下文
    preferences = Column(JSON)  # 用户偏好

    # 时间信息
    created_at = Column(DateTime, default=func.now())
    last_activity = Column(DateTime, default=func.now())
    expires_at = Column(DateTime)


class ToolUsage(Base):
    """工具使用记录表"""
    __tablename__ = "tool_usage"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), ForeignKey("user_sessions.session_id"))

    # 工具信息
    tool_name = Column(String(100), nullable=False)
    tool_category = Column(String(50))

    # 调用信息
    parameters = Column(JSON)
    context = Column(JSON)

    # 结果信息
    success = Column(Boolean, default=True)
    result = Column(JSON)
    error_message = Column(Text)
    execution_time = Column(Float)  # 执行时间（秒）

    # 时间信息
    called_at = Column(DateTime, default=func.now())

    # 使用统计
    token_usage = Column(JSON)  # Token使用情况


# 数据库工具函数
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config.settings import get_settings


def get_database_url() -> str:
    """获取数据库URL"""
    settings = get_settings()
    return settings.database.url


def create_database_engine():
    """创建数据库引擎"""
    database_url = get_database_url()
    engine = create_engine(
        database_url,
        echo=get_settings().database.echo,
        pool_size=get_settings().database.pool_size
    )
    return engine


def create_database_session():
    """创建数据库会话"""
    engine = create_database_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def init_database():
    """初始化数据库"""
    engine = create_database_engine()
    Base.metadata.create_all(bind=engine)
    print("数据库初始化完成")


def drop_database():
    """删除所有表"""
    engine = create_database_engine()
    Base.metadata.drop_all(bind=engine)
    print("数据库已清空")


# 数据访问对象 (DAO)
class NovelDAO:
    """小说数据访问对象"""

    def __init__(self, db_session=None):
        self.db = db_session or create_database_session()

    def create_novel(self, novel_data: Dict[str, Any]) -> Novel:
        """创建小说"""
        novel = Novel(**novel_data)
        self.db.add(novel)
        self.db.commit()
        self.db.refresh(novel)
        return novel

    def get_novel(self, novel_id: int) -> Optional[Novel]:
        """获取小说"""
        return self.db.query(Novel).filter(Novel.id == novel_id).first()

    def get_novels_by_status(self, status: str) -> List[Novel]:
        """按状态获取小说列表"""
        return self.db.query(Novel).filter(Novel.status == status).all()

    def update_novel(self, novel_id: int, update_data: Dict[str, Any]) -> bool:
        """更新小说"""
        result = self.db.query(Novel).filter(Novel.id == novel_id).update(update_data)
        self.db.commit()
        return result > 0

    def delete_novel(self, novel_id: int) -> bool:
        """删除小说"""
        novel = self.get_novel(novel_id)
        if novel:
            self.db.delete(novel)
            self.db.commit()
            return True
        return False


class CharacterDAO:
    """角色数据访问对象"""

    def __init__(self, db_session=None):
        self.db = db_session or create_database_session()

    def create_character(self, character_data: Dict[str, Any]) -> Character:
        """创建角色"""
        character = Character(**character_data)
        self.db.add(character)
        self.db.commit()
        self.db.refresh(character)
        return character

    def get_characters_by_novel(self, novel_id: int) -> List[Character]:
        """获取小说的所有角色"""
        return self.db.query(Character).filter(Character.novel_id == novel_id).all()

    def get_main_characters(self, novel_id: int) -> List[Character]:
        """获取主要角色"""
        return self.db.query(Character).filter(
            Character.novel_id == novel_id,
            Character.importance >= 7
        ).all()


# 全局数据库实例
_db_session = None


def get_db_session():
    """获取全局数据库会话"""
    global _db_session
    if _db_session is None:
        _db_session = create_database_session()
    return _db_session


def close_db_session():
    """关闭全局数据库会话"""
    global _db_session
    if _db_session:
        _db_session.close()
        _db_session = None


if __name__ == "__main__":
    # 初始化数据库
    init_database()

    # 创建示例数据
    dao = NovelDAO()

    sample_novel = dao.create_novel({
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

    print(f"创建示例小说：{sample_novel.title} (ID: {sample_novel.id})")
