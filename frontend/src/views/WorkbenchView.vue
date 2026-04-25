<script setup lang="ts">
/**
 * WorkbenchView.vue — CRM 式命理工作台
 * 布局：案例列表(320px) | 案例详情+命盘(1fr)
 * 左侧导航已迁移到 AppSidebar.vue
 */
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useReportStore } from '@/stores/report'
import { useAiStore } from '@/stores/ai'
import { useUiStore } from '@/stores/ui'
import { useNavStore } from '@/stores/nav'
import { useProfileStore } from '@/stores/profile'
import type { CaseOut } from '@/api/report'
import { computeFullBazi, computeZiwei, createCase, updateCase, deleteCase as deleteCaseApi, createShareToken } from '@/api/report'
import { exportCaseJson, exportCasePdf, downloadBlob } from '@/api/export'
import { listSnapshots } from '@/api/snapshots'
import type { SnapshotOut } from '@/api/snapshots'
import { getJieqi, type JieqiItemOut } from '@/api/bazi'
import type { ZiweiResponse } from '@/api/ziwei'
import { getWesternChart } from '@/api/western'
import { getCities, type CityModel } from '@/api/static-data'
import { CANG_GAN, NAYIN_MAP, ZODIAC_MAP } from '@/data/ganzhi'
import WorkbenchCaseList from '@/components/workbench/WorkbenchCaseList.vue'
import WorkbenchGuideCard from '@/components/workbench/WorkbenchGuideCard.vue'
import WorkbenchInfoBar from '@/components/workbench/WorkbenchInfoBar.vue'
import WorkbenchBaziSummary from '@/components/workbench/WorkbenchBaziSummary.vue'
import WorkbenchBaziIndicators from '@/components/workbench/WorkbenchBaziIndicators.vue'
import WorkbenchBaziOverviewPanels from '@/components/workbench/WorkbenchBaziOverviewPanels.vue'
import WorkbenchBaziChart from '@/components/workbench/WorkbenchBaziChart.vue'
import WorkbenchBaziDayunTimeline from '@/components/workbench/WorkbenchBaziDayunTimeline.vue'
import WorkbenchBaziLiunianGrid from '@/components/workbench/WorkbenchBaziLiunianGrid.vue'
import WorkbenchBaziLiuyueHeatmap from '@/components/workbench/WorkbenchBaziLiuyueHeatmap.vue'
import WorkbenchBaziInsights from '@/components/workbench/WorkbenchBaziInsights.vue'
import WorkbenchStateBlock from '@/components/workbench/WorkbenchStateBlock.vue'
import WorkbenchZiweiSummary from '@/components/workbench/WorkbenchZiweiSummary.vue'
import WorkbenchDualDayunAxis from '@/components/workbench/WorkbenchDualDayunAxis.vue'
import WorkbenchZiweiSelectors from '@/components/workbench/WorkbenchZiweiSelectors.vue'
import WorkbenchZiweiFocus from '@/components/workbench/WorkbenchZiweiFocus.vue'
import WorkbenchZiweiAdvice from '@/components/workbench/WorkbenchZiweiAdvice.vue'
import WorkbenchZiweiOverview from '@/components/workbench/WorkbenchZiweiOverview.vue'

const router     = useRouter()
const store      = useReportStore()
const ai         = useAiStore()
const ui         = useUiStore()
const nav        = useNavStore()
const profile    = useProfileStore()

const PROFILE_SYNC_TAG = '个人信息同步'
const PROFILE_SYNC_MARK = '[PROFILE_SYNC]'

// ─── 左侧导航菜单 ───────────────────────────────────────────────
// NAV_ITEMS 和 QUICK_ACTIONS 已迁移到 AppSidebar.vue

const selectedId = ref<string | null>(null)
const caseDetail = ref<CaseOut | null>(null)
const searchQ = ref('')
const localBazi = ref<any | null>(null)
const localZiwei = ref<ZiweiResponse | null>(null)
const baziLoading = ref(false)
const ziweiLoading = ref(false)
const auxLoading = ref(false)
const baziError = ref<string | null>(null)
const ziweiError = ref<string | null>(null)
const simpleView = ref(true)
const showNewbieGuide = ref(true)
const currentGuideStep = ref(1)

const jieqiByCaseId = ref<Record<string, JieqiItemOut[] | null>>({})
const lunarByCaseId = ref<Record<string, { date: string; text: string } | null>>({})
const westernAuxByCaseId = ref<Record<string, any | null | undefined>>({})

const filteredList = computed(() => {
  const source = store.caseList ?? []
  const query = searchQ.value.trim().toLowerCase()
  if (!query) return source
  return source.filter((item) => {
    const text = [
      item.name,
      item.city,
      item.tags,
      item.notes,
      item.birth_dt_local,
    ]
      .filter(Boolean)
      .join(' ')
      .toLowerCase()
    return text.includes(query)
  })
})

let cachedCities: CityModel[] | null = null

function isZiweiSectionId(sectionId: string | null | undefined): boolean {
  return !!sectionId && sectionId.startsWith('ziwei-')
}

function isBaziSection(sectionId: string | null | undefined): boolean {
  return !!sectionId && sectionId.startsWith('bazi-')
}

const isZiweiSection = computed(() => isZiweiSectionId(nav.currentSectionId))

function normalizeLocalIso(value: string | null | undefined): string {
  if (!value) return ''
  const trimmed = value.trim().replace(/\s+/, 'T')
  if (!trimmed) return ''
  if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(trimmed)) return `${trimmed}:00`
  return trimmed
}

function parseBirthLocal(c: CaseOut): { year: number; month: number; day: number; hour: number; minute: number } | null {
  const normalized = normalizeLocalIso(c.birth_dt_local)
  if (normalized && normalized.includes('T')) {
    const [datePart, timePart] = normalized.split('T')
    const [year, month, day] = datePart.split('-').map(Number)
    const [hour, minute] = (timePart ?? '').split(':').map(Number)
    if ([year, month, day, hour, minute].every(v => Number.isFinite(v))) {
      return { year, month, day, hour, minute }
    }
  }

  const raw = (c.birth_dt_local ?? '').trim()
  const matched = raw.match(/(\d{4})-(\d{1,2})-(\d{1,2})(?:\D+(\d{1,2}):(\d{1,2}))?/) 
  if (!matched) return null

  const year = Number(matched[1])
  const month = Number(matched[2])
  const day = Number(matched[3])
  const hour = Number(matched[4] ?? '12')
  const minute = Number(matched[5] ?? '0')
  if ([year, month, day, hour, minute].some(v => !Number.isFinite(v))) return null
  return { year, month, day, hour, minute }
}

function toZiweiGender(gender: string | null | undefined): '男' | '女' {
  return gender === 'female' ? '女' : '男'
}

async function ensureCityGeoForCase(c: CaseOut): Promise<void> {
  if (Number.isFinite(c.lon) && c.lon > 0) return
  if (!c.city) return
  try {
    if (!cachedCities) cachedCities = await getCities()
    const city = cachedCities.find(item => item.name === c.city)
    if (!city) return
    c.lon = Number(city.lng)
  } catch (_error) {
  }
}

async function ensureJieqiForCase(c: CaseOut): Promise<void> {
  if (jieqiByCaseId.value[c.id] !== undefined) return
  try {
    const year = Number(c.birth_dt_local?.slice(0, 4))
    if (!year || Number.isNaN(year)) {
      jieqiByCaseId.value = { ...jieqiByCaseId.value, [c.id]: null }
      return
    }
    const rsp = await getJieqi(year)
    jieqiByCaseId.value = { ...jieqiByCaseId.value, [c.id]: rsp.items ?? null }
  } catch (_error) {
    jieqiByCaseId.value = { ...jieqiByCaseId.value, [c.id]: null }
  }
}

async function ensureLunarForCase(c: CaseOut): Promise<void> {
  if (lunarByCaseId.value[c.id] !== undefined) return
  try {
    const parsed = parseBirthLocal(c)
    if (!parsed) {
      lunarByCaseId.value = { ...lunarByCaseId.value, [c.id]: null }
      return
    }
    const date = new Date(parsed.year, parsed.month - 1, parsed.day, parsed.hour, parsed.minute)
    const text = new Intl.DateTimeFormat('zh-CN-u-ca-chinese', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    }).format(date)
    lunarByCaseId.value = {
      ...lunarByCaseId.value,
      [c.id]: { date: `${parsed.year}-${parsed.month}-${parsed.day}`, text },
    }
  } catch (_error) {
    lunarByCaseId.value = { ...lunarByCaseId.value, [c.id]: null }
  }
}

function summarizeLongitudes(values: Record<string, number>, keys: string[]): string {
  return keys
    .filter(key => typeof values?.[key] === 'number')
    .map(key => `${key} ${values[key].toFixed(1)}°`)
    .join('，')
}

function getMoonPhaseText(sunLongitude: number, moonLongitude: number): string {
  const delta = ((moonLongitude - sunLongitude) % 360 + 360) % 360
  if (delta < 22.5 || delta >= 337.5) return '新月'
  if (delta < 67.5) return '娥眉月'
  if (delta < 112.5) return '上弦月'
  if (delta < 157.5) return '盈凸月'
  if (delta < 202.5) return '满月'
  if (delta < 247.5) return '亏凸月'
  if (delta < 292.5) return '下弦月'
  return '残月'
}

