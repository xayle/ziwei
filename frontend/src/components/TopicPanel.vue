<script setup lang="ts">
/**
 * TopicPanel.vue — 右侧面板：当前选中小节的结构化内容
 * 显示：章节面包屑 | 内容区域 | 课题列表 | 右侧显示说明 | 通用工具项 | AI 操作
 */
import { computed, ref } from 'vue'
import { useNavStore } from '@/stores/nav'
import { useAiStore } from '@/stores/ai'
import type { CaseOut } from '@/api/report'
import { useReportStore } from '@/stores/report'

const nav = useNavStore()
const ai  = useAiStore()
const store = useReportStore()

const section = computed(() => nav.currentSection)
const chapter = computed(() => nav.currentChapter)
const selectedCase = computed(() => {
  const caseId = ai.currentCaseId
  return store.caseList.find(c => c.id === caseId) ?? null
})

// 通用显示项（每个课题都有）
const COMMON_ITEMS = [
  { icon: '📌', label: '标题与简短 canonical short answer（1–3 句）' },
  { icon: '📖', label: '详细解释（段落，可折叠）' },
  { icon: '📊', label: '数据视图／计算输出（四柱 JSON、五行统计、相位表、飞星矩阵）' },
  { icon: '📈', label: '可视化组件（柱图/盘图/时间轴/雷达/飞星图）' },
  { icon: '💡', label: '建议与行动项（短句 + 优先级）' },
  { icon: '🔗', label: '证据/来源（典籍、案例、检索 doc IDs）' },
  { icon: '✅', label: '审核与签名信息（谁审核、签名时间）' },
  { icon: '⚠️', label: '风险标注（高/中/低 + 合规提示）' },
  { icon: '📤', label: '导出/分享按钮（PDF、图片、链接）' },
  { icon: '🕐', label: '历史版本 / 审计记录（版本回滚）' },
]

// UI 组件提示
const UI_COMPONENTS = [
  'canonical 卡片（标题、短答、签名、来源）',
  '图表区（Bazi柱、紫微盘、五行雷达、大运时间轴、飞星图）',
  'RichText 编辑器 + Markdown 预览（带版本历史）',
  '小工具条（时区转换器、阴阳历切换、节气提示）',
  '对话助手浮窗（带来源列表）',
  '审计抽屉（弹出全部检索链路）',
]

const showCommon = ref(false)
const showUiComp = ref(false)

type QuickAction = 'adjust' | 'copy' | 'export' | 'share' | 'notes' | 'calendar' | 'compare' | 'bookmarks'

function emitQuickAction(action: QuickAction) {
  window.dispatchEvent(new CustomEvent<QuickAction>('ziwei:quick-action', { detail: action }))
}

// 快速发 AI 请求分析当前课题
function askAI() {
  if (!section.value) return
  const prompt = `请对该命理课题进行专业分析：\n章节：${chapter.value?.label} › ${section.value.label}\n课题涉及：${section.value.topics.map(t => t.label).join('、')}`
  ai.sendMessage(prompt)
}
</script>

