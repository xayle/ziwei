/**
 * ui.ts — 全局 UI 状态（侧边栏 / 右栏展开态）
 * 持久化到 localStorage，避免刷新后布局跳动
 */
import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export const useUiStore = defineStore('ui', () => {
  // ── 侧边栏 ──────────────────────────────────────────────────
  const sidebarExpanded = ref<boolean>(
    localStorage.getItem('ui_sidebar') !== 'false'
  )

  // ── 右侧 AI 面板 ──────────────────────────────────────────────
  const rightPanelExpanded = ref<boolean>(
    localStorage.getItem('ui_rightpanel') === 'true'
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

  /** 进入报告书时自动折叠侧边栏（报告书有专属章节导航） */
  function collapseSidebarForReport() {
    sidebarExpanded.value = false
  }

  return {
    sidebarExpanded,
    rightPanelExpanded,
    toggleSidebar,
    toggleRightPanel,
    collapseSidebarForReport,
  }
})
