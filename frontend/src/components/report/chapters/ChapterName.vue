<script setup lang="ts">
/**
 * ChapterName.vue — ④ 姓名学章节
 * 数据: store.nameData (NameAnalysisResponse)
 * API字段: tianGe/renGe/diGe/waiGe/zongGe + _str / sancai_pattern / element_composition
 */
import { computed, onMounted } from 'vue'
import { useReportStore } from '@/stores/report'
import ParamControl from '@/components/report/ParamControl.vue'

const store = useReportStore()

onMounted(() => {
  if (!store.nameData && !store.loadingMap['name']) {
    store.loadChapterData(4)
  }
})

const nm      = computed(() => store.nameData)
const loading = computed(() => store.loadingMap['name'])
const error   = computed(() => store.errorMap['name'])

// 五行颜色映射
const WX_CSS: Record<string, string> = {
  '木': 'var(--wx-wood)',  '火': 'var(--wx-fire)',  '土': 'var(--wx-earth)',
  '金': 'var(--wx-metal)', '水': 'var(--wx-water)',
}
function elColor(el: string): string { return WX_CSS[el] ?? 'var(--text-3)' }

// 评分颜色
function scoreColor(s: number): string {
  return s >= 80 ? 'var(--success-dark)' : s >= 60 ? 'var(--accent)' : 'var(--danger-dark)'
}

// SVG 圆形进度环计算
function circleProps(score: number) {
  const r = 44, circ = 2 * Math.PI * r
  return {
    dash: `${(score / 100) * circ} ${circ}`,
    offset: circ * 0.25,  // 从顶部开始
  }
}

// 全名（姓+名 拼合）
const fullName = computed(() => nm.value ? nm.value.surname + nm.value.given_name : '')

// 三才配置分析
const sancaiText = computed(() => {
  if (!nm.value) return ''
  const s = nm.value.sancai.score
  return s >= 8 ? '吉祥配置，相生相扶' : s >= 6 ? '尚可，小有克制' : '欠佳，建议重新选字'
})

// 五格数据（NameAnalysisResponse: tianke/renke/dike/waike/zonge 均为 GridInfoResponse）
const wugeList = computed(() => {
  if (!nm.value) return []
  const d = nm.value
  return [
    { key: '天格', val: d.tianke.number, str: d.tianke.lucky, note: '姓的根源，先天之数', element: d.tianke.element, score: d.tianke.score, desc: d.tianke.desc },
    { key: '人格', val: d.renke.number, str: d.renke.lucky, note: '五格核心，主命主性格', element: d.renke.element, score: d.renke.score, desc: d.renke.desc },
    { key: '地格', val: d.dike.number, str: d.dike.lucky, note: '名字本体，主峰期运势', element: d.dike.element, score: d.dike.score, desc: d.dike.desc },
    { key: '外格', val: d.waike.number, str: d.waike.lucky, note: '社交表现，对外展现', element: d.waike.element, score: d.waike.score, desc: d.waike.desc },
    { key: '总格', val: d.zonge.number, str: d.zonge.lucky, note: '综合运势，成就表现', element: d.zonge.element, score: d.zonge.score, desc: d.zonge.desc },
  ]
})

function onChip(term: string) {
  store.setGlossaryTerm(term)
}

// 五行相生判断（用于字间关系箭头）
const SHENG_MAP: Record<string, string> = { '木': '火', '火': '土', '土': '金', '金': '水', '水': '木' }
function isSheng(from: string, to: string): boolean {
  return SHENG_MAP[from] === to
}

// 五格五行序列（天→人→地→外→总）
const gridElements = computed(() => {
  if (!nm.value) return []
  return [
    { label: '天格', el: nm.value.tianke.element },
    { label: '人格', el: nm.value.renke.element },
    { label: '地格', el: nm.value.dike.element },
    { label: '外格', el: nm.value.waike.element },
    { label: '总格', el: nm.value.zonge.element },
  ]
})
</script>

