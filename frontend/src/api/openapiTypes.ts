/**
 * OpenAPI schema 类型桥接（DEV-AUDIT P3-3）
 *
 * 请求体 / 响应体以 `schema.d.ts` 为真源；`bazi.ts` 等模块通过此处 re-export，
 * 不再重复手写与 OpenAPI 已对齐的字段。
 */
import type { components } from './schema'

export type SchemaComponents = components

type S = SchemaComponents['schemas']

// ── /bazi/full ─────────────────────────────────────────────
export type BaziFullRequest = S['BaziFullRequest']
export type BaziFullResponse = S['BaziFullResponse']

// ── BaziFullResponse 嵌套模型 ───────────────────────────────
export type PillarModel = S['PillarModel']
export type PillarsModel = S['PillarsModel']
export type TenGodsModel = S['TenGodsModel']
export type YongShenModel = S['YongShenModel']
export type StrengthFactorModel = S['StrengthFactorModel']
export type DayMasterStrengthModel = S['DayMasterStrengthModel']
export type GejuModel = S['GejuModel']
export type DaYunItemModel = S['DaYunItemModel']
export type DaYunModel = S['DaYunModel']
export type WuXingScoreModel = S['WuXingScoreModel']
export type ShenshaModel = S['ShenshaModel']
export type LifeArcModel = S['LifeArcModel']
export type PersonalityModel = S['PersonalityModel']
export type WealthAnalysisModel = S['WealthAnalysisModel']
export type CareerAnalysisModel = S['CareerAnalysisModel']
export type MarriageAnalysisModel = S['MarriageAnalysisModel']
export type HealthAnalysisModel = S['HealthAnalysisModel']
export type MonthlyFortuneModel = S['MonthlyFortuneModel']
export type LuckyModel = S['LuckyModel']
export type CurrentFortuneSummaryModel = S['CurrentFortuneSummaryModel']
export type ShishenPillarSummaryModel = S['ShishenPillarSummaryModel']
export type ShishenContributionModel = S['ShishenContributionModel']
export type ShishenSummaryModel = S['ShishenSummaryModel']
export type LiuNianDetailModel = S['LiuNianDetailModel']
export type MilestoneModel = S['MilestoneModel']
export type RelationshipAnalysisModel = S['RelationshipAnalysisModel']
export type JewelryItemModel = S['JewelryItemModel']
export type JewelryModel = S['JewelryModel']
export type FengshuiModel = S['FengshuiModel']
export type LifestyleModel = S['LifestyleModel']
export type PalaceItemModel = S['PalaceItemModel']
export type PalaceModel = S['PalaceModel']
export type WarningModel = S['WarningModel']
export type RuleMatchModel = S['RuleMatchModel']
export type ProvenanceLayer = S['ProvenanceLayer']
export type ResponseProvenance = S['ResponseProvenance']
export type LiuriLiushiModel = S['LiuriLiushiModel']
export type DayunTransitionModel = S['DayunTransitionModel']
export type RiskFlagsModel = S['RiskFlagsModel']
export type ValidationModel = S['ValidationModel']
export type RelationsSummaryModel = S['RelationsSummaryModel']
export type ShenshaSummaryModel = S['ShenshaSummaryModel']

// ── 补充端点 ────────────────────────────────────────────────
export type LiuriLiushiRequest = S['LiuriLiushiRequest']
export type LiuriLiushiEndpointResponse = S['LiuriLiushiEndpointResponse']
export type LiunianDomainRequest = S['LiunianDomainRequest']
export type LiunianDomainResponse = S['LiunianDomainResponse']
export type DayunReportRequest = S['DayunReportRequest']
export type DayunReportItem = S['DayunReportItem']
export type DayunReportResponse = S['DayunReportResponse']
export type BaziCompatibilityRequest = S['routers__bazi__CompatibilityRequest']
export type BaziCompatibilityResponse = S['routers__bazi__CompatibilityResponse']
export type CompatibilitySubject = S['CompatibilitySubject']
export type MonthlyRequest = S['MonthlyRequest']
export type MonthlyItemOut = S['MonthlyItemOut']
export type MonthlyResponse = S['MonthlyResponse']
export type AnalyzeRequest = S['AnalyzeRequest']
export type JieqiItemOut = S['JieqiItemOut']
export type JieqiResponse = S['JieqiResponse']
export type GejuSubjectRequest = S['GejuSubjectRequest']
export type GejuLightResponse = S['GejuLightResponse']
export type CalendarCompareRequest = S['CalendarCompareRequest']
export type CalendarCompareResponse = S['CalendarCompareResponse']
export type PillarOut = S['PillarOut']
export type LunarToSolarRequest = S['LunarToSolarRequest']
export type LunarToSolarResponse = S['LunarToSolarResponse']
export type BatchCompareRequest = S['BatchCompareRequest']
export type BatchCompareResponse = S['BatchCompareResponse']
export type BatchCaseProfile = S['BatchCaseProfile']
export type LiunianReportRequest = S['LiunianReportRequest']
export type LiunianReportResponse = S['LiunianReportResponse']

