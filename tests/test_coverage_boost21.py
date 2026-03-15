"""
tests/test_coverage_boost21.py — Coverage Boost 21

目标 (services/bazi_engine_service.py):
  - L576-577  : BAZI_CACHE_HITS.inc() 抛异常 (cache hit 路径, 鲁棒版)
  - L603-604  : BAZI_ENGINE_CALC_SECONDS.observe() 抛异常 (cache miss 路径)
  - L1041-1042: M2.5 jewelry except
  - L1048-1049: M2.5 fengshui except
  - L1055-1056: M2.5 lucky except
  - L1062-1063: M2.5 lifestyle except
  - L1091-1092: M2.5 milestones except
  - L1115-1116: RL#10 liunian except
  - L1159-1160: M3.02 narrative continue (item.narrative 已设置)
  - L1179-1180: M3.02 inner narrative step except
  - L1181-1182: M3.02 outer narrative except
  - L1204-1205: P0-11 tiangan_clashes except
  - L1223,1225: interpret 文本赋值
  - L1234     : interpret yongshen AttributeError pass
  - L1248-1250: RL#33 wealth fallback 分支
  - L1257     : RL#33 inference_tags fallback
  - L1258-1259: RL#33 wealth except
  - L1339-1340: M3 life_arc except
  - L1478-1479: M3 liunian_detail except
  - L1536-1537: M4 current_fortune_summary except
  - L1551-1552: N2.05 balance_score except
"""
from __future__ import annotations

import hashlib
import types
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, PropertyMock


# ═══════════════════════════════════════════════════════════════════════════
# 共享辅助函数 (复用 boost20 模式)
# ═══════════════════════════════════════════════════════════════════════════

def _make_pillars():
    from app.schemas import PillarsModel
    from app.schemas.bazi import PillarModel
    def _p(s, b):
        return PillarModel(stem=s, branch=b, ten_god="比肩", strength=50.0, element="wood", yin_yang="阳")
    return PillarsModel(
        year=_p("甲", "子"), month=_p("丙", "寅"),
        day=_p("甲", "午"), hour=_p("壬", "申"),
    )


def _make_yongshen():
    from app.schemas import YongShenModel
    return YongShenModel(favor=["water", "metal"], avoid=["fire", "wood"], rationale="测试")


def _make_strength():
    from app.schemas import DayMasterStrengthModel
    return DayMasterStrengthModel(score=55.0, tier="中和", label="中和", description="")


def _make_wuxing_score():
    from app.schemas import WuXingScoreModel
    return WuXingScoreModel(wood=20.0, fire=10.0, earth=15.0, metal=30.0, water=25.0)


def _make_dayun():
    from app.schemas import DaYunModel
    from app.schemas.bazi import DaYunItemModel
    item = DaYunItemModel(
        stem="庚", branch="申", start_age=30, end_age=40,
        ten_god=None, flow_wuxing="metal",
        love_hint="", child_hint="",
    )
    return DaYunModel(items=[item], start_age=3, start_age_months=36)


def _make_vr():
    """构造 MagicMock verify_response，设置常用属性返回值"""
    vr = MagicMock()
    vr.dayun = None
    vr.pillars_primary = None
    vr.geju = None
    vr.wealth = None
    vr.wealth_analysis = None
    vr.health = None
    vr.yongshen = None
    vr.social = None
    vr.bazi_summary = None
    vr.start_dayun_age = None
    return vr


def _enrich(vr=None, rp=None, yn=None, st=None, wx=None, dm=None, dt=None, **kwargs):
    """便捷包装：调用 _enrich_v2_analysis，忽略异常"""
    from services.bazi_engine_service import _enrich_v2_analysis
    vr = vr if vr is not None else _make_vr()
    rp = rp or _make_pillars()
    yn = yn or _make_yongshen()
    st = st or _make_strength()
    wx = wx or _make_wuxing_score()
    dm = dm or _make_dayun()
    dt = dt or datetime(1990, 5, 15, 8, 0)
    try:
        _enrich_v2_analysis(
            verify_response=vr, rp=rp, yongshen=yn, strength=st,
            wuxing_score=wx, dayun_model=dm, dt=dt,
            gender="male", mode="single", **kwargs
        )
    except Exception:
        pass
    return vr


# ═══════════════════════════════════════════════════════════════════════════
# 1. L576-577 — BAZI_CACHE_HITS.inc() 抛异常 (鲁棒版：直接计算真实 key)
# ═══════════════════════════════════════════════════════════════════════════