<template>
  <div class="chapter-name">

    <!-- 姓名参数控制栏 -->
    <ParamControl chapter-key="name" />

    <!-- 加载中 -->
    <div v-if="loading" class="loading-wrap">
      <div class="skel-card" style="height: 260px;" />
      <div class="skel-card" style="height: 140px;" />
      <div class="skel-card" style="height: 200px;" />
    </div>

    <div v-else-if="error" class="error-block">
      <p class="error-txt">{{ error }}</p>
      <button class="btn-sec" @click="store.loadChapterData(4, true)">重新分析</button>
    </div>

    <template v-else-if="nm">

      <!-- ══ 4-1 五格数理 ═══════════════════════════════════════════ -->
      <section id="section-4-1" class="section-block">
        <div class="section-title-row">
          <span class="section-num">4-1</span>
          <h2 class="section-title">五格数理</h2>
        </div>

        <div class="conclusion-block">
          <p class="conclusion-text">
            <span class="chip-term" @click="onChip(fullName)">{{ fullName }}</span>
            五格数理综合得分
            <strong :style="{ color: scoreColor(nm.overall_score) }">{{ nm.overall_score }}</strong>
            分。人格数 {{ nm.renke.number }}（{{ nm.renke.lucky }}）是五格核心，主命主性格。
          </p>
        </div>

        <!-- 五格竖排连线图 -->
        <div class="wuge-layout">
          <!-- 竖列主图 -->
          <div class="wuge-tower">
            <!-- 天 -->
            <div class="wuge-box wuge-tian">
              <span class="wuge-key">天格</span>
              <span class="wuge-num">{{ nm.tianke.number }}</span>
              <span class="wuge-str">{{ nm.tianke.lucky }}</span>
            </div>
            <div class="wuge-connector" />
            <!-- 人 -->
            <div class="wuge-box wuge-ren" :style="{ borderColor: 'var(--accent)', boxShadow: '0 0 0 2px var(--accent-glow)' }">
              <span class="wuge-key">人格</span>
              <span class="wuge-num" :style="{ color: 'var(--accent-dark)', fontSize: '40px' }">{{ nm.renke.number }}</span>
              <span class="wuge-str">{{ nm.renke.lucky }}</span>
              <!-- 人格强度进度条 -->
              <div class="renke-bar-wrap">
                <div class="renke-bar" :style="{ width: (nm.renke.score * 10) + '%', background: scoreColor(nm.renke.score * 10) }" />
              </div>
              <span class="renke-score">{{ nm.renke.score }}/10</span>
            </div>
            <div class="wuge-connector" />
            <!-- 地 -->
            <div class="wuge-box wuge-di">
              <span class="wuge-key">地格</span>
              <span class="wuge-num">{{ nm.dike.number }}</span>
              <span class="wuge-str">{{ nm.dike.lucky }}</span>
            </div>
          </div>

          <!-- 右侧外格/总格 -->
          <div class="wuge-side">
            <div class="wuge-box wuge-wai">
              <span class="wuge-key">外格</span>
              <span class="wuge-num">{{ nm.waike.number }}</span>
              <span class="wuge-str">{{ nm.waike.lucky }}</span>
            </div>
            <div class="wuge-box wuge-zong">
              <span class="wuge-key">总格</span>
              <span class="wuge-num">{{ nm.zonge.number }}</span>
              <span class="wuge-str">{{ nm.zonge.lucky }}</span>
            </div>
          </div>

          <!-- 字段说明 -->
          <div class="wuge-desc">
            <div v-for="item in wugeList" :key="item.key" class="wuge-desc-row">
              <span class="desc-key">{{ item.key }}</span>
              <span class="desc-val" @click="onChip(item.str)">{{ item.val }}（{{ item.str }}）</span>
              <span v-if="item.score != null" class="desc-score" :style="{ color: scoreColor(item.score * 10) }">{{ item.score }}/10</span>
              <span class="desc-note">{{ item.note }}</span>
              <p v-if="item.desc" class="desc-expand">{{ item.desc }}</p>
            </div>
          </div>
        </div>
      </section>

      <!-- ══ 4-2 三才配置 ═══════════════════════════════════════════ -->
      <section id="section-4-2" class="section-block">
        <div class="section-title-row">
          <span class="section-num">4-2</span>
          <h2 class="section-title">三才配置</h2>
        </div>

        <div class="conclusion-block">
          <p class="conclusion-text">
            三才配置
            <span class="chip-term" @click="onChip('三才')">{{ nm.sancai.pattern }}</span>，
            <template v-if="nm.sancai.lucky">
              <strong :style="{ color: nm.sancai.lucky.includes('吉') ? 'var(--success-dark)' : nm.sancai.lucky.includes('凶') ? 'var(--danger-dark)' : 'var(--accent)' }">{{ nm.sancai.lucky }}</strong>，
            </template>
            得分 <strong :style="{ color: scoreColor(nm.sancai.score * 10) }">{{ nm.sancai.score }}</strong>/10。
            {{ nm.sancai.desc || sancaiText }}。
          </p>
        </div>

        <div class="sancai-visual">
          <!-- 三色横条 -->
          <div class="sancai-bars">
            <div
              v-for="(el, i) in nm.sancai.pattern.split('')"
              :key="i"
              class="sancai-bar"
              :style="{ background: elColor(el), '--el-color': elColor(el) }"
            >
              <span class="sancai-el">{{ el }}</span>
              <span class="sancai-pos">{{ ['天', '人', '地'][i] }}</span>
            </div>
          </div>

          <!-- 分数 -->
          <div class="sancai-score-box">
            <svg width="100" height="100" viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="44" fill="none" stroke="var(--border)" stroke-width="8" />
              <circle
                cx="50" cy="50" r="44" fill="none"
                :stroke="scoreColor(nm.sancai.score * 10)"
                stroke-width="8"
                stroke-linecap="round"
                :stroke-dasharray="circleProps(nm.sancai.score * 10).dash"
                :stroke-dashoffset="-circleProps(nm.sancai.score * 10).offset"
                transform="rotate(-90 50 50)"
              />
              <text x="50" y="54" text-anchor="middle" font-size="22" font-weight="bold"
                :fill="scoreColor(nm.sancai.score * 10)" font-family="monospace">{{ nm.sancai.score }}</text>
            </svg>
          </div>
        </div>
      </section>

      <!-- ══ 4-3 姓名五行 ═══════════════════════════════════════════ -->
      <section id="section-4-3" class="section-block">
        <div class="section-title-row">
          <span class="section-num">4-3</span>
          <h2 class="section-title">姓名五行</h2>
        </div>

        <div class="conclusion-block">
          <p class="conclusion-text">
            {{ fullName }}五格五行：天格
            <span class="chip-term" @click="onChip(nm.tianke.element)">{{ nm.tianke.element }}</span>
            · 人格
            <span class="chip-term" @click="onChip(nm.renke.element)">{{ nm.renke.element }}</span>
            · 地格
            <span class="chip-term" @click="onChip(nm.dike.element)">{{ nm.dike.element }}</span>，
            三才配置 {{ nm.sancai.pattern }}（{{ nm.sancai.lucky }}）。
          </p>
        </div>

        <!-- 五格五行卡片 + 相生/相克箭头 -->
        <div class="element-cards">
          <template v-for="(item, i) in gridElements" :key="item.label">
            <div class="el-card" :style="{ '--el': elColor(item.el), background: elColor(item.el) }">
              <p class="el-char">{{ item.label }}</p>
              <p class="el-el">{{ item.el }}</p>
            </div>
            <!-- 关系箭头 -->
            <div
              v-if="i < gridElements.length - 1"
              class="el-arrow"
              :class="isSheng(item.el, gridElements[i + 1].el) ? 'sheng' : 'ke'"
            >
              {{ isSheng(item.el, gridElements[i + 1].el) ? '⦶' : '⦷' }}
            </div>
          </template>
        </div>
      </section>

      <!-- ══ 4-4 吉凶评分与建议 ═══════════════════════════════════ -->
      <section id="section-4-4" class="section-block">
        <div class="section-title-row">
          <span class="section-num">4-4</span>
          <h2 class="section-title">吉凶评分与建议</h2>
        </div>

        <div class="score-layout">
          <!-- 圆形进度环 -->
          <div class="score-ring-wrap">
            <svg width="140" height="140" viewBox="0 0 120 120">
              <circle cx="60" cy="60" r="50" fill="none" stroke="var(--border)" stroke-width="10" />
              <circle
                cx="60" cy="60" r="50" fill="none"
                :stroke="scoreColor(nm.overall_score)"
                stroke-width="10"
                stroke-linecap="round"
                :stroke-dasharray="`${(nm.overall_score / 100) * (2 * Math.PI * 50)} ${2 * Math.PI * 50}`"
                :stroke-dashoffset="-(2 * Math.PI * 50) * 0.25"
                transform="rotate(-90 60 60)"
              />
              <text x="60" y="64" text-anchor="middle" font-size="26" font-weight="900"
                :fill="scoreColor(nm.overall_score)" font-family="monospace">{{ nm.overall_score }}</text>
            </svg>
            <p class="ring-label">综合得分</p>
          </div>

          <!-- 文字评价 -->
          <div class="score-text">
            <p class="conclusion-text">{{ nm.summary }}</p>
          </div>
        </div>

        <!-- 改名建议 -->
        <div v-if="nm.overall_score < 70" class="improve-banner">
          <p class="improve-text">建议考虑改名，可参考以下五行方向</p>
          <router-link to="/name" class="btn-improve">前往改名页</router-link>
        </div>
      </section>

    </template>

    <div v-else class="empty-hint">
      <p>点击「重新分析」开始姓名分析</p>
      <button class="btn-primary" @click="store.loadChapterData(4, true)">开始分析</button>
    </div>

  </div>
