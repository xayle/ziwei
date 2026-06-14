"""Legacy schema shim - re-exports from app.schemas to avoid duplicate class definitions.

All actual class definitions live in app/schemas/bazi.py.
Importing from this module gives the same Python objects as importing from app.schemas,
so type-checkers treat them as identical.
"""

from __future__ import annotations

# Re-export everything from the canonical location
from app.schemas import (
    BackendInfo,
    BaziFullRequest,
    BaziFullResponse,
    BaziMethodsModel,
    BaziRawDayunModel,
    BaziRawModel,
    ChildHintModel,
    DayMasterStrengthModel,
    DaYunItemModel,
    DaYunModel,
    LiuNianItemModel,
    LiuNianResultModel,
    LoveWindowModel,
    MarriageFlagsModel,
    MarriageModel,
    # BaZi
    PillarModel,
    PillarsModel,
    RangeModel,
    RiskFlagsModel,
    SocialModel,
    StrengthFactorModel,
    TenGodsModel,
    ValidationModel,
    VerifyRequest,
    VerifyResponse,
    # Common
    WarningModel,
    WealthModel,
    WuXingBreakdownModel,
    WuXingScoreModel,
    YongShenModel,
)

__all__ = [
    "BackendInfo",
    "BaziFullRequest",
    "BaziFullResponse",
    "BaziMethodsModel",
    "BaziRawDayunModel",
    "BaziRawModel",
    "ChildHintModel",
    "DaYunItemModel",
    "DaYunModel",
    "DayMasterStrengthModel",
    "LiuNianItemModel",
    "LiuNianResultModel",
    "LoveWindowModel",
    "MarriageFlagsModel",
    "MarriageModel",
    "PillarModel",
    "PillarsModel",
    "RangeModel",
    "RiskFlagsModel",
    "SocialModel",
    "StrengthFactorModel",
    "TenGodsModel",
    "ValidationModel",
    "VerifyRequest",
    "VerifyResponse",
    "WarningModel",
    "WealthModel",
    "WuXingBreakdownModel",
    "WuXingScoreModel",
    "YongShenModel",
]
