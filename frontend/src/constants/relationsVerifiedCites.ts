/**
 * 关系卷 verified cite 摘句（对齐 BE `relations_classic_cite`）。
 * 仅收录已 verified 宿主/子集；dizhi_ext01/02/03 不进本表。
 */
export type RelationsVerifiedCite = {
  id: string
  title: string
  passage: string
  tags: string[]
}

export const RELATIONS_VERIFIED_CITES: readonly RelationsVerifiedCite[] = [
  {
    id: 'daizhige.ziping.论刑冲会合解法',
    title: '《子平真诠评注》·论刑冲会合解法',
    passage:
      '冲者，六冲也，子午卯酉之类是也。会者，三会也，申子辰之类是也。合者，六合也，子与丑合之类是也。此皆以地支宫分而言，系对射之意也。',
    tags: ['六冲', '六合', '三合', '刑'],
  },
  {
    id: 'engine_ref.dizhi_ext04',
    title: '《滴天髓》',
    passage:
      '刑者，三刑寅巳申、丑戌未、子卯自刑辰午酉亥；刑主损伤，刑中亦有生机，须辨喜忌而论。',
    tags: ['刑'],
  },
  {
    id: 'engine_ref.dizhi_ext05',
    title: '《三命通会》',
    passage:
      '害者，子未害、丑午害、寅巳害、卯辰害、申亥害、酉戌害；害则阻碍，逢害宜防人际摩擦。',
    tags: ['害'],
  },
] as const