/** OpenAPI 未建模的 golden-cases 响应体 */
export type GoldenCasesResponse = {
  total: number
  cases: Array<Record<string, unknown>>
}

// ── /ziwei/full ────────────────────────────────────────────
export type SchemaZiweiRequest = S['ZiweiRequest']
export type ZiweiFullResponse = S['ZiweiResponse']

// ── ZiweiResponse 嵌套模型 ──────────────────────────────────
export type StarInfo = S['StarInfo']
export type PalaceStructuredAnalysis = S['PalaceStructuredAnalysis']
export type LiuriItem = S['LiuriItem']
export type LiushiItem = S['LiushiItem']
export type LiuriLiushiResponse = S['LiuriLiushiResponse']
export type PalaceResponse = S['PalaceResponse']
export type LunarResponse = S['LunarResponse']
export type ZiweiDayunItemResponse = S['DayunItemResponse']
export type ZiweiDayunResponse = S['DayunResponse']
export type PatternResponse = S['PatternResponse']
export type LiunianResponse = S['LiunianResponse']
export type LiuyueItem = S['LiuyueItem']
export type IztroDualTrackResponse = S['IztroDualTrackResponse']
export type IztroCrosscheckResponse = S['IztroCrosscheckResponse']
export type FlyingPalaceResponse = S['FlyingPalaceResponse']
export type FlyingChartResponse = S['FlyingChartResponse']
export type EventTagResponse = S['EventTagResponse']
export type PeriodForecastResponse = S['PeriodForecastResponse']
export type ForecastResultResponse = S['ForecastResultResponse']
export type RemedyResponse = S['RemedyResponse']
export type LifeSuggestionResponse = S['LifeSuggestionResponse']
export type EvidenceItemModel = S['EvidenceItemModel']
export type TimelinePointModel = S['TimelinePointModel']
export type PalaceWeightModel = S['PalaceWeightModel']
export type SihuaTraceItemModel = S['SihuaTraceItemModel']
export type StarBrightnessSummaryModel = S['StarBrightnessSummaryModel']
export type ChartRelationSummaryModel = S['ChartRelationSummaryModel']
export type ZiweiConfidenceSummaryModel = S['app__schemas__ziwei__ConfidenceSummaryModel']
export type PalaceRefModel = S['PalaceRefModel']
export type SanfangStructureModel = S['SanfangStructureModel']
export type ZiweiChartStructuralSummaryModel = S['ZiweiChartStructuralSummaryModel']
export type ZiweiCoreSnapshotModel = S['ZiweiCoreSnapshotModel']
export type PatternSummaryBlockModel = S['PatternSummaryBlockModel']
export type ReportSummaryBlockModel = S['ReportSummaryBlockModel']
export type SihuaTraceEntryModel = S['SihuaTraceEntryModel']
export type KeyYearPointModel = S['KeyYearPointModel']
export type KeyMonthPointModel = S['KeyMonthPointModel']
export type ZiweiStructuralSummaryModel = S['ZiweiStructuralSummaryModel']

// ── 紫微补充端点 ────────────────────────────────────────────
export type ZiweiCompatibilityRequest = S['app__schemas__ziwei__CompatibilityRequest']
export type ZiweiCompatibilityResponse = S['app__schemas__ziwei__CompatibilityResponse']
export type CompatibilityDimensionResponse = S['CompatibilityDimensionResponse']
export type MultiCompatRequest = S['MultiCompatRequest']
export type MultiCompatPairResponse = S['MultiCompatPairResponse']
export type MultiCompatResponse = S['MultiCompatResponse']

