<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { recommendZeri, getZeriPurposes } from '@/api/zeri'
import type { ZeriDayItem, ZeriMonthResult } from '@/api/zeri'

const route = useRoute()

// ── 常量 ─────────────────────────────────────────────────────
const BRANCHES = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
const BRANCH_ZODIAC: Record<string, string> = {
  '子':'鼠','丑':'牛','寅':'虎','卯':'兔','辰':'龙','巳':'蛇',
  '午':'马','未':'羊','申':'猴','酉':'鸡','戌':'狗','亥':'猪',
}
const WX_JU_LIST = ['水二局','木三局','金四局','土五局','火六局']

// ── 本命年支辅助计算 ───────────────────────────────────────────
const birthYearInput = ref<number | ''>(new Date().getFullYear() - 30)
function calcNatalBranch() {
  const y = Number(birthYearInput.value)
  if (!y || y < 1900 || y > 2100) return
  natalYearBranch.value = BRANCHES[((y - 4) % 12 + 12) % 12]
}
const DEFAULT_PURPOSES: Record<string, string> = {
  general:  '通用', marriage: '婚嫁', business: '开业', travel: '出行',
  medical:  '就医', move:     '搬家', career:   '求职',
}
const LEVEL_BG: Record<string, string> = {
  daji:  '#dcfce7', ji:    '#dbeafe', zhong: '#f3f4f6', xiong: '#fee2e2',
}
const LEVEL_FG: Record<string, string> = {
  daji:  '#15803d', ji:    '#1d4ed8', zhong: '#6b7280', xiong: '#dc2626',
}
const LEVEL_BORDER: Record<string, string> = {
  daji:  '#16a34a', ji:    '#2563eb', zhong: '#d1d5db', xiong: '#ef4444',
}
const WEEK_HEADERS = ['一','二','三','四','五','六','日']

// ── 表单状态 ──────────────────────────────────────────────────
const now = new Date()
const formYear  = ref(now.getFullYear())
const formMonth = ref(now.getMonth() + 1)
const lifePalaceBranch   = ref('')
const wuxingJuName       = ref('水二局')
const natalYearBranch    = ref('')
const purpose            = ref('general')

const loading  = ref(false)
const error    = ref('')
const result   = ref<ZeriMonthResult | null>(null)
const selectedDay   = ref<ZeriDayItem | null>(null)
const purposes = ref<Record<string, string>>(DEFAULT_PURPOSES)
const fromZiwei = ref(false)   // 是否从紫微页自动带入数据

// ── 从 URL query 预填（从紫微/八字页跳转过来）──────────────────
onMounted(async () => {
  const q = route.query
  if (q.life_palace_branch)   lifePalaceBranch.value  = String(q.life_palace_branch)
  if (q.wuxing_ju_name)       wuxingJuName.value       = String(q.wuxing_ju_name)
  if (q.natal_year_branch)    natalYearBranch.value    = String(q.natal_year_branch)
  if (q.birth_year)           birthYearInput.value     = Number(q.birth_year)
  if (q.purpose)              purpose.value            = String(q.purpose)
  fromZiwei.value = !!q.life_palace_branch
  // 加载用途列表
  try { purposes.value = await getZeriPurposes() } catch { /* ignore, use defaults */ }
  // 如果有命宫参数则自动查询
  if (lifePalaceBranch.value) await doRecommend()
})

// ── 日历网格计算（Mon=col0 … Sun=col6）────────────────────────
const calendarGrid = computed((): (ZeriDayItem | null)[][] => {
  if (!result.value?.days.length) return []
  const firstDate = new Date(result.value.days[0].date + 'T00:00:00')
  const firstCol  = (firstDate.getDay() + 6) % 7  // Mon=0
  const rows: (ZeriDayItem | null)[][] = []
  let row: (ZeriDayItem | null)[] = Array(firstCol).fill(null)
  for (const d of result.value.days) {
    row.push(d)
    if (row.length === 7) { rows.push(row); row = [] }
  }
  if (row.length) {
    while (row.length < 7) row.push(null)
    rows.push(row)
  }
  return rows
})

// ── 推荐日期 Set（用于高亮标记）─────────────────────────────────
const topDaySet = computed(() => new Set(result.value?.top_days ?? []))

// ── 格式化：月份标题 ────────────────────────────────────────────
const monthTitle = computed(() =>
  result.value
    ? `${result.value.year}年${result.value.month}月  ${result.value.year_gz}年 · ${result.value.month_gz}月  [${result.value.purpose_label}]`
    : ''
)

// ── 翻月 ────────────────────────────────────────────────────────
function prevMonth() {
  if (formMonth.value === 1) { formYear.value--; formMonth.value = 12 }
  else formMonth.value--
  if (result.value) doRecommend()
}
function nextMonth() {
  if (formMonth.value === 12) { formYear.value++; formMonth.value = 1 }
  else formMonth.value++
  if (result.value) doRecommend()
}

