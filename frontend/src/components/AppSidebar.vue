<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'
import { useNavStore } from '@/stores/nav'
import { useThemePreference } from '@/composables/useThemePreference'
import { MODULE_GROUPS, PRIMARY_NAV_ITEMS, getModuleMetaText, getStatusLabel } from '@/data/appModules'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const ui = useUiStore()
const nav = useNavStore()

const { theme, toggleTheme } = useThemePreference()
const knowledgeExpanded = ref(false)

onMounted(() => nav.initFromRoute(route.path))
watch(() => route.path, (path) => {
  nav.initFromRoute(path)
  if (nav.currentSectionId) knowledgeExpanded.value = true
})

function handlePrimaryClick(item: (typeof PRIMARY_NAV_ITEMS)[number]) {
  if (item.action === 'toggle-ai') {
    ui.toggleRightPanel()
    return
  }
  nav.currentSectionId = null
  if (item.path && route.path !== item.path) router.push(item.path)
}

function handleModuleClick(path?: string) {
  if (!path) return
  if (route.path !== path) router.push(path)
}

function onSectionClick(sectionId: string, sectionRoute: string) {
  nav.selectSection(sectionId)
  knowledgeExpanded.value = true
  if (sectionRoute && !route.path.startsWith(sectionRoute)) {
    router.push(sectionRoute)
  }
  ui.openRightPanelIfAllowed()
}

function isPrimaryActive(item: (typeof PRIMARY_NAV_ITEMS)[number]) {
  if (item.action === 'toggle-ai') return ui.rightPanelVisible && !nav.currentSectionId
  return !!item.path && route.path.startsWith(item.path) && !nav.currentSectionId
}

function isModuleActive(path?: string) {
  return !!path && route.path.startsWith(path)
}

function logout() {
  auth.clearToken()
  router.push('/login')
}
</script>

