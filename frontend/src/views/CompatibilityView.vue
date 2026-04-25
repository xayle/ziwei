<script setup lang="ts">
/**
 * CompatibilityView.vue — 四柱合婚（§5.1）
 * 功能：甲乙双方八字输入 → 五维评分 → SVG 可视化 + 详细解析
 */
import { ref } from 'vue'
import { getBaziCompat } from '@/api/compat'

// ── 表单 ──────────────────────────────────────────────────────
interface PersonForm {
  date: string
  time: string
  lon:  string
  tz:   string
}

const personA = ref<PersonForm>({ date: '1990-06-15', time: '10:30', lon: '116.41', tz: 'Asia/Shanghai' })
const personB = ref<PersonForm>({ date: '1992-03-22', time: '08:00', lon: '116.41', tz: 'Asia/Shanghai' })

const loading = ref(false)
const error   = ref<string | null>(null)

interface CompatDetail {
  dimension:   string
  score:       number
  max:         number
  description: string
  level:       string
}
interface PersonSummary {
  pillars:  Record<string, { stem: string; branch: string }>
  weights:  Record<string, number>
  day_stem: string
  day_elem: string
}
interface CompatResult {
  score:    number
  grade:    string
  summary:  string
  details:  CompatDetail[]
  person_a: PersonSummary
  person_b: PersonSummary
}

const result = ref<CompatResult | null>(null)

const CITIES = [
  { label: '北京', lon: '116.41', tz: 'Asia/Shanghai' },
  { label: '上海', lon: '121.47', tz: 'Asia/Shanghai' },
  { label: '广州', lon: '113.26', tz: 'Asia/Shanghai' },
  { label: '成都', lon: '104.07', tz: 'Asia/Shanghai' },
]

async function query() {
  loading.value = true
  error.value   = null
  result.value  = null
  try {
    result.value = await getBaziCompat({
      a_dt:  `${personA.value.date}T${personA.value.time}:00`,
      a_tz:  personA.value.tz,
      a_lon: Number(personA.value.lon),
      b_dt:  `${personB.value.date}T${personB.value.time}:00`,
      b_tz:  personB.value.tz,
      b_lon: Number(personB.value.lon),
    })
  } catch (e: unknown) {
    error.value = (e as Error).message ?? '计算失败'
  } finally {
    loading.value = false
  }
}

// ── 五行颜色 ──────────────────────────────────────────────────
const ELEM_COLOR: Record<string, string> = {
  wood: '#22c55e', fire: '#ef4444', earth: '#f59e0b',
  metal: '#94a3b8', water: '#3b82f6',
}
const ELEM_CN: Record<string, string> = {
  wood: '木', fire: '火', earth: '土', metal: '金', water: '水'
}

// ── 评分等级颜色 ──────────────────────────────────────────────
const GRADE_COLOR: Record<string, string> = {
  '上上': '#ef4444', '上': '#f97316', '中': '#f59e0b', '下': '#64748b', '下下': '#94a3b8'
}
const LEVEL_COLOR: Record<string, string> = {
  '佳': '#22c55e', '中': '#f59e0b', '差': '#ef4444'
}

// ── SVG 雷达图（五行对比） ────────────────────────────────────
function radarPath(weights: Record<string, number>, scale: number, cx: number, cy: number, r: number): string {
  const elems = ['wood', 'fire', 'earth', 'metal', 'water']
  const pts = elems.map((e, i) => {
    const angle = (i * 2 * Math.PI / 5) - Math.PI / 2
    const val = ((weights[e] ?? 0) / 100) * r * scale
    return [cx + val * Math.cos(angle), cy + val * Math.sin(angle)]
  })
  return pts.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(' ') + ' Z'
}

function radarGrid(cx: number, cy: number, r: number): string {
  const elems = 5
  return [0.25, 0.5, 0.75, 1.0].map(scale => {
    const pts = Array.from({ length: elems }, (_, i) => {
      const angle = (i * 2 * Math.PI / elems) - Math.PI / 2
      return [cx + r * scale * Math.cos(angle), cy + r * scale * Math.sin(angle)]
    })
    return pts.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(' ') + ' Z'
  }).join(' ')
}

