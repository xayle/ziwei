<script setup lang="ts">
import type { ArchiveFieldKey, EnhancerFieldKey } from '@/utils/profileReadiness'

defineProps<{
  completeness: number
  blockers: ArchiveFieldKey[]
  enhancers: EnhancerFieldKey[]
  timeLabel: string
  timeHint?: string
  getBlockerLabel: (key: ArchiveFieldKey) => string
  getEnhancerLabel: (key: EnhancerFieldKey) => string
}>()

const emit = defineEmits<{
  action: []
}>()
</script>

<template>
  <article class="readiness-card fs-card">
    <div class="readiness-card__head">
      <h2>档案就绪度</h2>
      <strong>{{ completeness }}%</strong>
    </div>

    <div class="readiness-card__bar">
      <span :style="{ width: `${completeness}%` }" />
    </div>

    <p class="readiness-card__time">时间可信度：{{ timeLabel }}</p>
    <p v-if="timeHint" class="readiness-card__hint">{{ timeHint }}</p>

    <div v-if="blockers.length" class="readiness-card__missing readiness-card__missing--blocker">
      <p><strong>必填阻断项：</strong>{{ blockers.map(getBlockerLabel).join('、') }}</p>
      <button class="fs-btn fs-btn--primary" type="button" @click="emit('action')">去补全档案</button>
    </div>
    <div v-else-if="enhancers.length" class="readiness-card__missing">
      <p>可增强项：{{ enhancers.map(getEnhancerLabel).join('、') }}</p>
    </div>
    <p v-else class="readiness-card__ok">档案已齐备，可进入排盘与报告。</p>
  </article>
</template>

<style scoped>
.readiness-card {
  display: grid;
  gap: 10px;
}

.readiness-card__head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 12px;
}

.readiness-card__head h2 {
  margin: 0;
  font-size: 16px;
}

.readiness-card__head strong {
  font-size: 22px;
  color: var(--brand-gold-dark);
  font-family: var(--font-cn);
}

.readiness-card__bar {
  height: 8px;
  border-radius: 999px;
  background: var(--surface-2);
  overflow: hidden;
}

.readiness-card__bar span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--brand-gold);
}

.readiness-card__time,
.readiness-card__hint,
.readiness-card__ok {
  margin: 0;
  font-size: 13px;
  color: var(--text-2);
  line-height: 1.6;
}

.readiness-card__missing {
  display: grid;
  gap: 10px;
  padding: 12px;
  border-radius: 12px;
  background: rgba(184, 137, 77, 0.08);
  border: 1px solid rgba(184, 137, 77, 0.2);
}

.readiness-card__missing--blocker {
  background: rgba(139, 58, 42, 0.06);
  border-color: rgba(139, 58, 42, 0.12);
}

.readiness-card__missing p {
  margin: 0;
  font-size: 13px;
  color: var(--brand-cinnabar);
}

.readiness-card__ok {
  color: var(--success-dark);
}
</style>
