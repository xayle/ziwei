<script setup lang="ts">
/**
 * CompatibilityView.vue — 合婚 / 合盘工作区
 * 功能：
 * - /compat：四柱合婚（§5.1）
 * - /compat/synastry：紫微 / 西方合盘入口工作区
 */
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getBaziCompat } from '@/api/compat'
import { computeRelationCompat, type RelationComputeResponse } from '@/api/relations'

type ViewMode = 'bazi' | 'synastry'

interface PersonForm {
  date: string
  time: string
  lon: string
  tz: string
}

interface CompatDetail {
  dimension: string
  score: number
  max: number
  description: string
  level: string
}

interface PersonSummary {
  pillars: Record<string, { stem: string; branch: string }>
  weights: Record<string, number>
  day_stem: string
  day_elem: string
}

interface CompatResult {
  score: number
  grade: string
  summary: string
  details: CompatDetail[]
  person_a: PersonSummary
  person_b: PersonSummary
}

const route = useRoute()
const router = useRouter()
const viewMode = computed<ViewMode>(() => route.path.startsWith('/compat/synastry') ? 'synastry' : 'bazi')

const modeMeta: Record<ViewMode, {
  title: string
  subtitle: string
  description: string
}> = {
  bazi: {
    title: '合婚 / 合盘工作区',
    subtitle: '四柱合婚 · 八字合盘',
    description: '先承接双方出生信息与四柱兼容评分，再根据咨询目标切换到紫微或西方合盘。',
  },
  synastry: {
    title: '合婚 / 合盘工作区',
    subtitle: '紫微合盘 / 西方合盘',
    description: '统一承接关系分析入口，把紫微双人合盘、多人关系矩阵与西方相位互照拆分到独立体系。',
  },
}

const synastryCards = [
  {
    title: '紫微双人合盘',
    description: '适合已经掌握双方出生信息，重点查看宫位互照、四化互动与关系张力。',
    path: '/ziwei',
    badge: '已就绪',
    apis: ['/api/v1/ziwei/compatibility'],
  },
  {
    title: '多人关系矩阵',
    description: '适合家族、团队或多角色关系评估，输出多人配对矩阵与整体和谐度。',
    path: '/compat/team',
    badge: '已就绪',
    apis: ['/api/v1/ziwei/multi_compat'],
  },
  {
    title: '西方 Synastry / Composite',
    description: '适合查看行星相位互照、关系动力与沟通模式，后续再沉淀到报告页。',
    path: '/western',
    badge: '入口已独立',
    apis: ['/api/v1/western（规划中）'],
  },
] as const

const workspaceSteps = [
  '先在案例中心确认双方出生时间、地点、时区。',
  '需要快速定量评分时，先使用四柱合婚获得基础兼容结论。',
  '需要深度关系结构时，进入紫微或西方模块做合盘。',
  '确认结论后，再进入报告书与 AI 草稿沉淀交付。',
]

const personA = ref<PersonForm>({ date: '1990-06-15', time: '10:30', lon: '116.41', tz: 'Asia/Shanghai' })
const personB = ref<PersonForm>({ date: '1992-03-22', time: '08:00', lon: '116.41', tz: 'Asia/Shanghai' })

const loading = ref(false)
const error = ref<string | null>(null)
const result = ref<CompatResult | null>(null)

const CITIES = [
  { label: '北京', lon: '116.41', tz: 'Asia/Shanghai' },
  { label: '上海', lon: '121.47', tz: 'Asia/Shanghai' },
  { label: '广州', lon: '113.26', tz: 'Asia/Shanghai' },
  { label: '成都', lon: '104.07', tz: 'Asia/Shanghai' },
]

async function query() {
  loading.value = true
  error.value = null
  result.value = null
  try {
    result.value = await getBaziCompat({
      a_dt: `${personA.value.date}T${personA.value.time}:00`,
      a_tz: personA.value.tz,
      a_lon: Number(personA.value.lon),
      b_dt: `${personB.value.date}T${personB.value.time}:00`,
      b_tz: personB.value.tz,
      b_lon: Number(personB.value.lon),
    })
  } catch (e: unknown) {
    error.value = (e as Error).message ?? '计算失败'
  } finally {
    loading.value = false
  }
}

