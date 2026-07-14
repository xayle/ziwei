<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useRouter, useRoute } from 'vue-router'
import SummaryStrip from '@/components/fusheng/SummaryStrip.vue'
import AnalysisPanel, { type AnalysisBlock } from '@/components/fusheng/AnalysisPanel.vue'
import BaziReferenceTable from '@/components/new/BaziReferenceTable.vue'
import BaziStructuralRelations from '@/components/fusheng/BaziStructuralRelations.vue'
import BaziLiuriTodayCard from '@/components/fusheng/BaziLiuriTodayCard.vue'
import FushengZiweiPlate from '@/components/fusheng/FushengZiweiPlate.vue'
import brandMark from '@/assets/brand/fusheng-mark.svg'
import { useFushengReport } from '@/composables/useFushengReport'
import { useEngineTrustDisplay } from '@/composables/useEngineTrustDisplay'
import DualTrackTable from '@/components/fusheng/DualTrackTable.vue'
import EngineTrustPanel from '@/components/fusheng/EngineTrustPanel.vue'
import { exportReportElementToPdf } from '@/composables/useReportPdfExport'
import { downloadFushengReportPdf, saveBlobAsFile } from '@/api/fushengReport'
import { useReportNotesStore } from '@/stores/reportNotes'
import { useAiStore } from '@/stores/ai'
import { useAuthStore } from '@/stores/auth'
import { LLM_MODULES, type LlmModuleId } from '@/api/llm'
import { buildProfileSignature } from '@/utils/buildChartRequests'
import { getProfileCompleteness, getTimeConfidence } from '@/utils/profileMetrics'
import { buildFushengReportPdfRequest } from '@/utils/buildChartRequests'
import { buildBaziColumns } from '@/utils/buildBaziColumns'
import { formatCnElementsJoin } from '@/utils/yongshenElements'
import { buildBaziModuleCards, baziModuleCardsToAnalysisBlocks } from '@/utils/buildBaziModuleCards'
import { buildZiweiInsightBlocks, buildPatternAnalysisBlocks } from '@/utils/buildZiweiInsightBlocks'
import { buildLifeVolumes } from '@/utils/buildLifeVolumes'
import { buildChartHash } from '@/utils/chartHash'
import { fetchLifeVolumes, fetchLifeSnippets, useLifeVolumesApiEnabled } from '@/api/life'
import type { LifeSnippetsResponseModel } from '@/api/openapiTypes'
import { fetchReportExplainBatches, type ExplainBatchResponse } from '@/api/explain'
import type { LifeVolumeResponse, LifeVolume } from '@/types/life-volume'
import { buildBaziRequest, buildZiweiRequest } from '@/utils/buildChartRequests'
import ReportChapterNav from '@/components/fusheng/ReportChapterNav.vue'
import VolumeSection from '@/components/fusheng/VolumeSection.vue'
import VolumePaywall from '@/components/fusheng/VolumePaywall.vue'
import SnippetHooksPanel from '@/components/fusheng/SnippetHooksPanel.vue'
import DouyinShareCard from '@/components/fusheng/DouyinShareCard.vue'
import ColophonFootnote from '@/components/fusheng/ColophonFootnote.vue'
import ReadingGuide from '@/components/fusheng/ReadingGuide.vue'
import TrustDegradedBanner from '@/components/fusheng/TrustDegradedBanner.vue'
import { useReadingProgress } from '@/composables/useReadingProgress'
import { useReportReadingGuide } from '@/composables/useReportReadingGuide'
import { LIFE_VOLUME_LABELS, type LifeVolumeId } from '@/types/life-volume'
import {
  DEMO_LOCKED_VOLUME_IDS,
  demoVolumeLocksEnabled,
} from '@/constants/volumePaywall'
import { useEntitlementStore } from '@/stores/entitlement'
import { useYoubiHourAlign } from '@/composables/useYoubiHourAlign'
import { buildDayunDisplayRow } from '@/utils/dayunDisplay'
import { validateBaziZiweiConsistency } from '@/utils/crossValidation'
import { trackFlowEvent } from '@/utils/flowAnalytics'
import {
  shouldTryLifeVolumesRemote,
  resolveLifeVolumeDoc,
  shouldBuildLifeVolumesAdapter,
  isLifeVolumeResponse,
} from '@/utils/feBeAdapter'
import '@/assets/fusheng-page.css'
import '@/assets/report-print.css'

const router = useRouter()
const route = useRoute()
const reportBodyRef = ref<HTMLElement | null>(null)
const exportingPdf = ref(false)
const exportingServerPdf = ref(false)
const notesStore = useReportNotesStore()
const aiStore = useAiStore()
const auth = useAuthStore()
const reportNotes = ref('')

const {
  profile,
  loading,
  loadingDayun,
  error,
  bazi,
  ziwei,
  dayunReport,
  loadReport,
  requestMeta,
  generatedAt,
  engineLabel,
  dayunError,
  snapshotNote,
  snapshotError,
} = useFushengReport()
const { activeProfileId } = storeToRefs(profile)
const {
  missingFields,
  provenanceRows,
  dualTracks,
  dualTrackReference,
  classicPendingLines,
  validationLines,
  iztro,
  liuri,
  pillarDetails,
  relations,
  strengthFactorLines,
  baziStructural,
  ziweiStructural,
  palaceStructured,
} = useEngineTrustDisplay(bazi, ziwei)
const liuriRaw = computed(() => bazi.value?.liuri_liushi ?? null)
const liuriNarrative = computed(() => {
  const l = liuriRaw.value
  if (!l?.flow_summary && l?.flow_score_dayun == null) return ''
  const parts: string[] = []
  if (l.flow_summary) parts.push(l.flow_summary)
  const dims = [
    l.flow_score_dayun != null ? `大运维 ${l.flow_score_dayun}` : '',
    l.flow_score_liunian != null ? `流年维 ${l.flow_score_liunian}` : '',
    l.flow_score_geju != null ? `格局维 ${l.flow_score_geju}` : '',
  ].filter(Boolean)
  if (dims.length) parts.push(`联动：${dims.join(' · ')}`)
  if (l.transition_hint) parts.push(l.transition_hint)
  return parts.join('。')
})
const { showYoubiDriftHint, applyYoubiHour: alignYoubiHour } = useYoubiHourAlign(ziwei)
const activeChapter = ref<LifeVolumeId>('preface')
const continuousRead = ref(true)
const selectedLlmModule = ref<LlmModuleId>('career_detail')
const chartHashRef = ref('pending')
const explainBatch = ref<ExplainBatchResponse | null>(null)
const lifeVolumeRemote = ref<LifeVolumeResponse | null>(null)

const reportPageClass = computed(() => ({
  'report-page--continuous': continuousRead.value,
}))
async function applyYoubiHour() {
  lifeVolumeRemote.value = null
  await alignYoubiHour(async () => {
    await loadReport(true)
    await finalizeReportLoad()
  })
}

watch(() => profile.activeProfileId, (id) => {
  reportNotes.value = notesStore.getNotes(id)
  lifeVolumeRemote.value = null
}, { immediate: true })