function radarLabels(cx: number, cy: number, r: number) {
  const elems = ['木', '火', '土', '金', '水']
  return Array.from({ length: 5 }, (_, i) => {
    const angle = (i * 2 * Math.PI / 5) - Math.PI / 2
    return {
      x: cx + (r + 18) * Math.cos(angle),
      y: cy + (r + 18) * Math.sin(angle),
      label: elems[i],
    }
  })
}

// ── 四柱显示 ─────────────────────────────────────────────────
const PILLAR_LABELS = ['年', '月', '日', '时']
const PILLAR_KEYS   = ['year', 'month', 'day', 'hour']
const STEM_ELEM_CH: Record<string, string> = {
  甲:'wood',乙:'wood',丙:'fire',丁:'fire',戊:'earth',己:'earth',
  庚:'metal',辛:'metal',壬:'water',癸:'water',
}
</script>

<template>
  <div class="cp-wrap">
    <!-- 标题 -->
    <div class="cp-header">
      <h1 class="cp-title">四柱合婚 · 八字合盘</h1>
      <p class="cp-subtitle">§5.1 天干地支生克 + 年支合冲 + 五行互补 — 综合评分（0-100）</p>
    </div>

    <!-- 双人输入表单 -->
    <div class="cp-forms">
      <template v-for="(person, key) in [{ form: personA, label: '甲方（男/女）' }, { form: personB, label: '乙方（男/女）' }]" :key="key">
        <div class="cp-person-card" :class="key === 0 ? 'cp-card-a' : 'cp-card-b'">
          <h2 class="cp-person-title">{{ person.label }}</h2>
          <div class="cp-form-grid">
            <div class="cp-field">
              <label class="cp-label">出生日期</label>
              <input v-model="person.form.date" type="date" class="cp-input" />
            </div>
            <div class="cp-field">
              <label class="cp-label">出生时间</label>
              <input v-model="person.form.time" type="time" class="cp-input" />
            </div>
            <div class="cp-field">
              <label class="cp-label">经度</label>
              <input v-model="person.form.lon" type="number" step="0.01" class="cp-input" />
            </div>
            <div class="cp-field">
              <label class="cp-label">时区</label>
              <input v-model="person.form.tz" type="text" class="cp-input" placeholder="Asia/Shanghai" />
            </div>
          </div>
          <!-- 快捷城市 -->
          <div class="cp-cities">
            <button
              v-for="c in CITIES" :key="c.label"
              class="cp-city-btn"
              @click="person.form.lon = c.lon; person.form.tz = c.tz"
            >{{ c.label }}</button>
          </div>
        </div>
      </template>
    </div>

    <!-- 按钮 -->
    <div class="cp-actions">
      <button class="cp-btn-primary" :disabled="loading" @click="query">
        {{ loading ? '合盘计算中…' : '💑 开始合婚' }}
      </button>
    </div>

    <div v-if="error" class="cp-error">⚠️ {{ error }}</div>

    <!-- ── 结果 ── -->
    <template v-if="result">
      <!-- 综合评分横幅 -->
      <div class="cp-score-banner" :style="{ borderColor: GRADE_COLOR[result.grade] }">
        <div class="cp-score-left">
          <div class="cp-score-num" :style="{ color: GRADE_COLOR[result.grade] }">{{ result.score }}</div>
          <div class="cp-score-unit">/ 100</div>
        </div>
        <div class="cp-score-center">
          <div class="cp-grade" :style="{ color: GRADE_COLOR[result.grade] }">{{ result.grade }}</div>
          <div class="cp-summary">{{ result.summary }}</div>
        </div>
        <!-- 评分条 -->
        <div class="cp-score-bar-wrap">
          <div class="cp-score-track">
            <div class="cp-score-fill"
              :style="{ width: result.score + '%', background: GRADE_COLOR[result.grade] }">
            </div>
          </div>
          <div class="cp-grade-labels">
            <span>下下</span><span>下</span><span>中</span><span>上</span><span>上上</span>
          </div>
        </div>
      </div>

      <div class="cp-result-grid">
        <!-- 左：五行雷达 + 四柱对比 -->
        <div class="cp-left-col">
          <!-- SVG 五行雷达对比 -->
          <div class="cp-radar-card">
            <h2 class="cp-sec-title">五行分布对比</h2>
            <svg viewBox="0 0 260 260" width="240" height="240">
              <!-- 网格 -->
              <path :d="radarGrid(130, 130, 90)" fill="none" stroke="var(--border)" stroke-width="0.8"/>
              <!-- 轴线 -->
              <g v-for="lbl in radarLabels(130, 130, 90)" :key="lbl.label">
                <line x1="130" y1="130" :x2="lbl.x - (lbl.x > 130 ? 16 : -16) * 0" :y2="lbl.y" stroke="var(--border)" stroke-width="0.5"/>
                <text :x="lbl.x" :y="lbl.y" text-anchor="middle" dominant-baseline="central"
                  class="radar-label">{{ lbl.label }}</text>
              </g>
              <!-- 甲方五行面 -->
              <path :d="radarPath(result.person_a.weights, 1.0, 130, 130, 90)"
                fill="#ef444422" stroke="#ef4444" stroke-width="1.5"/>
              <!-- 乙方五行面 -->
              <path :d="radarPath(result.person_b.weights, 1.0, 130, 130, 90)"
                fill="#3b82f622" stroke="#3b82f6" stroke-width="1.5"/>
              <!-- 图例 -->
              <rect x="10" y="230" width="12" height="4" fill="#ef4444" rx="2"/>
              <text x="26" y="234" class="radar-legend">甲方</text>
              <rect x="70" y="230" width="12" height="4" fill="#3b82f6" rx="2"/>
              <text x="86" y="234" class="radar-legend">乙方</text>
            </svg>

            <!-- 五行数值表 -->
            <table class="cp-wx-table">
              <thead><tr>
                <th>五行</th>
                <th style="color:#ef4444">甲方 %</th>
                <th style="color:#3b82f6">乙方 %</th>
              </tr></thead>
              <tbody>
                <tr v-for="[e, cn] in [['wood','木'],['fire','火'],['earth','土'],['metal','金'],['water','水']]" :key="e">
                  <td :style="{ color: ELEM_COLOR[e] }"><strong>{{ cn }}</strong></td>
                  <td class="cp-wx-val">{{ result.person_a.weights[e] ?? 0 }}%</td>
                  <td class="cp-wx-val">{{ result.person_b.weights[e] ?? 0 }}%</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 四柱对比卡 -->
          <div class="cp-pillars-card">
            <h2 class="cp-sec-title">四柱对照</h2>
            <table class="cp-pillars-table">
              <thead><tr>
                <th>柱</th>
                <th style="color:#ef4444">甲方</th>
                <th style="color:#3b82f6">乙方</th>
              </tr></thead>
              <tbody>
                <tr v-for="(key, i) in PILLAR_KEYS" :key="key">
                  <td class="cp-pt-label">{{ PILLAR_LABELS[i] }}柱</td>
                  <td class="cp-pt-cell">
                    <span class="cp-gz"
                      :style="{ color: ELEM_COLOR[STEM_ELEM_CH[result.person_a.pillars[key].stem] ?? ''] }">
                      {{ result.person_a.pillars[key].stem }}{{ result.person_a.pillars[key].branch }}
                    </span>
                    <span v-if="key === 'day'" class="cp-day-mark">日主</span>
                  </td>
                  <td class="cp-pt-cell">
                    <span class="cp-gz"
                      :style="{ color: ELEM_COLOR[STEM_ELEM_CH[result.person_b.pillars[key].stem] ?? ''] }">
                      {{ result.person_b.pillars[key].stem }}{{ result.person_b.pillars[key].branch }}
                    </span>
                    <span v-if="key === 'day'" class="cp-day-mark">日主</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- 右：维度评分详情 -->
        <div class="cp-right-col">
          <h2 class="cp-sec-title">评分维度详情</h2>
          <div class="cp-details-list">
            <div class="cp-detail-card" v-for="d in result.details" :key="d.dimension">
              <div class="cp-detail-header">
                <span class="cp-dim-name">{{ d.dimension }}</span>
                <span class="cp-dim-level" :style="{ color: LEVEL_COLOR[d.level] }">{{ d.level }}</span>
                <span class="cp-dim-score">{{ d.score }} / {{ d.max }}</span>
              </div>
              <!-- 进度条 -->
              <div class="cp-dim-track">
                <div class="cp-dim-fill"
                  :style="{
                    width: (d.score / d.max * 100) + '%',
                    background: LEVEL_COLOR[d.level],
                  }">
                </div>
              </div>
              <p class="cp-dim-desc">{{ d.description }}</p>
            </div>
          </div>

          <!-- 日主说明 -->
          <div class="cp-day-summary">
            <div class="cp-day-row" v-for="[label, ps] in ([['甲方', result.person_a], ['乙方', result.person_b]] as const)" :key="label">
              <span class="cp-day-label">{{ label }} 日主：</span>
              <span class="cp-day-stem" :style="{ color: ELEM_COLOR[(ps as PersonSummary).day_elem] }">
                {{ (ps as PersonSummary).day_stem }}（{{ ELEM_CN[(ps as PersonSummary).day_elem] ?? (ps as PersonSummary).day_elem }}）
              </span>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- 空态 -->
    <div v-if="!result && !loading" class="cp-empty">
      <div class="cp-empty-icon">💑</div>
      <p>填写双方出生信息后点击「开始合婚」查看配对分析</p>
    </div>
  </div>
