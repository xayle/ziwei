"""
bazi_engine_service.py 工具函数扩展覆盖测试
目标：将覆盖率从 58% 提升到 70%+

覆盖以下可独立测试的工具函数：
- _make_cache_key（Lines 62-63）
- _engine_v2_enabled（Line 65）
- CalculateResult 数据类
- _to_wuxing_scores：三条输入路径（Lines 334-337）
- _to_pillars_model：两条输入路径（Lines 345-357）
- _build_month_ganzhis：正常路径 + invalid（Lines 481-491）
- _get_current_dayun_stem（Lines 493-510）
- calculate()：缓存命中路径 + v1/v2 路径（通过 mock）
"""
import os
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch


# ─────────────────────────────────────────────────────────────────────────────
# 被测模块
# ─────────────────────────────────────────────────────────────────────────────

from services.bazi_engine_service import (
    _make_cache_key,
    _engine_v2_enabled,
    _to_wuxing_scores,
    _to_pillars_model,
    _build_month_ganzhis,
    _get_current_dayun_stem,
    CalculateResult,
    _STEMS,
    _MONTH_BRANCHES,
    _YEAR_STEM_MONTH1_STEM,
)
from app.schemas import PillarsModel, WuXingScoreModel, VerifyResponse


# ─────────────────────────────────────────────────────────────────────────────
# 辅助工厂
# ─────────────────────────────────────────────────────────────────────────────

def _make_pillars_model(**kw) -> PillarsModel:
    defaults = {
        "year":  {"stem": "甲", "branch": "子", "ganzhi": "甲子"},
        "month": {"stem": "乙", "branch": "丑", "ganzhi": "乙丑"},
        "day":   {"stem": "丙", "branch": "寅", "ganzhi": "丙寅"},
        "hour":  {"stem": "丁", "branch": "卯", "ganzhi": "丁卯"},
    }
    defaults.update(kw)
    return PillarsModel.model_validate(defaults)


def _make_wuxing() -> WuXingScoreModel:
    return WuXingScoreModel(wood=30, fire=20, earth=15, metal=20, water=15)


def _make_dummy_verify_response() -> MagicMock:
    vr = MagicMock(spec=VerifyResponse)
    return vr


# ═══════════════════════════════════════════════════════════════════════════════
# _make_cache_key（Lines 62-63）
# ═══════════════════════════════════════════════════════════════════════════════

class TestMakeCacheKey:
    """缓存键生成函数"""

    def test_returns_64_char_hex_string(self):
        """SHA-256 should return 64-char hex string"""
        dt = datetime(2000, 1, 1, 12, 0)
        key = _make_cache_key(dt, 120.0, "single", "male")
        assert len(key) == 64
        assert all(c in "0123456789abcdef" for c in key)

    def test_same_input_same_key(self):
        """相同输入应产生相同 key"""
        dt = datetime(2000, 1, 1, 12, 0)
        k1 = _make_cache_key(dt, 120.0, "single", "male")
        k2 = _make_cache_key(dt, 120.0, "single", "male")
        assert k1 == k2

    def test_different_mode_different_key(self):
        """不同 mode 产生不同 key"""
        dt = datetime(2000, 1, 1, 12, 0)
        k1 = _make_cache_key(dt, 120.0, "single", None)
        k2 = _make_cache_key(dt, 120.0, "dual", None)
        assert k1 != k2

    def test_none_gender_handled(self):
        """None gender 不抛异常"""
        dt = datetime(1990, 5, 20, 8, 0)
        key = _make_cache_key(dt, 110.0, "single", None)
        assert isinstance(key, str)

    def test_longitude_precision(self):
        """经度保留 4 位小数参与 hash"""
        dt = datetime(2000, 1, 1, 0, 0)
        k1 = _make_cache_key(dt, 120.1234, "single", None)
        k2 = _make_cache_key(dt, 120.1235, "single", None)
        assert k1 != k2


# ═══════════════════════════════════════════════════════════════════════════════
# _engine_v2_enabled
# ═══════════════════════════════════════════════════════════════════════════════

