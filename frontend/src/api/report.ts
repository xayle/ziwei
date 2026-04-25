/**
 * report.ts — 报告书所需 API 类型定义与请求函数
 * 字段名以后端 Python schema 为准（非 bazi.ts 原有类型文件）
 */
import apiClient from './client'
import type { ZiweiResponse } from './ziwei'
import type { NameAnalysisResponse } from './name'

// ── CaseOut（镜像后端 CaseOut schema）──────────────────────────────

export interface CaseOut {
  id: string
  name: string
  gender: 'male' | 'female' | null
  birth_dt_local: string    // ISO8601 naive，如 "1990-01-15T08:30:00"
  tz: string
  birth_dt: string | null
  lon: number
  city: string | null
  solar_time_enabled: boolean
  notes: string | null
  tags: string[] | null
  created_at: string
  updated_at: string
  last_snapshot_at: string | null
  api_version_last: string | null
  rule_version_last: string | null
  schema_version: string | null
  latest_verify_summary: Record<string, unknown> | null
}

// ── BaziFullRequest（精确镜像后端，⚠️ 无 gender 字段）───────────────

export interface BaziFullRequest {
  dt: string                    // ISO8601 naive
  lon: number
  tz: string
  mode?: 'dual' | 'single'
  solar_time_enabled?: boolean
  liunian_years?: number[]      // 指定要计算的流年年份数组
}

// ── BaziFullResponse 子类型（后端准确字段名）──────────────────────

export interface Pillar { stem: string; branch: string }
export interface PillarSet { year: Pillar; month: Pillar; day: Pillar; hour: Pillar }

export interface TenGodsModel {
  year: string; month: string; day: string; hour: string
}

export interface DayMasterStrengthModel {
  score: number
  tier: string
  factors: Array<{ name: string; score: number; reason?: string }>
}

export interface YongShenModel {
  favor: string[]
  avoid: string[]
  rationale: string | null
}

export interface GejuModel {
  geju_name: string
  geju_level: string
  inference_tags: string[]
  interpretation_text: string
  is_broken: boolean
  classic_ref?: string
  geju_detail?: string
  confidence?: number
  month_stem_shishen?: string
  disclaimer?: string
  fact_data?: Record<string, unknown>
}

export interface PalaceItemModel {
  palace_name: string
  dizhi: string
  tiangan?: string
  strength: '旺' | '相' | '休' | '囚' | '死'
  shishen?: string
  note?: string
}

export interface PalaceModel {
  ming_gong: PalaceItemModel
  shen_gong: PalaceItemModel
  twelve_palaces: PalaceItemModel[]
  inference_tags: string[]
  interpretation_text: string
  disclaimer?: string
  fact_data?: Record<string, unknown>
}

export interface ShenshaModel {
  name: string
  dizhi: string
  pillar: string
  is_beneficial: boolean
  is_star?: boolean
  priority: 'A' | 'B' | 'C'
  meaning: string
  classic_source: string
}

export interface DaYunItemModel {
  start_age: number
  start_year: number
  stem: string                  // ⚠️ 无 .ganzhi，需 stem+branch 拼接
  branch: string
  narrative: string
}

export interface DaYunModel {
  items: DaYunItemModel[]       // ⚠️ 非 .cycles
}

export interface LiuNianItemModel {
  year: number
  stem: string
  branch: string
  ten_god: string
  clash: string | null
}

export interface LiuNianResultModel {
  items: LiuNianItemModel[]     // ⚠️ 非 .years
}

export interface LiuNianDetailModel {
  year: number
  ganzhi: string
  tai_sui_relations: string[]
  clash_pillars: string[]
  notable_months: number[]
  annual_score: number
  domain_forecasts: Record<string, string>
  optimal_action?: string
  inference_tags: string[]
  interpretation_text: string
  disclaimer?: string
  ten_god?: string
  flow_wuxing?: string
  clash?: string
}

export interface WuXingScoreModel {
  wood: number; fire: number; earth: number; metal: number; water: number
}