</template>

<style scoped>
.chapter-name { display: flex; flex-direction: column; gap: var(--sp-6); }

/* ─── 章节块 ─────────────────────────────────────────────────── */
.section-block {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: var(--sp-6);
  scroll-margin-top: 64px;
}
.section-title-row {
  display: flex; align-items: center; gap: var(--sp-3);
  margin-bottom: var(--sp-4); padding-bottom: var(--sp-3);
  border-bottom: 1px solid var(--border);
}
.section-num {
  font-size: var(--fs-xs); color: var(--text-3);
  font-family: var(--font-mono); background: var(--bg);
  padding: 2px 8px; border-radius: 99px; border: 1px solid var(--border);
}
.section-title { font-size: var(--fs-xl); font-weight: 700; color: var(--text); font-family: var(--font-cn); }

.conclusion-block {
  padding: var(--sp-4); background: var(--surface-2);
  border-radius: var(--radius-sm); border-left: 3px solid var(--accent);
  margin-bottom: var(--sp-5);
}
.conclusion-text { font-size: var(--fs-md); color: var(--text); line-height: 1.8; font-family: var(--font-cn); }

.chip-term {
  border-bottom: 1px dashed var(--accent); cursor: pointer;
  color: var(--accent-dark); font-weight: 600;
}

