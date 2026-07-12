import apiClient from './client'

// ── 请求类型 ────────────────────────────────────────────
export interface BaziRequest {
  dt: string            // ISO8601 naive, e.g. "1990-01-15T08:30:00"
  lon: number           // 经度 73~135
  tz: string            // IANA timezone
  mode?: 'dual' | 'single'
  solar_time_enabled?: boolean
  gender?: 'male' | 'female' | ''
  city_tier?: '一线' | '新一线' | '其余' | null
  industry?: '金融IT' | '教育公务' | '其余' | null
  city_tier?: '一线' | '新一线' | '其余' | null
  industry?: '金融IT' | '教育公务' | '其余' | null
  target_date?: string  // ISO8601，流日/流时目标日期
  target_hour?: number  // 0-23，流时小时
  include_liuri?: boolean // 默认 true；未传 target_date 时使用当天
  zi_day_rule?: 'sxtwl' | 'early_zi_prev_day' | 'early_zi_same_day'
}

// ── 响应子类型 ──────────────────────────────────────────
export interface Pillar {
  stem: string
  branch: string
  ganzhi?: string
}

export interface PillarSet {
  year: Pillar
  month: Pillar
  day: Pillar
  hour: Pillar
}

// 十神（字段名为 year/month/day/hour，对应四柱天干神格）
export interface TenGods {
  year?: string
  month?: string
  day?: string
  hour?: string
}

// 用神
export interface Yongshen {
  favor: string[]
  avoid: string[]
  rationale?: string
  recorded_favor?: string[]
  engine_favor?: string[]
  dual_track_note?: string | null
  dual_track_id?: string | null
}

// 日元强弱
export interface StrengthFactor {
  name: string
  score: number
  weight?: number | null
  weighted_score?: number | null
  reason?: string
}
export interface DayMasterStrength {
  score: number
  tier: string
  factors?: StrengthFactor[]
  strength_factors?: StrengthFactor[]
}

// 格局
export interface GejuModel {
  geju_name: string
  geju_level: string
  is_broken?: boolean
  interpretation_text: string
  classic_ref?: string
  geju_detail?: string
  confidence?: number
  month_stem_shishen?: string
  inference_tags?: string[]
  disclaimer?: string
  fact_data?: Record<string, unknown>
  derived_geju?: string | null
  po_geju?: {
    broken?: boolean
    reason?: string
    severity?: string
    po_jiu?: { saved?: boolean; method?: string; note?: string }
  } | null
  recorded_geju?: string | null
  engine_geju?: string | null
  dual_track_note?: string | null
  dual_track_id?: string | null
}

// 大运条目（stem + branch 组合成干支）
export interface DayunItem {
  start_age?: number
  start_year?: number
  stem?: string
  branch?: string
  ten_god?: string
  hidden_stems?: Array<{ stem?: string; weight?: number; element?: string; ten_god?: string }>
  xingyun?: string
  self_seat?: string
  kongwang?: string[]
  nayin?: string
  shensha?: Array<Record<string, unknown>>
  wuxing?: string
  yin_yang?: string
  narrative?: string
  wealth_hint?: string
  health_hint?: string
  love_hint?: string
  geju_impact?: string
  yongshen_shift?: 'forward' | 'backward' | 'neutral' | string
  start_age_months?: number
  flow_wuxing?: string
  wealth_range?: { low?: number; high?: number }
  child_hint?: string
  refs?: Array<Record<string, unknown>>
}

// 大运
export interface Dayun {
  method?: string
  direction?: string
  start_age?: number
  items: DayunItem[]
  cycles?: DayunItem[]
  boundary?: string
  direction_basis?: Record<string, unknown>
  start_age_months?: number
  anchor_jieqi_name?: string
  anchor_jieqi_dt?: string
  days_to_next_transition?: number | null
  next_transition_age?: number | null
  next_transition_ganzhi?: string | null
  next_transition_hint?: string | null
}

// 五行分数
export interface WuxingScore {
  wood: number
  fire: number
  earth: number
  metal: number
  water: number
  [key: string]: number
}

// 神煞
export interface Shensha {
  name: string
  dizhi: string
  pillar: string
  is_beneficial: boolean
  priority: string
  meaning: string
  classic_source?: string
  is_star?: boolean
}

