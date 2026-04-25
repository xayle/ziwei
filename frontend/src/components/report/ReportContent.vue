<script setup lang="ts">
/**
 * ReportContent.vue — 报告书第三列（内容区）
 * 包含顶部栏、章节内容渲染，以及 ScrollSpy 逻辑
 */
import { onMounted, onBeforeUnmount, ref, watch } from 'vue'
import { useReportStore } from '@/stores/report'
import ReportTopBar    from './ReportTopBar.vue'
import ChapterPersonal from './chapters/ChapterPersonal.vue'
import ChapterBazi     from './chapters/ChapterBazi.vue'
import ChapterZiwei    from './chapters/ChapterZiwei.vue'
import ChapterName     from './chapters/ChapterName.vue'
import ChapterZeri     from './chapters/ChapterZeri.vue'
import ChapterOtherCN  from './chapters/ChapterOtherCN.vue'
import ChapterStub     from './chapters/ChapterStub.vue'

const store = useReportStore()

// ─── 章节组件映射 ─────────────────────────────────────────────
const CHAPTER_COMPONENTS: Record<number, unknown> = {
  1: ChapterPersonal,
  2: ChapterBazi,
  3: ChapterZiwei,
  4: ChapterName,
  5: ChapterZeri,
  6: ChapterOtherCN,
  7: ChapterStub,
  8: ChapterStub,
}

// ─── Scroll Spy ───────────────────────────────────────────────
const contentBodyRef = ref<HTMLElement | null>(null)
let scrollObserver: IntersectionObserver | null = null

function setupScrollSpy() {
  destroyScrollSpy()
  const root = contentBodyRef.value
  if (!root) return

  scrollObserver = new IntersectionObserver(
    (entries) => {
      const visible = entries
        .filter(e => e.isIntersecting)
        .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)
      if (visible.length) {
        const id = visible[0].target.id.replace(/^section-/, '')
        store.setActiveSection(id)
      }
    },
    { root, rootMargin: '-30% 0px -60% 0px', threshold: 0 },
  )

  root.querySelectorAll<HTMLElement>('section[id^="section-"]').forEach(el => {
    scrollObserver!.observe(el)
  })
}

function destroyScrollSpy() {
  scrollObserver?.disconnect()
  scrollObserver = null
}

watch(() => store.activeChapter, () => {
  setTimeout(setupScrollSpy, 120)
})

onMounted(setupScrollSpy)
onBeforeUnmount(destroyScrollSpy)
</script>

<template>
  <div class="report-content">
    <!-- 顶部固定栏 -->
    <ReportTopBar />

    <!-- 主内容滚动区 -->
    <main ref="contentBodyRef" class="content-body">
      <!-- 加载中骨架屏 -->
      <div v-if="store.caseLoading" class="loading-wrap">
        <div class="skel-card" v-for="i in 3" :key="i"></div>
      </div>

      <!-- 加载失败 -->
      <div v-else-if="store.caseError" class="error-card">
        <p class="error-msg">{{ store.caseError }}</p>
        <button class="btn-secondary" @click="store.loadCase(store.caseId!)">重新加载</button>
      </div>

      <!-- 章节内容 -->
      <component
        v-else-if="store.caseData"
        :is="CHAPTER_COMPONENTS[store.activeChapter]"
        :chapter-num="store.activeChapter"
      />
    </main>
  </div>
</template>

<style scoped>
/* ─── 外层容器（由父注入 col-content 的网格定位） ─────────────── */
.report-content {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  height: 100%;
}

/* ─── 内容滚动区 ──────────────────────────────────────────────── */
.content-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--sp-6) var(--sp-6) var(--sp-8);
}

/* ─── 加载骨架屏 ──────────────────────────────────────────────── */
.loading-wrap {
  display: flex;
  flex-direction: column;
  gap: var(--sp-6);
  padding-top: var(--sp-2);
}

.skel-card {
  height: 160px;
  border-radius: var(--radius);
  background: linear-gradient(90deg, #e2e8f0 25%, #f1f5f9 50%, #e2e8f0 75%);
  background-size: 400px;
  animation: shimmer 1.2s infinite;
}

@keyframes shimmer {
  from { background-position: -400px 0; }
  to   { background-position:  400px 0; }
}

/* ─── 错误态 ──────────────────────────────────────────────────── */
.error-card {
  padding: var(--sp-8);
  background: var(--surface);
  border-radius: var(--radius);
  border: 1px solid var(--border);
  text-align: center;
}

.error-msg {
  color: var(--danger);
  margin-bottom: var(--sp-4);
}

.btn-secondary {
  padding: 8px 16px;
  background: transparent;
  border: 1px solid var(--border-md);
  border-radius: var(--radius-sm);
  font-size: var(--fs-sm);
  cursor: pointer;
  color: var(--text-2);
  transition: border-color var(--dur-fast), color var(--dur-fast);
}
.btn-secondary:hover {
  border-color: var(--accent);
  color: var(--accent);
}
</style>
