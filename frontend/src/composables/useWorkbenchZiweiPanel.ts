import { computed, ref, type ComputedRef, type Ref } from 'vue'
import type { ZiweiResponse } from '@/api/ziwei'

type ZiweiPalaceLike = {
  name: string
  opposition_name?: string | null
  flying_out?: Record<string, string | null | undefined>
}

type ZiweiDayunLike = {
  index: number
  ganzhi?: string
  start_year?: number
  start_age?: number
  end_age?: number
}

type ZiweiLiuyueLike = {
  month: number
  month_name?: string
  month_gz?: string
  palace_name?: string
  life_palace_branch?: string | number
}

type TrendMeta = {
  text: string
  cls: 'up' | 'down' | 'flat'
}

type ScoreToneClass = 'c-good' | 'c-warn' | 'c-bad' | ''

type ZiweiSummaryCards = {
  lifePalace: string
  bodyPalace: string
  wuxingJu: string
  rulers: string
  dayun: string
  liunian: string
  yearlyScore: number | null
  yearlyTone: ScoreToneClass
  liuyue: string
  liuyuePalace: string
  currentMonthScore: number | null
  liuyueTrend: TrendMeta
  liuyueTone: ScoreToneClass
}

type ZiweiRelationEntry = {
  transform: string
  target: string
}

type ZiweiReceivingEntry = {
  src: string
  transform: string
  target: string | null | undefined
}

type ZiweiRelations = {
  opposite: string
  flyingOutEntries: ZiweiRelationEntry[]
  receiving: ZiweiReceivingEntry[]
}

type ZiweiRelationNodeKind = 'active' | 'opposite' | 'out' | 'in'

type ZiweiRelationNode = {
  id: string
  label: string
  displayLabel: { line1: string; line2: string }
  fullLabel: string
  x: number
  y: number
  kind: ZiweiRelationNodeKind
  palaceName?: string
}

type ZiweiRelationLink = {
  from: string
  to: string
  label: string
  kind: 'opposite' | 'out' | 'in'
  d: string
  labelX: number
  labelY: number
}

type ZiweiRelationGraph = {
  width: number
  height: number
  centerX: number
  centerY: number
  innerRadius: number
  outerRadius: number
  nodes: ZiweiRelationNode[]
  links: ZiweiRelationLink[]
  nodeMap: Record<string, ZiweiRelationNode>
}

type UseWorkbenchZiweiPanelReturn = {
  ziweiPalaces: ComputedRef<ZiweiPalaceLike[]>
  selectedZiweiPalaceName: Ref<string | null>
  selectedZiweiDayunIndex: Ref<number | null>
  selectedZiweiLiuyueMonth: Ref<number | null>
  activeZiweiPalace: ComputedRef<ZiweiPalaceLike | null>
  currentZiweiDayun: ComputedRef<ZiweiDayunLike | null>
  activeZiweiDayun: ComputedRef<ZiweiDayunLike | null>
  currentZiweiLiuyue: ComputedRef<ZiweiLiuyueLike | null>
  activeZiweiLiuyue: ComputedRef<ZiweiLiuyueLike | null>
  ziweiHighlightedPalaceName: ComputedRef<string>
  ziweiSummaryCards: ComputedRef<ZiweiSummaryCards | null>
  activeZiweiDayunSummary: ComputedRef<string>
  activeZiweiLiuyueSummary: ComputedRef<string>
  activeZiweiRelations: ComputedRef<ZiweiRelations | null>
  activeZiweiRelationGraph: ComputedRef<ZiweiRelationGraph | null>
  selectZiweiPalace: (name: string) => void
  selectZiweiDayun: (index: number) => void
  selectZiweiLiuyue: (month: number) => void
}

function trendMeta(diff: number | null | undefined): TrendMeta {
  if (diff == null || Number.isNaN(diff) || diff === 0) return { text: '→ 持平', cls: 'flat' }
  if (diff > 0) return { text: `↑ ${Math.abs(diff).toFixed(0)}`, cls: 'up' }
  return { text: `↓ ${Math.abs(diff).toFixed(0)}`, cls: 'down' }
}

function scoreToneClass(score: number | null | undefined): ScoreToneClass {
  if (score == null || Number.isNaN(score)) return ''
  if (score >= 80) return 'c-good'
  if (score >= 60) return 'c-warn'
  return 'c-bad'
}

