<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useReportStore } from '@/stores/report'
import { fetchDrafts } from '@/api/llm'
import { getClassics, getConcepts } from '@/api/static-data'
import { MODULE_GROUPS, getStatusLabel } from '@/data/appModules'

const router = useRouter()
const report = useReportStore()

const draftsCount = ref<number | null>(null)
const conceptsCount = ref<number | null>(null)
const classicsCount = ref<number | null>(null)
const loading = ref(true)

const caseCount = computed(() => report.caseList.length)
const recentCases = computed(() => report.caseList.slice(0, 6))

const workflowSteps = [
  {
    title: '1. 建立案例',
    desc: '先在案例工作台创建或同步客户档案，统一承接后续命盘、AI 与报告流转。',
    path: '/workbench',
  },
  {
    title: '2. 进入分析模块',
    desc: '根据需求进入八字、紫微、姓名、择日、西占等独立模块，不再堆叠到一个超级页面。',
    path: '/bazi',
  },
  {
    title: '3. 生成输出',
    desc: '需要沉淀时进入报告书、AI 草稿和审核流，形成标准化交付。',
    path: '/report',
  },
]

const summaryCards = computed(() => [
  {
    label: '案例总数',
    value: caseCount.value,
    hint: '来自 /api/v1/cases',
  },
  {
    label: 'AI 草稿',
    value: draftsCount.value ?? '—',
    hint: '来自 /api/v1/llm/drafts',
  },
  {
    label: '概念词条',
    value: conceptsCount.value ?? '—',
    hint: '来自 /api/v1/docs/concepts',
  },
  {
    label: '古籍片段',
    value: classicsCount.value ?? '—',
    hint: '来自 /api/v1/classics',
  },
])

async function loadOverview() {
  loading.value = true
  await report.loadCaseList()
  const [draftsRes, conceptsRes, classicsRes] = await Promise.allSettled([
    fetchDrafts({ limit: 50 }),
    getConcepts({ limit: 200 }),
    getClassics({ limit: 100 }),
  ])

  draftsCount.value = draftsRes.status === 'fulfilled' ? draftsRes.value.total : null
  conceptsCount.value = conceptsRes.status === 'fulfilled' ? conceptsRes.value.length : null
  classicsCount.value = classicsRes.status === 'fulfilled' ? classicsRes.value.length : null
  loading.value = false
}

function openPath(path?: string) {
  if (!path) return
  router.push(path)
}

onMounted(() => {
  void loadOverview()
})
</script>

<template>
  <main class="home-view">
    <section class="home-hero card">
      <div>
        <p class="hero-kicker">后端能力驱动的前端总览</p>
        <h1 class="hero-title">命理中控总览</h1>
        <p class="hero-desc">
          首页先按真实 API 模块组织入口，把“分析、案例、内容、治理”拆开，避免所有功能挤在单一页面中。
        </p>
      </div>
      <div class="hero-actions">
        <button class="btn-primary" @click="openPath('/workbench')">进入案例工作台</button>
        <button class="btn-secondary" @click="openPath('/ziwei')">查看紫微模块</button>
      </div>
    </section>

    <section class="summary-grid">
      <article v-for="card in summaryCards" :key="card.label" class="summary-card card">
        <div class="summary-label">{{ card.label }}</div>
        <div class="summary-value">{{ loading ? '...' : card.value }}</div>
        <div class="summary-hint">{{ card.hint }}</div>
      </article>
    </section>

    <section class="content-grid">
      <div class="content-main">
        <section v-for="group in MODULE_GROUPS" :key="group.id" class="card module-section">
          <div class="section-head">
            <div>
              <h2 class="section-title">{{ group.label }}</h2>
              <p class="section-desc">{{ group.description }}</p>
            </div>
          </div>

          <div class="module-grid">
            <article v-for="item in group.items" :key="item.key" class="module-card">
              <div class="module-top">
                <div class="module-icon">{{ item.icon }}</div>
                <span class="module-status" :class="item.status">{{ getStatusLabel(item.status) }}</span>
              </div>
              <h3 class="module-title">{{ item.label }}</h3>
              <p class="module-desc">{{ item.description }}</p>
              <p v-if="item.note" class="module-note">{{ item.note }}</p>
              <div class="module-backend">
                <span v-for="api in item.backend" :key="api" class="backend-chip">{{ api }}</span>
                <span v-if="!item.backend.length" class="backend-chip muted">暂无独立 API</span>
              </div>
              <button class="module-link" :disabled="!item.path" @click="openPath(item.path)">
                {{ item.path ? '打开模块' : '等待后端能力' }}
              </button>
            </article>
          </div>
        </section>
      </div>

      <aside class="content-side">
        <section class="card side-section">
          <div class="section-head compact">
            <div>
              <h2 class="section-title">最近案例</h2>
              <p class="section-desc">从案例中心继续进入分析与输出。</p>
            </div>
          </div>
          <div v-if="recentCases.length" class="recent-list">
            <button
              v-for="item in recentCases"
              :key="item.id"
              class="recent-item"
              @click="openPath('/workbench')"
            >
              <div>
                <div class="recent-name">{{ item.name }}</div>
                <div class="recent-meta">{{ item.city || item.tz || '未设地点' }} · {{ item.birth_dt_local.slice(0, 10) }}</div>
              </div>
              <span class="recent-arrow">›</span>
            </button>
          </div>
          <div v-else class="empty-state">暂无案例，可先进入工作台新建。</div>
        </section>

        <section class="card side-section">
          <div class="section-head compact">
            <div>
              <h2 class="section-title">建议工作流</h2>
              <p class="section-desc">先收口信息架构，再逐页迁移入口。</p>
            </div>
          </div>
          <div class="workflow-list">
            <button v-for="step in workflowSteps" :key="step.title" class="workflow-item" @click="openPath(step.path)">
              <div class="workflow-title">{{ step.title }}</div>
              <div class="workflow-desc">{{ step.desc }}</div>
            </button>
          </div>
        </section>
      </aside>
    </section>
  </main>
