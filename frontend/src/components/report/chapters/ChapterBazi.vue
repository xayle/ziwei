<script setup lang="ts">
/**
 * ChapterBazi.vue — ② 八字四柱章节
 * 数据来源: BaziFullResponse（POST /api/v1/bazi/full）
 */
import { computed, onMounted, ref } from 'vue'
import { useReportStore } from '@/stores/report'
import ParamControl from '@/components/report/ParamControl.vue'
import {
  CANG_GAN, NAYIN_MAP, STEM_ELEMENT, WX_VAR, stemColor,
} from '@/data/ganzhi'

const store = useReportStore()

onMounted(() => {
  if (!store.baziData && !store.loadingMap['bazi']) {
    store.loadChapterData(2)
  }
})

const bazi = computed(() => store.baziData)
const pillars = computed(() => bazi.value?.pillars_primary)
const loading = computed(() => store.loadingMap['bazi'])
const error   = computed(() => store.errorMap['bazi'])

// 五行颜色
function wxColor(element: string) {
  return `var(${WX_VAR[element] ?? '--text'})`
}

// 藏干
function cangGan(branch: string) {
  return (CANG_GAN[branch] ?? []).join('')
}

// 纳音
function nayin(stem: string, branch: string): string {
  return NAYIN_MAP[stem + branch] ?? ''
}

// 十神（按柱位）
const tenGods = computed(() => bazi.value?.ten_gods ?? { year:'', month:'', day:'', hour:'' })

// 十神环形布局
const TEN_GODS_ALL = ['比肩','劫财','食神','伤官','偏财','正财','七杀','正官','偏印','正印']
const TEN_GOD_COLORS: Record<string, string> = {
  '比肩': '#3b82f6', '劫财': '#6366f1', '食神': '#10b981', '伤官': '#f59e0b',
  '偏财': '#f97316', '正财': '#ef4444', '七杀': '#dc2626', '正官': '#7c3aed',
  '偏印': '#0891b2', '正印': '#065f46',
}
const presentTenGods = computed(() => {
  const tg = tenGods.value as Record<string, string>
  const s = new Set<string>()
  for (const key of ['year', 'month', 'hour'] as const) {
    if (tg[key]) s.add(tg[key])
  }
  return s
})

// 五行评分横条（最大值归一化）
const wuxingBars = computed(() => {
  const s = bazi.value?.wuxing_score
  if (!s) return []
  const entries: [string, number][] = [
    ['木', s.wood], ['火', s.fire], ['土', s.earth], ['金', s.metal], ['水', s.water],
  ]
  const max = Math.max(...entries.map(e => e[1]), 1)
  return entries.map(([el, val]) => ({
    el, val, pct: Math.round((val / max) * 100), color: wxColor(STEM_ELEMENT[el] ?? el),
  }))
})

// ── 五行雷达图（SVG 五边形）──────────────────────────────────
// 顶点顺序（顺时针，从顶部12点开始）：木→火→土→金→水
const RADAR_ANGLES = [270, 342, 54, 126, 198].map(deg => (deg * Math.PI) / 180)
const RADAR_CX = 100, RADAR_CY = 100, RADAR_R = 72
const RADAR_ELEMENTS = ['木', '火', '土', '金', '水']

const radarBg = RADAR_ANGLES.map(a =>
  `${(RADAR_CX + RADAR_R * Math.cos(a)).toFixed(1)},${(RADAR_CY + RADAR_R * Math.sin(a)).toFixed(1)}`
).join(' ')
const radarBgHalf = RADAR_ANGLES.map(a =>
  `${(RADAR_CX + (RADAR_R * 0.5) * Math.cos(a)).toFixed(1)},${(RADAR_CY + (RADAR_R * 0.5) * Math.sin(a)).toFixed(1)}`
).join(' ')

const radarPoints = computed(() => {
  const s = bazi.value?.wuxing_score
  if (!s) return radarBg
  const vals = [s.wood, s.fire, s.earth, s.metal, s.water]
  const maxVal = Math.max(...vals, 1)
  return RADAR_ANGLES.map((angle, i) => {
    const r = RADAR_R * (vals[i] / maxVal)
    return `${(RADAR_CX + r * Math.cos(angle)).toFixed(1)},${(RADAR_CY + r * Math.sin(angle)).toFixed(1)}`
  }).join(' ')
})

const radarLabels = computed(() => {
  const s = bazi.value?.wuxing_score
  const vals = s ? [s.wood, s.fire, s.earth, s.metal, s.water] : [0, 0, 0, 0, 0]
  return RADAR_ANGLES.map((angle, i) => {
    const lr = RADAR_R + 18
    return {
      el: RADAR_ELEMENTS[i],
      val: vals[i],
      color: wxColor(RADAR_ELEMENTS[i]),
      x: +(RADAR_CX + lr * Math.cos(angle)).toFixed(1),
      y: +(RADAR_CY + lr * Math.sin(angle)).toFixed(1),
    }
  })
})

// 用神颜色
function favorColor(el: string): string {
  const elem = STEM_ELEMENT[el] ?? el
  return wxColor(elem)
}

// dayun 时间线（当前大运高亮）
const currentYear = new Date().getFullYear()
const dayunItems = computed(() => {
  if (!bazi.value?.dayun?.items) return []
  return bazi.value.dayun.items.map((item, i) => {
    const nextStart = bazi.value!.dayun.items[i + 1]?.start_year ?? 9999
    const isCurrent = item.start_year <= currentYear && currentYear < nextStart
    return { ...item, ganzhi: item.stem + item.branch, endYear: nextStart - 1, isCurrent }
  })
})