<template>
  <div v-if="section" class="topic-panel">

    <!-- ── 面包屑 ── -->
    <div class="breadcrumb">
      <span class="bc-chapter" :style="`color: ${chapter?.color}`">{{ chapter?.num }}. {{ chapter?.label }}</span>
      <span class="bc-sep">›</span>
      <span class="bc-section">{{ section.num }} {{ section.label }}</span>
    </div>

    <!-- ── 内容区域（根据小节ID动态渲染） ── -->
    <div class="content-area">
      <!-- 1.1 生辰数据 -->
      <div v-if="section.id === 'bazi-birth'" class="content-block">
        <div class="content-title">生辰基本信息</div>
        <div class="content-grid">
          <div class="info-item">
            <div class="info-label">姓名</div>
            <div class="info-value">{{ selectedCase?.name ?? '—' }}</div>
          </div>
          <div class="info-item">
            <div class="info-label">性别</div>
            <div class="info-value">{{ selectedCase?.gender === 'male' ? '男' : '女' }}</div>
          </div>
          <div class="info-item">
            <div class="info-label">出生地</div>
            <div class="info-value">{{ selectedCase?.city ?? '—' }}</div>
          </div>
          <div class="info-item">
            <div class="info-label">出生时间（本地）</div>
            <div class="info-value" style="font-family: monospace">{{ selectedCase?.birth_dt_local?.slice(0, 16).replace('T', ' ') ?? '—' }}</div>
          </div>
          <div class="info-item">
            <div class="info-label">时区</div>
            <div class="info-value">{{ selectedCase?.tz ?? '—' }}</div>
          </div>
          <div class="info-item">
            <div class="info-label">经度</div>
            <div class="info-value" style="font-family: monospace">{{ selectedCase?.lon ?? '—' }}</div>
          </div>
          <div class="info-item">
            <div class="info-label">真太阳时</div>
            <div class="info-value">{{ selectedCase?.solar_time_enabled ? '✓ 已启用' : '— 未启用' }}</div>
          </div>
        </div>
        <div class="content-hint">💡 从左侧选择案例，生辰信息会自动加载。可在工作台编辑案例详情。</div>
      </div>

      <!-- 其他小节的内容区 -->
      <!-- 1.2 四柱基础 -->
      <div v-else-if="section.id === 'bazi-pillars'" class="content-block">
        <div class="content-title">四柱推演</div>
        <div class="content-placeholder">
          <p>📊 需要从工作台选定案例后，显示：</p>
          <ul style="margin: 8px 0 0; padding-left: 20px; font-size: 12px; color: var(--text-3); line-height: 1.8;">
            <li>年柱（干支与纳音）</li>
            <li>月柱（干支与纳音）</li>
            <li>日柱（干支与纳音）</li>
            <li>时柱（干支与纳音）</li>
          </ul>
        </div>
      </div>

      <!-- 1.3 日主与十神 -->
      <div v-else-if="section.id === 'bazi-daymaster'" class="content-block">
        <div class="content-title">日主与十神分析</div>
        <div class="content-placeholder">
          <p>🎯 需要从工作台选定案例后，显示：</p>
          <ul style="margin: 8px 0 0; padding-left: 20px; font-size: 12px; color: var(--text-3); line-height: 1.8;">
            <li>日主判定（日元干支）</li>
            <li>十神对照表（7个十神的含义）</li>
            <li>每柱对应十神的高亮标记</li>
            <li>十神在命盘中的关键表现</li>
          </ul>
        </div>
      </div>

      <!-- 1.4 五行分析 -->
      <div v-else-if="section.id === 'bazi-wuxing'" class="content-block">
        <div class="content-title">五行分布与用神</div>
        <div class="content-placeholder">
          <p>📈 需要从工作台选定案例后，显示：</p>
          <ul style="margin: 8px 0 0; padding-left: 20px; font-size: 12px; color: var(--text-3); line-height: 1.8;">
            <li>五行饼图 / 雷达图</li>
            <li>五行数值（强/中/弱）</li>
            <li>五行平衡度与失衡提示</li>
            <li>用神候选列表与排序</li>
          </ul>
        </div>
      </div>

      <!-- 1.5 藏干/纳音/生肖 -->
      <div v-else-if="section.id === 'bazi-canggan'" class="content-block">
        <div class="content-title">藏干、纳音与生肖</div>
        <div class="content-placeholder">
          <p>🔍 需要从工作台选定案例后，显示：</p>
          <ul style="margin: 8px 0 0; padding-left: 20px; font-size: 12px; color: var(--text-3); line-height: 1.8;">
            <li>各柱藏干详细表（含权重）</li>
            <li>四柱纳音五行解释</li>
            <li>生肖属相与冲合提示</li>
          </ul>
        </div>
      </div>

      <!-- 1.6 神煞与空亡 -->
      <div v-else-if="section.id === 'bazi-shensha'" class="content-block">
        <div class="content-title">神煞与定位</div>
        <div class="content-placeholder">
          <p>✨ 需要从工作台选定案例后，显示：</p>
          <ul style="margin: 8px 0 0; padding-left: 20px; font-size: 12px; color: var(--text-3); line-height: 1.8;">
            <li>神煞落点（命盘标注）</li>
            <li>神煞定义与触发条件</li>
            <li>强弱 / 影响等级（吉/中/凶）</li>
          </ul>
        </div>
      </div>

      <!-- 1.7 冲合刑害破 -->
      <div v-else-if="section.id === 'bazi-chonghe'" class="content-block">
        <div class="content-title">冲合刑害破</div>
        <div class="content-placeholder">
          <p>⚔️ 需要从工作台选定案例后，显示：</p>
          <ul style="margin: 8px 0 0; padding-left: 20px; font-size: 12px; color: var(--text-3); line-height: 1.8;">
            <li>冲合列表（涉及柱位）</li>
            <li>大运 / 流年影响建议</li>
            <li>化解建议</li>
          </ul>
        </div>
      </div>

      <!-- 1.8 格局判定与用神 -->
      <div v-else-if="section.id === 'bazi-gejv'" class="content-block">
        <div class="content-title">格局判定与用神</div>
        <div class="content-placeholder">
          <p>🏛️ 需要从工作台选定案例后，显示：</p>
          <ul style="margin: 8px 0 0; padding-left: 20px; font-size: 12px; color: var(--text-3); line-height: 1.8;">
            <li>格局类型判定结果</li>
            <li>用神 / 忌神候选列表</li>
            <li>应用建议（事业 / 健康 / 财运）</li>
          </ul>
        </div>
      </div>

      <!-- 1.9 大运/流年/流月 -->
      <div v-else-if="section.id === 'bazi-dayun'" class="content-block">
        <div class="content-title">大运/流年/流月</div>
        <div class="content-placeholder">
          <p>⏰ 需要从工作台选定案例后，显示：</p>
          <ul style="margin: 8px 0 0; padding-left: 20px; font-size: 12px; color: var(--text-3); line-height: 1.8;">
            <li>大运时间轴（可滑动）</li>
            <li>流年 / 流月要点卡片</li>
            <li>起运年龄与方法说明</li>
          </ul>
        </div>
      </div>

      <!-- 1.10 十神宫位用法 -->
      <div v-else-if="section.id === 'bazi-shishen-gong'" class="content-block">
        <div class="content-title">十神宫位用法</div>
        <div class="content-placeholder">
          <p>📍 需要从工作台选定案例后，显示：</p>
          <ul style="margin: 8px 0 0; padding-left: 20px; font-size: 12px; color: var(--text-3); line-height: 1.8;">
            <li>事业宫位十神影响</li>
            <li>婚姻宫位十神影响</li>
            <li>财帛宫位十神影响</li>
            <li>子女宫位十神影响</li>
          </ul>
        </div>
      </div>

      <!-- 占位符：其他章节 -->
      <div v-else class="content-block">
        <div class="content-title">{{ section.label }}</div>
        <div class="content-placeholder">📋 内容开发中…（{{ section.num }}）</div>
      </div>
    </div>
    <div class="block">
      <div class="block-title">
        <span class="block-icon">📚</span>
        <span>本节课题</span>
        <span class="count-badge">{{ section.topics.length }}</span>
      </div>
      <div class="topic-grid">
        <div
          v-for="topic in section.topics"
          :key="topic.id"
          class="topic-chip"
        >
          <span class="chip-dot" :style="`background: ${chapter?.color}`"></span>
          {{ topic.label }}
        </div>
      </div>
    </div>

    <!-- ── 右侧显示说明 ── -->
    <div class="block">
      <div class="block-title">
        <span class="block-icon">🖥</span>
        <span>右侧显示内容</span>
      </div>
      <div class="display-list">
        <div
          v-for="(item, i) in section.displays"
          :key="i"
          class="display-item"
        >
          <span class="di-idx" :style="`background: ${chapter?.color}22; color: ${chapter?.color}`">{{ i + 1 }}</span>
          <span class="di-text">{{ item }}</span>
        </div>
      </div>
    </div>

    <!-- ── 通用显示项（可折叠） ── -->
    <div class="block">
      <button class="collapse-trigger" @click="showCommon = !showCommon">
        <span class="block-icon">⚙</span>
        <span>通用工具项</span>
        <span class="arrow" :class="{ rotated: showCommon }">›</span>
      </button>
      <div v-if="showCommon" class="common-list">
        <div v-for="item in COMMON_ITEMS" :key="item.label" class="common-item">
          <span class="ci-icon">{{ item.icon }}</span>
          <span class="ci-text">{{ item.label }}</span>
        </div>
      </div>
    </div>

    <!-- ── UI 组件提示（可折叠） ── -->
    <div class="block">
      <button class="collapse-trigger" @click="showUiComp = !showUiComp">
        <span class="block-icon">🧩</span>
        <span>涉及 UI 组件</span>
        <span class="arrow" :class="{ rotated: showUiComp }">›</span>
      </button>
      <div v-if="showUiComp" class="common-list">
        <div v-for="comp in UI_COMPONENTS" :key="comp" class="common-item">
          <span class="ci-icon">▸</span>
          <span class="ci-text">{{ comp }}</span>
        </div>
      </div>
    </div>

    <!-- ── AI 分析按钮 ── -->
    <div class="ai-action-row">
      <button
        class="ai-btn"
        :disabled="ai.streaming"
        @click="askAI"
        :style="`--btn-color: ${chapter?.color}`"
      >
        <span>🤖</span>
        <span>{{ ai.streaming ? 'AI 分析中…' : `AI 分析：${section.label}` }}</span>
      </button>
    </div>

    <!-- ── 快捷操作（同步主盘中部按钮） ── -->
    <div class="block quick-actions-block">
      <div class="block-title">
        <span class="block-icon">🧰</span>
        <span>快捷操作</span>
      </div>
      <div class="quick-actions-grid">
        <button class="qa-btn qa-adjust" type="button" @click="emitQuickAction('adjust')">⏱ 定盘</button>
        <button class="qa-btn qa-copy" type="button" @click="emitQuickAction('copy')">📋 复制</button>
        <button class="qa-btn qa-export" type="button" @click="emitQuickAction('export')">📷 导出</button>
        <button class="qa-btn qa-share" type="button" @click="emitQuickAction('share')">🔗 分享</button>
        <button class="qa-btn qa-notes" type="button" @click="emitQuickAction('notes')">📝 笔记</button>
        <button class="qa-btn qa-calendar" type="button" @click="emitQuickAction('calendar')">📅 日历</button>
        <button class="qa-btn qa-compare" type="button" @click="emitQuickAction('compare')">⚖ 对比</button>
        <button class="qa-btn qa-bookmarks" type="button" @click="emitQuickAction('bookmarks')">★ 收藏 (0)</button>
      </div>
    </div>

  </div>

  <!-- 未选中任何小节时 -->
  <div v-else class="empty-state">
    <div class="empty-icon">☯</div>
    <div class="empty-title">命理中控系统</div>
    <div class="empty-sub">从左侧导航选择章节，<br>右侧将显示对应课题内容与工具</div>
    <div class="chapter-pills">
      <button
        v-for="ch in nav.NAV_CHAPTERS"
        :key="ch.id"
        class="ch-pill"
        :style="`background: ${ch.color}18; color: ${ch.color}; border-color: ${ch.color}30`"
        @click="nav.toggleChapter(ch.id)"
      >
        <span>{{ ch.icon }}</span>
        <span>{{ ch.label }}</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
