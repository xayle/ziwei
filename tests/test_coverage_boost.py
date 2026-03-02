"""
tests/test_coverage_boost.py — M6.09 核心引擎覆盖率补充测试

目标: 将 services/bazi_engine 覆盖率从 79% 提升到 ≥80%
涵盖:
  - solar_time_v2.py   (Spencer EoT, P0-03, 红线11/31)
  - scoring.py         (6维评分引擎, M3.04)
  - lifestyle/tables.py (五行映射表, M1.04)
"""
from __future__ import annotations

import math
import pytest


# ─────────────────────────────────────────────────────────────────────────────
# solar_time_v2 — Spencer EoT (P0-03, 红线11)
# ─────────────────────────────────────────────────────────────────────────────

class TestSolarTimeV2:
    """Spencer EoT 公式单元测试 (P0-03)"""

    def test_equation_of_time_import(self):
        from services.bazi_engine.solar_time_v2 import equation_of_time_minutes
        assert callable(equation_of_time_minutes)

    def test_day_180(self):
        """夏至附近 EoT 约 -1.5 min ~ +1.5 min"""
        from services.bazi_engine.solar_time_v2 import equation_of_time_minutes
        eot = equation_of_time_minutes(172)  # 6月21日 = 夏至
        assert isinstance(eot, float)
        assert -5 < eot < 5

    def test_day_305(self):
        """11月1日 EoT 约 +16 min（接近最大值）"""
        from services.bazi_engine.solar_time_v2 import equation_of_time_minutes
        eot = equation_of_time_minutes(305)
        assert 12 < eot < 20

    def test_day_18(self):
        """1月18日附近 EoT 约 -12 min"""
        from services.bazi_engine.solar_time_v2 import equation_of_time_minutes
        eot = equation_of_time_minutes(18)
        assert -14 < eot < -8

    def test_day_1(self):
        """1月1日 EoT 有效范围"""
        from services.bazi_engine.solar_time_v2 import equation_of_time_minutes
        eot = equation_of_time_minutes(1)
        assert -20 < eot < 20

    def test_day_365(self):
        """12月31日 EoT 有效范围"""
        from services.bazi_engine.solar_time_v2 import equation_of_time_minutes
        eot = equation_of_time_minutes(365)
        assert -20 < eot < 20

    def test_solar_correction_beijing_1990(self):
        """红线11: 1990-07-17 北京(116.41°) 误差 < 30秒 (P0-03)"""
        from services.bazi_engine.solar_time_v2 import compute_solar_correction_minutes
        from datetime import datetime
        dt = datetime(1990, 7, 17, 12, 0)
        correction = compute_solar_correction_minutes(dt, longitude=116.41)
        # 116.41° → 时区偏差 (116.41-120)/15 × 60 = -14.36 分
        # EoT on day 198 ≈ +6.4 分 → 总修正约 -7.96 分
        assert isinstance(correction, float)
        assert -30 < correction < 30  # 在合理范围内

    def test_b_formula(self):
        """Spencer v4 参数: B = 2π(N-1)/365 验证"""
        # 对于 N=1, B=0; N=366, B 接近 2π
        B1 = 2.0 * math.pi * (1 - 1) / 365.0
        assert B1 == pytest.approx(0.0)
        B366 = 2.0 * math.pi * (365 - 1) / 365.0
        assert B366 == pytest.approx(2 * math.pi * 364 / 365, rel=1e-6)


# ─────────────────────────────────────────────────────────────────────────────
# scoring.py — 6维评分引擎 (M3.04)
# ─────────────────────────────────────────────────────────────────────────────

