<script setup lang="ts">
/**
 * WesternView.vue — 西方占星出生盘（§6.1）
 * 功能：出生时间输入 → SVG 星盘圆轮 + 行星位置表 + 相位矩阵 + 元素/模式统计
 */
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import {
  getWesternChart, getSolarReturn,
  type WesternChartResponse, type SolarReturnResponse,
} from '@/api/western'

const route = useRoute()

// ── 表单状态 ──────────────────────────────────────────────────
const form = ref({
  date: '1990-01-15',
  time: '12:00',
  lat:  '39.90',
  lon:  '116.41',
  tz:   'Asia/Shanghai',
})

const loading = ref(false)
const error   = ref<string | null>(null)
const result  = ref<WesternChartResponse | null>(null)

// 预设城市
const CITIES = [
  { label: '北京',   lat: '39.90',  lon: '116.41', tz: 'Asia/Shanghai' },
  { label: '上海',   lat: '31.23',  lon: '121.47', tz: 'Asia/Shanghai' },
  { label: '广州',   lat: '23.13',  lon: '113.26', tz: 'Asia/Shanghai' },
  { label: '成都',   lat: '30.67',  lon: '104.07', tz: 'Asia/Shanghai' },
  { label: '纽约',   lat: '40.71',  lon: '-74.01', tz: 'America/New_York' },
  { label: '伦敦',   lat: '51.51',  lon: '-0.13',  tz: 'Europe/London' },
  { label: '东京',   lat: '35.69',  lon: '139.69', tz: 'Asia/Tokyo' },
  { label: '巴黎',   lat: '48.86',  lon: '2.35',   tz: 'Europe/Paris' },
]

function selectCity(c: typeof CITIES[0]) {
  form.value.lat = c.lat
  form.value.lon = c.lon
  form.value.tz  = c.tz
}

// URL query 预填
onMounted(() => {
  if (route.query.date) form.value.date = String(route.query.date)
  if (route.query.time) form.value.time = String(route.query.time)
  if (route.query.lat)  form.value.lat  = String(route.query.lat)
  if (route.query.lon)  form.value.lon  = String(route.query.lon)
  if (route.query.tz)   form.value.tz   = String(route.query.tz)
  if (route.query.date) query()
})

async function query() {
  const dt = `${form.value.date}T${form.value.time}:00`
  loading.value = true
  error.value   = null
  result.value  = null
  try {
    result.value = await getWesternChart({
      dt,
      lat: parseFloat(form.value.lat),
      lon: parseFloat(form.value.lon),
      tz:  form.value.tz,
    })
  } catch (e: unknown) {
    error.value = (e as Error).message ?? '计算失败'
  } finally {
    loading.value = false
  }
}
// ── 太阳回归年盘状态 ────────────────────────────────────────

const srForm = ref({
  year: new Date().getFullYear(),
  lat:  '',
  lon:  '',
})
const srLoading = ref(false)
const srError   = ref<string | null>(null)
const srResult  = ref<SolarReturnResponse | null>(null)

// 当出生盘计算完成后，默认用同一地点
function initSrLocation() {
  if (srForm.value.lat === '' && form.value.lat) srForm.value.lat = form.value.lat
  if (srForm.value.lon === '' && form.value.lon) srForm.value.lon = form.value.lon
}

async function querySolarReturn() {
  if (!result.value) return
  initSrLocation()
  const dt = `${form.value.date}T${form.value.time}:00`
  srLoading.value = true
  srError.value   = null
  srResult.value  = null
  try {
    srResult.value = await getSolarReturn({
      natal_dt:  dt,
      natal_lat: parseFloat(form.value.lat),
      natal_lon: parseFloat(form.value.lon),
      natal_tz:  form.value.tz,
      sr_year:   srForm.value.year,
      sr_lat:    parseFloat(String(srForm.value.lat) || form.value.lat),
      sr_lon:    parseFloat(String(srForm.value.lon) || form.value.lon),
    })
  } catch (e: unknown) {
    srError.value = (e as Error).message ?? '计算失败'
  } finally {
    srLoading.value = false
  }
}

// 格式化 SR UTC datetime
function formatSrDt(iso: string): string {
  try {
    const d = new Date(iso)
    return d.toLocaleString('zh-CN', {
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit',
      timeZone: 'UTC', timeZoneName: 'short',
    })
  } catch { return iso }
}
// ── SVG 星盘圆轮参数 ──────────────────────────────────────────
const CX = 200, CY = 200
const R_OUTER = 195   // SVG 背景圆
const R_SIGN_OUT = 190  // 星座外环
const R_SIGN_IN  = 158  // 星座内环
const R_PLANET   = 136  // 行星符号
const R_INNER    = 90   // 内圆（相位区域边界）

