<script setup lang="ts">
interface GuideStep {
  title: string
  desc: string
}

const props = defineProps<{
  currentStep: number
  progressPercent: string
  steps: GuideStep[]
}>()

const emit = defineEmits<{
  prev: []
  next: []
  play: []
  close: []
  focusStep: [step: number]
}>()
</script>

<template>
  <div class="wb-guide-card" role="region" aria-label="新手三步引导">
    <div class="wb-guide-head">
      <div class="wb-guide-title">新手三步引导</div>
      <div class="wb-guide-head-actions">
        <button type="button" class="wb-guide-jump wb-guide-nav" @click="emit('prev')" :disabled="props.currentStep <= 1">上一步</button>
        <button type="button" class="wb-guide-jump wb-guide-nav" @click="emit('next')" :disabled="props.currentStep >= 3">下一步</button>
        <button type="button" class="wb-guide-play" @click="emit('play')">自动演示</button>
        <button type="button" class="wb-guide-close" @click="emit('close')">我知道了</button>
      </div>
    </div>
    <div class="wb-guide-progress" aria-hidden="true">
      <span class="wb-guide-progress-label">进度 {{ props.currentStep }}/3</span>
      <div class="wb-guide-progress-track">
        <i class="wb-guide-progress-fill" :style="{ width: props.progressPercent }"></i>
      </div>
    </div>
    <div class="wb-guide-steps">
      <div v-for="(step, idx) in props.steps" :key="step.title" class="wb-guide-step" :class="{ 'is-active': props.currentStep === idx + 1 }">
        <div class="wb-guide-index">{{ idx + 1 }}</div>
        <div>
          <div class="wb-guide-step-title">{{ step.title }}</div>
          <p class="wb-guide-step-desc">{{ step.desc }}</p>
          <button type="button" class="wb-guide-jump" @click="emit('focusStep', idx + 1)">定位到此区域</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.wb-guide-card {
  margin: 10px 0 12px;
  padding: 12px;
  border-radius: 12px;
  border: 1px solid rgba(37, 99, 235, 0.28);
  background: rgba(37, 99, 235, 0.06);
}

.wb-guide-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 10px;
}

.wb-guide-progress {
  display: grid;
  gap: 6px;
  margin-bottom: 10px;
}

.wb-guide-progress-label {
  font-size: 12px;
  color: #475569;
}

.wb-guide-progress-track {
  height: 6px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.35);
  overflow: hidden;
}

.wb-guide-progress-fill {
  display: block;
  height: 100%;
  border-radius: 999px;
  background: #1d4ed8;
  transition: width 220ms ease;
}

.wb-guide-head-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.wb-guide-play {
  border: 1px solid rgba(16, 185, 129, 0.4);
  background: rgba(16, 185, 129, 0.1);
  color: #047857;
  border-radius: 999px;
  font-size: 12px;
  line-height: 1;
  padding: 6px 10px;
  cursor: pointer;
}

.wb-guide-play:hover {
  background: rgba(16, 185, 129, 0.16);
}

.wb-guide-title {
  font-size: 13px;
  font-weight: 700;
  color: #1e3a8a;
}

.wb-guide-close {
  border: 1px solid rgba(37, 99, 235, 0.32);
  background: #fff;
  color: #1e3a8a;
  border-radius: 999px;
  font-size: 12px;
  line-height: 1;
  padding: 6px 10px;
  cursor: pointer;
}

.wb-guide-close:hover {
  background: rgba(37, 99, 235, 0.1);
}

.wb-guide-steps {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.wb-guide-step {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px;
  border-radius: 10px;
  background: #fff;
  border: 1px solid rgba(148, 163, 184, 0.35);
}

.wb-guide-step.is-active {
  border-color: rgba(37, 99, 235, 0.45);
  box-shadow: inset 0 0 0 1px rgba(37, 99, 235, 0.18);
}

.wb-guide-index {
  width: 20px;
  height: 20px;
  border-radius: 999px;
  flex: 0 0 20px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(37, 99, 235, 0.14);
  color: #1d4ed8;
  font-size: 11px;
  font-weight: 700;
}

.wb-guide-step-title {
  font-size: 12px;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 4px;
}

.wb-guide-step-desc {
  margin: 0;
  font-size: 12px;
  line-height: 1.5;
  color: #334155;
}

.wb-guide-jump {
  margin-top: 8px;
  border: 1px dashed rgba(37, 99, 235, 0.45);
  background: rgba(37, 99, 235, 0.08);
  color: #1d4ed8;
  border-radius: 8px;
  font-size: 11px;
  line-height: 1;
  padding: 6px 8px;
  cursor: pointer;
}

.wb-guide-nav {
  margin-top: 0;
}

.wb-guide-jump:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.wb-guide-jump:hover {
  background: rgba(37, 99, 235, 0.14);
}

@media (max-width: 1024px) {
  .wb-guide-steps {
    grid-template-columns: 1fr;
  }
}
</style>
