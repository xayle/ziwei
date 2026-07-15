import type { BaziResponse, LiuriLiushiModel, ResponseProvenance } from '@/api/bazi'
import type { ZiweiResponse } from '@/api/ziwei'
import { mapProvenanceLayerToTrustLabel } from '@/utils/feBeAdapter'

export type { ResponseProvenance, ProvenanceLayer } from '@/api/bazi'
export type ProvenanceRow = {
  domain: string
  layer: string
  confidence?: number
  note?: string
}

export type DualTrackRow = {
  id: string
  recorded: string
  engine: string
  note?: string
}

export type PillarDetailRow = {
  pillar: string
  kongwang: string
  shensha: string
  hidden: string
}

export type PalaceStructuredRow = {
  name: string
  conclusion: string
  explanation: string
  suggestion: string
  tags: string[]
}

const MISSING_FIELD_LABELS: Record<string, string> = {
  clash_summary: '刑冲摘要',
  combine_summary: '合化摘要',
  harm_summary: '害破摘要',
  hour_pillar: '时柱',
  geju_detail: '格局细目',
  flow_score: '流日联动分',
  palace_stems_partial: '宫干部分缺失',
  palace_ten_gods: '宫位十神',
  youbi_month_vs_iztro_hour: '右弼 month/hour 口径差',
  forecast: '运限预测',
}

/** 产品刻意标 advisory 的字段：展示为对照说明，避免「引擎坏了」观感。 */
const ADVISORY_MISSING_FIELDS = new Set([
  'palace_ten_gods',
  'youbi_month_vs_iztro_hour',
  'palace_stems_partial',
])

export function formatMissingFieldLabel(field: string): string {
  const trimmed = field.trim()
  if (!trimmed) return field
  return MISSING_FIELD_LABELS[trimmed] ?? trimmed.replace(/_/g, ' ')
}

export function isAdvisoryMissingField(field: string): boolean {
  return ADVISORY_MISSING_FIELDS.has(field.trim())
}

export type TrustDisplayLine = {
  kind: 'missing' | 'validation' | 'cross'
  main: string
  note?: string
  tone: 'ok' | 'drift' | 'missing'
}

export function formatMissingFieldLine(field: string): TrustDisplayLine {
  const label = formatMissingFieldLabel(field)
  if (isAdvisoryMissingField(field)) {
    return {
      kind: 'missing',
      main: `${label}（对照口径 · 非故障）`,
      note: '产品主盘为 canonical；此项仅提示与对照轨可能不一致或未宣称。',
      tone: 'drift',
    }
  }
  return {
    kind: 'missing',
    main: `${label}（引擎未返回）`,
    tone: 'missing',
  }
}

const CONFIDENCE_LEVEL_LABELS: Record<string, string> = {
  high: '高',
  medium: '中等',
  low: '低',
}

const VALIDATION_MODE_LABELS: Record<string, string> = {
  dual: '双轨',
  single: '单轨',
}

const VALIDATION_REASON_LABELS: Record<string, string> = {
  near_shichen_boundary: '接近时辰交界',
  near_jieqi_boundary: '接近节气交界',
  near_boundary: '接近历法边界',
  dual: '双轨口径并存',
  dual_track: '双轨口径并存',
  hour_unknown: '时辰精度未知',
  birth_time_unknown: '出生时刻未知',
  boundary_risk: '边界解读风险',
}

function humanizeValidationToken(token: string): string {
  const trimmed = token.trim()
  if (!trimmed) return token
  return VALIDATION_REASON_LABELS[trimmed] ?? trimmed.replace(/_/g, ' ')
}

export function formatConfidenceLevel(level?: string | null): string {
  if (!level) return '—'
  return CONFIDENCE_LEVEL_LABELS[level] ?? level
}

