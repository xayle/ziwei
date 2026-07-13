import apiClient from './client'
import type {
  AnalyzeRequest,
  BaziCompatibilityRequest,
  BaziCompatibilityResponse,
  BaziFullRequest,
  BaziFullResponse,
  BatchCompareRequest,
  BatchCompareResponse,
  CalendarCompareRequest,
  CalendarCompareResponse,
  DaYunItemModel,
  DaYunModel,
  DayMasterStrengthModel,
  DayunReportRequest,
  DayunReportResponse,
  GejuLightResponse,
  GejuSubjectRequest,
  GoldenCasesResponse,
  JieqiResponse,
  LiunianDomainRequest,
  LiunianDomainResponse,
  LiunianReportRequest,
  LiunianReportResponse,
  LiuriLiushiEndpointResponse,
  LiuriLiushiRequest,
  LiuNianDetailModel,
  LunarToSolarRequest,
  LunarToSolarResponse,
  MonthlyFortuneModel,
  MonthlyRequest,
  MonthlyResponse,
  PillarModel,
  PillarsModel,
  ShenshaModel,
  ShishenContributionModel,
  ShishenPillarSummaryModel,
  StrengthFactorModel,
  TenGodsModel,
  WuXingScoreModel,
  YongShenModel,
} from './openapiTypes'

// ── 请求 / 响应（OpenAPI 真源 · P3-2/P3-3）────────────────
export type BaziRequest = BaziFullRequest
export type BaziResponse = BaziFullResponse & Record<string, unknown>

// ── 嵌套模型（FE 别名 · 向后兼容）──────────────────────────
export type Pillar = PillarModel
export type PillarSet = PillarsModel
export type TenGods = TenGodsModel
export type Yongshen = YongShenModel
export type StrengthFactor = StrengthFactorModel
export type DayMasterStrength = DayMasterStrengthModel
export type DayunItem = DaYunItemModel
export type Dayun = DaYunModel
export type WuxingScore = WuXingScoreModel
export type Shensha = ShenshaModel
export type MonthlyFortuneItem = MonthlyFortuneModel
export type ShishenPillarSummary = ShishenPillarSummaryModel
export type ShishenContribution = ShishenContributionModel
export type LiunianDetailModel = LiuNianDetailModel

export type {
  AnalyzeRequest,
  BaziCompatibilityRequest,
  BaziCompatibilityResponse,
  BatchCompareRequest,
  BatchCompareResponse,
  CalendarCompareRequest,
  CalendarCompareResponse,
  CareerAnalysisModel,
  CompatibilitySubject,
  CurrentFortuneSummaryModel,
  DayunReportItem,
  DayunReportRequest,
  DayunReportResponse,
  DayunTransitionModel,
  FengshuiModel,
  GejuLightResponse,
  GejuModel,
  GejuSubjectRequest,
  GoldenCasesResponse,
  HealthAnalysisModel,
  JewelryItemModel,
  JewelryModel,
  JieqiItemOut,
  JieqiResponse,
  LifeArcModel,
  LifestyleModel,
  LiunianDomainRequest,
  LiunianDomainResponse,
  LiunianReportRequest,
  LiuriLiushiEndpointResponse,
  LiuriLiushiModel,
  LiuriLiushiRequest,
  LuckyModel,
  LunarToSolarRequest,
  LunarToSolarResponse,
  MarriageAnalysisModel,
  MilestoneModel,
  MonthlyItemOut,
  MonthlyRequest,
  MonthlyResponse,
  PalaceItemModel,
  PalaceModel,
  PersonalityModel,
  PillarOut,
  ProvenanceLayer,
  RelationsSummaryModel,
  RelationshipAnalysisModel,
  ResponseProvenance,
  RiskFlagsModel,
  RuleMatchModel,
  ShenshaSummaryModel,
  ShishenSummaryModel,
  ValidationModel,
  WarningModel,
  WealthAnalysisModel,
} from './openapiTypes'

/** POST /bazi/dayun-report/inline — OpenAPI 请求体同 BaziFullRequest */
export type DayunReportInlineRequest = BaziFullRequest

/** POST /bazi/liunian-report — 任务状态响应 */
export type LiunianReportTaskResponse = LiunianReportResponse

// ── API 函数 ────────────────────────────────────────────
export async function computeBazi(req: BaziRequest): Promise<BaziResponse> {
  const { data } = await apiClient.post<BaziResponse>('/api/v1/bazi/full', req)
  return data
}

