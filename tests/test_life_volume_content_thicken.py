"""CNT：远端 life volumes 内容加厚回归（relations / 强弱 / 短块）。"""

from __future__ import annotations

from services.life_volume_service import (
    _enrich_vol_block,
    _relations_text,
    build_life_volumes_from_charts,
)


def test_relations_text_prefers_interaction_summary_not_type_label():
    bazi = {
        "relations_summary": {
            "interaction_summary": "拱合；丁[火]克庚[金]",
            "items": [
                {"type": "干支互动", "subject": "巳/丑", "summary": "拱合"},
            ],
        }
    }
    text = _relations_text(bazi)
    assert "拱合" in text
    assert "干支互动" not in text


def test_enrich_vol_block_pads_short_fact():
    out = _enrich_vol_block("卷一格局", "印旺生身")
    assert len(out) >= 40
    assert "印旺生身" in out


def test_colophon_labels_advisory_missing_fields():
    from services.life_volume_service import _build_colophon

    colo = _build_colophon(
        missing_fields=["palace_ten_gods", "youbi_month_vs_iztro_hour"],
        iztro_advisory=None,
        wenmo_advisory=None,
        engine_label="bazi+ziwei",
    )
    joined = "；".join(colo.summary_lines)
    assert "宫位十神" in joined
    assert "右弼" in joined
    assert "palace_ten_gods" not in joined
    assert "非故障" in joined


def test_build_volumes_includes_strength_factors_and_fortune_domains():
    bazi = {
        "pillars_primary": {
            "year": {"ganzhi": "己巳", "stem": "己", "branch": "巳"},
            "month": {"ganzhi": "丁丑", "stem": "丁", "branch": "丑"},
            "day": {"ganzhi": "庚辰", "stem": "庚", "branch": "辰"},
            "hour": {"ganzhi": "庚辰", "stem": "庚", "branch": "辰"},
        },
        "geju": {"geju_name": "正印格", "geju_detail": "印旺生身"},
        "day_master_strength": {
            "tier": "中和",
            "score": 53.0,
            "factors": [{"name": "月令得分", "reason": "月支旺相状态"}],
        },
        "current_fortune_summary": {
            "current_dayun": "癸酉",
            "current_liunian": "丙午",
            "this_year_domains": {"财运": "宜拓展收入渠道"},
        },
        "yongshen": {"favor": ["fire"], "avoid": ["wood"]},
    }
    doc = build_life_volumes_from_charts(
        case_id="cnt-thicken",
        chart_hash="h",
        bazi=bazi,
        ziwei=None,
        explain_bazi={},
        explain_ziwei={},
        entitlement="full_book",
    )
    vol1 = next(v for v in doc.volumes if v.id == "vol1")
    texts = {s.id: s.blocks[0].text for s in vol1.sections if s.blocks}
    assert "月令得分" in texts["strength"]
    assert "财运" in texts["current-fortune"]
    for sid in ("pillars", "geju", "yongshen", "strength"):
        assert len(texts[sid]) >= 40