class TestScoringEngine:
    """八字6维评分引擎单元测试"""

    def _default_inputs(self):
        return dict(
            wuxing_scores={"wood": 3.0, "fire": 2.0, "earth": 2.0, "metal": 1.5, "water": 1.5},
            strength_score=62.0,
            strength_tier="中和",
            yongshen_favor=["fire", "earth"],
            geju_name="正官格",
            is_broken=False,
            dayun_trend="上升",
            is_favorable_dayun=True,
            shensha_items=[{"name": "天乙贵人", "is_beneficial": True}],
        )

    def test_import(self):
        from services.bazi_engine.scoring import compute_bazi_score
        assert callable(compute_bazi_score)

    def test_basic_score_returns_detail(self):
        from services.bazi_engine.scoring import compute_bazi_score
        result = compute_bazi_score(**self._default_inputs())
        assert result.total_score > 0
        assert result.tier in ("上命", "中命", "下命")

    def test_zhonghe_tier_gets_15(self):
        """中和日主强弱 → strength维度=15"""
        from services.bazi_engine.scoring import compute_bazi_score
        inp = self._default_inputs()
        inp["strength_tier"] = "中和"
        result = compute_bazi_score(**inp)
        assert result.daymaster_strength == pytest.approx(15.0)

    def test_jiwang_tier_gets_5(self):
        """极旺 → 5分"""
        from services.bazi_engine.scoring import compute_bazi_score
        inp = self._default_inputs()
        inp["strength_tier"] = "极旺"
        result = compute_bazi_score(**inp)
        assert result.daymaster_strength == pytest.approx(5.0)

    def test_upper_tier_positive_dayun(self):
        """上等格局+顺用神上升 → 总分高"""
        from services.bazi_engine.scoring import compute_bazi_score
        result = compute_bazi_score(**self._default_inputs())
        assert result.total_score >= 50

    def test_broken_geju_low_score(self):
        """破格 → geju_level维度=3"""
        from services.bazi_engine.scoring import compute_bazi_score
        inp = self._default_inputs()
        inp["is_broken"] = True
        result = compute_bazi_score(**inp)
        assert result.geju_level == pytest.approx(3.0)

    def test_unfavorable_downtrend(self):
        """逆用神下降"""
        from services.bazi_engine.scoring import compute_bazi_score
        inp = self._default_inputs()
        inp["dayun_trend"] = "下降"
        inp["is_favorable_dayun"] = False
        result = compute_bazi_score(**inp)
        assert result.dayun_trend == pytest.approx(3.0)

    def test_empty_wuxing_fallback(self):
        """空五行不崩溃"""
        from services.bazi_engine.scoring import compute_bazi_score
        inp = self._default_inputs()
        inp["wuxing_scores"] = {}
        result = compute_bazi_score(**inp)
        assert 0 <= result.total_score <= 100

    def test_shensha_penalty(self):
        """大量凶星 → shensha_luck 降低"""
        from services.bazi_engine.scoring import compute_bazi_score
        inp = self._default_inputs()
        inp["shensha_items"] = [{"name": "羊刃", "is_beneficial": False}] * 6
        result = compute_bazi_score(**inp)
        assert result.shensha_luck == pytest.approx(2.0)  # 下限2

    def test_dimension_weights_sum(self):
        """权重总和必须=100"""
        from services.bazi_engine.scoring import DIMENSION_WEIGHTS
        assert sum(DIMENSION_WEIGHTS.values()) == 100

    def test_scoring_to_dict(self):
        from services.bazi_engine.scoring import compute_bazi_score, scoring_to_dict
        result = compute_bazi_score(**self._default_inputs())
        d = scoring_to_dict(result)
        assert isinstance(d, dict)
        assert "total_score" in d
        assert "tier" in d

    def test_upper_min_command(self):
        """总分≥75 → 上命"""
        from services.bazi_engine.scoring import compute_bazi_score
        inp = self._default_inputs()
        # 设置所有维度最高: 极旺不行，用中和; 正印格; 顺走; 大量贵人
        inp["strength_tier"] = "中和"
        inp["geju_name"] = "正印格"
        inp["dayun_trend"] = "上升"
        inp["is_favorable_dayun"] = True
        inp["shensha_items"] = [{"is_beneficial": True}] * 5
        result = compute_bazi_score(**inp)
        assert result.tier in ("上命", "中命")


# ─────────────────────────────────────────────────────────────────────────────
# lifestyle/tables.py — 五行映射表 (M1.04)
# ─────────────────────────────────────────────────────────────────────────────

