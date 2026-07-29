/** 地支冲合刑害软提示（对齐 BE `classic_refs.py` dizhi_ext01~06，供 Adapter 同源）。 */
export type DizhiClassicRef = {
  id: string
  source: string
  text: string
  tags: string[]
  hint_type: 'soft'
}

export const DIZHI_CLASSIC_REFS: readonly DizhiClassicRef[] = [
  {
    id: 'dizhi_ext01',
    source: '《三命通会·论冲》',
    text: '六冲者，子午冲、丑未冲、寅申冲、卯酉冲、辰戌冲、巳亥冲；冲则动，动则变，变有吉凶之分。',
    tags: ['六冲', '地支', '动变'],
    hint_type: 'soft',
  },
  {
    id: 'dizhi_ext02',
    source: '《渊海子平·论合》',
    text: '六合者，子丑合、寅亥合、卯戌合、辰酉合、巳申合、午未合；合则化，化则转变五行，意义深远。',
    tags: ['六合', '地支', '化气'],
    hint_type: 'soft',
  },
  {
    id: 'dizhi_ext03',
    source: '《子平真诠》',
    text: '三合局者，寅午戌合火、巳酉丑合金、申子辰合水、亥卯未合木；会三局则五行力量大增。',
    tags: ['三合', '地支', '五行'],
    hint_type: 'soft',
  },
  {
    id: 'dizhi_ext04',
    source: '《滴天髓》',
    text: '刑者，三刑寅巳申、丑戌未、子卯自刑辰午酉亥；刑主损伤，刑中亦有生机，须辨喜忌而论。',
    tags: ['刑', '地支', '损伤'],
    hint_type: 'soft',
  },
  {
    id: 'dizhi_ext05',
    source: '《三命通会》',
    text: '害者，子未害、丑午害、寅巳害、卯辰害、申亥害、酉戌害；害则阻碍，逢害宜防人际摩擦。',
    tags: ['害', '地支', '阻碍'],
    hint_type: 'soft',
  },
  {
    id: 'dizhi_ext06',
    source: '《渊海子平》',
    text: '地支藏干者，月令藏干为用神之本；日支藏干为配偶宫之象；时支藏干为子女晚年之信息。',
    tags: ['藏干', '月令', '日支', '时支'],
    hint_type: 'soft',
  },
] as const