// 流年列表（取 liunian_detail 优先）
const liunianItems = computed(() => {
  const detail = bazi.value?.liunian_detail
  if (detail?.length) return detail.map(d => ({
    year: d.year,
    ganzhi: d.ganzhi,
    score: d.annual_score,
    summary: d.interpretation_text,
    isCurrent: d.year === currentYear,
    domains: d.domain_forecasts ?? {} as Record<string, string>,
  }))
  const basic = bazi.value?.liunian?.items ?? []
  return basic.map(b => ({
    year: b.year,
    ganzhi: b.stem + b.branch,
    score: null,
    summary: null,
    isCurrent: b.year === currentYear,
    domains: {} as Record<string, string>,
  }))
})

// 流年抽屉
const expandedLiunianYear = ref<number | null>(null)
function toggleLiunian(year: number) {
  expandedLiunianYear.value = expandedLiunianYear.value === year ? null : year
}

// 神煞（仅显示 priority A）
const topShensha = computed(() => {
  if (!bazi.value?.shensha) return []
  return bazi.value.shensha
    .filter(s => s.priority === 'A')
    .slice(0, 8)
})

// 干支关系
const dizhiRelations = computed(() => bazi.value?.dizhi_relations ?? [])
const tiangangClashes = computed(() => bazi.value?.tiangan_clashes ?? [])

// 分数色值
function scoreColor(score: number | null): string {
  if (score == null) return 'var(--text-3)'
  if (score >= 80) return 'var(--success-dark)'
  if (score >= 60) return 'var(--accent)'
  return 'var(--danger-dark)'
}

// chip 点击触发词条卡
function onChip(term: string) {
  store.setGlossaryTerm(term)
}
</script>

