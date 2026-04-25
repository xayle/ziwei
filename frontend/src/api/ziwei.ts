import apiClient from './client'

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
}

// ── 子类型 ──────────────────────────────────────────────────
export interface StarInfo {
  name: string
  brightness: string
  brightness_val: number
  transforms: string[]
}

export interface PalaceResponse {
  index: number
  name: string
  branch: string
  stem: string
  main_stars: StarInfo[]
  aux_stars: string[]
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
}

export interface DayunItem {
  index: number
  ganzhi: string
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
  life_ruler_star: string
  body_ruler_star: string
  true_solar_time: string
  summary: string
  analysis: Record<string, string>
  forecast: ForecastResultResponse | null
  patterns: PatternResponse[]
  remedies: RemedyResponse[]
  life_suggestions: LifeSuggestionResponse[]
  template_version: string
  algorithm_version: string
  engine_version: string
  [key: string]: unknown
}

// ── 合婚 / 多人合盘 / 批量 / 飞星 补充类型 ─────────────────────

// POST /ziwei/compatibility
export interface ZiweiCompatSubject {
  year: number; month: number; day: number; hour: number; minute?: number; gender: '男' | '女'; longitude?: number
}
export interface ZiweiCompatibilityRequest { person_a: ZiweiCompatSubject; person_b: ZiweiCompatSubject }
export interface CompatibilityDimensionResponse { dimension: string; score: number; max_score: number; description: string }
export interface ZiweiCompatibilityResponse {
  total_score: number; max_score: number; level: string; summary: string
  dimensions: CompatibilityDimensionResponse[]; person_a_info: Record<string, unknown>; person_b_info: Record<string, unknown>
  harmony_points: string[]; conflict_points: string[]; complement_points: string[]; palace_compare: Record<string, unknown>
}

// POST /ziwei/multi_compat
export interface MultiCompatRequest { person_list: ZiweiRequest[] }
export interface MultiCompatPairResponse { person_a_idx: number; person_b_idx: number; total_score: number; max_score: number; level: string }
export interface MultiCompatResponse { person_count: number; pairs: MultiCompatPairResponse[]; matrix: number[][]; team_harmony_score: number }

// POST /ziwei/flying
export interface ZiweiFlyingRequest { year: number; month: number; day: number; hour: number; minute?: number; gender: string; longitude?: number }

// ── API 函数 ────────────────────────────────────────────────
export async function computeZiwei(req: ZiweiRequest): Promise<ZiweiResponse> {
  const { data } = await apiClient.post<ZiweiResponse>('/api/v1/ziwei/full', req)
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
  const { data } = await apiClient.post<FlyingChartResponse>('/api/v1/ziwei/flying', req)
  return data
}
