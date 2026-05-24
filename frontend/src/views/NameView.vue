<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useProfileStore } from '@/stores/profile'
import { analyzeName } from '@/api/name'
import type { NameAnalysisResponse } from '@/api/name'

const route = useRoute()
const profile   = useProfileStore()

// 姓名分析表单
const analyzeSurname = ref('')
const analyzeGivenName = ref('')
const analyzeResult = ref<NameAnalysisResponse | null>(null)
const analyzeLoading = ref(false)
const analyzeError = ref('')

const WX_COLORS: Record<string, string> = {
  '木': 'var(--wx-wood)', '火': 'var(--wx-fire)', '土': 'var(--wx-earth)',
  '金': 'var(--wx-metal)', '水': 'var(--wx-water)',
}

// URL 参数预填
onMounted(() => {
  const q = route.query
  if (q.surname) analyzeSurname.value = String(q.surname)
  // 从个人信息 store 预填姓氏
  if (profile.surname && !analyzeSurname.value) {
    analyzeSurname.value = profile.surname
  }
})

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

    <!-- ── 姓名分析 ────────────────────────────────────────── -->
    <section class="tab-panel">
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

/* 打印样式 */
@media print {
  .no-print { display: none !important; }
  .tabs { display: none !important; }
  .form-card { display: none !important; }
  .page-title { font-size: 20pt; }
  .result-card { box-shadow: none; border: 1px solid #ccc; }
  .grid-5 { grid-template-columns: repeat(5, 1fr); }
}

</style>
