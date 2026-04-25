<script setup lang="ts">
/**
 * AppSidebar.vue — 命理中控系统 完整可折叠导航树
 * 两级结构：10 大章（accordion）→ 小节（可点击）
 * 展开 240px | 折叠 64px（只显示章节图标）
 */
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'
import { useNavStore } from '@/stores/nav'

const route  = useRoute()
const router = useRouter()
const auth   = useAuthStore()
const ui     = useUiStore()
const nav    = useNavStore()

// 工作台快捷入口（固定在顶部，不属于知识树）
const QUICK_ITEMS = [
  { key: 'workbench', label: '工作台',  icon: '🗂', path: '/workbench' },
  { key: 'profile',  label: '个人信息', icon: '👤', path: '/profile' },
]

// 初始化：根据当前路由展开对应章节
onMounted(() => nav.initFromRoute(route.path))
watch(() => route.path, (p) => nav.initFromRoute(p))

// 点击小节：更新 nav store + 路由跳转 + 打开右侧面板
function onSectionClick(sectionId: string, sectionRoute: string) {
  nav.selectSection(sectionId)
  if (sectionRoute && !route.path.startsWith(sectionRoute)) {
    router.push(sectionRoute)
  }
  // 选中小节后自动打开右侧面板展示内容
  if (!ui.rightPanelExpanded) ui.toggleRightPanel()
}

// ── 主题切换 ──────────────────────────────────────────────────────────
const theme = ref<'default' | 'bazi'>('default')

function initTheme() {
  const saved = localStorage.getItem('theme') as 'default' | 'bazi' | null
  if (saved === 'bazi') {
    theme.value = 'bazi'
    document.documentElement.dataset.theme = 'bazi'
  }
}

function toggleTheme() {
  theme.value = theme.value === 'default' ? 'bazi' : 'default'
  if (theme.value === 'bazi') {
    document.documentElement.dataset.theme = 'bazi'
    localStorage.setItem('theme', 'bazi')
  } else {
    delete document.documentElement.dataset.theme
    localStorage.setItem('theme', 'default')
  }
}

onMounted(initTheme)

function logout() {
  auth.clearToken()
  router.push('/login')
}
</script>

<template>
  <aside class="sidebar" :class="{ collapsed: !ui.sidebarExpanded }">

    <!-- ── 头部 ── -->
    <div class="sidebar-header">
      <span class="sidebar-logo">命理中控系统</span>
      <button class="toggle-btn" @click="ui.toggleSidebar"
        :title="ui.sidebarExpanded ? '折叠侧栏' : '展开侧栏'">
        <span class="toggle-icon">{{ ui.sidebarExpanded ? '‹' : '›' }}</span>
      </button>
    </div>

    <!-- ── 可滚动导航区 ── -->
    <div class="sidebar-scroll">

      <!-- 快捷入口 -->
      <div class="quick-section">
        <button
          v-for="item in QUICK_ITEMS"
          :key="item.key"
          class="quick-item"
          :class="{ active: route.path.startsWith(item.path) && !nav.currentSectionId }"
          @click="() => { nav.currentSectionId = null; router.push(item.path) }"
          :title="!ui.sidebarExpanded ? item.label : undefined"
        >
          <span class="q-icon">{{ item.icon }}</span>
          <span class="q-label">{{ item.label }}</span>
        </button>

        <!-- AI 助手 -->
        <button
          class="quick-item"
          :class="{ active: ui.rightPanelExpanded && !nav.currentSectionId }"
          @click="ui.toggleRightPanel"
          :title="!ui.sidebarExpanded ? 'AI 助手' : undefined"
        >
          <span class="q-icon">🤖</span>
          <span class="q-label">AI 助手</span>
        </button>
      </div>

      <div class="nav-divider" />
      <div class="nav-section-title">
        <span class="section-title-text">知识体系</span>
      </div>

      <!-- ── 10 大章 accordion ── -->
      <div class="chapter-list">
        <div
          v-for="chapter in nav.NAV_CHAPTERS"
          :key="chapter.id"
          class="chapter"
        >
          <!-- 章节标题行 -->
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
            <span
              class="ch-arrow"
              :class="{ rotated: nav.expandedChapterId === chapter.id }"
            >›</span>
          </button>

          <!-- 小节列表（展开时显示） -->
          <div
            class="section-list"
            :class="{ open: nav.expandedChapterId === chapter.id }"
          >
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
    </div>

    <!-- ── 底部工具栏 ── -->
    <div class="sidebar-footer">
      <button class="footer-btn" @click="toggleTheme"
        :title="!ui.sidebarExpanded ? (theme === 'bazi' ? '科技主题' : '山水主题') : undefined">
        <span class="q-icon">{{ theme === 'bazi' ? '☉' : '☯' }}</span>
        <span class="q-label">{{ theme === 'bazi' ? '科技主题' : '山水主题' }}</span>
      </button>

      <button class="footer-btn logout-btn" @click="logout"
        :title="!ui.sidebarExpanded ? '退出登录' : undefined">
        <span class="q-icon">⬡</span>
        <span class="q-label user-label">{{ auth.username }}</span>
        <span class="q-label logout-hint">退出</span>
      </button>
    </div>

  </aside>
