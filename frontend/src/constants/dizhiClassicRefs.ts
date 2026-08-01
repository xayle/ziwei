/** 地支冲合刑害提示（对齐 BE `classic_refs.py` dizhi_ext01~06，供 Adapter 同源）。 */
export type DizhiClassicRef = {
  id: string
  source: string
  text: string
  tags: string[]
  hint_type: 'soft' | 'verified'
}

export const DIZHI_CLASSIC_REFS: readonly DizhiClassicRef[] = [
  {
    id: 'dizhi_ext01',
    source: '《子平真诠评注》·论刑冲会合解法',
    text: '冲者，六冲也，子午卯酉之类是也。',
    tags: ['六冲', '地支', '动变'],
    hint_type: 'verified',
  },
  {
    id: 'dizhi_ext02',
    source: '《子平真诠评注》·论刑冲会合解法',
    text: '合者，六合也，子与丑合之类是也。',
    tags: ['六合', '地支', '化气'],
    hint_type: 'verified',
  },
  {
    id: 'dizhi_ext03',
    source: '《子平真诠评注》·论刑冲会合解法',
    text: '会者，三会也，申子辰之类是也。',
    tags: ['三合', '地支', '五行'],
    hint_type: 'verified',
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
