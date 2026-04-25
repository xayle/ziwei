<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useNameStore } from '@/stores/name'
import { useProfileStore } from '@/stores/profile'
import { analyzeName, suggestNames } from '@/api/name'
import type { NameAnalysisResponse, NameSuggestResponse } from '@/api/name'

const route = useRoute()
const nameStore = useNameStore()
const profile   = useProfileStore()

// 当前 Tab
const activeTab = ref<'analyze' | 'suggest'>('analyze')

// 姓名分析表单
const analyzeSurname = ref('')
const analyzeGivenName = ref('')
const analyzeResult = ref<NameAnalysisResponse | null>(null)
const analyzeLoading = ref(false)
const analyzeError = ref('')

// 改名建议表单
const suggestSurname = ref('')
const suggestElements = ref<string[]>([])
const suggestTopN = ref(10)
const suggestMinScore = ref(60)
const suggestResult = ref<NameSuggestResponse | null>(null)
const suggestLoading = ref(false)
const suggestError = ref('')

const WX_ELEMENTS = ['木', '火', '土', '金', '水']
const WX_COLORS: Record<string, string> = {
  '木': 'var(--wx-wood)', '火': 'var(--wx-fire)', '土': 'var(--wx-earth)',
  '金': 'var(--wx-metal)', '水': 'var(--wx-water)',
}

// URL 参数预填
onMounted(() => {
  const q = route.query
  if (q.surname) analyzeSurname.value = String(q.surname)
  if (q.surname) suggestSurname.value = String(q.surname)
  if (q.elements) {
    suggestElements.value = String(q.elements).split(',').filter(e => WX_ELEMENTS.includes(e))
  }
  // 从 nameStore 预填（八字联动）
  if (nameStore.prefillSurname) {
    suggestSurname.value = nameStore.prefillSurname
    if (nameStore.prefillElements.length) suggestElements.value = nameStore.prefillElements
    activeTab.value = 'suggest'
    nameStore.setPrefill('', [])
  } else if (profile.surname && !analyzeSurname.value) {
    // 从个人信息 store 预填姓氏（若没有通过 URL 或 nameStore 传入）
    analyzeSurname.value = profile.surname
    suggestSurname.value = profile.surname
  }
})

function toggleElement(el: string) {
  const idx = suggestElements.value.indexOf(el)
  if (idx >= 0) suggestElements.value.splice(idx, 1)
  else suggestElements.value.push(el)
}

async function doAnalyze() {
  if (!analyzeSurname.value || !analyzeGivenName.value) return
  analyzeLoading.value = true
  analyzeError.value = ''
  try {
    analyzeResult.value = await analyzeName({
      surname: analyzeSurname.value,
      given_name: analyzeGivenName.value,
    })
  } catch (e: unknown) {
    analyzeError.value = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? '分析失败，请稍后重试'
  } finally {
    analyzeLoading.value = false
  }
}

async function doSuggest() {
  if (!suggestSurname.value) return
  suggestLoading.value = true
  suggestError.value = ''
  try {
    suggestResult.value = await suggestNames({
      surname: suggestSurname.value,
      preferred_elements: suggestElements.value.length ? suggestElements.value : undefined,
      top_n: suggestTopN.value,
      min_score: suggestMinScore.value,
    })
  } catch (e: unknown) {
    suggestError.value = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? '建议失败，请稍后重试'
  } finally {
    suggestLoading.value = false
  }
}

function useForAnalyze(givenName: string) {
  analyzeSurname.value = suggestSurname.value
  analyzeGivenName.value = givenName
  activeTab.value = 'analyze'
}

function scoreClass(score: number): string {
  if (score >= 85) return 'score-excellent'
  if (score >= 70) return 'score-good'
  if (score >= 55) return 'score-ok'
  return 'score-poor'
}

// 五格占卡片颜色类
function gridScoreClass(hint: string): string {
  if (/大吉|大好/.test(hint))  return 'grid-great'
  if (/吉祥|吉鑭|吉/.test(hint)) return 'grid-good'
  if (/大凶|凶险/.test(hint))  return 'grid-bad'
  if (/凶|不吉|警/.test(hint))  return 'grid-warn'
  return ''
}