// 人生弧线
export interface LifeArcModel {
  overall_tier: string
  early_fortune: string
  mid_fortune: string
  late_fortune: string
  peak_periods: string[]
  caution_periods: string[]
  life_motto: string
  interpretation_text: string
  inference_tags?: string[]
  disclaimer?: string
  optimal_action?: string
}

// 性格分析
export interface PersonalityModel {
  day_stem: string
  day_stem_trait: string
  strength_modifier: string
  advantages: string[]
  disadvantages: string[]
  growth_advice: string
  interpretation_text: string
  communication_style?: string
  stress_coping_mode?: string
  potential_activation?: string
  inference_tags?: string[]
  disclaimer?: string
  fact_data?: Record<string, unknown>
}

// 财运分析
export interface WealthAnalysisModel {
  wealth_score: number
  wealth_tier: string
  annual_range: string
  industries: string[]
  strategy: string
  interpretation_text: string
  investment_preference?: string
  financial_taboos?: string
  dayun_forecast?: Array<{ ganzhi: string; trend: string }>
  wealth_accumulation_phases?: string
  inference_tags?: string[]
  disclaimer?: string
  fact_data?: Record<string, unknown>
}

// 事业分析
export interface CareerAnalysisModel {
  career_score: number
  career_directions: string[]
  suitable_industries: string[]
  leadership_potential: boolean
  development_advice: string
  optimal_move_timing: string
  interpretation_text: string
  entrepreneurship_assessment?: string
  five_year_roadmap?: string
  collaboration_style?: string
  inference_tags?: string[]
  disclaimer?: string
  fact_data?: Record<string, unknown>
}

// 婚恋分析
export interface MarriageAnalysisModel {
  marriage_score: number
  peach_blossom: string
  partner_wuxing: string
  partner_profile: string
  partner_direction: string
  optimal_marriage_age: string
  marriage_windows: string[]
  children_outlook: string
  children_timing?: string
  interpretation_text: string
  emotional_pitfalls?: string
  second_marriage_indicator?: string
  inference_tags?: string[]
  disclaimer?: string
  fact_data?: Record<string, unknown>
}

// 健康分析
export interface HealthAnalysisModel {
  health_score: number
  risk_organs: string[]
  risk_level: string
  health_advice: string
  exercise: string[]
  diet: string[]
  peak_period: string
  interpretation_text: string
  seasonal_health?: string
  mental_health_advice?: string
  constitution_type?: string
  inference_tags?: string[]
  disclaimer?: string
  fact_data?: Record<string, unknown>
}

// 月运
export interface MonthlyFortuneItem {
  month: number
  lunar_month: number
  month_dizhi: string
  month_ganzhi?: string
  luck_level: string   // 吉/平/凶
  color_hint: string
  tip: string
  clash_with?: string
  relation_to_rizhu?: string
  dayun_stem?: string
  disclaimer?: string
}

// 开运数据
export interface LuckyModel {
  lucky_colors: string[]
  lucky_numbers: number[]
  lucky_direction: string
  lucky_item: string
  interpretation_text: string
  avoid_colors?: string[]
  avoid_direction?: string
  disclaimer?: string
}

// 当前运势摘要
export interface CurrentFortuneSummaryModel {
  current_dayun: string
  dayun_years_remaining: number
  current_liunian: string
  this_year_domains: Record<string, string>
  top3_actions: string[]
}

export interface ShishenPillarSummary {
  pillar: 'year' | 'month' | 'day' | 'hour'
  stem?: string | null
  ten_god?: string | null
  note?: string | null
}

export interface ShishenContribution {
  pillar: 'year' | 'month' | 'day' | 'hour'
  source: 'stem' | 'hidden'
  stem: string
  hidden_stem?: string | null
  ten_god?: string | null
  weight: number
  element?: string | null
}

export interface ShishenSummary {
  day_stem: string
  day_element?: string | null
  day_yinyang?: string | null
  pillars: Partial<Record<'year' | 'month' | 'day' | 'hour', ShishenPillarSummary>>
  score_total: number
  score_breakdown: Record<string, number>
  score_share: Record<string, number>
  dominant: string[]
  hidden_contrib_by_ten_god: Record<string, number>
  contributions: ShishenContribution[]
  liuqin_summary: string[]
  summary_text: string
}

