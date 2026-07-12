"""Backward-compatible shim for analysis schemas.

The actual model definitions now live in smaller submodules to keep the schema
package easier to navigate while preserving existing import paths.
"""

from __future__ import annotations

from .analysis_core import GejuModel, LifeArcModel, PalaceItemModel, PalaceModel, ShenshaModel
from .analysis_domains import (
    CareerAnalysisModel,
    HealthAnalysisModel,
    MarriageAnalysisModel,
    PersonalityModel,
    RelationshipAnalysisModel,
    WealthAnalysisModel,
)
from .analysis_lifestyle import FengshuiModel, JewelryItemModel, JewelryModel, LifestyleModel, LuckyModel
from .analysis_temporal import (
    CurrentFortuneSummaryModel,
    LiuNianDetailModel,
    LiuriLiushiModel,
    MilestoneModel,
    MonthlyFortuneModel,
)

__all__ = [
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
    "LiuriLiushiModel",
]
