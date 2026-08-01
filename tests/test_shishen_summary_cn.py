"""十神摘要文案须用中文五行，不夹 wood/water 等英文。"""

from __future__ import annotations

from app.schemas.bazi import TenGodsModel
from services.bazi_engine_service import _build_shishen_summary


def test_shishen_summary_text_uses_chinese_element():
    summary = _build_shishen_summary(
        ds_st="癸",
        ys_st="己",
        ms_st="丁",
        hs_st="庚",
        ys_br="巳",
        ms_br="丑",
        ds_br="辰",
        hs_br="辰",
        ten_gods=TenGodsModel(year="偏印", month="食神", day="日主", hour="七杀"),
        shishen_scores={"偏印": 2.0, "食神": 1.5, "七杀": 1.0, "比肩": 0.5},
    )
    assert "water" not in summary.summary_text.lower()
    assert "木" in summary.summary_text or "火" in summary.summary_text or "土" in summary.summary_text or "金" in summary.summary_text or "水" in summary.summary_text
    assert "水阴" in summary.summary_text or "（水阴）" in summary.summary_text
    assert "日主癸" in summary.summary_text