export function formatTrustValidationLine(line: string): TrustDisplayLine {
  const trimmed = line.trim()
  if (/near_shichen|近时辰边界/i.test(trimmed)) {
    const minutes = trimmed.match(/（(\d+)\s*分钟）/)?.[1]
    const suffix = minutes ? `（±${minutes} 分）` : '（±15 分）'
    return { kind: 'validation', main: `出生时刻接近时辰交界${suffix}`, note: trimmed, tone: 'drift' }
  }
  if (/near_jieqi|近节气边界/i.test(trimmed)) {
    return { kind: 'validation', main: '出生时刻接近节气交界', note: trimmed, tone: 'drift' }
  }
  if (/置信度.*medium|置信度：\s*medium/i.test(trimmed)) {
    return { kind: 'validation', main: '整体置信度：中等', note: trimmed, tone: 'ok' }
  }
  if (/置信度.*中等|置信度：\s*中等/.test(trimmed)) {
    return { kind: 'validation', main: '整体置信度：中等', tone: 'ok' }
  }
  if (/置信度.*high|置信度：\s*high/i.test(trimmed)) {
    return { kind: 'validation', main: '整体置信度：高', note: trimmed, tone: 'ok' }
  }
  if (/置信度.*low|置信度：\s*low/i.test(trimmed)) {
    return { kind: 'validation', main: '整体置信度：低', note: trimmed, tone: 'drift' }
  }
  if (/模式\s*dual|模式 dual/i.test(trimmed)) {
    return { kind: 'validation', main: '校验模式：双轨', note: trimmed, tone: 'ok' }
  }
  if (/near_shichen_boundary/i.test(trimmed)) {
    return { kind: 'validation', main: '接近时辰交界', tone: 'drift' }
  }
  if (/near_jieqi_boundary/i.test(trimmed)) {
    return { kind: 'validation', main: '接近节气交界', tone: 'drift' }
  }
  if (/^near_boundary$/i.test(trimmed)) {
    return { kind: 'validation', main: '接近历法边界', tone: 'drift' }
  }
  if (/双轨差异|diff_fields/i.test(trimmed)) {
    return { kind: 'validation', main: '存在双轨口径差异', note: trimmed, tone: 'drift' }
  }
  if (/边界风险|boundary_risk/i.test(trimmed)) {
    return { kind: 'validation', main: '时辰或节气边界存在解读风险', note: trimmed, tone: 'drift' }
  }
  if (/^L0\b|校验层级\s*L0/i.test(trimmed)) {
    return { kind: 'validation', main: '引擎校验层级较低', note: trimmed, tone: 'drift' }
  }
  return { kind: 'validation', main: trimmed, tone: trustLineTone(trimmed) }
}

export function buildTrustOverviewLines(
  missingFields: string[],
  validationLines: string[],
  options?: { max?: number; crossLines?: TrustDisplayLine[] },
): TrustDisplayLine[] {
  const max = options?.max ?? 2
  const cross = options?.crossLines ?? []
  const items: TrustDisplayLine[] = [
    ...cross,
    ...missingFields.map(formatMissingFieldLine),
    ...validationLines.map(formatTrustValidationLine),
  ]
  return items.slice(0, max)
}

export function countTrustOverviewItems(
  missingFields: string[],
  validationLines: string[],
  crossCount = 0,
): number {
  return crossCount + missingFields.length + validationLines.length
}

export function trustLineTone(line: string): 'ok' | 'drift' | 'missing' {
  if (/缺失|missing|不可用|未覆盖/i.test(line)) return 'missing'
  if (/双轨|边界|near_shichen|风险|warn|drift/i.test(line)) return 'drift'
  return 'ok'
}

const PROVENANCE_DOMAIN_LABELS: Record<string, string> = {
  pillars: '四柱',
  geju: '格局',
  yongshen: '用神',
  dayun: '大运',
  narrative: '叙事',
  analysis: '分析',
  scoring: '评分',
  forecast: '运限',
  compatibility: '合盘',
  patterns: '格局检测',
  stars: '安星',
}


function provenanceLayerLabel(layer?: string | null): string {
  return mapProvenanceLayerToTrustLabel(layer)
}

function uniqueStrings(values: Array<string | null | undefined>): string[] {
  return [...new Set(values.map((v) => v?.trim()).filter((v): v is string => !!v))]
}

export function collectMissingFields(
  bazi?: BaziResponse | null,
  ziwei?: ZiweiResponse | null,
): { bazi: string[]; ziwei: string[]; merged: string[] } {
  const baziFields = uniqueStrings([
    ...(bazi?.missing_fields ?? []),
    ...(bazi?.liuri_liushi?.missing_fields ?? []),
  ])
  const ziweiFields = uniqueStrings(ziwei?.missing_fields ?? [])
  return {
    bazi: baziFields,
    ziwei: ziweiFields,
    merged: uniqueStrings([...baziFields, ...ziweiFields]),
  }
}

