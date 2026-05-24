<script setup lang="ts">
/**
 * CardGlossary.vue — 卡2：术语词条
 * 触发方式：内容区 chip click / 左侧词条芯片 click / 紫微宫格 click
 * 宫格模式（activePalaceIndex != null）覆盖术语显示
 */
import { computed } from 'vue'
import { useOneTimeFlag } from '@/composables/useOneTimeFlag'
import { useReportStore } from '@/stores/report'

const store = useReportStore()
const isCollapsed = computed(() => store.cardCollapsed['glossary'] ?? false)

// ─── chip 引导提示（只显示一次，localStorage 持久化）─────
const CHIP_HINT_KEY = 'report:chip:hint:shown'
const { isVisible: showChipHint, dismiss: dismissChipHint } = useOneTimeFlag(CHIP_HINT_KEY)

// ─── 宫格详情模式 ─────────────────────────────────────────
const activePalace = computed(() => {
  if (store.activePalaceIndex == null || !store.ziweiData) return null
  return store.ziweiData.palaces.find((p: { index: number }) => p.index === store.activePalaceIndex) ?? null
})
</script>

<template>
  <div class="card" :class="{ collapsed: isCollapsed }">
    <button class="card-header" @click="store.toggleCard('glossary')">
      <span class="card-title">📖 术语词条</span>
      <span class="card-toggle">{{ isCollapsed ? '▸' : '▾' }}</span>
    </button>
    <div class="card-body" v-show="!isCollapsed">

      <!-- ── 宫格详情模式 ── -->
      <template v-if="activePalace">
        <button class="btn-back" @click="store.setActivePalace(null)">◀ 返回词条</button>
        <p class="palace-name">{{ (activePalace as any).name }}</p>
        <p class="palace-branch-lbl">地支：{{ (activePalace as any).branch }}</p>
        <p class="palace-analysis">{{ (activePalace as any).analysis }}</p>
        <p v-if="(activePalace as any).conclusion" class="palace-conclusion">结论：{{ (activePalace as any).conclusion }}</p>
        <p v-if="(activePalace as any).suggestion" class="palace-suggestion">建议：{{ (activePalace as any).suggestion }}</p>
        <div v-if="(activePalace as any).analysis_tags?.length" class="palace-tags">
          <span v-for="tag in (activePalace as any).analysis_tags" :key="tag" class="badge">{{ tag }}</span>
        </div>
      </template>

      <!-- ── 词条模式 ── -->
      <template v-else>
        <!-- 首次进入引导提示 -->
        <div v-if="showChipHint && !store.glossaryEntry" class="chip-hint">
          <p class="hint-text">💡 点击内容区带 📖 标记的术语可查看释义</p>
          <button class="hint-close" @click="dismissChipHint">知道了</button>
        </div>

        <template v-if="store.glossaryEntry">
          <p class="term">{{ store.glossaryEntry.term }}</p>
          <p v-if="store.glossaryEntry.pinyin" class="pinyin">{{ store.glossaryEntry.pinyin }}</p>
          <p class="definition">{{ store.glossaryEntry.definition }}</p>
          <p v-if="store.glossaryEntry.classic_source" class="source">
            ── {{ store.glossaryEntry.classic_source }}
          </p>
          <button class="btn-close" @click="store.setGlossaryTerm(null)">✕ 关闭</button>
        </template>
        <p v-else-if="!showChipHint" class="card-empty">点击内容区的 📖 词条查看释义</p>
      </template>

    </div>
  </div>
</template>

<style scoped>
.card {
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--surface-2);
  overflow: hidden;
  transition: box-shadow var(--dur-fast);
  flex-shrink: 0;
}
.card:hover { box-shadow: var(--shadow); }
.card-header {
  display: flex; align-items: center; justify-content: space-between;
  width: 100%; padding: var(--sp-2) var(--sp-3);
  background: transparent; border: none; cursor: pointer; gap: var(--sp-2);
}
.card-title { font-size: var(--fs-sm); font-weight: 600; color: var(--text); }
.card-toggle { font-size: 12px; color: var(--text-3); }
.card-body { padding: var(--sp-3); border-top: 1px solid var(--border); }
.card-empty { font-size: var(--fs-xs); color: var(--text-3); text-align: center; padding: var(--sp-2) 0; }

/* ── chip 引导提示 ─────────────────────────────────────── */
.chip-hint {
  display: flex; align-items: flex-start; gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-3); background: #fef9c3;
  border: 1px solid #fde047; border-radius: var(--radius-sm);
  margin-bottom: var(--sp-3);
}
.hint-text { font-size: var(--fs-xs); color: #854d0e; flex: 1; line-height: 1.5; }
.hint-close { font-size: 11px; color: #854d0e; background: none; border: none; cursor: pointer; white-space: nowrap; flex-shrink: 0; padding-top: 2px; }

/* ── 词条内容 ─────────────────────────────────────────── */
.term { font-size: var(--fs-lg); font-weight: 700; font-family: var(--font-cn); color: var(--text); }
.pinyin { font-size: var(--fs-xs); color: var(--text-3); margin: 2px 0 var(--sp-2); }
.definition { font-size: var(--fs-sm); color: var(--text); line-height: 1.7; font-family: var(--font-cn); }
.source { font-size: 11px; color: var(--text-3); margin-top: var(--sp-2); font-style: italic; }
.btn-close { margin-top: var(--sp-3); font-size: 11px; color: var(--text-3); background: none; border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 2px 8px; cursor: pointer; }

/* ── 宫格详情模式 ─────────────────────────────────────── */
.btn-back { font-size: 11px; color: var(--accent-dark); background: none; border: none; padding: 0 0 var(--sp-2); cursor: pointer; display: block; }
.btn-back:hover { text-decoration: underline; }
.palace-name { font-size: var(--fs-lg); font-weight: 700; font-family: var(--font-cn); color: var(--text); margin: 0 0 2px; }
.palace-branch-lbl { font-size: 11px; color: var(--text-3); margin: 0 0 var(--sp-2); }
.palace-analysis { font-size: var(--fs-sm); color: var(--text); line-height: 1.7; font-family: var(--font-cn); }
.palace-conclusion { font-size: var(--fs-sm); color: var(--text-2); margin-top: var(--sp-2); }
.palace-suggestion { font-size: var(--fs-sm); color: var(--text-2); }
.palace-tags { display: flex; flex-wrap: wrap; gap: 4px; margin-top: var(--sp-2); }
.badge { font-size: 11px; padding: 1px 7px; border-radius: 99px; background: var(--accent-soft); color: var(--accent-dark); font-family: var(--font-cn); }
</style>
