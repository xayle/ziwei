import apiClient from './client'
import type { ResponseProvenance } from './bazi'

// ── 请求 ────────────────────────────────────────────────────
export interface ZiweiRequest {
  year: number
  month: number
  day: number
  hour: number
  minute?: number
  gender: '男' | '女'
  liunian_year?: number
  longitude?: number
  template_version?: 'standard' | 'pro' | 'simple'
  // 算法设置
  late_zishi?: boolean
  year_divide?: 'lichun' | 'normal'
  day_divide?: 'solar_next' | 'forward' | 'current'
  sihua_stem_indices?: Record<string, number>
  leap_month_method?: 'mid' | 'next' | 'same'
  kuiyue_method?: 'standard' | 'gengxin_mahu' | 'gengxin_huima' | 'liuxin_mahu'
  // A1-A8 新增安星方法
  tianma_method?: 'year' | 'month'
  tiankong_method?: 'standard' | 'shun'
  brightness_method?: 'standard' | 'zhongzhou' | 'mod1' | 'mod2'
  jiukong_method?: 'dual' | 'single' | 'zhanyan'
  tianshang_method?: 'standard' | 'zhongzhou'
  mingzhu_method?: 'quanshu' | 'zhongzhou'
  liunian_sihua_method?: 'year_stem' | 'life_palace_stem'
  changsheng_method?: 'standard' | 'water_earth' | 'fire_earth'
  wenchang_method?: 'hour' | 'year_branch'
  youbi_method?: 'month' | 'hour'
  liunian_life_method?: 'taisui' | 'yin_start'
  liuyue_method?: 'doujun' | 'simplified'
  xiaoxian_start_method?: 'standard' | 'gender_split'
  flow_lunar_day?: number
  flow_liuyue_month?: number
  flow_hour_branch?: number
  /** standard/pro 默认 true：未传 flow_* 时按流年参考日自动计算 */
  include_flow_liuri?: boolean
  /** ISO8601 流日/流时目标日期（Timeline 选日） */
  target_date?: string
}

// ── 子类型 ──────────────────────────────────────────────────
export interface StarInfo {
  name: string
  brightness: string
  brightness_val: number
  transforms: string[]
}

export interface PalaceStructuredAnalysis {
  palace_index: number
  palace_name: string
  conclusion: string
  explanation: string
  suggestion: string
  tooltip: string
  analysis_tags: string[]
  is_empty_palace: boolean
}

export interface LiuriItem {
  lunar_day: number
  life_palace_branch: number
  branch: string
  palace_name: string
  liuyue_month?: number
}

export interface LiushiItem {
  hour_branch_idx: number
  life_palace_branch: number
  branch: string
  palace_name: string
  hour_label: string
}

export interface LiuriLiushiResponse {
  liuri: LiuriItem
  liushi: LiushiItem
  missing_fields?: string[]
}

export interface PalaceResponse {
  index: number
  name: string
  branch: string
  stem: string
  main_stars: StarInfo[]
  aux_stars: StarInfo[]
  borrowed_main_stars?: StarInfo[]
  borrowed_from_palace?: string | null
  borrowed_reason?: string | null
  is_empty_palace?: boolean
  is_body_palace?: boolean
  flying_out: Record<string, string>
  analysis: string
  analysis_tags: string[]
  conclusion: string
  explanation: string
  suggestion: string
  tooltip: string
  xiaoxian_ages: number[]
  opposition_name: string
  dayun_boshi: string[]
  changsheng: string
  jiangqian_star: string
  suiqian_star: string
}

export interface LunarResponse {
  lunar_year: number
  lunar_month: number
  lunar_day: number
  is_leap_month: boolean
  year_gz: string
  month_gz: string
  hour_branch: string
  jieqi_month_gz: string
  day_gz: string
  hour_gz: string
  year_divide?: 'lichun' | 'normal'
}

export interface DayunItem {
  index: number
  ganzhi: string
  branch_idx?: number
  start_age: number
  end_age: number
  start_year: number
  sihua: Record<string, string>
  boshi_stars: Record<string, string>
}

export interface DayunResponse {
  forward: boolean
  start_age: number
  start_age_exact: number
  start_age_text: string
  items: DayunItem[]
}

export interface PatternResponse {
  name: string
  level: string
  description?: string
  palaces?: string[]
  stars?: string[]
  source?: string
  rule_id?: string
}

export interface LiunianResponse {
  year: number
  year_gz: string
  life_palace_branch: number
  sihua: Record<string, string>
}

