import type { LifeVolumeId } from '@/types/life-volume'

export interface BrandHomeVolume {
  id: LifeVolumeId
  num: string
  title: string
  pi: string
  path: string
  requiresReport?: boolean
}

/** 品牌首页六卷批语 — docs/design/FUSHENG-BRAND-COPY-v1.md */
export const BRAND_HOME_VOLUMES: BrandHomeVolume[] = [
  { id: 'vol1', num: '卷一', title: '命之根', pi: '根于阴阳，命之所系', path: '/new/bazi' },
  { id: 'vol2', num: '卷二', title: '业之象', pi: '合冲错综，象而后明', path: '/report#report-volume-vol2', requiresReport: true },
  { id: 'vol3', num: '卷三', title: '运之波', pi: '运如江河，波随岁转', path: '/new/ziwei/timeline' },
  { id: 'vol4', num: '卷四', title: '宫之图', pi: '十二宫阙，界画昭然', path: '/new/ziwei' },
  { id: 'vol5', num: '卷五', title: '事之理', pi: '事有常理，慎而观之', path: '/report#report-volume-vol5', requiresReport: true },
  { id: 'vol6', num: '卷六', title: '问书', pi: '疑则问书，展卷乃见', path: '/report#report-volume-vol6', requiresReport: true },
]

export const BRAND_HOME_OPEN = {
  k: '开卷',
  lines: [
    '六卷命书，如展一幅长卷。',
    '远观其格，近察其运；势理既明，事乃可观。',
  ],
} as const

export const BRAND_HOME_LAYERS = [
  { label: '格物', text: '干支历数，一行一行读去，如刻本之精密。' },
  { label: '引经', text: '子平诸书，有所本而不尽信。' },
  { label: '余论', text: '雾中有花，展卷而后，方入其事。' },
] as const

/** 首页册页底纹 — 左「命」右「书」，合看为命书 */
export const BRAND_HOME_WATERMARK = {
  left: '命',
  right: '书',
} as const

/** 首页左轨竖排诗 — 《录辰》原创 */
export const BRAND_HOME_POEM = [
  '人间行路几春秋',
  '半卷浮生未白头',
  '世事茫茫何所似',
  '且向卷中认春秋',
] as const
