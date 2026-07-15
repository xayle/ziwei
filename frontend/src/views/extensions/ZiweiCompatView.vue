<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import ResultStateCard from '@/components/new/ResultStateCard.vue'
import { useProfileStore } from '@/stores/profile'
import { ziweiCompatibility, type ZiweiCompatibilityResponse } from '@/api/ziwei'
import '@/assets/fusheng-page.css'

const router = useRouter()
const profile = useProfileStore()

const partnerBirthDt = ref('')
const partnerGender = ref<'男' | '女'>('女')
const partnerLon = ref<number | null>(profile.lon ?? 116.41)
const loading = ref(false)
const error = ref('')
const result = ref<ZiweiCompatibilityResponse | null>(null)

const selfGenderLabel = computed(() => (
  profile.gender === 'female' ? '女' : profile.gender === 'male' ? '男' : '—'
))

function parseBirthParts(dt: string) {
  const normalized = dt.trim().replace(' ', 'T')
  const [datePart, timePart = '12:00'] = normalized.split('T')
  const [year, month, day] = datePart.split('-').map(Number)
  const [hour, minute = 0] = timePart.split(':').map(Number)
  return { year, month, day, hour, minute }
}

async function runCompat() {
  if (!profile.birthDt?.trim()) {
    error.value = '请先补全当前档案出生时间。'
    return
  }
  if (!partnerBirthDt.value.trim()) {
    error.value = '请填写对方出生时间。'
    return
  }
  if (profile.gender !== 'male' && profile.gender !== 'female') {
    error.value = '请先在档案中设置甲方性别。'
    return
  }
  if (!Number.isFinite(partnerLon.value)) {
    error.value = '请填写对方经度（勿默认沿用甲方而不知情）。'
    return
  }

  loading.value = true
  error.value = ''
  result.value = null

  try {
    const self = parseBirthParts(profile.birthDt)
    const partner = parseBirthParts(partnerBirthDt.value)
    result.value = await ziweiCompatibility({
      person_a: {
        year: self.year,
        month: self.month,
        day: self.day,
        hour: self.hour,
        minute: self.minute,
        gender: profile.gender === 'female' ? '女' : '男',
        longitude: profile.lon,
        year_divide: profile.yearDivide ?? 'lichun',
        day_divide: profile.dayDivide ?? 'solar_next',
        youbi_method: profile.ziweiYoubiMethod ?? 'month',
        brightness_method: profile.ziweiBrightnessMethod ?? 'standard',
      },
      person_b: {
        year: partner.year,
        month: partner.month,
        day: partner.day,
        hour: partner.hour,
        minute: partner.minute,
        gender: partnerGender.value,
        longitude: partnerLon.value!,
      },
    })
  } catch (e: unknown) {
    const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    error.value = typeof detail === 'string' ? detail : '紫微合盘分析失败，请稍后重试。'
  } finally {
    loading.value = false
  }
}

const dimensionRows = computed(() => {
  const dims = result.value?.dimensions ?? []
  return dims.map((d) => ({
    name: (d as { dimension?: string; name?: string }).dimension
      ?? (d as { dimension?: string; name?: string }).name
      ?? '维度',
    score: d.score,
    max: d.max_score,
    desc: (d as { description?: string; desc?: string }).description
      ?? (d as { description?: string; desc?: string }).desc
      ?? '',
  }))
})
</script>

<template>
  <main class="fs-page ziwei-compat-page">
    <p class="fs-page-lead">以当前档案为甲方，输入对方出生信息进行命宫/五行/夫妻宫等维度合盘（启发式层，仅供参考）。</p>
    <div class="fs-page-actions">
      <button class="fs-btn fs-btn--ghost" @click="router.push('/extensions')">返回工具箱</button>
      <button class="fs-btn fs-btn--ghost" @click="router.push('/extensions/compat')">八字合婚</button>
    </div>

    <section class="fs-card">
      <h2>对方信息</h2>
      <div class="field-grid">
        <label class="field field--wide">
          <span>出生时间</span>
          <input v-model="partnerBirthDt" type="datetime-local" data-testid="ziwei-compat-partner-birth" />
        </label>
        <label class="field">
          <span>性别</span>
          <select v-model="partnerGender">
            <option value="女">女</option>
            <option value="男">男</option>
          </select>
        </label>
        <label class="field">
          <span>对方经度</span>
          <input v-model.number="partnerLon" type="number" step="0.0001" data-testid="ziwei-compat-partner-lon" />
        </label>
      </div>
      <p class="hint">
        甲方：{{ profile.birthDt?.replace('T', ' ') || '未填写' }} · {{ selfGenderLabel }}
        · 对方经度默认与甲方相同，请按对方出生地修改。
      </p>
      <button class="fs-btn fs-btn--primary" :disabled="loading" data-testid="ziwei-compat-run" @click="runCompat">
        {{ loading ? '分析中…' : '开始紫微合盘' }}
      </button>
    </section>

    <ResultStateCard v-if="error" title="合盘失败" :message="error" />
    <section v-if="result" class="fs-card" data-testid="ziwei-compat-result">
      <h2>合盘结果</h2>
      <p class="compat-score">
        综合 <strong>{{ result.total_score }}</strong> / {{ result.max_score }} · {{ result.level }}
      </p>
      <p>{{ result.summary }}</p>
      <table v-if="dimensionRows.length" class="compat-table">
        <thead>
          <tr><th>维度</th><th>得分</th><th>说明</th></tr>
        </thead>
        <tbody>
          <tr v-for="row in dimensionRows" :key="row.name">
            <td>{{ row.name }}</td>
            <td>{{ row.score }}/{{ row.max }}</td>
            <td>{{ row.desc }}</td>
          </tr>
        </tbody>
      </table>
      <div v-if="result.harmony_points?.length" class="compat-block">
        <h3>相合点</h3>
        <ul><li v-for="(item, idx) in result.harmony_points" :key="`h-${idx}`">{{ item }}</li></ul>
      </div>
      <div v-if="result.conflict_points?.length" class="compat-block">
        <h3>冲突点</h3>
        <ul><li v-for="(item, idx) in result.conflict_points" :key="`c-${idx}`">{{ item }}</li></ul>
      </div>
      <div v-if="result.complement_points?.length" class="compat-block">
        <h3>互补点</h3>
        <ul><li v-for="(item, idx) in result.complement_points" :key="`p-${idx}`">{{ item }}</li></ul>
      </div>
      <p class="hint">合盘为规则化启发式模型，不构成婚恋或执业决策依据。</p>
    </section>
  </main>
</template>

<style scoped>
.ziwei-compat-page { gap: 14px; }

.field-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
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
  font-size: 14px;
}

.compat-score {
  margin: 0 0 8px;
  font-size: 15px;
}

.compat-table {
  width: 100%;
  margin-top: 12px;
  border-collapse: collapse;
  font-size: 13px;
}

.compat-table th,
.compat-table td {
  border-bottom: 1px solid var(--border);
  padding: 8px 6px;
  text-align: left;
}

.compat-block h3 {
  margin: 14px 0 6px;
  font-size: 14px;
}

.compat-block ul {
  margin: 0;
  padding-left: 18px;
  line-height: 1.7;
  color: var(--text-2);
}
</style>