function openMode(mode: ViewMode) {
  router.push(mode === 'bazi' ? '/compat' : '/compat/synastry')
}

function openPath(path: string) {
  router.push(path)
}

const ELEM_COLOR: Record<string, string> = {
  wood: '#22c55e', fire: '#ef4444', earth: '#f59e0b',
  metal: '#94a3b8', water: '#3b82f6',
}

const ELEM_CN: Record<string, string> = {
  wood: '木', fire: '火', earth: '土', metal: '金', water: '水',
}

const GRADE_COLOR: Record<string, string> = {
  上上: '#ef4444', 上: '#f97316', 中: '#f59e0b', 下: '#64748b', 下下: '#94a3b8',
}

const LEVEL_COLOR: Record<string, string> = {
  佳: '#22c55e', 中: '#f59e0b', 差: '#ef4444',
}

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

// ── 关系合盘评分 (T1.3) ─────────────────────────────────────
const relCaseA   = ref('')
const relCaseB   = ref('')
const relType    = ref('love')
const relLoading = ref(false)
const relError   = ref<string | null>(null)
const relResult  = ref<RelationComputeResponse | null>(null)

const RELATION_TYPE_OPTIONS = [
  { value: 'love',        label: '恋爱关系' },
  { value: 'marriage',    label: '婚姻关系' },
  { value: 'friendship',  label: '友谊关系' },
  { value: 'business',    label: '合伙关系' },
  { value: 'parent_child',label: '亲子关系' },
  { value: 'colleague',   label: '同事关系' },
]

async function queryRelation() {
  if (!relCaseA.value.trim() || !relCaseB.value.trim()) {
    relError.value = '请填写双方案例 ID'
    return
  }
  relLoading.value = true
  relError.value = null
  relResult.value = null
  try {
    relResult.value = await computeRelationCompat({
      case_a_id: relCaseA.value.trim(),
      case_b_id: relCaseB.value.trim(),
      relation_type: relType.value,
    })
  } catch (e: unknown) {
    relError.value = (e as Error).message ?? '关系分析失败'
  } finally {
    relLoading.value = false
  }
}

const PILLAR_LABELS = ['年', '月', '日', '时']
const PILLAR_KEYS = ['year', 'month', 'day', 'hour']
const STEM_ELEM_CH: Record<string, string> = {
  甲: 'wood', 乙: 'wood', 丙: 'fire', 丁: 'fire', 戊: 'earth', 己: 'earth',
  庚: 'metal', 辛: 'metal', 壬: 'water', 癸: 'water',
}
</script>