const ELEM_FILL: Record<string, string> = {
  fire:  '#fed7aa',   // 橙/火
  earth: '#d1fae5',   // 绿/土
  air:   '#e0f2fe',   // 蓝/风
  water: '#ede9fe',   // 紫/水
}
const ELEM_STROKE: Record<string, string> = {
  fire:  '#fb923c',
  earth: '#4ade80',
  air:   '#38bdf8',
  water: '#a78bfa',
}

// 坐标换算：黄经 lon 在 r 处的 SVG 坐标
// ASC 置于左侧（数学 180°），黄经增加沿 CCW
function chartXY(lon: number, r: number, ascLon: number): [number, number] {
  const theta = (180.0 + (lon - ascLon)) % 360.0
  const rad   = theta * Math.PI / 180.0
  return [
    CX + r * Math.cos(rad),
    CY - r * Math.sin(rad),
  ]
}

// 扇形路径（多边形近似，steps 个插值点）
function sectorPath(theta1: number, theta2: number, rIn: number, rOut: number, steps = 8): string {
  const pts: string[] = []
  const dTheta = (theta2 - theta1) / steps
  // 外弧（theta 递增，CCW）
  for (let i = 0; i <= steps; i++) {
    const t = (theta1 + i * dTheta) * Math.PI / 180.0
    pts.push(`${CX + rOut * Math.cos(t)},${CY - rOut * Math.sin(t)}`)
  }
  // 内弧（theta 递减，CW 反向）
  for (let i = steps; i >= 0; i--) {
    const t = (theta1 + i * dTheta) * Math.PI / 180.0
    pts.push(`${CX + rIn * Math.cos(t)},${CY - rIn * Math.sin(t)}`)
  }
  return `M ${pts[0]} L ${pts.slice(1).join(' L ')} Z`
}

// 计算所有星座扇形
const signSectors = computed(() => {
  if (!result.value) return []
  const asc = result.value.ascendant.longitude
  const SIGNS_CN  = ['♈白羊','♉金牛','♊双子','♋巨蟹','♌狮子','♍处女',
                      '♎天秤','♏天蝎','♐射手','♑摩羯','♒水瓶','♓双鱼']
  const ELEM_BY_IDX = ['fire','earth','air','water','fire','earth','air','water','fire','earth','air','water']
  return Array.from({ length: 12 }, (_, i) => {
    const theta1 = (180.0 + (i * 30 - asc)) % 360.0
    const theta2 = theta1 + 30.0
    // 中点角（用于放文字标签）
    const tmid  = (theta1 + 15.0) * Math.PI / 180.0
    const elem  = ELEM_BY_IDX[i]
    return {
      path:  sectorPath(theta1, theta2, R_SIGN_IN, R_SIGN_OUT),
      label: SIGNS_CN[i].slice(0, 2),  // 显示星座符号
      symbol: SIGNS_CN[i].slice(0, 1), // Unicode 符号
      lx: CX + (R_SIGN_IN + 18) * Math.cos(tmid),
      ly: CY - (R_SIGN_IN + 18) * Math.sin(tmid),
      fill:   ELEM_FILL[elem],
      stroke: ELEM_STROKE[elem],
    }
  })
})

// 计算行星 SVG 坐标
const planetPositions = computed(() => {
  if (!result.value) return []
  const asc = result.value.ascendant.longitude
  return result.value.planets.map(p => {
    const [px, py] = chartXY(p.longitude, R_PLANET, asc)
    return { ...p, px, py }
  })
})

// 计算相位连线
const aspectLines = computed(() => {
  if (!result.value) return []
  const asc = result.value.ascendant.longitude
  const posMap: Record<string, [number, number]> = {}
  result.value.planets.forEach(p => {
    posMap[p.name_en] = chartXY(p.longitude, R_INNER - 10, asc)
  })
  return result.value.aspects.slice(0, 20).map(a => {
    const [x1, y1] = posMap[a.planet1] ?? [CX, CY]
    const [x2, y2] = posMap[a.planet2] ?? [CX, CY]
    return { ...a, x1, y1, x2, y2 }
  })
})

// ASC 和 MC 参考线
const axisLines = computed(() => {
  if (!result.value) return []
  const asc = result.value.ascendant.longitude
  const mc  = result.value.midheaven.longitude
  const lines = []
  for (const [label, lon] of [['ASC', asc], ['MC', mc], ['DSC', (asc + 180) % 360], ['IC', (mc + 180) % 360]]) {
    const [ox, oy] = chartXY(lon as number, R_SIGN_OUT + 4, asc)
    const [ix, iy] = chartXY(lon as number, R_INNER, asc)
    const [lx, ly] = chartXY(lon as number, R_SIGN_OUT + 12, asc)
    lines.push({ label, ox, oy, ix, iy, lx, ly, lon: lon as number })
  }
  return lines
})

