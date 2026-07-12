"""year_divide 年界参数（立春 vs 正月初一）。"""
from __future__ import annotations

from services.ziwei_engine import ziwei_full
from services.ziwei_engine.lunar import solar_to_lunar


def test_solar_to_lunar_zw03_boundary():
    """1988-2-5（晚子换日后）：立春年界 vs 正月初一年界。"""
    info_lichun = solar_to_lunar(1988, 2, 5, 23, 45, year_divide="lichun")
    info_normal = solar_to_lunar(1988, 2, 5, 23, 45, year_divide="normal")
    assert info_lichun.year_gz == "戊辰"
    assert info_normal.year_gz == "丁卯"


def test_zw03_life_palace_year_divide():
    """ZW03：lichun→乙丑（引擎默认）；normal→癸丑（对齐 iztro 命宫）。"""
    c_lichun = ziwei_full(1988, 2, 4, 23, 45, "男", year_divide="lichun")
    c_normal = ziwei_full(1988, 2, 4, 23, 45, "男", year_divide="normal")
    assert c_lichun.life_palace_gz == "乙丑"
    assert c_normal.life_palace_gz == "癸丑"


def test_zw01_unchanged_with_lichun_default():
    """默认 lichun 不改变 ZW01 黄金盘。"""
    c = ziwei_full(2002, 3, 13, 14, 55, "女")
    assert c.life_palace_gz == "丁未"
    assert c.lunar.year_divide == "lichun"
