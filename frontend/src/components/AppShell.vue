<script setup lang="ts">
/**
 * AppShell.vue — 三栏布局容器
 * 左：AppSidebar（可折叠 240px / 64px）
 * 中：<slot>（RouterView）
 * 右：AppRightPanel（可折叠 360px / 0px）
 *
 * 进入 /report 系列路由时自动折叠侧边栏（报告书有专属 ReportChapterNav）
 */
import { onBeforeUnmount, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useUiStore } from '@/stores/ui'
import AppSidebar from '@/components/AppSidebar.vue'

const route = useRoute()
const ui    = useUiStore()

function resolveViewportMode() {
  const width = window.innerWidth
  if (width < 860) return 'mobile'
  if (width < 1280) return 'compact'
  return 'desktop'
}

function syncViewportMode() {
  ui.setViewportMode(resolveViewportMode())
}

onMounted(() => {
  syncViewportMode()
  window.addEventListener('resize', syncViewportMode)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', syncViewportMode)
})

// 进入报告书路由时自动折叠侧边栏
watch(
  () => route.path,
  (path) => {
    if (path.startsWith('/report')) {
      ui.collapseSidebarForReport()
    }
  },
  { immediate: true }
)
</script>

<template>
  <div class="app-shell" :class="`is-${ui.viewportMode}`">
    <AppSidebar />

    <div class="shell-center">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.app-shell {
  display: flex;
  height: 100vh;
  width: 100%;
  overflow: hidden;
  background: var(--bg);
}

.shell-center {
  flex: 1 1 0%;
  min-width: 0;
  min-height: 0;
  height: 100vh;
  overflow-x: hidden;
  display: flex;
  flex-direction: column;
}
</style>
