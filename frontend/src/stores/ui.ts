/**
 * ui.ts — 全局 UI 状态（侧边栏 / 右栏展开态）
 * 持久化到 localStorage，避免刷新后布局跳动
 */
import { defineStore } from 'pinia'
import { computed, ref, watch } from 'vue'

export type ViewportMode = 'desktop' | 'compact' | 'mobile'

export const useUiStore = defineStore('ui', () => {
  // ── 侧边栏 ──────────────────────────────────────────────────
  const sidebarExpanded = ref<boolean>(
    localStorage.getItem('ui_sidebar') !== 'false'
  )

  // ── 右侧 AI 面板 ──────────────────────────────────────────────
  const rightPanelExpanded = ref<boolean>(
    localStorage.getItem('ui_rightpanel') === 'true'
  )

  // ── 当前视口模式（由壳层同步）───────────────────────────────
  const viewportMode = ref<ViewportMode>('desktop')
  const isCompactLayout = computed(() => viewportMode.value === 'compact')
  const isMobileLayout = computed(() => viewportMode.value === 'mobile')
  const rightPanelVisible = computed(() =>
    viewportMode.value === 'desktop' && rightPanelExpanded.value
  )

  // 持久化
  watch(sidebarExpanded, (v) => localStorage.setItem('ui_sidebar', String(v)))
  watch(rightPanelExpanded, (v) => localStorage.setItem('ui_rightpanel', String(v)))

  function toggleSidebar() {
    sidebarExpanded.value = !sidebarExpanded.value
  }

  function toggleRightPanel() {
    rightPanelExpanded.value = !rightPanelExpanded.value
  }

  function openRightPanelIfAllowed() {
    if (viewportMode.value === 'desktop') {
      rightPanelExpanded.value = true
    }
  }

  function closeRightPanel() {
    rightPanelExpanded.value = false
  }

  function setViewportMode(mode: ViewportMode) {
    viewportMode.value = mode
  }

  /** 进入报告书时自动折叠侧边栏（报告书有专属章节导航） */
  function collapseSidebarForReport() {
    sidebarExpanded.value = false
  }

  return {
    sidebarExpanded,
    rightPanelExpanded,
    rightPanelVisible,
    viewportMode,
    isCompactLayout,
    isMobileLayout,
    toggleSidebar,
    toggleRightPanel,
    openRightPanelIfAllowed,
    closeRightPanel,
    setViewportMode,
    collapseSidebarForReport,
  }
})
