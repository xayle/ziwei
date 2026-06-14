"""
app/schemas/name.py — 姓名学 API 请求/响应模型
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class NameRequest(BaseModel):
    """姓名学分析请求。"""

    surname: str = Field(..., min_length=1, max_length=3, description="姓（1-3个汉字）")
    given_name: str = Field(..., min_length=1, max_length=6, description="名（1-6个汉字）")

    model_config = {
        "json_schema_extra": {
            "example": {
                "surname": "李",
                "given_name": "明",
            }
        }
    }


class GridInfoResponse(BaseModel):
    """单格（天/人/地/外/总格）分析结果。"""

    number: int  # 格数
    element: str  # 对应五行
    lucky: str  # 吉凶文字
    score: int  # 吉凶分值（1-10）
    desc: str  # 数理释义


class SancaiInfoResponse(BaseModel):
    """三才五行配置结果。"""

    pattern: str  # 三才组合，如 "木火土"
    lucky: str  # 吉凶
    score: int  # 吉凶分值（1-10）
    desc: str  # 三才释义


class NameAnalysisResponse(BaseModel):
    """完整姓名学分析响应。"""

    surname: str
    given_name: str

    # 五格
    tianke: GridInfoResponse  # 天格
    renke: GridInfoResponse  # 人格
    dike: GridInfoResponse  # 地格
    waike: GridInfoResponse  # 外格
    zonge: GridInfoResponse  # 总格

    # 三才
    sancai: SancaiInfoResponse

    # 综合
    overall_score: int  # 综合评分 0-100
    summary: str  # 一句话摘要

    algorithm_version: str = "1.0.0"


# ─── 改名建议 ─────────────────────────────────────────────────────────────────


class NameSuggestRequest(BaseModel):
    """改名建议请求。"""

    surname: str = Field(..., min_length=1, max_length=3, description="姓（1-3个汉字）")
    name_length: int = Field(2, ge=1, le=2, description="期望名字字数：1 或 2")
    preferred_elements: list[str] | None = Field(
        None,
        description="希望名字包含的五行，如 ['水','木']。可从八字用神/喜神分析结果填入；不填则不限五行。",
    )
    top_n: int = Field(10, ge=1, le=20, description="返回建议数量（1-20）")
    min_score: int = Field(60, ge=0, le=100, description="最低综合评分（低于此分不返回）")

    model_config = {
        "json_schema_extra": {
            "example": {
                "surname": "张",
                "name_length": 2,
                "preferred_elements": ["水", "木"],
                "top_n": 10,
                "min_score": 65,
            }
        }
    }


class NameSuggestionItem(BaseModel):
    """单条改名建议。"""

    given_name: str  # 建议名
    overall_score: int  # 综合评分 0-100
    renke_score: int  # 人格吉凶分（1-10）
    sancai_score: int  # 三才吉凶分（1-10）
    sancai_pattern: str  # 三才五行组合，如 "金水木"
    element_composition: list[str]  # 各字五行，如 ["水", "木"]
    summary: str  # 一句话评语


class NameSuggestResponse(BaseModel):
    """改名建议响应。"""

    surname: str
    name_length: int
    preferred_elements: list[str] | None
    total_candidates_evaluated: int  # 评估的候选组合数
    suggestions: list[NameSuggestionItem]
    algorithm_version: str = "1.0.0"
