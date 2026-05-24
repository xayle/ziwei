import type { PalaceResponse, StarInfo } from '@/api/ziwei'

export type StarLike = string | Partial<StarInfo>
export type FlyingReceivedItem = Record<string, string> | string[]

export const JU_COLORS: Record<number, string> = {
  2: 'var(--wx-water)',
  3: 'var(--wx-wood)',
  4: 'var(--wx-metal)',
  5: 'var(--wx-earth)',
  6: 'var(--wx-fire)',
}

export const BRANCHES = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'] as const
export const ZODIAC_ANIMALS = ['鼠', '牛', '虎', '兔', '龙', '蛇', '马', '羊', '猴', '鸡', '狗', '猪'] as const

export function getStarName(star: StarLike): string {
  return typeof star === 'string' ? star : star.name ?? ''
}

export function getStarTransforms(star: StarLike): string[] {
  if (typeof star === 'string') return []
  return Array.isArray(star.transforms) ? star.transforms : []
}

export function getStarBrightnessValue(star?: Partial<StarInfo>): number {
  return star?.brightness_val ?? 0
}

export function getAuxStars(palace: PalaceResponse): StarLike[] {
  return palace.aux_stars ?? []
}

export function getPalaceTransforms(palace: PalaceResponse): string[] {
  return [
    ...(palace.main_stars ?? []).flatMap((star) => getStarTransforms(star)),
    ...getAuxStars(palace).flatMap((star) => getStarTransforms(star)),
  ]
}

export function getReceivedTransformTexts(item?: FlyingReceivedItem): string[] {
  if (!item) return []
  return Array.isArray(item) ? item : Object.values(item)
}

export function getReceivedTransformLabels(item?: FlyingReceivedItem): string[] {
  if (!item) return []
  if (Array.isArray(item)) return item
  return Object.entries(item).map(([star, transform]) => `${star}${transform.slice(1)}`)
}

export function tfColorStyle(transform: string): Record<string, string> {
  const colors: Record<string, string> = {
    '化禄': '#16a34a',
    '化权': '#dc2626',
    '化科': '#2563eb',
    '化忌': '#7c3aed',
  }
  // 处理 ↓化X 和 ↑化X 自化标譖（去掉方向符号就是标准化X）
  const key = (transform.startsWith('↓') || transform.startsWith('↑'))
    ? transform.slice(1)
    : transform
  return { background: colors[key] ?? '#888', color: '#fff' }
}

export function tfOutlineStyle(transform: string): Record<string, string> {
  const colors: Record<string, string> = {
    '化禄': '#166534',
    '化权': '#991b1b',
    '化科': '#1e40af',
    '化忌': '#5b21b6',
  }
  return { color: colors[transform] ?? '#475569', background: 'transparent' }
}
