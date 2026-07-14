<script setup lang="ts">

import FushengZiweiPlate from '@/components/fusheng/FushengZiweiPlate.vue'

import ZiweiForecastSummary from '@/components/fusheng/ZiweiForecastSummary.vue'

import { computed, onMounted, ref, watch } from 'vue'

import type { OverlayLayer } from '@/utils/ziweiOverlay'

import { dayunBranchIdx } from '@/utils/ziweiOverlay'

import { useRouter } from 'vue-router'

import ResultStateCard from '@/components/new/ResultStateCard.vue'
import VolumeHead from '@/components/fusheng/VolumeHead.vue'

import { useFushengFlow } from '@/composables/useFushengFlow'

import { useFushengReport } from '@/composables/useFushengReport'

import '@/assets/fusheng-page.css'



const router = useRouter()

const { isArchiveComplete, navigateToStep } = useFushengFlow()

const { loadingZiwei, error, ziwei, loadZiwei, requestMeta } = useFushengReport()



const today = new Date()

const selectedDate = ref(today.toISOString().slice(0, 10))

const currentYear = today.getFullYear()



const overlayLayer = ref<OverlayLayer>('dayun')

const selectedDayunBranchIdx = ref<number | null>(null)

const liuyueMonth = ref(today.getMonth() + 1)



const liuyueOptions = computed(() => {

  const items = ziwei.value?.liuyue ?? []

  if (items.length) {

    return items.map((item) => ({

      value: item.month,

      label: item.month_name || `${item.month}月`,

    }))

  }

  return Array.from({ length: 12 }, (_, i) => ({

    value: i + 1,

    label: `${i + 1}月`,

  }))

})



const liuriSummary = computed(() => {

  const lr = ziwei.value?.liuri_liushi?.liuri

  if (!lr) return null

  return {

    branch: lr.branch,

    palace: lr.palace_name,

    lunarDay: lr.lunar_day,

    liuyueMonth: lr.liuyue_month,

  }

})



watch(overlayLayer, (layer) => {

  if (layer === 'liuyue' && liuyueOptions.value.length) {

    const has = liuyueOptions.value.some((opt) => opt.value === liuyueMonth.value)

    if (!has) liuyueMonth.value = liuyueOptions.value[0].value

  }

})



watch(selectedDate, (date) => {

  const parsed = new Date(`${date}T12:00:00`)

  if (!Number.isNaN(parsed.getTime())) {

    liuyueMonth.value = parsed.getMonth() + 1

  }

  void loadZiwei(true, date)

})



function dayunEndYear(item: { start_year?: number | null; end_year?: number | null; start_age?: number | null; end_age?: number | null }): number | null {
  if (item.end_year != null && Number.isFinite(item.end_year)) return Number(item.end_year)
  if (item.start_year == null || !Number.isFinite(item.start_year)) return null
  if (item.start_age != null && item.end_age != null) {
    return item.start_year + Math.max(0, item.end_age - item.start_age)
  }
  return item.start_year + 9
}

const dayunRows = computed(() => {
  const items = ziwei.value?.dayun?.items ?? []
  return items.map((item, idx) => {
    const endYear = dayunEndYear(item as { start_year?: number | null; end_year?: number | null; start_age?: number | null; end_age?: number | null })
    return {
      idx,
      branchIdx: dayunBranchIdx(item),
      ganzhi: item.ganzhi || '—',
      ages: `${item.start_age ?? '—'}–${item.end_age ?? '—'} 岁`,
      years: item.start_year != null && endYear != null
        ? `${item.start_year}–${endYear}`
        : `${item.start_year ?? '—'} 起`,
      sihua: Object.entries(item.sihua ?? {}).map(([star, tf]) => `${star}${tf}`).join(' · ') || '—',
      active: item.start_year != null && endYear != null
        && item.start_year <= currentYear
        && currentYear <= endYear,
    }
  })
})



const metaText = computed(() => {

  const meta = requestMeta.value

  if (!meta) return '口径说明将在排盘后显示。'

  return `${meta.precisionLabel} · ${meta.timeRiskLabel} · 参考日 ${selectedDate.value}`

})