<template>
  <div class="chapter-bazi">

    <!-- 参数控制栏 -->
    <ParamControl chapter-key="bazi" />

    <!-- 加载中骨架屏 -->
    <div v-if="loading" class="loading-wrap">
      <div class="skel-card" style="height: 220px;" />
      <div class="skel-card" style="height: 120px;" />
      <div class="skel-card" style="height: 100px;" />
      <div class="skel-card" style="height: 180px;" />
    </div>

    <!-- 错误态 -->
    <div v-else-if="error" class="error-card">
      <p class="error-msg">{{ error }}</p>
      <button class="btn-sec" @click="store.loadChapterData(2, true)">重新计算</button>
    </div>

    <!-- 数据渲染 -->
    <template v-else-if="bazi">

      <!-- ══ 2-1 四柱总览 ══════════════════════════════════════ -->
      <section id="section-2-1" class="section-block">
        <div class="section-title-row">
          <span class="section-num">2-1</span>
          <h2 class="section-title">四柱总览</h2>
        </div>

        <!-- 结论段落 -->
        <div class="conclusion-block">
          <p class="conclusion-text" v-if="bazi.bazi_summary">
            {{ bazi.bazi_summary }}
          </p>
          <p class="conclusion-text" v-else-if="pillars">
            日主
            <span
              class="chip-term"
              @click="onChip('日主')"
            >{{ pillars.day.stem }}</span>，
            <span
              class="chip-term"
              @click="onChip(bazi.day_master_strength?.tier ?? '')"
            >{{ bazi.day_master_strength?.tier }}</span>。
            <span v-if="bazi.geju">
              格局取
              <span class="chip-term" @click="onChip('格局')">{{ bazi.geju.geju_name }}</span>，
            </span>
            <span v-if="bazi.yongshen?.favor?.length">
              用神
              <span
                v-for="f in bazi.yongshen.favor"
                :key="f"
                class="wx-chip"
                :style="{ color: favorColor(f) }"
                @click="onChip(f)"
              >{{ f }}</span>，
            </span>
            <span v-if="bazi.yongshen?.avoid?.length">
              忌
              <span
                v-for="a in bazi.yongshen.avoid"
                :key="a"
                class="wx-chip wx-avoid"
                @click="onChip(a)"
              >{{ a }}</span>。
            </span>
          </p>
        </div>

        <!-- 四柱主表 -->
        <div class="pillars-table-wrap" v-if="pillars">
          <table class="pillars-table">
            <thead>
              <tr class="pillars-head">
                <th class="pillar-label-col"></th>
                <th>年柱</th>
                <th>月柱</th>
                <th class="day-col">日柱</th>
                <th>时柱</th>
              </tr>
            </thead>
            <tbody>
              <!-- 天干行 -->
              <tr class="stem-row">
                <td class="row-label">天干</td>
                <td v-for="key in ['year','month','day','hour']" :key="'stem-'+key"
                    :class="{ 'day-col': key === 'day' }">
                  <span
                    class="gz-char"
                    :style="{ color: stemColor((pillars as Record<string,{stem:string,branch:string}>)[key].stem) }"
                  >
                    {{ (pillars as Record<string,{stem:string,branch:string}>)[key].stem }}
                  </span>
                </td>
              </tr>
              <!-- 地支行 -->
              <tr class="branch-row">
                <td class="row-label">地支</td>
                <td v-for="key in ['year','month','day','hour']" :key="'branch-'+key"
                    :class="{ 'day-col': key === 'day' }">
                  <span class="gz-char">
                    {{ (pillars as Record<string,{stem:string,branch:string}>)[key].branch }}
                  </span>
                </td>
              </tr>
              <!-- 藏干行 -->
              <tr class="cang-row">
                <td class="row-label">藏干</td>
                <td v-for="key in ['year','month','day','hour']" :key="'cang-'+key"
                    :class="{ 'day-col': key === 'day' }">
                  <span class="cang-text">
                    {{ cangGan((pillars as Record<string,{stem:string,branch:string}>)[key].branch) }}
                  </span>
                </td>
              </tr>
              <!-- 纳音行 -->
              <tr class="nayin-row">
                <td class="row-label">纳音</td>
                <td v-for="key in ['year','month','day','hour']" :key="'ny-'+key"
                    :class="{ 'day-col': key === 'day' }">
                  <span class="nayin-text">
                    {{ nayin((pillars as Record<string,{stem:string,branch:string}>)[key].stem, (pillars as Record<string,{stem:string,branch:string}>)[key].branch) }}
                  </span>
                </td>
              </tr>
              <!-- 十神行 -->
              <tr class="shishen-row">
                <td class="row-label">十神</td>
                <td v-for="key in ['year','month','day','hour']" :key="'ss-'+key"
                    :class="{ 'day-col': key === 'day' }">
                  <span
                    class="ss-chip"
                    :class="{ 'ss-day': key === 'day' }"
                    @click="onChip((tenGods as Record<string,string>)[key])"
                  >
                    {{ key === 'day' ? '日主' : (tenGods as Record<string,string>)[key] }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- ══ 2-2 日主与十神 ══════════════════════════════════ -->
      <section id="section-2-2" class="section-block">
        <div class="section-title-row">
          <span class="section-num">2-2</span>
          <h2 class="section-title">日主与十神</h2>
        </div>
        <div class="conclusion-block" v-if="bazi.day_master_strength">
          <p class="conclusion-text">
            日主
            <span class="chip-term" @click="onChip('日主')">{{ pillars?.day.stem }}</span>
            属<strong>{{ STEM_ELEMENT[pillars?.day.stem ?? ''] }}</strong>，
            综合评分 <strong>{{ bazi.day_master_strength.score }}</strong> 分，
            判定为
            <span class="chip-term" @click="onChip(bazi.day_master_strength.tier)">
              {{ bazi.day_master_strength.tier }}
            </span>。
            <span v-if="bazi.day_master_strength.factors?.[0]">
              {{ bazi.day_master_strength.factors[0].reason }}
            </span>
          </p>
        </div>

        <!-- 十神速览 -->
        <div class="ten-gods-grid" v-if="pillars">
          <div v-for="key in ['year','month','day','hour']" :key="key" class="tg-cell">
            <span class="tg-pillar-name">{{ {year:'年',month:'月',day:'日',hour:'时'}[key as keyof {year:string,month:string,day:string,hour:string}] }}柱</span>
            <span
              class="gz-char tg-stem"
              :style="{ color: stemColor((pillars as Record<string,{stem:string,branch:string}>)[key].stem) }"
            >{{ (pillars as Record<string,{stem:string,branch:string}>)[key].stem }}</span>
            <span
              class="ss-chip"
              :class="{ 'ss-day': key === 'day' }"
              @click="onChip((tenGods as Record<string,string>)[key])"
            >{{ key === 'day' ? '日主' : (tenGods as Record<string,string>)[key] }}</span>
          </div>
        </div>

        <!-- 十神环形布局 -->
        <div v-if="pillars" class="tg-ring-wrap">
          <div class="tg-ring">
            <!-- 中心：日主天干 -->
            <div class="tg-ring-center">
              <span class="tg-ring-char" :style="{ color: stemColor(pillars.day.stem) }">{{ pillars.day.stem }}</span>
              <span class="tg-ring-sub">{{ STEM_ELEMENT[pillars.day.stem] ?? '' }}·日主</span>
            </div>
            <!-- 10个十神槽，用 CSS custom property 定位 -->
            <div
              v-for="(god, i) in TEN_GODS_ALL" :key="god"
              class="tg-slot"
              :class="{ 'tg-slot--active': presentTenGods.has(god) }"
              :style="{ '--i': i, '--color': TEN_GOD_COLORS[god] }"
              @click="presentTenGods.has(god) ? onChip(god) : undefined"
            >{{ god }}</div>
          </div>
          <!-- 强弱进度条 -->
          <div v-if="bazi.day_master_strength?.score != null" class="tg-strength-bar-wrap">
            <span class="tg-strength-label">{{ bazi.day_master_strength.tier }}</span>
            <div class="tg-strength-track">
              <div class="tg-strength-fill"
                :style="{ width: `${bazi.day_master_strength.score}%` }" />
            </div>
            <span class="tg-strength-val">{{ bazi.day_master_strength.score }}</span>
          </div>
        </div>

        <!-- 日主强弱依据 -->
        <div v-if="bazi.day_master_strength?.factors?.length" class="factors-list">
          <div v-for="f in bazi.day_master_strength.factors" :key="f.name" class="factor-row">
            <span class="factor-name">{{ f.name }}</span>
            <div class="factor-bar-wrap">
              <div class="factor-bar" :style="{ width: `${Math.abs(f.score * 10)}%`, background: f.score > 0 ? 'var(--wx-fire)' : 'var(--wx-water)' }" />
            </div>
            <span class="factor-reason">{{ f.reason }}</span>
          </div>
        </div>
      </section>

      <!-- ══ 2-3 五行分析 ═══════════════════════════════════ -->
      <section id="section-2-3" class="section-block">
        <div class="section-title-row">
          <span class="section-num">2-3</span>
          <h2 class="section-title">五行分析</h2>
        </div>

        <div class="conclusion-block" v-if="bazi.balance_advice || bazi.wuxing_weak?.length">
          <p class="conclusion-text">
            <span v-if="bazi.wuxing_weak?.length">
              偏缺<span v-for="el in bazi.wuxing_weak" :key="el">
                <span class="wx-chip" :style="{ color: wxColor(el) }">{{ el }}</span>
              </span>，
            </span>
            <span v-if="bazi.wuxing_strong?.length">
              偏旺<span v-for="el in bazi.wuxing_strong" :key="el">
                <span class="wx-chip" :style="{ color: wxColor(el) }">{{ el }}</span>
              </span>。
            </span>
            <span v-if="bazi.balance_advice"> {{ bazi.balance_advice }}</span>
          </p>
        </div>

        <!-- 五行横条图 -->
        <div class="wx-bars">
          <div v-for="item in wuxingBars" :key="item.el" class="wx-row">
            <span class="wx-label" :style="{ color: item.color }">{{ item.el }}</span>
            <div class="wx-bar-track">
              <div class="wx-bar-fill" :style="{ width: item.pct + '%', background: item.color }" />
            </div>
            <span class="wx-val">{{ item.val.toFixed(1) }}</span>
          </div>
        </div>

        <!-- 五行旺衰雷达图（SVG 五边形） -->
        <div v-if="bazi.wuxing_score" class="wx-radar-wrap">
          <svg viewBox="0 0 200 200" class="wx-radar-svg">
            <!-- 背景网格 -->
            <polygon :points="radarBgHalf" fill="none" stroke="var(--border)" stroke-width="0.8" stroke-dasharray="3,2"/>
            <polygon :points="radarBg"     fill="none" stroke="var(--border)" stroke-width="1"/>
            <!-- 轴线 -->
            <line v-for="(angle, i) in RADAR_ANGLES" :key="`axis-${i}`"
              :x1="RADAR_CX" :y1="RADAR_CY"
              :x2="+(RADAR_CX + RADAR_R * Math.cos(angle)).toFixed(1)"
              :y2="+(RADAR_CY + RADAR_R * Math.sin(angle)).toFixed(1)"
              stroke="var(--border)" stroke-width="0.6"
            />
            <!-- 数据区域 -->
            <polygon :points="radarPoints" fill="var(--accent-soft)" fill-opacity="0.6" stroke="var(--accent)" stroke-width="2"/>
            <!-- 数据顶点圆点 -->
            <circle v-for="(pt, i) in radarPoints.split(' ')" :key="`dot-${i}`"
              :cx="+pt.split(',')[0]" :cy="+pt.split(',')[1]" r="3"
              fill="var(--accent)" />
            <!-- 标签 -->
            <text v-for="lb in radarLabels" :key="lb.el"
              :x="lb.x" :y="lb.y"
              text-anchor="middle" dominant-baseline="middle"
              class="radar-label" :fill="lb.color"
            >{{ lb.el }}</text>
          </svg>
        </div>
      </section>

      <!-- ══ 2-4 干支关系 ═══════════════════════════════════ -->
      <section id="section-2-4" class="section-block">
        <div class="section-title-row">
          <span class="section-num">2-4</span>
          <h2 class="section-title">干支关系</h2>
        </div>

        <div class="ganzhi-relations">
          <div v-if="dizhiRelations.length">
            <h4 class="rel-subtitle">地支关系</h4>
            <div class="rel-tags">
              <span
                v-for="(rel, i) in dizhiRelations"
                :key="i"
                class="rel-tag"
                :title="(rel as {description?:string}).description"
              >
                {{ (rel as {type:string; branches:string[]}).type }}：
                {{ (rel as {branches:string[]}).branches.join(' ') }}
              </span>
            </div>
          </div>
          <div v-if="tiangangClashes.length" class="mt-3">
            <h4 class="rel-subtitle">天干克冲</h4>
            <div class="rel-tags">
              <span
                v-for="(rel, i) in tiangangClashes"
                :key="i"
                class="rel-tag rel-tag--clash"
                :title="(rel as {description?:string}).description"
              >
                {{ (rel as {type:string; stems:string[]}).type }}：
                {{ (rel as {stems:string[]}).stems.join(' ') }}
              </span>
            </div>
          </div>
          <p v-if="!dizhiRelations.length && !tiangangClashes.length" class="card-empty">
            命局干支无特殊冲合关系
          </p>
        </div>
      </section>

      <!-- ══ 2-5 神煞 ════════════════════════════════════════ -->
      <section v-if="topShensha.length" id="section-2-5" class="section-block">
        <div class="section-title-row">
          <span class="section-num">2-5</span>
          <h2 class="section-title">神煞</h2>
        </div>
        <div class="shensha-grid">
          <div
            v-for="ss in topShensha"
            :key="ss.name"
            class="ss-card"
            :class="{ beneficial: ss.is_beneficial }"
          >
            <span class="ss-name">{{ ss.name }}</span>
            <span class="ss-pillar">（{{ ss.pillar }}柱）</span>
            <p class="ss-meaning">{{ ss.meaning }}</p>
            <p v-if="ss.classic_source" class="ss-source">── {{ ss.classic_source }}</p>
          </div>
        </div>
      </section>

      <!-- ══ 2-6 格局与用神 ══════════════════════════════════ -->
      <section id="section-2-6" class="section-block">
        <div class="section-title-row">
          <span class="section-num">2-6</span>
          <h2 class="section-title">格局与用神</h2>
        </div>

        <!-- 格局 -->
        <div v-if="bazi.geju" class="geju-block">
          <div class="geju-header">
            <span class="geju-name chip-term" @click="onChip(bazi.geju.geju_name)">
              {{ bazi.geju.geju_name }}
            </span>
            <span class="geju-level">{{ bazi.geju.geju_level }}</span>
            <span v-if="bazi.geju.is_broken" class="geju-broken">格破</span>
          </div>
          <p class="geju-text">{{ bazi.geju.interpretation_text }}</p>
          <div class="geju-tags" v-if="bazi.geju.inference_tags?.length">
            <span v-for="tag in bazi.geju.inference_tags" :key="tag" class="badge">{{ tag }}</span>
          </div>
        </div>

        <!-- 用神 -->
        <div v-if="bazi.yongshen" class="yongshen-block">
          <div class="ys-row">
            <span class="ys-label">喜神</span>
            <div class="ys-tags">
              <span
                v-for="f in bazi.yongshen.favor"
                :key="f"
                class="ys-tag ys-favor"
                :style="{ '--wx-c': favorColor(f) }"
              >{{ f }}</span>
            </div>
          </div>
          <div class="ys-row">
            <span class="ys-label">忌神</span>
            <div class="ys-tags">
              <span v-for="a in bazi.yongshen.avoid" :key="a" class="ys-tag ys-avoid">{{ a }}</span>
            </div>
          </div>
          <p v-if="bazi.yongshen.rationale" class="ys-rationale">
            说明：{{ bazi.yongshen.rationale }}
          </p>
        </div>
      </section>

      <!-- ══ 2-7 命宫胎元 ════════════════════════════════════ -->
      <section v-if="bazi.palace" id="section-2-7" class="section-block">
        <div class="section-title-row">
          <span class="section-num">2-7</span>
          <h2 class="section-title">命宫胎元</h2>
        </div>
        <div class="palace-grid">
          <div class="palace-card" v-if="bazi.palace.ming_gong">
            <p class="palace-type">命宫</p>
            <p class="palace-name">{{ bazi.palace.ming_gong.palace_name }}</p>
            <p class="palace-stars">{{ bazi.palace.ming_gong.dizhi }}{{ bazi.palace.ming_gong.tiangan ? ' · ' + bazi.palace.ming_gong.tiangan : '' }}</p>
            <p v-if="bazi.palace.ming_gong.shishen" class="palace-meaning">十神：{{ bazi.palace.ming_gong.shishen }}</p>
            <p v-if="bazi.palace.ming_gong.note" class="palace-meaning">{{ bazi.palace.ming_gong.note }}</p>
          </div>
          <div class="palace-card" v-if="bazi.palace.shen_gong">
            <p class="palace-type">身宫</p>
            <p class="palace-name">{{ bazi.palace.shen_gong.palace_name }}</p>
            <p class="palace-stars">{{ bazi.palace.shen_gong.dizhi }}{{ bazi.palace.shen_gong.tiangan ? ' · ' + bazi.palace.shen_gong.tiangan : '' }}</p>
            <p v-if="bazi.palace.shen_gong.shishen" class="palace-meaning">十神：{{ bazi.palace.shen_gong.shishen }}</p>
            <p v-if="bazi.palace.shen_gong.note" class="palace-meaning">{{ bazi.palace.shen_gong.note }}</p>
          </div>
        </div>
        <p class="conclusion-text">
          命宫位于
          <span class="chip-term" @click="onChip('命宫')">{{ bazi.palace.ming_gong?.palace_name }}</span>，
          身宫位于 {{ bazi.palace.shen_gong?.palace_name }}。
        </p>
      </section>

      <!-- ══ 2-8 运势时间线 ══════════════════════════════════ -->
      <section id="section-2-8" class="section-block">
        <div class="section-title-row">
          <span class="section-num">2-8</span>
          <h2 class="section-title">运势时间线</h2>
        </div>

        <!-- 结论段落 -->
        <div class="conclusion-block" v-if="bazi.start_dayun_age != null || dayunItems.length">
          <p class="conclusion-text">
            <template v-if="bazi.start_dayun_age != null">
              起运年龄 <strong>{{ bazi.start_dayun_age }}</strong> 岁。
            </template>
            <template v-if="dayunItems.find(d => d.isCurrent) as any">
              当前大运
              <span class="chip-term" @click="onChip(dayunItems.find(d => d.isCurrent)!.ganzhi)">
                {{ dayunItems.find(d => d.isCurrent)!.ganzhi }}
              </span>
              （{{ dayunItems.find(d => d.isCurrent)!.start_year }}年起，约 {{ dayunItems.find(d => d.isCurrent)!.endYear }} 年结束）。
            </template>
            <template v-if="bazi.current_fortune_summary?.current_liunian">
              本流年
              <span class="chip-term" @click="onChip(bazi.current_fortune_summary.current_liunian)">
                {{ bazi.current_fortune_summary.current_liunian }}
              </span>，
              <template v-if="bazi.current_fortune_summary.this_year_domains?.['综合']">
                综合评分 <strong>{{ bazi.current_fortune_summary.this_year_domains['综合'] }}</strong>。
              </template>
            </template>
          </p>
        </div>

        <!-- 大运时间轴 -->
        <div v-if="dayunItems.length" class="dayun-timeline">
          <p class="timeline-label">大运
            <span v-if="bazi.start_dayun_age != null" class="muted">（起运年龄 {{ bazi.start_dayun_age }}岁）</span>
          </p>
          <div class="dayun-track">
            <div
              v-for="item in dayunItems"
              :key="item.start_year"
              class="dayun-cell"
              :class="{ current: item.isCurrent }"
              :title="item.narrative"
            >
              <span class="dayun-gz">{{ item.ganzhi }}</span>
              <span class="dayun-age">{{ item.start_age }}岁</span>
              <span class="dayun-yr">{{ item.start_year }}</span>
            </div>
          </div>
        </div>

        <!-- 流年列表 -->
        <div v-if="liunianItems.length" class="liunian-section">
          <p class="timeline-label">流年
            <span class="muted" style="font-size:11px;margin-left:6px;">点击查看详情</span>
          </p>
          <div class="liunian-grid">
            <div
              v-for="item in liunianItems"
              :key="item.year"
              class="liunian-cell"
              :class="{ current: item.isCurrent, 'liunian-cell--expanded': expandedLiunianYear === item.year }"
              @click="toggleLiunian(item.year)"
            >
              <span class="ly-year">{{ item.year }}</span>
              <span class="ly-gz">{{ item.ganzhi }}</span>
              <div
                v-if="item.score != null"
                class="ly-score"
                :style="{ color: scoreColor(item.score) }"
              >{{ item.score }}</div>
            </div>
          </div>

          <!-- 流年详情抽屉 -->
          <Transition name="ly-drawer">
            <div
              v-if="expandedLiunianYear !== null"
              class="ly-drawer-panel"
              :key="expandedLiunianYear"
            >
              <template v-for="item in liunianItems" :key="item.year">
                <template v-if="item.year === expandedLiunianYear">
                  <div class="ly-drawer-header">
                    <span class="ly-drawer-gz">{{ item.ganzhi }}年（{{ item.year }}）</span>
                    <div v-if="item.score != null" class="ly-drawer-score" :style="{ color: scoreColor(item.score) }">
                      综合运势 {{ item.score }}分
                    </div>
                    <button class="ly-drawer-close" @click.stop="expandedLiunianYear = null" aria-label="关闭">✕</button>
                  </div>
                  <p v-if="item.summary" class="ly-drawer-text">{{ item.summary }}</p>
                  <table v-if="Object.keys(item.domains).length" class="ly-domains-table">
                    <thead>
                      <tr>
                        <th>领域</th>
                        <th>运势</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(val, key) in item.domains" :key="key">
                        <td class="domain-name">{{ key }}</td>
                        <td class="domain-val">{{ val }}</td>
                      </tr>
                    </tbody>
                  </table>
                </template>
              </template>
            </div>
          </Transition>
        </div>
      </section>

    </template>

    <!-- 未加载时占位提示 -->
    <div v-else class="empty-hint">
      <p>点击「重新计算」开始八字排盘</p>
      <button class="btn-primary" @click="store.loadChapterData(2, true)">开始计算</button>
    </div>

  </div>
</template>

<style scoped>
.chapter-bazi {
  display: flex;
  flex-direction: column;
  gap: var(--sp-6);
}

/* ─── 通用章节块 ─────────────────────────────────────── */
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

/* ─── 结论块 ─────────────────────────────────────────── */
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

/* ─── chip ──────────────────────────────────────────── */
.chip-term {
  border-bottom: 1px dashed var(--accent);
  cursor: pointer;
  color: var(--accent-dark);
  font-weight: 600;
}
.chip-term:hover { background: var(--accent-lt); }

.wx-chip {
  font-weight: 700;
  margin: 0 2px;
  cursor: pointer;
  border-bottom: 1px dashed currentColor;
}
.wx-chip.wx-avoid { color: var(--danger-dark) !important; }

/* ─── 四柱表 ─────────────────────────────────────────── */
.pillars-table-wrap { overflow-x: auto; }
.pillars-table {
  width: 100%;
  border-collapse: collapse;
  font-family: var(--font-cn);
  min-width: 400px;
}

.pillars-table th, .pillars-table td {
  text-align: center;
  padding: var(--sp-2) var(--sp-3);
  border: 1px solid var(--border);
  font-size: var(--fs-sm);
}

.pillars-head th {
  background: var(--surface-2);
  font-size: var(--fs-xs);
  color: var(--text-3);
  font-weight: 600;
}

.pillar-label-col { width: 52px; }

.day-col {
  background: var(--accent-lt) !important;
  border-color: var(--accent) !important;
}

.gz-char {
  font-size: var(--fs-2xl);
  font-weight: 700;
  display: block;
}

.row-label {
  font-size: var(--fs-xs);
  color: var(--text-3);
  background: var(--surface-2);
}

.cang-text, .nayin-text {
  font-size: var(--fs-xs);
  color: var(--text-2);
  font-family: var(--font-cn);
}

.ss-chip {
  font-size: var(--fs-xs);
  padding: 2px 6px;
  border-radius: 3px;
  background: var(--accent-glow);
  color: var(--accent-dark);
  cursor: pointer;
  display: inline-block;
}
.ss-chip.ss-day {
  background: var(--accent);
  color: #fff;
}

/* ─── 十神速览 ───────────────────────────────────────── */
.ten-gods-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--sp-3);
  margin-bottom: var(--sp-4);
}

