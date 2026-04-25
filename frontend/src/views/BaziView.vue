<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { computeBazi } from '@/api/bazi'
import type { BaziResponse, WuxingScore, DayunItem } from '@/api/bazi'
import { createCase } from '@/api/report'
import { interpretBazi } from '@/api/llm'
import { useNameStore } from '@/stores/name'
import { useProfileStore } from '@/stores/profile'
import CityPicker from '@/components/CityPicker.vue'
import { CANG_GAN, NAYIN_MAP, STEM_ELEMENT, stemColor } from '@/data/ganzhi'

const router    = useRouter()
const nameStore = useNameStore()
const profile   = useProfileStore()

// ── 表单（初始化时从个人信息 store 预填）──────────────────
const birthDt   = ref(profile.birthDt || '1990-01-15T08:30')
const lon       = ref<number | undefined>(profile.lon)
const tz        = ref(profile.tz || 'Asia/Shanghai')
const gender    = ref<'male' | 'female' | ''>(profile.gender || 'male')
const mode      = ref<'dual' | 'single'>(profile.mode || 'dual')
const solarTime = ref(profile.solarTime)
const surname   = ref(profile.surname || '')
// CityPicker 的初始城市名（响应式，用于 :initial-city prop）
const initCity  = ref(profile.cityName || '北京')
const cityName  = ref(profile.cityName || '北京')
const province  = ref(profile.province || '北京市')

// 表单显示控制：已保存个人信息时默认折叠
const showForm = ref(!profile.saved)

// 每次进入页面时重新同步 profile 数据
onMounted(() => {
  birthDt.value   = profile.birthDt   || '1990-01-15T08:30'
  lon.value       = profile.lon
  tz.value        = profile.tz        || 'Asia/Shanghai'
  gender.value    = profile.gender    || 'male'
  mode.value      = profile.mode      || 'dual'
  solarTime.value = profile.solarTime
  surname.value   = profile.surname   || ''
  initCity.value  = profile.cityName  || '北京'
  cityName.value  = profile.cityName  || '北京'
  province.value  = profile.province  || '北京市'
  // 已保存个人信息则自动排盘并折叠表单
  if (profile.saved) {
    showForm.value = false
    nextTick(() => doCalculate())
  }
})

// ── 状态 ──────────────────────────────────────────────
const loading   = ref(false)
const error     = ref('')
const result    = ref<BaziResponse | null>(null)
const activeTab = ref<'overview' | 'dayun' | 'wuxing' | 'analysis' | 'fortune' | 'ai' | 'raw'>('overview')
const saveDialogOpen = ref(false)
const saveCaseName = ref('')
const saveCaseNotes = ref('')
const saveCaseSaving = ref(false)
const saveCaseError = ref('')
const saveCaseSuccess = ref('')
const savedCaseId = ref<string | null>(null)
const aiModule = ref('')
const aiLoading = ref(false)
const aiError = ref('')
const aiStatus = ref('')
const aiDraft = ref<{
  draft_text: string
  provider: string
  model: string
  prompt_version: string
  status: string
  input_tokens: number
  output_tokens: number
} | null>(null)

const AI_MODULE_OPTIONS = [
  { value: '', label: '（全局解读）' },
  { value: 'career_detail', label: '事业详解' },
  { value: 'wealth_detail', label: '财富详解' },
  { value: 'marriage_detail', label: '婚恋详解' },
  { value: 'dayun_narrative', label: '大运叙述' },
  { value: 'fengshui_suggestion', label: '风水建议' },
]

const aiParagraphs = computed(() => {
  const text = aiDraft.value?.draft_text ?? ''
  return text
    .split(/\n{2,}/)
    .map(item => item.trim())
    .filter(Boolean)
})

const rawResultJson = computed(() => {
  if (!result.value) return ''
  return JSON.stringify(result.value, null, 2)
})

function onCityChange(e: { cityName: string; province: string; lon: number }) {
  lon.value = e.lon
  cityName.value = e.cityName
  province.value = e.province
  initCity.value = e.cityName
}

function normalizeBirthDtLocal(value: string): string {
  if (!value) return ''
  const [datePart, timePart = '00:00'] = value.split('T')
  const normalizedTime = timePart.length === 5 ? `${timePart}:00` : timePart
  return `${datePart}T${normalizedTime}`
}

function buildDefaultCaseName(): string {
  const dateLabel = birthDt.value ? birthDt.value.replace('T', ' ') : '未命名时间'
  const cityLabel = cityName.value || initCity.value || '未命名城市'
  return `八字案例 · ${cityLabel} · ${dateLabel}`
}