watch(reportNotes, (text) => {
  notesStore.setNotes(profile.activeProfileId, text)
})

const volumeChapters = computed(() => (
  Object.entries(LIFE_VOLUME_LABELS).map(([id, label]) => ({ id: id as LifeVolumeId, label }))
))

async function loadExplainBatches() {
  const data = profile.asProfileData()
  if (!data.birthDt) return
  explainBatch.value = await fetchReportExplainBatches(
    buildBaziRequest(data) as unknown as Record<string, unknown>,
    buildZiweiRequest(data) as unknown as Record<string, unknown>,
  )
}

async function loadLifeVolumesRemote() {
  lifeVolumeRemote.value = null
  const remoteCaseId = profile.activeProfile?.remoteCaseId
  const tryRemote = shouldTryLifeVolumesRemote({
    envFlag: useLifeVolumesApiEnabled(),
    isLoggedIn: auth.isLoggedIn,
    remoteCaseId,
  })
  if (!tryRemote) return
  const caseId = remoteCaseId ?? profile.activeProfileId
  if (!caseId) return
  const doc = await fetchLifeVolumes(caseId)
  if (!doc) return
  lifeVolumeRemote.value = doc
  if (doc.chart_hash) {
    chartHashRef.value = doc.chart_hash
  }
}

const lifeSnippets = ref<LifeSnippetsResponseModel | null>(null)

async function loadLifeSnippets() {
  lifeSnippets.value = null
  if (!auth.isLoggedIn) return
  const caseId = profile.activeProfile?.remoteCaseId ?? profile.activeProfileId
  if (!caseId) return
  lifeSnippets.value = await fetchLifeSnippets(caseId)
}

const lifeVolumeLocal = computed(() => {
  const remote = lifeVolumeRemote.value
  // T081：remote 权威成功时不调用 deprecated Adapter
  if (!shouldBuildLifeVolumesAdapter(remote) && remote && isLifeVolumeResponse(remote)) {
    return remote
  }
  return buildLifeVolumes({
    caseId: profile.activeProfileId || 'local',
    chartHash: chartHashRef.value,
    bazi: bazi.value,
    ziwei: ziwei.value,
    profileLabel: profile.activeProfile?.label,
    explain: explainBatch.value,
    trustLevel: iztro.value?.status === 'degraded' ? 'degraded' : 'full',
    missingFields: missingFields.value,
    iztroAdvisory: iztro.value?.message,
    wenmoAdvisory: ziwei.value?.wenmo_advisory ?? explainBatch.value?.wenmo_advisory,
    engineLabel: engineLabel.value,
    generatedAt: generatedAt.value ?? undefined,
  })
})

const lifeVolumeResolved = computed(() => resolveLifeVolumeDoc({
  remote: lifeVolumeRemote.value,
  local: lifeVolumeLocal.value,
}))
const lifeVolumeDoc = computed(() => lifeVolumeResolved.value.doc)
const lifeVolumeSource = computed(() => lifeVolumeResolved.value.source)

const shareFactLines = computed(() => {
  const fromSnippets = lifeSnippets.value?.hooks?.map((h) => h.text).filter(Boolean) ?? []
  if (fromSnippets.length) return fromSnippets.slice(0, 4)
  const vol1 = lifeVolumeDoc.value.volumes?.find((v) => v.id === 'vol1')
  const blocks = vol1?.sections?.flatMap((s) => s.blocks?.map((b) => b.text) ?? []) ?? []
  return blocks.filter(Boolean).slice(0, 3)
})

const shareVolumeTitle = computed(
  () => lifeSnippets.value?.vertical_title || LIFE_VOLUME_LABELS.vol1 || '卷一·命之根',
)

const shareDisclaimer = computed(
  () =>
    lifeSnippets.value?.disclaimer
    || lifeVolumeDoc.value.disclaimer_block?.text
    || '传统文化与自我认知参考，非命运断言。',
)

const shareCaseId = computed(
  () => profile.activeProfile?.remoteCaseId || (auth.isLoggedIn ? profile.activeProfileId : null),
)

const showDouyinShare = computed(() => shareFactLines.value.length > 0 || Boolean(lifeSnippets.value))

/** T092：沙箱模拟解锁的卷 id（不经支付） */
const mockUnlockedVolumeIds = ref<Set<string>>(new Set())
const entitlementStore = useEntitlementStore()

function volumeShowsLock(volume: { id: string; locked?: boolean }): boolean {
  // T094：权益商店已解锁的卷（含支付回调后）
  if (entitlementStore.isVolumeUnlockedByEntitlement(volume.id)) return false
  if (mockUnlockedVolumeIds.value.has(volume.id)) return false
  if (volume.locked) return true
  return demoVolumeLocksEnabled() && (DEMO_LOCKED_VOLUME_IDS as string[]).includes(volume.id)
}

function lockedSectionDetail(volume: LifeVolume): string | null {
  const teaser = volume.sections?.find((s) => s.id === 'locked')
  const text = teaser?.blocks?.[0]?.text?.trim()
  return text || null
}

function onMockUnlock(volumeId: string) {
  const next = new Set(mockUnlockedVolumeIds.value)
  next.add(volumeId)
  mockUnlockedVolumeIds.value = next
}

/** T082：仅当 remote 卷已含对应 explain 段时，隐藏 archive AnalysisPanel，避免双重 cite */
function remoteVolumeHasSection(volumeId: string, sectionIds: string[]): boolean {
  if (lifeVolumeSource.value !== 'remote') return false
  const vol = lifeVolumeDoc.value.volumes.find((v) => v.id === volumeId)
  return (vol?.sections ?? []).some((s) => sectionIds.includes(s.id))
}
const hideVol1ArchivePanels = computed(() => remoteVolumeHasSection('vol1', ['geju-explain']))
const hideVol4ArchivePanels = computed(() => remoteVolumeHasSection('vol4', ['palaces-explain']))
const hideVol5ArchivePanels = computed(() => remoteVolumeHasSection('vol5', ['domains-explain']))

const {
  readingParagraphs: reportReadingParagraphs,
  usingDynamicReading: reportUsingDynamicReading,
  readingFailed: reportReadingFailed,
} = useReportReadingGuide(explainBatch, lifeVolumeDoc)

const readingGuideReady = computed(() => (
  Boolean(explainBatch.value) || lifeVolumeSource.value === 'remote' || !loading.value
))

const { resumeLabel, lastVolumeId, save: saveReadingProgress, load: reloadReadingProgress } = useReadingProgress(
  () => activeProfileId.value || 'default',
)

const resumeVolumeIdProp = computed((): LifeVolumeId | null => lastVolumeId.value)
const resumeLabelProp = computed((): string | null => resumeLabel.value)

function resumeReading() {
  if (!lastVolumeId.value) return
  navigateToChapter(lastVolumeId.value)
}

