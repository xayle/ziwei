<script setup lang="ts">
/**
 * ChapterZeri.vue — ⑤ 择日·风水章节
 * 5-1: 吉日推荐（月历网格）  ZeriResponse.days[]
 * 5-2: 风水方位（SVG八方位罗盘）  FengshuiResponse
 */
import { computed, onMounted, ref } from 'vue'
import { useReportStore } from '@/stores/report'
import type { ZeriDayItem, DirectionItem } from '@/api/report'
import ParamControl from '@/components/report/ParamControl.vue'

const store = useReportStore()

onMounted(() => {
  if (!store.zeriData && !store.loadingMap['zeri'])      store.loadChapterData(5)
  if (!store.fengshuiData && !store.loadingMap['fengshui']) store.loadFengshuiData()
})

const zeri    = computed(() => store.zeriData)
const feng    = computed(() => store.fengshuiData)
const zLoading = computed(() => store.loadingMap['zeri'])
const fLoading = computed(() => store.loadingMap['fengshui'])
const zError  = computed(() => store.errorMap['zeri'])
const fError  = computed(() => store.errorMap['fengshui'])

// ─── 日历数据 ─────────────────────────────────────────────────
const monthStr = computed(() => store.chapterParams.zeri.month)
const monthYear = computed(() => {
  const [y, m] = monthStr.value.split('-').map(Number)
  return { year: y, month: m }
})

const dateMap = computed<Map<string, ZeriDayItem>>(() => {
  const m = new Map<string, ZeriDayItem>()
  zeri.value?.days?.forEach(item => m.set(item.date, item))
  return m
})

