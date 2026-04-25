<script setup lang="ts">
import { computed } from 'vue'
import { useReportStore } from '@/stores/report'

const store = useReportStore()

const currentChapter = computed(() => store.currentChapterDef)

// 计算每个小节的状态
// eslint-disable-next-line @typescript-eslint/no-unused-vars
function sectionStatus(_sectionId: string): 'loaded' | 'loading' | 'error' | 'no-api' | 'idle' {
  const ch = currentChapter.value
  if (!ch.hasApi || !ch.apiKey) return 'no-api'
  const key = ch.apiKey
  if (store.errorMap[key]) return 'error'
  if (store.loadingMap[key]) return 'loading'
  // 检查对应数据是否已加载
  const dataMap: Record<string, boolean> = {
    bazi: !!store.baziData,
    ziwei: !!store.ziweiData,
    name: !!store.nameData,
    zeri: !!store.zeriData,
    fengshui: !!store.fengshuiData,
  }
  if (dataMap[key]) return 'loaded'
  return 'idle'
}

function onClickSection(sectionId: string) {
  store.setActiveSection(sectionId)
  // 滚动到对应锚点
  const el = document.getElementById(`section-${sectionId}`)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    // 短暂高亮
    el.classList.add('section-highlight')
    setTimeout(() => el.classList.remove('section-highlight'), 800)
  }
}

// 激活小节下方展开词条芯片（只显示 activeSection 的词条）
const activeSectionGlossary = computed(() => {
  const sec = currentChapter.value.sections.find(s => s.id === store.activeSection)
  return sec?.glossary ?? []
})
</script>

<template>
  <div class="toc-panel">
    <!-- 章节标题 -->
    <div class="toc-header">
      <span class="toc-chapter-icon">{{ currentChapter.icon }}</span>
      <span class="toc-chapter-label">{{ currentChapter.label }}</span>
    </div>

    <!-- 禁用提示 -->
    <div v-if="currentChapter.disabled" class="toc-disabled">
      <p>此章节尚未开放</p>
    </div>

    <!-- 小节列表 -->
    <ul v-else class="section-list">
      <li
        v-for="sec in currentChapter.sections"
        :key="sec.id"
        class="section-item"
        :class="{ active: store.activeSection === sec.id }"
        @click="onClickSection(sec.id)"
      >
        <span class="section-status" :class="sectionStatus(sec.id)">
          <span v-if="sectionStatus(sec.id) === 'loaded'">✓</span>
          <span v-else-if="sectionStatus(sec.id) === 'loading'" class="spin">⟳</span>
          <span v-else-if="sectionStatus(sec.id) === 'error'">✗</span>
          <span v-else-if="sectionStatus(sec.id) === 'no-api'">—</span>
          <span v-else>·</span>
        </span>
        <span class="section-label">{{ sec.label }}</span>

        <!-- 词条芯片（激活小节下方懒展开） -->
        <transition name="chip-slide">
          <div
            v-if="store.activeSection === sec.id && activeSectionGlossary.length"
            class="chip-row"
          >
            <button
              v-for="term in activeSectionGlossary.slice(0, 10)"
              :key="term"
              class="term-chip"
              @click.stop="store.setGlossaryTerm(term)"
            >
              📖 {{ term }}
            </button>
            <span v-if="activeSectionGlossary.length > 10" class="chip-more">
              +{{ activeSectionGlossary.length - 10 }} 更多…
            </span>
          </div>
        </transition>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.toc-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.toc-header {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-4) var(--sp-3);
  border-bottom: 1px solid var(--border);
  font-weight: 600;
  font-size: var(--fs-md);
  position: sticky;
  top: 0;
  background: var(--surface);
  z-index: 1;
}

.toc-chapter-icon { font-size: 16px; }
.toc-chapter-label { color: var(--text); }

.toc-disabled {
  padding: var(--sp-6) var(--sp-4);
  color: var(--text-3);
  font-size: var(--fs-sm);
  text-align: center;
}

.section-list {
  list-style: none;
  padding: var(--sp-2) 0;
  flex: 1;
}

.section-item {
  display: flex;
  align-items: flex-start;
  flex-wrap: wrap;
  padding: var(--sp-2) var(--sp-3);
  cursor: pointer;
  border-radius: var(--radius-sm);
  margin: 1px var(--sp-2);
  transition: background var(--dur-fast);
  gap: var(--sp-2);
}

.section-item:hover {
  background: var(--accent-glow);
}

.section-item.active {
  background: var(--accent-lt);
}

.section-status {
  flex-shrink: 0;
  width: 14px;
  font-size: 11px;
  line-height: 1.6;
}

.section-status.loaded { color: var(--success-dark); }
.section-status.error  { color: var(--danger-dark); }
.section-status.loading { color: var(--accent); }
.section-status.no-api { color: var(--text-3); }

.section-label {
  flex: 1;
  font-size: var(--fs-sm);
  color: var(--text);
  line-height: 1.4;
}

.section-item.active .section-label {
  font-weight: 600;
  color: var(--accent-dark);
}

.spin {
  display: inline-block;
  animation: rotate 1s linear infinite;
}
@keyframes rotate { to { transform: rotate(360deg); } }

/* 词条芯片 */
.chip-row {
  width: 100%;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  padding-top: 4px;
}

.term-chip {
  font-size: 11px;
  padding: 2px 6px;
  border: 1px dashed var(--accent-dark);
  border-radius: 99px;
  background: transparent;
  color: var(--accent-dark);
  cursor: pointer;
  transition: background var(--dur-fast);
}

.term-chip:hover {
  background: var(--accent-lt);
}

.chip-more {
  font-size: 11px;
  color: var(--text-3);
  padding: 2px 4px;
  align-self: center;
}

/* 展开动画 */
.chip-slide-enter-active, .chip-slide-leave-active {
  transition: all var(--dur-mid) ease;
  overflow: hidden;
}
.chip-slide-enter-from, .chip-slide-leave-to {
  opacity: 0;
  max-height: 0;
}
.chip-slide-enter-to, .chip-slide-leave-from {
  opacity: 1;
  max-height: 200px;
}
</style>