// ── 元素/模式颜色 ──────────────────────────────────────────────
const ELEM_COLOR_MAP: Record<string, string> = {
  fire: '#f97316', earth: '#22c55e', air: '#38bdf8', water: '#a855f7'
}
const ELEM_NAME: Record<string, string> = {
  fire: '🔥火象', earth: '🌱土象', air: '💨风象', water: '💧水象'
}
const MODE_NAME: Record<string, string> = {
  cardinal: '本位', fixed: '固定', mutable: '变动'
}

// 相位在矩阵中的背景色
function aspectBg(p1: string, p2: string): { text: string; bg: string; fg: string } {
  if (!result.value) return { text: '', bg: 'transparent', fg: 'var(--text-3)' }
  const asp = result.value.aspects.find(
    a => (a.planet1 === p1 && a.planet2 === p2) || (a.planet1 === p2 && a.planet2 === p1)
  )
  if (!asp) return { text: '', bg: 'transparent', fg: 'var(--text-3)' }
  const bg = asp.color + '33'  // 20% alpha
  return { text: asp.aspect_cn, bg, fg: asp.color }
}

// 行星符号列表（矩阵用）
const PLANET_SYMS: Record<string, string> = {
  Sun: '☉', Moon: '☽', Mercury: '☿', Venus: '♀', Mars: '♂',
  Jupiter: '♃', Saturn: '♄', Uranus: '⛢', Neptune: '♆',
}
const PLANET_ORDER = ['Sun','Moon','Mercury','Venus','Mars','Jupiter','Saturn','Uranus','Neptune']
</script>