/* ── 面板整体 ─────────────────────────────────────────────────── */
.topic-panel {
  display: flex;
  flex-direction: column;
  gap: 0;
  overflow-y: auto;
  height: 100%;
  scrollbar-width: thin;
  scrollbar-color: var(--color-border) transparent;
}

/* ── 面包屑 ───────────────────────────────────────────────────── */
.breadcrumb {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 12px 14px 8px;
  font-size: 0.75rem;
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}
.bc-chapter { font-weight: 700; }
.bc-sep { color: var(--color-text-muted); }
.bc-section {
  color: var(--color-text-secondary);
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ── 通用块 ───────────────────────────────────────────────────── */
.block {
  padding: 10px 14px;
  border-bottom: 1px solid var(--color-border);
}
.block-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--color-text-secondary);
  margin-bottom: 8px;
  letter-spacing: .02em;
}
.block-icon { font-size: 13px; }
.count-badge {
  margin-left: auto;
  font-size: 0.625rem;
  background: var(--color-bg-tertiary);
  color: var(--color-text-muted);
  padding: 1px 6px;
  border-radius: 99px;
  font-weight: 600;
}

/* ── 课题 chips ───────────────────────────────────────────────── */
.topic-grid {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.topic-chip {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 5px 8px;
  background: var(--color-bg-secondary);
  border-radius: 5px;
  font-size: 0.75rem;
  color: var(--color-text-primary);
  line-height: 1.4;
}
.chip-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
  opacity: .8;
}

