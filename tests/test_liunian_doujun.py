"""T-03: 流年命宫、斗君流月专项回归。"""

from __future__ import annotations

from services.ziwei_engine.liunian import (
    calc_doujun,
    calc_liunian,
    calc_liunian_life_branch,
    calc_liuyue,
    calc_liuyue_list,
)
from services.ziwei_engine.lunar import solar_to_lunar

GOLDEN_YEAR, GOLDEN_MONTH, GOLDEN_DAY = 2002, 3, 13
GOLDEN_HOUR, GOLDEN_MIN = 14, 55


class TestLiunianDoujun:
    def setup_method(self):
        self.lunar = solar_to_lunar(GOLDEN_YEAR, GOLDEN_MONTH, GOLDEN_DAY, GOLDEN_HOUR, GOLDEN_MIN)

    def test_taisui_default(self):
        assert calc_liunian_life_branch(6, liunian_life_method="taisui") == 6
        assert calc_liunian_life_branch(6, liunian_life_method="yin_start") == (2 + 6) % 12

    def test_liunian_2026_wu_year(self):
        ln = calc_liunian(2026, GOLDEN_YEAR, life_palace_branch=7)
        assert ln.year_branch_idx == 6
        assert ln.life_palace_branch == 6

    def test_doujun_golden_case(self):
        ln = calc_liunian(2026, GOLDEN_YEAR, 7)
        dj = calc_doujun(ln.year_branch_idx, self.lunar.calc_lunar_month, self.lunar.hour_branch_idx)
        assert dj == 1

    def test_liuyue_doujun_vs_simplified(self):
        ln = calc_liunian(2026, GOLDEN_YEAR, 7)
        dj = calc_doujun(ln.year_branch_idx, self.lunar.calc_lunar_month, self.lunar.hour_branch_idx)
        b_doujun = calc_liuyue(ln.life_palace_branch, 1, doujun_branch=dj, liuyue_method="doujun")
        b_simple = calc_liuyue(ln.life_palace_branch, 1, liuyue_method="simplified")
        assert b_doujun == dj
        assert b_simple == ln.life_palace_branch

    def test_liuyue_list_twelve_items(self):
        ln = calc_liunian(2026, GOLDEN_YEAR, 7)
        branch_map = {i: f"宫{i}" for i in range(12)}
        items = calc_liuyue_list(
            ln,
            branch_map,
            birth_month=self.lunar.calc_lunar_month,
            birth_hour_branch=self.lunar.hour_branch_idx,
        )
        assert len(items) == 12
        assert items[0].liuyue_method == "doujun"
        assert items[0].doujun_branch == calc_doujun(ln.year_branch_idx, self.lunar.calc_lunar_month, self.lunar.hour_branch_idx)