.tg-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--sp-1);
  padding: var(--sp-3);
  background: var(--surface-2);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
}

.tg-pillar-name { font-size: 11px; color: var(--text-3); }
.tg-stem { font-size: var(--fs-2xl) !important; }

/* ─── 十神环形布局 ──────────────────────────────────── */
.tg-ring-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--sp-4);
  margin-top: var(--sp-3);
}

.tg-ring {
  position: relative;
  width: 240px;
  height: 240px;
  flex-shrink: 0;
}

.tg-ring-center {
  position: absolute;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  pointer-events: none;
}
.tg-ring-char { font-size: 48px; font-family: var(--font-cn); font-weight: 900; line-height: 1; }
.tg-ring-sub  { font-size: 11px; color: var(--text-3); white-space: nowrap; }

.tg-slot {
  position: absolute;
  top: calc(50% - 18px);
  left: calc(50% - 18px);
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  /* 顺时针排列：第 i 个槽在 i*36° 处，半径 90px */
  transform:
    rotate(calc(var(--i) * 36deg))
    translateY(-90px)
    rotate(calc(-1 * var(--i) * 36deg));
  border-radius: 50%;
  font-size: 12px;
  font-family: var(--font-cn);
  cursor: default;
  border: 1px solid var(--border);
  background: var(--surface-2);
  color: var(--text-3);
  transition: box-shadow 0.2s, background 0.2s;
}
.tg-slot--active {
  background: var(--color, var(--accent-soft));
  border-color: var(--color, var(--accent));
  color: #fff;
  cursor: pointer;
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--color, var(--accent)) 30%, transparent);
}
.tg-slot--active[style*="--color"] { background: var(--color); }