class TestEngineV2Enabled:
    """ENGINE_V2 flag 读取"""

    def test_default_is_false(self):
        """未设环境变量时返回 False"""
        with patch.dict(os.environ, {"ENGINE_V2": "false"}):
            assert _engine_v2_enabled() is False

    def test_true_when_set(self):
        """ENGINE_V2=true 时返回 True"""
        with patch.dict(os.environ, {"ENGINE_V2": "true"}):
            assert _engine_v2_enabled() is True

    def test_case_insensitive(self):
        """大写 TRUE 也识别"""
        with patch.dict(os.environ, {"ENGINE_V2": "TRUE"}):
            assert _engine_v2_enabled() is True

    def test_spaces_stripped(self):
        """带前后空白也识别"""
        with patch.dict(os.environ, {"ENGINE_V2": "  true  "}):
            assert _engine_v2_enabled() is True


# ═══════════════════════════════════════════════════════════════════════════════
# CalculateResult 数据类
# ═══════════════════════════════════════════════════════════════════════════════

class TestCalculateResult:
    """CalculateResult dataclass"""

    def test_default_engine_version_is_v1(self):
        vr = _make_dummy_verify_response()
        result = CalculateResult(verify_response=vr)
        assert result.engine_version == "v1"

    def test_warnings_default_empty(self):
        vr = _make_dummy_verify_response()
        result = CalculateResult(verify_response=vr)
        assert result.warnings == []

    def test_custom_engine_version(self):
        vr = _make_dummy_verify_response()
        result = CalculateResult(verify_response=vr, engine_version="v2")
        assert result.engine_version == "v2"

    def test_warnings_not_shared_between_instances(self):
        """默认 list 不共享（dataclass field(default_factory=list)）"""
        vr = _make_dummy_verify_response()
        r1 = CalculateResult(verify_response=vr)
        r2 = CalculateResult(verify_response=vr)
        r1.warnings.append("x")
        assert r2.warnings == []


# ═══════════════════════════════════════════════════════════════════════════════
# _to_wuxing_scores（Lines 334-337）
# ═══════════════════════════════════════════════════════════════════════════════

class TestToWuxingScores:
    """WuXingScoreModel → dict 的三条路径"""

    def test_model_dump_path(self):
        """model.model_dump() 路径（Lines 334-335）"""
        m = _make_wuxing()
        out = _to_wuxing_scores(m)
        assert out == {"wood": 30.0, "fire": 20.0, "earth": 15.0, "metal": 20.0, "water": 15.0}

    def test_dict_path(self):
        """普通字典输入（else 分支，Lines 336-337）"""
        d = {"wood": 25.0, "fire": 25.0, "earth": 20.0, "metal": 15.0, "water": 15.0, "extra": 99}
        out = _to_wuxing_scores(d)
        assert "extra" not in out
        assert out["wood"] == 25.0

    def test_object_with_dict_path(self):
        """有 __dict__ 但无 model_dump 的对象（Lines 335-337）"""
        class FakeModel:
            def __init__(self):
                self.wood = 10.0
                self.fire = 10.0
                self.earth = 10.0
                self.metal = 10.0
                self.water = 10.0
                self.ignored_field = "xyz"

        out = _to_wuxing_scores(FakeModel())
        assert out == {"wood": 10.0, "fire": 10.0, "earth": 10.0, "metal": 10.0, "water": 10.0}

    def test_filters_non_wuxing_keys(self):
        """非五行键被过滤掉"""
        d = {"wood": 30.0, "fire": 30.0, "earth": 30.0, "metal": 0.0, "water": 0.0, "unknown": 999}
        out = _to_wuxing_scores(d)
        assert set(out.keys()) <= {"wood", "fire", "earth", "metal", "water"}


# ═══════════════════════════════════════════════════════════════════════════════
# _to_pillars_model（Lines 345-357）
# ═══════════════════════════════════════════════════════════════════════════════