/* ─── 五格竖排图 ──────────────────────────────────────────────── */
.wuge-layout {
  display: grid;
  grid-template-columns: 160px 120px 1fr;
  gap: var(--sp-5);
  align-items: start;
}

.wuge-tower {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0;
}

.wuge-box {
  width: 140px;
  text-align: center;
  padding: var(--sp-3);
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.wuge-ren {
  background: var(--accent-lt);
  border-color: var(--accent);
  width: 148px;
}

.wuge-connector {
  width: 2px;
  height: 16px;
  background: var(--border-md);
  margin: 0 auto;
}

.wuge-key { font-size: 11px; color: var(--text-3); font-family: var(--font-cn); }

.wuge-num {
  font-size: 32px;
  font-weight: 900;
  color: var(--text);
  font-family: var(--font-mono);
  line-height: 1.1;
}

.wuge-str { font-size: var(--fs-xs); color: var(--text-2); font-family: var(--font-cn); }

.renke-bar-wrap {
  height: 4px;
  background: var(--border);
  border-radius: 99px;
  overflow: hidden;
  margin-top: var(--sp-2);
}

.renke-bar {
  height: 100%;
  border-radius: 99px;
  transition: width 0.8s ease;
  min-width: 4px;
}

.renke-score { font-size: 11px; color: var(--text-3); font-family: var(--font-mono); }

.wuge-side {
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
  padding-top: var(--sp-4);
}

.wuge-wai, .wuge-zong { width: 100px; }

.lucky-nums { margin-top: var(--sp-3); }
.lucky-label { font-size: 11px; color: var(--text-3); margin-bottom: var(--sp-1); }
.lucky-chips { display: flex; flex-wrap: wrap; gap: 4px; }
.lucky-chip {
  font-size: var(--fs-xs); font-family: var(--font-mono);
  padding: 1px 7px; border-radius: 99px;
  background: var(--accent-lt); color: var(--accent-dark);
  border: 1px solid rgba(217,119,6,.2);
}

.wuge-desc {
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
  padding-top: var(--sp-1);
}

.wuge-desc-row {
  display: grid;
  grid-template-columns: 36px 120px 1fr;
  gap: var(--sp-3);
  align-items: start;
  padding: var(--sp-2) 0;
  border-bottom: 1px solid var(--border);
}

.desc-key { font-size: var(--fs-xs); color: var(--text-3); font-family: var(--font-cn); font-weight: 600; }
.desc-val { font-size: var(--fs-sm); font-weight: 700; color: var(--accent-dark); cursor: pointer; font-family: var(--font-cn); }
.desc-note { font-size: var(--fs-xs); color: var(--text-3); line-height: 1.5; }

/* ─── 三才 ─────────────────────────────────────────────────── */
.sancai-visual {
  display: flex;
  align-items: center;
  gap: var(--sp-8);
}

.sancai-bars {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
  flex: 1;
}

.sancai-bar {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  height: 44px;
  border-radius: var(--radius-sm);
  padding: 0 var(--sp-4);
  color: #fff;
  font-family: var(--font-cn);
}

.sancai-el { font-size: var(--fs-xl); font-weight: 700; }
.sancai-pos { font-size: var(--fs-xs); opacity: .75; }

.sancai-score-box { flex-shrink: 0; }

/* ─── 五行卡片 ──────────────────────────────────────────────── */
.element-cards {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  flex-wrap: wrap;
}

.el-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--sp-4) var(--sp-5);
  border-radius: var(--radius-sm);
  color: #fff;
  min-width: 72px;
}

