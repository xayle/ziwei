"""T-01: 辅煞星落宫与多流派参数回归。"""

from __future__ import annotations

import pytest

from services.ziwei_engine.lunar import solar_to_lunar
from services.ziwei_engine.palaces import calc_palaces
from services.ziwei_engine.stars_aux import place_aux_stars

GOLDEN = (2002, 3, 13, 14, 55)


class TestStarsAuxPlacement:
    def setup_method(self):
        y, m, d, h, mi = GOLDEN
        self.lunar = solar_to_lunar(y, m, d, h, mi)
        self.layout = calc_palaces(self.lunar)

    def test_standard_wenchang_youbi(self):
        aux = place_aux_stars(self.lunar, lp_b=self.layout.life_branch_idx)
        assert aux["文昌"] == 3
        assert aux["文曲"] == 11
        assert aux["右弼"] == 9

    def test_yuede_by_year_branch(self):
        aux = place_aux_stars(self.lunar, lp_b=self.layout.life_branch_idx)
        assert "月德" in aux
        yb = self.lunar.year_branch_idx
        assert aux["月德"] == yb % 12
        assert aux["天德"] == (9 + yb) % 12

    @pytest.mark.parametrize("kuiyue_method", ["standard", "gengxin_mahu"])
    def test_kuiyue_methods(self, kuiyue_method):
        from services.ziwei_engine.stars_aux import _KUIYUE_TABLES

        aux = place_aux_stars(
            self.lunar,
            lp_b=self.layout.life_branch_idx,
            kuiyue_method=kuiyue_method,
        )
        kui_table, yue_table = _KUIYUE_TABLES[kuiyue_method]
        ys = self.lunar.year_stem_idx
        assert aux["天魁"] == kui_table[ys]
        assert aux["天钺"] == yue_table[ys]

    def test_legacy_wenchang_year_branch(self):
        aux = place_aux_stars(
            self.lunar,
            lp_b=self.layout.life_branch_idx,
            wenchang_method="year_branch",
            youbi_method="hour",
        )
        yb = self.lunar.year_branch_idx
        hb = self.lunar.hour_branch_idx
        assert aux["文昌"] == (9 - yb) % 12
        assert aux["文曲"] == (4 + yb) % 12
        assert aux["右弼"] == (10 - hb) % 12

    def test_tiankong_methods(self):
        yb = self.lunar.year_branch_idx
        hb = self.lunar.hour_branch_idx
        std = place_aux_stars(self.lunar, lp_b=0, tiankong_method="standard")
        shun = place_aux_stars(self.lunar, lp_b=0, tiankong_method="shun")
        assert std["天空"] == (10 + yb) % 12
        assert shun["天空"] == (yb + hb) % 12