<template>
  <div class="cp-wrap">
    <div class="cp-header">
      <p class="cp-kicker">关系分析模块</p>
      <h1 class="cp-title">{{ modeMeta[viewMode].title }}</h1>
      <p class="cp-subtitle">{{ modeMeta[viewMode].subtitle }}</p>
      <p class="cp-desc">{{ modeMeta[viewMode].description }}</p>
      <div class="cp-mode-tabs">
        <button class="cp-mode-tab" :class="{ active: viewMode === 'bazi' }" @click="openMode('bazi')">四柱合婚</button>
        <button class="cp-mode-tab" :class="{ active: viewMode === 'synastry' }" @click="openMode('synastry')">紫微 / 西方合盘</button>
      </div>
    </div>

    <div v-if="viewMode === 'synastry'" class="cp-synastry-layout">
      <section class="cp-intro-card">
        <div>
          <div class="cp-intro-title">跨体系合盘入口</div>
          <p class="cp-intro-desc">
            合盘不再挂在案例中心的零散入口下，而是先由本页承接，再按分析体系分流到紫微、西占与多人关系工具。
          </p>
        </div>
        <div class="cp-intro-actions">
          <button class="cp-btn-primary" @click="openPath('/ziwei')">进入紫微模块</button>
          <button class="cp-btn-secondary" @click="openPath('/western')">进入西方占星</button>
        </div>
      </section>

      <section class="cp-synastry-grid">
        <article v-for="card in synastryCards" :key="card.title" class="cp-workspace-card">
          <div class="cp-workspace-top">
            <h2 class="cp-sec-title">{{ card.title }}</h2>
            <span class="cp-status-badge">{{ card.badge }}</span>
          </div>
          <p class="cp-workspace-desc">{{ card.description }}</p>
          <div class="cp-api-row">
            <span v-for="api in card.apis" :key="api" class="cp-api-chip">{{ api }}</span>
          </div>
          <button class="cp-workspace-link" @click="openPath(card.path)">打开对应模块</button>
        </article>
      </section>

      <section class="cp-guidance-grid">
        <article class="cp-guidance-card">
          <h2 class="cp-sec-title">推荐使用路径</h2>
          <ol class="cp-step-list">
            <li v-for="step in workspaceSteps" :key="step">{{ step }}</li>
          </ol>
        </article>
        <article class="cp-guidance-card">
          <h2 class="cp-sec-title">当前模块边界</h2>
          <div class="cp-boundary-list">
            <div class="cp-boundary-item">
              <strong>四柱合婚</strong>
              <span>保留在本页，适合先做基础兼容评分与冲合摘要。</span>
            </div>
            <div class="cp-boundary-item">
              <strong>紫微双人 / 多人合盘</strong>
              <span>继续由紫微模块承接，后续可再抽离更独立的关系工作区。</span>
            </div>
            <div class="cp-boundary-item">
              <strong>西方合盘</strong>
              <span>先提供独立入口与方法说明，避免知识树继续回落到案例中心总页。</span>
            </div>
          </div>
        </article>
      </section>
    </div>

    <template v-else>
      <div class="cp-entry-card">
        <div>
          <div class="cp-entry-title">八字兼容评分入口</div>
          <p class="cp-entry-desc">先做四柱层面的量化判断，再按需要切换到紫微或西方合盘。</p>
        </div>
        <div class="cp-entry-actions">
          <button class="cp-btn-secondary" @click="openPath('/ziwei')">查看紫微合盘入口</button>
          <button class="cp-btn-secondary" @click="openPath('/western')">查看西方合盘入口</button>
        </div>
      </div>

      <div class="cp-forms">
        <template v-for="(person, key) in [{ form: personA, label: '甲方（男/女）' }, { form: personB, label: '乙方（男/女）' }]" :key="key">
          <div class="cp-person-card" :class="key === 0 ? 'cp-card-a' : 'cp-card-b'">
            <h2 class="cp-person-title">{{ person.label }}</h2>
            <div class="cp-form-grid">
              <div class="cp-field">
                <label class="cp-label">出生日期</label>
                <input v-model="person.form.date" type="date" class="cp-input">
              </div>
              <div class="cp-field">
                <label class="cp-label">出生时间</label>
                <input v-model="person.form.time" type="time" class="cp-input">
              </div>
              <div class="cp-field">
                <label class="cp-label">经度</label>
                <input v-model="person.form.lon" type="number" step="0.01" class="cp-input">
              </div>
              <div class="cp-field">
                <label class="cp-label">时区</label>
                <input v-model="person.form.tz" type="text" class="cp-input" placeholder="Asia/Shanghai">
              </div>
            </div>
            <div class="cp-cities">
              <button
                v-for="c in CITIES"
                :key="c.label"
                class="cp-city-btn"
                @click="person.form.lon = c.lon; person.form.tz = c.tz"
              >{{ c.label }}</button>
            </div>
          </div>
        </template>
      </div>

      <div class="cp-actions">
        <button class="cp-btn-primary" :disabled="loading" @click="query">
          {{ loading ? '合盘计算中…' : '💑 开始合婚' }}
        </button>
      </div>

      <div v-if="error" class="cp-error">⚠️ {{ error }}</div>

      <template v-if="result">
        <div class="cp-score-banner" :style="{ borderColor: GRADE_COLOR[result.grade] }">
          <div class="cp-score-left">
            <div class="cp-score-num" :style="{ color: GRADE_COLOR[result.grade] }">{{ result.score }}</div>
            <div class="cp-score-unit">/ 100</div>
          </div>
          <div class="cp-score-center">
            <div class="cp-grade" :style="{ color: GRADE_COLOR[result.grade] }">{{ result.grade }}</div>
            <div class="cp-summary">{{ result.summary }}</div>
          </div>
          <div class="cp-score-bar-wrap">
            <div class="cp-score-track">
              <div class="cp-score-fill" :style="{ width: result.score + '%', background: GRADE_COLOR[result.grade] }"></div>
            </div>
            <div class="cp-grade-labels">
              <span>下下</span><span>下</span><span>中</span><span>上</span><span>上上</span>
            </div>
          </div>
        </div>

        <div class="cp-result-grid">
          <div class="cp-left-col">
            <div class="cp-radar-card">
              <h2 class="cp-sec-title">五行分布对比</h2>
              <svg viewBox="0 0 260 260" width="240" height="240">
                <path :d="radarGrid(130, 130, 90)" fill="none" stroke="var(--border)" stroke-width="0.8"></path>
                <g v-for="lbl in radarLabels(130, 130, 90)" :key="lbl.label">
                  <line x1="130" y1="130" :x2="lbl.x" :y2="lbl.y" stroke="var(--border)" stroke-width="0.5"></line>
                  <text :x="lbl.x" :y="lbl.y" text-anchor="middle" dominant-baseline="central" class="radar-label">{{ lbl.label }}</text>
                </g>
                <path :d="radarPath(result.person_a.weights, 1.0, 130, 130, 90)" fill="#ef444422" stroke="#ef4444" stroke-width="1.5"></path>
                <path :d="radarPath(result.person_b.weights, 1.0, 130, 130, 90)" fill="#3b82f622" stroke="#3b82f6" stroke-width="1.5"></path>
                <rect x="10" y="230" width="12" height="4" fill="#ef4444" rx="2"></rect>
                <text x="26" y="234" class="radar-legend">甲方</text>
                <rect x="70" y="230" width="12" height="4" fill="#3b82f6" rx="2"></rect>
                <text x="86" y="234" class="radar-legend">乙方</text>
              </svg>

              <table class="cp-wx-table">
                <thead>
                  <tr>
                    <th>五行</th>
                    <th style="color:#ef4444">甲方 %</th>
                    <th style="color:#3b82f6">乙方 %</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="[e, cn] in [['wood','木'],['fire','火'],['earth','土'],['metal','金'],['water','水']]" :key="e">
                    <td :style="{ color: ELEM_COLOR[e] }"><strong>{{ cn }}</strong></td>
                    <td class="cp-wx-val">{{ result.person_a.weights[e] ?? 0 }}%</td>
                    <td class="cp-wx-val">{{ result.person_b.weights[e] ?? 0 }}%</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div class="cp-pillars-card">
              <h2 class="cp-sec-title">四柱对照</h2>
              <table class="cp-pillars-table">
                <thead>
                  <tr>
                    <th>柱</th>
                    <th style="color:#ef4444">甲方</th>
                    <th style="color:#3b82f6">乙方</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(key, i) in PILLAR_KEYS" :key="key">
                    <td class="cp-pt-label">{{ PILLAR_LABELS[i] }}柱</td>
                    <td class="cp-pt-cell">
                      <span class="cp-gz" :style="{ color: ELEM_COLOR[STEM_ELEM_CH[result.person_a.pillars[key].stem] ?? ''] }">
                        {{ result.person_a.pillars[key].stem }}{{ result.person_a.pillars[key].branch }}
                      </span>
                      <span v-if="key === 'day'" class="cp-day-mark">日主</span>
                    </td>
                    <td class="cp-pt-cell">
                      <span class="cp-gz" :style="{ color: ELEM_COLOR[STEM_ELEM_CH[result.person_b.pillars[key].stem] ?? ''] }">
                        {{ result.person_b.pillars[key].stem }}{{ result.person_b.pillars[key].branch }}
                      </span>
                      <span v-if="key === 'day'" class="cp-day-mark">日主</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div class="cp-right-col">
            <h2 class="cp-sec-title">评分维度详情</h2>
            <div class="cp-details-list">
              <div v-for="d in result.details" :key="d.dimension" class="cp-detail-card">
                <div class="cp-detail-header">
                  <span class="cp-dim-name">{{ d.dimension }}</span>
                  <span class="cp-dim-level" :style="{ color: LEVEL_COLOR[d.level] }">{{ d.level }}</span>
                  <span class="cp-dim-score">{{ d.score }} / {{ d.max }}</span>
                </div>
                <div class="cp-dim-track">
                  <div class="cp-dim-fill" :style="{ width: (d.score / d.max * 100) + '%', background: LEVEL_COLOR[d.level] }"></div>
                </div>
                <p class="cp-dim-desc">{{ d.description }}</p>
              </div>
            </div>

            <div class="cp-day-summary">
              <div v-for="[label, ps] in ([['甲方', result.person_a], ['乙方', result.person_b]] as const)" :key="label" class="cp-day-row">
                <span class="cp-day-label">{{ label }} 日主：</span>
                <span class="cp-day-stem" :style="{ color: ELEM_COLOR[ps.day_elem] }">
                  {{ ps.day_stem }}（{{ ELEM_CN[ps.day_elem] ?? ps.day_elem }}）
                </span>
              </div>
            </div>
          </div>
        </div>
      </template>

      <div v-if="!result && !loading" class="cp-empty">
        <div class="cp-empty-icon">💑</div>
        <p>填写双方出生信息后点击「开始合婚」查看配对分析</p>
      </div>

      <!-- 关系合盘评分 (T1.3) -->
      <div class="cp-rel-section">
        <h2 class="cp-sec-title">🔗 关系合盘评分</h2>
        <p class="cp-rel-desc">基于案例 ID 计算双方综合关系得分，包含支持点、冲突点与建议。</p>
        <div class="cp-rel-form">
          <div class="cp-rel-inputs">
            <div class="cp-rel-field">
              <label class="cp-label">甲方案例 ID</label>
              <input class="cp-rel-input" v-model="relCaseA" placeholder="如 GT01 或数字 ID" />
            </div>
            <div class="cp-rel-field">
              <label class="cp-label">乙方案例 ID</label>
              <input class="cp-rel-input" v-model="relCaseB" placeholder="如 GT02" />
            </div>
            <div class="cp-rel-field">
              <label class="cp-label">关系类型</label>
              <select class="cp-rel-input" v-model="relType">
                <option v-for="opt in RELATION_TYPE_OPTIONS" :key="opt.value" :value="opt.value">
                  {{ opt.label }}
                </option>
              </select>
            </div>
            <button class="cp-rel-btn" :disabled="relLoading" @click="queryRelation">
              {{ relLoading ? '分析中…' : '开始分析' }}
            </button>
          </div>

          <div v-if="relError" class="cp-rel-error">{{ relError }}</div>

          <div v-if="relResult" class="cp-rel-result">
            <div class="cp-rel-score-row">
              <div class="cp-rel-names">
                <span class="cp-rel-name-a">{{ relResult.case_a.name }}</span>
                <span class="cp-rel-vs">♥</span>
                <span class="cp-rel-name-b">{{ relResult.case_b.name }}</span>
              </div>
              <div class="cp-rel-score">
                <span class="cp-rel-score-num">{{ relResult.result.compatibility_score }}</span>
                <span class="cp-rel-score-denom"> / 100</span>
              </div>
            </div>
            <div class="cp-rel-score-track">
              <div class="cp-rel-score-fill" :style="{ width: relResult.result.compatibility_score + '%' }"></div>
            </div>
            <p class="cp-rel-summary">{{ relResult.result.summary }}</p>

            <div class="cp-rel-points">
              <div class="cp-rel-col" v-if="relResult.result.support_points?.length">
                <h3 class="cp-rel-col-title cp-rel-support">❤️ 相得益彰</h3>
                <div v-for="p in relResult.result.support_points" :key="p.tag" class="cp-rel-point">
                  <span class="cp-rel-tag">{{ p.tag }}</span>
                  <span class="cp-rel-detail">{{ p.detail }}</span>
                </div>
              </div>
              <div class="cp-rel-col" v-if="relResult.result.conflict_points?.length">
                <h3 class="cp-rel-col-title cp-rel-conflict">⚠️ 在意事项</h3>
                <div v-for="p in relResult.result.conflict_points" :key="p.tag" class="cp-rel-point">
                  <span class="cp-rel-tag">{{ p.tag }}</span>
                  <span class="cp-rel-detail">{{ p.detail }}</span>
                </div>
              </div>
            </div>
            <p v-if="relResult.result.advice" class="cp-rel-advice">💡 {{ relResult.result.advice }}</p>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style src="./CompatibilityView.css" scoped />
