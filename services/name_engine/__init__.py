"""
services/name_engine/__init__.py — 姓名学引擎公开接口
"""
from __future__ import annotations

from .engine import (
    NameAnalysis,
    NameSuggestion,
    GridInfo,
    SancaiInfo,
    analyze_name,
    suggest_names,
    calc_five_grids,
    get_stroke_count,
)

__all__ = [
    "NameAnalysis",
    "NameSuggestion",
    "GridInfo",
    "SancaiInfo",
    "analyze_name",
    "suggest_names",
    "calc_five_grids",
    "get_stroke_count",
]
