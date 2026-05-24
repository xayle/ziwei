<script setup lang="ts">
/**
 * ChapterZiwei.vue — ③ 紫微斗数章节
 * 包含：参数控制栏 + 5个小节（命盘总览/命身主星/格局/建议/大限流年）
 */
import { computed, onMounted, ref } from 'vue'
import { useReportStore } from '@/stores/report'
import ParamControl from '@/components/report/ParamControl.vue'
import type { PalaceResponse } from '@/api/ziwei'

const store = useReportStore()

onMounted(() => {
  if (!store.ziweiData && !store.loadingMap['ziwei']) {
    store.loadChapterData(3)
  }
})

const ziwei  = computed(() => store.ziweiData)
const loading = computed(() => store.loadingMap['ziwei'])
const error   = computed(() => store.errorMap['ziwei'])

// ─── 宫格交互 ─────────────────────────────────────────────────
const activePalaceIndex = ref<number | null>(null)

const activePalace = computed<PalaceResponse | null>(() => {
  if (activePalaceIndex.value == null || !ziwei.value) return null
  return ziwei.value.palaces.find(p => p.index === activePalaceIndex.value) ?? null
})

function clickPalace(palace: PalaceResponse) {
  const next = activePalaceIndex.value === palace.index ? null : palace.index
  activePalaceIndex.value = next
  // 同步到 store：切换卡2为宫格详情模式（null 时恢复词条模式）
  store.setActivePalace(next)
}

// ─── 4×4 宫格位置映射 ─────────────────────────────────────────
// branch → { gridRow(1-indexed), gridCol(1-indexed) }
const BRANCH_GRID: Record<string, { r: number; c: number }> = {
  '巳': { r: 1, c: 1 }, '午': { r: 1, c: 2 }, '未': { r: 1, c: 3 }, '申': { r: 1, c: 4 },
  '酉': { r: 2, c: 4 }, '戌': { r: 3, c: 4 }, '亥': { r: 4, c: 4 },
  '子': { r: 4, c: 3 }, '丑': { r: 4, c: 2 }, '寅': { r: 4, c: 1 },
  '卯': { r: 3, c: 1 }, '辰': { r: 2, c: 1 },
}

// 获取某宫格位置对应的宫
const getPalaceAt = (branch: string): PalaceResponse | null => {
  if (!ziwei.value) return null
  return ziwei.value.palaces.find(p => p.branch === branch) ?? null
}

// 化曜颜色
const SIHUA_COLOR: Record<string, string> = {
  '化禄': '#16a34a', '化权': '#2563eb', '化科': '#7c3aed', '化忌': '#dc2626',
  '禄': '#16a34a', '权': '#2563eb', '科': '#7c3aed', '忌': '#dc2626',
}
function sihuaColor(tag: string): string {
  return SIHUA_COLOR[tag] ?? SIHUA_COLOR[tag.slice(1)] ?? '#666'
}
function scoreColor(pct: number): string {
  if (pct >= 80) return '#16a34a'
  if (pct >= 60) return '#ca8a04'
  return '#dc2626'
}

// 大运当前高亮
const currentYear = new Date().getFullYear()
const currentDayunIndex = computed(() => {
  if (!ziwei.value?.dayun?.items?.length) return null
  const items = ziwei.value.dayun.items
  for (let i = 0; i < items.length; i++) {
    const next = items[i + 1]
    if (items[i].start_year <= currentYear && (!next || currentYear < next.start_year)) {
      return items[i].index
    }
  }
  return null
})

function onChip(term: string) {
  store.setGlossaryTerm(term)
}

// 格局展开控制
const showAllPatterns = ref(false)
const visiblePatterns = computed(() => {
  const list = ziwei.value?.patterns ?? []
  return showAllPatterns.value ? list : list.slice(0, 3)
})
</script>

