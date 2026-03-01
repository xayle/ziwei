"""
JSON Schema 验证服务
用于强化 Event 和 Scenario 表中 JSON 字段的数据验证
"""
import json
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator, ValidationError
from datetime import datetime


# ============================================================================
# Event JSON Models - 八字计算结果验证
# ============================================================================

class PillarModel(BaseModel):
    """八字柱子模型 (年/月/日/时)"""
    heavenly_stem: str = Field(..., min_length=1, max_length=10)
    earthly_branch: str = Field(..., min_length=1, max_length=10)
    
    @field_validator('heavenly_stem', 'earthly_branch')
    @classmethod
    def validate_stem_branch(cls, v: str) -> str:
        """验证天干地支格式"""
        if not v or len(v.strip()) == 0:
            raise ValueError("天干地支不能为空")
        return v.strip()


class PillarsModel(BaseModel):
    """四柱模型"""
    year_pillar: PillarModel
    month_pillar: PillarModel
    day_pillar: PillarModel
    time_pillar: PillarModel


class TenGodsModel(BaseModel):
    """十神模型 - 描述各柱的十神关系"""
    year_ten_god: Optional[str] = None
    month_ten_god: Optional[str] = None
    day_ten_god: Optional[str] = None
    time_ten_god: Optional[str] = None


class FiveElementsModel(BaseModel):
    """五行评分模型"""
    wood: float = Field(default=0.0, ge=0.0, le=100.0)
    fire: float = Field(default=0.0, ge=0.0, le=100.0)
    earth: float = Field(default=0.0, ge=0.0, le=100.0)
    metal: float = Field(default=0.0, ge=0.0, le=100.0)
    water: float = Field(default=0.0, ge=0.0, le=100.0)
    
    @field_validator('wood', 'fire', 'earth', 'metal', 'water', mode='before')
    @classmethod
    def validate_element_score(cls, v):
        """确保五行评分为数字"""
        if isinstance(v, str):
            try:
                return float(v)
            except ValueError:
                raise ValueError(f"五行评分必须是有效的数字，得到: {v}")
        return v


class BaziResultModel(BaseModel):
    """八字完整计算结果模型 - 用于验证 Event.bazi_json"""
    pillars_primary: PillarsModel
    pillars_secondary: Optional[PillarsModel] = None
    ten_gods: TenGodsModel
    five_elements: Optional[FiveElementsModel] = None
    calculated_at: Optional[str] = None  # ISO 格式时间戳
    
    @field_validator('calculated_at', mode='before')
    @classmethod
    def validate_timestamp(cls, v):
        """验证时间戳格式"""
        if v is None:
            return None
        if isinstance(v, str):
            try:
                # 尝试解析 ISO 格式时间
                datetime.fromisoformat(v.replace('Z', '+00:00'))
                return v
            except ValueError:
                raise ValueError(f"无效的时间戳格式: {v}")
        return v


class RecommendationModel(BaseModel):
    """推荐信息模型"""
    title: Optional[str] = None
    description: Optional[str] = None
    advice: Optional[List[str]] = None  # 建议列表
    warning: Optional[str] = None  # 警告信息
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)


class EventJsonValidator:
    """Event 表 JSON 字段验证器"""
    
    @staticmethod
    def validate_bazi_json(data: str | Dict[str, Any]) -> BaziResultModel:
        """
        验证 Event.bazi_json 字段
        
        Args:
            data: JSON 字符串或字典
            
        Returns:
            BaziResultModel 实例
            
        Raises:
            ValidationError: 如果 JSON 数据不符合模式
        """
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError as e:
                raise ValueError(f"无效的 JSON 格式: {str(e)}")
        
        return BaziResultModel(**data)  # type: ignore[arg-type]
    
    @staticmethod
    def validate_recommendation(data: str | Dict[str, Any]) -> RecommendationModel:
        """
        验证 Event.recommendation 字段
        
        Args:
            data: JSON 字符串或字典
            
        Returns:
            RecommendationModel 实例
            
        Raises:
            ValidationError: 如果数据不符合模式
        """
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError as e:
                raise ValueError(f"无效的 JSON 格式: {str(e)}")
        
        return RecommendationModel(**data)  # type: ignore[arg-type]
    
    @staticmethod
    def validate_five_elements(data: str | Dict[str, Any]) -> FiveElementsModel:
        """
        验证 Event.five_elements 字段
        
        Args:
            data: JSON 字符串或字典
            
        Returns:
            FiveElementsModel 实例
        """
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError as e:
                raise ValueError(f"无效的 JSON 格式: {str(e)}")
        
        return FiveElementsModel(**data)  # type: ignore[arg-type]