.el-char { font-size: 40px; font-weight: 700; font-family: var(--font-cn); line-height: 1; }
.el-el { font-size: var(--fs-sm); opacity: .85; margin-top: var(--sp-1); }

.el-arrow {
  font-size: 22px;
  font-weight: 700;
}
.el-arrow.sheng { color: var(--success-dark); }
.el-arrow.ke { color: var(--danger-dark); }

/* ─── 评分区 -->
.score-layout {
  display: flex;
  gap: var(--sp-6);
  align-items: flex-start;
}

.score-ring-wrap {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--sp-2);
}

.ring-label { font-size: var(--fs-xs); color: var(--text-3); }

.score-text { flex: 1; }

.details-block {
  font-size: var(--fs-sm);
  color: var(--text-2);
  background: var(--surface-2);
  padding: var(--sp-3);
  border-radius: var(--radius-sm);
  border-left: 3px solid var(--border-md);
  line-height: 1.7;
  margin-top: var(--sp-3);
  font-family: var(--font-cn);
  max-height: 180px;
  overflow-y: auto;
}

.improve-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--sp-3) var(--sp-4);
  background: #fef9c3;
  border: 1px solid #fde047;
  border-radius: var(--radius-sm);
  margin-top: var(--sp-4);
}

.improve-text { font-size: var(--fs-sm); color: #854d0e; font-family: var(--font-cn); }

.btn-improve {
  padding: 6px 16px;
  background: var(--accent);
  color: #fff;
  border-radius: var(--radius-sm);
  font-size: var(--fs-sm);
  font-weight: 600;
  text-decoration: none;
  white-space: nowrap;
}

/* ─── 通用 ───────────────────────────────────────────────── */
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

/* ─── 五格描述扩展 ─── */
.desc-score { font-size: var(--fs-xs); font-weight: 700; margin-left: 6px; }
.desc-expand { font-size: var(--fs-xs); color: var(--text-2); line-height: 1.55; font-family: var(--font-cn); margin: 4px 0 0; }
</style>
