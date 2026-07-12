"""API schemas 包 - 集中导出所有Pydantic models."""

from __future__ import annotations

# Analysis (M2)
from .analysis_core import (
    GejuModel,
    LifeArcModel,
    PalaceItemModel,
    PalaceModel,
    ShenshaModel,
)
from .analysis_domains import (
    CareerAnalysisModel,
    HealthAnalysisModel,
    MarriageAnalysisModel,
    PersonalityModel,
    RelationshipAnalysisModel,
    WealthAnalysisModel,
)
from .analysis_lifestyle import FengshuiModel, JewelryItemModel, JewelryModel, LifestyleModel, LuckyModel
from .analysis_temporal import CurrentFortuneSummaryModel, LiuNianDetailModel, MilestoneModel, MonthlyFortuneModel

# BaZi
from .bazi import (
    AdjustmentSummaryModel,
    BatchVerifyRequest,
    BatchVerifyResponse,
    BaziFullRequest,
    BaziFullResponse,
    BaziMethodsModel,
    BaziRawDayunModel,
    BaziRawModel,
    BaziStructuralSummaryModel,
    ChildHintModel,
    ConfidenceSummaryModel,
    DayMasterStrengthModel,
    DaYunItemModel,
    DaYunModel,
    EvidenceItemModel,
    HiddenStemDetailModel,
    LiuNianItemModel,
    LiuNianResultModel,
    LiuriLiushiEndpointResponse,
    LiuriLiushiRequest,
    LoveWindowModel,
    MarriageFlagsModel,
    MarriageModel,
    PillarDetailModel,
    PillarModel,
    PillarShenshaDetailModel,
    PillarsModel,
    RelationItemModel,
    RiskFlagsModel,
    RuleMatchModel,
    ShishenContributionModel,
    ShishenPillarSummaryModel,
    ShishenSummaryModel,
    SocialModel,
    StrengthFactorModel,
    TenGodsModel,
    TimelinePointModel,
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

# Ziwei
from .ziwei import (
    ChartRelationSummaryModel,
    CompatibilityDimensionResponse,
    CompatibilityRequest,
    CompatibilityResponse,
    DayunItemResponse,
    DayunResponse,
    EventTagResponse,
    FlyingChartResponse,
    FlyingPalaceResponse,
    ForecastResultResponse,
    LifeSuggestionResponse,
    LiunianResponse,
    LiuyueItem,
    LunarResponse,
    MultiCompatPairResponse,
    MultiCompatRequest,
    MultiCompatResponse,
    PalaceResponse,
    PatternResponse,
    PeriodForecastResponse,
    RemedyResponse,
    SihuaTraceItemModel,
    StarBrightnessSummaryModel,
    StarInfo,
    ZiweiRequest,
    ZiweiResponse,
    ZiweiStructuralSummaryModel,
)
from .ziwei import (
    ConfidenceSummaryModel as ZiweiConfidenceSummaryModel,
)
from .ziwei import (
    EvidenceItemModel as ZiweiEvidenceItemModel,
)
from .ziwei import (
    PalaceWeightModel as ZiweiPalaceWeightModel,
)
from .ziwei import (
    TimelinePointModel as ZiweiTimelinePointModel,
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
    "ShishenPillarSummaryModel",
    "ShishenContributionModel",
    "ShishenSummaryModel",
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
    "HiddenStemDetailModel",
    "EvidenceItemModel",
    "TimelinePointModel",
    "PillarDetailModel",
    "PillarShenshaDetailModel",
    "RelationItemModel",
    "AdjustmentSummaryModel",
    "ConfidenceSummaryModel",
    "BaziStructuralSummaryModel",
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
    # Ziwei
    "EvidenceItemModel",
    "TimelinePointModel",
    "SihuaTraceItemModel",
    "StarBrightnessSummaryModel",
    "ChartRelationSummaryModel",
    "ZiweiStructuralSummaryModel",
    "ZiweiEvidenceItemModel",
    "ZiweiTimelinePointModel",
    "ZiweiPalaceWeightModel",
    "ZiweiConfidenceSummaryModel",
]