async function ensureWesternAuxForCase(c: CaseOut): Promise<void> {
  if (westernAuxByCaseId.value[c.id] !== undefined) return
  try {
    const parsed = parseBirthLocal(c)
    if (!parsed) throw new Error('invalid birth_dt_local')
    const dt = `${parsed.year.toString().padStart(4, '0')}-${String(parsed.month).padStart(2, '0')}-${String(parsed.day).padStart(2, '0')}T${String(parsed.hour).padStart(2, '0')}:${String(parsed.minute).padStart(2, '0')}:00`
    const west = await getWesternChart({
      dt,
      lat: 31.2304,
      lon: c.lon,
      tz: c.tz,
    })

    const cnByEn: Record<string, string> = {
      Sun: '太阳', Moon: '月亮', Mercury: '水星', Venus: '金星', Mars: '火星',
      Jupiter: '木星', Saturn: '土星', Uranus: '天王星', Neptune: '海王星', Pluto: '冥王星',
      Earth: '地球',
    }

    const topPlanets = (west.planets ?? [])
      .slice(0, 5)
      .map(item => `${item.name_cn} ${item.sign_cn}${item.degree_str}`)
      .join('；')

    const sun = (west.planets ?? []).find(item => item.name_en === 'Sun')
    const moon = (west.planets ?? []).find(item => item.name_en === 'Moon')
    const ascMcSummary = `ASC ${west.ascendant?.sign_cn ?? '—'} ｜ MC ${west.midheaven?.sign_cn ?? '—'}`

    const aspectSummary = (west.aspects ?? [])
      .sort((a, b) => a.orb - b.orb)
      .slice(0, 3)
      .map(a => `${cnByEn[a.planet1] ?? a.planet1}-${cnByEn[a.planet2] ?? a.planet2} ${a.aspect_cn}(${a.orb.toFixed(1)}°)`)
      .join('；')

    const geoSummary = summarizeLongitudes(west.geocentric_longitudes, ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars'])
    const helioSummary = summarizeLongitudes(west.heliocentric_longitudes, ['Earth', 'Mercury', 'Venus', 'Mars'])

    westernAuxByCaseId.value = {
      ...westernAuxByCaseId.value,
      [c.id]: {
        julianDay: west.julian_day,
        moonPhase: sun && moon ? getMoonPhaseText(sun.longitude, moon.longitude) : '待接入（无法读取日月黄经）',
        planetSummary: topPlanets || '—',
        ascMcSummary,
        coordinateSummary: `地心黄经：${geoSummary} ｜ 日心黄经：${helioSummary}`,
        aspectSummary: aspectSummary || '—',
      },
    }
  } catch (_error) {
    westernAuxByCaseId.value = { ...westernAuxByCaseId.value, [c.id]: null }
  }
}

async function loadBaziForCase(c: CaseOut) {
  baziLoading.value = true
  auxLoading.value  = false
  baziError.value   = null
  localBazi.value   = null
  try {
    await ensureCityGeoForCase(c)
    const parsed = parseBirthLocal(c)
    if (!parsed) throw new Error('出生时间格式无效')
    const y = String(parsed.year).padStart(4, '0')
    const m = String(parsed.month).padStart(2, '0')
    const d = String(parsed.day).padStart(2, '0')
    const hh = String(parsed.hour).padStart(2, '0')
    const mm = String(parsed.minute).padStart(2, '0')
    const dt = `${y}-${m}-${d}T${hh}:${mm}:00`
    const yr  = Number(new Date().getFullYear())
    const years = Array.from({ length: 16 }, (_, i) => yr - 5 + i)
    const result = await computeFullBazi({
      dt, lon: c.lon, tz: c.tz,
      mode: 'dual',
      solar_time_enabled: c.solar_time_enabled,
      liunian_years: years,
    })
    localBazi.value = result
  } catch (e: unknown) {
    console.error('[WB] loadBaziForCase 捕获异常:', e)
    baziError.value = (e as { response?: { data?: { detail?: string } } })
      .response?.data?.detail ?? '八字计算失败'
    return
  } finally {
    baziLoading.value = false
  }
  // bazi 已显示，并行拉取辅助数据（节气 / 农历 / 西方星盘）
  auxLoading.value = true
  try {
    await Promise.all([ensureJieqiForCase(c), ensureLunarForCase(c), ensureWesternAuxForCase(c)])
  } finally {
    auxLoading.value = false
  }
}

async function loadZiweiForCase(c: CaseOut) {
  ziweiLoading.value = true
  ziweiError.value = null
  localZiwei.value = null
  try {
    await ensureCityGeoForCase(c)
    const parsed = parseBirthLocal(c)
    if (!parsed) throw new Error('出生时间格式无效')
    localZiwei.value = await computeZiwei({
      ...parsed,
      gender: toZiweiGender(c.gender),
      liunian_year: CURRENT_YEAR,
      longitude: c.lon,
      template_version: 'standard',
    })
  } catch (e: unknown) {
    ziweiError.value = (e as { response?: { data?: { detail?: string } }; message?: string })
      .response?.data?.detail ?? (e as { message?: string }).message ?? '紫微计算失败'
  } finally {
    ziweiLoading.value = false
  }
}

async function reloadCurrentCase() {
  if (!caseDetail.value) return
  if (isZiweiSectionId(nav.currentSectionId)) {
    await Promise.all([loadBaziForCase(caseDetail.value), loadZiweiForCase(caseDetail.value)])
    return
  }
  await loadBaziForCase(caseDetail.value)
}

function toggleSimpleView() {
  simpleView.value = !simpleView.value
  try {
    localStorage.setItem('workbench:simple-view', simpleView.value ? '1' : '0')
  } catch (_error) {
  }
}

function closeNewbieGuide() {
  showNewbieGuide.value = false
  try {
    localStorage.setItem('workbench:newbie-guide', '0')
  } catch (_error) {
  }
}

function flashGuideTarget(el: Element | null) {
  if (!(el instanceof HTMLElement)) return
  el.classList.remove('wb-guide-focus-target')
  el.scrollIntoView({ behavior: 'smooth', block: 'center' })
  requestAnimationFrame(() => {
    el.classList.add('wb-guide-focus-target')
    setTimeout(() => el.classList.remove('wb-guide-focus-target'), 1800)
  })
}

let guideDemoTimers: ReturnType<typeof setTimeout>[] = []

function clearGuideDemoTimers() {
  guideDemoTimers.forEach(timer => clearTimeout(timer))
  guideDemoTimers = []
}

function focusGuideStep(step: number) {
  currentGuideStep.value = Math.min(3, Math.max(1, step))
  const root = document.querySelector('.wb-detail')
  if (!root) return

  if (step === 1) {
    flashGuideTarget(root.querySelector('.wb-chart-summary'))
    return
  }

  if (step === 2) {
    if (isZiweiSection.value) {
      flashGuideTarget(root.querySelector('.zw-layout'))
    } else {
      flashGuideTarget(root.querySelector('.wb-pillar-table-wrap'))
    }
    return
  }

  flashGuideTarget(root.querySelector('.wb-info-actions'))
}

function goPrevGuideStep() {
  if (currentGuideStep.value <= 1) return
  focusGuideStep(currentGuideStep.value - 1)
}

function goNextGuideStep() {
  if (currentGuideStep.value >= 3) return
  focusGuideStep(currentGuideStep.value + 1)
}

function playGuideDemo() {
  clearGuideDemoTimers()
  currentGuideStep.value = 1
  ;[1, 2, 3].forEach((step, idx) => {
    const timer = setTimeout(() => focusGuideStep(step), idx * 1100)
    guideDemoTimers.push(timer)
  })
}

const guideProgressPercent = computed(() => `${(currentGuideStep.value / 3) * 100}%`)

const newbieGuideSteps = computed(() => {
  if (isZiweiSection.value) {
    return [
      {
        title: '先看哪里',
        desc: '先看顶部四张速览卡：命宫/身宫、五行局、当前大限与本月流月。先建立全局判断。',
      },
      {
        title: '再点哪里',
        desc: '再点“十二宫与主星”里的任一宫位，右侧会展开该宫主星、对宫、四化飞出/流入关系。',
      },
      {
        title: '最后做什么',
        desc: '最后用右上“重算/完整报告书/PDF”输出结论；不确定时切到“完整视图”补看细节。',
      },
    ]
  }
  return [
    {
      title: '先看哪里',
      desc: '先看顶部四张速览卡：当前大运、当年流年、本月流月、五行平衡分。先抓主线。',
    },
    {
      title: '再点哪里',
      desc: '再点“四柱表”的年/月/日/时柱，查看该柱藏干、纳音和神煞；再看大运与流年时间轴。',
    },
    {
      title: '最后做什么',
      desc: '最后根据建议执行“重算/完整报告书/PDF导出”；想深挖时切到“完整视图”。',
    },
  ]
})

// ─── 选择案例 ────────────────────────────────────────────────────
async function selectCase(c: CaseOut) {
  if (selectedId.value === c.id) {
    return
  }
  selectedId.value = c.id
  caseDetail.value = c
  // 立即绑定案例到 AI store（使 AppRightPanel 快捷模板可用）
  ai.setCurrentCase(c.id)
  localZiwei.value = null
  ziweiError.value = null
  selectedZiweiPalaceName.value = null
  selectedZiweiDayunIndex.value = null
  selectedZiweiLiuyueMonth.value = new Date().getMonth() + 1
  selectedIndicatorShensha.value = null
  if (isZiweiSectionId(nav.currentSectionId)) {
    await Promise.all([loadBaziForCase(c), loadZiweiForCase(c)])
  } else {
    await loadBaziForCase(c)
  }
  // 八字计算完成后更新 chart_hash（用 request_id 关联草稿存档）
  if (localBazi.value) {
    ai.setCurrentCase(c.id, localBazi.value.request_id)
  }
}

function normalizeBirthMinute(value: string | null | undefined): string {
  if (!value) return ''
  const raw = value.trim().replace(' ', 'T')
  if (!raw) return ''
  return raw.length >= 16 ? raw.slice(0, 16) : raw
}

function buildProfileCaseName(): string {
  const surname = (profile.surname || '').trim()
  if (surname) return `${surname}氏档案`
  return '个人信息档案'
}

function isProfileSyncedCase(c: CaseOut): boolean {
  const tags = c.tags ?? []
  return tags.includes(PROFILE_SYNC_TAG) || (c.notes ?? '').includes(PROFILE_SYNC_MARK)
}

function isCaseMatchingProfile(c: CaseOut): boolean {
  const profileBirth = normalizeBirthMinute(profile.birthDt)
  const caseBirth = normalizeBirthMinute(c.birth_dt_local)
  const caseLon = Number(c.lon)
  const profileLon = Number(profile.lon)
  const profileGender = profile.gender || null
  return (
    caseBirth === profileBirth
    && c.tz === profile.tz
    && Number.isFinite(caseLon)
    && Number.isFinite(profileLon)
    && Math.abs(caseLon - profileLon) < 0.001
    && (c.gender ?? null) === profileGender
    && (c.city ?? '') === (profile.cityName ?? '')
    && c.solar_time_enabled === profile.solarTime
  )
}

async function ensureProfileSyncedCase(): Promise<CaseOut | null> {
  if (!profile.saved) return null
  if (!profile.birthDt || profile.lon === undefined || !profile.tz) return null

  const existing = (store.caseList ?? []).find(c => isProfileSyncedCase(c) && isCaseMatchingProfile(c))
  if (existing) return existing

  const created = await createCase({
    name: buildProfileCaseName(),
    birth_dt_local: normalizeBirthMinute(profile.birthDt) + ':00',
    tz: profile.tz,
    lon: Number(profile.lon),
    gender: profile.gender || null,
    city: profile.cityName || null,
    solar_time_enabled: profile.solarTime,
    notes: `${PROFILE_SYNC_MARK} 自动由“个人信息”同步`,
    tags: [PROFILE_SYNC_TAG],
  })
  return created
}

async function syncProfileToWorkbenchCase(): Promise<void> {
  if (!profile.saved || !profile.birthDt || profile.lon === undefined) {
    alert('请先在“个人信息”页保存完整出生信息')
    router.push('/profile')
    return
  }
  try {
    const profileCase = await ensureProfileSyncedCase()
    if (!profileCase) {
      alert('个人信息同步失败，请稍后重试')
      return
    }
    await store.loadCaseList()
    const matched = (store.caseList ?? []).find(c => c.id === profileCase.id)
    if (matched) {
      await selectCase(matched)
      nav.selectSection('bazi-birth')
      ui.rightPanelExpanded = true
      return
    }
    alert('同步案例创建成功，但未在列表中找到，请刷新页面重试')
  } catch (_error) {
    alert('同步个人信息到客户档案失败')
  }
}

watch(() => nav.currentSectionId, async (sectionId, prevSectionId) => {
  if (!caseDetail.value || sectionId === prevSectionId) return
  if (isZiweiSectionId(sectionId) && !localZiwei.value) {
    await loadZiweiForCase(caseDetail.value)
    return
  }
  if (isBaziSection(sectionId) && !localBazi.value) {
    await loadBaziForCase(caseDetail.value)
  }
})

onMounted(async () => {
  try {
    simpleView.value = localStorage.getItem('workbench:simple-view') !== '0'
  } catch (_error) {
    simpleView.value = true
  }
  try {
    showNewbieGuide.value = localStorage.getItem('workbench:newbie-guide') !== '0'
  } catch (_error) {
    showNewbieGuide.value = true
  }

  await store.loadCaseList()

  // 个人信息 → 客户档案自动同步：优先创建/选中“个人信息档案”
  try {
    const profileCase = await ensureProfileSyncedCase()
    if (profileCase) {
      await store.loadCaseList()
      const matched = (store.caseList ?? []).find(c => c.id === profileCase.id)
      if (matched) {
        await selectCase(matched)
      }
    }
  } catch (_error) {
    // ignore sync failure and fall back to default flow
  }
  
  // 自动选中第一个案例，如果列表为空则创建演示案例
  if (store.caseList.length > 0 && !selectedId.value) {
    await selectCase(store.caseList[0])
  } else if (store.caseList.length === 0) {
    // 创建一个默认演示案例用于展示
    try {
      await createCase({
        name: '演示案例',
        birth_dt_local: '2000-01-15T14:30:00',
        tz: 'Asia/Shanghai',
        lon: 116.41,
        gender: 'male',
        city: '北京',
        solar_time_enabled: false,
        notes: '用于演示四柱八字、紫微斗数等功能的默认案例',
      })
      await store.loadCaseList()
      if (store.caseList.length > 0) {
        await selectCase(store.caseList[0])
      }
    } catch (e) {
      console.error('创建演示案例失败:', e)
    }
  }
  
  // workbench 进入时，自动展开右面板并选中四柱第一个小节
  if (!nav.currentSectionId) {
    nav.selectSection('bazi-birth')  // 1.1 生辰数据
    ui.rightPanelExpanded = true
  }
})

onBeforeUnmount(() => {
  clearGuideDemoTimers()
})

// ─── 格式化工具 ──────────────────────────────────────────────────
function fmtDate(dt: string | null): string {
  if (!dt) return '—'
  const [date, time] = dt.split('T')
  const [y, m, d]   = date.split('-')
  const t           = (time ?? '').slice(0, 5)
  return `${y}年${m}月${d}日  ${t}`
}

function genderLabel(g: string | null): string {
  if (g === 'female') return '女'
  if (g === 'male')   return '男'
  return '—'
}

// ─── 五行色 ──────────────────────────────────────────────────────
const WX_COLOR: Record<string, string> = {
  wood:  'var(--wx-wood)',
  fire:  'var(--wx-fire)',
  earth: 'var(--wx-earth)',
  metal: 'var(--wx-metal)',
  water: 'var(--wx-water)',
  木:    'var(--wx-wood)',
  火:    'var(--wx-fire)',
  土:    'var(--wx-earth)',
  金:    'var(--wx-metal)',
}
const STEM_WX: Record<string, string> = {
  甲: '木', 乙: '木',
  丙: '火', 丁: '火',
  戊: '土', 己: '土',
  庚: '金', 辛: '金',
  壬: '水', 癸: '水',
}
const BRANCH_WX: Record<string, string> = {
  子: '水', 丑: '土', 寅: '木', 卯: '木', 辰: '土', 巳: '火',
  午: '火', 未: '土', 申: '金', 酉: '金', 戌: '土', 亥: '水',
}
function wxColor(key: string): string {
  return WX_COLOR[key] ?? 'var(--text-2)'
}
const LUCK_RANK: Record<string, number> = { '吉': 1, '平': 0, '凶': -1 }
// 当前年份
const CURRENT_YEAR = new Date().getFullYear()
function trendMeta(diff: number | null | undefined): { text: string; cls: 'up' | 'down' | 'flat' } {
  if (diff == null || Number.isNaN(diff) || diff === 0) return { text: '→ 持平', cls: 'flat' }
  if (diff > 0) return { text: `↑ ${Math.abs(diff).toFixed(0)}`, cls: 'up' }
  return { text: `↓ ${Math.abs(diff).toFixed(0)}`, cls: 'down' }
}
function scoreToneClass(score: number | null | undefined): 'c-good' | 'c-warn' | 'c-bad' | '' {
  if (score == null || Number.isNaN(score)) return ''
  if (score >= 80) return 'c-good'
  if (score >= 60) return 'c-warn'
  return 'c-bad'
}
// 大运时间轴显示（前后吃8个大运）
const dayunItems = computed(() => {
  const items = localBazi.value?.dayun?.items ?? []
  return items.slice(0, 8)
})

const currentCaseDayunLabel = computed(() => {
  const current = dayunItems.value.find((item: { start_year?: number }, index: number) => {
    if ((item.start_year ?? 0) > CURRENT_YEAR) return false
    const next = dayunItems.value[index + 1] as { start_year?: number } | undefined
    return !next || (next.start_year ?? Number.MAX_SAFE_INTEGER) > CURRENT_YEAR
  })
  if (!current) return null
  return `${current.stem ?? '—'}${current.branch ?? ''}`
})

// 流年数据（近5年）
const liunianItems = computed(() => {
  const items = localBazi.value?.liunian?.items ?? []
  const idx   = items.findIndex((i: { year: number }) => i.year === CURRENT_YEAR)
  const start = Math.max(0, idx - 2)
  return items.slice(start, start + 5)
})

// 五行得分
const wuxing = computed(() => {
  const s = localBazi.value?.wuxing_score
  if (!s) return []
  return [
    { key: '木', val: s.wood  },
    { key: '火', val: s.fire  },
    { key: '土', val: s.earth },
    { key: '金', val: s.metal },
    { key: '水', val: s.water },
  ]
})
const wuxingMax = computed(() =>
  Math.max(...wuxing.value.map(w => w.val), 1)
)
// 五行雷达图多边形
const wuxingRadarPoints = computed(() => {
  const list = wuxing.value
  if (!list.length) return ''
  const mx = wuxingMax.value
  const cx = 70; const cy = 70; const r = 54
  const toRad = (deg: number) => (deg * Math.PI) / 180
  return list.map((w, i) => {
    const angle = toRad(-90 + (360 / list.length) * i)
    const rv = (w.val / mx) * r
    return `${cx + rv * Math.cos(angle)},${cy + rv * Math.sin(angle)}`
  }).join(' ')
})
const wuxingRadarAxes = computed(() => {
  const list = wuxing.value
  const cx = 70; const cy = 70; const r = 54
  const toRad = (deg: number) => (deg * Math.PI) / 180
  return list.map((w, i) => {
    const angle = toRad(-90 + (360 / list.length) * i)
    const tx = cx + (r + 16) * Math.cos(angle)
    const ty = cy + (r + 16) * Math.sin(angle)
    return { label: w.key, x: tx, y: ty, color: wxColor(w.key) }
  })
})

type LiuyueItem = {
  month: number
  month_ganzhi?: string
  month_dizhi?: string
  luck_level: string
  color_hint?: string
}

type LiunianDetailItem = {
  year: number
  ganzhi?: string
  annual_score?: number
  ten_god?: string
  flow_wuxing?: string
  clash?: string
  domain_forecasts?: Record<string, string>
  tai_sui_relations?: string[]
  clash_pillars?: string[]
  notable_months?: number[]
  optimal_action?: string
  interpretation_text?: string
  inference_tags?: string[]
}

// 十神数据
const B = localBazi
const pillarLabels = ['年柱', '月柱', '日柱', '时柱']
const pillars = computed(() => {
  const p = B.value?.pillars_primary
  const t = B.value?.ten_gods
  if (!p || !t) return []
  const keys = ['year', 'month', 'day', 'hour'] as const
  return keys.map((k, i) => ({
    key: k,
    label:   pillarLabels[i],
    stem:    p[k].stem,
    branch:  p[k].branch,
    shishen: k === 'day' ? '日主' : (t[k] ?? '—'),
    isDay:   k === 'day',
    stemColor:   wxColor(STEM_WX[p[k].stem]   ?? ''),
    branchColor: wxColor(BRANCH_WX[p[k].branch] ?? ''),
  }))
})

// 格局用神
const geju    = computed(() => B.value?.geju)
const yongshen= computed(() => B.value?.yongshen)
const summary = computed(() => B.value?.bazi_summary ?? null)
const strength= computed(() => B.value?.day_master_strength)

// 今年流年解读
const thisYearDetail = computed(() =>
  (B.value?.liunian_detail ?? []).find((d: { year: number }) => d.year === CURRENT_YEAR) ?? null
)
const liunianDetailRows = computed(() => {
  const items = B.value?.liunian_detail ?? []
  if (!items.length) return []
  const idx = items.findIndex((i: { year: number }) => i.year === CURRENT_YEAR)
  const start = Math.max(0, (idx >= 0 ? idx : 0) - 2)
  return items.slice(start, start + 5).map((i: {
    year: number
    ganzhi?: string
    annual_score?: number
    ten_god?: string
    flow_wuxing?: string
    clash?: string
    domain_forecasts?: Record<string, string>
    tai_sui_relations?: string[]
    clash_pillars?: string[]
    notable_months?: number[]
    optimal_action?: string
    interpretation_text?: string
    inference_tags?: string[]
  }) => ({
    year: i.year,
    ganzhi: i.ganzhi ?? '—',
    annualScore: i.annual_score ?? 0,
    tenGod: i.ten_god ?? '',
    flowWuxing: i.flow_wuxing ?? '',
    clash: i.clash ?? '',
    domains: Object.entries(i.domain_forecasts ?? {}).map(([key, val]) => ({ key, val })),
    taiSuiRelations: i.tai_sui_relations ?? [],
    clashPillars: i.clash_pillars ?? [],
    notableMonths: i.notable_months ?? [],
    optimalAction: i.optimal_action ?? '',
    interpretationText: i.interpretation_text ?? '',
    tags: i.inference_tags ?? [],
    isCurrent: i.year === CURRENT_YEAR,
  }))
})
const activeLiunianDetailYear = ref<number | null>(CURRENT_YEAR)
const expandedLiunianDetailYear = computed(() =>
  activeLiunianDetailYear.value
  ?? liunianDetailRows.value.find((i: { isCurrent: boolean }) => i.isCurrent)?.year
  ?? liunianDetailRows.value[0]?.year
  ?? null,
)
const activeLiunianDetail = computed(() =>
  liunianDetailRows.value.find((i: { year: number }) => i.year === expandedLiunianDetailYear.value) ?? null,
)
function toggleLiunianDetail(year: number) {
  activeLiunianDetailYear.value = year
  const detail = liunianDetailRows.value.find((i: { year: number }) => i.year === year)
  if (detail?.year === CURRENT_YEAR && detail.notableMonths.length) {
    if (!detail.notableMonths.includes(activeLiuyueMonth.value ?? -1)) {
      activeLiuyueMonth.value = detail.notableMonths[0] ?? activeLiuyueMonth.value
    }
  }
}
const activeLiuyueMonth = ref<number | null>(new Date().getMonth() + 1)
const activeLiuyueDetail = computed(() => {
  const rows = (B.value?.monthly_fortune ?? []) as LiuyueItem[]
  const currentMonth = new Date().getMonth() + 1
  return rows.find((m: LiuyueItem) => m.month === activeLiuyueMonth.value)
    ?? rows.find((m: LiuyueItem) => m.month === currentMonth)
    ?? rows[0]
    ?? null
})
function selectLiuyue(month: number) {
  activeLiuyueMonth.value = month
}

const LIUYUE_SCORE: Record<string, number> = { '吉': 100, '平': 50, '凶': 0 }
const liuyueHeatmapData = computed(() => {
  const rows = (B.value?.monthly_fortune ?? []) as LiuyueItem[]
  const thisMonth = new Date().getMonth() + 1
  return rows.map((m: LiuyueItem) => {
    const color = m.color_hint
      || (m.luck_level === '吉' ? '#2E8B57' : m.luck_level === '凶' ? '#DC1432' : '#888888')
    const opHex = m.luck_level === '平' ? '18' : '2e'
    return {
      ...m,
      score: LIUYUE_SCORE[m.luck_level] ?? 50,
      heatBar: color,
      heatBg: `${color}${opHex}`,
      isSelected: m.month === activeLiuyueMonth.value,
      isCurrent: m.month === thisMonth,
      isLinked: linkedLiuyueMonths.value.includes(m.month),
    }
  })
})
const liuyueTrendSvg = computed(() => {
  const items = liuyueHeatmapData.value
  if (items.length < 2) return null
  const w = 360, h = 28, pad = 6
  const n = items.length
  const pts = items.map((m, i: number) => ({
    x: pad + ((w - pad * 2) / (n - 1)) * i,
    y: pad + (h - pad * 2) * (1 - (LIUYUE_SCORE[m.luck_level] ?? 50) / 100),
    color: m.heatBar,
    label: `${m.month}月 ${m.luck_level}`,
  }))
  return { w, h, pts }
})
const linkedLiuyueMonths = computed(() =>
  activeLiunianDetail.value?.year === CURRENT_YEAR ? activeLiunianDetail.value.notableMonths : [],
)
function selectLiunianMonth(year: number, month: number) {
  activeLiunianDetailYear.value = year
  if (year === CURRENT_YEAR) {
    activeLiuyueMonth.value = month
  }
}
const dayunTimelineItems = computed(() =>
  dayunItems.value.map((d: { stem?: string; branch?: string; start_year?: number; start_age?: number; ten_god?: string; flow_wuxing?: string; wealth_hint?: string; love_hint?: string; health_hint?: string; narrative?: string }, i: number, arr: Array<{ start_year?: number; start_age?: number }>) => {
    const startYear = d.start_year ?? null
    const nextStartYear = arr[i + 1]?.start_year ?? null
    const endYear = nextStartYear ? nextStartYear - 1 : null
    const startAge = d.start_age ?? null
    const nextStartAge = arr[i + 1]?.start_age ?? null
    const endAge = nextStartAge ? nextStartAge - 1 : null
    const isActive = startYear != null && startYear <= CURRENT_YEAR && (endYear == null || endYear >= CURRENT_YEAR)
    const isPast = endYear != null && endYear < CURRENT_YEAR
    const progress = isActive && startYear != null && endYear != null && endYear >= startYear
      ? Math.max(8, Math.min(100, ((CURRENT_YEAR - startYear + 1) / (endYear - startYear + 1)) * 100))
      : isPast ? 100 : 0
    return {
      ...d,
      startYear,
      endYear,
      startAge,
      endAge,
      isActive,
      isPast,
      progress,
      ganzhi: `${d.stem ?? ''}${d.branch ?? ''}` || '—',
      stemColor: wxColor(STEM_WX[d.stem ?? ''] ?? ''),
      branchColor: wxColor(BRANCH_WX[d.branch ?? ''] ?? ''),
    }
  }),
)
const activeDayunStartYear = ref<number | null>(null)
const activeDayunTimelineItem = computed(() =>
  dayunTimelineItems.value.find((i: { startYear: number | null }) => i.startYear === activeDayunStartYear.value)
  ?? dayunTimelineItems.value.find((i: { isActive: boolean }) => i.isActive)
  ?? dayunTimelineItems.value[0]
  ?? null,
)
function selectDayun(startYear: number | null) {
  activeDayunStartYear.value = startYear
}
const liunianTimelineItems = computed(() => {
  const detailMap = new Map<number, LiunianDetailItem>(((B.value?.liunian_detail ?? []) as LiunianDetailItem[]).map((item: LiunianDetailItem) => [item.year, item]))
  return liunianItems.value.map((ly: { year: number; stem: string; branch: string; ten_god?: string; clash?: string }) => {
    const detail = detailMap.get(ly.year)
    return {
      ...ly,
      annualScore: detail?.annual_score ?? null,
      clash: detail?.clash ?? ly.clash ?? '',
      optimalAction: detail?.optimal_action ?? '',
      tags: detail?.inference_tags ?? [],
      isCurrent: ly.year === CURRENT_YEAR,
      stemColor: wxColor(STEM_WX[ly.stem] ?? ''),
      branchColor: wxColor(BRANCH_WX[ly.branch] ?? ''),
    }
  })
})
// 流年分数走势 Sparkline
const liunianSparkline = computed(() => {
  const scores = liunianTimelineItems.value
    .map((i: { annualScore: number | null }) => i.annualScore)
    .filter((s: number | null): s is number => s != null)
  if (scores.length < 2) return null
  const w = 220; const h = 36; const pad = 4
  const minS = Math.min(...scores); const maxS = Math.max(...scores, minS + 1)
  const pts = scores.map((s: number, i: number) => ({
    x: pad + ((w - pad * 2) / (scores.length - 1)) * i,
    y: pad + (h - pad * 2) * (1 - (s - minS) / (maxS - minS)),
    s,
  }))
  const line = pts.map((p: { x: number; y: number }, i: number) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ')
  const area = `${line} L ${pts[pts.length - 1].x.toFixed(1)} ${h} L ${pts[0].x.toFixed(1)} ${h} Z`
  return { w, h, pts, line, area }
})
const activeLiunianTimelineItem = computed(() =>
  liunianTimelineItems.value.find((i: { year: number }) => i.year === expandedLiunianDetailYear.value)
  ?? liunianTimelineItems.value.find((i: { isCurrent: boolean }) => i.isCurrent)
  ?? liunianTimelineItems.value[0]
  ?? null,
)
const activeLiunianDayunInfo = computed(() => {
  const year = expandedLiunianDetailYear.value
  if (!year) return null
  return dayunTimelineItems.value.find((d: { startYear: number | null; endYear: number | null }) =>
    d.startYear != null && d.startYear <= year && (d.endYear == null || d.endYear >= year),
  ) ?? null
})

// 顶部命盘速览
const chartSummaryCards = computed(() => {
  if (!B.value) return null
  const dy = B.value.dayun
  const nowYear = CURRENT_YEAR
  // 当前大运
  const currentDayun = dy?.items?.find((d: { start_year?: number; end_year?: number }) =>
    (d.start_year ?? 0) <= nowYear && (d.end_year ?? 9999) >= nowYear
  ) ?? dy?.items?.[0]
  const dayunGz = currentDayun ? `${currentDayun.stem ?? ''}${currentDayun.branch ?? ''}` : '—'
  const dayunYearsLeft = currentDayun?.end_year ? currentDayun.end_year - nowYear : null

  // 当前流年
  const lyItem = liunianItems.value.find((i: { year: number }) => i.year === nowYear)
  const lyGz   = lyItem ? `${lyItem.stem ?? ''}${lyItem.branch ?? ''}` : '—'
  const lyShishen = lyItem?.ten_god ?? ''
  const lyDetail = (B.value.liunian_detail ?? []).find((i: { year?: number }) => i.year === nowYear)
  const prevLyDetail = (B.value.liunian_detail ?? []).find((i: { year?: number }) => i.year === nowYear - 1)
  const lyAnnualScore = lyDetail?.annual_score ?? null
  const lyTrend = trendMeta(
    lyAnnualScore != null && prevLyDetail?.annual_score != null
      ? lyAnnualScore - prevLyDetail.annual_score
      : null,
  )

  // 当月流月
  const nowMonth = new Date().getMonth() + 1
  const mfList = B.value.monthly_fortune ?? []
  const mfItem = mfList.find((m: { month: number }) => m.month === nowMonth)
  const prevMfItem = mfList.find((m: { month: number }) => m.month === nowMonth - 1)
  const lyueGz = mfItem ? (mfItem.month_ganzhi ?? mfItem.month_dizhi ?? '—') : '—'
  const lyueLuck = mfItem?.luck_level ?? ''
  const lyueTrend = trendMeta(
    mfItem && prevMfItem
      ? (LUCK_RANK[mfItem.luck_level] ?? 0) - (LUCK_RANK[prevMfItem.luck_level] ?? 0)
      : null,
  )

  // 五行平衡
  const wscore = B.value.wuxing_score
  const balanceScore = B.value.wuxing_balance_score
  const balanceText  = B.value.balance_advice ?? ''
  const weakList  = (B.value.wuxing_weak  ?? []).join('、') || '无'
  const strongList= (B.value.wuxing_strong?? []).join('、') || '无'
  const balanceTone = scoreToneClass(balanceScore)

  return {
    dayunGz, dayunYearsLeft,
    lyGz, lyShishen, lyAnnualScore, lyTrend,
    lyueGz, lyueLuck, lyueTrend,
    balanceScore, balanceText, weakList, strongList, wscore, balanceTone,
  }
})

const SHENSHA_BRIEF_MAP: Record<string, { meaning: string; goodAdvice: string; badAdvice: string }> = {
  天乙贵人: { meaning: '主遇贵扶持、逢难有解。', goodAdvice: '适合推进合作、求助权威资源。', badAdvice: '避免依赖他人，重要决策仍需自证。' },
  文昌贵人: { meaning: '主学习、考试、文书表达。', goodAdvice: '适合考试申报、写作汇报与复盘。', badAdvice: '避免文书疏漏，关键条款需复核。' },
  桃花: { meaning: '主人缘、社交与情感活跃。', goodAdvice: '适合拓展关系与公共沟通。', badAdvice: '边界优先，谨防情绪与关系消耗。' },
  驿马: { meaning: '主变动、奔波、出行迁移。', goodAdvice: '适合外出拓展、跑动项目。', badAdvice: '控制节奏，避免频繁变动导致失焦。' },
  羊刃: { meaning: '主刚烈与冲劲，易激进。', goodAdvice: '可用于攻坚，但需设风险阈值。', badAdvice: '避免硬碰硬，先稳后动。' },
  劫煞: { meaning: '主争夺与损耗风险。', goodAdvice: '加强边界管理与资源盘点。', badAdvice: '避免高杠杆与冲动投入。' },
  灾煞: { meaning: '主突发阻滞与杂务干扰。', goodAdvice: '预留缓冲时间和备选方案。', badAdvice: '不宜冒险推进高不确定事项。' },
  白虎: { meaning: '主冲突、伤灾与高压事件。', goodAdvice: '流程合规、风险检查前置。', badAdvice: '减少对抗情境与危险场景暴露。' },
}

const selectedIndicatorShensha = ref<string | null>(null)
const baziKeyIndicators = computed(() => {
  if (!B.value) return null
  const geju = B.value.geju
  const yongshen = B.value.yongshen
  const shensha: Array<{ is_beneficial: boolean; name?: string; pillar?: string }> = B.value.shensha ?? []
  const topGoodShensha = shensha.filter(s => s.is_beneficial).slice(0, 2)
  const topBadShensha = shensha.filter(s => !s.is_beneficial).slice(0, 2)
  return {
    geju: (geju?.name ?? '') as string,
    gejuLevel: (geju?.level ?? '') as string,
    yongshen: (yongshen?.god_element ?? yongshen?.element ?? '') as string,
    yongshenStar: (yongshen?.star ?? yongshen?.name ?? '') as string,
    topGoodShensha,
    topBadShensha,
    weakList: ((B.value.wuxing_weak ?? []) as string[]).join('、') || '',
  }
})
const indicatorShenshaItems = computed(() => {
  const indicators = baziKeyIndicators.value
  if (!indicators) return [] as Array<{ key: string; name: string; pillar?: string; isBeneficial: boolean; meaning: string; advice: string }>
  const all = [
    ...indicators.topGoodShensha.map(s => ({ ...s, isBeneficial: true })),
    ...indicators.topBadShensha.map(s => ({ ...s, isBeneficial: false })),
  ]
  return all
    .filter(s => !!s.name)
    .map(s => {
      const name = s.name as string
      const brief = SHENSHA_BRIEF_MAP[name]
      return {
        key: `${s.isBeneficial ? 'good' : 'bad'}-${name}`,
        name,
        pillar: s.pillar,
        isBeneficial: s.isBeneficial,
        meaning: brief?.meaning ?? '该神煞用于补充判断气机倾向，需结合四柱与大运流年综合解读。',
        advice: s.isBeneficial
          ? (brief?.goodAdvice ?? '可顺势借力，在优势场景放大收益。')
          : (brief?.badAdvice ?? '建议先控风险与节奏，再推进关键动作。'),
      }
    })
})
const activeIndicatorShensha = computed(() => {
  const items = indicatorShenshaItems.value
  if (!items.length) return null
  return items.find(s => s.key === selectedIndicatorShensha.value) ?? items[0]
})
function toggleIndicatorShensha(itemKey: string) {
  selectedIndicatorShensha.value = selectedIndicatorShensha.value === itemKey ? null : itemKey
}

// ── 双盘大运对照时间轴 ─────────────────────────────────────────
const dualDayunAxis = computed(() => {
  const baziItems = dayunTimelineItems.value
  const zwItems = (localZiwei.value?.dayun?.items ?? []).map((item, idx, arr) => ({
    ...item,
    startYear: item.start_year ?? null,
    endYear: arr[idx + 1]?.start_year ? arr[idx + 1].start_year - 1 : null,
    isActive:
      item.start_year != null &&
      item.start_year <= CURRENT_YEAR &&
      (arr[idx + 1]?.start_year == null || arr[idx + 1].start_year > CURRENT_YEAR),
    isPast:
      arr[idx + 1]?.start_year != null && arr[idx + 1].start_year - 1 < CURRENT_YEAR &&
      !(item.start_year != null && item.start_year <= CURRENT_YEAR &&
        (arr[idx + 1]?.start_year == null || arr[idx + 1].start_year > CURRENT_YEAR)),
  }))
  if (!baziItems.length && !zwItems.length) return null
  // 计算显示年份范围
  const allStarts = [
    ...baziItems.map((d: (typeof baziItems)[number]) => d.startYear ?? 0),
    ...zwItems.map((d: (typeof zwItems)[number]) => d.startYear ?? 0),
  ].filter(Boolean)
  const minYear = Math.max(Math.min(...allStarts), CURRENT_YEAR - 20)
  const maxYear = CURRENT_YEAR + 30
  const span = maxYear - minYear || 1
  const pct = (y: number | null) => y == null ? 0 : Math.max(0, Math.min(100, ((y - minYear) / span) * 100))
  const baziSegments = baziItems
    .filter((d: (typeof baziItems)[number]) => d.startYear != null && (d.endYear == null || d.endYear >= minYear))
    .map((d: (typeof baziItems)[number]) => ({
      label: d.ganzhi,
      left: pct(d.startYear),
      width: pct(d.endYear != null ? d.endYear + 1 : maxYear) - pct(d.startYear),
      isActive: d.isActive,
      isPast: d.isPast,
      startYear: d.startYear,
      onSelect: () => selectDayun(d.startYear),
    }))
  const zwSegments = zwItems
    .filter((d: (typeof zwItems)[number]) => d.startYear != null && (d.endYear == null || d.endYear >= minYear))
    .map((d: (typeof zwItems)[number]) => ({
      label: d.ganzhi,
      left: pct(d.startYear),
      width: pct(d.endYear != null ? d.endYear + 1 : maxYear) - pct(d.startYear),
      isActive: d.isActive,
      isPast: d.isPast,
      startYear: d.startYear,
      index: d.index,
      onSelect: () => selectZiweiDayun(d.index),
    }))
  const nowPct = pct(CURRENT_YEAR)
  return { baziSegments, zwSegments, nowPct, minYear, maxYear }
})

const ziweiPalaces = computed(() => localZiwei.value?.palaces ?? [])
const selectedZiweiPalaceName = ref<string | null>(null)
const selectedZiweiDayunIndex = ref<number | null>(null)
const selectedZiweiLiuyueMonth = ref<number | null>(new Date().getMonth() + 1)
const activeZiweiPalace = computed(() =>
  ziweiPalaces.value.find(p => p.name === selectedZiweiPalaceName.value)
  ?? ziweiPalaces.value.find(p => p.name.includes('命'))
  ?? ziweiPalaces.value[0]
  ?? null,
)
const currentZiweiDayun = computed(() => {
  const items = localZiwei.value?.dayun?.items ?? []
  return items.find((item, idx) => {
    const nextStartYear = items[idx + 1]?.start_year ?? 9999
    return item.start_year <= CURRENT_YEAR && nextStartYear > CURRENT_YEAR
  }) ?? items[0] ?? null
})
const activeZiweiDayun = computed(() => {
  const items = localZiwei.value?.dayun?.items ?? []
  return items.find(item => item.index === selectedZiweiDayunIndex.value)
    ?? currentZiweiDayun.value
    ?? items[0]
    ?? null
})
const currentZiweiLiuyue = computed(() => {
  const items = localZiwei.value?.liuyue ?? []
  const nowMonth = new Date().getMonth() + 1
  return items.find(item => item.month === nowMonth) ?? items[0] ?? null
})
const activeZiweiLiuyue = computed(() => {
  const items = localZiwei.value?.liuyue ?? []
  return items.find(item => item.month === selectedZiweiLiuyueMonth.value)
    ?? currentZiweiLiuyue.value
    ?? items[0]
    ?? null
})
const ziweiHighlightedPalaceName = computed(() => activeZiweiLiuyue.value?.palace_name ?? '')
const ziweiSummaryCards = computed(() => {
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
const ziweiCaseSummaryText = computed(() => {
  if (!isZiweiSection.value || !localZiwei.value) return ''
  const dayun = activeZiweiDayun.value ?? currentZiweiDayun.value
  const liuyue = activeZiweiLiuyue.value ?? currentZiweiLiuyue.value
  const dayunText = dayun ? `${dayun.ganzhi}(${dayun.start_age}-${dayun.end_age}岁)` : '—'
  const liuyueText = liuyue ? `${liuyue.month_name || `${liuyue.month}月`}${liuyue.month_gz}` : '—'
  return `紫微：${dayunText} ｜ ${liuyueText}`
})
const activeZiweiDayunSummary = computed(() => (
  activeZiweiDayun.value
    ? `${activeZiweiDayun.value.ganzhi} · ${activeZiweiDayun.value.start_age}-${activeZiweiDayun.value.end_age}岁`
    : ''
))
const activeZiweiLiuyueSummary = computed(() => (
  activeZiweiLiuyue.value
    ? `流月落宫：${activeZiweiLiuyue.value.palace_name} ｜ 宫位：${activeZiweiLiuyue.value.life_palace_branch}`
    : ''
))
const baziCaseSummaryLine = computed(() => {
  const c = chartSummaryCards.value
  if (!c) return ''
  const parts: string[] = []
  if (c.dayunGz && c.dayunGz !== '—') parts.push(`大运 ${c.dayunGz}`)
  if (c.lyGz && c.lyGz !== '—') parts.push(`流年 ${c.lyGz}${c.lyShishen ? `·${c.lyShishen}` : ''}`)
  if (c.weakList && c.weakList !== '无') parts.push(`忌 ${c.weakList}`)
  return parts.join(' ｜ ')
})
const activeZiweiRelations = computed(() => {
  const palace = activeZiweiPalace.value
  if (!palace) return null
  const opposite = palace.opposition_name || '—'
  const flyingOutEntries = Object.entries(palace.flying_out ?? {})
    .filter(([, target]) => !!target)
    .map(([transform, target]) => ({ transform, target }))
  const receiving = ziweiPalaces.value
    .flatMap(src => Object.entries(src.flying_out ?? {}).map(([transform, target]) => ({ src: src.name, transform, target })))
    .filter(link => link.target === palace.name)
  return {
    opposite,
    flyingOutEntries,
    receiving,
  }
})
const activeZiweiRelationGraph = computed(() => {
  const palace = activeZiweiPalace.value
  const rel = activeZiweiRelations.value
  if (!palace || !rel) return null

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
  const nodes: Array<{
    id: string
    label: string
    displayLabel: { line1: string; line2: string }
    fullLabel: string
    x: number
    y: number
    kind: 'active' | 'opposite' | 'out' | 'in'
    palaceName?: string
  }> = [
    { id: 'active', label: palace.name, displayLabel: wrapLabel(palace.name, 12), fullLabel: palace.name, x: centerX, y: centerY, kind: 'active', palaceName: palace.name },
  ]
  const links: Array<{
    from: string
    to: string
    label: string
    kind: 'opposite' | 'out' | 'in'
    d: string
    labelX: number
    labelY: number
  }> = []

  if (rel.opposite && rel.opposite !== '—') {
    const node = nodeByAngle('opposite', rel.opposite, 'opposite', innerRadius, 180, rel.opposite)
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
    sorted.forEach((item, idx) => {
      const adaptiveGap = 26 + Math.max(0, Math.min(10, (estimateLabelWidth(item.label) - 30) * 0.12))
      const targetY = Math.max(item.y, prevY + adaptiveGap)
      item.y = Math.min(maxY, targetY)
      prevY = item.y
      const drift = (idx - (sorted.length - 1) / 2) * 3
      if (side === 'right') item.x += drift
      else item.x -= drift
    })
    sorted
      .slice()
      .reverse()
      .forEach((item, idx) => {
        item.y = Math.max(minY, Math.min(item.y, maxY - idx * 4))
      })
    return sorted
  }

  const outAngles = [-58, -20, 18, 56]
  const outNodes: Array<{ id: string; label: string; x: number; y: number; kind: 'out'; palaceName?: string }> = []
  rel.flyingOutEntries.slice(0, 4).forEach((item, idx) => {
    const id = `out-${idx}`
    const widthBoost = Math.min(18, Math.max(0, (estimateLabelWidth(item.target) - 28) * 0.45))
    const angleNudge = item.target.length >= 4 ? (idx % 2 === 0 ? -4 : 4) : 0
    outNodes.push(nodeByAngle(id, item.target, 'out', outerRadius + widthBoost, (outAngles[idx] ?? 56) + angleNudge, item.target))
  })
  nodes.push(
    ...relaxVerticalOverlap(outNodes, 'right').map((node) => ({
      ...node,
      displayLabel: wrapLabel(node.label),
      fullLabel: node.label,
    }))
  )

  const inAngles = [128, 162, 202, 236]
  const inNodes: Array<{ id: string; label: string; x: number; y: number; kind: 'in'; palaceName?: string }> = []
  rel.receiving.slice(0, 4).forEach((item, idx) => {
    const id = `in-${idx}`
    const widthBoost = Math.min(18, Math.max(0, (estimateLabelWidth(item.src) - 28) * 0.45))
    const angleNudge = item.src.length >= 4 ? (idx % 2 === 0 ? -4 : 4) : 0
    inNodes.push(nodeByAngle(id, item.src, 'in', outerRadius + widthBoost, (inAngles[idx] ?? 236) + angleNudge, item.src))
  })
  nodes.push(
    ...relaxVerticalOverlap(inNodes, 'left').map((node) => ({
      ...node,
      displayLabel: wrapLabel(node.label),
      fullLabel: node.label,
    }))
  )

  const nodeMap = Object.fromEntries(nodes.map(node => [node.id, node])) as Record<string, (typeof nodes)[number]>
  if (nodeMap.opposite) {
    const curve = curvePath(nodeMap.active, nodeMap.opposite, 'opposite', 0)
    links.push({ from: 'active', to: 'opposite', label: '对宫', kind: 'opposite', ...curve })
  }
  rel.flyingOutEntries.slice(0, 4).forEach((item, idx) => {
    const id = `out-${idx}`
    if (!nodeMap[id]) return
    const curve = curvePath(nodeMap.active, nodeMap[id], 'out', idx)
    links.push({ from: 'active', to: id, label: item.transform, kind: 'out', ...curve })
  })
  rel.receiving.slice(0, 4).forEach((item, idx) => {
    const id = `in-${idx}`
    if (!nodeMap[id]) return
    const curve = curvePath(nodeMap[id], nodeMap.active, 'in', idx)
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
  const palaceName = (localZiwei.value?.liuyue ?? []).find(item => item.month === month)?.palace_name
  if (palaceName) selectedZiweiPalaceName.value = palaceName
}

// 建议
const fortSummary = computed(() => B.value?.current_fortune_summary)
const shenshaItems = computed(() => B.value?.shensha ?? [])
const shenshaByPillar = computed(() => {
  const labels = [
    { key: 'year', label: '年柱' },
    { key: 'month', label: '月柱' },
    { key: 'day', label: '日柱' },
    { key: 'hour', label: '时柱' },
  ]
  const norm = (v: string | undefined) => (v ?? '').toLowerCase()
  return labels.map(({ key, label }) => {
    const items = shenshaItems.value.filter((s: { pillar?: string; is_beneficial: boolean }) => {
      const pillar = norm(s.pillar)
      return pillar.includes(key) || pillar.includes(label)
    })
    return {
      key,
      label,
      good: items.filter((s: { is_beneficial: boolean }) => s.is_beneficial).slice(0, 4),
      bad: items.filter((s: { is_beneficial: boolean }) => !s.is_beneficial).slice(0, 4),
    }
  })
})
const cangganNayinRows = computed(() => {
  const p = B.value?.pillars_primary
  if (!p) return []
  const keys = ['year', 'month', 'day', 'hour'] as const
  return keys.map((k, idx) => {
    const stem = p[k].stem
    const branch = p[k].branch
    return {
      key: k,
      label: pillarLabels[idx],
      canggan: (CANG_GAN[branch] ?? []).join(' / '),
      nayin: NAYIN_MAP[stem + branch] ?? '—',
    }
  })
})
const activePillarKey = ref<'year' | 'month' | 'day' | 'hour'>('day')
const activePillarDetail = computed(() => {
  const pillar = pillars.value.find(item => item.key === activePillarKey.value)
  const meta = cangganNayinRows.value.find(item => item.key === activePillarKey.value)
  const shensha = shenshaByPillar.value.find(item => item.key === activePillarKey.value)
  if (!pillar || !meta) return null
  return {
    ...pillar,
    canggan: meta.canggan || '—',
    nayin: meta.nayin || '—',
    stemWx: STEM_WX[pillar.stem] ?? '—',
    branchWx: BRANCH_WX[pillar.branch] ?? '—',
    goodShensha: shensha?.good ?? [],
    badShensha: shensha?.bad ?? [],
  }
})
function selectPillar(key: 'year' | 'month' | 'day' | 'hour') {
  activePillarKey.value = key
}
const zodiacText = computed(() => {
  const yearBranch = B.value?.pillars_primary?.year?.branch
  return yearBranch ? ZODIAC_MAP[yearBranch] ?? '—' : '—'
})

const birthLocalText = computed(() => {
  const dt = caseDetail.value?.birth_dt_local
  if (!dt) return '—'
  return dt.replace('T', ' ').slice(0, 16)
})

const tenGodsText = computed(() => {
  if (!pillars.value.length) return '—'
  return pillars.value.map(p => `${p.label}${p.shishen}`).join(' / ')
})

const shenshaSummaryText = computed(() => {
  if (!shenshaItems.value.length) return '—'
  return shenshaItems.value.slice(0, 8).map((s: { name?: string }) => s.name).join('、')
})

const dayunFlowSummaryText = computed(() => {
  const dayun = dayunItems.value.slice(0, 2).map((d: { start_year?: number; stem?: string; branch?: string }) => `${d.start_year ?? '起运'} ${d.stem ?? ''}${d.branch ?? ''}`).join('；')
  const liunian = liunianItems.value.slice(0, 2).map((y: { year?: number; stem?: string; branch?: string }) => `${y.year ?? '—'} ${y.stem ?? ''}${y.branch ?? ''}`).join('；')
  // 流月：取 monthly_fortune 中当年、当月及后 2 月
  const mf = B.value?.monthly_fortune ?? []
  let liuyueText = '—'
  if (mf.length) {
    const nowMonth = new Date().getMonth() + 1  // 1-12
    const relevant = mf
      .filter((m: LiuyueItem) => m.month >= nowMonth)
      .slice(0, 3)
    if (relevant.length) {
      liuyueText = relevant.map((m: LiuyueItem) => `${m.month}月${m.month_ganzhi ?? m.month_dizhi}`).join('；')
    } else {
      liuyueText = mf.slice(-3).map((m: LiuyueItem) => `${m.month}月${m.month_ganzhi ?? m.month_dizhi}`).join('；')
    }
  }
  if (!dayun && !liunian) return '—'
  return `大运：${dayun || '—'} ｜ 流年：${liunian || '—'} ｜ 流月：${liuyueText}`
})


// ─── 案例 CRUD ──────────────────────────────────────────────────
const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const formData = ref({ name: '', birth_dt_local: '1990-01-15T08:30', tz: 'Asia/Shanghai', lon: 116.41, gender: 'male' as 'male' | 'female', city: '', solar_time_enabled: false, notes: '', tags: '' })

function openCreateDialog() {
  formData.value = { name: '', birth_dt_local: '1990-01-15T08:30', tz: 'Asia/Shanghai', lon: 116.41, gender: 'male', city: '', solar_time_enabled: false, notes: '', tags: '' }
  showCreateDialog.value = true
}
function openEditDialog() {
  if (!caseDetail.value) return
  const c = caseDetail.value
  formData.value = { name: c.name, birth_dt_local: c.birth_dt_local.slice(0, 16), tz: c.tz, lon: c.lon, gender: (c.gender as 'male' | 'female') ?? 'male', city: c.city ?? '', solar_time_enabled: c.solar_time_enabled, notes: c.notes ?? '', tags: (c.tags ?? []).join(', ') }
  showEditDialog.value = true
}
const formSaving = ref(false)
async function submitCreate() {
  formSaving.value = true
  try {
    const tags = formData.value.tags.split(',').map(s => s.trim()).filter(Boolean)
    await createCase({ name: formData.value.name, birth_dt_local: formData.value.birth_dt_local + ':00', tz: formData.value.tz, lon: formData.value.lon, gender: formData.value.gender, city: formData.value.city || undefined, solar_time_enabled: formData.value.solar_time_enabled, notes: formData.value.notes || undefined, tags: tags.length ? tags : undefined })
    showCreateDialog.value = false
    await store.loadCaseList()
  } catch (e: unknown) { alert((e as Error).message) }
  finally { formSaving.value = false }
}
async function submitEdit() {
  if (!caseDetail.value) return
  formSaving.value = true
  try {
    const tags = formData.value.tags.split(',').map(s => s.trim()).filter(Boolean)
    const updated = await updateCase(caseDetail.value.id, { name: formData.value.name, gender: formData.value.gender, city: formData.value.city || undefined, solar_time_enabled: formData.value.solar_time_enabled, notes: formData.value.notes || undefined, tags: tags.length ? tags : undefined })
    caseDetail.value = updated
    showEditDialog.value = false
    await store.loadCaseList()
  } catch (e: unknown) { alert((e as Error).message) }
  finally { formSaving.value = false }
}
async function handleDeleteCase() {
  if (!caseDetail.value) return
  if (!confirm('确认删除案例？此操作不可恢复。')) return
  try {
    await deleteCaseApi(caseDetail.value.id)
    caseDetail.value = null
    selectedId.value = null
    await store.loadCaseList()
  } catch (_error) { alert('删除失败') }
}

// ─── 打印模式 ────────────────────────────────────────────────
function triggerPrint() {
  window.print()
}

// ─── 分享 / 导出 ────────────────────────────────────────────────
const shareUrl = ref<string | null>(null)
async function handleShare() {
  if (!caseDetail.value) return
  try {
    const res = await createShareToken(caseDetail.value.id)
    shareUrl.value = res.share_url
    setTimeout(() => { shareUrl.value = null }, 8000)
  } catch (_error) { alert('生成分享链接失败') }
}
async function handleExportJson() {
  if (!caseDetail.value) return
  try {
    const blob = await exportCaseJson(caseDetail.value.id)
    downloadBlob(blob, `${caseDetail.value.name}.json`)
  } catch (_error) { alert('导出失败') }
}
async function handleExportPdf() {
  if (!caseDetail.value) return
  try {
    const blob = await exportCasePdf(caseDetail.value.id)
    downloadBlob(blob, `${caseDetail.value.name}.pdf`)
  } catch (_error) { alert('PDF导出失败') }
}

// ─── 快照 ───────────────────────────────────────────────────────
const snapshots = ref<SnapshotOut[]>([])
const snapshotsLoading = ref(false)
async function loadSnapshots() {
  if (!caseDetail.value) return
  snapshotsLoading.value = true
  const result = await listSnapshots(caseDetail.value.id, { limit: 10 }).catch(() => null as SnapshotOut[] | null)
  if (result) snapshots.value = result
  snapshotsLoading.value = false
}
</script>

<template>

        <WorkbenchStateBlock
          v-if="!baziLoading && !ziweiLoading && !baziError && !ziweiError && !localBazi && !(isZiweiSection && localZiwei)"
          state="empty"
          title="暂无可展示的命盘内容"
          description="请先点击“重算”，或切换到其他案例后再返回当前案例。"
          retry-label="重新加载命盘"
          @retry="reloadCurrentCase()"
        />
  <div class="wb-layout">

    <!-- ══════ 中央区域 ══════ -->
    <main class="wb-main">

      <!-- ── 左子列：案例列表 ── -->
      <WorkbenchCaseList
        v-model="searchQ"
        :cases="filteredList"
        :selected-id="selectedId"
        :profile-sync-tag="PROFILE_SYNC_TAG"
        :current-dayun-label="currentCaseDayunLabel"
        :ziwei-summary-text="ziweiCaseSummaryText"
        :bazi-summary-line="baziCaseSummaryLine"
        @create="openCreateDialog()"
        @select-case="selectCase"
      />

      <!-- ── 右子列：案例详情 ── -->
      <section class="wb-detail" v-if="caseDetail && !nav.currentSectionId?.startsWith('bazi-')">

        <!-- ① 顶部：基本信息 -->
        <WorkbenchInfoBar
          :case-detail="caseDetail"
          :simple-view="simpleView"
          :share-url="shareUrl"
          @toggle-view="toggleSimpleView()"
          @sync-profile="syncProfileToWorkbenchCase()"
          @open-report="router.push(`/report/${caseDetail.id}`)"
          @reload="reloadCurrentCase()"
          @edit="openEditDialog()"
          @share="handleShare()"
          @export-json="handleExportJson()"
          @export-pdf="handleExportPdf()"
          @print="triggerPrint()"
          @snapshots="loadSnapshots()"
          @delete-case="handleDeleteCase()"
        />

        <WorkbenchGuideCard
          v-if="showNewbieGuide"
          :current-step="currentGuideStep"
          :progress-percent="guideProgressPercent"
          :steps="newbieGuideSteps"
          @prev="goPrevGuideStep"
          @next="goNextGuideStep"
          @play="playGuideDemo"
          @close="closeNewbieGuide"
          @focus-step="focusGuideStep"
        />

        <!-- 加载中 / 错误 -->
        <WorkbenchStateBlock
          v-if="isZiweiSection ? ziweiLoading : baziLoading"
          state="loading"
        />
        <WorkbenchStateBlock
          v-else-if="isZiweiSection ? !!ziweiError : !!baziError"
          state="error"
          :message="isZiweiSection ? ziweiError : baziError"
          @retry="reloadCurrentCase()"
        />
        <WorkbenchStateBlock
          v-else-if="!isZiweiSection && !localBazi"
          state="empty"
          title="八字结果尚未加载"
          description="当前未在加载中，也没有错误提示。请点击重试重新拉取命盘。"
          retry-label="重新加载命盘"
          @retry="reloadCurrentCase()"
        />

        <template v-else-if="isZiweiSection && localZiwei">

          <div v-if="simpleView" class="wb-simple-hint">已开启简洁视图：仅展示核心命盘与关键走势，可点击右上角切换到完整视图。</div>

          <WorkbenchZiweiSummary
            v-if="ziweiSummaryCards"
            :summary="ziweiSummaryCards"
          />

          <!-- 双盘大运对照条 -->
          <WorkbenchDualDayunAxis
            v-if="dualDayunAxis"
            :axis="dualDayunAxis"
            :selected-bazi-start-year="activeDayunTimelineItem?.startYear"
            :selected-ziwei-index="activeZiweiDayun?.index ?? currentZiweiDayun?.index"
          />

          <WorkbenchZiweiOverview
            v-if="!simpleView"
            :summary="localZiwei.summary"
            :patterns="localZiwei.patterns ?? []"
            :lunar-text="`${localZiwei.lunar?.lunar_year ?? '—'}年${localZiwei.lunar?.lunar_month ?? '—'}月${localZiwei.lunar?.lunar_day ?? '—'}日`"
            :template-version="localZiwei.template_version"
            :true-solar-time="localZiwei.true_solar_time"
            :engine-version="localZiwei.engine_version"
          />

          <WorkbenchZiweiFocus
            :palaces="ziweiPalaces"
            :active-palace="activeZiweiPalace"
            :highlighted-palace-name="ziweiHighlightedPalaceName"
            :relations="activeZiweiRelations"
            :relation-graph="activeZiweiRelationGraph"
            @select-palace="selectZiweiPalace"
          />

          <div v-if="!simpleView" class="wb-section wb-zw-bottom-grid">
            <WorkbenchZiweiSelectors
              :dayun-items="localZiwei.dayun?.items?.slice(0, 6) ?? []"
              :liuyue-items="localZiwei.liuyue?.slice(0, 6) ?? []"
              :active-dayun-index="activeZiweiDayun?.index ?? currentZiweiDayun?.index"
              :active-liuyue-month="activeZiweiLiuyue?.month ?? currentZiweiLiuyue?.month"
              :active-dayun-summary="activeZiweiDayunSummary"
              :active-liuyue-summary="activeZiweiLiuyueSummary"
              @select-dayun="selectZiweiDayun"
              @select-liuyue="selectZiweiLiuyue"
            />
            <WorkbenchZiweiAdvice
              :remedies="localZiwei.remedies ?? []"
              :suggestions="localZiwei.life_suggestions ?? []"
            />
          </div>
        </template>

        <!-- ② 命盘可视化 -->
        <template v-else-if="localBazi">

          <div v-if="simpleView" class="wb-simple-hint">已开启简洁视图：保留四柱/五行/大运流年核心模块，其他扩展分析暂时收起。</div>

          <!-- 命盘顶部速览 -->
          <WorkbenchBaziSummary
            v-if="chartSummaryCards"
            :summary="chartSummaryCards"
            :current-year="CURRENT_YEAR"
          />
          <WorkbenchBaziIndicators
            :key-indicators="baziKeyIndicators"
            :active-indicator="activeIndicatorShensha"
            :geju="geju"
            :yongshen="yongshen"
            :strength="strength"
            :day-stem="pillars[2]?.stem ?? '—'"
            :day-stem-color="wxColor(STEM_WX[pillars[2]?.stem ?? ''] ?? '')"
            @toggle-indicator-shensha="toggleIndicatorShensha"
          />

          <!-- 四柱主表 + 五行横条 -->
          <WorkbenchBaziChart
            :pillars="pillars"
            :active-pillar-key="activePillarKey"
            :active-pillar-detail="activePillarDetail"
            :strength="strength"
            :strength-bar-color="wxColor(STEM_WX[pillars[2]?.stem ?? ''] ?? '')"
            :wuxing="wuxing"
            :wuxing-max="wuxingMax"
            :wuxing-radar-points="wuxingRadarPoints"
            :wuxing-radar-axes="wuxingRadarAxes"
            @select-pillar="selectPillar"
          />

          <!-- 大运时间轴 -->
          <WorkbenchBaziDayunTimeline
            v-if="dayunItems.length"
            :items="dayunTimelineItems"
            :active-item="activeDayunTimelineItem"
            @select-dayun="selectDayun"
          />

          <!-- 流年网格 -->
          <WorkbenchBaziLiunianGrid
            v-if="liunianItems.length"
            :current-year="CURRENT_YEAR"
            :items="liunianTimelineItems"
            :active-item="activeLiunianTimelineItem"
            :active-dayun-info="activeLiunianDayunInfo"
            :active-domains="activeLiunianDetail?.domains ?? []"
            :sparkline="liunianSparkline"
            @select-year="toggleLiunianDetail"
          />

          <!-- 流月运势 -->
          <WorkbenchBaziLiuyueHeatmap
            v-if="B?.monthly_fortune?.length"
            :current-year="CURRENT_YEAR"
            :heatmap-items="liuyueHeatmapData"
            :trend-data="liuyueTrendSvg"
            :active-detail="activeLiuyueDetail"
            :linked-months="linkedLiuyueMonths"
            :show-current-year-link-hint="activeLiunianDetail?.year !== CURRENT_YEAR"
            @select-month="selectLiuyue"
          />

        </template>

        <!-- ③ 解读区 -->
        <template v-if="localBazi && !baziLoading">
          <WorkbenchBaziInsights
            :current-year="CURRENT_YEAR"
            :simple-view="simpleView"
            :summary="summary"
            :bazi-data="B"
            :this-year-detail="thisYearDetail"
            :fort-summary="fortSummary"
            :liunian-detail-rows="liunianDetailRows"
            :expanded-liunian-detail-year="expandedLiunianDetailYear"
            :active-liuyue-month="activeLiuyueMonth"
            :geju="geju"
            :yongshen="yongshen"
            @toggle-liunian-detail="toggleLiunianDetail"
            @select-liunian-month="({ year, month }) => selectLiunianMonth(year, month)"
          />

        </template>

        <!-- ④ 快照历史 -->
        <div v-if="snapshots.length && !simpleView" class="wb-section">
          <h2 class="wb-sec-title">快照历史</h2>
          <div class="wb-snapshot-list">
            <div v-for="snap in snapshots" :key="snap.id" class="wb-snapshot-item">
              <span class="wb-snap-kind">{{ snap.kind }}</span>
              <span class="wb-snap-ver">{{ snap.api_version ?? '—' }}</span>
              <span class="wb-snap-date">{{ fmtDate(snap.created_at) }}</span>
              <span v-if="snap.note" class="wb-snap-note">{{ snap.note }}</span>
            </div>
          </div>
        </div>

      </section>

      <!-- 未选中占例时：按当前课题显示中间内容，而不是留白 -->
      <section v-else :class="['wb-detail', { 'wb-no-select': !caseDetail }]">
        <template v-if="nav.currentSectionId?.startsWith('bazi-')">
          <div class="wb-onboard">
            <div class="wb-onboard-hero">
              <div class="wb-onboard-icon">📚</div>
              <div>
                <h1 class="wb-onboard-title">四柱八字总览</h1>
                <p class="wb-onboard-sub">同类型小节已整合为一个界面，1.1~1.10 可在本页连续查看。</p>
              </div>
            </div>

            <div v-if="!caseDetail || !localBazi" class="wb-card wb-onboard-card">
              <div class="wb-card-label">{{ baziError ? '计算失败：' + baziError : '请先选择案例 / 等待加载' }}</div>
              <p class="wb-tips" style="margin: 0;">选择左侧案例后，此处会显示完整八字链路（生辰、四柱、五行、神煞、格局、大运等）。</p>
              <div class="wb-onboard-actions" style="margin-top: 12px;">
                <button class="wb-btn-accent" @click="openCreateDialog()">＋ 新建案例</button>
                <button class="wb-btn-ghost" @click="router.push('/bazi')">打开八字页</button>
                <button v-if="caseDetail" class="wb-btn-ghost" @click="reloadCurrentCase()">🔄 重算</button>
              </div>
            </div>

            <WorkbenchBaziOverviewPanels
              mode="overview"
              :case-name="caseDetail?.name ?? ''"
              :birth-local-text="birthLocalText"
              :gender-text="caseDetail ? genderLabel(caseDetail.gender) : ''"
              :city="caseDetail?.city ?? ''"
              :tz="caseDetail?.tz ?? ''"
              :lon="caseDetail?.lon ?? null"
              :summary-text="dayunFlowSummaryText"
              :pillars="pillars"
              :active-pillar-key="activePillarKey"
              :strength="strength"
              :ten-gods-text="tenGodsText"
              :active-pillar-detail="activePillarDetail"
              :wuxing="wuxing"
              :wuxing-max="wuxingMax"
              :canggan-nayin-rows="cangganNayinRows"
              :zodiac-text="zodiacText"
              :geju-name="geju?.geju_name ?? ''"
              :favor-text="yongshen?.favor?.join('、') || ''"
              :avoid-text="yongshen?.avoid?.join('、') || ''"
              :shensha-summary-text="shenshaSummaryText"
              :dayun-items="dayunItems"
              @select-pillar="selectPillar"
            />
          </div>
        </template>

        <!-- 其他章节（紫微等）占位符 -->
        <template v-else>
          <div class="wb-empty-icon">🗂️</div>
          <p class="wb-empty-txt">当前课题：{{ nav.currentSection?.label }}</p>
          <div class="wb-empty-actions">
            <button class="wb-btn-accent" @click="openCreateDialog()">＋ 新建案例</button>
            <button class="wb-btn-ghost" @click="nav.selectSection('bazi-birth')">查看生辰数据</button>
          </div>
        </template>
      </section>

    </main>

    <div v-if="caseDetail && nav.currentSectionId?.startsWith('bazi-')" class="wb-bazi-hotfix">
      <div class="wb-bazi-hotfix-inner">
        <div class="wb-bazi-hotfix-head">
          <div>
            <h1 class="wb-bazi-hotfix-title">四柱八字 · {{ nav.currentSection?.label || '总览' }}</h1>
            <p class="wb-bazi-hotfix-sub">{{ caseDetail.name }} ｜ {{ birthLocalText }} ｜ {{ genderLabel(caseDetail.gender) }}命</p>
            <div class="wb-bazi-hotfix-badges">
              <span class="wb-hotfix-badge">{{ caseDetail.city || caseDetail.tz || '未知地点' }}</span>
              <span v-if="caseDetail.tags?.includes(PROFILE_SYNC_TAG)" class="wb-hotfix-badge">来源：个人信息同步</span>
            </div>
          </div>
          <div style="display:flex;gap:8px;align-items:center;">
            <button class="wb-btn-ghost" type="button" @click="syncProfileToWorkbenchCase()">👤 同步个人信息</button>
            <button class="wb-btn-ghost" type="button" @click="reloadCurrentCase()">🔄 重算</button>
          </div>
        </div>

        <WorkbenchStateBlock
          v-if="baziLoading"
          state="loading"
        />

        <WorkbenchStateBlock
          v-else-if="baziError"
          state="error"
          :message="baziError"
          @retry="reloadCurrentCase()"
        />

        <WorkbenchStateBlock
          v-else-if="!localBazi"
          state="empty"
          title="八字结果尚未加载"
          description="当前案例已选中，但命盘结果还没有进入界面。"
          retry-label="重新加载命盘"
          @retry="reloadCurrentCase()"
        />

        <WorkbenchBaziOverviewPanels
          v-else
          mode="hotfix"
          :birth-local-text="birthLocalText"
          :city="caseDetail?.city ?? ''"
          :tz="caseDetail?.tz ?? ''"
          :lon="caseDetail?.lon ?? null"
          :summary-text="dayunFlowSummaryText"
          :pillars="pillars"
          :active-pillar-key="activePillarKey"
          :strength="strength"
          :ten-gods-text="tenGodsText"
          :wuxing="wuxing"
          :wuxing-max="wuxingMax"
          :geju-name="geju?.geju_name ?? ''"
          :favor-text="yongshen?.favor?.join('、') || ''"
          :shensha-summary-text="shenshaSummaryText"
          :dayun-items="dayunItems"
          @select-pillar="selectPillar"
        />
      </div>
    </div>

    <!-- ═══ 新建/编辑案例弹窗 ═══ -->
    <Teleport to="body">
      <div v-if="showCreateDialog || showEditDialog" class="wb-modal-mask" @click.self="showCreateDialog = false; showEditDialog = false">
        <div class="wb-modal">
          <h2 class="wb-modal-title">{{ showEditDialog ? '编辑案例' : '新建案例' }}</h2>
          <div class="wb-form-grid">
            <label class="wb-form-item">
              <span class="wb-form-label">姓名</span>
              <input v-model="formData.name" class="wb-form-input" placeholder="例：张三" />
            </label>
            <label v-if="!showEditDialog" class="wb-form-item">
              <span class="wb-form-label">出生时间</span>
              <input v-model="formData.birth_dt_local" type="datetime-local" class="wb-form-input" />
            </label>
            <label class="wb-form-item">
              <span class="wb-form-label">性别</span>
              <select v-model="formData.gender" class="wb-form-input">
                <option value="male">男</option>
                <option value="female">女</option>
              </select>
            </label>
            <label v-if="!showEditDialog" class="wb-form-item">
              <span class="wb-form-label">
                <input type="checkbox" v-model="formData.solar_time_enabled" /> 启用真太阳时
              </span>
            </label>
          </div>
          <div class="wb-modal-actions">
            <button class="wb-btn-ghost" @click="showCreateDialog = false; showEditDialog = false">取消</button>
            <button class="wb-btn-accent" :disabled="formSaving" @click="showEditDialog ? submitEdit() : submitCreate()">
              {{ formSaving ? '保存中…' : (showEditDialog ? '保存修改' : '创建') }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
/* ══════════════════════════════════════════════════════════
   WorkbenchView 样式
   布局：caselist(320) | detail(1fr)
   侧边导航已迁移到 AppSidebar.vue
   ══════════════════════════════════════════════════════════ */

/* ─── 根布局 ──────────────────────────────────────────────── */
.wb-layout {
  position: relative;
  display: grid;
  grid-template-columns: 320px 1fr;
  height: 100vh;
  overflow: hidden;
  background: var(--bg);
  font-family: var(--font-ui);
}

/* ─── 案例列表 ────────────────────────────────────────────── */
.wb-case-tags { display: flex; gap: 4px; margin-top: 4px; flex-wrap: wrap; }
.wb-case-sync {
  display: inline-flex;
  align-items: center;
  height: 18px;
  padding: 0 7px;
  border: 1px solid var(--border-md);
  border-radius: 999px;
  font-size: 10px;
  color: var(--text-2);
  background: var(--surface-2);
}
.wb-tag {
  font-size: 10px; padding: 1px 6px; border-radius: 99px;
  background: var(--surface-2); border: 1px solid var(--border);
  color: var(--text-3);
}

.wb-empty-hint { text-align: center; padding: 40px 16px; font-size: 13px; color: var(--text-3); }

/* ─── 案例详情 ────────────────────────────────────────────── */
.wb-detail {
  display: flex; flex-direction: column;
  height: 100%; overflow-y: auto;
  background: var(--bg);
}

.wb-bazi-hotfix {
  position: absolute;
  left: 320px;
  right: 0;
  top: 0;
  bottom: 0;
  overflow-y: auto;
  padding: 18px 22px 28px;
  background: rgba(245, 236, 217, 0.96);
  z-index: 8;
}

.wb-bazi-hotfix-inner {
  max-width: 980px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
}

.wb-bazi-hotfix-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  background: var(--surface);
}

.wb-bazi-hotfix-title {
  margin: 0;
  font-size: 22px;
  color: var(--text);
  font-family: var(--font-cn);
}

.wb-bazi-hotfix-sub {
  margin: 6px 0 0;
  font-size: 13px;
  color: var(--text-3);
}

.wb-bazi-hotfix-badges {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.wb-hotfix-badge {
  font-size: 11px;
  color: var(--text-2);
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 2px 8px;
}

.wb-case-dayun,
.wb-case-ziwei,
.wb-case-bazi-summary {
  display: -webkit-box;
  line-clamp: 2;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.wb-btn-ghost.is-active {
  border-color: rgba(37, 99, 235, 0.45);
  background: rgba(37, 99, 235, 0.10);
  color: #1e40af;
}

.wb-simple-hint {
  margin: 10px 0 12px;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid rgba(16, 185, 129, 0.28);
  background: rgba(16, 185, 129, 0.08);
  color: #065f46;
  font-size: 12px;
  line-height: 1.45;
}

.wb-guide-focus-target {
  animation: wb-guide-focus-pulse 1.8s ease;
}

@keyframes wb-guide-focus-pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(37, 99, 235, 0);
    outline: 0 solid rgba(37, 99, 235, 0);
  }
  25% {
    box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.18);
    outline: 2px solid rgba(37, 99, 235, 0.45);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(37, 99, 235, 0);
    outline: 0 solid rgba(37, 99, 235, 0);
  }
}
.wb-btn-accent {
  padding: 8px 16px;
  background: var(--accent); color: #fff; border: none;
  border-radius: 8px; font-size: 13px; font-weight: 600;
  cursor: pointer; transition: background var(--dur-fast);
  white-space: nowrap;
}
.wb-btn-accent:hover { background: var(--accent-dark); }
.wb-btn-ghost {
  padding: 8px 14px;
  background: transparent; border: 1px solid var(--border-md);
  border-radius: 8px; font-size: 13px; color: var(--text-2);
  cursor: pointer; transition: all var(--dur-fast);
  white-space: nowrap;
}
.wb-btn-ghost:hover { border-color: var(--accent); color: var(--accent); }

@keyframes wb-spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

/* ② 命盘区块 */
.wb-section {
  padding: 20px 24px 0;
}
.wb-sec-title {
  font-size: 14px; font-weight: 700; color: var(--text);
  margin: 0 0 14px; display: flex; align-items: center; gap: 8px;
}
.wb-sec-note { font-size: 11px; color: var(--text-3); font-weight: 400; }

.wb-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 10px; padding: 12px 16px; min-width: 100px;
}
.wb-card-label { font-size: 10px; color: var(--text-3); margin-bottom: 4px; text-transform: uppercase; letter-spacing: .05em; }
/* ─── 打印样式 ────────────────────────────────────────────── */
@media print {
  .wb-layout { grid-template-columns: 1fr; }
  .wb-caselist { display: none; }
  .wb-detail { height: auto; overflow: visible; background: white; }
  .wb-section { page-break-inside: avoid; padding: 16px 24px; }
  .wb-sec-title { font-size: 16px; margin-bottom: 12px; border-bottom: 1px solid #ccc; padding-bottom: 6px; }
  .wb-btn-ghost, .wb-btn-accent { display: none; }
  .wb-search-wrap { display: none; }
  .wb-modal { display: none; }
  body { background: white; }
  table { width: 100%; border-collapse: collapse; margin-bottom: 12px; }
  table th, table td { border: 1px solid #333; padding: 6px; text-align: center; font-size: 11px; }
}

/* 空选中态 */
.wb-no-select {
  justify-content: center; align-items: center; gap: 16px;
  padding: 28px;
}
.wb-empty-icon { font-size: 48px; opacity: 0.3; }
.wb-empty-txt  { font-size: 14px; color: var(--text-3); }
.wb-empty-actions { display: flex; gap: 10px; }

.wb-onboard {
  width: 100%;
  max-width: 1040px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.wb-onboard-hero {
  display: flex;
  gap: 16px;
  align-items: center;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 22px 24px;
}
.wb-onboard-icon {
  width: 64px;
  height: 64px;
  border-radius: 18px;
  display: grid;
  place-items: center;
  font-size: 30px;
  background: var(--accent-lt);
}
.wb-onboard-title {
  margin: 0;
  font-size: 26px;
  color: var(--text);
  font-family: var(--font-cn);
}
.wb-onboard-sub {
  margin: 6px 0 0;
  color: var(--text-2);
  font-size: 14px;
  line-height: 1.7;
}
.wb-onboard-card {
  min-height: 260px;
  padding: 18px 20px;
}
.wb-onboard-actions {
  display: flex;
  gap: 10px;
}

/* 最后一个 section 加底部 padding */
.wb-section:last-child { padding-bottom: 32px; }

/* 快照列表 */
.wb-snapshot-list { display: flex; flex-direction: column; gap: 6px; }
.wb-snapshot-item {
  display: flex; gap: 12px; align-items: center;
  padding: 8px 14px; background: var(--surface);
  border: 1px solid var(--border); border-radius: 8px;
  font-size: 12px; color: var(--text-2);
}
.wb-snap-kind { font-weight: 600; color: var(--accent-dark); padding: 1px 8px; background: var(--accent-lt); border-radius: 99px; }
.wb-snap-ver { color: var(--text-3); font-family: var(--font-mono); }
.wb-snap-date { color: var(--text-3); font-family: var(--font-mono); }
.wb-snap-note { color: var(--text-2); flex: 1; }

/* 弹窗 */
.wb-modal-mask {
  position: fixed; inset: 0; z-index: 999;
  background: rgba(0,0,0,.35); display: grid; place-items: center;
}
.wb-modal {
  background: var(--surface); border-radius: 14px;
  padding: 24px 28px; width: 480px; max-width: 92vw;
  box-shadow: 0 20px 60px rgba(0,0,0,.2);
}
.wb-modal-title { font-size: 16px; font-weight: 700; margin: 0 0 16px; color: var(--text); }
.wb-form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px 14px; }
.wb-form-item { display: flex; flex-direction: column; gap: 3px; }
.wb-form-label { font-size: 11px; color: var(--text-3); font-weight: 500; }
.wb-form-input {
  padding: 7px 10px; border: 1px solid var(--border); border-radius: 7px;
  font-size: 13px; background: var(--bg); color: var(--text);
  outline: none; transition: border-color .15s;
}
.wb-form-input:focus { border-color: var(--accent); }
.wb-textarea { resize: vertical; font-family: inherit; }
.wb-modal-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 16px; }

.wb-tips {
  font-size: 13px;
  color: var(--text-3);
  margin: 0 0 12px 0;
  line-height: 1.6;
  font-family: var(--font-cn);
}

/* ─── 紫微概览 ─────────────────────────────────────────────── */
.wb-zw-bottom-grid {
  display: grid;
  grid-template-columns: 1.3fr 1fr;
  gap: 12px;
}

/* ─── 响应式 ──────────────────────────────────────────────── */
@media (max-width: 1280px) {
  .wb-layout { grid-template-columns: 280px 1fr; }
}

@media (max-width: 900px) {
  .wb-layout { grid-template-columns: 240px 1fr; }
  .wb-zw-bottom-grid { grid-template-columns: 1fr; }
}
@media (max-width: 768px) {
  .wb-pillar-detail-head { flex-direction: column; }
}
@media (max-width: 560px) {
  .wb-layout { grid-template-columns: 1fr; }
  .wb-sec-title { flex-wrap: wrap; gap: 6px; }
}
</style>
