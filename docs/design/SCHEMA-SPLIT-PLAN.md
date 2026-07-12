# Schema Split Plan — 2026-06-15

## Target: Split 3 mega-files into domain submodules

### analysis.py (18,607 lines, 20 classes)
→ 5 files:
  - analysis_core.py:    LifeArcModel, GejuModel, PalaceItemModel, PalaceModel, ShenshaModel
  - analysis_domains.py: WealthAnalysisModel, CareerAnalysisModel, MarriageAnalysisModel,
                         HealthAnalysisModel, RelationshipAnalysisModel
  - analysis_personality.py: PersonalityModel
  - analysis_temporal.py: MonthlyFortuneModel, MilestoneModel, LiuNianDetailModel,
                          CurrentFortuneSummaryModel
  - analysis_lifestyle.py: JewelryItemModel, JewelryModel, FengshuiModel, LifestyleModel, LuckyModel

### bazi.py (22,149 lines, 30 classes)
→ 5 files:
  - bazi_basic.py:    PillarModel, PillarsModel, RiskFlagsModel, ValidationModel
  - bazi_marriage.py: MarriageFlagsModel, LoveWindowModel, ChildHintModel, MarriageModel
  - bazi_strength.py: TenGodsModel, StrengthFactorModel, DayMasterStrengthModel,
                      WuXingScoreModel, WuXingBreakdownModel, YongShenModel
  - bazi_dayun.py:    DaYunItemModel, DaYunModel, LiuNianItemModel, LiuNianResultModel
  - bazi_wealth.py:   WealthModel, SocialModel, VerifyRequest, VerifyResponse, etc.

### ziwei.py (14,301 lines, 23 classes)
→ 4 files:
  - ziwei_basic.py:    ZiweiRequest, StarInfo, PalaceResponse, LunarResponse
  - ziwei_dayun.py:    DayunItemResponse, DayunResponse, LiunianResponse, LiuyueItem
  - ziwei_analysis.py: EventTagResponse, PeriodForecastResponse, ForecastResultResponse,
                       PatternResponse, RemedyResponse, LifeSuggestionResponse
  - ziwei_compat.py:   CompatibilityRequest, CompatibilityDimensionResponse, CompatibilityResponse
  - ziwei_flying.py:   FlyingPalaceResponse, FlyingChartResponse

## Execution procedure (per file):
1. Create submodule files with copied class+import blocks
2. Replace original file with re-export shim: `from .submodule import Class1, Class2`
3. Update app/schemas/__init__.py if needed
4. Run `python -m pytest tests -q --tb=no` to verify no regressions

## Priority: analysis.py (clearest domain boundaries) → bazi.py → ziwei.py