class TestToPillarsModel:
    """_to_pillars_model 的路径覆盖"""

    def test_pillarmodel_instance_returned_directly(self):
        """isinstance(p, PillarsModel) 路径直接返回（Line 346）"""
        p = _make_pillars_model()
        out = _to_pillars_model(p)
        assert out is p

    def test_model_dump_path(self):
        """有 model_dump() 方法的对象走验证路径（Lines 347-348）"""
        p = _make_pillars_model()
        # 创建一个有 model_dump() 但不是 PillarsModel 的对象
        class FakePillars:
            def model_dump(self):
                return p.model_dump()

        out = _to_pillars_model(FakePillars())
        assert isinstance(out, PillarsModel)
        assert out.year.stem == "甲"

    def test_dataclass_path(self):
        """有 __dict__ 的类（如 boundary.Pillars）走字段逐一转换路径（Lines 349-357）"""
        class FakePillar:
            def __init__(self, stem, branch):
                self.stem = stem
                self.branch = branch
                self.ganzhi = stem + branch

        class FakePillarsDataclass:
            def __init__(self):
                self.year = FakePillar("甲", "子")
                self.month = FakePillar("乙", "丑")
                self.day = FakePillar("丙", "寅")
                self.hour = FakePillar("丁", "卯")

        out = _to_pillars_model(FakePillarsDataclass())
        assert isinstance(out, PillarsModel)
        assert out.year.stem == "甲"
        assert out.day.stem == "丙"


# ═══════════════════════════════════════════════════════════════════════════════
# _build_month_ganzhis（Lines 481-491）
# ═══════════════════════════════════════════════════════════════════════════════

class TestBuildMonthGanzhis:
    """月干支数组生成"""

    def test_jia_year_returns_12_items(self):
        """甲年返回 12 个月干支"""
        result = _build_month_ganzhis("甲")
        assert result is not None
        assert len(result) == 12

    def test_jia_year_first_month_is_bingyin(self):
        """甲年正月（寅月）起天干丙 → 丙寅"""
        result = _build_month_ganzhis("甲")
        assert result is not None
        assert result[0] == "丙寅"

    def test_all_valid_year_stems(self):
        """10个天干均返回非 None"""
        for stem in ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]:
            result = _build_month_ganzhis(stem)
            assert result is not None, f"stem {stem} returned None"
            assert len(result) == 12

    def test_invalid_year_stem_returns_none(self):
        """无效天干返回 None（Line 485）"""
        assert _build_month_ganzhis("X") is None
        assert _build_month_ganzhis("") is None

    def test_geng_year_first_month_is_wuyin(self):
        """庚年正月起天干戊 → 戊寅"""
        result = _build_month_ganzhis("庚")
        assert result is not None
        assert result[0] == "戊寅"

    def test_month_branches_in_correct_order(self):
        """月支顺序：寅卯辰巳午未申酉戌亥子丑"""
        result = _build_month_ganzhis("甲")
        assert result is not None
        branches = [gz[1] for gz in result]
        assert branches == list(_MONTH_BRANCHES)


# ═══════════════════════════════════════════════════════════════════════════════
# _get_current_dayun_stem（Lines 493-510）
# ═══════════════════════════════════════════════════════════════════════════════

class TestGetCurrentDayunStem:
    """当前大运天干推算"""

    def test_returns_correct_stem_for_current_age(self):
        """25岁对应第二个大运（start_age=18）"""
        dayun = [
            {"stem": "甲", "start_age": 8},
            {"stem": "乙", "start_age": 18},
            {"stem": "丙", "start_age": 28},
        ]
        from datetime import date
        birth_year = date.today().year - 25
        stem = _get_current_dayun_stem(dayun, birth_year)
        assert stem == "乙"

    def test_returns_none_when_list_empty(self):
        """空大运列表返回 None"""
        stem = _get_current_dayun_stem([], 1990)
        assert stem is None

    def test_returns_none_if_no_matching_age(self):
        """年龄在首个大运起步年之前返回 None"""
        from datetime import date
        birth_year = date.today().year - 3   # only 3 years old
        dayun = [{"stem": "甲", "start_age": 8}]
        stem = _get_current_dayun_stem(dayun, birth_year)
        assert stem is None

    def test_missing_start_age_key_skipped(self):
        """start_age 为 None 的条目被跳过"""
        from datetime import date
        birth_year = date.today().year - 30
        dayun = [
            {"stem": "甲", "start_age": None},
            {"stem": "乙", "start_age": 20},
        ]
        stem = _get_current_dayun_stem(dayun, birth_year)
        # 年龄30 >= 20 → 乙
        assert stem == "乙"

    def test_float_start_age_supported(self):
        """float 类型 start_age 通过 float() 比较"""
        from datetime import date
        birth_year = date.today().year - 15
        dayun = [
            {"stem": "壬", "start_age": 8.5},
            {"stem": "癸", "start_age": 18.5},
        ]
        stem = _get_current_dayun_stem(dayun, birth_year)
        assert stem == "壬"