function selectDayun(row: { branchIdx: number }) {

  if (row.branchIdx < 0) return

  selectedDayunBranchIdx.value = row.branchIdx

  overlayLayer.value = 'dayun'

}



function isDayunSelected(row: { branchIdx: number; active: boolean }) {

  if (selectedDayunBranchIdx.value != null && row.branchIdx >= 0) {

    return selectedDayunBranchIdx.value === row.branchIdx

  }

  return row.active

}



onMounted(() => {

  if (!isArchiveComplete.value) {

    navigateToStep('/profile')

    return

  }

  void loadZiwei(false, selectedDate.value)

})



function goPlate() {

  router.push('/new/ziwei')

}

</script>



<template>

  <main class="fs-page ziwei-timeline-page">
    <VolumeHead
      volume-id="vol3"
      title="运限时间轴"
      :desc="metaText"
    >
      <template #actions>
        <button class="fs-btn fs-btn--ghost" @click="goPlate">返回命盘</button>
      </template>
    </VolumeHead>



    <section class="fs-card timeline-date-card timeline-date-card--sticky" data-testid="timeline-sticky-date">
      <label class="timeline-date-card__label" for="timeline-date">卷三·运波 — 参考日</label>
      <input

        id="timeline-date"

        v-model="selectedDate"

        type="date"

        class="timeline-date-card__input"

        data-testid="timeline-date"

      />

    </section>



    <ResultStateCard

      v-if="loadingZiwei"

      compact

      title="正在载入运限"

      message="请稍候。"

    />

    <ResultStateCard

      v-else-if="error"

      title="紫微运限暂时不可用"

      :message="error"

      action-label="重新计算"

      @action="loadZiwei(true, selectedDate)"

    />



    <ZiweiForecastSummary

      v-if="!loadingZiwei && !error && ziwei?.forecast"

      :forecast="ziwei.forecast"

      :evidence-chain="ziwei.evidence_chain"

    />



    <section
      v-if="!loadingZiwei && !error && liuriSummary"
      class="fs-card liuri-card"
      data-testid="timeline-liuri-section"
    >
      <h2>流日叠宫</h2>
      <p class="timeline-section-eyebrow">卷三·运波 — 流日</p>
      <p>

        农历 {{ liuriSummary.lunarDay }} 日 · 流月 {{ liuriSummary.liuyueMonth ?? '—' }} ·

        流日地支 <strong>{{ liuriSummary.branch }}</strong> · 叠入 <strong>{{ liuriSummary.palace }}</strong>

      </p>

      <button type="button" class="fs-btn fs-btn--ghost" @click="overlayLayer = 'liuri'">

        在命盘查看流日层

      </button>

    </section>



    <section v-if="!loadingZiwei && !error && ziwei" class="fs-card overlay-card" data-testid="timeline-overlay-section">
      <h2>叠宫命盘</h2>
      <p class="overlay-hint">

        切换「大限 / 流年 / 流月 / 流日 / 飞星」查看叠宫标签；点击下方大运行可切换大限叠入宫位。

      </p>

      <div v-if="overlayLayer === 'liuyue'" class="liuyue-picker">

        <label class="liuyue-picker__label" for="liuyue-month">流月</label>

        <select

          id="liuyue-month"

          v-model.number="liuyueMonth"

          class="liuyue-picker__select"

        >

          <option v-for="opt in liuyueOptions" :key="opt.value" :value="opt.value">

            {{ opt.label }}

          </option>

        </select>

      </div>

      <FushengZiweiPlate

        :result="ziwei"

        :overlay-layer="overlayLayer"

        :selected-dayun-branch-idx="selectedDayunBranchIdx"

        :liuyue-month="liuyueMonth"

        :show-overlay-controls="true"

        @update:overlay-layer="overlayLayer = $event"

      />

    </section>



    <section v-if="!loadingZiwei && !error && dayunRows.length" class="fs-card timeline-card" data-testid="timeline-dayun-section">
      <h2>大运序列</h2>
      <p class="timeline-section-eyebrow">卷三·运波 — 大限</p>
      <p class="timeline-hint">点击任一大运，方盘将叠入该步大限（高亮行）。</p>

      <ol class="timeline-list">

        <li

          v-for="row in dayunRows"

          :key="row.idx"

          class="timeline-item"

          :class="{ 'is-active': isDayunSelected(row), 'is-clickable': row.branchIdx >= 0 }"

          role="button"

          tabindex="0"

          @click="selectDayun(row)"

          @keydown.enter="selectDayun(row)"

        >

          <span class="timeline-item__gz">{{ row.ganzhi }}</span>

          <span class="timeline-item__ages">{{ row.ages }}</span>

          <span class="timeline-item__years">{{ row.years }}</span>

          <span class="timeline-item__sihua">{{ row.sihua }}</span>

        </li>

      </ol>

    </section>

    <ResultStateCard

      v-else-if="!loadingZiwei && !error"

      compact

      title="暂无大运数据"

      message="请先完成紫微排盘。"

    />

  </main>