const profileData = computed(() => ({
  surname: profile.surname,
  givenName: profile.givenName,
  gender: profile.gender,
  birthDt: profile.birthDt,
  cityName: profile.cityName,
  lon: profile.lon,
  tz: profile.tz,
  solarTime: profile.solarTime,
  calendarMode: profile.calendarMode,
  isLeapMonth: profile.isLeapMonth,
  birthTimePrecision: profile.birthTimePrecision,
  unknownTimeFallback: profile.unknownTimeFallback,
  focusTopic: profile.focusTopic,
  currentCityName: profile.currentCityName,
  currentProvince: profile.currentProvince,
  currentLon: profile.currentLon,
  currentTz: profile.currentTz,
  mode: profile.mode,
}))

const completeness = computed(() => getProfileCompleteness(profileData.value))
const timeConfidence = computed(() => getTimeConfidence(profileData.value))
const crossValidation = computed(() => validateBaziZiweiConsistency(bazi.value, ziwei.value))

const dayunRows = computed(() => {
  const items = bazi.value?.dayun?.items ?? bazi.value?.dayun?.cycles ?? []
  const narratives = dayunReport.value?.items ?? []
  return items.slice(0, 10).map((item, idx) => {
    const narrativeItem = narratives.find((n) => n.ganzhi === `${item.stem || ''}${item.branch || ''}`.trim()) ?? narratives[idx]
    const range = item.start_year ? `${item.start_year}-${(item.start_year ?? 0) + 9}` : (
      narrativeItem?.start_age != null && narrativeItem?.end_age != null
        ? `${narrativeItem.start_age}–${narrativeItem.end_age}岁`
        : '—'
    )
    return buildDayunDisplayRow(item, {
      range,
      tenGod: narrativeItem?.ten_god,
      narrative: narrativeItem?.narrative || item.narrative || '',
    })
  })
})

const palaceRows = computed(() => (ziwei.value?.palaces ?? []).map((p) => ({
  name: p.name,
  gz: `${p.stem}${p.branch}`,
  stars: p.main_stars?.map((s) => s.name).join('、') || '无主星',
})))

const metaSummary = computed(() => {
  const meta = requestMeta.value
  const yd = ziwei.value?.lunar?.year_divide
  const yearDivideLabel = yd === 'normal' ? '正月初一换年' : yd === 'lichun' ? '立春换年' : '—'
  return [
    { label: '引擎', value: engineLabel.value },
    { label: '生成时间', value: generatedAt.value ? generatedAt.value.replace('T', ' ').slice(0, 19) : '—' },
    { label: '时辰精度', value: meta?.precisionLabel || '—' },
    { label: '历法口径', value: meta?.calendarNote || '—' },
    { label: '年界', value: yearDivideLabel },
  ]
})

const baziColumns = computed(() => buildBaziColumns(bazi.value))

const archiveSummary = computed(() => [
  { label: '姓名', value: profile.activeProfile?.label || '默认档案' },
  { label: '姓氏', value: profile.surname || '未填写' },
  { label: '完整度', value: `${completeness.value}%` },
  { label: '时间可信度', value: timeConfidence.value.label },
  { label: '出生地', value: profile.cityName || '缺失' },
])

const baziSummary = computed(() => {
  const r = bazi.value
  if (!r) return [{ label: '状态', value: '待计算' }]
  const day = r.pillars_primary?.day
  return [
    { label: '日主', value: day ? `${day.stem}${day.branch}` : '缺失' },
    { label: '格局', value: r.geju?.geju_name || '缺失' },
    { label: '用神', value: formatCnElementsJoin(r.yongshen?.favor) },
    { label: '强弱', value: r.day_master_strength?.tier || '缺失' },
  ]
})

const ziweiSummary = computed(() => {
  const r = ziwei.value
  if (!r) return [{ label: '状态', value: '待计算' }]
  return [
    { label: '五行局', value: r.wuxing_ju_name || '缺失' },
    { label: '命宫', value: r.life_palace_gz || '缺失' },
    { label: '身宫', value: r.body_palace_gz || '缺失' },
    { label: '命主', value: r.life_ruler_star || '缺失' },
  ]
})

const baziBlocks = computed(() => {
  const r = bazi.value
  if (!r) return []
  const g = r.geju
  const engineLead = g?.engine_geju || g?.geju_name || '待分析'
  const classicBody = g?.classic_ref?.trim() || '暂无典籍句式。'
  const bullets: string[] = [
    `引擎格：${engineLead}${g?.is_broken ? '（破格）' : ''}`,
    `用神：${formatCnElementsJoin(r.yongshen?.favor)}`,
    `忌神：${formatCnElementsJoin(r.yongshen?.avoid)}`,
  ]
  if (g?.derived_geju && g.derived_geju !== g.geju_name) {
    bullets.push(`衍生格：${g.derived_geju}`)
  }
  if (g?.po_geju?.broken) {
    bullets.push(`破格：${g.po_geju.reason || '是'}${g.po_geju.po_jiu?.saved ? `；救应：${g.po_geju.po_jiu.method}` : ''}`)
  }
  if (g?.recorded_geju && g.recorded_geju !== g.geju_name) {
    bullets.push(`古籍口径：${g.recorded_geju}（${g.dual_track_id || '双轨'}）`)
  }
  const blocks: AnalysisBlock[] = [
    {
      id: 'bazi-engine',
      title: '格局（引擎层）',
      lead: engineLead,
      body: g?.geju_detail || g?.interpretation_text || '暂无引擎说明。',
      bullets,
      layer: 'engine',
    },
    {
      id: 'bazi-classical',
      title: '典籍句式',
      lead: classicBody.slice(0, 40) + (classicBody.length > 40 ? '…' : ''),
      body: classicBody,
      layer: 'classical',
    },
  ]
  if (g?.dual_track_note) {
    blocks.push({
      id: 'bazi-dual-track',
      title: '格局双轨说明',
      lead: g.recorded_geju || '古籍口径',
      body: g.dual_track_note,
      layer: 'classical',
    })
  }
  const y = r.yongshen
  if (y?.dual_track_note) {
    const wx = { wood: '木', fire: '火', earth: '土', metal: '金', water: '水' } as Record<string, string>
    const fmt = (arr?: string[]) => (arr ?? []).map((v) => wx[v] ?? v).join('、') || '—'
    blocks.push({
      id: 'bazi-yongshen-dual',
      title: '用神双轨说明',
      lead: `${y.dual_track_id || '双轨'}：古籍 ${fmt(y.recorded_favor)} · 引擎 ${fmt(y.engine_favor ?? y.favor)}`,
      body: y.dual_track_note,
      layer: 'classical',
    })
  }
  if (r.bazi_summary?.trim()) {
    blocks.push({
      id: 'bazi-heuristic-summary',
      title: '综合总评（启发式）',
      lead: '仅供参考',
      body: r.bazi_summary,
      layer: 'heuristic',
    })
  }
  return blocks
})

const ziweiBlocks = computed(() => {
  const r = ziwei.value
  if (!r) return []
  const patternItems = buildPatternAnalysisBlocks(r.patterns, 6)
  const blocks: AnalysisBlock[] = [...patternItems]
  if (r.summary?.trim()) {
    blocks.push({
      id: 'ziwei-heuristic-summary',
      title: '命盘摘要（启发式）',
      lead: '仅供参考',
      body: r.summary,
      layer: 'heuristic',
    })
  }
  return blocks
})

