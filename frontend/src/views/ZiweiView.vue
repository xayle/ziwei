<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useUiStore } from '@/stores/ui'
import { useAiStore } from '@/stores/ai'
import { useAuthStore } from '@/stores/auth'
import { computeZiwei, demoZiwei, ziweiBatch, ziweiMultiCompat } from '@/api/ziwei'
import type { ZiweiResponse, PalaceResponse, DayunItem, MultiCompatResponse, ZiweiRequest, StarInfo } from '@/api/ziwei'
import {
  createReview,
  listReviews,
  getReviewStats,
  getReviewQueue,
  getMyReviewQueue,
  getReviewAssignees,
  updateReview,
  getReviewHistory,
  bulkReviewAction,
  assignReview,
  getAdminStats,
  createExperiment,
  listExperiments,
  updateExperiment,
  deleteExperiment,
  getExperimentResults,
  type ChartReviewResponse,
  type ReviewAssigneeItem,
  type ReviewStats,
  type ReviewHistoryItem,
  type AdminStatsResponse,
  type ExperimentResponse,
  type ExperimentResults,
} from '@/api/admin'
import { createCase, fetchCaseList, deleteCase, fetchFengshuiBagua, type CaseOut, type FengshuiResponse } from '@/api/report'
import { createSnapshot, listSnapshots, diffSnapshots, type SnapshotOut, type SnapshotDiffResponse } from '@/api/snapshots'
import { indexChart, searchSimilar, type SimilarResult } from '@/api/similarity'
import { getLlmConfig, interpretGeneric, streamInterpretation, fetchDrafts, getDraft, updateDraft, type LlmDraft } from '@/api/llm'
import { getGlossary, type GlossaryItem } from '@/api/static-data'
import { getFengshuiOptions, analyzeRoomLayout, type FengshuiOptions, type RoomLayoutResponse } from '@/api/fengshui'
import { useProfileStore } from '@/stores/profile'
import CityPicker from '@/components/CityPicker.vue'

const router = useRouter()
const ui      = useUiStore()
const ai      = useAiStore()
const auth    = useAuthStore()

const profile = useProfileStore()

// 从个人信息 store 解析出年月日时分
const _bd = profile.parseBirthDt()

// ── 表单（初始化时从 profile 预填）──────────────────────────
const year    = ref(_bd.year)
const month   = ref(_bd.month)
const day     = ref(_bd.day)
const hour    = ref(_bd.hour)
const minute  = ref(_bd.minute)
const gender  = ref<'男' | '女'>(profile.gender === 'female' ? '女' : '男')
const liunianYear = ref<number | undefined>(undefined)
const longitude   = ref<number | undefined>(profile.lon)
// CityPicker 初始城市
const initCity = ref(profile.cityName || '北京')

// 表单显示控制：已保存个人信息时默认折叠
const showForm = ref(!profile.saved)

type StarLike = string | Partial<StarInfo>
type FlyingReceivedItem = Record<string, string> | string[]

function getStarName(star: StarLike): string {
  return typeof star === 'string' ? star : star.name ?? ''
}

function getStarTransforms(star: StarLike): string[] {
  if (typeof star === 'string') return []
  return Array.isArray(star.transforms) ? star.transforms : []
}

function getStarBrightnessValue(star?: Partial<StarInfo>): number {
  return star?.brightness_val ?? 0
}

function getAuxStars(palace: PalaceResponse): StarLike[] {
  return (palace.aux_stars ?? []) as unknown as StarLike[]
}

function getPalaceTransforms(palace: PalaceResponse): string[] {
  return [
    ...(palace.main_stars ?? []).flatMap((star) => getStarTransforms(star)),
    ...getAuxStars(palace).flatMap((star) => getStarTransforms(star)),
  ]
}

function getReceivedTransformTexts(item?: FlyingReceivedItem): string[] {
  if (!item) return []
  return Array.isArray(item) ? item : Object.values(item)
}

function getReceivedTransformLabels(item?: FlyingReceivedItem): string[] {
  if (!item) return []
  if (Array.isArray(item)) return item
  return Object.entries(item).map(([star, transform]) => `${star}${transform.slice(1)}`)
}

// ── 算法设置 ──────────────────────────────────────────
const showAlgoSettings = ref(false)
const algoLateZishi   = ref<boolean>(true)
const algoLeapMethod  = ref<'mid' | 'next' | 'same'>('mid')
const algoKuiyue      = ref<'standard' | 'gengxin_mahu' | 'gengxin_huima' | 'liuxin_mahu'>('standard')
// A1-A8 新增
const algoTianma      = ref<'year' | 'month'>('year')
const algoTiankong    = ref<'standard' | 'shun'>('standard')
const algoBrightness  = ref<'standard' | 'zhongzhou' | 'mod1' | 'mod2'>('standard')
const algoJiukong     = ref<'dual' | 'single' | 'zhanyan'>('dual')
const algoTianshang   = ref<'standard' | 'zhongzhou'>('standard')
const algoMingzhu     = ref<'quanshu' | 'zhongzhou'>('quanshu')
const algoLiunianSihua = ref<'year_stem' | 'life_palace_stem'>('year_stem')
const algoChangsheng  = ref<'standard' | 'water_earth' | 'fire_earth'>('standard')

// 四化表 per-stem 方案 (0=标准)
const sihuaJia  = ref(0)  // 甲: 廉破武阳/廉破曲阳
const sihuaWu   = ref(0)  // 戊: 贪阴右机/贪阴阳机
const sihuaGeng = ref(0)  // 庚: 0-4
const sihuaXin  = ref(0)  // 辛: 巨阳曲昌/巨阳武昌
const sihuaRen  = ref(0)  // 壬: 0-2
const sihuaGui  = ref(0)  // 癸: 破巨阴贪/破巨阳贪

function buildSihuaIndices(): Record<string, number> | undefined {
  const m: Record<string, number> = {}
  if (sihuaJia.value)  m['甲'] = sihuaJia.value
  if (sihuaWu.value)   m['戊'] = sihuaWu.value
  if (sihuaGeng.value) m['庚'] = sihuaGeng.value
  if (sihuaXin.value)  m['辛'] = sihuaXin.value
  if (sihuaRen.value)  m['壬'] = sihuaRen.value
  if (sihuaGui.value)  m['癸'] = sihuaGui.value
  return Object.keys(m).length > 0 ? m : undefined
}

function resetAlgoSettings() {
  algoLateZishi.value  = true
  algoLeapMethod.value = 'mid'
  algoKuiyue.value     = 'standard'
  sihuaJia.value = sihuaWu.value = sihuaGeng.value = 0
  sihuaXin.value = sihuaRen.value = sihuaGui.value = 0
  algoTianma.value      = 'year'
  algoTiankong.value    = 'standard'
  algoBrightness.value  = 'standard'
  algoJiukong.value     = 'dual'
  algoTianshang.value   = 'standard'
  algoMingzhu.value     = 'quanshu'
  algoLiunianSihua.value = 'year_stem'
  algoChangsheng.value  = 'standard'
}

// C-6: 预设方案应用
function applyPreset(preset: 'sanhe' | 'feixing' | 'qintian' | 'zhongzhou') {
  // 先重置为默认
  resetAlgoSettings()
  
  switch (preset) {
    case 'sanhe':
      // 三合派：传统默认设置（已重置，无需额外修改）
      break
    case 'feixing':
      // 飞星派：注重飞星连线、取象
      algoLeapMethod.value = 'next'    // 闰月视为下月
      algoTianma.value = 'month'       // 天马依月支
      algoBrightness.value = 'mod1'    // 现代修订亮度
      break
    case 'qintian':
      // 钦天门：独特的晚子时和四化处理
      algoLateZishi.value = false      // 晚子时视为当日
      algoLeapMethod.value = 'same'    // 闰月视为本月
      algoKuiyue.value = 'gengxin_mahu'
      sihuaGeng.value = 2              // 庚干：阳武府同
      algoJiukong.value = 'zhanyan'    // 占验派排法
      break
    case 'zhongzhou':
      // 中州派：王亭之体系
      algoBrightness.value = 'zhongzhou'
      algoTianshang.value = 'zhongzhou'
      algoMingzhu.value = 'zhongzhou'
      break
  }
}

// 每次进入页面时同步 profile 数据
onMounted(() => {
  const bd = profile.parseBirthDt()
  year.value    = bd.year
  month.value   = bd.month
  day.value     = bd.day
  hour.value    = bd.hour
  minute.value  = bd.minute
  gender.value  = profile.gender === 'female' ? '女' : '男'
  longitude.value = profile.lon
  initCity.value  = profile.cityName || '北京'
  // 已保存个人信息则自动排盘并折叠表单
  if (profile.saved) {
    showForm.value = false
    nextTick(() => doCalculate())
  }
  // 注册键盘快捷键
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})

// ── 键盘快捷键 ─────────────────────────────────────────
const TAB_ORDER: typeof activeTab.value[] = ['chart', 'summary', 'palaces', 'dayun', 'liunian', 'liuyue', 'patterns', 'flying', 'forecast', 'suggest']
function handleKeydown(e: KeyboardEvent) {
  // 如果焦点在输入框，不处理
  const tag = (e.target as HTMLElement).tagName
  if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return
  
  // 只在有结果时处理
  if (!result.value) return
  
  switch (e.key) {
    case 'ArrowLeft':
    case '[': {
      const idx = TAB_ORDER.indexOf(activeTab.value)
      if (idx > 0) activeTab.value = TAB_ORDER[idx - 1]
      e.preventDefault()
      break
    }
    case 'ArrowRight':
    case ']': {
      const idx = TAB_ORDER.indexOf(activeTab.value)
      if (idx < TAB_ORDER.length - 1) activeTab.value = TAB_ORDER[idx + 1]
      e.preventDefault()
      break
    }
    case 'Escape':
      selectedPalace.value = null
      e.preventDefault()
      break
    case '1': case '2': case '3': case '4': case '5': case '6':
    case '7': case '8': case '9': case '0': {
      // 数字键选择宫位 (1=命,2=兄,...)
      const num = e.key === '0' ? 10 : parseInt(e.key, 10)
      if (num <= result.value.palaces.length) {
        const palace = result.value.palaces[num - 1]
        if (palace) selectPalace(palace)
      }
      e.preventDefault()
      break
    }
    case '?':
    case '/': {
      // 显示/隐藏快捷键帮助
      if (e.shiftKey || e.key === '?') {
        showHotkeyPanel.value = !showHotkeyPanel.value
        e.preventDefault()
      }
      break
    }
    case 'f':
    case 's': {
      // Ctrl/Cmd+F 或 S 打开星曜搜索
      if (e.ctrlKey || e.metaKey || e.key === 's') {
        showStarSearch.value = true
        e.preventDefault()
        nextTick(() => {
          const input = document.querySelector<HTMLInputElement>('.star-search-input')
          input?.focus()
        })
      }
      break
    }
  }
}

// ── 状态 ──────────────────────────────────────────────
const loading  = ref(false)
const error    = ref('')
const result   = ref<ZiweiResponse | null>(null)
const activeTab = ref<'chart' | 'summary' | 'palaces' | 'dayun' | 'liunian' | 'liuyue' | 'patterns' | 'flying' | 'forecast' | 'suggest'>('chart')
const selectedPalace = ref<PalaceResponse | null>(null)

// ── C-1: 盘面类型切换（飞星/三合/四化）───────────────────
const chartMode = ref<'sanhe' | 'feixing' | 'sihua'>('sanhe')

// ── C-7: 限流系统状态 ─────────────────────────────────────
const selectedDaxianIdx = ref<number>(-1)    // -1 = 自动（当前大运）
const selectedLiunianYear = ref<number>(new Date().getFullYear())
const selectedLiuyueMonth = ref<number>(0)   // 0 = 不选择，1-12 = 具体月份
const showLiunianOverlay = ref(false)        // 是否叠加流年显示

// ── C-3: 四化连线控制 ─────────────────────────────────────
const showSihuaLines = ref(false)            // 是否显示四化飞星 SVG 连线
const expandedLiuyue = ref<number | null>(null)  // 展开的流月索引
const expandedForecastMonth = ref<number | null>(null)  // 展开的月度运势索引

// ── 四柱八字菜单状态 ──────────────────────────────────────
const baziMenuActive = ref<'shengchen' | 'sizhu' | 'ribuzhu' | 'wuxing' | 'canggan' | 'shenshai' | 'chonghehexpo' | 'geju' | 'dayun' | 'shishen'>('sizhu')  // 当前选中的四柱子菜单
const baziDayunFocusIdx = ref<number>(-1)
const baziCopyDone = ref(false)
const baziMenuItems = {
  'shengchen': '1.1 生辰数据',
  'sizhu': '1.2 四柱基础',
  'ribuzhu': '1.3 日主与十神',
  'wuxing': '1.4 五行分析',
  'canggan': '1.5 藏干/纳音/生肖',
  'shenshai': '1.6 神煞与定位',
  'chonghehexpo': '1.7 冲合刑破',
  'geju': '1.8 格局判定与用神',
  'dayun': '1.9 大运/流年/流月',
  'shishen': '1.10 十神宫位用法',
}

// ── C-4: 星曜显示控制 ─────────────────────────────────────
const starDisplayOpts = ref({
  showMainStars: true,      // 显示主星
  showAuxStars: true,       // 显示辅星
  showTransforms: true,     // 显示四化
  showBrightness: true,     // 显示亮度
  showChangsheng: true,     // 显示长生12神
  showBoshi: false,         // 显示博士十二星（默认关闭）
  showJiangSui: false,      // 显示将前/岁前（默认关闭）
  auxLimit: 8,              // 辅星最大显示数量（0=不限制）
})

// ── 叠加层显示控制 ─────────────────────────────────────────
const overlayOpts = ref({
  showDaxian: true,         // 显示大限叠加
  showLiunian: true,        // 显示流年叠加
  showLiuyue: false,        // 显示流月叠加（默认关闭）
  showXiaoxian: false,      // 显示小限叠加（默认关闭）
})

function parseZiweiApiError(e: unknown, fallback: string): string {
  const detail = (e as {
    response?: { data?: { detail?: unknown; message?: string } }
    message?: string
  })?.response?.data?.detail

  if (typeof detail === 'string' && detail.trim()) {
    return detail
  }

  if (Array.isArray(detail)) {
    const msgs = detail
      .map((item) => {
        if (typeof item === 'string') return item
        if (item && typeof item === 'object') {
          const maybeMsg = (item as { msg?: unknown }).msg
          if (typeof maybeMsg === 'string') return maybeMsg
        }
        return ''
      })
      .filter(Boolean)
    if (msgs.length) return msgs.join('；')
  }

  if (detail && typeof detail === 'object') {
    const maybeMsg = (detail as { message?: unknown }).message
    if (typeof maybeMsg === 'string' && maybeMsg.trim()) {
      return maybeMsg
    }
  }

  const directMsg = (e as { message?: string })?.message
  if (typeof directMsg === 'string' && directMsg.trim()) {
    return directMsg
  }

  return fallback
}

function validateZiweiForm(): string | null {
  if (!Number.isInteger(year.value) || year.value < 1900 || year.value > 2100) {
    return '年份需在 1900-2100 之间'
  }
  if (!Number.isInteger(month.value) || month.value < 1 || month.value > 12) {
    return '月份需在 1-12 之间'
  }
  if (!Number.isInteger(day.value) || day.value < 1 || day.value > 31) {
    return '日期需在 1-31 之间'
  }
  if (!Number.isInteger(hour.value) || hour.value < 0 || hour.value > 23) {
    return '小时需在 0-23 之间'
  }
  if (!Number.isInteger(minute.value) || minute.value < 0 || minute.value > 59) {
    return '分钟需在 0-59 之间'
  }
  if (!['男', '女'].includes(gender.value)) {
    return '性别仅支持 男/女'
  }
  const validDate = new Date(year.value, month.value - 1, day.value)
  if (
    validDate.getFullYear() !== year.value ||
    validDate.getMonth() !== month.value - 1 ||
    validDate.getDate() !== day.value
  ) {
    return '日期不合法，请检查年月日'
  }
  if (longitude.value !== undefined && longitude.value !== null) {
    if (!Number.isFinite(longitude.value) || longitude.value < -180 || longitude.value > 180) {
      return '经度需在 -180 到 180 之间'
    }
  }
  return null
}

function clearSavedCaseState() {
  savedCaseId.value = ''
  savedCaseName.value = ''
  currentSnapshotId.value = ''
}

// ── 计算 ──────────────────────────────────────────────
async function doCalculate() {
  const validationError = validateZiweiForm()
  if (validationError) {
    error.value = validationError
    return
  }

  loading.value = true
  error.value   = ''
  result.value  = null
  selectedPalace.value = null
  clearSavedCaseState()
  try {
    result.value = await computeZiwei({
      year: year.value,
      month: month.value,
      day: day.value,
      hour: hour.value,
      minute: minute.value,
      gender: gender.value,
      liunian_year: liunianYear.value || undefined,
      longitude: longitude.value || undefined,
      late_zishi: algoLateZishi.value,
      leap_month_method: algoLeapMethod.value,
      kuiyue_method: algoKuiyue.value,
      sihua_stem_indices: buildSihuaIndices(),
      tianma_method: algoTianma.value,
      tiankong_method: algoTiankong.value,
      brightness_method: algoBrightness.value,
      jiukong_method: algoJiukong.value,
      tianshang_method: algoTianshang.value,
      mingzhu_method: algoMingzhu.value,
      liunian_sihua_method: algoLiunianSihua.value,
      changsheng_method: algoChangsheng.value,
    })
    activeTab.value = 'chart'
    // 保存到历史记录
    saveToHistory()
    chartHistory.value = loadHistory()
  } catch (e: unknown) {
    error.value = parseZiweiApiError(e, '排盘失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

async function doDemo() {
  loading.value = true
  error.value   = ''
  result.value  = null
  selectedPalace.value = null
  clearSavedCaseState()
  try {
    result.value = await demoZiwei()
    activeTab.value = 'chart'
  } catch (e: unknown) {
    error.value = parseZiweiApiError(e, '演示命盘加载失败')
  } finally {
    loading.value = false
  }
}

function resetForm() {
  const bd = profile.parseBirthDt()
  year.value   = bd.year; month.value = bd.month; day.value = bd.day
  hour.value   = bd.hour; minute.value = bd.minute
  gender.value = profile.gender === 'female' ? '女' : '男'
  liunianYear.value = undefined
  longitude.value = profile.lon
  initCity.value  = profile.cityName || '北京'
  result.value = null; error.value = ''
  clearSavedCaseState()
}

// ── 12宫网格（3×4布局，顺时针） ─────────────────────
// 按传统紫微命盘布局（地支固定位置）：
// [巳 午 未 申]  上行  branch_idx: 5,6,7,8
// [辰 --宫-- 酉]  中行  branch_idx: 4,  ,  ,9
// [卯 --宫-- 戌]  中行  branch_idx: 3,  ,  ,10
// [寅 丑 子 亥]  下行  branch_idx: 2,1,0,11
// GRID_ORDER 中的数字是地支索引（0=子, 5=巳...），需按地支查找宫位
const GRID_ORDER_BRANCHES = [5,6,7,8, 4,-1,-1,9, 3,-1,-1,10, 2,1,0,11] // branch indices

const palaceGrid = computed(() => {
  if (!result.value) return []
  const palaces = result.value.palaces
  // 构建地支字符串 → 宫位的映射（branch字段为地支文字如"子"）
  const _BRANCH_CHARS = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
  const branchToPalace = new Map<number, import('@/api/ziwei').PalaceResponse>()
  for (const p of palaces) {
    const bi = _BRANCH_CHARS.indexOf(p.branch)
    if (bi >= 0) branchToPalace.set(bi, p)
  }
  let centerAdded = false
  return GRID_ORDER_BRANCHES.map((branchIdx, pos) => {
    if (branchIdx === -1) {
      if (centerAdded) return null   // 只保留第一个中宫格，其余跳过
      centerAdded = true
      return { empty: true, pos }
    }
    const p = branchToPalace.get(branchIdx)
    return { empty: false, pos, palace: p }
  }).filter(Boolean) as Array<{ empty: boolean; pos: number; palace?: import('@/api/ziwei').PalaceResponse }>
})

// ── 当前大运 ──────────────────────────────────────────
const currentYear = new Date().getFullYear()
const currentMonth = new Date().getMonth() + 1  // 1-12
const currentDayun = computed(() => {
  if (!result.value?.dayun?.items) return null
  return result.value.dayun.items.find(
    d => d.start_year <= currentYear && (d.start_year + 10) > currentYear
  ) ?? null
})

// ── C-7: 流年年份范围（基于大运起始年 ±20年） ──────────────
const liunianYears = computed(() => {
  const center = selectedLiunianYear.value || currentYear
  const years: number[] = []
  for (let y = center - 5; y <= center + 10; y++) {
    years.push(y)
  }
  return years
})

// ── 流年下拉选择器年份范围 ───────────────────────────────
const allLiunianYears = computed(() => {
  const years: number[] = []
  // 提供从1930到2080的年份范围
  for (let y = 1930; y <= 2080; y++) {
    years.push(y)
  }
  return years
})

// ── 宫位→大限映射（干支匹配） ─────────────────────────
const palaceDayunMap = computed(() => {
  if (!result.value?.dayun?.items || !result.value?.palaces) return {} as Record<number, DayunItem>
  const map: Record<number, DayunItem> = {}
  result.value.dayun.items.forEach(d => {
    const idx = result.value!.palaces.findIndex(p => (p.stem + p.branch) === d.ganzhi)
    if (idx >= 0) map[idx] = d
  })
  return map
})

// ══════════════════════════════════════════════════════════════════
// C-3: 四化飞星 SVG 连线计算
// ══════════════════════════════════════════════════════════════════

// 地支索引 → 4x4 网格坐标 (col, row)（固定传统布局，地支位置永不变）
// 巳(5)午(6)未(7)申(8) 上行 / 辰(4) 酉(9) 中行 / 卯(3) 戌(10) 中行 / 寅(2)丑(1)子(0)亥(11) 下行
const BRANCH_TO_GRID: Record<number, [number, number]> = {
  5: [0, 0], 6: [1, 0], 7: [2, 0], 8: [3, 0],   // 巳午未申
  4: [0, 1],                        9: [3, 1],   // 辰  酉
  3: [0, 2],                       10: [3, 2],   // 卯  戌
  2: [0, 3], 1: [1, 3], 0: [2, 3], 11: [3, 3],   // 寅丑子亥
}
const _BRANCH_CHARS_SIHUA = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']

// 四化颜色配置
const SIHUA_COLORS: Record<string, { color: string; label: string }> = {
  '化禄': { color: '#22c55e', label: 'A' },  // 绿
  '化权': { color: '#f97316', label: 'B' },  // 橙
  '化科': { color: '#3b82f6', label: 'C' },  // 蓝
  '化忌': { color: '#ef4444', label: 'D' },  // 红
}

interface SihuaLine {
  fromBranchIdx: number
  toBranchIdx: number
  starName: string
  transform: string
  color: string
  label: string
  isSelfHua: boolean
}

// 计算四化连线数据 - 只显示选中宫位的飞出连线，避免显示过于杂乱
const sihuaLines = computed((): SihuaLine[] => {
  if (!result.value?.palaces || !showSihuaLines.value) return []
  // 只有选中宫位才显示连线
  if (!selectedPalace.value) return []

  const lines: SihuaLine[] = []
  const palace = selectedPalace.value
  // 使用地支（branch字符串）映射到地支索引，保证与固定网格坐标对齐
  const fromBranchIdx = _BRANCH_CHARS_SIHUA.indexOf(palace.branch)
  if (fromBranchIdx < 0) return []

  if (palace.flying_out) {
    Object.entries(palace.flying_out).forEach(([starName, transform]) => {
      const cfg = SIHUA_COLORS[transform]
      if (!cfg) return

      // 找目标宫：哪个宫有这颗星，取其地支索引
      const targetPalace = result.value!.palaces.find(p =>
        p.main_stars.some(s => s.name === starName) ||
        p.aux_stars.includes(starName)
      )
      if (!targetPalace) return
      const toBranchIdx = _BRANCH_CHARS_SIHUA.indexOf(targetPalace.branch)
      if (toBranchIdx < 0) return

      lines.push({
        fromBranchIdx,
        toBranchIdx,
        starName,
        transform,
        color: cfg.color,
        label: cfg.label,
        isSelfHua: fromBranchIdx === toBranchIdx,
      })
    })
  }
  return lines
})

// 宫位中心坐标（百分比）—— 按地支索引查固定网格坐标
function getPalaceCenter(branchIdx: number): { x: number; y: number } {
  const grid = BRANCH_TO_GRID[branchIdx]
  if (!grid) return { x: 50, y: 50 }
  const [col, row] = grid
  const x = col * 25 + 12.5
  const y = row * 25 + 12.5
  return { x, y }
}

// 获取宫位边缘点（朝向目标宫位的边缘）
function getPalaceEdge(fromIdx: number, toIdx: number): { x: number; y: number } {
  const from = getPalaceCenter(fromIdx)
  const to = getPalaceCenter(toIdx)
  
  // 计算方向向量
  const dx = to.x - from.x
  const dy = to.y - from.y
  const len = Math.sqrt(dx * dx + dy * dy)
  if (len === 0) return from
  
  // 宫格尺寸约为 25x25，边缘偏移约 10
  const offset = 8
  return {
    x: from.x + (dx / len) * offset,
    y: from.y + (dy / len) * offset
  }
}

// 生成弧线路径（使用二次贝塞尔曲线）
function getCurvedPath(fromIdx: number, toIdx: number, curveOffset: number = 0.15): string {
  const fromEdge = getPalaceEdge(fromIdx, toIdx)
  const toEdge = getPalaceEdge(toIdx, fromIdx)
  
  // 计算中点和垂直偏移作为控制点
  const midX = (fromEdge.x + toEdge.x) / 2
  const midY = (fromEdge.y + toEdge.y) / 2
  
  // 计算垂直方向（顺时针偏移）
  const dx = toEdge.x - fromEdge.x
  const dy = toEdge.y - fromEdge.y
  const len = Math.sqrt(dx * dx + dy * dy)
  
  // 控制点偏移（垂直于连线方向，向外弯曲）
  const perpX = -dy / len * len * curveOffset
  const perpY = dx / len * len * curveOffset
  
  const ctrlX = midX + perpX
  const ctrlY = midY + perpY
  
  // 返回二次贝塞尔曲线路径
  return `M ${fromEdge.x} ${fromEdge.y} Q ${ctrlX} ${ctrlY} ${toEdge.x} ${toEdge.y}`
}

// 获取弧线中点（用于放置标签）
function getCurvedMidpoint(fromIdx: number, toIdx: number, curveOffset: number = 0.15): { x: number; y: number } {
  const fromEdge = getPalaceEdge(fromIdx, toIdx)
  const toEdge = getPalaceEdge(toIdx, fromIdx)
  
  const midX = (fromEdge.x + toEdge.x) / 2
  const midY = (fromEdge.y + toEdge.y) / 2
  
  const dx = toEdge.x - fromEdge.x
  const dy = toEdge.y - fromEdge.y
  const len = Math.sqrt(dx * dx + dy * dy)
  
  const perpX = -dy / len * len * curveOffset * 0.5
  const perpY = dx / len * len * curveOffset * 0.5
  
  return { x: midX + perpX, y: midY + perpY }
}

// ── 四化颜色样式 ──────────────────────────────────────
function tfColorStyle(t: string): Record<string, string> {
  const colors: Record<string, string> = {
    '化禄': '#16a34a', '化权': '#dc2626', '化科': '#2563eb', '化忌': '#7c3aed',
  }
  return { background: colors[t] ?? '#888', color: '#fff' }
}

function tfOutlineStyle(t: string): Record<string, string> {
  const colors: Record<string, string> = {
    '化禄': '#166534',
    '化权': '#991b1b',
    '化科': '#1e40af',
    '化忌': '#5b21b6',
  }
  return { color: colors[t] ?? '#475569', background: 'transparent' }
}

// ── 五行局颜色 ────────────────────────────────────────
const JU_COLORS: Record<number, string> = {
  2: 'var(--wx-water)', 3: 'var(--wx-wood)',
  4: 'var(--wx-metal)', 5: 'var(--wx-earth)', 6: 'var(--wx-fire)',
}
const BRANCHES = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
const ZODIAC_ANIMALS = ['鼠','牛','虎','兔','龙','蛇','马','羊','猴','鸡','狗','猪']

// ── 当前大运干支 ──────────────────────────
const currentDayunGz = computed(() => {
  if (!result.value?.dayun?.items?.length) return ''
  const cur = result.value.dayun.items.find(d => 
    d.start_year <= currentYear && (d.start_year + 10) > currentYear
  )
  return cur?.ganzhi || ''
})

// ── 大运统计与进度 ────────────────────────────────
const dayunStats = computed(() => {
  const items = result.value?.dayun?.items ?? []
  let past = 0, current = 0, future = 0
  items.forEach(d => {
    if ((d.start_year + 10) <= currentYear) past++
    else if (d.start_year <= currentYear) current++
    else future++
  })
  return {
    total: items.length,
    past,
    current,
    future,
    startYear: items[0]?.start_year ?? 0,
    endYear: items.length ? items[items.length - 1].start_year + 9 : 0,
  }
})

const dayunProgress = computed(() => {
  const cur = currentDayun.value
  if (!cur) return null
  const yearsIn = currentYear - cur.start_year
  const pct = Math.min(100, Math.round((yearsIn / 10) * 100))
  return { yearsIn, yearsLeft: 10 - yearsIn, pct, ganzhi: cur.ganzhi }
})

// ── 格局等级样式 ──────────────────────────────────────
function patternClass(level: string) {
  const l = level?.toLowerCase() ?? ''
  if (l.includes('上') || l.includes('大') || l.includes('high')) return 'level-high'
  if (l.includes('中') || l.includes('med')) return 'level-med'
  return 'level-low'
}

// ── 格局统计 ──────────────────────────────────────────
const patternStats = computed(() => {
  if (!result.value?.patterns?.length) return { high: 0, med: 0, low: 0, total: 0 }
  let high = 0, med = 0, low = 0
  result.value.patterns.forEach(p => {
    const cls = patternClass(p.level)
    if (cls === 'level-high') high++
    else if (cls === 'level-med') med++
    else low++
  })
  return { high, med, low, total: result.value.patterns.length }
})

// ── 运势统计 ──────────────────────────────────────────
const forecastStats = computed(() => {
  if (!result.value?.forecast?.monthly?.length) {
    return { good: 0, mid: 0, low: 0, avg: 0, best: null as { period: string; score: number } | null, worst: null as { period: string; score: number } | null }
  }
  let good = 0, mid = 0, low = 0, sum = 0, count = 0
  let best = { period: '', score: 0 }
  let worst = { period: '', score: 100 }
  result.value.forecast.monthly.forEach(m => {
    if (m.score != null) {
      if (m.score >= 80) good++
      else if (m.score >= 50) mid++
      else low++
      sum += m.score
      count++
      if (m.score > best.score) best = { period: m.period, score: m.score }
      if (m.score < worst.score) worst = { period: m.period, score: m.score }
    }
  })
  return {
    good, mid, low,
    avg: count > 0 ? Math.round(sum / count) : 0,
    best: best.period ? best : null,
    worst: worst.period ? worst : null,
  }
})

const forecastMonthlyOverview = computed(() => {
  const monthly = result.value?.forecast?.monthly ?? []
  return monthly.map((item, index) => {
    const score = Number(item.score ?? 0)
    const scoreClamped = Math.max(0, Math.min(100, score))
    let level: 'good' | 'mid' | 'low' = 'low'
    if (scoreClamped >= 80) level = 'good'
    else if (scoreClamped >= 50) level = 'mid'
    return {
      index,
      score: scoreClamped,
      level,
      periodShort: (item.period || '').replace(/\(.+?\)/g, '').replace(/\s+/g, ''),
    }
  })
})

const forecastRiskMonths = computed(() =>
  forecastMonthlyOverview.value
    .filter(item => item.score > 0 && item.score < 50)
    .map(item => item.periodShort)
    .slice(0, 4),
)

const summaryQuickFacts = computed(() => {
  if (!result.value) return [] as Array<{ label: string; value: string }>
  const lunar = result.value.lunar
  const facts: Array<{ label: string; value: string }> = [
    { label: '公历', value: result.value.birth_solar || '-' },
    {
      label: '农历',
      value: lunar
        ? `${lunar.lunar_year}年${lunar.is_leap_month ? '闰' : ''}${lunar.lunar_month}月${lunar.lunar_day}日`
        : '-',
    },
    { label: '模板', value: result.value.template_version || 'standard' },
  ]

  if (result.value.true_solar_time) {
    facts.push({ label: '真太阳时', value: result.value.true_solar_time })
  }
  if (currentDayunGz.value) {
    facts.push({ label: '当前大运', value: currentDayunGz.value })
  }
  if (result.value.liunian?.year_gz) {
    facts.push({ label: '当前流年', value: `${result.value.liunian.year} ${result.value.liunian.year_gz}` })
  }
  return facts
})

const summaryInsightTags = computed(() => {
  if (!result.value) return [] as string[]
  const tags: string[] = []

  if (patternStats.value.high >= 2) {
    tags.push(`格局偏强（上格 ${patternStats.value.high}）`)
  } else if (patternStats.value.total > 0) {
    tags.push(`格局分布：上${patternStats.value.high}/中${patternStats.value.med}/普${patternStats.value.low}`)
  }

  if (forecastStats.value.avg >= 80) {
    tags.push(`流月均分较高（${forecastStats.value.avg}）`)
  } else if (forecastStats.value.avg > 0 && forecastStats.value.avg < 60) {
    tags.push(`近期波动偏大（均分 ${forecastStats.value.avg}）`)
  }

  if (detectedCombos.value.length >= 3) {
    tags.push(`检测到 ${detectedCombos.value.length} 组星曜组合`)
  }
  if (result.value.life_ruler_star) {
    tags.push(`命主星：${result.value.life_ruler_star}`)
  }
  if (result.value.body_ruler_star) {
    tags.push(`身主星：${result.value.body_ruler_star}`)
  }

  return tags.slice(0, 6)
})

// ── 首屏关键结论卡 ────────────────────────────────────
const summaryKeyConclusions = computed(() => {
  if (!result.value) return [] as Array<{ title: string; content: string; tag: string; type: 'good' | 'warn' | 'info' }>
  const items: Array<{ title: string; content: string; tag: string; type: 'good' | 'warn' | 'info' }> = []

  // 1. 最高格局
  const top = patternHighlights.value[0]
  if (top) {
    const extra = patternStats.value.total > 1 ? `，共 ${patternStats.value.total} 格局` : ''
    items.push({
      title: '命盘格局',
      content: top.name + extra,
      tag: top.cls === 'level-high' ? '上格' : top.cls === 'level-med' ? '中格' : '普格',
      type: top.cls === 'level-high' ? 'good' : 'info',
    })
  }

  // 2. 当前运势摘要
  const dyParts: string[] = []
  if (currentDayunGz.value) dyParts.push(`大运 ${currentDayunGz.value}`)
  if (result.value.liunian?.year_gz) dyParts.push(`流年 ${result.value.liunian.year_gz}`)
  if (forecastStats.value.avg > 0) dyParts.push(`均分 ${forecastStats.value.avg}`)
  if (dyParts.length) {
    const avg = forecastStats.value.avg
    items.push({
      title: '当前运势',
      content: dyParts.join(' · '),
      tag: avg >= 75 ? '旺' : avg >= 55 ? '平' : avg > 0 ? '弱' : '-',
      type: avg >= 75 ? 'good' : avg > 0 && avg < 55 ? 'warn' : 'info',
    })
  }

  // 3. 化忌落命宫 → 警示；否则取重点低分月
  const lifeJi = (sihuaByType.value['忌'] ?? []).filter(p => p.source === '命宫')
  if (lifeJi.length) {
    items.push({
      title: '化忌提示',
      content: `${lifeJi.map(p => p.star).join('、')} 化忌在命宫`,
      tag: '注意',
      type: 'warn',
    })
  } else if (forecastRiskMonths.value.length) {
    items.push({
      title: '重点关注',
      content: `低分月：${forecastRiskMonths.value.join('、')}`,
      tag: '提示',
      type: 'warn',
    })
  }

  // 4. 命身主星
  const rulers = [result.value.life_ruler_star, result.value.body_ruler_star].filter(Boolean).join(' / ')
  if (rulers) {
    items.push({
      title: '命身主星',
      content: rulers,
      tag: '参考',
      type: 'info',
    })
  }

  return items.slice(0, 4)
})

// ── 宫位统计 ──────────────────────────────────────────
const palaceFilter = ref<string>('')
const palacesStats = computed(() => {
  if (!result.value?.palaces?.length) return { total: 0, withMain: 0, withConclusion: 0 }
  let withMain = 0, withConclusion = 0
  result.value.palaces.forEach(p => {
    if (p.main_stars.length > 0) withMain++
    if (p.conclusion || p.analysis) withConclusion++
  })
  return { total: result.value.palaces.length, withMain, withConclusion }
})

const filteredPalaces = computed(() => {
  if (!result.value?.palaces?.length) return []
  if (!palaceFilter.value) return result.value.palaces
  const kw = palaceFilter.value.toLowerCase()
  return result.value.palaces.filter(p => 
    p.name.toLowerCase().includes(kw) ||
    p.main_stars.some(s => s.name.includes(kw))
  )
})

const PALACE_GROUPS = [
  { key: 'core', title: '核心宫位', names: ['命宫', '身宫'] },
  { key: 'career', title: '事业财禄', names: ['官禄宫', '财帛宫', '田宅宫', '福德宫'] },
  { key: 'relation', title: '关系家庭', names: ['夫妻宫', '子女宫', '兄弟宫', '父母宫'] },
  { key: 'movement', title: '迁移健康', names: ['迁移宫', '疾厄宫', '仆役宫', '交友宫'] },
] as const

const palaceGroupExpanded = ref<Record<string, boolean>>({
  core: true,
  career: true,
  relation: true,
  movement: true,
  other: true,
})

function togglePalaceGroup(groupKey: string) {
  palaceGroupExpanded.value[groupKey] = !palaceGroupExpanded.value[groupKey]
}

const groupedFilteredPalaces = computed(() => {
  const source = filteredPalaces.value
  const used = new Set<number>()
  const groups: Array<{ key: string; title: string; items: PalaceResponse[] }> = PALACE_GROUPS.map(group => {
    const items = source.filter(p => group.names.includes(p.name as never))
    items.forEach(p => used.add(p.index))
    return {
      key: group.key,
      title: group.title,
      items,
    }
  })
  const otherItems = source.filter(p => !used.has(p.index))
  if (otherItems.length) {
    groups.push({
      key: 'other',
      title: '其他宫位',
      items: otherItems,
    })
  }
  return groups.filter(g => g.items.length > 0)
})

// ── 格局分组展示 ──────────────────────────────────────
const patternViewMode = ref<'list' | 'group'>('group')
const groupedPatterns = computed(() => {
  if (!result.value?.patterns?.length) return { high: [], med: [], low: [] }
  const high: typeof result.value.patterns = []
  const med: typeof result.value.patterns = []
  const low: typeof result.value.patterns = []
  result.value.patterns.forEach(p => {
    const cls = patternClass(p.level)
    if (cls === 'level-high') high.push(p)
    else if (cls === 'level-med') med.push(p)
    else low.push(p)
  })
  return { high, med, low }
})

function patternWeight(level: string): number {
  const cls = patternClass(level)
  if (cls === 'level-high') return 3
  if (cls === 'level-med') return 2
  return 1
}

const sortedPatterns = computed(() => {
  const patterns = result.value?.patterns ?? []
  return [...patterns].sort((a, b) => {
    const wa = patternWeight(a.level)
    const wb = patternWeight(b.level)
    if (wa !== wb) return wb - wa
    const sa = (a.stars?.length || 0) + (a.palaces?.length || 0)
    const sb = (b.stars?.length || 0) + (b.palaces?.length || 0)
    return sb - sa
  })
})

const patternHighlights = computed(() =>
  sortedPatterns.value.slice(0, 3).map((p) => ({
    name: p.name,
    level: p.level,
    cls: patternClass(p.level),
  })),
)

// ── 飞星筛选 ──────────────────────────────────────────
const flyingFilter = ref<'all' | 'lu' | 'quan' | 'ke' | 'ji'>('all')
const filteredFlyingPalaces = computed(() => {
  if (!result.value?.flying?.palaces?.length) return []
  if (flyingFilter.value === 'all') return result.value.flying.palaces
  const tfMap: Record<string, string> = { lu: '禄', quan: '权', ke: '科', ji: '忌' }
  const target = tfMap[flyingFilter.value]
  return result.value.flying.palaces.filter(fp => {
    if (!fp.flying_out) return false
    return Object.values(fp.flying_out).some(t => t.includes(target))
  })
})

// ── 飞星关键洞察 ──────────────────────────────────────────────────────────────
const flyingKeyInsights = computed(() => {
  const flying = result.value?.flying
  if (!flying) return [] as Array<{ type: string; label: string; palaces: string[]; cls: string }>

  const TF_TYPES = ['禄', '权', '科', '忌'] as const
  type TfType = typeof TF_TYPES[number]
  const TF_CLS: Record<TfType, string> = { '禄': 'fi-lu', '权': 'fi-quan', '科': 'fi-ke', '忌': 'fi-ji' }

  const groups: Record<TfType, string[]> = { '禄': [], '权': [], '科': [], '忌': [] }

  const received = flying.received
  if (received) {
    Object.entries(received).forEach(([palace, transforms]) => {
      getReceivedTransformTexts(transforms as FlyingReceivedItem).forEach(t => {
        TF_TYPES.forEach(tf => {
          if (t.includes(tf) && !groups[tf].includes(palace)) groups[tf].push(palace)
        })
      })
    })
  } else {
    ;(flying.palaces ?? []).forEach(fp => {
      Object.values(fp.flying_out ?? {}).forEach(t => {
        TF_TYPES.forEach(tf => {
          if (t.includes(tf)) {
            const target = fp.opposition_palace || fp.palace_name
            if (!groups[tf].includes(target)) groups[tf].push(target)
          }
        })
      })
    })
  }

  return TF_TYPES.map(tf => ({
    type: tf,
    label: tf === '忌' ? '化忌落宫' : `化${tf}落宫`,
    palaces: groups[tf],
    cls: TF_CLS[tf],
  })).filter(i => i.palaces.length > 0)
})

// ── 命盘快速洞察 ──────────────────────────────────────────────────────────────
const chartQuickInsights = computed(() => {
  if (!result.value) return [] as Array<{ label: string; value: string; sub?: string; cls?: string }>
  const items: Array<{ label: string; value: string; sub?: string; cls?: string }> = []

  const totalJi = (sihuaByType.value['忌'] ?? []).length
  if (totalJi > 0) {
    const jiPalaces = (sihuaByType.value['忌'] ?? []).map(p => p.source).join('、')
    items.push({ label: '化忌', value: `${totalJi}颗`, sub: jiPalaces, cls: 'cqi-ji' })
  }

  const totalLu = (sihuaByType.value['禄'] ?? []).length
  if (totalLu > 0) {
    const luStars = (sihuaByType.value['禄'] ?? []).map(p => p.star).join('、')
    items.push({ label: '化禄', value: `${totalLu}颗`, sub: luStars, cls: 'cqi-lu' })
  }

  const topDist = [...(starDistribution.value ?? [])].sort((a, b) => b.total - a.total)[0]
  if (topDist) {
    items.push({ label: '星曜最密', value: topDist.palaceName.replace('宫', ''), sub: `${topDist.total}颗星`, cls: 'cqi-dense' })
  }

  const lifeMainBright = lifePalaceMainStars.value.filter(s => getStarBrightnessValue(s) >= 3).length
  const lifeMainTotal = lifePalaceMainStars.value.length
  if (lifeMainTotal > 0) {
    items.push({ label: '命宫旺星', value: `${lifeMainBright}/${lifeMainTotal}`, sub: '主星庙旺', cls: lifeMainBright >= lifeMainTotal ? 'cqi-good' : 'cqi-normal' })
  }

  return items
})

// ── 建议页分类筛选 ──────────────────────────────────────────
const suggestCategoryFilter = ref<string>('all')
const suggestCategories = computed(() => {
  const cats = new Set<string>()
  ;(result.value?.life_suggestions ?? []).forEach(s => {
    const cat = s.category_label || s.category
    if (cat) cats.add(cat)
  })
  return Array.from(cats)
})
const filteredLifeSuggestions = computed(() => {
  const suggestions = result.value?.life_suggestions ?? []
  if (suggestCategoryFilter.value === 'all') return suggestions
  return suggestions.filter(s =>
    (s.category_label || s.category) === suggestCategoryFilter.value
  )
})
const sortedRemedies = computed(() => {
  const r = result.value?.remedies ?? []
  return [...r].sort((a, b) => (a.priority ?? 9) - (b.priority ?? 9))
})

// ── 四化追踪路径 ──────────────────────────────────────────
interface SihuaPath {
  type: '禄' | '权' | '科' | '忌'
  star: string
  source: string  // 宫位名
  target?: string // 落宫位置
  sourcePalaceIdx: number
}
const sihuaPathList = computed((): SihuaPath[] => {
  if (!result.value?.palaces) return []
  const paths: SihuaPath[] = []
  
  // 遍历所有宫位收集四化
  result.value.palaces.forEach((p, idx) => {
    // 主星四化
    p.main_stars?.forEach(s => {
      s.transforms?.forEach(tf => {
        paths.push({
          type: tf as '禄' | '权' | '科' | '忌',
          star: s.name,
          source: p.name,
          sourcePalaceIdx: idx,
        })
      })
    })
    // 辅星四化
    getAuxStars(p).forEach(s => {
      getStarTransforms(s).forEach((tf) => {
        paths.push({
          type: tf as '禄' | '权' | '科' | '忌',
          star: getStarName(s),
          source: p.name,
          sourcePalaceIdx: idx,
        })
      })
    })
  })
  return paths
})

// 按四化类型分组
const sihuaByType = computed(() => {
  const groups: Record<string, SihuaPath[]> = { '禄': [], '权': [], '科': [], '忌': [] }
  sihuaPathList.value.forEach(p => {
    if (groups[p.type]) groups[p.type].push(p)
  })
  return groups
})

// ── 星曜分布统计 ──────────────────────────────────────────
interface StarDistribution {
  palaceName: string
  palaceIdx: number
  mainCount: number
  auxCount: number
  total: number
  hasLu: boolean
  hasJi: boolean
}
const starDistribution = computed((): StarDistribution[] => {
  if (!result.value?.palaces) return []
  return result.value.palaces.map((p, idx) => {
    const mainStars = p.main_stars || []
    const auxStars = getAuxStars(p)
    const allTransforms = [
      ...mainStars.flatMap(s => getStarTransforms(s)),
      ...auxStars.flatMap(s => getStarTransforms(s))
    ]
    return {
      palaceName: p.name,
      palaceIdx: idx,
      mainCount: mainStars.length,
      auxCount: auxStars.length,
      total: mainStars.length + auxStars.length,
      hasLu: allTransforms.includes('禄'),
      hasJi: allTransforms.includes('忌'),
    }
  })
})

const maxStarsInPalace = computed(() => Math.max(...starDistribution.value.map(d => d.total), 1))

// ── 五行分布统计 ──────────────────────────────────────────
const WUXING_MAP: Record<string, string> = {
  '紫微': '土', '天机': '木', '太阳': '火', '武曲': '金', '天同': '水',
  '廉贞': '火', '天府': '土', '太阴': '水', '贪狼': '水', '巨门': '水',
  '天相': '水', '天梁': '土', '七杀': '金', '破军': '水',
  '文昌': '金', '文曲': '水', '左辅': '土', '右弼': '水',
  '天魁': '火', '天钺': '火', '禄存': '土', '天马': '火',
  '擎羊': '金', '陀罗': '金', '火星': '火', '铃星': '火',
  '地空': '火', '地劫': '火',
}
const WUXING_COLORS: Record<string, string> = {
  '金': '#d97706', '木': '#16a34a', '水': '#2563eb', '火': '#dc2626', '土': '#78716c'
}
interface WuxingDistribution {
  element: string
  count: number
  color: string
  stars: string[]
}
const wuxingDistribution = computed((): WuxingDistribution[] => {
  if (!result.value?.palaces) return []
  const counts: Record<string, string[]> = { '金': [], '木': [], '水': [], '火': [], '土': [] }
  
  result.value.palaces.forEach(p => {
    p.main_stars?.forEach(s => {
      const wx = WUXING_MAP[s.name]
      if (wx && counts[wx]) counts[wx].push(s.name)
    })
  })
  
  return ['金', '木', '水', '火', '土'].map(el => ({
    element: el,
    count: counts[el].length,
    color: WUXING_COLORS[el],
    stars: counts[el]
  }))
})

const maxWuxingCount = computed(() => Math.max(...wuxingDistribution.value.map(d => d.count), 1))

// ── 星曜组合提示 ──────────────────────────────────────────
interface StarCombo {
  name: string
  stars: string[]
  palace: string
  desc: string
  type: 'auspicious' | 'inauspicious' | 'neutral'
}
const STAR_COMBOS: Array<{ name: string; stars: string[]; desc: string; type: 'auspicious' | 'inauspicious' | 'neutral' }> = [
  { name: '紫府同宫', stars: ['紫微', '天府'], desc: '帝星与库星同宫，贵气重重', type: 'auspicious' },
  { name: '日月同宫', stars: ['太阳', '太阴'], desc: '日月双辉，阴阳调和', type: 'auspicious' },
  { name: '机月同梁', stars: ['天机', '太阴', '天同', '天梁'], desc: '四星会照，适合文职公职', type: 'auspicious' },
  { name: '府相朝垣', stars: ['天府', '天相'], desc: '双贵会照，官禄亨通', type: 'auspicious' },
  { name: '昌曲夹命', stars: ['文昌', '文曲'], desc: '双文夹命，才华出众', type: 'auspicious' },
  { name: '左右夹拱', stars: ['左辅', '右弼'], desc: '贵人相助，逢凶化吉', type: 'auspicious' },
  { name: '魁钺夹命', stars: ['天魁', '天钺'], desc: '贵人星夹命，遇难呈祥', type: 'auspicious' },
  { name: '禄马交驰', stars: ['禄存', '天马'], desc: '财禄流动，利于经商', type: 'auspicious' },
  { name: '杀破狼格', stars: ['七杀', '破军', '贪狼'], desc: '变动星曜，开创格局', type: 'neutral' },
  { name: '火贪格', stars: ['火星', '贪狼'], desc: '暴发之兆，宜把握时机', type: 'neutral' },
  { name: '铃贪格', stars: ['铃星', '贪狼'], desc: '偏财运佳，宜投机取巧', type: 'neutral' },
  { name: '羊陀夹命', stars: ['擎羊', '陀罗'], desc: '刑克星夹命，多是非', type: 'inauspicious' },
  { name: '火铃夹命', stars: ['火星', '铃星'], desc: '煞星夹命，性急躁', type: 'inauspicious' },
  { name: '空劫夹命', stars: ['地空', '地劫'], desc: '空亡星夹命，损失多', type: 'inauspicious' },
]

const detectedCombos = computed((): StarCombo[] => {
  if (!result.value?.palaces) return []
  const combos: StarCombo[] = []
  
  result.value.palaces.forEach(p => {
    const allStars = [
      ...(p.main_stars?.map(s => s.name) || []),
      ...(p.aux_stars || [])
    ]
    
    STAR_COMBOS.forEach(combo => {
      // 检查是否所有星曜都在此宫
      const allPresent = combo.stars.every(s => allStars.includes(s))
      // 或者检查2颗及以上的星曜组合
      const presentCount = combo.stars.filter(s => allStars.includes(s)).length
      
      if (allPresent || (combo.stars.length >= 3 && presentCount >= 2 && allPresent === false && combo.stars.length === presentCount + 1)) {
        // 避免重复
        if (!combos.find(c => c.name === combo.name && c.palace === p.name)) {
          combos.push({
            name: combo.name,
            stars: combo.stars.filter(s => allStars.includes(s)),
            palace: p.name,
            desc: combo.desc,
            type: combo.type,
          })
        }
      }
    })
  })
  
  return combos
})

// ══════════════════════════════════════════════════════════════════
// 键盘快捷键帮助面板
// ══════════════════════════════════════════════════════════════════
const showHotkeyPanel = ref(false)
const HOTKEY_LIST = [
  { key: '←/[', desc: '切换到上一个Tab' },
  { key: '→/]', desc: '切换到下一个Tab' },
  { key: 'Esc', desc: '关闭宫位详情面板' },
  { key: '1-9,0', desc: '选择第1-10个宫位' },
  { key: '?', desc: '打开/关闭快捷键帮助' },
]

// ══════════════════════════════════════════════════════════════════
// 星曜亮度图例
// ══════════════════════════════════════════════════════════════════
const showBrightnessLegend = ref(false)
const BRIGHTNESS_LEGEND = [
  { level: '庙', desc: '最旺，如鱼得水', color: '#dc2626', val: 5 },
  { level: '旺', desc: '次吉，力量强盛', color: '#ea580c', val: 4 },
  { level: '得', desc: '平吉，发挥正常', color: '#ca8a04', val: 3 },
  { level: '利', desc: '小吉，略受限制', color: '#65a30d', val: 2 },
  { level: '平', desc: '普通，力量一般', color: '#6b7280', val: 1 },
  { level: '陷', desc: '失势，力量受损', color: '#3b82f6', val: 0 },
]

// ══════════════════════════════════════════════════════════════════
// 全盘星曜搜索
// ══════════════════════════════════════════════════════════════════
const showStarSearch = ref(false)
const starSearchQuery = ref('')

// 收集全盘所有星曜
const allStarsInChart = computed(() => {
  if (!result.value?.palaces) return []
  const stars: Array<{ name: string; palace: string; palaceIdx: number; type: 'main' | 'aux'; brightness?: string; transforms?: string[] }> = []
  result.value.palaces.forEach((p, idx) => {
    p.main_stars.forEach(s => {
      stars.push({
        name: s.name,
        palace: p.name,
        palaceIdx: idx,
        type: 'main',
        brightness: s.brightness,
        transforms: s.transforms,
      })
    })
    p.aux_stars.forEach(s => {
      stars.push({
        name: s,
        palace: p.name,
        palaceIdx: idx,
        type: 'aux',
      })
    })
  })
  return stars
})

// 搜索结果
const starSearchResults = computed(() => {
  if (!starSearchQuery.value.trim()) return []
  const q = starSearchQuery.value.trim().toLowerCase()
  return allStarsInChart.value.filter(s => s.name.toLowerCase().includes(q))
})

// 选中搜索结果中的宫位
function selectSearchResult(palaceIdx: number) {
  if (!result.value?.palaces?.[palaceIdx]) return
  selectPalace(result.value.palaces[palaceIdx])
  showStarSearch.value = false
  starSearchQuery.value = ''
}

// ══════════════════════════════════════════════════════════════════
// 命盘历史记录功能
// ══════════════════════════════════════════════════════════════════
interface ChartHistory {
  id: string
  timestamp: number
  birthSolar: string
  gender: string
  lifePalaceGz: string
  wuxingJuName: string
  params: {
    year: number
    month: number
    day: number
    hour: number
    minute: number
    gender: string
    longitude?: number
  }
}

const HISTORY_KEY = 'ziwei_chart_history'
const MAX_HISTORY = 10
const showHistoryPanel = ref(false)

// 从 localStorage 加载历史
function loadHistory(): ChartHistory[] {
  try {
    const raw = localStorage.getItem(HISTORY_KEY)
    return raw ? JSON.parse(raw) : []
  } catch { return [] }
}

// 保存到历史
function saveToHistory() {
  if (!result.value) return
  const history = loadHistory()
  const newItem: ChartHistory = {
    id: Date.now().toString(),
    timestamp: Date.now(),
    birthSolar: result.value.birth_solar,
    gender: result.value.gender,
    lifePalaceGz: result.value.life_palace_gz,
    wuxingJuName: result.value.wuxing_ju_name,
    params: {
      year: year.value,
      month: month.value,
      day: day.value,
      hour: hour.value,
      minute: minute.value,
      gender: gender.value,
      longitude: longitude.value,
    }
  }
  // 去重：相同出生时间不重复添加
  const existIdx = history.findIndex(h => 
    h.params.year === newItem.params.year &&
    h.params.month === newItem.params.month &&
    h.params.day === newItem.params.day &&
    h.params.hour === newItem.params.hour &&
    h.params.gender === newItem.params.gender
  )
  if (existIdx >= 0) {
    history.splice(existIdx, 1)
  }
  history.unshift(newItem)
  if (history.length > MAX_HISTORY) history.pop()
  localStorage.setItem(HISTORY_KEY, JSON.stringify(history))
}

// 从历史恢复
function restoreFromHistory(item: ChartHistory) {
  year.value = item.params.year
  month.value = item.params.month
  day.value = item.params.day
  hour.value = item.params.hour
  minute.value = item.params.minute
  gender.value = item.params.gender as '男' | '女'
  longitude.value = item.params.longitude
  showHistoryPanel.value = false
  nextTick(() => doCalculate())
}

// 清空历史
function clearHistory() {
  localStorage.removeItem(HISTORY_KEY)
  showHistoryPanel.value = false
}

// 格式化时间
function formatHistoryTime(ts: number): string {
  const d = new Date(ts)
  return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`
}

// 计算后自动保存历史
const chartHistory = ref<ChartHistory[]>(loadHistory())

// ══════════════════════════════════════════════════════════════════
// 大运/流年/流月快速定位
// ══════════════════════════════════════════════════════════════════
function scrollToCurrentDayun() {
  const el = document.querySelector('.dayun-item.cur, .dt-node.dt-cur')
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    // 闪烁高亮
    el.classList.add('highlight-blink')
    setTimeout(() => el.classList.remove('highlight-blink'), 1500)
  }
}

function scrollToCurrentLiuyue() {
  const el = document.querySelector('.liuyue-item.liuyue-cur, .lyq-btn.lyq-cur')
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    el.classList.add('highlight-blink')
    setTimeout(() => el.classList.remove('highlight-blink'), 1500)
  }
}

// 流年年份快速选择
const showYearPicker = ref(false)
const yearPickerRange = computed(() => {
  const items = result.value?.dayun?.items
  if (!items?.length) return { start: currentYear - 30, end: currentYear + 30 }
  return {
    start: items[0].start_year,
    end: items[items.length - 1].start_year + 10
  }
})
const yearPickerList = computed(() => {
  const { start, end } = yearPickerRange.value
  const list = []
  for (let y = start; y <= end; y++) list.push(y)
  return list
})
function selectYearFromPicker(yr: number) {
  selectedLiunianYear.value = yr
  showYearPicker.value = false
  liunianYear.value = yr
  if (result.value) {
    void doCalculate()
  }
}

// ══════════════════════════════════════════════════════════════════
// 导出命盘为图片
// ══════════════════════════════════════════════════════════════════
const isExportingImage = ref(false)

function getChartExportElement(): HTMLElement | null {
  return document.querySelector('.palace-grid-wrap') as HTMLElement | null
    ?? document.querySelector('.chart-tab-panel') as HTMLElement | null
}

async function exportChartAsImage() {
  if (!result.value) {
    showOverlayFeedback('chart', '请先完成排盘再导出 PNG', 'error')
    return
  }

  if (activeTab.value !== 'chart') {
    activeTab.value = 'chart'
    await nextTick()
  }

  const chartEl = getChartExportElement()
  if (!chartEl) {
    showOverlayFeedback('chart', '未找到命盘区域，请稍后重试', 'error')
    return
  }
  
  isExportingImage.value = true
  try {
    const html2canvas = (await import('html2canvas')).default
    const canvas = await html2canvas(chartEl, {
      backgroundColor: '#fff',
      scale: 2,
      useCORS: true,
      logging: false,
    })
    
    // 下载图片
    const link = document.createElement('a')
    const birthInfo = result.value?.birth_solar || '命盘'
    link.download = `紫微命盘_${birthInfo.replace(/[^\d\u4e00-\u9fa5]/g, '_')}.png`
    link.href = canvas.toDataURL('image/png')
    link.click()
    showOverlayFeedback('chart', 'PNG 已开始下载')
  } catch (e) {
    console.error('导出图片失败:', e)
    showOverlayFeedback('chart', '导出 PNG 失败，请稍后重试', 'error')
  } finally {
    isExportingImage.value = false
  }
}

// ══════════════════════════════════════════════════════════════════
// 命盘分享功能
// ══════════════════════════════════════════════════════════════════
const showSharePanel = ref(false)
const shareLink = computed(() => {
  if (!result.value) return ''
  const params = new URLSearchParams({
    y: String(year.value),
    m: String(month.value),
    d: String(day.value),
    h: String(hour.value),
    mi: String(minute.value),
    g: gender.value,
  })
  if (longitude.value) params.set('lng', String(longitude.value))
  return `${window.location.origin}${window.location.pathname}?${params.toString()}`
})

function copyShareLink() {
  if (!shareLink.value) return
  navigator.clipboard.writeText(shareLink.value)
    .then(() => {
      alert('链接已复制到剪贴板')
      showSharePanel.value = false
    })
    .catch(() => alert('复制失败，请手动复制'))
}

// ══════════════════════════════════════════════════════════════════
// 案例保存 / 案例库
// ══════════════════════════════════════════════════════════════════
const savedCaseId = ref('')
const savedCaseName = ref('')
const currentSnapshotId = ref('')
const isSavingCase = ref(false)
const showCasesPanel = ref(false)
const caseList = ref<CaseOut[]>([])
const casesLoading = ref(false)
const casesError = ref('')
const casesKeyword = ref('')
const casesTotal = ref(0)
const casesOffset = ref(0)
const CASES_LIMIT = 10

const canSaveCurrentChart = computed(() => Boolean(result.value) && !isSavingCase.value)
const hasCasesPagination = computed(() => casesTotal.value > CASES_LIMIT)
const showSimilarPanel = ref(false)
const similarLoading = ref(false)
const similarStatus = ref('')
const similarResults = ref<SimilarResult[]>([])
const similarTotalIndexed = ref(0)
const similarTopK = ref(10)

const similarQuerySummary = computed(() => {
  if (!result.value) return '请先在主界面排盘，再使用相似盘检索。'
  return `查询命盘：${result.value.birth_solar} · ${result.value.gender} · 命宫 ${result.value.life_palace_gz} · ${result.value.wuxing_ju_name} · 格局 ${(result.value.patterns || []).length} 个`
})
const showSnapshotsPanel = ref(false)
const snapshotsLoading = ref(false)
const snapshotsError = ref('')
const snapshots = ref<SnapshotOut[]>([])
const snapshotCompareA = ref('')
const snapshotCompareB = ref('')
const snapshotDiffLoading = ref(false)
const snapshotDiffResult = ref<SnapshotDiffResponse | null>(null)
const snapshotDiffError = ref('')
const showReviewPanel = ref(false)
const reviewLoading = ref(false)
const reviewError = ref('')
const reviewStats = ref<ReviewStats | null>(null)
const reviewList = ref<ChartReviewResponse[]>([])
const REVIEW_ASSIGNEE_RECENTS_KEY = 'ziwei_review_assignee_recents'
const reviewListMode = ref<'all' | 'queue' | 'mine'>('all')
const reviewLastLoadedAt = ref('')
const reviewFilter = ref('all')
const reviewSelectedId = ref<number | null>(null)
const reviewSelectedNotes = ref('')
const reviewAssignInput = ref('reviewer')
const reviewRecentAssignees = ref<string[]>([])
const reviewAssigneeCandidates = ref<ReviewAssigneeItem[]>([])
const reviewSelectedHistory = ref<ReviewHistoryItem[]>([])
const reviewHistoryLoading = ref(false)
const reviewSubmitNotes = ref('')
const reviewBulkNotes = ref('')
const reviewBulkSelectedIds = ref<number[]>([])
const reviewActionLoading = ref(false)
const showLlmPanel = ref(false)
const llmConfigLabel = ref('未加载')
const llmStatus = ref('')
const llmLoading = ref(false)
const llmDrafts = ref<LlmDraft[]>([])
const llmFilterStatus = ref('')
const llmCurrentDraft = ref<LlmDraft | null>(null)
const llmCurrentText = ref('')
const llmReviewerNotes = ref('')
const llmCopied = ref(false)
const showOpsPanel = ref(false)
const opsLoading = ref(false)
const opsError = ref('')
const opsStats = ref<AdminStatsResponse | null>(null)
const opsExperiments = ref<ExperimentResponse[]>([])
const opsExperimentsTotal = ref(0)
const opsExperimentFilter = ref('all')
const opsExperimentSaving = ref(false)
const opsExperimentResults = ref<ExperimentResults | null>(null)
const opsExperimentResultsLoading = ref(false)
const opsStatus = ref('')
const opsCreateFormVisible = ref(false)
const opsCreateForm = ref({
  name: '',
  description: '',
  targetMetric: 'conversion',
  hypothesis: '',
  minSampleSize: 100,
  controlWeight: 50,
  variantWeight: 50,
})
const showBatchPanel = ref(false)
const batchSelectedFile = ref<File | null>(null)
const batchTemplateVersion = ref('')
const batchLoading = ref(false)
const batchStatus = ref('')
const batchError = ref('')
const showGlossaryPanel = ref(false)
const glossaryToolLoading = ref(false)
const glossaryToolError = ref('')
const glossaryToolSearch = ref('')
const glossaryToolCategory = ref('')
const glossaryToolItems = ref<GlossaryItem[]>([])
const glossaryCopiedTerm = ref('')
const showMultiCompatPanel = ref(false)
const multiCompatLoading = ref(false)
const multiCompatError = ref('')
const multiCompatResult = ref<MultiCompatResponse | null>(null)
const multiCompatPersons = ref<Array<ZiweiRequest>>([
  { year: 1992, month: 6, day: 15, hour: 8, minute: 0, gender: '女' },
])
const showFengshuiPanel = ref(false)
const fengshuiLoading = ref(false)
const fengshuiError = ref('')
const fengshuiRoomLoading = ref(false)
const fengshuiRoomError = ref('')
const fengshuiData = ref<FengshuiResponse | null>(null)
const fengshuiOptions = ref<FengshuiOptions | null>(null)
const fengshuiRoomResult = ref<RoomLayoutResponse | null>(null)
const fengshuiForm = ref({
  birthYear: year.value,
  gender: gender.value,
  houseFacing: '',
})
const fengshuiRooms = ref<Record<string, string>>({})
const overlayFeedback = ref<{ panel: string; type: 'success' | 'info' | 'error'; message: string } | null>(null)
let overlayFeedbackTimer: number | undefined

const currentReview = computed(() => reviewList.value.find((item) => item.id === reviewSelectedId.value) ?? null)
const reviewBulkSelectedCount = computed(() => reviewBulkSelectedIds.value.length)
const reviewCurrentViewCount = computed(() => reviewList.value.length)
const reviewAllVisibleSelected = computed(() => {
  const visibleIds = reviewList.value.map((item) => item.id)
  return visibleIds.length > 0 && visibleIds.every((id) => reviewBulkSelectedIds.value.includes(id))
})
const REVIEW_ASSIGNEE_ROLE_PRIORITY: Record<string, number> = {
  owner: 0,
  admin: 1,
  reviewer: 2,
  qa: 3,
  ops: 4,
  editor: 5,
}

function normalizeReviewRole(role?: string | null) {
  return (role || '').trim().toLowerCase()
}

function isReviewAssigneeRole(candidate: ReviewAssigneeItem) {
  if (candidate.is_current_user || candidate.is_admin) return true
  return normalizeReviewRole(candidate.role) in REVIEW_ASSIGNEE_ROLE_PRIORITY
}

function getReviewAssigneeRoleTag(candidate?: ReviewAssigneeItem | null) {
  if (!candidate) return ''
  if (candidate.is_current_user) return '当前'
  if (candidate.is_admin) return '管理员'
  const role = normalizeReviewRole(candidate.role)
  if (role === 'owner') return 'Owner'
  if (role === 'reviewer') return '审核'
  if (role === 'qa') return 'QA'
  if (role === 'ops') return '运营'
  if (role === 'editor') return '编辑'
  if (role === 'admin') return '管理'
  return candidate.role || ''
}

const reviewAssigneeServerCandidates = computed(() => [...reviewAssigneeCandidates.value]
  .filter((item) => isReviewAssigneeRole(item))
  .sort((a, b) => {
    const aPriority = a.is_current_user ? -2 : a.is_admin ? -1 : (REVIEW_ASSIGNEE_ROLE_PRIORITY[normalizeReviewRole(a.role)] ?? 99)
    const bPriority = b.is_current_user ? -2 : b.is_admin ? -1 : (REVIEW_ASSIGNEE_ROLE_PRIORITY[normalizeReviewRole(b.role)] ?? 99)
    if (aPriority !== bPriority) return aPriority - bPriority
    return a.username.localeCompare(b.username, 'zh-CN')
  }))

const reviewAssigneeName = computed(() => {
  const storeUsername = auth.username?.trim()
  if (storeUsername) return storeUsername
  const currentCandidate = reviewAssigneeServerCandidates.value.find((item) => item.is_current_user)
  return currentCandidate?.username || 'reviewer'
})
const reviewAssigneeCandidateMap = computed(() => new Map(reviewAssigneeServerCandidates.value.map((item) => [item.username, item])))
const reviewAssigneeQuickOptions = computed(() => {
  const seen = new Set<string>()
  const values: Array<{ username: string; tag: string; candidate?: ReviewAssigneeItem }> = []
  const pushValue = (username?: string | null, tag = '', candidate?: ReviewAssigneeItem) => {
    const normalized = username?.trim()
    if (!normalized || seen.has(normalized)) return
    seen.add(normalized)
    values.push({ username: normalized, tag, candidate })
  }

  pushValue(reviewAssigneeName.value, '当前', reviewAssigneeCandidateMap.value.get(reviewAssigneeName.value))
  reviewAssigneeServerCandidates.value.forEach((item) => {
    pushValue(item.username, getReviewAssigneeRoleTag(item), item)
  })
  pushValue(currentReview.value?.reviewer || '', '当前单', reviewAssigneeCandidateMap.value.get(currentReview.value?.reviewer || ''))
  reviewRecentAssignees.value.forEach((item) => pushValue(item, '最近', reviewAssigneeCandidateMap.value.get(item)))
  pushValue('qa-reviewer', '预设')
  pushValue('ops-reviewer', '预设')
  return values
})
const reviewModeTitle = computed(() => {
  if (reviewListMode.value === 'queue') return '待审队列'
  if (reviewListMode.value === 'mine') return '我的队列'
  return '全部审核记录'
})
const reviewLastLoadedLabel = computed(() => reviewLastLoadedAt.value ? `最后刷新 ${reviewLastLoadedAt.value}` : '尚未刷新')
const reviewBulkDisabledByMode = computed(() => reviewListMode.value === 'queue')
const reviewBulkModeHint = computed(() => {
  if (reviewListMode.value === 'queue') return '待审队列建议先领取到我的队列，再执行批量处理。'
  if (reviewListMode.value === 'mine') return '我的队列仅处理已归我的审核单，可直接执行批量处理。'
  return '全部记录支持跨状态批量操作，建议优先筛选后执行。'
})
const reviewMineModeStrongHint = computed(() => reviewListMode.value === 'mine'
  ? '当前为我的队列：建议优先处理已归我记录，避免跨人协作遗漏。'
  : '')
const reviewPanelTip = computed(() => {
  if (reviewListMode.value === 'queue') {
    return '当前展示待审核 FIFO 队列，可先领取再处理。'
  }
  if (reviewListMode.value === 'mine') {
    return '当前展示我的审核队列，适合集中处理已领取任务。'
  }
  return '建议先提交当前命盘，再在右侧完成批注、通过或修订处理。'
})
const reviewEmptyStateText = computed(() => {
  if (reviewListMode.value === 'queue') return '当前待审队列为空，可稍后刷新或先提交新的审核单'
  if (reviewListMode.value === 'mine') return '我的队列暂无待处理审核单，可先从待审队列领取'
  return '暂无审核记录，可先提交当前命盘进入审核队列'
})

function loadReviewRecentAssignees() {
  try {
    const raw = localStorage.getItem(REVIEW_ASSIGNEE_RECENTS_KEY)
    reviewRecentAssignees.value = raw ? JSON.parse(raw) : []
  } catch {
    reviewRecentAssignees.value = []
  }
}

function saveReviewRecentAssignee(assignee: string) {
  const normalized = assignee.trim()
  if (!normalized) return
  reviewRecentAssignees.value = [normalized, ...reviewRecentAssignees.value.filter((item) => item !== normalized)].slice(0, 6)
  localStorage.setItem(REVIEW_ASSIGNEE_RECENTS_KEY, JSON.stringify(reviewRecentAssignees.value))
}

async function loadReviewAssigneeCandidates() {
  try {
    const data = await getReviewAssignees()
    reviewAssigneeCandidates.value = data.items
  } catch {
    reviewAssigneeCandidates.value = []
  }
}
const glossarySuggestedTerms = computed(() => {
  if (!result.value) return [] as string[]

  const terms = [
    ...result.value.patterns.map((item) => item.name),
    result.value.life_ruler_star,
    result.value.body_ruler_star,
    ...result.value.palaces.flatMap((palace) => palace.main_stars.map((star) => star.name)),
  ]

  return Array.from(new Set(terms.filter((item): item is string => Boolean(item && item.trim())))).slice(0, 8)
})
const multiCompatBestPair = computed(() => {
  if (!multiCompatResult.value?.pairs?.length) return null
  return [...multiCompatResult.value.pairs].sort((a, b) => b.total_score - a.total_score)[0] ?? null
})
const multiCompatScoreLegend = computed(() => ([
  { label: '85+ 高契合', className: 'is-excellent', hint: '适合长期深度协作或亲密搭档' },
  { label: '70-84 良好', className: 'is-good', hint: '整体磨合顺畅，偶有分歧可协调' },
  { label: '55-69 中等', className: 'is-fair', hint: '可合作，但需要明确分工和边界' },
  { label: '55 以下 观察', className: 'is-low', hint: '建议先小范围配合，再决定长期协作' },
]))
const multiCompatActionAdvice = computed(() => {
  const bestPair = multiCompatBestPair.value
  if (!bestPair) return [] as string[]

  const pairLabel = `${getMultiCompatLabel(bestPair.person_a_idx)} × ${getMultiCompatLabel(bestPair.person_b_idx)}`
  if (bestPair.total_score >= 85) {
    return [
      `${pairLabel} 适合承担核心协作或关键沟通岗位。`,
      '可优先安排需要高信任度、持续配合的任务。',
    ]
  }
  if (bestPair.total_score >= 70) {
    return [
      `${pairLabel} 适合稳定配合，建议保持固定节奏协作。`,
      '可通过明确分工来进一步提升执行效率。',
    ]
  }
  if (bestPair.total_score >= 55) {
    return [
      `${pairLabel} 可先从小范围合作开始，逐步建立默契。`,
      '建议在任务边界、节奏和责任上提前约定。',
    ]
  }
  return [
    `${pairLabel} 当前更适合低耦合配合，不建议强绑定。`,
    '若必须合作，建议增加复核和中间同步节点。',
  ]
})
const fengshuiDirectionLegend = computed(() => {
  if (!fengshuiData.value) return [] as Array<{ direction: string; direction_zh: string; label: string; tone: 'good' | 'bad' }>

  return [
    ...fengshuiData.value.auspicious.map((item) => ({
      direction: item.direction,
      direction_zh: item.direction_zh,
      label: item.label,
      tone: 'good' as const,
    })),
    ...fengshuiData.value.inauspicious.map((item) => ({
      direction: item.direction,
      direction_zh: item.direction_zh,
      label: item.label,
      tone: 'bad' as const,
    })),
  ]
})
const fengshuiRoomBoardCells = computed(() => {
  const gridOrder = ['NW', 'N', 'NE', 'W', 'CENTER', 'E', 'SW', 'S', 'SE']
  const resultMap = new Map((fengshuiRoomResult.value?.cells || []).map((cell) => [cell.direction, cell]))

  return gridOrder.map((direction) => {
    if (direction === 'CENTER') {
      return {
        direction,
        directionLabel: '中宫',
        selectedRoom: '',
        resultCell: null,
        isCenter: true,
      }
    }

    return {
      direction,
      directionLabel: getDirectionBadgeLabel(direction),
      selectedRoom: fengshuiRooms.value[direction] || '',
      resultCell: resultMap.get(direction) || null,
      isCenter: false,
    }
  })
})
const fengshuiRecommendedRooms = computed(() => {
  if (!fengshuiRoomResult.value?.cells?.length) return [] as string[]

  return [...fengshuiRoomResult.value.cells]
    .sort((a, b) => b.assess_score - a.assess_score)
    .slice(0, 3)
    .map((cell) => `${cell.direction_zh}适合${cell.room_zh || getRoomTypeLabel(cell.room_type)}（${cell.assess_score}分）`)
})
const fengshuiAvoidRooms = computed(() => {
  if (!fengshuiRoomResult.value?.cells?.length) return [] as string[]

  return [...fengshuiRoomResult.value.cells]
    .sort((a, b) => a.assess_score - b.assess_score)
    .filter((cell) => cell.assess_level === 'poor' || cell.assess_level === 'fair' || cell.assess_score < 70)
    .slice(0, 3)
    .map((cell) => `${cell.direction_zh}暂不宜放${cell.room_zh || getRoomTypeLabel(cell.room_type)}（${cell.assess_note}）`)
})
const llmCurrentStatusLabel = computed(() => {
  const status = llmCurrentDraft.value?.status
  if (status === 'approved') return '已通过'
  if (status === 'rejected') return '已驳回'
  if (status === 'pending_review') return '待审核'
  return '未生成'
})

function getReviewStatusLabel(status?: string | null): string {
  if (status === 'approved') return '已通过'
  if (status === 'rejected') return '已拒绝'
  if (status === 'revised') return '修订中'
  if (status === 'pending') return '待审核'
  return status || '未知'
}

function getReviewStatusClass(status?: string | null): string {
  if (status === 'approved') return 'is-approved'
  if (status === 'rejected') return 'is-rejected'
  if (status === 'revised') return 'is-revised'
  if (status === 'pending') return 'is-pending'
  return 'is-unknown'
}

function getReviewHistoryTypeLabel(item?: ReviewHistoryItem | null): string {
  const changeType = item?.change_type
  if (changeType === 'bulk_action') return '批量操作'
  if (changeType === 'status_change') return '状态更新'
  if (changeType === 'assign') return '指派'
  if (changeType === 'created' || item?.action === 'created') return '创建'
  if (changeType === 'deleted') return '删除'
  return '记录'
}

function getReviewHistoryTypeClass(item?: ReviewHistoryItem | null): string {
  const changeType = item?.change_type
  if (changeType === 'bulk_action') return 'is-bulk'
  if (changeType === 'status_change') return 'is-status'
  if (changeType === 'assign') return 'is-assign'
  if (changeType === 'created' || item?.action === 'created') return 'is-created'
  if (changeType === 'deleted') return 'is-deleted'
  return 'is-default'
}

function isReviewOwnedByMe(item?: ChartReviewResponse | null): boolean {
  return Boolean(item?.reviewer && item.reviewer === reviewAssigneeName.value)
}

function getReviewOwnershipLabel(item?: ChartReviewResponse | null): string {
  if (!item) return '未分配'
  if (!item.reviewer) return '待领取'
  if (isReviewOwnedByMe(item)) return '已归我'
  return `已指派 ${item.reviewer}`
}

function getLlmDraftStatusLabel(status?: string | null): string {
  if (status === 'approved') return '已通过'
  if (status === 'rejected') return '已驳回'
  if (status === 'pending_review') return '待审核'
  return status || '未知'
}

function getExperimentStatusLabel(status?: string | null): string {
  if (status === 'draft') return '草稿'
  if (status === 'running') return '运行中'
  if (status === 'paused') return '已暂停'
  if (status === 'completed') return '已完成'
  return status || '未知'
}

function downloadBlobFile(blob: Blob, fileName: string) {
  const href = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = href
  anchor.download = fileName
  document.body.appendChild(anchor)
  anchor.click()
  document.body.removeChild(anchor)
  setTimeout(() => URL.revokeObjectURL(href), 1200)
}

function getMultiCompatLabel(index: number): string {
  return ['甲方', '乙方', '丙方', '丁方'][index] || `第${index + 1}人`
}

function getDirectionBadgeLabel(direction: string): string {
  return fengshuiOptions.value?.directions_zh?.[direction] || direction
}

function getRoomTypeLabel(roomType: string): string {
  return fengshuiOptions.value?.room_type_options?.[roomType] || roomType
}

function showOverlayFeedback(panel: string, message: string, type: 'success' | 'info' | 'error' = 'success') {
  overlayFeedback.value = { panel, message, type }
  if (overlayFeedbackTimer) {
    window.clearTimeout(overlayFeedbackTimer)
  }
  overlayFeedbackTimer = window.setTimeout(() => {
    if (overlayFeedback.value?.panel === panel && overlayFeedback.value?.message === message) {
      overlayFeedback.value = null
    }
  }, 2400)
}

function clearOverlayFeedback(panel?: string) {
  if (!panel || overlayFeedback.value?.panel === panel) {
    overlayFeedback.value = null
  }
}

function isOverlayFeedbackVisible(panel: string): boolean {
  return overlayFeedback.value?.panel === panel
}

function getGlossaryRelatedTerms(item: GlossaryItem): GlossaryItem[] {
  return glossaryToolItems.value
    .filter((candidate) => candidate.term !== item.term && (
      candidate.category === item.category
      || candidate.definition.includes(item.term)
      || item.definition.includes(candidate.term)
    ))
    .slice(0, 3)
}

async function copyGlossaryItem(item: GlossaryItem) {
  const copyText = [item.term, item.definition, item.classic_source ? `典籍：${item.classic_source}` : '']
    .filter(Boolean)
    .join('\n')

  try {
    await navigator.clipboard.writeText(copyText)
    glossaryCopiedTerm.value = item.term
    showOverlayFeedback('glossary', `已复制术语：${item.term}`)
  } catch {
    showOverlayFeedback('glossary', '复制失败，请手动复制', 'error')
  }
}

function useGlossarySuggestedTerm(term: string) {
  glossaryToolSearch.value = term
  loadGlossaryToolPanel()
}

function getMultiCompatMatrixCellClass(score: number, rowIndex: number, colIndex: number): string[] {
  if (rowIndex === colIndex) return ['is-self']

  const classes = ['is-score']
  if (score >= 85) classes.push('is-excellent')
  else if (score >= 70) classes.push('is-good')
  else if (score >= 55) classes.push('is-fair')
  else classes.push('is-low')

  if (multiCompatBestPair.value) {
    const { person_a_idx, person_b_idx } = multiCompatBestPair.value
    const isBestPair = (
      (rowIndex === person_a_idx && colIndex === person_b_idx)
      || (rowIndex === person_b_idx && colIndex === person_a_idx)
    )
    if (isBestPair) classes.push('is-best-pair')
  }

  return classes
}

function getMultiCompatPairClass(level?: string): string {
  if (level?.includes('极佳') || level?.includes('优秀')) return 'is-excellent'
  if (level?.includes('良')) return 'is-good'
  if (level?.includes('中')) return 'is-fair'
  return 'is-low'
}

function getMultiCompatCellHint(score: number, rowIndex: number, colIndex: number): string {
  if (rowIndex === colIndex) return `${getMultiCompatLabel(rowIndex)}与自己不参与配对评分`

  const pairLabel = `${getMultiCompatLabel(rowIndex)} × ${getMultiCompatLabel(colIndex)}`
  if (score >= 85) return `${pairLabel}：高契合，适合优先安排核心协作`
  if (score >= 70) return `${pairLabel}：整体良好，可稳定配合`
  if (score >= 55) return `${pairLabel}：中等匹配，建议先明确分工`
  return `${pairLabel}：需观察磨合，建议降低强绑定合作`
}

function getFengshuiRoomAssessClass(level?: string | null): string {
  if (!level) return 'is-empty'
  if (level === 'excellent') return 'is-excellent'
  if (level === 'good') return 'is-good'
  if (level === 'fair') return 'is-fair'
  return 'is-low'
}

function getFengshuiDirectionTag(direction: string): string {
  const good = fengshuiData.value?.auspicious.find((item) => item.direction === direction)
  if (good) return good.label
  const bad = fengshuiData.value?.inauspicious.find((item) => item.direction === direction)
  if (bad) return bad.label
  return '待评估'
}

function normalizeCaseGender(value: '男' | '女'): 'male' | 'female' {
  return value === '女' ? 'female' : 'male'
}

function buildCaseName(): string {
  const dateText = `${year.value}年${month.value}月${day.value}日 ${hour.value}时${String(minute.value).padStart(2, '0')}分`
  const suffix = result.value?.wuxing_ju_name ? ` · ${result.value.wuxing_ju_name}` : ''
  return `${dateText} ${gender.value}${suffix}`
}

function buildBirthDateLocal(): string {
  return `${year.value}-${String(month.value).padStart(2, '0')}-${String(day.value).padStart(2, '0')}T${String(hour.value).padStart(2, '0')}:${String(minute.value).padStart(2, '0')}`
}

function buildSimilarityHash(): string {
  const reportHash = result.value?.report_hash
  if (typeof reportHash === 'string' && reportHash.trim()) {
    return reportHash
  }
  return [
    year.value,
    month.value,
    day.value,
    hour.value,
    minute.value,
    gender.value,
    result.value?.life_palace_gz ?? '',
    result.value?.wuxing_ju_name ?? '',
  ].join('|')
}

function buildSnapshotInput(): Record<string, unknown> {
  return {
    year: year.value,
    month: month.value,
    day: day.value,
    hour: hour.value,
    minute: minute.value,
    gender: gender.value,
    longitude: longitude.value ?? null,
    liunian_year: liunianYear.value ?? null,
    template_version: result.value?.template_version ?? 'standard',
  }
}

function buildSimilarityPatternPayload() {
  return (result.value?.patterns || []).map((item) => ({
    name: item.name,
    level: item.level,
    description: item.description ?? '',
  }))
}

async function saveCurrentChart(silent = false) {
  if (!result.value || isSavingCase.value) return

  isSavingCase.value = true
  try {
    let caseId = savedCaseId.value
    const caseName = buildCaseName()

    if (!caseId) {
      const created = await createCase({
        name: caseName,
        birth_dt_local: buildBirthDateLocal(),
        tz: 'Asia/Shanghai',
        lon: longitude.value ?? profile.lon ?? 120,
        gender: normalizeCaseGender(gender.value),
        city: profile.cityName || initCity.value || null,
        solar_time_enabled: false,
      })
      caseId = created.id
      savedCaseId.value = created.id
      savedCaseName.value = created.name
    }

    const snapshot = await createSnapshot(caseId, {
      kind: 'ziwei',
      input_json: buildSnapshotInput(),
      output_json: result.value as unknown as Record<string, unknown>,
      api_version: result.value.algorithm_version || undefined,
      summary_engine_primary: result.value.engine_version || undefined,
    })
    currentSnapshotId.value = snapshot.id

    try {
      await indexChart({
        chart_hash: buildSimilarityHash(),
        birth_solar: result.value.birth_solar,
        birth_year: year.value,
        birth_month: month.value,
        birth_day: day.value,
        birth_hour: hour.value,
        gender: gender.value,
        wuxing_ju_name: result.value.wuxing_ju_name,
        life_palace_gz: result.value.life_palace_gz,
        patterns: buildSimilarityPatternPayload(),
        source_label: 'spa-ziwei',
      })
    } catch {
      // 相似盘索引失败不阻塞保存主流程
    }

    if (!savedCaseName.value) {
      savedCaseName.value = caseName
    }

    if (!silent) {
      alert(`已保存到案例库：${savedCaseName.value || caseName}`)
    }
  } catch (e: unknown) {
    const message = parseZiweiApiError(e, '保存命盘失败，请稍后重试')
    if (!silent) alert(message)
  } finally {
    isSavingCase.value = false
  }
}

async function loadCases(offset = 0) {
  casesLoading.value = true
  casesError.value = ''
  casesOffset.value = offset
  try {
    const data = await fetchCaseList({
      limit: CASES_LIMIT,
      offset,
      q: casesKeyword.value.trim() || undefined,
      order: 'updated_at',
      dir: 'desc',
    })
    caseList.value = data.items
    casesTotal.value = data.total
  } catch (e: unknown) {
    casesError.value = parseZiweiApiError(e, '案例库加载失败，请稍后重试')
  } finally {
    casesLoading.value = false
  }
}

function toggleCasesPanel() {
  showCasesPanel.value = !showCasesPanel.value
  if (showCasesPanel.value) {
    loadCases(0)
  }
}

async function searchCases() {
  await loadCases(0)
}

async function loadCaseChart(item: CaseOut) {
  try {
    const snapshots = await listSnapshots(item.id, { limit: 1, offset: 0 })
    const latest = snapshots[0]
    const input = latest?.input_json ?? null
    const output = latest?.output_json ?? null
    if (!output || typeof output !== 'object') {
      alert('该案例暂无可用快照，请重新排盘后再保存一次')
      return
    }

    if (input && typeof input === 'object') {
      year.value = Number((input as Record<string, unknown>).year ?? year.value)
      month.value = Number((input as Record<string, unknown>).month ?? month.value)
      day.value = Number((input as Record<string, unknown>).day ?? day.value)
      hour.value = Number((input as Record<string, unknown>).hour ?? hour.value)
      minute.value = Number((input as Record<string, unknown>).minute ?? minute.value)

      const inputGender = (input as Record<string, unknown>).gender
      if (inputGender === '男' || inputGender === '女') {
        gender.value = inputGender
      } else if (inputGender === 'male' || inputGender === 'female') {
        gender.value = inputGender === 'female' ? '女' : '男'
      }

      const inputLongitude = (input as Record<string, unknown>).longitude
      longitude.value = typeof inputLongitude === 'number' ? inputLongitude : longitude.value

      const inputLiunianYear = (input as Record<string, unknown>).liunian_year
      liunianYear.value = typeof inputLiunianYear === 'number' ? inputLiunianYear : undefined
    }

    result.value = output as unknown as ZiweiResponse
    activeTab.value = 'chart'
    selectedPalace.value = null
    savedCaseId.value = item.id
    savedCaseName.value = item.name
    currentSnapshotId.value = latest?.id ?? ''
    showCasesPanel.value = false
  } catch (e: unknown) {
    alert(parseZiweiApiError(e, '载入案例失败，请稍后重试'))
  }
}

async function removeCase(item: CaseOut) {
  if (!confirm(`确认删除案例「${item.name}」吗？`)) return

  try {
    await deleteCase(item.id)
    if (savedCaseId.value === item.id) {
      clearSavedCaseState()
    }

    const nextOffset = caseList.value.length === 1 && casesOffset.value > 0
      ? Math.max(0, casesOffset.value - CASES_LIMIT)
      : casesOffset.value
    await loadCases(nextOffset)
  } catch (e: unknown) {
    alert(parseZiweiApiError(e, '删除案例失败，请稍后重试'))
  }
}

function prevCasesPage() {
  if (casesOffset.value <= 0) return
  loadCases(Math.max(0, casesOffset.value - CASES_LIMIT))
}

function nextCasesPage() {
  if (casesOffset.value + CASES_LIMIT >= casesTotal.value) return
  loadCases(casesOffset.value + CASES_LIMIT)
}

function toggleSimilarPanel() {
  showSimilarPanel.value = !showSimilarPanel.value
  if (!showSimilarPanel.value) return
  similarStatus.value = result.value ? '点击“开始检索”查看相似命盘。' : '请先在主界面排盘，再使用相似盘检索。'
}

function getSimilarityPercent(value: number): number {
  return Math.max(0, Math.min(100, Math.round(value * 100)))
}

function getSimilarityLevel(value: number): string {
  const pct = getSimilarityPercent(value)
  if (pct >= 80) return '高度相似'
  if (pct >= 60) return '中度相似'
  return '低度相似'
}

function formatSimilarityPatterns(item: SimilarResult): string {
  const patterns = Array.isArray(item.case.patterns) ? item.case.patterns : []
  const labels = patterns
    .map((pattern) => {
      if (!pattern || typeof pattern !== 'object') return ''
      const name = typeof pattern.name === 'string' ? pattern.name : ''
      const level = typeof pattern.level === 'string' ? pattern.level : ''
      return [name, level].filter(Boolean).join(' ')
    })
    .filter(Boolean)
  return labels.length ? labels.slice(0, 3).join('、') : '无明显格局标签'
}

async function runSimilarSearch() {
  if (!result.value || similarLoading.value) return

  similarLoading.value = true
  similarStatus.value = '检索中…'
  similarResults.value = []
  try {
    const data = await searchSimilar({
      chart_hash: buildSimilarityHash(),
      life_palace_gz: result.value.life_palace_gz,
      wuxing_ju_name: result.value.wuxing_ju_name,
      gender: result.value.gender,
      birth_year: year.value,
      patterns: JSON.stringify(buildSimilarityPatternPayload()),
      top_k: similarTopK.value,
    })
    similarResults.value = data.results
    similarTotalIndexed.value = data.total_indexed
    similarStatus.value = data.results.length
      ? `找到 ${data.results.length} 条相似命盘，当前索引库共 ${data.total_indexed} 条。`
      : `未找到相似命盘，当前索引库共 ${data.total_indexed} 条。`
  } catch (e: unknown) {
    similarStatus.value = parseZiweiApiError(e, '相似盘检索失败，请稍后重试')
  } finally {
    similarLoading.value = false
  }
}

async function indexCurrentForSimilarity() {
  if (!result.value || similarLoading.value) return

  similarLoading.value = true
  similarStatus.value = '入相似库中…'
  try {
    await indexChart({
      chart_hash: buildSimilarityHash(),
      birth_solar: result.value.birth_solar,
      birth_year: year.value,
      birth_month: month.value,
      birth_day: day.value,
      birth_hour: hour.value,
      gender: gender.value,
      wuxing_ju_name: result.value.wuxing_ju_name,
      life_palace_gz: result.value.life_palace_gz,
      patterns: buildSimilarityPatternPayload(),
      source_label: 'spa-ziwei',
    })
    similarStatus.value = '当前命盘已加入相似盘索引库。'
  } catch (e: unknown) {
    similarStatus.value = parseZiweiApiError(e, '当前命盘入相似库失败，请稍后重试')
  } finally {
    similarLoading.value = false
  }
}

function resetSnapshotCompareState() {
  snapshotCompareA.value = ''
  snapshotCompareB.value = ''
  snapshotDiffResult.value = null
  snapshotDiffError.value = ''
}

function applySnapshotOutput(snapshot: SnapshotOut) {
  const input = snapshot.input_json ?? null
  const output = snapshot.output_json ?? null
  if (!output || typeof output !== 'object') {
    alert('该快照缺少可用输出数据')
    return
  }

  if (input && typeof input === 'object') {
    year.value = Number((input as Record<string, unknown>).year ?? year.value)
    month.value = Number((input as Record<string, unknown>).month ?? month.value)
    day.value = Number((input as Record<string, unknown>).day ?? day.value)
    hour.value = Number((input as Record<string, unknown>).hour ?? hour.value)
    minute.value = Number((input as Record<string, unknown>).minute ?? minute.value)

    const inputGender = (input as Record<string, unknown>).gender
    if (inputGender === '男' || inputGender === '女') {
      gender.value = inputGender
    } else if (inputGender === 'male' || inputGender === 'female') {
      gender.value = inputGender === 'female' ? '女' : '男'
    }

    const inputLongitude = (input as Record<string, unknown>).longitude
    longitude.value = typeof inputLongitude === 'number' ? inputLongitude : longitude.value

    const inputLiunianYear = (input as Record<string, unknown>).liunian_year
    liunianYear.value = typeof inputLiunianYear === 'number' ? inputLiunianYear : undefined
  }

  result.value = output as unknown as ZiweiResponse
  activeTab.value = 'chart'
  selectedPalace.value = null
  currentSnapshotId.value = snapshot.id
}

async function loadCaseSnapshots() {
  if (!savedCaseId.value) return

  snapshotsLoading.value = true
  snapshotsError.value = ''
  try {
    const data = await listSnapshots(savedCaseId.value, { limit: 10, offset: 0 })
    snapshots.value = data
    if (!snapshotCompareA.value && data[0]) snapshotCompareA.value = data[0].id
    if (!snapshotCompareB.value && data[1]) snapshotCompareB.value = data[1].id
    else if (!snapshotCompareB.value && data[0]) snapshotCompareB.value = data[0].id
  } catch (e: unknown) {
    snapshotsError.value = parseZiweiApiError(e, '快照列表加载失败，请稍后重试')
  } finally {
    snapshotsLoading.value = false
  }
}

function toggleSnapshotsPanel() {
  showSnapshotsPanel.value = !showSnapshotsPanel.value
  if (showSnapshotsPanel.value) {
    resetSnapshotCompareState()
    loadCaseSnapshots()
  }
}

function restoreSnapshot(snapshot: SnapshotOut) {
  applySnapshotOutput(snapshot)
  showSnapshotsPanel.value = false
}

async function compareSnapshotsNow() {
  if (!snapshotCompareA.value || !snapshotCompareB.value) {
    snapshotDiffError.value = '请选择两个快照后再比较'
    return
  }
  if (snapshotCompareA.value === snapshotCompareB.value) {
    snapshotDiffError.value = '请至少选择两个不同的快照'
    return
  }

  snapshotDiffLoading.value = true
  snapshotDiffError.value = ''
  snapshotDiffResult.value = null
  try {
    snapshotDiffResult.value = await diffSnapshots(snapshotCompareA.value, snapshotCompareB.value)
  } catch (e: unknown) {
    snapshotDiffError.value = parseZiweiApiError(e, '快照对比失败，请稍后重试')
  } finally {
    snapshotDiffLoading.value = false
  }
}

function buildPatternSummaryText(): string {
  return (result.value?.patterns || [])
    .map((item) => [item.name, item.level].filter(Boolean).join(' '))
    .filter(Boolean)
    .join('、')
}

async function loadReviewPanelData() {
  reviewLoading.value = true
  reviewError.value = ''
  try {
    const listPromise = reviewListMode.value === 'queue'
      ? getReviewQueue({ page: 1, page_size: 20 })
      : reviewListMode.value === 'mine'
        ? getMyReviewQueue({ page: 1, page_size: 20 })
        : listReviews(reviewFilter.value === 'all' ? undefined : { status: reviewFilter.value, page: 1, page_size: 20 })

    const [listData, statsData] = await Promise.all([
      listPromise,
      getReviewStats(),
      loadReviewAssigneeCandidates(),
    ])
    reviewList.value = listData.items
    reviewStats.value = statsData
    reviewLastLoadedAt.value = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })
    reviewBulkSelectedIds.value = reviewBulkSelectedIds.value.filter((id) => listData.items.some((item) => item.id === id))
    if (reviewSelectedId.value) {
      const selectedItem = listData.items.find((item) => item.id === reviewSelectedId.value)
      if (selectedItem) {
        reviewSelectedNotes.value = selectedItem.notes || ''
        reviewAssignInput.value = selectedItem.reviewer || reviewAssigneeName.value
      }
    }
    if (reviewSelectedId.value && !listData.items.some((item) => item.id === reviewSelectedId.value)) {
      reviewSelectedId.value = null
      reviewSelectedNotes.value = ''
      reviewAssignInput.value = reviewAssigneeName.value
      reviewSelectedHistory.value = []
    }
    if (!reviewSelectedId.value && listData.items[0]) {
      reviewSelectedId.value = listData.items[0].id
      reviewSelectedNotes.value = listData.items[0].notes || ''
      reviewAssignInput.value = listData.items[0].reviewer || reviewAssigneeName.value
      loadReviewHistory(listData.items[0].id)
    }
  } catch (e: unknown) {
    reviewError.value = parseZiweiApiError(e, '审核面板加载失败，请稍后重试')
  } finally {
    reviewLoading.value = false
  }
}

function toggleReviewPanel() {
  showReviewPanel.value = !showReviewPanel.value
  if (showReviewPanel.value) {
    loadReviewRecentAssignees()
    reviewListMode.value = 'all'
    reviewFilter.value = 'all'
    reviewBulkSelectedIds.value = []
    reviewBulkNotes.value = ''
    reviewAssignInput.value = reviewAssigneeName.value
    loadReviewPanelData()
  }
}

function setReviewListMode(mode: 'all' | 'queue' | 'mine') {
  reviewListMode.value = mode
  reviewBulkSelectedIds.value = []
  if (mode !== 'all') {
    reviewFilter.value = 'all'
  }
  loadReviewPanelData()
}

function refreshReviewPanel() {
  if (reviewLoading.value) return
  loadReviewPanelData()
}

function toggleReviewBulkItem(reviewId: number) {
  if (reviewBulkSelectedIds.value.includes(reviewId)) {
    reviewBulkSelectedIds.value = reviewBulkSelectedIds.value.filter((id) => id !== reviewId)
    return
  }
  reviewBulkSelectedIds.value = [...reviewBulkSelectedIds.value, reviewId]
}

function toggleAllReviewItems() {
  if (reviewAllVisibleSelected.value) {
    reviewBulkSelectedIds.value = []
    return
  }
  reviewBulkSelectedIds.value = reviewList.value.map((item) => item.id)
}

async function loadReviewHistory(reviewId: number) {
  reviewHistoryLoading.value = true
  try {
    const data = await getReviewHistory(reviewId)
    reviewSelectedHistory.value = data.items
  } catch {
    reviewSelectedHistory.value = []
  } finally {
    reviewHistoryLoading.value = false
  }
}

function selectReviewItem(item: ChartReviewResponse) {
  reviewSelectedId.value = item.id
  reviewSelectedNotes.value = item.notes || ''
  reviewAssignInput.value = item.reviewer || reviewAssigneeName.value
  loadReviewHistory(item.id)
}

async function submitCurrentReview() {
  if (!result.value || reviewActionLoading.value) return

  reviewActionLoading.value = true
  reviewError.value = ''
  try {
    const created = await createReview({
      case_id: savedCaseId.value || undefined,
      chart_hash: buildSimilarityHash(),
      chart_type: 'ziwei',
      notes: reviewSubmitNotes.value.trim() || undefined,
    })
    reviewSubmitNotes.value = ''
    reviewSelectedId.value = created.id
    await loadReviewPanelData()
    showOverlayFeedback('review', `审核单 #${created.id} 已加入队列`)
  } catch (e: unknown) {
    reviewError.value = parseZiweiApiError(e, '提交审核失败，请稍后重试')
  } finally {
    reviewActionLoading.value = false
  }
}

async function saveReviewNotes() {
  if (!currentReview.value || reviewActionLoading.value) return

  reviewActionLoading.value = true
  reviewError.value = ''
  try {
    const updated = await updateReview(currentReview.value.id, {
      status: currentReview.value.status,
      reviewer: currentReview.value.reviewer || undefined,
      notes: reviewSelectedNotes.value,
      reject_reason: currentReview.value.reject_reason || undefined,
    })
    const idx = reviewList.value.findIndex((item) => item.id === updated.id)
    if (idx >= 0) reviewList.value[idx] = updated
    showOverlayFeedback('review', `审核单 #${updated.id} 批注已保存`)
  } catch (e: unknown) {
    reviewError.value = parseZiweiApiError(e, '保存审核批注失败，请稍后重试')
  } finally {
    reviewActionLoading.value = false
  }
}

async function changeReviewStatus(status: 'approved' | 'rejected' | 'revised') {
  if (!currentReview.value || reviewActionLoading.value) return

  reviewActionLoading.value = true
  reviewError.value = ''
  try {
    const updated = await updateReview(currentReview.value.id, {
      status,
      reviewer: currentReview.value.reviewer || 'reviewer',
      notes: reviewSelectedNotes.value || undefined,
      reject_reason: status === 'rejected' ? (reviewSelectedNotes.value || '需要补充修订') : undefined,
    })
    const idx = reviewList.value.findIndex((item) => item.id === updated.id)
    if (idx >= 0) reviewList.value[idx] = updated
    await loadReviewHistory(updated.id)
    showOverlayFeedback('review', `审核单 #${updated.id} 已标记为${getReviewStatusLabel(status)}`)
  } catch (e: unknown) {
    reviewError.value = parseZiweiApiError(e, '更新审核状态失败，请稍后重试')
  } finally {
    reviewActionLoading.value = false
  }
}

async function assignCurrentReviewToMe() {
  await assignCurrentReview(reviewAssigneeName.value, '已领取到我的队列')
}

async function assignCurrentReview(assignee?: string, successMessage?: string) {
  if (!currentReview.value || reviewActionLoading.value) return

  const normalizedAssignee = assignee?.trim() || reviewAssignInput.value.trim()
  if (!normalizedAssignee) {
    reviewError.value = '请输入审核人标识后再指派'
    return
  }

  reviewActionLoading.value = true
  reviewError.value = ''
  try {
    const updated = await assignReview(currentReview.value.id, {
      assignee: normalizedAssignee,
    })
    const idx = reviewList.value.findIndex((item) => item.id === updated.id)
    if (idx >= 0) reviewList.value[idx] = updated
    reviewAssignInput.value = updated.reviewer || normalizedAssignee
    saveReviewRecentAssignee(updated.reviewer || normalizedAssignee)
    await loadReviewHistory(updated.id)
    showOverlayFeedback('review', successMessage || `审核单 #${updated.id} 已指派给 ${updated.reviewer || normalizedAssignee}`)
  } catch (e: unknown) {
    reviewError.value = parseZiweiApiError(e, '指派审核单失败，请稍后重试')
  } finally {
    reviewActionLoading.value = false
  }
}

async function applyBulkReviewStatus(action: 'approved' | 'rejected' | 'revised') {
  if (!reviewBulkSelectedIds.value.length || reviewActionLoading.value) return

  reviewActionLoading.value = true
  reviewError.value = ''
  try {
    const noteText = reviewBulkNotes.value.trim()
    const result = await bulkReviewAction({
      ids: reviewBulkSelectedIds.value,
      action,
      reviewer: 'reviewer',
      notes: noteText || undefined,
      reject_reason: action === 'rejected' ? (noteText || '批量驳回，请补充修订') : undefined,
    })
    await loadReviewPanelData()
    reviewBulkSelectedIds.value = []
    reviewBulkNotes.value = ''
    showOverlayFeedback('review', `批量${getReviewStatusLabel(action)}完成：成功 ${result.succeeded.length} 条`)
  } catch (e: unknown) {
    reviewError.value = parseZiweiApiError(e, '批量审核失败，请稍后重试')
  } finally {
    reviewActionLoading.value = false
  }
}

function buildLlmRequest() {
  if (!result.value) return null
  return {
    chart_hash: buildSimilarityHash(),
    life_palace_gz: result.value.life_palace_gz,
    wuxing_ju_name: result.value.wuxing_ju_name,
    pattern_summary: buildPatternSummaryText(),
    birth_info_summary: `${result.value.birth_solar} ${result.value.gender}`,
  }
}

async function loadLlmDraftList() {
  try {
    const data = await fetchDrafts({ limit: 10, status: llmFilterStatus.value || undefined })
    llmDrafts.value = data.items
  } catch {
    llmDrafts.value = []
  }
}

async function toggleLlmPanel() {
  showLlmPanel.value = !showLlmPanel.value
  if (!showLlmPanel.value) return

  llmStatus.value = result.value ? '可生成紫微 AI 草稿。' : '请先在主界面排盘，再生成 AI 草稿。'
  try {
    const cfg = await getLlmConfig()
    const provider = typeof cfg.provider === 'string' ? cfg.provider : 'unknown'
    const model = typeof cfg.model === 'string' ? cfg.model : ''
    llmConfigLabel.value = model ? `${provider} / ${model}` : provider
  } catch {
    llmConfigLabel.value = '加载失败'
  }
  await loadLlmDraftList()
}

async function generateLlmDraft() {
  const req = buildLlmRequest()
  if (!req || llmLoading.value) return

  llmLoading.value = true
  llmStatus.value = '生成中…'
  try {
    const draft = await interpretGeneric(req)
    llmCurrentDraft.value = draft
    llmCurrentText.value = draft.draft_text || ''
    llmReviewerNotes.value = draft.reviewer_notes || ''
    llmStatus.value = '已生成 AI 草稿。'
    await loadLlmDraftList()
    showOverlayFeedback('llm', 'AI 草稿已生成，可继续审核或复制')
  } catch (e: unknown) {
    llmStatus.value = parseZiweiApiError(e, 'AI 草稿生成失败，请稍后重试')
  } finally {
    llmLoading.value = false
  }
}

async function streamLlmDraft() {
  const req = buildLlmRequest()
  if (!req || llmLoading.value) return

  llmLoading.value = true
  llmCurrentText.value = ''
  llmStatus.value = '流式生成中…'
  try {
    await streamInterpretation(
      req,
      (chunk) => { llmCurrentText.value += chunk },
      (fullText) => {
        llmCurrentText.value = fullText
        llmStatus.value = '流式生成完成。'
        showOverlayFeedback('llm', '流式草稿已生成完成')
      },
      async (savedId) => {
        llmCurrentDraft.value = await getDraft(savedId)
        llmReviewerNotes.value = llmCurrentDraft.value?.reviewer_notes || ''
        await loadLlmDraftList()
      },
    )
  } catch (e: unknown) {
    llmStatus.value = parseZiweiApiError(e, '流式生成失败，请稍后重试')
  } finally {
    llmLoading.value = false
  }
}

async function openLlmDraft(draftId: number) {
  try {
    const draft = await getDraft(draftId)
    llmCurrentDraft.value = draft
    llmCurrentText.value = draft.draft_text || ''
    llmReviewerNotes.value = draft.reviewer_notes || ''
    llmStatus.value = '已载入历史草稿。'
    showOverlayFeedback('llm', `已载入草稿 #${draft.id}`)
  } catch (e: unknown) {
    llmStatus.value = parseZiweiApiError(e, '读取草稿失败，请稍后重试')
  }
}

async function copyCurrentLlmDraft() {
  if (!llmCurrentText.value.trim()) return

  try {
    await navigator.clipboard.writeText(llmCurrentText.value)
    llmCopied.value = true
    showOverlayFeedback('llm', '当前草稿已复制到剪贴板')
    window.setTimeout(() => {
      llmCopied.value = false
    }, 1400)
  } catch {
    showOverlayFeedback('llm', '复制失败，请手动复制', 'error')
  }
}

async function saveCurrentDraftNotes() {
  if (!llmCurrentDraft.value || llmLoading.value) return

  llmLoading.value = true
  try {
    const updated = await updateDraft(llmCurrentDraft.value.id, {
      reviewer: llmCurrentDraft.value.reviewer || 'reviewer',
      reviewer_notes: llmReviewerNotes.value || '',
    })
    llmCurrentDraft.value = updated
    llmReviewerNotes.value = updated.reviewer_notes || ''
    llmStatus.value = '审核备注已保存。'
    await loadLlmDraftList()
    showOverlayFeedback('llm', 'reviewer notes 已保存')
  } catch (e: unknown) {
    llmStatus.value = parseZiweiApiError(e, '保存草稿备注失败，请稍后重试')
  } finally {
    llmLoading.value = false
  }
}

async function reviewCurrentDraft(status: 'approved' | 'rejected') {
  if (!llmCurrentDraft.value || llmLoading.value) return

  llmLoading.value = true
  try {
    const updated = await updateDraft(llmCurrentDraft.value.id, {
      status,
      reviewer: 'reviewer',
      reviewer_notes: llmReviewerNotes.value || '',
    })
    llmCurrentDraft.value = updated
    llmReviewerNotes.value = updated.reviewer_notes || ''
    llmStatus.value = status === 'approved' ? '草稿已通过。' : '草稿已驳回。'
    await loadLlmDraftList()
    showOverlayFeedback('llm', status === 'approved' ? '当前草稿已通过审核' : '当前草稿已驳回')
  } catch (e: unknown) {
    llmStatus.value = parseZiweiApiError(e, '草稿审核失败，请稍后重试')
  } finally {
    llmLoading.value = false
  }
}

async function loadOpsPanelData() {
  opsLoading.value = true
  opsError.value = ''
  opsStatus.value = ''
  try {
    const [statsData, experimentsData] = await Promise.all([
      getAdminStats(),
      listExperiments({
        status: opsExperimentFilter.value === 'all' ? undefined : opsExperimentFilter.value,
        skip: 0,
        limit: 20,
      }),
    ])
    opsStats.value = statsData
    opsExperiments.value = experimentsData.items
    opsExperimentsTotal.value = experimentsData.total
  } catch (e: unknown) {
    opsError.value = parseZiweiApiError(e, '运营面板加载失败，请稍后重试')
  } finally {
    opsLoading.value = false
  }
}

function toggleOpsPanel() {
  showOpsPanel.value = !showOpsPanel.value
  if (showOpsPanel.value) {
    loadOpsPanelData()
  }
}

async function createOpsExperiment() {
  if (!opsCreateForm.value.name.trim() || opsExperimentSaving.value) return

  opsExperimentSaving.value = true
  opsStatus.value = ''
  try {
    await createExperiment({
      name: opsCreateForm.value.name.trim(),
      description: opsCreateForm.value.description.trim(),
      target_metric: opsCreateForm.value.targetMetric,
      hypothesis: opsCreateForm.value.hypothesis.trim(),
      min_sample_size: Number(opsCreateForm.value.minSampleSize) || 100,
      variants: [
        { name: 'control', description: '对照组', weight: Number(opsCreateForm.value.controlWeight) || 50 },
        { name: 'variant_a', description: '实验组 A', weight: Number(opsCreateForm.value.variantWeight) || 50 },
      ],
    })
    opsStatus.value = '实验已创建。'
    opsCreateFormVisible.value = false
    opsCreateForm.value = {
      name: '',
      description: '',
      targetMetric: 'conversion',
      hypothesis: '',
      minSampleSize: 100,
      controlWeight: 50,
      variantWeight: 50,
    }
    await loadOpsPanelData()
    showOverlayFeedback('ops', 'A/B 实验已创建，已刷新列表')
  } catch (e: unknown) {
    opsError.value = parseZiweiApiError(e, '创建实验失败，请稍后重试')
  } finally {
    opsExperimentSaving.value = false
  }
}

async function changeOpsExperimentStatus(expId: number, status: 'running' | 'paused' | 'completed') {
  try {
    await updateExperiment(expId, { status })
    opsStatus.value = `实验状态已更新为${getExperimentStatusLabel(status)}。`
    await loadOpsPanelData()
    showOverlayFeedback('ops', `实验 #${expId} 已${getExperimentStatusLabel(status)}`)
  } catch (e: unknown) {
    opsError.value = parseZiweiApiError(e, '更新实验状态失败，请稍后重试')
  }
}

async function showOpsExperimentResults(expId: number) {
  opsExperimentResultsLoading.value = true
  opsStatus.value = '加载实验结果中…'
  try {
    opsExperimentResults.value = await getExperimentResults(expId)
    opsStatus.value = '实验结果已更新。'
    showOverlayFeedback('ops', `实验 #${expId} 结果已刷新`, 'info')
  } catch (e: unknown) {
    opsError.value = parseZiweiApiError(e, '加载实验结果失败，请稍后重试')
  } finally {
    opsExperimentResultsLoading.value = false
  }
}

async function removeOpsExperiment(expId: number) {
  if (!confirm('确认删除该实验？')) return
  try {
    await deleteExperiment(expId)
    opsStatus.value = '实验已删除。'
    if (opsExperimentResults.value?.experiment_id === expId) {
      opsExperimentResults.value = null
    }
    await loadOpsPanelData()
    showOverlayFeedback('ops', `实验 #${expId} 已删除`)
  } catch (e: unknown) {
    opsError.value = parseZiweiApiError(e, '删除实验失败，请稍后重试')
  }
}

function toggleBatchPanel() {
  showBatchPanel.value = !showBatchPanel.value
  if (showBatchPanel.value) {
    batchStatus.value = batchSelectedFile.value ? '准备就绪，点击“开始批量排盘”。' : '请选择 CSV 文件后开始批量排盘。'
    batchError.value = ''
  }
}

function handleBatchFileChange(event: Event) {
  const files = (event.target as HTMLInputElement).files
  batchSelectedFile.value = files?.[0] ?? null
  batchError.value = ''
  batchStatus.value = batchSelectedFile.value
    ? `已选择：${batchSelectedFile.value.name}`
    : '请选择 CSV 文件后开始批量排盘。'
}

function downloadBatchSample() {
  const csv = 'name,year,month,day,hour,minute,gender,liunian_year\n'
    + '张三,1990,5,20,8,30,男,2026\n'
    + '李四,1985,9,15,14,0,女,2026\n'
    + '王五,2000,1,1,0,0,男,\n'
  downloadBlobFile(new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' }), 'ziwei_batch_sample.csv')
}

async function runZiweiBatch() {
  if (!batchSelectedFile.value || batchLoading.value) return

  batchLoading.value = true
  batchError.value = ''
  batchStatus.value = '上传并计算中，请稍候…'
  try {
    const blob = await ziweiBatch(batchSelectedFile.value, batchTemplateVersion.value || undefined)
    const dt = new Date().toISOString().slice(0, 10).replace(/-/g, '')
    downloadBlobFile(blob, `ziwei_batch_${dt}.zip`)
    batchStatus.value = '批量排盘完成，ZIP 已开始下载。'
  } catch (e: unknown) {
    batchError.value = parseZiweiApiError(e, '批量排盘失败，请稍后重试')
    batchStatus.value = '批量排盘失败。'
  } finally {
    batchLoading.value = false
  }
}

async function loadGlossaryToolPanel() {
  glossaryToolLoading.value = true
  glossaryToolError.value = ''
  try {
    glossaryToolItems.value = await getGlossary({
      q: glossaryToolSearch.value.trim() || undefined,
      category: glossaryToolCategory.value || undefined,
      limit: 30,
    })
  } catch (e: unknown) {
    glossaryToolError.value = parseZiweiApiError(e, '词汇加载失败，请稍后重试')
  } finally {
    glossaryToolLoading.value = false
  }
}

function toggleGlossaryPanel() {
  showGlossaryPanel.value = !showGlossaryPanel.value
  if (showGlossaryPanel.value) {
    clearOverlayFeedback('glossary')
    loadGlossaryToolPanel()
  }
}

function addMultiCompatPerson() {
  if (multiCompatPersons.value.length >= 3) return
  multiCompatPersons.value.push({ year: 1995, month: 1, day: 1, hour: 12, minute: 0, gender: '男' })
}

function removeMultiCompatPerson(index: number) {
  multiCompatPersons.value.splice(index, 1)
}

function buildCurrentZiweiRequest(): ZiweiRequest | null {
  if (!result.value) return null
  return {
    year: year.value,
    month: month.value,
    day: day.value,
    hour: hour.value,
    minute: minute.value,
    gender: gender.value,
    longitude: longitude.value,
  }
}

async function runMultiCompat() {
  const current = buildCurrentZiweiRequest()
  if (!current || multiCompatLoading.value) return

  multiCompatLoading.value = true
  multiCompatError.value = ''
  multiCompatResult.value = null
  try {
    multiCompatResult.value = await ziweiMultiCompat({ person_list: [current, ...multiCompatPersons.value] })
    showOverlayFeedback('multi', '缘分矩阵已更新，可重点查看高亮组合', 'info')
  } catch (e: unknown) {
    multiCompatError.value = parseZiweiApiError(e, '多人合盘失败，请稍后重试')
  } finally {
    multiCompatLoading.value = false
  }
}

function toggleMultiCompatPanel() {
  showMultiCompatPanel.value = !showMultiCompatPanel.value
  if (!showMultiCompatPanel.value) return
  multiCompatError.value = ''
  clearOverlayFeedback('multi')
}

async function loadFengshuiPanel() {
  fengshuiLoading.value = true
  fengshuiError.value = ''
  fengshuiForm.value.birthYear = year.value
  fengshuiForm.value.gender = gender.value
  try {
    const [options, bagua] = await Promise.all([
      getFengshuiOptions(),
      fetchFengshuiBagua({ birth_year: fengshuiForm.value.birthYear, gender: fengshuiForm.value.gender }),
    ])
    fengshuiOptions.value = options
    fengshuiData.value = bagua
    showOverlayFeedback('fengshui', '风水基础信息已同步，可继续评估布局', 'info')
  } catch (e: unknown) {
    fengshuiError.value = parseZiweiApiError(e, '风水助手加载失败，请稍后重试')
  } finally {
    fengshuiLoading.value = false
  }
}

function toggleFengshuiPanel() {
  router.push({
    path: '/fengshui',
    query: {
      birth_year: String(year.value),
      gender: gender.value,
    },
  })
}

async function runFengshuiBagua() {
  fengshuiLoading.value = true
  fengshuiError.value = ''
  fengshuiRoomResult.value = null
  try {
    fengshuiData.value = await fetchFengshuiBagua({
      birth_year: Number(fengshuiForm.value.birthYear),
      gender: fengshuiForm.value.gender,
    })
    showOverlayFeedback('fengshui', '命卦分析已更新')
  } catch (e: unknown) {
    fengshuiError.value = parseZiweiApiError(e, '风水命卦分析失败，请稍后重试')
  } finally {
    fengshuiLoading.value = false
  }
}

async function runFengshuiRoomLayout() {
  if (!Object.keys(fengshuiRooms.value).length) {
    fengshuiRoomError.value = '请至少设置一个方位的房间类型'
    return
  }

  fengshuiRoomLoading.value = true
  fengshuiRoomError.value = ''
  try {
    fengshuiRoomResult.value = await analyzeRoomLayout({
      birth_year: Number(fengshuiForm.value.birthYear),
      gender: fengshuiForm.value.gender,
      house_facing: fengshuiForm.value.houseFacing || undefined,
      rooms: fengshuiRooms.value,
    })
    showOverlayFeedback('fengshui', '九宫格布局评估已完成')
  } catch (e: unknown) {
    fengshuiRoomError.value = parseZiweiApiError(e, '房间布局评估失败，请稍后重试')
  } finally {
    fengshuiRoomLoading.value = false
  }
}

function updateFengshuiRoom(direction: string, value: string) {
  if (!value) {
    const next = { ...fengshuiRooms.value }
    delete next[direction]
    fengshuiRooms.value = next
    return
  }
  fengshuiRooms.value = {
    ...fengshuiRooms.value,
    [direction]: value,
  }
}

type RightPanelQuickAction = 'adjust' | 'copy' | 'export' | 'share' | 'notes' | 'calendar' | 'compare' | 'bookmarks'

function handleRightPanelQuickAction(evt: Event) {
  const action = (evt as CustomEvent<RightPanelQuickAction>).detail
  if (!action) return

  switch (action) {
    case 'adjust':
      showAdjustModal()
      break
    case 'copy':
      copyChartInfo()
      break
    case 'export':
      exportChartAsImage()
      break
    case 'share':
      showSharePanel.value = !showSharePanel.value
      break
    case 'notes':
      showNotesPanel.value = !showNotesPanel.value
      break
    case 'calendar':
      showCalendarView.value = !showCalendarView.value
      break
    case 'compare':
      showComparePanel.value = !showComparePanel.value
      break
    case 'bookmarks':
      showBookmarksPanel.value = !showBookmarksPanel.value
      break
  }
}

onMounted(() => {
  window.addEventListener('ziwei:quick-action', handleRightPanelQuickAction as EventListener)
})

onUnmounted(() => {
  window.removeEventListener('ziwei:quick-action', handleRightPanelQuickAction as EventListener)
  if (overlayFeedbackTimer) {
    window.clearTimeout(overlayFeedbackTimer)
  }
})

// 从URL参数恢复命盘
function loadFromUrlParams() {
  const params = new URLSearchParams(window.location.search)
  if (params.has('y') && params.has('m') && params.has('d')) {
    year.value = parseInt(params.get('y') || '1990')
    month.value = parseInt(params.get('m') || '1')
    day.value = parseInt(params.get('d') || '1')
    hour.value = parseInt(params.get('h') || '12')
    minute.value = parseInt(params.get('mi') || '0')
    gender.value = (params.get('g') as '男' | '女') || '男'
    if (params.has('lng')) longitude.value = parseFloat(params.get('lng') || '')
    // 清除URL参数后计算
    window.history.replaceState({}, '', window.location.pathname)
    nextTick(() => doCalculate())
  }
}

// 初始化时检查URL参数
onMounted(() => {
  loadFromUrlParams()
})

// ══════════════════════════════════════════════════════════════════
// 命盘配色主题
// ══════════════════════════════════════════════════════════════════
type ChartTheme = 'classic' | 'modern' | 'elegant' | 'dark'
const THEME_KEY = 'ziwei_chart_theme'
const chartTheme = ref<ChartTheme>((localStorage.getItem(THEME_KEY) as ChartTheme) || 'classic')
const showThemePanel = ref(false)

const CHART_THEMES: Array<{ id: ChartTheme; name: string; desc: string; colors: { primary: string; bg: string } }> = [
  { id: 'classic', name: '经典', desc: '传统紫色调', colors: { primary: '#7c3aed', bg: '#faf5ff' } },
  { id: 'modern', name: '现代', desc: '清新蓝色调', colors: { primary: '#3b82f6', bg: '#eff6ff' } },
  { id: 'elegant', name: '雅致', desc: '沉稳棕色调', colors: { primary: '#92400e', bg: '#fef3c7' } },
  { id: 'dark', name: '暗黑', desc: '深色护眼', colors: { primary: '#a78bfa', bg: '#1e1b4b' } },
]

function setChartTheme(theme: ChartTheme) {
  chartTheme.value = theme
  localStorage.setItem(THEME_KEY, theme)
  applyTheme(theme)
  showThemePanel.value = false
}

function applyTheme(theme: ChartTheme) {
  const root = document.documentElement
  const themeVars: Record<ChartTheme, Record<string, string>> = {
    classic: {
      '--theme-primary': '#7c3aed',
      '--theme-primary-bg': 'rgba(124, 58, 237, 0.1)',
      '--theme-bg': '#faf5ff',
      '--theme-card': '#ffffff',
      '--theme-text': '#1f2937',
      '--theme-text-2': '#6b7280',
      '--theme-border': '#e5e7eb',
    },
    modern: {
      '--theme-primary': '#3b82f6',
      '--theme-primary-bg': 'rgba(59, 130, 246, 0.1)',
      '--theme-bg': '#eff6ff',
      '--theme-card': '#ffffff',
      '--theme-text': '#1e3a5f',
      '--theme-text-2': '#64748b',
      '--theme-border': '#dbeafe',
    },
    elegant: {
      '--theme-primary': '#92400e',
      '--theme-primary-bg': 'rgba(146, 64, 14, 0.1)',
      '--theme-bg': '#fefbf3',
      '--theme-card': '#fffdf7',
      '--theme-text': '#451a03',
      '--theme-text-2': '#78716c',
      '--theme-border': '#fde68a',
    },
    dark: {
      '--theme-primary': '#a78bfa',
      '--theme-primary-bg': 'rgba(167, 139, 250, 0.15)',
      '--theme-bg': '#0f0d1a',
      '--theme-card': '#1e1b2e',
      '--theme-text': '#e2e8f0',
      '--theme-text-2': '#94a3b8',
      '--theme-border': '#334155',
    },
  }
  
  const vars = themeVars[theme]
  Object.entries(vars).forEach(([key, val]) => {
    root.style.setProperty(key, val)
  })
}

// 初始化主题
onMounted(() => {
  applyTheme(chartTheme.value)
})

// ══════════════════════════════════════════════════════════════════
// 字体大小调整
// ══════════════════════════════════════════════════════════════════
const FONT_SIZE_KEY = 'ziwei_font_size'
type FontSizeLevel = 'sm' | 'md' | 'lg' | 'xl'
const fontSizeLevel = ref<FontSizeLevel>((localStorage.getItem(FONT_SIZE_KEY) as FontSizeLevel) || 'md')

const FONT_SIZE_OPTIONS: Array<{ id: FontSizeLevel; label: string; scale: number }> = [
  { id: 'sm', label: '小', scale: 0.9 },
  { id: 'md', label: '中', scale: 1.0 },
  { id: 'lg', label: '大', scale: 1.1 },
  { id: 'xl', label: '特大', scale: 1.2 },
]

function setFontSize(level: FontSizeLevel) {
  fontSizeLevel.value = level
  localStorage.setItem(FONT_SIZE_KEY, level)
  applyFontSize(level)
}

function applyFontSize(level: FontSizeLevel) {
  const opt = FONT_SIZE_OPTIONS.find(o => o.id === level)
  if (!opt) return
  const root = document.documentElement
  root.style.setProperty('--font-scale', String(opt.scale))
}

// 初始化字体大小
onMounted(() => {
  applyFontSize(fontSizeLevel.value)
})

// ══════════════════════════════════════════════════════════════════
// 星曜详情提示
// ══════════════════════════════════════════════════════════════════
const STAR_INFO: Record<string, { nature: string; meaning: string }> = {
  '紫微': { nature: '帝星', meaning: '尊贵、领导、自尊心强' },
  '天机': { nature: '智慧', meaning: '聪明、善变、多谋略' },
  '太阳': { nature: '光明', meaning: '热情、正直、博爱' },
  '武曲': { nature: '财星', meaning: '正财、刚毅、果断' },
  '天同': { nature: '福星', meaning: '温和、享福、懒散' },
  '廉贞': { nature: '次桃', meaning: '才艺、桃花、是非' },
  '天府': { nature: '财库', meaning: '稳重、守成、保守' },
  '太阴': { nature: '财星', meaning: '细腻、阴柔、财富' },
  '贪狼': { nature: '桃花', meaning: '欲望、才艺、多情' },
  '巨门': { nature: '口舌', meaning: '口才、是非、暗曜' },
  '天相': { nature: '印星', meaning: '贵人、衣食、细心' },
  '天梁': { nature: '荫星', meaning: '清高、长辈缘、化解' },
  '七杀': { nature: '将星', meaning: '魄力、冒险、孤独' },
  '破军': { nature: '耗星', meaning: '变动、破旧立新、开创' },
  '文昌': { nature: '科甲', meaning: '文采、考试、文书' },
  '文曲': { nature: '才艺', meaning: '艺术、口才、桃花' },
  '左辅': { nature: '助力', meaning: '贵人、助力、人缘' },
  '右弼': { nature: '助力', meaning: '贵人、助力、异性缘' },
  '天魁': { nature: '贵人', meaning: '阳贵、男贵人、白天' },
  '天钺': { nature: '贵人', meaning: '阴贵、女贵人、夜晚' },
  '禄存': { nature: '正财', meaning: '稳定财源、保守、孤' },
  '天马': { nature: '驿马', meaning: '流动、变迁、奔波' },
  '擎羊': { nature: '煞星', meaning: '刑克、冲动、开创' },
  '陀罗': { nature: '煞星', meaning: '拖延、纠缠、磨练' },
  '火星': { nature: '煞星', meaning: '急躁、爆发、冲突' },
  '铃星': { nature: '煞星', meaning: '阴险、暗损、急躁' },
  '地空': { nature: '空曜', meaning: '虚空、灵感、损失' },
  '地劫': { nature: '空曜', meaning: '劫夺、破坏、修行' },
  '化禄': { nature: '四化', meaning: '财运、好运、顺利' },
  '化权': { nature: '四化', meaning: '权力、掌控、强势' },
  '化科': { nature: '四化', meaning: '名声、贵人、文采' },
  '化忌': { nature: '四化', meaning: '阻碍、执念、不顺' },
}

const hoveredStar = ref<string | null>(null)
const starTooltipPos = ref({ x: 0, y: 0 })

function showStarTooltip(starName: string, event: MouseEvent) {
  if (!STAR_INFO[starName]) return
  hoveredStar.value = starName
  starTooltipPos.value = { x: event.clientX + 10, y: event.clientY + 10 }
}

function hideStarTooltip() {
  hoveredStar.value = null
}

// ── 宫位弹窗 ──────────────────────────────────────────
function selectPalace(p: PalaceResponse) {
  selectedPalace.value = selectedPalace.value?.index === p.index ? null : p
}

function selectPalaceByIndex(idx: number) {
  if (!result.value?.palaces) return
  const p = result.value.palaces.find(p => p.index === idx)
  if (p) {
    selectedPalace.value = p
    // 滚动到命盘区域
    const chartEl = getChartExportElement()
    chartEl?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

// ── 宫位辅助函数 ──────────────────────────────────────
function palaceHasTransform(p: PalaceResponse, tf: string): boolean {
  const allTransforms = getPalaceTransforms(p)
  return allTransforms.includes(tf)
}

function getPalaceQuickInfo(p: PalaceResponse): string {
  const mainNames = p.main_stars?.map(s => s.name).join('、') || '无主星'
  const transforms = getPalaceTransforms(p)
  const tfStr = transforms.length ? `｜${transforms.join(' ')}` : ''
  return `${p.name}：${mainNames}${tfStr}`
}

// ── C-5: 定盘调整 ─────────────────────────────────────
function showAdjustModal() {
  // 简单实现：滚动到时辰输入框并聚焦
  const hourInput = document.querySelector<HTMLSelectElement>('.ziwei-form select[name="hour"]')
  if (hourInput) {
    hourInput.scrollIntoView({ behavior: 'smooth', block: 'center' })
    hourInput.focus()
    // 添加高亮提示
    hourInput.classList.add('highlight-input')
    setTimeout(() => hourInput.classList.remove('highlight-input'), 2000)
  }
}

// ── 日↑日↓时↑时↓：调整出生日期/时辰并重新计算 ─────────────
function shiftDay(delta: number) {
  const d = new Date(year.value, month.value - 1, day.value)
  d.setDate(d.getDate() + delta)
  year.value  = d.getFullYear()
  month.value = d.getMonth() + 1
  day.value   = d.getDate()
  doCalculate()
}

function shiftHour(delta: number) {
  // 时辰以2小时为单位（子=0，丑=2，寅=4…）
  const hrs = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22]
  const curIdx = hrs.findIndex(h => h === hour.value)
  const nextIdx = ((curIdx < 0 ? 0 : curIdx) + delta + 12) % 12
  hour.value = hrs[nextIdx]!
  doCalculate()
}

// ── 打印 ──────────────────────────────────────────────
function exportPDF() { window.print() }

// ── 复制命盘信息 ──────────────────────────────────────
function copyChartInfo() {
  if (!result.value) return
  const r = result.value
  const lines = [
    `【紫微斗数命盘】`,
    `出生：${r.birth_solar} ${r.gender}`,
    `农历：${r.lunar.lunar_year}年${r.lunar.is_leap_month ? '闰' : ''}${r.lunar.lunar_month}月${r.lunar.lunar_day}日 ${r.lunar.hour_branch}时`,
    `四柱：${r.lunar.year_gz} ${r.lunar.jieqi_month_gz || r.lunar.month_gz} ${r.lunar.hour_branch}`,
    `命宫：${r.life_palace_gz}  身宫：${r.body_palace_gz}`,
    `五行局：${r.wuxing_ju_name}`,
    `命主：${r.life_ruler_star}  身主：${r.body_ruler_star}`,
    r.dayun ? `起运：${r.dayun.start_age_text || r.dayun.start_age + '岁'} ${r.dayun.forward ? '顺行' : '逆行'}` : '',
    ``,
    `【十二宫】`,
    ...r.palaces.map(p => `${p.name}（${p.stem}${p.branch}）：${p.main_stars.map(s => s.name + (s.brightness ? `[${s.brightness}]` : '')).join('、') || '无主星'}`),
    ``,
    r.patterns?.length ? `【格局】${r.patterns.map(p => p.name).join('、')}` : '',
  ].filter(Boolean)
  
  navigator.clipboard.writeText(lines.join('\n')).then(() => {
    // 简单提示
    const btn = document.querySelector('.pc-copy-btn') as HTMLButtonElement
    if (btn) {
      const orig = btn.textContent
      btn.textContent = '✓ 已复制'
      setTimeout(() => { btn.textContent = orig }, 1500)
    }
  })
}

// ── 前往择日 ──────────────────────────────────────────
function gotoZeri() {
  if (!result.value) return
  const branch = result.value.life_palace_gz.slice(-1)
  const juName = result.value.wuxing_ju_name
  router.push({ path: '/zeri', query: { life_palace_branch: branch, wuxing_ju_name: juName } })
}

// ── AI 解读 ───────────────────────────────────────────
function gotoAi() {
  if (!result.value) return
  ui.rightPanelExpanded = true
  const lp       = result.value.life_palace_gz
  const ju       = result.value.wuxing_ju_name
  const pattern  = typeof result.value.geju_name === 'string' ? result.value.geju_name : buildPatternSummaryText()
  ai.sendMessage(`请帮我解读紫微斗数命盘：命宫${lp}，${ju}，格局${pattern || '待分析'}。`, {
    life_palace_gz:    lp,
    wuxing_ju_name:    ju,
    pattern_summary:   pattern,
    birth_info_summary: `命宫${lp} ${ju}`,
  })
}

// ── 五行计数 ──────────────────────────────────────────────
function baziWuxingCount(element: string): number {
  if (!result.value?.lunar || !baziDetails.value) return 0
  const details = baziDetails.value
  
  const stemElementMap: Record<string, string> = {
    '甲': '木', '乙': '木', '丙': '火', '丁': '火',
    '戊': '土', '己': '土', '庚': '金', '辛': '金',
    '壬': '水', '癸': '水',
  }
  const branchElementMap: Record<string, string> = {
    '子': '水', '丑': '土', '寅': '木', '卯': '木',
    '辰': '土', '巳': '火', '午': '火', '未': '土',
    '申': '金', '酉': '金', '戌': '土', '亥': '水',
  }
  
  let count = 0
  if (stemElementMap[details.year.stem] === element) count++
  if (branchElementMap[details.year.branch] === element) count++
  if (stemElementMap[details.month.stem] === element) count++
  if (branchElementMap[details.month.branch] === element) count++
  if (stemElementMap[details.day.stem] === element) count++
  if (branchElementMap[details.day.branch] === element) count++
  if (stemElementMap[details.hour.stem] === element) count++
  if (branchElementMap[details.hour.branch] === element) count++
  
  return count
}

// ── 运势分数颜色 ──────────────────────────────────────
function forecastScoreColor(score: number): string {
  if (score >= 80) return '#15803d'
  if (score >= 60) return '#d97706'
  return '#dc2626'
}

// ── 根据月份获取对应的运势预测 ──────────────────────────
function getMonthForecast(month: number) {
  if (!result.value?.forecast?.monthly) return null
  // 尝试精确匹配月份
  return result.value.forecast.monthly.find(m => {
    // period格式如 "2026年正月(寅)" 或 "2026年二月(卯)"
    const monthNames = ['正', '二', '三', '四', '五', '六', '七', '八', '九', '十', '冬', '腊']
    const monthName = monthNames[month - 1]
    return m.period?.includes(monthName + '月')
  }) ?? result.value.forecast.monthly[month - 1] ?? null
}

const liuyueRows = computed(() => {
  const months = result.value?.liuyue ?? []
  return months.map((m) => ({
    month: m,
    forecast: getMonthForecast(m.month),
  }))
})

const liuyueSummary = computed(() => {
  const rows = liuyueRows.value
  const withForecast = rows.filter(r => r.forecast?.score != null)
  const scores = withForecast.map(r => Number(r.forecast?.score || 0)).filter(s => s > 0)
  const avg = scores.length ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : 0
  const riskMonths = withForecast
    .filter(r => Number(r.forecast?.score || 0) < 50)
    .map(r => r.month.month_name)
    .slice(0, 3)
  return {
    total: rows.length,
    withSihua: rows.filter(r => Object.keys(r.month.sihua || {}).length > 0).length,
    withForecast: withForecast.length,
    avg,
    riskMonths,
  }
})

// ── 命宫主星列表 ──────────────────────────────────────
const lifePalaceMainStars = computed(() => {
  if (!result.value?.palaces) return []
  const lifePalace = result.value.palaces.find(p => p.name.includes('命'))
  return lifePalace?.main_stars ?? []
})

// ── 命宫辅星列表 ──────────────────────────────────────
const lifePalaceAuxStars = computed(() => {
  if (!result.value?.palaces) return []
  const lifePalace = result.value.palaces.find(p => p.name.includes('命'))
  return lifePalace?.aux_stars ?? []
})

// ── 十二宫名称（按顺序） ─────────────────────────────────
const DAXIAN_PREFIX = ['大命','大兄','大夫','大子','大财','大疾','大迁','大友','大官','大田','大福','大父']
const LIUNIAN_PREFIX = ['年命','年兄','年夫','年子','年财','年疾','年迁','年友','年官','年田','年福','年父']
const LIUYUE_PREFIX = ['月命','月兄','月夫','月子','月财','月疾','月迁','月友','月官','月田','月福','月父']

// ── 流年宫位信息映射（宫位索引 → 流年年龄） ──────────────
const palaceLiunianInfo = computed(() => {
  if (!result.value?.palaces) return {} as Record<number, { age: number; year: number }>
  const map: Record<number, { age: number; year: number }> = {}
  const birthYear = year.value
  const lifePalaceIdx = result.value.life_palace_branch_idx  // 命宫地支索引（子=0...亥=11）
  
  // 十二地支
  const branches = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
  
  // 找出每个宫位的地支索引
  result.value.palaces.forEach((p, idx) => {
    const branchIdx = branches.indexOf(p.branch)
    if (branchIdx < 0) return
    
    // 计算该宫位对应流年的年龄偏移（相对于命宫）
    // 流年命宫按地支轮转：该宫地支与命宫地支的差值
    const selectedYear = selectedLiunianYear.value
    
    // 计算该宫位何时为流年命宫
    // 流年地支每年+1，某宫为流年命宫时的年份 = 命宫为流年命宫的年份 + offset
    // 命宫为流年命宫的年份周期为12年
    
    // 找寻最接近当前选择流年的该宫位流年
    const yearsToCheck = []
    for (let y = birthYear; y <= 2100; y++) {
      // 该年的流年地支（简化：出生年命宫地支 + (该年 - 出生年) mod 12）
      // 实际上流年命宫由流年地支决定，但这里我们简化处理
      const liunianBranchOffset = (y - birthYear) % 12
      const liunianBranchIdx = (lifePalaceIdx + liunianBranchOffset) % 12
      if (liunianBranchIdx === branchIdx) {
        yearsToCheck.push(y)
      }
    }
    
    // 找最接近selectedYear的年份
    const closestYear = yearsToCheck.reduce((closest, y) => 
      Math.abs(y - selectedYear) < Math.abs(closest - selectedYear) ? y : closest
    , yearsToCheck[0] || selectedYear)
    
    if (closestYear) {
      map[idx] = { 
        age: closestYear - birthYear, 
        year: closestYear 
      }
    }
  })
  return map
})

// ── 大限宫位名称映射（宫位索引 → 大限名称） ───────────────
const palaceDaxianNames = computed(() => {
  if (!result.value?.palaces || !result.value?.dayun?.items) return {} as Record<number, string>
  
  const map: Record<number, string> = {}
  
  // 获取选中的大限或当前大限
  const activeDayun = selectedDaxianIdx.value >= 0 
    ? result.value.dayun.items[selectedDaxianIdx.value]
    : currentDayun.value
  
  if (!activeDayun) return map
  
  // 找到大限命宫（大限干支对应的宫位）
  const dayunPalaceIdx = result.value.palaces.findIndex(
    p => (p.stem + p.branch) === activeDayun.ganzhi
  )
  if (dayunPalaceIdx < 0) return map
  
  // 按顺/逆排布大限十二宫名称
  const forward = result.value.dayun.forward
  
  for (let i = 0; i < 12; i++) {
    // 计算该宫位在大限中的位置
    let targetIdx: number
    if (forward) {
      targetIdx = (dayunPalaceIdx + i) % 12
    } else {
      targetIdx = (dayunPalaceIdx - i + 12) % 12
    }
    map[targetIdx] = DAXIAN_PREFIX[i]
  }
  
  return map
})

// ── 当前流年命宫的宫位索引 ──────────────────────────────
const liunianLifePalaceIdx = computed(() => {
  if (!result.value?.palaces || result.value.palaces.length < 12) return -1
  
  const birthYear = year.value
  const lifePalaceIdx = result.value.life_palace_branch_idx  // 命宫地支索引
  
  // 流年命宫按年份轮转：每年往前移一个地支
  const yearOffset = (selectedLiunianYear.value - birthYear) % 12
  const liunianBranchIdx = (lifePalaceIdx + yearOffset + 120) % 12  // +120确保为正
  
  // 找到该地支对应的宫位索引
  const branches = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
  const targetBranch = branches[liunianBranchIdx]
  
  return result.value.palaces.findIndex(p => p.branch === targetBranch)
})

// ── 流年宫位名称映射（宫位索引 → 年命/年兄/年夫...） ────────
const palaceLiunianNames = computed(() => {
  const map: Record<number, string> = {}
  if (!result.value?.palaces || liunianLifePalaceIdx.value < 0) return map
  
  // 从流年命宫开始，顺时针排布十二宫名称
  // 流年始终顺行
  for (let i = 0; i < 12; i++) {
    const targetIdx = (liunianLifePalaceIdx.value + i) % 12
    map[targetIdx] = LIUNIAN_PREFIX[i]
  }
  
  return map
})

// ── 大限四化映射（星曜名 → 四化类型） ────────────────────
const daxianSihuaMap = computed(() => {
  if (!result.value?.dayun?.items) return {} as Record<string, string>
  
  const activeDayun = selectedDaxianIdx.value >= 0 
    ? result.value.dayun.items[selectedDaxianIdx.value]
    : currentDayun.value
  
  return activeDayun?.sihua || {}
})

// ── 流年四化映射（星曜名 → 四化类型） ────────────────────
const liunianSihuaMap = computed(() => {
  if (!result.value?.liunian) return {} as Record<string, string>
  return result.value.liunian.sihua || {}
})

// ── 流年四化附带宫位信息 ────────────────────────────────
const liunianSihuaWithPalace = computed(() => {
  const sihua = result.value?.liunian?.sihua || {}
  const palaces = result.value?.palaces || []
  return Object.entries(sihua).map(([star, transform]) => {
    const palace = palaces.find(p =>
      p.main_stars.some((s: { name: string }) => s.name === star) || p.aux_stars.includes(star)
    )
    return { star, transform, palaceName: palace?.name || '' }
  })
})

// ── 四柱八字详情 ──────────────────────────────────────────
const baziDetails = computed(() => {
  if (!result.value?.lunar) return null
  const lunar = result.value.lunar
  
  // 天干地支的传统含义
  const stemMeanings: Record<string, { element: string, yin_yang: string, meaning: string }> = {
    '甲': { element: '木', yin_yang: '阳', meaning: '生长出生，生机勃勃' },
    '乙': { element: '木', yin_yang: '阴', meaning: '柔软灵活，缠绕缗柔' },
    '丙': { element: '火', yin_yang: '阳', meaning: '炎热光彩，热情似火' },
    '丁': { element: '火', yin_yang: '阴', meaning: '温暖内秀，火焰柔和' },
    '戊': { element: '土', yin_yang: '阳', meaning: '厚实高大，坚实稳定' },
    '己': { element: '土', yin_yang: '阴', meaning: '温厚细腻，柔和谦虚' },
    '庚': { element: '金', yin_yang: '阳', meaning: '坚硬锐利，变革开放' },
    '辛': { element: '金', yin_yang: '阴', meaning: '精致细腻，锋芒内敛' },
    '壬': { element: '水', yin_yang: '阳', meaning: '流动奔放，聪敏多变' },
    '癸': { element: '水', yin_yang: '阴', meaning: '柔弱神秘，敏感智慧' },
  }
  
  const branchMeanings: Record<string, { zodiac: string, element: string, meaning: string }> = {
    '子': { zodiac: '鼠', element: '水', meaning: '聪慧敏锐，夜间之灵' },
    '丑': { zodiac: '牛', element: '土', meaning: '勤勉踏实，坚韧刻苦' },
    '寅': { zodiac: '虎', element: '木', meaning: '勇猛阳刚，震撼雄峙' },
    '卯': { zodiac: '兔', element: '木', meaning: '温柔秀雅，活泼灵巧' },
    '辰': { zodiac: '龙', element: '土', meaning: '龙威显赫，气势磅礴' },
    '巳': { zodiac: '蛇', element: '火', meaning: '聪敏狡黠，智慧深思' },
    '午': { zodiac: '马', element: '火', meaning: '热烈奔放，光彩夺目' },
    '未': { zodiac: '羊', element: '土', meaning: '温和善良，艺术灵秀' },
    '申': { zodiac: '猴', element: '金', meaning: '灵机敏锐，多才多艺' },
    '酉': { zodiac: '鸡', element: '金', meaning: '警惕认真，文采斐然' },
    '戌': { zodiac: '狗', element: '土', meaning: '忠诚守信，坦诚直率' },
    '亥': { zodiac: '猪', element: '水', meaning: '温和坦率，智慧感悟' },
  }
  
  const yearStem = lunar.year_gz?.charAt(0) || ''
  const yearBranch = lunar.year_gz?.charAt(1) || ''
  const monthStem = lunar.jieqi_month_gz?.charAt(0) || lunar.month_gz?.charAt(0) || ''
  const monthBranch = lunar.jieqi_month_gz?.charAt(1) || lunar.month_gz?.charAt(1) || ''
  const dayStem = lunar.day_gz?.charAt(0) || ''
  const dayBranch = lunar.day_gz?.charAt(1) || ''
  const hourStem = lunar.hour_gz?.charAt(0) || ''
  const hourBranch = lunar.hour_branch || lunar.hour_gz?.charAt(1) || ''
  
  return {
    year: { stem: yearStem, branch: yearBranch, stemInfo: stemMeanings[yearStem], branchInfo: branchMeanings[yearBranch] },
    month: { stem: monthStem, branch: monthBranch, stemInfo: stemMeanings[monthStem], branchInfo: branchMeanings[monthBranch], isJieqi: lunar.jieqi_month_gz && lunar.jieqi_month_gz !== lunar.month_gz },
    day: { stem: dayStem, branch: dayBranch, stemInfo: stemMeanings[dayStem], branchInfo: branchMeanings[dayBranch] },
    hour: { stem: hourStem, branch: hourBranch, stemInfo: stemMeanings[hourStem], branchInfo: branchMeanings[hourBranch] },
  }
})

  // ── 十神分析 ────────────────────────────────────────────────
  const shiShenAnalyze = computed(() => {
    if (!baziDetails.value) return null
    const dayMaster = baziDetails.value.day.stem
    const shishenRelations: Record<string, Record<string, string>> = {
      '甲': { '甲': '比肩', '乙': '劫财', '丙': '食神', '丁': '伤官', '戊': '偏财', '己': '正财', '庚': '七杀', '辛': '正官', '壬': '偏印', '癸': '正印' },
      '乙': { '甲': '劫财', '乙': '比肩', '丙': '伤官', '丁': '食神', '戊': '正财', '己': '偏财', '庚': '正官', '辛': '七杀', '壬': '正印', '癸': '偏印' },
      '丙': { '甲': '食神', '乙': '伤官', '丙': '比肩', '丁': '劫财', '戊': '偏印', '己': '正印', '庚': '偏财', '辛': '正财', '壬': '七杀', '癸': '正官' },
      '丁': { '甲': '伤官', '乙': '食神', '丙': '劫财', '丁': '比肩', '戊': '正印', '己': '偏印', '庚': '正财', '辛': '偏财', '壬': '正官', '癸': '七杀' },
      '戊': { '甲': '偏财', '乙': '正财', '丙': '偏印', '丁': '正印', '戊': '比肩', '己': '劫财', '庚': '伤官', '辛': '食神', '壬': '正官', '癸': '七杀' },
      '己': { '甲': '正财', '乙': '偏财', '丙': '正印', '丁': '偏印', '戊': '劫财', '己': '比肩', '庚': '食神', '辛': '伤官', '壬': '七杀', '癸': '正官' },
      '庚': { '甲': '七杀', '乙': '正官', '丙': '偏财', '丁': '正财', '戊': '伤官', '己': '食神', '庚': '比肩', '辛': '劫财', '壬': '偏印', '癸': '正印' },
      '辛': { '甲': '正官', '乙': '七杀', '丙': '正财', '丁': '偏财', '戊': '食神', '己': '伤官', '庚': '劫财', '辛': '比肩', '壬': '正印', '癸': '偏印' },
      '壬': { '甲': '偏印', '乙': '正印', '丙': '七杀', '丁': '正官', '戊': '偏财', '己': '正财', '庚': '正官', '辛': '七杀', '壬': '比肩', '癸': '劫财' },
      '癸': { '甲': '正印', '乙': '偏印', '丙': '正官', '丁': '七杀', '戊': '正财', '己': '偏财', '庚': '七杀', '辛': '正官', '壬': '劫财', '癸': '比肩' },
    }
    return { dayMaster, relations: shishenRelations[dayMaster] || {} }
  })

  // ── 地支藏干与纳音五行 ────────────────────────────────────
  const cangganNayin = computed(() => {
    const branchCanggan: Record<string, { main: string, aux1?: string, aux2?: string }> = {
      '子': { main: '癸' },
      '丑': { main: '己', aux1: '辛', aux2: '癸' },
      '寅': { main: '甲', aux1: '丙', aux2: '戊' },
      '卯': { main: '乙' },
      '辰': { main: '戊', aux1: '乙', aux2: '癸' },
      '巳': { main: '丙', aux1: '戊', aux2: '庚' },
      '午': { main: '丁', aux1: '己' },
      '未': { main: '己', aux1: '丁', aux2: '乙' },
      '申': { main: '庚', aux1: '壬', aux2: '戊' },
      '酉': { main: '辛' },
      '戌': { main: '戊', aux1: '辛', aux2: '丁' },
      '亥': { main: '壬', aux1: '甲' },
    }
  
    const nayinMap: Record<string, string> = {
      '甲子': '海中金', '乙丑': '海中金',
      '丙寅': '炉中火', '丁卯': '炉中火',
      '戊辰': '大林木', '己巳': '大林木',
      '庚午': '路旁土', '辛未': '路旁土',
      '壬申': '剑锋金', '癸酉': '剑锋金',
      '甲戌': '山头火', '乙亥': '山头火',
      '丙子': '涧下水', '丁丑': '涧下水',
      '戊寅': '城头土', '己卯': '城头土',
      '庚辰': '白蜡金', '辛巳': '白蜡金',
      '壬午': '杨柳木', '癸未': '杨柳木',
      '甲申': '泉中水', '乙酉': '泉中水',
      '丙戌': '屋上土', '丁亥': '屋上土',
      '戊子': '霹雳火', '己丑': '霹雳火',
      '庚寅': '松柏木', '辛卯': '松柏木',
      '壬辰': '长流水', '癸巳': '长流水',
      '甲午': '沙中金', '乙未': '沙中金',
      '丙申': '山下火', '丁酉': '山下火',
      '戊戌': '平地木', '己亥': '平地木',
    }
  
    if (!baziDetails.value) return null
    const details = baziDetails.value
    return {
      year: { branch: details.year.branch, canggan: branchCanggan[details.year.branch], nayin: nayinMap[details.year.stem + details.year.branch] },
      month: { branch: details.month.branch, canggan: branchCanggan[details.month.branch], nayin: nayinMap[details.month.stem + details.month.branch] },
      day: { branch: details.day.branch, canggan: branchCanggan[details.day.branch], nayin: nayinMap[details.day.stem + details.day.branch] },
      hour: { branch: details.hour.branch, canggan: branchCanggan[details.hour.branch], nayin: nayinMap[details.hour.stem + details.hour.branch] },
    }
  })

// ── 神煞与定位（1.6）────────────────────────────────────
const baziShenshaList = computed(() => {
  if (!baziDetails.value) return [] as Array<{ name: string; level: '吉' | '中' | '警'; hit: string[]; reason: string }>

  const details = baziDetails.value
  const branches = [details.year.branch, details.month.branch, details.day.branch, details.hour.branch]
  const branchLabels = ['年柱', '月柱', '日柱', '时柱']

  const findHit = (targets: string[]) =>
    branches
      .map((b, idx) => (targets.includes(b) ? branchLabels[idx] : ''))
      .filter(Boolean)

  const dayStem = details.day.stem
  const dayBranch = details.day.branch
  const yearBranch = details.year.branch

  const tianyiMap: Record<string, string[]> = {
    '甲': ['丑', '未'], '乙': ['子', '申'], '丙': ['亥', '酉'], '丁': ['亥', '酉'],
    '戊': ['丑', '未'], '己': ['子', '申'], '庚': ['寅', '午'], '辛': ['寅', '午'],
    '壬': ['卯', '巳'], '癸': ['卯', '巳'],
  }
  const taohuaMap: Record<string, string> = { '申': '酉', '子': '酉', '辰': '酉', '寅': '卯', '午': '卯', '戌': '卯', '亥': '子', '卯': '子', '未': '子', '巳': '午', '酉': '午', '丑': '午' }
  const yimaMap: Record<string, string> = { '申': '寅', '子': '寅', '辰': '寅', '寅': '申', '午': '申', '戌': '申', '亥': '巳', '卯': '巳', '未': '巳', '巳': '亥', '酉': '亥', '丑': '亥' }
  const huagaiMap: Record<string, string> = { '申': '辰', '子': '辰', '辰': '辰', '寅': '戌', '午': '戌', '戌': '戌', '亥': '未', '卯': '未', '未': '未', '巳': '丑', '酉': '丑', '丑': '丑' }

  const resultList: Array<{ name: string; level: '吉' | '中' | '警'; hit: string[]; reason: string }> = []

  const tianyiHit = findHit(tianyiMap[dayStem] || [])
  if (tianyiHit.length) {
    resultList.push({
      name: '天乙贵人',
      level: '吉',
      hit: tianyiHit,
      reason: `以日干${dayStem}查贵人位，命局见${(tianyiMap[dayStem] || []).join('、')}，主逢凶化吉。`,
    })
  }

  const taohuaTarget = taohuaMap[yearBranch] || taohuaMap[dayBranch]
  const taohuaHit = taohuaTarget ? findHit([taohuaTarget]) : []
  if (taohuaHit.length) {
    resultList.push({
      name: '桃花',
      level: '中',
      hit: taohuaHit,
      reason: `以年支/日支查桃花位，见${taohuaTarget}，人缘与情感互动较活跃。`,
    })
  }

  const yimaTarget = yimaMap[yearBranch] || yimaMap[dayBranch]
  const yimaHit = yimaTarget ? findHit([yimaTarget]) : []
  if (yimaHit.length) {
    resultList.push({
      name: '驿马',
      level: '中',
      hit: yimaHit,
      reason: `命局见驿马位${yimaTarget}，多主变动、奔波或跨地域机会。`,
    })
  }

  const huagaiTarget = huagaiMap[yearBranch] || huagaiMap[dayBranch]
  const huagaiHit = huagaiTarget ? findHit([huagaiTarget]) : []
  if (huagaiHit.length) {
    resultList.push({
      name: '华盖',
      level: '中',
      hit: huagaiHit,
      reason: `命局临华盖位${huagaiTarget}，偏向思辨、艺术与独处沉淀。`,
    })
  }

  const wuxingWeak = ['木', '火', '土', '金', '水'].filter((e) => baziWuxingCount(e) === Math.min(...['木', '火', '土', '金', '水'].map((x) => baziWuxingCount(x))))
  if (wuxingWeak.length > 0) {
    resultList.push({
      name: '五行偏枯提示',
      level: '警',
      hit: ['全盘'],
      reason: `当前偏弱五行为${wuxingWeak.join('、')}，建议在起名、行业与作息中做补益。`,
    })
  }

  return resultList
})

// ── 冲合刑破（1.7）──────────────────────────────────────
const baziRelationAnalyze = computed(() => {
  if (!baziDetails.value) return { branchRelations: [], stemRelations: [] } as {
    branchRelations: Array<{ type: string; a: string; b: string; pillars: string }>
    stemRelations: Array<{ type: string; a: string; b: string; pillars: string }>
  }

  const details = baziDetails.value
  const pillarData = [
    { key: '年柱', stem: details.year.stem, branch: details.year.branch },
    { key: '月柱', stem: details.month.stem, branch: details.month.branch },
    { key: '日柱', stem: details.day.stem, branch: details.day.branch },
    { key: '时柱', stem: details.hour.stem, branch: details.hour.branch },
  ]

  const liuhe = new Map<string, string>([['子', '丑'], ['寅', '亥'], ['卯', '戌'], ['辰', '酉'], ['巳', '申'], ['午', '未']])
  const liuchong = new Map<string, string>([['子', '午'], ['丑', '未'], ['寅', '申'], ['卯', '酉'], ['辰', '戌'], ['巳', '亥']])
  const xiangxingGroups = [['寅', '巳', '申'], ['丑', '未', '戌']]
  const ziMaoXing = ['子', '卯']

  const stemHe = new Map<string, string>([['甲', '己'], ['乙', '庚'], ['丙', '辛'], ['丁', '壬'], ['戊', '癸']])
  const stemKe: Record<string, string[]> = {
    '甲': ['戊', '己'], '乙': ['戊', '己'], '丙': ['庚', '辛'], '丁': ['庚', '辛'],
    '戊': ['壬', '癸'], '己': ['壬', '癸'], '庚': ['甲', '乙'], '辛': ['甲', '乙'],
    '壬': ['丙', '丁'], '癸': ['丙', '丁'],
  }

  const branchRelations: Array<{ type: string; a: string; b: string; pillars: string }> = []
  const stemRelations: Array<{ type: string; a: string; b: string; pillars: string }> = []

  for (let i = 0; i < pillarData.length; i++) {
    for (let j = i + 1; j < pillarData.length; j++) {
      const A = pillarData[i]
      const B = pillarData[j]

      if (liuhe.get(A.branch) === B.branch || liuhe.get(B.branch) === A.branch) {
        branchRelations.push({ type: '六合', a: A.branch, b: B.branch, pillars: `${A.key} - ${B.key}` })
      }
      if (liuchong.get(A.branch) === B.branch || liuchong.get(B.branch) === A.branch) {
        branchRelations.push({ type: '六冲', a: A.branch, b: B.branch, pillars: `${A.key} - ${B.key}` })
      }
      if (xiangxingGroups.some((g) => g.includes(A.branch) && g.includes(B.branch)) || (ziMaoXing.includes(A.branch) && ziMaoXing.includes(B.branch))) {
        branchRelations.push({ type: '相刑', a: A.branch, b: B.branch, pillars: `${A.key} - ${B.key}` })
      }

      if (stemHe.get(A.stem) === B.stem || stemHe.get(B.stem) === A.stem) {
        stemRelations.push({ type: '天干合', a: A.stem, b: B.stem, pillars: `${A.key} - ${B.key}` })
      }
      if ((stemKe[A.stem] || []).includes(B.stem) || (stemKe[B.stem] || []).includes(A.stem)) {
        stemRelations.push({ type: '天干克', a: A.stem, b: B.stem, pillars: `${A.key} - ${B.key}` })
      }
    }
  }

  return { branchRelations, stemRelations }
})

// ── 格局判定与用神（1.8）────────────────────────────────
const baziGejuYongshen = computed(() => {
  if (!baziDetails.value || !shiShenAnalyze.value) return null

  const details = baziDetails.value
  const rel = shiShenAnalyze.value.relations
  const otherStems = [details.year.stem, details.month.stem, details.hour.stem]
  const countMap: Record<string, number> = {}

  otherStems.forEach((stem) => {
    const r = rel[stem]
    if (!r) return
    countMap[r] = (countMap[r] || 0) + 1
  })

  const dominant = Object.entries(countMap).sort((a, b) => b[1] - a[1])[0]?.[0] || '比肩'
  const gejuMap: Record<string, string> = {
    '正官': '正官格倾向', '七杀': '七杀格倾向', '正财': '财格倾向', '偏财': '偏财格倾向',
    '食神': '食神格倾向', '伤官': '伤官格倾向', '正印': '印绶格倾向', '偏印': '偏印格倾向',
    '比肩': '比劫格倾向', '劫财': '比劫格倾向',
  }

  const wuxingAll = ['木', '火', '土', '金', '水']
  const counts = wuxingAll.map((element) => ({ element, count: baziWuxingCount(element) }))
  const minCount = Math.min(...counts.map((x) => x.count))
  const maxCount = Math.max(...counts.map((x) => x.count))
  const favor = counts.filter((x) => x.count === minCount).map((x) => x.element)
  const avoid = counts.filter((x) => x.count === maxCount).map((x) => x.element)

  return {
    dominant,
    gejuName: gejuMap[dominant] || '综合平衡格局',
    favor,
    avoid,
    rationale: `以月令与透干关系估算，当前十神主导为${dominant}；结合五行分布，宜补${favor.join('、')}，慎过旺之${avoid.join('、')}。`,
  }
})

// ── 大运/流年/流月（1.9）────────────────────────────────
const baziLuckOverview = computed(() => {
  const dayunItems = (result.value?.dayun?.items || []) as Array<Record<string, unknown>>
  const liuyueItems = (result.value?.liuyue || []) as Array<Record<string, unknown>>
  const liunian = (result.value?.liunian || null) as Record<string, unknown> | null

  const dayun = dayunItems.slice(0, 8).map((item, idx) => {
    const stem = String(item.stem || '')
    const branch = String(item.branch || '')
    const ganzhi = String(item.ganzhi || `${stem}${branch}`)
    const startAge = Number(item.start_age || 0)
    const endAge = Number(item.end_age || 0)
    const startYear = Number(item.start_year || 0)
    return {
      rawIdx: idx,
      idx: idx + 1,
      ganzhi,
      startAge,
      endAge,
      startYear,
      isCurrent: currentDayunGz.value ? currentDayunGz.value === ganzhi : false,
    }
  })

  const liuyue = liuyueItems.slice(0, 12).map((m) => ({
    month: Number(m.month || 0),
    monthName: String(m.month_name || `${m.month || ''}月`),
    monthGz: String(m.month_gz || ''),
    palace: String(m.palace_name || ''),
  }))

  return {
    currentDayun: currentDayunGz.value || '',
    dayun,
    liunianYear: Number(liunian?.year || 0),
    liunianGz: String(liunian?.ganzhi || ''),
    liuyue,
  }
})

const baziDayunFocusDetail = computed(() => {
  const dayunItems = (result.value?.dayun?.items || []) as Array<Record<string, unknown>>
  if (!dayunItems.length) return null

  let idx = baziDayunFocusIdx.value
  if (idx < 0 || idx >= dayunItems.length) {
    idx = dayunItems.findIndex((item) => {
      const gz = String(item.ganzhi || `${String(item.stem || '')}${String(item.branch || '')}`)
      return currentDayunGz.value ? gz === currentDayunGz.value : false
    })
    if (idx < 0) idx = 0
  }

  const item = dayunItems[idx]
  const ganzhi = String(item.ganzhi || `${String(item.stem || '')}${String(item.branch || '')}`)
  return {
    idx: idx + 1,
    rawIdx: idx,
    ganzhi,
    startAge: Number(item.start_age || 0),
    endAge: Number(item.end_age || 0),
    startYear: Number(item.start_year || 0),
    tenGod: String(item.ten_god || ''),
    narrative: String(item.narrative || ''),
  }
})

const baziFocusedDayunSihuaStars = computed(() => {
  const dayunItems = (result.value?.dayun?.items || []) as Array<Record<string, unknown>>
  if (!dayunItems.length || !baziDayunFocusDetail.value) return [] as string[]
  const item = dayunItems[baziDayunFocusDetail.value.rawIdx]
  if (!item || typeof item !== 'object') return [] as string[]
  const sihua = (item.sihua || {}) as Record<string, unknown>
  return Object.keys(sihua)
})

const baziRelatedLiuyueMap = computed(() => {
  const liuyueItems = (result.value?.liuyue || []) as Array<Record<string, unknown>>
  const dayunStars = baziFocusedDayunSihuaStars.value
  const related: Record<number, number> = {}
  if (!liuyueItems.length || !dayunStars.length) return related

  const dayunSet = new Set(dayunStars)
  liuyueItems.forEach((m) => {
    const month = Number(m.month || 0)
    if (!month) return
    const monthSihua = (m.sihua || {}) as Record<string, unknown>
    const monthStars = Object.keys(monthSihua)
    const matched = monthStars.filter((s) => dayunSet.has(s)).length
    if (matched > 0) related[month] = matched
  })
  return related
})

// ── 十神宫位用法（1.10）────────────────────────────────
const baziTenGodUsage = computed(() => {
  if (!baziDetails.value || !shiShenAnalyze.value) return [] as Array<{ pillar: string; stem: string; tenGod: string; interpretation: string }>

  const details = baziDetails.value
  const dayMasterRel = shiShenAnalyze.value.relations

  const usageMap: Record<string, string> = {
    '比肩': '适合自主与并行发展，宜强化执行与自我边界。',
    '劫财': '强调资源调配与竞争意识，需注意财务分配。',
    '食神': '利输出与口碑沉淀，适合长期主义路径。',
    '伤官': '表达力强，利创新突破，注意节奏与规则平衡。',
    '偏财': '利市场与机会型收益，宜重风控。',
    '正财': '利稳健经营与现金流管理，适合可持续积累。',
    '七杀': '目标导向强，利攻坚，需配套情绪与压力管理。',
    '正官': '利组织与制度体系，适合走规范路径。',
    '偏印': '利学习与研究，适合策略型岗位。',
    '正印': '利贵人与资质提升，适合长期进修与背书。',
  }

  const items = [
    { pillar: '年柱（外部环境）', stem: details.year.stem },
    { pillar: '月柱（事业核心）', stem: details.month.stem },
    { pillar: '日柱（自我关系）', stem: details.day.stem },
    { pillar: '时柱（晚景与产出）', stem: details.hour.stem },
  ]

  return items.map((item) => {
    const tenGod = dayMasterRel[item.stem] || '比肩'
    return {
      pillar: item.pillar,
      stem: item.stem,
      tenGod,
      interpretation: usageMap[tenGod] || '可结合大运流年进一步细化。',
    }
  })
})

function copyBaziSectionSummary() {
  if (!result.value) return

  const title = baziMenuItems[baziMenuActive.value] || '四柱摘要'
  const lines: string[] = [`【${title}】`]

  if (baziMenuActive.value === 'shengchen') {
    lines.push(`出生：${result.value.birth_solar} ${result.value.gender}`)
    lines.push(`农历：${result.value.lunar.lunar_year}年${result.value.lunar.is_leap_month ? '闰' : ''}${result.value.lunar.lunar_month}月${result.value.lunar.lunar_day}日 ${result.value.lunar.hour_branch}时`)
    if (result.value.true_solar_time) lines.push(`真太阳时：${result.value.true_solar_time}`)
  }

  if (baziMenuActive.value === 'sizhu' && baziDetails.value) {
    lines.push(`年柱：${baziDetails.value.year.stem}${baziDetails.value.year.branch}`)
    lines.push(`月柱：${baziDetails.value.month.stem}${baziDetails.value.month.branch}`)
    lines.push(`日柱：${baziDetails.value.day.stem}${baziDetails.value.day.branch}`)
    lines.push(`时柱：${baziDetails.value.hour.stem}${baziDetails.value.hour.branch}`)
  }

  if (baziMenuActive.value === 'ribuzhu' && shiShenAnalyze.value) {
    lines.push(`日主：${shiShenAnalyze.value.dayMaster}`)
    const core = ['甲', '乙', '丙', '丁']
      .map((s) => `${s}:${shiShenAnalyze.value?.relations?.[s] || '-'}`)
      .join('，')
    lines.push(`十神参考：${core}`)
  }

  if (baziMenuActive.value === 'wuxing') {
    lines.push(`五行分布：木${baziWuxingCount('木')} 火${baziWuxingCount('火')} 土${baziWuxingCount('土')} 金${baziWuxingCount('金')} 水${baziWuxingCount('水')}`)
  }

  if (baziMenuActive.value === 'canggan' && cangganNayin.value) {
    ;(['year', 'month', 'day', 'hour'] as const).forEach((k, idx) => {
      const p = cangganNayin.value?.[k]
      if (!p) return
      const cg = [p.canggan?.main, p.canggan?.aux1, p.canggan?.aux2].filter(Boolean).join('/')
      lines.push(`${['年', '月', '日', '时'][idx]}柱：藏干${cg || '-'}，纳音${p.nayin || '-'}`)
    })
  }

  if (baziMenuActive.value === 'shenshai') {
    if (baziShenshaList.value.length) {
      lines.push(...baziShenshaList.value.map((x) => `${x.name}（${x.level}）- ${x.hit.join('、')}`))
    } else {
      lines.push('当前命盘未检出显著神煞组合。')
    }
  }

  if (baziMenuActive.value === 'chonghehexpo') {
    const branch = baziRelationAnalyze.value.branchRelations.slice(0, 5).map((x) => `${x.type}:${x.a}${x.b}`).join('，')
    const stem = baziRelationAnalyze.value.stemRelations.slice(0, 5).map((x) => `${x.type}:${x.a}${x.b}`).join('，')
    lines.push(`地支：${branch || '平和'}`)
    lines.push(`天干：${stem || '平和'}`)
  }

  if (baziMenuActive.value === 'geju' && baziGejuYongshen.value) {
    lines.push(`格局：${baziGejuYongshen.value.gejuName}`)
    lines.push(`宜：${baziGejuYongshen.value.favor.join('、') || '-'}`)
    lines.push(`慎：${baziGejuYongshen.value.avoid.join('、') || '-'}`)
    lines.push(`说明：${baziGejuYongshen.value.rationale}`)
  }

  if (baziMenuActive.value === 'dayun') {
    lines.push(`当前大运：${baziLuckOverview.value.currentDayun || '未定位'}`)
    lines.push(`流年：${baziLuckOverview.value.liunianYear || '-'} ${baziLuckOverview.value.liunianGz || ''}`)
    if (baziDayunFocusDetail.value) {
      lines.push(`选中大运：${baziDayunFocusDetail.value.ganzhi}（${baziDayunFocusDetail.value.startAge}-${baziDayunFocusDetail.value.endAge}岁）`)
    }
  }

  if (baziMenuActive.value === 'shishen') {
    lines.push(...baziTenGodUsage.value.map((x) => `${x.pillar}：${x.stem}→${x.tenGod}`))
  }

  navigator.clipboard.writeText(lines.join('\n')).then(() => {
    baziCopyDone.value = true
    setTimeout(() => { baziCopyDone.value = false }, 1400)
  })
}
// ── 选中的流月数据 ─────────────────────────────────────────
const selectedLiuyueData = computed(() => {
  if (!result.value?.liuyue?.length || selectedLiuyueMonth.value <= 0) return null
  return result.value.liuyue.find(m => m.month === selectedLiuyueMonth.value) || null
})

// ── 流月命宫的宫位索引 ─────────────────────────────────────
const liuyueLifePalaceIdx = computed(() => {
  if (!result.value?.palaces || !selectedLiuyueData.value) return -1
  
  const branches = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
  // 流月命宫由 life_palace_branch 字段指定
  const branchIdx = selectedLiuyueData.value.life_palace_branch
  if (branchIdx < 0 || branchIdx > 11) return -1
  
  const targetBranch = branches[branchIdx]
  return result.value.palaces.findIndex(p => p.branch === targetBranch)
})

// ── 流月宫位名称映射（宫位索引 → 月命/月兄/月夫...） ────────
const palaceLiuyueNames = computed(() => {
  const map: Record<number, string> = {}
  if (!result.value?.palaces || liuyueLifePalaceIdx.value < 0) return map
  
  // 从流月命宫开始，顺时针排布十二宫名称
  for (let i = 0; i < 12; i++) {
    const targetIdx = (liuyueLifePalaceIdx.value + i) % 12
    map[targetIdx] = LIUYUE_PREFIX[i]
  }
  
  return map
})

// ── 流月四化映射（星曜名 → 四化类型） ────────────────────
const liuyueSihuaMap = computed(() => {
  if (!selectedLiuyueData.value) return {} as Record<string, string>
  return selectedLiuyueData.value.sihua || {}
})

// ── 当前流年年龄 ─────────────────────────────────────────
const currentLiunianAge = computed(() => {
  return selectedLiunianYear.value - year.value
})

// ── 小限宫位索引（根据当前流年年龄计算） ─────────────────
const xiaoxianPalaceIdx = computed(() => {
  if (!result.value?.palaces || currentLiunianAge.value < 1) return -1
  
  // 从xiaoxian_ages字段找到对应的宫位
  const targetAge = currentLiunianAge.value
  const idx = result.value.palaces.findIndex(p => 
    p.xiaoxian_ages && p.xiaoxian_ages.includes(targetAge)
  )
  return idx
})

// ── 三方四正高亮（选中宫位的三合+对宫）───────────────────
const sanfangIndices = computed(() => {
  if (!selectedPalace.value) return new Set<number>()
  const idx = selectedPalace.value.index
  // 三合: idx, idx+4, idx+8 (每隔4宫，形成三角)
  // 对宫: idx+6
  return new Set([
    (idx + 4) % 12,
    (idx + 8) % 12,
    (idx + 6) % 12,
  ])
})

// ── 小限宫位名称常量 ─────────────────────────────────────
const XIAOXIAN_PREFIX = ['小命','小兄','小夫','小子','小财','小疾','小迁','小友','小官','小田','小福','小父']

// ── 小限宫位名称映射（宫位索引 → 小命/小兄/小夫...） ────────
const palaceXiaoxianNames = computed(() => {
  const map: Record<number, string> = {}
  if (!result.value?.palaces || xiaoxianPalaceIdx.value < 0) return map
  
  // 从小限命宫开始排布，性别决定顺逆
  const forward = gender.value === '男'
  
  for (let i = 0; i < 12; i++) {
    let targetIdx: number
    if (forward) {
      targetIdx = (xiaoxianPalaceIdx.value + i) % 12
    } else {
      targetIdx = (xiaoxianPalaceIdx.value - i + 12) % 12
    }
    map[targetIdx] = XIAOXIAN_PREFIX[i]
  }
  
  return map
})

// ══════════════════════════════════════════════════════════════════
// 命盘批注/笔记功能
// ══════════════════════════════════════════════════════════════════
interface ChartNote {
  id: string
  target: 'palace' | 'star' | 'general'
  targetName: string
  content: string
  createdAt: number
  updatedAt: number
}

const NOTES_KEY = 'ziwei_chart_notes'
const chartNotes = ref<ChartNote[]>(JSON.parse(localStorage.getItem(NOTES_KEY) || '[]'))
const showNotesPanel = ref(false)
const editingNote = ref<ChartNote | null>(null)
const noteInput = ref('')
const noteTarget = ref<'palace' | 'star' | 'general'>('general')
const noteTargetName = ref('')

function saveNotesToStorage() {
  localStorage.setItem(NOTES_KEY, JSON.stringify(chartNotes.value))
}

function addNote() {
  if (!noteInput.value.trim()) return
  const note: ChartNote = {
    id: `note_${Date.now()}`,
    target: noteTarget.value,
    targetName: noteTargetName.value || '全盘',
    content: noteInput.value.trim(),
    createdAt: Date.now(),
    updatedAt: Date.now(),
  }
  chartNotes.value.unshift(note)
  saveNotesToStorage()
  noteInput.value = ''
  noteTargetName.value = ''
  noteTarget.value = 'general'
}

function updateNote() {
  if (!editingNote.value || !noteInput.value.trim()) return
  const idx = chartNotes.value.findIndex(n => n.id === editingNote.value?.id)
  if (idx >= 0) {
    chartNotes.value[idx] = {
      ...chartNotes.value[idx],
      content: noteInput.value.trim(),
      updatedAt: Date.now(),
    }
    saveNotesToStorage()
  }
  editingNote.value = null
  noteInput.value = ''
}

function startEditNote(note: ChartNote) {
  editingNote.value = note
  noteInput.value = note.content
  noteTarget.value = note.target
  noteTargetName.value = note.targetName
}

function cancelEditNote() {
  editingNote.value = null
  noteInput.value = ''
  noteTarget.value = 'general'
  noteTargetName.value = ''
}

function deleteNote(id: string) {
  chartNotes.value = chartNotes.value.filter(n => n.id !== id)
  saveNotesToStorage()
  if (editingNote.value?.id === id) {
    cancelEditNote()
  }
}

// ══════════════════════════════════════════════════════════════════
// 宫位收藏/书签功能
// ══════════════════════════════════════════════════════════════════
const BOOKMARKS_KEY = 'ziwei_palace_bookmarks'
const palaceBookmarks = ref<Set<number>>(new Set(JSON.parse(localStorage.getItem(BOOKMARKS_KEY) || '[]')))

function togglePalaceBookmark(idx: number) {
  if (palaceBookmarks.value.has(idx)) {
    palaceBookmarks.value.delete(idx)
  } else {
    palaceBookmarks.value.add(idx)
  }
  localStorage.setItem(BOOKMARKS_KEY, JSON.stringify([...palaceBookmarks.value]))
}

function isPalaceBookmarked(idx: number): boolean {
  return palaceBookmarks.value.has(idx)
}

// 获取已收藏宫位列表
const bookmarkedPalaces = computed(() => {
  if (!result.value?.palaces) return []
  return result.value.palaces.filter(p => palaceBookmarks.value.has(p.index))
})

// ══════════════════════════════════════════════════════════════════
// 命盘对比模式
// ══════════════════════════════════════════════════════════════════
const showComparePanel = ref(false)
const compareTarget = ref<{
  year: number
  month: number
  day: number
  hour: number
  minute: number
  gender: '男' | '女'
} | null>(null)

const compareYear = ref(1990)
const compareMonth = ref(1)
const compareDay = ref(1)
const compareHour = ref(12)
const compareMinute = ref(0)
const compareGender = ref<'男' | '女'>('女')

function setCompareTarget() {
  compareTarget.value = {
    year: compareYear.value,
    month: compareMonth.value,
    day: compareDay.value,
    hour: compareHour.value,
    minute: compareMinute.value,
    gender: compareGender.value,
  }
  showComparePanel.value = false
}

function clearCompareTarget() {
  compareTarget.value = null
}

// ══════════════════════════════════════════════════════════════════
// 运势日历快捷视图
// ══════════════════════════════════════════════════════════════════
const showCalendarView = ref(false)
const calendarViewYear = ref(new Date().getFullYear())
const calendarViewMonth = ref(new Date().getMonth() + 1)

interface DayFortune {
  day: number
  score: number
  brief: string
}

// 生成当月日历数据
const calendarDays = computed((): DayFortune[] => {
  const days: DayFortune[] = []
  const daysInMonth = new Date(calendarViewYear.value, calendarViewMonth.value, 0).getDate()
  
  for (let d = 1; d <= daysInMonth; d++) {
    // 简化的运势计算：基于流月数据 + 日期调整
    const monthForecast = getMonthForecast(calendarViewMonth.value)
    const baseScore = monthForecast?.score ?? 70
    
    // 根据日期微调分数（简化模拟）
    const dayMod = ((d * 7) % 20) - 10  // -10 ~ +10 的波动
    const score = Math.max(30, Math.min(100, baseScore + dayMod))
    
    // 简要描述
    let brief = '平'
    if (score >= 85) brief = '大吉'
    else if (score >= 75) brief = '吉'
    else if (score >= 60) brief = '平'
    else if (score >= 45) brief = '凶'
    else brief = '大凶'
    
    days.push({ day: d, score, brief })
  }
  
  return days
})

// 获取当月第一天是周几 (0=周日, 1=周一, ...)
const calendarFirstDayOfWeek = computed(() => {
  return new Date(calendarViewYear.value, calendarViewMonth.value - 1, 1).getDay()
})

// 日历网格（包含前置空白）
const calendarGrid = computed(() => {
  const grid: (DayFortune | null)[] = []
  // 添加前置空白
  for (let i = 0; i < calendarFirstDayOfWeek.value; i++) {
    grid.push(null)
  }
  // 添加实际日期
  grid.push(...calendarDays.value)
  return grid
})

function prevCalendarMonth() {
  if (calendarViewMonth.value === 1) {
    calendarViewMonth.value = 12
    calendarViewYear.value--
  } else {
    calendarViewMonth.value--
  }
}

function nextCalendarMonth() {
  if (calendarViewMonth.value === 12) {
    calendarViewMonth.value = 1
    calendarViewYear.value++
  } else {
    calendarViewMonth.value++
  }
}

function getDayFortuneClass(score: number): string {
  if (score >= 85) return 'fortune-great'
  if (score >= 75) return 'fortune-good'
  if (score >= 60) return 'fortune-normal'
  if (score >= 45) return 'fortune-bad'
  return 'fortune-terrible'
}

// ══════════════════════════════════════════════════════════════════
// 已收藏宫位快捷面板
// ══════════════════════════════════════════════════════════════════
const showBookmarksPanel = ref(false)

// ══════════════════════════════════════════════════════════════════
// 键盘方向键导航宫位
// ══════════════════════════════════════════════════════════════════
function handleKeyNavigation(e: KeyboardEvent) {
  if (!result.value?.palaces || !selectedPalace.value) return
  
  // 只在命盘区域激活时响应
  const idx = selectedPalace.value.index
  let newIdx = idx
  
  // 紫微斗数盘布局：
  // 逆时针排列 4x4 格子，中间4格为中心
  // 索引布局（参考）:
  //  巳4  午5  未6  申7
  //  辰3  --   --  酉8
  //  卯2  --   --  戌9
  //  寅1  丑0  子11 亥10
  
  const navMap: Record<number, Record<string, number>> = {
    0:  { ArrowUp: 3, ArrowRight: 11, ArrowLeft: 1 },
    1:  { ArrowUp: 2, ArrowRight: 0, ArrowLeft: 4 },
    2:  { ArrowUp: 3, ArrowDown: 1, ArrowLeft: 5 },
    3:  { ArrowDown: 2, ArrowRight: 8, ArrowLeft: 4 },
    4:  { ArrowUp: 5, ArrowRight: 3, ArrowDown: 1 },
    5:  { ArrowUp: 6, ArrowRight: 4, ArrowDown: 2 },
    6:  { ArrowUp: 7, ArrowRight: 5, ArrowDown: 9 },
    7:  { ArrowRight: 6, ArrowDown: 8, ArrowLeft: 10 },
    8:  { ArrowUp: 7, ArrowDown: 9, ArrowLeft: 3 },
    9:  { ArrowUp: 8, ArrowDown: 10, ArrowLeft: 2 },
    10: { ArrowUp: 9, ArrowRight: 11, ArrowLeft: 7 },
    11: { ArrowUp: 8, ArrowRight: 10, ArrowLeft: 0 },
  }
  
  if (navMap[idx] && navMap[idx][e.key]) {
    newIdx = navMap[idx][e.key]
    e.preventDefault()
  }
  
  if (newIdx !== idx) {
    const newPalace = result.value.palaces.find(p => p.index === newIdx)
    if (newPalace) {
      selectedPalace.value = newPalace
    }
  }
}

// 注册键盘事件
onMounted(() => {
  window.addEventListener('keydown', handleKeyNavigation)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyNavigation)
})

// ══════════════════════════════════════════════════════════════════
// 星曜关注/收藏功能
// ══════════════════════════════════════════════════════════════════
const STARRED_STARS_KEY = 'ziwei_starred_stars'
const starredStars = ref<Set<string>>(new Set(JSON.parse(localStorage.getItem(STARRED_STARS_KEY) || '[]')))

function toggleStarStar(starName: string) {
  if (starredStars.value.has(starName)) {
    starredStars.value.delete(starName)
  } else {
    starredStars.value.add(starName)
  }
  localStorage.setItem(STARRED_STARS_KEY, JSON.stringify([...starredStars.value]))
}

function isStarStarred(starName: string): boolean {
  return starredStars.value.has(starName)
}

// 获取已关注星曜在命盘中的分布
const starredStarsDistribution = computed(() => {
  if (!result.value?.palaces || starredStars.value.size === 0) return []
  
  const distribution: Array<{ star: string; palaces: string[] }> = []
  
  starredStars.value.forEach(starName => {
    const palaces: string[] = []
    result.value!.palaces.forEach(p => {
      const inMain = p.main_stars?.some(s => s.name === starName)
      const inAux = getAuxStars(p).some(s => getStarName(s) === starName)
      if (inMain || inAux) {
        palaces.push(p.name.replace('宫', ''))
      }
    })
    if (palaces.length > 0) {
      distribution.push({ star: starName, palaces })
    }
  })
  
  return distribution
})

// ══════════════════════════════════════════════════════════════════
// 命盘统计汇总卡片
// ══════════════════════════════════════════════════════════════════
const chartSummaryStats = computed(() => {
  if (!result.value?.palaces) return null
  
  let totalMainStars = 0
  let totalAuxStars = 0
  let totalTransforms = 0
  let luCount = 0
  let quanCount = 0
  let keCount = 0
  let jiCount = 0
  let brightStars = 0   // 庙旺
  let weakStars = 0     // 陷落
  
  result.value.palaces.forEach(p => {
    const mainStars = p.main_stars || []
    const auxStars = p.aux_stars || []
    
    totalMainStars += mainStars.length
    totalAuxStars += auxStars.length
    
    mainStars.forEach(s => {
      if (getStarBrightnessValue(s) >= 3) brightStars++
      if (getStarBrightnessValue(s) <= 1) weakStars++
      
      getStarTransforms(s).forEach((t) => {
        totalTransforms++
        if (t.includes('禄')) luCount++
        if (t.includes('权')) quanCount++
        if (t.includes('科')) keCount++
        if (t.includes('忌')) jiCount++
      })
    })
    
    getAuxStars(p).forEach(s => {
      getStarTransforms(s).forEach((t) => {
        totalTransforms++
        if (t.includes('禄')) luCount++
        if (t.includes('权')) quanCount++
        if (t.includes('科')) keCount++
        if (t.includes('忌')) jiCount++
      })
    })
  })
  
  // 六煞星统计
  const SHA_STARS = ['擎羊', '陀罗', '火星', '铃星', '地空', '地劫']
  let shaCount = 0
  result.value.palaces.forEach(p => {
    const allStars = [...(p.main_stars || []), ...getAuxStars(p)]
    allStars.forEach(s => {
      if (SHA_STARS.includes(getStarName(s))) shaCount++
    })
  })
  
  // 吉星统计
  const JI_STARS = ['天魁', '天钺', '左辅', '右弼', '文昌', '文曲']
  let jiStarCount = 0
  result.value.palaces.forEach(p => {
    const allStars = [...(p.main_stars || []), ...getAuxStars(p)]
    allStars.forEach(s => {
      if (JI_STARS.includes(getStarName(s))) jiStarCount++
    })
  })
  
  return {
    totalMainStars,
    totalAuxStars,
    totalTransforms,
    luCount,
    quanCount,
    keCount,
    jiCount,
    brightStars,
    weakStars,
    shaCount,
    jiStarCount,
    patternsCount: result.value.patterns?.length || 0,
  }
})
</script>

<template>
  <div class="wrap ziwei-view">
    <h1 class="page-title">紫微斗数</h1>

    <!-- 表单折叠控制栏 -->
    <div class="form-toggle-bar">
      <button class="btn-toggle-form" @click="showForm = !showForm">
        {{ showForm ? '▴ 收起参数' : '▾ 修改参数' }}
      </button>
      <span v-if="!showForm && result" class="current-params">
        {{ year }}/{{ String(month).padStart(2,'0') }}/{{ String(day).padStart(2,'0') }} {{ String(hour).padStart(2,'0') }}:{{ String(minute).padStart(2,'0') }} · {{ gender }}
      </span>
    </div>

    <!-- 输入表单 -->
    <section v-show="showForm" class="card form-card">
      <div class="form-grid">
        <div class="form-row">
          <label>出生年</label>
          <input type="number" v-model.number="year" min="1900" max="2100" style="width:90px" />
          <label style="width:auto">月</label>
          <input type="number" v-model.number="month" min="1" max="12" style="width:60px" />
          <label style="width:auto">日</label>
          <input type="number" v-model.number="day" min="1" max="31" style="width:60px" />
          <label style="width:auto">时</label>
          <input type="number" v-model.number="hour" min="0" max="23" style="width:60px" />
          <label style="width:auto">分</label>
          <input type="number" v-model.number="minute" min="0" max="59" style="width:60px" />
        </div>
        <div class="form-row">
          <label>性别</label>
          <label class="radio-opt"><input type="radio" v-model="gender" value="女" />女</label>
          <label class="radio-opt"><input type="radio" v-model="gender" value="男" />男</label>
        </div>
        <div class="form-row">
          <label>流年</label>
          <input type="number" v-model.number="liunianYear" placeholder="今年" style="width:90px" />
        </div>
        <div class="form-row">
          <CityPicker v-model="longitude" :optional="true" :initial-city="initCity" />
        </div>
      </div>

      <!-- 算法设置折叠区 -->
      <div class="algo-toggle-row">
        <button type="button" class="btn-algo-toggle" @click="showAlgoSettings = !showAlgoSettings">
          ⚙ 安星设置 {{ showAlgoSettings ? '▴' : '▾' }}
        </button>
        <span v-if="!algoLateZishi || algoLeapMethod !== 'mid' || algoKuiyue !== 'standard'
                    || sihuaJia || sihuaWu || sihuaGeng || sihuaXin || sihuaRen || sihuaGui
                    || algoTianma !== 'year' || algoTiankong !== 'standard' || algoBrightness !== 'standard'
                    || algoJiukong !== 'dual' || algoTianshang !== 'standard' || algoMingzhu !== 'quanshu'
                    || algoLiunianSihua !== 'year_stem' || algoChangsheng !== 'standard'"
              class="algo-custom-badge">已自定义</span>
        <button v-if="showAlgoSettings" type="button" class="btn-sec btn-tiny" @click="resetAlgoSettings">恢复默认</button>
      </div>

      <div v-show="showAlgoSettings" class="algo-panel">
        <!-- C-6: 预设方案快速选择 -->
        <div class="algo-presets">
          <span class="preset-label">快速预设：</span>
          <button type="button" class="preset-btn" @click="applyPreset('sanhe')" title="三合派（传统默认）">三合派</button>
          <button type="button" class="preset-btn" @click="applyPreset('feixing')" title="飞星派设置">飞星派</button>
          <button type="button" class="preset-btn" @click="applyPreset('qintian')" title="钦天门设置">钦天门</button>
          <button type="button" class="preset-btn" @click="applyPreset('zhongzhou')" title="中州派设置">中州派</button>
        </div>
        <div class="algo-divider"></div>

        <!-- 晚子时 -->
        <div class="algo-group">
          <span class="algo-label">晚子时(23:00~00:00)</span>
          <label class="radio-opt"><input type="radio" v-model="algoLateZishi" :value="true"  />视为次日（默认）</label>
          <label class="radio-opt"><input type="radio" v-model="algoLateZishi" :value="false" />视为当日</label>
        </div>
        <!-- 闰月处理 -->
        <div class="algo-group">
          <span class="algo-label">闰月本命盘</span>
          <label class="radio-opt"><input type="radio" v-model="algoLeapMethod" value="mid"  />月中分界（默认）</label>
          <label class="radio-opt"><input type="radio" v-model="algoLeapMethod" value="next" />视为下月</label>
          <label class="radio-opt"><input type="radio" v-model="algoLeapMethod" value="same" />视为本月</label>
        </div>
        <!-- 安魁钺 -->
        <div class="algo-group">
          <span class="algo-label">安天魁天钺</span>
          <label class="radio-opt"><input type="radio" v-model="algoKuiyue" value="standard"      />六辛逢虎马（默认）</label>
          <label class="radio-opt"><input type="radio" v-model="algoKuiyue" value="gengxin_mahu"  />庚辛逢马虎</label>
          <label class="radio-opt"><input type="radio" v-model="algoKuiyue" value="gengxin_huima" />庚辛逢虎马</label>
          <label class="radio-opt"><input type="radio" v-model="algoKuiyue" value="liuxin_mahu"   />六辛逢马虎</label>
        </div>
        <!-- 四化表 -->
        <div class="algo-group sihua-group">
          <span class="algo-label">四化表选项</span>
          <div class="sihua-rows">
            <div class="sihua-row">
              <span class="sihua-stem">甲</span>
              <label class="radio-opt"><input type="radio" v-model="sihuaJia" :value="0" />廉破武阳（默认）</label>
              <label class="radio-opt"><input type="radio" v-model="sihuaJia" :value="1" />廉破曲阳</label>
            </div>
            <div class="sihua-row">
              <span class="sihua-stem">戊</span>
              <label class="radio-opt"><input type="radio" v-model="sihuaWu" :value="0" />贪阴右机（默认）</label>
              <label class="radio-opt"><input type="radio" v-model="sihuaWu" :value="1" />贪阴阳机</label>
            </div>
            <div class="sihua-row">
              <span class="sihua-stem">庚</span>
              <label class="radio-opt"><input type="radio" v-model="sihuaGeng" :value="0" />阳武阴同（默认）</label>
              <label class="radio-opt"><input type="radio" v-model="sihuaGeng" :value="1" />阳武同阴</label>
              <label class="radio-opt"><input type="radio" v-model="sihuaGeng" :value="2" />阳武府同</label>
              <label class="radio-opt"><input type="radio" v-model="sihuaGeng" :value="3" />阳武府相</label>
              <label class="radio-opt"><input type="radio" v-model="sihuaGeng" :value="4" />阳武同相</label>
            </div>
            <div class="sihua-row">
              <span class="sihua-stem">辛</span>
              <label class="radio-opt"><input type="radio" v-model="sihuaXin" :value="0" />巨阳曲昌（默认）</label>
              <label class="radio-opt"><input type="radio" v-model="sihuaXin" :value="1" />巨阳武昌</label>
            </div>
            <div class="sihua-row">
              <span class="sihua-stem">壬</span>
              <label class="radio-opt"><input type="radio" v-model="sihuaRen" :value="0" />梁紫辅武（默认）</label>
              <label class="radio-opt"><input type="radio" v-model="sihuaRen" :value="1" />梁紫府武</label>
              <label class="radio-opt"><input type="radio" v-model="sihuaRen" :value="2" />梁紫相武</label>
            </div>
            <div class="sihua-row">
              <span class="sihua-stem">癸</span>
              <label class="radio-opt"><input type="radio" v-model="sihuaGui" :value="0" />破巨阴贪（默认）</label>
              <label class="radio-opt"><input type="radio" v-model="sihuaGui" :value="1" />破巨阳贪</label>
            </div>
          </div>
        </div>
        <!-- A1: 安天马 -->
        <div class="algo-group">
          <span class="algo-label">安天马</span>
          <label class="radio-opt"><input type="radio" v-model="algoTianma" value="year"  />依据年支（默认）</label>
          <label class="radio-opt"><input type="radio" v-model="algoTianma" value="month" />依据月支</label>
        </div>
        <!-- A2: 安天空 -->
        <div class="algo-group">
          <span class="algo-label">安天空</span>
          <label class="radio-opt"><input type="radio" v-model="algoTiankong" value="standard" />常规排法（默认）</label>
          <label class="radio-opt"><input type="radio" v-model="algoTiankong" value="shun"     />顺加生时</label>
        </div>
        <!-- A3: 星曜亮度 -->
        <div class="algo-group">
          <span class="algo-label">星曜亮度</span>
          <label class="radio-opt"><input type="radio" v-model="algoBrightness" value="standard"  />依据斗数全书（默认）</label>
          <label class="radio-opt"><input type="radio" v-model="algoBrightness" value="zhongzhou" />依据中州派理论</label>
          <label class="radio-opt"><input type="radio" v-model="algoBrightness" value="mod1"      />现代修订亮度一</label>
          <label class="radio-opt"><input type="radio" v-model="algoBrightness" value="mod2"      />现代修订亮度二</label>
        </div>
        <!-- A4: 安截空旬空 -->
        <div class="algo-group">
          <span class="algo-label">安截空旬空</span>
          <label class="radio-opt"><input type="radio" v-model="algoJiukong" value="dual"    />正副双星法（默认）</label>
          <label class="radio-opt"><input type="radio" v-model="algoJiukong" value="single"  />常规单星法</label>
          <label class="radio-opt"><input type="radio" v-model="algoJiukong" value="zhanyan" />占验派排法</label>
        </div>
        <!-- A5: 安天使天伤 -->
        <div class="algo-group">
          <span class="algo-label">安天使天伤</span>
          <label class="radio-opt"><input type="radio" v-model="algoTianshang" value="standard"  />常规排法（默认）</label>
          <label class="radio-opt"><input type="radio" v-model="algoTianshang" value="zhongzhou" />中州派排法</label>
        </div>
        <!-- A6: 安命主 -->
        <div class="algo-group">
          <span class="algo-label">安命主</span>
          <label class="radio-opt"><input type="radio" v-model="algoMingzhu" value="quanshu"  />依据斗数全书（默认）</label>
          <label class="radio-opt"><input type="radio" v-model="algoMingzhu" value="zhongzhou"/>依据中州派理论</label>
        </div>
        <!-- A7: 流年四化 -->
        <div class="algo-group">
          <span class="algo-label">流年四化</span>
          <label class="radio-opt"><input type="radio" v-model="algoLiunianSihua" value="year_stem"        />依据流年天干（默认）</label>
          <label class="radio-opt"><input type="radio" v-model="algoLiunianSihua" value="life_palace_stem" />依据流年命宫天干</label>
        </div>
        <!-- A8: 安长生十二神 -->
        <div class="algo-group">
          <span class="algo-label">安长生十二神</span>
          <label class="radio-opt"><input type="radio" v-model="algoChangsheng" value="standard"    />区分阴阳顺逆（默认）</label>
          <label class="radio-opt"><input type="radio" v-model="algoChangsheng" value="water_earth" />水土共长生</label>
          <label class="radio-opt"><input type="radio" v-model="algoChangsheng" value="fire_earth"  />火土共长生</label>
        </div>
      </div>

      <div class="form-actions">
        <button class="btn-primary" :disabled="loading" @click="doCalculate">
          {{ loading ? '排盘中…' : '排　盘' }}
        </button>
        <button class="btn-sec" :disabled="loading" @click="doDemo">演示盘</button>
        <button class="btn-sec" @click="resetForm">重置</button>
        <span v-if="error" class="error-msg">{{ error }}</span>
      </div>
    </section>

    <!-- 骨架屏 -->
    <div v-if="loading" class="skeleton-wrap">
      <div class="skel-line" style="width:50%"></div>
      <div class="skel-box" style="height:200px"></div>
    </div>

    <!-- 结果区 -->
    <template v-if="result">
      <!-- 基本信息栏 -->
      <div class="info-bar card">
        <span class="info-item">
          <b>{{ result.birth_solar }}</b> · {{ result.gender }}
        </span>
        <span class="info-item">
          农历 {{ result.lunar.lunar_year }}年
          {{ result.lunar.is_leap_month ? '闰' : '' }}{{ result.lunar.lunar_month }}月{{ result.lunar.lunar_day }}日
        </span>
        <span class="info-item">
          命宫：<b>{{ result.life_palace_gz }}</b>
          &nbsp;身宫：<b>{{ result.body_palace_gz }}</b>
        </span>
        <span class="info-item">
          <span class="ju-badge" :style="{ background: JU_COLORS[result.wuxing_ju] }">
            {{ result.wuxing_ju_name }}
          </span>
        </span>
        <span v-if="result.life_ruler_star" class="info-item">
          命主：<b>{{ result.life_ruler_star }}</b>
        </span>
        <span v-if="result.body_ruler_star" class="info-item">
          身主：<b>{{ result.body_ruler_star }}</b>
        </span>
        <span v-if="result.true_solar_time" class="info-item">
          真太阳时：<b>{{ result.true_solar_time }}</b>
        </span>

        <div v-if="isOverlayFeedbackVisible('chart')" :class="['panel-feedback', overlayFeedback!.type, 'no-print']">{{ overlayFeedback!.message }}</div>

        <!-- 主操作 -->
        <button class="btn-export btn-export-main no-print" @click="exportPDF">⬇ 导出 PDF</button>
        <button class="btn-export no-print" :disabled="isExportingImage" @click="exportChartAsImage">
          {{ isExportingImage ? 'PNG 导出中…' : '🖼 导出 PNG' }}
        </button>
        <button class="btn-zeri no-print" @click="gotoZeri">📅 择日</button>
        <button class="btn-ai no-print" :disabled="!result" @click="gotoAi">🤖 AI 解读</button>
        <button class="btn-save-case no-print" :disabled="!canSaveCurrentChart" @click="saveCurrentChart()">
          {{ isSavingCase ? '保存中…' : savedCaseId ? '✅ 已保存' : '💾 保存命盘' }}
        </button>

        <details class="ziwei-action-menu no-print">
          <summary class="btn-cases">📚 案例工作流</summary>
          <div class="ziwei-menu-panel">
            <button class="ziwei-menu-item" @click="toggleCasesPanel">📚 打开案例库</button>
            <button class="ziwei-menu-item" :disabled="!savedCaseId" @click="toggleSnapshotsPanel">📸 查看快照</button>
            <button class="ziwei-menu-item" :disabled="!result" @click="toggleSimilarPanel">🧭 相似盘分析</button>
          </div>
        </details>

        <details class="ziwei-action-menu no-print">
          <summary class="btn-review">🧾 协同治理</summary>
          <div class="ziwei-menu-panel">
            <button class="ziwei-menu-item" :disabled="!result" @click="toggleReviewPanel">🧾 审核面板</button>
            <button class="ziwei-menu-item" :disabled="!result" @click="toggleLlmPanel">✍ AI 草稿</button>
            <button class="ziwei-menu-item" :disabled="!result" @click="toggleOpsPanel">📊 运营看板</button>
            <button class="ziwei-menu-item" @click="toggleBatchPanel">📦 批量处理</button>
            <button class="ziwei-menu-item" @click="toggleGlossaryPanel">📖 词汇面板</button>
            <button class="ziwei-menu-item" :disabled="!result" @click="toggleMultiCompatPanel">👥 多人合盘</button>
            <button class="ziwei-menu-item" @click="toggleFengshuiPanel">🧭 风水助手</button>
          </div>
        </details>

        <details class="ziwei-action-menu no-print">
          <summary class="btn-tool-summary">🛠 工具</summary>
          <div class="ziwei-menu-panel ziwei-menu-panel-tools">
            <button class="ziwei-menu-item" @click="showStarSearch = true">🔍 搜索星曜</button>
            <button class="ziwei-menu-item" @click="showBrightnessLegend = !showBrightnessLegend">💡 亮度图例</button>
            <button class="ziwei-menu-item" @click="showHotkeyPanel = !showHotkeyPanel">⌨ 快捷键面板</button>
            <button class="ziwei-menu-item" @click="showHistoryPanel = !showHistoryPanel; chartHistory = loadHistory()">
              <span>📋 历史记录</span>
              <span v-if="chartHistory.length" class="history-badge">{{ chartHistory.length }}</span>
            </button>
          </div>
        </details>
      </div>

      <!-- ═══════════════════════════════════════════════════════════════════
           快捷键帮助面板
           ═══════════════════════════════════════════════════════════════════ -->
      <transition name="fade">
        <div v-if="showHotkeyPanel" class="hotkey-panel card no-print">
          <div class="hp-header">
            <span class="hp-title">⌨ 键盘快捷键</span>
            <button class="hp-close" @click="showHotkeyPanel = false">✕</button>
          </div>
          <div class="hp-list">
            <div v-for="hk in HOTKEY_LIST" :key="hk.key" class="hp-item">
              <kbd class="hp-key">{{ hk.key }}</kbd>
              <span class="hp-desc">{{ hk.desc }}</span>
            </div>
            <div class="hp-item">
              <kbd class="hp-key">S</kbd>
              <span class="hp-desc">打开星曜搜索</span>
            </div>
          </div>
        </div>
      </transition>

      <!-- ═══════════════════════════════════════════════════════════════════
           星曜亮度图例面板
           ═══════════════════════════════════════════════════════════════════ -->
      <transition name="fade">
        <div v-if="showBrightnessLegend" class="brightness-legend card no-print">
          <div class="bl-header">
            <span class="bl-title">💡 星曜亮度图例</span>
            <button class="bl-close" @click="showBrightnessLegend = false">✕</button>
          </div>
          <div class="bl-list">
            <div v-for="b in BRIGHTNESS_LEGEND" :key="b.level" class="bl-item">
              <span class="bl-level" :style="{ background: b.color }">{{ b.level }}</span>
              <span class="bl-desc">{{ b.desc }}</span>
            </div>
          </div>
          <div class="bl-note">
            <small>亮度越高，星曜吉性越易发挥；陷落时则力量受损</small>
          </div>
        </div>
      </transition>

      <!-- ═══════════════════════════════════════════════════════════════════
           星曜搜索弹窗
           ═══════════════════════════════════════════════════════════════════ -->
      <transition name="fade">
        <div v-if="showStarSearch" class="star-search-modal no-print" @click.self="showStarSearch = false">
          <div class="star-search-box card">
            <div class="ss-header">
              <span class="ss-title">🔍 全盘星曜搜索</span>
              <button class="ss-close" @click="showStarSearch = false">✕</button>
            </div>
            <input v-model="starSearchQuery" 
                   type="text" 
                   class="star-search-input" 
                   placeholder="输入星曜名称，如：紫微、天机、禄存..."
                   @keydown.esc="showStarSearch = false" />
            <div class="ss-results">
              <div v-if="starSearchQuery && starSearchResults.length === 0" class="ss-empty">
                未找到匹配的星曜
              </div>
              <div v-for="s in starSearchResults" :key="`${s.name}-${s.palaceIdx}`" 
                   class="ss-item" @click="selectSearchResult(s.palaceIdx)">
                <span :class="['ss-star', s.type === 'main' ? 'ss-main' : 'ss-aux']">{{ s.name }}</span>
                <span v-if="s.brightness" class="ss-brightness">{{ s.brightness }}</span>
                <span v-if="s.transforms?.length" class="ss-transforms">
                  {{ s.transforms.join(' ') }}
                </span>
                <span class="ss-palace">{{ s.palace }}</span>
              </div>
            </div>
            <div class="ss-hint">
              <small>点击结果可跳转至对应宫位</small>
            </div>
          </div>
        </div>
      </transition>

      <!-- ═══════════════════════════════════════════════════════════════════
           命盘历史记录面板
           ═══════════════════════════════════════════════════════════════════ -->
      <transition name="fade">
        <div v-if="showHistoryPanel" class="history-panel card no-print">
          <div class="hist-header">
            <span class="hist-title">📋 排盘历史</span>
            <div class="hist-actions">
              <button v-if="chartHistory.length" class="hist-clear" @click="clearHistory" title="清空历史">🗑</button>
              <button class="hist-close" @click="showHistoryPanel = false">✕</button>
            </div>
          </div>
          <div v-if="chartHistory.length === 0" class="hist-empty">
            暂无历史记录
          </div>
          <div v-else class="hist-list">
            <div v-for="item in chartHistory" :key="item.id" class="hist-item" @click="restoreFromHistory(item)">
              <div class="hist-main">
                <span class="hist-birth">{{ item.birthSolar }}</span>
                <span class="hist-gender">{{ item.gender }}</span>
              </div>
              <div class="hist-sub">
                <span class="hist-palace">命宫 {{ item.lifePalaceGz }}</span>
                <span class="hist-ju">{{ item.wuxingJuName }}</span>
              </div>
              <div class="hist-time">{{ formatHistoryTime(item.timestamp) }}</div>
            </div>
          </div>
        </div>
      </transition>

      <!-- ═══════════════════════════════════════════════════════════════════
           星曜详情提示气泡
           ═══════════════════════════════════════════════════════════════════ -->
      <transition name="fade">
        <div v-if="hoveredStar && STAR_INFO[hoveredStar]" 
             class="star-tooltip no-print"
             :style="{ left: starTooltipPos.x + 'px', top: starTooltipPos.y + 'px' }">
          <div class="st-name">{{ hoveredStar }}</div>
          <div class="st-nature">性质：{{ STAR_INFO[hoveredStar].nature }}</div>
          <div class="st-meaning">{{ STAR_INFO[hoveredStar].meaning }}</div>
        </div>
      </transition>

      <!-- 概述 -->
      <p v-if="result.summary" class="summary-block">{{ result.summary }}</p>

      <!-- Tab 导航 -->
      <div class="tabs">
        <button :class="['tab-btn', { active: activeTab === 'chart' }]"
                @click="activeTab = 'chart'">命盘宫位</button>
        <button :class="['tab-btn', { active: activeTab === 'summary' }]"
                @click="activeTab = 'summary'">摘要</button>
        <button :class="['tab-btn', { active: activeTab === 'palaces' }]"
                @click="activeTab = 'palaces'">逐宫解读</button>
        <button :class="['tab-btn', { active: activeTab === 'dayun' }]"
                @click="activeTab = 'dayun'">大运</button>
        <button v-if="result.liunian" :class="['tab-btn', { active: activeTab === 'liunian' }]"
                @click="activeTab = 'liunian'">流年</button>
        <button v-if="result.liuyue?.length" :class="['tab-btn', { active: activeTab === 'liuyue' }]"
                @click="activeTab = 'liuyue'">流月</button>
        <button :class="['tab-btn', { active: activeTab === 'patterns' }]"
                @click="activeTab = 'patterns'">
          格局
          <span v-if="result.patterns?.length" class="badge">{{ result.patterns.length }}</span>
        </button>
        <button v-if="result.flying" :class="['tab-btn', { active: activeTab === 'flying' }]"
                @click="activeTab = 'flying'">飞星</button>
        <button v-if="result.forecast" :class="['tab-btn', { active: activeTab === 'forecast' }]"
                @click="activeTab = 'forecast'">运势</button>
        <button :class="['tab-btn', { active: activeTab === 'suggest' }]"
                @click="activeTab = 'suggest'">建议</button>
      </div>

      <!-- Tab: 命盘宫位 -->
      <section v-if="activeTab === 'chart'" class="tab-panel chart-tab-panel">

        <!-- ═══════════════════════════════════════════════════════════════════
             C-1: 盘面类型切换按钮组（飞星 / 三合 / 四化）
             ═══════════════════════════════════════════════════════════════════ -->
        <div class="chart-mode-bar">
          <div class="mode-btns">
            <button :class="['mode-btn', { active: chartMode === 'feixing' }]"
                    @click="chartMode = 'feixing'">飞星</button>
            <button :class="['mode-btn', { active: chartMode === 'sanhe' }]"
                    @click="chartMode = 'sanhe'">三合</button>
            <button :class="['mode-btn', { active: chartMode === 'sihua' }]"
                    @click="chartMode = 'sihua'">四化</button>
          </div>
          <!-- C-3: 四化连线开关（仅四化盘显示） -->
          <label v-if="chartMode === 'sihua'" class="sihua-line-toggle">
            <input type="checkbox" v-model="showSihuaLines" />
            显示飞星连线
          </label>
          <!-- C-7: 流年叠加开关 -->
          <label class="liunian-overlay-toggle">
            <input type="checkbox" v-model="showLiunianOverlay" />
            叠加流年
          </label>
          <!-- 流月选择器 -->
          <div v-if="result?.liuyue?.length" class="liuyue-selector">
            <label>流月：</label>
            <select v-model.number="selectedLiuyueMonth" class="liuyue-select">
              <option :value="0">不显示</option>
              <option v-for="m in result.liuyue" :key="m.month" :value="m.month">
                {{ m.month_name }} ({{ m.month_gz }})
              </option>
            </select>
          </div>
          <!-- C-4: 星曜显示控制 -->
          <div class="star-display-opts">
            <label><input type="checkbox" v-model="starDisplayOpts.showMainStars" />主星</label>
            <label><input type="checkbox" v-model="starDisplayOpts.showAuxStars" />辅星</label>
            <label><input type="checkbox" v-model="starDisplayOpts.showTransforms" />四化</label>
            <label><input type="checkbox" v-model="starDisplayOpts.showBrightness" />亮度</label>
            <label><input type="checkbox" v-model="starDisplayOpts.showChangsheng" />长生</label>
            <label><input type="checkbox" v-model="starDisplayOpts.showBoshi" />博士</label>
            <label><input type="checkbox" v-model="starDisplayOpts.showJiangSui" />将岁</label>
          </div>
          <!-- 叠加层显示控制 -->
          <div class="overlay-display-opts">
            <span class="overlay-label">叠加：</span>
            <label><input type="checkbox" v-model="overlayOpts.showDaxian" />大限</label>
            <label><input type="checkbox" v-model="overlayOpts.showLiunian" />流年</label>
            <label><input type="checkbox" v-model="overlayOpts.showLiuyue" />流月</label>
            <label><input type="checkbox" v-model="overlayOpts.showXiaoxian" />小限</label>
          </div>
          <!-- 主题与字体控制 -->
          <div class="visual-settings">
            <button class="vs-btn" @click="showThemePanel = !showThemePanel" title="切换配色主题">
              🎨
            </button>
            <div class="font-size-btns">
              <button v-for="opt in FONT_SIZE_OPTIONS" :key="opt.id"
                      :class="['fs-btn', { active: fontSizeLevel === opt.id }]"
                      @click="setFontSize(opt.id)" :title="`字体${opt.label}`">
                {{ opt.label }}
              </button>
            </div>
          </div>
        </div>

        <!-- 主题选择面板 -->
        <div v-if="showThemePanel" class="theme-panel">
          <div class="tp-header">
            <span>选择配色主题</span>
            <button class="tp-close" @click="showThemePanel = false">✕</button>
          </div>
          <div class="tp-grid">
            <button v-for="t in CHART_THEMES" :key="t.id"
                    :class="['tp-item', { active: chartTheme === t.id }]"
                    @click="setChartTheme(t.id)">
              <div class="tp-preview">
                <span class="tp-dot" :style="{ background: t.colors.primary }"></span>
                <span class="tp-bg" :style="{ background: t.colors.bg }"></span>
              </div>
              <div class="tp-name">{{ t.name }}</div>
              <div class="tp-desc">{{ t.desc }}</div>
            </button>
          </div>
        </div>

        <!-- 当前大运提示 -->
        <div v-if="currentDayun" class="cur-dayun-tip">
          当前大运：<b>{{ currentDayun.ganzhi }}</b>（{{ currentDayun.start_age }}~{{ currentDayun.end_age }}岁，{{ currentDayun.start_year }}年起）
          <span v-if="Object.keys(currentDayun.sihua).length">
            ·
            <span v-for="(val, star) in currentDayun.sihua" :key="star"
                  class="sihua-badge">{{ star }}{{ val }}</span>
          </span>
        </div>

        <!-- 命盘快速洞察栏 -->
        <div v-if="chartQuickInsights.length" class="chart-quick-insights">
          <div v-for="item in chartQuickInsights" :key="item.label"
               :class="['cqi-item', item.cls]">
            <span class="cqi-label">{{ item.label }}</span>
            <span class="cqi-value">{{ item.value }}</span>
            <span v-if="item.sub" class="cqi-sub">{{ item.sub }}</span>
          </div>
        </div>

        <!-- 宫位快捷导航面板 -->
        <div class="palace-quick-nav-panel">
          <div class="pqnp-row">
            <button v-for="p in result.palaces" :key="p.index"
                    :class="['pqnp-btn', { 
                      'pqnp-selected': selectedPalace?.index === p.index,
                      'pqnp-life': p.name.includes('命'),
                      'pqnp-body': p.name.includes('身'),
                      'pqnp-has-lu': palaceHasTransform(p, '禄'),
                      'pqnp-has-ji': palaceHasTransform(p, '忌')
                    }]"
                    @click="selectPalace(p)"
                    :title="getPalaceQuickInfo(p)">
              <span class="pqnp-name">{{ p.name.replace('宫', '') }}</span>
              <span class="pqnp-count">{{ (p.main_stars?.length || 0) + (p.aux_stars?.length || 0) }}</span>
            </button>
          </div>
        </div>

        <!-- 传统命盘网格（带方位标注） -->
        <div class="palace-grid-wrap">
          <!-- 方位标注行 -->
          <div class="grid-compass">
            <div class="compass-cell compass-nw"></div>
            <div class="compass-cell compass-n">南</div>
            <div class="compass-cell compass-ne"></div>
          </div>
          <div class="grid-body">
            <div class="compass-side compass-w">东</div>
            <div class="palace-grid-pro">
              <template v-for="cell in palaceGrid" :key="cell.pos">
                <!-- 中宫：显示命盘基本信息（C-5增强） -->
                <div v-if="cell.empty" class="pc-center">
                  <div class="pc-center-inner">
                    <!-- 五行局 + 性别 -->
                    <div class="pc-center-top">
                      <span class="pc-cj" :style="{ color: JU_COLORS[result!.wuxing_ju] }">{{ result!.wuxing_ju_name }}</span>
                      <span class="pc-cg-badge">{{ result!.gender }}</span>
                    </div>

                    <!-- 四柱信息（年/月/时） -->
                    <div class="pc-sizhu">
                      <span class="pc-sz-item" title="年柱">{{ result!.lunar.year_gz }}</span>
                      <span class="pc-sz-item" title="节气月柱">{{ result!.lunar.jieqi_month_gz || result!.lunar.month_gz }}</span>
                      <span class="pc-sz-item" title="日柱">{{ result!.lunar.day_gz }}</span>
                      <span class="pc-sz-item pc-sz-hour" title="时柱">{{ result!.lunar.hour_gz || result!.lunar.hour_branch + '时' }}</span>
                    </div>
                    <!-- 非节气四柱（若节气月柱与农历月柱不同则显示第二行） -->
                    <div v-if="result!.lunar.jieqi_month_gz && result!.lunar.jieqi_month_gz !== result!.lunar.month_gz" class="pc-sizhu pc-sizhu-alt">
                      <span class="pc-sz-item pc-sz-alt" title="年柱">{{ result!.lunar.year_gz }}</span>
                      <span class="pc-sz-item pc-sz-alt" title="农历月柱">{{ result!.lunar.month_gz }}</span>
                      <span class="pc-sz-item pc-sz-alt" title="日柱">{{ result!.lunar.day_gz }}</span>
                      <span class="pc-sz-item pc-sz-alt pc-sz-hour" title="时柱">{{ result!.lunar.hour_gz || result!.lunar.hour_branch + '时' }}</span>
                    </div>

                    <div class="pc-divider"></div>

                    <!-- 生日信息 -->
                    <div class="pc-birth-info">
                      <div class="pc-cb">{{ result!.birth_solar }}</div>
                      <div class="pc-cl">农历{{ result!.lunar.lunar_year }}年{{ result!.lunar.is_leap_month ? '闰' : '' }}{{ result!.lunar.lunar_month }}月{{ result!.lunar.lunar_day }}日</div>
                      <div v-if="result!.true_solar_time" class="pc-ct">真太阳时 {{ result!.true_solar_time }}</div>
                    </div>

                    <div class="pc-divider"></div>

                    <!-- 命主/身主 -->
                    <div class="pc-rulers">
                      <span v-if="result!.life_ruler_star" class="pc-cr-tag pc-cr-life">命·{{ result!.life_ruler_star }}</span>
                      <span v-if="result!.body_ruler_star" class="pc-cr-tag pc-cr-body">身·{{ result!.body_ruler_star }}</span>
                    </div>

                    <!-- 起运信息 -->
                    <div v-if="result!.dayun" class="pc-dayun-info">
                      <span class="pc-dayun-dir">{{ result!.dayun.forward ? '顺行' : '逆行' }}</span>
                      <span class="pc-dayun-age">{{ result!.dayun.start_age_text || `${result!.dayun.start_age}岁起运` }}</span>
                    </div>

                    <!-- 大运年龄行 + 起运年份行 -->
                    <div v-if="result!.dayun?.items?.length" class="pc-dayun-strip">
                      <div class="pc-dayun-ages">
                        <span v-for="d in result!.dayun.items" :key="d.index"
                              :class="['pc-dys-age', { 'pc-dys-cur': d.start_year <= currentYear && (d.start_year + 10) > currentYear }]">
                          {{ d.start_age }}
                        </span>
                      </div>
                      <div class="pc-dayun-years">
                        <span v-for="d in result!.dayun.items" :key="d.index"
                              :class="['pc-dys-year', { 'pc-dys-cur': d.start_year <= currentYear && (d.start_year + 10) > currentYear }]">
                          {{ d.start_year }}
                        </span>
                      </div>
                    </div>

                    <!-- 操作按钮：日↑ 日↓ 天盘▽ 时↑ 时↓ -->
                    <div class="pc-ops-btns">
                      <button class="pc-op-btn" @click="shiftDay(-1)" title="前一天">日↑</button>
                      <button class="pc-op-btn" @click="shiftDay(1)" title="后一天">日↓</button>
                      <button class="pc-op-btn pc-op-tray" @click="activeTab = 'chart'" title="返回天盘">天盘▽</button>
                      <button class="pc-op-btn" @click="shiftHour(-1)" title="前一时辰">时↑</button>
                      <button class="pc-op-btn" @click="shiftHour(1)" title="后一时辰">时↓</button>
                    </div>

                    <!-- 自化图示 -->
                    <div v-if="result!.flying?.self_transforms?.length" class="pc-zihua-row">
                      <span class="pc-zihua-label">自化图示：</span>
                      <span v-for="s in result!.flying.self_transforms" :key="s"
                            :class="['pc-zihua-tag', s.includes('禄') ? 'zh-lu' : s.includes('权') ? 'zh-quan' : s.includes('科') ? 'zh-ke' : 'zh-ji']">
                        {{ s }}
                      </span>
                    </div>
                    <div v-else class="pc-zihua-row pc-zihua-hint">
                      <span class="pc-zihua-label">自化图示：</span>
                      <span class="pc-zihua-none">→禄</span>
                      <span class="pc-zihua-none">→权</span>
                      <span class="pc-zihua-none">→科</span>
                      <span class="pc-zihua-none">→忌</span>
                    </div>


                    <!-- 分享面板 -->
                    <div v-if="showSharePanel" class="share-panel">
                      <div class="sp-header">
                        <span>分享命盘</span>
                        <button class="sp-close" @click="showSharePanel = false">✕</button>
                      </div>
                      <div class="sp-content">
                        <input type="text" readonly :value="shareLink" class="sp-link-input" @click="($event.target as HTMLInputElement).select()" />
                        <button class="sp-copy-btn" @click="copyShareLink">复制链接</button>
                      </div>
                      <p class="sp-hint">他人打开链接后将自动计算相同命盘</p>
                    </div>

                    <!-- 案例库面板 -->
                    <div v-if="showCasesPanel" class="cases-panel">
                      <div class="cp-header">
                        <span>案例库</span>
                        <button class="cp-close" @click="showCasesPanel = false">✕</button>
                      </div>
                      <div class="cp-toolbar">
                        <input
                          v-model="casesKeyword"
                          type="text"
                          class="cp-search-input"
                          placeholder="搜索案例名称"
                          @keydown.enter.prevent="searchCases"
                        />
                        <button class="cp-search-btn" @click="searchCases">搜索</button>
                      </div>
                      <div class="cp-summary">
                        <span>共 {{ casesTotal }} 条</span>
                        <span v-if="savedCaseName" class="cp-current">当前：{{ savedCaseName }}</span>
                      </div>
                      <div v-if="casesLoading" class="cp-state">加载中…</div>
                      <div v-else-if="casesError" class="cp-state cp-error">{{ casesError }}</div>
                      <div v-else-if="caseList.length === 0" class="cp-state">暂无案例</div>
                      <div v-else class="cp-list">
                        <div v-for="item in caseList" :key="item.id" class="cp-item">
                          <div class="cp-item-main" @click="loadCaseChart(item)">
                            <div class="cp-name-row">
                              <span class="cp-name">{{ item.name }}</span>
                              <span v-if="savedCaseId === item.id" class="cp-badge">当前</span>
                            </div>
                            <div class="cp-meta">
                              <span>{{ item.birth_dt_local.replace('T', ' ').slice(0, 16) }}</span>
                              <span>{{ item.gender === 'female' ? '女' : item.gender === 'male' ? '男' : '—' }}</span>
                            </div>
                            <div class="cp-meta cp-meta-muted">
                              <span>{{ item.last_snapshot_at ? `最近快照 ${item.last_snapshot_at.replace('T', ' ').slice(0, 16)}` : '暂无快照' }}</span>
                            </div>
                          </div>
                          <div class="cp-actions">
                            <button class="cp-load-btn" @click="loadCaseChart(item)">载入</button>
                            <button class="cp-del-btn" @click="removeCase(item)">删除</button>
                          </div>
                        </div>
                      </div>
                      <div v-if="hasCasesPagination" class="cp-pagination">
                        <button class="cp-page-btn" :disabled="casesOffset <= 0" @click="prevCasesPage">上一页</button>
                        <span>{{ Math.floor(casesOffset / CASES_LIMIT) + 1 }} / {{ Math.max(1, Math.ceil(casesTotal / CASES_LIMIT)) }}</span>
                        <button class="cp-page-btn" :disabled="casesOffset + CASES_LIMIT >= casesTotal" @click="nextCasesPage">下一页</button>
                      </div>
                    </div>

                    <!-- 快照面板 -->
                    <div v-if="showSnapshotsPanel" class="snapshots-panel">
                      <div class="snp-header">
                        <span>快照历史</span>
                        <button class="snp-close" @click="showSnapshotsPanel = false">✕</button>
                      </div>
                      <div class="snp-summary">
                        <span v-if="savedCaseName">案例：{{ savedCaseName }}</span>
                        <span v-if="currentSnapshotId">当前快照：{{ currentSnapshotId.slice(0, 8) }}…</span>
                      </div>
                      <div v-if="snapshotsLoading" class="snp-state">加载中…</div>
                      <div v-else-if="snapshotsError" class="snp-state snp-error">{{ snapshotsError }}</div>
                      <div v-else-if="snapshots.length === 0" class="snp-state">暂无快照</div>
                      <template v-else>
                        <div class="snp-list">
                          <div v-for="snap in snapshots" :key="snap.id" class="snp-item">
                            <div class="snp-item-main">
                              <div class="snp-item-row">
                                <span class="snp-kind">{{ snap.kind }}</span>
                                <span v-if="currentSnapshotId === snap.id" class="snp-current">当前</span>
                              </div>
                              <div class="snp-meta">{{ snap.created_at.replace('T', ' ').slice(0, 16) }} · API {{ snap.api_version ?? '—' }}</div>
                              <div v-if="snap.note" class="snp-note">{{ snap.note }}</div>
                            </div>
                            <button class="snp-load-btn" @click="restoreSnapshot(snap)">载入</button>
                          </div>
                        </div>

                        <div class="snp-compare-box">
                          <div class="snp-compare-title">快照对比</div>
                          <div class="snp-compare-controls">
                            <select v-model="snapshotCompareA" class="snp-select">
                              <option value="">选择快照 A</option>
                              <option v-for="snap in snapshots" :key="`a-${snap.id}`" :value="snap.id">
                                {{ snap.created_at.replace('T', ' ').slice(0, 16) }} · {{ snap.id.slice(0, 8) }}
                              </option>
                            </select>
                            <select v-model="snapshotCompareB" class="snp-select">
                              <option value="">选择快照 B</option>
                              <option v-for="snap in snapshots" :key="`b-${snap.id}`" :value="snap.id">
                                {{ snap.created_at.replace('T', ' ').slice(0, 16) }} · {{ snap.id.slice(0, 8) }}
                              </option>
                            </select>
                            <button class="snp-compare-btn" :disabled="snapshotDiffLoading" @click="compareSnapshotsNow">
                              {{ snapshotDiffLoading ? '对比中…' : '开始对比' }}
                            </button>
                          </div>
                          <div v-if="snapshotDiffError" class="snp-diff-error">{{ snapshotDiffError }}</div>
                          <div v-else-if="snapshotDiffResult" class="snp-diff-result">
                            <div class="snp-diff-summary">共 {{ snapshotDiffResult.total_changes }} 处变更</div>
                            <div v-if="snapshotDiffResult.changed_fields.length" class="snp-diff-list">
                              <div v-for="field in snapshotDiffResult.changed_fields.slice(0, 8)" :key="field.field" class="snp-diff-item">
                                <span class="snp-diff-field">{{ field.field }}</span>
                                <span class="snp-diff-values">{{ String(field.value_a) }} → {{ String(field.value_b) }}</span>
                              </div>
                            </div>
                            <div v-if="snapshotDiffResult.added_fields.length" class="snp-diff-extra">
                              新增：{{ snapshotDiffResult.added_fields.slice(0, 5).join('、') }}
                            </div>
                            <div v-if="snapshotDiffResult.removed_fields.length" class="snp-diff-extra">
                              移除：{{ snapshotDiffResult.removed_fields.slice(0, 5).join('、') }}
                            </div>
                          </div>
                        </div>
                      </template>
                    </div>

                    <!-- 相似盘面板 -->
                    <div v-if="showSimilarPanel" class="similar-panel">
                      <div class="simp-header">
                        <span>相似盘检索</span>
                        <button class="simp-close" @click="showSimilarPanel = false">✕</button>
                      </div>
                      <div class="simp-query">{{ similarQuerySummary }}</div>
                      <div class="simp-toolbar">
                        <label class="simp-topk">
                          <span>返回数量</span>
                          <select v-model.number="similarTopK">
                            <option :value="5">5</option>
                            <option :value="10">10</option>
                            <option :value="15">15</option>
                          </select>
                        </label>
                        <button class="simp-btn" :disabled="!result || similarLoading" @click="runSimilarSearch">
                          {{ similarLoading ? '检索中…' : '开始检索' }}
                        </button>
                        <button class="simp-btn simp-btn-soft" :disabled="!result || similarLoading" @click="indexCurrentForSimilarity">
                          当前命盘入库
                        </button>
                      </div>
                      <div class="simp-status">{{ similarStatus || '—' }}</div>
                      <div v-if="similarResults.length" class="simp-badge">已索引 {{ similarTotalIndexed }} 张命盘</div>
                      <div v-if="similarResults.length === 0" class="simp-empty">
                        暂无相似结果。若当前命盘较新，可先点击“当前命盘入库”。
                      </div>
                      <div v-else class="simp-list">
                        <div v-for="item in similarResults" :key="`${item.case.id}-${item.case.chart_hash}`" class="simp-card">
                          <div :class="['simp-score', getSimilarityPercent(item.similarity) >= 80 ? 'is-high' : getSimilarityPercent(item.similarity) >= 60 ? 'is-mid' : 'is-low']">
                            {{ getSimilarityPercent(item.similarity) }}%
                          </div>
                          <div class="simp-main">
                            <div class="simp-title-row">
                              <span class="simp-title">{{ item.case.life_palace_gz }} 命宫 · {{ item.case.wuxing_ju_name }} · {{ item.case.gender }}</span>
                              <span class="simp-level">{{ getSimilarityLevel(item.similarity) }}</span>
                            </div>
                            <div class="simp-meta">
                              出生：{{ item.case.birth_year }}-{{ String(item.case.birth_month).padStart(2, '0') }}-{{ String(item.case.birth_day).padStart(2, '0') }} {{ String(item.case.birth_hour).padStart(2, '0') }}:00
                            </div>
                            <div class="simp-meta">来源：{{ item.case.source_label || '未知' }}</div>
                            <div class="simp-patterns">格局：{{ formatSimilarityPatterns(item) }}</div>
                          </div>
                        </div>
                      </div>
                    </div>

                    <!-- 审核面板 -->
                    <div v-if="showReviewPanel" class="review-panel-zw">
                      <div class="rvp-header">
                        <span>审核面板</span>
                        <button class="rvp-close" @click="showReviewPanel = false">✕</button>
                      </div>
                      <div v-if="isOverlayFeedbackVisible('review')" :class="['panel-feedback', overlayFeedback!.type]">{{ overlayFeedback!.message }}</div>
                      <div class="rvp-toolbar">
                        <div class="rvp-mode-switch">
                          <button class="rvp-mode-btn" :class="{ active: reviewListMode === 'all' }" @click="setReviewListMode('all')">全部</button>
                          <button class="rvp-mode-btn" :class="{ active: reviewListMode === 'queue' }" @click="setReviewListMode('queue')">待审队列</button>
                          <button class="rvp-mode-btn" :class="{ active: reviewListMode === 'mine' }" @click="setReviewListMode('mine')">我的队列</button>
                        </div>
                        <select v-model="reviewFilter" class="rvp-select" :disabled="reviewListMode !== 'all'" @change="loadReviewPanelData">
                          <option value="all">全部状态</option>
                          <option value="pending">待审</option>
                          <option value="approved">已通过</option>
                          <option value="rejected">已拒绝</option>
                          <option value="revised">修订中</option>
                        </select>
                        <button class="rvp-btn rvp-btn-soft" :disabled="reviewLoading" @click="refreshReviewPanel">刷新</button>
                        <button class="rvp-btn" :disabled="reviewActionLoading || !result" @click="submitCurrentReview">提交当前命盘</button>
                      </div>
                      <div class="panel-tip">{{ reviewPanelTip }}</div>
                      <div class="rvp-mode-summary">
                        <span class="rvp-mode-title">{{ reviewModeTitle }}</span>
                        <span class="rvp-mode-desc">当前共 {{ reviewCurrentViewCount }} 条 · {{ reviewLastLoadedLabel }}</span>
                      </div>
                      <div v-if="reviewStats" class="rvp-stats">
                        <span>总 {{ reviewStats.total }}</span>
                        <span>待审 {{ reviewStats.pending }}</span>
                        <span>通过 {{ reviewStats.approved }}</span>
                        <span>拒绝 {{ reviewStats.rejected }}</span>
                        <span>当前视图 {{ reviewCurrentViewCount }}</span>
                      </div>
                      <div v-if="reviewList.length" class="rvp-bulk-box">
                        <div class="rvp-bulk-top">
                          <button class="rvp-btn-soft" :disabled="reviewActionLoading || reviewBulkDisabledByMode" @click="toggleAllReviewItems">
                            {{ reviewAllVisibleSelected ? '清空本页' : '全选本页' }}
                          </button>
                          <span class="rvp-bulk-count">已选 {{ reviewBulkSelectedCount }} 条</span>
                        </div>
                        <div v-if="reviewMineModeStrongHint" class="rvp-bulk-strong-hint">{{ reviewMineModeStrongHint }}</div>
                        <div class="rvp-bulk-hint">{{ reviewBulkModeHint }}</div>
                        <textarea v-model="reviewBulkNotes" class="rvp-bulk-notes" rows="2" :disabled="reviewBulkDisabledByMode" placeholder="批量操作备注 / 驳回原因（可选）"></textarea>
                        <div class="rvp-bulk-actions">
                          <button class="rvp-btn-ok" :disabled="reviewActionLoading || !reviewBulkSelectedCount || reviewBulkDisabledByMode" @click="applyBulkReviewStatus('approved')">批量通过</button>
                          <button class="rvp-btn-warn" :disabled="reviewActionLoading || !reviewBulkSelectedCount || reviewBulkDisabledByMode" @click="applyBulkReviewStatus('revised')">批量修订</button>
                          <button class="rvp-btn-danger" :disabled="reviewActionLoading || !reviewBulkSelectedCount || reviewBulkDisabledByMode" @click="applyBulkReviewStatus('rejected')">批量拒绝</button>
                        </div>
                      </div>
                      <textarea v-model="reviewSubmitNotes" class="rvp-submit-notes" rows="2" placeholder="提交审核时附带备注（可选）"></textarea>
                      <div v-if="reviewLoading" class="rvp-state">加载中…</div>
                      <div v-else-if="reviewError" class="rvp-state rvp-error">{{ reviewError }}</div>
                      <div v-else-if="reviewList.length === 0" class="rvp-state">{{ reviewEmptyStateText }}</div>
                      <div v-else class="rvp-layout">
                        <div class="rvp-list">
                          <div
                            v-for="item in reviewList"
                            :key="item.id"
                            :class="['rvp-item', { active: reviewSelectedId === item.id, 'selected-bulk': reviewBulkSelectedIds.includes(item.id), 'claimed-me': isReviewOwnedByMe(item) }]"
                            @click="selectReviewItem(item)"
                          >
                            <div class="rvp-item-top">
                              <div class="rvp-item-left">
                                <input
                                  class="rvp-item-check"
                                  type="checkbox"
                                  :checked="reviewBulkSelectedIds.includes(item.id)"
                                  @click.stop="toggleReviewBulkItem(item.id)"
                                />
                                <span class="rvp-item-id">#{{ item.id }}</span>
                              </div>
                              <span :class="['rvp-item-status', getReviewStatusClass(item.status)]">{{ getReviewStatusLabel(item.status) }}</span>
                            </div>
                            <div class="rvp-item-meta-row">
                              <span class="rvp-item-meta">{{ item.chart_type || 'ziwei' }} · {{ item.created_at.replace('T', ' ').slice(0, 16) }}</span>
                              <span :class="['rvp-owner-tag', isReviewOwnedByMe(item) ? 'is-mine' : item.reviewer ? 'is-assigned' : 'is-unassigned']">{{ getReviewOwnershipLabel(item) }}</span>
                            </div>
                          </div>
                        </div>
                        <div v-if="currentReview" class="rvp-detail">
                          <div class="rvp-detail-title">审核单 #{{ currentReview.id }}</div>
                          <div class="rvp-detail-meta rvp-detail-meta-rich">
                            <span>状态：</span>
                            <span :class="['rvp-item-status', getReviewStatusClass(currentReview.status)]">{{ getReviewStatusLabel(currentReview.status) }}</span>
                            <span>审核人：</span>
                            <span :class="['rvp-owner-tag', isReviewOwnedByMe(currentReview) ? 'is-mine' : currentReview.reviewer ? 'is-assigned' : 'is-unassigned']">{{ getReviewOwnershipLabel(currentReview) }}</span>
                          </div>
                          <div v-if="currentReview.status === 'pending'" class="rvp-assign-box">
                            <div class="rvp-assign-title">快速指派</div>
                            <div class="rvp-assign-presets">
                              <button
                                v-for="assignee in reviewAssigneeQuickOptions"
                                :key="assignee.username"
                                class="rvp-assign-chip"
                                :class="{ active: reviewAssignInput === assignee.username }"
                                @click="reviewAssignInput = assignee.username"
                              >
                                <span>{{ assignee.username }}</span>
                                <span v-if="assignee.tag" class="rvp-assign-chip-tag">{{ assignee.tag }}</span>
                              </button>
                            </div>
                            <div class="rvp-assign-row">
                              <input v-model="reviewAssignInput" class="rvp-assign-input" type="text" placeholder="输入 reviewer / 工号" />
                              <button class="rvp-btn-soft" :disabled="reviewActionLoading" @click="assignCurrentReview()">指派</button>
                            </div>
                          </div>
                          <textarea v-model="reviewSelectedNotes" class="rvp-detail-notes" rows="4" placeholder="审核批注 / 拒绝原因"></textarea>
                          <div class="rvp-actions">
                            <button
                              v-if="currentReview.status === 'pending' && currentReview.reviewer !== reviewAssigneeName"
                              class="rvp-btn-soft"
                              :disabled="reviewActionLoading"
                              @click="assignCurrentReviewToMe"
                            >领取当前</button>
                            <button class="rvp-btn-soft" :disabled="reviewActionLoading" @click="saveReviewNotes">保存批注</button>
                            <button class="rvp-btn-ok" :disabled="reviewActionLoading" @click="changeReviewStatus('approved')">通过</button>
                            <button class="rvp-btn-warn" :disabled="reviewActionLoading" @click="changeReviewStatus('revised')">修订</button>
                            <button class="rvp-btn-danger" :disabled="reviewActionLoading" @click="changeReviewStatus('rejected')">拒绝</button>
                          </div>
                          <div class="rvp-history-title">历史记录</div>
                          <div v-if="reviewHistoryLoading" class="rvp-history-state">加载中…</div>
                          <div v-else-if="reviewSelectedHistory.length === 0" class="rvp-history-state">暂无历史</div>
                          <div v-else class="rvp-history-list">
                            <div v-for="(item, index) in reviewSelectedHistory" :key="index" class="rvp-history-item">
                              <div class="rvp-history-meta rvp-history-meta-rich">
                                <span>{{ item.timestamp || item.changed_at || '—' }}</span>
                                <span>·</span>
                                <span>{{ item.actor || item.reviewer || '系统' }}</span>
                                <span :class="['rvp-history-tag', getReviewHistoryTypeClass(item)]">{{ getReviewHistoryTypeLabel(item) }}</span>
                              </div>
                              <div class="rvp-history-note">{{ item.notes || item.reject_reason || item.action || item.status || '无附加说明' }}</div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>

                    <!-- AI 草稿面板 -->
                    <div v-if="showLlmPanel" class="llm-panel-zw">
                      <div class="lzp-header">
                        <span>AI 草稿</span>
                        <button class="lzp-close" @click="showLlmPanel = false">✕</button>
                      </div>
                      <div v-if="isOverlayFeedbackVisible('llm')" :class="['panel-feedback', overlayFeedback!.type]">{{ overlayFeedback!.message }}</div>
                      <div class="lzp-config">模型：{{ llmConfigLabel }}</div>
                      <div class="lzp-toolbar">
                        <button class="lzp-btn" :disabled="llmLoading || !result" @click="generateLlmDraft">生成草稿</button>
                        <button class="lzp-btn lzp-btn-soft" :disabled="llmLoading || !result" @click="streamLlmDraft">流式生成</button>
                        <select v-model="llmFilterStatus" class="lzp-select" @change="loadLlmDraftList">
                          <option value="">全部草稿</option>
                          <option value="pending_review">待审核</option>
                          <option value="approved">已通过</option>
                          <option value="rejected">已驳回</option>
                        </select>
                      </div>
                      <div class="panel-tip">先生成草稿，再决定是否审核通过；历史区可回看此前版本。</div>
                      <div class="lzp-status">{{ llmStatus || '—' }}</div>
                      <div class="lzp-current-box">
                        <div class="lzp-current-head">
                          <span>当前草稿</span>
                          <span class="lzp-current-tag">{{ llmCurrentStatusLabel }}</span>
                        </div>
                        <pre class="lzp-current-text">{{ llmCurrentText || '尚未生成草稿' }}</pre>
                        <div class="lzp-copy-row">
                          <button class="lzp-btn lzp-btn-soft" :disabled="!llmCurrentText || llmLoading" @click="copyCurrentLlmDraft">
                            {{ llmCopied ? '已复制草稿' : '复制草稿' }}
                          </button>
                        </div>
                        <textarea
                          v-model="llmReviewerNotes"
                          class="lzp-reviewer-notes"
                          rows="3"
                          placeholder="reviewer notes：记录审核依据、修改建议或驳回原因"
                        />
                        <div class="lzp-current-actions">
                          <button class="lzp-btn lzp-btn-soft" :disabled="llmLoading || !llmCurrentDraft" @click="saveCurrentDraftNotes">保存备注</button>
                          <button v-if="llmCurrentDraft && llmCurrentDraft.status === 'pending_review'" class="lzp-btn-ok" :disabled="llmLoading" @click="reviewCurrentDraft('approved')">通过草稿</button>
                          <button v-if="llmCurrentDraft && llmCurrentDraft.status === 'pending_review'" class="lzp-btn-danger" :disabled="llmLoading" @click="reviewCurrentDraft('rejected')">驳回草稿</button>
                        </div>
                      </div>
                      <div class="lzp-list-title">历史草稿</div>
                      <div v-if="llmDrafts.length === 0" class="lzp-empty">暂无历史草稿，可先生成一版 AI 解读</div>
                      <div v-else class="lzp-list">
                        <button v-for="draft in llmDrafts" :key="draft.id" class="lzp-item" @click="openLlmDraft(draft.id)">
                          <div class="lzp-item-top">
                            <span class="lzp-item-status">{{ getLlmDraftStatusLabel(draft.status) }}</span>
                            <span class="lzp-item-time">{{ draft.created_at.slice(0, 16).replace('T', ' ') }}</span>
                          </div>
                          <div class="lzp-item-preview">{{ draft.draft_text.slice(0, 72) }}{{ draft.draft_text.length > 72 ? '…' : '' }}</div>
                        </button>
                      </div>
                    </div>

                    <!-- 运营面板 -->
                    <div v-if="showOpsPanel" class="ops-panel-zw">
                      <div class="ozp-header">
                        <span>运营面板</span>
                        <button class="ozp-close" @click="showOpsPanel = false">✕</button>
                      </div>
                      <div v-if="isOverlayFeedbackVisible('ops')" :class="['panel-feedback', overlayFeedback!.type]">{{ overlayFeedback!.message }}</div>
                      <div class="ozp-toolbar">
                        <select v-model="opsExperimentFilter" class="ozp-select" @change="loadOpsPanelData">
                          <option value="all">全部实验</option>
                          <option value="draft">草稿</option>
                          <option value="running">运行中</option>
                          <option value="paused">已暂停</option>
                          <option value="completed">已完成</option>
                        </select>
                        <button class="ozp-btn" @click="loadOpsPanelData">刷新</button>
                        <button class="ozp-btn ozp-btn-soft" @click="opsCreateFormVisible = !opsCreateFormVisible">
                          {{ opsCreateFormVisible ? '收起新实验' : '新建实验' }}
                        </button>
                      </div>
                      <div class="panel-tip">先看统计，再创建或推进实验；结果区会展示当前赢家建议。</div>
                      <div v-if="opsStatus" class="ozp-status">{{ opsStatus }}</div>
                      <div v-if="opsLoading" class="ozp-state">加载中…</div>
                      <div v-else-if="opsError" class="ozp-state ozp-error">{{ opsError }}</div>
                      <template v-else>
                        <div v-if="opsStats" class="ozp-stats-grid">
                          <div class="ozp-stat-card">
                            <div class="ozp-stat-num">{{ opsStats.users.total }}</div>
                            <div class="ozp-stat-label">总用户</div>
                            <div class="ozp-stat-sub">活跃 {{ opsStats.users.active ?? 0 }}</div>
                          </div>
                          <div class="ozp-stat-card">
                            <div class="ozp-stat-num">{{ opsStats.cases.total }}</div>
                            <div class="ozp-stat-label">命盘档案</div>
                            <div class="ozp-stat-sub">快照 {{ opsStats.snapshots.total }}</div>
                          </div>
                          <div class="ozp-stat-card">
                            <div class="ozp-stat-num">{{ opsStats.reviews.total }}</div>
                            <div class="ozp-stat-label">人工审核</div>
                            <div class="ozp-stat-sub">待审 {{ opsStats.reviews.pending }}</div>
                          </div>
                          <div class="ozp-stat-card">
                            <div class="ozp-stat-num">{{ opsStats.experiments.total }}</div>
                            <div class="ozp-stat-label">A/B 实验</div>
                            <div class="ozp-stat-sub">运行中 {{ opsStats.experiments.running ?? 0 }}</div>
                          </div>
                        </div>

                        <div v-if="opsStats" class="ozp-chart-grid">
                          <div class="ozp-chart-box">
                            <div class="ozp-box-title">热门命格</div>
                            <div v-if="opsStats.top_patterns.length === 0" class="ozp-box-empty">暂无数据</div>
                            <div v-else class="ozp-bar-list">
                              <div v-for="item in opsStats.top_patterns" :key="item.name" class="ozp-bar-row">
                                <span class="ozp-bar-name">{{ item.name }}</span>
                                <span class="ozp-bar-count">{{ item.count }}</span>
                              </div>
                            </div>
                          </div>
                          <div class="ozp-chart-box">
                            <div class="ozp-box-title">五行局分布</div>
                            <div v-if="opsStats.top_wuxing.length === 0" class="ozp-box-empty">暂无数据</div>
                            <div v-else class="ozp-bar-list">
                              <div v-for="item in opsStats.top_wuxing" :key="item.name" class="ozp-bar-row">
                                <span class="ozp-bar-name">{{ item.name }}</span>
                                <span class="ozp-bar-count">{{ item.count }}</span>
                              </div>
                            </div>
                          </div>
                        </div>

                        <div v-if="opsCreateFormVisible" class="ozp-create-box">
                          <div class="ozp-box-title">新建 A/B 实验</div>
                          <div class="ozp-form-grid">
                            <input v-model="opsCreateForm.name" class="ozp-input" type="text" placeholder="实验名称" />
                            <input v-model="opsCreateForm.targetMetric" class="ozp-input" type="text" placeholder="目标指标，如 conversion" />
                            <textarea v-model="opsCreateForm.description" class="ozp-textarea" rows="2" placeholder="实验描述"></textarea>
                            <textarea v-model="opsCreateForm.hypothesis" class="ozp-textarea" rows="2" placeholder="实验假设"></textarea>
                            <input v-model.number="opsCreateForm.minSampleSize" class="ozp-input" type="number" min="1" placeholder="最小样本量" />
                            <div class="ozp-weight-row">
                              <input v-model.number="opsCreateForm.controlWeight" class="ozp-input" type="number" min="0" max="100" placeholder="对照组权重" />
                              <input v-model.number="opsCreateForm.variantWeight" class="ozp-input" type="number" min="0" max="100" placeholder="实验组权重" />
                            </div>
                          </div>
                          <div class="ozp-form-actions">
                            <button class="ozp-btn" :disabled="opsExperimentSaving" @click="createOpsExperiment">
                              {{ opsExperimentSaving ? '创建中…' : '创建实验' }}
                            </button>
                          </div>
                        </div>

                        <div class="ozp-experiments-head">
                          <span class="ozp-box-title">实验列表</span>
                          <span class="ozp-total">共 {{ opsExperimentsTotal }} 个实验</span>
                        </div>
                        <div v-if="opsExperiments.length === 0" class="ozp-box-empty">暂无实验记录，可先创建一个 A/B 试验</div>
                        <div v-else class="ozp-exp-list">
                          <div v-for="exp in opsExperiments" :key="exp.id" class="ozp-exp-card">
                            <div class="ozp-exp-top">
                              <span class="ozp-exp-name">{{ exp.name }}</span>
                              <span class="ozp-exp-badge">{{ getExperimentStatusLabel(exp.status) }}</span>
                            </div>
                            <div class="ozp-exp-desc">{{ exp.description || '无描述' }}</div>
                            <div class="ozp-exp-meta">目标指标：{{ exp.target_metric }} · 最小样本：{{ exp.min_sample_size }}</div>
                            <div v-if="Array.isArray(exp.variants) && exp.variants.length" class="ozp-exp-variants">
                              <span v-for="variant in exp.variants" :key="variant.name" class="ozp-variant-chip">
                                {{ variant.name }} ({{ variant.weight }})
                              </span>
                            </div>
                            <div class="ozp-exp-actions">
                              <button v-if="exp.status === 'draft'" class="ozp-btn" @click="changeOpsExperimentStatus(exp.id, 'running')">启动</button>
                              <button v-if="exp.status === 'running'" class="ozp-btn ozp-btn-soft" @click="changeOpsExperimentStatus(exp.id, 'paused')">暂停</button>
                              <button v-if="exp.status === 'paused'" class="ozp-btn" @click="changeOpsExperimentStatus(exp.id, 'running')">继续</button>
                              <button v-if="exp.status === 'running' || exp.status === 'paused'" class="ozp-btn ozp-btn-warn" @click="changeOpsExperimentStatus(exp.id, 'completed')">完成</button>
                              <button class="ozp-btn ozp-btn-soft" @click="showOpsExperimentResults(exp.id)">结果</button>
                              <button v-if="exp.status !== 'running'" class="ozp-btn ozp-btn-danger" @click="removeOpsExperiment(exp.id)">删除</button>
                            </div>
                          </div>
                        </div>

                        <div v-if="opsExperimentResults || opsExperimentResultsLoading" class="ozp-results-box">
                          <div class="ozp-box-title">实验结果</div>
                          <div v-if="opsExperimentResultsLoading" class="ozp-box-empty">加载中…</div>
                          <template v-else-if="opsExperimentResults">
                            <div class="ozp-results-meta">
                              {{ opsExperimentResults.experiment_name }} · {{ getExperimentStatusLabel(opsExperimentResults.status) }} · 总分配 {{ opsExperimentResults.total_assigned }}
                            </div>
                            <div class="ozp-results-winner">建议赢家：{{ opsExperimentResults.winner || '暂无' }}</div>
                            <div class="ozp-results-note">{{ opsExperimentResults.note || '暂无结论说明' }}</div>
                            <div class="ozp-result-list">
                              <div v-for="variant in opsExperimentResults.variants" :key="variant.variant" class="ozp-result-item">
                                <div class="ozp-result-top">
                                  <span>{{ variant.variant }}</span>
                                  <span>{{ Math.round(variant.conversion_rate * 10000) / 100 }}%</span>
                                </div>
                                <div class="ozp-result-meta">分配 {{ variant.assigned }} · 转化 {{ variant.conversions }}</div>
                              </div>
                            </div>
                          </template>
                        </div>
                      </template>
                    </div>

                    <!-- 批量排盘面板 -->
                    <div v-if="showBatchPanel" class="batch-panel-zw">
                      <div class="bzp-header">
                        <span>批量排盘</span>
                        <button class="bzp-close" @click="showBatchPanel = false">✕</button>
                      </div>
                      <div class="panel-tip">流程：下载模板 → 选择 CSV → 开始批量排盘 → 等待 ZIP 下载。</div>
                      <div class="bzp-toolbar">
                        <button class="bzp-btn bzp-btn-soft" @click="downloadBatchSample">下载 CSV 模板</button>
                        <input class="bzp-template-input" v-model="batchTemplateVersion" type="text" placeholder="模板版本（可选）" />
                      </div>
                      <label class="bzp-upload-box">
                        <input class="bzp-file-input" type="file" accept=".csv,text/csv" @change="handleBatchFileChange" />
                        <span>{{ batchSelectedFile ? `已选择：${batchSelectedFile.name}` : '选择 CSV 文件或拖放到此处' }}</span>
                      </label>
                      <div class="bzp-status">{{ batchStatus || '支持上传 CSV，返回 ZIP 压缩包。' }}</div>
                      <div v-if="batchError" class="bzp-error">{{ batchError }}</div>
                      <div class="bzp-actions">
                        <button class="bzp-btn" :disabled="!batchSelectedFile || batchLoading" @click="runZiweiBatch">
                          {{ batchLoading ? '批量处理中…' : '开始批量排盘' }}
                        </button>
                      </div>
                      <div class="bzp-hint">
                        结果将下载为 ZIP，包含每个命盘的 JSON 输出与汇总文件。
                      </div>
                    </div>

                    <!-- 词汇工具面板 -->
                    <div v-if="showGlossaryPanel" class="glossary-panel-zw">
                      <div class="gzp-header">
                        <span>词汇工具</span>
                        <button class="gzp-close" @click="showGlossaryPanel = false">✕</button>
                      </div>
                      <div v-if="isOverlayFeedbackVisible('glossary')" :class="['panel-feedback', overlayFeedback!.type]">{{ overlayFeedback!.message }}</div>
                      <div class="gzp-toolbar">
                        <input
                          v-model="glossaryToolSearch"
                          class="gzp-input"
                          type="text"
                          placeholder="搜索术语，如 紫府同宫 / 化忌"
                          @keydown.enter.prevent="loadGlossaryToolPanel"
                        />
                        <select v-model="glossaryToolCategory" class="gzp-select" @change="loadGlossaryToolPanel">
                          <option value="">全部分类</option>
                          <option value="格局">格局</option>
                          <option value="神煞">神煞</option>
                          <option value="五行">五行</option>
                          <option value="十神">十神</option>
                          <option value="大运">大运</option>
                          <option value="其他">其他</option>
                        </select>
                        <button class="gzp-btn" :disabled="glossaryToolLoading" @click="loadGlossaryToolPanel">查询</button>
                      </div>
                      <div class="panel-tip">可直接搜索、点击命盘联想词条，或复制当前术语定义到外部文档。</div>
                      <div v-if="glossarySuggestedTerms.length" class="gzp-suggest-row">
                        <span class="gzp-suggest-label">命盘联想：</span>
                        <button
                          v-for="term in glossarySuggestedTerms"
                          :key="term"
                          class="gzp-suggest-chip"
                          @click="useGlossarySuggestedTerm(term)"
                        >
                          {{ term }}
                        </button>
                      </div>
                      <div v-if="glossaryToolLoading" class="gzp-state">加载中…</div>
                      <div v-else-if="glossaryToolError" class="gzp-state gzp-error">{{ glossaryToolError }}</div>
                      <div v-else-if="glossaryToolItems.length === 0" class="gzp-state">
                        {{ glossaryToolSearch ? `未找到“${glossaryToolSearch}”相关词汇` : '暂无词汇，可试试上方命盘联想词条' }}
                      </div>
                      <div v-else class="gzp-list">
                        <div v-for="item in glossaryToolItems" :key="item.term" class="gzp-item">
                          <div class="gzp-item-top">
                            <span class="gzp-term">{{ item.term }}</span>
                            <div class="gzp-item-actions">
                              <span class="gzp-cat">{{ item.category }}</span>
                              <button class="gzp-copy-btn" @click="copyGlossaryItem(item)">
                                {{ glossaryCopiedTerm === item.term ? '已复制' : '复制' }}
                              </button>
                            </div>
                          </div>
                          <div v-if="item.pinyin" class="gzp-pinyin">{{ item.pinyin }}</div>
                          <div class="gzp-def">{{ item.definition || '暂无定义' }}</div>
                          <div v-if="item.classic_source" class="gzp-source">典籍：{{ item.classic_source }}</div>
                          <div v-if="getGlossaryRelatedTerms(item).length" class="gzp-related">
                            <span class="gzp-related-label">相关词条：</span>
                            <button
                              v-for="related in getGlossaryRelatedTerms(item)"
                              :key="`${item.term}-${related.term}`"
                              class="gzp-related-chip"
                              @click="useGlossarySuggestedTerm(related.term)"
                            >
                              {{ related.term }}
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>

                    <!-- 多人合盘面板 -->
                    <div v-if="showMultiCompatPanel" class="mcp-panel-zw">
                      <div class="mcz-header">
                        <span>多人合盘</span>
                        <button class="mcz-close" @click="showMultiCompatPanel = false">✕</button>
                      </div>
                      <div v-if="isOverlayFeedbackVisible('multi')" :class="['panel-feedback', overlayFeedback!.type]">{{ overlayFeedback!.message }}</div>
                      <div class="mcz-current-card">
                        <div class="mcz-current-title">甲方（当前命盘）</div>
                        <div class="mcz-current-meta">
                          {{ year }}-{{ String(month).padStart(2, '0') }}-{{ String(day).padStart(2, '0') }} {{ String(hour).padStart(2, '0') }}:{{ String(minute).padStart(2, '0') }} · {{ gender }}
                        </div>
                      </div>
                      <div class="mcz-person-list">
                        <div v-for="(person, index) in multiCompatPersons" :key="index" class="mcz-person-card">
                          <div class="mcz-person-top">
                            <span class="mcz-person-title">{{ getMultiCompatLabel(index + 1) }}</span>
                            <button v-if="multiCompatPersons.length > 1" class="mcz-del-btn" @click="removeMultiCompatPerson(index)">删除</button>
                          </div>
                          <div class="mcz-form-grid">
                            <input v-model.number="person.year" class="mcz-input" type="number" min="1900" max="2100" placeholder="年" />
                            <input v-model.number="person.month" class="mcz-input" type="number" min="1" max="12" placeholder="月" />
                            <input v-model.number="person.day" class="mcz-input" type="number" min="1" max="31" placeholder="日" />
                            <input v-model.number="person.hour" class="mcz-input" type="number" min="0" max="23" placeholder="时" />
                            <input v-model.number="person.minute" class="mcz-input" type="number" min="0" max="59" placeholder="分" />
                            <select v-model="person.gender" class="mcz-input">
                              <option value="男">男</option>
                              <option value="女">女</option>
                            </select>
                            <input v-model.number="person.longitude" class="mcz-input mcz-input-wide" type="number" step="0.1" placeholder="经度（可选）" />
                          </div>
                        </div>
                      </div>
                      <div class="mcz-actions">
                        <button class="mcz-btn mcz-btn-soft" :disabled="multiCompatPersons.length >= 3" @click="addMultiCompatPerson">添加成员</button>
                        <button class="mcz-btn" :disabled="multiCompatLoading" @click="runMultiCompat">
                          {{ multiCompatLoading ? '计算中…' : '计算缘分矩阵' }}
                        </button>
                      </div>
                      <div class="panel-tip">建议先补齐成员出生信息，再计算矩阵并优先查看高亮最佳组合。</div>
                      <div v-if="multiCompatError" class="mcz-error">{{ multiCompatError }}</div>
                      <div v-else-if="!multiCompatResult" class="mcz-empty">尚未生成缘分矩阵，点击上方按钮开始计算</div>
                      <div v-if="multiCompatResult" class="mcz-result-box">
                        <div class="mcz-score-card">
                          <div class="mcz-score-num">{{ multiCompatResult.team_harmony_score }}</div>
                          <div class="mcz-score-label">团队和谐指数</div>
                        </div>
                        <div class="mcz-legend">
                          <span class="mcz-legend-title">图例说明</span>
                          <span v-for="item in multiCompatScoreLegend" :key="item.label" class="mcz-legend-chip" :class="item.className" :title="item.hint">
                            {{ item.label }}
                          </span>
                        </div>
                        <div v-if="multiCompatBestPair" class="mcz-summary-banner">
                          当前最佳组合：{{ getMultiCompatLabel(multiCompatBestPair.person_a_idx) }} × {{ getMultiCompatLabel(multiCompatBestPair.person_b_idx) }}
                          · {{ multiCompatBestPair.total_score }} 分 · {{ multiCompatBestPair.level }}
                        </div>
                        <div v-if="multiCompatActionAdvice.length" class="mcz-advice-box">
                          <div class="mcz-advice-title">行动建议</div>
                          <ul class="mcz-advice-list">
                            <li v-for="item in multiCompatActionAdvice" :key="item">{{ item }}</li>
                          </ul>
                        </div>
                        <div class="mcz-matrix-wrap">
                          <table class="mcz-matrix">
                            <thead>
                              <tr>
                                <th></th>
                                <th v-for="idx in multiCompatResult.person_count" :key="`head-${idx}`">{{ getMultiCompatLabel(idx - 1) }}</th>
                              </tr>
                            </thead>
                            <tbody>
                              <tr v-for="(row, rowIndex) in multiCompatResult.matrix" :key="`row-${rowIndex}`">
                                <th>{{ getMultiCompatLabel(rowIndex) }}</th>
                                <td
                                  v-for="(cell, colIndex) in row"
                                  :key="`cell-${rowIndex}-${colIndex}`"
                                  :class="getMultiCompatMatrixCellClass(cell, rowIndex, colIndex)"
                                  :title="getMultiCompatCellHint(cell, rowIndex, colIndex)"
                                >
                                  {{ rowIndex === colIndex ? '—' : cell }}
                                </td>
                              </tr>
                            </tbody>
                          </table>
                        </div>
                        <div class="mcz-pairs">
                          <div
                            v-for="pair in multiCompatResult.pairs"
                            :key="`${pair.person_a_idx}-${pair.person_b_idx}`"
                            class="mcz-pair-item"
                            :class="getMultiCompatPairClass(pair.level)"
                          >
                            <div class="mcz-pair-top">
                              <span>{{ getMultiCompatLabel(pair.person_a_idx) }} × {{ getMultiCompatLabel(pair.person_b_idx) }}</span>
                              <span>{{ pair.total_score }}/{{ pair.max_score }}</span>
                            </div>
                            <div class="mcz-pair-level">{{ pair.level }}</div>
                          </div>
                        </div>
                      </div>
                    </div>

                    <!-- 风水助手面板 -->
                    <div v-if="showFengshuiPanel" class="fengshui-panel-zw">
                      <div class="fsp-header">
                        <span>风水助手</span>
                        <button class="fsp-close" @click="showFengshuiPanel = false">✕</button>
                      </div>
                      <div v-if="isOverlayFeedbackVisible('fengshui')" :class="['panel-feedback', overlayFeedback!.type]">{{ overlayFeedback!.message }}</div>
                      <div class="fsp-toolbar">
                        <input v-model.number="fengshuiForm.birthYear" class="fsp-input" type="number" min="1900" max="2100" placeholder="出生年" />
                        <select v-model="fengshuiForm.gender" class="fsp-select">
                          <option value="男">男</option>
                          <option value="女">女</option>
                        </select>
                        <select v-model="fengshuiForm.houseFacing" class="fsp-select">
                          <option value="">房屋朝向（可选）</option>
                          <option v-for="(label, key) in (fengshuiOptions?.house_facing_options || {})" :key="key" :value="key">
                            {{ label }}
                          </option>
                        </select>
                        <button class="fsp-btn" :disabled="fengshuiLoading" @click="runFengshuiBagua">
                          {{ fengshuiLoading ? '计算中…' : '命卦分析' }}
                        </button>
                      </div>
                      <div class="panel-tip">先同步命卦，再设置房间方位并评估九宫格布局。</div>
                      <div v-if="fengshuiError" class="fsp-error">{{ fengshuiError }}</div>
                      <div v-if="fengshuiData" class="fsp-result-box">
                        <div class="fsp-summary-card">
                          <div class="fsp-summary-title">{{ fengshuiData.gua_name }}命 · 第{{ fengshuiData.life_gua }}卦</div>
                          <div class="fsp-summary-meta">{{ fengshuiData.gua_element }} · {{ fengshuiData.group }}</div>
                          <div v-if="fengshuiData.compatibility" class="fsp-compat">人宅{{ fengshuiData.compatibility }} · {{ fengshuiData.compatibility_note || '—' }}</div>
                        </div>
                        <div v-if="fengshuiDirectionLegend.length" class="fsp-direction-legend">
                          <div class="fsp-legend-title">方位图例</div>
                          <div class="fsp-legend-list">
                            <div v-for="item in fengshuiDirectionLegend" :key="`${item.tone}-${item.direction}`" class="fsp-legend-chip" :class="item.tone">
                              {{ item.direction_zh }} · {{ item.label }}
                            </div>
                          </div>
                        </div>
                        <div class="fsp-grid">
                          <div class="fsp-box">
                            <div class="fsp-box-title">四吉方</div>
                            <div class="fsp-dir-list">
                              <div v-for="item in fengshuiData.auspicious" :key="`good-${item.direction}`" class="fsp-dir-item good">
                                <div class="fsp-dir-top">
                                  <span>{{ item.direction_zh }}（{{ item.direction }}）</span>
                                  <span>{{ item.label }}</span>
                                </div>
                                <div class="fsp-dir-desc">{{ item.desc }}</div>
                              </div>
                            </div>
                          </div>
                          <div class="fsp-box">
                            <div class="fsp-box-title">四凶方</div>
                            <div class="fsp-dir-list">
                              <div v-for="item in fengshuiData.inauspicious" :key="`bad-${item.direction}`" class="fsp-dir-item bad">
                                <div class="fsp-dir-top">
                                  <span>{{ item.direction_zh }}（{{ item.direction }}）</span>
                                  <span>{{ item.label }}</span>
                                </div>
                                <div class="fsp-dir-desc">{{ item.desc }}</div>
                              </div>
                            </div>
                          </div>
                        </div>
                        <div class="fsp-tip-list">
                          <div v-for="tip in [fengshuiData.bed_tip, fengshuiData.desk_tip, fengshuiData.door_tip].filter(Boolean)" :key="`${tip!.item}-${tip!.direction}`" class="fsp-tip-card">
                            <div class="fsp-tip-title">{{ tip!.item }}</div>
                            <div class="fsp-tip-meta">{{ tip!.direction_zh }}（{{ tip!.direction }}） · {{ tip!.label }}</div>
                            <div class="fsp-tip-reason">{{ tip!.reason }}</div>
                          </div>
                        </div>
                        <div class="fsp-room-box">
                          <div class="fsp-box-title">九宫格房间布局评估</div>
                          <div class="fsp-room-grid">
                            <div v-for="dir in ['N','NE','E','SE','S','SW','W','NW']" :key="dir" class="fsp-room-cell">
                              <div class="fsp-room-label">{{ getDirectionBadgeLabel(dir) }}（{{ dir }}）</div>
                              <select class="fsp-room-select" :value="fengshuiRooms[dir] || ''" @change="updateFengshuiRoom(dir, ($event.target as HTMLSelectElement).value)">
                                <option value="">不设置</option>
                                <option v-for="(label, key) in (fengshuiOptions?.room_type_options || {})" :key="`${dir}-${key}`" :value="key">{{ label }}</option>
                              </select>
                            </div>
                          </div>
                          <div class="fsp-room-actions">
                            <button class="fsp-btn fsp-btn-soft" :disabled="fengshuiRoomLoading" @click="runFengshuiRoomLayout">
                              {{ fengshuiRoomLoading ? '评估中…' : '评估布局' }}
                            </button>
                          </div>
                          <div v-if="fengshuiRoomError" class="fsp-error">{{ fengshuiRoomError }}</div>
                          <div v-if="fengshuiRoomResult" class="fsp-room-result">
                            <div class="fsp-room-score">{{ fengshuiRoomResult.grade }} · {{ fengshuiRoomResult.score }} 分</div>
                            <div v-if="fengshuiRecommendedRooms.length" class="fsp-recommend-box">
                              <div class="fsp-legend-title">推荐房型</div>
                              <div class="fsp-recommend-list">
                                <span v-for="item in fengshuiRecommendedRooms" :key="item" class="fsp-recommend-chip">{{ item }}</span>
                              </div>
                            </div>
                            <div v-if="fengshuiAvoidRooms.length" class="fsp-avoid-box">
                              <div class="fsp-legend-title">避开房型</div>
                              <div class="fsp-recommend-list">
                                <span v-for="item in fengshuiAvoidRooms" :key="item" class="fsp-avoid-chip">{{ item }}</span>
                              </div>
                            </div>
                            <div class="fsp-layout-board">
                              <div
                                v-for="cell in fengshuiRoomBoardCells"
                                :key="`board-${cell.direction}`"
                                class="fsp-layout-cell"
                                :class="[
                                  cell.isCenter ? 'is-center' : getFengshuiRoomAssessClass(cell.resultCell?.assess_level),
                                ]"
                              >
                                <div class="fsp-layout-dir">{{ cell.directionLabel }}</div>
                                <template v-if="!cell.isCenter">
                                  <div class="fsp-layout-room">{{ cell.resultCell?.room_zh || (cell.selectedRoom ? getRoomTypeLabel(cell.selectedRoom) : '未设置') }}</div>
                                  <div class="fsp-layout-tag">{{ cell.resultCell?.label || getFengshuiDirectionTag(cell.direction) }}</div>
                                  <div v-if="cell.resultCell" class="fsp-layout-score">{{ cell.resultCell.assess_score }} 分</div>
                                </template>
                                <template v-else>
                                  <div class="fsp-layout-room">布局总览</div>
                                  <div class="fsp-layout-tag">{{ fengshuiRoomResult.grade }}</div>
                                </template>
                              </div>
                            </div>
                            <div class="fsp-room-cells">
                              <div
                                v-for="cell in fengshuiRoomResult.cells"
                                :key="`${cell.direction}-${cell.room_type}`"
                                class="fsp-room-badge"
                                :class="getFengshuiRoomAssessClass(cell.assess_level)"
                              >
                                {{ cell.room_zh || getRoomTypeLabel(cell.room_type) }}@{{ cell.direction_zh }} · {{ cell.assess_note }}
                              </div>
                            </div>
                            <ul v-if="fengshuiRoomResult.suggestions.length" class="fsp-suggestion-list">
                              <li v-for="(item, index) in fengshuiRoomResult.suggestions" :key="index">{{ item }}</li>
                            </ul>
                          </div>
                        </div>
                        <div class="fsp-disclaimer">{{ fengshuiData.disclaimer }}</div>
                      </div>
                    </div>
                    
                    <!-- 笔记面板 -->
                    <div v-if="showNotesPanel" class="notes-panel">
                      <div class="np-header">
                        <span>命盘笔记 ({{ chartNotes.length }})</span>
                        <button class="np-close" @click="showNotesPanel = false">✕</button>
                      </div>
                      <div class="np-content">
                        <div class="np-add-form">
                          <select v-model="noteTarget" class="np-target-select">
                            <option value="general">全盘</option>
                            <option value="palace">宫位</option>
                            <option value="star">星曜</option>
                          </select>
                          <input v-if="noteTarget !== 'general'" v-model="noteTargetName" class="np-target-name" 
                                 :placeholder="noteTarget === 'palace' ? '宫名如:命宫' : '星名如:紫微'" />
                          <textarea v-model="noteInput" class="np-textarea" rows="2" placeholder="输入笔记内容..." />
                          <div class="np-btns">
                            <button v-if="editingNote" class="np-cancel" @click="cancelEditNote">取消</button>
                            <button v-if="editingNote" class="np-save" @click="updateNote">保存修改</button>
                            <button v-else class="np-add" @click="addNote">添加笔记</button>
                          </div>
                        </div>
                        <div v-if="chartNotes.length" class="np-list">
                          <div v-for="note in chartNotes" :key="note.id" class="np-item">
                            <div class="np-item-head">
                              <span class="np-item-target" :class="'np-' + note.target">{{ note.targetName }}</span>
                              <span class="np-item-time">{{ new Date(note.updatedAt).toLocaleDateString() }}</span>
                            </div>
                            <div class="np-item-content">{{ note.content }}</div>
                            <div class="np-item-actions">
                              <button @click="startEditNote(note)">编辑</button>
                              <button @click="deleteNote(note.id)">删除</button>
                            </div>
                          </div>
                        </div>
                        <div v-else class="np-empty">暂无笔记，快来记录你的心得吧</div>
                      </div>
                    </div>
                    
                    <!-- 日历视图面板 -->
                    <div v-if="showCalendarView" class="calendar-panel">
                      <div class="cal-header">
                        <button class="cal-nav" @click="prevCalendarMonth">◀</button>
                        <span class="cal-title">{{ calendarViewYear }}年{{ calendarViewMonth }}月 运势日历</span>
                        <button class="cal-nav" @click="nextCalendarMonth">▶</button>
                        <button class="cal-close" @click="showCalendarView = false">✕</button>
                      </div>
                      <div class="cal-weekdays">
                        <span>日</span><span>一</span><span>二</span><span>三</span><span>四</span><span>五</span><span>六</span>
                      </div>
                      <div class="cal-grid">
                        <div v-for="(item, i) in calendarGrid" :key="i" 
                             :class="['cal-day', item ? getDayFortuneClass(item.score) : 'cal-empty']">
                          <template v-if="item">
                            <span class="cal-day-num">{{ item.day }}</span>
                            <span class="cal-day-fortune">{{ item.brief }}</span>
                          </template>
                        </div>
                      </div>
                      <div class="cal-legend">
                        <span class="fortune-great">大吉</span>
                        <span class="fortune-good">吉</span>
                        <span class="fortune-normal">平</span>
                        <span class="fortune-bad">凶</span>
                        <span class="fortune-terrible">大凶</span>
                      </div>
                    </div>
                    
                    <!-- 对比设置面板 -->
                    <div v-if="showComparePanel" class="compare-panel">
                      <div class="cmp-header">
                        <span>命盘对比设置</span>
                        <button class="cmp-close" @click="showComparePanel = false">✕</button>
                      </div>
                      <div class="cmp-content">
                        <p class="cmp-hint">输入第二人资料进行对比分析</p>
                        <div class="cmp-form">
                          <div class="cmp-row">
                            <label>年</label>
                            <input type="number" v-model.number="compareYear" min="1900" max="2100" />
                            <label>月</label>
                            <input type="number" v-model.number="compareMonth" min="1" max="12" />
                            <label>日</label>
                            <input type="number" v-model.number="compareDay" min="1" max="31" />
                          </div>
                          <div class="cmp-row">
                            <label>时</label>
                            <input type="number" v-model.number="compareHour" min="0" max="23" />
                            <label>分</label>
                            <input type="number" v-model.number="compareMinute" min="0" max="59" />
                            <label>性别</label>
                            <select v-model="compareGender">
                              <option value="男">男</option>
                              <option value="女">女</option>
                            </select>
                          </div>
                        </div>
                        <div class="cmp-btns">
                          <button v-if="compareTarget" class="cmp-clear" @click="clearCompareTarget">清除对比</button>
                          <button class="cmp-set" @click="setCompareTarget">设置对比</button>
                        </div>
                        <div v-if="compareTarget" class="cmp-status">
                          当前对比: {{ compareTarget.year }}/{{ compareTarget.month }}/{{ compareTarget.day }} 
                          {{ compareTarget.hour }}:{{ String(compareTarget.minute).padStart(2,'0') }} {{ compareTarget.gender }}
                        </div>
                      </div>
                    </div>
                    
                    <!-- 已收藏宫位面板 -->
                    <div v-if="showBookmarksPanel" class="bookmarks-panel">
                      <div class="bkm-header">
                        <span>已收藏宫位 ({{ bookmarkedPalaces.length }})</span>
                        <button class="bkm-close" @click="showBookmarksPanel = false">✕</button>
                      </div>
                      <div class="bkm-content">
                        <div v-if="bookmarkedPalaces.length" class="bkm-list">
                          <div v-for="p in bookmarkedPalaces" :key="p.index" class="bkm-item" @click="selectPalaceByIndex(p.index); showBookmarksPanel = false">
                            <span class="bkm-palace-name">{{ p.name }}</span>
                            <span class="bkm-palace-gz">{{ p.stem }}{{ p.branch }}</span>
                            <span class="bkm-palace-stars">
                              {{ p.main_stars?.map(s => s.name).join('、') || '无主星' }}
                            </span>
                            <button class="bkm-remove" @click.stop="togglePalaceBookmark(p.index)">✕</button>
                          </div>
                        </div>
                        <div v-else class="bkm-empty">
                          暂无收藏，点击宫位中的☆可收藏
                        </div>
                      </div>
                    </div>
                    
                    <!-- 命盘统计汇总卡片 -->
                    <div v-if="chartSummaryStats" class="chart-summary-card">
                      <div class="csc-row">
                        <span class="csc-label">主星</span>
                        <span class="csc-value">{{ chartSummaryStats.totalMainStars }}</span>
                        <span class="csc-label">辅星</span>
                        <span class="csc-value">{{ chartSummaryStats.totalAuxStars }}</span>
                        <span class="csc-label">庙旺</span>
                        <span class="csc-value csc-good">{{ chartSummaryStats.brightStars }}</span>
                        <span class="csc-label">陷落</span>
                        <span class="csc-value csc-bad">{{ chartSummaryStats.weakStars }}</span>
                      </div>
                      <div class="csc-row">
                        <span class="csc-label">禄</span>
                        <span class="csc-value csc-lu">{{ chartSummaryStats.luCount }}</span>
                        <span class="csc-label">权</span>
                        <span class="csc-value csc-quan">{{ chartSummaryStats.quanCount }}</span>
                        <span class="csc-label">科</span>
                        <span class="csc-value csc-ke">{{ chartSummaryStats.keCount }}</span>
                        <span class="csc-label">忌</span>
                        <span class="csc-value csc-ji">{{ chartSummaryStats.jiCount }}</span>
                      </div>
                      <div class="csc-row">
                        <span class="csc-label">吉星</span>
                        <span class="csc-value csc-good">{{ chartSummaryStats.jiStarCount }}</span>
                        <span class="csc-label">煞星</span>
                        <span class="csc-value csc-bad">{{ chartSummaryStats.shaCount }}</span>
                        <span class="csc-label">格局</span>
                        <span class="csc-value">{{ chartSummaryStats.patternsCount }}</span>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- 宫位格 -->
                <div v-else
                     :class="['pc-cell',
                       cell.palace?.name?.includes('命') ? 'pc-life' : '',
                       cell.palace?.name?.includes('身') ? 'pc-body' : '',
                       selectedPalace?.index === cell.palace?.index ? 'pc-sel' : '',
                       sanfangIndices.has(cell.palace!.index) ? 'pc-sanfang' : '',
                       overlayOpts.showLiunian && liunianLifePalaceIdx === cell.palace?.index ? 'pc-liunian-life' : '',
                       overlayOpts.showLiuyue && liuyueLifePalaceIdx === cell.palace?.index ? 'pc-liuyue-life' : '',
                       overlayOpts.showXiaoxian && xiaoxianPalaceIdx === cell.palace?.index ? 'pc-xiaoxian-life' : ''
                     ]"
                     :title="cell.palace?.tooltip || ''"
                     @click="selectPalace(cell.palace!)">
                  <!-- 宫名行：左宫名+标记，右干支 -->
                  <div class="pc-head">
                    <div class="pc-head-left">
                      <span class="pc-pname">{{ cell.palace!.name.replace('宫','') }}</span>
                      <span v-if="cell.palace!.name.includes('命')" class="pc-life-tag">命</span>
                      <span v-if="cell.palace!.name.includes('身')" class="pc-body-tag">身</span>
                      <!-- 宫位收藏按钮 -->
                      <button class="pc-bookmark-btn" 
                              :class="{ 'bookmarked': isPalaceBookmarked(cell.palace!.index) }"
                              @click.stop="togglePalaceBookmark(cell.palace!.index)"
                              :title="isPalaceBookmarked(cell.palace!.index) ? '取消收藏' : '收藏此宫'">
                        {{ isPalaceBookmarked(cell.palace!.index) ? '★' : '☆' }}
                      </button>
                      <!-- 大限宫位名称 -->
                      <span v-if="overlayOpts.showDaxian && palaceDaxianNames[cell.palace!.index]" class="pc-daxian-name">
                        {{ palaceDaxianNames[cell.palace!.index] }}
                      </span>
                      <!-- 流年宫位名称 -->
                      <span v-if="overlayOpts.showLiunian && palaceLiunianNames[cell.palace!.index]" class="pc-liunian-name">
                        {{ palaceLiunianNames[cell.palace!.index] }}
                      </span>
                      <!-- 流月宫位名称 -->
                      <span v-if="overlayOpts.showLiuyue && palaceLiuyueNames[cell.palace!.index]" class="pc-liuyue-name">
                        {{ palaceLiuyueNames[cell.palace!.index] }}
                      </span>
                      <!-- 小限宫位名称 -->
                      <span v-if="overlayOpts.showXiaoxian && palaceXiaoxianNames[cell.palace!.index]" class="pc-xiaoxian-name">
                        {{ palaceXiaoxianNames[cell.palace!.index] }}
                      </span>
                    </div>
                    <span class="pc-gzhi">{{ cell.palace!.stem }}{{ cell.palace!.branch }}</span>
                  </div>
                  <!-- 大限年龄 + 流年年龄 + 长生（C-4: 受 showChangsheng 控制） -->
                  <div class="pc-da-row">
                    <span v-if="palaceDayunMap[cell.palace!.index]" class="pc-da">
                      {{ palaceDayunMap[cell.palace!.index].start_age }}-{{ palaceDayunMap[cell.palace!.index].end_age }}岁
                    </span>
                    <!-- 流年年龄显示 -->
                    <span v-if="palaceLiunianInfo[cell.palace!.index]" class="pc-liunian-age">
                      {{ palaceLiunianInfo[cell.palace!.index].age }}岁
                    </span>
                    <span v-if="cell.palace!.changsheng && starDisplayOpts.showChangsheng" class="pc-cs">{{ cell.palace!.changsheng }}</span>
                    <!-- 将前/岁前星 -->
                    <span v-if="cell.palace!.jiangqian_star && starDisplayOpts.showJiangSui" class="pc-jiangqian">将{{ cell.palace!.jiangqian_star }}</span>
                    <span v-if="cell.palace!.suiqian_star && starDisplayOpts.showJiangSui" class="pc-suiqian">岁{{ cell.palace!.suiqian_star }}</span>
                  </div>
                  <!-- 博士十二星（C-8: 受 showBoshi 控制） -->
                  <div v-if="starDisplayOpts.showBoshi && cell.palace!.dayun_boshi && cell.palace!.dayun_boshi.length" class="pc-boshi-row">
                    <span v-for="bs in cell.palace!.dayun_boshi" :key="bs" class="pc-boshi">{{ bs }}</span>
                  </div>
                  <!-- 主星区块（C-4: 受 showMainStars, showBrightness, showTransforms 控制） -->
                  <div v-if="starDisplayOpts.showMainStars" class="pc-mstars">
                    <div v-for="s in cell.palace!.main_stars" :key="s.name" class="pc-mstar">
                      <span :class="['pc-sn', `pc-br${s.brightness_val}`]">{{ s.name }}</span>
                      <span v-if="starDisplayOpts.showBrightness" class="pc-sbr">{{ s.brightness.charAt(0) }}</span>
                      <template v-if="starDisplayOpts.showTransforms">
                        <span v-for="t in s.transforms" :key="t"
                              class="pc-tf"
                              :style="tfColorStyle(t)">{{ t.slice(1) }}</span>
                      </template>
                      <!-- 大限四化 -->
                      <span v-if="overlayOpts.showDaxian && daxianSihuaMap[s.name]" 
                            class="pc-tf pc-tf-daxian"
                            :style="tfOutlineStyle(daxianSihuaMap[s.name])">限{{ daxianSihuaMap[s.name].slice(1) }}</span>
                      <!-- 流年四化 -->
                      <span v-if="overlayOpts.showLiunian && liunianSihuaMap[s.name]" 
                            class="pc-tf pc-tf-liunian"
                            :style="tfOutlineStyle(liunianSihuaMap[s.name])">年{{ liunianSihuaMap[s.name].slice(1) }}</span>
                      <!-- 流月四化 -->
                      <span v-if="overlayOpts.showLiuyue && liuyueSihuaMap[s.name]" 
                            class="pc-tf pc-tf-liuyue"
                            :style="tfOutlineStyle(liuyueSihuaMap[s.name])">月{{ liuyueSihuaMap[s.name].slice(1) }}</span>
                    </div>
                  </div>
                  <!-- 辅星（C-4: 受 showAuxStars 和 auxLimit 控制） -->
                  <div v-if="starDisplayOpts.showAuxStars && cell.palace!.aux_stars.length" class="pc-aux">
                    {{ cell.palace!.aux_stars.slice(0, starDisplayOpts.auxLimit || cell.palace!.aux_stars.length).join('·') }}
                  </div>
                </div>
              </template>
            </div>
            <div class="compass-side compass-e">西</div>

            <!-- ═══════════════════════════════════════════════════════════════
                 C-3: 四化飞星 SVG 连线覆盖层
                 ═══════════════════════════════════════════════════════════════ -->
            <svg v-if="showSihuaLines && sihuaLines.length && chartMode === 'sihua'"
                 class="sihua-lines-svg" viewBox="0 0 100 100" preserveAspectRatio="none">
              <defs>
                <!-- 箭头标记 -->
                <marker v-for="[tf, cfg] in Object.entries(SIHUA_COLORS)" :key="tf"
                        :id="'arrow-' + cfg.label"
                        markerWidth="6" markerHeight="6" refX="5" refY="3"
                        orient="auto" markerUnits="strokeWidth">
                  <path d="M0,0 L6,3 L0,6 Z" :fill="cfg.color"/>
                </marker>
              </defs>
              <!-- 四化连线 -->
              <template v-for="(line, i) in sihuaLines" :key="i">
                <!-- 自化：画圆弧回到自身 -->
                <g v-if="line.isSelfHua" class="sihua-self">
                  <circle :cx="getPalaceCenter(line.fromBranchIdx).x"
                          :cy="getPalaceCenter(line.fromBranchIdx).y - 8"
                          r="5"
                          fill="none"
                          :stroke="line.color"
                          stroke-width="0.8"
                          stroke-dasharray="2,1"/>
                  <text :x="getPalaceCenter(line.fromBranchIdx).x"
                        :y="getPalaceCenter(line.fromBranchIdx).y - 14"
                        class="sihua-label" :fill="line.color">{{ line.label }}</text>
                </g>
                <!-- 非自化：画弧线箭头 -->
                <g v-else class="sihua-line">
                  <path :d="getCurvedPath(line.fromBranchIdx, line.toBranchIdx, 0.12 + i * 0.03)"
                        fill="none"
                        :stroke="line.color"
                        stroke-width="0.6"
                        :stroke-dasharray="line.transform === '化忌' ? '2,1' : 'none'"
                        :marker-end="'url(#arrow-' + line.label + ')'"/>
                  <!-- 弧线中点标签 -->
                  <circle :cx="getCurvedMidpoint(line.fromBranchIdx, line.toBranchIdx, 0.12 + i * 0.03).x"
                          :cy="getCurvedMidpoint(line.fromBranchIdx, line.toBranchIdx, 0.12 + i * 0.03).y"
                          r="3" :fill="line.color"/>
                  <text :x="getCurvedMidpoint(line.fromBranchIdx, line.toBranchIdx, 0.12 + i * 0.03).x"
                        :y="getCurvedMidpoint(line.fromBranchIdx, line.toBranchIdx, 0.12 + i * 0.03).y + 1"
                        class="sihua-label" fill="#fff">{{ line.label }}</text>
                </g>
              </template>
              <!-- 图例 -->
              <g class="sihua-legend" transform="translate(38, 38)">
                <text x="0" y="4" class="sihua-legend-text">自化图示:</text>
                <text x="0" y="10" class="sihua-legend-text">
                  <tspan fill="#22c55e">→禄</tspan>
                  <tspan fill="#f97316">→权</tspan>
                  <tspan fill="#3b82f6">→科</tspan>
                  <tspan fill="#ef4444">→忌</tspan>
                </text>
              </g>
            </svg>

          </div>
          <div class="grid-compass">
            <div class="compass-cell compass-sw"></div>
            <div class="compass-cell compass-s">北</div>
            <div class="compass-cell compass-se"></div>
          </div>
        </div>

        <!-- ═══════════════════════════════════════════════════════════════════
             C-7: 底部时间轴（大限 + 流年）
             ═══════════════════════════════════════════════════════════════════ -->
        <div v-if="result.dayun?.items?.length" class="timeline-bar">
          <!-- 大限轴 -->
          <div class="tl-section">
            <span class="tl-label">大限</span>
            <div class="tl-track">
              <button v-for="(d, i) in result.dayun.items" :key="d.ganzhi"
                      :class="['tl-item tl-dayun', {
                        'tl-current': currentDayun?.ganzhi === d.ganzhi && selectedDaxianIdx === -1,
                        'tl-selected': selectedDaxianIdx === i
                      }]"
                      @click="selectedDaxianIdx = selectedDaxianIdx === i ? -1 : i"
                      :title="`${d.ganzhi} (${d.start_year}年起)`">
                <span class="tl-gz">{{ d.ganzhi }}</span>
                <span class="tl-age">{{ d.start_age }}~{{ d.end_age }}岁</span>
                <span class="tl-year-info">{{ d.start_year }}年</span>
              </button>
            </div>
          </div>
          <!-- 流年轴 -->
          <div class="tl-section">
            <span class="tl-label">流年</span>
            <select v-model="selectedLiunianYear" class="tl-select">
              <option v-for="yr in allLiunianYears" :key="yr" :value="yr">{{ yr }}年</option>
            </select>
            <div class="tl-track tl-liunian">
              <button v-for="yr in liunianYears" :key="yr"
                      :class="['tl-item tl-year', { 'tl-current': yr === currentYear, 'tl-selected': yr === selectedLiunianYear }]"
                      @click="selectedLiunianYear = yr"
                      :title="`${yr}年 · ${yr - year}岁`">
                <span class="tl-yr-num">{{ yr }}</span>
                <span class="tl-yr-age">{{ yr - year }}岁</span>
              </button>
            </div>
            <div class="tl-nav">
              <button class="tl-nav-btn" @click="selectedLiunianYear--">◀</button>
              <button class="tl-nav-btn" @click="selectedLiunianYear++">▶</button>
            </div>
          </div>
        </div>

        <!-- 宫位详情面板 -->
        <transition name="slide">
          <div v-if="selectedPalace" class="palace-detail card">
            <div class="detail-header">
              <h3>{{ selectedPalace.name }}
                <span class="detail-branch">{{ selectedPalace.branch }}</span>
              </h3>
              <button class="close-btn" @click="selectedPalace = null">✕</button>
            </div>
            <div class="detail-layout">
              <div class="detail-left">
                <div v-if="selectedPalace.main_stars.length" class="detail-stars">
                  <span v-for="s in selectedPalace.main_stars" :key="s.name" class="detail-star"
                        @mouseenter="showStarTooltip(s.name, $event)"
                        @mouseleave="hideStarTooltip">
                    <b class="star-name-hover">{{ s.name }}</b>
                    <button class="star-fav-btn" :class="{ 'starred': isStarStarred(s.name) }"
                            @click.stop="toggleStarStar(s.name)" :title="isStarStarred(s.name) ? '取消关注' : '关注此星'">
                      {{ isStarStarred(s.name) ? '♥' : '♡' }}
                    </button>
                    <span class="star-br">{{ s.brightness }}</span>
                    <span v-if="s.transforms.length" class="star-tf">
                      {{ s.transforms.join(' ') }}
                    </span>
                  </span>
                </div>

                <div v-if="Object.keys(selectedPalace.flying_out || {}).length" class="detail-flying detail-panel">
                  <span class="detail-sec-label">飞出四化：</span>
                  <span v-for="(val, star) in selectedPalace.flying_out" :key="star"
                        class="pc-tf detail-tf" :style="tfColorStyle(val)">{{ star }}{{ val.slice(1) }}</span>
                </div>

                <div v-if="selectedPalace.analysis_tags?.length" class="detail-tags detail-panel">
                  <span v-for="tag in selectedPalace.analysis_tags" :key="tag" class="detail-tag">{{ tag }}</span>
                </div>

                <div v-if="selectedPalace.xiaoxian_ages?.length || selectedPalace.opposition_name" class="detail-shens detail-panel">
                  <span v-if="selectedPalace.xiaoxian_ages?.length" class="shen-item">
                    小限年龄：<b>{{ selectedPalace.xiaoxian_ages.join('、') }}</b>
                  </span>
                  <span v-if="selectedPalace.opposition_name" class="shen-item">
                    对宫：<b>{{ selectedPalace.opposition_name }}</b>
                  </span>
                </div>

                <div v-if="selectedPalace.changsheng" class="detail-shens detail-panel">
                  <span class="shen-item">长生：<b>{{ selectedPalace.changsheng }}</b></span>
                  <span v-if="selectedPalace.jiangqian_star" class="shen-item">将前：<b>{{ selectedPalace.jiangqian_star }}</b></span>
                  <span v-if="selectedPalace.suiqian_star" class="shen-item">岁前：<b>{{ selectedPalace.suiqian_star }}</b></span>
                </div>

                <div v-if="selectedPalace.dayun_boshi && Object.keys(selectedPalace.dayun_boshi).length" class="detail-shens detail-panel">
                  <span class="shen-item">大运博士星：</span>
                  <span v-for="(branch, star) in selectedPalace.dayun_boshi" :key="star" class="boshi-tag">
                    {{ star }}·{{ branch }}
                  </span>
                </div>

                <div v-if="starredStarsDistribution.length" class="detail-starred-stars detail-panel">
                  <span class="shen-item">关注星曜分布：</span>
                  <span v-for="item in starredStarsDistribution" :key="item.star" class="starred-star-item">
                    <b>{{ item.star }}</b>在{{ item.palaces.join('、') }}
                  </span>
                </div>
              </div>

              <div class="detail-right detail-panel">
                <p v-if="selectedPalace.conclusion" class="detail-conclusion">
                  {{ selectedPalace.conclusion }}
                </p>
                <p v-if="selectedPalace.explanation" class="detail-explanation">
                  {{ selectedPalace.explanation }}
                </p>
                <p v-if="selectedPalace.suggestion" class="detail-suggestion">
                  💡 {{ selectedPalace.suggestion }}
                </p>
                <p v-else-if="selectedPalace.analysis" class="detail-explanation">
                  {{ selectedPalace.analysis }}
                </p>
              </div>
            </div>
          </div>
        </transition>
      </section>

      <!-- Tab: 摘要 -->
      <section v-if="activeTab === 'summary'" class="tab-panel">
        <div class="summary-full card">
          <h3 class="section-title">命盘综述</h3>
          <p v-if="result.summary" class="summary-text">{{ result.summary }}</p>

          <div v-if="summaryQuickFacts.length" class="summary-quick-facts">
            <div v-for="item in summaryQuickFacts" :key="item.label" class="sqf-item">
              <span class="sqf-label">{{ item.label }}</span>
              <span class="sqf-value">{{ item.value }}</span>
            </div>
          </div>

          <div v-if="summaryInsightTags.length" class="summary-insights">
            <span v-for="tag in summaryInsightTags" :key="tag" class="summary-insight-tag">{{ tag }}</span>
          </div>

          <!-- 关键结论卡 -->
          <div v-if="summaryKeyConclusions.length" class="summary-key-conclusions">
            <div v-for="item in summaryKeyConclusions" :key="item.title"
                 :class="['skc-item', `skc-${item.type}`]">
              <div class="skc-head">
                <span class="skc-title">{{ item.title }}</span>
                <span class="skc-tag">{{ item.tag }}</span>
              </div>
              <p class="skc-content">{{ item.content }}</p>
            </div>
          </div>

          <!-- 命盘要点 -->
          <div class="summary-highlights">
            <div class="sh-item">
              <span class="sh-label">五行局</span>
              <span class="sh-value" :style="{ color: JU_COLORS[result.wuxing_ju] }">{{ result.wuxing_ju_name }}</span>
            </div>
            <div class="sh-item">
              <span class="sh-label">命宫</span>
              <span class="sh-value">{{ result.life_palace_gz }}</span>
            </div>
            <div class="sh-item">
              <span class="sh-label">身宫</span>
              <span class="sh-value">{{ result.body_palace_gz }}</span>
            </div>
            <div class="sh-item">
              <span class="sh-label">命主</span>
              <span class="sh-value">{{ result.life_ruler_star || '-' }}</span>
            </div>
            <div class="sh-item">
              <span class="sh-label">身主</span>
              <span class="sh-value">{{ result.body_ruler_star || '-' }}</span>
            </div>
            <div v-if="result.dayun" class="sh-item">
              <span class="sh-label">起运</span>
              <span class="sh-value">{{ result.dayun.start_age_text || result.dayun.start_age + '岁' }}</span>
            </div>
          </div>
          
          <!-- 四柱八字详情 -->
          <div v-if="baziDetails" class="bazi-detail-section card">
            <div class="bazi-head">
              <h3 class="section-title">四柱八字详情</h3>
            </div>

            <!-- 菜单导航 -->
            <div class="bazi-menu-nav">
              <button v-for="(label, key) in baziMenuItems" :key="key"
                      :class="['bazi-menu-btn', { active: baziMenuActive === key }]"
                      @click="baziMenuActive = key as any">
                {{ label }}
              </button>
              <button class="bazi-copy-btn" @click="copyBaziSectionSummary">
                {{ baziCopyDone ? '✓ 已复制' : '复制本节摘要' }}
              </button>
            </div>

            <!-- 菜单内容面板 -->
            <div class="bazi-content-panels">
              <!-- 1.1 生辰数据 -->
              <div v-if="baziMenuActive === 'shengchen'" class="bazi-panel">
                <div class="bazi-info-grid">
                  <div class="bazi-info-item">
                    <span class="bazi-label">出生日期</span>
                    <span class="bazi-value">{{ result.birth_solar }}</span>
                  </div>
                  <div class="bazi-info-item">
                    <span class="bazi-label">农历日期</span>
                    <span class="bazi-value">{{ result.lunar.lunar_year }}年{{ result.lunar.is_leap_month ? '闰' : '' }}{{ result.lunar.lunar_month }}月{{ result.lunar.lunar_day }}日</span>
                  </div>
                  <div class="bazi-info-item">
                    <span class="bazi-label">出生时刻</span>
                    <span class="bazi-value">{{ result.lunar.hour_branch }}时</span>
                  </div>
                  <div class="bazi-info-item">
                    <span class="bazi-label">性别</span>
                    <span class="bazi-value">{{ result.gender }}</span>
                  </div>
                  <div v-if="result.true_solar_time" class="bazi-info-item">
                    <span class="bazi-label">真太阳时</span>
                    <span class="bazi-value">{{ result.true_solar_time }}</span>
                  </div>
                </div>
              </div>

              <!-- 1.2 四柱基础 -->
              <div v-if="baziMenuActive === 'sizhu'" class="bazi-panel">
                <div class="bazi-grid">
                  <div class="bazi-col">
                    <div class="bazi-col-header">年柱</div>
                    <div class="bazi-item">
                      <div class="bazi-gz" title="天干">
                        <span class="bazi-char">{{ baziDetails.year.stem }}</span>
                        <span class="bazi-meaning" v-if="baziDetails.year.stemInfo">
                          {{ baziDetails.year.stemInfo.element }}·{{ baziDetails.year.stemInfo.yin_yang }}
                        </span>
                      </div>
                      <div class="bazi-gz" title="地支">
                        <span class="bazi-char">{{ baziDetails.year.branch }}</span>
                        <span class="bazi-meaning" v-if="baziDetails.year.branchInfo">
                          {{ baziDetails.year.branchInfo.zodiac }}·{{ baziDetails.year.branchInfo.element }}
                        </span>
                      </div>
                    </div>
                    <div v-if="baziDetails.year.stemInfo || baziDetails.year.branchInfo" class="bazi-meaning-text">
                      <p v-if="baziDetails.year.stemInfo" class="bazi-meaning-line">
                        <b>{{ baziDetails.year.stem }}</b>：{{ baziDetails.year.stemInfo.meaning }}
                      </p>
                      <p v-if="baziDetails.year.branchInfo" class="bazi-meaning-line">
                        <b>{{ baziDetails.year.branch }}</b>：{{ baziDetails.year.branchInfo.meaning }}
                      </p>
                    </div>
                  </div>

                  <div class="bazi-col">
                    <div class="bazi-col-header">
                      月柱
                      <span v-if="baziDetails.month.isJieqi" class="bazi-jieqi-badge">节气</span>
                    </div>
                    <div class="bazi-item">
                      <div class="bazi-gz" title="天干">
                        <span class="bazi-char">{{ baziDetails.month.stem }}</span>
                        <span class="bazi-meaning" v-if="baziDetails.month.stemInfo">
                          {{ baziDetails.month.stemInfo.element }}·{{ baziDetails.month.stemInfo.yin_yang }}
                        </span>
                      </div>
                      <div class="bazi-gz" title="地支">
                        <span class="bazi-char">{{ baziDetails.month.branch }}</span>
                        <span class="bazi-meaning" v-if="baziDetails.month.branchInfo">
                          {{ baziDetails.month.branchInfo.zodiac }}·{{ baziDetails.month.branchInfo.element }}
                        </span>
                      </div>
                    </div>
                    <div v-if="baziDetails.month.stemInfo || baziDetails.month.branchInfo" class="bazi-meaning-text">
                      <p v-if="baziDetails.month.stemInfo" class="bazi-meaning-line">
                        <b>{{ baziDetails.month.stem }}</b>：{{ baziDetails.month.stemInfo.meaning }}
                      </p>
                      <p v-if="baziDetails.month.branchInfo" class="bazi-meaning-line">
                        <b>{{ baziDetails.month.branch }}</b>：{{ baziDetails.month.branchInfo.meaning }}
                      </p>
                    </div>
                  </div>

                  <div class="bazi-col">
                    <div class="bazi-col-header">日柱</div>
                    <div class="bazi-item">
                      <div class="bazi-gz" title="天干">
                        <span class="bazi-char">{{ baziDetails.day.stem }}</span>
                        <span class="bazi-meaning" v-if="baziDetails.day.stemInfo">
                          {{ baziDetails.day.stemInfo.element }}·{{ baziDetails.day.stemInfo.yin_yang }}
                        </span>
                      </div>
                      <div class="bazi-gz" title="地支">
                        <span class="bazi-char">{{ baziDetails.day.branch }}</span>
                        <span class="bazi-meaning" v-if="baziDetails.day.branchInfo">
                          {{ baziDetails.day.branchInfo.zodiac }}·{{ baziDetails.day.branchInfo.element }}
                        </span>
                      </div>
                    </div>
                    <div v-if="baziDetails.day.stemInfo || baziDetails.day.branchInfo" class="bazi-meaning-text">
                      <p v-if="baziDetails.day.stemInfo" class="bazi-meaning-line">
                        <b>{{ baziDetails.day.stem }}</b>：{{ baziDetails.day.stemInfo.meaning }}
                      </p>
                      <p v-if="baziDetails.day.branchInfo" class="bazi-meaning-line">
                        <b>{{ baziDetails.day.branch }}</b>：{{ baziDetails.day.branchInfo.meaning }}
                      </p>
                    </div>
                  </div>

                  <div class="bazi-col">
                    <div class="bazi-col-header">时柱</div>
                    <div class="bazi-item">
                      <div class="bazi-gz" title="天干">
                        <span class="bazi-char">{{ baziDetails.hour.stem }}</span>
                        <span class="bazi-meaning" v-if="baziDetails.hour.stemInfo">
                          {{ baziDetails.hour.stemInfo.element }}·{{ baziDetails.hour.stemInfo.yin_yang }}
                        </span>
                      </div>
                      <div class="bazi-gz" title="地支">
                        <span class="bazi-char">{{ baziDetails.hour.branch }}</span>
                        <span class="bazi-meaning" v-if="baziDetails.hour.branchInfo">
                          {{ baziDetails.hour.branchInfo.zodiac }}·{{ baziDetails.hour.branchInfo.element }}
                        </span>
                      </div>
                    </div>
                    <div v-if="baziDetails.hour.stemInfo || baziDetails.hour.branchInfo" class="bazi-meaning-text">
                      <p v-if="baziDetails.hour.stemInfo" class="bazi-meaning-line">
                        <b>{{ baziDetails.hour.stem }}</b>：{{ baziDetails.hour.stemInfo.meaning }}
                      </p>
                      <p v-if="baziDetails.hour.branchInfo" class="bazi-meaning-line">
                        <b>{{ baziDetails.hour.branch }}</b>：{{ baziDetails.hour.branchInfo.meaning }}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 1.3 日主与十神 -->
              <div v-if="baziMenuActive === 'ribuzhu' && shiShenAnalyze" class="bazi-panel">
                <div class="bazi-daymaster">
                  <h5 class="sec-label">日主（日元）</h5>
                  <div class="bazi-dm-info">
                    <div class="bazi-dm-stem">
                      <span class="bazi-dm-char">{{ shiShenAnalyze.dayMaster }}</span>
                      <span class="bazi-dm-text">日主</span>
                    </div>
                    <div class="bazi-dm-desc">{{ baziDetails?.day.stemInfo?.meaning }}</div>
                  </div>
                  <h5 class="sec-label" style="margin-top:var(--sp-3)">十神关系</h5>
                  <div class="shishen-grid">
                    <template v-for="stem in ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']" :key="stem">
                      <div v-if="shiShenAnalyze.relations[stem]" class="shishen-card">
                        <span class="shishen-stem">{{ stem }}</span>
                        <span class="shishen-relation">{{ shiShenAnalyze.relations[stem] }}</span>
                      </div>
                    </template>
                  </div>
                </div>
              </div>

              <!-- 1.4 五行分析 -->
              <div v-if="baziMenuActive === 'wuxing'" class="bazi-panel">
                <div class="bazi-wuxing-summary">
                  <h5 class="sec-label">五行分布</h5>
                  <div class="bazi-wuxing-grid">
                    <div class="bazi-wx-item" v-for="element in ['木', '火', '土', '金', '水']" :key="element"
                         :class="{ 'bazi-wx-active': baziWuxingCount(element) > 0 }">
                      <span class="bazi-wx-name">{{ element }}</span>
                      <span class="bazi-wx-count">{{ baziWuxingCount(element) }}</span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 1.5 藏干/纳音/生肖 -->
              <div v-if="baziMenuActive === 'canggan' && cangganNayin" class="bazi-panel">
                <div class="canggan-grid">
                  <div v-for="(item, key) in cangganNayin" :key="key" class="canggan-col">
                    <div class="canggan-header">{{ ['年', '月', '日', '时'][['year', 'month', 'day', 'hour'].indexOf(key)] }}柱</div>
                    <div class="canggan-item">
                      <div v-if="item.canggan" class="canggan-cg">
                        <span class="canggan-label">藏干</span>
                        <span class="canggan-main">{{ item.canggan.main }}</span>
                        <span v-if="item.canggan.aux1" class="canggan-aux">{{ item.canggan.aux1 }}</span>
                        <span v-if="item.canggan.aux2" class="canggan-aux">{{ item.canggan.aux2 }}</span>
                      </div>
                      <div v-if="item.nayin" class="canggan-ny">
                        <span class="canggan-label">纳音</span>
                        <span class="canggan-value">{{ item.nayin }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 1.6 神煞与定位 -->
              <div v-if="baziMenuActive === 'shenshai'" class="bazi-panel">
                <h5 class="sec-label">神煞与定位</h5>
                <div v-if="baziShenshaList.length" class="bazi-simple-list">
                  <div v-for="item in baziShenshaList" :key="item.name + item.reason" class="bazi-simple-card">
                    <div class="bsc-head">
                      <span class="bsc-name">{{ item.name }}</span>
                      <span :class="['bsc-badge', item.level === '吉' ? 'ok' : item.level === '中' ? 'mid' : 'warn']">{{ item.level }}</span>
                    </div>
                    <p class="bsc-sub">落点：{{ item.hit.join('、') }}</p>
                    <p class="bsc-text">{{ item.reason }}</p>
                  </div>
                </div>
                <p v-else class="muted">当前命盘未检出显著神煞组合。</p>
              </div>

              <!-- 1.7 冲合刑破 -->
              <div v-if="baziMenuActive === 'chonghehexpo'" class="bazi-panel">
                <h5 class="sec-label">干支关系分析</h5>
                <div class="bazi-rel-wrap">
                  <div class="bazi-rel-col">
                    <h6 class="bazi-mini-title">地支关系</h6>
                    <div v-if="baziRelationAnalyze.branchRelations.length" class="bazi-simple-list">
                      <div v-for="(r, idx) in baziRelationAnalyze.branchRelations" :key="'b'+idx" class="bazi-rel-item">
                        <span class="bri-type">{{ r.type }}</span>
                        <span class="bri-pair">{{ r.a }} × {{ r.b }}</span>
                        <span class="bri-pillars">{{ r.pillars }}</span>
                      </div>
                    </div>
                    <p v-else class="muted">地支关系以平和为主。</p>
                  </div>
                  <div class="bazi-rel-col">
                    <h6 class="bazi-mini-title">天干关系</h6>
                    <div v-if="baziRelationAnalyze.stemRelations.length" class="bazi-simple-list">
                      <div v-for="(r, idx) in baziRelationAnalyze.stemRelations" :key="'s'+idx" class="bazi-rel-item">
                        <span class="bri-type">{{ r.type }}</span>
                        <span class="bri-pair">{{ r.a }} × {{ r.b }}</span>
                        <span class="bri-pillars">{{ r.pillars }}</span>
                      </div>
                    </div>
                    <p v-else class="muted">天干关系以平衡为主。</p>
                  </div>
                </div>
              </div>

              <!-- 1.8 格局判定与用神 -->
              <div v-if="baziMenuActive === 'geju'" class="bazi-panel">
                <h5 class="sec-label">格局判定与用神</h5>
                <div v-if="baziGejuYongshen" class="bazi-simple-card">
                  <div class="bsc-head">
                    <span class="bsc-name">{{ baziGejuYongshen.gejuName }}</span>
                    <span class="bsc-badge ok">主导：{{ baziGejuYongshen.dominant }}</span>
                  </div>
                  <p class="bsc-text">{{ baziGejuYongshen.rationale }}</p>
                  <div class="bazi-tags-row">
                    <span class="btr-label">宜：</span>
                    <span v-for="x in baziGejuYongshen.favor" :key="'f'+x" class="btr-tag good">{{ x }}</span>
                  </div>
                  <div class="bazi-tags-row">
                    <span class="btr-label">慎：</span>
                    <span v-for="x in baziGejuYongshen.avoid" :key="'a'+x" class="btr-tag bad">{{ x }}</span>
                  </div>
                </div>
                <p v-else class="muted">暂无足够数据进行格局判定。</p>
              </div>

              <!-- 1.9 大运/流年/流月 -->
              <div v-if="baziMenuActive === 'dayun'" class="bazi-panel">
                <h5 class="sec-label">大运 / 流年 / 流月</h5>
                <div class="bazi-simple-card">
                  <p class="bsc-sub">当前大运：<b>{{ baziLuckOverview.currentDayun || '未定位' }}</b></p>
                  <p class="bsc-sub">流年：<b>{{ baziLuckOverview.liunianYear || '-' }}</b> {{ baziLuckOverview.liunianGz || '' }}</p>
                </div>
                <div v-if="baziLuckOverview.dayun.length" class="bazi-timeline">
                  <div v-for="d in baziLuckOverview.dayun" :key="d.idx + d.ganzhi"
                       :class="['btl-item', { cur: d.isCurrent, active: baziDayunFocusDetail?.idx === d.idx }]"
                       @click="baziDayunFocusIdx = d.rawIdx">
                    <div class="btl-gz">{{ d.ganzhi }}</div>
                    <div class="btl-age">{{ d.startAge }}-{{ d.endAge }}岁</div>
                    <div class="btl-year">{{ d.startYear }}年起</div>
                  </div>
                </div>

                <div v-if="baziDayunFocusDetail" class="bazi-simple-card bazi-dayun-detail">
                  <div class="bsc-head">
                    <span class="bsc-name">第{{ baziDayunFocusDetail.idx }}步大运 · {{ baziDayunFocusDetail.ganzhi }}</span>
                    <span class="bsc-badge mid">{{ baziDayunFocusDetail.startAge }}-{{ baziDayunFocusDetail.endAge }}岁</span>
                  </div>
                  <p class="bsc-sub">起始年份：{{ baziDayunFocusDetail.startYear || '未知' }}<span v-if="baziDayunFocusDetail.tenGod">｜十神：{{ baziDayunFocusDetail.tenGod }}</span></p>
                  <p v-if="baziDayunFocusDetail.narrative" class="bsc-text">{{ baziDayunFocusDetail.narrative }}</p>
                  <p v-else class="bsc-text">此步大运建议结合流年与流月同步观察，重点关注阶段性机会与风险管理。</p>
                </div>

                <div v-if="baziLuckOverview.liuyue.length" class="bazi-month-grid">
                  <div v-for="m in baziLuckOverview.liuyue" :key="m.month"
                       :class="['bmg-item', { related: (baziRelatedLiuyueMap[m.month] || 0) > 0 }]">
                    <span class="bmg-month">{{ m.monthName }}</span>
                    <span class="bmg-gz">{{ m.monthGz || '-' }}</span>
                    <span class="bmg-palace">{{ m.palace || '-' }}</span>
                    <span v-if="(baziRelatedLiuyueMap[m.month] || 0) > 0" class="bmg-link">同星{{ baziRelatedLiuyueMap[m.month] }}个</span>
                  </div>
                </div>
                <p v-if="baziFocusedDayunSihuaStars.length" class="bsc-sub" style="margin-top:8px">
                  联动依据：已高亮与该步大运四化同星的流月（{{ baziFocusedDayunSihuaStars.join('、') }}）。
                </p>
              </div>

              <!-- 1.10 十神宫位用法 -->
              <div v-if="baziMenuActive === 'shishen'" class="bazi-panel">
                <h5 class="sec-label">十神宫位用法</h5>
                <div v-if="baziTenGodUsage.length" class="bazi-simple-list">
                  <div v-for="item in baziTenGodUsage" :key="item.pillar" class="bazi-simple-card">
                    <div class="bsc-head">
                      <span class="bsc-name">{{ item.pillar }}</span>
                      <span class="bsc-badge mid">{{ item.stem }} → {{ item.tenGod }}</span>
                    </div>
                    <p class="bsc-text">{{ item.interpretation }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
<!-- analysis 维度解读 -->
          <div v-if="result.analysis && Object.keys(result.analysis).length" class="analysis-dimensions">
            <h4 class="sec-label" style="margin-top: var(--sp-4)">各维度详解</h4>
            <div class="dimension-grid">
              <div v-for="(text, domain) in result.analysis" :key="domain" class="dimension-item">
                <span class="dimension-label">{{ domain }}</span>
                <p class="dimension-text">{{ text }}</p>
              </div>
            </div>
          </div>

          <!-- 命宫主星 -->
          <div v-if="lifePalaceMainStars.length" class="stars-section">
            <h4 class="sec-label">命宫主星</h4>
            <div class="stars-tags">
              <span v-for="s in lifePalaceMainStars" :key="s.name" class="star-tag" :class="{ 'lucky': s.brightness_val >= 3, 'neutral': s.brightness_val === 2, 'unlucky': s.brightness_val <= 1 }">
                {{ s.name }} <small>{{ s.brightness }}</small>
              </span>
            </div>
          </div>

          <!-- 命宫辅星 -->
          <div v-if="lifePalaceAuxStars.length" class="stars-section">
            <h4 class="sec-label">命宫辅曜</h4>
            <div class="stars-tags">
              <span v-for="s in lifePalaceAuxStars" :key="s" class="star-tag neutral">{{ s }}</span>
            </div>
          </div>
          
          <!-- 四化追踪 -->
          <div v-if="sihuaPathList.length" class="sihua-tracking-section">
            <h4 class="sec-label">命盘四化 <span class="count-badge">{{ sihuaPathList.length }}</span></h4>
            <div class="sihua-track-grid">
              <div v-for="(paths, type) in sihuaByType" :key="type" class="sihua-track-col">
                <div :class="['stc-header', `stc-${type}`]">
                  <span class="stc-type">{{ type }}</span>
                  <span class="stc-count">{{ paths.length }}</span>
                </div>
                <div class="stc-list">
                  <div v-for="p in paths" :key="`${p.star}-${p.source}`" class="stc-item"
                       @click="selectPalaceByIndex(p.sourcePalaceIdx)">
                    <span class="stc-star">{{ p.star }}</span>
                    <span class="stc-arrow">→</span>
                    <span class="stc-palace">{{ p.source }}</span>
                  </div>
                  <div v-if="paths.length === 0" class="stc-empty">无</div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 星曜分布图 -->
          <div v-if="starDistribution.length" class="star-distribution-section">
            <h4 class="sec-label">十二宫星曜分布</h4>
            <div class="star-dist-chart">
              <div v-for="d in starDistribution" :key="d.palaceIdx" class="sdc-bar-wrap"
                   @click="selectPalaceByIndex(d.palaceIdx)">
                <div class="sdc-bar" 
                     :style="{ height: (d.total / maxStarsInPalace * 60 + 20) + 'px' }">
                  <div class="sdc-main" :style="{ height: (d.mainCount / d.total * 100) + '%' }"></div>
                  <div class="sdc-aux" :style="{ height: (d.auxCount / d.total * 100) + '%' }"></div>
                  <span class="sdc-count">{{ d.total }}</span>
                </div>
                <div class="sdc-label">{{ d.palaceName.replace('宫', '') }}</div>
                <div class="sdc-markers">
                  <span v-if="d.hasLu" class="sdc-lu">禄</span>
                  <span v-if="d.hasJi" class="sdc-ji">忌</span>
                </div>
              </div>
            </div>
            <div class="sdc-legend">
              <span class="sdc-leg-item"><span class="sdc-leg-main"></span>主星</span>
              <span class="sdc-leg-item"><span class="sdc-leg-aux"></span>辅星</span>
            </div>
          </div>
          
          <!-- 五行分布图 -->
          <div v-if="wuxingDistribution.length" class="wuxing-distribution-section">
            <h4 class="sec-label">命盘五行分布</h4>
            <div class="wuxing-dist-chart">
              <div v-for="wx in wuxingDistribution" :key="wx.element" class="wdc-bar-wrap">
                <div class="wdc-bar" 
                     :style="{ 
                       height: (wx.count / maxWuxingCount * 50 + 16) + 'px',
                       background: `linear-gradient(180deg, ${wx.color} 0%, ${wx.color}88 100%)`
                     }">
                  <span class="wdc-count">{{ wx.count }}</span>
                </div>
                <div class="wdc-label" :style="{ color: wx.color }">{{ wx.element }}</div>
                <div v-if="wx.stars.length" class="wdc-stars" :title="wx.stars.join('、')">
                  {{ wx.stars.slice(0, 2).join('、') }}{{ wx.stars.length > 2 ? '...' : '' }}
                </div>
              </div>
            </div>
            <div class="wuxing-summary">
              <span v-if="result.wuxing_ju_name" class="ws-item">
                五行局：<b :style="{ color: JU_COLORS[result.wuxing_ju] }">{{ result.wuxing_ju_name }}</b>
              </span>
            </div>
          </div>
          
          <!-- 星曜组合提示 -->
          <div v-if="detectedCombos.length" class="star-combos-section">
            <h4 class="sec-label">星曜组合提示 <span class="count-badge">{{ detectedCombos.length }}</span></h4>
            <div class="star-combos-grid">
              <div v-for="(combo, idx) in detectedCombos" :key="`${combo.name}-${idx}`"
                   :class="['combo-card', `combo-${combo.type}`]">
                <div class="combo-header">
                  <span class="combo-name">{{ combo.name }}</span>
                  <span class="combo-palace">{{ combo.palace }}</span>
                </div>
                <div class="combo-stars">
                  <span v-for="s in combo.stars" :key="s" class="combo-star">{{ s }}</span>
                </div>
                <p class="combo-desc">{{ combo.desc }}</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Tab: 逐宫解读 -->
      <section v-if="activeTab === 'palaces'" class="tab-panel">
        <!-- 宫位统计与筛选 -->
        <div class="palaces-toolbar">
          <div class="palaces-stats">
            <span class="ps-item">共 <b>{{ palacesStats.total }}</b> 宫</span>
            <span class="ps-item">有主星 <b>{{ palacesStats.withMain }}</b></span>
            <span class="ps-item">有解读 <b>{{ palacesStats.withConclusion }}</b></span>
          </div>
          <div class="palaces-filter">
            <input v-model="palaceFilter" type="text" placeholder="搜索宫位/星曜..." class="palace-search-input" />
            <button v-if="palaceFilter" class="palace-clear-btn" @click="palaceFilter = ''">✕</button>
          </div>
        </div>
        
        <div class="palaces-quick-nav">
          <button v-for="p in result.palaces" :key="p.index" 
                  :class="['pqn-btn', { 'pqn-active': palaceFilter === p.name }]"
                  @click="palaceFilter = palaceFilter === p.name ? '' : p.name">
            {{ p.name.replace('宫', '') }}
          </button>
        </div>
        
        <div class="palaces-interpretations-grouped">
          <div v-for="group in groupedFilteredPalaces" :key="group.key" class="pig-group card">
            <button class="pig-head" @click="togglePalaceGroup(group.key)">
              <span class="pig-title">{{ group.title }}</span>
              <span class="pig-count">{{ group.items.length }} 宫</span>
              <span class="pig-toggle">{{ palaceGroupExpanded[group.key] ? '收起' : '展开' }}</span>
            </button>

            <div v-if="palaceGroupExpanded[group.key]" class="palaces-interpretations">
              <div v-for="p in group.items" :key="p.index" class="palace-interp-card card">
                <div class="pi-header">
                  <span class="pi-name">{{ p.name }}</span>
                  <span class="pi-gz">{{ p.stem }}{{ p.branch }}</span>
                  <span v-if="p.name.includes('命')" class="pi-tag life">命宫</span>
                  <span v-if="p.name.includes('身')" class="pi-tag body">身宫</span>
                </div>

                <div v-if="p.main_stars.length" class="pi-stars">
                  <span v-for="s in p.main_stars" :key="s.name" class="pi-star">
                    <b>{{ s.name }}</b>
                    <span class="pi-br">{{ s.brightness }}</span>
                    <span v-if="s.transforms.length" class="pi-tf">{{ s.transforms.join(' ') }}</span>
                  </span>
                </div>

                <div v-if="p.analysis_tags?.length" class="pi-tags">
                  <span v-for="tag in p.analysis_tags" :key="tag" class="pi-tag-item">{{ tag }}</span>
                </div>

                <p v-if="p.conclusion" class="pi-conclusion">
                  <strong>结论：</strong>{{ p.conclusion }}
                </p>
                <p v-if="p.explanation" class="pi-explanation">
                  <strong>详解：</strong>{{ p.explanation }}
                </p>
                <p v-if="p.suggestion" class="pi-suggestion">
                  <strong>建议：</strong>{{ p.suggestion }}
                </p>
                <p v-else-if="p.analysis" class="pi-analysis">{{ p.analysis }}</p>
              </div>
            </div>
          </div>
          <p v-if="filteredPalaces.length === 0" class="muted">没有匹配的宫位</p>
        </div>
      </section>

      <!-- Tab: 大运 -->
      <section v-if="activeTab === 'dayun'" class="tab-panel">
        <!-- 大运统计资讯卡 -->
        <div class="dayun-stats-card card">
          <div class="dsc-grid">
            <div class="dsc-item">
              <span class="dsc-label">运行方向</span>
              <span class="dsc-value">{{ result.dayun.forward ? '顺运' : '逆运' }}</span>
            </div>
            <div class="dsc-item">
              <span class="dsc-label">起运年龄</span>
              <span class="dsc-value">{{ result.dayun.start_age }}岁</span>
            </div>
            <div class="dsc-item">
              <span class="dsc-label">居历年限</span>
              <span class="dsc-value">{{ dayunStats.past }}步</span>
            </div>
            <div class="dsc-item">
              <span class="dsc-label">尚待年限</span>
              <span class="dsc-value">{{ dayunStats.future }}步</span>
            </div>
            <div class="dsc-item">
              <span class="dsc-label">共计局数</span>
              <span class="dsc-value">{{ dayunStats.total }}局</span>
            </div>
            <div class="dsc-item">
              <span class="dsc-label">跨度年份</span>
              <span class="dsc-value">{{ dayunStats.startYear }}–{{ dayunStats.endYear }}</span>
            </div>
          </div>
          <!-- 当前大运进度条 -->
          <div v-if="dayunProgress" class="dsc-progress">
            <div class="dsc-prog-head">
              <span class="dsc-prog-title">当前大运：{{ dayunProgress.ganzhi }}</span>
              <span class="dsc-prog-meta">已进 {{ dayunProgress.yearsIn }} 年，剩 {{ dayunProgress.yearsLeft }} 年</span>
            </div>
            <div class="dsc-prog-bar">
              <div class="dsc-prog-fill" :style="{ width: dayunProgress.pct + '%' }"></div>
            </div>
            <div class="dsc-prog-labels">
              <span>起始</span>
              <span>{{ dayunProgress.pct }}%</span>
              <span>终首</span>
            </div>
          </div>
        </div>

        <div class="dayun-toolbar">
          <div class="dayun-summary-bar">
            <p class="dayun-info">
              {{ result.dayun.forward ? '顺运' : '逆运' }}，
              起运 <b>{{ result.dayun.start_age }} 岁</b>
              （{{ result.dayun.start_age_text }}）
            </p>
            <p v-if="result.dayun.items?.length" class="dayun-range">
              大运跨度：<b>{{ result.dayun.items[0]?.start_year }}</b> ~ <b>{{ result.dayun.items[result.dayun.items.length - 1]?.start_year + 9 }}</b> 年
            </p>
          </div>
          <button class="dayun-locate-btn" @click="scrollToCurrentDayun" title="定位到当前大运">
            📍 定位当前
          </button>
        </div>
        
        <!-- 大运时间线 -->
        <div class="dayun-timeline">
          <div class="dt-line"></div>
          <div v-for="(d, idx) in result.dayun.items" :key="d.index"
               :class="['dt-node', { 'dt-cur': d.start_year <= currentYear && (d.start_year + 10) > currentYear, 'dt-past': (d.start_year + 10) <= currentYear }]">
            <div class="dt-marker"></div>
            <div class="dt-label">{{ d.ganzhi }}</div>
            <div class="dt-age">{{ d.start_age }}岁</div>
            <div v-if="d.start_year <= currentYear && (d.start_year + 10) > currentYear" class="dt-cur-badge">当前</div>
          </div>
        </div>
        
        <div class="dayun-list">
          <div v-for="d in result.dayun.items" :key="d.index"
               :class="['dayun-item', {
                 cur: d.start_year <= currentYear && (d.start_year + 10) > currentYear
               }]">
            <span v-if="d.start_year <= currentYear && (d.start_year + 10) > currentYear" class="dayun-cur-badge">当前</span>
            <div class="dayun-gz">{{ d.ganzhi }}</div>
            <div class="dayun-age">{{ d.start_age }}～{{ d.end_age }}岁</div>
            <div class="dayun-year">{{ d.start_year }}年</div>
            <div v-if="Object.keys(d.sihua).length" class="dayun-sihua">
              <span v-for="(val, star) in d.sihua" :key="star"
                    class="sihua-badge">{{ star }}{{ val }}</span>
            </div>
            <div v-if="Object.keys(d.boshi_stars || {}).length" class="dayun-boshi">
              <span v-for="(branch, star) in d.boshi_stars" :key="star" class="boshi-tag">{{ star }}·{{ branch }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Tab: 流年 -->
      <section v-if="activeTab === 'liunian'" class="tab-panel">
        <template v-if="result.liunian">
          <!-- 流年工具栏 -->
          <div class="liunian-toolbar">
            <div class="liunian-year-picker">
              <button class="lyp-btn" @click="selectYearFromPicker(result.liunian.year - 1)" title="上一年">◀</button>
              <button class="lyp-current" @click="showYearPicker = !showYearPicker">
                {{ result.liunian.year }}年
                <span v-if="result.liunian.year === currentYear" class="lyp-cur-badge">今年</span>
              </button>
              <button class="lyp-btn" @click="selectYearFromPicker(result.liunian.year + 1)" title="下一年">▶</button>
              <button v-if="result.liunian.year !== currentYear" class="lyp-reset" @click="selectYearFromPicker(currentYear)" title="回到今年">
                📍 今年
              </button>
            </div>
            <!-- 年份快速选择面板 -->
            <div v-if="showYearPicker" class="year-picker-panel">
              <div class="ypp-header">
                <span>选择年份</span>
                <button class="ypp-close" @click="showYearPicker = false">✕</button>
              </div>
              <div class="ypp-grid">
                <button v-for="yr in yearPickerList" :key="yr"
                        :class="['ypp-item', { 
                          'ypp-selected': yr === result.liunian?.year,
                          'ypp-current': yr === currentYear
                        }]"
                        @click="selectYearFromPicker(yr)">
                  {{ yr }}
                </button>
              </div>
            </div>
          </div>

          <!-- ① 流年英雄头部：干支 + 基本信息 + 评分环 -->
          <div class="liunian-hero card">
            <div class="lnh-left">
              <div class="lnh-gz">
                {{ result.liunian.year_gz }}年
                <span v-if="result.liunian.year === currentYear" class="liunian-cur-badge">今年</span>
              </div>
              <div class="lnh-sub">{{ result.liunian.year }}年</div>
              <div class="lnh-meta">
                <span v-if="result.liunian.life_palace_branch >= 0">
                  流年命宫 <b>{{ BRANCHES[result.liunian.life_palace_branch] }}宫</b>
                </span>
                <span v-if="currentDayunGz">所在大运 <b>{{ currentDayunGz }}</b></span>
              </div>
              <div class="lnh-attrs">
                <div class="la-item">
                  <span class="la-label">年干</span>
                  <span class="la-value">{{ result.liunian.year_gz?.charAt(0) }}</span>
                </div>
                <div class="la-item">
                  <span class="la-label">年支</span>
                  <span class="la-value">{{ result.liunian.year_gz?.charAt(1) }}</span>
                </div>
                <div class="la-item">
                  <span class="la-label">生肖</span>
                  <span class="la-value">{{ BRANCHES.indexOf(result.liunian.year_gz?.charAt(1) || '') >= 0 ? ZODIAC_ANIMALS[BRANCHES.indexOf(result.liunian.year_gz?.charAt(1) || '')] : '-' }}</span>
                </div>
                <div class="la-item">
                  <span class="la-label">太岁</span>
                  <span class="la-value" style="font-size:var(--fs-sm)">{{ result.liunian.year_gz?.charAt(1) }}年</span>
                </div>
              </div>
            </div>
            <!-- 右侧评分环 -->
            <div v-if="result.forecast?.yearly?.score" class="lnh-score-ring">
              <svg viewBox="0 0 80 80" class="score-ring-svg">
                <circle cx="40" cy="40" r="34" fill="none" stroke="var(--surface-2)" stroke-width="7"/>
                <circle cx="40" cy="40" r="34" fill="none"
                        :stroke="forecastScoreColor(result.forecast.yearly.score)"
                        stroke-width="7" stroke-linecap="round"
                        :stroke-dasharray="`${(result.forecast.yearly.score / 100) * 213.6} 213.6`"
                        transform="rotate(-90 40 40)"/>
                <text x="40" y="45" text-anchor="middle" font-size="20" font-weight="bold"
                      :fill="forecastScoreColor(result.forecast.yearly.score)">{{ result.forecast.yearly.score }}</text>
              </svg>
              <div class="score-ring-label">年度评分</div>
            </div>
          </div>

          <!-- ② 年度综合运势详情 -->
          <div v-if="result.forecast?.yearly" class="liunian-forecast-full card">
            <h3 class="section-title">年度运势详情</h3>
            <p v-if="result.forecast.yearly.overall" class="lfy-overall">{{ result.forecast.yearly.overall }}</p>
            <!-- 四维详情：感情/财运/事业/健康 -->
            <div v-if="result.forecast.yearly.details && Object.keys(result.forecast.yearly.details).length" class="lfy-details">
              <div v-for="(text, domain) in result.forecast.yearly.details" :key="String(domain)" class="lfyd-item">
                <span class="lfyd-domain">{{ domain }}</span>
                <span class="lfyd-text">{{ text }}</span>
              </div>
            </div>
            <!-- 重要事件 -->
            <div v-if="result.forecast.yearly.events?.length" class="lfy-events">
              <div v-for="(ev, ei) in result.forecast.yearly.events" :key="ei"
                   :class="['lfye-item', `fye-${ev.level}`]" :title="ev.source || ''">
                <span class="fye-cat">{{ ev.category }}</span>
                <span class="fye-desc">{{ ev.description }}</span>
              </div>
            </div>
            <!-- 年度建议 -->
            <p v-if="result.forecast.yearly.advice" class="lfy-advice">💡 {{ result.forecast.yearly.advice }}</p>
          </div>

          <!-- ③ 流年四化（增强版：显示所在宫位） -->
          <div v-if="liunianSihuaWithPalace.length" class="liunian-sihua-section card">
            <h3 class="section-title">流年四化</h3>
            <div class="liunian-sihua-grid lsg-enhanced">
              <div v-for="item in liunianSihuaWithPalace" :key="item.star" class="liunian-sihua-card lsc-enhanced">
                <div class="lsc-top">
                  <span class="lss-star">{{ item.star }}</span>
                  <span class="lss-tf" :style="tfColorStyle(item.transform)">{{ item.transform }}</span>
                </div>
                <span v-if="item.palaceName" class="lss-palace">{{ item.palaceName }}</span>
              </div>
            </div>
          </div>

          <!-- ④ 十二月评分迷你柱状图 -->
          <div v-if="result.forecast?.monthly?.length" class="liunian-monthly-chart card">
            <h3 class="section-title">十二月运势概览</h3>
            <div class="lmc-bars">
              <div v-for="(m, idx) in result.forecast.monthly" :key="idx"
                   :class="['lmc-col', { 'lmc-cur': result.liunian.year === currentYear && idx + 1 === currentMonth }]">
                <div class="lmc-bar-wrap">
                  <span v-if="m.score" class="lmc-score">{{ m.score }}</span>
                  <div class="lmc-bar"
                       :style="{ height: `${m.score ? Math.max(6, m.score) : 6}%`, background: m.score ? forecastScoreColor(m.score) : 'var(--border)' }">
                  </div>
                </div>
                <div class="lmc-label">{{ m.ganzhi || (idx + 1) + '月' }}</div>
              </div>
            </div>
          </div>

          <!-- ⑤ 当前月高亮（仅当年显示） -->
          <div v-if="result.liunian.year === currentYear && result.forecast?.current_month" class="liunian-curmonth card">
            <div class="lcm-head">
              <span class="lcm-badge">本月</span>
              <span class="lcm-gz">{{ result.forecast.current_month.ganzhi }}</span>
              <span class="lcm-period">{{ result.forecast.current_month.period }}</span>
              <span v-if="result.forecast.current_month.score" class="lcm-score"
                    :style="{ color: forecastScoreColor(result.forecast.current_month.score) }">
                {{ result.forecast.current_month.score }}分
              </span>
            </div>
            <p v-if="result.forecast.current_month.overall" class="lcm-overall">{{ result.forecast.current_month.overall }}</p>
            <div v-if="result.forecast.current_month.details && Object.keys(result.forecast.current_month.details).length" class="lfy-details">
              <div v-for="(text, domain) in result.forecast.current_month.details" :key="String(domain)" class="lfyd-item">
                <span class="lfyd-domain">{{ domain }}</span>
                <span class="lfyd-text">{{ text }}</span>
              </div>
            </div>
            <p v-if="result.forecast.current_month.advice" class="lcm-advice">💡 {{ result.forecast.current_month.advice }}</p>
          </div>

        </template>
        <p v-else class="muted">无流年数据</p>
      </section>

      <!-- Tab: 流月 -->
      <section v-if="activeTab === 'liuyue'" class="tab-panel">
        <div v-if="result.liuyue?.length">
          <!-- 流月工具栏 -->
          <div class="liuyue-toolbar">
            <div class="liuyue-stats">
              <span class="lys-item">共 <b>{{ liuyueSummary.total }}</b> 月</span>
              <span class="lys-item">有四化 <b>{{ liuyueSummary.withSihua }}</b></span>
              <span v-if="liuyueSummary.withForecast" class="lys-item">有运势 <b>{{ liuyueSummary.withForecast }}</b></span>
            </div>
            <button v-if="result.liunian?.year === currentYear" class="liuyue-locate-btn" @click="scrollToCurrentLiuyue" title="定位到本月">
              📍 定位本月
            </button>
          </div>

          <div class="liuyue-summary-cards">
            <div class="lysc-item">
              <span class="lysc-label">运势均分</span>
              <span class="lysc-value" :style="{ color: forecastScoreColor(liuyueSummary.avg || 50) }">{{ liuyueSummary.avg || '-' }}</span>
            </div>
            <div class="lysc-item">
              <span class="lysc-label">重点月份</span>
              <span class="lysc-value">{{ liuyueSummary.riskMonths.length ? liuyueSummary.riskMonths.join('、') : '整体平稳' }}</span>
            </div>
          </div>
          
          <!-- 月份快捷导航 -->
          <div class="liuyue-quick-nav">
            <button v-for="(row, idx) in liuyueRows" :key="row.month.month"
                    :class="['lyq-btn', { 
                      'lyq-cur': row.month.month === currentMonth && result.liunian?.year === currentYear,
                      'lyq-active': expandedLiuyue === idx 
                    }]"
                    @click="expandedLiuyue = expandedLiuyue === idx ? null : idx">
              {{ row.month.month_name?.replace('月', '') || row.month.month }}
            </button>
          </div>
          
          <div class="liuyue-grid">
            <div v-for="(row, idx) in liuyueRows" :key="row.month.month" 
                 :class="['liuyue-item', { 'liuyue-expanded': expandedLiuyue === idx, 'liuyue-cur': row.month.month === currentMonth && result.liunian?.year === currentYear }]"
                 @click="expandedLiuyue = expandedLiuyue === idx ? null : idx">
              <div class="liuyue-head">
                <span class="liuyue-month">{{ row.month.month_name }}</span>
                <span class="liuyue-gz">{{ row.month.month_gz }}</span>
                <span v-if="row.month.month === currentMonth && result.liunian?.year === currentYear" class="liuyue-cur-badge">本月</span>
                <span class="liuyue-expand-icon">{{ expandedLiuyue === idx ? '▴' : '▾' }}</span>
              </div>
              <div class="liuyue-palace">{{ row.month.palace_name }}</div>
              <div v-if="Object.keys(row.month.sihua).length" class="liuyue-sihua">
                <span v-for="(val, star) in row.month.sihua" :key="star"
                      class="pc-tf liuyue-tf" :style="tfColorStyle(val)">{{ star }}{{ val.slice(1) }}</span>
              </div>
              <!-- 展开详情：从forecast.monthly关联运势数据 -->
              <div v-if="expandedLiuyue === idx && row.forecast" class="liuyue-detail">
                <div v-if="row.forecast?.events?.length" class="liuyue-events">
                  <div v-for="(ev, ei) in row.forecast?.events" :key="ei" class="liuyue-event">
                    <span class="liuyue-ev-cat">{{ ev.category }}</span>
                    <span class="liuyue-ev-desc">{{ ev.description }}</span>
                  </div>
                </div>
                <div v-if="row.forecast?.details && Object.keys(row.forecast?.details || {}).length" class="liuyue-dimensions">
                  <div v-for="(text, domain) in row.forecast?.details" :key="domain" class="liuyue-dim">
                    <span class="liuyue-dim-label">{{ domain }}</span>
                    <span class="liuyue-dim-text">{{ text }}</span>
                  </div>
                </div>
                <p v-if="row.forecast?.advice" class="liuyue-advice">💡 {{ row.forecast?.advice }}</p>
                <p v-if="row.forecast?.overall" class="liuyue-overall">{{ row.forecast?.overall }}</p>
                <div v-if="row.forecast?.score" class="liuyue-score">
                  运势评分：<span :style="{ color: forecastScoreColor(row.forecast?.score || 50) }">{{ row.forecast?.score }}分</span>
                </div>
              </div>
              <!-- 无运势数据时显示基本信息 -->
              <div v-else-if="expandedLiuyue === idx" class="liuyue-detail">
                <p class="muted">暂无该月运势详情</p>
              </div>
            </div>
          </div>
        </div>
        <p v-else class="muted">无流月数据</p>
      </section>

      <!-- Tab: 格局 -->
      <section v-if="activeTab === 'patterns'" class="tab-panel">
        <div v-if="result.patterns?.length" class="patterns-list">
          <!-- 格局统计与视图切换 -->
          <div class="pattern-toolbar">
            <div class="pattern-stats">
              <span class="pattern-stat total">共 <b>{{ patternStats.total }}</b> 个格局</span>
              <span v-if="patternStats.high" class="pattern-stat high">上格 <b>{{ patternStats.high }}</b></span>
              <span v-if="patternStats.med" class="pattern-stat med">中格 <b>{{ patternStats.med }}</b></span>
              <span v-if="patternStats.low" class="pattern-stat low">普通 <b>{{ patternStats.low }}</b></span>
            </div>
            <div class="pattern-view-toggle">
              <button :class="['pvt-btn', { active: patternViewMode === 'group' }]" @click="patternViewMode = 'group'">分组</button>
              <button :class="['pvt-btn', { active: patternViewMode === 'list' }]" @click="patternViewMode = 'list'">列表</button>
            </div>
          </div>

          <div v-if="patternHighlights.length" class="pattern-focus-strip">
            <span class="pfs-label">重点格局</span>
            <span
              v-for="item in patternHighlights"
              :key="item.name"
              :class="['pfs-item', item.cls]">
              {{ item.name }}
            </span>
          </div>
          
          <!-- 分组视图 -->
          <template v-if="patternViewMode === 'group'">
            <!-- 上格组 -->
            <div v-if="groupedPatterns.high.length" class="pattern-group pg-high">
              <div class="pg-header">
                <span class="pg-icon">⭐</span>
                <span class="pg-title">上等格局</span>
                <span class="pg-count">{{ groupedPatterns.high.length }}</span>
              </div>
              <div class="pg-items">
                <div v-for="(p, i) in groupedPatterns.high" :key="'h'+i" class="pattern-item level-high">
                  <div class="pattern-header">
                    <span class="pattern-name">{{ p.name }}</span>
                    <span class="pattern-level">{{ p.level }}</span>
                  </div>
                  <p v-if="p.description" class="pattern-desc">{{ p.description }}</p>
                  <div v-if="p.palaces?.length || p.stars?.length" class="pattern-meta">
                    <span v-if="p.palaces?.length" class="pattern-palaces">
                      <span class="meta-label">宫位</span>
                      <span v-for="pal in p.palaces" :key="pal" class="meta-tag palace-tag">{{ pal }}</span>
                    </span>
                    <span v-if="p.stars?.length" class="pattern-stars">
                      <span class="meta-label">星曜</span>
                      <span v-for="star in p.stars" :key="star" class="meta-tag star-tag">{{ star }}</span>
                    </span>
                  </div>
                  <p v-if="p.source" class="pattern-source">📖 {{ p.source }}</p>
                </div>
              </div>
            </div>
            
            <!-- 中格组 -->
            <div v-if="groupedPatterns.med.length" class="pattern-group pg-med">
              <div class="pg-header">
                <span class="pg-icon">✦</span>
                <span class="pg-title">中等格局</span>
                <span class="pg-count">{{ groupedPatterns.med.length }}</span>
              </div>
              <div class="pg-items">
                <div v-for="(p, i) in groupedPatterns.med" :key="'m'+i" class="pattern-item level-med">
                  <div class="pattern-header">
                    <span class="pattern-name">{{ p.name }}</span>
                    <span class="pattern-level">{{ p.level }}</span>
                  </div>
                  <p v-if="p.description" class="pattern-desc">{{ p.description }}</p>
                  <div v-if="p.palaces?.length || p.stars?.length" class="pattern-meta">
                    <span v-if="p.palaces?.length" class="pattern-palaces">
                      <span class="meta-label">宫位</span>
                      <span v-for="pal in p.palaces" :key="pal" class="meta-tag palace-tag">{{ pal }}</span>
                    </span>
                    <span v-if="p.stars?.length" class="pattern-stars">
                      <span class="meta-label">星曜</span>
                      <span v-for="star in p.stars" :key="star" class="meta-tag star-tag">{{ star }}</span>
                    </span>
                  </div>
                  <p v-if="p.source" class="pattern-source">📖 {{ p.source }}</p>
                </div>
              </div>
            </div>
            
            <!-- 普通格组 -->
            <div v-if="groupedPatterns.low.length" class="pattern-group pg-low">
              <div class="pg-header">
                <span class="pg-icon">◆</span>
                <span class="pg-title">一般格局</span>
                <span class="pg-count">{{ groupedPatterns.low.length }}</span>
              </div>
              <div class="pg-items">
                <div v-for="(p, i) in groupedPatterns.low" :key="'l'+i" class="pattern-item level-low">
                  <div class="pattern-header">
                    <span class="pattern-name">{{ p.name }}</span>
                    <span class="pattern-level">{{ p.level }}</span>
                  </div>
                  <p v-if="p.description" class="pattern-desc">{{ p.description }}</p>
                  <div v-if="p.palaces?.length || p.stars?.length" class="pattern-meta">
                    <span v-if="p.palaces?.length" class="pattern-palaces">
                      <span class="meta-label">宫位</span>
                      <span v-for="pal in p.palaces" :key="pal" class="meta-tag palace-tag">{{ pal }}</span>
                    </span>
                    <span v-if="p.stars?.length" class="pattern-stars">
                      <span class="meta-label">星曜</span>
                      <span v-for="star in p.stars" :key="star" class="meta-tag star-tag">{{ star }}</span>
                    </span>
                  </div>
                  <p v-if="p.source" class="pattern-source">📖 {{ p.source }}</p>
                </div>
              </div>
            </div>
          </template>
          
          <!-- 列表视图 -->
          <template v-else>
            <div v-for="(p, i) in sortedPatterns" :key="i"
                 :class="['pattern-item', patternClass(p.level)]">
              <div class="pattern-header">
                <span class="pattern-name">{{ p.name }}</span>
                <span class="pattern-level">{{ p.level }}</span>
              </div>
              <p v-if="p.description" class="pattern-desc">{{ p.description }}</p>
              <div v-if="p.palaces?.length || p.stars?.length" class="pattern-meta">
                <span v-if="p.palaces?.length" class="pattern-palaces">
                  <span class="meta-label">宫位</span>
                  <span v-for="pal in p.palaces" :key="pal" class="meta-tag palace-tag">{{ pal }}</span>
                </span>
                <span v-if="p.stars?.length" class="pattern-stars">
                  <span class="meta-label">星曜</span>
                  <span v-for="star in p.stars" :key="star" class="meta-tag star-tag">{{ star }}</span>
                </span>
              </div>
              <p v-if="p.source" class="pattern-source">📖 {{ p.source }}</p>
            </div>
          </template>
        </div>
        <p v-else class="muted">未命中特定格局</p>
      </section>

      <!-- Tab: 飞星 -->
      <section v-if="activeTab === 'flying' && result.flying" class="tab-panel">
        <!-- 飞星四化落宫汇总 -->
        <div v-if="flyingKeyInsights.length" class="flying-insights-bar">
          <span class="fib-label">落宫</span>
          <div v-for="item in flyingKeyInsights" :key="item.type"
               :class="['fib-item', item.cls]">
            <span class="fib-type">{{ item.type }}</span>
            <span class="fib-arrow">→</span>
            <span class="fib-palaces">{{ item.palaces.join('、') }}</span>
          </div>
        </div>

        <!-- 飞星统计与筛选 -->
        <div class="flying-toolbar">
          <div class="flying-stats">
            <span class="flying-stat">
              自化 <b>{{ result.flying.self_transforms?.length || 0 }}</b>
            </span>
            <span class="flying-stat">
              宫位 <b>{{ result.flying.palaces?.length || 0 }}</b>
            </span>
            <span class="flying-stat">
              接收 <b>{{ Object.keys(result.flying.received || {}).length }}</b>
            </span>
            <span class="flying-stat">
              冲宫 <b>{{ Object.keys(result.flying.chonged || {}).length }}</b>
            </span>
          </div>
          <div class="flying-filter">
            <span class="ff-label">筛选：</span>
            <button :class="['ff-btn', { active: flyingFilter === 'all' }]" @click="flyingFilter = 'all'">全部</button>
            <button :class="['ff-btn ff-lu', { active: flyingFilter === 'lu' }]" @click="flyingFilter = 'lu'">禄</button>
            <button :class="['ff-btn ff-quan', { active: flyingFilter === 'quan' }]" @click="flyingFilter = 'quan'">权</button>
            <button :class="['ff-btn ff-ke', { active: flyingFilter === 'ke' }]" @click="flyingFilter = 'ke'">科</button>
            <button :class="['ff-btn ff-ji', { active: flyingFilter === 'ji' }]" @click="flyingFilter = 'ji'">忌</button>
          </div>
        </div>
        
        <!-- 自化星 -->
        <div v-if="result.flying.self_transforms?.length && flyingFilter === 'all'" class="section-block">
          <h3 class="section-title">
            自化星
            <span class="section-count">{{ result.flying.self_transforms.length }}</span>
          </h3>
          <div class="flying-tags-row">
            <span v-for="s in result.flying.self_transforms" :key="s" class="flying-self-tag">{{ s }}</span>
          </div>
        </div>
        
        <!-- 各宫飞化 -->
        <div class="flying-palaces-grid">
          <div v-for="fp in filteredFlyingPalaces" :key="fp.palace_name" class="flying-palace-card">
            <div class="fp-head">
              <span class="fp-name">{{ fp.palace_name }}</span>
              <span v-if="fp.stem_name" class="fp-stem">{{ fp.stem_name }}</span>
            </div>
            <div v-if="Object.keys(fp.flying_out || {}).length" class="fp-row">
              <span class="fp-label">飞出：</span>
              <span v-for="(t, star) in fp.flying_out" :key="star"
                    class="pc-tf" :style="tfColorStyle(t)">{{ star }}{{ t.slice(1) }}</span>
            </div>
            <div v-if="fp.opposition_palace" class="fp-row fp-opp">
              对宫：<b>{{ fp.opposition_palace }}</b>
            </div>
            <div v-if="fp.self_transforms?.length" class="fp-row">
              <span class="fp-label">自化：</span>
              <span v-for="s in fp.self_transforms" :key="s" class="fp-self-tag">{{ s }}</span>
            </div>
          </div>
        </div>
        <p v-if="filteredFlyingPalaces.length === 0 && flyingFilter !== 'all'" class="muted">没有符合筛选条件的飞化</p>
        
        <!-- 受星汇总 (received) -->
        <div v-if="result.flying.received && Object.keys(result.flying.received).length && flyingFilter === 'all'" class="section-block" style="margin-top:var(--sp-5)">
          <h3 class="section-title">各宫接收四化</h3>
          <div class="flying-received-grid">
            <div v-for="(transforms, palace) in result.flying.received" :key="palace" class="fr-item">
              <span class="fr-palace">{{ palace }}</span>
              <div class="fr-tfs">
                    <span v-for="label in getReceivedTransformLabels(transforms as FlyingReceivedItem)" :key="label"
                      class="pc-tf fr-tf">{{ label }}</span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 冲宫汇总 (chonged) -->
        <div v-if="result.flying.chonged && Object.keys(result.flying.chonged).length && flyingFilter === 'all'" class="section-block" style="margin-top:var(--sp-5)">
          <h3 class="section-title">冲宫关系</h3>
          <div class="flying-received-grid">
            <div v-for="(val, palace) in result.flying.chonged" :key="palace" class="fr-item">
              <span class="fr-palace">{{ palace }}</span>
              <span class="fr-opp">↔ {{ val }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Tab: 运势预测 -->
      <section v-if="activeTab === 'forecast' && result.forecast" class="tab-panel">
        <!-- 运势统计概览 -->
        <div v-if="result.forecast.monthly?.length" class="forecast-stats">
          <div class="forecast-stat-main">
            <span class="fs-label">年均评分</span>
            <span class="fs-value" :style="{ color: forecastScoreColor(forecastStats.avg) }">{{ forecastStats.avg }}</span>
          </div>
          <div class="forecast-stat-dist">
            <span class="fs-item good">吉月 <b>{{ forecastStats.good }}</b></span>
            <span class="fs-item mid">平月 <b>{{ forecastStats.mid }}</b></span>
            <span class="fs-item low">凶月 <b>{{ forecastStats.low }}</b></span>
          </div>
          <div v-if="forecastStats.best" class="forecast-stat-peak">
            <span class="fs-peak best">最佳：{{ forecastStats.best.period?.replace(/\(.+?\)/, '') }} <b>{{ forecastStats.best.score }}分</b></span>
            <span v-if="forecastStats.worst" class="fs-peak worst">注意：{{ forecastStats.worst.period?.replace(/\(.+?\)/, '') }} <b>{{ forecastStats.worst.score }}分</b></span>
          </div>
          <div v-if="forecastRiskMonths.length" class="forecast-risk-tags">
            <span class="frt-label">重点关注</span>
            <span v-for="item in forecastRiskMonths" :key="item" class="frt-item">{{ item }}</span>
          </div>
        </div>

        <div v-if="forecastMonthlyOverview.length" class="forecast-heatmap card">
          <h3 class="section-title">月度评分分布</h3>
          <div class="fhm-grid">
            <button
              v-for="bar in forecastMonthlyOverview"
              :key="bar.index"
              :class="['fhm-item', `fhm-${bar.level}`, { 'fhm-active': expandedForecastMonth === bar.index }]"
              @click="expandedForecastMonth = expandedForecastMonth === bar.index ? null : bar.index"
            >
              <span class="fhm-period">{{ bar.periodShort || `第${bar.index + 1}月` }}</span>
              <span class="fhm-score">{{ bar.score }}</span>
              <span class="fhm-bar"><i :style="{ width: `${bar.score}%` }"></i></span>
            </button>
          </div>
        </div>

        <!-- 流年大运 -->
        <div v-if="result.forecast.yearly" class="forecast-yearly card">
          <div class="fy-head">
            <span class="fy-gz">{{ result.forecast.yearly.ganzhi }}</span>
            <span class="fy-period">{{ result.forecast.yearly.period }}</span>
            <span v-if="result.forecast.yearly.score" class="fy-score"
                  :style="{ color: forecastScoreColor(result.forecast.yearly.score) }">
              {{ result.forecast.yearly.score }}分
            </span>
          </div>
          <p v-if="result.forecast.yearly.overall" class="fy-overall">{{ result.forecast.yearly.overall }}</p>
          <div v-if="result.forecast.yearly.details && Object.keys(result.forecast.yearly.details).length" class="fy-details">
            <div v-for="(text, domain) in result.forecast.yearly.details" :key="domain" class="fyd-item">
              <span class="fyd-domain">{{ domain }}</span>
              <span class="fyd-text">{{ text }}</span>
            </div>
          </div>
          <div v-if="result.forecast.yearly.events?.length" class="fy-events">
            <div v-for="(ev, i) in result.forecast.yearly.events" :key="i"
                 :class="['fye-item', `fye-${ev.level}`]"
                 :title="ev.source || ''">
              <span class="fye-cat">{{ ev.category }}</span>
              <span class="fye-desc">{{ ev.description }}</span>
            </div>
          </div>
          <p v-if="result.forecast.yearly.advice" class="fy-advice">💡 {{ result.forecast.yearly.advice }}</p>
        </div>

        <!-- 当前月 高亮 -->
        <div v-if="result.forecast.current_month" class="forecast-curmonth card">
          <div class="fcm-head">
            <span class="fcm-label">本月运势</span>
            <span class="fcm-gz">{{ result.forecast.current_month.ganzhi }}</span>
            <span v-if="result.forecast.current_month.score" class="fy-score"
                  :style="{ color: forecastScoreColor(result.forecast.current_month.score) }">
              {{ result.forecast.current_month.score }}分
            </span>
          </div>
          <p v-if="result.forecast.current_month.overall" class="fy-overall">{{ result.forecast.current_month.overall }}</p>
          <p v-if="result.forecast.current_month.advice" class="fy-advice">💡 {{ result.forecast.current_month.advice }}</p>
        </div>

        <!-- 全年月份 -->
        <div v-if="result.forecast.monthly?.length" class="section-block">
          <h3 class="section-title">月度运势概览 <small style="font-weight:400;color:var(--text-3);font-size:var(--fs-sm)">(点击展开详情)</small></h3>
          <div class="forecast-monthly-grid">
            <div v-for="(m, mi) in result.forecast.monthly" :key="m.period"
                 :class="['fm-item', m.score >= 80 ? 'fm-good' : m.score >= 50 ? 'fm-mid' : 'fm-low', { 'fm-expanded': expandedForecastMonth === mi }]"
                 @click="expandedForecastMonth = expandedForecastMonth === mi ? null : mi">
              <div class="fm-period">{{ m.period }}</div>
              <div class="fm-gz">{{ m.ganzhi }}</div>
              <div v-if="m.score" class="fm-score" :style="{ color: forecastScoreColor(m.score) }">{{ m.score }}</div>
              <div v-if="m.score" class="fm-score-bar"><i :style="{ width: `${Math.max(0, Math.min(100, Number(m.score))) || 0}%` }"></i></div>
              <div v-if="m.palace_name" class="fm-palace">{{ m.palace_name }}</div>
              <div v-if="m.overall" class="fm-overall">{{ m.overall }}</div>
              <!-- 展开详情区 -->
              <template v-if="expandedForecastMonth === mi">
                <div v-if="m.details && Object.keys(m.details).length" class="fm-details">
                  <div v-for="(text, domain) in m.details" :key="domain" class="fmd-item">
                    <span class="fmd-domain">{{ domain }}</span>
                    <span class="fmd-text">{{ text }}</span>
                  </div>
                </div>
                <div v-if="m.events?.length" class="fm-events">
                  <div v-for="(ev, ei) in m.events" :key="ei"
                       :class="['fme-item', `fme-${ev.level}`]"
                       :title="ev.source || ''">
                    <span class="fme-cat">{{ ev.category }}</span>
                    <span class="fme-desc">{{ ev.description }}</span>
                  </div>
                </div>
                <p v-if="m.advice" class="fm-advice">💡 {{ m.advice }}</p>
              </template>
            </div>
          </div>
        </div>
      </section>

      <!-- Tab: 建议 -->
      <section v-if="activeTab === 'suggest'" class="tab-panel">
        <!-- 建议统计卡 -->
        <div class="suggest-overview card">
          <div class="sov-grid">
            <div class="sov-item sov-remedy">
              <span class="sov-num">{{ result.remedies?.length || 0 }}</span>
              <span class="sov-label">化解建议</span>
            </div>
            <div class="sov-item sov-life">
              <span class="sov-num">{{ result.life_suggestions?.length || 0 }}</span>
              <span class="sov-label">生活建议</span>
            </div>
            <div v-if="suggestCategories.length" class="sov-item sov-cats">
              <span class="sov-num">{{ suggestCategories.length }}</span>
              <span class="sov-label">领域分类</span>
            </div>
            <div class="sov-item sov-p1">
              <span class="sov-num">{{ (result.remedies ?? []).filter(r => r.priority === 1).length }}</span>
              <span class="sov-label">高优先项</span>
            </div>
          </div>
          <!-- 分类筛选节卡 -->
          <div v-if="suggestCategories.length" class="sov-filter">
            <button :class="['sov-cat-btn', { active: suggestCategoryFilter === 'all' }]"
                    @click="suggestCategoryFilter = 'all'">全部</button>
            <button v-for="cat in suggestCategories" :key="cat"
                    :class="['sov-cat-btn', { active: suggestCategoryFilter === cat }]"
                    @click="suggestCategoryFilter = cat">{{ cat }}</button>
          </div>
        </div>
        <!-- 化解建议 -->
        <div v-if="sortedRemedies.length" class="section-block">
          <h3 class="section-title">
            化解与调整
            <span class="section-count">{{ sortedRemedies.length }}</span>
          </h3>
          <div class="remedies-list">
            <div v-for="(r, i) in sortedRemedies" :key="i" class="remedy-item">
              <div class="remedy-head">
                <span v-if="r.priority" class="remedy-priority" :class="'priority-' + r.priority">P{{ r.priority }}</span>
                <span class="remedy-cat">{{ r.cost_level || '建议' }}</span>
                <span class="remedy-name">{{ r.name }}</span>
                <span v-if="r.valid_scope" class="remedy-scope">{{ r.valid_scope }}</span>
              </div>
              <div v-if="r.actions?.length" class="remedy-actions">
                <div v-for="(a, ai) in r.actions" :key="ai" class="remedy-step">{{ ai + 1 }}. {{ a }}</div>
              </div>
              <div v-if="r.evidence" class="remedy-reason">— {{ r.evidence }}</div>
              <p v-if="r.disclaimer" class="remedy-disclaimer">⚠ {{ r.disclaimer }}</p>
            </div>
          </div>
        </div>
        <!-- 生活建议 -->
        <div v-if="filteredLifeSuggestions.length" class="section-block">
          <h3 class="section-title">
            生活领域建议
            <span class="section-count">{{ filteredLifeSuggestions.length }}</span>
          </h3>
          <div class="suggest-list">
            <div v-for="(s, i) in filteredLifeSuggestions" :key="i" class="suggest-item">
              <div class="suggest-head">
                <span v-if="s.priority" class="suggest-priority" :class="'priority-' + s.priority">P{{ s.priority }}</span>
                <span class="suggest-domain">{{ s.category_label || s.category }}</span>
                <span v-if="s.cost_level" class="suggest-cost">{{ s.cost_level }}</span>
              </div>
              <div class="suggest-name">{{ s.name }}</div>
              <p v-if="s.short_desc" class="suggest-text">{{ s.short_desc }}</p>
              <div v-if="s.actions?.length" class="suggest-actions">
                <div v-for="(a, ai) in s.actions" :key="ai" class="suggest-step">{{ ai + 1 }}. {{ a }}</div>
              </div>
              <div v-if="s.evidence" class="suggest-evidence">依据：{{ s.evidence }}</div>
              <div v-if="s.notes" class="suggest-notes">备注：{{ s.notes }}</div>
              <div v-if="s.valid_scope" class="suggest-scope">适用：{{ s.valid_scope }}</div>
              <p v-if="s.disclaimer" class="suggest-disclaimer">⚠ {{ s.disclaimer }}</p>
            </div>
          </div>
        </div>
        <p v-if="!result.remedies?.length && !result.life_suggestions?.length" class="muted">
          暂无建议数据
        </p>
      </section>

      <!-- 版本信息脚注 -->
      <footer v-if="result.engine_version || result.algorithm_version" class="result-footer">
        <span v-if="result.engine_version" class="ver-item">引擎 {{ result.engine_version }}</span>
        <span v-if="result.algorithm_version" class="ver-item">算法 {{ result.algorithm_version }}</span>
        <span v-if="result.template_version" class="ver-item">模板 {{ result.template_version }}</span>
      </footer>
    </template>
  </div>
</template>

<style scoped>
.wrap.ziwei-view {
  padding-bottom: var(--sp-8);
  flex: 1 1 auto;
  min-height: 0 !important;
  height: 100% !important;
  width: 100% !important;
  overflow-y: auto !important;
  display: flex;
  flex-direction: column;
  max-width: none !important;
}
.page-title { font-size: var(--fs-2xl); font-weight: 700; color: var(--text); margin-bottom: var(--sp-3); font-family: var(--font-cn); }

/* 表单折叠控制栏 */
.form-toggle-bar {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  margin-bottom: var(--sp-3);
}
.btn-toggle-form {
  padding: 5px 14px;
  border: 1px solid var(--border-md);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text-2);
  font-size: var(--fs-sm);
  cursor: pointer;
  transition: border-color var(--dur-fast), color var(--dur-fast);
}
.btn-toggle-form:hover { border-color: var(--accent); color: var(--accent); }
.current-params { font-size: var(--fs-sm); color: var(--text-3); }

.chart-tab-panel {
  position: relative;
}

/* 卡片 */
.card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: var(--sp-5); box-shadow: var(--shadow); margin-bottom: var(--sp-5); }

/* 表单 */
.form-grid { display: flex; flex-direction: column; gap: var(--sp-3); margin-bottom: var(--sp-4); }
.form-row { display: flex; align-items: center; gap: var(--sp-2); flex-wrap: wrap; }
.form-row > label:first-child { width: 60px; font-size: var(--fs-md); color: var(--text-2); flex-shrink: 0; }
.form-row > label[style] { font-size: var(--fs-md); color: var(--text-2); }
.form-row input[type="number"] { padding: 7px 10px; border: 1px solid var(--border-md); border-radius: var(--radius-sm); font-size: var(--fs-md); }
.form-row input:focus { outline: none; border-color: var(--accent); }
.radio-opt { display: flex; align-items: center; gap: 4px; cursor: pointer; font-size: var(--fs-md); }
.hint { font-size: var(--fs-xs); color: var(--text-3); }

.form-actions { display: flex; align-items: center; gap: var(--sp-3); flex-wrap: wrap; }

/* ── 算法设置面板 ─────────────────────────────── */
.algo-toggle-row { display: flex; align-items: center; gap: var(--sp-3); margin: var(--sp-3) 0 var(--sp-2); flex-wrap: wrap; }
.btn-algo-toggle { background: none; border: 1px solid var(--border-md); border-radius: var(--radius-sm); padding: 5px 12px; font-size: var(--fs-sm); color: var(--text-2); cursor: pointer; transition: border-color var(--dur-fast); }
.btn-algo-toggle:hover { border-color: var(--accent); color: var(--accent); }
.btn-tiny { padding: 4px 10px !important; font-size: var(--fs-xs) !important; }
.algo-custom-badge { background: var(--warning, #f59e0b); color: #fff; border-radius: 4px; padding: 2px 8px; font-size: var(--fs-xs); font-weight: 600; }

.algo-panel { background: var(--surface-alt, #f9f9fb); border: 1px solid var(--border); border-radius: var(--radius-md); padding: var(--sp-3) var(--sp-4); margin-bottom: var(--sp-3); display: flex; flex-direction: column; gap: var(--sp-3); }

/* C-6: 预设方案样式 */
.algo-presets {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.preset-label {
  font-size: var(--fs-sm);
  color: var(--text-3);
  font-weight: 500;
}
.preset-btn {
  padding: 4px 12px;
  font-size: var(--fs-sm);
  font-weight: 600;
  font-family: var(--font-cn);
  background: linear-gradient(135deg, #fff 0%, #f5f5f4 100%);
  border: 1px solid var(--border-md);
  border-radius: 6px;
  color: var(--text-2);
  cursor: pointer;
  transition: all 0.2s ease;
}
.preset-btn:hover {
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  border-color: var(--accent);
  color: var(--accent-dark);
}
.algo-divider {
  height: 1px;
  background: var(--border);
  margin: 4px 0;
}

.algo-group { display: flex; align-items: flex-start; gap: var(--sp-3); flex-wrap: wrap; }
.algo-label { min-width: 110px; font-size: var(--fs-sm); color: var(--text-3); font-weight: 500; padding-top: 2px; }
.sihua-group { flex-direction: column; gap: var(--sp-2); }
.sihua-group .algo-label { align-self: flex-start; }
.sihua-rows { display: flex; flex-direction: column; gap: var(--sp-2); }
.sihua-row { display: flex; align-items: center; gap: var(--sp-3); flex-wrap: wrap; }
.sihua-stem { min-width: 22px; font-weight: 700; color: var(--accent); font-size: var(--fs-sm); }
.btn-primary { padding: 9px 22px; background: var(--accent); color: #fff; border: none; border-radius: var(--radius-sm); font-size: var(--fs-md); font-weight: 600; cursor: pointer; transition: background var(--dur-fast); }
.btn-primary:hover { background: var(--accent-dark); }
.btn-primary:disabled { opacity: .6; cursor: not-allowed; }
.btn-sec { padding: 9px 18px; background: var(--surface); color: var(--text-2); border: 1px solid var(--border-md); border-radius: var(--radius-sm); font-size: var(--fs-md); cursor: pointer; transition: border-color var(--dur-fast); }
.btn-sec:hover { border-color: var(--accent); color: var(--accent); }
.btn-sec:disabled { opacity: .5; cursor: not-allowed; }
.error-msg { color: var(--danger-dark); font-size: var(--fs-sm); }

/* 骨架屏 */
.skeleton-wrap { padding: var(--sp-5); }
.skel-line { height: 16px; background: var(--border); border-radius: 4px; margin-bottom: var(--sp-3); animation: shimmer 1.2s infinite; }
.skel-box { background: var(--border); border-radius: var(--radius-sm); margin-top: var(--sp-4); animation: shimmer 1.2s infinite; }
@keyframes shimmer { 0%,100% { opacity: 1; } 50% { opacity: .4; } }

/* 信息栏 */
.info-bar { display: flex; flex-wrap: wrap; align-items: center; gap: var(--sp-3); padding: var(--sp-3) var(--sp-5); }
.info-item { font-size: var(--fs-sm); color: var(--text-2); }
.info-item b { color: var(--text); }
.ju-badge { padding: 2px 10px; border-radius: 12px; color: #fff; font-size: var(--fs-xs); font-weight: 700; }
.btn-export { padding: 6px 14px; background: var(--surface); color: var(--accent); border: 1.5px solid var(--accent); border-radius: var(--radius-sm); font-size: var(--fs-sm); font-weight: 600; cursor: pointer; transition: all var(--dur-fast); }
.btn-export-main { margin-left: auto; }
.btn-export:hover { background: var(--accent); color: #fff; }
.btn-zeri { margin-left: var(--sp-2); padding: 6px 14px; background: var(--surface); color: #d97706; border: 1.5px solid #fbbf24; border-radius: var(--radius-sm); font-size: var(--fs-sm); font-weight: 600; cursor: pointer; transition: all var(--dur-fast); }
.btn-zeri:hover { background: #fef3c7; }
.btn-ai { margin-left: var(--sp-2); padding: 6px 14px; background: var(--surface); color: #7c3aed; border: 1.5px solid #a78bfa; border-radius: var(--radius-sm); font-size: var(--fs-sm); font-weight: 600; cursor: pointer; transition: all var(--dur-fast); }
.btn-ai:hover:not(:disabled) { background: #ede9fe; }
.btn-ai:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-save-case { margin-left: var(--sp-2); padding: 6px 14px; background: #ecfdf5; color: #047857; border: 1.5px solid #6ee7b7; border-radius: var(--radius-sm); font-size: var(--fs-sm); font-weight: 600; cursor: pointer; transition: all var(--dur-fast); }
.btn-save-case:hover:not(:disabled) { background: #d1fae5; }
.btn-save-case:disabled { opacity: .6; cursor: not-allowed; }
.btn-cases { margin-left: var(--sp-2); padding: 6px 14px; background: #eff6ff; color: #1d4ed8; border: 1.5px solid #93c5fd; border-radius: var(--radius-sm); font-size: var(--fs-sm); font-weight: 600; cursor: pointer; transition: all var(--dur-fast); }
.btn-cases:hover { background: #dbeafe; }
.btn-snapshots { margin-left: var(--sp-2); padding: 6px 14px; background: #fff7ed; color: #c2410c; border: 1.5px solid #fdba74; border-radius: var(--radius-sm); font-size: var(--fs-sm); font-weight: 600; cursor: pointer; transition: all var(--dur-fast); }
.btn-snapshots:hover:not(:disabled) { background: #ffedd5; }
.btn-snapshots:disabled { opacity: .6; cursor: not-allowed; }
.btn-similar { margin-left: var(--sp-2); padding: 6px 14px; background: #eef2ff; color: #4338ca; border: 1.5px solid #c7d2fe; border-radius: var(--radius-sm); font-size: var(--fs-sm); font-weight: 600; cursor: pointer; transition: all var(--dur-fast); }
.btn-similar:hover:not(:disabled) { background: #e0e7ff; }
.btn-similar:disabled { opacity: .6; cursor: not-allowed; }
.btn-review { margin-left: var(--sp-2); padding: 6px 14px; background: #f0fdf4; color: #166534; border: 1.5px solid #86efac; border-radius: var(--radius-sm); font-size: var(--fs-sm); font-weight: 600; cursor: pointer; transition: all var(--dur-fast); }
.btn-review:hover:not(:disabled) { background: #dcfce7; }
.btn-review:disabled { opacity: .6; cursor: not-allowed; }
.btn-llm { margin-left: var(--sp-2); padding: 6px 14px; background: #faf5ff; color: #7e22ce; border: 1.5px solid #d8b4fe; border-radius: var(--radius-sm); font-size: var(--fs-sm); font-weight: 600; cursor: pointer; transition: all var(--dur-fast); }
.btn-llm:hover:not(:disabled) { background: #f3e8ff; }
.btn-llm:disabled { opacity: .6; cursor: not-allowed; }
.btn-ops { margin-left: var(--sp-2); padding: 6px 14px; background: #eff6ff; color: #1d4ed8; border: 1.5px solid #93c5fd; border-radius: var(--radius-sm); font-size: var(--fs-sm); font-weight: 600; cursor: pointer; transition: all var(--dur-fast); }
.btn-ops:hover:not(:disabled) { background: #dbeafe; }
.btn-ops:disabled { opacity: .6; cursor: not-allowed; }
.btn-batch { margin-left: var(--sp-2); padding: 6px 14px; background: #fff7ed; color: #9a3412; border: 1.5px solid #fdba74; border-radius: var(--radius-sm); font-size: var(--fs-sm); font-weight: 600; cursor: pointer; transition: all var(--dur-fast); }
.btn-batch:hover:not(:disabled) { background: #ffedd5; }
.btn-batch:disabled { opacity: .6; cursor: not-allowed; }
.btn-glossary { margin-left: var(--sp-2); padding: 6px 14px; background: #fdf4ff; color: #a21caf; border: 1.5px solid #f0abfc; border-radius: var(--radius-sm); font-size: var(--fs-sm); font-weight: 600; cursor: pointer; transition: all var(--dur-fast); }
.btn-glossary:hover:not(:disabled) { background: #fae8ff; }
.btn-glossary:disabled { opacity: .6; cursor: not-allowed; }
.btn-compat { margin-left: var(--sp-2); padding: 6px 14px; background: #f0f9ff; color: #0369a1; border: 1.5px solid #7dd3fc; border-radius: var(--radius-sm); font-size: var(--fs-sm); font-weight: 600; cursor: pointer; transition: all var(--dur-fast); }
.btn-compat:hover:not(:disabled) { background: #e0f2fe; }
.btn-compat:disabled { opacity: .6; cursor: not-allowed; }
.btn-fengshui { margin-left: var(--sp-2); padding: 6px 14px; background: #ecfeff; color: #0f766e; border: 1.5px solid #5eead4; border-radius: var(--radius-sm); font-size: var(--fs-sm); font-weight: 600; cursor: pointer; transition: all var(--dur-fast); }
.btn-fengshui:hover:not(:disabled) { background: #ccfbf1; }
.btn-fengshui:disabled { opacity: .6; cursor: not-allowed; }
.ziwei-action-menu { position: relative; }
.ziwei-action-menu summary { list-style: none; }
.ziwei-action-menu summary::-webkit-details-marker { display: none; }
.ziwei-action-menu[open] > summary { box-shadow: inset 0 0 0 1px rgba(37, 99, 235, 0.18); }
.ziwei-menu-panel {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  min-width: 180px;
  padding: 8px;
  border-radius: 12px;
  border: 1px solid var(--border);
  background: var(--surface);
  box-shadow: 0 16px 40px rgba(15, 23, 42, 0.16);
  display: flex;
  flex-direction: column;
  gap: 4px;
  z-index: 20;
}
.ziwei-menu-panel-tools { min-width: 156px; }
.ziwei-menu-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  width: 100%;
  border: none;
  background: transparent;
  text-align: left;
  padding: 9px 10px;
  border-radius: 8px;
  color: var(--text-2);
  font-size: var(--fs-sm);
  cursor: pointer;
}
.ziwei-menu-item:hover:not(:disabled) {
  background: var(--surface-2);
  color: var(--accent-dark);
}
.ziwei-menu-item:disabled {
  opacity: .55;
  cursor: not-allowed;
}
.btn-tool-summary {
  margin-left: var(--sp-2);
  padding: 6px 12px;
  border-radius: var(--radius-sm);
  border: 1.5px solid var(--border-md);
  background: var(--surface);
  color: var(--text-2);
  font-size: var(--fs-sm);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--dur-fast);
}
.btn-tool-summary:hover { border-color: var(--accent); color: var(--accent); }

.summary-block { font-size: var(--fs-md); color: var(--text); line-height: 1.7; margin-bottom: var(--sp-5); padding: var(--sp-4); background: var(--surface-2); border-radius: var(--radius-sm); border-left: 3px solid var(--accent); }

/* Tabs */
.tabs { display: flex; gap: var(--sp-2); margin-bottom: var(--sp-4); border-bottom: 2px solid var(--border); }
.tab-btn { padding: 8px 20px; border: none; background: none; cursor: pointer; font-size: var(--fs-md); color: var(--text-2); border-bottom: 2px solid transparent; margin-bottom: -2px; transition: color var(--dur-fast), border-color var(--dur-fast); display: flex; align-items: center; gap: 4px; }
.tab-btn.active { color: var(--accent); border-bottom-color: var(--accent); font-weight: 600; }
.tab-btn:hover { color: var(--text); }
.badge { background: var(--accent); color: #fff; border-radius: 10px; padding: 1px 6px; font-size: 10px; font-weight: 700; }

/* 当前大运提示 */
.cur-dayun-tip { font-size: var(--fs-sm); color: var(--text-2); margin-bottom: var(--sp-4); padding: var(--sp-2) var(--sp-4); background: rgba(217,119,6,.08); border-radius: var(--radius-sm); border-left: 3px solid var(--accent); }
.sihua-badge { display: inline-block; padding: 1px 6px; background: var(--surface); border: 1px solid var(--border-md); border-radius: 10px; font-size: var(--fs-xs); margin-left: 4px; }

/* ── 传统命盘网格 Pro ──────────────────────────────── */

/* 外包装：方位标注 */
.palace-grid-wrap {
  margin-bottom: var(--sp-5);
  user-select: none;
  overflow-y: auto;
  max-height: 70vh;
}
.grid-compass {
  display: grid;
  grid-template-columns: 26px 1fr 26px;
  align-items: center;
}
.compass-cell { display: flex; align-items: center; justify-content: center; }
.compass-n, .compass-s {
  text-align: center;
  font-size: var(--fs-xs);
  color: var(--text-3);
  font-weight: 600;
  letter-spacing: 1px;
  padding: 3px 0;
}
.grid-body {
  display: flex;
  align-items: stretch;
}
.compass-side {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  font-size: var(--fs-xs);
  color: var(--text-3);
  font-weight: 600;
  letter-spacing: 1px;
  writing-mode: vertical-rl;
  flex-shrink: 0;
}

.palace-grid-pro {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0;
  border: 1.5px solid #c9b99a;
  border-radius: 2px;
  overflow: hidden;
  flex: 1;
  background: #e8dcc8;
}

/* 宫位格 */
.pc-cell {
  background: #fffdf7;
  padding: 5px 5px 4px;
  cursor: pointer;
  min-height: 108px;
  display: flex;
  flex-direction: column;
  gap: 1px;
  transition: background var(--dur-fast);
  position: relative;
  border-right: 1px solid #d6c9b3;
  border-bottom: 1px solid #d6c9b3;
}
.pc-cell:last-child { border-right: none; }
.pc-cell:hover { background: #fef9ee; }
.pc-sel { background: #fef3d8 !important; box-shadow: inset 0 0 0 2px #c07a00; }
.pc-sanfang { background: rgba(254, 243, 216, 0.4); box-shadow: inset 0 0 0 1px rgba(192, 122, 0, 0.3); }
.pc-life { border-top: 3px solid #dc2626 !important; }
.pc-body { border-top: 3px solid #2563eb !important; }
.pc-liunian-life { 
  background: linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%) !important; 
  box-shadow: inset 0 0 0 2px #7c3aed;
}
.pc-liuyue-life { 
  background: linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%) !important; 
  box-shadow: inset 0 0 0 2px #ea580c;
}
.pc-xiaoxian-life { 
  background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%) !important; 
  box-shadow: inset 0 0 0 2px #059669;
}

/* 宫格头部 */
.pc-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 2px;
}
.pc-head-left {
  display: flex;
  align-items: center;
  gap: 2px;
  flex-wrap: wrap;
}
.pc-pname {
  font-size: 10px;
  color: #78716c;
  font-weight: 600;
  font-family: var(--font-cn);
  letter-spacing: 0.5px;
}
.pc-life-tag {
  font-size: 8px;
  padding: 0 2px;
  background: #dc2626;
  color: #fff;
  border-radius: 2px;
  font-weight: 700;
  line-height: 1.4;
}
.pc-body-tag {
  font-size: 8px;
  padding: 0 2px;
  background: #2563eb;
  color: #fff;
  border-radius: 2px;
  font-weight: 700;
  line-height: 1.4;
}
.pc-gzhi {
  font-size: 12px;
  color: #44403c;
  font-weight: 700;
  font-family: var(--font-cn);
  white-space: nowrap;
  flex-shrink: 0;
}

/* 大限年龄 + 长生 行 */
.pc-da-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 2px;
  flex-wrap: wrap;
}
.pc-da {
  font-size: 9px;
  color: #b45309;
  font-weight: 700;
  background: rgba(180,83,9,.08);
  border-radius: 2px;
  padding: 0 3px;
}
/* 流年年龄标签 */
.pc-liunian-age {
  font-size: 8px;
  color: #7c3aed;
  font-weight: 600;
  background: rgba(124,58,237,.1);
  border-radius: 2px;
  padding: 0 2px;
}
/* 大限宫位名称 */
.pc-daxian-name {
  font-size: 7px;
  color: #0d9488;
  font-weight: 700;
  background: rgba(13,148,136,.12);
  border-radius: 2px;
  padding: 0 2px;
  margin-left: 2px;
}
/* 流年宫位名称 */
.pc-liunian-name {
  font-size: 7px;
  color: #7c3aed;
  font-weight: 700;
  background: rgba(124,58,237,.1);
  border-radius: 2px;
  padding: 0 2px;
  margin-left: 2px;
}
/* 流月宫位名称 */
.pc-liuyue-name {
  font-size: 7px;
  color: #ea580c;
  font-weight: 700;
  background: rgba(234,88,12,.1);
  border-radius: 2px;
  padding: 0 2px;
  margin-left: 2px;
}
/* 小限宫位名称 */
.pc-xiaoxian-name {
  font-size: 7px;
  color: #059669;
  font-weight: 700;
  background: rgba(5,150,105,.1);
  border-radius: 2px;
  padding: 0 2px;
  margin-left: 2px;
}
.pc-cs {
  font-size: 8px;
  color: #a8a29e;
  margin-left: auto;
}
/* 将前/岁前星 */
.pc-jiangqian,
.pc-suiqian {
  font-size: 7px;
  color: #9ca3af;
  margin-left: 2px;
}
.pc-jiangqian { color: #10b981; } /* 绿色 */
.pc-suiqian { color: #f59e0b; }   /* 橙色 */
/* 博士十二星 */
.pc-boshi-row {
  display: flex;
  flex-wrap: wrap;
  gap: 2px;
  margin-top: 1px;
}
.pc-boshi {
  font-size: 7px;
  color: #8b5cf6;
  background: rgba(139, 92, 246, 0.1);
  border-radius: 2px;
  padding: 0 2px;
}

/* 主星区块 */
.pc-mstars { display: flex; flex-direction: column; gap: 2px; flex: 1; margin-top: 2px; }
.pc-mstar  { display: flex; align-items: center; gap: 2px; flex-wrap: nowrap; }
.pc-sn {
  font-size: 14px;
  font-weight: 900;
  font-family: var(--font-cn);
  line-height: 1.1;
}
/* 亮度颜色 (7级: 0陷~6庙) */
.pc-br6 { color: #92400e; }   /* 庙  - 深琥珀 */
.pc-br5 { color: #dc2626; }   /* 旺  - 红     */
.pc-br4 { color: #b45309; }   /* 得  - 琥珀   */
.pc-br3 { color: #1d4ed8; }   /* 利  - 蓝     */
.pc-br2 { color: #374151; }   /* 平  - 深灰   */
.pc-br1 { color: #78716c; }   /* 不  - 中灰   */
.pc-br0 { color: #a8a29e; }   /* 陷  - 浅灰   */

.pc-sbr {
  font-size: 8px;
  color: #a8a29e;
  line-height: 1;
  margin-top: 1px;
  border: 1px solid #e5e0d8;
  border-radius: 2px;
  padding: 0 1px;
}

/* 四化彩色小标签 */
.pc-tf {
  font-size: 9px;
  font-weight: 800;
  padding: 0 3px;
  border-radius: 2px;
  line-height: 1.5;
  color: #fff;
  flex-shrink: 0;
}
/* 大限四化标记 */
.pc-tf-daxian {
  font-size: 8px;
  opacity: 0.9;
  border: 1px dashed currentColor;
  background: transparent !important;
  color: #334155 !important;
}
/* 流年四化标记 */
.pc-tf-liunian {
  font-size: 8px;
  opacity: 0.9;
  border: 1px dotted currentColor;
  background: transparent !important;
  color: #334155 !important;
}
/* 流月四化标记 */
.pc-tf-liuyue {
  font-size: 8px;
  opacity: 0.9;
  border: 1px solid currentColor;
  border-radius: 3px;
  background: transparent !important;
  color: #334155 !important;
}

/* 叠加四化文字对比兜底：按类型给深色前景，防止继承白字 */
.pc-tf-daxian[style*='化禄'], .pc-tf-liunian[style*='化禄'], .pc-tf-liuyue[style*='化禄'] { color: #166534 !important; }
.pc-tf-daxian[style*='化权'], .pc-tf-liunian[style*='化权'], .pc-tf-liuyue[style*='化权'] { color: #991b1b !important; }
.pc-tf-daxian[style*='化科'], .pc-tf-liunian[style*='化科'], .pc-tf-liuyue[style*='化科'] { color: #1e40af !important; }
.pc-tf-daxian[style*='化忌'], .pc-tf-liunian[style*='化忌'], .pc-tf-liuyue[style*='化忌'] { color: #5b21b6 !important; }

/* 辅星 */
.pc-aux {
  font-size: 9px;
  color: #a8a29e;
  line-height: 1.4;
  word-break: break-all;
  margin-top: auto;
  padding-top: 2px;
  border-top: 1px dashed #e5e0d8;
}

/* 中宫信息格（C-5增强） */
.pc-center {
  grid-column: span 2;
  grid-row: span 2;
  background: linear-gradient(135deg, #fffff5 0%, #fdf6e3 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-right: 1px solid #d6c9b3;
  border-bottom: 1px solid #d6c9b3;
}
.pc-center-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px;
  text-align: center;
  width: 100%;
}
.pc-center-top {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 2px;
}
.pc-cj  { font-size: 18px; font-weight: 900; font-family: var(--font-cn); letter-spacing: 1px; }
.pc-cg-badge {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 8px;
  background: rgba(120, 113, 108, 0.12);
  color: #57534e;
  font-weight: 600;
}
.pc-sizhu {
  display: flex;
  gap: 8px;
  margin: 4px 0;
}
.pc-sizhu-alt {
  margin-top: 2px;
  opacity: 0.65;
}
.pc-sz-item {
  font-size: 13px;
  font-weight: 700;
  font-family: var(--font-cn);
  color: #44403c;
  padding: 2px 6px;
  background: rgba(214, 201, 179, 0.3);
  border-radius: 4px;
}
.pc-sz-alt {
  background: rgba(214, 201, 179, 0.15);
  color: #78716c;
  font-weight: 500;
  font-size: 11px;
}
.pc-sz-hour {
  color: #78716c;
  font-weight: 600;
}
.pc-divider { width: 60%; height: 1px; background: #d6c9b3; margin: 2px 0; }
.pc-birth-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.pc-cb  { font-size: 11px; color: #57534e; }
.pc-cl  { font-size: 10px; color: #78716c; }
.pc-ct  { font-size: 9px; color: #a8a29e; }
.pc-rulers {
  display: flex;
  gap: 6px;
  justify-content: center;
  flex-wrap: wrap;
  margin: 2px 0;
}
.pc-cr-tag { padding: 1px 6px; border-radius: 10px; font-size: 10px; font-weight: 600; }
.pc-cr-life { background: rgba(220,38,38,.12); color: #dc2626; }
.pc-cr-body { background: rgba(37,99,235,.12); color: #2563eb; }
.pc-dayun-info {
  display: flex;
  gap: 8px;
  font-size: 10px;
  color: #78716c;
  margin-top: 2px;
}
.pc-dayun-dir {
  padding: 1px 5px;
  border-radius: 6px;
  background: rgba(34, 197, 94, 0.12);
  color: #16a34a;
  font-weight: 600;
}
.pc-dayun-age {
  font-weight: 500;
}
/* 大运年龄/年份条 */
.pc-dayun-strip {
  width: 100%;
  margin-top: 4px;
  overflow-x: auto;
  scrollbar-width: none;
}
.pc-dayun-strip::-webkit-scrollbar { display: none; }
.pc-dayun-ages,
.pc-dayun-years {
  display: flex;
  gap: 2px;
  width: max-content;
}
.pc-dys-age, .pc-dys-year {
  font-size: 9px;
  color: #a8a29e;
  padding: 1px 4px;
  min-width: 24px;
  text-align: center;
}
.pc-dys-cur.pc-dys-age { color: #dc2626; font-weight: 700; }
.pc-dys-cur.pc-dys-year { color: #dc2626; font-weight: 600; }
/* 操作按钮 */
.pc-ops-btns {
  display: flex;
  gap: 4px;
  margin-top: 6px;
  justify-content: center;
  flex-wrap: wrap;
}
.pc-op-btn {
  padding: 3px 8px;
  font-size: 10px;
  font-family: var(--font-cn);
  background: #e7e5e4;
  border: 1px solid #d6d3d1;
  border-radius: 4px;
  color: #57534e;
  cursor: pointer;
  transition: background 0.15s;
}
.pc-op-btn:hover { background: #d6d3d1; color: #292524; }
.pc-op-tray { background: #f0fdf4; border-color: #86efac; color: #16a34a; }
.pc-op-tray:hover { background: #dcfce7; }
/* 自化图示 */
.pc-zihua-row {
  display: flex;
  gap: 4px;
  align-items: center;
  margin-top: 4px;
  flex-wrap: wrap;
  justify-content: center;
}
.pc-zihua-label { font-size: 9px; color: #a8a29e; }
.pc-zihua-tag {
  font-size: 9px;
  font-weight: 600;
  padding: 1px 4px;
  border-radius: 3px;
}
.zh-lu { color: #16a34a; }
.zh-quan { color: #ea580c; }
.zh-ke { color: #2563eb; }
.zh-ji { color: #dc2626; }
.pc-zihua-none { font-size: 9px; color: #d6d3d1; }

.highlight-input {
  animation: highlight-pulse 0.5s ease-in-out 3;
  box-shadow: 0 0 0 3px rgba(217, 119, 6, 0.3) !important;
}
@keyframes highlight-pulse {
  0%, 100% { box-shadow: 0 0 0 3px rgba(217, 119, 6, 0.3); }
  50% { box-shadow: 0 0 0 6px rgba(217, 119, 6, 0.15); }
}

/* 宫位详情 */
.slide-enter-active, .slide-leave-active { transition: all .25s ease; }
.slide-enter-from, .slide-leave-to { opacity: 0; transform: translateY(-8px); }

.palace-detail { margin-bottom: var(--sp-5); }
.detail-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--sp-3); }
.detail-header h3 { font-size: var(--fs-lg); font-weight: 700; font-family: var(--font-cn); }
.detail-branch { font-size: var(--fs-sm); color: var(--text-3); margin-left: var(--sp-2); }
.detail-layout {
  display: grid;
  grid-template-columns: minmax(280px, 1fr) minmax(320px, 1.2fr);
  gap: var(--sp-3);
}
.detail-left,
.detail-right {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}
.detail-panel {
  padding: var(--sp-3);
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
}
.close-btn { background: none; border: none; cursor: pointer; color: var(--text-3); font-size: var(--fs-lg); padding: 0 4px; }
.close-btn:hover { color: var(--danger-dark); }
.detail-stars { display: flex; flex-wrap: wrap; gap: var(--sp-2); }
.detail-star { display: flex; align-items: center; gap: 4px; padding: 4px 10px; background: var(--surface-2); border-radius: var(--radius-sm); font-size: var(--fs-sm); cursor: help; }
.detail-star:hover { background: var(--surface); }
.star-name-hover { transition: color 0.15s; }
.detail-star:hover .star-name-hover { color: var(--accent); }
.star-br { color: var(--text-3); font-size: var(--fs-xs); }
.star-tf { color: var(--accent); font-size: var(--fs-xs); font-weight: 600; }
.detail-conclusion { font-size: var(--fs-md); font-weight: 600; color: var(--text); margin-bottom: var(--sp-2); }
.detail-explanation { font-size: var(--fs-md); color: var(--text); line-height: 1.7; margin-bottom: var(--sp-2); white-space: pre-line; }
.detail-suggestion { font-size: var(--fs-sm); color: var(--accent-dark); background: rgba(217,119,6,.08); border-radius: var(--radius-sm); padding: var(--sp-2) var(--sp-3); }
@media (max-width: 960px) {
  .detail-layout {
    grid-template-columns: 1fr;
  }
}

/* 大运 */
.dayun-stats-card {
  padding: var(--sp-4);
  margin-bottom: var(--sp-4);
}
.dsc-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  gap: var(--sp-2);
  margin-bottom: var(--sp-4);
}
.dsc-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  padding: var(--sp-2) var(--sp-3);
  background: var(--surface-2);
  border-radius: var(--radius-sm);
}
.dsc-label {
  font-size: var(--fs-xs);
  color: var(--text-2);
}
.dsc-value {
  font-size: var(--fs-md);
  font-weight: 700;
  color: var(--text);
}
.dsc-progress { margin-top: var(--sp-2); }
.dsc-prog-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 6px;
}
.dsc-prog-title {
  font-size: var(--fs-sm);
  font-weight: 600;
  color: var(--text);
}
.dsc-prog-meta {
  font-size: var(--fs-xs);
  color: var(--text-2);
}
.dsc-prog-bar {
  height: 8px;
  background: var(--border);
  border-radius: 999px;
  overflow: hidden;
}
.dsc-prog-fill {
  height: 100%;
  background: linear-gradient(90deg, #d97706, #f59e0b);
  border-radius: 999px;
  transition: width 0.4s ease;
}
.dsc-prog-labels {
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  color: var(--text-2);
  margin-top: 3px;
}
.dayun-info { font-size: var(--fs-sm); color: var(--text-2); margin-bottom: var(--sp-4); }
.dayun-list { display: flex; flex-wrap: wrap; gap: var(--sp-3); }
.dayun-item { padding: var(--sp-3) var(--sp-4); background: var(--surface-2); border: 1px solid var(--border); border-radius: var(--radius-sm); text-align: center; min-width: 90px; position: relative; }
.dayun-item.cur { border-color: var(--accent); background: rgba(217,119,6,.06); }
.dayun-cur-badge {
  position: absolute;
  top: -8px;
  right: -8px;
  background: #d97706;
  color: #fff;
  font-size: 9px;
  padding: 2px 6px;
  border-radius: 8px;
  font-weight: 600;
}
.dayun-gz { font-size: var(--fs-lg); font-weight: 700; font-family: var(--font-cn); }
.dayun-age { font-size: var(--fs-xs); color: var(--text-2); margin-top: 3px; }
.dayun-year { font-size: var(--fs-xs); color: var(--text-3); }
.dayun-sihua { display: flex; flex-wrap: wrap; gap: 2px; justify-content: center; margin-top: 4px; }

/* 格局 */
.patterns-list { display: flex; flex-direction: column; gap: var(--sp-3); }
.pattern-stats {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-3);
  padding: var(--sp-3) var(--sp-4);
  background: var(--surface-2);
  border-radius: var(--radius-sm);
  margin-bottom: var(--sp-2);
}
.pattern-stat { font-size: var(--fs-sm); color: var(--text-2); }
.pattern-stat b { font-weight: 700; }
.pattern-stat.high b { color: #dc2626; }
.pattern-stat.med b { color: #d97706; }
.pattern-stat.low b { color: #64748b; }
.pattern-item { padding: var(--sp-4); border-radius: var(--radius-sm); border-left: 4px solid var(--border-md); background: var(--surface-2); }
.pattern-item.level-high { border-left-color: #dc2626; }
.pattern-item.level-med  { border-left-color: #d97706; }
.pattern-item.level-low  { border-left-color: #64748b; }
.pattern-header { display: flex; align-items: center; gap: var(--sp-3); margin-bottom: var(--sp-2); }
.pattern-name { font-size: var(--fs-md); font-weight: 700; font-family: var(--font-cn); }
.pattern-level { font-size: var(--fs-xs); padding: 1px 8px; border-radius: 10px; background: var(--surface); border: 1px solid var(--border-md); color: var(--text-2); }
.pattern-desc { font-size: var(--fs-sm); color: var(--text); line-height: 1.6; }
.pattern-meta { display: flex; flex-wrap: wrap; gap: var(--sp-3); margin-top: var(--sp-2); }
.pattern-palaces, .pattern-stars { display: flex; align-items: center; gap: 4px; flex-wrap: wrap; }
.meta-label { font-size: 10px; color: var(--text-2); }
.meta-tag { font-size: 10px; padding: 1px 6px; border-radius: 8px; }
.palace-tag { background: rgba(124, 58, 237, 0.1); color: #7c3aed; }
.star-tag { background: rgba(217, 119, 6, 0.1); color: #d97706; }
.pattern-source { font-size: var(--fs-xs); color: var(--text-2); margin-top: 4px; }

/* 建议 */
.section-block { margin-bottom: var(--sp-6); }
.section-title { font-size: var(--fs-lg); font-weight: 600; margin-bottom: var(--sp-4); color: var(--text); }
.remedies-list { display: flex; flex-direction: column; gap: var(--sp-3); }
.remedy-item { display: flex; flex-direction: column; gap: var(--sp-2); padding: var(--sp-3); background: var(--surface-2); border-radius: var(--radius-sm); }
.remedy-head { display: flex; flex-wrap: wrap; align-items: center; gap: var(--sp-2); }
.remedy-priority { font-size: var(--fs-xs); padding: 1px 6px; border-radius: 4px; font-weight: 700; }
.remedy-priority.priority-1 { background: #dc2626; color: #fff; }
.remedy-priority.priority-2 { background: #f59e0b; color: #fff; }
.remedy-priority.priority-3 { background: #3b82f6; color: #fff; }
.remedy-priority.priority-4, .remedy-priority.priority-5 { background: #6b7280; color: #fff; }
.remedy-cat { font-size: var(--fs-xs); padding: 2px 8px; background: var(--accent); color: #fff; border-radius: 10px; font-weight: 600; flex-shrink: 0; }
.remedy-name { font-weight: 600; color: var(--text); }
.remedy-scope { font-size: var(--fs-xs); color: var(--text-3); margin-left: auto; }
.remedy-actions { display: flex; flex-direction: column; gap: 2px; padding-left: var(--sp-3); }
.remedy-step { font-size: var(--fs-sm); color: var(--text-2); }
.remedy-reason { font-size: var(--fs-sm); color: var(--text-3); font-style: italic; }
.suggest-overview {
  padding: var(--sp-4);
  margin-bottom: var(--sp-4);
}
.sov-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  gap: var(--sp-2);
  margin-bottom: var(--sp-3);
}
.sov-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  padding: var(--sp-2) var(--sp-3);
  background: var(--surface-2);
  border-radius: var(--radius-sm);
}
.sov-num { font-size: var(--fs-xl); font-weight: 700; color: var(--text); }
.sov-label { font-size: var(--fs-xs); color: var(--text-2); }
.sov-remedy .sov-num { color: #92400e; }
.sov-p1 .sov-num { color: #991b1b; }
.sov-filter { display: flex; flex-wrap: wrap; gap: 6px; }
.sov-cat-btn {
  font-size: var(--fs-xs);
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid var(--border-md);
  background: var(--surface);
  color: var(--text-2);
  cursor: pointer;
  transition: all 0.15s;
}
.sov-cat-btn.active,
.sov-cat-btn:hover {
  border-color: var(--accent);
  background: rgba(217,119,6,.10);
  color: #78350f;
}
/* 大运进度头位置由 .dayun-stats-card 处理，.dsc-prog-head 紧跟 */
.dsc-prog-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 6px;
}
.dsc-prog-title { font-size: var(--fs-sm); font-weight: 600; color: var(--text); }
.dsc-prog-meta { font-size: var(--fs-xs); color: var(--text-3); }
.dsc-prog-bar {
  height: 8px;
  background: var(--border);
  border-radius: 999px;
  overflow: hidden;
}
.dsc-prog-fill {
  height: 100%;
  background: linear-gradient(90deg, #d97706, #f59e0b);
  border-radius: 999px;
  transition: width 0.4s ease;
}
.dsc-prog-labels {
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  color: var(--text-3);
  margin-top: 3px;
}
.dayun-info { font-size: var(--fs-sm); color: var(--text-2); margin-bottom: var(--sp-4); }
.suggest-stats {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-3);
  padding: var(--sp-3) var(--sp-4);
  background: var(--surface-2);
  border-radius: var(--radius-sm);
  margin-bottom: var(--sp-4);
}
.suggest-stat { font-size: var(--fs-sm); color: var(--text-2); }
.suggest-stat b { font-weight: 700; color: var(--accent); }

/* ── 运势统计概览 ────────────────────────── */
.forecast-stats {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--sp-4);
  padding: var(--sp-4);
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
  border: 1px solid #86efac;
  border-radius: var(--radius-md);
  margin-bottom: var(--sp-5);
}
.forecast-stat-main {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-right: var(--sp-4);
  border-right: 1px solid #86efac;
}
.forecast-stat-main .fs-label { font-size: var(--fs-xs); color: var(--text-3); }
.forecast-stat-main .fs-value { font-size: var(--fs-2xl); font-weight: 800; }
.forecast-stat-dist {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-3);
}
.forecast-stat-dist .fs-item {
  font-size: var(--fs-sm);
  padding: 4px 10px;
  border-radius: var(--radius-sm);
  background: #fff;
  border: 1px solid var(--border);
}
.forecast-stat-dist .fs-item b { font-weight: 700; margin-left: 4px; }
.forecast-stat-dist .fs-item.good { color: #15803d; border-color: #86efac; }
.forecast-stat-dist .fs-item.mid { color: #d97706; border-color: #fcd34d; }
.forecast-stat-dist .fs-item.low { color: #dc2626; border-color: #fca5a5; }
.forecast-stat-peak {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-3);
  margin-left: auto;
}
.forecast-stat-peak .fs-peak {
  font-size: var(--fs-xs);
  padding: 3px 8px;
  border-radius: 6px;
}
.forecast-stat-peak .fs-peak.best { background: #dcfce7; color: #166534; }
.forecast-stat-peak .fs-peak.worst { background: #fef2f2; color: #991b1b; }
.forecast-stat-peak .fs-peak b { font-weight: 700; margin-left: 3px; }
.forecast-risk-tags {
  width: 100%;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}
.frt-label {
  font-size: var(--fs-xs);
  color: var(--text-2);
}
.frt-item {
  font-size: var(--fs-xs);
  color: #991b1b;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 999px;
  padding: 3px 8px;
}

.forecast-heatmap {
  margin-bottom: var(--sp-4);
  padding: var(--sp-4);
}
.fhm-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
  gap: 10px;
}
.fhm-item {
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface-2);
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  text-align: left;
  cursor: pointer;
}
.fhm-period { font-size: var(--fs-xs); color: var(--text-2); }
.fhm-score { font-size: var(--fs-sm); font-weight: 700; }
.fhm-bar {
  display: block;
  width: 100%;
  height: 6px;
  border-radius: 999px;
  background: rgba(0,0,0,.08);
  overflow: hidden;
}
.fhm-bar i {
  display: block;
  height: 100%;
  border-radius: 999px;
  background: currentColor;
}
.fhm-good { color: #15803d; border-color: #86efac; }
.fhm-mid { color: #b45309; border-color: #fcd34d; }
.fhm-low { color: #b91c1c; border-color: #fca5a5; }
.fhm-active { box-shadow: 0 0 0 2px rgba(217,119,6,.2) inset; }

/* ── 宫位工具栏 ─────────────────────────── */
.palaces-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-3);
  padding: var(--sp-3) var(--sp-4);
  background: var(--surface-2);
  border-radius: var(--radius-sm);
  margin-bottom: var(--sp-3);
}
.palaces-stats {
  display: flex;
  gap: var(--sp-4);
}
.palaces-stats .ps-item {
  font-size: var(--fs-sm);
  color: var(--text-2);
}
.palaces-stats .ps-item b { font-weight: 700; color: var(--accent); }
.palaces-filter {
  display: flex;
  align-items: center;
  gap: 4px;
  position: relative;
}
.palace-search-input {
  padding: 6px 28px 6px 10px;
  border: 1px solid var(--border-md);
  border-radius: var(--radius-sm);
  font-size: var(--fs-sm);
  width: 160px;
  background: #fff;
}
.palace-search-input:focus { outline: none; border-color: var(--accent); }
.palace-clear-btn {
  position: absolute;
  right: 6px;
  width: 18px;
  height: 18px;
  border: none;
  background: var(--surface-2);
  border-radius: 50%;
  font-size: 10px;
  color: var(--text-3);
  cursor: pointer;
}
.palace-clear-btn:hover { background: var(--border); color: var(--text); }

.palaces-quick-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: var(--sp-4);
}
.pqn-btn {
  padding: 4px 8px;
  font-size: var(--fs-xs);
  font-family: var(--font-cn);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text-2);
  cursor: pointer;
  transition: all 0.15s;
}
.pqn-btn:hover { border-color: var(--accent); color: var(--accent); }
.pqn-btn.pqn-active {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}

/* ── 大运时间线 ─────────────────────────── */
.dayun-summary-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: var(--sp-4);
  margin-bottom: var(--sp-4);
}
.dayun-range { font-size: var(--fs-sm); color: var(--text-2); }
.dayun-range b { color: var(--accent); font-weight: 600; }

.dayun-timeline {
  position: relative;
  display: flex;
  gap: 0;
  overflow-x: auto;
  padding: var(--sp-4) 0 var(--sp-6);
  margin-bottom: var(--sp-4);
}
.dt-line {
  position: absolute;
  top: 40px;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--border-md), var(--accent), var(--border-md));
  z-index: 0;
}
.dt-node {
  position: relative;
  flex: 1;
  min-width: 60px;
  display: flex;
  flex-direction: column;
  align-items: center;
  z-index: 1;
}
.dt-marker {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--surface);
  border: 3px solid var(--border-md);
  margin-top: 26px;
  transition: all 0.2s;
}
.dt-node.dt-cur .dt-marker {
  width: 18px;
  height: 18px;
  background: var(--accent);
  border-color: var(--accent);
  margin-top: 24px;
  box-shadow: 0 0 0 4px rgba(217,119,6,.2);
}
.dt-node.dt-past .dt-marker {
  background: var(--accent);
  border-color: var(--accent);
  opacity: 0.6;
}
.dt-label {
  margin-top: 10px;
  font-size: var(--fs-sm);
  font-weight: 700;
  font-family: var(--font-cn);
  color: var(--text);
}
.dt-node.dt-cur .dt-label { color: var(--accent); }
.dt-node.dt-past .dt-label { color: var(--text-2); }
.dt-age {
  font-size: var(--fs-xs);
  color: var(--text-2);
}
.dt-cur-badge {
  position: absolute;
  top: 0;
  font-size: 9px;
  padding: 1px 5px;
  background: var(--accent);
  color: #fff;
  border-radius: 4px;
  font-weight: 600;
}

/* ── 流年Tab增强样式 ────────────────────── */
.liunian-summary-card {
  margin-bottom: var(--sp-4);
}
.liunian-head {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--sp-3);
  margin-bottom: var(--sp-3);
}
.liunian-main {
  display: flex;
  align-items: baseline;
  gap: var(--sp-2);
}
.liunian-gz {
  font-size: var(--fs-2xl);
  font-weight: 800;
  font-family: var(--font-cn);
  color: var(--accent);
}
.liunian-year { font-size: var(--fs-md); color: var(--text-2); }
.liunian-cur-badge {
  font-size: var(--fs-xs);
  padding: 2px 8px;
  background: #dc2626;
  color: #fff;
  border-radius: 8px;
  font-weight: 600;
}
.liunian-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-3);
}
.liunian-meta-item {
  font-size: var(--fs-sm);
  color: var(--text-2);
}
.liunian-meta-item b { color: var(--text); font-weight: 600; }

.liunian-attrs {
  display: flex;
  gap: var(--sp-4);
  padding: var(--sp-3);
  background: var(--surface-2);
  border-radius: var(--radius-sm);
}
.liunian-insights {
  margin-top: var(--sp-3);
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.liunian-insight-tag {
  font-size: var(--fs-xs);
  color: var(--text-2);
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 3px 8px;
}
.la-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 50px;
}
.la-label { font-size: var(--fs-xs); color: var(--text-3); }
.la-value { font-size: var(--fs-lg); font-weight: 700; font-family: var(--font-cn); color: var(--text); }

.liunian-sihua-section { margin-bottom: var(--sp-4); }
.liunian-sihua-grid {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-3);
}
.liunian-sihua-card {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-3);
  background: var(--surface-2);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
}
.lss-star { font-size: var(--fs-md); font-weight: 600; font-family: var(--font-cn); }
.lss-tf { font-size: var(--fs-sm); font-weight: 700; padding: 2px 8px; border-radius: 6px; }

.liunian-forecast-link {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-3);
  padding: var(--sp-3) var(--sp-4);
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  border: 1px solid #fcd34d;
  border-radius: var(--radius-sm);
}
.lfl-hint { font-size: var(--fs-sm); color: #92400e; margin: 0; }
.lfl-score { font-size: var(--fs-sm); font-weight: 600; color: #78350f; }
.lfl-score span { font-size: var(--fs-lg); font-weight: 800; }

/* ── 流年英雄头部 ─────────────────────────────────────── */
.liunian-hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--sp-4);
  margin-bottom: var(--sp-4);
}
.lnh-left { flex: 1; min-width: 0; }
.lnh-gz {
  font-size: var(--fs-2xl);
  font-weight: 800;
  font-family: var(--font-cn);
  color: var(--accent);
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  flex-wrap: wrap;
}
.lnh-sub { font-size: var(--fs-md); color: var(--text-2); margin-top: var(--sp-1); }
.lnh-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-3);
  margin-top: var(--sp-2);
  font-size: var(--fs-sm);
  color: var(--text-2);
}
.lnh-meta b { color: var(--text); font-weight: 600; }
.lnh-attrs {
  display: flex;
  gap: var(--sp-4);
  padding: var(--sp-3);
  background: var(--surface-2);
  border-radius: var(--radius-sm);
  margin-top: var(--sp-3);
  flex-wrap: wrap;
}
.lnh-score-ring {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--sp-1);
}
.score-ring-svg { width: 84px; height: 84px; }
.score-ring-label { font-size: var(--fs-xs); color: var(--text-3); text-align: center; }

/* ── 年度运势详情 ─────────────────────────────────────── */
.liunian-forecast-full { margin-bottom: var(--sp-4); }
.lfy-overall {
  font-size: var(--fs-md);
  color: var(--text);
  line-height: 1.7;
  margin-bottom: var(--sp-3);
  padding: var(--sp-3) var(--sp-4);
  background: var(--surface-2);
  border-radius: var(--radius-sm);
  border-left: 3px solid var(--accent);
}
.lfy-details {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--sp-2);
  margin-bottom: var(--sp-3);
}
@media (max-width: 480px) { .lfy-details { grid-template-columns: 1fr; } }
.lfyd-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: var(--sp-2) var(--sp-3);
  background: var(--surface-2);
  border-radius: var(--radius-sm);
}
.lfyd-domain {
  font-size: var(--fs-xs);
  font-weight: 700;
  color: var(--text-3);
  letter-spacing: 0.04em;
}
.lfyd-text { font-size: var(--fs-sm); color: var(--text); line-height: 1.5; }
.lfy-events {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: var(--sp-3);
}
.lfye-item {
  display: flex;
  align-items: flex-start;
  gap: var(--sp-2);
  padding: 6px var(--sp-3);
  border-radius: var(--radius-sm);
  font-size: var(--fs-sm);
}
.lfy-advice {
  font-size: var(--fs-sm);
  color: #92400e;
  background: #fef3c7;
  border: 1px solid #fcd34d;
  border-radius: var(--radius-sm);
  padding: var(--sp-3);
  margin: 0;
}

/* ── 流年四化增强 ─────────────────────────────────────── */
.lsg-enhanced { gap: var(--sp-3); }
.lsc-enhanced {
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
  padding: var(--sp-3);
  min-width: 80px;
}
.lsc-top { display: flex; align-items: center; gap: var(--sp-2); }
.lss-palace { font-size: var(--fs-xs); color: var(--text-3); }

/* ── 十二月评分迷你柱状图 ────────────────────────────── */
.liunian-monthly-chart { margin-bottom: var(--sp-4); }
.lmc-bars {
  display: flex;
  align-items: flex-end;
  gap: 3px;
  height: 110px;
  padding-top: var(--sp-2);
  padding-bottom: 28px;
  position: relative;
}
.lmc-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
  justify-content: flex-end;
  position: relative;
}
.lmc-col.lmc-cur .lmc-bar { outline: 2px solid var(--accent); outline-offset: 1px; }
.lmc-col.lmc-cur .lmc-label { color: var(--accent); font-weight: 700; }
.lmc-bar-wrap {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  height: 80px;
  gap: 2px;
}
.lmc-bar {
  width: 100%;
  border-radius: 3px 3px 0 0;
  min-height: 6px;
  transition: height 0.3s ease;
}
.lmc-score {
  font-size: 9px;
  color: var(--text-3);
  line-height: 1;
  text-align: center;
}
.lmc-label {
  position: absolute;
  bottom: 0;
  font-size: 9px;
  color: var(--text-3);
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  max-width: 100%;
}

/* ── 当前月高亮 ────────────────────────────────────────── */
.liunian-curmonth {
  margin-bottom: var(--sp-4);
  border-left: 3px solid var(--accent);
}
.lcm-head {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  margin-bottom: var(--sp-2);
  flex-wrap: wrap;
}
.lcm-badge {
  font-size: var(--fs-xs);
  padding: 2px 8px;
  background: #dc2626;
  color: #fff;
  border-radius: 999px;
  font-weight: 600;
}
.lcm-gz {
  font-size: var(--fs-lg);
  font-weight: 700;
  font-family: var(--font-cn);
  color: var(--text);
}
.lcm-period { font-size: var(--fs-sm); color: var(--text-2); flex: 1; }
.lcm-score { font-size: var(--fs-md); font-weight: 700; }
.lcm-overall {
  font-size: var(--fs-sm);
  color: var(--text-2);
  line-height: 1.6;
  margin-bottom: var(--sp-2);
}
.lcm-advice {
  font-size: var(--fs-sm);
  color: #92400e;
  background: #fef3c7;
  border: 1px solid #fcd34d;
  border-radius: var(--radius-sm);
  padding: var(--sp-2) var(--sp-3);
  margin: var(--sp-2) 0 0;
}

/* ── 四柱八字详情展示 ────────────────────────────────── */
.bazi-detail-section { margin: var(--sp-4) 0; }
.bazi-head { margin-bottom: var(--sp-3); }

/* 菜单导航 */
.bazi-menu-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: var(--sp-4);
  padding-bottom: var(--sp-3);
  border-bottom: 1px solid var(--border);
}
.bazi-menu-btn {
  padding: 6px 12px;
  font-size: var(--fs-xs);
  font-family: var(--font-cn);
  background: var(--surface-2);
  color: var(--text-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.2s;
}
.bazi-menu-btn:hover { border-color: var(--accent); color: var(--accent); }
.bazi-menu-btn.active {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
  font-weight: 600;
}
.bazi-copy-btn {
  margin-left: auto;
  padding: 6px 12px;
  font-size: var(--fs-xs);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-md);
  background: var(--surface);
  color: var(--text-2);
  cursor: pointer;
  transition: all 0.2s;
}
.bazi-copy-btn:hover {
  border-color: var(--accent);
  color: var(--accent);
}

/* 面板内容 */
.bazi-content-panels { min-height: 100px; }
.bazi-panel { animation: fadeIn 0.3s ease-in; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

/* 生辰数据 */
.bazi-info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--sp-3);
}
@media (max-width: 480px) { .bazi-info-grid { grid-template-columns: 1fr; } }
.bazi-info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: var(--sp-2);
  background: var(--surface-2);
  border-radius: var(--radius-sm);
}
.bazi-label { font-size: var(--fs-xs); font-weight: 700; color: var(--text-3); }
.bazi-value { font-size: var(--fs-sm); color: var(--text); font-family: var(--font-cn); }

/* 十神关系 */
.bazi-daymaster { padding: var(--sp-3); }
.bazi-dm-info {
  display: flex;
  gap: var(--sp-3);
  align-items: center;
  padding: var(--sp-3);
  background: var(--surface-2);
  border-radius: var(--radius-sm);
  margin-bottom: var(--sp-3);
}
.bazi-dm-stem {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}
.bazi-dm-char { font-size: var(--fs-2xl); font-weight: 800; font-family: var(--font-cn); color: var(--accent); }
.bazi-dm-text { font-size: var(--fs-xs); color: var(--text-3); }
.bazi-dm-desc { font-size: var(--fs-sm); color: var(--text-2); }

.shishen-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  gap: var(--sp-2);
}
.shishen-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: var(--sp-2);
  background: var(--surface-2);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
}
.shishen-stem { font-size: var(--fs-lg); font-weight: 800; font-family: var(--font-cn); color: var(--accent); }
.shishen-relation { font-size: var(--fs-xs); color: var(--text-2); }

/* 藏干纳音 */
.canggan-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: var(--sp-3);
}
.canggan-col {
  padding: var(--sp-3);
  background: var(--surface-2);
  border-radius: var(--radius-sm);
}
.canggan-header { font-size: var(--fs-sm); font-weight: 700; margin-bottom: var(--sp-2); }
.canggan-item { display: flex; flex-direction: column; gap: var(--sp-2); }
.canggan-cg,
.canggan-ny {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px;
  background: var(--surface);
  border-radius: var(--radius-xs);
}
.canggan-label { font-size: var(--fs-xs); color: var(--text-3); font-weight: 700; }
.canggan-main {
  font-size: var(--fs-sm);
  font-weight: 700;
  font-family: var(--font-cn);
  color: var(--accent);
}
.canggan-aux {
  font-size: var(--fs-xs);
  color: var(--text-2);
}
.canggan-value { font-size: var(--fs-sm); color: var(--text); }
.bazi-simple-list {
  display: grid;
  gap: var(--sp-2);
}
.bazi-simple-card {
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: var(--sp-3);
}
.bsc-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-2);
  margin-bottom: 6px;
}
.bsc-name {
  font-size: var(--fs-sm);
  font-weight: 700;
  color: var(--text);
}
.bsc-badge {
  font-size: var(--fs-xs);
  padding: 2px 8px;
  border-radius: 999px;
  font-weight: 700;
}
.bsc-badge.ok { background: rgba(22, 163, 74, 0.15); color: #166534; }
.bsc-badge.mid { background: rgba(217, 119, 6, 0.15); color: #92400e; }
.bsc-badge.warn { background: rgba(220, 38, 38, 0.15); color: #991b1b; }
.bsc-sub {
  font-size: var(--fs-xs);
  color: var(--text-3);
  margin: 0 0 6px;
}
.bsc-text {
  margin: 0;
  font-size: var(--fs-sm);
  color: var(--text-2);
  line-height: 1.6;
}

.bazi-rel-wrap {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--sp-3);
}
@media (max-width: 640px) { .bazi-rel-wrap { grid-template-columns: 1fr; } }
.bazi-rel-col {
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: var(--sp-3);
}
.bazi-mini-title {
  margin: 0 0 var(--sp-2);
  font-size: var(--fs-sm);
  color: var(--text);
}
.bazi-rel-item {
  display: grid;
  grid-template-columns: 60px 58px 1fr;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  border-bottom: 1px dashed var(--border);
}
.bazi-rel-item:last-child { border-bottom: none; }
.bri-type { font-size: var(--fs-xs); font-weight: 700; color: var(--accent); }
.bri-pair { font-size: var(--fs-sm); font-family: var(--font-cn); color: var(--text); }
.bri-pillars { font-size: var(--fs-xs); color: var(--text-3); }

.bazi-tags-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
}
.btr-label { font-size: var(--fs-xs); color: var(--text-3); }
.btr-tag {
  font-size: var(--fs-xs);
  border-radius: 999px;
  padding: 2px 8px;
  font-weight: 700;
}
.btr-tag.good { background: rgba(22, 163, 74, 0.15); color: #166534; }
.btr-tag.bad { background: rgba(220, 38, 38, 0.15); color: #991b1b; }

.bazi-timeline {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: var(--sp-2);
  margin-top: var(--sp-3);
}
.btl-item {
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface-2);
  padding: var(--sp-2);
}
.btl-item.cur {
  border-color: var(--accent);
  box-shadow: 0 0 0 1px rgba(217, 119, 6, 0.2);
}
.btl-item.active {
  border-color: #2563eb;
  box-shadow: 0 0 0 1px rgba(37, 99, 235, 0.2);
  background: linear-gradient(135deg, var(--surface-2) 0%, rgba(37, 99, 235, 0.08) 100%);
}
.btl-gz { font-size: var(--fs-md); font-weight: 800; font-family: var(--font-cn); color: var(--accent); }
.btl-age, .btl-year { font-size: var(--fs-xs); color: var(--text-3); }
.bazi-dayun-detail { margin-top: var(--sp-3); }

.bazi-month-grid {
  margin-top: var(--sp-3);
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(95px, 1fr));
  gap: var(--sp-2);
}
.bmg-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-xs);
  padding: 6px;
}
.bmg-item.related {
  border-color: #2563eb;
  box-shadow: 0 0 0 1px rgba(37, 99, 235, 0.2);
  background: linear-gradient(135deg, var(--surface) 0%, rgba(37, 99, 235, 0.08) 100%);
}
.bmg-month { font-size: var(--fs-xs); color: var(--text-3); }
.bmg-gz { font-size: var(--fs-sm); color: var(--text); font-family: var(--font-cn); }
.bmg-palace { font-size: var(--fs-xs); color: var(--accent); }
.bmg-link {
  margin-top: 2px;
  font-size: var(--fs-xs);
  color: #1d4ed8;
  font-weight: 700;
}
.bazi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: var(--sp-3);
  margin-bottom: var(--sp-4);
}
.bazi-col {
  padding: var(--sp-3);
  background: var(--surface-2);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
}
.bazi-col-header {
  font-size: var(--fs-sm);
  font-weight: 700;
  color: var(--text-2);
  margin-bottom: var(--sp-2);
  display: flex;
  align-items: center;
  gap: var(--sp-1);
}
.bazi-jieqi-badge {
  font-size: var(--fs-xs);
  padding: 1px 6px;
  background: var(--accent);
  color: #fff;
  border-radius: 999px;
  font-weight: 600;
}
.bazi-item {
  display: flex;
  gap: 4px;
  margin-bottom: var(--sp-2);
}
.bazi-gz {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: var(--sp-2);
  background: var(--surface);
  border-radius: var(--radius-xs);
}
.bazi-char {
  font-size: var(--fs-lg);
  font-weight: 800;
  font-family: var(--font-cn);
  color: var(--accent);
}
.bazi-meaning {
  font-size: var(--fs-xs);
  color: var(--text-3);
  line-height: 1;
}
.bazi-meaning-text {
  font-size: var(--fs-xs);
  color: var(--text-2);
  padding-top: var(--sp-2);
  border-top: 1px solid var(--border);
}
.bazi-meaning-line {
  margin: 4px 0;
  line-height: 1.4;
}
.bazi-meaning-line b {
  color: var(--accent);
  font-weight: 700;
}

/* ── 五行统计 ────────────────────────────────────────── */
.bazi-wuxing-summary {
  padding: var(--sp-3);
  background: var(--surface-2);
  border-radius: var(--radius-sm);
}
.bazi-wuxing-grid {
  display: flex;
  gap: var(--sp-2);
  justify-content: space-around;
  margin-top: var(--sp-2);
}
.bazi-wx-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: var(--sp-2);
  background: var(--surface);
  border-radius: var(--radius-xs);
  border: 1px solid var(--border);
  opacity: 0.5;
  transition: all 0.2s;
}
.bazi-wx-item.bazi-wx-active {
  opacity: 1;
  border-color: var(--accent);
  background: linear-gradient(135deg, var(--surface) 0%, rgba(var(--accent-rgb), 0.05) 100%);
}
.bazi-wx-name {
  font-size: var(--fs-sm);
  font-weight: 700;
  font-family: var(--font-cn);
  color: var(--text);
}
.bazi-wx-count {
  font-size: var(--fs-lg);
  font-weight: 800;
  color: var(--accent);
}

/* ── 流月Tab增强样式 ────────────────────── */
.liuyue-stats {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-4);
  padding: var(--sp-3) var(--sp-4);
  background: var(--surface-2);
  border-radius: var(--radius-sm);
  margin-bottom: var(--sp-3);
}
.liuyue-stats .lys-item { font-size: var(--fs-sm); color: var(--text-2); }
.liuyue-stats .lys-item b { font-weight: 700; color: var(--accent); }

.liuyue-quick-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: var(--sp-4);
}
.lyq-btn {
  padding: 5px 10px;
  font-size: var(--fs-sm);
  font-family: var(--font-cn);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text-2);
  cursor: pointer;
  transition: all 0.15s;
}
.lyq-btn:hover { border-color: var(--accent); color: var(--accent); }
.lyq-btn.lyq-cur {
  background: #fef2f2;
  border-color: #fca5a5;
  color: #dc2626;
  font-weight: 600;
}
.lyq-btn.lyq-active {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}

/* ── 格局Tab分组样式 ────────────────────── */
.pattern-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-3);
  margin-bottom: var(--sp-4);
}
.pattern-view-toggle {
  display: flex;
  gap: 0;
  border: 1px solid var(--border-md);
  border-radius: var(--radius-sm);
  overflow: hidden;
}
.pvt-btn {
  padding: 5px 12px;
  font-size: var(--fs-sm);
  border: none;
  background: var(--surface);
  color: var(--text-2);
  cursor: pointer;
  transition: all 0.15s;
}
.pvt-btn:hover { background: var(--surface-2); }
.pvt-btn.active {
  background: var(--accent);
  color: #fff;
}
.pattern-focus-strip {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: var(--sp-4);
}
.pfs-label {
  font-size: var(--fs-xs);
  color: var(--text-2);
}
.pfs-item {
  font-size: var(--fs-xs);
  padding: 3px 9px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--surface-2);
  color: var(--text-2);
}
.pfs-item.level-high {
  color: #991b1b;
  background: #fee2e2;
  border-color: #fca5a5;
}
.pfs-item.level-med {
  color: #92400e;
  background: #fef3c7;
  border-color: #fcd34d;
}
.pfs-item.level-low {
  color: #334155;
  background: #f1f5f9;
  border-color: #cbd5e1;
}

.pattern-group {
  margin-bottom: var(--sp-5);
  border-radius: var(--radius-md);
  overflow: hidden;
}
.pg-header {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-3) var(--sp-4);
  font-weight: 600;
}
.pg-high .pg-header { background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); color: #92400e; }
.pg-med .pg-header { background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%); color: #3730a3; }
.pg-low .pg-header { background: var(--surface-2); color: var(--text-2); }
.pg-icon { font-size: var(--fs-lg); }
.pg-title { flex: 1; }
.pg-count {
  font-size: var(--fs-xs);
  padding: 2px 8px;
  background: rgba(255,255,255,.82);
  border-radius: 10px;
}
.pg-items {
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
  padding: var(--sp-3);
  background: var(--surface);
  border: 1px solid var(--border);
  border-top: none;
}

/* ── 飞星Tab工具栏 ──────────────────────── */
.flying-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-3);
  padding: var(--sp-3) var(--sp-4);
  background: var(--surface-2);
  border-radius: var(--radius-sm);
  margin-bottom: var(--sp-4);
}
.flying-filter {
  display: flex;
  align-items: center;
  gap: 4px;
}
.ff-label { font-size: var(--fs-sm); color: var(--text-2); margin-right: 4px; }
.ff-btn {
  padding: 4px 10px;
  font-size: var(--fs-sm);
  font-family: var(--font-cn);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text-2);
  cursor: pointer;
  transition: all 0.15s;
}
.ff-btn:hover { border-color: var(--accent); }
.ff-btn.active {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}
.ff-btn.ff-lu.active { background: #16a34a; border-color: #16a34a; }
.ff-btn.ff-quan.active { background: #dc2626; border-color: #dc2626; }
.ff-btn.ff-ke.active { background: #2563eb; border-color: #2563eb; }
.ff-btn.ff-ji.active { background: #1e293b; border-color: #1e293b; }

/* ══════════════════════════════════════════════════════════════════
   工具按钮样式
   ══════════════════════════════════════════════════════════════════ */
.btn-tool {
  background: transparent;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 4px 8px;
  font-size: var(--fs-sm);
  cursor: pointer;
  transition: all 0.15s;
}
.btn-tool:hover {
  background: var(--surface-2);
  border-color: var(--accent);
}

/* ══════════════════════════════════════════════════════════════════
   快捷键帮助面板
   ══════════════════════════════════════════════════════════════════ */
.hotkey-panel {
  position: fixed;
  top: 80px;
  right: 20px;
  width: 280px;
  z-index: 1000;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
}
.hp-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: var(--sp-3);
  border-bottom: 1px solid var(--border);
  margin-bottom: var(--sp-3);
}
.hp-title {
  font-size: var(--fs-md);
  font-weight: 700;
}
.hp-close {
  background: none;
  border: none;
  font-size: var(--fs-md);
  cursor: pointer;
  color: var(--text-3);
}
.hp-close:hover { color: var(--text); }
.hp-list {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}
.hp-item {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
}
.hp-key {
  display: inline-block;
  min-width: 50px;
  padding: 4px 8px;
  background: var(--surface-2);
  border: 1px solid var(--border-md);
  border-radius: var(--radius-sm);
  font-family: monospace;
  font-size: var(--fs-sm);
  text-align: center;
  color: var(--text);
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}
.hp-desc {
  font-size: var(--fs-sm);
  color: var(--text-2);
}

/* ══════════════════════════════════════════════════════════════════
   星曜亮度图例面板
   ══════════════════════════════════════════════════════════════════ */
.brightness-legend {
  position: fixed;
  top: 80px;
  right: 320px;
  width: 220px;
  z-index: 1000;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
}
.bl-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: var(--sp-3);
  border-bottom: 1px solid var(--border);
  margin-bottom: var(--sp-3);
}
.bl-title {
  font-size: var(--fs-md);
  font-weight: 700;
}
.bl-close {
  background: none;
  border: none;
  font-size: var(--fs-md);
  cursor: pointer;
  color: var(--text-3);
}
.bl-close:hover { color: var(--text); }
.bl-list {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}
.bl-item {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
}
.bl-level {
  display: inline-block;
  min-width: 36px;
  padding: 4px 8px;
  color: #fff;
  border-radius: var(--radius-sm);
  font-size: var(--fs-sm);
  font-weight: 700;
  text-align: center;
}
.bl-desc {
  font-size: var(--fs-sm);
  color: var(--text-2);
}
.bl-note {
  margin-top: var(--sp-3);
  padding-top: var(--sp-3);
  border-top: 1px solid var(--border);
  color: var(--text-3);
  line-height: 1.5;
}

/* ══════════════════════════════════════════════════════════════════
   星曜搜索弹窗
   ══════════════════════════════════════════════════════════════════ */
.star-search-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.4);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 100px;
  z-index: 1100;
}
.star-search-box {
  width: 400px;
  max-width: 90vw;
  max-height: 70vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 30px rgba(0,0,0,0.2);
}
.ss-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: var(--sp-3);
  border-bottom: 1px solid var(--border);
  margin-bottom: var(--sp-3);
}
.ss-title {
  font-size: var(--fs-md);
  font-weight: 700;
}
.ss-close {
  background: none;
  border: none;
  font-size: var(--fs-md);
  cursor: pointer;
  color: var(--text-3);
}
.ss-close:hover { color: var(--text); }
.star-search-input {
  width: 100%;
  padding: var(--sp-3);
  border: 1px solid var(--border-md);
  border-radius: var(--radius-sm);
  font-size: var(--fs-md);
  margin-bottom: var(--sp-3);
  outline: none;
}
.star-search-input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(217,119,6,0.15);
}
.ss-results {
  flex: 1;
  overflow-y: auto;
  max-height: 300px;
}
.ss-empty {
  text-align: center;
  padding: var(--sp-5);
  color: var(--text-3);
}
.ss-item {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-3);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background 0.15s;
}
.ss-item:hover {
  background: var(--surface-2);
}
.ss-star {
  font-weight: 700;
  font-family: var(--font-cn);
}
.ss-main { color: var(--accent); }
.ss-aux { color: var(--text-2); }
.ss-brightness {
  font-size: var(--fs-xs);
  padding: 1px 5px;
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: 4px;
  color: var(--text-3);
}
.ss-transforms {
  font-size: var(--fs-xs);
  color: #7c3aed;
}
.ss-palace {
  margin-left: auto;
  font-size: var(--fs-sm);
  color: var(--text-3);
}
.ss-hint {
  margin-top: var(--sp-3);
  padding-top: var(--sp-3);
  border-top: 1px solid var(--border);
  color: var(--text-3);
  text-align: center;
}

/* ══════════════════════════════════════════════════════════════════
   过渡动画
   ══════════════════════════════════════════════════════════════════ */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

.suggest-list { display: flex; flex-direction: column; gap: var(--sp-3); }
.suggest-item { padding: var(--sp-4); background: var(--surface-2); border-radius: var(--radius-sm); border: 1px solid var(--border); display: flex; flex-direction: column; gap: var(--sp-2); }
.suggest-head { display: flex; flex-wrap: wrap; align-items: center; gap: var(--sp-2); margin-bottom: var(--sp-1); }
.suggest-priority { font-size: var(--fs-xs); padding: 1px 6px; border-radius: 4px; font-weight: 700; }
.suggest-priority.priority-1 { background: #dc2626; color: #fff; }
.suggest-priority.priority-2 { background: #f59e0b; color: #fff; }
.suggest-priority.priority-3 { background: #3b82f6; color: #fff; }
.suggest-priority.priority-4, .suggest-priority.priority-5 { background: #6b7280; color: #fff; }
.suggest-domain { display: inline-block; font-size: var(--fs-xs); padding: 2px 8px; background: var(--surface); border: 1px solid var(--border-md); border-radius: 10px; color: var(--text-2); }
.suggest-cost { font-size: var(--fs-xs); padding: 2px 8px; background: #dbeafe; color: #1d4ed8; border-radius: 10px; }
.suggest-name { font-weight: 600; color: var(--text); font-size: var(--fs-md); }
.suggest-text { font-size: var(--fs-md); color: var(--text-2); line-height: 1.7; }
.suggest-actions { display: flex; flex-direction: column; gap: 2px; padding-left: var(--sp-3); }
.suggest-step { font-size: var(--fs-sm); color: var(--text-2); }
.suggest-evidence { font-size: var(--fs-sm); color: var(--text-3); font-style: italic; }
.suggest-notes { font-size: var(--fs-sm); color: var(--text-3); }
.suggest-scope { font-size: var(--fs-xs); color: var(--text-3); }
.suggest-disclaimer { font-size: var(--fs-xs); color: #b45309; background: #fef3c7; padding: var(--sp-2); border-radius: var(--radius-sm); margin-top: var(--sp-1); }

.muted { color: var(--text-3); font-size: var(--fs-sm); }

/* 结果页脚版本信息 */
.result-footer {
  display: flex;
  justify-content: center;
  gap: var(--sp-4);
  padding: var(--sp-4) 0;
  margin-top: var(--sp-6);
  border-top: 1px solid var(--border);
  font-size: var(--fs-xs);
  color: var(--text-3);
}
.ver-item { opacity: 0.7; }
.ver-item::before { content: "•"; margin-right: 4px; }
.ver-item:first-child::before { content: ""; margin-right: 0; }

/* ══════════════════════════════════════════════════════════════════
   历史记录面板
   ══════════════════════════════════════════════════════════════════ */
.history-panel {
  position: fixed;
  top: 80px;
  right: 20px;
  width: 300px;
  max-height: 400px;
  z-index: 1000;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.hist-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: var(--sp-3);
  border-bottom: 1px solid var(--border);
  margin-bottom: var(--sp-2);
}
.hist-title {
  font-size: var(--fs-md);
  font-weight: 700;
}
.hist-actions {
  display: flex;
  gap: var(--sp-2);
}
.hist-clear, .hist-close {
  background: none;
  border: none;
  font-size: var(--fs-md);
  cursor: pointer;
  color: var(--text-3);
}
.hist-clear:hover { color: #dc2626; }
.hist-close:hover { color: var(--text); }
.hist-empty {
  text-align: center;
  padding: var(--sp-5);
  color: var(--text-3);
}
.hist-list {
  flex: 1;
  overflow-y: auto;
}
.hist-item {
  padding: var(--sp-2) var(--sp-3);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background 0.15s;
  border-left: 3px solid transparent;
}
.hist-item:hover {
  background: var(--surface-2);
  border-left-color: var(--accent);
}
.hist-main {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
}
.hist-birth {
  font-weight: 600;
  font-size: var(--fs-sm);
}
.hist-gender {
  font-size: var(--fs-xs);
  padding: 1px 5px;
  background: var(--surface-2);
  border-radius: 4px;
  color: var(--text-3);
}
.hist-sub {
  display: flex;
  gap: var(--sp-2);
  margin-top: 2px;
}
.hist-palace, .hist-ju {
  font-size: var(--fs-xs);
  color: var(--text-2);
}
.hist-time {
  font-size: var(--fs-xs);
  color: var(--text-3);
  margin-top: 2px;
}
.history-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  font-size: 10px;
  background: var(--accent);
  color: #fff;
  min-width: 16px;
  height: 16px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
}
.btn-tool {
  position: relative;
}

/* ══════════════════════════════════════════════════════════════════
   星曜详情提示气泡
   ══════════════════════════════════════════════════════════════════ */
.star-tooltip {
  position: fixed;
  z-index: 1200;
  background: var(--surface);
  border: 1px solid var(--border-md);
  border-radius: var(--radius-sm);
  padding: var(--sp-2) var(--sp-3);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  min-width: 140px;
  max-width: 200px;
  pointer-events: none;
}
.st-name {
  font-size: var(--fs-md);
  font-weight: 700;
  color: var(--accent);
  font-family: var(--font-cn);
  margin-bottom: 4px;
}
.st-nature {
  font-size: var(--fs-xs);
  color: var(--text-2);
  margin-bottom: 2px;
}
.st-meaning {
  font-size: var(--fs-sm);
  color: var(--text);
  line-height: 1.4;
}

/* ══════════════════════════════════════════════════════════════════
   大运/流年/流月快速定位
   ══════════════════════════════════════════════════════════════════ */
.dayun-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 16px;
  padding: 12px;
  background: var(--bg-card);
  border-radius: 8px;
}
.dayun-locate-btn {
  padding: 6px 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--primary);
  color: #fff;
  font-size: var(--fs-sm);
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s;
}
.dayun-locate-btn:hover {
  filter: brightness(1.1);
}

/* 流年工具栏 */
.liunian-toolbar {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding: 12px;
  background: var(--bg-card);
  border-radius: 8px;
}
.liunian-year-picker {
  display: flex;
  align-items: center;
  gap: 8px;
}
.lyp-btn {
  width: 32px;
  height: 32px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--bg);
  color: var(--text);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}
.lyp-btn:hover {
  background: var(--primary);
  color: #fff;
  border-color: var(--primary);
}
.lyp-current {
  padding: 6px 16px;
  border: 2px solid var(--primary);
  border-radius: 8px;
  background: var(--bg);
  color: var(--text);
  font-size: var(--fs-md);
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
}
.lyp-current:hover {
  background: var(--primary-bg);
}
.lyp-cur-badge {
  font-size: 10px;
  padding: 1px 4px;
  background: var(--primary);
  color: #fff;
  border-radius: 3px;
}
.lyp-reset {
  padding: 6px 10px;
  border: 1px solid var(--green);
  border-radius: 6px;
  background: var(--green);
  color: #fff;
  font-size: var(--fs-sm);
  cursor: pointer;
  transition: all 0.2s;
}
.lyp-reset:hover {
  filter: brightness(1.1);
}

/* 年份选择面板 */
.year-picker-panel {
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  z-index: 100;
  width: 320px;
  max-height: 300px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.15);
  overflow: hidden;
}
.ypp-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-bottom: 1px solid var(--border);
  font-weight: 500;
}
.ypp-close {
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  color: var(--text-2);
  cursor: pointer;
  font-size: 14px;
}
.ypp-close:hover { color: var(--danger); }
.ypp-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 4px;
  padding: 8px;
  max-height: 240px;
  overflow-y: auto;
}
.ypp-item {
  padding: 6px 4px;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--bg);
  color: var(--text);
  font-size: var(--fs-sm);
  cursor: pointer;
  text-align: center;
  transition: all 0.15s;
}
.ypp-item:hover {
  background: var(--primary-bg);
  border-color: var(--primary);
}
.ypp-item.ypp-selected {
  background: var(--primary);
  color: #fff;
  border-color: var(--primary);
}
.ypp-item.ypp-current {
  border-color: var(--green);
  font-weight: 600;
}
.ypp-item.ypp-current:not(.ypp-selected) {
  background: rgba(34, 197, 94, 0.1);
}

/* 流月工具栏 */
.liuyue-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  padding: 8px 12px;
  background: var(--bg-card);
  border-radius: 8px;
}
.liuyue-summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: var(--sp-3);
  margin-bottom: var(--sp-3);
}
.lysc-item {
  padding: var(--sp-3);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  background: var(--surface-2);
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.lysc-label {
  font-size: var(--fs-xs);
  color: var(--text-3);
}
.lysc-value {
  font-size: var(--fs-md);
  font-weight: 700;
  color: var(--text);
}
.liuyue-locate-btn {
  padding: 6px 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--primary);
  color: #fff;
  font-size: var(--fs-sm);
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s;
}
.liuyue-locate-btn:hover {
  filter: brightness(1.1);
}

/* 高亮闪烁动画 */
@keyframes highlight-blink {
  0%, 100% { box-shadow: 0 0 0 0 transparent; }
  25%, 75% { box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.4); }
  50% { box-shadow: 0 0 0 8px rgba(59, 130, 246, 0.2); }
}
.highlight-blink {
  animation: highlight-blink 0.5s ease-in-out 3;
}



/* ══════════════════════════════════════════════════════════════════
   主题与字体控制
   ══════════════════════════════════════════════════════════════════ */
.visual-settings {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}
.vs-btn {
  width: 32px;
  height: 32px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--bg);
  font-size: 16px;
  cursor: pointer;
  transition: all 0.2s;
}
.vs-btn:hover {
  background: var(--primary-bg);
  border-color: var(--primary);
}
.font-size-btns {
  display: flex;
  gap: 2px;
}
.fs-btn {
  padding: 4px 8px;
  border: 1px solid var(--border);
  background: var(--bg);
  color: var(--text-2);
  font-size: 11px;
  cursor: pointer;
  transition: all 0.15s;
}
.fs-btn:first-child { border-radius: 4px 0 0 4px; }
.fs-btn:last-child { border-radius: 0 4px 4px 0; }
.fs-btn.active {
  background: var(--primary);
  color: #fff;
  border-color: var(--primary);
}
.fs-btn:hover:not(.active) {
  background: var(--primary-bg);
}

/* 主题选择面板 */
.theme-panel {
  position: absolute;
  top: 60px;
  right: 12px;
  z-index: 100;
  width: 280px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.15);
  overflow: hidden;
}
.tp-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  border-bottom: 1px solid var(--border);
  font-weight: 500;
}
.tp-close {
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  color: var(--text-2);
  cursor: pointer;
}
.tp-close:hover { color: var(--danger); }
.tp-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  padding: 12px;
}
.tp-item {
  padding: 10px;
  border: 2px solid var(--border);
  border-radius: 8px;
  background: var(--bg);
  cursor: pointer;
  text-align: center;
  transition: all 0.2s;
}
.tp-item:hover {
  border-color: var(--primary);
}
.tp-item.active {
  border-color: var(--primary);
  background: var(--primary-bg);
}
.tp-preview {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 4px;
  margin-bottom: 6px;
}
.tp-dot {
  width: 16px;
  height: 16px;
  border-radius: 50%;
}
.tp-bg {
  width: 24px;
  height: 16px;
  border-radius: 3px;
  border: 1px solid rgba(0,0,0,0.1);
}
.tp-name {
  font-size: var(--fs-sm);
  font-weight: 600;
  color: var(--text);
}
.tp-desc {
  font-size: 10px;
  color: var(--text-2);
}

/* ══════════════════════════════════════════════════════════════════
   四化追踪
   ══════════════════════════════════════════════════════════════════ */
.sihua-tracking-section {
  margin-top: var(--sp-4);
  padding-top: var(--sp-4);
  border-top: 1px solid var(--border);
}
.sihua-track-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-top: 12px;
}
.sihua-track-col {
  background: var(--bg);
  border-radius: 8px;
  overflow: hidden;
}
.stc-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 10px;
  font-weight: 600;
}
.stc-header.stc-禄 { background: rgba(34, 197, 94, 0.15); color: #15803d; }
.stc-header.stc-权 { background: rgba(234, 179, 8, 0.15); color: #a16207; }
.stc-header.stc-科 { background: rgba(139, 92, 246, 0.15); color: #7c3aed; }
.stc-header.stc-忌 { background: rgba(239, 68, 68, 0.15); color: #dc2626; }
.stc-type { font-size: var(--fs-md); }
.stc-count {
  font-size: var(--fs-xs);
  padding: 2px 6px;
  background: rgba(255,255,255,0.5);
  border-radius: 10px;
}
.stc-list {
  padding: 8px;
}
.stc-item {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 6px;
  margin-bottom: 4px;
  border-radius: 4px;
  font-size: var(--fs-sm);
  cursor: pointer;
  transition: background 0.15s;
}
.stc-item:hover { background: var(--primary-bg); }
.stc-star { font-weight: 500; color: var(--text); }
.stc-arrow { color: var(--text-2); font-size: 10px; }
.stc-palace { color: var(--text-2); }
.stc-empty { 
  color: var(--text-2); 
  font-size: var(--fs-xs); 
  text-align: center;
  padding: 8px;
}
.count-badge {
  font-size: var(--fs-xs);
  font-weight: normal;
  padding: 2px 6px;
  background: var(--primary);
  color: #fff;
  border-radius: 10px;
  margin-left: 6px;
}

/* ══════════════════════════════════════════════════════════════════
   星曜分布图
   ══════════════════════════════════════════════════════════════════ */
.star-distribution-section {
  margin-top: var(--sp-4);
  padding-top: var(--sp-4);
  border-top: 1px solid var(--border);
}
.star-dist-chart {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 4px;
  margin-top: 12px;
  padding: 12px;
  background: var(--bg);
  border-radius: 8px;
  min-height: 120px;
}
.sdc-bar-wrap {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  transition: transform 0.15s;
}
.sdc-bar-wrap:hover { transform: translateY(-2px); }
.sdc-bar {
  width: 100%;
  max-width: 32px;
  display: flex;
  flex-direction: column;
  border-radius: 4px 4px 0 0;
  overflow: hidden;
  position: relative;
}
.sdc-main {
  background: linear-gradient(180deg, #7c3aed 0%, #a78bfa 100%);
}
.sdc-aux {
  background: linear-gradient(180deg, #3b82f6 0%, #93c5fd 100%);
}
.sdc-count {
  position: absolute;
  top: 2px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 10px;
  font-weight: 600;
  color: #fff;
  text-shadow: 0 1px 2px rgba(0,0,0,0.3);
}
.sdc-label {
  font-size: 10px;
  color: var(--text-2);
  margin-top: 4px;
  white-space: nowrap;
}
.sdc-markers {
  display: flex;
  gap: 2px;
  margin-top: 2px;
}
.sdc-lu, .sdc-ji {
  font-size: 9px;
  padding: 1px 3px;
  border-radius: 2px;
}
.sdc-lu { background: rgba(34, 197, 94, 0.2); color: #15803d; }
.sdc-ji { background: rgba(239, 68, 68, 0.2); color: #dc2626; }
.sdc-legend {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 8px;
  font-size: var(--fs-xs);
  color: var(--text-2);
}
.sdc-leg-item {
  display: flex;
  align-items: center;
  gap: 4px;
}
.sdc-leg-main, .sdc-leg-aux {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}
.sdc-leg-main { background: linear-gradient(180deg, #7c3aed 0%, #a78bfa 100%); }
.sdc-leg-aux { background: linear-gradient(180deg, #3b82f6 0%, #93c5fd 100%); }

/* ══════════════════════════════════════════════════════════════════
   宫位快捷导航面板
   ══════════════════════════════════════════════════════════════════ */
.palace-quick-nav-panel {
  margin: 12px 0;
  padding: 8px 12px;
  background: var(--bg-card);
  border-radius: 8px;
  border: 1px solid var(--border);
}
.pqnp-row {
  display: flex;
  justify-content: space-between;
  gap: 4px;
}
.pqnp-btn {
  flex: 1;
  padding: 6px 4px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--bg);
  cursor: pointer;
  text-align: center;
  transition: all 0.15s;
  position: relative;
}
.pqnp-btn:hover {
  background: var(--primary-bg);
  border-color: var(--primary);
}
.pqnp-btn.pqnp-selected {
  background: var(--primary);
  color: #fff;
  border-color: var(--primary);
}
.pqnp-btn.pqnp-life { border-left: 3px solid var(--danger); }
.pqnp-btn.pqnp-body { border-left: 3px solid var(--primary); }
.pqnp-btn.pqnp-has-lu::after {
  content: '禄';
  position: absolute;
  top: 2px;
  right: 2px;
  font-size: 8px;
  color: #22c55e;
}
.pqnp-btn.pqnp-has-ji::before {
  content: '忌';
  position: absolute;
  top: 2px;
  left: 2px;
  font-size: 8px;
  color: #ef4444;
}
.pqnp-name {
  display: block;
  font-size: var(--fs-sm);
  font-weight: 500;
}
.pqnp-count {
  display: block;
  font-size: 10px;
  color: var(--text-2);
  margin-top: 2px;
}
.pqnp-btn.pqnp-selected .pqnp-count { color: rgba(255,255,255,0.8); }

/* ══════════════════════════════════════════════════════════════════
   五行分布图
   ══════════════════════════════════════════════════════════════════ */
.wuxing-distribution-section {
  margin-top: var(--sp-4);
  padding-top: var(--sp-4);
  border-top: 1px solid var(--border);
}
.wuxing-dist-chart {
  display: flex;
  justify-content: center;
  align-items: flex-end;
  gap: 20px;
  margin-top: 12px;
  padding: 16px;
  background: var(--bg);
  border-radius: 8px;
  min-height: 100px;
}
.wdc-bar-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 48px;
}
.wdc-bar {
  width: 36px;
  border-radius: 4px 4px 0 0;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 4px;
  transition: height 0.3s;
}
.wdc-count {
  font-size: 11px;
  font-weight: 600;
  color: #fff;
  text-shadow: 0 1px 2px rgba(0,0,0,0.3);
}
.wdc-label {
  font-size: var(--fs-md);
  font-weight: 600;
  margin-top: 6px;
}
.wdc-stars {
  font-size: 10px;
  color: var(--text-2);
  margin-top: 2px;
  max-width: 60px;
  text-align: center;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.wuxing-summary {
  text-align: center;
  margin-top: 12px;
  font-size: var(--fs-sm);
  color: var(--text-2);
}
.ws-item b { font-size: var(--fs-md); }

/* ══════════════════════════════════════════════════════════════════
   分享面板
   ══════════════════════════════════════════════════════════════════ */


.share-panel {
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  z-index: 100;
  width: 280px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.15);
  margin-top: 8px;
}
.sp-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  border-bottom: 1px solid var(--border);
  font-weight: 500;
}
.sp-close {
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  color: var(--text-2);
  cursor: pointer;
}
.sp-close:hover { color: var(--danger); }
.sp-content {
  padding: 12px;
  display: flex;
  gap: 8px;
}
.sp-link-input {
  flex: 1;
  padding: 8px 10px;
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: var(--fs-xs);
  background: var(--bg);
  color: var(--text);
}
.sp-copy-btn {
  padding: 8px 12px;
  background: var(--primary);
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: var(--fs-xs);
  cursor: pointer;
  white-space: nowrap;
}
.sp-copy-btn:hover { filter: brightness(1.1); }
.sp-hint {
  padding: 0 14px 12px;
  font-size: 11px;
  color: var(--text-2);
  margin: 0;
}

.cases-panel {
  position: absolute;
  top: 100%;
  right: 0;
  z-index: 100;
  width: 360px;
  max-height: 65vh;
  display: flex;
  flex-direction: column;
  margin-top: 8px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.16);
  overflow: hidden;
}
.cp-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  border-bottom: 1px solid var(--border);
  font-weight: 600;
  color: #1d4ed8;
}
.cp-close {
  border: none;
  background: transparent;
  color: var(--text-2);
  cursor: pointer;
}
.cp-toolbar {
  display: flex;
  gap: 8px;
  padding: 12px 14px 8px;
}
.cp-search-input {
  flex: 1;
  min-width: 0;
  padding: 8px 10px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg);
  color: var(--text);
  font-size: var(--fs-sm);
}
.cp-search-btn,
.cp-load-btn,
.cp-del-btn,
.cp-page-btn {
  padding: 7px 10px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--surface);
  cursor: pointer;
  font-size: var(--fs-xs);
}
.cp-search-btn,
.cp-load-btn { color: #1d4ed8; }
.cp-del-btn { color: #dc2626; }
.cp-summary {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  padding: 0 14px 10px;
  color: var(--text-2);
  font-size: var(--fs-xs);
}
.cp-current {
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.cp-state {
  padding: 18px 14px;
  text-align: center;
  color: var(--text-2);
  font-size: var(--fs-sm);
}
.cp-error { color: #dc2626; }
.cp-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 0 14px 12px;
  overflow-y: auto;
}
.cp-item {
  display: flex;
  gap: 10px;
  padding: 10px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--bg);
}
.cp-item-main {
  flex: 1;
  min-width: 0;
  cursor: pointer;
}
.cp-name-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}
.cp-name {
  font-weight: 600;
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.cp-badge {
  padding: 2px 6px;
  border-radius: 999px;
  background: #dbeafe;
  color: #1d4ed8;
  font-size: 10px;
  flex-shrink: 0;
}
.cp-meta {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  font-size: var(--fs-xs);
  color: var(--text-2);
}
.cp-meta-muted {
  margin-top: 4px;
}
.cp-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.cp-pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px 14px;
  border-top: 1px solid var(--border);
  font-size: var(--fs-xs);
  color: var(--text-2);
}

.snapshots-panel {
  position: absolute;
  top: 100%;
  right: 0;
  z-index: 100;
  width: 420px;
  max-height: 70vh;
  display: flex;
  flex-direction: column;
  margin-top: 8px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.16);
  overflow: hidden;
}
.snp-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  border-bottom: 1px solid var(--border);
  color: #c2410c;
  font-weight: 600;
}
.snp-close {
  border: none;
  background: transparent;
  color: var(--text-2);
  cursor: pointer;
}
.snp-summary {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;
  padding: 10px 14px;
  font-size: var(--fs-xs);
  color: var(--text-2);
}
.snp-state {
  padding: 18px 14px;
  text-align: center;
  color: var(--text-2);
  font-size: var(--fs-sm);
}
.snp-error,
.snp-diff-error { color: #dc2626; }
.snp-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 0 14px 12px;
  overflow-y: auto;
}
.snp-item {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  padding: 10px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--bg);
}
.snp-item-main {
  flex: 1;
  min-width: 0;
}
.snp-item-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.snp-kind {
  font-weight: 600;
  color: var(--text);
}
.snp-current {
  padding: 2px 6px;
  border-radius: 999px;
  background: #ffedd5;
  color: #c2410c;
  font-size: 10px;
}
.snp-meta,
.snp-note,
.snp-diff-summary,
.snp-diff-extra,
.snp-diff-values {
  margin-top: 4px;
  font-size: var(--fs-xs);
  color: var(--text-2);
}
.snp-load-btn,
.snp-compare-btn {
  padding: 7px 10px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--surface);
  cursor: pointer;
  font-size: var(--fs-xs);
}
.snp-load-btn { color: #c2410c; }
.snp-compare-btn:disabled { opacity: .6; cursor: not-allowed; }
.snp-compare-box {
  border-top: 1px solid var(--border);
  padding: 12px 14px 14px;
}
.snp-compare-title {
  font-weight: 600;
  color: var(--text);
  margin-bottom: 8px;
}
.snp-compare-controls {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.snp-select {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg);
  color: var(--text);
}
.snp-diff-result {
  margin-top: 10px;
  padding: 10px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--bg);
}
.snp-diff-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 8px;
}
.snp-diff-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.snp-diff-field {
  font-size: var(--fs-xs);
  font-weight: 600;
  color: var(--text);
}

.similar-panel {
  position: absolute;
  top: 100%;
  right: 0;
  z-index: 100;
  width: 390px;
  max-height: 68vh;
  display: flex;
  flex-direction: column;
  margin-top: 8px;
  padding: 0;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.16);
  overflow: hidden;
}
.simp-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  border-bottom: 1px solid var(--border);
  color: #4338ca;
  font-weight: 600;
}
.simp-close {
  border: none;
  background: transparent;
  color: var(--text-2);
  cursor: pointer;
}
.simp-query {
  padding: 12px 14px 8px;
  font-size: var(--fs-xs);
  line-height: 1.6;
  color: var(--text-2);
}
.simp-toolbar {
  display: flex;
  align-items: end;
  gap: 8px;
  padding: 0 14px 10px;
  flex-wrap: wrap;
}
.simp-topk {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: var(--fs-xs);
  color: var(--text-2);
}
.simp-topk select {
  min-width: 72px;
  padding: 7px 8px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg);
}
.simp-btn {
  padding: 7px 12px;
  border: 1px solid #c7d2fe;
  border-radius: 8px;
  background: #eef2ff;
  color: #4338ca;
  cursor: pointer;
  font-size: var(--fs-xs);
}
.simp-btn-soft {
  background: var(--surface);
  color: var(--text-2);
  border-color: var(--border);
}
.simp-btn:disabled {
  opacity: .6;
  cursor: not-allowed;
}
.simp-status {
  padding: 0 14px 8px;
  font-size: var(--fs-xs);
  color: var(--text-2);
}
.simp-badge {
  margin: 0 14px 10px;
  align-self: flex-start;
  padding: 4px 8px;
  border-radius: 999px;
  background: #eef2ff;
  color: #4338ca;
  font-size: 11px;
}
.simp-empty {
  padding: 18px 14px;
  color: var(--text-2);
  font-size: var(--fs-sm);
  text-align: center;
}
.simp-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 0 14px 14px;
  overflow-y: auto;
}
.simp-card {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 12px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--bg);
}
.simp-score {
  flex-shrink: 0;
  min-width: 58px;
  height: 58px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-weight: 700;
  font-size: var(--fs-sm);
  background: #f3f4f6;
  color: #4b5563;
}
.simp-score.is-high {
  background: #dcfce7;
  color: #15803d;
}
.simp-score.is-mid {
  background: #fef3c7;
  color: #b45309;
}
.simp-score.is-low {
  background: #fee2e2;
  color: #b91c1c;
}
.simp-main {
  flex: 1;
  min-width: 0;
}
.simp-title-row {
  display: flex;
  gap: 8px;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
}
.simp-title {
  font-weight: 600;
  color: var(--text);
}
.simp-level {
  font-size: 11px;
  color: #4338ca;
  background: #eef2ff;
  padding: 2px 6px;
  border-radius: 999px;
}
.simp-meta,
.simp-patterns {
  margin-top: 4px;
  font-size: var(--fs-xs);
  color: var(--text-2);
  line-height: 1.5;
}

.review-panel-zw,
.llm-panel-zw,
.ops-panel-zw,
.batch-panel-zw,
.glossary-panel-zw,
.mcp-panel-zw,
.fengshui-panel-zw {
  position: absolute;
  top: 100%;
  right: 0;
  z-index: 100;
  width: 420px;
  max-height: 72vh;
  display: flex;
  flex-direction: column;
  margin-top: 8px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.16);
  overflow: hidden;
}

.rvp-header,
.lzp-header,
.ozp-header,
.bzp-header,
.gzp-header,
.mcz-header,
.fsp-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  border-bottom: 1px solid var(--border);
  font-weight: 700;
}

.rvp-header { color: #166534; }
.lzp-header { color: #7e22ce; }
.ozp-header { color: #1d4ed8; }
.bzp-header { color: #9a3412; }
.gzp-header { color: #a21caf; }
.mcz-header { color: #0369a1; }
.fsp-header { color: #0f766e; }

.rvp-close,
.lzp-close,
.ozp-close,
.bzp-close,
.gzp-close,
.mcz-close,
.fsp-close {
  border: none;
  background: transparent;
  color: var(--text-2);
  cursor: pointer;
}

.rvp-toolbar,
.lzp-toolbar,
.ozp-toolbar,
.bzp-toolbar,
.gzp-toolbar,
.mcz-actions,
.fsp-toolbar,
.fsp-room-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
  padding: 12px 14px 8px;
}

.rvp-select,
.lzp-select,
.ozp-select,
.rvp-submit-notes,
.rvp-detail-notes,
.ozp-input,
.ozp-textarea,
.bzp-template-input,
.gzp-input,
.gzp-select,
.mcz-input,
.fsp-input,
.fsp-select,
.fsp-room-select {
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg);
}

.rvp-select,
.lzp-select,
.ozp-select,
.ozp-input,
.bzp-template-input,
.gzp-input,
.gzp-select,
.mcz-input,
.fsp-input,
.fsp-select,
.fsp-room-select {
  padding: 7px 8px;
  min-width: 96px;
}

.ozp-textarea {
  width: 100%;
  padding: 8px 10px;
  resize: vertical;
}

.rvp-btn,
.lzp-btn,
.ozp-btn,
.bzp-btn,
.gzp-btn,
.mcz-btn,
.fsp-btn,
.rvp-btn-soft,
.rvp-btn-ok,
.rvp-btn-warn,
.rvp-btn-danger,
.lzp-btn-ok,
.lzp-btn-danger,
.ozp-btn-soft,
.ozp-btn-warn,
.ozp-btn-danger,
.mcz-btn-soft,
.mcz-del-btn,
.fsp-btn-soft {
  padding: 7px 12px;
  border-radius: 8px;
  font-size: var(--fs-xs);
  cursor: pointer;
  border: 1px solid transparent;
}

.rvp-btn,
.rvp-btn-ok,
.lzp-btn,
.lzp-btn-ok,
.ozp-btn,
.bzp-btn,
.gzp-btn,
.mcz-btn {
  background: #ecfdf5;
  color: #166534;
  border-color: #86efac;
}

.ozp-btn,
.bzp-btn,
.fsp-btn {
  background: #eff6ff;
  color: #1d4ed8;
  border-color: #93c5fd;
}

.gzp-btn {
  background: #fdf4ff;
  color: #a21caf;
  border-color: #f0abfc;
}

.mcz-btn {
  background: #f0f9ff;
  color: #0369a1;
  border-color: #7dd3fc;
}

.fsp-btn {
  background: #ecfeff;
  color: #0f766e;
  border-color: #5eead4;
}

.rvp-btn-soft,
.lzp-btn-soft,
.ozp-btn-soft,
.bzp-btn-soft,
.mcz-btn-soft,
.fsp-btn-soft {
  background: var(--surface);
  color: var(--text-2);
  border-color: var(--border);
}

.rvp-btn-warn,
.ozp-btn-warn {
  background: #fffbeb;
  color: #b45309;
  border-color: #fcd34d;
}

.rvp-btn-danger,
.lzp-btn-danger,
.ozp-btn-danger {
  background: #fef2f2;
  color: #b91c1c;
  border-color: #fca5a5;
}

.rvp-btn:disabled,
.lzp-btn:disabled,
.ozp-btn:disabled,
.bzp-btn:disabled,
.gzp-btn:disabled,
.mcz-btn:disabled,
.fsp-btn:disabled,
.rvp-btn-soft:disabled,
.rvp-btn-ok:disabled,
.rvp-btn-warn:disabled,
.rvp-btn-danger:disabled,
.lzp-btn-ok:disabled,
.lzp-btn-danger:disabled,
.ozp-btn-soft:disabled,
.ozp-btn-warn:disabled,
.ozp-btn-danger:disabled,
.bzp-btn-soft:disabled,
.mcz-btn-soft:disabled,
.mcz-del-btn:disabled {
  opacity: .6;
  cursor: not-allowed;
}

.rvp-stats,
.lzp-config,
.lzp-status,
.ozp-status,
.bzp-status,
.gzp-state,
.mcz-empty,
.mcz-error,
.fsp-error {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  padding: 0 14px 10px;
  font-size: var(--fs-xs);
  color: var(--text-2);
}

.rvp-mode-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 0 14px 10px;
}

.rvp-mode-title {
  font-weight: 700;
  color: var(--text);
}

.rvp-mode-desc {
  font-size: var(--fs-xs);
  color: var(--text-2);
}

.panel-feedback,
.panel-tip {
  margin: 0 14px 10px;
  padding: 9px 12px;
  border-radius: 10px;
  font-size: var(--fs-xs);
  line-height: 1.6;
}

.panel-feedback {
  border: 1px solid #bfdbfe;
  background: #eff6ff;
  color: #1d4ed8;
}

.panel-feedback.success {
  border-color: #86efac;
  background: #ecfdf5;
  color: #166534;
}

.panel-feedback.info {
  border-color: #93c5fd;
  background: #eff6ff;
  color: #1d4ed8;
}

.panel-feedback.error {
  border-color: #fca5a5;
  background: #fef2f2;
  color: #b91c1c;
}

.panel-tip {
  border: 1px dashed var(--border);
  background: var(--surface);
  color: var(--text-2);
}

.rvp-submit-notes,
.rvp-detail-notes {
  width: calc(100% - 28px);
  margin: 0 14px 10px;
  padding: 8px 10px;
  resize: vertical;
}

.rvp-assign-box {
  margin: 0 14px 10px;
  padding: 12px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--bg);
}

.rvp-assign-title {
  font-size: var(--fs-xs);
  font-weight: 700;
  color: var(--text);
}

.rvp-assign-presets,
.rvp-assign-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 10px;
}

.rvp-assign-chip {
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text-2);
  border-radius: 999px;
  padding: 5px 10px;
  cursor: pointer;
}

.rvp-assign-chip.active {
  border-color: #93c5fd;
  background: #eff6ff;
  color: #1d4ed8;
}

.rvp-assign-input {
  flex: 1 1 180px;
  min-width: 180px;
  padding: 8px 10px;
}

.rvp-state,
.lzp-empty,
.rvp-history-state,
.ozp-state {
  padding: 16px 14px;
  text-align: center;
  color: var(--text-2);
  font-size: var(--fs-sm);
}

.rvp-error,
.ozp-error,
.bzp-error { color: #b91c1c; }

.rvp-layout {
  display: grid;
  grid-template-columns: 150px 1fr;
  min-height: 260px;
  border-top: 1px solid var(--border);
}

.rvp-list,
.rvp-detail,
.lzp-list {
  overflow-y: auto;
}

.rvp-list {
  border-right: 1px solid var(--border);
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.rvp-mode-switch {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--bg);
}

.rvp-mode-btn {
  border: 0;
  background: transparent;
  color: var(--text-2);
  padding: 6px 10px;
  border-radius: 999px;
  cursor: pointer;
}

.rvp-mode-btn.active {
  background: rgba(59, 130, 246, 0.12);
  color: #2563eb;
  font-weight: 600;
}

.rvp-item,
.lzp-item {
  width: 100%;
  text-align: left;
  padding: 10px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--bg);
  cursor: pointer;
}

.rvp-bulk-box {
  margin: 0 14px 10px;
  padding: 12px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--bg);
}

.rvp-bulk-top,
.rvp-bulk-actions,
.rvp-item-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.rvp-bulk-top {
  justify-content: space-between;
}

.rvp-bulk-count {
  font-size: var(--fs-xs);
  color: var(--text-2);
}

.rvp-bulk-hint {
  margin-top: 10px;
  font-size: var(--fs-xs);
  color: var(--text-2);
  line-height: 1.6;
}

.rvp-bulk-strong-hint {
  margin-top: 10px;
  padding: 8px 10px;
  border-radius: 10px;
  border: 1px solid #86efac;
  background: #ecfdf5;
  color: #166534;
  font-size: var(--fs-xs);
  line-height: 1.6;
}

.rvp-bulk-notes {
  width: 100%;
  margin-top: 10px;
  padding: 8px 10px;
  resize: vertical;
}

.rvp-bulk-actions {
  flex-wrap: wrap;
  margin-top: 10px;
}

.rvp-item.active {
  border-color: #86efac;
  box-shadow: 0 0 0 1px rgba(34, 197, 94, 0.18);
}

.rvp-item.selected-bulk {
  border-color: #93c5fd;
  box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.18);
}

.rvp-item.claimed-me {
  background: linear-gradient(180deg, #f0fdf4 0%, var(--bg) 100%);
}

.rvp-item-top,
.lzp-item-top,
.lzp-current-head,
.rvp-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.rvp-item-id,
.rvp-detail-title,
.lzp-list-title {
  font-weight: 700;
  color: var(--text);
}

.rvp-item-status,
.lzp-item-status,
.lzp-current-tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--surface-2);
  color: var(--text-2);
}

.rvp-item-status.is-pending {
  background: #eff6ff;
  color: #1d4ed8;
}

.rvp-item-status.is-approved {
  background: #ecfdf5;
  color: #166534;
}

.rvp-item-status.is-rejected {
  background: #fef2f2;
  color: #b91c1c;
}

.rvp-item-status.is-revised {
  background: #fffbeb;
  color: #b45309;
}

.rvp-item-status.is-unknown {
  background: var(--surface-2);
  color: var(--text-2);
}

.rvp-item-meta-row,
.rvp-detail-meta-rich {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.rvp-owner-tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 11px;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text-2);
}

.rvp-owner-tag.is-mine {
  border-color: #86efac;
  background: #ecfdf5;
  color: #166534;
}

.rvp-owner-tag.is-assigned {
  border-color: #bfdbfe;
  background: #eff6ff;
  color: #1d4ed8;
}

.rvp-owner-tag.is-unassigned {
  border-color: #e5e7eb;
  background: #f9fafb;
  color: #6b7280;
}

.rvp-history-meta-rich {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.rvp-history-tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 11px;
  border: 1px solid var(--border);
}

.rvp-history-tag.is-created {
  background: #eff6ff;
  border-color: #bfdbfe;
  color: #1d4ed8;
}

.rvp-history-tag.is-status {
  background: #ecfdf5;
  border-color: #86efac;
  color: #166534;
}

.rvp-history-tag.is-bulk {
  background: #f5f3ff;
  border-color: #c4b5fd;
  color: #6d28d9;
}

.rvp-history-tag.is-assign {
  background: #fffbeb;
  border-color: #fcd34d;
  color: #b45309;
}

.rvp-history-tag.is-deleted {
  background: #fef2f2;
  border-color: #fca5a5;
  color: #b91c1c;
}

.rvp-history-tag.is-default {
  background: var(--surface);
  border-color: var(--border);
  color: var(--text-2);
}

.rvp-item-meta,
.rvp-detail-meta,
.rvp-history-meta,
.lzp-item-time {
  margin-top: 4px;
  font-size: var(--fs-xs);
  color: var(--text-2);
}

.rvp-item-check {
  margin: 0;
}

.rvp-detail,
.lzp-current-box {
  padding: 12px 14px 14px;
}

.rvp-history-title {
  margin-top: 8px;
  font-weight: 600;
  color: var(--text);
}

.rvp-history-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 8px;
}

.rvp-history-item {
  padding: 8px 10px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg);
}

.rvp-history-note,
.lzp-item-preview {
  margin-top: 4px;
  font-size: var(--fs-xs);
  line-height: 1.6;
  color: var(--text);
}

.lzp-current-box {
  margin: 0 14px 12px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--bg);
}

.lzp-current-text {
  margin: 10px 0 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: var(--fs-sm);
  line-height: 1.7;
  color: var(--text);
  font-family: inherit;
}

.lzp-copy-row {
  display: flex;
  justify-content: flex-end;
  margin-top: 10px;
}

.lzp-reviewer-notes {
  width: 100%;
  margin-top: 10px;
  padding: 8px 10px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg);
  resize: vertical;
}

.lzp-current-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.lzp-list-title {
  padding: 0 14px 8px;
}

.lzp-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 0 14px 14px;
}

.ops-panel-zw,
.batch-panel-zw,
.glossary-panel-zw,
.mcp-panel-zw,
.fengshui-panel-zw {
  width: 430px;
}

.gzp-toolbar,
.gzp-list,
.mcz-person-list,
.mcz-result-box {
  padding: 0 14px 14px;
}

.gzp-toolbar {
  padding-top: 12px;
}

.gzp-list,
.mcz-person-list,
.mcz-result-box {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 50vh;
  overflow-y: auto;
}

.gzp-item,
.mcz-current-card,
.mcz-person-card,
.mcz-score-card,
.mcz-pair-item {
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--bg);
  padding: 12px;
}

.gzp-item-top,
.mcz-person-top,
.mcz-pair-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.gzp-term,
.mcz-current-title,
.mcz-person-title {
  font-weight: 700;
  color: var(--text);
}

.gzp-item-actions,
.gzp-related,
.gzp-suggest-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.gzp-cat,
.mcz-pair-level,
.mcz-del-btn {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--surface-2);
  color: var(--text-2);
  border: none;
}

.gzp-pinyin,
.gzp-source,
.mcz-current-meta {
  margin-top: 4px;
  font-size: var(--fs-xs);
  color: var(--text-2);
}

.gzp-suggest-row {
  padding: 0 14px 12px;
}

.gzp-suggest-label,
.gzp-related-label {
  font-size: var(--fs-xs);
  color: var(--text-2);
}

.gzp-copy-btn,
.gzp-suggest-chip,
.gzp-related-chip {
  border: 1px solid var(--border);
  border-radius: 999px;
  background: #fff;
  color: var(--text);
  cursor: pointer;
}

.gzp-copy-btn {
  padding: 4px 10px;
  font-size: 11px;
}

.gzp-suggest-chip,
.gzp-related-chip {
  padding: 4px 10px;
  font-size: var(--fs-xs);
}

.gzp-def {
  margin-top: 8px;
  font-size: var(--fs-sm);
  line-height: 1.7;
  color: var(--text);
}

.gzp-related {
  margin-top: 10px;
}

.mcz-current-card,
.mcz-actions,
.mcz-error {
  margin: 0 14px 12px;
}

.mcz-form-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin-top: 10px;
}

.mcz-input-wide {
  grid-column: span 3;
}

.mcz-score-card {
  text-align: center;
}

.mcz-score-num {
  font-size: 28px;
  font-weight: 700;
  color: #0369a1;
}

.mcz-score-label {
  margin-top: 4px;
  font-size: var(--fs-sm);
  color: var(--text-2);
}

.mcz-summary-banner {
  padding: 10px 12px;
  border: 1px solid #bae6fd;
  border-radius: 12px;
  background: #f0f9ff;
  font-size: var(--fs-sm);
  color: #0c4a6e;
}

.mcz-advice-box {
  padding: 12px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--bg);
}

.mcz-advice-title {
  font-weight: 700;
  color: var(--text);
}

.mcz-advice-list {
  margin: 8px 0 0;
  padding-left: 18px;
  font-size: var(--fs-sm);
  color: var(--text);
}

.mcz-legend {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
}

.mcz-legend-title,
.fsp-legend-title {
  font-size: var(--fs-xs);
  color: var(--text-2);
}

.mcz-legend-chip {
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 11px;
  border: 1px solid var(--border);
}

.mcz-matrix-wrap {
  overflow-x: auto;
}

.mcz-matrix {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--fs-xs);
}

.mcz-matrix th,
.mcz-matrix td {
  padding: 8px;
  border: 1px solid var(--border);
  text-align: center;
}

.mcz-matrix td.is-self {
  background: #f8fafc;
  color: var(--text-2);
}

.mcz-matrix td.is-score.is-excellent,
.mcz-pair-item.is-excellent {
  background: #ecfdf5;
}

.mcz-matrix td.is-score.is-good,
.mcz-pair-item.is-good {
  background: #f0fdf4;
}

.mcz-matrix td.is-score.is-fair,
.mcz-pair-item.is-fair {
  background: #fffbeb;
}

.mcz-matrix td.is-score.is-low,
.mcz-pair-item.is-low {
  background: #fef2f2;
}

.mcz-matrix td.is-best-pair {
  box-shadow: inset 0 0 0 2px #0ea5e9;
  font-weight: 700;
}

.mcz-pairs {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 8px;
}

.fsp-result-box,
.fsp-room-box {
  padding: 0 14px 14px;
}

.fsp-summary-card,
.fsp-box,
.fsp-tip-card,
.fsp-room-box,
.fsp-room-badge {
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--bg);
}

.fsp-summary-card,
.fsp-box,
.fsp-tip-card,
.fsp-room-box {
  padding: 12px;
}

.fsp-summary-title,
.fsp-box-title,
.fsp-tip-title,
.fsp-room-score {
  font-weight: 700;
  color: var(--text);
}

.fsp-summary-meta,
.fsp-compat,
.fsp-dir-desc,
.fsp-tip-meta,
.fsp-tip-reason,
.fsp-disclaimer {
  margin-top: 4px;
  font-size: var(--fs-xs);
  color: var(--text-2);
}

.fsp-grid,
.fsp-tip-list,
.fsp-room-grid,
.fsp-room-cells {
  display: grid;
  gap: 10px;
}

.fsp-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  padding: 0 14px 14px;
}

.fsp-dir-list,
.fsp-tip-list,
.fsp-room-cells,
.fsp-suggestion-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.fsp-dir-item {
  padding: 8px 10px;
  border-radius: 10px;
}

.fsp-dir-item.good { background: #ecfdf5; }
.fsp-dir-item.bad { background: #fef2f2; }

.fsp-dir-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  font-size: var(--fs-sm);
  color: var(--text);
}

.fsp-tip-list {
  padding: 0 14px 14px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.fsp-room-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin-top: 10px;
}

.fsp-room-cell {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.fsp-room-label {
  font-size: var(--fs-xs);
  color: var(--text-2);
}

.fsp-room-result {
  margin-top: 12px;
}

.fsp-direction-legend,
.fsp-recommend-box,
.fsp-avoid-box {
  margin: 0 14px 14px;
  padding: 12px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--bg);
}

.fsp-legend-list,
.fsp-recommend-list {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 8px;
}

.fsp-legend-chip,
.fsp-recommend-chip {
  padding: 5px 10px;
  border-radius: 999px;
  font-size: var(--fs-xs);
  border: 1px solid var(--border);
}

.fsp-legend-chip.good {
  background: #ecfdf5;
  color: #166534;
}

.fsp-legend-chip.bad {
  background: #fef2f2;
  color: #b91c1c;
}

.fsp-recommend-chip {
  background: #f8fafc;
  color: var(--text);
}

.fsp-avoid-chip {
  padding: 5px 10px;
  border-radius: 999px;
  font-size: var(--fs-xs);
  border: 1px solid #fecaca;
  background: #fff1f2;
  color: #b91c1c;
}

.fsp-layout-board {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin-top: 12px;
}

.fsp-layout-cell {
  min-height: 92px;
  padding: 10px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: #fff;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.fsp-layout-cell.is-center {
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f8fafc, #eef2ff);
}

.fsp-layout-cell.is-excellent,
.fsp-room-badge.is-excellent {
  background: #ecfdf5;
}

.fsp-layout-cell.is-good,
.fsp-room-badge.is-good {
  background: #f0fdf4;
}

.fsp-layout-cell.is-fair,
.fsp-room-badge.is-fair {
  background: #fffbeb;
}

.fsp-layout-cell.is-low,
.fsp-room-badge.is-low {
  background: #fef2f2;
}

.fsp-layout-dir {
  font-size: var(--fs-xs);
  color: var(--text-2);
}

.fsp-layout-room,
.fsp-layout-tag,
.fsp-layout-score {
  color: var(--text);
}

.fsp-layout-room,
.fsp-layout-tag {
  font-size: var(--fs-sm);
  font-weight: 600;
}

.fsp-layout-score {
  margin-top: auto;
  font-size: var(--fs-xs);
}

.fsp-room-badge {
  padding: 8px 10px;
  font-size: var(--fs-xs);
}

.fsp-suggestion-list {
  margin: 10px 0 0;
  padding-left: 18px;
  font-size: var(--fs-sm);
  color: var(--text);
}

.fsp-disclaimer {
  padding: 0 14px 14px;
}

.ozp-stats-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  padding: 0 14px 12px;
}

.ozp-stat-card,
.ozp-chart-box,
.ozp-create-box,
.ozp-results-box,
.ozp-exp-card {
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--bg);
}

.ozp-stat-card {
  padding: 12px;
}

.ozp-stat-num {
  font-size: 22px;
  font-weight: 700;
  color: var(--text);
}

.ozp-stat-label {
  margin-top: 4px;
  font-size: var(--fs-sm);
  color: var(--text);
}

.ozp-stat-sub,
.ozp-exp-meta,
.ozp-results-meta,
.ozp-result-meta,
.bzp-hint {
  margin-top: 4px;
  font-size: var(--fs-xs);
  color: var(--text-2);
}

.ozp-chart-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  padding: 0 14px 12px;
}

.ozp-chart-box,
.ozp-create-box,
.ozp-results-box {
  padding: 12px;
}

.ozp-box-title,
.ozp-exp-name {
  font-weight: 700;
  color: var(--text);
}

.ozp-box-empty {
  padding: 10px 0;
  font-size: var(--fs-sm);
  color: var(--text-2);
}

.ozp-bar-list,
.ozp-exp-list,
.ozp-result-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ozp-bar-row,
.ozp-result-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.ozp-bar-name,
.ozp-bar-count,
.ozp-total,
.ozp-results-winner,
.ozp-results-note,
.bzp-status {
  font-size: var(--fs-xs);
}

.ozp-create-box,
.ozp-results-box,
.ozp-experiments-head,
.bzp-upload-box,
.bzp-actions,
.bzp-hint,
.bzp-error {
  margin: 0 14px 12px;
}

.ozp-form-grid {
  display: grid;
  gap: 8px;
  margin-top: 10px;
}

.ozp-weight-row,
.ozp-form-actions,
.ozp-exp-top,
.ozp-exp-actions,
.ozp-results-winner,
.ozp-result-top,
.ozp-experiments-head,
.bzp-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.ozp-exp-list {
  padding: 0 14px 14px;
  max-height: 260px;
  overflow-y: auto;
}

.ozp-exp-card {
  padding: 12px;
}

.ozp-exp-desc {
  margin-top: 6px;
  font-size: var(--fs-sm);
  color: var(--text);
  line-height: 1.6;
}

.ozp-exp-badge,
.ozp-variant-chip {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--surface-2);
  color: var(--text-2);
}

.ozp-exp-variants {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.bzp-upload-box {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 96px;
  padding: 14px;
  border: 1px dashed var(--border-md);
  border-radius: 12px;
  background: var(--bg);
  color: var(--text-2);
  cursor: pointer;
  text-align: center;
}

.bzp-file-input {
  display: none;
}

/* ══════════════════════════════════════════════════════════════════
   星曜组合提示
   ══════════════════════════════════════════════════════════════════ */
.star-combos-section {
  margin-top: var(--sp-4);
  padding-top: var(--sp-4);
  border-top: 1px solid var(--border);
}
.star-combos-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
  margin-top: 12px;
}
.combo-card {
  padding: 12px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--bg);
}
.combo-card.combo-auspicious {
  border-color: rgba(34, 197, 94, 0.3);
  background: rgba(34, 197, 94, 0.05);
}
.combo-card.combo-inauspicious {
  border-color: rgba(239, 68, 68, 0.3);
  background: rgba(239, 68, 68, 0.05);
}
.combo-card.combo-neutral {
  border-color: rgba(234, 179, 8, 0.3);
  background: rgba(234, 179, 8, 0.05);
}
.combo-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.combo-name {
  font-weight: 600;
  font-size: var(--fs-sm);
}
.combo-auspicious .combo-name { color: #15803d; }
.combo-inauspicious .combo-name { color: #dc2626; }
.combo-neutral .combo-name { color: #a16207; }
.combo-palace {
  font-size: var(--fs-xs);
  color: var(--text-2);
  background: var(--bg-card);
  padding: 2px 6px;
  border-radius: 4px;
}
.combo-stars {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 8px;
}
.combo-star {
  font-size: 11px;
  padding: 2px 6px;
  background: var(--bg-card);
  border-radius: 4px;
  color: var(--text);
}
.combo-desc {
  font-size: var(--fs-xs);
  color: var(--text-2);
  margin: 0;
  line-height: 1.4;
}

/* ══════════════════════════════════════════════════════════════════
   打印样式优化
   ══════════════════════════════════════════════════════════════════ */
@media print {
  .no-print { display: none !important; }
  .form-card { display: none !important; }
  .tabs { display: none !important; }
  .palace-grid { break-inside: avoid; }
  
  /* 页面设置 */
  @page {
    size: A4 portrait;
    margin: 15mm;
  }
  
  /* 隐藏不必要的元素 */
  .chart-mode-bar,
  .info-bar button,
  .palace-detail,
  .hotkey-panel,
  .brightness-legend,
  .star-search-modal,
  .history-panel,
  .star-tooltip { display: none !important; }
  
  /* 基础样式调整 */
  body {
    font-size: 11pt;
    color: #000 !important;
    background: #fff !important;
  }
  
  .ziwei-page {
    padding: 0;
    max-width: 100%;
  }
  
  .card {
    box-shadow: none !important;
    border: 1px solid #ccc;
  }
  
  /* 信息栏打印样式 */
  .info-bar {
    border: none;
    padding: 8px 0;
    flex-wrap: wrap;
    justify-content: flex-start;
    gap: 12px;
    background: transparent !important;
  }
  
  .info-item {
    font-size: 10pt;
  }
  
  /* 命盘网格打印优化 */
  .palace-grid-pro {
    border: 2px solid #333;
    background: #fff !important;
  }
  
  .pc-cell {
    background: #fff !important;
    border-color: #333;
    min-height: 100px;
    padding: 6px;
  }
  
  .pc-center {
    background: #fff !important;
    border-color: #333;
  }
  
  /* 宫位名称 */
  .pc-pname {
    font-size: 11pt;
    font-weight: bold;
    color: #000;
  }
  
  /* 干支 */
  .pc-gzhi {
    font-size: 9pt;
    color: #333;
  }
  
  /* 主星 */
  .pc-sn {
    font-size: 10pt;
    font-weight: bold;
    color: #000;
  }
  
  /* 亮度 */
  .pc-sbr {
    font-size: 8pt;
    color: #666;
  }
  
  /* 四化标签 */
  .pc-tf {
    font-size: 8pt !important;
    padding: 1px 3px !important;
    border: 1px solid #333;
  }
  
  /* 辅星 */
  .pc-aux {
    font-size: 8pt;
    color: #666;
  }
  
  /* 大限年龄 */
  .pc-da {
    font-size: 8pt;
    color: #333;
  }
  
  /* 长生 */
  .pc-cs {
    font-size: 8pt;
  }
  
  /* 中宫 */
  .pc-cj {
    font-size: 14pt;
    font-weight: bold;
  }
  
  .pc-cb, .pc-cl {
    font-size: 9pt;
    color: #333;
  }
  
  /* 方位 */
  .compass-side, .compass-n, .compass-s {
    color: #666;
    font-size: 9pt;
  }
  
  /* 概述 */
  .summary-block {
    font-size: 10pt;
    line-height: 1.6;
    border: none;
    background: transparent !important;
    padding: 8px 0;
  }
  
  /* 分页控制 */
  .tab-panel {
    page-break-inside: avoid;
  }
  
  h3.section-title {
    page-break-after: avoid;
  }
  
  /* 友好的链接处理 */
  a { color: #000; text-decoration: none; }
}

@media (max-width: 600px) {
  .pc-cell { min-height: 80px; padding: 4px 3px; }
  .pc-sn   { font-size: 12px; }
  .pc-gzhi { font-size: 11px; }
  .pc-center { }
  .pc-cj { font-size: var(--fs-lg); }
  .compass-side, .compass-n, .compass-s { font-size: 9px; width: 18px; }
}

/* ── 宫位详情扩展 ───────────────────────── */
.detail-flying {
  display: flex; align-items: center; flex-wrap: wrap; gap: 5px;
  padding: var(--sp-2) 0; margin-bottom: var(--sp-2);
  border-top: 1px solid var(--border);
}
.detail-sec-label { font-size: var(--fs-xs); color: var(--text-3); flex-shrink: 0; }
.detail-tf { font-size: 11px !important; padding: 1px 5px !important; }
.detail-shens {
  display: flex; flex-wrap: wrap; gap: var(--sp-3);
  padding: var(--sp-2) 0; margin-bottom: var(--sp-2);
  border-top: 1px solid var(--border); font-size: var(--fs-sm);
}
.shen-item { color: var(--text-2); }
.shen-item b { color: var(--text); }

/* ── 大运博士星 ─────────────────────────── */
.dayun-boshi { display: flex; flex-wrap: wrap; gap: 3px; margin-top: 4px; }
.boshi-tag { font-size: 9px; padding: 1px 4px; background: var(--surface); border: 1px solid var(--border); border-radius: 3px; color: var(--text-3); }

/* ── 大运建议样式兼容 ────────────────────── */
.remedy-head { display: flex; align-items: baseline; gap: var(--sp-2); margin-bottom: 4px; }
.remedy-name { font-size: var(--fs-md); font-weight: 600; color: var(--text); }
.remedy-actions { display: flex; flex-direction: column; gap: 2px; margin: 4px 0; }
.remedy-step { font-size: var(--fs-sm); color: var(--text); line-height: 1.5; }
.suggest-name { font-size: var(--fs-sm); font-weight: 600; color: var(--text); margin: 2px 0 4px; }
.suggest-actions { display: flex; flex-direction: column; gap: 2px; margin-top: 4px; }
.suggest-step { font-size: var(--fs-sm); color: var(--text); line-height: 1.5; }

/* ── 流年 tab ───────────────────────────── */
.liunian-wrap { padding: var(--sp-5); background: var(--surface-2); border-radius: var(--radius-sm); }
.liunian-head { display: flex; align-items: baseline; gap: var(--sp-3); margin-bottom: var(--sp-4); flex-wrap: wrap; }
.liunian-gz { font-size: var(--fs-2xl); font-weight: 800; font-family: var(--font-cn); color: var(--accent); }
.liunian-year { font-size: var(--fs-sm); color: var(--text-3); }
.liunian-cur-badge {
  background: #7c3aed;
  color: #fff;
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 600;
}
.liunian-lp { font-size: var(--fs-sm); color: var(--text-2); border: 1px solid var(--border-md); border-radius: 10px; padding: 1px 8px; }
.liunian-sihua-wrap { }
.sec-label { font-size: var(--fs-sm); color: var(--text-3); margin-bottom: var(--sp-3); font-weight: 500; }
.liunian-sihua { display: flex; flex-wrap: wrap; gap: var(--sp-3); }
.sihua-row { display: flex; align-items: center; gap: 6px; padding: var(--sp-2) var(--sp-4); background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-sm); min-width: 90px; }
.sihua-star-name { font-size: var(--fs-md); font-weight: 700; font-family: var(--font-cn); }
.sihua-tf-badge { font-size: var(--fs-sm) !important; padding: 2px 7px !important; }

/* ── 宫位详情标签 & 对宫 ─────────────────────────────── */
.detail-tags {
  display: flex; flex-wrap: wrap; gap: 5px;
  padding: var(--sp-2) 0; margin-bottom: var(--sp-2);
  border-top: 1px solid var(--border);
}
.detail-tag {
  font-size: var(--fs-xs); padding: 2px 8px;
  background: rgba(37,99,235,.08); color: #1d4ed8;
  border: 1px solid rgba(37,99,235,.2); border-radius: 10px;
}

/* ── 飞星 tab ─────────────────────────────────────────── */
.flying-tags-row { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: var(--sp-4); }
.flying-self-tag {
  font-size: var(--fs-sm); padding: 3px 10px;
  background: rgba(124,58,237,.1); color: #7c3aed;
  border: 1px solid rgba(124,58,237,.2); border-radius: 10px;
}
.flying-stats {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-3);
  padding: var(--sp-3) var(--sp-4);
  background: var(--surface-2);
  border-radius: var(--radius-sm);
  margin-bottom: var(--sp-4);
}
.flying-stat { font-size: var(--fs-sm); color: var(--text-2); }
.flying-stat b { font-weight: 700; color: var(--accent); }
.section-count { 
  font-size: 10px; 
  background: var(--accent); 
  color: #fff; 
  padding: 1px 6px; 
  border-radius: 8px; 
  margin-left: 6px; 
  font-weight: 600; 
}
.flying-palaces-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: var(--sp-3);
  margin-bottom: var(--sp-5);
}
.flying-insights-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  padding: var(--sp-3) var(--sp-4);
  background: var(--surface-2);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  margin-bottom: var(--sp-4);
}
.fib-label { font-size: var(--fs-xs); color: var(--text-2); flex-shrink: 0; }
.fib-item {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-md);
  background: var(--surface);
  font-size: var(--fs-xs);
}
.fib-type { font-weight: 700; font-size: var(--fs-sm); }
.fib-arrow { color: var(--text-2); }
.fib-palaces { color: var(--text); }
.fi-lu { border-color: #86efac; background: #f0fdf4; }
.fi-lu .fib-type { color: #166534; }
.fi-quan { border-color: #fca5a5; background: #fff1f2; }
.fi-quan .fib-type { color: #991b1b; }
.fi-ke { border-color: #93c5fd; background: #eff6ff; }
.fi-ke .fib-type { color: #1e40af; }
.fi-ji { border-color: #c4b5fd; background: #f5f3ff; }
.fi-ji .fib-type { color: #5b21b6; }

/* 命盘快速洞察栏 */
.chart-quick-insights {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-2);
  margin-bottom: var(--sp-3);
}
.cqi-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: var(--sp-2) var(--sp-3);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  background: var(--surface-2);
  min-width: 72px;
}
.cqi-label { font-size: 10px; color: var(--text-2); }
.cqi-value { font-size: var(--fs-md); font-weight: 700; color: var(--text); }
.cqi-sub { font-size: 10px; color: var(--text-2); max-width: 110px; text-align: center; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.cqi-ji { border-color: #c4b5fd; background: #f5f3ff; }
.cqi-ji .cqi-value { color: #5b21b6; }
.cqi-lu { border-color: #86efac; background: #f0fdf4; }
.cqi-lu .cqi-value { color: #166534; }
.cqi-dense { border-color: #fcd34d; background: #fffbeb; }
.cqi-dense .cqi-value { color: #92400e; }
.cqi-good .cqi-value { color: #166534; }
.flying-palace-card {
  padding: var(--sp-3); background: var(--surface-2);
  border: 1px solid var(--border); border-radius: var(--radius-sm);
}
.fp-head { display: flex; align-items: center; gap: 6px; margin-bottom: 6px; }
.fp-name { font-size: var(--fs-sm); font-weight: 700; font-family: var(--font-cn); }
.fp-stem { font-size: var(--fs-xs); color: var(--text-2); }
.fp-row { display: flex; align-items: center; gap: 4px; flex-wrap: wrap; margin-bottom: 3px; font-size: var(--fs-xs); }
.fp-label { color: var(--text-2); flex-shrink: 0; }
.fp-opp { color: var(--text-2); }
.fp-self-tag {
  font-size: var(--fs-xs); padding: 1px 5px;
  background: rgba(124,58,237,.08); color: #7c3aed;
  border-radius: 4px; border: 1px solid rgba(124,58,237,.15);
}
.flying-received-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: var(--sp-2);
}
.fr-item {
  display: flex; align-items: center; gap: 6px; flex-wrap: wrap;
  padding: var(--sp-2) var(--sp-3);
  background: var(--surface-2); border: 1px solid var(--border); border-radius: var(--radius-sm);
}
.fr-palace { font-size: var(--fs-sm); font-weight: 600; font-family: var(--font-cn); min-width: 36px; }
.fr-tfs { display: flex; flex-wrap: wrap; gap: 3px; }
.fr-tf { font-size: 10px !important; padding: 1px 4px !important; }
.fr-opp { font-size: var(--fs-sm); color: var(--text-2); }

/* ── 运势预测 tab ─────────────────────────────────────── */
.forecast-yearly, .forecast-curmonth { margin-bottom: var(--sp-4); }
.fy-head { display: flex; align-items: baseline; gap: var(--sp-3); margin-bottom: var(--sp-3); flex-wrap: wrap; }
.fy-gz { font-size: var(--fs-xl); font-weight: 800; font-family: var(--font-cn); color: var(--accent); }
.fy-period { font-size: var(--fs-sm); color: var(--text-3); }
.fy-score { font-size: var(--fs-sm); font-weight: 700; }
.fy-overall { font-size: var(--fs-md); color: var(--text); line-height: 1.7; margin-bottom: var(--sp-3); }
.fy-details { display: flex; flex-direction: column; gap: 6px; margin-bottom: var(--sp-3); }
.fyd-item { display: flex; gap: var(--sp-3); align-items: baseline; }
.fyd-domain { font-size: var(--fs-xs); padding: 1px 8px; background: var(--surface); border: 1px solid var(--border-md); border-radius: 10px; color: var(--text-2); flex-shrink: 0; }
.fyd-text { font-size: var(--fs-sm); color: var(--text); line-height: 1.6; }
.fy-events { display: flex; flex-direction: column; gap: 5px; margin-bottom: var(--sp-3); }
.fye-item { display: flex; gap: 8px; align-items: center; padding: 5px 10px; border-radius: var(--radius-sm); background: var(--surface-2); }
.fye-high { border-left: 3px solid #dc2626; }
.fye-mid  { border-left: 3px solid #d97706; }
.fye-low  { border-left: 3px solid #64748b; }
.fye-cat  { font-size: var(--fs-xs); padding: 1px 6px; background: var(--surface); border: 1px solid var(--border-md); border-radius: 8px; color: var(--text-2); flex-shrink: 0; }
.fye-desc { font-size: var(--fs-sm); color: var(--text); }
.fy-advice { font-size: var(--fs-sm); color: var(--accent-dark); background: rgba(217,119,6,.08); border-radius: var(--radius-sm); padding: var(--sp-2) var(--sp-3); }

.fcm-head { display: flex; align-items: baseline; gap: var(--sp-3); margin-bottom: var(--sp-3); flex-wrap: wrap; }
.fcm-label { font-size: var(--fs-xs); padding: 2px 8px; background: var(--accent); color: #fff; border-radius: 10px; font-weight: 600; }
.fcm-gz { font-size: var(--fs-lg); font-weight: 700; font-family: var(--font-cn); }

.forecast-monthly-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
  gap: var(--sp-3);
}
.fm-item {
  padding: var(--sp-3); background: var(--surface-2);
  border: 1px solid var(--border); border-radius: var(--radius-sm);
  border-left: 3px solid var(--border-md);
}
.fm-good { border-left-color: #16a34a; }
.fm-mid  { border-left-color: #d97706; }
.fm-low  { border-left-color: #dc2626; }
.fm-period { font-size: var(--fs-xs); color: var(--text-3); margin-bottom: 2px; }
.fm-gz { font-size: var(--fs-md); font-weight: 700; font-family: var(--font-cn); }
.fm-score { font-size: var(--fs-lg); font-weight: 800; margin: 2px 0; }
.fm-score-bar {
  width: 100%;
  height: 6px;
  border-radius: 999px;
  background: rgba(0,0,0,.08);
  overflow: hidden;
  margin: 2px 0 6px;
}
.fm-score-bar i {
  display: block;
  height: 100%;
  border-radius: 999px;
  background: currentColor;
}
.fm-palace { font-size: var(--fs-xs); color: var(--text-2); margin-bottom: 3px; }
.fm-overall { font-size: var(--fs-xs); color: var(--text); line-height: 1.5; margin-top: 3px; }
.fm-item { cursor: pointer; transition: all var(--dur-fast); }
.fm-item:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.fm-expanded { grid-column: 1 / -1; background: var(--surface); border-width: 2px; }
.fm-details { display: flex; flex-wrap: wrap; gap: var(--sp-2); margin-top: var(--sp-3); padding-top: var(--sp-3); border-top: 1px dashed var(--border); }
.fmd-item { display: flex; flex-direction: column; flex: 1 1 140px; }
.fmd-domain { font-size: var(--fs-xs); color: var(--accent); font-weight: 600; }
.fmd-text { font-size: var(--fs-sm); color: var(--text); line-height: 1.5; }
.fm-events { display: flex; flex-wrap: wrap; gap: var(--sp-2); margin-top: var(--sp-3); }
.fme-item { display: inline-flex; align-items: center; gap: 4px; padding: 2px 8px; border-radius: 10px; font-size: var(--fs-xs); }
.fme-强, .fme-item.fme-强 { background: rgba(239, 68, 68, 0.15); color: #b91c1c; }
.fme-中, .fme-item.fme-中 { background: rgba(245, 158, 11, 0.15); color: #b45309; }
.fme-弱, .fme-item.fme-弱 { background: rgba(59, 130, 246, 0.15); color: #1d4ed8; }
.fme-cat { font-weight: 600; }
.fme-desc { color: inherit; opacity: 0.9; }
.fm-advice { font-size: var(--fs-sm); color: var(--text-2); margin-top: var(--sp-3); padding: var(--sp-2); background: var(--surface-2); border-radius: var(--radius-sm); }

/* ═══════════════════════════════════════════════════════════════════
   C-1: 盘面类型切换按钮组样式
   ═══════════════════════════════════════════════════════════════════ */
.chart-mode-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-4);
  margin-bottom: var(--sp-4);
  padding: 8px 12px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
}
.mode-btns {
  display: flex;
  gap: 0;
  border: 1px solid var(--border-md);
  border-radius: var(--radius-sm);
  overflow: hidden;
}
.mode-btn {
  padding: 8px 20px;
  border: none;
  background: var(--surface);
  color: var(--text-2);
  font-size: var(--fs-md);
  font-weight: 600;
  font-family: var(--font-cn);
  cursor: pointer;
  transition: all var(--dur-fast);
  border-right: 1px solid var(--border-md);
}
.mode-btn:last-child { border-right: none; }
.mode-btn:hover { background: var(--surface-2); color: var(--text); }
.mode-btn.active {
  background: var(--accent);
  color: #fff;
}
.sihua-line-toggle, .liunian-overlay-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: var(--fs-sm);
  color: var(--text-2);
  cursor: pointer;
}
.sihua-line-toggle input, .liunian-overlay-toggle input {
  width: 16px;
  height: 16px;
  accent-color: var(--accent);
}

/* 流月选择器 */
.liuyue-selector {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: var(--fs-sm);
  color: var(--text-2);
}
.liuyue-select {
  font-size: var(--fs-sm);
  padding: 2px 6px;
  border: 1px solid #d6c9b3;
  border-radius: 4px;
  background: #fff;
  color: var(--text-1);
}
.liuyue-select option {
  color: #1f2937;
  background: #fff;
}
.liuyue-select option:checked,
.liuyue-select option:hover {
  color: #111827;
  background: #e5e7eb;
}

/* ═══════════════════════════════════════════════════════════════════
   C-4: 星曜显示控制样式
   ═══════════════════════════════════════════════════════════════════ */
.star-display-opts {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-left: 12px;
  border-left: 1px solid var(--border);
  margin-left: auto;
}
.star-display-opts label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: var(--fs-sm);
  color: var(--text-2);
  cursor: pointer;
  user-select: none;
}
.star-display-opts input[type="checkbox"] {
  width: 14px;
  height: 14px;
  accent-color: var(--accent);
  cursor: pointer;
}
.star-display-opts label:hover {
  color: var(--text);
}

/* 叠加层显示控制 */
.overlay-display-opts {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  font-size: var(--fs-sm);
  margin-top: 6px;
  padding: 6px 10px;
  background: rgba(13,148,136,.05);
  border-radius: 6px;
  border: 1px solid rgba(13,148,136,.15);
}
.overlay-display-opts .overlay-label {
  font-weight: 600;
  color: #0d9488;
}
.overlay-display-opts label {
  display: flex;
  align-items: center;
  gap: 3px;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 4px;
  transition: background 0.15s;
  color: var(--text-2);
}
.overlay-display-opts label:hover {
  background: rgba(13,148,136,.1);
  color: var(--text);
}
.overlay-display-opts input[type="checkbox"] {
  width: 14px;
  height: 14px;
  accent-color: #0d9488;
  cursor: pointer;
}

/* ═══════════════════════════════════════════════════════════════════
   C-3: 四化飞星 SVG 连线样式
   ═══════════════════════════════════════════════════════════════════ */
.sihua-lines-svg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 10;
}
.sihua-lines-svg .sihua-label {
  font-size: 2.5px;
  font-weight: 700;
  text-anchor: middle;
  dominant-baseline: middle;
  font-family: var(--font-cn);
}
.sihua-lines-svg .sihua-legend-text {
  font-size: 2px;
  fill: var(--text-3);
  font-family: var(--font-cn);
}
.sihua-lines-svg line {
  opacity: 0.85;
  transition: opacity 0.2s ease;
}
.sihua-lines-svg g:hover line,
.sihua-lines-svg g:hover circle {
  opacity: 1;
  stroke-width: 1;
}

/* ═══════════════════════════════════════════════════════════════════
   C-7: 底部时间轴样式
   ═══════════════════════════════════════════════════════════════════ */
.timeline-bar {
  margin-top: var(--sp-5);
  padding: 12px 16px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.tl-section {
  display: flex;
  align-items: center;
  gap: 12px;
}
.tl-label {
  font-size: var(--fs-sm);
  font-weight: 700;
  color: var(--text-2);
  min-width: 36px;
  font-family: var(--font-cn);
}
.tl-track {
  display: flex;
  gap: 4px;
  overflow-x: auto;
  padding-bottom: 4px;
  flex: 1;
}
.tl-track::-webkit-scrollbar { height: 4px; }
.tl-track::-webkit-scrollbar-track { background: var(--surface-2); border-radius: 2px; }
.tl-track::-webkit-scrollbar-thumb { background: var(--border-md); border-radius: 2px; }
.tl-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 6px 10px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  cursor: pointer;
  transition: all var(--dur-fast);
  white-space: nowrap;
  flex-shrink: 0;
}
.tl-item:hover { border-color: var(--accent); background: var(--surface-2); }
.tl-item.tl-current {
  border-color: #f97316;
  background: #fff7ed;
}
.tl-item.tl-selected {
  border-color: var(--accent);
  background: var(--accent);
  color: #fff;
}
.tl-item.tl-selected .tl-gz,
.tl-item.tl-selected .tl-age { color: #fff; }
.tl-gz {
  font-size: var(--fs-md);
  font-weight: 700;
  font-family: var(--font-cn);
  color: var(--text);
}
.tl-age {
  font-size: 10px;
  color: var(--text-3);
  margin-top: 2px;
}
/* 大限项增强 - 显示起始年份 */
.tl-item.tl-dayun {
  min-width: 58px;
}
.tl-year-info {
  font-size: 9px;
  color: #6b7280;
  margin-top: 1px;
}
.tl-item.tl-selected .tl-year-info { color: rgba(255,255,255,.8); }
/* 流年项增强 - 显示年龄 */
.tl-year {
  flex-direction: column;
  padding: 5px 10px;
  min-width: 50px;
}
.tl-yr-num {
  font-family: var(--font-mono);
  font-size: var(--fs-sm);
  font-weight: 600;
}
.tl-yr-age {
  font-size: 9px;
  color: var(--text-3);
  margin-top: 1px;
}
.tl-item.tl-selected .tl-yr-num,
.tl-item.tl-selected .tl-yr-age { color: #fff; }
.tl-nav {
  display: flex;
  gap: 4px;
}
.tl-nav-btn {
  width: 28px;
  height: 28px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  cursor: pointer;
  font-size: 11px;
  color: var(--text-2);
  transition: all var(--dur-fast);
}
.tl-nav-btn:hover { border-color: var(--accent); color: var(--accent); }
.tl-select {
  padding: 6px 24px 6px 10px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  font-size: var(--fs-sm);
  font-family: var(--font-mono);
  color: var(--text);
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2378716c' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 6px center;
  flex-shrink: 0;
}
.tl-select:hover { border-color: var(--accent); }
.tl-select:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 2px rgba(217,119,6,.15); }

/* ═══════════════════════════════════════════════════════════════════
   新增：摘要Tab样式
   ═══════════════════════════════════════════════════════════════════ */
.summary-full { padding: var(--sp-5); }
.summary-text { 
  font-size: var(--fs-md); 
  line-height: 1.8; 
  color: var(--text); 
  margin-bottom: var(--sp-4);
}
.summary-quick-facts {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: var(--sp-2);
  margin-bottom: var(--sp-3);
}
.sqf-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 8px 10px;
  border-radius: 10px;
  border: 1px solid var(--border);
  background: var(--surface-2);
}
.sqf-label {
  font-size: var(--fs-xs);
  color: var(--text-2);
}
.sqf-value {
  font-size: var(--fs-sm);
  color: var(--text);
  font-weight: 600;
}
.summary-insights {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: var(--sp-4);
}
.summary-insight-tag {
  font-size: var(--fs-xs);
  color: var(--text-2);
  background: var(--surface-2);
  border: 1px dashed var(--border-md);
  border-radius: 999px;
  padding: 4px 10px;
}
.summary-key-conclusions {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--sp-2);
  margin-bottom: var(--sp-4);
}
.skc-item {
  padding: var(--sp-3);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  background: var(--surface-2);
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.skc-item.skc-good { border-color: #86efac; background: #f0fdf4; }
.skc-item.skc-warn { border-color: #fca5a5; background: #fff7f7; }
.skc-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
}
.skc-title {
  font-size: var(--fs-xs);
  color: var(--text-2);
  font-weight: 500;
}
.skc-tag {
  font-size: 10px;
  padding: 1px 7px;
  border-radius: 999px;
  background: var(--border);
  color: var(--text-2);
}
.skc-item.skc-good .skc-tag { background: #bbf7d0; color: #166534; }
.skc-item.skc-warn .skc-tag { background: #fecaca; color: #991b1b; }
.skc-content {
  font-size: var(--fs-sm);
  color: var(--text);
  font-weight: 600;
  margin: 0;
  line-height: 1.4;
}
.summary-highlights {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-3);
  padding: var(--sp-4);
  background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
  border: 1px solid #fcd34d;
  border-radius: var(--radius-sm);
  margin-bottom: var(--sp-4);
}
.sh-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 70px;
}
.sh-label {
  font-size: 10px;
  color: #92400e;
  margin-bottom: 2px;
}
.sh-value {
  font-size: var(--fs-md);
  font-weight: 700;
  font-family: var(--font-cn);
  color: #78350f;
}
.analysis-dimensions { margin-top: var(--sp-4); }
.dimension-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--sp-4);
}
.dimension-item {
  padding: var(--sp-4);
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  border-left: 3px solid var(--accent);
}
.dimension-label {
  display: inline-block;
  font-size: var(--fs-sm);
  font-weight: 700;
  color: var(--accent);
  padding: 2px 10px;
  background: rgba(217,119,6,.1);
  border-radius: 10px;
  margin-bottom: var(--sp-2);
}
.dimension-text {
  font-size: var(--fs-sm);
  color: var(--text);
  line-height: 1.6;
  margin: 0;
}
.stars-section { margin-top: var(--sp-4); }
.stars-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.star-tag {
  font-size: var(--fs-sm);
  padding: 3px 10px;
  border-radius: 10px;
  font-weight: 600;
}
.star-tag.lucky { background: rgba(34,197,94,.1); color: #16a34a; border: 1px solid rgba(34,197,94,.2); }
.star-tag.unlucky { background: rgba(239,68,68,.1); color: #dc2626; border: 1px solid rgba(239,68,68,.2); }

/* ═══════════════════════════════════════════════════════════════════
   新增：逐宫解读Tab样式
   ═══════════════════════════════════════════════════════════════════ */
.palaces-interpretations {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: var(--sp-4);
}
.palaces-interpretations-grouped {
  display: grid;
  gap: var(--sp-4);
}
.pig-group {
  padding: 0;
  overflow: hidden;
}
.pig-head {
  width: 100%;
  border: 0;
  background: var(--surface-2);
  border-bottom: 1px solid var(--border);
  padding: 10px 12px;
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  text-align: left;
}
.pig-title {
  font-size: var(--fs-md);
  font-weight: 700;
  color: var(--text);
  flex: 1;
}
.pig-count {
  font-size: var(--fs-xs);
  color: var(--text-3);
  background: var(--surface-1);
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 2px 8px;
}
.pig-toggle {
  font-size: var(--fs-xs);
  color: var(--accent);
}
.pig-group .palaces-interpretations {
  padding: var(--sp-3);
}
.palace-interp-card {
  padding: var(--sp-4);
  border-left: 3px solid var(--border-md);
}
.palace-interp-card:has(.pi-tag.life) { border-left-color: #dc2626; }
.palace-interp-card:has(.pi-tag.body) { border-left-color: #2563eb; }
.pi-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: var(--sp-3);
  flex-wrap: wrap;
}
.pi-name {
  font-size: var(--fs-lg);
  font-weight: 700;
  font-family: var(--font-cn);
  color: var(--text);
}
.pi-gz {
  font-size: var(--fs-sm);
  color: var(--text-3);
}
.pi-tag {
  font-size: var(--fs-xs);
  padding: 1px 6px;
  border-radius: 8px;
  font-weight: 600;
}
.pi-tag.life { background: rgba(220,38,38,.12); color: #dc2626; }
.pi-tag.body { background: rgba(37,99,235,.12); color: #2563eb; }
.pi-stars {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: var(--sp-3);
}
.pi-star {
  display: flex;
  align-items: center;
  gap: 3px;
  padding: 3px 8px;
  background: var(--surface-2);
  border-radius: var(--radius-sm);
  font-size: var(--fs-sm);
}
.pi-star b { color: var(--text); }
.pi-br { color: var(--text-3); font-size: var(--fs-xs); }
.pi-tf { color: var(--accent); font-size: var(--fs-xs); font-weight: 600; }
.pi-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: var(--sp-3);
}
.pi-tag-item {
  font-size: var(--fs-xs);
  padding: 2px 8px;
  background: rgba(37,99,235,.08);
  color: #1d4ed8;
  border: 1px solid rgba(37,99,235,.2);
  border-radius: 10px;
}
.pi-conclusion {
  font-size: var(--fs-sm);
  color: var(--text);
  line-height: 1.6;
  margin-bottom: var(--sp-2);
}
.pi-conclusion strong { color: var(--accent); }
.pi-explanation {
  font-size: var(--fs-sm);
  color: var(--text-2);
  line-height: 1.6;
  margin-bottom: var(--sp-2);
}
.pi-explanation strong { color: var(--text-3); }
.pi-suggestion {
  font-size: var(--fs-sm);
  color: var(--accent-dark);
  background: rgba(217,119,6,.08);
  padding: var(--sp-2) var(--sp-3);
  border-radius: var(--radius-sm);
  line-height: 1.6;
}
.pi-suggestion strong { color: var(--accent); }
.pi-analysis {
  font-size: var(--fs-sm);
  color: var(--text-2);
  line-height: 1.6;
}

/* ═══════════════════════════════════════════════════════════════════
   新增：流月展开详情样式
   ═══════════════════════════════════════════════════════════════════ */
.liuyue-item {
  cursor: pointer;
  transition: all var(--dur-fast);
}
.liuyue-item:hover { border-color: var(--accent); }
.liuyue-cur { border-color: #ea580c !important; background: rgba(234,88,12,.06) !important; }
.liuyue-cur-badge {
  background: #ea580c;
  color: #fff;
  font-size: 9px;
  padding: 1px 6px;
  border-radius: 8px;
  font-weight: 600;
}
.liuyue-expanded {
  grid-column: 1 / -1;
  border-color: var(--accent);
  background: rgba(217,119,6,.04);
}
.liuyue-expand-icon {
  margin-left: auto;
  font-size: 10px;
  color: var(--text-3);
}
.liuyue-detail {
  margin-top: var(--sp-3);
  padding-top: var(--sp-3);
  border-top: 1px solid var(--border);
}
.liuyue-events { margin-bottom: var(--sp-3); }
.liuyue-event {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
}
.liuyue-ev-cat {
  font-size: var(--fs-xs);
  padding: 1px 6px;
  background: var(--surface);
  border: 1px solid var(--border-md);
  border-radius: 8px;
  color: var(--text-2);
  flex-shrink: 0;
}
.liuyue-ev-desc {
  font-size: var(--fs-sm);
  color: var(--text);
}
.liuyue-dimensions { margin-bottom: var(--sp-3); }
.liuyue-dim {
  display: flex;
  gap: 8px;
  padding: 3px 0;
  font-size: var(--fs-sm);
}
.liuyue-dim-label {
  color: var(--text-3);
  flex-shrink: 0;
  min-width: 50px;
}
.liuyue-dim-text { color: var(--text); }
.liuyue-advice {
  font-size: var(--fs-sm);
  color: var(--accent-dark);
  background: rgba(217,119,6,.08);
  padding: var(--sp-2) var(--sp-3);
  border-radius: var(--radius-sm);
  margin: 0;
}
.liuyue-overall {
  font-size: var(--fs-sm);
  color: var(--text-2);
  margin: var(--sp-2) 0 0;
}

/* ═══════════════════════════════════════════════════════════════════
   命盘批注/笔记功能样式
   ═══════════════════════════════════════════════════════════════════ */


.notes-panel {
  position: absolute;
  top: 100%;
  right: 0;
  z-index: 100;
  background: #fff;
  border: 1px solid var(--border-md);
  border-radius: var(--radius-md);
  box-shadow: 0 8px 24px rgba(0,0,0,.15);
  width: 340px;
  max-height: 420px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  max-height: 60vh;
  overflow-y: auto;
}
.np-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  border-bottom: 1px solid var(--border);
  font-weight: 600;
  color: #7c3aed;
}
.np-close {
  border: none;
  background: none;
  cursor: pointer;
  font-size: 16px;
  color: var(--text-3);
}
.np-close:hover { color: var(--danger); }
.np-content {
  padding: 12px;
  overflow-y: auto;
  flex: 1;
}
.np-add-form {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px dashed var(--border);
}
.np-target-select {
  padding: 6px 10px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: var(--fs-sm);
}
.np-target-name {
  padding: 6px 10px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: var(--fs-sm);
}
.np-textarea {
  padding: 8px 10px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: var(--fs-sm);
  resize: vertical;
  min-height: 50px;
}
.np-btns {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}
.np-add, .np-save {
  padding: 6px 14px;
  background: #7c3aed;
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: var(--fs-sm);
}
.np-add:hover, .np-save:hover { background: #6d28d9; }
.np-cancel {
  padding: 6px 14px;
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: var(--fs-sm);
}
.np-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.np-item {
  padding: 10px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
}
.np-item-head {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
}
.np-item-target {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 8px;
  font-weight: 500;
}
.np-general { background: #e0e7ff; color: #4338ca; }
.np-palace { background: #dcfce7; color: #166534; }
.np-star { background: #fef3c7; color: #b45309; }
.np-item-time {
  font-size: 10px;
  color: var(--text-3);
}
.np-item-content {
  font-size: var(--fs-sm);
  color: var(--text);
  line-height: 1.5;
  white-space: pre-wrap;
}
.np-item-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}
.np-item-actions button {
  font-size: 11px;
  color: var(--text-3);
  background: none;
  border: none;
  cursor: pointer;
  text-decoration: underline;
}
.np-item-actions button:hover { color: var(--accent); }
.np-empty {
  text-align: center;
  color: var(--text-3);
  font-size: var(--fs-sm);
  padding: 20px;
}

/* ═══════════════════════════════════════════════════════════════════
   宫位收藏书签样式
   ═══════════════════════════════════════════════════════════════════ */
.pc-bookmark-btn {
  padding: 0 2px;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 11px;
  color: #d1d5db;
  transition: all 0.2s;
  opacity: 0.5;
}
.pc-cell:hover .pc-bookmark-btn { opacity: 1; }
.pc-bookmark-btn:hover { color: #fbbf24; }
.pc-bookmark-btn.bookmarked {
  color: #f59e0b;
  opacity: 1;
}

/* ═══════════════════════════════════════════════════════════════════
   运势日历样式
   ═══════════════════════════════════════════════════════════════════ */


.calendar-panel {
  position: absolute;
  top: 100%;
  right: 0;
  z-index: 100;
  background: #fff;
  border: 1px solid var(--border-md);
  border-radius: var(--radius-md);
  box-shadow: 0 8px 24px rgba(0,0,0,.15);
  width: 360px;
  padding: 12px;
  max-height: 60vh;
  overflow-y: auto;
}
.cal-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}
.cal-nav {
  width: 28px;
  height: 28px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  cursor: pointer;
  font-size: 12px;
}
.cal-nav:hover { border-color: var(--accent); color: var(--accent); }
.cal-title {
  flex: 1;
  text-align: center;
  font-weight: 600;
  color: var(--text);
}
.cal-close {
  border: none;
  background: none;
  cursor: pointer;
  font-size: 16px;
  color: var(--text-3);
}
.cal-weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  text-align: center;
  font-size: 11px;
  color: var(--text-3);
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--border);
}
.cal-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
}
.cal-day {
  aspect-ratio: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  font-size: 12px;
  cursor: default;
}
.cal-empty { background: transparent; }
.cal-day-num { font-weight: 600; }
.cal-day-fortune { font-size: 9px; margin-top: 2px; }

.fortune-great { background: #dcfce7; color: #166534; }
.fortune-good { background: #d1fae5; color: #047857; }
.fortune-normal { background: #f3f4f6; color: #6b7280; }
.fortune-bad { background: #fee2e2; color: #b91c1c; }
.fortune-terrible { background: #fecaca; color: #991b1b; }

.cal-legend {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid var(--border);
}
.cal-legend span {
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 8px;
}

/* ═══════════════════════════════════════════════════════════════════
   命盘对比样式
   ═══════════════════════════════════════════════════════════════════ */


.compare-panel {
  position: absolute;
  top: 100%;
  right: 0;
  z-index: 100;
  background: #fff;
  border: 1px solid var(--border-md);
  border-radius: var(--radius-md);
  box-shadow: 0 8px 24px rgba(0,0,0,.15);
  width: 340px;
  overflow: hidden;
  max-height: 60vh;
  overflow-y: auto;
}
.cmp-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  border-bottom: 1px solid var(--border);
  font-weight: 600;
  color: #f97316;
}
.cmp-close {
  border: none;
  background: none;
  cursor: pointer;
  font-size: 16px;
  color: var(--text-3);
}
.cmp-content { padding: 14px; }
.cmp-hint {
  font-size: var(--fs-sm);
  color: var(--text-2);
  margin: 0 0 12px;
}
.cmp-form {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.cmp-row {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.cmp-row label {
  font-size: var(--fs-sm);
  color: var(--text-2);
  min-width: 20px;
}
.cmp-row input, .cmp-row select {
  padding: 6px 8px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: var(--fs-sm);
  width: 60px;
}
.cmp-row select { width: 52px; }
.cmp-btns {
  display: flex;
  gap: 8px;
  margin-top: 14px;
}
.cmp-set {
  flex: 1;
  padding: 8px;
  background: #f97316;
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: var(--fs-sm);
  font-weight: 500;
}
.cmp-set:hover { background: #ea580c; }
.cmp-clear {
  padding: 8px 14px;
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: var(--fs-sm);
}
.cmp-status {
  margin-top: 12px;
  padding: 8px 10px;
  background: #fff7ed;
  border: 1px solid #fed7aa;
  border-radius: var(--radius-sm);
  font-size: var(--fs-sm);
  color: #c2410c;
}

/* ═══════════════════════════════════════════════════════════════════
   已收藏宫位面板样式
   ═══════════════════════════════════════════════════════════════════ */


.bookmarks-panel {
  position: absolute;
  top: 100%;
  right: 0;
  z-index: 100;
  background: #fff;
  border: 1px solid var(--border-md);
  border-radius: var(--radius-md);
  box-shadow: 0 8px 24px rgba(0,0,0,.15);
  width: 320px;
  max-height: 360px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  max-height: 60vh;
  overflow-y: auto;
}
.bkm-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  border-bottom: 1px solid var(--border);
  font-weight: 600;
  color: #d97706;
}
.bkm-close {
  border: none;
  background: none;
  cursor: pointer;
  font-size: 16px;
  color: var(--text-3);
}
.bkm-content {
  padding: 10px;
  overflow-y: auto;
  flex: 1;
}
.bkm-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.bkm-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.15s;
}
.bkm-item:hover {
  border-color: var(--accent);
  background: var(--accent-light);
}
.bkm-palace-name {
  font-weight: 600;
  color: var(--text);
  min-width: 40px;
}
.bkm-palace-gz {
  font-size: 11px;
  color: var(--text-3);
  font-family: var(--font-mono);
}
.bkm-palace-stars {
  flex: 1;
  font-size: 11px;
  color: var(--text-2);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.bkm-remove {
  border: none;
  background: none;
  cursor: pointer;
  font-size: 12px;
  color: var(--text-3);
  padding: 0;
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}
.bkm-remove:hover {
  background: var(--danger);
  color: #fff;
}
.bkm-empty {
  text-align: center;
  color: var(--text-3);
  font-size: var(--fs-sm);
  padding: 30px 10px;
}

/* ═══════════════════════════════════════════════════════════════════
   星曜收藏按钮样式
   ═══════════════════════════════════════════════════════════════════ */
.star-fav-btn {
  padding: 0 2px;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 12px;
  color: #d1d5db;
  transition: all 0.2s;
  vertical-align: baseline;
}
.star-fav-btn:hover { color: #ec4899; }
.star-fav-btn.starred { color: #ec4899; }

.detail-starred-stars {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  margin: 8px 0;
  font-size: var(--fs-sm);
}
.starred-star-item {
  padding: 3px 8px;
  background: #fdf2f8;
  border: 1px solid #fbcfe8;
  border-radius: 12px;
  color: #be185d;
  font-size: 11px;
}
.starred-star-item b {
  color: #db2777;
  margin-right: 2px;
}

/* ═══════════════════════════════════════════════════════════════════
   命盘统计汇总卡片样式
   ═══════════════════════════════════════════════════════════════════ */
.chart-summary-card {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 10px 14px;
  background: linear-gradient(145deg, #f8fafc 0%, #f1f5f9 100%);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  margin-top: 8px;
}
.csc-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.csc-label {
  font-size: 11px;
  color: var(--text-3);
}
.csc-value {
  font-size: 12px;
  font-weight: 600;
  color: var(--text);
  font-family: var(--font-mono);
  min-width: 18px;
  text-align: center;
}
.csc-good { color: #15803d; }
.csc-bad { color: #dc2626; }
.csc-lu { color: #15803d; }
.csc-quan { color: #d97706; }
.csc-ke { color: #2563eb; }
.csc-ji { color: #dc2626; }

/* ── 可读性修正（浅底文字对比增强）──────────────────── */
.sqf-label,
.frt-label,
.fhm-period,
.forecast-stat-main .fs-label,
.pfs-label,
.ff-label,
.meta-label,
.pattern-source,
.dt-age,
.dt-node.dt-past .dt-label,
.liunian-year,
.sec-label,
.fy-period,
.fm-period,
.fp-stem,
.fp-label,
.suggest-evidence,
.suggest-notes,
.suggest-scope,
.muted,
.dsc-prog-meta,
.dsc-prog-labels,
.dayun-year,
.remedy-scope,
.remedy-reason,
.csc-label {
  color: var(--text-2);
}

.sov-label,
.cqi-label,
.cqi-sub,
.fib-label,
.fib-arrow {
  color: var(--text-2);
}

/* ── 可读性修正（第二层：表单/详情/流月常见灰字）────────────── */
.current-params,
.hint,
.algo-label,
.detail-branch,
.close-btn,
.star-br,
.la-label,
.detail-sec-label,
.boshi-tag,
.pi-br,
.pi-explanation strong {
  color: var(--text-2);
}

.lyq-btn.lyq-cur {
  background: #fef2f2;
  border-color: #fca5a5;
  color: #991b1b;
  font-weight: 700;
}
</style>
