<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import ResultStateCard from '@/components/new/ResultStateCard.vue'
import { useFushengReport } from '@/composables/useFushengReport'
import { getZeriPurposes, getZeriRecommend, type ZeriMonthResponse } from '@/api/zeri'
import '@/assets/fusheng-page.css'

const router = useRouter()
const { ziwei, loadZiwei, loadingZiwei } = useFushengReport()

const now = new Date()
const year = ref(now.getFullYear())
const month = ref(now.getMonth() + 1)
const purpose = ref('marriage')
const purposes = ref<Record<string, string>>({})
const loading = ref(false)
const error = ref('')
const result = ref<ZeriMonthResponse | null>(null)

const lifePalaceBranch = computed(() => {
  const gz = ziwei.value?.life_palace_gz || ''
  return gz.length >= 2 ? gz.slice(-1) : ''
})

const wuxingJuName = computed(() => ziwei.value?.wuxing_ju_name || '')

async function loadPurposes() {
  try {
    purposes.value = await getZeriPurposes()
  } catch {
    purposes.value = { marriage: '婚嫁', move: '搬家', business: '开业' }
  }
}

async function runRecommend() {
  if (!lifePalaceBranch.value || !wuxingJuName.value) {
    error.value = '请先完成紫微排盘（需命宫地支与五行局）。'
    return
  }

  loading.value = true
  error.value = ''
  result.value = null

  try {
    result.value = await getZeriRecommend({
      year: year.value,
      month: month.value,
      life_palace_branch: lifePalaceBranch.value,
      wuxing_ju_name: wuxingJuName.value,
      purpose: purpose.value,
    })
  } catch {
    error.value = '择日推荐失败，请稍后重试。'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadPurposes()
  if (!ziwei.value) {
    await loadZiwei()
  }
  if (ziwei.value) {
    await runRecommend()
  }
})
</script>

<template>
  <main class="fs-page zeri-page">
    <p class="fs-page-lead">命宫 {{ ziwei?.life_palace_gz || '待排盘' }} · {{ wuxingJuName || '五行局待计算' }}</p>
    <div class="fs-page-actions">
      <button class="fs-btn fs-btn--ghost" @click="router.push('/extensions')">返回工具箱</button>
    </div>

    <ResultStateCard
      v-if="loadingZiwei && !ziwei"
      compact
      title="载入紫微盘"
      message="择日需命宫与五行局，正在排盘…"
    />

    <section v-else class="fs-card">
      <h2>查询条件</h2>
      <div class="field-grid">
        <label class="field">
          <span>年份</span>
          <input v-model.number="year" type="number" min="1900" max="2100" />
        </label>
        <label class="field">
          <span>月份</span>
          <input v-model.number="month" type="number" min="1" max="12" />
        </label>
        <label class="field">
          <span>用途</span>
          <select v-model="purpose" data-testid="zeri-purpose">
            <option v-for="(label, key) in purposes" :key="key" :value="key">{{ label }}</option>
          </select>
        </label>
      </div>
      <button class="fs-btn fs-btn--primary" :disabled="loading" data-testid="zeri-run" @click="runRecommend">
        {{ loading ? '查询中…' : '获取择日推荐' }}
      </button>
    </section>

    <ResultStateCard v-if="error" title="择日查询" :message="error" />

    <section v-if="result" class="fs-card">
      <h2>{{ result.year }} 年 {{ result.month }} 月 · {{ result.purpose_label }}</h2>
      <p class="hint">命宫支 {{ result.life_palace_branch }} · {{ result.wuxing_ju_name }}</p>
      <h3>推荐吉日</h3>
      <ul v-if="result.recommended?.length" class="zeri-list">
        <li v-for="day in result.recommended" :key="`rec-${day.day}`">
          <strong>{{ day.day }} 日 {{ day.ganzhi }}</strong>
          <span>{{ day.level }} · {{ day.score }} 分</span>
          <p>{{ day.reason }}</p>
        </li>
      </ul>
      <p v-else class="hint">本月暂无高分推荐日。</p>
    </section>
  </main>
</template>

<style scoped>
.zeri-page { gap: 14px; }

.field-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  margin-bottom: 12px;
}

.field {
  display: grid;
  gap: 6px;
  font-size: 13px;
}

.field input,
.field select {
  padding: 8px 10px;
  border: 1px solid var(--border);
  border-radius: 10px;
}

.zeri-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 10px;
}

.zeri-list li {
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--surface);
}

.zeri-list li span {
  display: block;
  font-size: 12px;
  color: var(--text-2);
}

.zeri-list li p {
  margin: 6px 0 0;
  font-size: 13px;
  color: var(--text-2);
  line-height: 1.6;
}
</style>
