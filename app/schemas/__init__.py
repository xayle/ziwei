"""API schemas 包 - 集中导出所有Pydantic models."""
from __future__ import annotations

# Analysis (M2)
from .analysis import (
    LifeArcModel,
    GejuModel,
    PalaceItemModel,
    PalaceModel,
    ShenshaModel,
    WealthAnalysisModel,
    CareerAnalysisModel,
    MarriageAnalysisModel,
    HealthAnalysisModel,
    RelationshipAnalysisModel,
    PersonalityModel,
    MonthlyFortuneModel,
    JewelryItemModel,
    JewelryModel,
    FengshuiModel,
    LifestyleModel,
    LuckyModel,
    MilestoneModel,
    LiuNianDetailModel,
    CurrentFortuneSummaryModel,
)

# Common
from .common import (
    WarningModel,
    RangeModel,
    BackendInfo,
)

# BaZi
from .bazi import (
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
    BatchVerifyRequest,
    BatchVerifyResponse,
    BaziFullRequest,
    BaziFullResponse,
    RuleMatchModel,
)

# Cases
from .case import (
    CaseBase,
    CaseCreate,
    CasePatch,
    CaseOut,
    SnapshotOut,
    CaseListResponse,
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

# Compute
from .compute import (
    ComputeRequest,
    ComputeResponse,
    ComputeTaskStatus,
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