function fiveGrids(r: NameAnalysisResponse) {
  return [
    { label: '天格', num: r.tianke.number, hint: r.tianke.lucky, element: r.tianke.element, desc: r.tianke.desc, score: r.tianke.score },
    { label: '人格', num: r.renke.number,  hint: r.renke.lucky,  element: r.renke.element,  desc: r.renke.desc,  score: r.renke.score },
    { label: '地格', num: r.dike.number,   hint: r.dike.lucky,   element: r.dike.element,   desc: r.dike.desc,   score: r.dike.score },
    { label: '外格', num: r.waike.number,  hint: r.waike.lucky,  element: r.waike.element,  desc: r.waike.desc,  score: r.waike.score },
    { label: '总格', num: r.zonge.number,  hint: r.zonge.lucky,  element: r.zonge.element,  desc: r.zonge.desc,  score: r.zonge.score },
  ]
}

function exportPDF() {
  window.print()
}
</script>

<template>
  <div class="wrap name-view">
    <h1 class="page-title">姓名学</h1>

    <!-- Tab 切换 -->
    <div class="tabs">
      <button :class="['tab-btn', { active: activeTab === 'analyze' }]"
              @click="activeTab = 'analyze'">姓名分析</button>
      <button :class="['tab-btn', { active: activeTab === 'suggest' }]"
              @click="activeTab = 'suggest'">改名建议</button>
    </div>

    <!-- ── 姓名分析 Tab ────────────────────────────────────────── -->
    <section v-if="activeTab === 'analyze'" class="tab-panel">
      <form class="card form-card" @submit.prevent="doAnalyze">
        <div class="form-row">
          <label>姓氏</label>
          <input v-model="analyzeSurname" placeholder="张" maxlength="3" required />
        </div>
        <div class="form-row">
          <label>名字</label>
          <input v-model="analyzeGivenName" placeholder="伟" maxlength="4" required />
        </div>
        <button type="submit" class="btn-primary" :disabled="analyzeLoading">
          {{ analyzeLoading ? '分析中…' : '开始分析' }}
        </button>
        <p v-if="analyzeError" class="error-msg">{{ analyzeError }}</p>
      </form>

      <!-- 分析结果 -->
      <div v-if="analyzeResult" class="card result-card">
        <div class="result-header">
          <span class="full-name">{{ analyzeResult.surname }}{{ analyzeResult.given_name }}</span>
          <span class="score-badge" :class="scoreClass(analyzeResult.overall_score)">
            综合 {{ analyzeResult.overall_score }}分
          </span>
        </div>

        <!-- 五格数理 -->
        <div class="grid-5">
          <div v-for="(item, i) in fiveGrids(analyzeResult)" :key="i"
               class="grid-item" :class="gridScoreClass(item.hint)">
            <span class="grid-label">{{ item.label }}</span>
            <span class="grid-num">{{ item.num }}</span>
            <span class="grid-hint">{{ item.hint }}</span>
            <span v-if="item.element" class="grid-element" :style="{ color: WX_COLORS[item.element] }">{{ item.element }}</span>
            <span v-if="item.desc" class="grid-desc">{{ item.desc }}</span>
          </div>
        </div>

        <!-- 三才图案 -->
        <div class="sancai-row">
          <span class="sancai-label">三才：</span>
          <span class="sancai-pattern">{{ analyzeResult.sancai.pattern }}</span>
          <span class="sancai-score">{{ analyzeResult.sancai.score }}分</span>
          <span class="sancai-lucky">{{ analyzeResult.sancai.lucky }}</span>
        </div>
        <p v-if="analyzeResult.sancai.desc" class="sancai-desc">{{ analyzeResult.sancai.desc }}</p>
        <!-- 摘要 -->
        <p class="summary-text">{{ analyzeResult.summary }}</p>
        <p v-if="analyzeResult.algorithm_version" class="algo-ver">算法版本：{{ analyzeResult.algorithm_version }}</p>

        <!-- 导出按钮 -->
        <div class="export-row no-print">
          <button class="btn-export" @click="exportPDF">⬇ 导出 PDF 报告</button>
        </div>
      </div>
    </section>

    <!-- ── 改名建议 Tab ────────────────────────────────────────── -->
    <section v-if="activeTab === 'suggest'" class="tab-panel">
      <form class="card form-card" @submit.prevent="doSuggest">
        <div class="form-row">
          <label>姓氏</label>
          <input v-model="suggestSurname" placeholder="张" maxlength="3" required />
        </div>
        <div class="form-row">
          <label>偏好五行</label>
          <div class="element-chips">
            <button v-for="el in WX_ELEMENTS" :key="el" type="button"
                    :class="['chip', { selected: suggestElements.includes(el) }]"
                    :style="suggestElements.includes(el) ? { background: WX_COLORS[el], color: '#fff' } : {}"
                    @click="toggleElement(el)">{{ el }}</button>
          </div>
        </div>
        <div class="form-row">
          <label>返回数量</label>
          <input type="number" v-model.number="suggestTopN" min="1" max="20" />
        </div>
        <div class="form-row">
          <label>最低分数</label>
          <input type="number" v-model.number="suggestMinScore" min="0" max="100" />
        </div>
        <button type="submit" class="btn-primary" :disabled="suggestLoading">
          {{ suggestLoading ? '搜索中…' : '生成建议名' }}
        </button>
        <p v-if="suggestError" class="error-msg">{{ suggestError }}</p>
      </form>

      <!-- 建议结果 -->
      <div v-if="suggestResult" class="suggest-results">
        <p class="suggest-meta">
          共评选 {{ suggestResult.total_candidates_evaluated.toLocaleString() }} 个候选，
          推荐 {{ suggestResult.suggestions.length }} 个
        </p>
        <div class="suggest-grid">
          <div v-for="s in suggestResult.suggestions" :key="s.given_name"
               class="card suggest-card" @click="useForAnalyze(s.given_name)">
            <div class="suggest-name">{{ suggestSurname }}{{ s.given_name }}</div>
            <div class="suggest-score-row">
              <span class="score-badge" :class="scoreClass(s.overall_score)">{{ s.overall_score }}分</span>
              <div class="element-badges">
                <span v-for="el in s.element_composition" :key="el"
                      class="el-badge" :style="{ background: WX_COLORS[el] }">{{ el }}</span>
              </div>
            </div>
            <p class="suggest-summary">{{ s.summary }}</p>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.name-view { padding-bottom: var(--sp-8); }