<template>
  <div class="w-wrap">
    <!-- ── 顶部标题 ── -->
    <div class="w-header">
      <h1 class="w-title">西方占星 · 出生盘</h1>
      <p class="w-subtitle">§6.1 太阳 · 月亮 · 上升 · 行星位置 · 相位分析</p>
    </div>

    <!-- ── 输入表单 ── -->
    <div class="w-form-card">
      <div class="w-form-grid">
        <div class="w-field">
          <label class="w-label">出生日期</label>
          <input v-model="form.date" type="date" class="w-input" />
        </div>
        <div class="w-field">
          <label class="w-label">出生时间</label>
          <input v-model="form.time" type="time" class="w-input" />
        </div>
        <div class="w-field">
          <label class="w-label">纬度（北纬+）</label>
          <input v-model="form.lat" type="number" step="0.01" class="w-input" placeholder="如 39.90" />
        </div>
        <div class="w-field">
          <label class="w-label">经度（东经+）</label>
          <input v-model="form.lon" type="number" step="0.01" class="w-input" placeholder="如 116.41" />
        </div>
        <div class="w-field">
          <label class="w-label">时区</label>
          <input v-model="form.tz" type="text" class="w-input" placeholder="Asia/Shanghai" />
        </div>
        <div class="w-field w-field-btn">
          <label class="w-label">&nbsp;</label>
          <button class="w-btn-primary" :disabled="loading" @click="query">
            {{ loading ? '计算中…' : '🔭 排盘' }}
          </button>
        </div>
      </div>

      <!-- 快捷城市 -->
      <div class="w-cities">
        <span class="w-city-label">快捷：</span>
        <button
          v-for="c in CITIES" :key="c.label"
          class="w-city-btn"
          @click="selectCity(c)"
        >{{ c.label }}</button>
      </div>
    </div>

    <!-- 错误提示 -->
    <div v-if="error" class="w-error">⚠️ {{ error }}</div>

    <!-- ── 结果区 ── -->
    <template v-if="result">
      <div class="w-result-grid">

        <!-- 左：SVG 星盘圆轮 -->
        <div class="w-chart-card">
          <h2 class="w-sec-title">出生星盘</h2>
          <div class="w-svg-wrap">
            <svg viewBox="0 0 400 400" width="380" height="380" aria-label="西方星盘">
              <!-- 背景圆 -->
              <circle cx="200" cy="200" :r="R_OUTER" fill="var(--surface)" stroke="var(--border)" stroke-width="1"/>

              <!-- 星座扇形（彩色分区） -->
              <path
                v-for="(s, i) in signSectors"
                :key="'sign-' + i"
                :d="s.path"
                :fill="s.fill"
                :stroke="s.stroke"
                stroke-width="0.5"
                opacity="0.7"
              />

              <!-- 星座符号标签 -->
              <text
                v-for="(s, i) in signSectors"
                :key="'slabel-' + i"
                :x="s.lx"
                :y="s.ly"
                text-anchor="middle"
                dominant-baseline="central"
                class="svg-sign"
              >{{ s.symbol }}</text>

              <!-- 内界圆 -->
              <circle cx="200" cy="200" :r="R_SIGN_IN" fill="var(--bg)" stroke="var(--border)" stroke-width="1"/>

              <!-- 相位连线 -->
              <line
                v-for="(a, i) in aspectLines"
                :key="'asp-' + i"
                :x1="a.x1" :y1="a.y1"
                :x2="a.x2" :y2="a.y2"
                :stroke="a.color"
                stroke-width="1"
                opacity="0.45"
              />

              <!-- 行星轨道圆 -->
              <circle cx="200" cy="200" :r="R_PLANET + 14" fill="none" stroke="var(--border)" stroke-width="0.5" stroke-dasharray="2,3"/>

              <!-- ASC/MC 轴线 -->
              <line
                v-for="ax in axisLines"
                :key="'ax-' + ax.label"
                :x1="ax.ox" :y1="ax.oy"
                :x2="ax.ix" :y2="ax.iy"
                stroke="var(--accent)"
                stroke-width="1.2"
                opacity="0.7"
              />
              <text
                v-for="ax in axisLines"
                :key="'axl-' + ax.label"
                :x="ax.lx" :y="ax.ly"
                text-anchor="middle"
                dominant-baseline="central"
                class="svg-axis"
              >{{ ax.label }}</text>

              <!-- 行星 -->
              <g v-for="p in planetPositions" :key="'p-' + p.name_en">
                <circle :cx="p.px" :cy="p.py" r="11" fill="var(--surface)" stroke="var(--border)" stroke-width="0.8"/>
                <text :x="p.px" :y="p.py" text-anchor="middle" dominant-baseline="central" class="svg-planet">
                  {{ p.symbol }}
                </text>
                <text v-if="p.retrograde" :x="p.px + 9" :y="p.py - 9" class="svg-retro">℞</text>
              </g>

              <!-- 中心信息 -->
              <circle cx="200" cy="200" :r="R_INNER - 12" fill="var(--surface)" stroke="var(--border)" stroke-width="1"/>
              <text x="200" y="190" text-anchor="middle" class="svg-center-main">
                {{ result.ascendant.sign_symbol }} {{ result.ascendant.sign_cn }}
              </text>
              <text x="200" y="208" text-anchor="middle" class="svg-center-sub">上升</text>
            </svg>
          </div>

          <!-- 元素分布 -->
          <div class="w-elem-row">
            <div
              v-for="(cnt, elem) in result.element_counts"
              :key="String(elem)"
              class="w-elem-chip"
              :style="{ borderColor: ELEM_COLOR_MAP[String(elem)] }"
            >
              <span class="w-elem-name">{{ ELEM_NAME[String(elem)] }}</span>
              <span class="w-elem-cnt" :style="{ color: ELEM_COLOR_MAP[String(elem)] }">{{ cnt }}</span>
            </div>
          </div>
          <!-- 模式分布 -->
          <div class="w-mode-row">
            <div v-for="(cnt, mode) in result.mode_counts" :key="String(mode)" class="w-mode-chip">
              <span class="w-mode-name">{{ MODE_NAME[String(mode)] }}</span>
              <span class="w-mode-cnt">{{ cnt }}</span>
            </div>
          </div>
        </div>

        <!-- 右：行星位置表 + 相位 -->
        <div class="w-right-col">

          <!-- 上升 / 中天 -->
          <div class="w-angles-row">
            <div class="w-angle-card w-angle-asc">
              <div class="w-angle-label">上升 ASC</div>
              <div class="w-angle-sign">{{ result.ascendant.sign_symbol }} {{ result.ascendant.sign_cn }}</div>
              <div class="w-angle-deg">{{ result.ascendant.degree_str }}</div>
              <div class="w-angle-elem">{{ result.ascendant.element_cn }}</div>
            </div>
            <div class="w-angle-card w-angle-mc">
              <div class="w-angle-label">中天 MC</div>
              <div class="w-angle-sign">{{ result.midheaven.sign_symbol }} {{ result.midheaven.sign_cn }}</div>
              <div class="w-angle-deg">{{ result.midheaven.degree_str }}</div>
              <div class="w-angle-elem">{{ result.midheaven.element_cn }}</div>
            </div>
          </div>

          <!-- 行星位置表 -->
          <div class="w-planets-card">
            <h2 class="w-sec-title">行星位置</h2>
            <table class="w-planet-table">
              <thead>
                <tr>
                  <th>天体</th>
                  <th>符号</th>
                  <th>星座</th>
                  <th>度数</th>
                  <th>元素</th>
                  <th>逆行</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="p in result.planets" :key="p.name_en">
                  <td class="w-pt-name">{{ p.symbol }} {{ p.name_cn }}</td>
                  <td class="w-pt-sign">{{ p.sign_symbol }}</td>
                  <td class="w-pt-sign">{{ p.sign_cn }}</td>
                  <td class="w-pt-deg">{{ p.degree_str }}</td>
                  <td class="w-pt-elem" :style="{ color: ELEM_COLOR_MAP[p.element] }">{{ p.element_cn }}</td>
                  <td class="w-pt-retro">{{ p.retrograde ? '℞' : '—' }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 相位列表 -->
          <div v-if="result.aspects.length" class="w-aspects-card">
            <h2 class="w-sec-title">主要相位</h2>
            <div class="w-aspect-list">
              <div
                v-for="(a, i) in result.aspects"
                :key="i"
                class="w-aspect-item"
              >
                <span class="w-asp-dot" :style="{ background: a.color }"></span>
                <span class="w-asp-p1">{{ PLANET_SYMS[a.planet1] }}{{ result.planets.find(p=>p.name_en===a.planet1)?.name_cn }}</span>
                <span class="w-asp-type" :style="{ color: a.color }">{{ a.aspect_cn }}</span>
                <span class="w-asp-p2">{{ PLANET_SYMS[a.planet2] }}{{ result.planets.find(p=>p.name_en===a.planet2)?.name_cn }}</span>
                <span class="w-asp-orb">±{{ a.orb }}°</span>
              </div>
            </div>
          </div>

          <!-- 相位矩阵 -->
          <div v-if="result.aspects.length" class="w-matrix-card">
            <h2 class="w-sec-title">相位矩阵</h2>
            <div class="w-matrix-scroll">
              <table class="w-matrix-table">
                <thead>
                  <tr>
                    <th></th>
                    <th v-for="pname in PLANET_ORDER.slice(1)" :key="pname" class="w-mth">
                      {{ PLANET_SYMS[pname] }}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(p1, ri) in PLANET_ORDER.slice(0, -1)" :key="p1">
                    <td class="w-mth">{{ PLANET_SYMS[p1] }}</td>
                    <td
                      v-for="(p2, ci) in PLANET_ORDER.slice(1)"
                      :key="p2"
                      class="w-mcell"
                      :class="{ 'w-mcell-diag': ci < ri }"
                      :style="{
                        background: ci >= ri ? aspectBg(p1, p2).bg : 'var(--surface-2)',
                        color: ci >= ri ? aspectBg(p1, p2).fg : 'transparent',
                      }"
                      :title="ci >= ri ? aspectBg(p1, p2).text : ''"
                    >
                      {{ ci >= ri ? aspectBg(p1, p2).text : '' }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

        </div>
      </div>
    </template>

    <!-- ── 太阳回归年盘区域 ── -->
    <template v-if="result">
      <div class="sr-section">
        <h2 class="sr-heading">☉ 太阳回归年盘 <span class="sr-tag">§6.2 Solar Return</span></h2>
        <p class="sr-desc">太阳回归：当太阳回到出生天太阳黄经相同的度数时，以该时刻指定地点排得支配未来一年的年盘。</p>

        <div class="sr-form">
          <div class="sr-field">
            <label class="sr-label">回归年</label>
            <input v-model.number="srForm.year" type="number" min="1950" max="2100"
              class="sr-input" style="width:90px" />
          </div>
          <div class="sr-field">
            <label class="sr-label">所在地纬度</label>
            <input v-model="srForm.lat" type="number" step="0.01" class="sr-input"
              :placeholder="form.lat" />
          </div>
          <div class="sr-field">
            <label class="sr-label">所在地经度</label>
            <input v-model="srForm.lon" type="number" step="0.01" class="sr-input"
              :placeholder="form.lon" />
          </div>
          <div class="sr-field">
            <label class="sr-label">&nbsp;</label>
            <button class="sr-btn" :disabled="srLoading" @click="querySolarReturn">
              {{ srLoading ? '计算中…' : '☉ 计算回归年盘' }}
            </button>
          </div>
        </div>

        <div v-if="srError" class="w-error">⚠️ {{ srError }}</div>

        <template v-if="srResult">
          <!-- SR 时刻标注 -->
          <div class="sr-datetime">
            <span class="sr-dt-label">太阳回归时刻（UTC）：</span>
            <span class="sr-dt-val">{{ formatSrDt(srResult.sr_dt_utc) }}</span>
            <span class="sr-dt-note">—— 太阳处于 {{ result?.planets[0].sign_symbol }}{{ result?.planets[0].sign_cn }} {{ result?.planets[0].degree_str }}</span>
          </div>

          <!-- SR 上升/中天 -->
          <div class="sr-angles">
            <div class="sr-angle-card">
              <span class="sr-al">SR 上升 ASC</span>
              <span class="sr-av">{{ srResult.ascendant.sign_symbol }} {{ srResult.ascendant.sign_cn }} {{ srResult.ascendant.degree_str }}</span>
            </div>
            <div class="sr-angle-card">
              <span class="sr-al">SR 中天 MC</span>
              <span class="sr-av">{{ srResult.midheaven.sign_symbol }} {{ srResult.midheaven.sign_cn }} {{ srResult.midheaven.degree_str }}</span>
            </div>
          </div>

          <!-- 出生盘 vs 回归年盘 行星对比表 -->
          <div class="sr-compare-wrap">
            <h3 class="sr-sub-title">行星对比：出生盘 vs {{ srResult.sr_year }} 年回归</h3>
            <div class="sr-compare-scroll">
              <table class="sr-compare-table">
                <thead><tr>
                  <th class="sr-th">天体</th>
                  <th class="sr-th">出生年盘</th>
                  <th class="sr-th">回归年盘</th>
                  <th class="sr-th">屡转</th>
                </tr></thead>
                <tbody>
                  <tr v-for="(rp, i) in srResult.planets" :key="rp.name_en" class="sr-row">
                    <td class="sr-td">{{ rp.symbol }} {{ rp.name_cn }}</td>
                    <td class="sr-td sr-natal">
                      {{ result?.planets[i].sign_symbol }} {{ result?.planets[i].sign_cn }}
                      {{ result?.planets[i].degree_str }}
                    </td>
                    <td class="sr-td sr-ret">
                      {{ rp.sign_symbol }} {{ rp.sign_cn }} {{ rp.degree_str }}
                      <span v-if="rp.retrograde" class="sr-r">℞</span>
                    </td>
                    <td class="sr-td">
                      <span v-if="result && rp.sign_index !== result.planets[i].sign_index" class="sr-moved">已入{{ rp.sign_cn }}</span>
                      <span v-else class="sr-same">同星座</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </template>
      </div>
    </template>

    <!-- 空态提示 -->
    <div v-if="!result && !loading" class="w-empty">
      <div class="w-empty-icon">🔭</div>
      <p>填写出生数据后点击「排盘」查看出生星盘</p>
    </div>
  </div>
</template>

<style scoped>
/* ── 布局 ───────────────────────────────────────────────────── */
.w-wrap {
  max-width: 1280px;
  margin: 0 auto;
  padding: 24px 20px 48px;
}

.w-header { margin-bottom: 20px; }
.w-title  { font-size: 22px; font-weight: 700; color: var(--text); margin: 0; font-family: var(--font-cn); }
.w-subtitle { font-size: 13px; color: var(--text-3); margin: 4px 0 0; }

/* ── 表单卡片 ───────────────────────────────────────────────── */
.w-form-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
}

