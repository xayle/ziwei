"""
app/models/chart_case.py — 相似盘案例库模型

存储命盘特征向量用于近邻检索，每条记录对应一次排盘。
向量维度：21 维（命宫地支 12 + 五行局 5 + 性别 1 + 出生年 1 + 吉格数 1 + 凶格数 1）。
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Text
from sqlmodel import Field, SQLModel


class ChartCase(SQLModel, table=True):
    __tablename__ = "chart_cases"

    id: Optional[int] = Field(default=None, primary_key=True)

    # 命盘唯一标识（与 LLM 草稿的 chart_hash 保持一致）
    chart_hash: str = Field(index=True, max_length=64)

    # 出生信息摘要（用于展示）
    birth_year:  int   = Field(default=0)
    birth_month: int   = Field(default=0)
    birth_day:   int   = Field(default=0)
    birth_hour:  int   = Field(default=0)
    gender:      str   = Field(default="", max_length=4)

    # 命盘关键字段（用于展示与筛选）
    wuxing_ju_name:  str = Field(default="", max_length=10)
    life_palace_gz:  str = Field(default="", max_length=10)
    pattern_summary: str = Field(default="", max_length=400)   # 格局名逗号分隔

    # 特征向量（JSON 数组，21 维 float）
    vector_json: str = Field(sa_column=Column(Text), default="[]")

    # 来源标签（ground_truth / user / imported）
    source_label: str = Field(default="user", max_length=32)

    # 时间戳
    created_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = Field(default=None)
