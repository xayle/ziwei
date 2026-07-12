<script setup lang="ts">
defineProps<{
  items: Array<{ label: string; value: string }>
}>()
</script>

<template>
  <div class="fs-kpi-strip" role="region" aria-label="摘要">    <div v-for="item in items" :key="item.label" class="fs-kpi-strip__cell">
      <span class="fs-kpi-strip__label">{{ item.label }}</span>
      <strong class="fs-kpi-strip__value">{{ item.value }}</strong>
    </div>
  </div>
</template>
