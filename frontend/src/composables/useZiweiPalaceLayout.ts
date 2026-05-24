import { computed } from 'vue'
import type { DayunItem, PalaceResponse, ZiweiResponse } from '@/api/ziwei'

const GRID_ORDER_BRANCHES = [5, 6, 7, 8, 4, -1, -1, 9, 3, -1, -1, 10, 2, 1, 0, 11] as const
const BRANCH_CHARS = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'] as const
const BRANCH_TO_GRID: Record<number, [number, number]> = {
  5: [0, 0], 6: [1, 0], 7: [2, 0], 8: [3, 0],
  4: [0, 1], 9: [3, 1],
  3: [0, 2], 10: [3, 2],
  2: [0, 3], 1: [1, 3], 0: [2, 3], 11: [3, 3],
}

export const SIHUA_COLORS: Record<string, { color: string; label: string }> = {
  '化禄': { color: '#22c55e', label: 'A' },
  '化权': { color: '#f97316', label: 'B' },
  '化科': { color: '#3b82f6', label: 'C' },
  '化忌': { color: '#ef4444', label: 'D' },
}

type PalaceGridCell = {
  empty: boolean
  pos: number
  palace?: PalaceResponse
}

type SihuaLine = {
  fromBranchIdx: number
  toBranchIdx: number
  starName: string
  transform: string
  color: string
  label: string
  isSelfHua: boolean
}

type UseZiweiPalaceLayoutOptions = {
  getResult: () => ZiweiResponse | null
  getSelectedPalace: () => PalaceResponse | null
  isSihuaLinesVisible: () => boolean
}

export function useZiweiPalaceLayout(options: UseZiweiPalaceLayoutOptions) {
  const palaceGrid = computed(() => {
    const result = options.getResult()
    if (!result?.palaces) return [] as PalaceGridCell[]

    const branchToPalace = new Map<number, PalaceResponse>()
    for (const palace of result.palaces) {
      const branchIdx = BRANCH_CHARS.indexOf(palace.branch as (typeof BRANCH_CHARS)[number])
      if (branchIdx >= 0) branchToPalace.set(branchIdx, palace)
    }

    let centerAdded = false
    return GRID_ORDER_BRANCHES.map((branchIdx, pos) => {
      if (branchIdx === -1) {
        if (centerAdded) return null
        centerAdded = true
        return { empty: true, pos }
      }
      return { empty: false, pos, palace: branchToPalace.get(branchIdx) }
    }).filter(Boolean) as PalaceGridCell[]
  })

  const palaceDayunMap = computed(() => {
    const result = options.getResult()
    if (!result?.dayun?.items || !result.palaces) return {} as Record<number, DayunItem>

    const mapping: Record<number, DayunItem> = {}
    result.dayun.items.forEach((item) => {
      const palaceIdx = result.palaces.findIndex((palace) => (palace.stem + palace.branch) === item.ganzhi)
      if (palaceIdx >= 0) mapping[palaceIdx] = item
    })
    return mapping
  })

  const sihuaLines = computed((): SihuaLine[] => {
    const result = options.getResult()
    if (!result?.palaces || !options.isSihuaLinesVisible()) return []

    const selectedPalace = options.getSelectedPalace()
    if (!selectedPalace) return []

    const fromBranchIdx = BRANCH_CHARS.indexOf(selectedPalace.branch as (typeof BRANCH_CHARS)[number])
    if (fromBranchIdx < 0 || !selectedPalace.flying_out) return []

    const lines: SihuaLine[] = []
    Object.entries(selectedPalace.flying_out).forEach(([starName, transform]) => {
      const config = SIHUA_COLORS[transform]
      if (!config) return

      const targetPalace = result.palaces.find((palace) =>
        palace.main_stars.some((star) => star.name === starName) || palace.aux_stars.some(s => s.name === starName),
      )
      if (!targetPalace) return

      const toBranchIdx = BRANCH_CHARS.indexOf(targetPalace.branch as (typeof BRANCH_CHARS)[number])
      if (toBranchIdx < 0) return

      lines.push({
        fromBranchIdx,
        toBranchIdx,
        starName,
        transform,
        color: config.color,
        label: config.label,
        isSelfHua: fromBranchIdx === toBranchIdx,
      })
    })

    return lines
  })

  function getPalaceCenter(branchIdx: number): { x: number; y: number } {
    const grid = BRANCH_TO_GRID[branchIdx]
    if (!grid) return { x: 50, y: 50 }
    const [col, row] = grid
    return {
      x: col * 25 + 12.5,
      y: row * 25 + 12.5,
    }
  }

  function getPalaceEdge(fromIdx: number, toIdx: number): { x: number; y: number } {
    const from = getPalaceCenter(fromIdx)
    const to = getPalaceCenter(toIdx)
    const dx = to.x - from.x
    const dy = to.y - from.y
    const length = Math.sqrt(dx * dx + dy * dy)
    if (length === 0) return from

    const offset = 8
    return {
      x: from.x + (dx / length) * offset,
      y: from.y + (dy / length) * offset,
    }
  }

  function getCurvedPath(fromIdx: number, toIdx: number, curveOffset: number = 0.15): string {
    const fromEdge = getPalaceEdge(fromIdx, toIdx)
    const toEdge = getPalaceEdge(toIdx, fromIdx)
    const midX = (fromEdge.x + toEdge.x) / 2
    const midY = (fromEdge.y + toEdge.y) / 2
    const dx = toEdge.x - fromEdge.x
    const dy = toEdge.y - fromEdge.y
    const length = Math.sqrt(dx * dx + dy * dy)
    if (length === 0) return `M ${fromEdge.x} ${fromEdge.y}`

    const ctrlX = midX + (-dy / length) * length * curveOffset
    const ctrlY = midY + (dx / length) * length * curveOffset
    return `M ${fromEdge.x} ${fromEdge.y} Q ${ctrlX} ${ctrlY} ${toEdge.x} ${toEdge.y}`
  }

  function getCurvedMidpoint(fromIdx: number, toIdx: number, curveOffset: number = 0.15): { x: number; y: number } {
    const fromEdge = getPalaceEdge(fromIdx, toIdx)
    const toEdge = getPalaceEdge(toIdx, fromIdx)
    const midX = (fromEdge.x + toEdge.x) / 2
    const midY = (fromEdge.y + toEdge.y) / 2
    const dx = toEdge.x - fromEdge.x
    const dy = toEdge.y - fromEdge.y
    const length = Math.sqrt(dx * dx + dy * dy)
    if (length === 0) return { x: midX, y: midY }

    return {
      x: midX + (-dy / length) * length * curveOffset * 0.5,
      y: midY + (dx / length) * length * curveOffset * 0.5,
    }
  }

  return {
    palaceGrid,
    palaceDayunMap,
    SIHUA_COLORS,
    sihuaLines,
    getPalaceCenter,
    getCurvedPath,
    getCurvedMidpoint,
  }
}