.page-title {
  font-size: var(--fs-2xl);
  font-weight: 700;
  color: var(--text);
  margin-bottom: var(--sp-5);
  font-family: var(--font-cn);
}

/* Tabs */
.tabs {
  display: flex;
  gap: var(--sp-2);
  margin-bottom: var(--sp-5);
  border-bottom: 2px solid var(--border);
  padding-bottom: -2px;
}
.tab-btn {
  padding: 8px 20px;
  border: none;
  background: none;
  cursor: pointer;
  font-size: var(--fs-md);
  color: var(--text-2);
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  transition: color var(--dur-fast), border-color var(--dur-fast);
}
.tab-btn.active { color: var(--accent); border-bottom-color: var(--accent); font-weight: 600; }
.tab-btn:hover { color: var(--text); }

/* Card */
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: var(--sp-5);
  box-shadow: var(--shadow);
}

/* Form */
.form-card { max-width: 480px; display: flex; flex-direction: column; gap: var(--sp-4); }
.form-row { display: flex; align-items: center; gap: var(--sp-3); }
.form-row label { width: 70px; font-size: var(--fs-md); color: var(--text-2); flex-shrink: 0; }
.form-row input[type="text"],
.form-row input:not([type]) {
  flex: 1; padding: 8px 12px; border: 1px solid var(--border-md);
  border-radius: var(--radius-sm); font-size: var(--fs-md);
  transition: border-color var(--dur-fast);
}
.form-row input:focus { outline: none; border-color: var(--accent); }
.form-row input[type="number"] {
  width: 80px; padding: 8px 12px; border: 1px solid var(--border-md);
  border-radius: var(--radius-sm);
}

.btn-primary {
  align-self: flex-start;
  padding: 9px 22px; background: var(--accent); color: #fff;
  border: none; border-radius: var(--radius-sm);
  font-size: var(--fs-md); font-weight: 600; cursor: pointer;
  transition: background var(--dur-fast);
}
.btn-primary:hover { background: var(--accent-dark); }
.btn-primary:disabled { opacity: .6; cursor: not-allowed; }

.error-msg { color: var(--danger-dark); font-size: var(--fs-sm); }

/* Result */
.result-card { margin-top: var(--sp-5); }
.result-header { display: flex; align-items: center; gap: var(--sp-4); margin-bottom: var(--sp-4); }
.full-name { font-size: var(--fs-2xl); font-weight: 700; font-family: var(--font-cn); }