const domainBlocks = computed(() => baziModuleCardsToAnalysisBlocks(buildBaziModuleCards(bazi.value)))

const ziweiInsightBlocks = computed(() => buildZiweiInsightBlocks(ziwei.value))

function isChapterActive(id: LifeVolumeId) {
  if (continuousRead.value) return true
  return activeChapter.value === id
}

function printReport() {
  window.print()
}

async function downloadPdf() {
  if (exportingServerPdf.value || exportingPdf.value) return
  const label = profile.activeProfile?.label || '浮生报告'
  const filename = `${label}.pdf`

  exportingServerPdf.value = true
  try {
    const blob = await downloadFushengReportPdf(buildFushengReportPdfRequest(profile.asProfileData(), {
      label,
      notes: reportNotes.value,
    }))
    saveBlobAsFile(blob, filename)
    trackFlowEvent('report_pdf_server', profile.activeProfileId)
    return
  } catch {
    // 服务端不可用时回退客户端导出
  } finally {
    exportingServerPdf.value = false
  }

  if (!reportBodyRef.value) return
  exportingPdf.value = true
  try {
    await exportReportElementToPdf(reportBodyRef.value, filename)
    trackFlowEvent('report_pdf_export', profile.activeProfileId)
  } finally {
    exportingPdf.value = false
  }
}

async function generateAiInterpretation() {
  if (!bazi.value || !ziwei.value) return
  const signature = buildProfileSignature(profile.asProfileData())
  await aiStore.generateInterpretation({
    bazi: bazi.value,
    ziwei: ziwei.value,
    profileSignature: signature,
  })
  trackFlowEvent('report_ai_interpret', profile.activeProfileId)
}

async function generateModuleInterpretation() {
  await aiStore.generateModuleInterpretation(selectedLlmModule.value)
  trackFlowEvent('report_ai_module', profile.activeProfileId)
}

function toggleContinuousRead() {
  continuousRead.value = !continuousRead.value
}