export function buildProvenanceRows(
  baziProv?: ResponseProvenance | null,
  ziweiProv?: ResponseProvenance | null,
): ProvenanceRow[] {
  const rows: ProvenanceRow[] = []
  const append = (source: '八字' | '紫微', provenance: ResponseProvenance) => {
    for (const [key, layer] of Object.entries(provenance)) {
      if (!layer?.layer) continue
      rows.push({
        domain: `${source}·${PROVENANCE_DOMAIN_LABELS[key] ?? key}`,
        layer: provenanceLayerLabel(layer.layer),
        confidence: layer.confidence,
        note: layer.note ?? layer.method_registry_id ?? undefined,
      })
    }
  }
  if (baziProv) append('八字', baziProv)
  if (ziweiProv) append('紫微', ziweiProv)
  return rows
}

export type YongshenDualTrackRow = {
  id: string
  recorded: string
  engine: string
  note?: string
}

const WX_LABEL: Record<string, string> = {
  wood: '木', fire: '火', earth: '土', metal: '金', water: '水',
}

function formatWxList(values?: string[]) {
  return (values ?? []).map((v) => WX_LABEL[v] ?? v).join('、') || '—'
}

export function buildYongshenDualTrackRows(bazi?: BaziResponse | null): YongshenDualTrackRow[] {
  const y = bazi?.yongshen
  if (!y?.dual_track_id && !(y?.recorded_favor?.length)) return []
  return [{
    id: y.dual_track_id || '用神双轨',
    recorded: formatWxList(y.recorded_favor),
    engine: formatWxList(y.engine_favor?.length ? y.engine_favor : y.favor),
    note: y.dual_track_note || undefined,
  }]
}

export function buildDualTrackRows(bazi?: BaziResponse | null): DualTrackRow[] {
  const g = bazi?.geju
  if (!g?.recorded_geju && !g?.dual_track_id) return []
  return [{
    id: g.dual_track_id || '双轨',
    recorded: g.recorded_geju || '—',
    engine: g.engine_geju || g.geju_name || '—',
    note: g.dual_track_note || undefined,
  }]
}

export function buildLiuriSummary(liuri?: LiuriLiushiModel | null) {
  if (!liuri?.day_ganzhi) return null
  const scoreParts = [
    liuri.flow_score_dayun != null ? `大运 ${liuri.flow_score_dayun}` : '',
    liuri.flow_score_liunian != null ? `流年 ${liuri.flow_score_liunian}` : '',
    liuri.flow_score_geju != null ? `格局 ${liuri.flow_score_geju}` : '',
  ].filter(Boolean)
  const composite = liuri.flow_score != null
    ? String(liuri.flow_score)
    : scoreParts.length
      ? scoreParts.join(' / ')
      : undefined
  return {
    date: liuri.date,
    day: `${liuri.day_ganzhi}${liuri.day_ten_god ? `（${liuri.day_ten_god}）` : ''}`,
    hour: `${liuri.hour_ganzhi}${liuri.hour_label ? ` · ${liuri.hour_label}` : ''}${liuri.hour_ten_god ? `（${liuri.hour_ten_god}）` : ''}`,
    flow: liuri.flow_summary || liuri.flow_tone || '—',
    links: [
      liuri.current_dayun_ganzhi ? `大运 ${liuri.current_dayun_ganzhi}` : '',
      liuri.current_liunian_ganzhi ? `流年 ${liuri.current_liunian_ganzhi}` : '',
      liuri.dayun_link || '',
      liuri.liunian_link || '',
      liuri.transition_hint || '',
      ...(liuri.warnings ?? []),
    ].filter(Boolean),
    score: composite,
    flowScoreDayun: liuri.flow_score_dayun,
    flowScoreLiunian: liuri.flow_score_liunian,
    flowScoreGeju: liuri.flow_score_geju,
    transitionHint: liuri.transition_hint,
    warnings: liuri.warnings ?? [],
  }
}

export function buildStrengthFactorLines(bazi?: BaziResponse | null): string[] {
  const factors = bazi?.day_master_strength?.strength_factors
    ?? bazi?.day_master_strength?.factors
    ?? []
  if (!factors.length) return []
  return factors.map((f) => {
    const weight = f.weight != null ? `权重 ${Math.round(f.weight * 100)}%` : ''
    const ws = f.weighted_score != null ? `加权 ${f.weighted_score.toFixed(1)}` : `分 ${f.score}`
    const reason = f.reason ? ` — ${f.reason}` : ''
    return `${f.name}：${ws}${weight ? `（${weight}）` : ''}${reason}`
  })
}