<template>
  <aside class="sidebar" :class="{ collapsed: !ui.sidebarExpanded }">
    <div class="sidebar-header">
      <span class="sidebar-logo">命理工作台</span>
      <button class="toggle-btn" @click="ui.toggleSidebar" :title="ui.sidebarExpanded ? '折叠侧栏' : '展开侧栏'">
        <span class="toggle-icon">{{ ui.sidebarExpanded ? '‹' : '›' }}</span>
      </button>
    </div>

    <div class="sidebar-scroll">
      <div class="primary-section">
        <button
          v-for="item in PRIMARY_NAV_ITEMS"
          :key="item.key"
          class="primary-item"
          :class="{ active: isPrimaryActive(item) }"
          @click="handlePrimaryClick(item)"
          :title="!ui.sidebarExpanded ? item.label : undefined"
        >
          <span class="item-icon">{{ item.icon }}</span>
          <span class="item-body">
            <span class="item-label">{{ item.label }}</span>
            <span class="item-desc">{{ item.description }}</span>
          </span>
        </button>
      </div>

      <div class="nav-divider" />

      <section v-for="group in MODULE_GROUPS" :key="group.id" class="module-group">
        <div class="section-title-row">
          <span class="section-title">{{ group.label }}</span>
          <span v-if="ui.sidebarExpanded" class="section-hint">{{ group.items.length }} 项</span>
        </div>

        <button
          v-for="item in group.items"
          :key="item.key"
          class="module-item"
          :class="{ active: isModuleActive(item.path), disabled: !item.path }"
          @click="handleModuleClick(item.path)"
          :title="!ui.sidebarExpanded ? item.label : undefined"
        >
          <span class="item-icon module-icon">{{ item.icon }}</span>
          <span class="item-body">
            <span class="item-row">
              <span class="item-label">{{ item.label }}</span>
              <span class="status-chip" :class="item.status">{{ getStatusLabel(item.status) }}</span>
            </span>
            <span class="item-desc">{{ getModuleMetaText(item) }}</span>
          </span>
        </button>
      </section>

      <div class="nav-divider" />

      <section class="knowledge-section">
        <button
          class="knowledge-toggle"
          :class="{ open: knowledgeExpanded }"
          @click="knowledgeExpanded = !knowledgeExpanded"
          :title="!ui.sidebarExpanded ? '知识体系' : undefined"
        >
          <span class="item-icon">📚</span>
          <span class="item-body">
            <span class="item-label">知识参考</span>
            <span class="item-desc">保留知识树，作为辅助阅读与查询入口</span>
          </span>
          <span class="ch-arrow" :class="{ rotated: knowledgeExpanded }">›</span>
        </button>

        <div class="knowledge-tree" :class="{ open: knowledgeExpanded }">
          <div v-for="chapter in nav.NAV_CHAPTERS" :key="chapter.id" class="chapter">
            <button
              class="chapter-header"
              :class="{
                'ch-expanded': nav.expandedChapterId === chapter.id,
                'ch-active': nav.currentChapter?.id === chapter.id,
              }"
              :style="nav.currentChapter?.id === chapter.id ? `--ch-color: ${chapter.color}` : ''"
              @click="nav.toggleChapter(chapter.id)"
              :title="!ui.sidebarExpanded ? `${chapter.num}. ${chapter.label}` : undefined"
            >
              <span class="ch-icon" :style="`color: ${chapter.color}`">{{ chapter.icon }}</span>
              <span class="ch-info">
                <span class="ch-num">{{ chapter.num }}</span>
                <span class="ch-label">{{ chapter.label }}</span>
              </span>
              <span class="ch-arrow" :class="{ rotated: nav.expandedChapterId === chapter.id }">›</span>
            </button>

            <div class="section-list" :class="{ open: nav.expandedChapterId === chapter.id }">
              <button
                v-for="sec in chapter.sections"
                :key="sec.id"
                class="section-item"
                :class="{ 'sec-active': nav.currentSectionId === sec.id }"
                :style="nav.currentSectionId === sec.id ? `--sec-color: ${chapter.color}` : ''"
                @click="onSectionClick(sec.id, sec.route)"
              >
                <span class="sec-num">{{ sec.num }}</span>
                <span class="sec-label">{{ sec.label }}</span>
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>

    <div class="sidebar-footer">
      <button class="footer-btn" @click="toggleTheme" :title="!ui.sidebarExpanded ? (theme === 'bazi' ? '科技主题' : '山水主题') : undefined">
        <span class="item-icon">{{ theme === 'bazi' ? '☉' : '☯' }}</span>
        <span class="item-label footer-label">{{ theme === 'bazi' ? '科技主题' : '山水主题' }}</span>
      </button>

      <button class="footer-btn logout-btn" @click="logout" :title="!ui.sidebarExpanded ? '退出登录' : undefined">
        <span class="item-icon">⬡</span>
        <span class="item-label footer-label">{{ auth.username || '当前用户' }}</span>
      </button>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  width: 296px;
  height: 100vh;
  background: #161e2d;
  border-right: 1px solid rgba(255,255,255,.06);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: width var(--transition-base);
  flex-shrink: 0;
  z-index: 100;
}

.sidebar.collapsed { width: 72px; }

.sidebar-header {
  height: 56px;
  padding: 0 10px 0 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(255,255,255,.07);
  flex-shrink: 0;
}

.sidebar-logo {
  font-size: 14px;
  font-weight: 700;
  color: #f0f4ff;
  letter-spacing: .03em;
  white-space: nowrap;
  transition: opacity var(--transition-fast);
}

.sidebar.collapsed .sidebar-logo {
  opacity: 0;
  pointer-events: none;
  width: 0;
}

.toggle-btn {
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  cursor: pointer;
  color: #6b7280;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
}

.toggle-btn:hover { background: rgba(255,255,255,.08); color: #d1d5db; }
.toggle-icon { font-size: 18px; line-height: 1; }

.sidebar-scroll {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 10px 8px 12px;
}

.primary-section,
.module-group,
.knowledge-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.module-group + .module-group { margin-top: 12px; }

.section-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 0 8px;
}

.section-title {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .08em;
  color: #64748b;
}

