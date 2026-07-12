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
  <nav class="profile-tabs" aria-label="档案分组">
    <button
      v-for="tab in tabs"
      :key="tab.id"
      type="button"
      class="profile-tabs__btn"
      :class="{ 'is-active': active === tab.id }"
      :data-testid="tab.testId"
      @click="emit('change', tab.id)"
    >
      {{ tab.label }}
    </button>
  </nav>
</template>

<style scoped>
.profile-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.profile-tabs__btn {
  padding: 8px 14px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text-2);
  font-size: 13px;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
}

.profile-tabs__btn.is-active {
  background: var(--brand-gold-lt);
  border-color: var(--brand-gold);
  color: var(--brand-gold-dark);
  font-weight: 600;
}
</style>
