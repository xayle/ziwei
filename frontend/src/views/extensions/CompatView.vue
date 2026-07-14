<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import ResultStateCard from '@/components/new/ResultStateCard.vue'
import { useProfileStore } from '@/stores/profile'
import { baziCompatibility, type BaziCompatibilityResponse } from '@/api/bazi'
import '@/assets/fusheng-page.css'

const router = useRouter()
const profile = useProfileStore()

const partnerBirthDt = ref('')
const partnerGender = ref('female')
const partnerLon = ref<number | null>(profile.lon ?? 116.41)
const partnerTz = ref(profile.tz || 'Asia/Shanghai')
const loading = ref(false)
const error = ref('')
const result = ref<BaziCompatibilityResponse | null>(null)

async function runCompat() {
  if (!profile.birthDt?.trim()) {
    error.value = '请先补全当前档案出生时间。'
    return
  }
  if (!partnerBirthDt.value.trim()) {
    error.value = '请填写对方出生时间。'
    return
  }
  if (!Number.isFinite(partnerLon.value)) {
    error.value = '请填写对方出生地经度（或确认与甲方相同）。'
    return
  }

  loading.value = true
  error.value = ''
  result.value = null

  try {
    result.value = await baziCompatibility({
      person_a: {
        birth_dt: profile.birthDt,
        lon: profile.lon,
        tz: profile.tz,
        gender: profile.gender || undefined,
      },
      person_b: {
        birth_dt: partnerBirthDt.value.trim(),
        gender: partnerGender.value,
        lon: partnerLon.value!,
        tz: partnerTz.value || 'Asia/Shanghai',
      },
    })
  } catch {
    error.value = '合婚分析失败，请检查输入后重试。'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="fs-page compat-page">
    <p class="fs-page-lead">主方：{{ profile.activeProfile?.label || '当前档案' }} · {{ profile.birthDt?.replace('T', ' ') || '出生时间未填' }}</p>
    <div class="fs-page-actions">
      <button class="fs-btn fs-btn--ghost" @click="router.push('/extensions')">返回工具箱</button>
      <button class="fs-btn fs-btn--ghost" @click="router.push('/relation/new')">权威合盘</button>
    </div>

    <section class="fs-card">
      <h2>对方信息</h2>
      <div class="field-grid">
        <label class="field">
          <span>出生时间</span>
          <input v-model="partnerBirthDt" type="datetime-local" data-testid="compat-partner-birth" />
        </label>
        <label class="field">
          <span>性别</span>
          <select v-model="partnerGender">
            <option value="female">女</option>
            <option value="male">男</option>
          </select>
        </label>
        <label class="field">
          <span>经度</span>
          <input v-model.number="partnerLon" type="number" step="0.0001" data-testid="compat-partner-lon" />
        </label>
        <label class="field">
          <span>时区</span>
          <input v-model="partnerTz" type="text" data-testid="compat-partner-tz" />
        </label>
      </div>
      <p class="hint">经度默认与甲方相同，请按对方出生城市修改（勿长期沿用北京默认）。</p>
      <button class="fs-btn fs-btn--primary" :disabled="loading" data-testid="compat-run" @click="runCompat">
        {{ loading ? '分析中…' : '开始合婚分析' }}
      </button>
    </section>

    <ResultStateCard v-if="error" title="合婚分析失败" :message="error" />
    <section v-if="result" class="fs-card">
      <h2>分析结果</h2>
      <p class="compat-score">综合得分 <strong>{{ result.score }}</strong> 分</p>
      <p>{{ result.summary }}</p>
      <ul v-if="result.branch_clash?.length" class="compat-list">
        <li v-for="(item, idx) in result.branch_clash" :key="`clash-${idx}`">{{ item }}</li>
      </ul>
      <ul v-if="result.born_year_he?.length" class="compat-list">
        <li v-for="(item, idx) in result.born_year_he" :key="`he-${idx}`">{{ item }}</li>
      </ul>
    </section>
  </main>
</template>

<style scoped>
.compat-page { gap: 14px; }

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

.hint {
  margin: 0 0 12px;
  font-size: 12px;
  color: var(--muted);
}

.compat-score { margin: 0 0 8px; }
.compat-list { margin: 8px 0 0; padding-left: 1.2em; }
</style>
