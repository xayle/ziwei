import apiClient from './client'
import type {
  ChartRelationSummaryModel,
  EvidenceItemModel,
  FlyingChartResponse,
  IztroCrosscheckResponse,
  IztroDualTrackResponse,
  KeyMonthPointModel,
  KeyYearPointModel,
  MultiCompatRequest,
  MultiCompatResponse,
  PalaceRefModel,
  PalaceWeightModel,
  PatternSummaryBlockModel,
  ReportSummaryBlockModel,
  SanfangStructureModel,
  SchemaZiweiRequest,
  SihuaTraceEntryModel,
  SihuaTraceItemModel,
  StarBrightnessSummaryModel,
  TimelinePointModel,
  ZiweiChartStructuralSummaryModel,
  ZiweiCompatibilityRequest,
  ZiweiCompatibilityResponse,
  ZiweiCoreSnapshotModel,
  ZiweiDayunItemResponse,
  ZiweiDayunResponse,
  ZiweiFullResponse,
  ZiweiStructuralSummaryModel,
  ZiweiConfidenceSummaryModel,
} from './openapiTypes'

// ── 请求 / 响应（OpenAPI 真源 · P3-3）──────────────────────
/** POST /api/v1/ziwei/full — OpenAPI 基线 + FE 扩展字段 */
export type ZiweiRequest = Omit<SchemaZiweiRequest, 'gender'> & {
  gender?: SchemaZiweiRequest['gender']
  /** Timeline 选日；OpenAPI 待正式入库 */
  target_date?: string
}

export type ZiweiResponse = ZiweiFullResponse & Record<string, unknown>

// ── 嵌套模型（FE 别名 · 向后兼容）──────────────────────────
export type DayunItem = ZiweiDayunItemResponse
export type DayunResponse = ZiweiDayunResponse
export type IztroDualTrack = IztroDualTrackResponse
export type IztroCrosscheck = IztroCrosscheckResponse
export type EvidenceItem = EvidenceItemModel
export type TimelinePoint = TimelinePointModel
export type PalaceWeight = PalaceWeightModel
export type PalaceRef = PalaceRefModel
export type SanfangStructure = SanfangStructureModel
export type ZiweiChartStructuralSummary = ZiweiChartStructuralSummaryModel
export type ZiweiCoreSnapshot = ZiweiCoreSnapshotModel
export type PatternSummaryBlock = PatternSummaryBlockModel
export type ReportSummaryBlock = ReportSummaryBlockModel
export type SihuaTraceEntry = SihuaTraceEntryModel
export type KeyYearPoint = KeyYearPointModel
export type KeyMonthPoint = KeyMonthPointModel
export type ZiweiStructuralSummary = ZiweiStructuralSummaryModel
export type ChartRelationSummary = ChartRelationSummaryModel
export type StarBrightnessSummary = StarBrightnessSummaryModel
export type ConfidenceSummary = ZiweiConfidenceSummaryModel
export type SihuaTraceItem = SihuaTraceItemModel

/** @deprecated 合盘主体与 ZiweiRequest 同构 */
export type ZiweiCompatSubject = ZiweiRequest

export type ZiweiFlyingRequest = ZiweiRequest

export type {
  ChartRelationSummaryModel,
  CompatibilityDimensionResponse,
  EventTagResponse,
  EvidenceItemModel,
  FlyingChartResponse,
  FlyingPalaceResponse,
  ForecastResultResponse,
  IztroCrosscheckResponse,
  IztroDualTrackResponse,
  KeyMonthPointModel,
  KeyYearPointModel,
  LifeSuggestionResponse,
  LiunianResponse,
  LiuriItem,
  LiuriLiushiResponse,
  LiushiItem,
  LiuyueItem,
  LunarResponse,
  MultiCompatPairResponse,
  MultiCompatRequest,
  MultiCompatResponse,
  PalaceRefModel,
  PalaceResponse,
  PalaceStructuredAnalysis,
  PalaceWeightModel,
  PatternResponse,
  PatternSummaryBlockModel,
  PeriodForecastResponse,
  RemedyResponse,
  ReportSummaryBlockModel,
  SanfangStructureModel,
  SihuaTraceEntryModel,
  SihuaTraceItemModel,
  StarBrightnessSummaryModel,
  StarInfo,
  TimelinePointModel,
  ZiweiChartStructuralSummaryModel,
  ZiweiCompatibilityRequest,
  ZiweiCompatibilityResponse,
  ZiweiCoreSnapshotModel,
  ZiweiStructuralSummaryModel,
} from './openapiTypes'

// ── API 函数 ────────────────────────────────────────────────
function normalizeZiweiGender(gender: string | undefined): '男' | '女' {
  const value = String(gender ?? '').trim().toLowerCase()
  if (value === '女' || value === 'female' || value === 'f') return '女'
  return '男'
}

export async function computeZiwei(req: ZiweiRequest): Promise<ZiweiResponse> {
  const { data } = await apiClient.post<ZiweiResponse>('/api/v1/ziwei/full', {
    ...req,
    gender: normalizeZiweiGender(req.gender),
  })
  return data
}

export async function demoZiwei(): Promise<ZiweiResponse> {
  const { data } = await apiClient.get<ZiweiResponse>('/api/v1/ziwei/demo')
  return data
}

/** POST /api/v1/ziwei/compatibility — 紫微双人合盘 */
export async function ziweiCompatibility(req: ZiweiCompatibilityRequest): Promise<ZiweiCompatibilityResponse> {
  const { data } = await apiClient.post<ZiweiCompatibilityResponse>('/api/v1/ziwei/compatibility', req)
  return data
}

/** POST /api/v1/ziwei/multi_compat — 紫微多人合盘 */
export async function ziweiMultiCompat(req: MultiCompatRequest): Promise<MultiCompatResponse> {
  const { data } = await apiClient.post<MultiCompatResponse>('/api/v1/ziwei/multi_compat', req)
  return data
}

/** POST /api/v1/ziwei/multi_compat/export/pdf — 多人矩阵 PDF */
export async function ziweiMultiCompatExportPdf(req: MultiCompatRequest): Promise<Blob> {
  const { data } = await apiClient.post<Blob>('/api/v1/ziwei/multi_compat/export/pdf', req, {
    responseType: 'blob',
    timeout: 120_000,
  })
  return data
}

/** POST /api/v1/ziwei/batch — 批量排盘（上传CSV，返回ZIP） */
export async function ziweiBatch(file: File, templateVersion?: string): Promise<Blob> {
  const formData = new FormData()
  formData.append('file', file)
  const params = templateVersion ? { template_version: templateVersion } : undefined
  const { data } = await apiClient.post<Blob>('/api/v1/ziwei/batch', formData, {
    params,
    headers: { 'Content-Type': 'multipart/form-data' },
    responseType: 'blob',
  })
  return data
}

/** POST /api/v1/ziwei/flying — 飞星盘 */
export async function ziweiFlying(req: ZiweiFlyingRequest): Promise<FlyingChartResponse> {
  const { data } = await apiClient.post<FlyingChartResponse>('/api/v1/ziwei/flying', {
    ...req,
    gender: normalizeZiweiGender(req.gender),
  })
  return data
}