</template>

<style scoped>
/* ── 布局 ───────────────────────────────────────────────────── */
.cp-wrap {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px 20px 56px;
}

.cp-header { margin-bottom: 20px; }
.cp-title  { font-size: 22px; font-weight: 700; color: var(--text); margin: 0; font-family: var(--font-cn); }
.cp-subtitle { font-size: 12px; color: var(--text-3); margin: 4px 0 0; }

/* ── 双人表单 ───────────────────────────────────────────────── */
.cp-forms {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

.cp-person-card {
  background: var(--surface);
  border: 2px solid var(--border);
  border-radius: 12px;
  padding: 18px;
}
.cp-card-a { border-top: 3px solid #ef4444; }
.cp-card-b { border-top: 3px solid #3b82f6; }

.cp-person-title {
  font-size: 14px; font-weight: 700; color: var(--text);
  font-family: var(--font-cn); margin: 0 0 14px;
}

.cp-form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-bottom: 10px;
}

.cp-field { display: flex; flex-direction: column; gap: 4px; }
.cp-label { font-size: 10px; color: var(--text-3); font-weight: 500; text-transform: uppercase; letter-spacing: .04em; }
.cp-input {
  padding: 7px 10px;
  border: 1px solid var(--border);
  border-radius: 7px;
  background: var(--bg);
  color: var(--text);
  font-size: 13px;
  outline: none;
  transition: border-color .15s;
  font-family: var(--font-mono);
}
.cp-input:focus { border-color: var(--accent); }

.cp-cities { display: flex; flex-wrap: wrap; gap: 6px; }
.cp-city-btn {
  padding: 3px 9px;
  border: 1px solid var(--border);
  border-radius: 99px;
  background: var(--bg);
  font-size: 11px;
  color: var(--text-3);
  cursor: pointer;
  transition: all .15s;
}
.cp-city-btn:hover { border-color: var(--accent); color: var(--accent); }

/* ── 按钮 ───────────────────────────────────────────────────── */
.cp-actions { display: flex; justify-content: center; margin-bottom: 20px; }
.cp-btn-primary {
  padding: 11px 36px;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: background .15s;
  font-family: var(--font-cn);
}
.cp-btn-primary:hover:not(:disabled) { background: var(--accent-dark); }
.cp-btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }

/* ── 错误 ───────────────────────────────────────────────────── */
.cp-error {
  padding: 12px 16px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 10px;
  color: #dc2626;
  font-size: 13px;
  margin-bottom: 20px;
}

/* ── 评分横幅 ───────────────────────────────────────────────── */
.cp-score-banner {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
  background: var(--surface);
  border: 2px solid;
  border-radius: 14px;
  padding: 20px 24px;
  margin-bottom: 20px;
}

.cp-score-left { display: flex; align-items: baseline; gap: 4px; }
.cp-score-num  { font-size: 56px; font-weight: 900; font-family: var(--font-mono); line-height: 1; }
.cp-score-unit { font-size: 16px; color: var(--text-3); }

.cp-score-center { flex: 1; }
.cp-grade   { font-size: 28px; font-weight: 800; font-family: var(--font-cn); }
.cp-summary { font-size: 13px; color: var(--text-2); font-family: var(--font-cn); line-height: 1.5; margin-top: 4px; }

.cp-score-bar-wrap { flex: 1; min-width: 200px; }
.cp-score-track {
  height: 8px; background: var(--surface-2);
  border-radius: 99px; overflow: hidden; margin-bottom: 6px;
}
.cp-score-fill { height: 100%; border-radius: 99px; transition: width .6s ease; }
.cp-grade-labels {
  display: flex; justify-content: space-between;
  font-size: 9px; color: var(--text-3); font-family: var(--font-cn);
}

/* ── 结果网格 ───────────────────────────────────────────────── */
.cp-result-grid {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 20px;
  align-items: start;
}

/* ── 左侧 ───────────────────────────────────────────────────── */
.cp-left-col { display: flex; flex-direction: column; gap: 16px; }

.cp-radar-card, .cp-pillars-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 16px;
}