.tg-strength-bar-wrap {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  width: 240px;
}
.tg-strength-label { font-size: var(--fs-xs); color: var(--text-2); width: 40px; text-align: right; flex-shrink: 0; }
.tg-strength-track  { flex: 1; height: 6px; background: var(--border); border-radius: 99px; overflow: hidden; }
.tg-strength-fill   { height: 100%; background: var(--accent); border-radius: 99px; transition: width 0.8s; }
.tg-strength-val    { font-size: var(--fs-xs); color: var(--text-3); width: 28px; font-family: var(--font-mono); }

/* ─── 日主强弱依据 ───────────────────────────────────── */
.factors-list {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}

.factor-row {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
}

.factor-name { width: 52px; font-size: var(--fs-xs); color: var(--text-3); flex-shrink: 0; }

.factor-bar-wrap {
  flex: 1;
  height: 6px;
  background: var(--border);
  border-radius: 99px;
  overflow: hidden;
}

.factor-bar {
  height: 100%;
  border-radius: 99px;
  transition: width 0.5s ease;
  min-width: 4px;
}

.factor-reason { font-size: var(--fs-xs); color: var(--text-2); flex: 2; }

/* ─── 五行横条 ───────────────────────────────────────── */
.wx-bars { display: flex; flex-direction: column; gap: var(--sp-3); }