<template>
  <div class="chapter-ziwei">

    <!-- 参数控制栏 -->
    <ParamControl chapter-key="ziwei" />

    <!-- 加载骨架屏 -->
    <div v-if="loading" class="loading-wrap">
      <div class="skel-card" style="height: 544px;" />
      <div class="skel-card" style="height: 160px;" />
      <div class="skel-card" style="height: 80px;" />
    </div>

    <!-- 错误 -->
    <div v-else-if="error" class="error-block">
      <p class="error-txt">{{ error }}</p>
      <button class="btn-sec" @click="store.loadChapterData(3, true)">重新计算</button>
    </div>

    <!-- 数据 -->
    <template v-else-if="ziwei">

      <!-- ══ 3-1 命盘总览 ══════════════════════════════════════ -->
      <section id="section-3-1" class="section-block">
        <div class="section-title-row">
          <span class="section-num">3-1</span>
          <h2 class="section-title">命盘总览</h2>
        </div>

        <!-- 结论段落 -->
        <div class="conclusion-block">
          <p class="conclusion-text">{{ ziwei.summary }}</p>
        </div>

        <!-- ─── 4×4 宫格盘 ─────────────────────────── -->
        <div class="palace-board">
          <!-- 12个外围宫格 -->
          <div
            v-for="(pos, branch) in BRANCH_GRID"
            :key="branch"
            class="palace-cell"
            :class="{ active: getPalaceAt(branch)?.index === activePalaceIndex }"
            :style="{ gridRow: pos.r, gridColumn: pos.c }"
            @click="getPalaceAt(branch) && clickPalace(getPalaceAt(branch)!)"
          >
            <template v-if="getPalaceAt(branch)">
              <div class="palace-header">
                <span class="palace-name">{{ getPalaceAt(branch)!.name }}</span>
                <span class="palace-branch">{{ branch }}</span>
              </div>
              <!-- 化曜标记 -->
              <div class="palace-sihua">
                <span
                  v-for="star in getPalaceAt(branch)!.main_stars"
                  :key="star.name"
                  class="sihua-tag"
                >
                  <span
                    v-for="t in star.transforms"
                    :key="t"
                    :style="{ color: sihuaColor(t) }"
                  >{{ t }}</span>
                </span>
              </div>
              <!-- 主星 -->
              <div class="palace-main-stars">
                <span
                  v-for="star in getPalaceAt(branch)!.main_stars"
                  :key="star.name"
                  class="main-star"
                  :class="'bright-' + star.brightness_val"
                  @click.stop="onChip(star.name)"
                >{{ star.name }}</span>
              </div>
              <!-- 辅星 -->
              <div class="palace-aux-stars">
                <span
                  v-for="aux in getPalaceAt(branch)!.aux_stars.slice(0, 3)"
                  :key="aux"
                  class="aux-star"
                  @click.stop="onChip(aux)"
                >{{ aux }}</span>
              </div>
              <!-- 小限年龄 -->
              <div class="palace-ages">
                <span
                  v-for="age in getPalaceAt(branch)!.xiaoxian_ages.slice(0, 2)"
                  :key="age"
                  class="age-chip"
                >{{ age }}</span>
              </div>
            </template>
          </div>

          <!-- 中心 2×2 命主信息 -->
          <div class="palace-center" style="grid-row: 2 / 4; grid-column: 2 / 4;">
            <p class="center-label">命主</p>
            <p class="center-star" @click="onChip(ziwei.life_ruler_star)">{{ ziwei.life_ruler_star }}</p>
            <p class="center-label mt-2">身主</p>
            <p class="center-star" @click="onChip(ziwei.body_ruler_star)">{{ ziwei.body_ruler_star }}</p>
            <p class="center-ju">{{ ziwei.wuxing_ju_name }}</p>
          </div>
        </div>

        <!-- 激活宫格详情 -->
        <Transition name="slide-down">
          <div v-if="activePalace" class="palace-detail">
            <div class="detail-header">
              <span class="detail-name">{{ activePalace.name }}</span>
              <span class="detail-branch">{{ activePalace.branch }}</span>
              <button class="btn-close" @click="activePalaceIndex = null; store.setActivePalace(null)">✕</button>
            </div>
            <p class="detail-analysis">{{ activePalace.analysis }}</p>
            <p class="detail-conclusion" v-if="activePalace.conclusion">结论：{{ activePalace.conclusion }}</p>
            <p class="detail-suggestion" v-if="activePalace.suggestion">建议：{{ activePalace.suggestion }}</p>
            <div class="detail-tags" v-if="activePalace.analysis_tags?.length">
              <span v-for="tag in activePalace.analysis_tags" :key="tag" class="badge">{{ tag }}</span>
            </div>
          </div>
        </Transition>
      </section>

      <!-- ══ 3-2 命身主星 ══════════════════════════════════════ -->
      <section id="section-3-2" class="section-block">
        <div class="section-title-row">
          <span class="section-num">3-2</span>
          <h2 class="section-title">命身主星</h2>
        </div>

        <div class="conclusion-block">
          <p class="conclusion-text">
            命主星
            <span class="chip-term" @click="onChip(ziwei.life_ruler_star)">{{ ziwei.life_ruler_star }}</span>，
            身主星
            <span class="chip-term" @click="onChip(ziwei.body_ruler_star)">{{ ziwei.body_ruler_star }}</span>，
            <span class="chip-term" @click="onChip(ziwei.wuxing_ju_name)">{{ ziwei.wuxing_ju_name }}</span>。
            命宫 {{ ziwei.life_palace_gz }}，身宫 {{ ziwei.body_palace_gz }}。
          </p>
        </div>

        <div class="ruler-stars-grid">
          <div class="ruler-card">
            <p class="ruler-type">命主星</p>
            <p class="ruler-star" @click="onChip(ziwei.life_ruler_star)">{{ ziwei.life_ruler_star }}</p>
            <p class="ruler-palace">命宫：{{ ziwei.life_palace_gz }}</p>
          </div>
          <div class="ruler-card">
            <p class="ruler-type">身主星</p>
            <p class="ruler-star" @click="onChip(ziwei.body_ruler_star)">{{ ziwei.body_ruler_star }}</p>
            <p class="ruler-palace">身宫：{{ ziwei.body_palace_gz }}</p>
          </div>
          <div class="ruler-card ju-card">
            <p class="ruler-type">五行局</p>
            <p class="ruler-ju" @click="onChip(ziwei.wuxing_ju_name)">{{ ziwei.wuxing_ju_name }}</p>
            <p class="ruler-palace">{{ ziwei.wuxing_ju }}局</p>
          </div>
        </div>
      </section>

      <!-- ══ 3-3 格局类型 ══════════════════════════════════════ -->
      <section v-if="ziwei.patterns?.length" id="section-3-3" class="section-block">
        <div class="section-title-row">
          <span class="section-num">3-3</span>
          <h2 class="section-title">格局类型</h2>
        </div>

        <div class="conclusion-block">
          <p class="conclusion-text">
            命盘共 {{ ziwei.patterns.length }} 个格局，
            <span class="chip-term" @click="onChip(ziwei.patterns[0].name)">{{ ziwei.patterns[0].name }}</span>
            （{{ ziwei.patterns[0].level }}）。
            <span v-if="ziwei.patterns[0].description"> {{ ziwei.patterns[0].description }}</span>
          </p>
        </div>

        <div class="pattern-cards">
          <div v-for="pat in visiblePatterns" :key="pat.name" class="pattern-card">
            <div class="pattern-header">
              <span class="pattern-name" @click="onChip(pat.name)">{{ pat.name }}</span>
              <span class="pattern-level" :class="'level-' + pat.level">{{ pat.level }}</span>
            </div>
            <p class="pattern-desc">{{ pat.description }}</p>
            <p v-if="pat.source" class="pattern-source">── {{ pat.source }}</p>
          </div>
        </div>
        <button
          v-if="ziwei.patterns.length > 3"
          class="show-more-btn"
          @click="showAllPatterns = !showAllPatterns"
        >{{ showAllPatterns ? '收起' : `查看更多 ${ziwei.patterns.length - 3} 个格局` }}</button>
      </section>

      <!-- ══ 3-4 建议与化解 ══════════════════════════════════= -->
      <section v-if="ziwei.remedies?.length || ziwei.life_suggestions?.length" id="section-3-4" class="section-block">
        <div class="section-title-row">
          <span class="section-num">3-4</span>
          <h2 class="section-title">建议与化解</h2>
        </div>

        <div class="advice-two-cols">
          <!-- 趋吉化解 -->
          <div v-if="ziwei.remedies?.length" class="advice-col">
            <h3 class="advice-col-title">趋吉化解</h3>
            <div class="remedy-list">
              <div
                v-for="rem in ziwei.remedies"
                :key="rem.id"
                class="remedy-item"
              >
                <span class="remedy-cat">{{ rem.cost_level }}</span>
                <p class="remedy-action">{{ rem.name }}</p>
                <p v-if="rem.actions?.length" class="remedy-actions-list">{{ rem.actions.join('；') }}</p>
                <p v-if="rem.evidence" class="remedy-reason">{{ rem.evidence }}</p>
              </div>
            </div>
          </div>
          <!-- 生活建议 -->
          <div v-if="ziwei.life_suggestions?.length" class="advice-col">
            <h3 class="advice-col-title">生活建议</h3>
            <div class="suggestion-list">
              <div
                v-for="sug in ziwei.life_suggestions"
                :key="sug.id"
                class="suggestion-item"
              >
                <span class="sug-domain">{{ sug.category_label }}</span>
                <p class="sug-text">{{ sug.short_desc }}</p>
                <div class="sug-priority-dot"
                  :style="{ background: sug.priority <= 2 ? 'var(--danger-dark)' : sug.priority <= 4 ? 'var(--accent)' : 'var(--success-dark)' }"
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- ══ 3-5 大限流年 ══════════════════════════════════════ -->
      <section id="section-3-5" class="section-block">
        <div class="section-title-row">
          <span class="section-num">3-5</span>
          <h2 class="section-title">大限流年</h2>
        </div>

        <div class="conclusion-block" v-if="ziwei.dayun?.items?.length">
          <p class="conclusion-text">
            起运年龄 {{ ziwei.dayun.start_age }} 岁（{{ ziwei.dayun.start_age_text }}），
            行运<strong>{{ ziwei.dayun.forward ? '顺' : '逆' }}</strong>。
          </p>
        </div>

        <!-- 大限时间轴 -->
        <div v-if="ziwei.dayun?.items?.length" class="dayun-timeline">
          <p class="timeline-label">大限</p>
          <div class="dayun-track">
            <div
              v-for="item in ziwei.dayun.items"
              :key="item.index"
              class="dayun-cell"
              :class="{ current: item.index === currentDayunIndex }"
            >
              <span class="dayun-gz">{{ item.ganzhi }}</span>
              <span class="dayun-age">{{ item.start_age }}~{{ item.end_age }}岁</span>
              <span class="dayun-yr">{{ item.start_year }}</span>
              <!-- 四化标记 -->
              <div class="dayun-sihua">
                <span
                  v-for="(star, tag) in item.sihua"
                  :key="tag"
                  class="sihua-mini"
                  :style="{ color: sihuaColor(tag) }"
                  :title="star"
                >{{ tag.slice(-1) }}</span>
              </div>
            </div>
          </div>
        </div>

        <p v-else class="card-empty">暂无大限数据</p>
      </section>

      <!-- ── 流年概览 ── -->
      <section v-if="ziwei.liunian" id="section-3-6" class="section-block">
        <div class="section-title-row">
          <span class="section-num">3-6</span>
          <h2 class="section-title">流年概览</h2>
          <span class="month-badge">{{ ziwei.liunian.year }}年 · {{ ziwei.liunian.year_gz }}</span>
        </div>
        <div v-if="ziwei.liunian.sihua && Object.keys(ziwei.liunian.sihua).length" class="sihua-row">
          <span class="sihua-title">流年四化</span>
          <span
            v-for="(star, tag) in ziwei.liunian.sihua"
            :key="tag"
            class="sihua-tag"
            :style="{ background: sihuaColor(tag) + '1a', color: sihuaColor(tag), borderColor: sihuaColor(tag) + '66' }"
          >{{ star }} {{ tag }}</span>
        </div>
        <p v-else class="card-empty">暂无流年四化数据</p>
      </section>

      <!-- ── 流月详情 ── -->
      <section v-if="ziwei.liuyue?.length" id="section-3-7" class="section-block">
        <div class="section-title-row">
          <span class="section-num">3-7</span>
          <h2 class="section-title">流月详情</h2>
        </div>
        <div class="liuyue-grid">
          <div
            v-for="ly in ziwei.liuyue"
            :key="ly.month"
            class="liuyue-cell"
          >
            <div class="ly-header">
              <span class="ly-month">{{ ly.month }}月</span>
              <span class="ly-gz">{{ ly.month_gz }}</span>
              <span class="ly-palace">{{ ly.palace_name }}</span>
            </div>
            <div v-if="ly.sihua && Object.keys(ly.sihua).length" class="ly-sihua">
              <span
                v-for="(star, tag) in ly.sihua"
                :key="tag"
                class="sihua-mini"
                :style="{ color: sihuaColor(tag) }"
                :title="star"
              >{{ tag.slice(-1) }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- ── 年度预测 ── -->
      <section v-if="ziwei.forecast?.yearly" id="section-3-8" class="section-block">
        <div class="section-title-row">
          <span class="section-num">3-8</span>
          <h2 class="section-title">年度预测</h2>
          <span class="month-badge">{{ ziwei.forecast.year }}年 · {{ ziwei.forecast.yearly.ganzhi }}</span>
        </div>
        <div class="forecast-score">
          <span class="fc-score-num" :style="{ color: scoreColor(ziwei.forecast.yearly.score * 10) }">{{ ziwei.forecast.yearly.score }}</span>
          <span class="fc-palace">流年命宫：{{ ziwei.forecast.yearly.palace_name }}</span>
        </div>
        <div v-if="ziwei.forecast.yearly.overall" class="conclusion-block">
          <p class="conclusion-text">{{ ziwei.forecast.yearly.overall }}</p>
        </div>
        <div v-if="ziwei.forecast.yearly.details && Object.keys(ziwei.forecast.yearly.details).length" class="forecast-domains">
          <div v-for="(val, key) in ziwei.forecast.yearly.details" :key="key" class="fc-domain-row">
            <span class="fc-domain-key">{{ key }}</span>
            <span class="fc-domain-val">{{ val }}</span>
          </div>
        </div>
        <div v-if="ziwei.forecast.yearly.events?.length" class="forecast-events">
          <span class="fc-section-lbl">事件预测</span>
          <div v-for="ev in ziwei.forecast.yearly.events" :key="ev.description" class="fc-event-item"
            :class="ev.level === 'high' ? 'ev-high' : ev.level === 'low' ? 'ev-low' : 'ev-mid'">
            <span class="ev-cat">{{ ev.category }}</span>
            <span class="ev-desc">{{ ev.description }}</span>
          </div>
        </div>
        <p v-if="ziwei.forecast.yearly.advice" class="fc-advice">💡 {{ ziwei.forecast.yearly.advice }}</p>
      </section>

    </template>

    <!-- 空态 -->
    <div v-else class="empty-hint">
      <p>点击「重新计算」开始紫微命盘</p>
      <button class="btn-primary" @click="store.loadChapterData(3, true)">开始计算</button>
    </div>

  </div>
</template>

<style scoped>
.chapter-ziwei { display: flex; flex-direction: column; gap: var(--sp-6); }

/* ─── 章节块 ─────────────────────────────────────────────────── */
.section-block {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: var(--sp-6);
  scroll-margin-top: 64px;
}

.section-title-row {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  margin-bottom: var(--sp-4);
  padding-bottom: var(--sp-3);
  border-bottom: 1px solid var(--border);
}

.section-num {
  font-size: var(--fs-xs);
  color: var(--text-3);
  font-family: var(--font-mono);
  background: var(--bg);
  padding: 2px 8px;
  border-radius: 99px;
  border: 1px solid var(--border);
}

.section-title {
  font-size: var(--fs-xl);
  font-weight: 700;
  color: var(--text);
  font-family: var(--font-cn);
}

/* ─── 结论块 ──────────────────────────────────────────────────── */
.conclusion-block {
  padding: var(--sp-4);
  background: var(--surface-2);
  border-radius: var(--radius-sm);
  border-left: 3px solid var(--accent);
  margin-bottom: var(--sp-5);
}

.conclusion-text {
  font-size: var(--fs-md);
  color: var(--text);
  line-height: 1.8;
  font-family: var(--font-cn);
}

.chip-term {
  border-bottom: 1px dashed var(--accent);
  cursor: pointer;
  color: var(--accent-dark);
  font-weight: 600;
}

/* ─── 流年 ─── */
.sihua-row { display: flex; align-items: center; flex-wrap: wrap; gap: var(--sp-2); margin-top: var(--sp-3); }
.sihua-title { font-size: var(--fs-xs); font-weight: 700; color: var(--text-3); margin-right: var(--sp-2); }
.sihua-tag { font-size: var(--fs-xs); font-weight: 600; padding: 2px 10px; border-radius: 10px; border: 1px solid; }

/* ─── 流月网格 ─── */
.liuyue-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(80px, 1fr)); gap: 6px; }
.liuyue-cell { background: var(--surface-2); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: var(--sp-2); }
.ly-header { display: flex; align-items: center; gap: 4px; margin-bottom: 4px; flex-wrap: wrap; }
.ly-month { font-size: var(--fs-sm); font-weight: 700; color: var(--text); }
.ly-gz { font-size: 10px; color: var(--accent-dark); font-weight: 600; }
.ly-palace { font-size: 10px; color: var(--text-3); flex: 1; text-align: right; }
.ly-sihua { display: flex; flex-wrap: wrap; gap: 3px; }