# ═══════════════════════════════════════════════════════════════════════════════
# calculate() 函数 - 缓存路径 + v1/v2 路径（通过 mock）
# ═══════════════════════════════════════════════════════════════════════════════

class TestCalculateFunction:
    """calculate() 公开入口函数的路径覆盖"""

    def _make_fake_result(self, engine_version="v1") -> CalculateResult:
        vr = _make_dummy_verify_response()
        return CalculateResult(verify_response=vr, engine_version=engine_version)

    def test_calls_v1_by_default(self):
        """ENGINE_V2=false 时调用 _calculate_v1"""
        fake_result = self._make_fake_result("v1")

        with patch("services.bazi_engine_service._engine_v2_enabled", return_value=False), \
             patch("services.bazi_engine_service._calculate_v1", return_value=fake_result) as mock_v1, \
             patch("services.bazi_engine_service._CACHETOOLS_AVAILABLE", False):

            from services.bazi_engine_service import calculate
            dt = datetime(2000, 1, 1, 12, 0)
            result = calculate(dt, 120.0, "Asia/Shanghai", mode="single")

        mock_v1.assert_called_once()
        assert result.engine_version == "v1"

    def test_calls_v2_when_flag_set(self):
        """ENGINE_V2=true 时调用 _calculate_v2"""
        fake_result = self._make_fake_result("v2")

        with patch("services.bazi_engine_service._engine_v2_enabled", return_value=True), \
             patch("services.bazi_engine_service._calculate_v2", return_value=fake_result) as mock_v2, \
             patch("services.bazi_engine_service._CACHETOOLS_AVAILABLE", False):

            from services.bazi_engine_service import calculate
            dt = datetime(2000, 1, 1, 12, 0)
            result = calculate(dt, 120.0, "Asia/Shanghai", mode="single")

        mock_v2.assert_called_once()
        assert result.engine_version == "v2"

    def test_cache_hit_returns_cached_result(self):
        """缓存命中时直接返回缓存结果，不调用 _calculate_v1"""
        fake_result = self._make_fake_result("v1")
        dt = datetime(1985, 3, 15, 6, 0)

        with patch("services.bazi_engine_service._CACHETOOLS_AVAILABLE", True), \
             patch("services.bazi_engine_service._RESULT_CACHE", {}) as mock_cache, \
             patch("services.bazi_engine_service._engine_v2_enabled", return_value=False), \
             patch("services.bazi_engine_service._calculate_v1", return_value=fake_result) as mock_v1:

            # 先存入缓存
            from services.bazi_engine_service import _make_cache_key
            cache_key = _make_cache_key(dt, 110.0, "single", None)
            mock_cache[cache_key] = fake_result

            from services.bazi_engine_service import calculate
            result = calculate(dt, 110.0, "Asia/Shanghai", mode="single")

        # 命中缓存，不应调用 _calculate_v1
        mock_v1.assert_not_called()
        assert result is fake_result

    def test_extra_warnings_forwarded(self):
        """extra_warnings 被正确透传到 _calculate_v1"""
        fake_result = self._make_fake_result("v1")

        with patch("services.bazi_engine_service._engine_v2_enabled", return_value=False), \
             patch("services.bazi_engine_service._calculate_v1", return_value=fake_result) as mock_v1, \
             patch("services.bazi_engine_service._CACHETOOLS_AVAILABLE", False):

            from services.bazi_engine_service import calculate
            dt = datetime(2000, 1, 1, 12, 0)
            calculate(dt, 120.0, "Asia/Shanghai", extra_warnings=["w1", "w2"])

        call_kwargs = mock_v1.call_args.kwargs
        assert call_kwargs["extra_warnings"] == ["w1", "w2"]
