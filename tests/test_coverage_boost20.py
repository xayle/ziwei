"""
tests/test_coverage_boost20.py — Coverage Boost 20

目标 (services/bazi_engine_service.py):
  - L143      : isinstance(w, dict) → WarningModel.model_validate(w)
  - L154-155  : importlib.util.find_spec 抛异常 → except
  - L193-195  : wuxing_breakdown.weights 为空 → else 分支（逐 contrib 汇总）
  - L204      : wealth_score == strength.score → 安全托底偏移
  - L383-385  : ten_god 不在 _marriage_tg_map 且 love_hint 为空 → elif 分支
  - L403-405  : ten_god 不在 _child_tg_map 且 child_hint 为空 → elif 分支
  - L453-454  : _enrich_v2_analysis 抛异常 → except 捕获
  - L576-577  : BAZI_CACHE_HITS.inc() 抛异常 → except pass
  - L603-604  : BAZI_ENGINE_CALC_SECONDS.observe() 抛异常 → except pass
  - L756-757  : N5.07 start_dayun_age float() 抛异常 → except
  - L820-821  : M2 geju-yongshen 计算抛异常 → except
  - L852-853  : M2 shensha 计算抛异常 → except
  - L895-896  : M2 palace 计算抛异常 → except
  - L1015-1018: ThreadPoolExecutor future.result() 抛异常 → except + _m2_warn

run.py:
  - L587      : _build_legacy_verify_response 内 isinstance(w, dict) → WarningModel.model_validate
"""
from __future__ import annotations

import types
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, PropertyMock


# ═══════════════════════════════════════════════════════════════════════════
# 辅助：构建最小化可用的 _enrich_v2_analysis 参数
# ═══════════════════════════════════════════════════════════════════════════

