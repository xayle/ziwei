/**
 * western.ts — 西方占星出生盘 API 客户端（§6.1）
 */
import apiClient from './client'

// ── 类型定义 ──────────────────────────────────────────────────

export interface PlanetDetail {
  name_en:    string
  name_cn:    string
  symbol:     string
  longitude:  number
  retrograde: boolean
  sign_index: number
  sign_cn:    string
  sign_en:    string
  sign_symbol: string
  element:    string
  element_cn: string
  mode:       string
  mode_cn:    string
  degree:     number
  degree_str: string
}

export interface ChartPoint {
  longitude:   number
  sign_index:  number
  sign_cn:     string
  sign_en:     string
  sign_symbol: string
  element:     string
  element_cn:  string
  mode:        string
  mode_cn:     string
  degree:      number
  degree_str:  string
}

export interface AspectItem {
  planet1:   string
  planet2:   string
  aspect_cn: string
  aspect_en: string
  angle:     number
  orb:       number
  color:     string
}

export interface WesternChartResponse {
  julian_day:      number
  planets:         PlanetDetail[]
  ascendant:       ChartPoint
  midheaven:       ChartPoint
  aspects:         AspectItem[]
  element_counts:  Record<string, number>
  mode_counts:     Record<string, number>
  geocentric_longitudes: Record<string, number>
  heliocentric_longitudes: Record<string, number>
}

export interface WesternChartParams {
  dt:  string    // ISO 8601 本地时间
  lat: number
  lon: number
  tz:  string
}

// §6.2 太阳回归
export interface SolarReturnParams {
  natal_dt:  string
  natal_lat: number
  natal_lon: number
  natal_tz:  string
  sr_year:   number
  sr_lat:    number
  sr_lon:    number
}

export interface SolarReturnResponse extends WesternChartResponse {
  sr_dt_utc:     string
  sr_year:       number
  natal_sun_lon: number
}

// ── API 函数 ──────────────────────────────────────────────────

export async function getWesternChart(params: WesternChartParams): Promise<WesternChartResponse> {
  const { data } = await apiClient.get<WesternChartResponse>('/api/v1/western/chart', {
    params: {
      dt:  params.dt,
      lat: params.lat,
      lon: params.lon,
      tz:  params.tz,
    }
  })
  return data
}

export async function getSolarReturn(params: SolarReturnParams): Promise<SolarReturnResponse> {
  const { data } = await apiClient.get<SolarReturnResponse>('/api/v1/western/solar-return', {
    params: {
      natal_dt:  params.natal_dt,
      natal_lat: params.natal_lat,
      natal_lon: params.natal_lon,
      natal_tz:  params.natal_tz,
      sr_year:   params.sr_year,
      sr_lat:    params.sr_lat,
      sr_lon:    params.sr_lon,
    }
  })
  return data
}