export interface LiuyueItem {
  month: number
  month_name: string
  month_gz: string
  life_palace_branch: number
  palace_name: string
  sihua: Record<string, string>
}

export interface IztroDualTrack {
  label?: string
  year_divide?: string
  day_divide?: string
  life_palace_gz?: string | null
  main_match?: number
  main_total?: number
  note?: string | null
}

export interface IztroCrosscheck {
  status: string
  main_match: number
  main_total: number
  life_palace_match: boolean
  iztro_life_palace_gz?: string | null
  engine_life_palace_gz?: string | null
  advisory?: string | null
  dual_track?: IztroDualTrack | null
}

export interface FlyingPalaceResponse {
  palace_name: string
  stem_name: string
  flying_out: Record<string, string>
  opposition_palace: string
  self_transforms: string[]
}

export interface FlyingChartResponse {
  palaces: FlyingPalaceResponse[]
  received: Record<string, string[]>
  chonged: Record<string, string[]>
  self_transforms: string[]
}

export interface EventTagResponse {
  category: string
  level: string
  description: string
  source: string
}

export interface PeriodForecastResponse {
  period: string
  ganzhi: string
  palace_name: string
  overall: string
  details: Record<string, string>
  events: EventTagResponse[]
  advice: string
  score: number
  tier?: 'favorable' | 'neutral' | 'caution'
}

export interface ForecastResultResponse {
  year: number
  yearly: PeriodForecastResponse
  monthly: PeriodForecastResponse[]
  current_month: PeriodForecastResponse
}

export interface RemedyResponse {
  id: string
  name: string
  priority: number
  cost_level: string
  valid_scope: string
  actions: string[]
  evidence: string
  disclaimer: string
}

export interface LifeSuggestionResponse {
  id: string
  category: string
  category_label: string
  name: string
  priority: number
  cost_level: string
  valid_scope: string
  short_desc: string
  actions: string[]
  evidence?: string
  notes?: string
  disclaimer?: string
}

export interface EvidenceItem {
  title: string
  value: string
  source?: string | null
  confidence?: 'high' | 'medium' | 'low' | null
}

export interface TimelinePoint {
  year: number
  label: string
  summary: string
  tone?: 'danger' | 'warn' | 'neutral' | 'info' | 'current'
}

export interface PalaceWeight {
  palace_name: string
  weight: number
  reason?: string | null
}

export interface SihuaTraceItem {
  phase: '生年' | '大限' | '流年' | '流月'
  target: string
  transform: string
  palace_name?: string | null
  summary?: string | null
}

export interface StarBrightnessSummary {
  strong: string[]
  weak: string[]
  details: Record<string, string>
}

export interface ChartRelationSummary {
  minggong?: string | null
  shengong?: string | null
  wuxing_ju?: string | null
  triad_tetrad: string[]
  opposition: string[]
  palace_weights: PalaceWeight[]
  key_palaces: string[]
  palace_influence_notes: string[]
}

export interface ConfidenceSummary {
  level: 'high' | 'medium' | 'low'
  score?: number | null
  evidence: EvidenceItem[]
  risk_notes: string[]
  inference_notes: string[]
  blocked_fields: string[]
}

export interface PalaceRef {
  index: number
  name: string
  branch: string
  branch_idx: number
  stem?: string
  ganzhi?: string
  is_empty_palace?: boolean
  is_body_palace?: boolean
}

export interface SanfangStructure {
  life_palace: PalaceRef
  opposite_palace?: PalaceRef | null
  triad_palaces: PalaceRef[]
}

export interface ZiweiChartStructuralSummary {
  life_palace: PalaceRef
  body_palace: PalaceRef
  opposite_palace?: PalaceRef | null
  sanfang: SanfangStructure
  life_branch_idx: number
  body_branch_idx: number
  source?: string | null
  missing?: string[]
}

export interface ZiweiCoreSnapshot {
  life_palace_gz: string
  body_palace_gz: string
  life_palace_branch_idx: number
  body_palace_branch_idx: number
  wuxing_ju: number
  wuxing_ju_name: string
  life_ruler_star: string
  body_ruler_star: string
  laiyin_palace: string
}

export interface PatternSummaryBlock {
  patterns: Array<Record<string, unknown>>
  special_pattern_names: string[]
  summary_text: string
  confidence: 'high' | 'medium' | 'low'
}

export interface ReportSummaryBlock {
  title: string
  summary: string
  highlights: string[]
  warnings: string[]
  annotation_prompt: string
  source?: string | null
  missing?: string[]
}