.cp-sec-title {
  font-size: 14px; font-weight: 700; color: var(--text);
  font-family: var(--font-cn); margin: 0 0 12px;
}

svg .radar-label { font-size: 11px; fill: var(--text-2); font-family: var(--font-cn); }
svg .radar-legend { font-size: 10px; fill: var(--text-3); font-family: var(--font-cn); dominant-baseline: central; }

.cp-wx-table { width: 100%; border-collapse: collapse; font-family: var(--font-cn); font-size: 13px; margin-top: 8px; }
.cp-wx-table th { padding: 4px 8px; text-align: left; font-size: 10px; color: var(--text-3); text-transform: uppercase; border-bottom: 1px solid var(--border); }
.cp-wx-table td { padding: 6px 8px; border-bottom: 1px solid var(--border); }
.cp-wx-table tr:last-child td { border-bottom: none; }
.cp-wx-val { font-family: var(--font-mono); }

.cp-pillars-table { width: 100%; border-collapse: collapse; font-family: var(--font-cn); }
.cp-pillars-table th { padding: 5px 8px; font-size: 10px; color: var(--text-3); border-bottom: 1px solid var(--border); text-align: left; text-transform: uppercase; }
.cp-pillars-table td { padding: 7px 8px; border-bottom: 1px solid var(--border); }
.cp-pillars-table tr:last-child td { border-bottom: none; }
.cp-pt-label { font-size: 11px; color: var(--text-3); }
.cp-pt-cell { display: flex; align-items: center; gap: 6px; }
.cp-gz { font-size: 18px; font-weight: 800; font-family: var(--font-cn); letter-spacing: 1px; }
.cp-day-mark { font-size: 10px; color: var(--accent); border: 1px solid var(--accent); border-radius: 4px; padding: 1px 4px; }