/* ── 右侧显示说明 ─────────────────────────────────────────────── */
.display-list {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.display-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 0.75rem;
  color: var(--color-text-secondary);
}
.di-idx {
  min-width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  font-size: 0.625rem;
  font-weight: 700;
  flex-shrink: 0;
  margin-top: 1px;
}
.di-text { flex: 1; line-height: 1.5; }

/* ── 可折叠触发器 ─────────────────────────────────────────────── */
.collapse-trigger {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--color-text-secondary);
  padding: 0;
  font-family: var(--font-ui);
  text-align: left;
  letter-spacing: .02em;
}
.collapse-trigger:hover { color: var(--color-text-primary); }
.arrow {
  margin-left: auto;
  font-size: 13px;
  color: var(--color-text-muted);
  transition: transform var(--transition-fast);
}
.arrow.rotated { transform: rotate(90deg); }

/* ── 通用项列表 ───────────────────────────────────────────────── */
.common-list {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.common-item {
  display: flex;
  align-items: flex-start;
  gap: 7px;
  font-size: 0.75rem;
  color: var(--color-text-muted);
  padding: 3px 0;
}
.ci-icon { flex-shrink: 0; width: 16px; text-align: center; }
.ci-text { flex: 1; line-height: 1.5; }

/* ── AI 按钮 ──────────────────────────────────────────────────── */
.ai-action-row {
  padding: 12px 14px;
}
.ai-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 9px 14px;
  border: 1px solid var(--btn-color, var(--color-brand));
  border-radius: 8px;
  background: transparent;
  color: var(--btn-color, var(--color-brand));
  font-size: 0.8125rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
  font-family: var(--font-ui);
  justify-content: center;
}
.ai-btn:hover:not(:disabled) {
  background: var(--btn-color, var(--color-brand));
  color: #fff;
}
.ai-btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* ── 快捷操作区 ───────────────────────────────────────────────── */
.quick-actions-block {
  padding-top: 8px;
  padding-bottom: 14px;
}
.quick-actions-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}
.qa-btn {
  border: none;
  border-radius: 7px;
  padding: 8px 10px;
  font-size: 0.75rem;
  font-weight: 700;
  cursor: pointer;
  line-height: 1;
  font-family: var(--font-ui);
  transition: transform var(--transition-fast), filter var(--transition-fast);
}
.qa-btn:hover {
  filter: brightness(1.05);
  transform: translateY(-1px);
}
.qa-adjust,
.qa-copy {
  background: #f1f5f9;
  color: #475569;
}
.qa-export,
.qa-share {
  background: #4f46e5;
  color: #fff;
}
.qa-notes {
  background: #7c3aed;
  color: #fff;
}
.qa-calendar {
  background: #059669;
  color: #fff;
}
.qa-compare {
  background: #f97316;
  color: #fff;
}
.qa-bookmarks {
  background: #f59e0b;
  color: #fff;
}

