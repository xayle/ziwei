<script setup lang="ts">
import { computed, ref, watch, onMounted } from 'vue'
import { useOneTimeFlag } from '@/composables/useOneTimeFlag'
import { useReportStore } from '@/stores/report'

const store = useReportStore()

// ─── 卡片折叠 ─────────────────────────────────────────────────
const isCollapsed = (cardId: string) => store.cardCollapsed[cardId] ?? false

// ─── 卡1: 五行迷你图 ─────────────────────────────────────────
// ─── 卡2: chip 引导提示 ──────────────────────────────────────
const CHIP_HINT_KEY = 'report:chip:hint:shown'
const { isVisible: showChipHint, dismiss: dismissChipHint } = useOneTimeFlag(CHIP_HINT_KEY)

// 卡2 宫格详情模式（当 activePalaceIndex != null 时）
const activePalace = computed(() => {
  if (store.activePalaceIndex == null || !store.ziweiData) return null
  return store.ziweiData.palaces.find(p => p.index === store.activePalaceIndex) ?? null
})

// ─── 卡3: 运势模式（八字/紫微）───────────────────────────────
const isZiweiMode = computed(() => store.activeChapter === 3 && !!store.ziweiData)
const isBaziMode  = computed(() => store.activeChapter === 2 && !!store.baziData)

// 八字流年大运
const bazi = computed(() => store.baziData)

// 紫微当前大限
const CURRENT_YEAR = new Date().getFullYear()
const currentZiweiDayun = computed(() => {
  if (!store.ziweiData?.dayun?.items?.length) return null
  const items = store.ziweiData.dayun.items
  return items.find((item, i) => {
    const next = items[i + 1]
    if (!next) return true
    return item.start_year <= CURRENT_YEAR && CURRENT_YEAR < next.start_year
  }) ?? null
})

// 卡3 自动展开逻辑
watch(() => store.activeChapter, (ch) => {
  if (ch === 2 || ch === 3) {
    if (isCollapsed('fortune')) store.toggleCard('fortune')
  }
}, { immediate: false })

// ─── 卡4: 笔记 debounce + char count ────────────────────────
const noteRaw = ref(store.notes[store.activeSection ?? ''] ?? '')

// 监听 activeSection 变化，加载对应笔记
watch(() => store.activeSection, (sec) => {
  noteRaw.value = store.notes[sec ?? ''] ?? ''
})

// debounce 500ms
let debounceTimer: ReturnType<typeof setTimeout> | null = null
function onNoteInput(e: Event) {
  const val = (e.target as HTMLTextAreaElement).value
  noteRaw.value = val
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    store.saveNote(store.activeSection ?? '', val)
  }, 500)
}

const noteCharCount = computed(() => noteRaw.value.length)

onMounted(() => {
  noteRaw.value = store.notes[store.activeSection ?? ''] ?? ''
})
</script>

