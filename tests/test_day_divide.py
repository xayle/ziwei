"""day_divide 晚子时换日参数（solar_next / forward / current）。"""

from __future__ import annotations

from services.ziwei_engine import ziwei_full
from services.ziwei_engine.lunar import forward_lunar_day_for_stars


def test_forward_lunar_day_zw03():
    """1988-2-4 农历十七 → forward 安星日十八（与 2-5 农历日一致）。"""
    assert forward_lunar_day_for_stars(1988, 2, 4) == 18


def test_zw03_iztro_track_normal_forward():
    """iztro 对照轨：normal 年界 + forward 安星 → 癸丑命宫。"""
    c = ziwei_full(1988, 2, 4, 23, 45, "男", year_divide="normal", day_divide="forward")
    assert c.life_palace_gz == "癸丑"
    assert c.lunar.lunar_day == 17
    assert c.lunar.day_divide == "forward"


def test_zw03_engine_golden_lichun_solar_next():
    """引擎 golden 轨：lichun + solar_next → 乙丑。"""
    c = ziwei_full(1988, 2, 4, 23, 45, "男", year_divide="lichun", day_divide="solar_next")
    assert c.life_palace_gz == "乙丑"
    assert c.lunar.lunar_day == 18


def test_zw01_unchanged_default():
    """非边界盘默认 day_divide 不改变 ZW01。"""
    c = ziwei_full(2002, 3, 13, 14, 55, "女")
    assert c.life_palace_gz == "丁未"
    assert c.lunar.day_divide == "solar_next"
