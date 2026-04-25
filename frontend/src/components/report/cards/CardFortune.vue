<script setup lang="ts">
/**
 * CardFortune.vue — 卡3：当前运势
 * 进入②八字 → 展开显示大运/流年；进入③紫微 → 切换显示大限；其它章节 → 自动折叠
 */
import { computed, watch } from 'vue'
import { useReportStore } from '@/stores/report'

const store = useReportStore()
const isCollapsed = computed(() => store.cardCollapsed['fortune'] ?? false)

// ─── 模式判断 ────────────────────────────────────────────────
const isZiweiMode = computed(() => store.activeChapter === 3 && !!store.ziweiData)
const isBaziMode  = computed(() => store.activeChapter === 2 && !!store.baziData)
const bazi = computed(() => store.baziData)

// ─── 紫微当前大限 ────────────────────────────────────────────
const CURRENT_YEAR = new Date().getFullYear()
const currentZiweiDayun = computed(() => {
  if (!store.ziweiData?.dayun?.items?.length) return null
  const items = store.ziweiData.dayun.items
  return items.find((item: { start_year: number }, i: number) => {
    const next = items[i + 1] as { start_year: number } | undefined
    if (!next) return true
    return item.start_year <= CURRENT_YEAR && CURRENT_YEAR < next.start_year
  }) ?? null
})

// ─── 自动展开/折叠逻辑 ────────────────────────────────────────
watch(() => store.activeChapter, (ch) => {
  if (ch === 2 || ch === 3) {
    if (isCollapsed.value) store.toggleCard('fortune')
  }
}, { immediate: false })
</script>

<template>
  <div class="card" :class="{ collapsed: isCollapsed }">
    <button class="card-header" @click="store.toggleCard('fortune')">
      <span class="card-title">🔮 当前运势</span>
      <span class="card-toggle">{{ isCollapsed ? '▸' : '▾' }}</span>
    </button>
    <div class="card-body" v-show="!isCollapsed">

      <!-- 紫微大限模式 -->
      <template v-if="isZiweiMode && currentZiweiDayun">
        <p class="mode-label">紫微大限</p>
        <div class="ganzhi-row">
          <span class="gz">{{ (currentZiweiDayun as any).ganzhi }}</span>
          <span class="gz-sub">大限</span>
        </div>
        <div class="kv-row">
          <span class="kv-key">年龄</span>
          <span class="kv-val">{{ (currentZiweiDayun as any).start_age }}~{{ (currentZiweiDayun as any).end_age }}岁</span>
        </div>
        <div class="kv-row">
          <span class="kv-key">起年</span>
          <span class="kv-val">{{ (currentZiweiDayun as any).start_year }} 年</span>
        </div>
        <!-- 四化标记 -->
        <div v-if="Object.keys((currentZiweiDayun as any).sihua ?? {}).length" class="sihua-row">
          <span
            v-for="(star, hua) in (currentZiweiDayun as any).sihua"
            :key="String(hua)"
            class="sihua-chip"
            :class="`sihua-${hua}`"
          >{{ star }}{{ hua }}</span>
        </div>
      </template>

      <!-- 八字大运/流年模式 -->
      <template v-else-if="isBaziMode && bazi?.current_fortune_summary">
        <p class="mode-label">八字运势</p>
        <div class="ganzhi-row">
          <span class="gz">{{ bazi.current_fortune_summary.current_dayun }}</span>
          <span class="gz-sub">大运</span>
        </div>
        <div class="ganzhi-row" style="margin-top:var(--sp-1)">
          <span class="gz sm">{{ bazi.current_fortune_summary.current_liunian }}</span>
          <span class="gz-sub">流年 {{ CURRENT_YEAR }}</span>
        </div>
        <div
          v-for="(val, domain) in bazi.current_fortune_summary.this_year_domains"
          :key="String(domain)"
          class="kv-row"
        >
          <span class="kv-key">{{ domain }}</span>
          <span class="kv-val">{{ val }}</span>
        </div>
        <div v-if="bazi.current_fortune_summary.top3_actions?.length" class="top3">
          <p class="top3-title">今年重点</p>
          <ol class="top3-list">
            <li v-for="(a, i) in bazi.current_fortune_summary.top3_actions" :key="i">{{ a }}</li>
          </ol>
        </div>
      </template>

      <p v-else class="card-empty">在②八字或③紫微章节查看运势</p>

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

/* ── 运势内容 ───────────────────────────────────────────── */
.mode-label {
  font-size: 11px; color: var(--text-3); background: var(--bg);
  padding: 1px 8px; border-radius: 99px; display: inline-block; margin-bottom: var(--sp-2);
}
.ganzhi-row { display: flex; align-items: baseline; gap: var(--sp-2); margin-bottom: var(--sp-2); }
.gz { font-size: var(--fs-xl); font-family: var(--font-cn); font-weight: 700; color: var(--accent-dark); }
.gz.sm { font-size: var(--fs-md); }
.gz-sub { font-size: 11px; color: var(--text-3); }

/* KV 行（域运数据）*/
.kv-row { display: flex; gap: var(--sp-2); padding: 3px 0; font-size: var(--fs-xs); border-bottom: 1px solid var(--border); }
.kv-row:last-of-type { border-bottom: none; }
.kv-key { width: 36px; color: var(--text-3); flex-shrink: 0; }
.kv-val { flex: 1; color: var(--text); }

/* 四化标记 */
.sihua-row { display: flex; flex-wrap: wrap; gap: 4px; margin-top: var(--sp-2); }
.sihua-chip { font-size: 11px; padding: 1px 6px; border-radius: 99px; font-family: var(--font-cn); }
.sihua-化禄, .sihua-禄 { background: #dcfce7; color: #15803d; }
.sihua-化权, .sihua-权 { background: #dbeafe; color: #1d4ed8; }
.sihua-化科, .sihua-科 { background: #f3e8ff; color: #7e22ce; }
.sihua-化忌, .sihua-忌 { background: #fee2e2; color: #b91c1c; }

/* 今年重点 */
.top3 { margin-top: var(--sp-3); }
.top3-title { font-size: var(--fs-xs); font-weight: 600; color: var(--text-2); margin-bottom: 4px; }
.top3-list { padding-left: 16px; font-size: var(--fs-xs); color: var(--text); line-height: 1.8; }
</style>