.wx-row {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
}

.wx-label { width: 24px; font-size: var(--fs-md); font-family: var(--font-cn); font-weight: 700; text-align: center; }

.wx-bar-track {
  flex: 1;
  height: 10px;
  background: var(--border);
  border-radius: 99px;
  overflow: hidden;
}

.wx-bar-fill {
  height: 100%;
  border-radius: 99px;
  transition: width 0.8s cubic-bezier(.25,.8,.25,1);
  min-width: 4px;
}

.wx-val { width: 36px; text-align: right; font-size: var(--fs-xs); color: var(--text-3); font-family: var(--font-mono); }

/* 五行雷达图 */
.wx-radar-wrap {
  display: flex;
  justify-content: center;
  margin-top: var(--sp-4);
}
.wx-radar-svg {
  width: 180px;
  height: 180px;
}
.radar-label {
  font-size: 13px;
  font-weight: 700;
  font-family: var(--font-cn);
}

/* ─── 干支关系 ───────────────────────────────────────── */
.ganzhi-relations { display: flex; flex-direction: column; gap: var(--sp-4); }
.rel-subtitle { font-size: var(--fs-sm); font-weight: 600; color: var(--text-2); margin-bottom: var(--sp-2); }
.rel-tags { display: flex; flex-wrap: wrap; gap: var(--sp-2); }
.rel-tag {
  font-size: var(--fs-xs);
  padding: 3px 10px;
  border-radius: 4px;
  background: #dbeafe;
  color: #1e40af;
  border: 1px solid #bfdbfe;
  font-family: var(--font-cn);
}
.rel-tag--clash {
  background: #fee2e2;
  color: var(--danger-dark);
  border-color: #fca5a5;
}
.mt-3 { margin-top: var(--sp-3); }
.card-empty { color: var(--text-3); font-size: var(--fs-sm); padding: var(--sp-3) 0; }

