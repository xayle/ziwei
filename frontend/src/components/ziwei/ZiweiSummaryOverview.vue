<script setup lang="ts">
interface SummaryQuickFactItem {
  label: string
  value: string
}

interface SummaryKeyConclusionItem {
  title: string
  tag: string
  content: string
  type: string
}

defineProps<{
  summary?: string | null
  quickFacts: SummaryQuickFactItem[]
  insightTags: string[]
  keyConclusions: SummaryKeyConclusionItem[]
  wuxingJu: number | string
  wuxingJuName: string
  juColors: Record<number | string, string>
  lifePalaceGz: string
  bodyPalaceGz: string
  lifeRulerStar?: string | null
  bodyRulerStar?: string | null
  dayunStartText?: string | null
}>()
</script>

<template>
  <div class="summary-overview">
    <p v-if="summary" class="summary-text">{{ summary }}</p>

    <div v-if="quickFacts.length" class="summary-quick-facts">
      <div v-for="item in quickFacts" :key="item.label" class="sqf-item">
        <span class="sqf-label">{{ item.label }}</span>
        <span class="sqf-value">{{ item.value }}</span>
      </div>
    </div>

    <div v-if="insightTags.length" class="summary-insights">
      <span v-for="tag in insightTags" :key="tag" class="summary-insight-tag">{{ tag }}</span>
    </div>

    <div v-if="keyConclusions.length" class="summary-key-conclusions">
      <div
        v-for="item in keyConclusions"
        :key="item.title"
        :class="['skc-item', `skc-${item.type}`]"
      >
        <div class="skc-head">
          <span class="skc-title">{{ item.title }}</span>
          <span class="skc-tag">{{ item.tag }}</span>
        </div>
        <p class="skc-content">{{ item.content }}</p>
      </div>
    </div>

    <div class="summary-highlights">
      <div class="sh-item">
        <span class="sh-label">五行局</span>
        <span class="sh-value" :style="{ color: juColors[wuxingJu] }">{{ wuxingJuName }}</span>
      </div>
      <div class="sh-item">
        <span class="sh-label">命宫</span>
        <span class="sh-value">{{ lifePalaceGz }}</span>
      </div>
      <div class="sh-item">
        <span class="sh-label">身宫</span>
        <span class="sh-value">{{ bodyPalaceGz }}</span>
      </div>
      <div class="sh-item">
        <span class="sh-label">命主</span>
        <span class="sh-value">{{ lifeRulerStar || '-' }}</span>
      </div>
      <div class="sh-item">
        <span class="sh-label">身主</span>
        <span class="sh-value">{{ bodyRulerStar || '-' }}</span>
      </div>
      <div v-if="dayunStartText" class="sh-item">
        <span class="sh-label">起运</span>
        <span class="sh-value">{{ dayunStartText }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.summary-overview {
  display: flex;
  flex-direction: column;
}

.summary-text {
  font-size: var(--fs-md);
  line-height: 1.8;
  color: var(--text);
  margin-bottom: var(--sp-4);
}

.summary-quick-facts {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: var(--sp-2);
  margin-bottom: var(--sp-3);
}

.sqf-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 8px 10px;
  border-radius: 10px;
  border: 1px solid var(--border);
  background: var(--surface-2);
}

.sqf-label {
  font-size: var(--fs-xs);
  color: var(--text-2);
}

.sqf-value {
  font-size: var(--fs-sm);
  color: var(--text);
  font-weight: 600;
}

.summary-insights {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: var(--sp-4);
}

.summary-insight-tag {
  font-size: var(--fs-xs);
  color: var(--text-2);
  background: var(--surface-2);
  border: 1px dashed var(--border-md);
  border-radius: 999px;
  padding: 4px 10px;
}

.summary-key-conclusions {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--sp-2);
  margin-bottom: var(--sp-4);
}

.skc-item {
  padding: var(--sp-3);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  background: var(--surface-2);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.skc-item.skc-good { border-color: #86efac; background: #f0fdf4; }
.skc-item.skc-warn { border-color: #fca5a5; background: #fff7f7; }

.skc-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
}

.skc-title {
  font-size: var(--fs-xs);
  color: var(--text-2);
  font-weight: 500;
}

.skc-tag {
  font-size: 10px;
  padding: 1px 7px;
  border-radius: 999px;
  background: var(--border);
  color: var(--text-2);
}

.skc-item.skc-good .skc-tag { background: #bbf7d0; color: #166534; }
.skc-item.skc-warn .skc-tag { background: #fecaca; color: #991b1b; }

.skc-content {
  font-size: var(--fs-sm);
  color: var(--text);
  font-weight: 600;
  margin: 0;
  line-height: 1.4;
}

.summary-highlights {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-3);
  padding: var(--sp-4);
  background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
  border: 1px solid #fcd34d;
  border-radius: var(--radius-sm);
  margin-bottom: var(--sp-4);
}

.sh-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 70px;
}

.sh-label {
  font-size: 10px;
  color: #92400e;
  margin-bottom: 2px;
}

.sh-value {
  font-size: var(--fs-md);
  font-weight: 700;
  font-family: var(--font-cn);
  color: #78350f;
}
</style>
