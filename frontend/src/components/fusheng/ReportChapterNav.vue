<script setup lang="ts">
import type { LifeVolumeId } from '@/types/life-volume'

defineProps<{
  chapters: Array<{ id: LifeVolumeId; label: string }>
  activeId: LifeVolumeId
}>()

const emit = defineEmits<{
  navigate: [id: LifeVolumeId]
}>()
</script>

<template>
  <nav class="report-chapter-nav no-print" aria-label="卷目目录">
    <button
      v-for="chapter in chapters"
      :key="chapter.id"
      type="button"
      class="report-chapter-nav__btn"
      :class="{ 'is-active': activeId === chapter.id }"
      :aria-current="activeId === chapter.id ? 'location' : undefined"
      :data-testid="`report-volume-${chapter.id}`"
      @click="emit('navigate', chapter.id)"
    >
      {{ chapter.label }}
    </button>
  </nav>
</template>

<style scoped>
.report-chapter-nav {
  display: grid;
  gap: 6px;
  position: sticky;
  top: 72px;
  align-self: start;
}

.report-chapter-nav__btn {
  text-align: left;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text-2);
  font-size: 13px;
  font-family: var(--font-display);
  cursor: pointer;
}

.report-chapter-nav__btn.is-active {
  border-color: var(--brand-gold);
  background: var(--brand-gold-lt);
  color: var(--brand-ink);
}
</style>