export interface SihuaTraceEntry {
  palace: string
  stem?: string
  flying_out: Record<string, string>
  conclusion?: string
  opposition?: string
  source?: string
  missing?: boolean
}

export interface KeyYearPoint {
  label: string
  ganzhi?: string
  palace?: string
  score?: number | null
  overall?: string
  events?: string[]
}

export interface KeyMonthPoint {
  month: number
  month_name?: string
  month_gz?: string
  palace_name?: string
  sihua?: Record<string, string>
}

export interface ZiweiStructuralSummary {
  core_snapshot: ZiweiCoreSnapshot
  chart_relation_summary?: ChartRelationSummary | null
  sihua_summary: SihuaTraceItem[]
  brightness_summary?: StarBrightnessSummary | null
  timeline_summary: Record<string, TimelinePoint[]>
  pattern_summary: PatternSummaryBlock
  confidence_summary?: ConfidenceSummary | null
  report_summary: ReportSummaryBlock
  source?: string | null
  missing?: string[]
}

export interface ZiweiResponse {
  birth_solar: string
  gender: string
  lunar: LunarResponse
  life_palace_gz: string
  body_palace_gz: string
  life_palace_branch_idx: number
  body_palace_branch_idx: number
  wuxing_ju: number
  wuxing_ju_name: string
  palaces: PalaceResponse[]
  dayun: DayunResponse
  liunian: LiunianResponse | null
  flying: FlyingChartResponse | null
  liuyue: LiuyueItem[]
  liuri_liushi?: LiuriLiushiResponse | null
  missing_fields?: string[]
  trust_level?: 'full' | 'degraded' | 'reference' | 'advisory' | 'verified'
  content_versions?: Record<string, string>
  wenmo_advisory?: string
  engine_warnings?: string[]
  iztro_crosscheck?: IztroCrosscheck | null
  life_ruler_star: string
  body_ruler_star: string
  true_solar_time: string
  laiyin_palace: string
  summary: string
  analysis: Record<string, string>
  analysis_structured?: PalaceStructuredAnalysis[]
  structural_summary?: ZiweiChartStructuralSummary | null
  sihua_trace?: SihuaTraceEntry[]
  key_years?: KeyYearPoint[]
  key_months?: KeyMonthPoint[]
  ziwei_structural_summary?: ZiweiStructuralSummary | null
  provenance?: ResponseProvenance | null
  forecast: ForecastResultResponse | null
  patterns: PatternResponse[]
  remedies: RemedyResponse[]
  life_suggestions: LifeSuggestionResponse[]
  evidence_chain?: EvidenceItem[]
  template_version: string
  algorithm_version: string
  engine_version: string
  [key: string]: unknown
}

// ── 合婚 / 多人合盘 / 批量 / 飞星 补充类型 ─────────────────────

// POST /ziwei/compatibility
export interface ZiweiCompatSubject {
  year: number; month: number; day: number; hour: number; minute?: number; gender: '男' | '女'; longitude?: number
  year_divide?: 'lichun' | 'normal'
  day_divide?: 'solar_next' | 'forward' | 'current'
  youbi_method?: 'month' | 'hour'
  brightness_method?: 'standard' | 'zhongzhou' | 'mod1' | 'mod2'
}
export interface ZiweiCompatibilityRequest { person_a: ZiweiCompatSubject; person_b: ZiweiCompatSubject }
export interface CompatibilityDimensionResponse { dimension?: string; name?: string; score: number; max_score: number; description?: string; desc?: string }
export interface ZiweiCompatibilityResponse {
  total_score: number; max_score: number; level: string; summary: string
  dimensions: CompatibilityDimensionResponse[]
  person_a_info: Record<string, unknown>
  person_b_info: Record<string, unknown>
  harmony_points?: string[]
  conflict_points?: string[]
  complement_points?: string[]
  palace_compare?: Record<string, unknown> | Record<string, unknown>[]
}

// POST /ziwei/multi_compat
export interface MultiCompatRequest { person_list: ZiweiRequest[] }
export interface MultiCompatPairResponse { person_a_idx: number; person_b_idx: number; total_score: number; max_score: number; level: string }
export interface MultiCompatResponse { person_count: number; pairs: MultiCompatPairResponse[]; matrix: number[][]; team_harmony_score: number }

// POST /ziwei/flying — 与 /full 相同请求体
export type ZiweiFlyingRequest = ZiweiRequest

// ── API 函数 ────────────────────────────────────────────────
function normalizeZiweiGender(gender: string): '男' | '女' {
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
