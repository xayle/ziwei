"""
JSON 验证服务的单元测试
"""
import pytest
import json
from pydantic import ValidationError
from services.json_validators import (
    EventJsonValidator,
    ScenarioJsonValidator,
    BaziResultModel,
    RecommendationModel,
    PillarsModel,
    FiveElementsModel,
    ScenarioVariationsModel,
)


class TestEventJsonValidators:
    """Event JSON 验证测试"""
    
    def test_valid_bazi_json(self):
        """测试有效的 bazi_json"""
        valid_data = {
            "pillars_primary": {
                "year_pillar": {"heavenly_stem": "甲", "earthly_branch": "子"},
                "month_pillar": {"heavenly_stem": "乙", "earthly_branch": "丑"},
                "day_pillar": {"heavenly_stem": "丙", "earthly_branch": "寅"},
                "time_pillar": {"heavenly_stem": "丁", "earthly_branch": "卯"}
            },
            "ten_gods": {}
        }
        
        result = EventJsonValidator.validate_bazi_json(valid_data)
        assert result.pillars_primary.year_pillar.heavenly_stem == "甲"
        assert result.pillars_primary.year_pillar.earthly_branch == "子"
    
    def test_bazi_json_with_json_string(self):
        """测试从 JSON 字符串验证 bazi_json"""
        json_string = json.dumps({
            "pillars_primary": {
                "year_pillar": {"heavenly_stem": "甲", "earthly_branch": "子"},
                "month_pillar": {"heavenly_stem": "乙", "earthly_branch": "丑"},
                "day_pillar": {"heavenly_stem": "丙", "earthly_branch": "寅"},
                "time_pillar": {"heavenly_stem": "丁", "earthly_branch": "卯"}
            },
            "ten_gods": {}
        })
        
        result = EventJsonValidator.validate_bazi_json(json_string)
        assert isinstance(result, BaziResultModel)
    
    def test_invalid_bazi_json_empty_stem(self):
        """测试无效的 bazi_json - 空天干"""
        invalid_data = {
            "pillars_primary": {
                "year_pillar": {"heavenly_stem": "", "earthly_branch": "子"},
                "month_pillar": {"heavenly_stem": "乙", "earthly_branch": "丑"},
                "day_pillar": {"heavenly_stem": "丙", "earthly_branch": "寅"},
                "time_pillar": {"heavenly_stem": "丁", "earthly_branch": "卯"}
            },
            "ten_gods": {}
        }
        
        with pytest.raises(ValidationError):
            EventJsonValidator.validate_bazi_json(invalid_data)
    
    def test_invalid_json_format(self):
        """测试无效的 JSON 格式"""
        invalid_json_string = "{ invalid json }"
        
        with pytest.raises(ValueError):
            EventJsonValidator.validate_bazi_json(invalid_json_string)
    
    def test_valid_recommendation(self):
        """测试有效的推荐信息"""
        valid_data = {
            "title": "八字分析建议",
            "description": "根据您的八字...",
            "advice": ["建议1", "建议2"],
            "confidence": 0.95
        }
        
        result = EventJsonValidator.validate_recommendation(valid_data)
        assert result.title == "八字分析建议"
        assert len(result.advice or []) == 2
        assert result.confidence == 0.95
    
    def test_invalid_recommendation_confidence(self):
        """测试无效的推荐信息 - 置信度超出范围"""
        invalid_data = {
            "title": "测试",
            "confidence": 1.5  # 超出 0-1 范围
        }
        
        with pytest.raises(ValidationError):
            EventJsonValidator.validate_recommendation(invalid_data)
    
    def test_valid_five_elements(self):
        """测试有效的五行数据"""
        valid_data = {
            "wood": 25.5,
            "fire": 20.0,
            "earth": 15.5,
            "metal": 22.0,
            "water": 17.0
        }
        
        result = EventJsonValidator.validate_five_elements(valid_data)
        assert result.wood == 25.5
        assert result.fire == 20.0
    
    def test_invalid_five_elements_value_out_of_range(self):
        """测试无效的五行数据 - 值超出范围"""
        invalid_data = {
            "wood": 150.0,  # 超出 0-100 范围
            "fire": 20.0,
            "earth": 15.5,
            "metal": 22.0,
            "water": 17.0
        }
        
        with pytest.raises(ValidationError):
            EventJsonValidator.validate_five_elements(invalid_data)