// ── API 调用 ─────────────────────────────────────────────────
async function doRecommend() {
  if (!lifePalaceBranch.value || !wuxingJuName.value) {
    error.value = '请先选择命宫地支和五行局'
    return
  }
  loading.value  = true
  error.value    = ''
  selectedDay.value = null
  try {
    result.value = await recommendZeri({
      year:  formYear.value,
      month: formMonth.value,
      life_palace_branch:  lifePalaceBranch.value,
      wuxing_ju_name:      wuxingJuName.value,
      natal_year_branch:   natalYearBranch.value || undefined,
      purpose:             purpose.value,
    })
  } catch (e: unknown) {
    error.value = (e as { response?: { data?: { detail?: string } } })
      ?.response?.data?.detail ?? '查询失败，请重试'
  } finally {
    loading.value = false
  }
}

// ── 工具函数 ─────────────────────────────────────────────────
function selectDay(d: ZeriDayItem | null) {
  if (!d) return
  selectedDay.value = selectedDay.value?.date === d.date ? null : d
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr + 'T00:00:00')
  return `${d.getMonth() + 1}月${d.getDate()}日`
}
</script>

<template>
  <div class="wrap zeri-view">
    <h1 class="page-title">择日推荐</h1>

    <!-- ① 从紫微自动带入：成功横幅 -->
    <div v-if="fromZiwei" class="autofill-banner autofill-ok">
      ✅ 已从紫微命盘自动填入命宫地支「{{ lifePalaceBranch }}」、{{ wuxingJuName }}
      <template v-if="natalYearBranch">、本命年支「{{ natalYearBranch }}」</template>，
      正在计算推荐吉日…
    </div>

    <!-- ② 直接进入：引导提示 -->
    <div v-else-if="!lifePalaceBranch" class="autofill-banner autofill-hint">
      <span class="hint-icon">💡</span>
      <div class="hint-body">
        <strong>推荐从紫微排盘直接跳转</strong>，命宫地支和五行局将自动填入，无需手动查找。
        <br />
        <RouterLink to="/ziwei" class="hint-link">前往紫微排盘 →</RouterLink>
        计算完命盘后，点击顶部
        <span class="hint-badge">📅 择日</span>
        按钮即可自动跳转并填入数据。
      </div>
    </div>

    <!-- 查询表单 -->
    <div class="card form-card">
      <!-- 填写说明 -->
      <div class="field-guide">
        <p class="guide-title">📌 如何填写这两项？</p>
        <p class="guide-text">
          <strong>命宫地支</strong> 是紫微命盘中「命宫」所在的地支（子丑寅卯…），
          在<RouterLink to="/ziwei" class="guide-link">紫微排盘</RouterLink>页面命盘格中的「命宫」右上角可看到。
        </p>
        <p class="guide-text">
          <strong>五行局</strong> 是命盘中心显示的「X X局」（如水二局、木三局），两者均来自紫微命盘。
        </p>
        <p class="guide-text">
          <strong>本命年支</strong> 是出生年对应的生肖地支，如 1990 年 = 午（马）。
          可在下方输入出生年自动换算，<span class="opt-text">此项可不填</span>。
        </p>
      </div>

      <div class="form-grid">
        <div class="form-field">
          <label>命宫地支 <span class="field-badge">必填</span></label>
          <select v-model="lifePalaceBranch">
            <option value="">— 选择 —</option>
            <option v-for="b in BRANCHES" :key="b" :value="b">{{ b }}（{{ BRANCH_ZODIAC[b] }}）</option>
          </select>
          <span class="field-hint">紫微命盘「命宫」格的地支</span>
        </div>
        <div class="form-field">
          <label>五行局 <span class="field-badge">必填</span></label>
          <select v-model="wuxingJuName">
            <option v-for="j in WX_JU_LIST" :key="j" :value="j">{{ j }}</option>
          </select>
          <span class="field-hint">紫微命盘中心区域显示</span>
        </div>
        <div class="form-field natal-field">
          <label>本命年支 <span class="opt-tag">可选</span></label>
          <div class="natal-calc">
            <input
              type="number" v-model.number="birthYearInput"
              placeholder="出生年如 1990"
              class="birth-year-input"
              min="1900" max="2100"
              @keyup.enter="calcNatalBranch"
            />
            <button class="btn-calc" type="button" @click="calcNatalBranch">换算</button>
          </div>
          <select v-model="natalYearBranch">
            <option value="">— 不限 —</option>
            <option v-for="b in BRANCHES" :key="b" :value="b">{{ b }}（{{ BRANCH_ZODIAC[b] }}年生）</option>
          </select>
          <span class="field-hint">输入出生年后点"换算"自动填入</span>
        </div>
        <div class="form-field">
          <label>用途</label>
          <select v-model="purpose">
            <option v-for="(label, key) in purposes" :key="key" :value="key">{{ label }}</option>
          </select>
        </div>
        <div class="form-field">
          <label>年份</label>
          <input type="number" v-model.number="formYear" min="2020" max="2040" />
        </div>
        <div class="form-field">
          <label>月份</label>
          <select v-model.number="formMonth">
            <option v-for="m in 12" :key="m" :value="m">{{ m }}月</option>
          </select>
        </div>
      </div>
      <button class="btn-primary" :disabled="loading" @click="doRecommend">
        {{ loading ? '计算中…' : '开始推荐' }}
      </button>
      <p v-if="error" class="error-msg">{{ error }}</p>
    </div>

    <!-- 结果区域 -->
    <div v-if="result" class="result-wrap">

      <!-- 月份标题 + 翻月 -->
      <div class="month-nav">
        <button class="nav-btn" @click="prevMonth">‹</button>
        <span class="month-title">{{ monthTitle }}</span>
        <button class="nav-btn" @click="nextMonth">›</button>
      </div>

      <!-- 等级图例 -->
      <div class="legend-row">
        <span v-for="(label, key) in { daji: '大吉', ji: '吉', zhong: '中', xiong: '凶' }"
              :key="key" class="legend-item"
              :style="{ background: LEVEL_BG[key], color: LEVEL_FG[key], borderColor: LEVEL_BORDER[key] }">
          {{ label }}
        </span>
        <span class="legend-item legend-top">⭐ 推荐</span>
      </div>

      <!-- 日历主体 -->
      <div class="calendar-wrap">
        <!-- 周标题 -->
        <div class="cal-header">
          <div v-for="h in WEEK_HEADERS" :key="h" class="cal-hd">{{ h }}</div>
        </div>
        <!-- 日行 -->
        <div v-for="(row, ri) in calendarGrid" :key="ri" class="cal-row">
          <div v-for="(day, ci) in row" :key="ci"
               :class="['cal-cell',
                 day ? `level-${day.level_css}` : 'cal-empty',
                 { 'cal-top':   day ? topDaySet.has(day.date) : false },
                 { 'cal-sel':   day?.date === selectedDay?.date },
                 { 'cal-break': day?.is_break },
               ]"
               @click="selectDay(day)">
            <template v-if="day">
              <div class="cell-day-num">{{ new Date(day.date + 'T00:00:00').getDate() }}</div>
              <div class="cell-gz">{{ day.day_gz }}</div>
              <div class="cell-lunar">{{ day.lunar_info.slice(-3) }}</div>
              <div class="cell-score"
                   :style="{ background: LEVEL_BG[day.level_css], color: LEVEL_FG[day.level_css] }">
                {{ day.score }}
              </div>
              <div v-if="day.is_virtue" class="cell-virtue">德</div>
              <div v-if="topDaySet.has(day.date)" class="cell-star">⭐</div>
            </template>
          </div>
        </div>
      </div>

      <!-- 选中日期详情 -->
      <transition name="slide-up">
        <div v-if="selectedDay" class="day-detail card">
          <div class="dd-header">
            <span class="dd-date">{{ formatDate(selectedDay.date) }}</span>
            <span class="dd-gz">{{ selectedDay.day_gz }}</span>
            <span class="dd-lunar">{{ selectedDay.lunar_info }}</span>
            <span class="dd-badge"
                  :style="{ background: LEVEL_BG[selectedDay.level_css], color: LEVEL_FG[selectedDay.level_css] }">
              {{ selectedDay.level }} · {{ selectedDay.score }}分
            </span>
            <span v-if="selectedDay.is_virtue" class="dd-flag dd-virtue">天德/月德</span>
            <span v-if="selectedDay.is_break"  class="dd-flag dd-break">岁破/月破</span>
            <button class="dd-close" @click="selectedDay = null">×</button>
          </div>
          <ul v-if="selectedDay.evidence.length" class="dd-evidence">
            <li v-for="(ev, i) in selectedDay.evidence" :key="i">{{ ev }}</li>
          </ul>
          <p v-else class="dd-no-ev">该日无特殊加减分项</p>
        </div>
      </transition>

      <!-- 推荐日汇总 -->
      <div v-if="result.top_days.length" class="top-days-card card">
        <h3 class="top-days-title">⭐ 本月推荐吉日（共 {{ result.top_days.length }} 天）</h3>
        <div class="top-days-list">
          <div v-for="dateStr in result.top_days" :key="dateStr"
               class="top-day-item"
               @click="selectedDay = result!.days.find(d => d.date === dateStr) ?? null">
            <div class="td-date">{{ formatDate(dateStr) }}</div>
            <div class="td-gz">
              {{ result.days.find(d => d.date === dateStr)?.day_gz ?? '' }}
            </div>
            <div class="td-lunar">
              {{ result.days.find(d => d.date === dateStr)?.lunar_info ?? '' }}
            </div>
            <div class="td-score"
                 :style="{ background: LEVEL_BG[result.days.find(d => d.date === dateStr)?.level_css ?? 'zhong'],
                           color:      LEVEL_FG[result.days.find(d => d.date === dateStr)?.level_css ?? 'zhong'] }">
              {{ result.days.find(d => d.date === dateStr)?.score ?? '' }}分
            </div>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<style src="./ZeriView.css" scoped />