<template>
  <aside class="card-panel">

    <!-- ══ 卡1: 命盘概要 ════════════════════════════════════════ -->
    <div class="card" :class="{ collapsed: isCollapsed('overview') }">
      <button class="card-header" @click="store.toggleCard('overview')">
        <span class="card-title">📊 命盘概要</span>
        <span class="card-toggle">{{ isCollapsed('overview') ? '▸' : '▾' }}</span>
      </button>
      <div class="card-body" v-show="!isCollapsed('overview')">

        <!-- 案例基本信息 -->
        <div v-if="store.caseData" class="case-info">
          <p class="case-name">{{ store.caseData.name }}</p>
          <p class="case-meta">
            {{ store.caseData.gender === 'male' ? '男' : '女' }}
            · {{ store.caseData.birth_dt_local?.slice(0, 10) ?? '—' }}
          </p>
        </div>
        <p v-else class="card-empty">未加载案例</p>

        <!-- 八字核心指标 -->
        <template v-if="store.baziData">
          <div class="kv-sep" />

          <!-- 五行迷你图 -->
          <div class="wxbar-wrap">
            <div class="wxbar-row">
              <div class="wxbar-seg" style="background:var(--wx-wood)"  :style="{ flex: store.baziData.wuxing_score.wood }" />
              <div class="wxbar-seg" style="background:var(--wx-fire)"  :style="{ flex: store.baziData.wuxing_score.fire }" />
              <div class="wxbar-seg" style="background:var(--wx-earth)" :style="{ flex: store.baziData.wuxing_score.earth }" />
              <div class="wxbar-seg" style="background:var(--wx-metal)" :style="{ flex: store.baziData.wuxing_score.metal }" />
              <div class="wxbar-seg" style="background:var(--wx-water)" :style="{ flex: store.baziData.wuxing_score.water }" />
            </div>
            <div class="wxbar-labels">
              <span style="color:var(--wx-wood)">木{{ store.baziData.wuxing_score.wood }}</span>
              <span style="color:var(--wx-fire)">火{{ store.baziData.wuxing_score.fire }}</span>
              <span style="color:var(--wx-earth)">土{{ store.baziData.wuxing_score.earth }}</span>
              <span style="color:var(--wx-metal)">金{{ store.baziData.wuxing_score.metal }}</span>
              <span style="color:var(--wx-water)">水{{ store.baziData.wuxing_score.water }}</span>
            </div>
          </div>

          <div class="badges-row">
            <span class="info-badge">{{ store.baziData.pillars_primary?.day?.stem }} 日主</span>
            <span v-if="store.baziData.geju" class="info-badge accent">{{ store.baziData.geju.geju_name }}</span>
            <span v-if="store.baziData.day_master_strength?.tier" class="info-badge">{{ store.baziData.day_master_strength.tier }}</span>
          </div>

          <div class="kv-row" v-if="store.baziData.yongshen?.favor?.length">
            <span class="kv-key">用神</span>
            <span class="kv-val">
              <span v-for="f in store.baziData.yongshen.favor" :key="f" class="wx-tag">{{ f }}</span>
            </span>
          </div>
        </template>
        <p v-else-if="store.caseData" class="card-empty sm">八字未计算</p>

      </div>
    </div>

    <!-- ══ 卡2: 术语词条 ════════════════════════════════════════ -->
    <div class="card" :class="{ collapsed: isCollapsed('glossary') }">
      <button class="card-header" @click="store.toggleCard('glossary')">
        <span class="card-title">📖 术语词条</span>
        <span class="card-toggle">{{ isCollapsed('glossary') ? '▸' : '▾' }}</span>
      </button>
      <div class="card-body" v-show="!isCollapsed('glossary')">
        <!-- ── 宫格详情模式 ── -->
        <template v-if="activePalace">
          <button class="btn-back-glossary" @click="store.setActivePalace(null)">◀ 返回词条</button>
          <p class="palace-name">{{ activePalace.name }}</p>
          <p class="palace-branch-label">地支：{{ activePalace.branch }}</p>
          <p class="palace-analysis">{{ activePalace.analysis }}</p>
          <p v-if="activePalace.conclusion" class="palace-conclusion">结论：{{ activePalace.conclusion }}</p>
          <p v-if="activePalace.suggestion" class="palace-suggestion">建议：{{ activePalace.suggestion }}</p>
          <div v-if="activePalace.analysis_tags?.length" class="palace-tags">
            <span v-for="tag in activePalace.analysis_tags" :key="tag" class="badge">{{ tag }}</span>
          </div>
        </template>

        <!-- ── 词条模式 ── -->
        <template v-else>
          <!-- 首次引导 -->
          <div v-if="showChipHint && !store.glossaryEntry" class="chip-hint">
            <p class="hint-text">💡 点击内容区带 📖 标记的术语可查看释义</p>
            <button class="hint-close" @click="dismissChipHint">知道了</button>
          </div>

          <template v-if="store.glossaryEntry">
            <p class="glossary-term">{{ store.glossaryEntry.term }}</p>
            <p v-if="store.glossaryEntry.pinyin" class="glossary-pinyin">{{ store.glossaryEntry.pinyin }}</p>
            <p class="glossary-def">{{ store.glossaryEntry.definition }}</p>
            <p v-if="store.glossaryEntry.classic_source" class="glossary-source">
              ── {{ store.glossaryEntry.classic_source }}
            </p>
            <button class="btn-close-glossary" @click="store.setGlossaryTerm(null)">✕ 关闭</button>
          </template>
          <p v-else-if="!showChipHint" class="card-empty">点击内容区的 📖 词条查看释义</p>
        </template>
      </div>
    </div>

    <!-- ══ 卡3: 当前运势 ════════════════════════════════════════ -->
    <div class="card" :class="{ collapsed: isCollapsed('fortune') }">
      <button class="card-header" @click="store.toggleCard('fortune')">
        <span class="card-title">🔮 当前运势</span>
        <span class="card-toggle">{{ isCollapsed('fortune') ? '▸' : '▾' }}</span>
      </button>
      <div class="card-body" v-show="!isCollapsed('fortune')">

        <!-- 紫微大限模式 -->
        <template v-if="isZiweiMode && currentZiweiDayun">
          <p class="fortune-mode-label">紫微大限</p>
          <div class="fortune-ganzhi">
            <span class="gz">{{ currentZiweiDayun.ganzhi }}</span>
            <span class="gz-sub">大限</span>
          </div>
          <div class="kv-row">
            <span class="kv-key">年龄</span>
            <span class="kv-val">{{ currentZiweiDayun.start_age }}~{{ currentZiweiDayun.end_age }}岁</span>
          </div>
          <div class="kv-row">
            <span class="kv-key">起年</span>
            <span class="kv-val">{{ currentZiweiDayun.start_year }} 年</span>
          </div>
          <!-- 化曜 -->
          <div v-if="Object.keys(currentZiweiDayun.sihua ?? {}).length" class="sihua-row">
            <span
              v-for="(star, hua) in currentZiweiDayun.sihua"
              :key="hua"
              class="sihua-chip"
              :class="`sihua-${hua}`"
            >{{ star }}{{ hua }}</span>
          </div>
        </template>

        <!-- 八字大运/流年模式 -->
        <template v-else-if="isBaziMode && bazi?.current_fortune_summary">
          <p class="fortune-mode-label">八字运势</p>
          <div class="fortune-ganzhi">
            <span class="gz">{{ bazi.current_fortune_summary.current_dayun }}</span>
            <span class="gz-sub">大运</span>
          </div>
          <div class="fortune-ganzhi" style="margin-top:var(--sp-1)">
            <span class="gz sm">{{ bazi.current_fortune_summary.current_liunian }}</span>
            <span class="gz-sub">流年 {{ CURRENT_YEAR }}</span>
          </div>
          <div
            v-for="(val, domain) in bazi.current_fortune_summary.this_year_domains"
            :key="domain"
            class="domain-row"
          >
            <span class="domain-key">{{ domain }}</span>
            <span class="domain-val">{{ val }}</span>
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

    <!-- ══ 卡4: 批注笔记 ════════════════════════════════════════ -->
    <div class="card" :class="{ collapsed: isCollapsed('notes') }">
      <button class="card-header" @click="store.toggleCard('notes')">
        <span class="card-title">✏️ 批注笔记</span>
        <span class="card-toggle">{{ isCollapsed('notes') ? '▸' : '▾' }}</span>
      </button>
      <div class="card-body" v-show="!isCollapsed('notes')">
        <p class="note-hint">{{ store.activeSection ?? '—' }} 小节</p>
        <textarea
          :value="noteRaw"
          class="note-textarea"
          placeholder="在此记录本节分析批注…"
          rows="6"
          @input="onNoteInput"
        />
        <div class="note-footer">
          <span class="note-charcount">{{ noteCharCount }} 字</span>
        </div>
      </div>
    </div>

  </aside>