</template>



<style scoped>

.ziwei-timeline-page {
  gap: 14px;
  min-width: 0;
  overflow-x: clip;
}

.timeline-date-card--sticky {
  position: sticky;
  top: 0;
  z-index: 12;
  background: rgba(255, 250, 245, 0.96);
  backdrop-filter: blur(6px);
  border-bottom: 1px solid var(--border);
}

.timeline-section-eyebrow {
  margin: -4px 0 10px;
  font-size: 11px;
  letter-spacing: 0.12em;
  color: var(--brand-gold-dark);
  font-family: var(--font-cn);
}


.timeline-date-card {

  display: flex;

  align-items: center;

  gap: 10px;

  padding: 12px 14px;

}



.timeline-date-card__label {

  font-size: 13px;

  font-weight: 700;

  color: #57534e;

}



.timeline-date-card__input {

  padding: 6px 10px;

  border-radius: 8px;

  border: 1px solid #d6c9b3;

  background: #fffdf7;

  font-size: 13px;

}



.liuri-card h2,

.overlay-card h2,

.timeline-card h2 {

  margin: 0 0 12px;

  font-family: var(--font-cn);

  color: var(--brand-ink);

}



.liuri-card p {

  margin: 0 0 10px;

  font-size: 13px;

  line-height: 1.6;

  color: #44403c;

}



.overlay-hint,

.timeline-hint {

  margin: 0 0 10px;

  font-size: 13px;

  color: var(--text-3, #78716c);

  line-height: 1.6;

}



.liuyue-picker {

  display: flex;

  align-items: center;

  gap: 8px;

  margin-bottom: 10px;

}



.liuyue-picker__label {

  font-size: 12px;

  font-weight: 700;

  color: #57534e;

}



.liuyue-picker__select {

  padding: 4px 8px;

  border-radius: 8px;

  border: 1px solid #d6c9b3;

  background: #fffdf7;

  font-size: 12px;

}



.timeline-list {

  margin: 0;

  padding: 0;

  list-style: none;

  display: flex;

  flex-direction: column;

  gap: 8px;

}



.timeline-item {

  display: grid;

  grid-template-columns: 64px 1fr 88px;

  gap: 8px 12px;

  padding: 10px 12px;

  border: 1px solid var(--border-soft, #e7e0d5);

  border-radius: 10px;

  font-size: 12px;

  background: #fffdf7;

}



.timeline-item.is-clickable {

  cursor: pointer;

}



.timeline-item.is-clickable:hover {

  border-color: var(--brand-gold);

  background: var(--brand-gold-lt);

}



.timeline-item.is-active {

  border-color: var(--brand-gold);

  background: var(--brand-gold-lt);

}



.timeline-item__gz {

  font-weight: 800;

  font-family: var(--font-cn);

  color: var(--brand-ink);

}



.timeline-item__sihua {

  grid-column: 1 / -1;

  color: var(--text-3, #78716c);

}



@media (min-width: 640px) {

  .timeline-item {

    grid-template-columns: 72px 120px 100px 1fr;

  }



  .timeline-item__sihua {

    grid-column: auto;

  }

}

</style>

