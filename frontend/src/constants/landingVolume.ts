/** 抖音落地页文案（FE-GTM-01 / T091）— 卷首试读，不接实盘 */

export const LANDING_BRAND = '浮生' as const

export const LANDING_TAGLINE = '人生六卷 · 命书可读' as const

export const LANDING_HEADLINE = '先读卷首：如何展开这本命书' as const

export const LANDING_LEAD =
  '从格局与干支入手，再看流年起伏。免费建档后，卷一·二可先展阅。' as const

/** 卷首摘要段落（试读占位；实盘后走 life/volumes） */
export const LANDING_PREFACE_PARAS = [
  '开卷先看读法：事实一层、典籍一层、余论一层，勿混为一谈。',
  '卷一记命之根——日主与格局；卷二记业之象——合冲刑害。',
  '卷三以后述运势波澜，须权益解锁后方可通读全文。',
] as const

export const LANDING_CTA = '免费建档 · 录入生辰' as const

export const LANDING_DISCLAIMER =
  '本站内容仅供传统文化研究与自我对照，不构成任何决策建议，勿以「改命」相称。' as const

export const LANDING_VOL_TEASERS = [
  { id: 'vol1', label: '卷一·命之根', note: '免费试读' },
  { id: 'vol2', label: '卷二·业之象', note: '免费试读' },
  { id: 'vol3', label: '卷三·运之波', note: '读卷 Pass' },
] as const
