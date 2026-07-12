"""T-02: 长生/将前/岁前十二神回归。"""

from __future__ import annotations

from services.ziwei_engine.decorative import (
    CHANGSHENG_12,
    JIANGQIAN_12,
    SUIQIAN_12,
    place_changsheng12,
    place_jiangqian12,
    place_suiqian12,
)


class TestDecorativeStars:
    def test_changsheng12_covers_all_branches(self):
        # 火六局、阳男、午年(6)
        m = place_changsheng12(wuxing_ju=6, gender="男", year_branch_idx=6)
        assert len(m) == 12
        assert set(m.values()) == set(CHANGSHENG_12)

    def test_jiangqian12_starts_from_sanhe_group(self):
        # 午年(6) → 寅午戌 → 起午(6)
        m = place_jiangqian12(liunian_branch_idx=6)
        assert m[6] == "将星"
        assert len(set(m.values())) == len(JIANGQIAN_12)

    def test_suiqian12_starts_at_year_branch(self):
        m = place_suiqian12(liunian_branch_idx=6)
        assert m[6] == "岁建"
        assert len(set(m.values())) == len(SUIQIAN_12)

    def test_changsheng_direction_female_yin_year(self):
        m = place_changsheng12(wuxing_ju=3, gender="女", year_branch_idx=1)
        assert len(m) == 12