class TestScenarioJsonValidators:
    """Scenario JSON 验证测试"""
    
    def test_valid_scenario_variations(self):
        """测试有效的场景变量"""
        valid_data = {
            "name": "时间调整场景",
            "description": "调整出生时间1小时",
            "time_adjustment": {
                "hours_offset": 1,
                "minutes_offset": 0
            }
        }
        
        result = ScenarioJsonValidator.validate_variations(valid_data)
        assert result.name == "时间调整场景"
        assert result.time_adjustment and result.time_adjustment.hours_offset == 1
    
    def test_invalid_scenario_variations_out_of_range(self):
        """测试无效的场景变量 - 偏移量超出范围"""
        invalid_data = {
            "name": "测试",
            "time_adjustment": {
                "hours_offset": 25,  # 超出 -24 到 24 范围
                "minutes_offset": 0
            }
        }
        
        with pytest.raises(ValidationError):
            ScenarioJsonValidator.validate_variations(invalid_data)
    
    def test_valid_location_adjustment(self):
        """测试有效的地点调整"""
        valid_data = {
            "name": "地点调整场景",
            "location_adjustment": {
                "longitude": 120.5,
                "latitude": 30.5,
                "timezone_offset": 8
            }
        }
        
        result = ScenarioJsonValidator.validate_variations(valid_data)
        assert result.location_adjustment and result.location_adjustment.longitude == 120.5
        assert result.location_adjustment and result.location_adjustment.latitude == 30.5
    
    def test_invalid_location_longitude_out_of_range(self):
        """测试无效的经度"""
        invalid_data = {
            "name": "测试",
            "location_adjustment": {
                "longitude": 200.0,  # 超出 -180 到 180 范围
                "latitude": 30.5
            }
        }
        
        with pytest.raises(ValidationError):
            ScenarioJsonValidator.validate_variations(invalid_data)


class TestJsonValidatorEdgeCases:
    """JSON 验证器边界情况测试"""
    
    def test_bazi_json_with_secondary_pillars(self):
        """测试包含次要四柱的 bazi_json"""
        data = {
            "pillars_primary": {
                "year_pillar": {"heavenly_stem": "甲", "earthly_branch": "子"},
                "month_pillar": {"heavenly_stem": "乙", "earthly_branch": "丑"},
                "day_pillar": {"heavenly_stem": "丙", "earthly_branch": "寅"},
                "time_pillar": {"heavenly_stem": "丁", "earthly_branch": "卯"}
            },
            "pillars_secondary": {
                "year_pillar": {"heavenly_stem": "戊", "earthly_branch": "辰"},
                "month_pillar": {"heavenly_stem": "己", "earthly_branch": "巳"},
                "day_pillar": {"heavenly_stem": "庚", "earthly_branch": "午"},
                "time_pillar": {"heavenly_stem": "辛", "earthly_branch": "未"}
            },
            "ten_gods": {}
        }
        
        result = EventJsonValidator.validate_bazi_json(data)
        assert result.pillars_secondary is not None
        assert result.pillars_secondary.year_pillar.heavenly_stem == "戊"
    
    def test_recommendation_with_only_title(self):
        """测试只有标题的推荐信息"""
        data = {
            "title": "快速建议"
        }
        
        result = EventJsonValidator.validate_recommendation(data)
        assert result.title == "快速建议"
        assert result.advice is None
    
    def test_five_elements_with_string_numbers(self):
        """测试五行数据转换字符串数字"""
        data = {
            "wood": "25.5",  # 字符串
            "fire": 20.0,
            "earth": 15,  # 整数
            "metal": "22",  # 字符串整数
            "water": 17.0
        }
        
        result = EventJsonValidator.validate_five_elements(data)
        assert result.wood == 25.5
        assert isinstance(result.fire, float)


class TestMissingJsonValidation:
    """缺失数据的验证测试"""
    
    def test_bazi_json_missing_pillars(self):
        """测试缺失四柱数据"""
        incomplete_data = {
            "ten_gods": {}
            # 缺失 pillars_primary
        }
        
        with pytest.raises(ValidationError):
            EventJsonValidator.validate_bazi_json(incomplete_data)
    
    def test_recommendation_with_empty_dict(self):
        """测试空推荐数据"""
        data = {}
        
        result = EventJsonValidator.validate_recommendation(data)
        assert result.title is None
    
    def test_scenario_variations_missing_name(self):
        """测试缺失场景名称"""
        incomplete_data = {
            "description": "测试场景"
            # 缺失 name
        }
        
        with pytest.raises(ValidationError):
            ScenarioJsonValidator.validate_variations(incomplete_data)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