export function buildPillarDetailRows(bazi?: BaziResponse | null): PillarDetailRow[] {
  const details = bazi?.pillar_details
  if (!details) return []
  const order: Array<keyof typeof details> = ['year', 'month', 'day', 'hour']
  const labels: Record<string, string> = { year: '年', month: '月', day: '日', hour: '时' }
  return order.map((key) => {
    const item = details[key]
    if (!item) return null
    const hidden = (item.hidden_stems ?? [])
      .map((h) => `${h.stem || ''}${h.ten_god ? `(${h.ten_god})` : ''}`.trim())
      .filter(Boolean)
      .join('、') || '—'
    const shensha = (item.shensha ?? []).map((s) => s.name).filter(Boolean).join('、') || '—'
    return {
      pillar: labels[key] ?? key,
      kongwang: (item.kongwang ?? []).join('、') || (bazi?.kongwang?.length ? bazi.kongwang.join('、') : '—'),
      shensha,
      hidden,
    }
  }).filter((row): row is PillarDetailRow => !!row)
}

export function formatRelationLines(bazi?: BaziResponse | null): string[] {
  const lines: string[] = []
  for (const rel of bazi?.dizhi_relations ?? []) {
    if (!rel || typeof rel !== 'object') continue
    const type = String((rel as Record<string, unknown>).type ?? (rel as Record<string, unknown>).relation ?? '')
    const branches = String((rel as Record<string, unknown>).branches ?? (rel as Record<string, unknown>).pair ?? '')
    const note = String((rel as Record<string, unknown>).note ?? (rel as Record<string, unknown>).desc ?? '')
    const text = [type, branches, note].filter(Boolean).join(' · ')
    if (text) lines.push(text)
  }
  for (const clash of bazi?.tiangan_clashes ?? []) {
    if (!clash || typeof clash !== 'object') continue
    const stems = String((clash as Record<string, unknown>).stems ?? (clash as Record<string, unknown>).pair ?? '')
    const note = String((clash as Record<string, unknown>).note ?? (clash as Record<string, unknown>).type ?? '天干冲')
    if (stems || note) lines.push([note, stems].filter(Boolean).join(' · '))
  }
  const globalShensha = (bazi?.shensha ?? []).map((s) => s.name).filter(Boolean)
  if (globalShensha.length) lines.push(`命局神煞：${globalShensha.join('、')}`)
  return lines
}

function flattenObjectLines(obj: Record<string, unknown> | undefined, prefix = ''): string[] {
  if (!obj) return []
  const lines: string[] = []
  for (const [key, value] of Object.entries(obj)) {
    if (value == null || value === '') continue
    const label = prefix ? `${prefix}.${key}` : key
    if (typeof value === 'object' && !Array.isArray(value)) {
      lines.push(...flattenObjectLines(value as Record<string, unknown>, label))
    } else if (Array.isArray(value)) {
      const text = value.map(String).join('、')
      if (text) lines.push(`${label}：${text}`)
    } else {
      lines.push(`${label}：${String(value)}`)
    }
  }
  return lines.slice(0, 8)
}

export function buildBaziStructuralLines(bazi?: BaziResponse | null): string[] {
  const summary = bazi?.bazi_structural_summary as Record<string, unknown> | undefined
  if (!summary) return []
  return [
    ...flattenObjectLines(summary.core_snapshot as Record<string, unknown> | undefined, '核心'),
    ...flattenObjectLines(summary.relation_summary as Record<string, unknown> | undefined, '关系'),
    ...flattenObjectLines(summary.report_summary as Record<string, unknown> | undefined, '报告'),
  ].slice(0, 10)
}

export function buildZiweiStructuralLines(ziwei?: ZiweiResponse | null): string[] {
  const summary = ziwei?.ziwei_structural_summary ?? ziwei?.structural_summary
  if (!summary) return []
  const lines: string[] = []
  if (summary.core_snapshot) {
    const cs = summary.core_snapshot
    lines.push(`命宫 ${cs.life_palace_gz ?? '—'} · 身宫 ${cs.body_palace_gz ?? '—'} · ${cs.wuxing_ju_name ?? ''}`)
  }
  if (summary.pattern_summary?.headline) lines.push(summary.pattern_summary.headline)
  if (summary.report_summary?.headline) lines.push(summary.report_summary.headline)
  return lines.filter(Boolean).slice(0, 8)
}

