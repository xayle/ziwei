/**
 * api/name.spec.ts — Name API 模块单元测试（mock axios）
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
import { analyzeName, suggestNames } from '@/api/name'

const MOCK_ANALYSIS = {
  surname: '张',
  given_name: '伟',
  full_name: '张伟',
  tianGe: 12, renGe: 18, diGe: 9, waiGe: 3, zongGe: 18,
  tianGe_str: '天格:12', renGe_str: '人格:18',
  diGe_str: '地格:9', waiGe_str: '外格:3', zongGe_str: '总格:18',
  renke_score: 7, sancai_pattern: '木火土', sancai_score: 8,
  element_composition: ['木', '火'],
  overall_score: 72, lucky_numbers: [3, 8],
  summary: '人格18水，主聪慧但略带孤傲。',
  details: '...',
}

const MOCK_SUGGEST = {
  surname: '张',
  name_length: 2,
  preferred_elements: ['水', '木'],
  total_candidates_evaluated: 480,
  suggestions: [
    {
      given_name: '泽林',
      overall_score: 85,
      renke_score: 9,
      sancai_score: 8,
      sancai_pattern: '水木木',
      element_composition: ['水', '木'],
      summary: '水木相生，格局上佳。',
    },
  ],
  algorithm_version: '1.0.0',
}

describe('analyzeName()', () => {
  beforeEach(() => vi.clearAllMocks())

  it('调用 POST /api/v1/name/analyze', async () => {
    ;(apiClient.post as Mock).mockResolvedValueOnce({ data: MOCK_ANALYSIS })
    const result = await analyzeName({ surname: '张', given_name: '伟' })
    expect(apiClient.post).toHaveBeenCalledWith('/api/v1/name/analyze', {
      surname: '张', given_name: '伟',
    })
    expect(result.overall_score).toBe(72)
    expect(result.sancai_pattern).toBe('木火土')
  })

  it('传入 birth_year 时一并发送', async () => {
    ;(apiClient.post as Mock).mockResolvedValueOnce({ data: MOCK_ANALYSIS })
    await analyzeName({ surname: '张', given_name: '伟', birth_year: 1990 })
    expect(apiClient.post).toHaveBeenCalledWith('/api/v1/name/analyze', {
      surname: '张', given_name: '伟', birth_year: 1990,
    })
  })
})

describe('suggestNames()', () => {
  beforeEach(() => vi.clearAllMocks())

  it('调用 POST /api/v1/name/suggest', async () => {
    ;(apiClient.post as Mock).mockResolvedValueOnce({ data: MOCK_SUGGEST })
    const result = await suggestNames({
      surname: '张',
      name_length: 2,
      preferred_elements: ['水', '木'],
    })
    expect(apiClient.post).toHaveBeenCalledWith('/api/v1/name/suggest', {
      surname: '张', name_length: 2, preferred_elements: ['水', '木'],
    })
    expect(result.suggestions).toHaveLength(1)
    expect(result.suggestions[0].given_name).toBe('泽林')
    expect(result.algorithm_version).toBe('1.0.0')
  })
})
