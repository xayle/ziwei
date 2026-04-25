<script setup lang="ts">
import { useReportStore } from '@/stores/report'
import { CHAPTERS } from '@/data/toc'

const store = useReportStore()

function onClickChapter(num: number, disabled?: boolean) {
  if (disabled) return
  store.setActiveChapter(num)
}
</script>

<template>
  <nav class="chapter-nav">
    <!-- 案例切换按钮 -->
    <button
      class="nav-icon nav-icon--top"
      title="切换案例"
      @click="$router.push('/report')"
    >
      📚
    </button>

    <div class="divider" />

    <!-- 8大章节图标 -->
    <button
      v-for="ch in CHAPTERS"
      :key="ch.num"
      class="nav-icon"
      :class="{
        active: store.activeChapter === ch.num,
        disabled: ch.disabled,
      }"
      :title="ch.label"
      :disabled="!!ch.disabled"
      @click="onClickChapter(ch.num, ch.disabled)"
    >
      <span class="icon-text">{{ ch.icon }}</span>
      <span class="icon-num">{{ ch.num }}</span>
    </button>
  </nav>
</template>

<style scoped>
.chapter-nav {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--sp-2) 0;
  gap: 2px;
  background: var(--surface);
  height: 100%;
}

.nav-icon--top {
  margin-bottom: var(--sp-1);
}

.divider {
  width: 32px;
  height: 1px;
  background: var(--border);
  margin: var(--sp-2) 0;
}

.nav-icon {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  cursor: pointer;
  transition: background var(--dur-fast), transform var(--dur-fast);
  gap: 0;
}

.nav-icon:hover:not(.disabled) {
  background: var(--accent-glow);
}

.nav-icon.active {
  background: var(--accent-lt);
  box-shadow: inset 2px 0 0 var(--accent);
}

.nav-icon.disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.icon-text {
  font-size: 20px;
  line-height: 1;
}

.icon-num {
  font-size: 9px;
  color: var(--text-3);
  line-height: 1;
  font-family: var(--font-mono);
}

.nav-icon.active .icon-num {
  color: var(--accent-dark);
}
</style>