/* ── 右侧 ───────────────────────────────────────────────────── */
.cp-right-col { display: block; }

.cp-details-list { display: flex; flex-direction: column; gap: 12px; margin-bottom: 16px; }
.cp-detail-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px 16px;
}
.cp-detail-header {
  display: flex; align-items: center; gap: 10px; margin-bottom: 8px;
}
.cp-dim-name  { font-size: 14px; font-weight: 700; color: var(--text); font-family: var(--font-cn); flex: 1; }
.cp-dim-level { font-size: 13px; font-weight: 700; font-family: var(--font-cn); }
.cp-dim-score { font-size: 13px; font-family: var(--font-mono); color: var(--text-2); }
.cp-dim-track {
  height: 6px; background: var(--surface-2); border-radius: 99px; overflow: hidden; margin-bottom: 8px;
}
.cp-dim-fill { height: 100%; border-radius: 99px; transition: width .5s; }
.cp-dim-desc { font-size: 12px; color: var(--text-2); font-family: var(--font-cn); margin: 0; line-height: 1.6; }

.cp-day-summary {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px 16px;
  display: flex; flex-direction: column; gap: 8px;
}
.cp-day-row { display: flex; align-items: center; gap: 6px; }
.cp-day-label { font-size: 12px; color: var(--text-3); font-family: var(--font-cn); }
.cp-day-stem  { font-size: 18px; font-weight: 800; font-family: var(--font-cn); }

/* ── 空态 ───────────────────────────────────────────────────── */
.cp-empty {
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  padding: 60px 20px; gap: 12px;
  color: var(--text-3);
}
.cp-empty-icon { font-size: 52px; opacity: 0.3; }
.cp-empty p { font-size: 14px; font-family: var(--font-cn); }

/* ── 响应式 ─────────────────────────────────────────────────── */
@media (max-width: 1024px) {
  .cp-result-grid { grid-template-columns: 1fr; }
}
@media (max-width: 720px) {
  .cp-forms { grid-template-columns: 1fr; }
  .cp-score-banner { flex-direction: column; text-align: center; }
}
</style>