.w-form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
  margin-bottom: 12px;
}

.w-field { display: flex; flex-direction: column; gap: 5px; }
.w-field-btn { justify-content: flex-end; }
.w-label { font-size: 11px; color: var(--text-3); font-weight: 500; letter-spacing: .04em; text-transform: uppercase; }
.w-input {
  padding: 8px 10px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg);
  color: var(--text);
  font-size: 13px;
  outline: none;
  transition: border-color .15s;
  font-family: var(--font-mono);
}
.w-input:focus { border-color: var(--accent); }

.w-btn-primary {
  padding: 9px 20px;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background .15s;
  white-space: nowrap;
}
.w-btn-primary:hover:not(:disabled) { background: var(--accent-dark); }
.w-btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }

.w-cities { display: flex; align-items: center; flex-wrap: wrap; gap: 6px; }
.w-city-label { font-size: 11px; color: var(--text-3); }
.w-city-btn {
  padding: 3px 10px;
  border: 1px solid var(--border);
  border-radius: 99px;
  background: var(--bg);
  font-size: 12px;
  color: var(--text-2);
  cursor: pointer;
  transition: all .15s;
}
.w-city-btn:hover { border-color: var(--accent); color: var(--accent); background: var(--accent-lt); }

/* ── 错误 ───────────────────────────────────────────────────── */
.w-error {
  padding: 12px 16px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 10px;
  color: #dc2626;
  font-size: 13px;
  margin-bottom: 20px;
}