// 流年四维详情
export interface LiunianDetailModel {
  year: number
  ganzhi: string
  annual_score: number
  domain_forecasts: Record<string, string>
  tai_sui_relations: string[]
  clash_pillars: string[]
  notable_months: number[]
  optimal_action?: string
  interpretation_text: string
  ten_god?: string
  flow_wuxing?: string
  clash?: string
  inference_tags?: string[]
  disclaimer?: string
}

// 人生里程碑
export interface MilestoneModel {
  age: number
  year: number
  milestone_type: string
  ganzhi_context: string
  description: string
  risk_level: string
  advice: string
}

// 六亲人际分析
export interface RelationshipAnalysisModel {
  relationship_score: number
  liu_qin: Record<string, string>
  noble_people: string[]
  petty_people: string[]
  social_strategy: string
  interpretation_text: string
  inference_tags: string[]
  disclaimer?: string
  fact_data?: Record<string, unknown>
}

// 饰品建议
export interface JewelryItemModel {
  material: string
  gemstone: string
  position: string
  wuxing: string
}
export interface JewelryModel {
  primary: JewelryItemModel
  secondary: JewelryItemModel
  combination: string
  taboo: string[]
  interpretation_text: string
  disclaimer?: string
}

// 风水建议
export interface FengshuiModel {
  auspicious_directions: string[]
  decor: string[]
  plants: string[]
  lucky_colors: string[]
  taboo: string[]
  interpretation_text: string
  disclaimer?: string
}

// 生活建议
export interface LifestyleModel {
  exercise: string[]
  best_times: string
  diet: string[]
  travel_direction: string
  sleep_advice: string
  interpretation_text: string
  disclaimer?: string
}

// 宫位
export interface PalaceItemModel {
  palace_name: string
  dizhi: string
  shishen?: string
  tiangan?: string
  strength?: '旺' | '相' | '休' | '囚' | '死'
  note?: string
}
export interface PalaceModel {
  ming_gong?: PalaceItemModel
  shen_gong?: PalaceItemModel
  twelve_palaces?: PalaceItemModel[]
  interpretation_text?: string
  inference_tags?: string[]
  disclaimer?: string
  fact_data?: Record<string, unknown>
}

// 警告
export interface WarningModel {
  code: string
  message: string
}

// 规则命中
export interface RuleMatchModel {
  rule_id: string
  name: string
  flags: string[]
  evidence_text: string
  classic_hint?: string
  disclaimer?: string
}

// ── 可信度分层（根级 provenance）────────────────────────
export type ProvenanceLayer = {
  layer?: 'classical' | 'engine' | 'heuristic' | 'modern_convention' | string
  confidence?: number
  method_registry_id?: string | null
  note?: string | null
}

export type ResponseProvenance = Partial<Record<
  | 'pillars' | 'geju' | 'yongshen' | 'dayun' | 'narrative' | 'analysis'
  | 'scoring' | 'forecast' | 'compatibility' | 'patterns' | 'stars',
  ProvenanceLayer
>>

// 流日/流时（B-P2/P3）
export interface LiuriLiushiModel {
  date: string
  day_ganzhi: string
  day_stem: string
  day_branch: string
  hour_ganzhi: string
  hour_stem: string
  hour_branch: string
  hour_branch_idx?: number
  hour_label?: string
  day_ten_god?: string | null
  hour_ten_god?: string | null
  method?: string
  missing_fields?: string[]
  flow_score?: number | null
  flow_score_dayun?: number | null
  flow_score_liunian?: number | null
  flow_score_geju?: number | null
  transition_hint?: string | null
  warnings?: string[]
  flow_tone?: string | null
  dayun_link?: string | null
  liunian_link?: string | null
  current_dayun_ganzhi?: string | null
  current_liunian_ganzhi?: string | null
  flow_summary?: string | null
}

export interface DayunTransitionModel {
  days_to_next_transition?: number | null
  next_transition_age?: number | null
  next_transition_ganzhi?: string | null
  next_transition_hint?: string | null
}

// ── 校验与可信度 ─────────────────────────────────────────
export interface RiskFlagsModel {
  near_shichen_boundary?: boolean
  near_jieqi_boundary?: boolean
  jieqi_boundary_status?: 'ok' | 'unavailable'
  minutes_to_shichen_boundary?: number | null
  minutes_to_jieqi_boundary?: number | null
}

