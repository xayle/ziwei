import { createCase } from '@/api/report'
import { createSnapshot } from '@/api/snapshots'
import { indexChart } from '@/api/similarity'
import type { ZiweiResponse } from '@/api/ziwei'
import type { ZiweiCaseWorkflowContext, ZiweiCaseWorkflowInput } from './ziweiCaseWorkflowContext'

type SaveZiweiChartOptions = {
  input: ZiweiCaseWorkflowInput
  chart: ZiweiResponse
  existingCaseId?: string | null
  existingCaseName?: string | null
  cityName?: string | null
  longitudeFallback?: number | null
  timezone?: string
  sourceLabel?: string
}

type SaveZiweiChartResult = {
  caseId: string
  caseName: string
  snapshotId: string
}

export function normalizeZiweiCaseGender(value: '男' | '女'): 'male' | 'female' {
  return value === '女' ? 'female' : 'male'
}

export function buildZiweiWorkflowSummary(
  chart: ZiweiResponse | null | undefined,
  input: ZiweiCaseWorkflowInput | null | undefined,
  savedCaseName = '',
): string {
  if (!chart || !input) return savedCaseName || '暂无上下文'
  const parts = [
    chart.birth_solar,
    chart.gender,
    `命宫 ${chart.life_palace_gz}`,
    chart.wuxing_ju_name,
  ]
  if (savedCaseName) parts.push(`案例 ${savedCaseName}`)
  return parts.filter(Boolean).join(' · ')
}

export function buildZiweiCaseName(input: ZiweiCaseWorkflowInput, chart?: ZiweiResponse | null): string {
  const dateText = `${input.year}年${input.month}月${input.day}日 ${input.hour}时${String(input.minute).padStart(2, '0')}分`
  const suffix = chart?.wuxing_ju_name ? ` · ${chart.wuxing_ju_name}` : ''
  return `${dateText} ${input.gender}${suffix}`
}

export function buildZiweiBirthDateLocal(input: ZiweiCaseWorkflowInput): string {
  return `${input.year}-${String(input.month).padStart(2, '0')}-${String(input.day).padStart(2, '0')}T${String(input.hour).padStart(2, '0')}:${String(input.minute).padStart(2, '0')}`
}

export function buildZiweiSimilarityHash(input: ZiweiCaseWorkflowInput, chart: ZiweiResponse | null | undefined): string {
  const reportHash = chart?.report_hash
  if (typeof reportHash === 'string' && reportHash.trim()) {
    return reportHash
  }
  return [
    input.year,
    input.month,
    input.day,
    input.hour,
    input.minute,
    input.gender,
    chart?.life_palace_gz ?? '',
    chart?.wuxing_ju_name ?? '',
  ].join('|')
}

export function buildZiweiSimilarityPatternPayload(chart: ZiweiResponse | null | undefined) {
  return (chart?.patterns || []).map((item) => ({
    name: item.name,
    level: item.level,
    description: item.description ?? '',
  }))
}

export function buildZiweiWorkflowContext(options: {
  input: ZiweiCaseWorkflowInput | null
  chart: ZiweiResponse | null
  savedCaseId?: string | null
  savedCaseName?: string | null
  currentSnapshotId?: string | null
}): ZiweiCaseWorkflowContext {
  const savedCaseName = options.savedCaseName || ''
  return {
    chartInput: options.input,
    chartResult: options.chart,
    savedCaseId: options.savedCaseId || '',
    savedCaseName,
    currentSnapshotId: options.currentSnapshotId || '',
    summary: buildZiweiWorkflowSummary(options.chart, options.input, savedCaseName),
    createdAt: new Date().toISOString(),
  }
}

export async function saveZiweiChartToLibrary(options: SaveZiweiChartOptions): Promise<SaveZiweiChartResult> {
  const {
    input,
    chart,
    existingCaseId,
    existingCaseName,
    cityName,
    longitudeFallback,
    timezone = 'Asia/Shanghai',
    sourceLabel = 'spa-ziwei',
  } = options

  let caseId = existingCaseId || ''
  let caseName = existingCaseName || buildZiweiCaseName(input, chart)

  if (!caseId) {
    const created = await createCase({
      name: caseName,
      birth_dt_local: buildZiweiBirthDateLocal(input),
      tz: timezone,
      lon: input.longitude ?? longitudeFallback ?? 120,
      gender: normalizeZiweiCaseGender(input.gender),
      city: cityName ?? input.city_name ?? null,
      solar_time_enabled: false,
    })
    caseId = created.id
    caseName = created.name
  }

  const snapshot = await createSnapshot(caseId, {
    kind: 'ziwei',
    input_json: input as unknown as Record<string, unknown>,
    output_json: chart as unknown as Record<string, unknown>,
    api_version: chart.algorithm_version || undefined,
    summary_engine_primary: chart.engine_version || undefined,
  })

  try {
    await indexChart({
      chart_hash: buildZiweiSimilarityHash(input, chart),
      birth_solar: chart.birth_solar,
      birth_year: input.year,
      birth_month: input.month,
      birth_day: input.day,
      birth_hour: input.hour,
      gender: input.gender,
      wuxing_ju_name: chart.wuxing_ju_name,
      life_palace_gz: chart.life_palace_gz,
      patterns: buildZiweiSimilarityPatternPayload(chart),
      source_label: sourceLabel,
    })
  } catch {
    // 相似盘索引失败不阻断主流程
  }

  return {
    caseId,
    caseName,
    snapshotId: snapshot.id,
  }
}