/* ── 结果布局 ───────────────────────────────────────────────── */
.w-result-grid {
  display: grid;
  grid-template-columns: 420px 1fr;
  gap: 20px;
  align-items: start;
}

/* ── SVG 星盘卡片 ───────────────────────────────────────────── */
.w-chart-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px;
  position: sticky;
  top: 20px;
}

.w-sec-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--text);
  margin: 0 0 14px;
  font-family: var(--font-cn);
}

.w-svg-wrap {
  display: flex;
  justify-content: center;
  margin-bottom: 16px;
}

/* SVG 文字样式 */
.svg-sign   { font-size: 13px; font-family: var(--font-cn); fill: var(--text-2); }
.svg-planet { font-size: 13px; fill: var(--text); font-weight: 600; }
.svg-retro  { font-size: 8px;  fill: #ef4444; font-weight: 700; }
.svg-axis   { font-size: 8px;  fill: var(--accent); font-weight: 700; font-family: var(--font-ui); }
.svg-center-main { font-size: 14px; font-weight: 700; fill: var(--text);   font-family: var(--font-cn); }
.svg-center-sub  { font-size: 10px;                  fill: var(--text-3);  font-family: var(--font-ui); }

/* 元素分布 */
.w-elem-row { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 8px; }
.w-elem-chip {
  flex: 1; min-width: 65px;
  display: flex; align-items: center; justify-content: space-between;
  padding: 6px 10px;
  border: 1px solid;
  border-radius: 8px;
  background: var(--bg);
}
.w-elem-name { font-size: 12px; color: var(--text-2); font-family: var(--font-cn); }
.w-elem-cnt  { font-size: 16px; font-weight: 700; font-family: var(--font-mono); }

.w-mode-row { display: flex; gap: 8px; }
.w-mode-chip {
  flex: 1;
  display: flex; align-items: center; justify-content: space-between;
  padding: 5px 10px;
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: 8px;
}
.w-mode-name { font-size: 11px; color: var(--text-3); }
.w-mode-cnt  { font-size: 14px; font-weight: 600; color: var(--text); }

/* ── 右侧列 ─────────────────────────────────────────────────── */
.w-right-col { display: flex; flex-direction: column; gap: 16px; }

/* 上升/中天卡片 */
.w-angles-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.w-angle-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px 16px;
}
.w-angle-asc { border-left: 3px solid var(--accent); }
.w-angle-mc  { border-left: 3px solid #a855f7; }
.w-angle-label { font-size: 10px; color: var(--text-3); text-transform: uppercase; letter-spacing: .05em; margin-bottom: 4px; }
.w-angle-sign  { font-size: 20px; font-weight: 700; color: var(--text); font-family: var(--font-cn); }
.w-angle-deg   { font-size: 12px; color: var(--text-2); font-family: var(--font-mono); margin-top: 2px; }
.w-angle-elem  { font-size: 11px; color: var(--text-3); margin-top: 2px; }

/* 行星位置表 */
.w-planets-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 16px;
}

