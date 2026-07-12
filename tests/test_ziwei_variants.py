"""T-04: 多流派参数黄金集（四化/亮度/安星）。"""

from __future__ import annotations

import pytest

from services.ziwei_engine import ziwei_full
from services.ziwei_engine.stars_main import place_main_stars
from services.ziwei_engine.lunar import solar_to_lunar
from services.ziwei_engine.palaces import calc_palaces
from services.ziwei_engine.transforms import build_sihua_table

Y, M, D, H, MI, G = 2002, 3, 13, 14, 55, "女"


class TestSihuaVariants:
    """庚干四化多方案各应可排盘。"""

    @pytest.mark.parametrize("geng_idx", [0, 1, 2, 3, 4])
    def test_geng_stem_sihua_schemes(self, geng_idx):
        table = build_sihua_table({"庚": geng_idx})
        assert "庚" in table
        assert len(table["庚"]) == 4

    def test_chart_with_custom_geng_sihua(self):
        chart = ziwei_full(Y, M, D, H, MI, G, sihua_stem_indices={"庚": 2})
        assert len(chart.palaces) == 12


class TestBrightnessVariants:
    @pytest.mark.parametrize("method", ["standard", "zhongzhou", "mod1", "mod2"])
    def test_brightness_methods(self, method):
        lunar = solar_to_lunar(Y, M, D, H, MI)
        layout = calc_palaces(lunar)
        stars = place_main_stars(lunar.lunar_day, layout.wuxing_ju, brightness_method=method)
        assert len(stars) >= 14
        ziwei = stars.get("紫微")
        assert ziwei is not None
        assert ziwei.brightness_val >= 0
