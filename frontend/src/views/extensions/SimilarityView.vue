<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import ResultStateCard from '@/components/new/ResultStateCard.vue'
import { useFushengReport } from '@/composables/useFushengReport'
import { useProfileStore } from '@/stores/profile'
import { buildProfileSignature } from '@/utils/buildChartRequests'
import { buildChartHash } from '@/utils/chartHash'
import { searchSimilar, indexChart, type SimilarResult } from '@/api/similarity'
import { buildChartRequestMeta } from '@/utils/buildChartRequests'
import '@/assets/fusheng-page.css'

const router = useRouter()
const profile = useProfileStore()
const { bazi, ziwei, loadReport } = useFushengReport()

const loading = ref(false)
const error = ref('')
const indexNotice = ref('')
const items = ref<SimilarResult[]>([])

function similarCaseLabel(item: SimilarResult, index: number): string {
  const label = item.case.source_label?.trim()
  if (label && label !== 'fusheng') return label
  const pattern = item.case.pattern_summary?.trim()
  if (pattern) return pattern.split(/[;；,，]/)[0]?.trim() || pattern
  const palace = item.case.life_palace_gz?.trim()
  if (palace) return `案例${index + 1} · ${palace}`
  return `相似案例 ${index + 1}`
}

async function runSearch() {
  loading.value = true
  error.value = ''
  indexNotice.value = ''
  items.value = []

  try {
    if (!bazi.value) {
      await loadReport()
    }
    const signature = buildProfileSignature(profile.asProfileData())
    const hash = await buildChartHash(signature)
    const data = profile.asProfileData()
    const meta = buildChartRequestMeta(data)
    const [datePart, timePart = '08:30:00'] = meta.normalizedBirthDt.split('T')
    const [year, month, day] = datePart.split('-').map(Number)
    const hour = Number(timePart.split(':')[0] ?? 8)

    try {
      await indexChart({
        chart_hash: hash,
        birth_year: year,
        birth_month: month,
        birth_day: day,
        birth_hour: hour,
        gender: data.gender === 'female' ? 'female' : data.gender === 'male' ? 'male' : 'unknown',
        wuxing_ju_name: ziwei.value?.wuxing_ju_name ?? '',
        life_palace_gz: ziwei.value?.life_palace_gz ?? '',
        patterns: bazi.value?.geju?.geju_name ? [{ name: bazi.value.geju.geju_name }] : [],
        source_label: profile.activeProfile?.label || 'fusheng',
      })
    } catch {
      // EXT-04：索引失败不阻断检索，但需可见提示
      indexNotice.value = '索引未更新（写入失败），下列结果可能基于旧库。'
    }

    items.value = await searchSimilar(hash, 8)
    if (!items.value.length) {
      error.value = '未找到相似命盘，索引库可能尚未收录当前盘。'
    }
  } catch {
    error.value = '相似盘检索失败，请稍后重试。'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void runSearch()
})
</script>

<template>
  <main class="fs-page similarity-page">
    <p class="fs-page-lead">基于档案 {{ profile.activeProfile?.label || '当前' }} 的命盘哈希检索库内相近案例。</p>
    <div class="fs-page-actions">
      <button class="fs-btn fs-btn--ghost" @click="router.push('/extensions')">返回工具箱</button>
      <button class="fs-btn fs-btn--primary" :disabled="loading" @click="runSearch">重新检索</button>
    </div>

    <ResultStateCard v-if="loading" compact title="检索中" message="正在比对命盘哈希…" />
    <template v-else>
      <p v-if="indexNotice" class="fs-hint" data-testid="similarity-index-notice">{{ indexNotice }}</p>
      <ResultStateCard v-if="error" severity="error" title="检索结果" :message="error" />
    </template>

    <section v-if="items.length" class="fs-card">
      <h2>相似案例（{{ items.length }}）</h2>
      <table class="similar-table">
        <thead>
          <tr><th>案例</th><th>相似度</th><th>五行局</th><th>命宫</th></tr>
        </thead>
        <tbody>
          <tr v-for="(item, index) in items" :key="item.case.id">
            <td :title="item.case.chart_hash">{{ similarCaseLabel(item, index) }}</td>
            <td>{{ Math.round(item.similarity * 100) }}%</td>
            <td>{{ item.case.wuxing_ju_name || ziwei?.wuxing_ju_name || '—' }}</td>
            <td>{{ item.case.life_palace_gz || ziwei?.life_palace_gz || '—' }}</td>
          </tr>
        </tbody>
      </table>
      <p v-if="bazi?.geju?.geju_name" class="hint">当前格局：{{ bazi.geju.geju_name }}</p>
    </section>
  </main>
</template>

<style scoped>
.similarity-page { gap: 14px; }

.similar-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.similar-table th,
.similar-table td {
  border: 1px solid var(--border);
  padding: 8px 10px;
  text-align: left;
}

.similar-table th {
  background: var(--inset-tint);
}
</style>
