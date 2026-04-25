/**
 * api/report.spec.ts — report API 模块单元测试（mock axios）
 * 覆盖：fetchCase / fetchCaseList / computeFullBazi / computeZiwei /
 *        computeName / fetchZeriRecommend / fetchFengshuiBagua
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { Mock } from 'vitest'

vi.mock('@/api/client', () => ({
  default: {
    get:  vi.fn(),
    post: vi.fn(),
    interceptors: {
      request:  { use: vi.fn() },
      response: { use: vi.fn() },
    },
  },
}))

import apiClient from '@/api/client'
import {
  fetchCase,
  fetchCaseList,
  computeFullBazi,
  computeZiwei,
  computeName,
  fetchZeriRecommend,
  fetchFengshuiBagua,
  type CaseOut,
  type BaziFullResponse,
  type ZeriResponse,
  type FengshuiResponse,
} from '@/api/report'
import type { ZiweiResponse } from '@/api/ziwei'
import type { NameAnalysisResponse } from '@/api/name'

// ─── mock 数据 ────────────────────────────────────────────────────

const MOCK_CASE: CaseOut = {
  id: '42',
  name: '张三',
  gender: 'male',
  birth_dt_local: '1990-05-15T08:30:00',
  tz: 'Asia/Shanghai',
  birth_dt: '1990-05-15T00:30:00Z',
  lon: 116.4,
  city: '北京',
  solar_time_enabled: false,
  notes: null,
  tags: ['测试'],
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
}

const MOCK_BAZI: BaziFullResponse = {
  api_version: '2.0',
  request_id: 'req-001',
  pillars_primary: {
    year:  { stem: '庚', branch: '午' },
    month: { stem: '丁', branch: '丑' },
    day:   { stem: '甲', branch: '子' },
    hour:  { stem: '壬', branch: '辰' },
  },
  ten_gods: { year: '七杀', month: '伤官', day: '日主', hour: '偏印' },
  day_master_strength: { score: 38, tier: '偏弱', factors: [] },
  yongshen: { favor: ['水', '金'], avoid: ['木', '火'], rationale: '甲木以水为源' },
  geju: { geju_name: '伤官见官', geju_level: '中', inference_tags: [], interpretation_text: '说明', is_broken: false },
  palace: {
    ming_gong: { palace_name: '命宫', main_stars: [], element: '土', meaning: '' },
    shen_gong: { palace_name: '身宫', main_stars: [], element: '水', meaning: '' },
    twelve_palaces: [],
  },
  shensha: [],
  dayun: { items: [{ start_age: 3, start_year: 2000, stem: '戊', branch: '寅', narrative: '大运说明' }] },
  liunian: { items: [] },
  liunian_detail: null,
  start_dayun_age: 3,
  wuxing_score: { wood: 3, fire: 1, earth: 2, metal: 2, water: 2 },
  wuxing_weak: ['火'],
  wuxing_strong: ['木'],
  balance_advice: '补水金',
  dizhi_relations: null,
  tiangan_clashes: null,
  current_fortune_summary: null,
  bazi_summary: '六段综述...',
}

const MOCK_CASE_LIST = { items: [MOCK_CASE], total: 1, next_cursor: null }

const MOCK_ZERI: ZeriResponse = {
  dates: [
    { date: '2026-04-01', score: 85, tags: ['吉日', '天德'], description: '宜嫁娶出行' },
    { date: '2026-04-05', score: 72, tags: ['小吉'], description: '宜一般事务' },
  ],
}

const MOCK_FENGSHUI: FengshuiResponse = {
  lucky_directions: ['南', '东南'],
  unlucky_directions: ['北', '西北'],
}

// ─── fetchCase ────────────────────────────────────────────────────

describe('fetchCase()', () => {
  beforeEach(() => vi.clearAllMocks())

  it('调用 GET /api/v1/cases/:id 并返回 CaseOut', async () => {
    ;(apiClient.get as Mock).mockResolvedValueOnce({ data: MOCK_CASE })
    const res = await fetchCase('42')
    expect(apiClient.get).toHaveBeenCalledOnce()
    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/cases/42')
    expect(res.id).toBe('42')
    expect(res.name).toBe('张三')
    expect(res.gender).toBe('male')
    expect(res.birth_dt_local).toBe('1990-05-15T08:30:00')
  })

  it('返回 solar_time_enabled = false', async () => {
    ;(apiClient.get as Mock).mockResolvedValueOnce({ data: MOCK_CASE })
    const res = await fetchCase('42')
    expect(res.solar_time_enabled).toBe(false)
  })

  it('API 失败时 Promise reject', async () => {
    ;(apiClient.get as Mock).mockRejectedValueOnce(new Error('Network Error'))
    await expect(fetchCase('42')).rejects.toThrow('Network Error')
  })
})

// ─── fetchCaseList ────────────────────────────────────────────────

describe('fetchCaseList()', () => {
  beforeEach(() => vi.clearAllMocks())

  it('无参数时调用 GET /api/v1/cases', async () => {
    ;(apiClient.get as Mock).mockResolvedValueOnce({ data: MOCK_CASE_LIST })
    const res = await fetchCaseList()
    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/cases', { params: undefined })
    expect(res.items).toHaveLength(1)
    expect(res.total).toBe(1)
    expect(res.next_cursor).toBeNull()
  })

  it('传入搜索参数时 params 正确传递', async () => {
    ;(apiClient.get as Mock).mockResolvedValueOnce({ data: MOCK_CASE_LIST })
    await fetchCaseList({ limit: 20, q: '张' })
    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/cases', { params: { limit: 20, q: '张' } })
  })

  it('返回空列表时结构正常', async () => {
    ;(apiClient.get as Mock).mockResolvedValueOnce({ data: { items: [], total: 0, next_cursor: null } })
    const res = await fetchCaseList()
    expect(res.items).toHaveLength(0)
    expect(res.total).toBe(0)
  })
})

// ─── computeFullBazi ──────────────────────────────────────────────

describe('computeFullBazi()', () => {
  beforeEach(() => vi.clearAllMocks())

  it('调用 POST /api/v1/bazi/full 并返回 BaziFullResponse', async () => {
    ;(apiClient.post as Mock).mockResolvedValueOnce({ data: MOCK_BAZI })
    const req = { dt: '1990-05-15T08:30:00', lon: 116.4, tz: 'Asia/Shanghai' }
    const res = await computeFullBazi(req)
    expect(apiClient.post).toHaveBeenCalledWith('/api/v1/bazi/full', req)
    expect(res.pillars_primary.day.stem).toBe('甲')
    expect(res.yongshen.favor).toContain('水')
    expect(res.dayun.items).toHaveLength(1)
    expect(res.bazi_summary).toBeTruthy()
  })

  it('带可选参数 mode/liunian_years 时正确传递', async () => {
    ;(apiClient.post as Mock).mockResolvedValueOnce({ data: MOCK_BAZI })
    const req = {
      dt: '1990-05-15T08:30:00', lon: 116.4, tz: 'Asia/Shanghai',
      mode: 'dual' as const,
      solar_time_enabled: true,
      liunian_years: [2024, 2025, 2026],
    }
    await computeFullBazi(req)
    expect(apiClient.post).toHaveBeenCalledWith('/api/v1/bazi/full', req)
  })

  it('结果包含 wuxing_score 五个字段', async () => {
    ;(apiClient.post as Mock).mockResolvedValueOnce({ data: MOCK_BAZI })
    const res = await computeFullBazi({ dt: '1990-05-15T08:30:00', lon: 116.4, tz: 'Asia/Shanghai' })
    const wx = res.wuxing_score
    expect(wx.wood + wx.fire + wx.earth + wx.metal + wx.water).toBeGreaterThan(0)
  })

  it('API 失败时 Promise reject', async () => {
    ;(apiClient.post as Mock).mockRejectedValueOnce(new Error('500'))
    await expect(
      computeFullBazi({ dt: '1990-05-15T08:30:00', lon: 116.4, tz: 'Asia/Shanghai' })
    ).rejects.toThrow('500')
  })
})

// ─── computeZiwei ────────────────────────────────────────────────

describe('computeZiwei()', () => {
  beforeEach(() => vi.clearAllMocks())

  const MOCK_ZIWEI: ZiweiResponse = {
    api_version: '1.0',
    request_id: 'req-z01',
    palaces: [],
    stars: {},
    dayun: { items: [] } as any,
    liunian: { items: [] } as any,
    formatted_ganzhi: '',
    geju: [] as any,
    ming_zhu: '',
    shen_zhu: '',
    shenshas: [] as any,
  } as unknown as ZiweiResponse

  it('调用 POST /api/v1/ziwei/full', async () => {
    ;(apiClient.post as Mock).mockResolvedValueOnce({ data: MOCK_ZIWEI })
    const req = { year: 1990, month: 5, day: 15, hour: 8, minute: 30, gender: '男' as const }
    await computeZiwei(req)
    expect(apiClient.post).toHaveBeenCalledWith('/api/v1/ziwei/full', req)
  })

  it('带 template_version 时正确传递', async () => {
    ;(apiClient.post as Mock).mockResolvedValueOnce({ data: MOCK_ZIWEI })
    const req = {
      year: 1990, month: 5, day: 15, hour: 8, gender: '女' as const,
      template_version: 'pro',
    }
    await computeZiwei(req)
    expect(apiClient.post).toHaveBeenCalledWith('/api/v1/ziwei/full', req)
  })
})

// ─── computeName ─────────────────────────────────────────────────

describe('computeName()', () => {
  beforeEach(() => vi.clearAllMocks())

  const MOCK_NAME: NameAnalysisResponse = {
    surname: '张',
    given_name: '三',
    total_score: 78,
    wuge: { heaven: 8, person: 16, earth: 9, outer: 1, total: 17, scores: {} as any },
    sancai: { pattern: '土水木', rating: '中', description: '' },
    wuxing_balance: '',
    recommendations: [],
    lucky_numbers: [],
    birth_year: 1990,
  } as unknown as NameAnalysisResponse

  it('调用 POST /api/v1/name/analyze', async () => {
    ;(apiClient.post as Mock).mockResolvedValueOnce({ data: MOCK_NAME })
    const req = { surname: '张', given_name: '三', birth_year: 1990 }
    await computeName(req)
    expect(apiClient.post).toHaveBeenCalledWith('/api/v1/name/analyze', req)
  })

  it('不带 birth_year 也可正常调用', async () => {
    ;(apiClient.post as Mock).mockResolvedValueOnce({ data: MOCK_NAME })
    await computeName({ surname: '李', given_name: '四' })
    expect(apiClient.post).toHaveBeenCalledWith('/api/v1/name/analyze', { surname: '李', given_name: '四' })
  })
})

// ─── fetchZeriRecommend ───────────────────────────────────────────

describe('fetchZeriRecommend()', () => {
  beforeEach(() => vi.clearAllMocks())

  it('调用 GET /api/v1/zeri/recommend 并传入 params', async () => {
    ;(apiClient.get as Mock).mockResolvedValueOnce({ data: MOCK_ZERI })
    const params = {
      year: 2026, month: 4,
      life_palace_branch: '子',
      wuxing_ju_name: '水二局',
      purpose: 'wedding',
    }
    const res = await fetchZeriRecommend(params)
    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/zeri/recommend', { params })
    expect(res.dates).toHaveLength(2)
    expect(res.dates[0].score).toBe(85)
  })

  it('无 purpose 时仍可调用（仅必填参数）', async () => {
    ;(apiClient.get as Mock).mockResolvedValueOnce({ data: MOCK_ZERI })
    const params = { year: 2026, month: 4, life_palace_branch: '午', wuxing_ju_name: '火六局' }
    await fetchZeriRecommend(params)
    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/zeri/recommend', { params })
  })

  it('返回日期包含 tags 数组', async () => {
    ;(apiClient.get as Mock).mockResolvedValueOnce({ data: MOCK_ZERI })
    const res = await fetchZeriRecommend({ year: 2026, month: 4, life_palace_branch: '子', wuxing_ju_name: '水二局' })
    expect(Array.isArray(res.dates[0].tags)).toBe(true)
    expect(res.dates[0].tags).toContain('吉日')
  })
})

// ─── fetchFengshuiBagua ───────────────────────────────────────────

describe('fetchFengshuiBagua()', () => {
  beforeEach(() => vi.clearAllMocks())

  it('调用 GET /api/v1/fengshui/bagua 并传入 params', async () => {
    ;(apiClient.get as Mock).mockResolvedValueOnce({ data: MOCK_FENGSHUI })
    const params = { birth_year: 1990, gender: '男' as const }
    const res = await fetchFengshuiBagua(params)
    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/fengshui/bagua', { params })
    expect(res.lucky_directions).toContain('南')
    expect(res.unlucky_directions).toContain('北')
  })

  it('女性参数也正确传递', async () => {
    ;(apiClient.get as Mock).mockResolvedValueOnce({ data: MOCK_FENGSHUI })
    const params = { birth_year: 1985, gender: '女' as const }
    await fetchFengshuiBagua(params)
    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/fengshui/bagua', { params })
  })

  it('lucky_directions 和 unlucky_directions 均为字符串数组', async () => {
    ;(apiClient.get as Mock).mockResolvedValueOnce({ data: MOCK_FENGSHUI })
    const res = await fetchFengshuiBagua({ birth_year: 1990, gender: '男' })
    expect(Array.isArray(res.lucky_directions)).toBe(true)
    expect(Array.isArray(res.unlucky_directions)).toBe(true)
    ;(res.lucky_directions as string[]).forEach(d => expect(typeof d).toBe('string'))
  })
})