.score-badge {
  padding: 3px 10px; border-radius: 20px; font-size: var(--fs-sm); font-weight: 600;
}
.score-excellent { background: #dcfce7; color: #15803d; }
.score-good      { background: #dbeafe; color: #1d4ed8; }
.score-ok        { background: #fef9c3; color: #a16207; }
.score-poor      { background: #fee2e2; color: #dc2626; }

/* 五格表格 */
.grid-5 { display: grid; grid-template-columns: repeat(5, 1fr); gap: var(--sp-3); margin-bottom: var(--sp-4); }
.grid-item {
  text-align: center; padding: var(--sp-3);
  background: var(--surface-2); border-radius: var(--radius-sm);
  border: 1.5px solid transparent; transition: border-color .15s;
}
.grid-item.grid-great { border-color: #16a34a; background: #f0fdf4; }
.grid-item.grid-good  { border-color: #3b82f6; background: #eff6ff; }
.grid-item.grid-warn  { border-color: #f59e0b; background: #fffbeb; }
.grid-item.grid-bad   { border-color: #ef4444; background: #fff1f2; }
.grid-label { display: block; font-size: var(--fs-xs); color: var(--text-3); margin-bottom: 2px; }
.grid-num { display: block; font-size: var(--fs-xl); font-weight: 700; color: var(--accent); }
.grid-hint { display: block; font-size: var(--fs-xs); color: var(--text-2); margin-top: 2px; }
.grid-element { display: block; font-size: var(--fs-xs); font-weight: 600; margin-top: 2px; }
.grid-desc { display: block; font-size: var(--fs-xs); color: var(--text-3); margin-top: 2px; line-height: 1.4; }

/* 三才 */
.sancai-row { display: flex; align-items: center; gap: var(--sp-3); flex-wrap: wrap; margin-bottom: var(--sp-2); }
.sancai-label { font-size: var(--fs-sm); color: var(--text-2); }
.sancai-pattern { font-size: var(--fs-lg); font-weight: 600; font-family: var(--font-cn); }
.sancai-score { font-size: var(--fs-sm); color: var(--text-2); }
.sancai-lucky { font-size: var(--fs-sm); padding: 1px 8px; border-radius: 10px; background: var(--accent-soft); color: var(--accent); font-weight: 600; }
.sancai-desc { font-size: var(--fs-sm); color: var(--text-2); margin-bottom: var(--sp-4); line-height: 1.6; }

.summary-text { font-size: var(--fs-md); color: var(--text); line-height: 1.7; }
.algo-ver { font-size: var(--fs-xs); color: var(--text-3); margin-top: var(--sp-2); }

/* 导出按钮 */
.export-row { margin-top: var(--sp-5); padding-top: var(--sp-4); border-top: 1px solid var(--border); }
.btn-export {
  padding: 9px 20px; background: var(--surface); color: var(--accent);
  border: 1.5px solid var(--accent); border-radius: var(--radius-sm);
  font-size: var(--fs-md); font-weight: 600; cursor: pointer;
  transition: all var(--dur-fast);
}
.btn-export:hover { background: var(--accent); color: #fff; }

/* Element chips */
.element-chips { display: flex; gap: var(--sp-2); flex-wrap: wrap; }
.chip {
  padding: 5px 14px; border-radius: 20px;
  border: 1px solid var(--border-md); background: var(--surface);
  font-size: var(--fs-sm); cursor: pointer;
  transition: all var(--dur-fast);
}
.chip:hover { border-color: var(--accent); color: var(--accent); }
.chip.selected { border-color: transparent; font-weight: 600; }

/* 打印样式 */
@media print {
  .no-print { display: none !important; }
  .tabs { display: none !important; }
  .form-card { display: none !important; }
  .page-title { font-size: 20pt; }
  .result-card { box-shadow: none; border: 1px solid #ccc; }
  .grid-5 { grid-template-columns: repeat(5, 1fr); }
}

/* Suggest results */
.suggest-meta { font-size: var(--fs-sm); color: var(--text-3); margin-bottom: var(--sp-4); }
.suggest-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: var(--sp-4);
}
.suggest-card {
  cursor: pointer;
  transition: transform var(--dur-fast), box-shadow var(--dur-fast);
}
.suggest-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-lg); }
.suggest-name { font-size: var(--fs-xl); font-weight: 700; font-family: var(--font-cn); margin-bottom: var(--sp-2); }
.suggest-score-row { display: flex; align-items: center; gap: var(--sp-2); margin-bottom: var(--sp-2); flex-wrap: wrap; }
.suggest-summary { font-size: var(--fs-xs); color: var(--text-2); line-height: 1.5; }
</style>
