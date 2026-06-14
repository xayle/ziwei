<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useProfileStore } from '@/stores/profile'
import { analyzeName, suggestNames } from '@/api/name'
import type { NameAnalysisResponse, NameSuggestResponse, NameSuggestionItem } from '@/api/name'

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

// ── 起名推荐（含五行用神过滤）──────────────────────────────
const suggestSurname    = ref('')
const suggestLength     = ref<1 | 2>(2)
const suggestTopN       = ref(10)
const suggestMinScore   = ref(70)
const suggestElements   = ref<string[]>([])
const suggestResult     = ref<NameSuggestResponse | null>(null)
const suggestLoading    = ref(false)
const suggestError      = ref('')

const WX_ELEMENT_OPTIONS = ['木', '火', '土', '金', '水']

function toggleElement(el: string) {
  const idx = suggestElements.value.indexOf(el)
  if (idx >= 0) {
    suggestElements.value.splice(idx, 1)
  } else {
    suggestElements.value.push(el)
  }
}

async function doSuggest() {
  if (!suggestSurname.value.trim()) { suggestError.value = '请填写姓氏'; return }
  suggestLoading.value = true
  suggestError.value = ''
  suggestResult.value = null
  try {
    suggestResult.value = await suggestNames({
      surname: suggestSurname.value.trim(),
      name_length: suggestLength.value,
      preferred_elements: suggestElements.value.length ? suggestElements.value : undefined,
      top_n: suggestTopN.value,
      min_score: suggestMinScore.value,
    })
  } catch (e: unknown) {
    suggestError.value = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? '推荐失败，请稍后重试'
  } finally {
    suggestLoading.value = false
  }
}

function elemColor(el: string) {
  return WX_COLORS[el] ?? 'var(--text-2)'
}

function copyName(item: NameSuggestionItem) {
  const text = `${suggestResult.value?.surname ?? ''}${item.given_name}`
  navigator.clipboard?.writeText(text).catch(() => {})
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

    <!-- ── 起名推荐（含五行用神过滤）─────────────────────── -->
    <section class="tab-panel suggest-section">
      <h2 class="section-title">🌿 起名推荐</h2>
      <form class="card form-card suggest-form" @submit.prevent="doSuggest">
        <div class="form-row">
          <label>姓氏</label>
          <input v-model="suggestSurname" placeholder="张" maxlength="3" required />
        </div>
        <div class="form-row">
          <label>字数</label>
          <label class="radio-opt"><input type="radio" v-model="suggestLength" :value="1" /> 单字名</label>
          <label class="radio-opt"><input type="radio" v-model="suggestLength" :value="2" /> 双字名</label>
        </div>
        <div class="form-row">
          <label>最低分</label>
          <input type="number" min="0" max="100" v-model.number="suggestMinScore" style="width:80px" />
          <span class="form-hint">建议 70 以上</span>
        </div>
        <div class="form-row">
          <label>候选数</label>
          <input type="number" min="1" max="50" v-model.number="suggestTopN" style="width:80px" />
        </div>
        <!-- 五行用神过滤 -->
        <div class="form-row wx-filter-row">
          <label>用神五行</label>
          <div class="wx-chips">
            <button
              v-for="el in WX_ELEMENT_OPTIONS"
              :key="el"
              type="button"
              class="wx-chip"
              :class="{ selected: suggestElements.includes(el) }"
              :style="suggestElements.includes(el) ? { background: elemColor(el), borderColor: elemColor(el), color: '#fff' } : {}"
              @click="toggleElement(el)"
            >{{ el }}</button>
          </div>
          <span class="form-hint">不选则不限</span>
        </div>
        <button type="submit" class="btn-primary" :disabled="suggestLoading">
          {{ suggestLoading ? '生成中…' : '生成候选名' }}
        </button>
        <p v-if="suggestError" class="error-msg">{{ suggestError }}</p>
      </form>

      <!-- 推荐结果 -->
      <div v-if="suggestResult" class="card suggest-result-card">
        <div class="suggest-meta">
          <span class="suggest-surname">「{{ suggestResult.surname }}」</span>
          <span class="suggest-len">{{ suggestResult.name_length === 1 ? '单字名' : '双字名' }}</span>
          <span v-if="suggestResult.preferred_elements?.length" class="suggest-elements">
            用神：<span v-for="e in suggestResult.preferred_elements" :key="e" :style="{ color: elemColor(e) }">{{ e }} </span>
          </span>
          <span class="suggest-total">共评估 {{ suggestResult.total_candidates_evaluated }} 个候选</span>
        </div>

        <div v-if="!suggestResult.suggestions.length" class="suggest-empty">
          未找到符合条件的名字，尝试降低最低分或取消五行限制。
        </div>
        <div v-else class="suggest-list">
          <div
            v-for="(item, i) in suggestResult.suggestions"
            :key="item.given_name"
            class="suggest-item"
          >
            <span class="suggest-rank">{{ i + 1 }}</span>
            <span class="suggest-name">{{ suggestResult.surname }}{{ item.given_name }}</span>
            <span class="suggest-score score-badge" :class="scoreClass(item.overall_score)">{{ item.overall_score }}分</span>
            <div class="suggest-elements-row">
              <span
                v-for="el in item.element_composition"
                :key="el"
                class="wx-tag"
                :style="{ color: elemColor(el) }"
              >{{ el }}</span>
            </div>
            <span class="suggest-sancai">三才 {{ item.sancai_pattern }}</span>
            <p class="suggest-summary">{{ item.summary }}</p>
            <button class="btn-copy" @click="copyName(item)" title="复制姓名">📋</button>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style src="./NameView.css" scoped />