/** POST /api/v1/bazi/liuri-liushi — 独立流日/流时计算 */
export async function computeLiuriLiushi(req: LiuriLiushiRequest): Promise<LiuriLiushiEndpointResponse> {
  const { data } = await apiClient.post<LiuriLiushiEndpointResponse>('/api/v1/bazi/liuri-liushi', req)
  return data
}

/** POST /api/v1/bazi/liunian-domain — 流年领域预测 */
export async function liunianDomain(req: LiunianDomainRequest): Promise<LiunianDomainResponse> {
  const { data } = await apiClient.post<LiunianDomainResponse>('/api/v1/bazi/liunian-domain', req)
  return data
}

/** POST /api/v1/bazi/dayun-report — 大运叙事报告 */
export async function dayunReport(req: DayunReportRequest): Promise<DayunReportResponse> {
  const { data } = await apiClient.post<DayunReportResponse>('/api/v1/bazi/dayun-report', req)
  return data
}

/** POST /api/v1/bazi/dayun-report/inline — 档案驱动大运叙事（无需 case_id） */
export async function dayunReportInline(req: DayunReportInlineRequest): Promise<DayunReportResponse> {
  const { data } = await apiClient.post<DayunReportResponse>('/api/v1/bazi/dayun-report/inline', req)
  return data
}

/** POST /api/v1/bazi/compatibility — 双人合婚分析 */
export async function baziCompatibility(req: BaziCompatibilityRequest): Promise<BaziCompatibilityResponse> {
  const { data } = await apiClient.post<BaziCompatibilityResponse>('/api/v1/bazi/compatibility', req)
  return data
}

/** POST /api/v1/bazi/monthly — 月运预测 */
export async function monthlyFortune(req: MonthlyRequest): Promise<MonthlyResponse> {
  const { data } = await apiClient.post<MonthlyResponse>('/api/v1/bazi/monthly', req)
  return data
}

/** POST /api/v1/bazi/analyze — 动态分析（指定模块） */
export async function analyzeBazi(req: AnalyzeRequest): Promise<Record<string, unknown>> {
  const { data } = await apiClient.post<Record<string, unknown>>('/api/v1/bazi/analyze', req)
  return data
}

/** GET /api/v1/bazi/jieqi — 节气查询 */
export async function getJieqi(year: number): Promise<JieqiResponse> {
  const { data } = await apiClient.get<JieqiResponse>('/api/v1/bazi/jieqi', { params: { year } })
  return data
}

/** POST /api/v1/bazi/geju — 格局速查 */
export async function computeGeju(req: GejuSubjectRequest): Promise<GejuLightResponse> {
  const { data } = await apiClient.post<GejuLightResponse>('/api/v1/bazi/geju', req)
  return data
}

/** POST /api/v1/bazi/lunar-to-solar — 农历转公历 */
export async function lunarToSolar(req: LunarToSolarRequest): Promise<LunarToSolarResponse> {
  const { data } = await apiClient.post<LunarToSolarResponse>('/api/v1/bazi/lunar-to-solar', req)
  return data
}

/** POST /api/v1/bazi/calendar-compare — 历法对照 */
export async function calendarCompare(req: CalendarCompareRequest): Promise<CalendarCompareResponse> {
  const { data } = await apiClient.post<CalendarCompareResponse>('/api/v1/bazi/calendar-compare', req)
  return data
}

/** POST /api/v1/bazi/batch-compare — 批量对比 */
export async function batchCompare(req: BatchCompareRequest): Promise<BatchCompareResponse> {
  const { data } = await apiClient.post<BatchCompareResponse>('/api/v1/bazi/batch-compare', req)
  return data
}

/** POST /api/v1/bazi/liunian-report — 提交流年报告任务 (202) */
export async function submitLiunianReport(req: LiunianReportRequest): Promise<LiunianReportTaskResponse> {
  const { data } = await apiClient.post<LiunianReportTaskResponse>('/api/v1/bazi/liunian-report', req)
  return data
}

/** GET /api/v1/bazi/liunian-report/{task_id} — 流年报告任务状态 */
export async function getLiunianReportStatus(taskId: string): Promise<LiunianReportTaskResponse> {
  const { data } = await apiClient.get<LiunianReportTaskResponse>(`/api/v1/bazi/liunian-report/${taskId}`)
  return data
}

/** GET /api/v1/bazi/golden-cases — 金典案例 */
export async function getGoldenCases(params?: { geju?: string; tag?: string; limit?: number }): Promise<GoldenCasesResponse> {
  const { data } = await apiClient.get<GoldenCasesResponse>('/api/v1/bazi/golden-cases', { params })
  return data
}
