import { describe, expect, it } from 'vitest'
import { parseDayunNarrativeSections } from '@/utils/parseDayunNarrativeSections'

describe('parseDayunNarrativeSections', () => {
  it('splits labeled domains', () => {
    const sections = parseDayunNarrativeSections(
      '【0岁—9岁·丙子大运】天干丙。\n\n'
      + '【事业】事业文。\n\n'
      + '【财运】财运文。\n\n'
      + '【情感】情感文。\n\n'
      + '【健康】健康文。\n\n'
      + '此运用神火气场顺旺。\n\n'
      + '【古籍佐证】\n'
      + '  ——《渊海子平》：「岁运并临。」\n\n'
      + '（仅供学术研究参考，不构成任何形式的预测或建议）',
    )
    expect(sections?.career).toContain('事业文')
    expect(sections?.wealth).toContain('财运文')
    expect(sections?.love).toContain('情感文')
    expect(sections?.health).toContain('健康文')
    expect(sections?.classics[0]?.source).toContain('渊海子平')
    expect(sections?.disclaimer).toContain('仅供学术研究参考')
  })
})
