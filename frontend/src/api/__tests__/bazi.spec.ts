/**
 * api/bazi.spec.ts — BaziAPI 模块单元测试（mock axios）
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { Mock } from 'vitest'

vi.mock('@/api/client', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  },
}))

import apiClient from '@/api/client'
import { computeBazi } from '@/api/bazi'
import type { BaziResponse } from '@/api/bazi'

const MOCK_RESPONSE: BaziResponse = {
  pillars_primary: {
    year:  { stem: '庚', branch: '午' },
    month: { stem: '丁', branch: '丑' },
    day:   { stem: '甲', branch: '子' },
    hour:  { stem: '壬', branch: '辰' },
  },
  ten_gods: { year: '七杀', month: '伤官', day: '日主', hour: '偏印' },
  yongshen: {
    favor: ['水', '金'],
    neutral: ['土'],
    avoid: ['木', '火'],
    summary: '日主甲木，建议用水金',
  },
  day_master_strength: { label: '偏弱', strength: 'weak', score: 38 },
  geju: { name: '伤官见官', description: '格局说明' },
  wuxing_score: { wood: 3, fire: 1, earth: 2, metal: 2, water: 2 },
  palace: { mingong: '辰', taiyuan: '甲子' },
  start_dayun_age: 3,
  dayun: {
    cycles: [
      { ganzhi: '戊寅', start_age: 3,  start_year: 1993, end_year: 2003 },
      { ganzhi: '己卯', start_age: 13, start_year: 2003, end_year: 2013 },
    ],
  },
}

describe('computeBazi()', () => {
  beforeEach(() => vi.clearAllMocks())

  it('调用 POST /api/v1/bazi/full 并返回数据', async () => {
    ;(apiClient.post as Mock).mockResolvedValueOnce({ data: MOCK_RESPONSE })

    const req = { dt: '1990-01-15T08:30:00', lon: 116.4, tz: 'Asia/Shanghai' }
    const result = await computeBazi(req)

    expect(apiClient.post).toHaveBeenCalledOnce()
    expect(apiClient.post).toHaveBeenCalledWith('/api/v1/bazi/full', req)
    expect(result.pillars_primary.day.stem).toBe('甲')
    expect(result.pillars_primary.day.branch).toBe('子')
  })

  it('包含可选参数 mode/gender 时全部传递', async () => {
    ;(apiClient.post as Mock).mockResolvedValueOnce({ data: MOCK_RESPONSE })

    const req = {
      dt: '1990-01-15T08:30:00',
      lon: 116.4,
      tz: 'Asia/Shanghai',
      mode: 'dual' as const,
      gender: 'male' as const,
      solar_time_enabled: true,
    }
    await computeBazi(req)

    expect(apiClient.post).toHaveBeenCalledWith('/api/v1/bazi/full', req)
  })

  it('正确解析用神/喜忌数据', async () => {
    ;(apiClient.post as Mock).mockResolvedValueOnce({ data: MOCK_RESPONSE })

    const result = await computeBazi({ dt: '1990-01-15T08:30:00', lon: 116.4, tz: 'Asia/Shanghai' })

    expect(result.yongshen).toBeDefined()
    expect(result.yongshen!.favor).toContain('水')
    expect(result.yongshen!.avoid).toContain('火')
    expect(result.wuxing_score).toBeDefined()
    expect(result.dayun?.cycles).toHaveLength(2)
  })
})