.w-planet-table { width: 100%; border-collapse: collapse; font-family: var(--font-cn); }
.w-planet-table th {
  font-size: 10px; color: var(--text-3);
  text-align: left; padding: 4px 8px 8px;
  border-bottom: 1px solid var(--border);
  font-family: var(--font-ui); text-transform: uppercase;
}
.w-planet-table td { padding: 7px 8px; border-bottom: 1px solid var(--border); }
.w-planet-table tr:last-child td { border-bottom: none; }
.w-pt-name  { font-size: 14px; font-weight: 600; color: var(--text); }
.w-pt-sign  { font-size: 14px; }
.w-pt-deg   { font-size: 12px; font-family: var(--font-mono); color: var(--text-2); }
.w-pt-elem  { font-size: 12px; }
.w-pt-retro { font-size: 13px; color: #ef4444; font-weight: 700; text-align: center; }

/* 相位列表 */
.w-aspects-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 16px;
}
.w-aspect-list { display: flex; flex-direction: column; gap: 6px; }
.w-aspect-item {
  display: flex; align-items: center; gap: 8px;
  font-size: 13px; font-family: var(--font-cn);
}
.w-asp-dot  { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.w-asp-p1   { color: var(--text); font-weight: 600; min-width: 60px; }
.w-asp-type { font-size: 12px; font-weight: 600; min-width: 60px; }
.w-asp-p2   { color: var(--text); font-weight: 600; min-width: 60px; }
.w-asp-orb  { font-size: 11px; color: var(--text-3); font-family: var(--font-mono); margin-left: auto; }

/* 相位矩阵 */
.w-matrix-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 16px;
}
.w-matrix-scroll { overflow-x: auto; }
.w-matrix-table { border-collapse: collapse; font-size: 11px; font-family: var(--font-cn); }
.w-mth {
  padding: 4px 8px; text-align: center;
  font-size: 13px; font-weight: 600;
  background: var(--surface-2);
  border: 1px solid var(--border);
}
.w-mcell {
  padding: 3px 6px;
  text-align: center;
  font-size: 10px;
  border: 1px solid var(--border);
  min-width: 48px;
  height: 28px;
  white-space: nowrap;
  font-family: var(--font-cn);
}
.w-mcell-diag { background: var(--surface-2) !important; }