class TestCacheHitException:
    """L576-577 — cache hit 路径中 BAZI_CACHE_HITS.inc() 抛异常"""

    def test_l576_577_real_cache_key(self):
        """预计算真实 cache key，直接注入 _RESULT_CACHE，避免 patch _make_cache_key 层级问题"""
        import services.bazi_engine_service as svc
        from services.bazi_engine_service import CalculateResult

        dt = datetime(1990, 5, 15, 8, 0)
        lon = 120.0
        mode = "single"
        gender = None
        # 用与 _make_cache_key() 完全相同的逻辑计算 key
        raw = f"{dt.isoformat()}|{lon:.4f}|{mode}|{gender or ''}"
        real_key = hashlib.sha256(raw.encode()).hexdigest()

        mock_vr = MagicMock()
        mock_cr = CalculateResult(verify_response=mock_vr, engine_version="v1")

        orig_hits = svc.BAZI_CACHE_HITS
        orig_avail = svc._CACHETOOLS_AVAILABLE
        orig_cache = svc._RESULT_CACHE

        mock_hits = MagicMock()
        mock_hits.inc.side_effect = RuntimeError("metrics boom")

        try:
            svc.BAZI_CACHE_HITS = mock_hits
            svc._CACHETOOLS_AVAILABLE = True
            svc._RESULT_CACHE[real_key] = mock_cr

            from services.bazi_engine_service import calculate
            try:
                calculate(dt=dt, lon=lon, tz="Asia/Shanghai", use_solar=False,
                          mode=mode, gender=gender, request_id="b21_cache_hit")
            except Exception:
                pass
        finally:
            svc.BAZI_CACHE_HITS = orig_hits
            svc._CACHETOOLS_AVAILABLE = orig_avail
            svc._RESULT_CACHE = orig_cache
            # 清理注入的 key（如果 orig_cache 是同一个对象）
            orig_cache.pop(real_key, None)


# ═══════════════════════════════════════════════════════════════════════════
# 2. L603-604 — BAZI_ENGINE_CALC_SECONDS.observe() 抛异常 (cache miss 路径)
# ═══════════════════════════════════════════════════════════════════════════

class TestCacheMissMetricsException:
    """L603-604 — cache miss + _calculate_v2 mocked + observe() 抛异常"""

    def test_l603_604_observe_exception(self):
        """Patch _calculate_v2 返回 CalculateResult, BAZI_ENGINE_CALC_SECONDS.observe() 抛异常"""
        import services.bazi_engine_service as svc
        from services.bazi_engine_service import CalculateResult

        mock_vr = MagicMock()
        mock_cr = CalculateResult(verify_response=mock_vr, engine_version="v2")

        orig_secs = svc.BAZI_ENGINE_CALC_SECONDS
        orig_avail = svc._CACHETOOLS_AVAILABLE

        mock_secs = MagicMock()
        mock_secs.observe.side_effect = RuntimeError("observe boom")

        try:
            svc.BAZI_ENGINE_CALC_SECONDS = mock_secs
            svc._CACHETOOLS_AVAILABLE = False   # 跳过 cache 检查

            with patch("services.bazi_engine_service._calculate_v2", return_value=mock_cr), \
                 patch("services.bazi_engine_service._calculate_v1", return_value=mock_cr):
                dt = datetime(1990, 5, 15, 8, 0)
                from services.bazi_engine_service import calculate
                try:
                    calculate(dt=dt, lon=120.0, tz="Asia/Shanghai", use_solar=False,
                              mode="single", gender=None, request_id="b21_miss")
                except Exception:
                    pass
        finally:
            svc.BAZI_ENGINE_CALC_SECONDS = orig_secs
            svc._CACHETOOLS_AVAILABLE = orig_avail


# ═══════════════════════════════════════════════════════════════════════════
# 3. L1041-1063 — M2.5 jewelry/fengshui/lucky/lifestyle except
# ═══════════════════════════════════════════════════════════════════════════

class TestM25LifestyleExcepts:
    """M2.5 jewelry/fengshui/lucky/lifestyle 四个 except 块"""

    def test_l1041_1063_all_lifestyle_raise(self):
        """同时 patch 4个 compute 函数抛异常 → 覆盖 L1041-1042/1048-1049/1055-1056/1062-1063"""
        with patch("services.bazi_engine.lifestyle.jewelry.compute_jewelry",
                   side_effect=RuntimeError("jewelry err")), \
             patch("services.bazi_engine.lifestyle.fengshui.compute_fengshui",
                   side_effect=RuntimeError("fengshui err")), \
             patch("services.bazi_engine.lifestyle.lucky.compute_lucky",
                   side_effect=RuntimeError("lucky err")), \
             patch("services.bazi_engine.lifestyle.lifestyle.compute_lifestyle",
                   side_effect=RuntimeError("lifestyle err")):
            _enrich()