const calendarGrid = computed(() => {
  const { year, month } = monthYear.value
  const firstDay = new Date(year, month - 1, 1)
  const totalDays = new Date(year, month, 0).getDate()
  const startWd = firstDay.getDay() // 0=Sun

  type Cell = { day: number | null; item?: ZeriDayItem; key: string }
  const cells: Cell[] = []

  // 空格占位
  for (let i = 0; i < startWd; i++) cells.push({ day: null, key: `e${i}` })
  // 实际日期
  for (let d = 1; d <= totalDays; d++) {
    const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(d).padStart(2, '0')}`
    cells.push({ day: d, item: dateMap.value.get(dateStr), key: dateStr })
  }
  return cells
})

function scoreClass(item?: ZeriDayItem): string {
  if (!item) return ''
  return item.score >= 80 ? 'day-lucky' : item.score >= 60 ? 'day-ok' : 'day-plain'
}

const activeDate = ref<string | null>(null)
function toggleDate(key: string) {
  activeDate.value = activeDate.value === key ? null : key
}

// 月最佳日
const bestDate = computed(() => {
  if (!zeri.value?.days?.length) return null
  return [...zeri.value.days].sort((a, b) => b.score - a.score)[0]
})

const luckyCount = computed(() => zeri.value?.days?.filter(d => d.score >= 80).length ?? 0)

function onChip(term: string) { store.setGlossaryTerm(term) }

// ─── 风水方位 SVG ─────────────────────────────────────────────
const DIRECTIONS = ['北', '东北', '东', '东南', '南', '西南', '西', '西北']
const DIR_EN     = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']

/** 从 auspicious/inauspicious 数组中找出方位的吉凶状态 */
function dirStatus(dir: string): 'lucky' | 'unlucky' | 'neutral' {
  if (!feng.value) return 'neutral'
  if (feng.value.auspicious?.some((d: DirectionItem) => d.direction_zh === dir)) return 'lucky'
  if (feng.value.inauspicious?.some((d: DirectionItem) => d.direction_zh === dir)) return 'unlucky'
  return 'neutral'
}

/** 获取方位的详细信息 */
function dirDetail(dir: string): DirectionItem | undefined {
  if (!feng.value) return undefined
  return feng.value.auspicious?.find((d: DirectionItem) => d.direction_zh === dir)
    ?? feng.value.inauspicious?.find((d: DirectionItem) => d.direction_zh === dir)
}
const STATUS_FILL: Record<string, string> = {
  lucky:   '#dcfce7', unlucky: '#fee2e2', neutral: '#f8fafc',
}
const STATUS_STROKE: Record<string, string> = {
  lucky:   '#16a34a', unlucky: '#dc2626', neutral: '#cbd5e1',
}

// SVG 扇形路径（cx=100,cy=100,r=88）
function fanPath(index: number): string {
  const cx = 100, cy = 100, r = 88
  const startDeg = -90 + index * 45
  const endDeg   = startDeg + 45
  const toRad    = (d: number) => (d * Math.PI) / 180
  const x1 = cx + r * Math.cos(toRad(startDeg))
  const y1 = cy + r * Math.sin(toRad(startDeg))
  const x2 = cx + r * Math.cos(toRad(endDeg))
  const y2 = cy + r * Math.sin(toRad(endDeg))
  return `M${cx},${cy} L${x1.toFixed(2)},${y1.toFixed(2)} A${r},${r},0,0,1,${x2.toFixed(2)},${y2.toFixed(2)} Z`
}
// 方位标签坐标
function labelPos(index: number): { x: number; y: number } {
  const cx = 100, cy = 100, r = 64
  const midDeg = -90 + index * 45 + 22.5
  const rad = (midDeg * Math.PI) / 180
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) }
}
</script>

<template>
  <div class="chapter-zeri">

    <!-- 参数控制栏：择日 -->
    <ParamControl chapter-key="zeri" />

    <!-- ══ 5-1 吉日推荐 ════════════════════════════════════════════ -->
    <section id="section-5-1" class="section-block">
      <div class="section-title-row">
        <span class="section-num">5-1</span>
        <h2 class="section-title">吉日推荐</h2>
        <span class="month-badge">{{ monthStr }}</span>
      </div>

      <!-- 骨架屏 -->
      <div v-if="zLoading" class="skel-card" style="height: 260px;" />

      <!-- 错误 -->
      <div v-else-if="zError" class="error-block">
        <p class="error-txt">{{ zError }}</p>
        <button class="btn-sec" @click="store.loadChapterData(5, true)">重试</button>
      </div>

      <template v-else-if="zeri">
        <!-- 结论 -->
        <div class="conclusion-block">
          <p class="conclusion-text">
            {{ monthStr }} 月共推荐
            <strong>{{ zeri.days?.length ?? 0 }}</strong> 个
            <span class="chip-term" @click="onChip('吉日')">吉日</span>
            <template v-if="luckyCount">，其中
              <strong style="color:var(--success-dark)">{{ luckyCount }}</strong>
              个评分≥80（大吉）
            </template>
            <template v-if="bestDate">，最佳为
              <strong>{{ bestDate.date }}</strong>（{{ bestDate.score }}分）
            </template>。
          </p>
        </div>

        <!-- 日历网格 -->
        <div class="cal-wrap">
          <!-- 星期标题 -->
          <div class="cal-head">
            <span v-for="wd in ['日','一','二','三','四','五','六']" :key="wd">{{ wd }}</span>
          </div>

          <!-- 日期格 -->
          <div class="cal-grid">
            <div
              v-for="cell in calendarGrid"
              :key="cell.key"
              class="cal-cell"
              :class="[
                cell.day == null ? 'cal-empty' : '',
                cell.item ? scoreClass(cell.item) : '',
                cell.key === activeDate ? 'cal-active' : '',
              ]"
              @click="cell.item ? toggleDate(cell.key) : undefined"
            >
              <span class="cal-day">{{ cell.day ?? '' }}</span>
              <span v-if="cell.item?.score" class="cal-score">{{ cell.item.score }}</span>
            </div>
          </div>

          <!-- 图例 -->
          <div class="cal-legend">
            <span class="leg-item"><span class="leg-dot lucky" />≥80大吉</span>
            <span class="leg-item"><span class="leg-dot ok" />60-79小吉</span>
            <span class="leg-item"><span class="leg-dot plain" />其余</span>
          </div>
        </div>

        <!-- 展开详情 -->
        <transition name="slide-down">
          <div v-if="activeDate && dateMap.get(activeDate)" class="date-detail">
            <div class="detail-header">
              <strong class="detail-date">{{ activeDate }}</strong>
              <span
                class="detail-score"
                :style="{ color: (dateMap.get(activeDate)!.score >= 80) ? 'var(--success-dark)' : 'var(--accent)' }"
              >{{ dateMap.get(activeDate)!.score }} 分</span>
            </div>
            <div class="detail-tags">
              <span
                v-for="ev in dateMap.get(activeDate)!.evidence"
                :key="ev"
                class="detail-tag"
              >{{ ev }}</span>
            </div>
            <p class="detail-desc">
              <span class="detail-level" :class="dateMap.get(activeDate)!.level_css">{{ dateMap.get(activeDate)!.level }}</span>
              {{ dateMap.get(activeDate)!.lunar_info }} · {{ dateMap.get(activeDate)!.day_gz }}
            </p>
          </div>
        </transition>

      </template>

      <div v-else class="empty-hint">
        <p>需先加载紫微命盘后可进行择日分析</p>
        <button class="btn-primary" @click="store.loadChapterData(3)">加载紫微</button>
      </div>
    </section>

    <!-- ══ 5-2 风水方位 ════════════════════════════════════════════ -->
    <section id="section-5-2" class="section-block">
      <div class="section-title-row">
        <span class="section-num">5-2</span>
        <h2 class="section-title">风水方位</h2>
      </div>
      <!-- 风水参数控制栏 -->
      <ParamControl chapter-key="fengshui" />

      <div v-if="fLoading" class="skel-card" style="height: 220px;" />

      <div v-else-if="fError" class="error-block">
        <p class="error-txt">{{ fError }}</p>
        <button class="btn-sec" @click="store.loadFengshuiData(true)">重试</button>
      </div>

      <template v-else-if="feng">

        <!-- ── 命卦信息卡 ── -->
        <div class="gua-info-card">
          <div class="gua-badge">
            <span class="gua-num">{{ feng.life_gua }}</span>
            <span class="gua-label">命卦</span>
          </div>
          <div class="gua-meta">
            <div class="gua-row">
              <span class="gua-key">卦名</span>
              <span class="gua-val" @click="onChip(feng.gua_name + '卦')">{{ feng.gua_name }}</span>
            </div>
            <div class="gua-row">
              <span class="gua-key">五行</span>
              <span class="gua-val">{{ feng.gua_element }}</span>
            </div>
            <div class="gua-row">
              <span class="gua-key">命组</span>
              <span class="gua-val gua-group" :class="feng.group === '东四命' ? 'east' : 'west'">{{ feng.group }}</span>
            </div>
          </div>
        </div>

        <!-- 结论 -->
        <div class="conclusion-block">
          <p class="conclusion-text">
            本命吉方：
            <span
              v-for="d in feng.auspicious" :key="d.direction"
              class="dir-badge lucky-dir"
              @click="onChip(d.direction_zh + '方')"
            >{{ d.direction_zh }}·{{ d.label }}</span>
            ；凶方：
            <span
              v-for="d in feng.inauspicious" :key="d.direction"
              class="dir-badge unlucky-dir"
            >{{ d.direction_zh }}·{{ d.label }}</span>。
          </p>
        </div>

        <div class="fengshui-layout">
          <!-- SVG 罗盘 -->
          <div class="compass-wrap">
            <svg viewBox="0 0 200 200" class="compass-svg">
              <!-- 扇形 -->
              <path
                v-for="(dir, i) in DIRECTIONS"
                :key="dir"
                :d="fanPath(i)"
                :fill="STATUS_FILL[dirStatus(dir)]"
                :stroke="STATUS_STROKE[dirStatus(dir)]"
                stroke-width="1.5"
              />
              <!-- 内圆 -->
              <circle cx="100" cy="100" r="28" fill="var(--surface)" stroke="var(--border)" stroke-width="1.5" />
              <text x="100" y="97" text-anchor="middle" font-size="10" fill="var(--text-3)" font-family="serif">{{ feng.gua_name }}</text>
              <text x="100" y="109" text-anchor="middle" font-size="10" fill="var(--text-3)" font-family="serif">{{ feng.group }}</text>
              <!-- 方位标签 -->
              <text
                v-for="(dir, i) in DIRECTIONS"
                :key="dir + 'lbl'"
                :x="labelPos(i).x"
                :y="labelPos(i).y + 4"
                text-anchor="middle"
                font-size="11"
                :fill="dirStatus(dir) === 'lucky' ? '#15803d' : dirStatus(dir) === 'unlucky' ? '#b91c1c' : 'var(--text-3)'"
                font-family="serif"
                font-weight="700"
              >{{ dir }}</text>
            </svg>
            <!-- 图例 -->
            <div class="compass-legend">
              <span class="leg-item"><span class="leg-dot lucky" />吉方</span>
              <span class="leg-item"><span class="leg-dot unlucky" />凶方</span>
              <span class="leg-item"><span class="leg-dot plain" />中性</span>
            </div>
          </div>

          <!-- 方位对照表（增强版：显示 label, level, desc） -->
          <div class="dir-table">
            <div class="dir-table-head">
              <span>方位</span><span>标签</span><span>级别</span><span>说明</span>
            </div>
            <div
              v-for="(dir, i) in DIRECTIONS"
              :key="dir + 'row'"
              class="dir-row"
              :class="dirStatus(dir)"
            >
              <span class="dir-cn">{{ dir }}<small class="dir-en">{{ DIR_EN[i] }}</small></span>
              <span class="dir-label" :class="dirDetail(dir)?.level_css">{{ dirDetail(dir)?.label ?? '—' }}</span>
              <span class="dir-status-badge" :class="dirStatus(dir)">
                {{ dirDetail(dir)?.level ?? (dirStatus(dir) === 'lucky' ? '吉' : dirStatus(dir) === 'unlucky' ? '凶' : '平') }}
              </span>
              <span class="dir-desc">{{ dirDetail(dir)?.desc ?? '普通方位' }}</span>
            </div>
          </div>
        </div>

        <!-- ── 家具方位建议 ── -->
        <div v-if="feng.bed_tip || feng.desk_tip || feng.door_tip" class="furniture-tips">
          <h3 class="tips-title">📐 家具方位建议</h3>
          <div class="tips-grid">
            <div v-if="feng.bed_tip" class="tip-card">
              <span class="tip-icon">🛏️</span>
              <div class="tip-body">
                <strong class="tip-item">{{ feng.bed_tip.item }}</strong>
                <span class="tip-dir">{{ feng.bed_tip.direction_zh }}（{{ feng.bed_tip.label }}）</span>
                <p class="tip-reason">{{ feng.bed_tip.reason }}</p>
              </div>
            </div>
            <div v-if="feng.desk_tip" class="tip-card">
              <span class="tip-icon">🖥️</span>
              <div class="tip-body">
                <strong class="tip-item">{{ feng.desk_tip.item }}</strong>
                <span class="tip-dir">{{ feng.desk_tip.direction_zh }}（{{ feng.desk_tip.label }}）</span>
                <p class="tip-reason">{{ feng.desk_tip.reason }}</p>
              </div>
            </div>
            <div v-if="feng.door_tip" class="tip-card">
              <span class="tip-icon">🚪</span>
              <div class="tip-body">
                <strong class="tip-item">{{ feng.door_tip.item }}</strong>
                <span class="tip-dir">{{ feng.door_tip.direction_zh }}（{{ feng.door_tip.label }}）</span>
                <p class="tip-reason">{{ feng.door_tip.reason }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- ── 人宅相合 ── -->
        <div v-if="feng.compatibility" class="compat-block">
          <h3 class="tips-title">🏠 人宅相合</h3>
          <div class="compat-card" :class="feng.compatibility === '相合' ? 'compat-good' : 'compat-bad'">
            <span class="compat-icon">{{ feng.compatibility === '相合' ? '✅' : '⚠️' }}</span>
            <div class="compat-body">
              <strong class="compat-result">
                {{ feng.house_gua_name ?? '' }}
                <template v-if="feng.house_group">（{{ feng.house_group }}）</template>
                → {{ feng.compatibility }}
              </strong>
              <p v-if="feng.compatibility_note" class="compat-note">{{ feng.compatibility_note }}</p>
            </div>
          </div>
        </div>

        <!-- ── 免责声明 ── -->
        <p v-if="feng.disclaimer" class="feng-disclaimer">⚠ {{ feng.disclaimer }}</p>

      </template>

      <div v-else class="empty-hint">
        <p>点击加载风水方位数据</p>
        <button class="btn-primary" @click="store.loadFengshuiData()">加载风水</button>
      </div>
    </section>

  </div>
</template>

<style scoped>
.chapter-zeri { display: flex; flex-direction: column; gap: var(--sp-6); }

/* ─── 章节块 */
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
  font-size: var(--fs-xs); color: var(--text-3); font-family: var(--font-mono);
  background: var(--bg); padding: 2px 8px; border-radius: 99px; border: 1px solid var(--border);
}
.section-title { font-size: var(--fs-xl); font-weight: 700; color: var(--text); font-family: var(--font-cn); }
.month-badge { font-size: var(--fs-xs); color: var(--text-3); font-family: var(--font-mono); margin-left: auto; }

.conclusion-block {
  padding: var(--sp-3) var(--sp-4); background: var(--surface-2);
  border-radius: var(--radius-sm); border-left: 3px solid var(--accent);
  margin-bottom: var(--sp-4);
}
.conclusion-text { font-size: var(--fs-sm); color: var(--text); line-height: 1.8; font-family: var(--font-cn); }
.chip-term { border-bottom: 1px dashed var(--accent); cursor: pointer; color: var(--accent-dark); font-weight: 600; }

/* ─── 日历 */
.cal-wrap { display: flex; flex-direction: column; gap: var(--sp-2); }

.cal-head {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  text-align: center;
  font-size: 11px;
  color: var(--text-3);
  padding: 0 2px;
}

.cal-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
}

.cal-cell {
  aspect-ratio: 1;
  border-radius: var(--radius-sm);
  background: var(--surface-2);
  border: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: default;
  min-height: 44px;
  transition: border-color .15s;
}

.cal-empty { background: transparent; border-color: transparent; }

.cal-cell.day-lucky {
  background: #dcfce7; border-color: #86efac; cursor: pointer;
}
.cal-cell.day-lucky:hover { border-color: #16a34a; }

.cal-cell.day-ok {
  background: #fef9c3; border-color: #fde047; cursor: pointer;
}
.cal-cell.day-ok:hover { border-color: #ca8a04; }

.cal-cell.day-plain { cursor: pointer; }
.cal-cell.day-plain:hover { border-color: var(--border-md); }

.cal-cell.cal-active { outline: 2px solid var(--accent); outline-offset: 1px; }

.cal-day { font-size: 14px; font-weight: 600; font-family: var(--font-mono); color: var(--text); }
.cal-score { font-size: 9px; color: var(--text-3); font-family: var(--font-mono); }

.cal-legend {
  display: flex; gap: var(--sp-4); margin-top: var(--sp-1);
  font-size: 11px; color: var(--text-3);
}
.leg-item { display: flex; align-items: center; gap: 4px; }
.leg-dot { width: 10px; height: 10px; border-radius: 2px; }
.leg-dot.lucky  { background: #dcfce7; border: 1px solid #86efac; }
.leg-dot.ok     { background: #fef9c3; border: 1px solid #fde047; }
.leg-dot.plain  { background: var(--surface-2); border: 1px solid var(--border); }
.leg-dot.unlucky { background: #fee2e2; border: 1px solid #fca5a5; }

/* ─── 日期详情 */
.date-detail {
  margin-top: var(--sp-3); padding: var(--sp-4);
  background: var(--surface-2); border-radius: var(--radius-sm);
  border-left: 3px solid var(--accent);
}
.detail-header { display: flex; align-items: center; gap: var(--sp-3); margin-bottom: var(--sp-2); }
.detail-date { font-size: var(--fs-md); font-family: var(--font-mono); }
.detail-score { font-size: var(--fs-xl); font-weight: 900; font-family: var(--font-mono); }
.detail-tags { display: flex; flex-wrap: wrap; gap: var(--sp-1); margin-bottom: var(--sp-2); }
.detail-tag {
  font-size: 11px; padding: 2px 8px;
  background: var(--accent-lt); border-radius: 99px;
  color: var(--accent-dark); cursor: pointer;
  border: 1px solid rgba(217,119,6,.2);
}
.detail-desc { font-size: var(--fs-sm); color: var(--text); line-height: 1.7; font-family: var(--font-cn); }
.detail-level { font-weight: 700; margin-right: 4px; }
.detail-level.daji { color: #15803d; }
.detail-level.ji { color: #65a30d; }
.detail-level.zhong { color: var(--text-2); }
.detail-level.xiong { color: #dc2626; }

/* ─── 风水罗盘 */
.fengshui-layout { display: flex; gap: var(--sp-6); align-items: flex-start; }

.compass-wrap { flex-shrink: 0; display: flex; flex-direction: column; align-items: center; gap: var(--sp-3); }
.compass-svg { width: 200px; height: 200px; }
.compass-legend { display: flex; gap: var(--sp-3); font-size: 11px; color: var(--text-3); }

.dir-badge {
  display: inline-block; font-size: 11px; padding: 1px 8px;
  border-radius: 99px; margin: 0 2px; font-weight: 600;
}
.lucky-dir   { background: #dcfce7; color: #15803d; }
.unlucky-dir { background: #fee2e2; color: #b91c1c; }

/* 对照表 */
.dir-table { flex: 1; }
.dir-table-head {
  display: grid; grid-template-columns: 56px 60px 48px 1fr;
  gap: var(--sp-2); padding: 4px var(--sp-2);
  font-size: 11px; color: var(--text-3); border-bottom: 1px solid var(--border);
}
.dir-row {
  display: grid; grid-template-columns: 56px 60px 48px 1fr;
  gap: var(--sp-2); align-items: center;
  padding: var(--sp-2); border-bottom: 1px solid var(--border);
  font-size: var(--fs-xs);
}
.dir-row:last-child { border-bottom: none; }
.dir-cn { font-family: var(--font-cn); font-weight: 700; color: var(--text); }
.dir-cn .dir-en { font-family: var(--font-mono); color: var(--text-3); font-weight: 400; margin-left: 2px; font-size: 10px; }
.dir-label { font-weight: 600; font-family: var(--font-cn); }
.dir-label.ji1 { color: #15803d; }
.dir-label.ji2 { color: #22c55e; }
.dir-label.ji3 { color: #65a30d; }
.dir-label.ji4 { color: #78716c; }
.dir-label.xiong1 { color: #dc2626; }
.dir-label.xiong2 { color: #ea580c; }
.dir-label.xiong3 { color: #d97706; }
.dir-label.xiong4 { color: #92400e; }
.dir-status-badge {
  font-size: 11px; font-weight: 700;
  padding: 1px 6px;
  border-radius: var(--radius-sm);
  text-align: center;
}
.dir-status-badge.lucky   { background: #dcfce7; color: #15803d; }
.dir-status-badge.unlucky { background: #fee2e2; color: #b91c1c; }
.dir-status-badge.neutral { background: var(--surface-2); color: var(--text-3); }
.dir-desc { color: var(--text-2); line-height: 1.5; font-family: var(--font-cn); }

/* ─── 命卦信息卡 */
.gua-info-card {
  display: flex; gap: var(--sp-4); align-items: center;
  padding: var(--sp-4); margin-bottom: var(--sp-4);
  background: var(--surface-2); border-radius: var(--radius-sm);
  border: 1px solid var(--border);
}
.gua-badge {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; width: 56px; height: 56px;
  border-radius: var(--radius-sm); background: var(--accent-lt);
  border: 2px solid var(--accent);
}
.gua-num { font-size: 22px; font-weight: 900; font-family: var(--font-mono); color: var(--accent-dark); line-height: 1; }
.gua-label { font-size: 10px; color: var(--accent); font-weight: 600; }
.gua-meta { display: flex; flex-wrap: wrap; gap: var(--sp-3) var(--sp-6); flex: 1; }
.gua-row { display: flex; gap: var(--sp-2); align-items: center; }
.gua-key { font-size: 11px; color: var(--text-3); }
.gua-val { font-size: var(--fs-sm); font-weight: 600; color: var(--text); cursor: pointer; }
.gua-group.east { color: #15803d; }
.gua-group.west { color: #b45309; }

/* ─── 家具方位建议 */
.furniture-tips { margin-top: var(--sp-5); }
.tips-title { font-size: var(--fs-md); font-weight: 700; margin-bottom: var(--sp-3); color: var(--text); font-family: var(--font-cn); }
.tips-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: var(--sp-3); }
.tip-card {
  display: flex; gap: var(--sp-3); padding: var(--sp-3);
  background: var(--surface-2); border-radius: var(--radius-sm);
  border: 1px solid var(--border);
}
.tip-icon { font-size: 24px; flex-shrink: 0; }
.tip-body { flex: 1; display: flex; flex-direction: column; gap: 2px; }
.tip-item { font-size: var(--fs-sm); color: var(--text); font-family: var(--font-cn); }
.tip-dir { font-size: 11px; color: var(--accent-dark); font-weight: 600; }
.tip-reason { font-size: 11px; color: var(--text-2); line-height: 1.5; margin: 0; }

/* ─── 人宅相合 */
.compat-block { margin-top: var(--sp-5); }
.compat-card {
  display: flex; gap: var(--sp-3); align-items: flex-start;
  padding: var(--sp-4); border-radius: var(--radius-sm);
  border: 1px solid var(--border);
}
.compat-good { background: #f0fdf4; border-color: #86efac; }
.compat-bad  { background: #fef2f2; border-color: #fca5a5; }
.compat-icon { font-size: 20px; flex-shrink: 0; }
.compat-body { flex: 1; }
.compat-result { font-size: var(--fs-sm); color: var(--text); font-family: var(--font-cn); }
.compat-note { font-size: 12px; color: var(--text-2); margin: 4px 0 0; line-height: 1.6; font-family: var(--font-cn); }

/* ─── 免责声明 */
.feng-disclaimer {
  margin-top: var(--sp-4); padding: var(--sp-3);
  background: var(--surface-2); border-radius: var(--radius-sm);
  font-size: 11px; color: var(--text-3); line-height: 1.6; text-align: center;
}

/* ─── 通用 */
.skel-card {
  border-radius: var(--radius-sm);
  background: linear-gradient(90deg, #e2e8f0 25%, #f1f5f9 50%, #e2e8f0 75%);
  background-size: 400px; animation: shimmer 1.2s infinite;
}
.error-block { display: flex; align-items: center; gap: var(--sp-3); padding: var(--sp-3); background: #fee2e2; border-radius: var(--radius-sm); }
.error-txt { color: var(--danger-dark); font-size: var(--fs-sm); flex: 1; }
.empty-hint { display: flex; flex-direction: column; align-items: center; gap: var(--sp-3); padding: var(--sp-6) 0; color: var(--text-3); }
.btn-primary { padding: 8px 20px; background: var(--accent); color: #fff; border: none; border-radius: var(--radius-sm); font-size: var(--fs-sm); font-weight: 600; cursor: pointer; }
.btn-sec { padding: 5px 14px; background: transparent; border: 1px solid var(--border-md); border-radius: var(--radius-sm); font-size: var(--fs-sm); cursor: pointer; color: var(--text-2); }

/* 展开动画 */
.slide-down-enter-active, .slide-down-leave-active { transition: all 0.18s ease; overflow: hidden; }
.slide-down-enter-from, .slide-down-leave-to { opacity: 0; max-height: 0; }
.slide-down-enter-to, .slide-down-leave-from { opacity: 1; max-height: 300px; }
</style>
