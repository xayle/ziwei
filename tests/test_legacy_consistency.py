"""T-06: legacy vs 新引擎一致性（wuxing/strength/yongshen）。"""

from __future__ import annotations

from app.schemas import PillarModel, PillarsModel
from services.bazi_full_service import compute_core_metrics


class TestLegacyConsistency:
    def test_compute_core_metrics_stable_for_gt04(self):
        """GT04 羊刃格：用神应含 metal/fire/earth（B-P0-02 口径）。"""
        pillars = PillarsModel(
            year=PillarModel(stem="戊", branch="辰", ganzhi="戊辰"),
            month=PillarModel(stem="乙", branch="卯", ganzhi="乙卯"),
            day=PillarModel(stem="甲", branch="戌", ganzhi="甲戌"),
            hour=PillarModel(stem="辛", branch="未", ganzhi="辛未"),
        )
        wx, bd, st, ys = compute_core_metrics(pillars, geju_name="月刃格")
        assert 0 <= wx.wood <= 100
        assert st.tier in ("极旺", "偏旺", "中和", "偏弱", "极弱")
        assert "metal" in ys.favor
        assert "fire" in ys.favor
        assert sum(bd.stem_contrib.values()) == 4.0

    def test_wuxing_percentages_sum_to_100(self):
        pillars = PillarsModel(
            year=PillarModel(stem="庚", branch="午", ganzhi="庚午"),
            month=PillarModel(stem="癸", branch="未", ganzhi="癸未"),
            day=PillarModel(stem="癸", branch="未", ganzhi="癸未"),
            hour=PillarModel(stem="戊", branch="午", ganzhi="戊午"),
        )
        wx, _, _, _ = compute_core_metrics(pillars)
        total = wx.wood + wx.fire + wx.earth + wx.metal + wx.water
        assert 99.0 <= total <= 101.0