/* ─── 神煞 ──────────────────────────────────────────── */
.shensha-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: var(--sp-3);
}

.ss-card {
  padding: var(--sp-3);
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
}
.ss-card.beneficial {
  border-color: #86efac;
  background: #f0fdf4;
}

.ss-name { font-size: var(--fs-md); font-weight: 700; font-family: var(--font-cn); color: var(--text); }
.ss-pillar { font-size: 11px; color: var(--text-3); }
.ss-meaning { font-size: var(--fs-xs); color: var(--text-2); margin-top: var(--sp-2); line-height: 1.6; }
.ss-source { font-size: 11px; color: var(--text-3); margin-top: var(--sp-1); font-style: italic; }

/* ─── 格局用神 ───────────────────────────────────────── */
.geju-block {
  padding: var(--sp-4);
  background: var(--accent-lt);
  border-radius: var(--radius-sm);
  border: 1px solid rgba(217,119,6,.2);
  margin-bottom: var(--sp-4);
}

.geju-header {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  margin-bottom: var(--sp-3);
}

.geju-name {
  font-size: var(--fs-xl);
  font-weight: 700;
  font-family: var(--font-cn);
  color: var(--accent-dark);
  border-bottom: 2px solid var(--accent-dark) !important;
}

.geju-level {
  font-size: var(--fs-xs);
  padding: 2px 8px;
  background: var(--accent);
  color: #fff;
  border-radius: 99px;
}

.geju-broken {
  font-size: var(--fs-xs);
  padding: 2px 8px;
  background: var(--danger-dark);
  color: #fff;
  border-radius: 99px;
}

.geju-text { font-size: var(--fs-sm); color: var(--text); line-height: 1.8; font-family: var(--font-cn); }
.geju-tags { display: flex; flex-wrap: wrap; gap: 4px; margin-top: var(--sp-3); }
.badge { font-size: 11px; padding: 2px 7px; border-radius: 99px; background: var(--surface); color: var(--text-2); border: 1px solid var(--border); }

.yongshen-block { display: flex; flex-direction: column; gap: var(--sp-3); }

.ys-row { display: flex; align-items: center; gap: var(--sp-3); }
.ys-label { width: 36px; font-size: var(--fs-xs); color: var(--text-3); }
.ys-tags { display: flex; flex-wrap: wrap; gap: var(--sp-2); }
.ys-tag {
  font-size: var(--fs-md);
  font-family: var(--font-cn);
  font-weight: 700;
  padding: 4px 12px;
  border-radius: var(--radius-sm);
  border: 1px solid currentColor;
}
.ys-favor { color: var(--wx-c, var(--accent)); background: var(--accent-lt); }
.ys-avoid { color: var(--danger-dark); background: #fee2e2; }

.ys-rationale {
  font-size: var(--fs-sm);
  color: var(--text-2);
  background: var(--surface-2);
  padding: var(--sp-3);
  border-radius: var(--radius-sm);
  border-left: 3px solid var(--border-md);
  line-height: 1.7;
  font-family: var(--font-cn);
}

/* ─── 命宫 ──────────────────────────────────────────── */
.palace-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--sp-4);
  margin-bottom: var(--sp-4);
}

