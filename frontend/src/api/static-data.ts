/**
 * static-data.ts — 静态数据查询 API（术语、城市、典籍、概念）
 */
import apiClient from './client'

// ── 类型定义 ──────────────────────────────────────────────────

export interface GlossaryItem {
  term: string
  pinyin: string
  definition: string
  category: '格局' | '神煞' | '五行' | '十神' | '大运' | '其他'
  classic_source?: string
}

export interface GlossaryUpdateRequest {
  definition: string
  pinyin?: string
  classic_source?: string
}

export interface CityModel {
  name: string
  province: string
  lng: number
  lat: number
  city_type: '直辖市' | '省会' | '计划单列市'
}

export interface ClassicPassage {
  id?: string
  title?: string
  content?: string
  source?: string
  tags?: string[]
  [key: string]: unknown
}

export interface ConceptModel {
  id: string
  term: string
  category: 'bazi' | 'ziwei'
  definition: string
  aliases: string[]
  related: string[]
}

// ── API 函数 ──────────────────────────────────────────────────

/** GET /api/v1/glossary — 术语表 */
export async function getGlossary(params?: { q?: string; category?: string; limit?: number }): Promise<GlossaryItem[]> {
  const { data } = await apiClient.get<GlossaryItem[]>('/api/v1/glossary', { params })
  return data
}

/** PUT /api/v1/glossary/:term — 更新术语 */
export async function updateGlossaryTerm(term: string, req: GlossaryUpdateRequest): Promise<GlossaryItem> {
  const { data } = await apiClient.put<GlossaryItem>(`/api/v1/glossary/${encodeURIComponent(term)}`, req)
  return data
}

/** GET /api/v1/cities — 城市列表 */
export async function getCities(params?: { q?: string; city_type?: string }): Promise<CityModel[]> {
  const { data } = await apiClient.get<CityModel[]>('/api/v1/cities', { params })
  return data
}

/** GET /api/v1/classics — 典籍搜索 */
export async function getClassics(params?: { query?: string; tag?: string; limit?: number }): Promise<ClassicPassage[]> {
  const { data } = await apiClient.get<ClassicPassage[]>('/api/v1/classics', { params })
  return data
}

/** GET /api/v1/docs/concepts — 概念查询 */
export async function getConcepts(params?: { category?: 'bazi' | 'ziwei'; q?: string; limit?: number }): Promise<ConceptModel[]> {
  const { data } = await apiClient.get<ConceptModel[]>('/api/v1/docs/concepts', { params })
  return data
}