function extractErrorMessage(e: unknown, fallback: string): string {
  return (e as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
    ?? (e as { message?: string })?.message
    ?? fallback
}

function resetSaveState(clearSuccess = true): void {
  saveDialogOpen.value = false
  saveCaseError.value = ''
  saveCaseSaving.value = false
  savedCaseId.value = null
  if (clearSuccess) saveCaseSuccess.value = ''
}

function resetAiState(): void {
  aiModule.value = ''
  aiLoading.value = false
  aiError.value = ''
  aiStatus.value = ''
  aiDraft.value = null
}

function openSaveDialog(): void {
  if (!result.value) return
  saveCaseError.value = ''
  saveCaseSuccess.value = ''
  if (!saveCaseName.value.trim()) {
    saveCaseName.value = buildDefaultCaseName()
  }
  saveDialogOpen.value = true
}

function closeSaveDialog(): void {
  saveDialogOpen.value = false
  saveCaseError.value = ''
}

// ── 计算排盘 ──────────────────────────────────────────
async function doCalculate() {
  if (!birthDt.value || lon.value === undefined) return
  loading.value = true
  error.value   = ''
  result.value  = null
  resetSaveState()
  resetAiState()
  try {
    const [datePart, timePart] = birthDt.value.split('T')
    const dt = `${datePart}T${timePart || '00:00'}:00`
    const req: Parameters<typeof computeBazi>[0] = {
      dt,
      lon: lon.value!,
      tz: tz.value,
      mode: mode.value,
      solar_time_enabled: solarTime.value,
    }
    if (gender.value) req.gender = gender.value
    result.value = await computeBazi(req)
    activeTab.value = 'overview'
  } catch (e: unknown) {
    error.value = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? '排盘失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

async function saveCurrentCase() {
  if (!birthDt.value || lon.value === undefined) {
    saveCaseError.value = '出生信息不完整，无法保存案例'
    return
  }

  saveCaseSaving.value = true
  saveCaseError.value = ''

  try {
    const created = await createCase({
      name: saveCaseName.value.trim() || buildDefaultCaseName(),
      birth_dt_local: normalizeBirthDtLocal(birthDt.value),
      tz: tz.value,
      lon: lon.value,
      gender: gender.value || null,
      city: cityName.value || initCity.value || null,
      solar_time_enabled: solarTime.value,
      notes: saveCaseNotes.value.trim() || null,
    })
    savedCaseId.value = created.id
    saveCaseSuccess.value = `已保存到案例库：${created.name}`
    saveDialogOpen.value = false
    aiStatus.value = '案例已保存，可生成 AI 解读'
  } catch (e: unknown) {
    saveCaseError.value = extractErrorMessage(e, '保存案例失败，请稍后重试')
  } finally {
    saveCaseSaving.value = false
  }
}

async function generateAiInterpretation() {
  if (!savedCaseId.value) {
    aiError.value = '请先保存案例，再生成 AI 解读'
    return
  }

  aiLoading.value = true
  aiError.value = ''
  aiStatus.value = '生成中，请稍候…'

  try {
    const draft = await interpretBazi(savedCaseId.value, aiModule.value || undefined)
    aiDraft.value = draft
    aiStatus.value = '生成完成'
    activeTab.value = 'ai'
  } catch (e: unknown) {
    aiError.value = extractErrorMessage(e, 'AI 解读生成失败，请稍后重试')
    aiStatus.value = ''
  } finally {
    aiLoading.value = false
  }
}

function resetForm() {
  birthDt.value   = profile.birthDt   || '1990-01-15T08:30'
  lon.value       = profile.lon
  tz.value        = profile.tz        || 'Asia/Shanghai'
  gender.value    = profile.gender    || 'male'
  mode.value      = profile.mode      || 'dual'
  solarTime.value = profile.solarTime
  surname.value   = profile.surname   || ''
  initCity.value  = profile.cityName  || '北京'
  cityName.value  = profile.cityName  || '北京'
  province.value  = profile.province  || '北京市'
  result.value    = null
  error.value     = ''
  saveCaseName.value = ''
  saveCaseNotes.value = ''
  resetSaveState()
  resetAiState()
}

// ── 用神五行 → 推荐改名 ──────────────────────────────
function gotoNameSuggest() {
  const ysFavor = result.value?.yongshen?.favor ?? []
  const WX_MAP: Record<string, string> = {
    '甲':'木','乙':'木','寅':'木','卯':'木',
    '丙':'火','丁':'火','巳':'火','午':'火',
    '戊':'土','己':'土','辰':'土','戌':'土','丑':'土','未':'土',
    '庚':'金','辛':'金','申':'金','酉':'金',
    '壬':'水','癸':'水','亥':'水','子':'水',
    '木':'木','火':'火','土':'土','金':'金','水':'水',
  }
  const elements = [...new Set(ysFavor.map(t => WX_MAP[t]).filter(Boolean))]
  nameStore.setPrefill(surname.value, elements)
  router.push('/name')
}

function gotoZeri() {
  router.push('/zeri')
}

// ── 五行柱状图 ──────────────────────────────────────
const WX_LIST = [
  { key: 'wood',  label: '木', color: 'var(--wx-wood)' },
  { key: 'fire',  label: '火', color: 'var(--wx-fire)' },
  { key: 'earth', label: '土', color: 'var(--wx-earth)' },
  { key: 'metal', label: '金', color: 'var(--wx-metal)' },
  { key: 'water', label: '水', color: 'var(--wx-water)' },
]

const wuxingBars = computed(() => {
  const wx = result.value?.wuxing_score as WuxingScore | undefined
  if (!wx) return []
  const total = WX_LIST.reduce((s, e) => s + (wx[e.key] || 0), 0) || 1
  return WX_LIST.map(e => ({
    ...e,
    val: wx[e.key] || 0,
    pct: Math.round((wx[e.key] || 0) / total * 100),
  }))
})

// ── 四柱 ──────────────────────────────────────────────
const currentYear = new Date().getFullYear()

const pillars = computed(() => {
  const pp = result.value?.pillars_primary
  if (!pp) return []
  const tg = result.value?.ten_gods ?? {}
  return [
    { label: '年柱', data: pp.year,  shishen: tg.year  ?? '', isDay: false },
    { label: '月柱', data: pp.month, shishen: tg.month ?? '', isDay: false },
    { label: '日柱', data: pp.day,   shishen: '日元',          isDay: true  },
    { label: '时柱', data: pp.hour,  shishen: tg.hour  ?? '', isDay: false },
  ]
})

// ── 大运列表（DaYunModel.items，干支 = stem+branch）──
const dayunItems = computed((): DayunItem[] => result.value?.dayun?.items ?? [])
// 大运选中(展开详情)
const dayunSelected = ref(-1)
// 当前大运索引
const dayunActiveIdx = computed((): number =>
  dayunItems.value.findIndex(
    c => c.start_year != null && c.start_year <= currentYear && (c.start_year + 10) > currentYear
  )
)

// ── 十神颜色 ──────────────────────────────────────────
const TEN_GOD_COLORS: Record<string, string> = {
  '比肩': '#3b82f6', '劫财': '#6366f1',
  '食神': '#10b981', '伤官': '#f59e0b',
  '正财': '#ef4444', '偏财': '#f97316',
  '正官': '#7c3aed', '七杀': '#dc2626',
  '正印': '#065f46', '偏印': '#0891b2',
}
function tgColor(tg: string): string {
  return TEN_GOD_COLORS[tg] ?? 'var(--text-3)'
}
function wxColor(el: string): string {
  const wx: Record<string, string> = {
    '木': 'var(--wx-wood)', '火': 'var(--wx-fire)', '土': 'var(--wx-earth)',
    '金': 'var(--wx-metal)', '水': 'var(--wx-water)',
  }
  return wx[el] ?? 'currentColor'
}

// ── 五行雷达图（SVG 五边形）──────────────────────────
// 顶点顺序 12点起顺时针：木→火→土→金→水
const RADAR_ANGLES = [270, 342, 54, 126, 198].map(d => (d * Math.PI) / 180)
const RADAR_CX = 100, RADAR_CY = 100, RADAR_R = 72
const RADAR_ELEMENTS = ['木', '火', '土', '金', '水']

const radarBg = RADAR_ANGLES.map(a =>
  `${(RADAR_CX + RADAR_R * Math.cos(a)).toFixed(1)},${(RADAR_CY + RADAR_R * Math.sin(a)).toFixed(1)}`
).join(' ')
const radarBgHalf = RADAR_ANGLES.map(a =>
  `${(RADAR_CX + RADAR_R * 0.5 * Math.cos(a)).toFixed(1)},${(RADAR_CY + RADAR_R * 0.5 * Math.sin(a)).toFixed(1)}`
).join(' ')

const radarPoints = computed(() => {
  const s = result.value?.wuxing_score
  if (!s) return radarBg
  const vals = [s.wood, s.fire, s.earth, s.metal, s.water]
  const maxVal = Math.max(...vals, 1)
  return RADAR_ANGLES.map((angle, i) => {
    const r = RADAR_R * (vals[i] / maxVal)
    return `${(RADAR_CX + r * Math.cos(angle)).toFixed(1)},${(RADAR_CY + r * Math.sin(angle)).toFixed(1)}`
  }).join(' ')
})

const radarLabels = computed(() => {
  const s = result.value?.wuxing_score
  const vals = s ? [s.wood, s.fire, s.earth, s.metal, s.water] : [0,0,0,0,0]
  return RADAR_ANGLES.map((angle, i) => {
    const lr = RADAR_R + 18
    return {
      el: RADAR_ELEMENTS[i],
      val: vals[i],
      color: wxColor(RADAR_ELEMENTS[i]),
      x: +(RADAR_CX + lr * Math.cos(angle)).toFixed(1),
      y: +(RADAR_CY + lr * Math.sin(angle)).toFixed(1),
    }
  })
})

// 评分颜色
function scoreColor(score: number): string {
  if (score >= 80) return '#15803d'
  if (score >= 60) return '#d97706'
  return '#dc2626'
}
</script>

<template>
  <div class="wrap bazi-view">
    <h1 class="page-title">八字排盘</h1>

    <!-- 表单折叠控制栏 -->
    <div class="form-toggle-bar">
      <button class="btn-toggle-form" @click="showForm = !showForm">
        {{ showForm ? '▴ 收起参数' : '▾ 修改参数' }}
      </button>
      <span v-if="!showForm && result" class="current-params">
        {{ birthDt }} · {{ initCity }} · {{ gender === 'male' ? '男' : gender === 'female' ? '女' : '不指定' }}
      </span>
    </div>

    <!-- 输入表单 -->
    <section v-show="showForm" class="card form-card">
      <div class="form-grid">
        <div class="form-row">
          <label>出生时间</label>
          <input type="datetime-local" v-model="birthDt" />
        </div>
        <div class="form-row">
          <CityPicker v-model="lon" :initial-city="initCity" @city-change="onCityChange" />
        </div>
        <div class="form-row">
          <label>时区</label>
          <select v-model="tz">
            <option value="Asia/Shanghai">Asia/Shanghai（东八区）</option>
            <option value="Asia/Tokyo">Asia/Tokyo（东九区）</option>
            <option value="UTC">UTC</option>
          </select>
        </div>
        <div class="form-row">
          <label>性别</label>
          <label class="radio-opt"><input type="radio" v-model="gender" value="male" />男</label>
          <label class="radio-opt"><input type="radio" v-model="gender" value="female" />女</label>
          <label class="radio-opt"><input type="radio" v-model="gender" value="" />不指定</label>
        </div>
        <div class="form-row">
          <label>计算模式</label>
          <label class="radio-opt"><input type="radio" v-model="mode" value="dual" />双历（节气校正）</label>
          <label class="radio-opt"><input type="radio" v-model="mode" value="single" />单历</label>
        </div>
        <div class="form-row">
          <label>真太阳时</label>
          <label class="check-opt"><input type="checkbox" v-model="solarTime" />启用真太阳时修正</label>
        </div>
        <div class="form-row">
          <label>姓氏（选填）</label>
          <input v-model="surname" placeholder="如：张" maxlength="3" />
          <span class="hint">用于改名建议联动</span>
        </div>
      </div>
      <div class="form-actions">
        <button class="btn-primary" :disabled="loading" @click="doCalculate">
          {{ loading ? '排盘中…' : '✦ 开始排盘' }}
        </button>
        <button class="btn-sec" @click="resetForm">重置</button>
        <span v-if="error" class="error-msg">{{ error }}</span>
      </div>
    </section>

    <!-- 错误提示（表单折叠时也显示） -->
    <div v-if="error && !showForm" class="error-msg" style="padding: 8px 0">{{ error }}</div>

    <!-- 骨架屏 -->
    <div v-if="loading" class="skeleton-wrap">
      <div class="skel-line" style="width:60%"></div>
      <div class="skel-line" style="width:80%"></div>
      <div class="skel-box"></div>
    </div>

    <!-- 结果区 -->
    <template v-if="result">
      <!-- 四柱 -->
      <section class="card pillars-card">
        <h2 class="card-title">四柱命盘</h2>
        <!-- 新版四柱表格 -->
        <div class="pillars-tbl-wrap" v-if="result.pillars_primary">
          <table class="pillars-tbl">
            <thead>
              <tr>
                <th class="row-lbl-th"></th>
                <th>年柱</th>
                <th>月柱</th>
                <th class="day-col-th">日柱</th>
                <th>时柱</th>
              </tr>
            </thead>
            <tbody>
              <!-- 十神行 -->
              <tr>
                <td class="row-lbl">十神</td>
                <td v-for="col in (['year','month','day','hour'] as const)" :key="'ss-'+col">
                  <span class="tg-chip"
                    :class="{ 'tg-day': col==='day' }"
                    :style="col==='day' ? {} : { color: tgColor((result.ten_gods as any)?.[col] ?? '') }">
                    {{ col === 'day' ? '日主' : ((result.ten_gods as any)?.[col] ?? '') }}
                  </span>
                </td>
              </tr>
              <!-- 天干行 -->
              <tr>
                <td class="row-lbl">天干</td>
                <td v-for="col in (['year','month','day','hour'] as const)" :key="'stem-'+col"
                    :class="{ 'day-col-th': col==='day' }">
                  <span class="gz-char"
                    :style="{ color: stemColor((result.pillars_primary as any)[col].stem) }">
                    {{ (result.pillars_primary as any)[col].stem }}
                  </span>
                </td>
              </tr>
              <!-- 地支行 -->
              <tr>
                <td class="row-lbl">地支</td>
                <td v-for="col in (['year','month','day','hour'] as const)" :key="'br-'+col"
                    :class="{ 'day-col-th': col==='day' }">
                  <span class="gz-char gz-branch">
                    {{ (result.pillars_primary as any)[col].branch }}
                  </span>
                </td>
              </tr>
              <!-- 藏干行 -->
              <tr>
                <td class="row-lbl">藏干</td>
                <td v-for="col in (['year','month','day','hour'] as const)" :key="'cg-'+col">
                  <span v-for="s in (CANG_GAN[(result.pillars_primary as any)[col].branch] ?? [])"
                        :key="s" class="cang-stem"
                        :style="{ color: stemColor(s) }">{{ s }}</span>
                </td>
              </tr>
              <!-- 纳音行 -->
              <tr>
                <td class="row-lbl">纳音</td>
                <td v-for="col in (['year','month','day','hour'] as const)" :key="'ny-'+col">
                  <span class="nayin-text">
                    {{ NAYIN_MAP[(result.pillars_primary as any)[col].stem + (result.pillars_primary as any)[col].branch] ?? '' }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="pillars-meta">
          <span v-if="result.methods?.solar_date" class="meta-item">
            阳历 <b>{{ result.methods.solar_date }}</b>
          </span>
          <span v-if="result.methods?.lunar_date" class="meta-item">
            农历 <b>{{ result.methods.lunar_date }}</b>
          </span>
          <span v-if="result.start_dayun_age != null" class="meta-item">
            起运 <b>{{ result.start_dayun_age }} 岁</b>
          </span>
        </div>
        <div class="case-actions-row">
          <button class="btn-case-save" @click="openSaveDialog">
            {{ savedCaseId ? '另存到案例库' : '保存到案例库' }}
          </button>
          <span v-if="savedCaseId" class="case-save-pill case-save-pill-success">
            已保存 · {{ savedCaseId }}
          </span>
          <span v-else class="case-save-pill">保存后可继续接入 AI 解读</span>
          <span v-if="saveCaseSuccess" class="case-save-msg">{{ saveCaseSuccess }}</span>
        </div>
        <!-- 推荐改名按钮 -->
        <div v-if="result.yongshen?.favor?.length" class="suggest-name-row">
          <button class="btn-suggest-name" @click="gotoNameSuggest">
            ✦ 根据用神推荐改名
          </button>
          <span class="hint">用神：{{ result.yongshen.favor.join('、') }}</span>
        </div>
      </section>

      <!-- Tab 导航 -->
      <div class="tabs">
        <button :class="['tab-btn', { active: activeTab === 'overview' }]"
                @click="activeTab = 'overview'">综合概览</button>
        <button :class="['tab-btn', { active: activeTab === 'dayun' }]"
                @click="activeTab = 'dayun'">大运</button>
        <button :class="['tab-btn', { active: activeTab === 'wuxing' }]"
                @click="activeTab = 'wuxing'">五行格局</button>
        <button v-if="result.wealth_analysis || result.career || result.marriage_analysis || result.health || result.relationship || result.jewelry || result.fengshui || result.lifestyle"
                :class="['tab-btn', { active: activeTab === 'analysis' }]"
                @click="activeTab = 'analysis'">四维分析</button>
        <button v-if="result.monthly_fortune?.length || result.current_fortune_summary || result.liunian_detail?.length"
                :class="['tab-btn', { active: activeTab === 'fortune' }]"
                @click="activeTab = 'fortune'">运势预测</button>
        <button :class="['tab-btn', { active: activeTab === 'ai' }]"
          @click="activeTab = 'ai'">AI 解读</button>
        <button :class="['tab-btn', { active: activeTab === 'raw' }]"
          @click="activeTab = 'raw'">原始数据</button>
      </div>

      <!-- Tab: 综合概览 -->
      <section v-if="activeTab === 'overview'" class="tab-panel">
        <!-- 命局总评 -->
        <div v-if="result.bazi_summary" class="bazi-summary-block">
          <div class="summary-label">命局综合总评</div>
          <p class="bazi-summary-text">{{ result.bazi_summary }}</p>
        </div>

        <!-- 当前运势摘要 -->
        <div v-if="result.current_fortune_summary" class="cur-fortune-card">
          <div class="cf-row">
            <div class="cf-item">
              <div class="cf-lbl">当前大运</div>
              <div class="cf-val">{{ result.current_fortune_summary.current_dayun }}</div>
              <div class="cf-sub">还剩 {{ result.current_fortune_summary.dayun_years_remaining }} 年</div>
            </div>
            <div class="cf-item">
              <div class="cf-lbl">流年</div>
              <div class="cf-val">{{ result.current_fortune_summary.current_liunian }}</div>
            </div>
          </div>
          <div v-if="result.current_fortune_summary.top3_actions?.length" class="cf-actions">
            <div class="cf-lbl">今年重点</div>
            <ul class="cf-action-list">
              <li v-for="(a,i) in result.current_fortune_summary.top3_actions" :key="i">{{ a }}</li>
            </ul>
          </div>
          <div v-if="Object.keys(result.current_fortune_summary.this_year_domains || {}).length" class="cf-domains">
            <div v-for="(val, key) in result.current_fortune_summary.this_year_domains" :key="key" class="cf-domain-item">
              <span class="cf-domain-key">{{ key }}</span>
              <span class="cf-domain-val">{{ val }}</span>
            </div>
          </div>
        </div>

        <div class="overview-grid">
          <!-- 用神/忌神 -->
          <div class="ov-card" v-if="result.yongshen">
            <div class="ov-title">用神 / 忌神</div>
            <div class="ov-body">
              <div class="tag-row">
                <span v-for="t in result.yongshen.favor"   :key="'f'+t" class="tag tag-favor">{{ t }}</span>
                <span v-for="t in result.yongshen.avoid"   :key="'a'+t" class="tag tag-avoid">{{ t }}</span>
                <span v-for="t in (result.yongshen.neutral ?? [])" :key="'n'+t" class="tag tag-neutral">{{ t }}</span>
              </div>
              <p v-if="result.yongshen.rationale" class="ov-summary">{{ result.yongshen.rationale }}</p>
            </div>
          </div>
          <!-- 日元强弱 -->
          <div class="ov-card" v-if="result.day_master_strength">
            <div class="ov-title">日元强弱</div>
            <div class="ov-body">
              <b>{{ result.day_master_strength.tier }}</b>
              <p v-if="result.day_master_strength.score != null" class="ov-summary">
                强弱分：{{ result.day_master_strength.score.toFixed(1) }}
              </p>
            </div>
          </div>
          <!-- 格局 -->
          <div class="ov-card" v-if="result.geju">
            <div class="ov-title">格局</div>
            <div class="ov-body">
              <b>{{ result.geju.geju_name }}</b>
              <span v-if="result.geju.geju_level" class="geju-level-badge">{{ result.geju.geju_level }}</span>
              <span v-if="result.geju.is_broken" class="geju-broken-badge">破格</span>
              <span v-if="result.geju.confidence != null" class="geju-conf">置信 {{ (result.geju.confidence * 100).toFixed(0) }}%</span>
              <p v-if="result.geju.geju_detail" class="ov-summary">{{ result.geju.geju_detail }}</p>
              <p v-else-if="result.geju.interpretation_text" class="ov-summary">{{ result.geju.interpretation_text.slice(0, 80) }}…</p>
              <p v-if="result.geju.classic_ref" class="ov-classic-ref">📜 {{ result.geju.classic_ref }}</p>
            </div>
          </div>
          <!-- 命宫/身宫 -->
          <div class="ov-card ov-card-wide" v-if="result.palace?.ming_gong">
            <div class="ov-title">命宫 / 身宫</div>
            <div class="ov-body">
              <span>命宫：<b>{{ result.palace.ming_gong.dizhi }} {{ result.palace.ming_gong.palace_name }}</b></span>
              <span v-if="result.palace.shen_gong" style="margin-left:12px">
                身宫：<b>{{ result.palace.shen_gong?.dizhi }} {{ result.palace.shen_gong?.palace_name }}</b>
              </span>
            </div>
            <div v-if="result.palace.twelve_palaces?.length" class="twelve-palaces">
              <div v-for="tp in result.palace.twelve_palaces" :key="tp.palace_name" class="tp-item">
                <span class="tp-name">{{ tp.palace_name }}</span>
                <span class="tp-dizhi">{{ tp.dizhi }}</span>
                <span v-if="tp.shishen" class="tp-ss">{{ tp.shishen }}</span>
                <span v-if="tp.tiangan" class="tp-tg">{{ tp.tiangan }}</span>
                <span v-if="tp.strength" :class="['tp-str', `tp-str-${tp.strength}`]">{{ tp.strength }}</span>
                <span v-if="tp.note" class="tp-note">{{ tp.note }}</span>
              </div>
            </div>
            <p v-if="result.palace.interpretation_text" class="ov-summary">{{ result.palace.interpretation_text }}</p>
          </div>
          <!-- 开运数据 -->
          <div class="ov-card" v-if="result.lucky">
            <div class="ov-title">开运参考</div>
            <div class="ov-body">
              <div class="lucky-row">
                <span class="lucky-lbl">幸运色</span>
                <span v-for="c in result.lucky.lucky_colors" :key="c" class="lucky-tag">{{ c }}</span>
              </div>
              <div class="lucky-row">
                <span class="lucky-lbl">幸运数</span>
                <span v-for="n in result.lucky.lucky_numbers" :key="n" class="lucky-tag">{{ n }}</span>
              </div>
              <div class="lucky-row">
                <span class="lucky-lbl">方位 / 物品</span>
                <span class="lucky-tag">{{ result.lucky.lucky_direction }}</span>
                <span class="lucky-tag">{{ result.lucky.lucky_item }}</span>
              </div>
              <div v-if="result.lucky.avoid_colors?.length" class="lucky-row lucky-avoid">
                <span class="lucky-lbl">忌颜色</span>
                <span v-for="c in result.lucky.avoid_colors" :key="c" class="lucky-tag lucky-tag-avoid">{{ c }}</span>
              </div>
              <div v-if="result.lucky.avoid_direction" class="lucky-row lucky-avoid">
                <span class="lucky-lbl">忌方位</span>
                <span class="lucky-tag lucky-tag-avoid">{{ result.lucky.avoid_direction }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 命局人生弧线 -->
        <div v-if="result.life_arc" class="life-arc-block">
          <div class="life-arc-header">
            <span class="life-arc-title">人生格局总论</span>
            <span v-if="result.life_arc.overall_tier" class="life-arc-tier">{{ result.life_arc.overall_tier }}</span>
          </div>
          <blockquote v-if="result.life_arc.life_motto" class="life-motto">
            "{{ result.life_arc.life_motto }}"
          </blockquote>
          <div v-if="result.life_arc.early_fortune || result.life_arc.mid_fortune || result.life_arc.late_fortune" class="life-arc-periods">
            <div v-if="result.life_arc.early_fortune" class="lp-item">
              <span class="lp-label">少年</span>
              <p class="lp-text">{{ result.life_arc.early_fortune }}</p>
            </div>
            <div v-if="result.life_arc.mid_fortune" class="lp-item">
              <span class="lp-label">中年</span>
              <p class="lp-text">{{ result.life_arc.mid_fortune }}</p>
            </div>
            <div v-if="result.life_arc.late_fortune" class="lp-item">
              <span class="lp-label">晚年</span>
              <p class="lp-text">{{ result.life_arc.late_fortune }}</p>
            </div>
          </div>
          <p v-if="result.life_arc.interpretation_text" class="life-arc-body">{{ result.life_arc.interpretation_text }}</p>
          <p v-if="result.life_arc.optimal_action" class="pers-advice" style="margin-bottom:var(--sp-3)">💡 {{ result.life_arc.optimal_action }}</p>
          <div v-if="result.life_arc.peak_periods?.length || result.life_arc.caution_periods?.length" class="life-arc-peaks">
            <div v-if="result.life_arc.peak_periods?.length" class="peak-item">
              <span class="peak-lbl peak-good">旺运大运</span>
              <span v-for="p in result.life_arc.peak_periods" :key="p" class="peak-tag peak-tag-good">{{ p }}</span>
            </div>
            <div v-if="result.life_arc.caution_periods?.length" class="peak-item">
              <span class="peak-lbl peak-warn">注意大运</span>
              <span v-for="p in result.life_arc.caution_periods" :key="p" class="peak-tag peak-tag-warn">{{ p }}</span>
            </div>
          </div>
        </div>

        <!-- 性格分析 -->
        <div v-if="result.personality" class="personality-block">
          <div class="section-title">性格分析</div>
          <p class="personality-trait"><b>{{ result.personality.day_stem_trait }}</b>（{{ result.personality.strength_modifier }}）</p>
          <div class="personality-cols">
            <div v-if="result.personality.advantages?.length" class="pers-col">
              <div class="pers-lbl pers-good">✦ 优势</div>
              <ul class="pers-list">
                <li v-for="a in result.personality.advantages" :key="a">{{ a }}</li>
              </ul>
            </div>
            <div v-if="result.personality.disadvantages?.length" class="pers-col">
              <div class="pers-lbl pers-warn">△ 弱点</div>
              <ul class="pers-list">
                <li v-for="d in result.personality.disadvantages" :key="d">{{ d }}</li>
              </ul>
            </div>
          </div>
          <p v-if="result.personality.growth_advice" class="pers-advice">💡 {{ result.personality.growth_advice }}</p>
          <div v-if="result.personality.communication_style || result.personality.stress_coping_mode || result.personality.potential_activation" class="pers-extra">
            <p v-if="result.personality.communication_style" class="pers-sub">🗣 沟通风格：{{ result.personality.communication_style }}</p>
            <p v-if="result.personality.stress_coping_mode" class="pers-sub">🧘 压力应对：{{ result.personality.stress_coping_mode }}</p>
            <p v-if="result.personality.potential_activation" class="pers-sub">⚡ 潜能激活：{{ result.personality.potential_activation }}</p>
          </div>
          <p v-if="result.personality.disclaimer" class="ac-disclaimer">{{ result.personality.disclaimer }}</p>
        </div>

        <!-- 神煞 -->
        <div v-if="result.shensha?.length" class="shensha-section">
          <div class="section-title">神煞</div>
          <div class="shensha-list">
            <div v-for="s in (result.shensha ?? []).filter(s => s.priority === 'A' || s.priority === 'B')" :key="s.name"
                 :class="['shensha-item', s.is_beneficial ? 'sh-good' : 'sh-bad']">
              <span class="sh-name">{{ s.name }}</span>
              <span class="sh-pillar">{{ s.pillar === 'year' ? '年' : s.pillar === 'month' ? '月' : s.pillar === 'day' ? '日' : '时' }}柱</span>
              <span class="sh-meaning">{{ s.meaning }}</span>
            </div>
          </div>
        </div>

        <!-- 推荐改名 -->
        <div v-if="result.yongshen?.favor?.length" class="suggest-name-row">
          <button class="btn-suggest-name" @click="gotoNameSuggest">
            ✦ 根据用神推荐改名
          </button>
          <button class="btn-zeri-link" @click="gotoZeri">📅 择日</button>
          <span class="hint">用神：{{ result.yongshen.favor.join('、') }}</span>
        </div>
      </section>

      <!-- Tab: 大运 -->
      <section v-if="activeTab === 'dayun'" class="tab-panel">
        <!-- 起运信息栏 -->
        <div class="dy-header">
          <span v-if="result.start_dayun_age != null">起运 <b>{{ result.start_dayun_age }} 岁</b></span>
          <span v-if="result.dayun?.direction" class="dy-dir">
            {{ result.dayun.direction === 'forward' ? '顺运' : '逆运' }}
          </span>
          <span v-if="dayunActiveIdx >= 0" class="dy-cur-lbl">
            当前大运：<b>{{ (dayunItems[dayunActiveIdx].stem ?? '') + (dayunItems[dayunActiveIdx].branch ?? '') }}</b>
            &nbsp;<span class="dy-cur-age">（{{ dayunItems[dayunActiveIdx].start_age ?? '?' }}–{{ (dayunItems[dayunActiveIdx].start_age ?? 0) + 9 }}岁）</span>
          </span>
        </div>

        <!-- 横向时间轴 -->
        <div v-if="dayunItems.length" class="dy-timeline-wrap">
          <div class="dy-track">
            <div v-for="(c, i) in dayunItems" :key="i"
                 :class="['dy-step',
                   { 'dy-cur':  i === dayunActiveIdx },
                   { 'dy-past': c.start_year != null && (c.start_year + 10) <= currentYear },
                   { 'dy-sel':  dayunSelected === i },
                 ]"
                 @click="dayunSelected = dayunSelected === i ? -1 : i">
              <!-- 连接线 + 节点 -->
              <div class="dy-dot-row">
                <div class="dy-line-l" v-if="i > 0"></div>
                <div class="dy-dot">
                  <div v-if="i === dayunActiveIdx" class="dy-dot-ring"></div>
                </div>
                <div class="dy-line-r" v-if="i < dayunItems.length - 1"></div>
              </div>
              <!-- 卡片 -->
              <div class="dy-card">
                <div class="dy-gz">{{ (c.stem ?? '') + (c.branch ?? '') }}</div>
                <div v-if="c.ten_god" class="dy-tg-chip"
                     :style="{ background: tgColor(c.ten_god) + '22', color: tgColor(c.ten_god), borderColor: tgColor(c.ten_god) + '55' }">
                  {{ c.ten_god }}
                </div>
                <div class="dy-age-range">{{ c.start_age ?? '?' }}–{{ (c.start_age ?? 0) + 9 }}岁</div>
                <div class="dy-yr">{{ c.start_year ?? '' }}年</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 展开详情面板 -->
        <transition name="dy-expand">
          <div v-if="dayunSelected >= 0 && dayunItems[dayunSelected]" class="dy-detail-card">
            <div class="dy-detail-header">
              <span class="dy-detail-gz">
                {{ (dayunItems[dayunSelected].stem ?? '') + (dayunItems[dayunSelected].branch ?? '') }}
              </span>
              <span v-if="dayunItems[dayunSelected].ten_god" class="tg-chip"
                    :style="{ background: tgColor(dayunItems[dayunSelected].ten_god!) + '22', color: tgColor(dayunItems[dayunSelected].ten_god!) }">
                {{ dayunItems[dayunSelected].ten_god }}
              </span>
              <span class="dy-detail-period">
                {{ dayunItems[dayunSelected].start_age ?? '?' }}–{{ (dayunItems[dayunSelected].start_age ?? 0) + 9 }}岁
                &nbsp;({{ dayunItems[dayunSelected].start_year ?? '' }}–{{ (dayunItems[dayunSelected].start_year ?? 0) + 9 }}年)
              </span>
              <button class="dy-detail-close" @click="dayunSelected = -1">×</button>
            </div>
            <p v-if="dayunItems[dayunSelected].narrative" class="dy-detail-narrative">{{ dayunItems[dayunSelected].narrative }}</p>
            <div v-if="dayunItems[dayunSelected].wealth_hint || dayunItems[dayunSelected].health_hint || dayunItems[dayunSelected].love_hint"
                 class="dayun-hints">
              <span v-if="dayunItems[dayunSelected].wealth_hint" class="dh-tag dh-wealth">财运：{{ dayunItems[dayunSelected].wealth_hint }}</span>
              <span v-if="dayunItems[dayunSelected].health_hint" class="dh-tag dh-health">健康：{{ dayunItems[dayunSelected].health_hint }}</span>
              <span v-if="dayunItems[dayunSelected].love_hint"   class="dh-tag dh-love">  感情：{{ dayunItems[dayunSelected].love_hint }}</span>
            </div>
          </div>
        </transition>

        <p v-if="!dayunItems.length" class="muted">暂无大运数据</p>
      </section>

      <!-- Tab: 五行格局 -->
      <section v-if="activeTab === 'wuxing'" class="tab-panel">
        <!-- 雷达图 + 横条并排 -->
        <div class="wx-chart-row">
          <!-- 五行雷达图 -->
          <div v-if="result.wuxing_score" class="wx-radar-wrap">
            <svg viewBox="0 0 200 200" class="wx-radar-svg">
              <!-- 背景网格 -->
              <polygon :points="radarBgHalf" fill="none" stroke="var(--border)" stroke-width="0.8" stroke-dasharray="3,2"/>
              <polygon :points="radarBg"     fill="none" stroke="var(--border)" stroke-width="1"/>
              <!-- 轴线 -->
              <line v-for="(angle, i) in RADAR_ANGLES" :key="`axis-${i}`"
                :x1="RADAR_CX" :y1="RADAR_CY"
                :x2="+(RADAR_CX + RADAR_R * Math.cos(angle)).toFixed(1)"
                :y2="+(RADAR_CY + RADAR_R * Math.sin(angle)).toFixed(1)"
                stroke="var(--border)" stroke-width="0.6" />
              <!-- 数据区域 -->
              <polygon :points="radarPoints"
                fill="var(--accent-soft)" fill-opacity="0.6"
                stroke="var(--accent)" stroke-width="2"/>
              <!-- 顶点圆点 -->
              <circle v-for="(pt, i) in radarPoints.split(' ')" :key="`dot-${i}`"
                :cx="+pt.split(',')[0]" :cy="+pt.split(',')[1]" r="3"
                fill="var(--accent)" />
              <!-- 标签 -->
              <text v-for="lb in radarLabels" :key="lb.el"
                :x="lb.x" :y="lb.y"
                text-anchor="middle" dominant-baseline="middle"
                class="radar-label" :fill="lb.color">{{ lb.el }}</text>
            </svg>
          </div>
          <!-- 横条图 -->
          <div v-if="wuxingBars.length" class="wuxing-list">
            <div v-for="bar in wuxingBars" :key="bar.key" class="wx-row">
              <div class="wx-lbl" :style="{ color: bar.color }">{{ bar.label }}</div>
              <div class="wx-bar-wrap">
                <div class="wx-bar" :style="{ width: bar.pct + '%', background: bar.color }"></div>
              </div>
              <div class="wx-val">{{ bar.val.toFixed(1) }}（{{ bar.pct }}%）</div>
            </div>
          </div>
        </div>
        <!-- 均衡评分 -->
        <div v-if="result.wuxing_balance_score != null" class="wx-balance">
          <div class="wx-balance-row">
            <span class="wx-bal-lbl">五行均衡分</span>
            <span class="wx-bal-val" :style="{ color: scoreColor(result.wuxing_balance_score) }">
              {{ result.wuxing_balance_score.toFixed(0) }}/100
            </span>
          </div>
          <div v-if="result.wuxing_weak?.length || result.wuxing_strong?.length" class="wx-imbalance">
            <span v-if="result.wuxing_weak?.length" class="wx-weak">
              偏缺：{{ result.wuxing_weak.join('、') }}
            </span>
            <span v-if="result.wuxing_strong?.length" class="wx-strong">
              偏旺：{{ result.wuxing_strong.join('、') }}
            </span>
          </div>
          <p v-if="result.balance_advice" class="wx-advice">💡 {{ result.balance_advice }}</p>
        </div>
        <p v-else-if="!wuxingBars.length" class="muted">暂无五行数据</p>
      </section>

      <!-- Tab: 四维分析 -->
      <section v-if="activeTab === 'analysis'" class="tab-panel">
        <!-- 财运 -->
        <div v-if="result.wealth_analysis" class="analysis-card">
          <div class="ac-header">
            <span class="ac-icon">💰</span>
            <span class="ac-title">财运分析</span>
            <span class="ac-score" :style="{ color: scoreColor(result.wealth_analysis.wealth_score) }">
              {{ result.wealth_analysis.wealth_score }}<small>/100</small>
            </span>
            <span class="ac-tier">{{ result.wealth_analysis.wealth_tier }}</span>
          </div>
          <p class="ac-range">年收入参考范围：<b>{{ result.wealth_analysis.annual_range }}</b></p>
          <div v-if="result.wealth_analysis.industries?.length" class="ac-tags">
            <span class="ac-tag-lbl">适合行业</span>
            <span v-for="ind in result.wealth_analysis.industries" :key="ind" class="ac-tag">{{ ind }}</span>
          </div>
          <p v-if="result.wealth_analysis.strategy" class="ac-text">{{ result.wealth_analysis.strategy }}</p>
          <p v-if="result.wealth_analysis.investment_preference" class="ac-sub">
            投资偏好：{{ result.wealth_analysis.investment_preference }}
          </p>
          <p v-if="result.wealth_analysis.financial_taboos" class="ac-sub ac-sub-warn">⚠ 理财禁忌：{{ result.wealth_analysis.financial_taboos }}</p>
          <p v-if="result.wealth_analysis.wealth_accumulation_phases" class="ac-sub">💰 积累节奏：{{ result.wealth_analysis.wealth_accumulation_phases }}</p>
          <div v-if="result.wealth_analysis.dayun_forecast?.length" class="ac-dayun-fc">
            <span class="ac-tag-lbl">大运财运趋势</span>
            <div v-for="df in result.wealth_analysis.dayun_forecast" :key="df.ganzhi" class="ac-df-item">
              <span class="ac-df-gz">{{ df.ganzhi }}</span>
              <span class="ac-df-trend">{{ df.trend }}</span>
            </div>
          </div>
          <p v-if="result.wealth_analysis.interpretation_text" class="ac-interp">{{ result.wealth_analysis.interpretation_text }}</p>
          <p v-if="result.wealth_analysis.disclaimer" class="ac-disclaimer">{{ result.wealth_analysis.disclaimer }}</p>
        </div>
        <!-- 事业 -->
        <div v-if="result.career" class="analysis-card">
          <div class="ac-header">
            <span class="ac-icon">🏆</span>
            <span class="ac-title">事业分析</span>
            <span class="ac-score" :style="{ color: scoreColor(result.career.career_score) }">
              {{ result.career.career_score }}<small>/100</small>
            </span>
            <span v-if="result.career.leadership_potential" class="ac-tier">领导潜质</span>
          </div>
          <div v-if="result.career.career_directions?.length" class="ac-tags">
            <span class="ac-tag-lbl">发展方向</span>
            <span v-for="d in result.career.career_directions" :key="d" class="ac-tag">{{ d }}</span>
          </div>
          <div v-if="result.career.suitable_industries?.length" class="ac-tags">
            <span class="ac-tag-lbl">适合行业</span>
            <span v-for="ind in result.career.suitable_industries" :key="ind" class="ac-tag">{{ ind }}</span>
          </div>
          <p v-if="result.career.development_advice" class="ac-text">{{ result.career.development_advice }}</p>
          <p v-if="result.career.optimal_move_timing" class="ac-sub">最佳时机：{{ result.career.optimal_move_timing }}</p>
          <p v-if="result.career.entrepreneurship_assessment" class="ac-sub">🚀 创业评估：{{ result.career.entrepreneurship_assessment }}</p>
          <p v-if="result.career.five_year_roadmap" class="ac-sub">📋 五年规划：{{ result.career.five_year_roadmap }}</p>
          <p v-if="result.career.collaboration_style" class="ac-sub">🤝 合作方式：{{ result.career.collaboration_style }}</p>
          <p v-if="result.career.interpretation_text" class="ac-interp">{{ result.career.interpretation_text }}</p>
          <p v-if="result.career.disclaimer" class="ac-disclaimer">{{ result.career.disclaimer }}</p>
        </div>
        <!-- 婚恋 -->
        <div v-if="result.marriage_analysis" class="analysis-card">
          <div class="ac-header">
            <span class="ac-icon">💑</span>
            <span class="ac-title">婚恋分析</span>
            <span class="ac-score" :style="{ color: scoreColor(result.marriage_analysis.marriage_score) }">
              {{ result.marriage_analysis.marriage_score }}<small>/100</small>
            </span>
            <span class="ac-tier">桃花{{ result.marriage_analysis.peach_blossom }}</span>
          </div>
          <p class="ac-text">另一半：{{ result.marriage_analysis.partner_profile }}</p>
          <div class="ac-row">
            <span>最佳年龄：{{ result.marriage_analysis.optimal_marriage_age }}</span>
            <span>方位：{{ result.marriage_analysis.partner_direction }}</span>
            <span>五行：{{ result.marriage_analysis.partner_wuxing }}</span>
          </div>
          <div v-if="result.marriage_analysis.marriage_windows?.length" class="ac-tags">
            <span class="ac-tag-lbl">姻缘窗口</span>
            <span v-for="w in result.marriage_analysis.marriage_windows" :key="w" class="ac-tag">{{ w }}</span>
          </div>
          <p v-if="result.marriage_analysis.children_outlook" class="ac-sub">子嗣：{{ result.marriage_analysis.children_outlook }}</p>
          <p v-if="result.marriage_analysis.children_timing" class="ac-sub">🍼 生育时机：{{ result.marriage_analysis.children_timing }}</p>
          <p v-if="result.marriage_analysis.emotional_pitfalls" class="ac-sub ac-sub-warn">⚠ 情感雷区：{{ result.marriage_analysis.emotional_pitfalls }}</p>
          <p v-if="result.marriage_analysis.second_marriage_indicator" class="ac-sub">💔 感情波折：{{ result.marriage_analysis.second_marriage_indicator }}</p>
          <p v-if="result.marriage_analysis.interpretation_text" class="ac-interp">{{ result.marriage_analysis.interpretation_text }}</p>
          <p v-if="result.marriage_analysis.disclaimer" class="ac-disclaimer">{{ result.marriage_analysis.disclaimer }}</p>
        </div>
        <!-- 健康 -->
        <div v-if="result.health" class="analysis-card">
          <div class="ac-header">
            <span class="ac-icon">🏥</span>
            <span class="ac-title">健康分析</span>
            <span class="ac-score" :style="{ color: scoreColor(result.health.health_score) }">
              {{ result.health.health_score }}<small>/100</small>
            </span>
            <span :class="['ac-tier', result.health.risk_level === '高' ? 'tier-warn' : '']">
              风险{{ result.health.risk_level }}
            </span>
          </div>
          <div v-if="result.health.risk_organs?.length" class="ac-tags">
            <span class="ac-tag-lbl">注意器官</span>
            <span v-for="o in result.health.risk_organs" :key="o" class="ac-tag ac-tag-warn">{{ o }}</span>
          </div>
          <p v-if="result.health.health_advice" class="ac-text">{{ result.health.health_advice }}</p>
          <div v-if="result.health.exercise?.length || result.health.diet?.length" class="ac-health-tips">
            <div v-if="result.health.exercise?.length" class="ht-row">
              <span class="ht-lbl">运动</span>
              <span v-for="e in result.health.exercise" :key="e" class="ht-item">{{ e }}</span>
            </div>
            <div v-if="result.health.diet?.length" class="ht-row">
              <span class="ht-lbl">饮食</span>
              <span v-for="d in result.health.diet" :key="d" class="ht-item">{{ d }}</span>
            </div>
          </div>
          <p v-if="result.health.peak_period" class="ac-sub">✦ 体质巅峰期：{{ result.health.peak_period }}</p>
          <p v-if="result.health.seasonal_health" class="ac-sub">🌿 季节养生：{{ result.health.seasonal_health }}</p>
          <p v-if="result.health.mental_health_advice" class="ac-sub">🧠 心理健康：{{ result.health.mental_health_advice }}</p>
          <p v-if="result.health.constitution_type" class="ac-sub">🏋 五行体质：{{ result.health.constitution_type }}</p>
          <p v-if="result.health.interpretation_text" class="ac-interp">{{ result.health.interpretation_text }}</p>
          <p v-if="result.health.disclaimer" class="ac-disclaimer">{{ result.health.disclaimer }}</p>
        </div>
        <p v-if="!result.wealth_analysis && !result.career && !result.marriage_analysis && !result.health" class="muted">
          暂无四维分析数据
        </p>

        <!-- 六亲人际 -->
        <div v-if="result.relationship" class="analysis-card">
          <div class="ac-header">
            <span class="ac-icon">👥</span>
            <span class="ac-title">六亲人际</span>
            <span class="ac-score" :style="{ color: scoreColor(result.relationship.relationship_score) }">
              {{ result.relationship.relationship_score }}<small>/100</small>
            </span>
          </div>
          <div v-if="result.relationship.liu_qin && Object.keys(result.relationship.liu_qin).length" class="ac-liuqin">
            <div v-for="(val, key) in result.relationship.liu_qin" :key="key" class="lq-item">
              <span class="lq-key">{{ key }}</span>
              <span class="lq-val">{{ val }}</span>
            </div>
          </div>
          <div v-if="result.relationship.noble_people?.length" class="ac-tags">
            <span class="ac-tag-lbl">贵人</span>
            <span v-for="p in result.relationship.noble_people" :key="p" class="ac-tag ac-tag-noble">{{ p }}</span>
          </div>
          <div v-if="result.relationship.petty_people?.length" class="ac-tags">
            <span class="ac-tag-lbl">小人</span>
            <span v-for="p in result.relationship.petty_people" :key="p" class="ac-tag ac-tag-warn">{{ p }}</span>
          </div>
          <p v-if="result.relationship.social_strategy" class="ac-text">{{ result.relationship.social_strategy }}</p>
          <p v-if="result.relationship.interpretation_text" class="ac-interp">{{ result.relationship.interpretation_text }}</p>
          <p v-if="result.relationship.disclaimer" class="ac-disclaimer">{{ result.relationship.disclaimer }}</p>
        </div>

        <!-- 开运饰品 -->
        <div v-if="result.jewelry" class="analysis-card">
          <div class="ac-header">
            <span class="ac-icon">💎</span>
            <span class="ac-title">开运饰品</span>
          </div>
          <div class="jewelry-items">
            <div class="ji-card ji-primary">
              <div class="ji-label">主饰品</div>
              <div class="ji-detail">
                <span v-if="result.jewelry.primary.material">{{ result.jewelry.primary.material }}</span>
                <span v-if="result.jewelry.primary.gemstone" class="ji-gem">{{ result.jewelry.primary.gemstone }}</span>
              </div>
              <div class="ji-meta">
                <span v-if="result.jewelry.primary.position">佩戴：{{ result.jewelry.primary.position }}</span>
                <span v-if="result.jewelry.primary.wuxing">五行：{{ result.jewelry.primary.wuxing }}</span>
              </div>
            </div>
            <div v-if="result.jewelry.secondary" class="ji-card">
              <div class="ji-label">辅饰品</div>
              <div class="ji-detail">
                <span v-if="result.jewelry.secondary.material">{{ result.jewelry.secondary.material }}</span>
                <span v-if="result.jewelry.secondary.gemstone" class="ji-gem">{{ result.jewelry.secondary.gemstone }}</span>
              </div>
              <div class="ji-meta">
                <span v-if="result.jewelry.secondary.position">佩戴：{{ result.jewelry.secondary.position }}</span>
                <span v-if="result.jewelry.secondary.wuxing">五行：{{ result.jewelry.secondary.wuxing }}</span>
              </div>
            </div>
          </div>
          <p v-if="result.jewelry.combination" class="ac-sub">✦ 搭配建议：{{ result.jewelry.combination }}</p>
          <p v-if="result.jewelry.taboo?.length" class="ac-sub ac-sub-warn">⚠ 禁忌：{{ result.jewelry.taboo.join('、') }}</p>
          <p v-if="result.jewelry.disclaimer" class="ac-disclaimer">{{ result.jewelry.disclaimer }}</p>
        </div>

        <!-- 风水建议 -->
        <div v-if="result.fengshui" class="analysis-card">
          <div class="ac-header">
            <span class="ac-icon">🏠</span>
            <span class="ac-title">风水建议</span>
          </div>
          <div v-if="result.fengshui.auspicious_directions?.length" class="ac-tags">
            <span class="ac-tag-lbl">吉方位</span>
            <span v-for="d in result.fengshui.auspicious_directions" :key="d" class="ac-tag">{{ d }}</span>
          </div>
          <div v-if="result.fengshui.lucky_colors?.length" class="ac-tags">
            <span class="ac-tag-lbl">旺色</span>
            <span v-for="c in result.fengshui.lucky_colors" :key="c" class="ac-tag">{{ c }}</span>
          </div>
          <div v-if="result.fengshui.decor?.length" class="ac-tags">
            <span class="ac-tag-lbl">摆件</span>
            <span v-for="d in result.fengshui.decor" :key="d" class="ac-tag">{{ d }}</span>
          </div>
          <div v-if="result.fengshui.plants?.length" class="ac-tags">
            <span class="ac-tag-lbl">绿植</span>
            <span v-for="p in result.fengshui.plants" :key="p" class="ac-tag">{{ p }}</span>
          </div>
          <p v-if="result.fengshui.taboo?.length" class="ac-sub ac-sub-warn">⚠ 禁忌：{{ result.fengshui.taboo.join('、') }}</p>
          <p v-if="result.fengshui.disclaimer" class="ac-disclaimer">{{ result.fengshui.disclaimer }}</p>
        </div>

        <!-- 生活建议 -->
        <div v-if="result.lifestyle" class="analysis-card">
          <div class="ac-header">
            <span class="ac-icon">🌿</span>
            <span class="ac-title">生活建议</span>
          </div>
          <div v-if="result.lifestyle.exercise?.length" class="ac-tags">
            <span class="ac-tag-lbl">运动</span>
            <span v-for="e in result.lifestyle.exercise" :key="e" class="ac-tag">{{ e }}</span>
          </div>
          <div v-if="result.lifestyle.best_times" class="ac-tags">
            <span class="ac-tag-lbl">最佳时段</span>
            <span class="ac-tag">{{ result.lifestyle.best_times }}</span>
          </div>
          <div v-if="result.lifestyle.diet?.length" class="ac-tags">
            <span class="ac-tag-lbl">饮食</span>
            <span v-for="d in result.lifestyle.diet" :key="d" class="ac-tag">{{ d }}</span>
          </div>
          <p v-if="result.lifestyle.travel_direction" class="ac-sub">🧭 旅行方位：{{ result.lifestyle.travel_direction }}</p>
          <p v-if="result.lifestyle.sleep_advice" class="ac-sub">😴 睡眠建议：{{ result.lifestyle.sleep_advice }}</p>
          <p v-if="result.lifestyle.disclaimer" class="ac-disclaimer">{{ result.lifestyle.disclaimer }}</p>
        </div>
      </section>

      <!-- Tab: 运势预测 -->
      <section v-if="activeTab === 'fortune'" class="tab-panel">
        <!-- 当前运势摘要 -->
        <div v-if="result.current_fortune_summary" class="section-block card">
          <div class="section-title">当前运势概况</div>
          <div class="cfs-info">
            <span v-if="result.current_fortune_summary.current_dayun" class="cfs-item">当前大运：<b>{{ result.current_fortune_summary.current_dayun }}</b></span>
            <span v-if="result.current_fortune_summary.dayun_years_remaining" class="cfs-item">剩余 <b>{{ result.current_fortune_summary.dayun_years_remaining }}</b> 年</span>
            <span v-if="result.current_fortune_summary.current_liunian" class="cfs-item">流年：<b>{{ result.current_fortune_summary.current_liunian }}</b></span>
          </div>
          <div v-if="result.current_fortune_summary.this_year_domains && Object.keys(result.current_fortune_summary.this_year_domains).length" class="cfs-domains">
            <div v-for="(val, key) in result.current_fortune_summary.this_year_domains" :key="key" class="cfs-dom">
              <span class="cfs-dk">{{ key }}</span>
              <span class="cfs-dv">{{ val }}</span>
            </div>
          </div>
          <div v-if="result.current_fortune_summary.top3_actions?.length" class="cfs-actions">
            <div class="cfs-actions-title">📌 重点行动建议</div>
            <div v-for="(a, i) in result.current_fortune_summary.top3_actions" :key="i" class="cfs-action">{{ i + 1 }}. {{ a }}</div>
          </div>
        </div>
        <!-- 流年四维详情 -->
        <div v-if="result.liunian_detail?.length" class="section-block">
          <div class="section-title">流年运势</div>
          <div class="liunian-detail-list">
            <div v-for="ld in result.liunian_detail" :key="ld.year" class="ld-item">
              <div class="ld-head">
                <span class="ld-gz">{{ ld.ganzhi }}</span>
                <span class="ld-year">{{ ld.year }}年</span>
                <span class="ld-score" :style="{ color: scoreColor(ld.annual_score) }">{{ ld.annual_score }}分</span>
                <span v-if="ld.ten_god" class="ld-tg">{{ ld.ten_god }}</span>
              </div>
              <div v-if="ld.tai_sui_relations?.length" class="ld-taisui">
                <span v-for="(ts, ti) in ld.tai_sui_relations" :key="ti" class="ld-ts-tag">{{ ts }}</span>
              </div>
              <div v-if="Object.keys(ld.domain_forecasts).length" class="ld-domains">
                <div v-for="(val, key) in ld.domain_forecasts" :key="key" class="ld-domain">
                  <span class="ld-dk">{{ key }}</span>
                  <span class="ld-dv">{{ val }}</span>
                </div>
              </div>
              <div v-if="ld.notable_months?.length" class="ld-notable">
                <span class="ld-notable-lbl">重要月份：</span>
                <span v-for="nm in ld.notable_months" :key="nm" class="ld-notable-m">{{ nm }}月</span>
              </div>
              <div v-if="ld.clash_pillars?.length" class="ld-clash-pillars">
                <span class="ld-notable-lbl">冲克柱位：</span>
                <span v-for="cp in ld.clash_pillars" :key="cp" class="ld-ts-tag">{{ cp }}</span>
              </div>
              <span v-if="ld.flow_wuxing" class="ld-flow-wx">五行 {{ ld.flow_wuxing }}</span>
              <p v-if="ld.optimal_action" class="ld-action">💡 {{ ld.optimal_action }}</p>
              <p v-if="ld.interpretation_text" class="ac-interp">{{ ld.interpretation_text }}</p>
            </div>
          </div>
        </div>
        <!-- 人生里程碑 -->
        <div v-if="result.milestones?.length" class="section-block">
          <div class="section-title">人生里程碑</div>
          <div class="milestones-list">
            <div v-for="ms in result.milestones" :key="ms.age" :class="['ms-item', `ms-${ms.risk_level}`]">
              <div class="ms-head">
                <span class="ms-age">{{ ms.age }}岁</span>
                <span class="ms-year">({{ ms.year }}年)</span>
                <span class="ms-type">{{ ms.milestone_type }}</span>
                <span class="ms-gz">{{ ms.ganzhi_context }}</span>
              </div>
              <p class="ms-desc">{{ ms.description }}</p>
              <p v-if="ms.advice" class="ms-advice">💡 {{ ms.advice }}</p>
            </div>
          </div>
        </div>
        <!-- 月运 -->
        <div v-if="result.monthly_fortune?.length" class="section-block">
          <div class="section-title">月运参考</div>
          <div class="monthly-grid">
            <div v-for="m in result.monthly_fortune" :key="m.month"
                 :class="['monthly-item', `ml-${m.luck_level}`]">
              <div class="ml-head">
                <span class="ml-month">农{{ m.lunar_month }}月</span>
                <span class="ml-gz">{{ m.month_ganzhi || m.month_dizhi }}</span>
                <span :class="['ml-luck', `ml-luck-${m.luck_level}`]">{{ m.luck_level }}</span>
              </div>
              <p class="ml-tip">{{ m.tip }}</p>
              <div class="ml-extra">
                <span v-if="m.clash_with" class="ml-clash">冲 {{ m.clash_with }}</span>
                <span v-if="m.relation_to_rizhu" class="ml-rel">{{ m.relation_to_rizhu }}</span>
              </div>
              <div v-if="m.color_hint" class="ml-color" :style="{ background: m.color_hint }"></div>
            </div>
          </div>
        </div>
        <p v-if="!result.liunian_detail?.length && !result.monthly_fortune?.length && !result.current_fortune_summary && !result.milestones?.length" class="muted">
          暂无运势数据
        </p>
      </section>

      <section v-if="activeTab === 'ai'" class="tab-panel">
        <div class="ai-panel card">
          <div class="ai-disclaimer-bar">
            ⚠️ AI 生成内容基于命理学研究与规则推断，仅供参考，不构成任何现实决策建议。
            需要先保存案例，再执行生成。
          </div>

          <div class="ai-actions-row">
            <button class="btn-ai-generate" :disabled="!savedCaseId || aiLoading" @click="generateAiInterpretation">
              {{ aiLoading ? '生成中…' : '✦ 生成解读' }}
            </button>
            <select v-model="aiModule" class="ai-module-select" :disabled="aiLoading">
              <option v-for="option in AI_MODULE_OPTIONS" :key="option.value || 'all'" :value="option.value">
                {{ option.label }}
              </option>
            </select>
            <span v-if="aiStatus" class="ai-status-text">{{ aiStatus }}</span>
            <span v-else-if="!savedCaseId" class="ai-status-text ai-status-warn">请先保存案例</span>
          </div>

          <p v-if="aiError" class="error-msg ai-error-msg">{{ aiError }}</p>

          <div v-if="aiDraft" class="ai-result-wrap">
            <div class="ai-result-meta">
              <span v-if="aiDraft.provider">🤖 {{ aiDraft.provider }}</span>
              <span v-if="aiDraft.model">📌 {{ aiDraft.model }}</span>
              <span v-if="aiDraft.prompt_version" class="ai-schema-badge">{{ aiDraft.prompt_version }}</span>
              <span v-if="aiDraft.status">状态：{{ aiDraft.status }}</span>
              <span v-if="aiDraft.input_tokens || aiDraft.output_tokens">
                开销：{{ aiDraft.input_tokens || 0 }} in / {{ aiDraft.output_tokens || 0 }} out
              </span>
            </div>
            <div class="ai-result-box">
              <p v-for="(paragraph, index) in aiParagraphs" :key="index" class="ai-paragraph">
                {{ paragraph }}
              </p>
            </div>
          </div>
          <p v-else class="ai-empty-state">
            {{ savedCaseId ? '可选择模块后生成 AI 解读。' : '请先通过上方“保存到案例库”完成案例入库。' }}
          </p>
        </div>
      </section>

      <section v-if="activeTab === 'raw'" class="tab-panel">
        <div class="raw-panel card">
          <div class="raw-panel-head">
            <div>
              <h3 class="raw-panel-title">原始排盘数据</h3>
              <p class="raw-panel-desc">用于排障、接口对照和后续迁移核验，直接展示最近一次八字排盘返回值。</p>
            </div>
            <span class="raw-panel-meta">最近一次计算结果</span>
          </div>
          <pre class="raw-json-block">{{ rawResultJson }}</pre>
        </div>
      </section>

      <!-- 警告信息 -->
      <div v-if="result.warnings?.length" class="bazi-warnings">
        <div v-for="(w, i) in result.warnings" :key="i" class="bw-item">
          ⚠ <span class="bw-code">[{{ w.code }}]</span> {{ w.message }}
        </div>
      </div>

      <!-- 版本信息 -->
      <div class="bazi-version-footer">
        <span v-if="result.api_version">API {{ result.api_version }}</span>
        <span v-if="result.rule_version">规则 {{ result.rule_version }}</span>
        <span v-if="result.schema_version">{{ result.schema_version }}</span>
      </div>
    </template>

    <Teleport to="body">
      <div v-if="saveDialogOpen" class="bazi-modal-mask" @click.self="closeSaveDialog">
        <div class="bazi-modal">
          <h2 class="bazi-modal-title">保存案例</h2>
          <p class="bazi-modal-desc">把当前八字排盘保存到案例库，后续可继续接入 AI 解读与运营工作流。</p>
          <div class="bazi-modal-body">
            <label class="bazi-form-item">
              <span class="bazi-form-label">案例名称</span>
              <input v-model="saveCaseName" class="bazi-form-input" placeholder="请输入案例名称" />
            </label>
            <label class="bazi-form-item">
              <span class="bazi-form-label">备注</span>
              <textarea v-model="saveCaseNotes" class="bazi-form-textarea" rows="3" placeholder="可选：记录客户背景、关注问题或备注"></textarea>
            </label>
            <div class="bazi-save-summary">
              <span>出生：{{ birthDt }}</span>
              <span>城市：{{ cityName || initCity }}</span>
              <span>性别：{{ gender === 'male' ? '男' : gender === 'female' ? '女' : '不指定' }}</span>
            </div>
            <p v-if="saveCaseError" class="error-msg bazi-save-error">{{ saveCaseError }}</p>
          </div>
          <div class="bazi-modal-actions">
            <button class="btn-sec" @click="closeSaveDialog">取消</button>
            <button class="btn-primary" :disabled="saveCaseSaving" @click="saveCurrentCase">
              {{ saveCaseSaving ? '保存中…' : '确认保存' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.bazi-view { padding-bottom: var(--sp-8); }
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

/* 卡片 */
.card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: var(--sp-5); box-shadow: var(--shadow); margin-bottom: var(--sp-5); }
.card-title { font-size: var(--fs-lg); font-weight: 600; margin-bottom: var(--sp-4); }

/* 表单 */
.form-grid { display: flex; flex-direction: column; gap: var(--sp-3); margin-bottom: var(--sp-4); }
.form-row { display: flex; align-items: center; gap: var(--sp-3); flex-wrap: wrap; }
.form-row > label:first-child { width: 90px; font-size: var(--fs-md); color: var(--text-2); flex-shrink: 0; }
.form-row input[type="datetime-local"],
.form-row input[type="number"],
.form-row input:not([type]),
.form-row select { padding: 7px 10px; border: 1px solid var(--border-md); border-radius: var(--radius-sm); font-size: var(--fs-md); }
.form-row input:focus, .form-row select:focus { outline: none; border-color: var(--accent); }
.radio-opt { display: flex; align-items: center; gap: 4px; cursor: pointer; font-size: var(--fs-md); }
.check-opt { display: flex; align-items: center; gap: 6px; cursor: pointer; font-size: var(--fs-md); }
.hint { font-size: var(--fs-xs); color: var(--text-3); }

.form-actions { display: flex; align-items: center; gap: var(--sp-3); flex-wrap: wrap; }
.btn-primary { padding: 9px 22px; background: var(--accent); color: #fff; border: none; border-radius: var(--radius-sm); font-size: var(--fs-md); font-weight: 600; cursor: pointer; transition: background var(--dur-fast); }
.btn-primary:hover { background: var(--accent-dark); }
.btn-primary:disabled { opacity: .6; cursor: not-allowed; }
.btn-sec { padding: 9px 18px; background: var(--surface); color: var(--text-2); border: 1px solid var(--border-md); border-radius: var(--radius-sm); font-size: var(--fs-md); cursor: pointer; transition: border-color var(--dur-fast); }
.btn-sec:hover { border-color: var(--accent); color: var(--accent); }
.error-msg { color: var(--danger-dark); font-size: var(--fs-sm); }

/* 骨架屏 */
.skeleton-wrap { padding: var(--sp-5); }
.skel-line { height: 16px; background: var(--border); border-radius: 4px; margin-bottom: var(--sp-3); animation: shimmer 1.2s infinite; }
.skel-box { height: 80px; background: var(--border); border-radius: var(--radius-sm); margin-top: var(--sp-4); animation: shimmer 1.2s infinite; }
@keyframes shimmer { 0%,100% { opacity: 1; } 50% { opacity: .4; } }

/* 四柱表格（新版） */
.pillars-tbl-wrap { overflow-x: auto; margin-bottom: var(--sp-4); }
.pillars-tbl { width: 100%; border-collapse: collapse; font-family: var(--font-cn); text-align: center; font-size: var(--fs-md); }
.pillars-tbl th, .pillars-tbl td { padding: 8px 10px; border: 1px solid var(--border); }
.pillars-tbl thead th { background: var(--surface-2); font-size: var(--fs-sm); font-weight: 600; color: var(--text-2); }
.pillars-tbl thead th.day-col-th { background: rgba(217,119,6,.08); color: var(--accent-dark); }
.pillars-tbl td.day-col-th { background: rgba(217,119,6,.04); }
.row-lbl-th, .row-lbl { width: 40px; font-size: var(--fs-xs); color: var(--text-3); background: var(--surface-2); font-weight: 600; }
.gz-char { font-size: var(--fs-2xl); font-weight: 700; display: block; }
.gz-branch { font-size: var(--fs-xl); }
.tg-chip { font-size: var(--fs-sm); font-weight: 700; }
.tg-day { color: var(--accent-dark) !important; }
.cang-stem { font-size: var(--fs-sm); font-weight: 600; margin-right: 2px; }
.nayin-text { font-size: 11px; color: var(--text-3); }

.pillars-meta { display: flex; flex-wrap: wrap; gap: var(--sp-3); font-size: var(--fs-sm); color: var(--text-2); }
.meta-item b { color: var(--text); }

.case-actions-row {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  flex-wrap: wrap;
  margin-top: var(--sp-4);
}
.btn-case-save {
  padding: 8px 18px;
  border: 1.5px solid var(--accent);
  border-radius: var(--radius-sm);
  background: rgba(217, 119, 6, 0.08);
  color: var(--accent-dark);
  font-size: var(--fs-md);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--dur-fast);
}
.btn-case-save:hover {
  background: var(--accent);
  color: #fff;
}
.case-save-pill {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  border: 1px solid var(--border-md);
  border-radius: 999px;
  background: var(--surface-2);
  color: var(--text-2);
  font-size: var(--fs-xs);
}
.case-save-pill-success {
  border-color: rgba(21, 128, 61, 0.3);
  background: rgba(220, 252, 231, 0.9);
  color: #166534;
}
.case-save-msg {
  font-size: var(--fs-xs);
  color: #166534;
}

.ai-panel {
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
}
.ai-disclaimer-bar {
  padding: 12px 14px;
  border: 1px solid rgba(217, 119, 6, 0.18);
  border-radius: var(--radius-sm);
  background: rgba(254, 243, 199, 0.7);
  color: #92400e;
  font-size: var(--fs-sm);
  line-height: 1.7;
}
.ai-actions-row {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  flex-wrap: wrap;
}
.btn-ai-generate {
  padding: 9px 18px;
  border: none;
  border-radius: var(--radius-sm);
  background: linear-gradient(135deg, #7c3aed, #a855f7);
  color: #fff;
  font-size: var(--fs-md);
  font-weight: 600;
  cursor: pointer;
}
.btn-ai-generate:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.ai-module-select {
  min-width: 180px;
  padding: 9px 12px;
  border: 1px solid var(--border-md);
  border-radius: var(--radius-sm);
  font-size: var(--fs-sm);
  background: var(--surface);
}
.ai-status-text {
  font-size: var(--fs-sm);
  color: var(--text-2);
}
.ai-status-warn { color: #b45309; }
.ai-error-msg { margin: 0; }
.ai-result-wrap {
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
}
.ai-result-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  font-size: var(--fs-xs);
  color: var(--text-3);
}
.ai-result-meta span {
  padding: 4px 8px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--surface-2);
}
.ai-schema-badge {
  color: #6d28d9;
  border-color: rgba(109, 40, 217, 0.18) !important;
  background: rgba(243, 232, 255, 0.9) !important;
}
.ai-result-box {
  padding: 16px 18px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: linear-gradient(180deg, rgba(250, 245, 255, 0.75), rgba(255, 255, 255, 0.95));
}
.ai-paragraph {
  margin: 0 0 12px;
  line-height: 1.9;
  color: var(--text);
  white-space: pre-wrap;
}
.ai-paragraph:last-child { margin-bottom: 0; }
.ai-empty-state {
  margin: 0;
  color: var(--text-3);
  font-size: var(--fs-sm);
}

.raw-panel {
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
}
.raw-panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--sp-3);
  flex-wrap: wrap;
}
.raw-panel-title {
  margin: 0 0 6px;
  font-size: var(--fs-lg);
  font-weight: 700;
  color: var(--text);
}
.raw-panel-desc {
  margin: 0;
  font-size: var(--fs-sm);
  color: var(--text-3);
  line-height: 1.7;
}
.raw-panel-meta {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  border: 1px solid var(--border-md);
  border-radius: 999px;
  background: var(--surface-2);
  color: var(--text-2);
  font-size: var(--fs-xs);
}
.raw-json-block {
  margin: 0;
  padding: 16px 18px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: #0f172a;
  color: #e2e8f0;
  font-size: 12px;
  line-height: 1.7;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-word;
}

.bazi-modal-mask {
  position: fixed;
  inset: 0;
  z-index: 60;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: rgba(15, 23, 42, 0.45);
}
.bazi-modal {
  width: min(100%, 520px);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg, 18px);
  box-shadow: 0 24px 60px rgba(15, 23, 42, 0.24);
  padding: 22px;
}
.bazi-modal-title {
  margin: 0 0 8px;
  font-size: var(--fs-xl);
  font-weight: 700;
  color: var(--text);
}
.bazi-modal-desc {
  margin: 0 0 var(--sp-4);
  font-size: var(--fs-sm);
  color: var(--text-3);
  line-height: 1.7;
}
.bazi-modal-body {
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
}
.bazi-form-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.bazi-form-label {
  font-size: var(--fs-sm);
  color: var(--text-2);
  font-weight: 600;
}
.bazi-form-input,
.bazi-form-textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-md);
  border-radius: var(--radius-sm);
  font-size: var(--fs-md);
  background: var(--surface);
}
.bazi-form-input:focus,
.bazi-form-textarea:focus {
  outline: none;
  border-color: var(--accent);
}
.bazi-form-textarea {
  resize: vertical;
  min-height: 84px;
}
.bazi-save-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  font-size: var(--fs-xs);
  color: var(--text-3);
}
.bazi-save-summary span {
  padding: 4px 8px;
  border-radius: 999px;
  background: var(--surface-2);
  border: 1px solid var(--border);
}
.bazi-save-error { margin: 0; }
.bazi-modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--sp-3);
  margin-top: var(--sp-4);
}

