"""P2: liuri linkage, next dayun transition, pattern rule_id."""

from __future__ import annotations

import datetime

from services.bazi_engine.dayun import compute_next_dayun_transition, virtual_age
from services.bazi_engine.liuri import get_liuri_liushi
from services.ziwei_engine.patterns import PatternResult, _assign_pattern_rule_ids


class TestNextDayunTransition:
    def test_days_until_next_limit(self):
        birth = datetime.date(1990, 7, 17)
        items = [
            {"start_age": 3, "stem": "甲", "branch": "子"},
            {"start_age": 13, "stem": "乙", "branch": "丑"},
        ]
        ref = datetime.date(1998, 1, 1)  # 虚岁 9，在首运内
        out = compute_next_dayun_transition(birth, items, ref)
        assert out["days_to_next_transition"] is not None
        assert out["days_to_next_transition"] > 0
        assert out["next_transition_age"] == 13
        assert "乙丑" in (out["next_transition_ganzhi"] or "")

    def test_virtual_age(self):
        assert virtual_age(datetime.date(1990, 7, 17), datetime.date(1990, 7, 16)) == 1
        assert virtual_age(datetime.date(1990, 7, 17), datetime.date(1991, 7, 17)) == 2

    def test_leap_day_birthday_anniversary(self):
        """闰日生日（2-29）在非闰年换运锚点不崩溃。"""
        birth = datetime.date(2000, 2, 29)
        items = [
            {"start_age": 3, "stem": "甲", "branch": "子"},
            {"start_age": 13, "stem": "乙", "branch": "丑"},
        ]
        ref = datetime.date(2012, 1, 1)
        out = compute_next_dayun_transition(birth, items, ref)
        assert out["days_to_next_transition"] is not None
        assert out["next_transition_age"] == 13


class TestLiuriLinkage:
    def test_flow_score_with_dayun_context(self):
        out = get_liuri_liushi(
            1990,
            7,
            17,
            12,
            day_stem="甲",
            target_date=datetime.date(1900, 1, 1),
            target_hour=14,
            dayun_ten_god="比肩",
            dayun_ganzhi="甲子",
            liunian_ten_god="食神",
            liunian_ganzhi="庚午",
        )
        assert out["flow_score"] is not None
        assert 0 <= out["flow_score"] <= 100
        assert out["flow_summary"]
        assert out["current_dayun_ganzhi"] == "甲子"


class TestPatternRuleId:
    def test_assign_rule_ids(self):
        results = [
            PatternResult(name="禄存守命", level="吉", description="test"),
            PatternResult(name="未知格局", level="凶", description="x"),
        ]
        _assign_pattern_rule_ids(results)
        assert results[0].rule_id == "ZRULE_001"
        assert results[1].rule_id == "ZRULE_002"