export interface CurrentFortuneSummaryModel {
  current_dayun: string
  dayun_years_remaining: number
  current_liunian: string
  this_year_domains: Record<string, string>
  top3_actions: string[]
}

export interface BaziFullResponse {
  api_version: string
  request_id: string
  pillars_primary: PillarSet
  ten_gods: TenGodsModel
  day_master_strength: DayMasterStrengthModel
  yongshen: YongShenModel
  geju: GejuModel | null
  palace: PalaceModel | null
  shensha: ShenshaModel[] | null
  dayun: DaYunModel
  liunian: LiuNianResultModel
  liunian_detail: LiuNianDetailModel[] | null
  start_dayun_age: number | null
  wuxing_score: WuXingScoreModel
  wuxing_weak: string[] | null
  wuxing_strong: string[] | null
  balance_advice: string | null
  dizhi_relations: Array<{ type: string; branches: string[]; description?: string }> | null
  tiangan_clashes: Array<{ type: string; stems: string[]; description?: string }> | null
  current_fortune_summary: CurrentFortuneSummaryModel | null
  bazi_summary: string          // 400-600字六段结构综述
  [key: string]: unknown
}

// ── ZeriParams / ZeriResponse ─────────────────────────────────────

export interface ZeriParams {
  year: number
  month: number
  life_palace_branch: string    // 命宫地支，如 '子'
  wuxing_ju_name: string        // 五行局名，如 '水二局'
  natal_year_branch?: string
  purpose?: string              // default "general"
}

export interface ZeriDayItem {
  date: string
  weekday: string
  day_gz: string
  day_stem: string
  day_branch: string
  lunar_info: string
  score: number
  level: string
  level_css: string
  evidence: string[]
  is_break: boolean
  is_virtue: boolean
}

export interface ZeriResponse {
  year: number
  month: number
  purpose: string
  purpose_label: string
  year_gz: string
  month_gz: string
  days: ZeriDayItem[]
  top_days: string[]
  [key: string]: unknown
}

// ── FengshuiParams / FengshuiResponse ────────────────────────────

export interface FengshuiParams {
  birth_year: number
  gender: '男' | '女'           // ⚠️ 必须中文字符串，非 male/female
}

/** 吉凶方位条目（对应后端 DirectionItemResponse） */
export interface DirectionItem {
  direction: string       // 方向代码，如 'N'
  direction_zh: string    // 方向中文，如 '北'
  label: string           // 能量标签，如 '生气'
  level: string           // 吉凶级别，如 '最吉'
  level_css: string       // CSS 类名，如 'ji1'
  desc: string            // 描述说明
}

/** 家具方位建议（对应后端 FurnitureTipResponse） */
export interface FurnitureTip {
  item: string            // 家具/位置名称，如 '床头朝向'
  direction: string       // 方向代码，如 'SE'
  direction_zh: string    // 方向中文，如 '东南'
  label: string           // 能量标签，如 '生气'
  reason: string          // 建议理由
}

/** 八宅命卦分析完整响应（对应后端 BaguaResponse） */
export interface FengshuiResponse {
  life_gua: number                      // 命卦数（1/2/3/4/6/7/8/9）
  gua_name: string                      // 卦名，如 '坎'
  gua_element: string                   // 五行，如 '水'
  group: string                         // 命组：东四命 / 西四命
  birth_year: number
  gender: string

  auspicious: DirectionItem[]           // 四吉方（生气/天医/延年/伏位）
  inauspicious: DirectionItem[]         // 四凶方（绝命/五鬼/六煞/祸害）

  bed_tip: FurnitureTip | null          // 床头方位建议
  desk_tip: FurnitureTip | null         // 书桌/工位方位建议
  door_tip: FurnitureTip | null         // 大门方位建议

  house_facing: string | null           // 房屋朝向代码
  house_gua: number | null              // 房屋卦数
  house_gua_name: string | null         // 房屋卦名
  house_group: string | null            // 房屋组：东四宅 / 西四宅
  compatibility: string | null          // 人宅相合：相合 / 不合
  compatibility_note: string | null     // 相合说明

