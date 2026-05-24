/**
 * api/ziwei.spec.ts — ZiweiAPI 模块单元测试（mock axios）
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
import { computeZiwei, demoZiwei } from '@/api/ziwei'
import type { ZiweiResponse } from '@/api/ziwei'

const MOCK_ZIWEI: ZiweiResponse = {
  birth_solar: '1990-01-15',
  gender: '男',
  lunar: {
    lunar_year: 1989,
    lunar_month: 12,
    lunar_day: 19,
    is_leap_month: false,
    year_gz: '己巳',
    month_gz: '戊子',
    hour_branch: '辰',
    jieqi_month_gz: '戊子',
  },
  life_palace_gz: '辰',
  body_palace_gz: '戌',
  wuxing_ju: 4,
  wuxing_ju_name: '金四局',
  palaces: [
    {
      index: 0,
      name: '命宫',
      branch: '辰',
      stem: '戊',
      main_stars: [
        { name: '紫微', brightness: '旺', brightness_val: 5, transforms: [] },
        { name: '天相', brightness: '庙', brightness_val: 6, transforms: ['化科'] },
      ],
      aux_stars: [{ name: '左辅', brightness: '得', brightness_val: 4, transforms: [] }, { name: '右弼', brightness: '得', brightness_val: 4, transforms: [] }],
      analysis: '命宫紫微天相，贵人运旺。',
      analysis_tags: ['贵人', '稳重'],
      conclusion: '整体上佳',
      explanation: '详细说明',
      suggestion: '建议...',
      tooltip: '提示',
      xiaoxian_ages: [2, 14, 26, 38],
      opposition_name: '迁移宫',
    },
  ],
  dayun: {
    forward: true,
    start_age: 3,
    start_age_text: '3岁起运',
    items: [
      { index: 0, ganzhi: '庚午', start_age: 3,  end_age: 12, start_year: 1993, sihua: {} },
      { index: 1, ganzhi: '辛未', start_age: 13, end_age: 22, start_year: 2003, sihua: {} },
    ],
  },
  life_ruler_star: '紫微',
  body_ruler_star: '天府',
  laiyin_palace: '官禄宫',
  true_solar_time: '1990-01-15T09:02:00',
  summary: '紫微星入命，格局崇高。',
  analysis: { overall: '整体运势上佳', career: '事业发展顺遂' },
  patterns: [
    { name: '紫微坐命', level: '大格', description: '贵格', source: '斗数全书' },
  ],
  remedies: [
    { category: '佩戴', action: '佩戴白水晶', reason: '增旺金局' },
  ],
  life_suggestions: [
    { domain: '事业', suggestion: '适合从政或大型企业', score: 85 },
  ],
  template_version: 'standard',
  algorithm_version: '3.0.0',
  engine_version: '3.0.0',
}

describe('computeZiwei()', () => {
  beforeEach(() => vi.clearAllMocks())

  it('调用 POST /api/v1/ziwei/full 并返回数据', async () => {
    ;(apiClient.post as Mock).mockResolvedValueOnce({ data: MOCK_ZIWEI })

    const req = {
      year: 1990, month: 1, day: 15,
      hour: 8, minute: 30, gender: '男' as const,
    }
    const result = await computeZiwei(req)

    expect(apiClient.post).toHaveBeenCalledOnce()
    expect(apiClient.post).toHaveBeenCalledWith('/api/v1/ziwei/full', req)
    expect(result.wuxing_ju_name).toBe('金四局')
    expect(result.palaces).toHaveLength(1)
  })

  it('包含可选参数 liunian_year/longitude 时全部传递', async () => {
    ;(apiClient.post as Mock).mockResolvedValueOnce({ data: MOCK_ZIWEI })

    const req = {
      year: 1990, month: 1, day: 15,
      hour: 8, gender: '男' as const,
      liunian_year: 2025,
      longitude: 116.4,
      template_version: 'pro' as const,
    }
    await computeZiwei(req)

    expect(apiClient.post).toHaveBeenCalledWith('/api/v1/ziwei/full', req)
  })

  it('正确解析大运/格局/建议数据', async () => {
    ;(apiClient.post as Mock).mockResolvedValueOnce({ data: MOCK_ZIWEI })

    const result = await computeZiwei({
      year: 1990, month: 1, day: 15, hour: 8, gender: '男',
    })

    expect(result.dayun.items).toHaveLength(2)
    expect(result.patterns[0].name).toBe('紫微坐命')
    expect(result.life_suggestions[0].domain).toBe('事业')
    expect(result.remedies[0].category).toBe('佩戴')
  })
})

describe('demoZiwei()', () => {
  beforeEach(() => vi.clearAllMocks())

  it('调用 GET /api/v1/ziwei/demo 并返回数据', async () => {
    ;(apiClient.get as Mock).mockResolvedValueOnce({ data: MOCK_ZIWEI })

    const result = await demoZiwei()

    expect(apiClient.get).toHaveBeenCalledOnce()
    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/ziwei/demo')
    expect(result.gender).toBe('男')
    expect(result.life_ruler_star).toBe('紫微')
  })
})