# ============================================================================
# Scenario JSON Models - 场景变量验证
# ============================================================================

class TimeAdjustmentModel(BaseModel):
    """时间调整场景"""
    hours_offset: int = Field(default=0, ge=-24, le=24)
    minutes_offset: int = Field(default=0, ge=-60, le=60)


class LocationAdjustmentModel(BaseModel):
    """地点调整场景"""
    longitude: float = Field(..., ge=-180.0, le=180.0)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    timezone_offset: int = Field(default=0, ge=-14, le=14)


class ScenarioVariationsModel(BaseModel):
    """场景变量模型"""
    name: str
    description: Optional[str] = None
    time_adjustment: Optional[TimeAdjustmentModel] = None
    location_adjustment: Optional[LocationAdjustmentModel] = None


class ScenarioResultModel(BaseModel):
    """场景结果模型"""
    scenario_id: int
    pillars_adjusted: Optional[PillarsModel] = None
    changes: Optional[Dict[str, Any]] = None  # 与基础成员的差异
    significance: Optional[str] = None  # "minor", "moderate", "major"


class ScenarioJsonValidator:
    """Scenario 表 JSON 字段验证器"""
    
    @staticmethod
    def validate_variations(data: str | Dict[str, Any]) -> ScenarioVariationsModel:
        """
        验证 Scenario.variations 字段
        
        Args:
            data: JSON 字符串或字典
            
        Returns:
            ScenarioVariationsModel 实例
        """
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError as e:
                raise ValueError(f"无效的 JSON 格式: {str(e)}")
        
        return ScenarioVariationsModel(**data)  # type: ignore[arg-type]
    
    @staticmethod
    def validate_results(data: str | List | Dict[str, Any]) -> List[ScenarioResultModel]:
        """
        验证 Scenario.results 字段 (JSON 数组)
        
        Args:
            data: JSON 字符串、字符或字典列表
            
        Returns:
            ScenarioResultModel 列表
        """
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError as e:
                raise ValueError(f"无效的 JSON 格式: {str(e)}")
        
        if not isinstance(data, list):
            raise ValueError(f"Scenario.results 必须是 JSON 数组，得到: {type(data).__name__}")
        
        return [ScenarioResultModel(**item) for item in data]


# ============================================================================
# 通用辅助函数
# ============================================================================

def validate_json_string(json_str: str, model_class: type[BaseModel]) -> BaseModel:
    """
    通用 JSON 验证函数
    
    Args:
        json_str: JSON 字符串
        model_class: Pydantic 模型类
        
    Returns:
        已验证的模型实例
        
    Raises:
        ValueError: 如果 JSON 无效
        ValidationError: 如果数据不符合模式
    """
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"无效的 JSON 格式: {str(e)}")
    
    return model_class(**data)


def safe_validate_json(json_str: str, model_class: type[BaseModel]) -> Optional[BaseModel]:
    """
    安全的 JSON 验证函数 - 返回 None 而不是抛出异常
    
    Args:
        json_str: JSON 字符串
        model_class: Pydantic 模型类
        
    Returns:
        已验证的模型实例或 None (如果验证失败)
    """
    try:
        return validate_json_string(json_str, model_class)
    except (ValueError, ValidationError):
        return None
