<script setup lang="ts">
/**
 * AppShell.vue — 三栏布局容器
 * 左：AppSidebar（可折叠 240px / 64px）
 * 中：<slot>（RouterView）
 * 右：AppRightPanel（可折叠 360px / 0px）
 *
 * 进入 /report 系列路由时自动折叠侧边栏（报告书有专属 ReportChapterNav）
 */
import { watch } from 'vue'
import { useRoute } from 'vue-router'
import { useUiStore } from '@/stores/ui'
import AppSidebar from '@/components/AppSidebar.vue'
import AppRightPanel from '@/components/AppRightPanel.vue'

const route = useRoute()
const ui    = useUiStore()

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
  <div class="app-shell">
    <AppSidebar />

    <div class="shell-center">
      <slot />
    </div>

    <AppRightPanel />
  </div>
</template>

<style scoped>
.app-shell {
  display: flex;
  height: 100vh;
  width: 100vw;
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
