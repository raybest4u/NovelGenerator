

# tests/conftest.py
"""
pytest配置和共享fixtures
"""

import pytest
import asyncio
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock

from core.llm_client import LLMService, LLMResponse
from core.base_tools import ToolRegistry
from config.settings import get_settings


@pytest.fixture
def mock_llm_response():
    """模拟LLM响应"""
    return LLMResponse(
        content="这是一个测试响应",
        usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        model="test-model",
        finish_reason="stop",
        response_time=1.0
    )


@pytest.fixture
def mock_llm_service(mock_llm_response):
    """模拟LLM服务"""
    service = MagicMock(spec=LLMService)
    service.generate_text = AsyncMock(return_value=mock_llm_response)
    service.stream_generate = AsyncMock()
    return service


@pytest.fixture
def tool_registry():
    """工具注册表fixture"""
    return ToolRegistry()


@pytest.fixture
def sample_world_setting():
    """示例世界设定"""
    return {
        "name": "测试世界",
        "type": "大陆",
        "time_period": "古代",
        "technology_level": "中世纪",
        "magic_prevalence": "高",
        "political_system": "封建制",
        "major_races": ["人族", "妖族"],
        "major_kingdoms": [{"name": "大周王朝", "description": "人族王朝"}],
        "natural_features": ["昆仑山脉", "长江"],
        "unique_elements": ["灵气", "仙境"],
        "history_timeline": [{"period": "远古", "event": "世界诞生"}],
        "culture_notes": "修仙文化",
        "economy_system": "农业为主",
        "languages": ["通用语"]
    }


@pytest.fixture
def sample_character():
    """示例角色"""
    return {
        "id": "char_1",
        "name": "李逍遥",
        "nickname": "剑仙",
        "character_type": "主角",
        "importance": 10,
        "appearance": {
            "gender": "男",
            "age": 18,
            "height": "中等",
            "build": "匀称",
            "hair_color": "黑色",
            "eye_color": "黑色",
            "skin_tone": "正常",
            "distinctive_features": ["剑眉星目"],
            "clothing_style": "青衫",
            "accessories": ["玉佩"]
        },
        "personality": {
            "core_traits": ["勇敢", "正义"],
            "strengths": ["意志坚强"],
            "weaknesses": ["冲动"],
            "fears": ["失去朋友"],
            "desires": ["变强"],
            "habits": ["晨练"],
            "speech_pattern": "直接",
            "moral_alignment": "善良"
        },
        "background": {
            "birthplace": "余杭镇",
            "family": {"父母": "已故"},
            "childhood": "孤儿",
            "education": ["私塾"],
            "major_events": [{"事件": "踏上修仙路"}],
            "relationships": [],
            "secrets": ["身世之谜"],
            "goals": ["成为剑仙"]
        },
        "abilities": {
            "power_level": "炼气期",
            "cultivation_method": "基础剑法",
            "special_abilities": [{"name": "御剑术"}],
            "combat_skills": ["剑法"],
            "non_combat_skills": ["炼丹"],
            "artifacts": [{"name": "飞剑"}],
            "spiritual_root": "金属性",
            "talent_level": "上等"
        }
    }


@pytest.fixture
def sample_story_outline():
    """示例故事大纲"""
    return {
        "title": "测试小说",
        "genre": "玄幻",
        "theme": "成长",
        "premise": "少年修仙记",
        "structure": "三幕式",
        "tone": "励志",
        "protagonist": "李逍遥",
        "antagonist": "魔教教主",
        "central_conflict": "正邪对决",
        "stakes": "拯救世界",
        "plot_points": [
            {
                "id": "opening",
                "name": "开场",
                "description": "介绍主角",
                "chapter_range": "1-2",
                "importance": 8,
                "plot_function": "设定",
                "characters_involved": ["李逍遥"],
                "conflicts": [],
                "outcomes": ["进入修仙世界"]
            }
        ],
        "chapters": [
            {
                "number": 1,
                "title": "第一章",
                "summary": "开始的故事",
                "word_count_target": 3000,
                "key_events": ["初遇"],
                "character_focus": ["李逍遥"],
                "plot_advancement": "开场",
                "tension_level": 3,
                "pacing": "slow",
                "mood": "平静"
            }
        ],
        "beginning": "平凡少年",
        "middle": "修炼成长",
        "climax": "最终决战",
        "resolution": "成就剑仙",
        "subplots": [],
        "themes": ["成长", "友谊"],
        "symbols": ["剑"],
        "motifs": ["修炼"]
    }