export interface ValidationModel {
  level?: 'L0' | 'L1' | 'L2' | 'L3'
  mode?: 'dual' | 'single'
  recommended?: string
  interpretation_enabled?: boolean
  reasons?: string[]
  diff_fields?: Array<'year' | 'month' | 'day' | 'hour'>
  risk_flags?: RiskFlagsModel
  boundary_risk_shichen?: boolean
  boundary_risk_jieqi?: boolean
  warnings?: WarningModel[]
}

// ── 卷二上浮摘要（BE-P3-05）────────────────────────────────
export interface RelationsSummaryModel {
  items?: Array<{ type?: string; pillars?: string; detail?: string }>
  clash_summary?: string
  combine_summary?: string
  harm_summary?: string
  interaction_summary?: string
  missing?: string[]
}

export interface ShenshaSummaryModel {
  items?: Shensha[]
  highlights?: string[]
  missing?: string[]
}

// ── 完整响应（对应后端 BaziFullResponse）── ────────────
export interface BaziResponse {
  // 元数据
  api_version?: string
  rule_version?: string
  schema_version?: string
  request_id?: string
  warnings?: WarningModel[]
  // 四柱
  pillars_primary: PillarSet
  pillars_secondary?: PillarSet
  ten_gods?: TenGods
  pillar_details?: Record<'year' | 'month' | 'day' | 'hour', {
    label?: string
    stem?: string | null
    branch?: string | null
    ganzhi?: string | null
    ten_god?: string | null
    hidden_stems?: Array<{ stem?: string; weight?: number; element?: string | null; ten_god?: string | null }>
    xingyun?: string | null
    self_seat?: string | null
    kongwang?: string[]
    nayin?: string | null
    shensha?: Array<{ name?: string; priority?: string; polarity?: string; pillar?: string; topic?: string; note?: string; classic?: string | null }>
    wuxing?: string | null
    yin_yang?: string | null
  }>
  // 核心分析
  yongshen?: Yongshen
  day_master_strength?: DayMasterStrength
  geju?: GejuModel
  palace?: PalaceModel
  start_dayun_age?: number
  shishen_summary?: ShishenSummary
  // 大运/流年
  dayun?: Dayun
  liunian?: { items?: Array<{ year?: number; stem?: string; branch?: string; ten_god?: string; clash?: string }>; years_used?: number[] }
  // 五行
  wuxing_score?: WuxingScore
  wuxing_breakdown?: Record<string, Record<string, number>>
  wuxing_balance_score?: number
  wuxing_weak?: string[]
  wuxing_strong?: string[]
  balance_advice?: string
  // 命局评 + 神煞
  bazi_summary?: string
  shensha?: Shensha[]
  kongwang?: string[]
  // 生命弧线 + 性格
  life_arc?: LifeArcModel
  personality?: PersonalityModel
  // 生活域分析（报告卷五；八字页不展示长文）
  wealth_analysis?: WealthAnalysisModel
  career?: CareerAnalysisModel
  marriage_analysis?: MarriageAnalysisModel
  health?: HealthAnalysisModel
  // 新增模块
  relationship?: RelationshipAnalysisModel
  jewelry?: JewelryModel
  fengshui?: FengshuiModel
  lifestyle?: LifestyleModel
  // 运势
  monthly_fortune?: MonthlyFortuneItem[]
  lucky?: LuckyModel
  current_fortune_summary?: CurrentFortuneSummaryModel
  liunian_detail?: LiunianDetailModel[]
  milestones?: MilestoneModel[]
  // 规则命中 + 原始数据
  rule_matches?: RuleMatchModel[]
  liuri_liushi?: LiuriLiushiModel | null
  missing_fields?: string[]
  provenance?: ResponseProvenance | null
  validation?: ValidationModel | null
  risk_flags?: RiskFlagsModel | null
  confidence_level?: 'high' | 'medium' | 'low'
  confidence_score?: number | null
  evidence_chain?: Array<Record<string, unknown>>
  bazi_structural_summary?: Record<string, unknown> | null
  dizhi_relations?: Array<Record<string, unknown>>
  relations_summary?: RelationsSummaryModel | null
  shensha_summary?: ShenshaSummaryModel | null
  tiangan_clashes?: Array<Record<string, unknown>>
  raw?: Record<string, unknown>
  methods?: Record<string, string>
  [key: string]: unknown
}

