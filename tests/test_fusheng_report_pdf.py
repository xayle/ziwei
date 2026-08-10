from __future__ import annotations

import asyncio
from datetime import datetime

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
    assert "八字满盘" in html
    assert "紫微总览" in html
    assert "姓名分析" in html
    assert "人工批注区" in html
    assert "换运节点 2028" in html
    assert "木" in html
    assert "校勘与可信度" in html
    assert "格局细目" in html
    assert "运限预测" in html
    assert "字段注记" in html
    assert "geju_detail" not in html
    assert "forecast" not in html
    assert "八字·格局=典籍" in html
    assert "置信度" in html and "中等" in html
    assert "对照结论" in html
    assert "iztro 交叉核验" not in html
    assert "main_match" not in html
    assert "主星一致" in html or "主星一致数" in html
    assert "1990年1月15日 08:30" in html
    assert "1990-01-15T08:30:00" not in html
    assert "行动建议" in html
    assert "一致" in html or "降级" in html or "命宫" in html or "未核验" in html
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
            "late_zishi": False,
            "birth_time_precision": "unknown",
            "unknown_time_fallback": "midday",
            "generated_at": "2026-07-11T12:00:00",
        },
        "bazi": {"geju": {}, "yongshen": {}, "pillars_primary": {}},
        "ziwei": {"palaces": [], "engine_warnings": ["右弼安星与 iztro 流派不同"]},
    }
    html = render_fusheng_report_html(payload)
    assert "正月初一换年" in html
    assert "农历日+1安星" in html
    assert "早子算前一日" in html
    assert "early_zi_prev_day" not in html
    assert "晚子不换日" in html
    assert "时辰未详" in html
    assert "日中 12:30" in html
    assert "公历" in html
    assert "gregorian" not in html
    assert "引擎提示" in html
    assert "右弼安星" in html
    assert "开源对照轨" in html
    assert "iztro" not in html.lower()


def test_exact_precision_hides_unknown_fallback_and_empty_notes():
    payload = {
        "meta": {
            "label": "刘博",
            "birth_dt": "1990-07-17T12:25:00",
            "city_name": "徐州",
            "calendar_mode": "gregorian",
            "birth_time_precision": "exact",
            "unknown_time_fallback": "midday",
            "notes": "",
            "generated_at": "2026-08-10T12:00:00",
        },
        "bazi": {
            "geju": {"geju_name": "七杀格"},
            "yongshen": {"favor": ["wood"], "avoid": ["metal"]},
            "day_master_strength": {"tier": "极弱"},
            "pillars_primary": {},
            "validation": {"level": "L0", "interpretation_enabled": True},
        },
        "ziwei": {
            "palaces": [],
            "life_palace_gz": "甲子",
            "iztro_crosscheck": {"status": "main_match", "main_match": 12, "main_total": 14},
        },
    }
    html = render_fusheng_report_html(payload)
    assert "未知默认" not in html
    assert "1990年7月17日 12:25（徐州）" in html
    assert "人工批注区" not in html
    assert "本命暂无古籍双轨样例" in html
    assert "双轨对照附录" not in html  # 空态并入基础档案，不单独成页
    assert "L0" not in html
    assert "双轨一致" in html
    assert "main_match" not in html
    assert "综合总结" in html
    assert "日主偏弱，喜木水" not in html  # 总结页不得整段粘贴旧摘要


