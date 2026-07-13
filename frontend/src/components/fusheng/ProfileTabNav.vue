<script setup lang="ts">
export type ProfileTabId = 'basic' | 'bazi' | 'ziwei' | 'cloud'

export type ProfileTabItem = {
  id: ProfileTabId
  label: string
  testId?: string
}

defineProps<{
  tabs: ProfileTabItem[]
  active: ProfileTabId
}>()

const emit = defineEmits<{
  change: [id: ProfileTabId]
}>()
</script>

<template>
  <nav class="archive-tabs" aria-label="档案分组">
    <button
      v-for="tab in tabs"
      :key="tab.id"
      type="button"
      class="archive-tabs__btn"
      :class="{ 'is-active': active === tab.id }"
      :data-testid="tab.testId"
      @click="emit('change', tab.id)"
    >
      {{ tab.label }}
    </button>
  </nav>
</template>
