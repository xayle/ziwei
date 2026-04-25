<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { recommendZeri, getZeriPurposes } from '@/api/zeri'
import type { ZeriDayItem, ZeriMonthResult } from '@/api/zeri'

const route = useRoute()

// ── 常量 ─────────────────────────────────────────────────────
const BRANCHES = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
const WX_JU_LIST = ['水二局','木三局','金四局','土五局','火六局']
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

// ── 从 URL query 预填（从紫微/八字页跳转过来）──────────────────
onMounted(async () => {
  const q = route.query
  if (q.life_palace_branch)   lifePalaceBranch.value  = String(q.life_palace_branch)
  if (q.wuxing_ju_name)       wuxingJuName.value       = String(q.wuxing_ju_name)
  if (q.natal_year_branch)    natalYearBranch.value    = String(q.natal_year_branch)
  if (q.purpose)              purpose.value            = String(q.purpose)
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

    <!-- 查询表单 -->
    <div class="card form-card">
      <div class="form-grid">
        <div class="form-field">
          <label>命宫地支</label>
          <select v-model="lifePalaceBranch">
            <option value="">— 选择 —</option>
            <option v-for="b in BRANCHES" :key="b" :value="b">{{ b }}</option>
          </select>
        </div>
        <div class="form-field">
          <label>五行局</label>
          <select v-model="wuxingJuName">
            <option v-for="j in WX_JU_LIST" :key="j" :value="j">{{ j }}</option>
          </select>
        </div>
        <div class="form-field">
          <label>本命年支<span class="opt-tag">可选</span></label>
          <select v-model="natalYearBranch">
            <option value="">— 不限 —</option>
            <option v-for="b in BRANCHES" :key="b" :value="b">{{ b }}</option>
          </select>
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

<style scoped>
.zeri-view { padding-bottom: var(--sp-8); }

.page-title {
  font-size: var(--fs-2xl); font-weight: 700;
  color: var(--text); margin-bottom: var(--sp-5);
  font-family: var(--font-cn);
}

/* 表单 */
.card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); padding: var(--sp-5); box-shadow: var(--shadow);
}
.form-card { margin-bottom: var(--sp-5); }
.form-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: var(--sp-3) var(--sp-4); margin-bottom: var(--sp-4);
}
.form-field { display: flex; flex-direction: column; gap: 4px; }
.form-field label { font-size: var(--fs-xs); color: var(--text-3); font-weight: 600; letter-spacing: .3px; }
.opt-tag { font-size: 10px; background: var(--surface-2); color: var(--text-3); border-radius: 4px; padding: 0 4px; margin-left: 4px; }
.form-field select,
.form-field input[type="number"] {
  padding: 7px 10px; border: 1px solid var(--border-md);
  border-radius: var(--radius-sm); font-size: var(--fs-md);
  background: var(--surface); color: var(--text);
  transition: border-color var(--dur-fast);
}
.form-field select:focus,
.form-field input:focus { outline: none; border-color: var(--accent); }
.btn-primary {
  padding: 9px 24px; background: var(--accent); color: #fff;
  border: none; border-radius: var(--radius-sm); font-size: var(--fs-md);
  font-weight: 600; cursor: pointer; transition: background var(--dur-fast);
}
.btn-primary:hover { background: var(--accent-dark); }
.btn-primary:disabled { opacity: .6; cursor: not-allowed; }
.error-msg { color: var(--danger-dark); font-size: var(--fs-sm); margin-top: var(--sp-2); }

