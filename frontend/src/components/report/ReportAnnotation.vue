<script setup lang="ts">
/**
 * ReportAnnotation.vue — 报告书第四列（批注卡组）
 * 统一容纳四个独立卡片组件
 */
import CardOverview from './cards/CardOverview.vue'
import CardGlossary from './cards/CardGlossary.vue'
import CardFortune  from './cards/CardFortune.vue'
import CardNotes    from './cards/CardNotes.vue'
</script>

<template>
  <aside class="annotation-panel">
    <CardOverview />
    <CardGlossary />
    <CardFortune  />
    <CardNotes    />
  </aside>
</template>

<style scoped>
.annotation-panel {
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
  padding: var(--sp-3);
  overflow-y: auto;
  height: 100%;
  box-sizing: border-box;
}
</style>
