<script setup lang="ts">
interface ZiweiPatternItem {
  name: string
  level?: string
}

const props = defineProps<{
  summary?: string | null
  patterns: ZiweiPatternItem[]
  lunarText: string
  templateVersion?: string | null
  trueSolarTime?: string | null
  engineVersion?: string | null
}>()
</script>

<template>
  <section class="zw-overview-section">
    <h2 class="zw-overview-title">紫微盘概览</h2>
    <div class="zw-overview-grid">
      <div class="zw-overview-card zw-overview-summary-card">
        <div class="zw-overview-label">总论</div>
        <div class="zw-overview-summary-text">{{ props.summary || '暂无总论。' }}</div>
        <div v-if="props.patterns.length" class="zw-overview-chip-list">
          <span v-for="item in props.patterns.slice(0, 6)" :key="`${item.name}-${item.level}`" class="zw-overview-chip">
            {{ item.name }} · {{ item.level }}
          </span>
        </div>
      </div>

      <div class="zw-overview-card">
        <div class="zw-overview-label">基础数据</div>
        <div class="zw-overview-row"><span class="zw-overview-key">农历</span><span class="zw-overview-value">{{ props.lunarText }}</span></div>
        <div class="zw-overview-row"><span class="zw-overview-key">四化版本</span><span class="zw-overview-value">{{ props.templateVersion || 'standard' }}</span></div>
        <div class="zw-overview-row"><span class="zw-overview-key">真太阳时</span><span class="zw-overview-value">{{ props.trueSolarTime || '—' }}</span></div>
        <div class="zw-overview-row"><span class="zw-overview-key">引擎版本</span><span class="zw-overview-value">{{ props.engineVersion || '—' }}</span></div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.zw-overview-section {
  padding: 16px 24px;
}

.zw-overview-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 12px;
  font-size: 18px;
  font-weight: 800;
  color: var(--text-1);
  letter-spacing: .01em;
}

.zw-overview-grid {
  display: grid;
  grid-template-columns: 1.3fr 1fr;
  gap: 12px;
}

.zw-overview-card {
  border: 1px solid var(--border);
  border-radius: 14px;
  background: var(--surface);
  padding: 14px 16px;
}

.zw-overview-summary-card {
  background: linear-gradient(180deg, rgba(124,77,171,.06), transparent 55%), var(--surface);
}

.zw-overview-label {
  font-size: 10px;
  color: var(--text-3);
  margin-bottom: 4px;
  text-transform: uppercase;
  letter-spacing: .05em;
}

.zw-overview-summary-text {
  margin-top: 8px;
  color: var(--text-2);
  line-height: 1.85;
  font-family: var(--font-cn);
}

.zw-overview-chip-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.zw-overview-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 999px;
  background: var(--surface-2, #f8fafc);
  border: 1px solid var(--border);
  font-size: 12px;
  color: var(--text-2);
  font-family: var(--font-cn);
}

.zw-overview-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px dashed var(--border);
  align-items: flex-start;
}

.zw-overview-row:last-child {
  border-bottom: none;
}

.zw-overview-key {
  min-width: 72px;
  font-size: 12px;
  color: var(--text-3);
  font-family: var(--font-cn);
}

.zw-overview-value {
  flex: 1;
  text-align: right;
  font-size: 12px;
  color: var(--text-1);
  font-family: var(--font-cn);
  line-height: 1.7;
}

@media (max-width: 900px) {
  .zw-overview-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 560px) {
  .zw-overview-title {
    flex-wrap: wrap;
    gap: 6px;
  }

  .zw-overview-row {
    flex-direction: column;
    gap: 4px;
  }

  .zw-overview-value {
    text-align: left;
  }
}
</style>
