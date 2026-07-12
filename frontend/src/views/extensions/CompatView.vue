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
      </div>
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

.compat-score {
  margin: 0 0 8px;
  font-size: 15px;
}

.compat-list {
  margin: 12px 0 0;
  padding-left: 18px;
  color: var(--text-2);
  line-height: 1.7;
}
</style>