def test_bazi_overview_includes_ten_gods_and_hidden_stems():
    payload = {
        "meta": {
            "label": "测试",
            "birth_dt": "1990-07-17T12:25:00",
            "birth_time_precision": "exact",
            "generated_at": "2026-08-10T12:00:00",
        },
        "bazi": {
            "geju": {"geju_name": "七杀格"},
            "yongshen": {"favor": ["metal", "water"], "avoid": ["fire"]},
            "day_master_strength": {"tier": "极弱"},
            "ten_gods": {"year": "正印", "month": "比肩", "day": "日主", "hour": "正官"},
            "pillars_primary": {
                "year": {"stem": "庚", "branch": "午"},
                "month": {"stem": "癸", "branch": "未"},
                "day": {"stem": "癸", "branch": "未"},
                "hour": {"stem": "戊", "branch": "午"},
            },
            "pillar_details": {
                "year": {
                    "stem": "庚",
                    "branch": "午",
                    "ten_god": "正印",
                    "hidden_stems": [
                        {"stem": "丁", "ten_god": "偏财"},
                        {"stem": "己", "ten_god": "七杀"},
                    ],
                    "xingyun": "绝",
                    "nayin": "路旁土",
                    "self_seat": "沐浴",
                    "kongwang": ["戌", "亥"],
                    "shensha": [{"name": "天乙贵人", "polarity": "+"}],
                },
                "month": {
                    "stem": "癸",
                    "branch": "未",
                    "ten_god": "比肩",
                    "hidden_stems": [{"stem": "己", "ten_god": "七杀"}],
                    "xingyun": "墓",
                    "nayin": "杨柳木",
                    "self_seat": "冠带",
                    "kongwang": ["戌", "亥"],
                    "shensha": [],
                },
                "day": {
                    "stem": "癸",
                    "branch": "未",
                    "ten_god": "日主",
                    "hidden_stems": [{"stem": "己", "ten_god": "七杀"}],
                    "xingyun": "墓",
                    "nayin": "杨柳木",
                    "self_seat": "冠带",
                    "kongwang": ["戌", "亥"],
                    "shensha": [{"name": "将星", "polarity": "+"}],
                },
                "hour": {
                    "stem": "戊",
                    "branch": "午",
                    "ten_god": "正官",
                    "hidden_stems": [{"stem": "丁", "ten_god": "偏财"}],
                    "xingyun": "病",
                    "nayin": "天上火",
                    "self_seat": "帝旺",
                    "kongwang": ["子", "丑"],
                    "shensha": [],
                },
            },
            "dayun": {
                "items": [
                    {
                        "start_year": 2020,
                        "stem": "己",
                        "branch": "卯",
                        "ten_god": "七杀",
                        "hidden_stems": [{"stem": "乙", "ten_god": "食神"}],
                        "xingyun": "长生",
                        "self_seat": "病",
                        "kongwang": ["子", "丑"],
                        "nayin": "城头土",
                        "shensha": [{"name": "华盖", "polarity": "+"}],
                    }
                ]
            },
            "liunian": {
                "items": [
                    {
                        "year": datetime.now().year,  # 对齐导出年流年列
                        "stem": "丙",
                        "branch": "午",
                        "ten_god": "正财",
                        "hidden_stems": [{"stem": "丁", "ten_god": "偏财"}],
                        "xingyun": "绝",
                        "self_seat": "帝旺",
                        "kongwang": ["寅", "卯"],
                        "nayin": "天河水",
                        "shensha": [],
                    }
                ]
            },
        },
        "ziwei": {"palaces": []},
    }
    html = render_fusheng_report_html(payload)
    assert "八字满盘" in html
    assert "流年" in html and "大运" in html
    assert "主星" in html and "藏干" in html and "空亡" in html and "星运" in html
    assert "正印" in html
    assert "偏财" in html
    assert "路旁土" in html
    assert "天乙贵人" in html
    assert "综合收束" not in html
    assert "FUSHENG ARCHIVE" in html


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
    assert "解读要点" in html
    assert "格局解读" in html or "格局" in html
    assert "正官格主贵气" in html
    assert "宫位解读" in html or "宫位" in html
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
    with pytest.raises(ValueError, match="unknown_time_fallback"):
        FushengReportPdfRequest(
            birth_dt="1990-01-15T08:30:00",
            lon=116.4,
            gender="male",
            unknown_time_fallback="bad",  # type: ignore[arg-type]
        )


def test_build_fusheng_report_payload_wires_algo_fields():
    from services.fusheng_report_service import build_fusheng_report_payload

    req = FushengReportPdfRequest(
        birth_dt="1990-01-15T08:30:00",
        lon=116.41,
        gender="male",
        late_zishi=False,
        birth_time_precision="hour",
        unknown_time_fallback="midday",
        year_divide="normal",
        day_divide="forward",
    )
    payload = asyncio.run(build_fusheng_report_payload(req))
    meta = payload["meta"]
    assert meta["late_zishi"] is False
    assert meta["birth_time_precision"] == "hour"
    assert meta["unknown_time_fallback"] == "midday"
    assert meta["year_divide"] == "normal"
    assert meta["day_divide"] == "forward"
    assert payload["bazi"]
    assert payload["ziwei"]