</template>

<style scoped>
.card-panel {
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
  padding: var(--sp-3);
  overflow-y: auto;
  height: 100%;
}

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
.card-empty.sm { padding: var(--sp-1) 0; }

/* ─── 卡1 */
.case-info { margin-bottom: var(--sp-2); }
.case-name { font-size: var(--fs-md); font-weight: 700; color: var(--text); font-family: var(--font-cn); }
.case-meta { font-size: var(--fs-xs); color: var(--text-3); margin-top: 1px; }

.kv-sep { height: 1px; background: var(--border); margin: var(--sp-2) 0; }

.wxbar-wrap { margin-bottom: var(--sp-2); }
.wxbar-row { display: flex; height: 8px; border-radius: 4px; overflow: hidden; gap: 1px; }
.wxbar-seg { min-width: 4px; transition: flex .4s ease; }
.wxbar-labels { display: flex; justify-content: space-between; margin-top: 3px; font-size: 10px; font-family: var(--font-mono); }

.badges-row { display: flex; flex-wrap: wrap; gap: 4px; margin: var(--sp-2) 0; }
.info-badge {
  font-size: 11px; padding: 2px 7px; border-radius: 99px;
  background: var(--surface); border: 1px solid var(--border);
  color: var(--text-2);
}
.info-badge.accent { background: var(--accent-lt); border-color: rgba(217,119,6,.25); color: var(--accent-dark); }

.kv-row { display: flex; align-items: center; gap: var(--sp-2); padding: 3px 0; font-size: var(--fs-xs); border-bottom: 1px solid var(--border); }
.kv-row:last-child { border-bottom: none; }
.kv-key { width: 40px; flex-shrink: 0; color: var(--text-3); }
.kv-val { color: var(--text); flex: 1; display: flex; flex-wrap: wrap; gap: 3px; }
.wx-tag { padding: 1px 5px; border-radius: 3px; font-size: 11px; background: var(--accent-lt); color: var(--accent-dark); }

