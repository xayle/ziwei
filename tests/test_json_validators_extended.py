"""
json_validators.py 扩展覆盖测试
目标：将覆盖率从 67% 提升到 90%+

覆盖以下未被测试的路径：
- PillarModel 空白字符串验证器（Line 25）
- FiveElementsModel 无效字符串数字转换（Lines 60-61）
- BaziResultModel 时间戳验证器（Lines 77-86）
- EventJsonValidator 各方法的 JSON 字符串输入分支（Lines 138-160）
- ScenarioJsonValidator JSON 字符串 + validate_results（Lines 213-240）
- validate_json_string / safe_validate_json 通用函数（Lines 262-284）
"""
import json
import pytest
from pydantic import ValidationError

from services.json_validators import (
    PillarModel,
    BaziResultModel,
    FiveElementsModel,
    RecommendationModel,
    ScenarioResultModel,
    EventJsonValidator,
    ScenarioJsonValidator,
    validate_json_string,
    safe_validate_json,
)

# ═══════════════════════════════════════════════════════════════════════════════
# 辅助数据
# ═══════════════════════════════════════════════════════════════════════════════

_VALID_PILLARS_DICT = {
    "year_pillar":  {"heavenly_stem": "甲", "earthly_branch": "子"},
    "month_pillar": {"heavenly_stem": "乙", "earthly_branch": "丑"},
    "day_pillar":   {"heavenly_stem": "丙", "earthly_branch": "寅"},
    "time_pillar":  {"heavenly_stem": "丁", "earthly_branch": "卯"},
}

_VALID_BAZI_DICT = {
    "pillars_primary": _VALID_PILLARS_DICT,
    "ten_gods": {},
}


# ═══════════════════════════════════════════════════════════════════════════════
# PillarModel 验证器（Line 25）
# ═══════════════════════════════════════════════════════════════════════════════

class TestPillarModelValidator:
    """PillarModel.validate_stem_branch 的边界路径"""

    def test_whitespace_only_stem_raises(self):
        """纯空白天干应触发 ValueError（Line 25 覆盖）"""
        with pytest.raises(ValidationError):
            PillarModel(heavenly_stem="   ", earthly_branch="子")

    def test_whitespace_only_branch_raises(self):
        """纯空白地支应触发 ValueError"""
        with pytest.raises(ValidationError):
            PillarModel(heavenly_stem="甲", earthly_branch="   ")

    def test_strip_leading_trailing_spaces(self):
        """带前后空白的天干/地支应被 strip 后接受"""
        p = PillarModel(heavenly_stem="  甲  ", earthly_branch="  子  ")
        assert p.heavenly_stem == "甲"
        assert p.earthly_branch == "子"


# ═══════════════════════════════════════════════════════════════════════════════
# FiveElementsModel 字符串转换（Lines 60-61）
# ═══════════════════════════════════════════════════════════════════════════════

class TestFiveElementsStringConversion:
    """五行评分字符串转换路径"""

    def test_invalid_string_raises_value_error(self):
        """非数字字符串触发 ValidationError（Lines 60-61）"""
        with pytest.raises(ValidationError):
            FiveElementsModel(wood="abc", fire=10.0, earth=10.0, metal=10.0, water=10.0)  # type: ignore[arg-type]

    def test_numeric_string_converts(self):
        """数字字符串正常转换为 float"""
        m = FiveElementsModel(wood="30.5", fire=10.0, earth=10.0, metal=10.0, water=10.0)  # type: ignore[arg-type]
        assert m.wood == 30.5

    def test_integer_string_converts(self):
        """整数字符串正常转换"""
        m = FiveElementsModel(wood="25", fire=10.0, earth=10.0, metal=10.0, water=10.0)  # type: ignore[arg-type]
        assert m.wood == 25.0


# ═══════════════════════════════════════════════════════════════════════════════
# BaziResultModel 时间戳验证器（Lines 77-86）
# ═══════════════════════════════════════════════════════════════════════════════

class TestBaziResultTimestampValidator:
    """calculated_at 时间戳字段的三条路径"""

    def _base(self, **kw):
        data = dict(_VALID_BAZI_DICT)
        data.update(kw)
        return data

    def test_none_timestamp_accepted(self):
        """None 时间戳正常通过（Line 79/80）"""
        m = BaziResultModel(**self._base(calculated_at=None))
        assert m.calculated_at is None

    def test_valid_iso_timestamp_accepted(self):
        """合法 ISO 格式时间戳通过（Lines 82-84）"""
        m = BaziResultModel(**self._base(calculated_at="2025-01-01T12:00:00"))
        assert m.calculated_at == "2025-01-01T12:00:00"

    def test_iso_timestamp_with_z_suffix(self):
        """带 Z 后缀的时间戳替换为 +00:00 后通过"""
        m = BaziResultModel(**self._base(calculated_at="2025-06-15T08:30:00Z"))
        assert m.calculated_at == "2025-06-15T08:30:00Z"

    def test_invalid_timestamp_format_raises(self):
        """非 ISO 格式时间戳抛出 ValidationError（Lines 85-86）"""
        with pytest.raises(ValidationError):
            BaziResultModel(**self._base(calculated_at="2025/01/01 12:00"))


# ═══════════════════════════════════════════════════════════════════════════════
# EventJsonValidator - JSON 字符串输入分支（Lines 138-160）
# ═══════════════════════════════════════════════════════════════════════════════