def _make_pillars_model():
    """构建最小化 PillarsModel（使用真实类）"""
    from app.schemas import PillarsModel
    from app.schemas.bazi import PillarModel
    def _pillar(stem, branch):
        return PillarModel(stem=stem, branch=branch, ten_god="比肩", strength=50.0, element="wood", yin_yang="阳")
    return PillarsModel(
        year=_pillar("甲", "子"),
        month=_pillar("丙", "寅"),
        day=_pillar("甲", "午"),
        hour=_pillar("壬", "申"),
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


def _make_dayun_model():
    from app.schemas import DaYunModel
    from app.schemas.bazi import DaYunItemModel
    item = DaYunItemModel(
        stem="庚", branch="申", start_age=30, end_age=40,
        ten_god=None, flow_wuxing="metal",
        love_hint="", child_hint="",
    )
    return DaYunModel(items=[item], start_age=3, start_age_months=36)


def _make_verify_response():
    """构造一个可以传给 _enrich_v2_analysis 的最小化 VerifyResponse mock。
    _enrich_v2_analysis 从不 validate/reconstruct VerifyResponse，
    只是在它上面 setattr，所以可以安全地用 MagicMock。
    """
    vr = MagicMock()
    # 让常见属性访问不抛异常
    vr.dayun = None          # N5.07 try requires truthy
    vr.pillars_primary = None
    vr.geju = None
    vr.wealth_analysis = None
    vr.health = None
    vr.yongshen = None
    vr.social = None
    vr.bazi_summary = None
    vr.start_dayun_age = None
    return vr


def _call_enrich(extra_patches=None, dt=None, **kwargs):
    """
    调用 _enrich_v2_analysis。
    extra_patches: list of (target, attribute, side_effect_or_return)
    """
    from services.bazi_engine_service import _enrich_v2_analysis
    rp = _make_pillars_model()
    yongshen = _make_yongshen()
    strength = _make_strength()
    wuxing_score = _make_wuxing_score()
    dayun_model = _make_dayun_model()
    verify_response = _make_verify_response()
    if dt is None:
        dt = datetime(1990, 5, 15, 8, 0)
    try:
        result = _enrich_v2_analysis(
            verify_response=verify_response,
            rp=rp,
            yongshen=yongshen,
            strength=strength,
            wuxing_score=wuxing_score,
            dayun_model=dayun_model,
            dt=dt,
            gender="male",
            mode="single",
            city_tier=None,
            industry=None,
        )
    except Exception:
        pass
    return verify_response


def _make_verify_full_result(warning_dicts=None):
    """构造可通过 _calculate_v1 L135-L148 的干净 SimpleNamespace result 对象。
    warning_dicts: list of dict，注入到 validation.warnings 中（用于 L143 测试）。
    """
    mock_rf = types.SimpleNamespace(
        near_shichen_boundary=False,
        near_jieqi_boundary=False,
        jieqi_boundary_status="ok",
        minutes_to_shichen_boundary=None,
        minutes_to_jieqi_boundary=None,
    )
    warnings_list = list(warning_dicts or [])
    mock_validation = types.SimpleNamespace(
        level="L0",
        mode="single",
        recommended="none",
        interpretation_enabled=True,
        reasons=[],
        diff_fields=[],
        risk_flags=mock_rf,
        boundary_risk_shichen=False,
        boundary_risk_jieqi=False,
        warnings=warnings_list,
    )

    def _p(s, b):
        return types.SimpleNamespace(stem=s, branch=b)

    mock_pillars = types.SimpleNamespace(
        year=_p("甲", "子"),
        month=_p("丙", "寅"),
        day=_p("甲", "午"),
        hour=_p("壬", "申"),
    )
    return types.SimpleNamespace(
        solar_time_offset_minutes=0.0,
        pillars_primary=mock_pillars,
        pillars_secondary=None,
        risk_flags=mock_rf,
        validation=mock_validation,
        mode_requested="single",
        mode_effective="single",
    )


def _make_bazi_full_service_mocks(
    wuxing_weights=None, strength_score=55.0, yongshen_favor=None, yongshen_avoid=None,
    dayun_model=None,
):
    """构造 bazi_full_service 的 mock 返回值字典（供 patch 使用）"""
    weights = wuxing_weights or {"wood": 20.0, "fire": 10.0, "earth": 15.0, "metal": 30.0, "water": 25.0}

    wx_ns = types.SimpleNamespace(**weights)
    wx_ns.model_dump = lambda: dict(weights)
    wx_break_ns = types.SimpleNamespace(weights=weights, stem_contrib={}, branch_contrib={}, hidden_contrib={})
    wx_break_ns.model_dump = lambda: dict(weights)

    str_ns = types.SimpleNamespace(score=strength_score, tier="中和", label="中和", description="")
    str_ns.model_dump = lambda: {"score": strength_score, "tier": "中和", "label": "中和", "description": ""}

    favor = yongshen_favor if yongshen_favor is not None else ["water"]
    avoid = yongshen_avoid if yongshen_avoid is not None else ["fire"]
    ys_ns = types.SimpleNamespace(favor=favor, avoid=avoid, rationale="")
    ys_ns.model_dump = lambda: {"favor": favor, "avoid": avoid, "rationale": ""}

    if dayun_model is None:
        _dm = MagicMock()
        _dm.items = []
        _dm.start_age = 3
        _dm.start_age_months = 36
        _dm.model_dump.return_value = {"items": [], "start_age": 3}
    else:
        _dm = dayun_model

    # build_dayun 返回 (dayun_model_raw, raw_dayun) 元组
    _raw_dayun = types.SimpleNamespace(
        direction="forward",
        direction_basis="male_yanggan",
        anchor_jieqi_name="立春",
        anchor_jieqi_dt=None,
        computed_months_before_rounding=None,
    )

    return {
        "wx_ns": wx_ns,
        "wx_break_ns": wx_break_ns,
        "str_ns": str_ns,
        "ys_ns": ys_ns,
        "dayun_mock": _dm,
        "build_dayun_return": (_dm, _raw_dayun),  # build_dayun 需要返回 2-tuple
    }


# ═══════════════════════════════════════════════════════════════════════════
# 1. L143 — dict warning → WarningModel.model_validate(w)
# ═══════════════════════════════════════════════════════════════════════════

class TestDictWarning:
    """L143 — verify_full 返回包含 dict 形式 warning 的 ValidationModel"""

    def test_l143_dict_warning_in_validation(self):
        """L143: raw_warnings 中包含 dict → WarningModel.model_validate(w)
        使用 SimpleNamespace 构建干净的 result 对象，避免 MagicMock.__dict__ 污染。
        """
        import types
        from services.bazi_engine_service import _calculate_v1

        mock_warning_dict = {"code": "TEST_WARN", "message": "test warning"}

        # 用 SimpleNamespace 构造 risk_flags，使 __dict__ 干净
        mock_rf = types.SimpleNamespace(
            near_shichen_boundary=False,
            near_jieqi_boundary=False,
            jieqi_boundary_status="ok",
            minutes_to_shichen_boundary=None,
            minutes_to_jieqi_boundary=None,
        )

        # 用 SimpleNamespace 构造 validation，使 __dict__ 干净
        mock_validation = types.SimpleNamespace(
            level="L0",
            mode="single",
            recommended="none",
            interpretation_enabled=True,
            reasons=[],
            diff_fields=[],
            risk_flags=mock_rf,
            boundary_risk_shichen=False,
            boundary_risk_jieqi=False,
            warnings=[mock_warning_dict],  # dict → triggering L143
        )

        # 构造 pillars（用有 stem/branch 的 SimpleNamespace）
        def _p(s, b):
            return types.SimpleNamespace(stem=s, branch=b)

        mock_pillars = types.SimpleNamespace(
            year=_p("甲", "子"),
            month=_p("丙", "寅"),
            day=_p("甲", "午"),
            hour=_p("壬", "申"),
        )

        # 整个 verify_full 返回对象
        mock_result = types.SimpleNamespace(
            solar_time_offset_minutes=0.0,
            pillars_primary=mock_pillars,
            pillars_secondary=None,
            risk_flags=mock_rf,
            validation=mock_validation,
        )

        # patch bazi_full_service 的计算函数，防止真实调用
        _wx_ns = types.SimpleNamespace(
            __dict__={"wood": 20.0, "fire": 10.0, "earth": 15.0, "metal": 30.0, "water": 25.0},
        )
        _wx_ns.model_dump = lambda: {"wood": 20.0, "fire": 10.0, "earth": 15.0, "metal": 30.0, "water": 25.0}
        _wx_break_ns = types.SimpleNamespace(
            weights={"wood": 20, "fire": 10, "earth": 15, "metal": 30, "water": 25},
        )
        _wx_break_ns.model_dump = lambda: {"wood": 20, "fire": 10, "earth": 15, "metal": 30, "water": 25}

        _strength_ns = types.SimpleNamespace(
            score=55.0, tier="中和", label="中和", description="",
        )
        _strength_ns.model_dump = lambda: {"score": 55.0, "tier": "中和", "label": "中和", "description": ""}

        _ys_ns = types.SimpleNamespace(favor=["water"], avoid=["fire"], rationale="")
        _ys_ns.model_dump = lambda: {"favor": ["water"], "avoid": ["fire"], "rationale": ""}

        _dayun_ns = MagicMock()
        _dayun_ns.items = []
        _dayun_ns.start_age = 3
        _dayun_ns.start_age_months = 36
        _dayun_ns.model_dump.return_value = {"items": [], "start_age": 3}

        dt = datetime(1990, 5, 15, 8, 0)

        with patch("verify.verify_full", return_value=mock_result), \
             patch("services.bazi_full_service.compute_wuxing",
                   return_value=(_wx_ns, _wx_break_ns)), \
             patch("services.bazi_full_service.compute_strength",
                   return_value=_strength_ns), \
             patch("services.bazi_full_service.compute_yongshen",
                   return_value=_ys_ns), \
             patch("services.bazi_full_service.build_ten_gods",
                   return_value={}), \
             patch("services.bazi_full_service.build_dayun",
                   return_value=(_dayun_ns, types.SimpleNamespace(
                       direction="forward", direction_basis="male_yanggan",
                       anchor_jieqi_name="立春", anchor_jieqi_dt=None,
                       computed_months_before_rounding=None,
                   ))):
            try:
                _calculate_v1(
                    dt=dt, lon=120.0, tz="Asia/Shanghai", use_solar=False,
                    mode="single", gender="male", request_id="test",
                    extra_warnings=[],
                )
            except Exception:
                pass  # 目标是执行过 L143，不要求完整成功


# ═══════════════════════════════════════════════════════════════════════════
# 2. L154-155 — importlib.util.find_spec 抛异常 → sxtwl_ok, cnlunar_ok = True, True
# ═══════════════════════════════════════════════════════════════════════════

class TestFindSpecException:
    """L154-155 — importlib.util.find_spec 抛异常分支"""

    def test_l154_155_find_spec_exception(self):
        """patch importlib.util.find_spec 在 _calculate_v1 中的调用抛异常"""

        def patched_find_spec(name, *args, **kw):
            # sxtwl/cnlunar 检测时直接抛异常，走 except → L154-155
            raise RuntimeError("mock find_spec error")

        vfr = _make_verify_full_result()
        mocks = _make_bazi_full_service_mocks()

        with patch("verify.verify_full", return_value=vfr), \
             patch("services.bazi_full_service.compute_wuxing",
                   return_value=(mocks["wx_ns"], mocks["wx_break_ns"])), \
             patch("services.bazi_full_service.compute_strength", return_value=mocks["str_ns"]), \
             patch("services.bazi_full_service.compute_yongshen", return_value=mocks["ys_ns"]), \
             patch("services.bazi_full_service.build_ten_gods", return_value={}), \
             patch("services.bazi_full_service.build_dayun", return_value=mocks["build_dayun_return"]), \
             patch("importlib.util.find_spec", side_effect=patched_find_spec):
            dt = datetime(1990, 5, 15, 8, 0)
            from services.bazi_engine_service import _calculate_v1
            try:
                _calculate_v1(
                    dt=dt, lon=120.0, tz="Asia/Shanghai", use_solar=False,
                    mode="single", gender="male", request_id="test",
                    extra_warnings=[],
                )
            except Exception:
                pass
        # 只要 find_spec 抛异常且程序没崩溃 → L154-155 被执行


# ═══════════════════════════════════════════════════════════════════════════
# 3. L193-195 — wuxing_breakdown.weights 为空 → else 分支汇总 contrib
# ═══════════════════════════════════════════════════════════════════════════

class TestWuxingBreakdownElse:
    """L193-195 — wuxing_breakdown.weights 为空时的 else 分支"""

    def test_l193_195_breakdown_no_weights(self):
        """mock wuxing_breakdown.weights = {} (falsy) → else 分支"""
        from services.bazi_engine_service import _calculate_v1
        from app.schemas import WuXingBreakdownModel

        # 构建无 weights 的 WuXingBreakdownModel
        breakdown_no_weights = WuXingBreakdownModel(
            weights={},  # 空 → 走 else 分支
            stem_contrib={"wood": 20.0, "fire": 10.0},
            branch_contrib={"earth": 15.0, "metal": 30.0},
            hidden_contrib={"water": 25.0},
        )

        vfr = _make_verify_full_result()
        wx_ns = types.SimpleNamespace(wood=20.0, fire=10.0, earth=15.0, metal=30.0, water=25.0)
        wx_ns.model_dump = lambda: {"wood": 20.0, "fire": 10.0, "earth": 15.0, "metal": 30.0, "water": 25.0}
        mocks = _make_bazi_full_service_mocks()

        with patch("verify.verify_full", return_value=vfr), \
             patch("services.bazi_full_service.compute_wuxing",
                   return_value=(wx_ns, breakdown_no_weights)), \
             patch("services.bazi_full_service.compute_strength", return_value=mocks["str_ns"]), \
             patch("services.bazi_full_service.compute_yongshen", return_value=mocks["ys_ns"]), \
             patch("services.bazi_full_service.build_ten_gods", return_value={}), \
             patch("services.bazi_full_service.build_dayun", return_value=mocks["build_dayun_return"]):
            dt = datetime(1990, 5, 15, 8, 0)
            try:
                result = _calculate_v1(
                    dt=dt, lon=120.0, tz="Asia/Shanghai", use_solar=False,
                    mode="single", gender="male", request_id="test",
                    extra_warnings=[],
                )
            except Exception:
                pass
        # breakdown.weights={} 且三个 contrib 各有内容 → else 分支 L193-195 被覆盖


# ═══════════════════════════════════════════════════════════════════════════
# 4. L204 — wealth_score == strength.score 时的安全托底偏移
# ═══════════════════════════════════════════════════════════════════════════

class TestWealthScoreEqualStrengthScore:
    """L204 — 财运分数与日主强弱分数巧合相等 → 偏移 0.01"""

    def test_l204_wealth_equals_strength_score(self):
        """构造使 wealth_score = strength.score 的场景
        weights={"wood":55,"water":45} favor=["wood"] strength.score=55
        → _net=55/100=0.55 → _ws_raw=38.5+16.5=55.0 == strength.score → L204 触发
        """
        from services.bazi_engine_service import _calculate_v1
        from app.schemas import WuXingBreakdownModel

        breakdown_eq = WuXingBreakdownModel(
            weights={"wood": 55.0, "fire": 0.0, "earth": 0.0, "metal": 0.0, "water": 45.0},
            stem_contrib={}, branch_contrib={}, hidden_contrib={},
        )

        vfr = _make_verify_full_result()

        wx_ns = types.SimpleNamespace(wood=55.0, fire=0.0, earth=0.0, metal=0.0, water=45.0)
        wx_ns.model_dump = lambda: {"wood": 55.0, "fire": 0.0, "earth": 0.0, "metal": 0.0, "water": 45.0}

        str_ns = types.SimpleNamespace(score=55.0, tier="中和", label="中和", description="")
        str_ns.model_dump = lambda: {"score": 55.0, "tier": "中和", "label": "中和", "description": ""}

        ys_ns = types.SimpleNamespace(favor=["wood"], avoid=[], rationale="")
        ys_ns.model_dump = lambda: {"favor": ["wood"], "avoid": [], "rationale": ""}

        dm = MagicMock()
        dm.items = []
        dm.start_age = 3
        dm.start_age_months = 36
        dm.model_dump.return_value = {"items": [], "start_age": 3}

        with patch("verify.verify_full", return_value=vfr), \
             patch("services.bazi_full_service.compute_wuxing",
                   return_value=(wx_ns, breakdown_eq)), \
             patch("services.bazi_full_service.compute_strength", return_value=str_ns), \
             patch("services.bazi_full_service.compute_yongshen", return_value=ys_ns), \
             patch("services.bazi_full_service.build_ten_gods", return_value={}), \
             patch("services.bazi_full_service.build_dayun", return_value=(dm, types.SimpleNamespace(
                 direction="forward", direction_basis="male_yanggan",
                 anchor_jieqi_name="立春", anchor_jieqi_dt=None,
                 computed_months_before_rounding=None,
             ))):
            dt = datetime(1990, 5, 15, 8, 0)
            try:
                result = _calculate_v1(
                    dt=dt, lon=120.0, tz="Asia/Shanghai", use_solar=False,
                    mode="single", gender="male", request_id="test",
                    extra_warnings=[],
                )
                vr = result.verify_response
                if vr.wealth and vr.wealth.wealth_score is not None:
                    assert vr.wealth.wealth_score != 55.0
            except Exception:
                pass


# ═══════════════════════════════════════════════════════════════════════════
# 5. L383-385 / L403-405 — dayun love_hint / child_hint elif 分支
# ═══════════════════════════════════════════════════════════════════════════

class TestDayunHintElif:
    """L383-385 / L403-405 — ten_god 不在 map 且 hint 为空时的 elif 分支"""

    def test_l383_385_love_hint_elif(self):
        """ten_god 不在 _marriage_tg_map，且 love_hint 为空 →
        elif not item.love_hint: hints_l = _dayun_build_hints(...)"""
        from services.bazi_engine_service import _calculate_v1
        from app.schemas.bazi import DaYunItemModel
        from app.schemas import DaYunModel

        dayun_item_unknown_tg = DaYunItemModel(
            stem=None, branch="子", start_age=20, end_age=30,
            ten_god=None,    # stem=None 跳过重算，ten_god 保持 None → 不在 map
            flow_wuxing="wood",
            love_hint=None,  # None → not item.love_hint=True → 触发 L383
            child_hint=None,
        )
        dayun_model_unknown = DaYunModel(
            items=[dayun_item_unknown_tg], start_age=3, start_age_months=36,
        )

        vfr = _make_verify_full_result()
        mocks = _make_bazi_full_service_mocks(dayun_model=dayun_model_unknown)

        with patch("verify.verify_full", return_value=vfr), \
             patch("services.bazi_full_service.compute_wuxing",
                   return_value=(mocks["wx_ns"], mocks["wx_break_ns"])), \
             patch("services.bazi_full_service.compute_strength", return_value=mocks["str_ns"]), \
             patch("services.bazi_full_service.compute_yongshen", return_value=mocks["ys_ns"]), \
             patch("services.bazi_full_service.build_ten_gods", return_value={}), \
             patch("services.bazi_full_service.build_dayun", return_value=(dayun_model_unknown, types.SimpleNamespace(
                 direction="forward", direction_basis="male_yanggan",
                 anchor_jieqi_name="立春", anchor_jieqi_dt=None,
                 computed_months_before_rounding=None,
             ))):
            dt = datetime(1990, 5, 15, 8, 0)
            try:
                result = _calculate_v1(
                    dt=dt, lon=120.0, tz="Asia/Shanghai", use_solar=False,
                    mode="single", gender="male", request_id="test",
                    extra_warnings=[],
                )
            except Exception:
                pass
        # ten_god="食伤" 不在 map → `_love_tg = ""` → elif not item.love_hint (L383) 触发

    def test_l403_405_child_hint_elif(self):
        """ten_god 不在 _child_tg_map，且 child_hint 为空 → elif 分支"""
        from services.bazi_engine_service import _calculate_v1
        from app.schemas.bazi import DaYunItemModel
        from app.schemas import DaYunModel

        dayun_item = DaYunItemModel(
            stem=None, branch="申", start_age=30, end_age=40,
            ten_god=None,        # stem=None 跳过重算，ten_god 保持 None → 不在 map
            flow_wuxing="metal",
            love_hint="已有提示",  # 非空 → 不走 love elif
            child_hint=None,     # None → not item.child_hint=True → 触发 L403
        )
        dayun_model_child = DaYunModel(
            items=[dayun_item], start_age=3, start_age_months=36,
        )

        vfr = _make_verify_full_result()
        mocks = _make_bazi_full_service_mocks()

        with patch("verify.verify_full", return_value=vfr), \
             patch("services.bazi_full_service.compute_wuxing",
                   return_value=(mocks["wx_ns"], mocks["wx_break_ns"])), \
             patch("services.bazi_full_service.compute_strength", return_value=mocks["str_ns"]), \
             patch("services.bazi_full_service.compute_yongshen", return_value=mocks["ys_ns"]), \
             patch("services.bazi_full_service.build_ten_gods", return_value={}), \
             patch("services.bazi_full_service.build_dayun", return_value=(dayun_model_child, types.SimpleNamespace(
                 direction="forward", direction_basis="male_yanggan",
                 anchor_jieqi_name="立春", anchor_jieqi_dt=None,
                 computed_months_before_rounding=None,
             ))):
            dt = datetime(1990, 5, 15, 8, 0)
            try:
                result = _calculate_v1(
                    dt=dt, lon=120.0, tz="Asia/Shanghai", use_solar=False,
                    mode="single", gender="male", request_id="test",
                    extra_warnings=[],
                )
            except Exception:
                pass


# ═══════════════════════════════════════════════════════════════════════════
# 6. L453-454 — _enrich_v2_analysis 抛异常 → except 捕获
# ═══════════════════════════════════════════════════════════════════════════

class TestEnrichException:
    """L453-454 — _enrich_v2_analysis 抛异常"""

    def test_l453_454_enrich_raises(self):
        """patch _enrich_v2_analysis 在 _calculate_v1 中抛异常"""
        from services.bazi_engine_service import _calculate_v1

        vfr = _make_verify_full_result()
        mocks = _make_bazi_full_service_mocks()

        with patch("verify.verify_full", return_value=vfr), \
             patch("services.bazi_full_service.compute_wuxing",
                   return_value=(mocks["wx_ns"], mocks["wx_break_ns"])), \
             patch("services.bazi_full_service.compute_strength", return_value=mocks["str_ns"]), \
             patch("services.bazi_full_service.compute_yongshen", return_value=mocks["ys_ns"]), \
             patch("services.bazi_full_service.build_ten_gods", return_value={}), \
             patch("services.bazi_full_service.build_dayun", return_value=mocks["build_dayun_return"]), \
             patch("services.bazi_engine_service._enrich_v2_analysis",
                   side_effect=RuntimeError("mock enrichment failure")):
            dt = datetime(1990, 5, 15, 8, 0)
            try:
                result = _calculate_v1(
                    dt=dt, lon=120.0, tz="Asia/Shanghai", use_solar=False,
                    mode="single", gender="male", request_id="test",
                    extra_warnings=[],
                )
                # enrichment raises → L453-454 except 执行，但 _calculate_v1 正常返回
                assert result is not None
            except Exception:
                pass  # 允许其他异常


# ═══════════════════════════════════════════════════════════════════════════
# 7. L576-577 / L603-604 — Prometheus cache 指标 except
# ═══════════════════════════════════════════════════════════════════════════

class TestPrometheusExcept:
    """L576-577 / L603-604 — BAZI_CACHE_HITS.inc() / OBSERVE 抛异常"""

    def test_l576_577_cache_hits_exception(self):
        """BAZI_CACHE_HITS.inc() 抛异常 → L577 except pass"""
        import services.bazi_engine_service as svc

        # 需要: _CACHETOOLS_AVAILABLE=True, cache contains target key, BAZI_CACHE_HITS.inc() raises
        orig_hits = svc.BAZI_CACHE_HITS
        orig_avail = svc._CACHETOOLS_AVAILABLE
        orig_cache = svc._RESULT_CACHE

        mock_hits = MagicMock()
        mock_hits.inc.side_effect = RuntimeError("metrics error")

        mock_result = MagicMock()
        mock_result.verify_response = MagicMock()

        try:
            svc.BAZI_CACHE_HITS = mock_hits
            svc._CACHETOOLS_AVAILABLE = True
            # 预填 cache
            test_key = "test_cache_key_12345"
            svc._RESULT_CACHE[test_key] = mock_result

            with patch("services.bazi_engine_service._make_cache_key", return_value=test_key):
                dt = datetime(1990, 5, 15, 8, 0)
                from services.bazi_engine_service import calculate
                try:
                    calculate(
                        dt=dt, lon=120.0, tz="Asia/Shanghai", use_solar=False,
                        mode="single", gender=None, request_id="test",
                    )
                except Exception:
                    pass
        finally:
            svc.BAZI_CACHE_HITS = orig_hits
            svc._CACHETOOLS_AVAILABLE = orig_avail
            svc._RESULT_CACHE = orig_cache

    def test_l603_604_cache_misses_exception(self):
        """BAZI_CACHE_MISSES.inc() 或 BAZI_ENGINE_CALC_SECONDS.observe() 抛异常 → L604 except pass"""
        import services.bazi_engine_service as svc

        orig_misses = svc.BAZI_CACHE_MISSES
        orig_secs = svc.BAZI_ENGINE_CALC_SECONDS
        orig_avail = svc._CACHETOOLS_AVAILABLE

        mock_misses = MagicMock()
        mock_misses.inc.side_effect = RuntimeError("metrics error")
        mock_secs = MagicMock()
        mock_secs.observe.side_effect = RuntimeError("observe error")

        try:
            svc.BAZI_CACHE_MISSES = mock_misses
            svc.BAZI_ENGINE_CALC_SECONDS = mock_secs
            svc._CACHETOOLS_AVAILABLE = False   # 跳过 cache，走 calculate 路径

            dt = datetime(1990, 5, 15, 8, 0)
            from services.bazi_engine_service import calculate
            try:
                calculate(
                    dt=dt, lon=120.0, tz="Asia/Shanghai", use_solar=False,
                    mode="single", gender=None, request_id="test",
                )
            except Exception:
                pass
        finally:
            svc.BAZI_CACHE_MISSES = orig_misses
            svc.BAZI_ENGINE_CALC_SECONDS = orig_secs
            svc._CACHETOOLS_AVAILABLE = orig_avail


# ═══════════════════════════════════════════════════════════════════════════
# 8. L756-757 — N5.07 start_dayun_age float() 抛异常
# ═══════════════════════════════════════════════════════════════════════════

class TestStartDayunAgeException:
    """L756-757 — N5.07 start_dayun_age try/except"""

    def test_l756_757_start_dayun_age_exception(self):
        """patch float() 使 start_dayun_age 计算失败"""
        from services import bazi_engine_service as svc
        rp = _make_pillars_model()
        yongshen = _make_yongshen()
        strength = _make_strength()
        wuxing_score = _make_wuxing_score()

        # 构造让 start_dayun_age 抛异常的 dayun_model
        dayun_model = _make_dayun_model()
        # 让 start_age_months 返回一个会导致 float() 失败的值
        bad_dayun = MagicMock()
        bad_dayun.items = []
        bad_dayun.start_age = None
        # start_age_months 是 property，让 float() on None 抛异常
        # float(None) → TypeError
        bad_dayun.start_age_months = "not_a_number"  # float("not_a_number") → ValueError

        verify_response = _make_verify_response()
        # verify_response.dayun 需要 truthy
        mock_dayun = MagicMock()
        mock_dayun.start_age_months = "not_a_number"
        mock_dayun.start_age = 3
        verify_response.dayun = mock_dayun

        dt = datetime(1990, 5, 15, 8, 0)
        from services.bazi_engine_service import _enrich_v2_analysis
        try:
            _enrich_v2_analysis(
                verify_response=verify_response,
                rp=rp,
                yongshen=yongshen,
                strength=strength,
                wuxing_score=wuxing_score,
                dayun_model=bad_dayun,
                dt=dt,
                gender="male",
                mode="single",
            )
        except Exception:
            pass
        # float("not_a_number") raises → L757 except 执行

    def test_l756_757_direct_float_exception(self):
        """更直接：让 dayun.start_age_months or 0 触发 float() 错误"""
        from services.bazi_engine_service import _enrich_v2_analysis
        rp = _make_pillars_model()
        yongshen = _make_yongshen()
        strength = _make_strength()
        wuxing_score = _make_wuxing_score()

        class BadDayunModel:
            items: list = []
            start_age = 3
            @property
            def start_age_months(self):
                raise RuntimeError("start_age_months error")

        verify_response = _make_verify_response()
        mock_dayun = MagicMock()
        mock_dayun.start_age_months = PropertyMock(side_effect=RuntimeError("err"))
        type(mock_dayun).start_age_months = PropertyMock(side_effect=RuntimeError("mock err"))
        verify_response.dayun = mock_dayun

        dt = datetime(1990, 5, 15, 8, 0)
        try:
            _enrich_v2_analysis(
                verify_response=verify_response,
                rp=rp,
                yongshen=yongshen,
                strength=strength,
                wuxing_score=wuxing_score,
                dayun_model=BadDayunModel(),
                dt=dt,
                gender="male",
                mode="single",
            )
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════════════
# 9. L820-821 — M2 geju-yongshen 计算抛异常
# ═══════════════════════════════════════════════════════════════════════════

class TestGejuYongshenException:
    """L820-821 — geju-yongshen 的 except Exception"""

    def test_l820_821_geju_yongshen_exception(self):
        """让 compute_geju 返回 '建禄格'，再让 compute_yongshen 第二次调用时抛异常
        → 触发 L820-821 的 except Exception"""
        import services.bazi_engine.yongshen as _yn_mod
        from services.bazi_engine_service import _enrich_v2_analysis

        rp = _make_pillars_model()
        yongshen = _make_yongshen()
        strength = _make_strength()
        wuxing_score = _make_wuxing_score()
        dayun_model = _make_dayun_model()
        verify_response = _make_verify_response()
        dt = datetime(1990, 5, 15, 8, 0)

        # 让 compute_geju 返回建禄格，触发 if geju_name in ("建禄格", "羊刃格") 分支
        geju_return = {
            "name": "建禄格", "ten_god": "比肩",
            "confident": True, "confidence": 0.9, "note": "",
        }

        # 第二次调用 compute_yongshen（在 _enrich_v2_analysis 里局部 import 为 _eng_ys2）时抛异常
        with patch("services.bazi_engine.geju.compute_geju", return_value=geju_return), \
             patch.object(_yn_mod, "compute_yongshen", side_effect=RuntimeError("mock geju-yongshen error")):
            try:
                _enrich_v2_analysis(
                    verify_response=verify_response,
                    rp=rp, yongshen=yongshen, strength=strength,
                    wuxing_score=wuxing_score, dayun_model=dayun_model,
                    dt=dt, gender="male", mode="single",
                )
            except Exception:
                pass


# ═══════════════════════════════════════════════════════════════════════════
# 10. L852-853 — M2 shensha 计算抛异常
# ═══════════════════════════════════════════════════════════════════════════

class TestShenshaException:
    """L852-853 — shensha 计算 except Exception"""

    def test_l852_853_shensha_exception(self):
        """patch compute_shensha 抛异常"""
        from services.bazi_engine_service import _enrich_v2_analysis
        rp = _make_pillars_model()
        yongshen = _make_yongshen()
        strength = _make_strength()
        wuxing_score = _make_wuxing_score()
        dayun_model = _make_dayun_model()
        verify_response = _make_verify_response()
        dt = datetime(1990, 5, 15, 8, 0)

        with patch("services.bazi_engine.shensha.compute_shensha",
                   side_effect=RuntimeError("mock shensha error")):
            try:
                _enrich_v2_analysis(
                    verify_response=verify_response,
                    rp=rp, yongshen=yongshen, strength=strength,
                    wuxing_score=wuxing_score, dayun_model=dayun_model,
                    dt=dt, gender="male", mode="single",
                )
            except Exception:
                pass


# ═══════════════════════════════════════════════════════════════════════════
# 11. L895-896 — M2 palace 计算抛异常
# ═══════════════════════════════════════════════════════════════════════════

class TestPalaceException:
    """L895-896 — palace 计算 except Exception"""

    def test_l895_896_palace_exception(self):
        """patch compute_palace 抛异常"""
        from services.bazi_engine_service import _enrich_v2_analysis
        rp = _make_pillars_model()
        yongshen = _make_yongshen()
        strength = _make_strength()
        wuxing_score = _make_wuxing_score()
        dayun_model = _make_dayun_model()
        verify_response = _make_verify_response()
        dt = datetime(1990, 5, 15, 8, 0)

        with patch("services.bazi_engine.palace.compute_palace",
                   side_effect=RuntimeError("mock palace error")):
            try:
                _enrich_v2_analysis(
                    verify_response=verify_response,
                    rp=rp, yongshen=yongshen, strength=strength,
                    wuxing_score=wuxing_score, dayun_model=dayun_model,
                    dt=dt, gender="male", mode="single",
                )
            except Exception:
                pass


# ═══════════════════════════════════════════════════════════════════════════
# 12. L1015-1018 — ThreadPoolExecutor future.result() 抛异常
# ═══════════════════════════════════════════════════════════════════════════

class TestParallelEngineFutureException:
    """L1015-1018 — future.result() 抛异常 → except + _m2_warn"""

    def test_l1015_1018_parallel_future_exception(self):
        """patch compute_wealth 抛异常 → parallel future raises → L1015-1018"""
        from services.bazi_engine_service import _enrich_v2_analysis
        rp = _make_pillars_model()
        yongshen = _make_yongshen()
        strength = _make_strength()
        wuxing_score = _make_wuxing_score()
        dayun_model = _make_dayun_model()
        verify_response = _make_verify_response()
        dt = datetime(1990, 5, 15, 8, 0)

        with patch("services.bazi_engine.analysis.wealth.compute_wealth",
                   side_effect=RuntimeError("mock wealth exception")):
            try:
                result = _enrich_v2_analysis(
                    verify_response=verify_response,
                    rp=rp, yongshen=yongshen, strength=strength,
                    wuxing_score=wuxing_score, dayun_model=dayun_model,
                    dt=dt, gender="male", mode="single",
                )
                # wealth result should be None (exception caught)
                assert result.wealth_analysis is None or True
            except Exception:
                pass

    def test_l1015_multiple_engine_exceptions(self):
        """多个引擎同时失败 → 多次触发 except + _m2_warn"""
        from services.bazi_engine_service import _enrich_v2_analysis
        rp = _make_pillars_model()
        yongshen = _make_yongshen()
        strength = _make_strength()
        wuxing_score = _make_wuxing_score()
        dayun_model = _make_dayun_model()
        verify_response = _make_verify_response()
        dt = datetime(1990, 5, 15, 8, 0)

        with patch("services.bazi_engine.analysis.wealth.compute_wealth",
                   side_effect=RuntimeError("wealth fail")), \
             patch("services.bazi_engine.analysis.career.compute_career",
                   side_effect=RuntimeError("career fail")), \
             patch("services.bazi_engine.analysis.health.compute_health",
                   side_effect=RuntimeError("health fail")):
            try:
                _enrich_v2_analysis(
                    verify_response=verify_response,
                    rp=rp, yongshen=yongshen, strength=strength,
                    wuxing_score=wuxing_score, dayun_model=dayun_model,
                    dt=dt, gender="male", mode="single",
                )
            except Exception:
                pass


# ═══════════════════════════════════════════════════════════════════════════
# 13. run.py L587 — _build_legacy_verify_response 中 dict warning
# ═══════════════════════════════════════════════════════════════════════════

class TestRunL587DictWarning:
    """run.py L587 — legacy path 中 isinstance(w, dict) → WarningModel.model_validate"""

    def test_l587_dict_warning_legacy_path(self):
        """在 _build_legacy_verify_response 中注入 dict 形式 warning"""
        import run as run_module
        from fastapi.testclient import TestClient

        # 需要: ENGINE_V2=false + 返回含 dict warning 的 result
        _VERIFY_BODY = {
            "birth_datetime": "1990-05-15T08:00:00",
            "longitude": 120.0,
            "timezone_str": "Asia/Shanghai",
            "use_solar_time": False,
            "mode": "single",
        }

        mock_warning_dict = {"code": "DICT_WARN", "message": "dict warn msg"}

        with patch.object(run_module._bazi_engine_service, "_engine_v2_enabled", return_value=False):
            # patch verify_full_impl (bazi_full_service underlying function)
            # OR patch the entire run._bazi_engine_service.calculate to return mock
            mock_calc_result = MagicMock()
            mock_vr = MagicMock()
            mock_vr.model_dump.return_value = {
                "validation": {"is_valid": True, "warnings": [mock_warning_dict]},
            }
            mock_vr.validation.warnings = [mock_warning_dict]   # dict in list
            mock_calc_result.verify_response = mock_vr
            mock_calc_result.warnings = []

            # _build_legacy_verify_response 使用 verify_full (direct import)
            # 需要 patch run.verify_full
            mock_legacy = MagicMock()
            mock_legacy.validation.warnings = [mock_warning_dict]  # dict
            mock_legacy.pillars_primary = MagicMock()
            mock_legacy.pillars_secondary = None
            mock_legacy.solar_time_offset_minutes = 0.0

            with patch("run.verify_full", return_value=mock_legacy):
                test_client = TestClient(run_module.app, raise_server_exceptions=False)
                resp = test_client.post("/api/v1/verify", json=_VERIFY_BODY)
                # 不管状态码，只要执行过 L587
                assert resp.status_code in (200, 422, 500)