/* ─── 卡2 */
.chip-hint {
  display: flex; align-items: flex-start; gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-3); background: #fef9c3;
  border: 1px solid #fde047; border-radius: var(--radius-sm);
  margin-bottom: var(--sp-3);
}
.hint-text { font-size: var(--fs-xs); color: #854d0e; flex: 1; line-height: 1.5; }
.hint-close { font-size: 11px; color: #854d0e; background: none; border: none; cursor: pointer; white-space: nowrap; flex-shrink: 0; padding-top: 2px; }

.glossary-term { font-size: var(--fs-lg); font-weight: 700; font-family: var(--font-cn); color: var(--text); }
.glossary-pinyin { font-size: var(--fs-xs); color: var(--text-3); margin: 2px 0 var(--sp-2); }
.glossary-def { font-size: var(--fs-sm); color: var(--text); line-height: 1.7; font-family: var(--font-cn); }
.glossary-source { font-size: 11px; color: var(--text-3); margin-top: var(--sp-2); font-style: italic; }
.btn-close-glossary { margin-top: var(--sp-3); font-size: 11px; color: var(--text-3); background: none; border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 2px 8px; cursor: pointer; }

/* ─── 卡2 宫格详情模式 */
.btn-back-glossary { font-size: 11px; color: var(--accent-dark); background: none; border: none; padding: 0 0 var(--sp-2); cursor: pointer; display: block; }
.btn-back-glossary:hover { text-decoration: underline; }
.palace-name { font-size: var(--fs-lg); font-weight: 700; font-family: var(--font-cn); color: var(--text); margin: 0 0 2px; }
.palace-branch-label { font-size: 11px; color: var(--text-3); margin: 0 0 var(--sp-2); }
.palace-analysis { font-size: var(--fs-sm); color: var(--text); line-height: 1.7; font-family: var(--font-cn); }
.palace-conclusion { font-size: var(--fs-sm); color: var(--text-2); margin-top: var(--sp-2); }
.palace-suggestion { font-size: var(--fs-sm); color: var(--text-2); }
.palace-tags { display: flex; flex-wrap: wrap; gap: 4px; margin-top: var(--sp-2); }
.palace-tags .badge { font-size: 11px; padding: 1px 7px; border-radius: 99px; background: var(--accent-soft); color: var(--accent-dark); font-family: var(--font-cn); }

/* ─── 卡3 */
.fortune-mode-label { font-size: 11px; color: var(--text-3); background: var(--bg); padding: 1px 8px; border-radius: 99px; display: inline-block; margin-bottom: var(--sp-2); }
.fortune-ganzhi { display: flex; align-items: baseline; gap: var(--sp-2); margin-bottom: var(--sp-2); }
.gz { font-size: var(--fs-xl); font-family: var(--font-cn); font-weight: 700; color: var(--accent-dark); }
.gz.sm { font-size: var(--fs-md); }
.gz-sub { font-size: 11px; color: var(--text-3); }

.sihua-row { display: flex; flex-wrap: wrap; gap: 4px; margin-top: var(--sp-2); }
.sihua-chip { font-size: 11px; padding: 1px 6px; border-radius: 99px; font-family: var(--font-cn); }
.sihua-化禄, .sihua-禄 { background: #dcfce7; color: #15803d; }
.sihua-化权, .sihua-权 { background: #dbeafe; color: #1d4ed8; }
.sihua-化科, .sihua-科 { background: #f3e8ff; color: #7e22ce; }
.sihua-化忌, .sihua-忌 { background: #fee2e2; color: #b91c1c; }

.domain-row { display: flex; gap: var(--sp-2); padding: 3px 0; font-size: var(--fs-xs); border-bottom: 1px solid var(--border); }
.domain-row:last-of-type { border-bottom: none; }
.domain-key { width: 36px; color: var(--text-3); flex-shrink: 0; }
.domain-val { flex: 1; color: var(--text); }

.top3 { margin-top: var(--sp-3); }
.top3-title { font-size: var(--fs-xs); font-weight: 600; color: var(--text-2); margin-bottom: 4px; }
.top3-list { padding-left: 16px; font-size: var(--fs-xs); color: var(--text); line-height: 1.8; }

/* ─── 卡4 */
.note-hint { font-size: 11px; color: var(--text-3); margin-bottom: var(--sp-2); }
.note-textarea {
  width: 100%; font-size: var(--fs-sm); font-family: var(--font-ui);
  color: var(--text); background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius-sm); padding: var(--sp-2); resize: vertical; line-height: 1.6;
  box-sizing: border-box;
}
.note-textarea:focus { outline: none; border-color: var(--accent); }
.note-footer { display: flex; justify-content: flex-end; margin-top: var(--sp-1); }
.note-charcount { font-size: 11px; color: var(--text-3); font-family: var(--font-mono); }
</style>
