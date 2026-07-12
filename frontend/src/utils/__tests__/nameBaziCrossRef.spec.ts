import { describe, expect, it } from 'vitest'
import type { BaziResponse } from '@/api/bazi'
import type { NameAnalysisResponse } from '@/api/name'
import { buildNameBaziCrossRef } from '@/utils/nameBaziCrossRef'

const grid = (element: string) => ({
  number: 1,
  element,
  lucky: '吉',
  score: 8,
  desc: '测试',
})

const sampleName: NameAnalysisResponse = {
  surname: '刘',
  given_name: '博',
  tianke: grid('金'),
  renke: grid('木'),
  dike: grid('水'),
  waike: grid('火'),
  zonge: grid('土'),
  sancai: { pattern: '木水火', lucky: '吉', score: 8, desc: '三才吉' },
  overall_score: 82,
  summary: '测试摘要',
  algorithm_version: 'v1',
}

const sampleBazi = {
  yongshen: {
    favor: ['wood', 'water'],
    avoid: ['metal'],
    rationale: '日主偏弱，喜木水',
  },
} as BaziResponse

describe('nameBaziCrossRef', () => {
  it('maps english yongshen to chinese elements', () => {
    const ref = buildNameBaziCrossRef(sampleName, sampleBazi)
    expect(ref).not.toBeNull()
    expect(ref?.favorCn).toEqual(['木', '水'])
    expect(ref?.avoidCn).toEqual(['金'])
    expect(ref?.items.find((item) => item.label === '人格')?.alignment).toBe('favor')
    expect(ref?.items.find((item) => item.label === '天格')?.alignment).toBe('avoid')
    expect(ref?.verdict).toContain('相合')
  })

  it('returns null without bazi yongshen', () => {
    expect(buildNameBaziCrossRef(sampleName, null)).toBeNull()
  })
})