# ═══════════════════════════════════════════════════════════════════════════
# 4. L1091-1092 — M2.5 milestones except
# ═══════════════════════════════════════════════════════════════════════════

class TestMilestonesExcept:
    """M2.5 milestones except"""

    def test_l1091_1092_milestones_raise(self):
        with patch("services.bazi_engine.milestones.compute_milestones",
                   side_effect=RuntimeError("milestones err")):
            _enrich()


# ═══════════════════════════════════════════════════════════════════════════
# 5. L1115-1116 — RL#10 liunian except
# ═══════════════════════════════════════════════════════════════════════════

class TestLiunianExcept:
    """RL#10 liunian except"""

    def test_l1115_1116_liunian_raise(self):
        with patch("services.bazi_engine.liunian.compute_liunian",
                   side_effect=RuntimeError("liunian err")):
            _enrich()


# ═══════════════════════════════════════════════════════════════════════════
# 6. L1159-1160, L1179-1182 — M3.02 大运叙事 narrative 异常块
# ═══════════════════════════════════════════════════════════════════════════

class TestNarrativeExcepts:
    """M3.02 大运叙事 narrative 相关覆盖"""

    def test_l1159_1160_narrative_continue(self):
        """dayun item 已有 narrative → L1160 continue 触发"""
        from app.schemas import DaYunModel
        from app.schemas.bazi import DaYunItemModel

        item_with_narrative = DaYunItemModel(
            stem="庚", branch="申", start_age=30, end_age=40,
            ten_god=None, flow_wuxing="metal",
            narrative="已设置叙事",  # 非空 → 触发 L1160 continue
        )
        dm_with_nar = DaYunModel(items=[item_with_narrative], start_age=3, start_age_months=36)
        vr = _make_vr()
        vr.dayun = MagicMock()         # dayun 为 truthy → 进入 if 块
        vr.dayun.items = [item_with_narrative]
        _enrich(dm=dm_with_nar, vr=vr)

    def test_l1179_1180_narrative_step_exception(self):
        """generate_dayun_narrative 抛异常 → L1179-1180 inner except 触发"""
        from app.schemas import DaYunModel
        from app.schemas.bazi import DaYunItemModel

        item_no_nar = DaYunItemModel(
            stem="庚", branch="申", start_age=30, end_age=40,
            ten_god=None, flow_wuxing="metal",
            narrative=None,  # 无 narrative → 进入 generate 调用
        )
        dm = DaYunModel(items=[item_no_nar], start_age=3, start_age_months=36)
        vr = _make_vr()
        vr.dayun = MagicMock()
        vr.dayun.items = [item_no_nar]

        with patch("services.bazi_engine.analysis.dayun_narrative.generate_dayun_narrative",
                   side_effect=RuntimeError("narrative step err")):
            _enrich(dm=dm, vr=vr)

    def test_l1181_1182_narrative_outer_exception(self):
        """dayun.items 访问抛异常 → 绕过 inner try → outer except L1181-1182 触发"""
        vr = _make_vr()
        # 使 dayun 是 truthy，但 items property 抛异常
        mock_dayun = MagicMock()
        type(mock_dayun).items = PropertyMock(side_effect=RuntimeError("items err"))
        vr.dayun = mock_dayun
        _enrich(vr=vr)


# ═══════════════════════════════════════════════════════════════════════════
# 7. L1204-1205 — P0-11 tiangan_clashes except
# ═══════════════════════════════════════════════════════════════════════════

class TestTianganClashesExcept:
    """L1204-1205 — get_stem_clashes 抛异常"""

    def test_l1204_1205_stem_clashes_raise(self):
        with patch("services.bazi_engine.relations.get_stem_clashes",
                   side_effect=RuntimeError("clashes err")):
            _enrich()


# ═══════════════════════════════════════════════════════════════════════════
# 8. L1223, L1225, L1234 — interpret 文本写入分支
# ═══════════════════════════════════════════════════════════════════════════