.section-hint { font-size: 10px; color: #4b5563; }

.primary-item,
.module-item,
.knowledge-toggle,
.footer-btn {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  width: 100%;
  padding: 10px;
  border: none;
  background: transparent;
  border-radius: 10px;
  cursor: pointer;
  color: #cbd5e1;
  text-align: left;
  transition: background var(--transition-fast), color var(--transition-fast), border-color var(--transition-fast);
}

.primary-item:hover,
.module-item:hover,
.knowledge-toggle:hover,
.footer-btn:hover { background: rgba(255,255,255,.06); color: #f8fafc; }

.primary-item.active,
.module-item.active,
.knowledge-toggle.open { background: rgba(59,130,246,.14); color: #bfdbfe; }

.module-item.disabled { opacity: .7; }

.item-icon {
  width: 24px;
  min-width: 24px;
  text-align: center;
  font-size: 15px;
  font-weight: 700;
  line-height: 24px;
}

.module-icon {
  border-radius: 8px;
  background: rgba(255,255,255,.06);
}

.item-body {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  flex: 1;
  transition: opacity var(--transition-fast);
}

.item-label {
  font-size: 13px;
  font-weight: 600;
  color: currentColor;
}

.item-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.item-desc {
  font-size: 11px;
  color: #94a3b8;
  line-height: 1.45;
}

.status-chip {
  display: inline-flex;
  align-items: center;
  height: 18px;
  padding: 0 7px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 700;
  white-space: nowrap;
}

.status-chip.ready { background: rgba(34,197,94,.16); color: #86efac; }
.status-chip.integrated { background: rgba(99,102,241,.18); color: #c4b5fd; }
.status-chip.planned { background: rgba(148,163,184,.14); color: #cbd5e1; }

.knowledge-toggle { align-items: center; }

.knowledge-tree {
  max-height: 0;
  overflow: hidden;
  transition: max-height .25s ease;
}

.knowledge-tree.open { max-height: 1600px; }
.chapter { margin-top: 4px; }

.chapter-header {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 8px 10px;
  border: none;
  background: transparent;
  border-radius: 8px;
  cursor: pointer;
  color: #9ca3af;
  text-align: left;
}

.chapter-header:hover { background: rgba(255,255,255,.05); color: #e5e7eb; }
.chapter-header.ch-expanded { background: rgba(255,255,255,.05); color: #e5e7eb; }
.chapter-header.ch-active { color: var(--ch-color, #93c5fd); }

.ch-icon { width: 20px; text-align: center; font-size: 13px; }

.ch-info {
  flex: 1;
  display: flex;
  gap: 6px;
  overflow: hidden;
  transition: opacity var(--transition-fast);
}

.ch-num { font-size: 11px; color: #4b5563; }
.ch-label { font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.ch-arrow {
  font-size: 14px;
  color: #4b5563;
  transition: transform var(--transition-fast), opacity var(--transition-fast);
}

.ch-arrow.rotated { transform: rotate(90deg); color: #9ca3af; }

.section-list {
  max-height: 0;
  overflow: hidden;
  transition: max-height .22s ease;
  padding-left: 10px;
}

.section-list.open { max-height: 640px; }

.section-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: calc(100% - 8px);
  margin-left: 8px;
  padding: 6px 8px;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  color: #6b7280;
  font-size: 12px;
  text-align: left;
  border-left: 2px solid transparent;
}

.section-item:hover { background: rgba(255,255,255,.05); color: #d1d5db; }

.section-item.sec-active {
  color: var(--sec-color, #93c5fd);
  background: rgba(99,102,241,.12);
  border-left-color: var(--sec-color, #6366f1);
}

.sec-num { min-width: 28px; font-size: 10px; color: #4b5563; }
.sec-label { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.nav-divider {
  height: 1px;
  background: rgba(255,255,255,.06);
  margin: 12px 8px;
}

.sidebar-footer {
  border-top: 1px solid rgba(255,255,255,.07);
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.footer-label {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.logout-btn:hover { color: #fca5a5; }

.sidebar.collapsed .item-body,
.sidebar.collapsed .ch-info,
.sidebar.collapsed .section-title,
.sidebar.collapsed .section-hint,
.sidebar.collapsed .footer-label,
.sidebar.collapsed .ch-arrow {
  opacity: 0;
  pointer-events: none;
  width: 0;
}

.sidebar.collapsed .primary-item,
.sidebar.collapsed .module-item,
.sidebar.collapsed .knowledge-toggle,
.sidebar.collapsed .footer-btn,
.sidebar.collapsed .chapter-header {
  justify-content: center;
  padding-left: 8px;
  padding-right: 8px;
}

.sidebar.collapsed .knowledge-tree.open,
.sidebar.collapsed .section-list.open { max-height: 0; }
</style>