</template>

<style scoped>
/* ── 根布局 ───────────────────────────────────────────────────── */
.sidebar {
  width: 240px;
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
.sidebar.collapsed { width: 64px; }

/* ── 头部 ─────────────────────────────────────────────────────── */
.sidebar-header {
  height: 52px;
  padding: 0 10px 0 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(255,255,255,.07);
  flex-shrink: 0;
}
.sidebar-logo {
  font-size: 0.8125rem;
  font-weight: 700;
  color: #f0f4ff;
  letter-spacing: .03em;
  white-space: nowrap;
  opacity: 1;
  transition: opacity var(--transition-fast);
}
.sidebar.collapsed .sidebar-logo {
  opacity: 0;
  pointer-events: none;
  width: 0;
}
.toggle-btn {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  cursor: pointer;
  color: #6b7280;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 5px;
  transition: background var(--transition-fast), color var(--transition-fast);
}
.toggle-btn:hover { background: rgba(255,255,255,.08); color: #d1d5db; }
.toggle-icon { font-size: 18px; line-height: 1; }

/* ── 滚动导航区 ───────────────────────────────────────────────── */
.sidebar-scroll {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 6px 0 4px;
  scrollbar-width: thin;
  scrollbar-color: rgba(255,255,255,.06) transparent;
}
.sidebar-scroll::-webkit-scrollbar { width: 4px; }
.sidebar-scroll::-webkit-scrollbar-thumb { background: rgba(255,255,255,.06); border-radius: 2px; }

/* ── 快捷入口 ─────────────────────────────────────────────────── */
.quick-section {
  padding: 0 8px;
  display: flex;
  flex-direction: column;
  gap: 1px;
}
.quick-item {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 7px 8px;
  border: none;
  background: transparent;
  border-radius: 7px;
  cursor: pointer;
  color: #9ca3af;
  font-size: 0.8125rem;
  text-align: left;
  white-space: nowrap;
  width: 100%;
  transition: background var(--transition-fast), color var(--transition-fast);
  font-family: var(--font-ui);
}
.quick-item:hover { background: rgba(255,255,255,.07); color: #e5e7eb; }
.quick-item.active { background: rgba(59,130,246,.2); color: #93c5fd; }
.q-icon { width: 20px; text-align: center; flex-shrink: 0; font-size: 14px; }
.q-label {
  overflow: hidden;
  white-space: nowrap;
  opacity: 1;
  transition: opacity var(--transition-fast);
}
.sidebar.collapsed .q-label { opacity: 0; pointer-events: none; width: 0; }

/* ── 分割线 & 标签 ────────────────────────────────────────────── */
.nav-divider {
  height: 1px;
  background: rgba(255,255,255,.06);
  margin: 6px 10px;
}
.nav-section-title {
  padding: 0 12px 4px;
  overflow: hidden;
}
.section-title-text {
  font-size: 0.625rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .08em;
  color: #4b5563;
  white-space: nowrap;
  opacity: 1;
  transition: opacity var(--transition-fast);
}
.sidebar.collapsed .section-title-text { opacity: 0; }

/* ── 章节列表 ─────────────────────────────────────────────────── */
.chapter-list { padding: 0 6px; }
.chapter { margin-bottom: 1px; }

/* 章节标题行 */
.chapter-header {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 7px 8px;
  border: none;
  background: transparent;
  border-radius: 7px;
  cursor: pointer;
  color: #9ca3af;
  font-size: 0.8125rem;
  text-align: left;
  transition: background var(--transition-fast), color var(--transition-fast);
  font-family: var(--font-ui);
}
.chapter-header:hover { background: rgba(255,255,255,.06); color: #d1d5db; }
.chapter-header.ch-expanded { color: #e5e7eb; background: rgba(255,255,255,.05); }
.chapter-header.ch-active { color: var(--ch-color, #93c5fd); }

.ch-icon {
  width: 20px;
  text-align: center;
  flex-shrink: 0;
  font-size: 13px;
  font-weight: 700;
}
.ch-info {
  flex: 1;
  display: flex;
  gap: 5px;
  align-items: baseline;
  overflow: hidden;
  opacity: 1;
  transition: opacity var(--transition-fast);
}
.sidebar.collapsed .ch-info { opacity: 0; pointer-events: none; width: 0; }
.ch-num {
  font-size: 0.6875rem;
  color: #4b5563;
  flex-shrink: 0;
}
.ch-label {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 0.8125rem;
}
.ch-arrow {
  font-size: 13px;
  color: #4b5563;
  transition: transform var(--transition-fast), opacity var(--transition-fast);
  flex-shrink: 0;
  opacity: 1;
}
.ch-arrow.rotated { transform: rotate(90deg); color: #9ca3af; }
.sidebar.collapsed .ch-arrow { opacity: 0; }

/* ── 小节列表 ─────────────────────────────────────────────────── */
.section-list {
  display: flex;
  flex-direction: column;
  gap: 0;
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.22s ease;
  padding-left: 10px;
}
.section-list.open {
  max-height: 600px; /* 足够容纳最多 10 个小节 */
}
.sidebar.collapsed .section-list.open { max-height: 0; }

.section-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 8px;
  border: none;
  background: transparent;
  border-radius: 5px;
  cursor: pointer;
  color: #6b7280;
  font-size: 0.75rem;
  text-align: left;
  width: 100%;
  transition: background var(--transition-fast), color var(--transition-fast);
  font-family: var(--font-ui);
  border-left: 2px solid transparent;
  margin-left: 8px;
  width: calc(100% - 8px);
}
.section-item:hover { background: rgba(255,255,255,.05); color: #d1d5db; }
.section-item.sec-active {
  color: var(--sec-color, #93c5fd);
  background: rgba(99,102,241,.12);
  border-left-color: var(--sec-color, #6366f1);
}
.sec-num {
  font-size: 0.625rem;
  color: #374151;
  flex-shrink: 0;
  min-width: 26px;
}
.section-item.sec-active .sec-num { color: var(--sec-color, #6366f1); opacity: .7; }
.sec-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

/* ── 底部工具栏 ───────────────────────────────────────────────── */
.sidebar-footer {
  border-top: 1px solid rgba(255,255,255,.07);
  padding: 6px 8px 8px;
  display: flex;
  flex-direction: column;
  gap: 1px;
  flex-shrink: 0;
}
.footer-btn {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 6px 8px;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  color: #4b5563;
  font-size: 0.75rem;
  text-align: left;
  white-space: nowrap;
  width: 100%;
  transition: background var(--transition-fast), color var(--transition-fast);
  font-family: var(--font-ui);
}
.footer-btn:hover { background: rgba(255,255,255,.05); color: #9ca3af; }
.logout-btn:hover { color: #f87171; }
.user-label { flex: 1; overflow: hidden; text-overflow: ellipsis; }
.logout-hint {
  font-size: 0.625rem;
  color: #374151;
  flex-shrink: 0;
}
.sidebar.collapsed .q-label,
.sidebar.collapsed .logout-hint { opacity: 0; pointer-events: none; width: 0; }
</style>
