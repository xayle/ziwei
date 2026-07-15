"""E-01：软句式不得当典籍层。"""

from app.schemas.bazi import BaziFullRequest
from services.bazi_engine.classical_narrative import (
    geju_classic_sentence,
    geju_heuristic_sentence,
    is_soft_geju_narrative,
)
from services.bazi_provenance import build_bazi_provenance


def test_heuristic_alias_matches_classic_name():
    a = geju_heuristic_sentence("正官格")
    b = geju_classic_sentence("正官格")
    assert a == b
    assert "官清印顺" in a


def test_soft_narrative_detector():
    assert is_soft_geju_narrative("官清印顺，贵气有序。")
    assert not is_soft_geju_narrative("【《滴天髓》】通神论摘句")


def test_provenance_narrative_is_heuristic_for_soft_ref():
    class _G:
        geju_name = "正官格"
        classic_ref = "官清印顺，贵气有序；宜守正道，忌伤官破官。"
        interpretation_text = None
        derived_geju = None
        engine_geju = "正官格"
        is_broken = False
        recorded_geju = None
        dual_track_id = None
        dual_track_note = None
        geju_detail = None

    class _Resp:
        geju = _G()
        yongshen = None
        dayun = None
        yearly_fortune = None
        bazi_summary = ""
        missing_fields = []
        pillars_primary = None

    req = BaziFullRequest(
        dt="1990-01-15T12:00:00",
        lon=116.4,
        zi_day_rule="sxtwl",
    )
    prov = build_bazi_provenance(_Resp(), req, missing_fields=[])
    assert prov.narrative.layer == "heuristic"