export function buildPalaceStructuredRows(ziwei?: ZiweiResponse | null): PalaceStructuredRow[] {
  const structured = ziwei?.analysis_structured ?? []
  if (structured.length) {
    return structured.map((item) => ({
      name: item.palace_name,
      conclusion: item.conclusion || '—',
      explanation: item.explanation || '',
      suggestion: item.suggestion || '',
      tags: item.analysis_tags ?? [],
    }))
  }
  return (ziwei?.palaces ?? []).map((p) => ({
    name: p.name,
    conclusion: p.conclusion || p.analysis || '—',
    explanation: p.explanation || '',
    suggestion: p.suggestion || '',
    tags: p.analysis_tags ?? [],
  }))
}

export type IztroDualTrackDisplay = {
  label: string
  yearDivide: string
  dayDivide: string
  lifePalaceGz: string
  mainMatch: string
  note?: string
}

export type IztroDisplay = {
  status: string
  mainMatch: string
  lifePalace?: string
  message: string
  engineLifePalaceGz?: string
  iztroLifePalaceGz?: string
  engineTrack?: { yearDivide: string; dayDivide: string }
  dualTrack?: IztroDualTrackDisplay | null
  showDualTrackTable: boolean
}

export function buildValidationLines(bazi?: BaziResponse | null): string[] {
  const lines: string[] = []
  const v = bazi?.validation
  const rf = bazi?.risk_flags ?? v?.risk_flags
  if (bazi?.confidence_level) {
    const score = bazi.confidence_score != null ? `（${bazi.confidence_score}）` : ''
    lines.push(`置信度：${formatConfidenceLevel(bazi.confidence_level)}${score}`)
  }
  if (v?.level) {
    const modeLabel = VALIDATION_MODE_LABELS[v.mode ?? ''] ?? v.mode ?? '—'
    lines.push(`校验层级 ${v.level} · 模式 ${modeLabel} · 解读${v.interpretation_enabled ? '允许' : '受限'}`)
  }
  if (v?.reasons?.length) {
    lines.push(`原因：${v.reasons.map(humanizeValidationToken).join('、')}`)
  }
  if (v?.diff_fields?.length) lines.push(`双轨差异柱：${v.diff_fields.join('、')}`)
  if (rf?.near_shichen_boundary) {
    lines.push(`近时辰边界${rf.minutes_to_shichen_boundary != null ? `（${rf.minutes_to_shichen_boundary} 分钟）` : ''}`)
  }
  if (rf?.near_jieqi_boundary) {
    lines.push(`近节气边界${rf.minutes_to_jieqi_boundary != null ? `（${rf.minutes_to_jieqi_boundary} 分钟）` : ''}`)
  }
  if (v?.boundary_risk_shichen) lines.push('时辰边界风险：可能阻断解读')
  if (v?.boundary_risk_jieqi) lines.push('节气边界风险：可能阻断解读')
  return lines
}

export function buildIztroDisplay(
  ziwei?: ZiweiResponse | null,
  profile?: { yearDivide?: string; dayDivide?: string } | null,
): IztroDisplay | null {
  const cc = ziwei?.iztro_crosscheck
  if (!cc) return null

  const yearDivide = profile?.yearDivide ?? 'lichun'
  const dayDivide = profile?.dayDivide ?? 'solar_next'
  const yearLabel = formatYearDivideLabel(yearDivide)
  const dayLabel = formatDayDivideLabel(dayDivide)

  const dual = cc.dual_track
  const showDualTrackTable = cc.status === 'life_palace_mismatch'
    || Boolean(dual)
    || (cc.life_palace_match === false && cc.engine_life_palace_gz && cc.iztro_life_palace_gz)

  return {
    status: cc.status || 'unknown',
    mainMatch: `${cc.main_match ?? '—'}/${cc.main_total ?? '—'}`,
    lifePalace: cc.life_palace_match != null
      ? (cc.life_palace_match ? '命宫一致' : '命宫不一致')
      : undefined,
    message: cc.advisory || `交叉核验状态：${cc.status || '已完成'}`,
    engineLifePalaceGz: cc.engine_life_palace_gz ?? ziwei?.life_palace_gz ?? undefined,
    iztroLifePalaceGz: cc.iztro_life_palace_gz ?? undefined,
    engineTrack: { yearDivide: yearLabel, dayDivide: dayLabel },
    dualTrack: dual
      ? {
          label: dual.label || 'iztro 对照轨',
          yearDivide: formatYearDivideLabel(dual.year_divide),
          dayDivide: formatDayDivideLabel(dual.day_divide),
          lifePalaceGz: dual.life_palace_gz || '—',
          mainMatch: `${dual.main_match ?? '—'}/${dual.main_total ?? '—'}`,
          note: dual.note ?? undefined,
        }
      : null,
    showDualTrackTable,
  }
}