class TestEventJsonValidatorStringInput:
    """EventJsonValidator 各方法的 JSON 字符串分支"""

    def test_validate_recommendation_json_string(self):
        """validate_recommendation 接受 JSON 字符串（Lines 138-141）"""
        payload = json.dumps({"title": "建议", "confidence": 0.8})
        result = EventJsonValidator.validate_recommendation(payload)
        assert result.title == "建议"
        assert result.confidence == 0.8

    def test_validate_recommendation_invalid_json_string(self):
        """validate_recommendation 遇无效 JSON 抛 ValueError"""
        with pytest.raises(ValueError, match="无效的 JSON 格式"):
            EventJsonValidator.validate_recommendation("{bad json}")

    def test_validate_five_elements_json_string(self):
        """validate_five_elements 接受 JSON 字符串（Lines 157-160）"""
        payload = json.dumps({"wood": 20.0, "fire": 20.0, "earth": 20.0, "metal": 20.0, "water": 20.0})
        result = EventJsonValidator.validate_five_elements(payload)
        assert result.wood == 20.0

    def test_validate_five_elements_invalid_json_string(self):
        """validate_five_elements 遇无效 JSON 抛 ValueError"""
        with pytest.raises(ValueError, match="无效的 JSON 格式"):
            EventJsonValidator.validate_five_elements("{bad json}")


# ═══════════════════════════════════════════════════════════════════════════════
# ScenarioJsonValidator（Lines 213-240）
# ═══════════════════════════════════════════════════════════════════════════════

class TestScenarioJsonValidatorExtended:
    """ScenarioJsonValidator 的 JSON 字符串分支 + validate_results"""

    def test_validate_variations_json_string(self):
        """validate_variations 接受 JSON 字符串（Lines 213-216）"""
        payload = json.dumps({"name": "test_scene", "description": "测试"})
        result = ScenarioJsonValidator.validate_variations(payload)
        assert result.name == "test_scene"

    def test_validate_variations_invalid_json(self):
        """validate_variations 遇无效 JSON 抛 ValueError"""
        with pytest.raises(ValueError, match="无效的 JSON 格式"):
            ScenarioJsonValidator.validate_variations("{invalid}")

    def test_validate_results_list_of_dicts(self):
        """validate_results：传入字典列表（Lines 231-240）"""
        data = [{"scenario_id": 1}, {"scenario_id": 2, "significance": "major"}]
        results = ScenarioJsonValidator.validate_results(data)
        assert len(results) == 2
        assert results[0].scenario_id == 1
        assert results[1].significance == "major"

    def test_validate_results_from_json_string(self):
        """validate_results：传入 JSON 字符串"""
        payload = json.dumps([{"scenario_id": 3}])
        results = ScenarioJsonValidator.validate_results(payload)
        assert results[0].scenario_id == 3

    def test_validate_results_non_list_raises(self):
        """validate_results：传入非列表字典抛 ValueError"""
        with pytest.raises(ValueError, match="必须是 JSON 数组"):
            ScenarioJsonValidator.validate_results({"scenario_id": 1})

    def test_validate_results_invalid_json_string(self):
        """validate_results：传入无效 JSON 字符串抛 ValueError"""
        with pytest.raises(ValueError, match="无效的 JSON 格式"):
            ScenarioJsonValidator.validate_results("{not a list}")

    def test_validate_results_with_pillars(self):
        """validate_results：包含 pillars_adjusted 的完整场景结果"""
        data = [{
            "scenario_id": 5,
            "pillars_adjusted": _VALID_PILLARS_DICT,
            "changes": {"month": "shifted"},
            "significance": "minor",
        }]
        results = ScenarioJsonValidator.validate_results(data)
        assert results[0].pillars_adjusted is not None
        assert results[0].changes == {"month": "shifted"}

    def test_validate_results_empty_list(self):
        """validate_results：空列表返回空 list"""
        results = ScenarioJsonValidator.validate_results([])
        assert results == []


# ═══════════════════════════════════════════════════════════════════════════════
# validate_json_string / safe_validate_json（Lines 262-284）
# ═══════════════════════════════════════════════════════════════════════════════

class TestGenericJsonValidators:
    """通用辅助函数的覆盖路径"""

    def test_validate_json_string_success(self):
        """validate_json_string 返回正确模型实例（Lines 262-267）"""
        payload = json.dumps({"title": "ok", "confidence": 0.5})
        result = validate_json_string(payload, RecommendationModel)
        assert isinstance(result, RecommendationModel)
        assert result.title == "ok"

    def test_validate_json_string_invalid_json_raises(self):
        """validate_json_string：无效 JSON 抛 ValueError"""
        with pytest.raises(ValueError):
            validate_json_string("{bad}", RecommendationModel)

    def test_validate_json_string_schema_mismatch_raises(self):
        """validate_json_string：数据不符合模式抛 ValidationError"""
        payload = json.dumps({"confidence": 5.0})  # 超出 0-1 范围
        with pytest.raises(ValidationError):
            validate_json_string(payload, RecommendationModel)

    def test_safe_validate_json_returns_instance_on_success(self):
        """safe_validate_json：成功时返回模型实例（Lines 281-284）"""
        payload = json.dumps({"wood": 20.0, "fire": 20.0, "earth": 20.0, "metal": 20.0, "water": 20.0})
        result = safe_validate_json(payload, FiveElementsModel)
        assert result is not None
        assert result.wood == 20.0  # type: ignore[union-attr]

    def test_safe_validate_json_returns_none_on_invalid_json(self):
        """safe_validate_json：无效 JSON 返回 None（Lines 281-284）"""
        result = safe_validate_json("{bad json}", FiveElementsModel)
        assert result is None

    def test_safe_validate_json_returns_none_on_schema_error(self):
        """safe_validate_json：模式错误返回 None"""
        payload = json.dumps({"confidence": 99.9})  # 超范围
        result = safe_validate_json(payload, RecommendationModel)
        assert result is None