/* ─── 年度预测 ─── */
.forecast-score { display: flex; align-items: center; gap: var(--sp-3); margin-bottom: var(--sp-3); }
.fc-score-num { font-size: 32px; font-weight: 700; line-height: 1; }
.fc-palace { font-size: var(--fs-sm); color: var(--text-2); }
.forecast-domains { display: flex; flex-direction: column; gap: 4px; margin: var(--sp-3) 0; }
.fc-domain-row { display: flex; gap: var(--sp-3); font-size: var(--fs-sm); padding: 3px 0; border-bottom: 1px solid var(--border); }
.fc-domain-key { color: var(--text-3); font-weight: 600; min-width: 60px; }
.fc-domain-val { color: var(--text); flex: 1; }
.forecast-events { margin: var(--sp-3) 0; }
.fc-section-lbl { font-size: var(--fs-xs); font-weight: 700; color: var(--text-3); display: block; margin-bottom: var(--sp-2); }
.fc-event-item { display: flex; align-items: flex-start; gap: var(--sp-2); padding: 4px 0; font-size: var(--fs-sm); }
.fc-event-item.ev-high .ev-cat { background: #fee2e2; color: #dc2626; }
.fc-event-item.ev-low .ev-cat { background: #dcfce7; color: #15803d; }
.fc-event-item.ev-mid .ev-cat { background: #fef3c7; color: #b45309; }
.ev-cat { font-size: var(--fs-xs); font-weight: 700; padding: 1px 6px; border-radius: 10px; background: var(--accent-soft); color: var(--accent); white-space: nowrap; }
.ev-desc { color: var(--text); line-height: 1.5; }
.fc-advice { font-size: var(--fs-sm); color: var(--accent-dark); background: rgba(217,119,6,.07); border-radius: var(--radius-sm); padding: 6px 12px; margin-top: var(--sp-3); }
.palace-board {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  grid-template-rows: repeat(4, var(--ph, 136px));
  gap: 1px;
  background: var(--border);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  overflow: hidden;
  margin-bottom: var(--sp-4);
}

.palace-cell {
  background: var(--surface);
  padding: var(--sp-2);
  cursor: pointer;
  transition: background var(--dur-fast);
  display: flex;
  flex-direction: column;
  gap: 2px;
  overflow: hidden;
  position: relative;
}

.palace-cell:hover { background: var(--accent-glow); }

.palace-cell.active {
  background: var(--accent-lt) !important;
  outline: 2px solid var(--accent);
  outline-offset: -2px;
  z-index: 1;
}

.palace-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.palace-name {
  font-size: var(--fs-xs);
  font-weight: 600;
  color: var(--text-2);
  font-family: var(--font-cn);
}

.palace-branch {
  font-size: 11px;
  color: var(--text-3);
}

.palace-sihua {
  display: flex;
  flex-wrap: wrap;
  gap: 1px;
  min-height: 14px;
}

.sihua-tag { display: contents; }

.palace-main-stars {
  display: flex;
  flex-wrap: wrap;
  gap: 2px;
  margin-top: 1px;
}

.main-star {
  font-size: var(--fs-md);
  font-family: var(--font-cn);
  font-weight: 700;
  color: var(--text);
  cursor: pointer;
  line-height: 1.2;
}

.main-star.bright-6 { color: var(--accent-dark); }  /* 庙 */
.main-star.bright-5 { color: var(--accent-dark); }  /* 旺 */
.main-star.bright-4 { color: var(--accent-dark); }  /* 得 */
.main-star.bright-3 { color: var(--text); }          /* 利 */
.main-star.bright-2 { color: var(--text); }          /* 平 */
.main-star.bright-1 { color: var(--text-3); }        /* 不 */
.main-star.bright-0 { color: var(--text-3); }        /* 陷 */

.palace-aux-stars {
  display: flex;
  flex-wrap: wrap;
  gap: 1px;
  margin-top: 1px;
}

.aux-star {
  font-size: 10px;
  color: var(--text-3);
  cursor: pointer;
  font-family: var(--font-cn);
}
.aux-star:hover { color: var(--text-2); }

.palace-ages {
  display: flex;
  flex-wrap: wrap;
  gap: 2px;
  margin-top: auto;
}

.age-chip {
  font-size: 10px;
  color: var(--text-3);
  padding: 0 3px;
  background: var(--surface-2);
  border-radius: 2px;
  font-family: var(--font-mono);
}

/* ─── 中心命主信息 ─────────────────────────────────────────── */
.palace-center {
  background: var(--bg);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  padding: var(--sp-3);
  text-align: center;
  border: 1px solid var(--border);
}

.center-label {
  font-size: 11px;
  color: var(--text-3);
}

.center-star {
  font-size: var(--fs-xl);
  font-weight: 700;
  font-family: var(--font-cn);
  color: var(--accent-dark);
  cursor: pointer;
  border-bottom: 1px dashed var(--accent);
}

.center-ju {
  font-size: var(--fs-sm);
  color: var(--text-2);
  font-family: var(--font-cn);
  margin-top: var(--sp-2);
}

.mt-2 { margin-top: var(--sp-2); }

/* ─── 宫格详情展开 ────────────────────────────────────────── */
.palace-detail {
  padding: var(--sp-4);
  background: var(--accent-lt);
  border: 1px solid rgba(217,119,6,.2);
  border-radius: var(--radius-sm);
  margin-top: 0;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  margin-bottom: var(--sp-3);
}

.detail-name {
  font-size: var(--fs-xl);
  font-weight: 700;
  font-family: var(--font-cn);
  color: var(--text);
}

.detail-branch {
  font-size: var(--fs-sm);
  color: var(--text-3);
  background: var(--surface);
  padding: 1px 6px;
  border-radius: 3px;
}

.btn-close {
  margin-left: auto;
  font-size: var(--fs-md);
  color: var(--text-3);
  background: none;
  border: none;
  cursor: pointer;
  padding: 2px 6px;
}

.detail-analysis {
  font-size: var(--fs-sm);
  color: var(--text);
  line-height: 1.8;
  font-family: var(--font-cn);
}

.detail-conclusion, .detail-suggestion {
  font-size: var(--fs-sm);
  color: var(--text-2);
  margin-top: var(--sp-2);
  font-family: var(--font-cn);
}

.detail-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: var(--sp-3);
}

.badge {
  font-size: 11px;
  padding: 2px 7px;
  border-radius: 99px;
  background: var(--surface);
  color: var(--text-2);
  border: 1px solid var(--border);
}

/* ─── 命身主星 ──────────────────────────────────────────────── */
.ruler-stars-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: var(--sp-4);
}

.ruler-card {
  padding: var(--sp-4);
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  text-align: center;
}

.ju-card { background: var(--accent-lt); }

.ruler-type { font-size: 11px; color: var(--text-3); margin-bottom: var(--sp-1); }

.ruler-star {
  font-size: 36px;
  font-weight: 700;
  font-family: var(--font-cn);
  color: var(--text);
  cursor: pointer;
  border-bottom: 1px dashed var(--accent);
  display: inline-block;
}

.ruler-ju {
  font-size: 28px;
  font-weight: 700;
  font-family: var(--font-cn);
  color: var(--accent-dark);
  cursor: pointer;
}

.ruler-palace {
  font-size: var(--fs-xs);
  color: var(--text-3);
  margin-top: var(--sp-2);
}

/* ─── 格局卡片 ──────────────────────────────────────────────── */
.pattern-cards {
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
}

.pattern-card {
  padding: var(--sp-4);
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
}

.pattern-header {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  margin-bottom: var(--sp-2);
}

.pattern-name {
  font-size: var(--fs-lg);
  font-weight: 700;
  font-family: var(--font-cn);
  cursor: pointer;
  border-bottom: 1px dashed var(--accent);
  color: var(--accent-dark);
}

.pattern-level {
  font-size: var(--fs-xs);
  padding: 2px 8px;
  border-radius: 99px;
  background: var(--accent);
  color: #fff;
}

.pattern-level.level-上品 { background: #f59e0b; }
.pattern-level.level-中品 { background: var(--accent); }
.pattern-level.level-下品 { background: #6b7280; }

.pattern-desc {
  font-size: var(--fs-sm);
  color: var(--text);
  line-height: 1.7;
  font-family: var(--font-cn);
}

.pattern-source {
  font-size: 11px;
  color: var(--text-3);
  font-style: italic;
  margin-top: var(--sp-2);
}

.show-more-btn {
  background: none;
  border: 1px dashed var(--border-md);
  border-radius: var(--radius-sm);
  padding: 6px 20px;
  color: var(--text-3);
  font-size: var(--fs-sm);
  cursor: pointer;
  margin-top: var(--sp-2);
  width: 100%;
}
.show-more-btn:hover { color: var(--accent); border-color: var(--accent); }

/* ─── 建议两列 ──────────────────────────────────────────────── */
.advice-two-cols {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--sp-5);
}

.advice-col-title {
  font-size: var(--fs-md);
  font-weight: 700;
  color: var(--text-2);
  margin-bottom: var(--sp-3);
  font-family: var(--font-cn);
}

.remedy-list, .suggestion-list {
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
}

.remedy-item, .suggestion-item {
  padding: var(--sp-3);
  background: var(--surface-2);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
}

.remedy-cat, .sug-domain {
  font-size: 11px;
  color: var(--accent-dark);
  background: var(--accent-lt);
  padding: 1px 6px;
  border-radius: 99px;
  font-family: var(--font-cn);
}

.remedy-action, .sug-text {
  font-size: var(--fs-sm);
  color: var(--text);
  line-height: 1.7;
  margin-top: var(--sp-2);
  font-family: var(--font-cn);
}

.remedy-reason {
  font-size: var(--fs-xs);
  color: var(--text-3);
  margin-top: 3px;
}

.sug-score-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-top: var(--sp-2);
}

/* ─── 大限时间轴 ─────────────────────────────────────────────── */
.dayun-timeline { }
.timeline-label { font-size: var(--fs-sm); font-weight: 600; color: var(--text-2); margin-bottom: var(--sp-3); }

.dayun-track {
  display: flex;
  overflow-x: auto;
  gap: 1px;
  padding-bottom: var(--sp-2);
}

.dayun-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--sp-3) var(--sp-4);
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  min-width: 80px;
  gap: 2px;
  cursor: default;
  flex-shrink: 0;
}