.palace-card {
  padding: var(--sp-4);
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  text-align: center;
}

.palace-type { font-size: 11px; color: var(--text-3); margin-bottom: var(--sp-1); }
.palace-name { font-size: var(--fs-xl); font-weight: 700; font-family: var(--font-cn); color: var(--text); }
.palace-stars { font-size: var(--fs-sm); color: var(--accent-dark); margin: var(--sp-2) 0; font-family: var(--font-cn); }
.palace-meaning { font-size: var(--fs-xs); color: var(--text-2); line-height: 1.6; }

/* ─── 大运时间线 ─────────────────────────────────────── */
.dayun-timeline { margin-bottom: var(--sp-6); }
.timeline-label { font-size: var(--fs-sm); font-weight: 600; color: var(--text-2); margin-bottom: var(--sp-3); }
.muted { font-weight: 400; color: var(--text-3); }

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
  min-width: 68px;
  gap: 2px;
  cursor: default;
  transition: all var(--dur-fast);
}
.dayun-cell:hover { background: var(--accent-glow); }
.dayun-cell.current {
  border-color: var(--accent) !important;
  background: var(--accent-lt) !important;
  box-shadow: 0 0 0 2px var(--accent-glow);
}

.dayun-gz { font-size: var(--fs-lg); font-family: var(--font-cn); font-weight: 700; color: var(--text); }
.dayun-age { font-size: 11px; color: var(--text-3); }
.dayun-yr { font-size: 10px; color: var(--text-3); font-family: var(--font-mono); }

/* ─── 流年网格 ───────────────────────────────────────── */
.liunian-section { margin-top: var(--sp-4); }

.liunian-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(64px, 1fr));
  gap: var(--sp-2);
}

.liunian-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--sp-2);
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  gap: 1px;
  cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.liunian-cell:hover {
  border-color: var(--accent);
}
.liunian-cell.current {
  border-color: var(--accent);
  background: var(--accent-lt);
}
.liunian-cell--expanded {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 2px var(--accent-soft);
}

.ly-year { font-size: 10px; color: var(--text-3); font-family: var(--font-mono); }
.ly-gz { font-size: var(--fs-md); font-family: var(--font-cn); font-weight: 600; color: var(--text); }
.ly-score { font-size: 11px; font-weight: 700; font-family: var(--font-mono); }

/* ─── 流年抽屉 ───────────────────────────────────────── */
.ly-drawer-panel {
  margin-top: var(--sp-3);
  padding: var(--sp-4);
  background: var(--surface-2);
  border: 1px solid var(--accent);
  border-radius: var(--radius);
  position: relative;
}

.ly-drawer-header {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  margin-bottom: var(--sp-3);
  flex-wrap: wrap;
}

.ly-drawer-gz {
  font-size: var(--fs-lg);
  font-weight: 700;
  font-family: var(--font-cn);
  color: var(--text);
}

.ly-drawer-score {
  font-size: var(--fs-sm);
  font-weight: 600;
  font-family: var(--font-mono);
  padding: 2px 8px;
  background: var(--bg);
  border-radius: 99px;
  border: 1px solid var(--border);
}

.ly-drawer-close {
  margin-left: auto;
  background: none;
  border: 1px solid var(--border);
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  cursor: pointer;
  color: var(--text-3);
  line-height: 1;
  padding: 0;
  transition: border-color 0.15s, color 0.15s;
}
.ly-drawer-close:hover {
  border-color: var(--danger);
  color: var(--danger);
}

.ly-drawer-text {
  font-size: var(--fs-md);
  color: var(--text-2);
  line-height: 1.8;
  font-family: var(--font-cn);
  margin-bottom: var(--sp-3);
}

.ly-domains-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--fs-sm);
}
.ly-domains-table th {
  text-align: left;
  padding: var(--sp-1) var(--sp-3);
  font-size: var(--fs-xs);
  color: var(--text-3);
  border-bottom: 1px solid var(--border);
  font-weight: 600;
}
.ly-domains-table td {
  padding: var(--sp-2) var(--sp-3);
  border-bottom: 1px solid var(--border);
  color: var(--text);
  font-family: var(--font-cn);
  vertical-align: top;
}
.domain-name {
  white-space: nowrap;
  font-weight: 600;
  color: var(--accent);
  width: 60px;
}
.domain-val {
  line-height: 1.7;
}

/* 抽屉展开动画 */
.ly-drawer-enter-active,
.ly-drawer-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.ly-drawer-enter-from,
.ly-drawer-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

/* ─── 骨架/错误/空 ────────────────────────────────────── */
.loading-wrap, .error-card, .empty-hint {
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
  padding: var(--sp-4) 0;
}

.skel-card {
  border-radius: var(--radius);
  background: linear-gradient(90deg, #e2e8f0 25%, #f1f5f9 50%, #e2e8f0 75%);
  background-size: 400px;
  animation: shimmer 1.2s infinite;
}

.error-card { align-items: flex-start; }
.error-msg { color: var(--danger-dark); }
.empty-hint { align-items: center; color: var(--text-3); }

.btn-primary {
  padding: 8px 20px;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  font-size: var(--fs-sm);
  font-weight: 600;
  cursor: pointer;
}
.btn-sec {
  padding: 6px 16px;
  background: transparent;
  border: 1px solid var(--border-md);
  border-radius: var(--radius-sm);
  font-size: var(--fs-sm);
  cursor: pointer;
  color: var(--text-2);
}
</style>