/* 推荐改名 */
.suggest-name-row { margin-top: var(--sp-4); display: flex; align-items: center; gap: var(--sp-3); flex-wrap: wrap; }
.btn-suggest-name { padding: 8px 18px; background: var(--surface); color: var(--accent); border: 1.5px solid var(--accent); border-radius: var(--radius-sm); font-size: var(--fs-md); font-weight: 600; cursor: pointer; transition: all var(--dur-fast); }
.btn-suggest-name:hover { background: var(--accent); color: #fff; }
.btn-zeri-link { padding: 8px 16px; background: var(--surface); color: #d97706; border: 1.5px solid #fbbf24; border-radius: var(--radius-sm); font-size: var(--fs-md); font-weight: 600; cursor: pointer; transition: all var(--dur-fast); }
.btn-zeri-link:hover { background: #fef3c7; }

/* Tabs */
.tabs { display: flex; gap: var(--sp-2); margin-bottom: var(--sp-4); border-bottom: 2px solid var(--border); }
.tab-btn { padding: 8px 20px; border: none; background: none; cursor: pointer; font-size: var(--fs-md); color: var(--text-2); border-bottom: 2px solid transparent; margin-bottom: -2px; transition: color var(--dur-fast), border-color var(--dur-fast); }
.tab-btn.active { color: var(--accent); border-bottom-color: var(--accent); font-weight: 600; }
.tab-btn:hover { color: var(--text); }

/* 综合概览 */
.overview-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: var(--sp-4); margin-bottom: var(--sp-5); }
.ov-card { background: var(--surface-2); border-radius: var(--radius-sm); border: 1px solid var(--border); padding: var(--sp-4); }
.ov-title { font-size: var(--fs-xs); color: var(--text-3); margin-bottom: var(--sp-2); font-weight: 600; text-transform: uppercase; }
.ov-body { font-size: var(--fs-md); }
.ov-summary { font-size: var(--fs-xs); color: var(--text-3); margin-top: 4px; }

.tag-row { display: flex; flex-wrap: wrap; gap: 4px; }
.tag { padding: 2px 8px; border-radius: 12px; font-size: var(--fs-xs); font-weight: 600; }
.tag-favor  { background: #dcfce7; color: #15803d; }
.tag-avoid  { background: #fee2e2; color: #dc2626; }
.tag-neutral{ background: #f0f9ff; color: #0369a1; }

/* ── 大运时间轴 ── */
.dy-header {
  display: flex; align-items: center; gap: var(--sp-3); flex-wrap: wrap;
  font-size: var(--fs-sm); color: var(--text-2); margin-bottom: var(--sp-5);
}
.dy-dir {
  padding: 2px 10px; background: var(--surface-2);
  border: 1px solid var(--border-md); border-radius: 20px;
}
.dy-cur-lbl { margin-left: auto; color: var(--accent); font-weight: 600; }
.dy-cur-age { font-weight: 400; color: var(--text-2); }

.dy-timeline-wrap { overflow-x: auto; padding-bottom: var(--sp-3); }
.dy-track {
  display: flex; align-items: flex-start;
  min-width: max-content; padding: 24px 16px 8px;
}

.dy-step {
  display: flex; flex-direction: column; align-items: center;
  width: 96px; cursor: pointer; position: relative;
}
.dy-step:hover .dy-card { border-color: var(--accent); }

/* 节点行（线 + 点） */
.dy-dot-row {
  display: flex; align-items: center; width: 100%;
  height: 20px; margin-bottom: 10px;
}
.dy-line-l, .dy-line-r { flex: 1; height: 2px; background: var(--border); }
.dy-dot {
  width: 14px; height: 14px; border-radius: 50%;
  background: var(--border-md);
  border: 2px solid var(--surface);
  box-shadow: 0 0 0 2px var(--border-md);
  flex-shrink: 0; position: relative; z-index: 1;
  transition: background .2s, box-shadow .2s;
}
.dy-dot-ring {
  position: absolute; top: -5px; left: -5px;
  width: 20px; height: 20px; border-radius: 50%;
  border: 2px solid var(--accent);
  animation: dy-ring-pulse 2s ease-in-out infinite;
}
@keyframes dy-ring-pulse {
  0%, 100% { transform: scale(1);   opacity: .9; }
  50%       { transform: scale(1.4); opacity: 0; }
}

.dy-cur  .dy-dot { background: var(--accent); box-shadow: 0 0 0 2px var(--surface), 0 0 0 4px var(--accent); }
.dy-past .dy-dot { background: var(--text-3); box-shadow: 0 0 0 2px var(--text-3); }

/* 卡片 */
.dy-card {
  width: 80px; padding: 6px 4px; text-align: center;
  border-radius: var(--radius-sm);
  border: 1.5px solid var(--border);
  background: var(--surface);
  transition: border-color .15s, box-shadow .15s;
  user-select: none;
}
.dy-cur .dy-card {
  border-color: var(--accent);
  background: linear-gradient(150deg, var(--surface) 0%, var(--accent-soft) 100%);
  box-shadow: 0 2px 8px var(--accent-soft);
}
.dy-past .dy-card { opacity: .55; }
.dy-sel .dy-card  { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-soft); }

.dy-gz { font-size: 22px; font-weight: 700; font-family: var(--font-cn); letter-spacing: 2px; }
.dy-tg-chip {
  font-size: 10px; padding: 1px 6px;
  border-radius: 10px; border: 1px solid transparent;
  display: inline-block; margin: 3px auto 0;
}
.dy-age-range { font-size: 11px; color: var(--text-2); margin-top: 4px; }
.dy-yr        { font-size: 10px; color: var(--text-3); margin-top: 1px; }

/* 详情面板 */
.dy-detail-card {
  margin-top: var(--sp-5);
  padding: var(--sp-4) var(--sp-5);
  background: var(--surface);
  border: 1.5px solid var(--accent);
  border-radius: var(--radius-sm);
  box-shadow: 0 2px 12px var(--accent-soft);
}
.dy-detail-header {
  display: flex; align-items: center; gap: var(--sp-3); flex-wrap: wrap;
  margin-bottom: var(--sp-3);
}
.dy-detail-gz    { font-size: var(--fs-2xl); font-weight: 700; font-family: var(--font-cn); }
.dy-detail-period{ font-size: var(--fs-sm); color: var(--text-2); }
.dy-detail-close {
  margin-left: auto; background: none; border: none;
  font-size: 22px; cursor: pointer; color: var(--text-3); line-height: 1;
}
.dy-detail-close:hover { color: var(--text); }
.dy-detail-narrative { font-size: var(--fs-md); color: var(--text); line-height: 1.8; margin-bottom: var(--sp-3); }

/* 展开过渡 */
.dy-expand-enter-active, .dy-expand-leave-active  { transition: opacity .2s, transform .2s; }
.dy-expand-enter-from,   .dy-expand-leave-to      { opacity: 0; transform: translateY(-6px); }

/* 大运提示标签（复用于详情面板） */
.dayun-hints { display: flex; gap: var(--sp-2); flex-wrap: wrap; }
.dh-tag  { padding: 3px 10px; border-radius: 12px; font-size: var(--fs-xs); font-weight: 600; }
.dh-wealth { background: #fef9c3; color: #a16207; }
.dh-health { background: #dcfce7; color: #15803d; }
.dh-love   { background: #fce7f3; color: #9d174d; }

/* 五行 */
.wuxing-list { display: flex; flex-direction: column; gap: var(--sp-3); }
.wx-row { display: flex; align-items: center; gap: var(--sp-3); }
.wx-lbl { width: 28px; font-size: var(--fs-md); font-weight: 700; text-align: center; }
.wx-bar-wrap { flex: 1; height: 18px; background: var(--surface-2); border-radius: 9px; overflow: hidden; }
.wx-bar { height: 100%; border-radius: 9px; transition: width .5s ease; }
.wx-val { width: 100px; font-size: var(--fs-sm); color: var(--text-2); text-align: right; }

.muted { color: var(--text-3); font-size: var(--fs-sm); }

/* 命局总评 */
.bazi-summary-block {
  background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
  border: 1px solid #fbbf24;
  border-left: 4px solid #d97706;
  border-radius: var(--radius-sm);
  padding: var(--sp-4) var(--sp-5);
  margin-bottom: var(--sp-5);
}
.summary-label { font-size: var(--fs-xs); color: #92400e; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: var(--sp-2); }
.bazi-summary-text { font-size: var(--fs-md); color: var(--text); line-height: 1.8; white-space: pre-line; }

/* 当前运势摘要卡片 */
.cur-fortune-card {
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: var(--sp-4);
  margin-bottom: var(--sp-5);
}
.cf-row { display: flex; gap: var(--sp-6); margin-bottom: var(--sp-3); }
.cf-item { text-align: center; }
.cf-lbl { font-size: var(--fs-xs); color: var(--text-3); margin-bottom: 2px; }
.cf-val { font-size: var(--fs-xl); font-weight: 700; font-family: var(--font-cn); }
.cf-sub { font-size: var(--fs-xs); color: var(--text-3); }
.cf-actions { margin-bottom: var(--sp-3); }
.cf-action-list { font-size: var(--fs-sm); color: var(--text); padding-left: 1.2em; margin: 4px 0; }
.cf-action-list li { margin-bottom: 3px; }
.cf-domains { display: flex; flex-wrap: wrap; gap: var(--sp-2); }
.cf-domain-item { padding: 4px 10px; background: var(--surface); border: 1px solid var(--border-md); border-radius: var(--radius-sm); font-size: var(--fs-xs); }
.cf-domain-key { color: var(--text-3); margin-right: 4px; }
.cf-domain-val { color: var(--text); }

/* 格局等级标签 */
.geju-level-badge { display: inline-block; font-size: 10px; padding: 1px 6px; border-radius: 10px; background: rgba(217,119,6,.12); color: #92400e; font-weight: 600; margin-left: 6px; vertical-align: middle; }

/* 开运数据 */
.lucky-row { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; flex-wrap: wrap; }
.lucky-lbl { font-size: var(--fs-xs); color: var(--text-3); width: 60px; flex-shrink: 0; }
.lucky-tag { font-size: var(--fs-xs); padding: 2px 8px; background: var(--surface); border: 1px solid var(--border-md); border-radius: 10px; }

/* 人生弧线（升级版）*/
.life-arc-block { background: var(--surface-2); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: var(--sp-5); margin-bottom: var(--sp-5); }
.life-arc-header { display: flex; align-items: center; gap: var(--sp-3); margin-bottom: var(--sp-3); }
.life-arc-title { font-size: var(--fs-md); font-weight: 600; color: var(--text); }
.life-arc-tier { font-size: var(--fs-xs); padding: 2px 9px; border-radius: 10px; background: rgba(217,119,6,.12); color: #92400e; font-weight: 700; }
.life-motto { font-size: var(--fs-md); color: #78716c; font-style: italic; border-left: 3px solid #d97706; padding-left: var(--sp-3); margin: 0 0 var(--sp-4); font-family: var(--font-cn); }
.life-arc-periods { display: grid; grid-template-columns: repeat(3,1fr); gap: var(--sp-3); margin-bottom: var(--sp-4); }
.lp-item { }
.lp-label { font-size: var(--fs-xs); color: var(--accent); font-weight: 700; display: block; margin-bottom: 3px; }
.lp-text { font-size: var(--fs-sm); color: var(--text); line-height: 1.6; margin: 0; }
.life-arc-body { font-size: var(--fs-md); color: var(--text); line-height: 1.7; margin-bottom: var(--sp-4); }
.life-arc-peaks { display: flex; flex-direction: column; gap: var(--sp-2); }
.peak-item { display: flex; align-items: center; flex-wrap: wrap; gap: 6px; }
.peak-lbl { font-size: var(--fs-xs); font-weight: 700; width: 64px; flex-shrink: 0; }
.peak-good { color: #15803d; }
.peak-warn { color: #dc2626; }
.peak-tag { font-size: var(--fs-xs); padding: 2px 8px; border-radius: 10px; }
.peak-tag-good { background: #dcfce7; color: #15803d; }
.peak-tag-warn { background: #fee2e2; color: #dc2626; }

/* 性格分析 */
.personality-block { background: var(--surface-2); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: var(--sp-4); margin-bottom: var(--sp-5); }
.personality-trait { font-size: var(--fs-md); color: var(--text); margin: var(--sp-2) 0 var(--sp-3); }
.personality-cols { display: grid; grid-template-columns: 1fr 1fr; gap: var(--sp-4); margin-bottom: var(--sp-3); }
.pers-col { }
.pers-lbl { font-size: var(--fs-xs); font-weight: 700; margin-bottom: 4px; }
.pers-good { color: #15803d; }
.pers-warn { color: #dc2626; }
.pers-list { font-size: var(--fs-sm); color: var(--text); padding-left: 1.2em; margin: 0; }
.pers-list li { margin-bottom: 3px; }
.pers-advice { font-size: var(--fs-sm); color: var(--accent-dark); background: rgba(217,119,6,.08); border-radius: var(--radius-sm); padding: var(--sp-2) var(--sp-3); margin: 0; }

/* 神煞 */
.shensha-section { margin-bottom: var(--sp-5); }
.shensha-list { display: flex; flex-direction: column; gap: 6px; }
.shensha-item { display: flex; align-items: baseline; gap: var(--sp-2); padding: 6px 10px; border-radius: var(--radius-sm); font-size: var(--fs-sm); }
.sh-good { background: rgba(21,128,61,.06); border-left: 3px solid #15803d; }
.sh-bad  { background: rgba(220,38,38,.04); border-left: 3px solid #dc2626; }
.sh-name { font-weight: 700; min-width: 50px; }
.sh-pillar { color: var(--text-3); font-size: var(--fs-xs); min-width: 30px; }
.sh-meaning { color: var(--text-2); flex: 1; }

/* 大运升级 */
.dayun-item { text-align: center; padding: var(--sp-3) var(--sp-4); background: var(--surface-2); border-radius: var(--radius-sm); border: 1px solid var(--border); min-width: 90px; max-width: 160px; flex: 1; }
.dayun-item.cur { border-color: var(--accent); background: rgba(217,119,6,.06); }
.dayun-tg { font-size: var(--fs-xs); color: var(--text-3); margin-top: 2px; }
.dayun-narrative { font-size: 10px; color: var(--text-2); line-height: 1.5; margin-top: 4px; text-align: left; }
.dayun-hints { display: flex; flex-direction: column; gap: 2px; margin-top: 4px; }
.dh-tag { font-size: 9px; padding: 1px 4px; border-radius: 2px; text-align: left; }
.dh-wealth { background: rgba(21,128,61,.1); color: #15803d; }
.dh-health { background: rgba(37,99,235,.1); color: #1d4ed8; }
.dh-love { background: rgba(217,119,6,.1); color: #92400e; }

/* 五行均衡 */
.wx-balance { margin-top: var(--sp-4); padding: var(--sp-4); background: var(--surface-2); border-radius: var(--radius-sm); border: 1px solid var(--border); }
.wx-balance-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--sp-2); }
.wx-bal-lbl { font-size: var(--fs-sm); color: var(--text-2); }
.wx-bal-val { font-size: var(--fs-xl); font-weight: 700; }
.wx-imbalance { display: flex; gap: var(--sp-4); margin-bottom: var(--sp-2); font-size: var(--fs-sm); }
.wx-weak { color: #dc2626; }
.wx-strong { color: #d97706; }
.wx-advice { font-size: var(--fs-sm); color: var(--text-2); margin: 0; }

/* 四维分析 */
.analysis-card { background: var(--surface-2); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: var(--sp-5); margin-bottom: var(--sp-4); }
.ac-header { display: flex; align-items: center; gap: var(--sp-2); margin-bottom: var(--sp-3); flex-wrap: wrap; }
.ac-icon { font-size: var(--fs-lg); }
.ac-title { font-size: var(--fs-lg); font-weight: 700; flex: 1; }
.ac-score { font-size: var(--fs-2xl); font-weight: 800; }
.ac-score small { font-size: var(--fs-xs); font-weight: 400; color: var(--text-3); }
.ac-tier { font-size: var(--fs-xs); padding: 2px 8px; border-radius: 10px; background: rgba(217,119,6,.10); color: #92400e; font-weight: 600; }
.tier-warn { background: rgba(220,38,38,.1); color: #dc2626; }
.ac-range { font-size: var(--fs-sm); color: var(--text-2); margin-bottom: var(--sp-3); }
.ac-tags { display: flex; align-items: center; flex-wrap: wrap; gap: 5px; margin-bottom: var(--sp-2); }
.ac-tag-lbl { font-size: var(--fs-xs); color: var(--text-3); flex-shrink: 0; }
.ac-tag { font-size: var(--fs-xs); padding: 2px 8px; background: var(--surface); border: 1px solid var(--border-md); border-radius: 10px; }
.ac-tag-warn { background: #fee2e2; border-color: #fca5a5; color: #dc2626; }
.ac-row { display: flex; flex-wrap: wrap; gap: var(--sp-4); font-size: var(--fs-sm); color: var(--text-2); margin-bottom: var(--sp-2); }
.ac-text { font-size: var(--fs-md); color: var(--text); line-height: 1.7; margin-bottom: var(--sp-2); }
.ac-sub { font-size: var(--fs-sm); color: var(--text-2); margin-bottom: 3px; }
.ac-interp { font-size: var(--fs-sm); color: var(--text-3); line-height: 1.6; border-top: 1px solid var(--border); padding-top: var(--sp-2); margin-top: var(--sp-2); }
.ac-health-tips { display: flex; flex-direction: column; gap: 4px; margin: var(--sp-2) 0; }
.ht-row { display: flex; align-items: center; gap: 5px; flex-wrap: wrap; }
.ht-lbl { font-size: var(--fs-xs); color: var(--text-3); width: 32px; flex-shrink: 0; }
.ht-item { font-size: var(--fs-xs); padding: 2px 7px; background: var(--surface); border: 1px solid var(--border-md); border-radius: 10px; }

/* 流年四维 */
.liunian-detail-list { display: flex; flex-direction: column; gap: var(--sp-3); margin-bottom: var(--sp-5); }
.ld-item { padding: var(--sp-4); background: var(--surface-2); border: 1px solid var(--border); border-radius: var(--radius-sm); }
.ld-head { display: flex; align-items: center; gap: var(--sp-3); margin-bottom: var(--sp-2); }
.ld-gz { font-size: var(--fs-lg); font-weight: 700; font-family: var(--font-cn); }
.ld-year { font-size: var(--fs-sm); color: var(--text-2); }
.ld-score { font-size: var(--fs-xl); font-weight: 700; margin-left: auto; }
.ld-tg { font-size: var(--fs-xs); color: var(--text-3); padding: 1px 6px; background: var(--surface); border: 1px solid var(--border-md); border-radius: 10px; }
.ld-domains { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 6px; }
.ld-domain { display: flex; gap: 4px; font-size: var(--fs-xs); padding: 3px 8px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-sm); }
.ld-dk { color: var(--text-3); }
.ld-dv { color: var(--text); }
.ld-action { font-size: var(--fs-sm); color: var(--accent-dark); background: rgba(217,119,6,.08); border-radius: var(--radius-sm); padding: 4px 10px; margin: 0; }
.ld-taisui { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 4px; }
.ld-ts-tag { font-size: var(--fs-xs); padding: 1px 6px; background: #fef3c7; color: #b45309; border-radius: 4px; }
.ld-notable { display: flex; align-items: center; gap: var(--sp-2); flex-wrap: wrap; margin-top: 4px; }
.ld-notable-lbl { font-size: var(--fs-xs); color: var(--text-3); }
.ld-notable-m { font-size: var(--fs-xs); padding: 1px 6px; background: var(--accent-soft); color: var(--accent); border-radius: 4px; font-weight: 600; }

/* 当前运势概况 */
.cfs-info { display: flex; flex-wrap: wrap; gap: var(--sp-3); margin-bottom: var(--sp-3); font-size: var(--fs-sm); color: var(--text-2); }
.cfs-info b { color: var(--text); font-weight: 700; }
.cfs-domains { display: flex; flex-wrap: wrap; gap: var(--sp-2); margin-bottom: var(--sp-3); }
.cfs-dom { display: flex; gap: 4px; font-size: var(--fs-sm); padding: 3px 8px; background: var(--surface-2); border: 1px solid var(--border); border-radius: var(--radius-sm); }
.cfs-dk { color: var(--accent); font-weight: 600; }
.cfs-dv { color: var(--text); }
.cfs-actions { padding: var(--sp-3); background: rgba(217,119,6,.05); border-radius: var(--radius-sm); }
.cfs-actions-title { font-size: var(--fs-sm); font-weight: 600; color: var(--accent-dark); margin-bottom: var(--sp-2); }
.cfs-action { font-size: var(--fs-sm); color: var(--text); margin-bottom: 2px; }

/* 人生里程碑 */
.milestones-list { display: flex; flex-direction: column; gap: var(--sp-3); }
.ms-item { padding: var(--sp-3); background: var(--surface-2); border-radius: var(--radius-sm); border-left: 3px solid var(--border-md); }
.ms-item.ms-高 { border-left-color: #dc2626; }
.ms-item.ms-中 { border-left-color: #f59e0b; }
.ms-item.ms-低 { border-left-color: #22c55e; }
.ms-head { display: flex; flex-wrap: wrap; align-items: center; gap: var(--sp-2); margin-bottom: var(--sp-2); }
.ms-age { font-weight: 700; font-size: var(--fs-md); color: var(--accent); }
.ms-year { font-size: var(--fs-sm); color: var(--text-3); }
.ms-type { font-size: var(--fs-xs); padding: 1px 8px; border-radius: 10px; background: var(--accent-soft); color: var(--accent); font-weight: 600; }
.ms-gz { font-size: var(--fs-xs); color: var(--text-3); margin-left: auto; }
.ms-desc { font-size: var(--fs-sm); color: var(--text); line-height: 1.5; margin: 0 0 4px; }
.ms-advice { font-size: var(--fs-sm); color: var(--accent-dark); margin: 0; }

/* 月运 */
.monthly-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); gap: var(--sp-2); }
.monthly-item { padding: var(--sp-3); border-radius: var(--radius-sm); border: 1px solid var(--border); background: var(--surface-2); }
.ml-head { display: flex; align-items: center; gap: 4px; margin-bottom: 4px; }
.ml-month { font-size: var(--fs-sm); font-weight: 700; }
.ml-gz { font-size: 10px; color: var(--text-3); flex: 1; }
.ml-luck { font-size: 10px; padding: 0 4px; border-radius: 3px; font-weight: 700; }
.ml-luck-吉 { background: #dcfce7; color: #15803d; }
.ml-luck-凶 { background: #fee2e2; color: #dc2626; }
.ml-luck-平 { background: var(--surface); color: var(--text-3); border: 1px solid var(--border-md); }
.ml-tip { font-size: 10px; color: var(--text-2); line-height: 1.4; margin: 0; }
.ml-color { width: 100%; height: 3px; border-radius: 2px; margin-top: 4px; opacity: 0.6; }

.section-block { margin-bottom: var(--sp-6); }
.section-title { font-size: var(--fs-lg); font-weight: 600; margin-bottom: var(--sp-4); color: var(--text); }

/* 免责声明 */
.ac-disclaimer { font-size: var(--fs-xs); color: var(--text-3); font-style: italic; background: rgba(0,0,0,.03); border-radius: var(--radius-sm); padding: 4px 10px; margin-top: var(--sp-2); }
.ac-sub-warn { color: #dc2626; }

/* 大运财运趋势 */
.ac-dayun-fc { margin: var(--sp-2) 0; }
.ac-df-item { display: inline-flex; gap: 4px; font-size: var(--fs-xs); padding: 2px 8px; background: var(--surface); border: 1px solid var(--border-md); border-radius: var(--radius-sm); margin: 2px 4px 2px 0; }
.ac-df-gz { font-weight: 600; color: var(--text); }
.ac-df-trend { color: var(--text-2); }

/* 性格扩展 */
.pers-extra { margin-top: var(--sp-2); display: flex; flex-direction: column; gap: 2px; }
.pers-sub { font-size: var(--fs-sm); color: var(--text-2); margin: 0; }

/* 格局增强 */
.geju-broken-badge { display: inline-block; font-size: 10px; padding: 1px 6px; border-radius: 10px; background: rgba(220,38,38,.12); color: #dc2626; font-weight: 600; margin-left: 4px; }
.geju-conf { font-size: var(--fs-xs); color: var(--text-3); margin-left: 6px; }
.ov-classic-ref { font-size: var(--fs-xs); color: var(--text-3); font-style: italic; margin-top: 4px; }

/* 开运忌讳 */
.lucky-avoid { opacity: .85; }
.lucky-tag-avoid { background: #fee2e2; border-color: #fca5a5; color: #dc2626; }

/* 十二宫 */
.ov-card-wide { grid-column: 1 / -1; }
.twelve-palaces { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 6px; margin: var(--sp-3) 0; }
.tp-item { display: flex; align-items: center; gap: 4px; padding: 4px 8px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-sm); font-size: var(--fs-xs); }
.tp-name { font-weight: 600; color: var(--text); }
.tp-dizhi { color: var(--accent); font-weight: 600; }
.tp-ss { color: var(--text-3); }
.tp-tg { color: var(--text-2); }
.tp-str { font-size: 10px; padding: 0 4px; border-radius: 3px; }
.tp-str-旺 { background: #dcfce7; color: #15803d; }
.tp-str-相 { background: #e0f2fe; color: #0369a1; }
.tp-str-休 { background: #f5f5f4; color: #78716c; }
.tp-str-囚 { background: #fef3c7; color: #b45309; }
.tp-str-死 { background: #fee2e2; color: #dc2626; }
.tp-note { color: var(--text-3); flex: 1; text-align: right; }

/* 六亲人际 */
.ac-liuqin { display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); gap: 6px; margin-bottom: var(--sp-3); }
.lq-item { display: flex; gap: 4px; font-size: var(--fs-sm); padding: 3px 8px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-sm); }
.lq-key { color: var(--text-3); font-weight: 600; }
.lq-val { color: var(--text); }
.ac-tag-noble { background: #fef3c7; border-color: #fbbf24; color: #92400e; }

/* 饰品 */
.jewelry-items { display: grid; grid-template-columns: 1fr 1fr; gap: var(--sp-3); margin-bottom: var(--sp-3); }
.ji-card { padding: var(--sp-3); background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-sm); }
.ji-primary { border-color: var(--accent); border-width: 1.5px; }
.ji-label { font-size: var(--fs-xs); color: var(--text-3); font-weight: 600; margin-bottom: 4px; }
.ji-detail { font-size: var(--fs-md); font-weight: 600; margin-bottom: 4px; }
.ji-gem { color: var(--accent); margin-left: 6px; }
.ji-meta { font-size: var(--fs-xs); color: var(--text-2); display: flex; gap: var(--sp-3); }

/* 月运扩展 */
.ml-extra { display: flex; gap: 4px; flex-wrap: wrap; margin-top: 2px; }
.ml-clash { font-size: 9px; padding: 0 4px; border-radius: 3px; background: #fee2e2; color: #dc2626; }
.ml-rel { font-size: 9px; padding: 0 4px; border-radius: 3px; background: #f0f9ff; color: #0369a1; }

/* 流年冲克 */
.ld-clash-pillars { display: flex; align-items: center; gap: var(--sp-2); flex-wrap: wrap; margin-top: 4px; }
.ld-flow-wx { font-size: var(--fs-xs); color: var(--text-3); margin-top: 4px; display: inline-block; }

/* 警告 + 版本 */
.bazi-warnings { margin-top: var(--sp-4); }
.bw-item { font-size: var(--fs-sm); color: #b45309; background: #fef3c7; border: 1px solid #fbbf24; border-radius: var(--radius-sm); padding: 6px 12px; margin-bottom: 4px; }
.bw-code { font-weight: 600; font-size: var(--fs-xs); }
.bazi-version-footer { margin-top: var(--sp-4); font-size: var(--fs-xs); color: var(--text-3); display: flex; gap: var(--sp-3); justify-content: flex-end; opacity: .6; }

@media (max-width: 600px) {
  .pillars-tbl th { font-size: 11px; padding: 6px 6px; }
  .pillars-tbl td { padding: 6px 6px; }
  .gz-char { font-size: var(--fs-xl); }
  .overview-grid { grid-template-columns: 1fr; }
  .life-arc-periods { grid-template-columns: 1fr; }
  .personality-cols { grid-template-columns: 1fr; }
  .wx-chart-row { flex-direction: column; }
  .wx-radar-wrap { width: 100%; max-width: 220px; margin: 0 auto; }
}

/* ── 打印 / PDF 样式 ── */
@media print {
  .app-nav, .form-card-wrap, .tabs, .suggest-name-row, .no-print { display: none !important; }
  .wrap { padding: 0 !important; }
  .tab-panel { display: block !important; page-break-inside: avoid; }
  .pillars-tbl-wrap { overflow: visible; }
  .dayun-timeline-wrap { overflow: visible; }
  .dy-track { flex-wrap: wrap; min-width: 0; }
  h1, h2, h3 { page-break-after: avoid; }
  .card, .ov-card { box-shadow: none; border: 1px solid #ccc; }
  .bazi-summary-block { background: #fffbeb !important; }
  body { font-size: 11pt; }
}

/* 五行雷达图 */
.wx-chart-row { display: flex; gap: var(--sp-6); align-items: flex-start; margin-bottom: var(--sp-4); flex-wrap: wrap; }
.wx-radar-wrap { flex: 0 0 200px; }
.wx-radar-svg { width: 200px; height: 200px; }
.radar-label { font-size: 12px; font-family: var(--font-cn); font-weight: 700; }
.wuxing-list { flex: 1; min-width: 200px; display: flex; flex-direction: column; gap: var(--sp-3); }
</style>
