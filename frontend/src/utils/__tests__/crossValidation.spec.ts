import { describe, expect, it } from 'vitest'
import { validateBaziZiweiConsistency } from '@/utils/crossValidation'

describe('crossValidation', () => {
  it('fails when data missing', () => {
    const result = validateBaziZiweiConsistency(null, null)
    expect(result.overall).toBe('fail')
  })

  it('passes when day pillars match', () => {
    const result = validateBaziZiweiConsistency(
      {
        pillars_primary: { day: { stem: '甲', branch: '子' } },
        geju: { geju_name: '正官格' },
        yongshen: { favor: ['水'] },
      } as never,
      {
        lunar: { day_gz: '甲子', hour_gz: '丙寅' },
        life_palace_gz: '甲子',
        wuxing_ju_name: '水二局',
      } as never,
    )
    expect(result.items.find((i) => i.label === '日柱')?.status).toBe('pass')
  })
})