/* 空态 */
.w-empty {
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  padding: 60px 20px;
  gap: 12px;
  color: var(--text-3);
}
.w-empty-icon { font-size: 48px; opacity: 0.3; }
.w-empty p { font-size: 14px; font-family: var(--font-cn); }

/* ── 响应式 ─────────────────────────────────────────────────── */
@media (max-width: 1024px) {
  .w-result-grid { grid-template-columns: 1fr; }
  .w-chart-card  { position: static; }
  .w-svg-wrap svg { max-width: 340px; }
}
@media (max-width: 600px) {
  .w-form-grid { grid-template-columns: 1fr 1fr; }
  .w-angles-row { grid-template-columns: 1fr; }
  .w-svg-wrap svg { width: 100%; max-width: 320px; }
}

/* ── 太阳回归年盘区域 ──────────────────────────────────────────── */
.sr-section {
  margin-top: 28px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px;
}
.sr-heading {
  font-size: 16px; font-weight: 700; color: var(--text);
  font-family: var(--font-cn); margin: 0 0 6px;
}
.sr-tag {
  font-size: 11px; font-weight: 400; color: var(--text-3);
  font-family: var(--font-ui); margin-left: 8px;
}
.sr-desc {
  font-size: 12px; color: var(--text-3); font-family: var(--font-cn);
  margin: 0 0 16px; line-height: 1.6;
}
.sr-form {
  display: flex; flex-wrap: wrap; gap: 12px; align-items: flex-end; margin-bottom: 16px;
}
.sr-field { display: flex; flex-direction: column; gap: 5px; }
.sr-label { font-size: 11px; color: var(--text-3); font-weight: 500;
  letter-spacing: .04em; text-transform: uppercase; }
.sr-input {
  padding: 7px 10px; border: 1px solid var(--border);
  border-radius: 8px; background: var(--bg); color: var(--text);
  font-size: 13px; outline: none; transition: border-color .15s;
  font-family: var(--font-mono); width: 120px;
}
.sr-input:focus { border-color: var(--accent); }
.sr-btn {
  padding: 8px 18px; background: var(--accent-lt);
  color: var(--accent); border: 1px solid var(--accent);
  border-radius: 8px; font-size: 13px; font-weight: 600;
  cursor: pointer; transition: all .15s; white-space: nowrap;
}
.sr-btn:hover:not(:disabled) { background: var(--accent); color: #fff; }
.sr-btn:disabled { opacity: 0.6; cursor: not-allowed; }

/* SR 时刻标注 */
.sr-datetime {
  display: flex; flex-wrap: wrap; align-items: center; gap: 8px;
  background: var(--surface-2); border-radius: 8px;
  padding: 10px 14px; margin-bottom: 14px;
  font-size: 13px; color: var(--text-2); font-family: var(--font-cn);
}
.sr-dt-label { font-weight: 600; color: var(--text); }
.sr-dt-val   { font-family: var(--font-mono); color: var(--accent); font-size: 14px; font-weight: 700; }
.sr-dt-note  { font-size: 12px; color: var(--text-3); }

/* SR 上升/中天 */
.sr-angles   { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 16px; }
.sr-angle-card {
  background: var(--bg); border: 1px solid var(--border); border-radius: 8px;
  padding: 10px 14px; display: flex; flex-direction: column; gap: 4px;
}
.sr-al { font-size: 11px; color: var(--text-3); text-transform: uppercase; letter-spacing: .05em; }
.sr-av { font-size: 16px; font-weight: 700; color: var(--text); font-family: var(--font-cn); }

/* SR 对比表 */
.sr-compare-wrap { display: block; }
.sr-sub-title {
  font-size: 13px; font-weight: 700; color: var(--text);
  font-family: var(--font-cn); margin: 0 0 10px;
}
.sr-compare-scroll { overflow-x: auto; }
.sr-compare-table { width: 100%; border-collapse: collapse; font-size: 13px; font-family: var(--font-cn); }
.sr-th {
  padding: 6px 12px; background: var(--surface-2);
  border-bottom: 2px solid var(--border); font-size: 11px;
  font-family: var(--font-ui); text-transform: uppercase;
  color: var(--text-3); text-align: left;
}
.sr-td { padding: 7px 12px; border-bottom: 1px solid var(--border); }
.sr-row:last-child .sr-td { border-bottom: none; }
.sr-natal { color: var(--text-2); }
.sr-ret   { color: var(--text); font-weight: 500; }
.sr-r     { font-size: 11px; color: #ef4444; margin-left: 4px; font-weight: 700; }
.sr-moved { font-size: 11px; padding: 2px 6px; background: #fef9c3;
            color: #854d0e; border-radius: 4px; font-weight: 600; }
.sr-same  { font-size: 11px; color: var(--text-3); }
</style>