function navigateToChapter(id: LifeVolumeId) {
  activeChapter.value = id
  saveReadingProgress(id)
  if (continuousRead.value) {
    continuousRead.value = false
  }
  requestAnimationFrame(() => {
    document.getElementById(`report-volume-${id}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  })
}

function syncChapterFromHash() {
  const raw = route.hash.replace(/^#/, '')
  if (!raw.startsWith('report-volume-')) return
  const id = raw.slice('report-volume-'.length) as LifeVolumeId
  if (id in LIFE_VOLUME_LABELS) {
    navigateToChapter(id)
  }
}

watch(() => route.hash, () => {
  syncChapterFromHash()
})

async function finalizeReportLoad() {
  trackFlowEvent('report_generate', profile.activeProfileId)
  try {
    chartHashRef.value = await buildChartHash(buildProfileSignature(profile.asProfileData()))
  } catch {
    chartHashRef.value = 'local'
  }
  // T079/T082：先拉 life/volumes；remote 已含 BE explain 则跳过 explain/batch（无双重 cite）
  await loadLifeVolumesRemote()
  void loadLifeSnippets()
  const volumesHasExplain = Boolean(lifeVolumeRemote.value)
  if (!volumesHasExplain) {
    await loadExplainBatches()
    if (explainBatch.value?.chart_hash) {
      chartHashRef.value = explainBatch.value.chart_hash
    }
  } else if (lifeVolumeRemote.value?.chart_hash) {
    chartHashRef.value = lifeVolumeRemote.value.chart_hash
  }
  if (auth.isLoggedIn && profile.activeProfile?.remoteCaseId) {
    void profile.pullRemoteSnapshots()
  }
}

async function reloadFullReport() {
  lifeVolumeRemote.value = null
  lifeSnippets.value = null
  await loadReport()
  await finalizeReportLoad()
}

onMounted(() => {
  reloadReadingProgress()
  void aiStore.loadConfig()
  if (auth.isLoggedIn) {
    void entitlementStore.refreshFromServer()
    if (profile.activeProfile?.remoteCaseId) {
      void profile.pullRemoteSnapshots()
    }
  }
  void loadReport().then(async () => {
    reloadReadingProgress()
    await finalizeReportLoad()
    // T094：支付回调带回 unlocked=1 → 再拉 volumes + 权益
    if (route.query.unlocked === '1') {
      await entitlementStore.refreshFromServer()
      lifeVolumeRemote.value = null
      await loadLifeVolumesRemote()
      mockUnlockedVolumeIds.value = new Set()
    }
    syncChapterFromHash()
  })
})

watch(
  () => route.query.unlocked,
  async (flag) => {
    if (flag !== '1') return
    await entitlementStore.refreshFromServer()
    lifeVolumeRemote.value = null
    await loadLifeVolumesRemote()
    mockUnlockedVolumeIds.value = new Set()
  },
)
</script>

<template>
  <main
    class="report-page"
    :class="reportPageClass"
    :data-life-volume-source="lifeVolumeSource"
  >
    <header class="report-toolbar no-print">
      <button class="fs-btn fs-btn--ghost" @click="router.push('/profile')">返回档案</button>
      <button class="fs-btn fs-btn--ghost" :disabled="loading" @click="reloadFullReport">重新生成</button>
      <button
        class="fs-btn fs-btn--ghost"
        :class="{ 'is-active': continuousRead }"
        data-testid="report-continuous-toggle"
        @click="toggleContinuousRead"
      >
        {{ continuousRead ? '连续阅读' : '单章阅读' }}
      </button>
      <button class="fs-btn fs-btn--ghost" @click="printReport">打印</button>
      <button class="fs-btn fs-btn--primary" :disabled="exportingPdf || exportingServerPdf || loading" data-testid="report-pdf" @click="downloadPdf">
        {{ exportingServerPdf ? '服务端导出中…' : exportingPdf ? '客户端导出中…' : '下载 PDF' }}
      </button>
    </header>

    <p v-if="loading" class="report-status">正在生成报告…</p>
    <p v-if="error" class="report-error">{{ error }}</p>
    <p v-if="snapshotNote" class="report-snapshot-note" data-testid="report-snapshot-note">{{ snapshotNote }}</p>
    <p v-if="snapshotError" class="report-snapshot-error">{{ snapshotError }}</p>

    <div class="report-layout">
      <ReportChapterNav
        class="report-layout__nav"
        :chapters="volumeChapters"
        :active-id="activeChapter"
        @navigate="navigateToChapter"
      />

      <article ref="reportBodyRef" class="report-body">
        <ReadingGuide
          :disclaimer="lifeVolumeDoc.disclaimer_block"
          :resume-volume-id="resumeVolumeIdProp"
          :resume-label="resumeLabelProp"
          :show-title="true"
          :show-layer-legend="true"
          :show-resume="true"
          :reading-paragraphs="reportReadingParagraphs"
          :reading-loading="loading && !readingGuideReady"
          :reading-failed="reportReadingFailed"
          :using-dynamic-reading="reportUsingDynamicReading"
          @resume="resumeReading"
        />
        <SnippetHooksPanel
          v-if="lifeSnippets?.hooks?.length"
          class="no-print"
          :hooks="lifeSnippets.hooks"
          :case-id="lifeSnippets.case_id"
          :vertical-title="lifeSnippets.vertical_title"
          :disclaimer="lifeSnippets.disclaimer"
          source="report"
        />
        <DouyinShareCard
          v-if="showDouyinShare"
          class="no-print"
          :volume-title="shareVolumeTitle"
          :fact-lines="shareFactLines"
          :disclaimer="shareDisclaimer"
          :case-id="shareCaseId"
          source="report"
        />
        <TrustDegradedBanner
          v-if="iztro?.status === 'degraded'"
          :message="iztro.message"
          status="degraded"
        />

        <section
          v-for="volume in lifeVolumeDoc.volumes"
          :key="volume.id"
          :id="`report-volume-${volume.id}`"
          class="report-volume"
          :class="{
            'is-active': isChapterActive(volume.id),
            'is-locked': volumeShowsLock(volume),
          }"
          :data-locked="volumeShowsLock(volume) ? '1' : undefined"
          :data-testid="volume.id === 'preface' ? 'report-cover-chapter' : volume.id === 'vol5' ? 'report-vol5-chapter' : undefined"
        >
          <h2 v-if="volume.id !== 'preface'">{{ LIFE_VOLUME_LABELS[volume.id] }}</h2>

          <VolumePaywall
            v-if="volumeShowsLock(volume)"
            :volume-id="volume.id"
            :detail="lockedSectionDetail(volume)"
            @mock-unlock="onMockUnlock(volume.id)"
          />

          <template v-if="!volumeShowsLock(volume)">
          <template v-if="volume.id === 'preface'">
            <div class="report-cover" data-testid="report-cover-hero">
              <img :src="brandMark" alt="浮生" class="report-cover__logo" width="96" height="96" />
              <h1>浮生 · 命理个人档案</h1>
              <p class="report-cover__slogan">浮生若寄，知命知心</p>
              <p class="report-cover__name">{{ profile.activeProfile?.label || '默认档案' }}</p>
              <p class="report-cover__meta">{{ profile.birthDt?.replace('T', ' ') || '出生时间未填写' }}</p>
              <p class="report-cover__version">浮生报告 v2.4 · {{ generatedAt ? generatedAt.slice(0, 10) : '—' }}</p>
            </div>
            <details class="report-preface-meta" data-testid="report-preface-meta">
              <summary>建档口径与摘要</summary>
              <SummaryStrip :items="metaSummary" />
              <div class="report-text">
                <p>{{ requestMeta?.timeRiskLabel }} — {{ requestMeta?.timeRiskHint }}</p>
                <p>{{ requestMeta?.dstLabel }}</p>
                <p>真太阳时：{{ profile.solarTime ? '已启用' : '未启用' }} · 时区 {{ profile.tz }}</p>
              </div>
              <SummaryStrip :items="archiveSummary" />
              <div class="report-text">
                <p>关注重点：{{ profile.focusTopic || '未填写' }}</p>
                <p>现居地：{{ profile.currentCityName || '未填写' }}</p>
                <p>经度 / 时区：{{ profile.lon ?? '缺失' }} / {{ profile.tz }}</p>
              </div>
            </details>
          </template>

          <template v-else-if="volume.id === 'vol1'">
            <p class="report-vol1-lead">卷一·命之根 — 四柱格局摘要；盘面可核对，深读见下方解读。</p>
            <SummaryStrip :items="baziSummary" />
            <div class="report-embed report-embed--compact" data-testid="report-vol1-compact-chart">
              <BaziReferenceTable :columns="baziColumns" active-key="day" :show-detail-rows="false" />
            </div>
            <AnalysisPanel
              v-if="!hideVol1ArchivePanels"
              :blocks="baziBlocks"
              default-open-id="bazi-engine"
            />
          </template>
          <template v-else-if="volume.id === 'vol2'">
            <TrustDegradedBanner
              v-if="crossValidation.overall === 'warn'"
              :message="crossValidation.items.find((item) => item.status === 'warn')?.detail || '八字与紫微口径需核对。'"
              status="warn"
            />
            <p class="report-cross-status" :data-status="crossValidation.overall">
              综合状态：{{ crossValidation.overall === 'pass' ? '一致' : crossValidation.overall === 'warn' ? '需核对' : '失败' }}
            </p>
            <div v-if="iztro" class="report-iztro-advisory" data-testid="report-cross-iztro" :data-status="iztro.status">
              <p>{{ iztro.message }}</p>
              <span class="report-iztro-advisory__meta">
                主星匹配 {{ iztro.mainMatch }}<template v-if="iztro.lifePalace"> · {{ iztro.lifePalace }}</template>
              </span>
            </div>
            <div
              v-if="iztro?.showDualTrackTable"
              class="report-iztro-dual-track"
              data-testid="report-iztro-dual-track"
            >
              <h3>紫微双轨对照（引擎主盘 vs iztro）</h3>
              <p class="hint">典型边界：立春前一日 + 晚子时（ZW03）。引擎主盘为产品 canonical，不静默覆盖。</p>
              <table class="report-table report-iztro-dual-track__table">
                <thead>
                  <tr>
                    <th>轨道</th>
                    <th>年界</th>
                    <th>换日</th>
                    <th>命宫</th>
                    <th>主星匹配</th>
                  </tr>
                </thead>
                <tbody>
                  <tr data-track="engine">
                    <td>引擎主盘</td>
                    <td>{{ iztro.engineTrack?.yearDivide || '—' }}</td>
                    <td>{{ iztro.engineTrack?.dayDivide || '—' }}</td>
                    <td><strong>{{ iztro.engineLifePalaceGz || ziwei?.life_palace_gz || '—' }}</strong></td>
                    <td>{{ iztro.mainMatch }}</td>
                  </tr>
                  <tr v-if="iztro.dualTrack" data-track="iztro-alt">
                    <td>{{ iztro.dualTrack.label }}</td>
                    <td>{{ iztro.dualTrack.yearDivide }}</td>
                    <td>{{ iztro.dualTrack.dayDivide }}</td>
                    <td><strong>{{ iztro.dualTrack.lifePalaceGz }}</strong></td>
                    <td>{{ iztro.dualTrack.mainMatch }}</td>
                  </tr>
                  <tr v-else data-track="iztro-default">
                    <td>iztro 库对照</td>
                    <td>正月初一换年</td>
                    <td>库默认</td>
                    <td><strong>{{ iztro.iztroLifePalaceGz || '—' }}</strong></td>
                    <td>—</td>
                  </tr>
                </tbody>
              </table>
              <p v-if="iztro.dualTrack?.note" class="hint">{{ iztro.dualTrack.note }}</p>
            </div>
            <div
              v-if="showYoubiDriftHint"
              class="report-youbi-drift"
              data-testid="report-youbi-drift-hint"
            >
              <p>
                右弼默认 <code>month</code> 口径与 iztro 生时安星可能差一宫（辅煞 ±1），不表示主星错误。
                可切换 <code>hour</code> 对齐 iztro 辅煞。
              </p>
              <button type="button" class="fs-btn fs-btn--ghost" data-testid="report-youbi-hour-btn" @click="applyYoubiHour">
                切换右弼为 hour 并重算
              </button>
            </div>
            <div data-testid="report-dual-track-reference">
              <DualTrackTable
                :rows="dualTrackReference"
                title="执业双轨对照表（固定清单）"
              />
            </div>
            <div
              v-if="classicPendingLines.length"
              class="report-classics-pending"
              data-testid="report-classics-pending"
            >
              <h3>典籍语料</h3>
              <ul>
                <li v-for="(line, idx) in classicPendingLines" :key="idx">{{ line }}</li>
              </ul>
            </div>
            <ul class="report-cross-list">
              <li v-for="(item, idx) in crossValidation.items" :key="idx" :data-status="item.status">
                <strong>{{ item.label }}</strong> — {{ item.detail }}
              </li>
            </ul>
            <div class="report-embed">
              <BaziStructuralRelations
                :relations="relations"
                :pillar-details="pillarDetails"
                :missing-fields="missingFields"
              />
            </div>
            <div class="report-embed">
              <BaziLiuriTodayCard :liuri="liuriRaw" />
            </div>
            <p v-if="liuriNarrative" class="report-liuri-narrative" data-testid="report-liuri-narrative">
              <strong>今日运势解读：</strong>{{ liuriNarrative }}
            </p>
            <EngineTrustPanel
              :dual-tracks="dualTracks"
              :validation-lines="validationLines"
              :iztro="iztro"
              compact
            />
          </template>

          <template v-else-if="volume.id === 'vol3'">
            <p v-if="loadingDayun" class="hint">正在加载大运叙事…</p>
            <p v-else-if="dayunError" class="report-dayun-error">{{ dayunError }}</p>
            <table class="report-table">
              <thead><tr><th>区间</th><th>干支</th><th>十神</th><th>用神进退</th></tr></thead>
              <tbody>
                <tr v-for="(row, idx) in dayunRows" :key="idx">
                  <td>{{ row.range }}</td>
                  <td>{{ row.ganzhi }}</td>
                  <td>{{ row.tenGod }}</td>
                  <td>{{ row.yongshenShiftLabel || '—' }}</td>
                </tr>
              </tbody>
            </table>
            <div v-for="(row, idx) in dayunRows" :key="`detail-${idx}`" class="dayun-detail">
              <h3>{{ row.ganzhi }} · {{ row.range }} · {{ row.tenGod }}</h3>
              <p v-if="row.gejuImpact" class="dayun-detail__engine">{{ row.gejuImpact }}</p>
              <p v-if="row.wealthHint" class="dayun-hint dayun-hint--heuristic">财运：{{ row.wealthHint }}</p>
              <p v-if="row.healthHint" class="dayun-hint dayun-hint--heuristic">健康：{{ row.healthHint }}</p>
              <p v-if="row.loveHint" class="dayun-hint dayun-hint--heuristic">感情：{{ row.loveHint }}</p>
              <p v-if="row.narrative" class="dayun-detail__narrative">{{ row.narrative }}</p>
            </div>
          </template>

          <template v-else-if="volume.id === 'vol4'">
            <p class="report-natal-note">
              命盘支持叠宫工具栏（大限 / 流年 / 流月 / 飞星）。详细运限序列见卷三或
              <router-link to="/new/ziwei/timeline">紫微时间轴</router-link>。
            </p>
            <SummaryStrip :items="ziweiSummary" />
            <div v-if="ziwei" class="report-embed">
              <FushengZiweiPlate :result="ziwei" />
            </div>
            <table class="report-table">
              <thead><tr><th>宫位</th><th>宫干</th><th>主星</th></tr></thead>
              <tbody>
                <tr v-for="(row, idx) in palaceRows" :key="idx">
                  <td>{{ row.name }}</td><td>{{ row.gz }}</td><td>{{ row.stars }}</td>
                </tr>
              </tbody>
            </table>
            <AnalysisPanel
              v-if="!hideVol4ArchivePanels"
              :blocks="ziweiBlocks"
              :default-open-id="ziweiBlocks[0]?.id"
            />
            <section v-if="palaceStructured?.length" class="report-palace-structured" data-testid="report-palace-structured">
              <h3>宫论（结构化）</h3>
              <article v-for="row in palaceStructured" :key="row.name" class="report-palace-structured__row">
                <h4>
                  {{ row.name }}
                  <span v-if="row.tags.length">{{ row.tags.join('、') }}</span>
                </h4>
                <p><strong>结论</strong> — {{ row.conclusion }}</p>
                <p v-if="row.explanation">{{ row.explanation }}</p>
                <p v-if="row.suggestion" class="hint">建议：{{ row.suggestion }}</p>
              </article>
            </section>
            <AnalysisPanel
              v-if="!hideVol4ArchivePanels && ziweiInsightBlocks.length"
              data-testid="report-ziwei-insight"
              :blocks="ziweiInsightBlocks"
              default-open-id="ziwei-forecast-year"
            />
          </template>

          <template v-else-if="volume.id === 'vol5'">
            <p class="hint">性格、事业、财运、婚恋、健康、人际等引擎模块；推断层默认折叠。</p>
            <AnalysisPanel
              v-if="!hideVol5ArchivePanels && domainBlocks.length"
              :blocks="domainBlocks"
            />
            <p
              v-else-if="!hideVol5ArchivePanels"
              class="report-placeholder"
            >域分析待生成，请先完成八字排盘。</p>
          </template>

          <template v-else-if="volume.id === 'vol6'">
            <textarea
              v-model="reportNotes"
              class="report-notes"
              rows="8"
              placeholder="记录换运节点、重点流年、客户反馈与复核结论…"
              data-testid="report-notes"
            />
            <p class="hint">批注按档案自动保存至本地，切换档案后内容独立。</p>

            <details class="ai-panel">
              <summary class="ai-panel__summary">AI 解读（需主动展开）</summary>
              <div class="ai-panel__content">
                <p v-if="aiStore.configNote" class="ai-panel__meta">{{ aiStore.configNote }}</p>
                <p v-if="!auth.isLoggedIn" class="hint">
                  <router-link to="/login">登录</router-link> 后可生成 AI 命盘解读草稿。
                </p>
                <template v-else>
                  <button
                    class="fs-btn fs-btn--ghost"
                    :disabled="aiStore.loading || loading || !bazi || !ziwei"
                    data-testid="report-ai-generate"
                    @click="generateAiInterpretation"
                  >
                    {{ aiStore.loading ? '生成中…' : '生成 AI 解读' }}
                  </button>
                  <p v-if="aiStore.error" class="ai-panel__error">{{ aiStore.error }}</p>
                  <div v-if="aiStore.messages.length" class="ai-panel__body">
                    <p v-for="(msg, idx) in aiStore.messages" :key="idx" :class="`ai-msg ai-msg--${msg.role}`">
                      {{ msg.text }}
                    </p>
                  </div>

                  <div class="ai-panel__modules">
                    <h4>分模块解读</h4>
                    <p v-if="!aiStore.configAvailable" class="hint">LLM 未配置或不可用。</p>
                    <div v-else class="ai-panel__module-row">
                      <select v-model="selectedLlmModule" class="ai-panel__select" data-testid="report-llm-module">
                        <option v-for="mod in LLM_MODULES" :key="mod.id" :value="mod.id">{{ mod.label }}</option>
                      </select>
                      <button
                        class="fs-btn fs-btn--ghost"
                        :disabled="aiStore.moduleLoading || !profile.activeProfile?.remoteCaseId"
                        data-testid="report-llm-module-generate"
                        @click="generateModuleInterpretation"
                      >
                        {{ aiStore.moduleLoading ? '生成中…' : '生成分模块解读' }}
                      </button>
                    </div>
                    <p v-if="!profile.activeProfile?.remoteCaseId" class="hint">需将档案同步至云端后方可使用分模块解读。</p>
                    <p v-if="aiStore.moduleError" class="ai-panel__error">{{ aiStore.moduleError }}</p>
                    <p v-if="aiStore.moduleInterpretation" class="ai-msg ai-msg--ai">{{ aiStore.moduleInterpretation }}</p>
                  </div>
                </template>
              </div>
            </details>
          </template>

          <template v-else-if="volume.id === 'colophon'">
            <ColophonFootnote :colophon="lifeVolumeDoc.colophon" />
            <EngineTrustPanel
              :missing-fields="missingFields"
              :provenance-rows="provenanceRows"
              :dual-tracks="dualTracks"
              :validation-lines="validationLines"
              :iztro="iztro"
              :liuri="liuri"
              :strength-factor-lines="strengthFactorLines"
              :bazi-structural="baziStructural"
              :ziwei-structural="ziweiStructural"
              :palace-structured="palaceStructured"
            />
          </template>

          <VolumeSection
            v-for="sec in volume.sections"
            :key="sec.id"
            :section="sec"
            :volume-id="volume.id"
            :volume-locked="volumeShowsLock(volume)"
          />
          </template>
        </section>
      </article>
    </div>
  </main>
</template>

<style scoped>
.report-page {
  display: grid;
  gap: 14px;
  width: 100%;
  min-width: 0;
  overflow-x: clip;
}

.report-toolbar {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.report-status,
.report-error {
  margin: 0;
  padding: 12px 14px;
  border-radius: 12px;
  font-size: 14px;
}

.report-status {
  background: var(--brand-gold-lt);
  color: var(--brand-gold-dark);
}

.report-natal-note {
  margin: 0 0 12px;
  padding: 10px 14px 10px 11px;
  border-radius: var(--radius-sm);
  background: var(--surface);
  border: 1px solid var(--border);
  border-left: 3px solid var(--brand-gold);
  font-size: 13px;
  line-height: 1.65;
  color: var(--brand-mist);
}

.report-iztro-advisory {
  margin: 0 0 12px;
  padding: 10px 14px 10px 11px;
  border-radius: var(--radius-sm);
  background: var(--surface);
  border: 1px solid var(--border);
  border-left: 3px solid var(--brand-cinnabar);
  font-size: 13px;
  line-height: 1.65;
  color: var(--brand-cinnabar);
}

.report-iztro-advisory[data-status="life_palace_only"] {
  border-left-color: var(--brand-gold);
  color: var(--brand-gold-dark);
}

.report-iztro-advisory__meta {
  display: block;
  margin-top: 4px;
  font-size: 11px;
  opacity: 0.85;
}

.report-iztro-dual-track {
  margin: 0 0 14px;
  padding: 12px 14px;
  border-radius: var(--radius-sm);
  background: var(--surface);
  border: 1px solid var(--border-md);
}

.report-iztro-dual-track h3 {
  margin: 0 0 6px;
  font-size: 14px;
  color: var(--brand-ink);
}

.report-iztro-dual-track__table {
  margin-top: 8px;
  font-size: 12px;
}

.report-iztro-dual-track__table td strong {
  color: var(--brand-ink);
}

.report-youbi-drift {
  margin: 0 0 14px;
  padding: 10px 14px 10px 11px;
  border-radius: var(--radius-sm);
  background: var(--surface);
  border: 1px solid var(--border);
  border-left: 3px solid var(--brand-gold);
  font-size: 13px;
  line-height: 1.65;
  color: var(--brand-mist);
  display: grid;
  gap: 8px;
}

.report-palace-structured {
  margin: 0 0 16px;
  padding: 12px 14px;
  border-radius: 10px;
  border: 1px solid var(--border-soft, #e7e0d5);
  background: #fffdf7;
}

.report-palace-structured h3 {
  margin: 0 0 10px;
  font-size: 15px;
  font-family: var(--font-cn);
}

.report-palace-structured__row {
  padding: 10px 0;
  border-top: 1px solid var(--border-soft, #e7e0d5);
}

.report-palace-structured__row:first-of-type {
  border-top: none;
  padding-top: 0;
}

.report-palace-structured__row h4 {
  margin: 0 0 6px;
  font-size: 14px;
}

.report-palace-structured__row h4 span {
  font-weight: 400;
  font-size: 12px;
  color: var(--text-3);
}

.report-youbi-drift p {
  margin: 0;
}

.report-dual-track-ref,
.report-classics-pending {
  margin: 14px 0;
  padding: 12px 14px;
  border: 1px solid #e7e5e4;
  border-radius: 10px;
  background: #fffdf7;
}

.report-dual-track-ref h3,
.report-classics-pending h3 {
  margin: 0 0 8px;
  font-size: 14px;
  color: #292524;
}

.report-dual-track-ref__table {
  width: 100%;
  font-size: 12px;
}

.report-classics-pending ul {
  margin: 0;
  padding-left: 18px;
  font-size: 12px;
  color: #78716c;
}

.report-natal-note a {
  color: var(--brand-gold-dark);
  font-weight: 600;
}

.report-error {
  background: rgba(139, 58, 42, 0.08);
  color: var(--brand-cinnabar);
}

.report-layout {
  display: grid;
  grid-template-columns: 200px minmax(0, 1fr);
  gap: 14px;
  align-items: start;
}

.report-layout__nav {
  min-width: 0;
}

.report-body {
  border: 1px solid var(--border);
  border-radius: 16px;
  background: rgba(255, 250, 245, 0.98);
  box-shadow: var(--shadow);
  padding: 28px;
  min-height: 520px;
  display: grid;
  gap: 20px;
  min-width: 0;
  overflow-x: clip;
}

.report-volume {
  display: none;
}

.report-volume.is-active {
  display: grid;
  gap: 12px;
}

.report-volume.is-locked > h2 {
  color: var(--brand-mist);
}

.report-page--continuous .report-volume {
  display: grid;
  gap: 12px;
  padding-bottom: 28px;
  margin-bottom: 28px;
  border-bottom: 1px dashed var(--border);
}

.report-page--continuous .report-volume:last-child {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.report-toolbar .fs-btn.is-active {
  border-color: var(--brand-gold);
  background: var(--brand-gold-lt);
  color: var(--brand-gold-dark);
}

.report-volume h2 {
  margin: 0 0 16px;
  padding-left: var(--sp-3);
  border-left: 3px solid var(--brand-gold);
  font-family: var(--font-cn);
  color: var(--brand-ink);
  font-size: 17px;
  letter-spacing: 0.08em;
}

.report-cover {
  text-align: center;
  padding: 48px 24px 40px;
  margin-bottom: 8px;
  border: 1px solid var(--border);
  border-radius: var(--radius-codex);
  background: var(--surface);
  box-shadow: none;
}

.report-preface-meta {
  margin-top: 4px;
  font-size: 13px;
  color: var(--brand-mist);
}

.report-preface-meta summary {
  cursor: pointer;
  font-family: var(--font-ui);
  color: var(--brand-gold-dark);
  margin-bottom: 8px;
}

.report-preface-meta[open] summary {
  margin-bottom: 12px;
}

.report-cover__logo {
  width: 88px;
  height: 88px;
  display: block;
  margin-bottom: 18px;
}

.report-cover h1 {
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(24px, 3vw, 30px);
  font-weight: 600;
  text-wrap: balance;
}

.report-cover__slogan {
  margin: 12px 0 0;
  color: var(--brand-gold-dark);
  letter-spacing: 0.12em;
  font-family: var(--font-display);
  font-size: 13px;
}

.report-cover__name {
  margin: 28px 0 0;
  font-size: 22px;
  font-weight: 600;
  font-family: var(--font-display);
  color: var(--brand-ink);
}

.report-cover__meta {
  margin: 8px 0 0;
  color: var(--text-2);
}

.report-cover__version {
  margin: 12px 0 0;
  font-size: 12px;
  color: var(--text-3);
}

.report-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 12px;
  font-size: 13px;
}

.report-table th,
.report-table td {
  border: 1px solid var(--border);
  padding: 8px 10px;
  text-align: left;
}

.report-table th {
  background: var(--inset-tint);
  font-family: var(--font-cn);
}

.report-cross-list {
  margin: 12px 0 0;
  padding-left: 18px;
  line-height: 1.8;
  color: var(--text-2);
}

.report-cross-status {
  margin: 0;
  font-weight: 700;
  color: var(--brand-gold-dark);
}

.report-text {
  margin-top: 16px;
  color: var(--text-2);
  line-height: 1.8;
}

.report-placeholder {
  padding: 16px;
  border-radius: 12px;
  background: var(--brand-gold-lt);
  border: 1px dashed var(--brand-gold);
}

.report-embed {
  margin-top: 16px;
  overflow-x: auto;
}

.report-vol1-lead {
  margin: 0 0 12px;
  color: var(--brand-mist);
  font-size: var(--fs-sm);
  line-height: 1.6;
  max-width: 62ch;
}

.report-embed--compact {
  max-width: 720px;
  overflow-x: visible;
}

.disclaimer {
  margin-top: 24px;
  font-size: 12px;
  color: var(--text-3);
}

.report-notes {
  width: 100%;
  margin-top: 12px;
  padding: 12px 14px;
  border: 1px solid var(--border);
  border-radius: 12px;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.7;
  resize: vertical;
  background: var(--surface);
  color: var(--text);
}

.report-snapshot-note,
.report-snapshot-error {
  margin: 0;
  padding: 8px 12px;
  border-radius: 10px;
  font-size: 12px;
}

.report-snapshot-note {
  background: var(--surface);
  border: 1px solid var(--border);
  border-left: 3px solid var(--brand-gold);
  color: var(--brand-mist);
}

.report-snapshot-error {
  background: var(--surface);
  border: 1px solid var(--border);
  border-left: 3px solid var(--brand-cinnabar);
  color: var(--brand-ink);
}

.ai-panel {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid var(--border);
}

.ai-panel__summary {
  cursor: pointer;
  font-size: 16px;
  font-weight: 600;
  color: var(--brand-ink);
  list-style: none;
}

.ai-panel__summary::-webkit-details-marker {
  display: none;
}

.ai-panel__content {
  margin-top: 12px;
  display: grid;
  gap: 10px;
}

.ai-panel__meta {
  font-size: 12px;
  color: var(--text-2);
}

.ai-panel__error {
  margin: 0;
  font-size: 13px;
  color: var(--brand-cinnabar);
}

.ai-panel__body {
  display: grid;
  gap: 10px;
}

.ai-msg {
  margin: 0;
  padding: 12px 14px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.75;
  white-space: pre-wrap;
}

.ai-msg--ai {
  background: var(--inset-tint);
  border: 1px solid var(--border);
  color: var(--text);
}

.ai-msg--user {
  background: var(--brand-gold-lt);
  color: var(--brand-gold-dark);
}

.ai-panel__modules {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed var(--border);
  display: grid;
  gap: 8px;
}

.ai-panel__modules h4 {
  margin: 0;
  font-size: 14px;
}

.ai-panel__module-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.ai-panel__select {
  min-width: 140px;
  padding: 8px 10px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--surface);
  font-size: 13px;
}

.dayun-narrative {
  margin-top: 14px;
  padding: 12px 14px;
  border-radius: 10px;
  background: var(--bg-muted, #faf8f5);
}

.dayun-narrative h3 {
  margin: 0 0 8px;
  font-size: 14px;
  color: var(--brand-ink);
}

.dayun-narrative p {
  margin: 0;
  font-size: 13px;
  line-height: 1.7;
  color: var(--text-2);
}

.dayun-detail {
  margin-top: 14px;
  padding: 12px 14px;
  border-radius: 10px;
  background: var(--bg-muted, #faf8f5);
}

.dayun-detail h3 {
  margin: 0 0 8px;
  font-size: 14px;
  color: var(--brand-ink);
}

.dayun-detail__engine {
  margin: 0 0 6px;
  font-size: 13px;
  color: var(--brand-ink);
  line-height: 1.65;
}

.dayun-detail__heuristic {
  margin: 0 0 4px;
  font-size: 12px;
  color: var(--text-2);
  line-height: 1.6;
}

.dayun-detail__narrative {
  margin: 8px 0 0;
  font-size: 13px;
  line-height: 1.75;
  color: var(--text-2);
}

.hint {
  margin: 8px 0 0;
  font-size: 12px;
  color: var(--text-3);
}

.report-dayun-error {
  margin: 8px 0 12px;
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  background: var(--surface);
  border: 1px solid var(--border);
  border-left: 3px solid var(--brand-cinnabar);
  color: var(--brand-ink);
  font-size: 13px;
}

@media (max-width: 800px) {
  .report-layout {
    grid-template-columns: 1fr;
  }

  .report-body {
    padding: 16px;
  }

  .report-table {
    display: block;
    width: 100%;
    overflow-x: auto;
    max-width: 100%;
  }
}

@media print {
  .no-print {
    display: none !important;
  }

  .report-body {
    box-shadow: none;
    border: none;
    padding: 0;
  }

  .report-volume {
    display: grid !important;
    gap: 12px;
    break-inside: avoid;
    page-break-inside: avoid;
    page-break-after: always;
  }

  .report-volume:last-child {
    page-break-after: auto;
  }

  .report-embed {
    break-inside: avoid;
    page-break-inside: avoid;
  }
}
</style>