export function useWorkbenchZiweiPanel(localZiwei: Ref<ZiweiResponse | null>): UseWorkbenchZiweiPanelReturn {
  const currentYear = new Date().getFullYear()

  const ziweiPalaces = computed<ZiweiPalaceLike[]>(() => localZiwei.value?.palaces ?? [])
  const selectedZiweiPalaceName = ref<string | null>(null)
  const selectedZiweiDayunIndex = ref<number | null>(null)
  const selectedZiweiLiuyueMonth = ref<number | null>(new Date().getMonth() + 1)

  const activeZiweiPalace = computed<ZiweiPalaceLike | null>(() =>
    ziweiPalaces.value.find(palace => palace.name === selectedZiweiPalaceName.value)
    ?? ziweiPalaces.value.find(palace => palace.name.includes('命'))
    ?? ziweiPalaces.value[0]
    ?? null,
  )

  const currentZiweiDayun = computed<ZiweiDayunLike | null>(() => {
    const items = (localZiwei.value?.dayun?.items ?? []) as ZiweiDayunLike[]
    return items.find((item, index) => {
      const nextStartYear = items[index + 1]?.start_year ?? 9999
      return (item.start_year ?? 0) <= currentYear && nextStartYear > currentYear
    }) ?? items[0] ?? null
  })

  const activeZiweiDayun = computed<ZiweiDayunLike | null>(() => {
    const items = (localZiwei.value?.dayun?.items ?? []) as ZiweiDayunLike[]
    return items.find(item => item.index === selectedZiweiDayunIndex.value)
      ?? currentZiweiDayun.value
      ?? items[0]
      ?? null
  })

  const currentZiweiLiuyue = computed<ZiweiLiuyueLike | null>(() => {
    const items = (localZiwei.value?.liuyue ?? []) as ZiweiLiuyueLike[]
    const nowMonth = new Date().getMonth() + 1
    return items.find(item => item.month === nowMonth) ?? items[0] ?? null
  })

  const activeZiweiLiuyue = computed<ZiweiLiuyueLike | null>(() => {
    const items = (localZiwei.value?.liuyue ?? []) as ZiweiLiuyueLike[]
    return items.find(item => item.month === selectedZiweiLiuyueMonth.value)
      ?? currentZiweiLiuyue.value
      ?? items[0]
      ?? null
  })

  const ziweiHighlightedPalaceName = computed<string>(() => activeZiweiLiuyue.value?.palace_name ?? '')

  const ziweiSummaryCards = computed<ZiweiSummaryCards | null>(() => {
    if (!localZiwei.value) return null
    const yearlyScore = localZiwei.value.forecast?.yearly?.score ?? null
    const currentMonthScore = localZiwei.value.forecast?.current_month?.score ?? null
    const monthlyAvg = localZiwei.value.forecast?.monthly?.length
      ? localZiwei.value.forecast.monthly.reduce((sum, item) => sum + item.score, 0) / localZiwei.value.forecast.monthly.length
      : null
    const liuyueTrend = trendMeta(
      currentMonthScore != null && monthlyAvg != null
        ? currentMonthScore - monthlyAvg
        : null,
    )
    return {
      lifePalace: localZiwei.value.life_palace_gz || '—',
      bodyPalace: localZiwei.value.body_palace_gz || '—',
      wuxingJu: `${localZiwei.value.wuxing_ju_name || '—'}${localZiwei.value.wuxing_ju ? ` · ${localZiwei.value.wuxing_ju}局` : ''}`,
      rulers: `${localZiwei.value.life_ruler_star || '—'} / ${localZiwei.value.body_ruler_star || '—'}`,
      dayun: activeZiweiDayun.value ? `${activeZiweiDayun.value.ganzhi} · ${activeZiweiDayun.value.start_age}-${activeZiweiDayun.value.end_age}岁` : '—',
      liunian: localZiwei.value.liunian ? `${localZiwei.value.liunian.year} · ${localZiwei.value.liunian.year_gz}` : '—',
      yearlyScore,
      yearlyTone: scoreToneClass(yearlyScore),
      liuyue: activeZiweiLiuyue.value ? `${activeZiweiLiuyue.value.month_name || `${activeZiweiLiuyue.value.month}月`} · ${activeZiweiLiuyue.value.month_gz}` : '—',
      liuyuePalace: activeZiweiLiuyue.value?.palace_name || '—',
      currentMonthScore,
      liuyueTrend,
      liuyueTone: scoreToneClass(currentMonthScore),
    }
  })

  const activeZiweiDayunSummary = computed<string>(() => (
    activeZiweiDayun.value
      ? `${activeZiweiDayun.value.ganzhi} · ${activeZiweiDayun.value.start_age}-${activeZiweiDayun.value.end_age}岁`
      : ''
  ))

  const activeZiweiLiuyueSummary = computed<string>(() => (
    activeZiweiLiuyue.value
      ? `流月落宫：${activeZiweiLiuyue.value.palace_name} ｜ 宫位：${activeZiweiLiuyue.value.life_palace_branch}`
      : ''
  ))

  const activeZiweiRelations = computed<ZiweiRelations | null>(() => {
    const palace = activeZiweiPalace.value
    if (!palace) return null
    const opposite = palace.opposition_name || '—'
    const flyingOutEntries = Object.entries(palace.flying_out ?? {})
      .filter(([, target]) => !!target)
      .map(([transform, target]) => ({ transform, target: target as string }))
    const receiving = ziweiPalaces.value
      .flatMap(src => Object.entries(src.flying_out ?? {}).map(([transform, target]) => ({ src: src.name, transform, target })))
      .filter(link => link.target === palace.name)
    return {
      opposite,
      flyingOutEntries,
      receiving,
    }
  })

  const activeZiweiRelationGraph = computed<ZiweiRelationGraph | null>(() => {
    const palace = activeZiweiPalace.value
    const relations = activeZiweiRelations.value
    if (!palace || !relations) return null

    const width = 400
    const height = 260
    const centerX = 200
    const centerY = 132
    const innerRadius = 82
    const outerRadius = 118
    const toRad = (deg: number) => (deg * Math.PI) / 180
    const toPoint = (radius: number, angleDeg: number) => ({
      x: centerX + radius * Math.cos(toRad(angleDeg)),
      y: centerY + radius * Math.sin(toRad(angleDeg)),
    })
    const estimateLabelWidth = (label: string) => Math.max(20, label.trim().length * 11)
    const nodeByAngle = <K extends 'opposite' | 'out' | 'in'>(
      id: string,
      label: string,
      kind: K,
      radius: number,
      angleDeg: number,
      palaceName?: string,
    ): { id: string; label: string; x: number; y: number; kind: K; palaceName?: string } => {
      const point = toPoint(radius, angleDeg)
      return { id, label, x: point.x, y: point.y, kind, palaceName }
    }
    const curvePath = (
      from: { x: number; y: number },
      to: { x: number; y: number },
      kind: 'opposite' | 'out' | 'in',
      index: number,
    ) => {
      const midX = (from.x + to.x) / 2
      const midY = (from.y + to.y) / 2
      const dx = to.x - from.x
      const dy = to.y - from.y
      const len = Math.hypot(dx, dy) || 1
      const nx = -dy / len
      const ny = dx / len
      const base = kind === 'opposite' ? 14 : 18
      const jitter = (index % 2 === 0 ? 1 : -1) * (kind === 'opposite' ? 0 : 8)
      const bend = base + jitter
      const cx = midX + nx * bend
      const cy = midY + ny * bend
      return {
        d: `M ${from.x} ${from.y} Q ${cx} ${cy} ${to.x} ${to.y}`,
        labelX: (from.x + to.x + cx) / 3,
        labelY: (from.y + to.y + cy) / 3 - 4,
      }
    }

    const wrapLabel = (label: string, maxLen: number = 8) => {
      if (label.length <= maxLen) return { line1: label, line2: '' }
      const mid = Math.ceil(label.length / 2)
      return { line1: label.substring(0, mid), line2: label.substring(mid) }
    }

    const nodes: ZiweiRelationNode[] = [
      { id: 'active', label: palace.name, displayLabel: wrapLabel(palace.name, 12), fullLabel: palace.name, x: centerX, y: centerY, kind: 'active', palaceName: palace.name },
    ]
    const links: ZiweiRelationLink[] = []

    if (relations.opposite && relations.opposite !== '—') {
      const node = nodeByAngle('opposite', relations.opposite, 'opposite', innerRadius, 180, relations.opposite)
      nodes.push({
        ...node,
        displayLabel: wrapLabel(node.label),
        fullLabel: node.label,
      })
    }

    const relaxVerticalOverlap = (
      group: Array<{ id: string; label: string; x: number; y: number; kind: 'out' | 'in'; palaceName?: string }>,
      side: 'left' | 'right',
    ) => {
      const sorted = [...group].sort((a, b) => a.y - b.y)
      let prevY = -Infinity
      const minY = 30
      const maxY = height - 30
      sorted.forEach((item, index) => {
        const adaptiveGap = 26 + Math.max(0, Math.min(10, (estimateLabelWidth(item.label) - 30) * 0.12))
        const targetY = Math.max(item.y, prevY + adaptiveGap)
        item.y = Math.min(maxY, targetY)
        prevY = item.y
        const drift = (index - (sorted.length - 1) / 2) * 3
        if (side === 'right') item.x += drift
        else item.x -= drift
      })
      sorted
        .slice()
        .reverse()
        .forEach((item, index) => {
          item.y = Math.max(minY, Math.min(item.y, maxY - index * 4))
        })
      return sorted
    }

    const outAngles = [-58, -20, 18, 56]
    const outNodes: Array<{ id: string; label: string; x: number; y: number; kind: 'out'; palaceName?: string }> = []
    relations.flyingOutEntries.slice(0, 4).forEach((item, index) => {
      const id = `out-${index}`
      const widthBoost = Math.min(18, Math.max(0, (estimateLabelWidth(item.target) - 28) * 0.45))
      const angleNudge = item.target.length >= 4 ? (index % 2 === 0 ? -4 : 4) : 0
      outNodes.push(nodeByAngle(id, item.target, 'out', outerRadius + widthBoost, (outAngles[index] ?? 56) + angleNudge, item.target))
    })
    nodes.push(
      ...relaxVerticalOverlap(outNodes, 'right').map(node => ({
        ...node,
        displayLabel: wrapLabel(node.label),
        fullLabel: node.label,
      })),
    )

    const inAngles = [128, 162, 202, 236]
    const inNodes: Array<{ id: string; label: string; x: number; y: number; kind: 'in'; palaceName?: string }> = []
    relations.receiving.slice(0, 4).forEach((item, index) => {
      const id = `in-${index}`
      const widthBoost = Math.min(18, Math.max(0, (estimateLabelWidth(item.src) - 28) * 0.45))
      const angleNudge = item.src.length >= 4 ? (index % 2 === 0 ? -4 : 4) : 0
      inNodes.push(nodeByAngle(id, item.src, 'in', outerRadius + widthBoost, (inAngles[index] ?? 236) + angleNudge, item.src))
    })
    nodes.push(
      ...relaxVerticalOverlap(inNodes, 'left').map(node => ({
        ...node,
        displayLabel: wrapLabel(node.label),
        fullLabel: node.label,
      })),
    )

    const nodeMap = Object.fromEntries(nodes.map(node => [node.id, node])) as Record<string, ZiweiRelationNode>
    if (nodeMap.opposite) {
      const curve = curvePath(nodeMap.active, nodeMap.opposite, 'opposite', 0)
      links.push({ from: 'active', to: 'opposite', label: '对宫', kind: 'opposite', ...curve })
    }
    relations.flyingOutEntries.slice(0, 4).forEach((item, index) => {
      const id = `out-${index}`
      if (!nodeMap[id]) return
      const curve = curvePath(nodeMap.active, nodeMap[id], 'out', index)
      links.push({ from: 'active', to: id, label: item.transform, kind: 'out', ...curve })
    })
    relations.receiving.slice(0, 4).forEach((item, index) => {
      const id = `in-${index}`
      if (!nodeMap[id]) return
      const curve = curvePath(nodeMap[id], nodeMap.active, 'in', index)
      links.push({ from: id, to: 'active', label: item.transform, kind: 'in', ...curve })
    })

    return { width, height, centerX, centerY, innerRadius, outerRadius, nodes, links, nodeMap }
  })

  function selectZiweiPalace(name: string) {
    selectedZiweiPalaceName.value = name
  }

  function selectZiweiDayun(index: number) {
    selectedZiweiDayunIndex.value = index
  }

  function selectZiweiLiuyue(month: number) {
    selectedZiweiLiuyueMonth.value = month
    const palaceName = ((localZiwei.value?.liuyue ?? []) as ZiweiLiuyueLike[]).find(item => item.month === month)?.palace_name
    if (palaceName) selectedZiweiPalaceName.value = palaceName
  }

  return {
    ziweiPalaces,
    selectedZiweiPalaceName,
    selectedZiweiDayunIndex,
    selectedZiweiLiuyueMonth,
    activeZiweiPalace,
    currentZiweiDayun,
    activeZiweiDayun,
    currentZiweiLiuyue,
    activeZiweiLiuyue,
    ziweiHighlightedPalaceName,
    ziweiSummaryCards,
    activeZiweiDayunSummary,
    activeZiweiLiuyueSummary,
    activeZiweiRelations,
    activeZiweiRelationGraph,
    selectZiweiPalace,
    selectZiweiDayun,
    selectZiweiLiuyue,
  }
}