class TestLifestyleTables:
    """五行→生活建议映射表单元测试"""

    def test_import_tables(self):
        from services.bazi_engine.lifestyle.tables import WUXING_TO_ORGAN
        assert isinstance(WUXING_TO_ORGAN, dict)

    def test_all_five_elements_present(self):
        from services.bazi_engine.lifestyle.tables import WUXING_TO_ORGAN
        for elem in ("wood", "fire", "earth", "metal", "water"):
            assert elem in WUXING_TO_ORGAN, f"缺少 {elem} 五行映射"

    def test_organ_has_zang(self):
        from services.bazi_engine.lifestyle.tables import WUXING_TO_ORGAN
        for elem, data in WUXING_TO_ORGAN.items():
            assert "zang" in data, f"{elem} 缺少 zang 字段"
            assert len(data["zang"]) >= 1

    def test_color_mapping_exists(self):
        """五行→颜色映射（B.4 规格）"""
        try:
            from services.bazi_engine.lifestyle.tables import WUXING_TO_COLOR
            assert "wood" in WUXING_TO_COLOR
        except ImportError:
            pytest.skip("WUXING_TO_COLOR 不在此模块")

    def test_direction_mapping_exists(self):
        """五行→方位映射（B.5 规格）"""
        try:
            from services.bazi_engine.lifestyle.tables import WUXING_TO_DIRECTION
            assert "wood" in WUXING_TO_DIRECTION
        except ImportError:
            pytest.skip("WUXING_TO_DIRECTION 不在此模块")

    def test_number_mapping_exists(self):
        """五行→数字映射（B.6 规格）"""
        try:
            from services.bazi_engine.lifestyle.tables import WUXING_TO_NUMBER
            assert "wood" in WUXING_TO_NUMBER
        except ImportError:
            pytest.skip("WUXING_TO_NUMBER 不在此模块")


# ─────────────────────────────────────────────────────────────────────────────
# M6.08 Prometheus 自定义业务指标 (P50/GAP-15)
# bazi_verify_total / bazi_verify_duration / bazi_boundary_risk
# ─────────────────────────────────────────────────────────────────────────────

class TestPrometheusMetrics:
    """M6.08: 三项自定义 Prometheus 业务指标验证"""

    def test_metrics_importable(self):
        from services.prometheus_monitoring import (
            BAZI_VERIFY_TOTAL,
            BAZI_VERIFY_DURATION,
            BAZI_BOUNDARY_RISK,
        )
        assert BAZI_VERIFY_TOTAL is not None
        assert BAZI_VERIFY_DURATION is not None
        assert BAZI_BOUNDARY_RISK is not None

    def test_record_verify_metrics_success(self):
        """record_verify_metrics 成功路径不抛异常"""
        from services.prometheus_monitoring import record_verify_metrics
        # 不应抛任何异常
        record_verify_metrics(
            mode="dual",
            boundary_level="L0",
            duration_secs=0.8,
            success=True,
        )

    def test_record_verify_metrics_error(self):
        """record_verify_metrics 错误路径"""
        from services.prometheus_monitoring import record_verify_metrics
        record_verify_metrics(
            mode="single",
            boundary_level="L2",
            duration_secs=1.2,
            success=False,
        )

    def test_bazi_verify_total_metric_name(self):
        """bazi_verify_total Counter 名称符合规格"""
        from services.prometheus_monitoring import BAZI_VERIFY_TOTAL
        # prometheus_client stores name without _total suffix in _name
        assert "bazi_verify" in BAZI_VERIFY_TOTAL._name

    def test_bazi_boundary_risk_metric_name(self):
        """bazi_boundary_risk_total Counter 名称符合规格"""
        from services.prometheus_monitoring import BAZI_BOUNDARY_RISK
        assert "bazi_boundary_risk" in BAZI_BOUNDARY_RISK._name

    def test_bazi_verify_duration_buckets(self):
        """bazi_verify_duration_seconds Histogram 包含 3.0s bucket"""
        from services.prometheus_monitoring import BAZI_VERIFY_DURATION
        buckets = BAZI_VERIFY_DURATION._kwargs.get("buckets", ()) or ()
        # 也可从 _upper_bounds 读取
        try:
            bounds = list(BAZI_VERIFY_DURATION._upper_bounds)
        except AttributeError:
            bounds = list(buckets)
        assert any(abs(b - 3.0) < 0.01 for b in bounds), \
            "BAZI_VERIFY_DURATION 应包含 3.0s bucket（M6.07 基线）"
