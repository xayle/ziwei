"""
services/name_engine/__init__.py — 姓名学引擎公开接口
"""

from __future__ import annotations

from .engine import (
    GridInfo,
    NameAnalysis,
    NameSuggestion,
    SancaiInfo,
    analyze_name,
    calc_five_grids,
    get_stroke_count,
    suggest_names,
)

__all__ = [
    "GridInfo",
    "NameAnalysis",
    "NameSuggestion",
    "SancaiInfo",
    "analyze_name",
    "calc_five_grids",
    "get_stroke_count",
    "suggest_names",
]
