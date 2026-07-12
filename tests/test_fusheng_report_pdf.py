from __future__ import annotations

import pytest

from app.schemas.fusheng_report import FushengReportPdfRequest
from services.fusheng_report_service import render_fusheng_report_html


def test_render_fusheng_report_html_contains_core_sections():
    payload = {
        "meta": {
            "label": "刘博 · 1990/01/15",
            "birth_dt": "1990-01-15T08:30:00",
            "city_name": "北京",
            "calendar_mode": "gregorian",
            "focus_topic": "事业",
            "notes": "换运节点 2028",
            "generated_at": "2026-07-11T12:00:00",
        },
        "bazi": {
            "bazi_summary": "日主偏弱，喜木水。",
            "geju": {"geju_name": "正官格", "interpretation_text": "官星透干。", "recorded_geju": "从官杀格", "engine_geju": "七杀格", "dual_track_id": "ZIP09", "dual_track_note": "古籍从杀 vs 引擎七杀"},
            "day_master_strength": {"tier": "偏弱"},
            "yongshen": {"favor": ["wood", "water"], "avoid": ["metal"]},
            "pillars_primary": {
                "year": {"stem": "己", "branch": "巳"},
                "month": {"stem": "丙", "branch": "子"},
                "day": {"stem": "甲", "branch": "子"},
                "hour": {"stem": "戊", "branch": "辰"},
            },
            "dayun": {"items": [{"start_year": 1998, "stem": "乙", "branch": "丑", "ten_god": "劫财"}]},
            "missing_fields": ["geju_detail"],
            "confidence_level": "medium",
            "provenance": {"geju": {"layer": "classical", "confidence": 0.9}},
            "liuri_liushi": {"date": "2026-07-11", "day_ganzhi": "甲子", "hour_ganzhi": "丙寅"},
        },
        "ziwei": {
            "summary": "命宫紫微天府，格局清正。",
            "wuxing_ju_name": "水二局",
            "life_palace_gz": "甲子",
            "missing_fields": ["forecast"],
            "iztro_crosscheck": {"status": "ok", "main_match": 12, "main_total": 14, "life_palace_match": True},
            "palaces": [{"name": "命宫", "stem": "甲", "branch": "子", "main_stars": [{"name": "紫微"}]}],
        },
        "name": {
            "summary": "五格综合良好。",
            "sancai": {"pattern": "木水火", "lucky": "吉", "desc": "三才吉"},
            "tianke": {"number": 8, "element": "金", "lucky": "吉", "score": 8},
            "renke": {"number": 15, "element": "木", "lucky": "吉", "score": 8},
            "dike": {"number": 7, "element": "水", "lucky": "吉", "score": 7},
            "waike": {"number": 2, "element": "火", "lucky": "凶", "score": 2},
            "zonge": {"number": 22, "element": "木", "lucky": "吉", "score": 8},
        },
    }

    html = render_fusheng_report_html(payload)

    assert "浮生 · 命理个人档案" in html
    assert "八字总览" in html
    assert "紫微总览" in html
    assert "姓名分析" in html
    assert "人工批注区" in html
    assert "换运节点 2028" in html
    assert "木" in html
    assert "引擎可信度" in html
    assert "geju_detail" in html
    assert "iztro 交叉核验" in html
    assert "双轨对照附录" in html
    assert "ZIP09" in html
    assert "从官杀格" in html


def test_render_fusheng_report_html_contains_algo_meta_labels():
    payload = {
        "meta": {
            "label": "测试",
            "birth_dt": "1990-01-15T08:30:00",
            "calendar_mode": "gregorian",
            "year_divide": "normal",
            "day_divide": "forward",
            "zi_day_rule": "early_zi_prev_day",
            "generated_at": "2026-07-11T12:00:00",
        },
        "bazi": {"geju": {}, "yongshen": {}, "pillars_primary": {}},
        "ziwei": {"palaces": [], "engine_warnings": ["右弼安星与 iztro 流派不同"]},
    }
    html = render_fusheng_report_html(payload)
    assert "正月初一换年" in html
    assert "农历日+1安星" in html
    assert "early_zi_prev_day" in html
    assert "引擎提示" in html
    assert "右弼安星" in html


def test_render_fusheng_report_html_contains_explain_draft():
    payload = {
        "meta": {
            "label": "测试",
            "birth_dt": "1990-01-15T08:30:00",
            "calendar_mode": "gregorian",
            "generated_at": "2026-07-11T12:00:00",
        },
        "bazi": {"geju": {}, "yongshen": {}, "pillars_primary": {}},
        "ziwei": {"palaces": []},
        "explain_bazi": {
            "disclaimer_block": {
                "text": "本辑录仅供文化研究与自我认知参考，不构成医疗、法律或投资建议。",
                "version": "2026-07-12",
            },
            "sections": [
                {
                    "section_id": "geju",
                    "blocks": [{"text": "正官格主贵气。", "layer": "inference"}],
                },
            ],
        },
        "explain_ziwei": {
            "sections": [
                {
                    "section_id": "palaces",
                    "blocks": [{"text": "命宫紫微坐守。", "layer": "reference"}],
                },
            ],
        },
    }
    html = render_fusheng_report_html(payload)
    assert "解读草案" in html
    assert "格局解读" in html
    assert "正官格主贵气" in html
    assert "宫位解读" in html
    assert "不构成医疗、法律或投资建议" in html


def test_fusheng_report_pdf_request_validates_algo_fields():
    with pytest.raises(ValueError, match="year_divide"):
        FushengReportPdfRequest(
            birth_dt="1990-01-15T08:30:00",
            lon=116.4,
            gender="male",
            year_divide="invalid",
        )
    with pytest.raises(ValueError, match="zi_day_rule"):
        FushengReportPdfRequest(
            birth_dt="1990-01-15T08:30:00",
            lon=116.4,
            gender="male",
            zi_day_rule="bad",
        )
