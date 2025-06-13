# modules/analysis/__init__.py
"""
小说分析模块
负责分析小说的各种特性，如一致性检查、质量评估等
"""

from .consistency_checker import ConsistencyChecker, ConsistencyCheckerTool

__all__ = ['ConsistencyChecker', 'ConsistencyCheckerTool']
