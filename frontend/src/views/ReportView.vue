<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useReportStore } from '@/stores/report'
import ReportChapterNav  from '@/components/report/ReportChapterNav.vue'
import ReportSectionList from '@/components/report/ReportSectionList.vue'
import ReportContent     from '@/components/report/ReportContent.vue'
import ReportAnnotation  from '@/components/report/ReportAnnotation.vue'
import CasePicker        from '@/components/report/CasePicker.vue'

const route = useRoute()
const store = useReportStore()

// ─── 案例加载 ─────────────────────────────────────────────────
onMounted(async () => {
  const id = route.params.caseId as string | undefined
  if (id) {
    await store.loadCase(id)
    store.restoreFromSession()
  } else {
    await store.loadCaseList()
  }
})

watch(() => route.params.caseId, async (id) => {
  if (typeof id === 'string' && id) {
    await store.loadCase(id)
    store.restoreFromSession()
  }
})
</script>

<template>
  <!-- 无 caseId 且无已加载案例 → 案例选择器 -->
  <div v-if="!route.params.caseId && !store.caseData" class="report-picker-wrap">
    <CasePicker />
  </div>

  <!-- 主报告布局 -->
  <div v-else id="cr" class="report-layout"
    :data-ready="!store.caseLoading && !!store.caseData && !!store.baziData && !!store.ziweiData && !!store.nameData"
  >

    <!-- 列1: 56px 章节图标导航 -->
    <ReportChapterNav class="col-nav" />

    <!-- 列2: 220px 小节列表 -->
    <ReportSectionList class="col-toc" />

    <!-- 列3: 1fr 内容区 -->
    <ReportContent class="col-content" />

    <!-- 列4: 280px 批注卡组 -->
    <ReportAnnotation class="col-cards" />
  </div>
</template>

<style scoped>
/* ─── 报告书四栏布局 ─────────────────────────────────────────── */
.report-layout {
  display: grid;
  grid-template-columns: 56px 220px 1fr 280px;
  height: 100vh;   /* AppNav 已移入 AppSidebar，整体高度占满 */
  overflow: hidden;
  background: var(--bg);
}

.col-nav {
  grid-column: 1;
  border-right: 1px solid var(--border);
  overflow-y: auto;
}

.col-toc {
  grid-column: 2;
  border-right: 1px solid var(--border);
  overflow-y: auto;
  background: var(--surface);
}

.col-content {
  grid-column: 3;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.col-cards {
  grid-column: 4;
  border-left: 1px solid var(--border);
  background: var(--surface);
}

/* ─── 案例选择器页面 ─────────────────────────────────────── */
.report-picker-wrap {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

@media (max-width: 1280px) {
  .report-layout {
    grid-template-columns: 56px 180px 1fr 240px;
  }
}
</style>
