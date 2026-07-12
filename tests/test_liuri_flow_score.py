"""B-P2 流日三维评分 + transition_hint 回归（PRODUCT-P-ROADMAP W3）。"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from services.bazi_engine.dayun import compute_next_dayun_transition, virtual_age
from services.bazi_engine.liuri import get_liuri_liushi
from services.bazi_full_service import build_liuri_liushi_enrichment
from services.bazi_engine_service import calculate

ROOT = Path(__file__).parent.parent
GT_PATH = ROOT / "data" / "ground_truth_cases.json"


def _load_lr_cases() -> list[dict]:
    data = json.loads(GT_PATH.read_text(encoding="utf-8"))
    return [c for c in data["cases"] if str(c.get("id", "")).startswith("LR")]


def _run_calculate(case: dict):
    dt = datetime.fromisoformat(case["birth_dt_solar"]).replace(tzinfo=ZoneInfo("Asia/Shanghai"))
    return calculate(
        dt,
        float(case.get("longitude", 116.4)),
        "Asia/Shanghai",
        use_solar=False,
        mode="single",
        gender=case.get("gender"),
    )


class TestLiuriFlowScore3D:
    def test_three_dimensions_present_and_bounded(self):
        raw = get_liuri_liushi(
            1990,
            7,
            17,
            12,
            day_stem="癸",
            target_date=date(2026, 7, 17),
            target_hour=12,
            dayun_ten_god="七杀",
            dayun_ganzhi="己卯",
            liunian_ten_god="正印",
            liunian_ganzhi="丙午",
            yongshen_favor=["metal", "water"],
            yongshen_avoid=["fire"],
        )
        for key in ("flow_score_dayun", "flow_score_liunian", "flow_score_geju", "flow_score"):
            assert key in raw
            assert 0 <= raw[key] <= 100
        assert raw["flow_tone"] in ("顺", "平", "逆")
        assert raw["flow_summary"]

    def test_transition_hint_within_seven_days(self):
        raw = get_liuri_liushi(
            1990,
            7,
            17,
            12,
            day_stem="癸",
            target_date=date(2029, 7, 10),
            target_hour=12,
            dayun_ten_god="七杀",
            dayun_ganzhi="己卯",
            liunian_ten_god="偏印",
            liunian_ganzhi="己酉",
            days_to_next_transition=7,
            next_transition_ganzhi="戊寅",
            next_transition_age=40,
            next_transition_hint="距下一运（戊寅，虚岁40岁）约 7 天",
        )
        assert raw["transition_hint"]
        assert "换运" in raw["transition_hint"] or "7" in raw["transition_hint"]

    def test_geju_broken_lowers_geju_score(self):
        base = get_liuri_liushi(
            1993,
            3,
            6,
            8,
            day_stem="丙",
            target_date=date(2026, 3, 15),
            target_hour=10,
            dayun_ten_god="正官",
            liunian_ten_god="比肩",
            yongshen_favor=["water", "wood"],
        )
        broken = get_liuri_liushi(
            1993,
            3,
            6,
            8,
            day_stem="丙",
            target_date=date(2026, 3, 15),
            target_hour=10,
            dayun_ten_god="正官",
            liunian_ten_god="比肩",
            yongshen_favor=["water", "wood"],
            geju_broken=True,
        )
        assert broken["flow_score_geju"] <= base["flow_score_geju"]

    @pytest.mark.parametrize("zi_day_rule", ["sxtwl", "early_zi_prev_day", "early_zi_same_day"])
    def test_zi_boundary_warnings_linked_to_rule(self, zi_day_rule: str):
        raw = get_liuri_liushi(
            1990,
            7,
            17,
            12,
            day_stem="癸",
            target_date=date(2026, 1, 1),
            target_hour=23,
            zi_day_rule=zi_day_rule,
        )
        if zi_day_rule == "early_zi_same_day":
            assert raw["warnings"] == []
        else:
            assert raw["warnings"]
            assert "zi_day_rule" in raw["warnings"][0] or zi_day_rule in raw["warnings"][0]

    def test_missing_dayun_context_no_silent_dayun_score(self):
        raw = get_liuri_liushi(
            1990,
            7,
            17,
            12,
            day_stem="癸",
            target_date=date(2026, 7, 17),
            liunian_ten_god="正印",
            liunian_ganzhi="丙午",
        )
        assert "dayun_context" in raw["missing_fields"]
        assert "flow_score_dayun" not in raw
        assert raw.get("flow_score_liunian") is not None
        assert raw.get("flow_score_geju") is not None

    def test_missing_natal_day_stem_registers_flow_fields(self):
        raw = get_liuri_liushi(
            1990,
            7,
            17,
            12,
            target_date=date(2026, 7, 17),
            dayun_ten_god="七杀",
            liunian_ten_god="正印",
        )
        assert "natal_day_stem" in raw["missing_fields"]
        assert "flow_score" in raw["missing_fields"]
        assert "flow_score" not in raw

    def test_enrichment_pipeline_exposes_3d_fields(self):
        case = next(c for c in _load_lr_cases() if c["id"] == "LR01")
        calc = _run_calculate(case)
        vr = calc.verify_response
        td = date.fromisoformat(case["liuri"]["target_date"])
        payload, _patch = build_liuri_liushi_enrichment(
            verify_response=vr,
            birth_dt=datetime.fromisoformat(case["birth_dt_solar"]).replace(tzinfo=ZoneInfo("Asia/Shanghai")),
            target_date=td,
            target_hour=case["liuri"].get("target_hour", 12),
        )
        assert payload.get("flow_score_dayun") is not None
        assert payload.get("flow_score_geju") is not None
        if payload.get("flow_score_liunian") is None:
            assert "liunian_context" in (payload.get("missing_fields") or [])
        if case["liuri"].get("expect_transition_hint"):
            assert payload.get("transition_hint")


@pytest.mark.parametrize("case", _load_lr_cases(), ids=lambda c: c["id"])
def test_lr_ground_cases(case: dict):
    calc = _run_calculate(case)
    vr = calc.verify_response
    liuri_cfg = case["liuri"]
    td = date.fromisoformat(liuri_cfg["target_date"])
    payload, _ = build_liuri_liushi_enrichment(
        verify_response=vr,
        birth_dt=datetime.fromisoformat(case["birth_dt_solar"]).replace(tzinfo=ZoneInfo("Asia/Shanghai")),
        target_date=td,
        target_hour=liuri_cfg.get("target_hour", 12),
    )
    if liuri_cfg.get("expect_flow_scores_3d"):
        assert payload.get("flow_score_dayun") is not None, f"{case['id']} missing flow_score_dayun"
        assert payload.get("flow_score_geju") is not None, f"{case['id']} missing flow_score_geju"
        if payload.get("flow_score_liunian") is None:
            assert "liunian_context" in (payload.get("missing_fields") or []), (
                f"{case['id']} should register liunian_context when流年缺失"
            )
    if liuri_cfg.get("expect_transition_hint"):
        assert payload.get("transition_hint")
    if liuri_cfg.get("expect_flow_score_geju_min") is not None:
        assert payload["flow_score_geju"] >= liuri_cfg["expect_flow_score_geju_min"]
