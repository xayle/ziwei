/** 落地页 / 无实盘时的示意钩子句（FE-GTM-04 · T096） */

export type LandingHookSnippet = {
  tag: string
  text: string
  layer: 'engine' | 'classical'
}

export const LANDING_HOOK_SNIPPETS: LandingHookSnippet[] = [
  { tag: '事实', text: '日主戊土，正官格透干。', layer: 'engine' },
  { tag: '典籍', text: '官格喜印护身，忌财破印。', layer: 'classical' },
  { tag: '推算', text: '流年冲日支，宜守成减负。', layer: 'engine' },
]

export const LANDING_HOOKS_TITLE = '卷三·运之波' as const

export const LANDING_HOOKS_DISCLAIMER =
  '传统文化与自我认知参考，非命运断言。' as const