function formatYearDivideLabel(value?: string | null): string {
  if (value === 'normal') return '正月初一换年'
  if (!value || value === 'lichun') return '立春换年'
  return value
}

function formatDayDivideLabel(value?: string | null): string {
  if (value === 'forward') return '农历日+1安星'
  if (value === 'current') return '当日不换日'
  if (!value || value === 'solar_next') return '公历次日换日'
  return value
}

export type DualTrackReferenceRow = {
  id: string
  topic: string
  recorded: string
  engine: string
  note?: string
}

export type ClassicCitationRow = {
  id: string
  title: string
  source?: string
  /** X-01：典籍页码（有则展示） */
  sourcePage?: string
  verificationStatus: 'verified' | 'unverified' | 'paraphrase'
  note?: string
}

const DUAL_TRACK_REFERENCE_ROWS: DualTrackReferenceRow[] = [
  { id: 'ZIP09', topic: '从官杀 vs 七杀', recorded: '从官杀格', engine: '七杀格', note: '时干乙木比肩助身，阻断从杀' },
  { id: 'ZIP21', topic: '食神制杀 vs 七杀', recorded: '食神制杀格', engine: '七杀格', note: '衍生格局口径' },
  { id: 'ZIP22', topic: '伤官佩印 vs 伤官', recorded: '伤官佩印格', engine: '伤官格', note: '衍生格局口径' },
  { id: 'ZIP01', topic: '外格回归', recorded: '—', engine: '引擎主盘', note: '千里命稿 pillar_direct' },
  { id: 'ZIP04', topic: '月刃回归', recorded: '—', engine: '引擎主盘', note: '千里命稿 pillar_direct' },
  { id: 'ZIP05', topic: '杂格回归', recorded: '—', engine: '引擎主盘', note: '千里命稿 pillar_direct' },
  { id: 'ZW03', topic: '立春前晚子', recorded: '开源排盘轨 癸丑', engine: '乙丑', note: '换年/换日口径双轨样例' },
  { id: 'youbi', topic: '右弼口径', recorded: 'month（默认）', engine: 'hour（可选）', note: '辅煞 ±1 不表示主星错误' },
]

export function buildDualTrackReferenceRows(): DualTrackReferenceRow[] {
  return DUAL_TRACK_REFERENCE_ROWS
}

export function buildClassicCitationRows(classics?: Array<Record<string, unknown>> | null): ClassicCitationRow[] {
  if (!classics?.length) return []
  return classics.slice(0, 12).map((item) => {
    const pageRaw = item.source_page
    const sourcePage = typeof pageRaw === 'string' && pageRaw.trim() ? pageRaw.trim() : undefined
    return {
      id: String(item.id ?? '—'),
      title: String(item.title ?? item.id ?? '典籍'),
      source: typeof item.source === 'string' && item.source.trim() ? item.source.trim() : undefined,
      sourcePage,
      verificationStatus: (item.verification_status as ClassicCitationRow['verificationStatus']) || 'unverified',
      note: typeof item.notes === 'string'
        ? item.notes.slice(0, 80)
        : (typeof item.note === 'string' ? item.note.slice(0, 80) : undefined),
    }
  })
}

/** X-01：按 classic_id 查抽检页码 */
export function lookupClassicSourcePage(
  classicId: string | null | undefined,
  classics?: Array<Record<string, unknown>> | null,
): string | undefined {
  const id = classicId?.trim()
  if (!id || !classics?.length) return undefined
  const hit = classics.find((item) => String(item.id ?? '') === id)
  const page = hit?.source_page
  return typeof page === 'string' && page.trim() ? page.trim() : undefined
}

export function countUnverifiedClassics(classics?: Array<Record<string, unknown>> | null): number {
  return (classics ?? []).filter((item) => item.verification_status !== 'verified').length
}

export function buildClassicPendingLines(classics?: Array<Record<string, unknown>> | null): string[] {
  const pending = (classics ?? []).filter((item) => item.verification_status === 'unverified').slice(0, 5)
  return pending.map((item) => {
    const page = typeof item.source_page === 'string' && item.source_page.trim()
      ? ` · 页 ${item.source_page.trim()}`
      : ''
    return `语料待核：${item.id ?? '—'} · ${item.title ?? ''}${page}`.trim()
  })
}

export function readProvenance(payload?: { provenance?: ResponseProvenance | null } | null) {
  return payload?.provenance ?? null
}
