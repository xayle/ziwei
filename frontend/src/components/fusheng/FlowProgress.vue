<script setup lang="ts">
import type { FlowStepId } from '@/utils/fushengFlow'

type FlowStepView = {
  id: FlowStepId
  label: string
  path: string
  requiresBirth?: boolean
  ready: boolean
  active: boolean
  done: boolean
}

defineProps<{
  steps: FlowStepView[]
  compact?: boolean
}>()

const emit = defineEmits<{
  navigate: [path: string, requiresBirth?: boolean]
}>()

function onStep(step: FlowStepView) {
  if (!step.ready) {
    emit('navigate', '/profile', false)
    return
  }
  emit('navigate', step.path, step.requiresBirth)
}
</script>

<template>
  <nav
    class="flow-progress"
    :class="{ 'flow-progress--compact': compact }"
    aria-label="主路径进度"
  >
    <button
      v-for="(step, index) in steps"
      :key="step.id"
      class="flow-progress__step"
      :class="{
        'is-active': step.active,
        'is-done': step.done,
        'is-locked': !step.ready,
      }"
      :aria-current="step.active ? 'step' : undefined"
      @click="onStep(step)"
    >
      <span class="flow-progress__index">{{ index + 1 }}</span>
      <span class="flow-progress__label">{{ step.label }}</span>
    </button>
  </nav>
</template>

<style scoped>
.flow-progress {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 8px;
}

.flow-progress--compact {
  grid-template-columns: repeat(5, minmax(0, 1fr));
}

.flow-progress__step {
  display: grid;
  justify-items: center;
  gap: 6px;
  min-height: 56px;
  padding: 8px 6px;
  border-radius: 12px;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text-2);
  cursor: pointer;
  transition: border-color var(--dur-fast), background-color var(--dur-fast), color var(--dur-fast);
}

.flow-progress__step:hover {
  border-color: var(--brand-gold);
}

.flow-progress__step.is-active {
  border-color: var(--brand-gold);
  background: var(--brand-gold-lt);
  color: var(--brand-gold-dark);
}

.flow-progress__step.is-done {
  color: var(--brand-ink);
}

.flow-progress__step.is-locked {
  opacity: 0.55;
  cursor: not-allowed;
}

.flow-progress__index {
  width: 22px;
  height: 22px;
  display: grid;
  place-items: center;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  background: var(--inset-tint);
}

.flow-progress__step.is-active .flow-progress__index,
.flow-progress__step.is-done .flow-progress__index {
  background: var(--brand-gold);
  color: #fffaf5;
}

.flow-progress__label {
  font-size: 12px;
  font-weight: 600;
  font-family: var(--font-cn);
}

@media (max-width: 720px) {
  .flow-progress {
    grid-template-columns: repeat(5, minmax(52px, 1fr));
    overflow-x: auto;
    padding-bottom: 2px;
  }

  .flow-progress__label {
    font-size: 11px;
  }
}
</style>