// ── /relation/full · /profile/{id}/summary ─────────────────
export type RelationFullRequest = S['RelationFullRequest']
export type RelationFullResponse = S['RelationFullResponse']
export type RelationPersonInput = S['RelationPersonInput']
export type RelationFullOptions = S['RelationFullOptions']
export type RelationExplainBatchRequest = S['RelationExplainBatchRequest']
export type ProfileSummaryResponse = S['ProfileSummaryResponse']
export type PersonRefModel = S['PersonRefModel']
export type SummaryCardModel = S['SummaryCardModel']
export type DimensionScoreModel = S['DimensionScoreModel']
export type PalaceCrossModel = S['PalaceCrossModel']
export type TimelineNodeModel = S['TimelineNodeModel']
export type ActionItemModel = S['ActionItemModel']
export type TensionNoteModel = S['TensionNoteModel']
export type LayerBlockModel = S['LayerBlockModel']

// ── /fusheng/archive-bundle · report/pdf ───────────────────
export type ArchiveBundleRequest = S['ArchiveBundleRequest']
export type SchemaArchiveBundleResponse = S['ArchiveBundleResponse']
export type ArchiveExtensionPointer = S['ArchiveExtensionPointer']
export type FushengReportPdfRequest = S['FushengReportPdfRequest']

// ── /bazi|ziwei/explain/batch ──────────────────────────────
export type ExplainBatchResponse = S['ExplainBatchResponse']
export type ExplainBlockModel = S['ExplainBlockModel']
export type ExplainSectionResultModel = S['ExplainSectionResultModel']
export type DisclaimerBlockModel = S['DisclaimerBlockModel']

// ── /life/volumes/{case_id} · /life/snippets/{case_id} ─────
export type LifeVolumeResponseModel = S['LifeVolumeResponseModel']
export type LifeVolumeModel = S['LifeVolumeModel']
export type VolumeSectionModel = S['VolumeSectionModel']
export type AnalysisBlockModel = S['AnalysisBlockModel']
export type ColophonModel = S['ColophonModel']
export type LifeSnippetsResponseModel = S['LifeSnippetsResponseModel']
export type LifeSnippetHookModel = S['LifeSnippetHookModel']

// ── /cases · snapshots ─────────────────────────────────────
export type CaseCreate = S['CaseCreate']
export type CaseOut = S['CaseOut']
export type CasePatch = S['CasePatch']
export type CaseListResponse = S['app__schemas__case__CaseListResponse']
export type SnapshotCreate = S['SnapshotCreate']
export type SchemaSnapshotOut = S['SnapshotOut']

// ── /auth ──────────────────────────────────────────────────
export type LoginRequest = S['LoginRequest']
export type TokenResponse = S['TokenResponse']
export type RefreshTokenResponse = S['RefreshTokenResponse']

// ── /name ──────────────────────────────────────────────────
export type NameRequest = S['NameRequest']
export type NameAnalysisResponse = S['NameAnalysisResponse']
export type NameSuggestRequest = S['NameSuggestRequest']
export type NameSuggestResponse = S['NameSuggestResponse']
export type NameSuggestionItem = S['NameSuggestionItem']
export type GridInfoResponse = S['GridInfoResponse']
export type SancaiInfoResponse = S['SancaiInfoResponse']
export type CharStrokeInfo = S['CharStrokeInfo']
export type StrokesResponse = S['StrokesResponse']

// ── /similarity ────────────────────────────────────────────
export type SimilarityIndexRequest = S['SimilarityIndexRequest']
export type SimilarityCaseResponse = S['CaseResponse']
export type SimilaritySearchResponse = S['SearchResponse']
export type SimilarResult = S['SimilarResult']

// ── /zeri ──────────────────────────────────────────────────
export type ZeriDayResponse = S['ZeriDayResponse']
export type ZeriMonthResponse = S['ZeriMonthResponse']

// ── /llm ───────────────────────────────────────────────────
export type LlmConfigResponse = S['LlmConfigResponse']
export type LlmInterpretRequest = S['LlmInterpretRequest']
export type LlmDraftResponse = S['LlmDraftResponse']
export type BaziInterpretRequest = S['BaziInterpretRequest']
export type ModuleInterpretRequest = S['ModuleInterpretRequest']
export type ModuleInterpretResponse = S['ModuleInterpretResponse']
export type InterpretModule = S['InterpretModule']

// ── /reviews · /cities ─────────────────────────────────────
export type ChartReviewCreate = S['ChartReviewCreate']
export type ChartReviewResponse = S['ChartReviewResponse']
export type CityModel = S['CityModel']

// ── /analytics/events（T089–T090）──────────────────────────
export type AnalyticsEventItem = S['AnalyticsEventItem']
export type AnalyticsEventsBatchRequest = S['AnalyticsEventsBatchRequest']
export type AnalyticsEventsBatchResponse = S['AnalyticsEventsBatchResponse']