// ── 补充请求 / 响应类型 ────────────────────────────────────

// POST /bazi/liuri-liushi — 独立流日/流时
export interface LiuriLiushiRequest {
  dt: string
  lon: number
  tz?: string
  gender?: 'male' | 'female'
  solar_time_enabled?: boolean
  target_date?: string
  target_hour?: number
  include_dayun_transition?: boolean
}
export interface LiuriLiushiEndpointResponse {
  request_id: string
  liuri_liushi: LiuriLiushiModel
  dayun_transition?: DayunTransitionModel | null
}

// POST /bazi/liunian-domain
export interface LiunianDomainRequest { case_id: string; year: number }
export interface LiunianDomainResponse { year: number; year_ganzhi: string; domains: Record<string, string> }

// POST /bazi/dayun-report
export interface DayunReportRequest { case_id: string }
export interface DayunReportInlineRequest {
  dt: string
  lon: number
  tz: string
  gender?: 'male' | 'female'
  solar_time_enabled?: boolean
  mode?: 'dual' | 'single'
}
export interface DayunReportItem { ganzhi: string; start_age?: number; end_age?: number; ten_god?: string; narrative: string }
export interface DayunReportResponse { items: DayunReportItem[]; narrative_total_chars: number }

// POST /bazi/compatibility
export interface CompatibilitySubject { birth_dt: string; lon?: number; tz?: string; gender?: string }
export interface BaziCompatibilityRequest { person_a: CompatibilitySubject; person_b: CompatibilitySubject }
export interface BaziCompatibilityResponse { score: number; wuxing_match: Record<string, string>; branch_clash: string[]; born_year_he: string[]; summary: string }

// POST /bazi/monthly
export interface MonthlyRequest { case_id: string; year: number }
export interface MonthlyItemOut { month: number; month_ganzhi: string; month_dizhi: string; luck_level: string; color_hint: string; tip: string; clash_with?: string }
export interface MonthlyResponse { year: number; year_ganzhi: string; items: MonthlyItemOut[] }

// POST /bazi/analyze
export interface AnalyzeRequest { birth_dt: string; lon?: number; tz?: string; gender?: string; tabs?: string[] }

// GET /bazi/jieqi
export interface JieqiItemOut { name: string; dt_local: string }
export interface JieqiResponse { year: number; items: JieqiItemOut[]; backend: string }

// POST /bazi/geju
export interface GejuSubjectRequest { birth_dt: string; lon?: number; tz?: string; gender?: string }
export interface GejuLightResponse { geju_name: string; confidence: number; is_broken: boolean; note: string; classic_ref?: string; ten_god?: string }

// POST /bazi/calendar-compare
export interface CalendarCompareRequest { birth_dt: string; lon?: number; tz?: string }
export interface LunarToSolarRequest {
  lunar_year: number
  lunar_month: number
  lunar_day: number
  hour?: number
  minute?: number
  is_leap_month?: boolean
}
export interface LunarToSolarResponse {
  solar_dt: string
  solar_year: number
  solar_month: number
  solar_day: number
  lunar_label: string
  warnings: string[]
}
export interface PillarOut { year: string; month: string; day: string; hour: string }
export interface CalendarCompareResponse { sxtwl?: PillarOut; cnlunar?: PillarOut; diff_fields: string[]; warnings: string[] }

// POST /bazi/batch-compare
export interface BatchCompareRequest { case_ids: string[] }
export interface BatchCaseProfile { case_id: string; name: string; geju_name: string; yongshen_favor: string[]; yongshen_avoid: string[]; wuxing_scores: Record<string, number>; error: string }
export interface BatchCompareResponse { count: number; profiles: BatchCaseProfile[]; common_favor: string[]; common_avoid: string[] }

// POST /bazi/liunian-report
export interface LiunianReportRequest { case_id: string; year: number; include_months?: boolean }
export interface LiunianReportTaskResponse { task_id: string; status: string; year: number; case_id: string; submitted_at: string; result?: Record<string, unknown>; error?: string }

// GET /bazi/golden-cases
export interface GoldenCasesResponse { total: number; cases: Array<Record<string, unknown>> }

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
