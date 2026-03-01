"""Legacy schema shim - re-exports from app.schemas to avoid duplicate class definitions.

All actual class definitions live in app/schemas/bazi.py.
Importing from this module gives the same Python objects as importing from app.schemas,
so type-checkers treat them as identical.
"""
from __future__ import annotations

# Re-export everything from the canonical location
from app.schemas import (
    # Common
    WarningModel,
    RangeModel,
    BackendInfo,
    # BaZi
    PillarModel,
    PillarsModel,
    RiskFlagsModel,
    ValidationModel,
    MarriageFlagsModel,
    LoveWindowModel,
    ChildHintModel,
    TenGodsModel,
    StrengthFactorModel,
    DayMasterStrengthModel,
    WuXingScoreModel,
    WuXingBreakdownModel,
    YongShenModel,
    DaYunModel,
    DaYunItemModel,
    LiuNianItemModel,
    LiuNianResultModel,
    BaziRawDayunModel,
    BaziRawModel,
    BaziMethodsModel,
    WealthModel,
    MarriageModel,
    SocialModel,
    VerifyRequest,
    VerifyResponse,
    BaziFullRequest,
    BaziFullResponse,
)

__all__ = [
    "WarningModel", "RangeModel", "BackendInfo",
    "PillarModel", "PillarsModel", "RiskFlagsModel", "ValidationModel",
    "MarriageFlagsModel", "LoveWindowModel", "ChildHintModel",
    "TenGodsModel", "StrengthFactorModel", "DayMasterStrengthModel",
    "WuXingScoreModel", "WuXingBreakdownModel", "YongShenModel",
    "DaYunModel", "DaYunItemModel", "LiuNianItemModel", "LiuNianResultModel",
    "BaziRawDayunModel", "BaziRawModel", "BaziMethodsModel",
    "WealthModel", "MarriageModel", "SocialModel",
    "VerifyRequest", "VerifyResponse", "BaziFullRequest", "BaziFullResponse",
]
