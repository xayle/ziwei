import apiClient from './client'

export interface CaseCreate {
  name: string
  gender?: 'male' | 'female' | null
  birth_dt_local: string
  tz: string
  lon: number
  city?: string | null
  current_city?: string | null
  current_province?: string | null
  current_lon?: number | null
  current_tz?: string | null
  calendar_mode?: 'gregorian' | 'lunar'
  is_leap_month?: boolean
  birth_time_precision?: 'exact' | 'hour' | 'approximate' | 'unknown'
  unknown_time_fallback?: 'midday' | 'noon' | 'start_of_hour'
  solar_time_enabled?: boolean
  year_divide?: 'lichun' | 'normal'
  day_divide?: 'solar_next' | 'forward' | 'current'
  zi_day_rule?: 'sxtwl' | 'early_zi_prev_day' | 'early_zi_same_day'
  ziwei_brightness_method?: 'standard' | 'zhongzhou' | 'mod1' | 'mod2'
  ziwei_youbi_method?: 'month' | 'hour'
  ziwei_sihua_method?: 'quanshu' | 'zhongzhou'
  ziwei_liunian_sihua_method?: 'year_stem' | 'life_palace_stem'
  ziwei_kuiyue_method?: 'standard' | 'gengxin_mahu' | 'gengxin_huima' | 'liuxin_mahu'
  ziwei_tianma_method?: 'year' | 'month'
  ziwei_template_version?: 'standard' | 'pro' | 'simple'
  notes?: string | null
  tags?: string | null
}

export type CasePatch = Partial<CaseCreate>

export interface CaseOut extends CaseCreate {
  id: string
  birth_dt?: string | null
  created_at: string
  updated_at: string
  last_snapshot_at?: string | null
  tags?: string[] | null
}

export interface CaseListResponse {
  items: CaseOut[]
  total: number
  next_cursor?: string | null
}

export async function createCase(payload: CaseCreate): Promise<CaseOut> {
  const { data } = await apiClient.post<CaseOut>('/api/v1/cases', payload)
  return data
}

export async function patchCase(caseId: string, payload: CasePatch): Promise<CaseOut> {
  const { data } = await apiClient.patch<CaseOut>(`/api/v1/cases/${caseId}`, payload)
  return data
}

export async function getCase(caseId: string): Promise<CaseOut> {
  const { data } = await apiClient.get<CaseOut>(`/api/v1/cases/${caseId}`)
  return data
}

export async function listCases(limit = 20): Promise<CaseListResponse> {
  const { data } = await apiClient.get<CaseListResponse>('/api/v1/cases', { params: { limit } })
  return data
}