/* 月份导航 */
.month-nav {
  display: flex; align-items: center; gap: var(--sp-4);
  margin-bottom: var(--sp-4);
}
.nav-btn {
  width: 32px; height: 32px; border: 1px solid var(--border-md);
  border-radius: 50%; background: var(--surface); color: var(--text);
  font-size: 20px; cursor: pointer; display: flex; align-items: center; justify-content: center;
  transition: all var(--dur-fast);
}
.nav-btn:hover { background: var(--accent); color: #fff; border-color: var(--accent); }
.month-title { font-size: var(--fs-lg); font-weight: 600; font-family: var(--font-cn); }

/* 图例 */
.legend-row { display: flex; gap: var(--sp-2); flex-wrap: wrap; margin-bottom: var(--sp-4); }
.legend-item {
  padding: 3px 12px; border-radius: 12px; font-size: var(--fs-xs);
  font-weight: 600; border: 1px solid transparent;
}
.legend-top { background: #fef9c3; color: #a16207; border-color: #fbbf24; }

/* 日历 */
.calendar-wrap { margin-bottom: var(--sp-5); }
.cal-header {
  display: grid; grid-template-columns: repeat(7, 1fr);
  gap: 3px; margin-bottom: 3px;
}
.cal-hd {
  text-align: center; font-size: var(--fs-xs); color: var(--text-3);
  padding: 6px 0; font-weight: 600;
}
.cal-row { display: grid; grid-template-columns: repeat(7, 1fr); gap: 3px; margin-bottom: 3px; }

.cal-cell {
  min-height: 80px; padding: 5px; border-radius: var(--radius-sm);
  border: 1.5px solid var(--border); background: var(--surface);
  cursor: pointer; position: relative; transition: border-color .15s, box-shadow .15s;
  overflow: hidden;
}
.cal-empty { background: transparent; border-color: transparent; cursor: default; }
.cal-cell:not(.cal-empty):hover { border-color: var(--accent); box-shadow: 0 1px 6px var(--accent-soft); }
.cal-sel   { border-color: var(--accent) !important; box-shadow: 0 0 0 2px var(--accent-soft); }
.cal-top   { box-shadow: inset 0 0 0 1.5px #fbbf24; }
.cal-break { opacity: .5; }

/* 吉凶背景 */
.level-daji  { background: #f0fdf4; border-color: #86efac; }
.level-ji    { background: #eff6ff; border-color: #93c5fd; }
.level-zhong { background: var(--surface); }
.level-xiong { background: #fff1f2; border-color: #fca5a5; }

/* 日历单元格内容 */
.cell-day-num { font-size: 15px; font-weight: 700; color: var(--text); line-height: 1.2; }
.cell-gz      { font-size: 11px; color: var(--text-2); font-family: var(--font-cn); margin-top: 2px; }
.cell-lunar   { font-size: 10px; color: var(--text-3); margin-top: 1px; }
.cell-score   {
  display: inline-block; font-size: 10px; font-weight: 700;
  padding: 1px 5px; border-radius: 8px; margin-top: 3px;
}
.cell-virtue {
  position: absolute; top: 3px; right: 4px;
  font-size: 9px; color: #15803d; font-weight: 700;
}
.cell-star {
  position: absolute; bottom: 3px; right: 3px; font-size: 11px;
}

/* 选中日详情 */
.day-detail { margin-bottom: var(--sp-5); }
.dd-header { display: flex; align-items: center; gap: var(--sp-3); flex-wrap: wrap; margin-bottom: var(--sp-3); }
.dd-date   { font-size: var(--fs-xl); font-weight: 700; }
.dd-gz     { font-size: var(--fs-xl); font-family: var(--font-cn); font-weight: 700; }
.dd-lunar  { font-size: var(--fs-sm); color: var(--text-3); }
.dd-badge  { padding: 4px 14px; border-radius: 20px; font-size: var(--fs-sm); font-weight: 700; }
.dd-flag   { padding: 3px 10px; border-radius: 12px; font-size: var(--fs-xs); font-weight: 600; }
.dd-virtue { background: #dcfce7; color: #15803d; }
.dd-break  { background: #fee2e2; color: #dc2626; }
.dd-close  { margin-left: auto; background: none; border: none; font-size: 22px; cursor: pointer; color: var(--text-3); }
.dd-close:hover { color: var(--text); }
.dd-evidence { padding-left: 1.4em; margin: 0; }
.dd-evidence li { font-size: var(--fs-sm); color: var(--text); line-height: 1.8; }
.dd-no-ev  { font-size: var(--fs-sm); color: var(--text-3); }

/* 推荐日汇总 */
.top-days-card { margin-top: var(--sp-5); }
.top-days-title { font-size: var(--fs-md); font-weight: 700; margin-bottom: var(--sp-4); color: var(--text); }
.top-days-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: var(--sp-3); }
.top-day-item {
  padding: var(--sp-3); border: 1px solid var(--border-md);
  border-radius: var(--radius-sm); background: var(--surface-2);
  cursor: pointer; transition: box-shadow .15s;
  display: flex; flex-direction: column; gap: 3px;
}
.top-day-item:hover { box-shadow: 0 2px 8px var(--accent-soft); border-color: var(--accent); }
.td-date  { font-size: var(--fs-md); font-weight: 700; }
.td-gz    { font-size: var(--fs-sm); font-family: var(--font-cn); color: var(--text-2); }
.td-lunar { font-size: var(--fs-xs); color: var(--text-3); }
.td-score { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: var(--fs-xs); font-weight: 700; align-self: flex-start; }

/* 过渡 */
.slide-up-enter-active, .slide-up-leave-active  { transition: opacity .2s, transform .2s; }
.slide-up-enter-from,   .slide-up-leave-to      { opacity: 0; transform: translateY(8px); }

/* 响应式 */
@media (max-width: 600px) {
  .cal-cell { min-height: 56px; padding: 3px; }
  .cell-day-num { font-size: 13px; }
  .cell-gz, .cell-lunar { display: none; }
  .form-grid { grid-template-columns: 1fr 1fr; }
  .top-days-list { grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); }
}
</style>
