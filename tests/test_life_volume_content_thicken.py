"""CNT：远端 life volumes 内容加厚回归（relations / 强弱 / 短块）。"""

from __future__ import annotations

from services.life_volume_service import (
    _clip,
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


def test_enrich_vol_block_skips_long_body():
    body = "甲" * 50
    assert _enrich_vol_block("干支关系", body) == body


def test_vol2_thicker_with_reading_polarity_and_cite_pending():
    bazi = {
        "relations_summary": {
            "interaction_summary": "拱合；丁[火]克庚[金]",
            "clash_summary": "冲：子午",
            "items": [],
        },
        "shensha_summary": {
            "items": [
                {"name": "天乙", "is_beneficial": True},
                {"name": "羊刃", "is_beneficial": False},
            ],
        },
    }
    doc = build_life_volumes_from_charts(
        case_id="vol2-thick",
        chart_hash="h2",
        bazi=bazi,
        ziwei=None,
        explain_bazi={},
        explain_ziwei={},
        entitlement="full_book",
    )
    vol2 = next(v for v in doc.volumes if v.id == "vol2")
    ids = [s.id for s in vol2.sections]
    assert "relations-reading" in ids
    assert "shensha-auspicious" in ids
    assert "shensha-caution" in ids
    assert "relations-cite" in ids
    assert "vol2-cite-pending" not in ids
    blocks = [b for s in vol2.sections for b in s.blocks]
    assert len(blocks) >= 5
    avg = sum(len(b.text) for b in blocks) / len(blocks)
    assert avg >= 90
    ji = next(s for s in vol2.sections if s.id == "shensha-auspicious")
    assert "天乙" in ji.blocks[0].text
    shen = next(s for s in vol2.sections if s.id == "shensha-caution")
    assert "羊刃" in shen.blocks[0].text
    cite = next(s for s in vol2.sections if s.id == "relations-cite")
    assert cite.layer == "cite"
    assert "典籍依据" in cite.blocks[0].text


def test_relations_candidates_match_clash_and_combine():
    from services.bazi_engine.classic_refs import relations_candidates, relations_signal_tags

    rs = {"clash_summary": "冲：子午", "combine_summary": "合：子丑", "items": []}
    assert "六冲" in relations_signal_tags(rs)
    assert "六合" in relations_signal_tags(rs)
    cands = relations_candidates(rs, limit=3)
    assert cands
    assert any(r.get("id") in {"dizhi_ext01", "engine_ref.dizhi_ext01"} for r in cands)
    assert any(r.get("hint_type") == "verified" for r in cands)


def test_vol2_mounts_shensha_classic_refs_as_soft_inference():
    bazi = {
        "relations_summary": {"interaction_summary": "拱合", "items": []},
        "shensha_summary": {
            "items": [
                {
                    "name": "天乙贵人",
                    "is_beneficial": True,
                    "classic_source": "三命通会",
                    "classic_refs": [
                        {
                            "id": "shensha_001",
                            "source": "三命通会·论神煞",
                            "text": "天乙贵人，命中有之，遇事有贵人扶助。",
                            "hint_type": "soft",
                        }
                    ],
                }
            ],
        },
    }
    doc = build_life_volumes_from_charts(
        case_id="shensha-cite",
        chart_hash="hc",
        bazi=bazi,
        ziwei=None,
        explain_bazi={},
        explain_ziwei={},
        entitlement="full_book",
    )
    vol2 = next(v for v in doc.volumes if v.id == "vol2")
    ids = [s.id for s in vol2.sections]
    assert "shensha-classic-soft" in ids
    assert "vol2-cite-pending" not in ids
    soft = next(s for s in vol2.sections if s.id == "shensha-classic-soft")
    assert soft.layer == "inference"
    assert soft.blocks[0].layer == "inference"
    assert "天乙贵人" in soft.blocks[0].text
    assert "贵人扶助" in soft.blocks[0].text
    assert soft.blocks[0].classic_id == "shensha_001"


def test_clip_prefers_sentence_boundary():
    body = "甲句完整。乙句也很完整。丙句会被裁掉并尽量不拦腰。"
    out = _clip(body * 8, 80)
    assert "…" not in out or out.endswith("。") or out.endswith("…")
    # 应落在句号后，而不是固定 79 字硬切
    assert out.endswith("。") or out.endswith("…")
    assert "甲句完整。" in out


def test_vol1_fortune_capped_geju_yongshen_intact():
    long_tip = "宜拓展收入渠道并注意合作边界，" * 12
    bazi = {
        "pillars_primary": {
            "year": {"ganzhi": "己巳"},
            "month": {"ganzhi": "丁丑"},
            "day": {"ganzhi": "庚辰"},
            "hour": {"ganzhi": "庚辰"},
        },
        "geju": {
            "geju_name": "正印格",
            "geju_detail": "印旺生身，宜学业与文书。此句应完整保留不被运势摘要挤掉。",
            "classic_ref": "官清印顺，贵气有序。续句亦应完整可见于典籍节。",
        },
        "yongshen": {"favor": ["fire", "earth"], "avoid": ["wood"]},
        "current_fortune_summary": {
            "current_dayun": "癸酉",
            "current_liunian": "丙午",
            "this_year_domains": {
                "财运": long_tip,
                "事业": long_tip,
                "健康": long_tip,
            },
            "top3_actions": [long_tip, long_tip],
        },
    }
    doc = build_life_volumes_from_charts(
        case_id="vol1-trunc",
        chart_hash="ht",
        bazi=bazi,
        ziwei=None,
        explain_bazi={
            "sections": [
                {
                    "section_id": "geju",
                    "blocks": [
                        {
                            "text": "格局讲解长句其一。格局讲解长句其二应在五百字内尽量按句保留。" * 6,
                            "layer": "cite",
                            "classic_id": "CL-TEST",
                        }
                    ],
                }
            ]
        },
        explain_ziwei={},
        entitlement="full_book",
    )
    vol1 = next(v for v in doc.volumes if v.id == "vol1")
    texts = {s.id: s.blocks[0].text for s in vol1.sections if s.blocks}
    assert "此句应完整保留" in texts["geju"]
    assert "用神须与格局" in texts["yongshen"]
    assert len(texts["current-fortune"]) <= 360
    assert len(texts["current-fortune"]) < 500
    explain = next(s for s in vol1.sections if s.id == "geju-explain")
    assert len(explain.blocks[0].text) <= 500
    assert "格局讲解长句其一。" in explain.blocks[0].text


def test_preface_reading_guide_chinese_layers_no_english():
    doc = build_life_volumes_from_charts(
        case_id="preface-thick",
        chart_hash="hp",
        bazi={},
        ziwei=None,
        explain_bazi={},
        explain_ziwei={},
        entitlement="full_book",
    )
    preface = next(v for v in doc.volumes if v.id == "preface")
    guide = next(s for s in preface.sections if s.id == "reading-guide")
    joined = "".join(b.text for b in guide.blocks)
    assert len(guide.blocks) >= 2
    assert "排盘推算" in joined
    assert "典籍依据" in joined
    assert "经验推断" in joined
    assert "cite" not in joined.lower()
    assert "inference" not in joined.lower()
    assert "fact" not in joined.lower()
    avg = sum(len(b.text) for b in guide.blocks) / len(guide.blocks)
    assert avg >= 80


def test_vol4_has_mingshen_and_sanjang_reading():
    ziwei = {
        "wuxing_ju_name": "水二局",
        "life_palace_gz": "甲子",
        "body_palace_gz": "丙寅",
        "patterns": [],
        "palaces": [],
    }
    doc = build_life_volumes_from_charts(
        case_id="vol4-thick",
        chart_hash="h4",
        bazi={},
        ziwei=ziwei,
        explain_bazi={},
        explain_ziwei={},
        entitlement="full_book",
    )
    vol4 = next(v for v in doc.volumes if v.id == "vol4")
    ids = [s.id for s in vol4.sections]
    assert "ziwei-meta" in ids
    assert "ziwei-reading" in ids
    reading = next(s for s in vol4.sections if s.id == "ziwei-reading")
    text = reading.blocks[0].text
    assert "命身轴" in text
    assert "三方" in text
    assert len(text) >= 90


def test_vol6_has_howto_bridge_access_no_llm_leak():
    doc = build_life_volumes_from_charts(
        case_id="vol6-thick",
        chart_hash="h6",
        bazi={},
        ziwei=None,
        explain_bazi={},
        explain_ziwei={},
        entitlement="full_book",
    )
    vol6 = next(v for v in doc.volumes if v.id == "vol6")
    ids = [s.id for s in vol6.sections]
    assert "vol6-how-to-ask" in ids
    assert "vol6-bridge" in ids
    assert "vol6-access" in ids
    blocks = [b for s in vol6.sections for b in s.blocks]
    assert len(blocks) >= 3
    joined = "".join(b.text for b in blocks)
    assert "LLM" not in joined
    assert "事业" in joined
    avg = sum(len(b.text) for b in blocks) / len(blocks)
    assert avg >= 90


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
    assert "五书核验进行中" not in joined
    assert "已核验引擎条" in joined
    assert "冲合会" in joined


def test_vol1_yongshen_cite_from_verified_engine_ref():
    doc = build_life_volumes_from_charts(
        case_id="yong-cite",
        chart_hash="hy",
        bazi={
            "yongshen": {"favor": ["fire"], "avoid": ["wood"]},
            "pillars_primary": {"day": {"stem": "甲", "branch": "子"}},
        },
        ziwei=None,
        explain_bazi={},
        explain_ziwei={},
        entitlement="full_book",
    )
    vol1 = next(v for v in doc.volumes if v.id == "vol1")
    cite = next((s for s in vol1.sections if s.id == "yongshen-cite"), None)
    assert cite is not None
    assert cite.blocks[0].layer == "cite"
    assert cite.blocks[0].classic_id
    assert cite.blocks[0].classic_id.startswith("engine_ref.")


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