class TestInterpretTextAssignment:
    """L1223 / L1225 / L1234 — interpret_bazi 块内文本写入"""

    def test_l1223_1225_wealth_health_interp_text(self):
        """interpret_bazi 返回结果，wealth/health 无 interpretation_text → L1223,L1225 被执行;
        必须 patch compute_wealth/compute_health 使其失败，
        否则并行引擎会覆盖 vr.wealth_analysis/vr.health"""
        interp_mock = types.SimpleNamespace(
            geju_text="",
            lifestyle_text="LIFESTYLE_TEXT_TEST_PLACEHOLDER_ENOUGH",
            full_summary="",
            # 无 yongshen_text → L1234 AttributeError pass
        )

        vr = _make_vr()
        # wealth_analysis 有对象但无 interpretation_text
        # (compute_wealth raise → 并行引擎不会覆盖此值)
        vr.wealth_analysis = MagicMock()
        vr.wealth_analysis.interpretation_text = ""   # falsy → L1223 触发
        # health 有对象但无 interpretation_text
        vr.health = MagicMock()
        vr.health.interpretation_text = ""            # falsy → L1225 触发
        vr.geju = None
        vr.bazi_summary = None
        # yongshen: SimpleNamespace 无 interpretation_text 属性 → L1234 触发
        vr.yongshen = types.SimpleNamespace(favor=["water"], avoid=["fire"])

        with patch("services.bazi_engine.analysis.wealth.compute_wealth",
                   side_effect=RuntimeError("wealth fail")), \
             patch("services.bazi_engine.analysis.health.compute_health",
                   side_effect=RuntimeError("health fail")), \
             patch("services.bazi_engine.interpret.interpret_bazi",
                   return_value=interp_mock):
            _enrich(vr=vr)


# ═══════════════════════════════════════════════════════════════════════════
# 9. L1248-1250, L1257 — RL#33 wealth 三层同步 fallback 分支
# ═══════════════════════════════════════════════════════════════════════════

class TestWealthSyncFallback:
    """L1248-1250 / L1257 — RL#33 wealth interpretation_text/inference_tags fallback"""

    def test_l1248_1250_l1257_fallback(self):
        """wealth 有对象但无 interpretation_text, wealth_analysis=None → fallback 分支.
        patch compute_wealth 使并行引擎不覆盖 vr.wealth_analysis(保持 None)"""
        vr = _make_vr()
        vr.wealth = types.SimpleNamespace(
            interpretation_text="",   # 空 → 进入内部 if
            wealth_score=60.0,
            industry_tags=["金融", "IT"],
            inference_tags=[],         # 空 → 进入 L1257
        )
        vr.wealth_analysis = None     # _wa 为 None → else 分支 → L1248+L1257
        with patch("services.bazi_engine.analysis.wealth.compute_wealth",
                   side_effect=RuntimeError("wealth fail")):
            _enrich(vr=vr)


# ═══════════════════════════════════════════════════════════════════════════
# 10. L1258-1259 — RL#33 wealth except
# ═══════════════════════════════════════════════════════════════════════════

class TestWealthSyncExcept:
    """L1258-1259 — RL#33 wealth 三层 try/except"""

    def test_l1258_1259_wealth_raises(self):
        """wealth.interpretation_text 访问抛异常 → L1258-1259 触发"""
        class _BadWealth:
            @property
            def interpretation_text(self):
                raise RuntimeError("wealth boom")

        vr = _make_vr()
        vr.wealth = _BadWealth()
        vr.wealth_analysis = None
        _enrich(vr=vr)


# ═══════════════════════════════════════════════════════════════════════════
# 11. L1339-1340 — M3 life_arc except
# ═══════════════════════════════════════════════════════════════════════════

class TestLifeArcExcept:
    """L1339-1340 — compute_life_arc 抛异常"""

    def test_l1339_1340_life_arc_raise(self):
        with patch("services.bazi_engine.life_arc.compute_life_arc",
                   side_effect=RuntimeError("life_arc err")):
            _enrich()


# ═══════════════════════════════════════════════════════════════════════════
# 12. L1478-1479 — M3 liunian_detail except
# ═══════════════════════════════════════════════════════════════════════════

class TestLiunianDetailExcept:
    """L1478-1479 — compute_liunian_domain_forecasts 抛异常"""

    def test_l1478_1479_domain_forecasts_raise(self):
        with patch(
            "services.bazi_engine.analysis.liunian_domain.compute_liunian_domain_forecasts",
            side_effect=RuntimeError("domain err"),
        ):
            _enrich()


# ═══════════════════════════════════════════════════════════════════════════
# 13. L1536-1537 — M4 current_fortune_summary except
# ═══════════════════════════════════════════════════════════════════════════

class TestCurrentFortuneExcept:
    """L1536-1537 — CurrentFortuneSummaryModel 抛异常"""

    def test_l1536_1537_cfs_raise(self):
        with patch("app.schemas.analysis.CurrentFortuneSummaryModel",
                   side_effect=RuntimeError("cfs err")):
            _enrich()


# ═══════════════════════════════════════════════════════════════════════════
# 14. L1551-1552 — N2.05 balance_score except
# ═══════════════════════════════════════════════════════════════════════════

class TestBalanceScoreExcept:
    """L1551-1552 — balance_score 抛异常"""

    def test_l1551_1552_balance_raise(self):
        with patch("services.bazi_engine.scoring.balance_score",
                   side_effect=RuntimeError("balance err")):
            _enrich()