</template>

<style scoped>
.home-view {
  height: 100%;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 18px;
  box-shadow: var(--shadow-sm);
}

.home-hero {
  padding: 28px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.08), rgba(217, 119, 6, 0.08));
}

.hero-kicker {
  font-size: 12px;
  font-weight: 700;
  color: var(--accent-dark);
  letter-spacing: .08em;
  text-transform: uppercase;
}

.hero-title {
  margin-top: 6px;
  font-size: 30px;
  line-height: 1.15;
  color: var(--text);
}

.hero-desc {
  margin-top: 12px;
  max-width: 760px;
  font-size: 14px;
  color: var(--text-2);
}

.hero-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.btn-primary,
.btn-secondary,
.module-link {
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-primary {
  padding: 10px 16px;
  border: none;
  background: var(--accent);
  color: #fff;
}

.btn-primary:hover { background: var(--accent-dark); }

.btn-secondary {
  padding: 10px 16px;
  border: 1px solid var(--border-md);
  background: rgba(255,255,255,.86);
  color: var(--text);
}

.btn-secondary:hover { border-color: var(--accent); color: var(--accent-dark); }

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.summary-card {
  padding: 20px;
}

.summary-label {
  font-size: 12px;
  color: var(--text-3);
}

.summary-value {
  margin-top: 10px;
  font-size: 30px;
  line-height: 1;
  font-weight: 700;
  color: var(--text);
}

.summary-hint {
  margin-top: 10px;
  font-size: 12px;
  color: var(--text-2);
}

.content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.8fr) minmax(300px, .9fr);
  gap: 20px;
  min-height: 0;
}

.content-main,
.content-side {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.module-section,
.side-section {
  padding: 20px;
}

.section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.section-head.compact {
  margin-bottom: 14px;
}

.section-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--text);
}

.section-desc {
  margin-top: 4px;
  font-size: 13px;
  color: var(--text-2);
}

.module-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.module-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 16px;
  border-radius: 14px;
  border: 1px solid var(--border);
  background: var(--surface-2);
}

.module-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.module-icon {
  width: 36px;
  height: 36px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  background: rgba(37, 99, 235, 0.1);
  color: var(--info-dark);
  font-weight: 700;
}

.module-status {
  padding: 4px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
}

.module-status.ready {
  background: #dcfce7;
  color: #15803d;
}

.module-status.integrated {
  background: #e0e7ff;
  color: #4338ca;
}

.module-status.planned {
  background: #f3f4f6;
  color: #6b7280;
}

.module-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--text);
}

.module-desc,
.module-note {
  font-size: 13px;
  color: var(--text-2);
}

.module-note {
  color: var(--accent-dark);
}

.module-backend {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.backend-chip {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 0 8px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: #fff;
  font-size: 11px;
  color: var(--text-2);
}

.backend-chip.muted {
  color: var(--text-3);
}

.module-link {
  margin-top: auto;
  padding: 10px 12px;
  border: 1px solid var(--border-md);
  background: #fff;
  color: var(--text);
}

.module-link:hover:not(:disabled) {
  border-color: var(--accent);
  color: var(--accent-dark);
}

.module-link:disabled {
  cursor: not-allowed;
  opacity: .55;
}

.recent-list,
.workflow-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.recent-item,
.workflow-item {
  width: 100%;
  border: 1px solid var(--border);
  background: var(--surface-2);
  border-radius: 12px;
  padding: 14px;
  text-align: left;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.recent-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.recent-item:hover,
.workflow-item:hover {
  border-color: var(--accent);
  background: #fff;
}

.recent-name,
.workflow-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--text);
}

.recent-meta,
.workflow-desc,
.empty-state {
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-2);
}

.recent-arrow {
  font-size: 20px;
  color: var(--text-3);
}

@media (max-width: 1280px) {
  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .content-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .home-view {
    padding: 16px;
  }

  .home-hero {
    flex-direction: column;
    padding: 20px;
  }

  .module-grid,
  .summary-grid {
    grid-template-columns: 1fr;
  }
}
</style>
