"""P1 fixes: current-dayun pattern + bazi enrich missing_fields."""

from __future__ import annotations

from types import SimpleNamespace

from services.ziwei_engine.dayun import DayunItem, DayunResult, resolve_current_dayun_item
from services.ziwei_engine.patterns import detect_patterns
from services.ziwei_engine.tables import BRANCHES


def _palace(name: str, branch_idx: int, main_stars=None, aux_names=None):
    return SimpleNamespace(
        name=name,
        branch_idx=branch_idx,
        branch=BRANCHES[branch_idx],
        main_stars=main_stars or [],
        aux_names=aux_names or set(),
    )


class TestResolveCurrentDayun:
    def test_picks_active_limit(self):
        dayun = DayunResult(
            forward=True,
            start_age_exact=2.0,
            start_age=2,
            items=[
                DayunItem(1, 0, 0, "甲子", 2, 11, 2000, sihua={"武曲": "化忌"}),
                DayunItem(2, 1, 1, "乙丑", 12, 21, 2010, sihua={"廉贞": "化忌"}),
            ],
        )
        assert resolve_current_dayun_item(dayun, 5).ganzhi == "甲子"
        assert resolve_current_dayun_item(dayun, 15).ganzhi == "乙丑"

    def test_before_start_returns_none(self):
        dayun = DayunResult(forward=True, start_age_exact=5.0, start_age=5, items=[
            DayunItem(1, 0, 0, "甲子", 5, 14, 2005, sihua={}),
        ])
        assert resolve_current_dayun_item(dayun, 3) is None


class TestDayunJiChongCurrentOnly:
    def test_only_current_dayun_triggers_pattern(self):
        life_opp = 6  # 命宫在 0，对宫在 6
        palaces = [_palace("命宫", 0)]
        star_branches = {"武曲": life_opp, "廉贞": life_opp}

        current = DayunItem(1, 0, 0, "甲子", 2, 11, 2000, sihua={"武曲": "化忌"})
        other = DayunItem(2, 1, 1, "乙丑", 12, 21, 2010, sihua={"廉贞": "化忌"})

        hits = detect_patterns(
            palaces,
            life_palace_branch=0,
            star_branches=star_branches,
            current_dayun_item=current,
        )
        names = {p.name for p in hits}
        assert "大限化忌冲本命" in names
        assert any("甲子" in p.description for p in hits if p.name == "大限化忌冲本命")

        misses = detect_patterns(
            palaces,
            life_palace_branch=0,
            star_branches=star_branches,
            current_dayun_item=other,
        )
        assert any("乙丑" in p.description for p in misses if p.name == "大限化忌冲本命")
        assert not any("甲子" in p.description for p in misses if p.name == "大限化忌冲本命")

    def test_no_current_dayun_skips_pattern(self):
        palaces = [_palace("命宫", 0)]
        star_branches = {"武曲": 6}
        current = DayunItem(1, 0, 0, "甲子", 2, 11, 2000, sihua={"武曲": "化忌"})
        all_hits = detect_patterns(
            palaces,
            dayun=SimpleNamespace(items=[current]),
            life_palace_branch=0,
            star_branches=star_branches,
            current_dayun_item=None,
        )
        assert "大限化忌冲本命" not in {p.name for p in all_hits}


class TestBaziEnrichMissingFields:
    def test_build_liunian_clash_not_placeholder(self):
        from services.bazi_full_service import build_liunian
        from app.schemas import PillarsModel, PillarModel

        pillars = PillarsModel(
            year=PillarModel(stem="庚", branch="午", ganzhi="庚午"),
            month=PillarModel(stem="己", branch="卯", ganzhi="己卯"),
            day=PillarModel(stem="甲", branch="子", ganzhi="甲子"),
            hour=PillarModel(stem="丙", branch="寅", ganzhi="丙寅"),
        )
        from datetime import datetime

        result = build_liunian(pillars, datetime(1990, 1, 1), [0])
        assert result.items
        assert result.items[0].clash != "缺失"