  disclaimer: string                    // 免责声明
  [key: string]: unknown
}

// ── CaseCreate / CasePatch（案例增改请求）──────────────────────

export interface CaseCreate {
  name: string
  birth_dt_local: string
  tz: string
  lon: number
  gender?: 'male' | 'female' | null
  city?: string | null
  solar_time_enabled?: boolean
  notes?: string | null
  tags?: string[] | null
}

export interface CasePatch {
  name?: string
  gender?: 'male' | 'female' | null
  city?: string | null
  notes?: string | null
  tags?: string[] | null
  solar_time_enabled?: boolean
}

// ── 分享 ──────────────────────────────────────────────────────
export interface ShareTokenResponse { share_url: string; expires_at: string }
export interface ShareCaseResponse { id: string; name: string; gender: string | null; city: string | null; tags: string[] | null; schema_version: string | null; created_at: string }

// ── API 函数 ──────────────────────────────────────────────────────

export async function fetchCase(caseId: string): Promise<CaseOut> {
  const { data } = await apiClient.get<CaseOut>(`/api/v1/cases/${caseId}`)
  return data
}

export async function fetchCaseList(params?: {
  limit?: number
  q?: string
  tag?: string
  offset?: number
  order?: string
  dir?: string
}): Promise<{ items: CaseOut[]; total: number; next_cursor: string | null }> {
  const { data } = await apiClient.get('/api/v1/cases', { params })
  return data
}

/** POST /api/v1/cases — 创建案例 */
export async function createCase(req: CaseCreate): Promise<CaseOut> {
  const { data } = await apiClient.post<CaseOut>('/api/v1/cases', req)
  return data
}

/** PATCH /api/v1/cases/:id — 更新案例 */
export async function updateCase(caseId: string, req: CasePatch): Promise<CaseOut> {
  const { data } = await apiClient.patch<CaseOut>(`/api/v1/cases/${caseId}`, req)
  return data
}

/** DELETE /api/v1/cases/:id — 删除案例 */
export async function deleteCase(caseId: string): Promise<void> {
  await apiClient.delete(`/api/v1/cases/${caseId}`)
}

/** POST /api/v1/cases/:id/share-token — 生成分享链接 */
export async function createShareToken(caseId: string): Promise<ShareTokenResponse> {
  const { data } = await apiClient.post<ShareTokenResponse>(`/api/v1/cases/${caseId}/share-token`)
  return data
}

/** GET /api/v1/share/:token — 通过分享链接查看 */
export async function fetchSharedCase(token: string): Promise<ShareCaseResponse> {
  const { data } = await apiClient.get<ShareCaseResponse>(`/api/v1/share/${token}`)
  return data
}

export async function computeFullBazi(req: BaziFullRequest): Promise<BaziFullResponse> {
  const { data } = await apiClient.post<BaziFullResponse>('/api/v1/bazi/full', req)
  return data
}

export async function computeZiwei(req: {
  year: number; month: number; day: number; hour: number; minute?: number
  gender: '男' | '女'
  liunian_year?: number; longitude?: number; template_version?: string
}): Promise<ZiweiResponse> {
  const { data } = await apiClient.post<ZiweiResponse>('/api/v1/ziwei/full', req)
  return data
}

export async function computeName(req: {
  surname: string; given_name: string; birth_year?: number
}): Promise<NameAnalysisResponse> {
  const { data } = await apiClient.post<NameAnalysisResponse>('/api/v1/name/analyze', req)
  return data
}

export async function fetchZeriRecommend(params: ZeriParams): Promise<ZeriResponse> {
  const { data } = await apiClient.get<ZeriResponse>('/api/v1/zeri/recommend', { params })
  return data
}

export async function fetchFengshuiBagua(params: FengshuiParams): Promise<FengshuiResponse> {
  const { data } = await apiClient.get<FengshuiResponse>('/api/v1/fengshui/bagua', { params })
  return data
}
