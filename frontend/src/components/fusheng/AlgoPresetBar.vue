<script setup lang="ts">
export type AlgoPreset = {
  id: string
  label: string
  hint?: string
}

defineProps<{
  presets: AlgoPreset[]
  disabled?: boolean
}>()

const emit = defineEmits<{
  apply: [id: string]
}>()
</script>

<template>
  <div class="algo-preset-bar" data-testid="algo-preset-bar">
    <p class="algo-preset-bar__lead">一键口径预设（写入档案并重算）</p>
    <div class="algo-preset-bar__actions">
      <button
        v-for="preset in presets"
        :key="preset.id"
        type="button"
        class="fs-btn fs-btn--ghost algo-preset-bar__btn"
        :data-testid="`algo-preset-${preset.id}`"
        :disabled="disabled"
        :title="preset.hint"
        @click="emit('apply', preset.id)"
      >
        {{ preset.label }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.algo-preset-bar {
  margin-top: 12px;
  padding: 12px 14px;
  border-radius: 12px;
  background: var(--inset-tint);
  border: 1px dashed var(--border-md);
}

.algo-preset-bar__lead {
  margin: 0 0 8px;
  font-size: 12px;
  color: var(--text-2);
}

.algo-preset-bar__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.algo-preset-bar__btn {
  font-size: 12px;
}
</style>