/* ── 内容区域 ───────────────────────────────────────────────────── */
.content-area {
  padding: 10px 14px;
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}
.content-block {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.content-title {
  font-size: 0.8125rem;
  font-weight: 700;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: .02em;
}
.content-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 8px;
}
.info-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 8px;
  border-radius: 6px;
  background: var(--color-bg-secondary);
}
.info-label {
  font-size: 0.625rem;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: .025em;
  font-weight: 600;
}
.info-value {
  font-size: 0.75rem;
  color: var(--color-text-primary);
  font-weight: 500;
  word-break: break-word;
}
.content-placeholder {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  padding: 8px 10px;
  border-radius: 6px;
  background: var(--color-bg-secondary);
  line-height: 1.6;
}
.content-hint {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  padding: 6px 0;
  font-style: italic;
}

/* ── 空状态 ───────────────────────────────────────────────────── */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 28px 16px;
  gap: 8px;
}
.empty-icon { font-size: 36px; opacity: .3; }
.empty-title {
  font-size: 0.9375rem;
  font-weight: 700;
  color: var(--color-text-secondary);
}
.empty-sub {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  text-align: center;
  line-height: 1.6;
}
.chapter-pills {
  display: flex;
  flex-direction: column;
  gap: 5px;
  width: 100%;
  margin-top: 10px;
}
.ch-pill {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 6px 10px;
  border-radius: 6px;
  border: 1px solid;
  background: transparent;
  cursor: pointer;
  font-size: 0.75rem;
  font-weight: 600;
  font-family: var(--font-ui);
  transition: opacity var(--transition-fast);
  text-align: left;
}
.ch-pill:hover { opacity: .8; }
</style>
