/** 紫微叠宫 / 运限 overlay 工具（对齐 services/ziwei_engine/liunian.py） */
import type { DayunResponse, PalaceResponse, ZiweiResponse } from '@/api/ziwei'

export const BRANCH_CHARS = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'] as const

export const PALACE_NAMES = [
  '命宫', '兄弟宫', '夫妻宫', '子女宫', '财帛宫', '疾厄宫',
  '迁移宫', '交友宫', '官禄宫', '田宅宫', '福德宫', '父母宫',
] as const

export type OverlayLayer = 'natal' | 'dayun' | 'liunian' | 'liuyue' | 'liuri' | 'flying'

export type OverlayOptions = {
  /** 手动选定的大限命宫地支索引（时间轴点击） */
  dayunBranchIdx?: number
  /** 流月序号 1–12，默认当前公历月 */
  liuyueMonth?: number
}

export function branchIdx(branch: string): number {
  const i = BRANCH_CHARS.indexOf(branch as (typeof BRANCH_CHARS)[number])
  return i >= 0 ? i : -1
}

export function overlayPalaceMap(natalLifeBranch: number, flowBranch: number): Record<string, string> {
  const offset = (natalLifeBranch - flowBranch + 12) % 12
  const out: Record<string, string> = {}
  for (let i = 0; i < 12; i++) {
    out[PALACE_NAMES[i]] = PALACE_NAMES[(i + offset) % 12]
  }
  return out
}

export function findDayunForYear(dayun: DayunResponse | undefined, year: number) {
  const items = dayun?.items ?? []
  return items.find((item) => {
    const start = item.start_year ?? 0
    return start <= year && year <= start + 9
  }) ?? items[0]
}

export function dayunBranchIdx(item: { branch_idx?: number; ganzhi?: string }): number {
  if (typeof item.branch_idx === 'number' && item.branch_idx >= 0) return item.branch_idx
  const gz = item.ganzhi || ''
  if (gz.length >= 2) return branchIdx(gz[1])
  return -1
}

export function palaceBranchIdx(palace: PalaceResponse): number {
  return branchIdx(palace.branch)
}

export function findLiuyueForMonth(
  liuyue: ZiweiResponse['liuyue'] | undefined,
  month: number,
) {
  const items = liuyue ?? []
  return items.find((item) => item.month === month) ?? items[Math.max(0, month - 1)]
}

export function buildOverlayBadges(
  result: ZiweiResponse,
  layer: OverlayLayer,
  year: number,
  opts?: OverlayOptions,
): Map<string, string[]> {
  const badges = new Map<string, string[]>()
  const add = (palaceName: string, tag: string) => {
    const list = badges.get(palaceName) ?? []
    if (!list.includes(tag)) list.push(tag)
    badges.set(palaceName, list)
  }

  const natalLife = result.life_palace_branch_idx ?? branchIdx(result.life_palace_gz?.[1] ?? '')

  if (layer === 'dayun' && result.dayun) {
    const dyBr = typeof opts?.dayunBranchIdx === 'number' && opts.dayunBranchIdx >= 0
      ? opts.dayunBranchIdx
      : (() => {
          const dy = findDayunForYear(result.dayun, year)
          return dy ? dayunBranchIdx(dy) : -1
        })()
    const dy = result.dayun.items?.find((item) => dayunBranchIdx(item) === dyBr)
    if (dyBr >= 0) {
      for (const p of result.palaces ?? []) {
        if (palaceBranchIdx(p) === dyBr) add(p.name, `大限命·${dy?.ganzhi ?? ''}`)
        const overlay = overlayPalaceMap(natalLife, dyBr)
        const tag = overlay[p.name]
        if (tag && tag !== p.name.replace('宫', '')) add(p.name, `叠${tag.replace('宫', '')}`)
      }
    }
  }

  if (layer === 'liunian' && result.liunian) {
    const lnBr = result.liunian.life_palace_branch
    for (const p of result.palaces ?? []) {
      if (palaceBranchIdx(p) === lnBr) add(p.name, `流年命·${result.liunian.year_gz}`)
      const overlay = overlayPalaceMap(natalLife, lnBr)
      const tag = overlay[p.name]
      if (tag) add(p.name, `叠${tag.replace('宫', '')}`)
    }
  }

  if (layer === 'liuyue' && result.liuyue?.length) {
    const month = opts?.liuyueMonth ?? new Date().getMonth() + 1
    const ly = findLiuyueForMonth(result.liuyue, month)
    const lyBr = ly?.life_palace_branch ?? -1
    if (lyBr >= 0) {
      for (const p of result.palaces ?? []) {
        if (palaceBranchIdx(p) === lyBr) {
          add(p.name, `流月命·${ly?.month_gz ?? ly?.month_name ?? `${month}月`}`)
        }
        const overlay = overlayPalaceMap(natalLife, lyBr)
        const tag = overlay[p.name]
        if (tag) add(p.name, `叠${tag.replace('宫', '')}`)
      }
    }
  }

  if (layer === 'liuri' && result.liuri_liushi?.liuri) {
    const lr = result.liuri_liushi.liuri
    const lrBr = lr.life_palace_branch ?? branchIdx(lr.branch)
    const label = lr.branch ? `流日·${lr.branch}` : `流日·${lr.lunar_day}日`
    if (lrBr >= 0) {
      for (const p of result.palaces ?? []) {
        if (palaceBranchIdx(p) === lrBr) add(p.name, `${label}命`)
        const overlay = overlayPalaceMap(natalLife, lrBr)
        const tag = overlay[p.name]
        if (tag) add(p.name, `叠${tag.replace('宫', '')}`)
      }
    }
  }

  if (layer === 'flying' && result.flying?.palaces) {
    for (const fp of result.flying.palaces) {
      const outs = Object.entries(fp.flying_out ?? {})
      if (outs.length) {
        add(fp.palace_name, outs.map(([k, v]) => `${k}→${v}`).slice(0, 2).join(' '))
      }
    }
  }

  return badges
}