.dayun-cell.current {
  border-color: var(--accent);
  background: var(--accent-lt);
  box-shadow: 0 0 0 2px var(--accent-glow);
}

.dayun-gz { font-size: var(--fs-lg); font-family: var(--font-cn); font-weight: 700; color: var(--text); }
.dayun-age { font-size: 11px; color: var(--text-3); }
.dayun-yr { font-size: 10px; color: var(--text-3); font-family: var(--font-mono); }

.dayun-sihua {
  display: flex;
  gap: 2px;
  margin-top: 2px;
}

.sihua-mini {
  font-size: 11px;
  font-weight: 700;
  font-family: var(--font-cn);
  cursor: help;
}

.card-empty { color: var(--text-3); font-size: var(--fs-sm); }

/* ─── 骨架/错误/空 ───────────────────────────────────────────── */
.loading-wrap { display: flex; flex-direction: column; gap: var(--sp-4); }
.skel-card {
  border-radius: var(--radius);
  background: linear-gradient(90deg, #e2e8f0 25%, #f1f5f9 50%, #e2e8f0 75%);
  background-size: 400px;
  animation: shimmer 1.2s infinite;
}
.error-block { display: flex; align-items: center; gap: var(--sp-3); padding: var(--sp-4); background: #fee2e2; border-radius: var(--radius-sm); }
.error-txt { color: var(--danger-dark); font-size: var(--fs-sm); flex: 1; }
.empty-hint { display: flex; flex-direction: column; align-items: center; gap: var(--sp-3); padding: var(--sp-8) 0; color: var(--text-3); }
.btn-primary { padding: 8px 20px; background: var(--accent); color: #fff; border: none; border-radius: var(--radius-sm); font-size: var(--fs-sm); font-weight: 600; cursor: pointer; }
.btn-sec { padding: 5px 14px; background: transparent; border: 1px solid var(--border-md); border-radius: var(--radius-sm); font-size: var(--fs-sm); cursor: pointer; color: var(--text-2); }

/* ─── 过渡动画 ───────────────────────────────────────────────── */
.slide-down-enter-active, .slide-down-leave-active {
  transition: all 0.2s ease;
  overflow: hidden;
}
.slide-down-enter-from, .slide-down-leave-to {
  opacity: 0;
  max-height: 0;
  transform: translateY(-8px);
}
.slide-down-enter-to, .slide-down-leave-from {
  opacity: 1;
  max-height: 600px;
}
</style>
