"""API schemas 包 - 集中导出所有Pydantic models."""

from __future__ import annotations

# Analysis (M2)
from .analysis import (
    CareerAnalysisModel,
    CurrentFortuneSummaryModel,
    FengshuiModel,
    GejuModel,
    HealthAnalysisModel,
    JewelryItemModel,
    JewelryModel,
    LifeArcModel,
    LifestyleModel,
    LiuNianDetailModel,
    LuckyModel,
    MarriageAnalysisModel,
    MilestoneModel,
    MonthlyFortuneModel,
    PalaceItemModel,
    PalaceModel,
    PersonalityModel,
    RelationshipAnalysisModel,
    ShenshaModel,
    WealthAnalysisModel,
)

# BaZi
from .bazi import (
    BatchVerifyRequest,
    BatchVerifyResponse,
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
    PillarModel,
    PillarsModel,
    RiskFlagsModel,
    RuleMatchModel,
    SocialModel,
    StrengthFactorModel,
    TenGodsModel,
    ValidationModel,
    VerifyRequest,
    VerifyResponse,
    WealthModel,
    WuXingBreakdownModel,
    WuXingScoreModel,
    YongShenModel,
)

# Cases
from .case import (
    CaseBase,
    CaseCreate,
    CaseListResponse,
    CaseOut,
    CasePatch,
    SnapshotOut,
)

# Common
from .common import (
    BackendInfo,
    RangeModel,
    WarningModel,
)

# Compute
from .compute import (
    ComputeRequest,
    ComputeResponse,
    ComputeTaskStatus,
)

# Relations
from .relation import (
    RelationComputeRequest,
    RelationComputeResponse,
    RelationPoint,
    RelationProfile,
    RelationResult,
    RelationType,
)

__all__ = [
    # Analysis (M2)
    "LifeArcModel",
    "GejuModel",
    "PalaceItemModel",
    "PalaceModel",
    "ShenshaModel",
    "WealthAnalysisModel",
    "CareerAnalysisModel",
    "MarriageAnalysisModel",
    "HealthAnalysisModel",
    "RelationshipAnalysisModel",
    "PersonalityModel",
    "MonthlyFortuneModel",
    "JewelryItemModel",
    "JewelryModel",
    "FengshuiModel",
    "LifestyleModel",
    "LuckyModel",
    "MilestoneModel",
    "LiuNianDetailModel",
    "CurrentFortuneSummaryModel",
    # Common
    "WarningModel",
    "RangeModel",
    "BackendInfo",
    # BaZi
    "PillarModel",
    "PillarsModel",
    "RiskFlagsModel",
    "ValidationModel",
    "MarriageFlagsModel",
    "LoveWindowModel",
    "ChildHintModel",
    "TenGodsModel",
    "StrengthFactorModel",
    "DayMasterStrengthModel",
    "WuXingScoreModel",
    "WuXingBreakdownModel",
    "YongShenModel",
    "DaYunModel",
    "DaYunItemModel",
    "LiuNianItemModel",
    "LiuNianResultModel",
    "BaziRawDayunModel",
    "BaziRawModel",
    "BaziMethodsModel",
    "WealthModel",
    "MarriageModel",
    "SocialModel",
    "VerifyRequest",
    "VerifyResponse",
    "BatchVerifyRequest",
    "BatchVerifyResponse",
    "BaziFullRequest",
    "BaziFullResponse",
    "RuleMatchModel",
    # Cases
    "CaseBase",
    "CaseCreate",
    "CasePatch",
    "CaseOut",
    "SnapshotOut",
    "CaseListResponse",
    # Relations
    "RelationComputeRequest",
    "RelationComputeResponse",
    "RelationPoint",
    "RelationProfile",
    "RelationResult",
    "RelationType",
    # Compute
    "ComputeRequest",
    "ComputeResponse",
    "ComputeTaskStatus",
]
