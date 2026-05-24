<script setup lang="ts">
import { computed } from 'vue'
import type {
  BaziDayunFocusDetail,
  BaziDetails,
  BaziGejuYongshen,
  BaziLuckOverview,
  BaziRelationAnalyze,
  BaziShenshaItem,
  BaziTenGodUsageItem,
  CangganNayin,
  ShiShenAnalyze,
} from '@/composables/useZiweiBaziAnalysis'
import type { BaziMenuKey } from '@/composables/useZiweiNarrativeActions'

const TEN_STEMS = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
const PILLAR_KEYS = ['year', 'month', 'day', 'hour'] as const
const PILLAR_LABELS = ['年', '月', '日', '时'] as const

const props = defineProps<{
  activeMenu: BaziMenuKey
  menuItems: Record<BaziMenuKey, string>
  baziCopyDone: boolean
  baziDetails: BaziDetails | null
  shiShenAnalyze: ShiShenAnalyze | null
  cangganNayin: CangganNayin | null
  baziShenshaList: BaziShenshaItem[]
  baziRelationAnalyze: BaziRelationAnalyze
  baziGejuYongshen: BaziGejuYongshen | null
  baziLuckOverview: BaziLuckOverview
  baziDayunFocusDetail: BaziDayunFocusDetail | null
  baziRelatedLiuyueMap: Record<number, number>
  baziFocusedDayunSihuaStars: string[]
  baziTenGodUsage: BaziTenGodUsageItem[]
  baziWuxingCount: (element: string) => number
}>()

const menuEntries = computed(() => Object.entries(props.menuItems) as Array<[BaziMenuKey, string]>)

const emit = defineEmits<{
  (e: 'update:activeMenu', value: BaziMenuKey): void
  (e: 'copy-section'): void
  (e: 'set-dayun-focus', value: number): void
}>()

function getPillarLabel(key: string) {
  const index = PILLAR_KEYS.indexOf(key as (typeof PILLAR_KEYS)[number])
  return index >= 0 ? PILLAR_LABELS[index] : key
}
</script>

<template>
  <div v-if="baziDetails" class="bazi-detail-section card">
    <div class="bazi-head">
      <h3 class="section-title">四柱八字详情</h3>
    </div>

    <div class="bazi-menu-nav">
      <button
        v-for="([key, label]) in menuEntries"
        :key="key"
        :class="['bazi-menu-btn', { active: activeMenu === key }]"
        @click="emit('update:activeMenu', key)"
      >
        {{ label }}
      </button>
      <button class="bazi-copy-btn" @click="emit('copy-section')">
        {{ baziCopyDone ? '✓ 已复制' : '复制本节摘要' }}
      </button>
    </div>

    <div class="bazi-content-panels">
      <div v-if="activeMenu === 'shengchen'" class="bazi-panel">
        <div class="bazi-info-grid">
          <div class="bazi-info-item">
            <span class="bazi-label">出生日期</span>
            <span class="bazi-value">{{ baziDetails.birth_solar }}</span>
          </div>
          <div class="bazi-info-item">
            <span class="bazi-label">农历日期</span>
            <span class="bazi-value">
              {{ baziDetails.lunar?.lunar_year }}年{{ baziDetails.lunar?.is_leap_month ? '闰' : '' }}{{ baziDetails.lunar?.lunar_month }}月{{ baziDetails.lunar?.lunar_day }}日
            </span>
          </div>
          <div class="bazi-info-item">
            <span class="bazi-label">出生时刻</span>
            <span class="bazi-value">{{ baziDetails.lunar?.hour_branch }}时</span>
          </div>
          <div class="bazi-info-item">
            <span class="bazi-label">性别</span>
            <span class="bazi-value">{{ baziDetails.gender }}</span>
          </div>
          <div v-if="baziDetails.true_solar_time" class="bazi-info-item">
            <span class="bazi-label">真太阳时</span>
            <span class="bazi-value">{{ baziDetails.true_solar_time }}</span>
          </div>
        </div>
      </div>

      <div v-if="activeMenu === 'sizhu'" class="bazi-panel">
        <div class="bazi-grid">
          <div class="bazi-col">
            <div class="bazi-col-header">年柱</div>
            <div class="bazi-item">
              <div class="bazi-gz" title="天干">
                <span class="bazi-char">{{ baziDetails.year.stem }}</span>
                <span v-if="baziDetails.year.stemInfo" class="bazi-meaning">
                  {{ baziDetails.year.stemInfo.element }}·{{ baziDetails.year.stemInfo.yin_yang }}
                </span>
              </div>
              <div class="bazi-gz" title="地支">
                <span class="bazi-char">{{ baziDetails.year.branch }}</span>
                <span v-if="baziDetails.year.branchInfo" class="bazi-meaning">
                  {{ baziDetails.year.branchInfo.zodiac }}·{{ baziDetails.year.branchInfo.element }}
                </span>
              </div>
            </div>
            <div v-if="baziDetails.year.stemInfo || baziDetails.year.branchInfo" class="bazi-meaning-text">
              <p v-if="baziDetails.year.stemInfo" class="bazi-meaning-line">
                <b>{{ baziDetails.year.stem }}</b>：{{ baziDetails.year.stemInfo.meaning }}
              </p>
              <p v-if="baziDetails.year.branchInfo" class="bazi-meaning-line">
                <b>{{ baziDetails.year.branch }}</b>：{{ baziDetails.year.branchInfo.meaning }}
              </p>
            </div>
          </div>

          <div class="bazi-col">
            <div class="bazi-col-header">
              月柱
              <span v-if="baziDetails.month.isJieqi" class="bazi-jieqi-badge">节气</span>
            </div>
            <div class="bazi-item">
              <div class="bazi-gz" title="天干">
                <span class="bazi-char">{{ baziDetails.month.stem }}</span>
                <span v-if="baziDetails.month.stemInfo" class="bazi-meaning">
                  {{ baziDetails.month.stemInfo.element }}·{{ baziDetails.month.stemInfo.yin_yang }}
                </span>
              </div>
              <div class="bazi-gz" title="地支">
                <span class="bazi-char">{{ baziDetails.month.branch }}</span>
                <span v-if="baziDetails.month.branchInfo" class="bazi-meaning">
                  {{ baziDetails.month.branchInfo.zodiac }}·{{ baziDetails.month.branchInfo.element }}
                </span>
              </div>
            </div>
            <div v-if="baziDetails.month.stemInfo || baziDetails.month.branchInfo" class="bazi-meaning-text">
              <p v-if="baziDetails.month.stemInfo" class="bazi-meaning-line">
                <b>{{ baziDetails.month.stem }}</b>：{{ baziDetails.month.stemInfo.meaning }}
              </p>
              <p v-if="baziDetails.month.branchInfo" class="bazi-meaning-line">
                <b>{{ baziDetails.month.branch }}</b>：{{ baziDetails.month.branchInfo.meaning }}
              </p>
            </div>
          </div>

          <div class="bazi-col">
            <div class="bazi-col-header">日柱</div>
            <div class="bazi-item">
              <div class="bazi-gz" title="天干">
                <span class="bazi-char">{{ baziDetails.day.stem }}</span>
                <span v-if="baziDetails.day.stemInfo" class="bazi-meaning">
                  {{ baziDetails.day.stemInfo.element }}·{{ baziDetails.day.stemInfo.yin_yang }}
                </span>
              </div>
              <div class="bazi-gz" title="地支">
                <span class="bazi-char">{{ baziDetails.day.branch }}</span>
                <span v-if="baziDetails.day.branchInfo" class="bazi-meaning">
                  {{ baziDetails.day.branchInfo.zodiac }}·{{ baziDetails.day.branchInfo.element }}
                </span>
              </div>
            </div>
            <div v-if="baziDetails.day.stemInfo || baziDetails.day.branchInfo" class="bazi-meaning-text">
              <p v-if="baziDetails.day.stemInfo" class="bazi-meaning-line">
                <b>{{ baziDetails.day.stem }}</b>：{{ baziDetails.day.stemInfo.meaning }}
              </p>
              <p v-if="baziDetails.day.branchInfo" class="bazi-meaning-line">
                <b>{{ baziDetails.day.branch }}</b>：{{ baziDetails.day.branchInfo.meaning }}
              </p>
            </div>
          </div>

          <div class="bazi-col">
            <div class="bazi-col-header">时柱</div>
            <div class="bazi-item">
              <div class="bazi-gz" title="天干">
                <span class="bazi-char">{{ baziDetails.hour.stem }}</span>
                <span v-if="baziDetails.hour.stemInfo" class="bazi-meaning">
                  {{ baziDetails.hour.stemInfo.element }}·{{ baziDetails.hour.stemInfo.yin_yang }}
                </span>
              </div>
              <div class="bazi-gz" title="地支">
                <span class="bazi-char">{{ baziDetails.hour.branch }}</span>
                <span v-if="baziDetails.hour.branchInfo" class="bazi-meaning">
                  {{ baziDetails.hour.branchInfo.zodiac }}·{{ baziDetails.hour.branchInfo.element }}
                </span>
              </div>
            </div>
            <div v-if="baziDetails.hour.stemInfo || baziDetails.hour.branchInfo" class="bazi-meaning-text">
              <p v-if="baziDetails.hour.stemInfo" class="bazi-meaning-line">
                <b>{{ baziDetails.hour.stem }}</b>：{{ baziDetails.hour.stemInfo.meaning }}
              </p>
              <p v-if="baziDetails.hour.branchInfo" class="bazi-meaning-line">
                <b>{{ baziDetails.hour.branch }}</b>：{{ baziDetails.hour.branchInfo.meaning }}
              </p>
            </div>
          </div>
        </div>
      </div>

      <div v-if="activeMenu === 'ribuzhu' && shiShenAnalyze" class="bazi-panel">
        <div class="bazi-daymaster">
          <h5 class="sec-label">日主（日元）</h5>
          <div class="bazi-dm-info">
            <div class="bazi-dm-stem">
              <span class="bazi-dm-char">{{ shiShenAnalyze.dayMaster }}</span>
              <span class="bazi-dm-text">日主</span>
            </div>
            <div class="bazi-dm-desc">{{ baziDetails?.day?.stemInfo?.meaning }}</div>
          </div>
          <h5 class="sec-label sec-label-gap">十神关系</h5>
          <div class="shishen-grid">
            <template v-for="stem in TEN_STEMS" :key="stem">
              <div v-if="shiShenAnalyze.relations[stem]" class="shishen-card">
                <span class="shishen-stem">{{ stem }}</span>
                <span class="shishen-relation">{{ shiShenAnalyze.relations[stem] }}</span>
              </div>
            </template>
          </div>
        </div>
      </div>

      <div v-if="activeMenu === 'wuxing'" class="bazi-panel">
        <div class="bazi-wuxing-summary">
          <h5 class="sec-label">五行分布</h5>
          <div class="bazi-wuxing-grid">
            <div
              v-for="element in ['木', '火', '土', '金', '水']"
              :key="element"
              class="bazi-wx-item"
              :class="{ 'bazi-wx-active': baziWuxingCount(element) > 0 }"
            >
              <span class="bazi-wx-name">{{ element }}</span>
              <span class="bazi-wx-count">{{ baziWuxingCount(element) }}</span>
            </div>
          </div>
        </div>
      </div>

      <div v-if="activeMenu === 'canggan' && cangganNayin" class="bazi-panel">
        <div class="canggan-grid">
          <div v-for="(item, key) in cangganNayin" :key="key" class="canggan-col">
            <div class="canggan-header">{{ getPillarLabel(String(key)) }}柱</div>
            <div class="canggan-item">
              <div v-if="item.canggan" class="canggan-cg">
                <span class="canggan-label">藏干</span>
                <span class="canggan-main">{{ item.canggan.main }}</span>
                <span v-if="item.canggan.aux1" class="canggan-aux">{{ item.canggan.aux1 }}</span>
                <span v-if="item.canggan.aux2" class="canggan-aux">{{ item.canggan.aux2 }}</span>
              </div>
              <div v-if="item.nayin" class="canggan-ny">
                <span class="canggan-label">纳音</span>
                <span class="canggan-value">{{ item.nayin }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="activeMenu === 'shenshai'" class="bazi-panel">
        <h5 class="sec-label">神煞与定位</h5>
        <div v-if="baziShenshaList.length" class="bazi-simple-list">
          <div v-for="item in baziShenshaList" :key="item.name + item.reason" class="bazi-simple-card">
            <div class="bsc-head">
              <span class="bsc-name">{{ item.name }}</span>
              <span :class="['bsc-badge', item.level === '吉' ? 'ok' : item.level === '中' ? 'mid' : 'warn']">{{ item.level }}</span>
            </div>
            <p class="bsc-sub">落点：{{ item.hit.join('、') }}</p>
            <p class="bsc-text">{{ item.reason }}</p>
          </div>
        </div>
        <p v-else class="muted">当前命盘未检出显著神煞组合。</p>
      </div>

      <div v-if="activeMenu === 'chonghehexpo'" class="bazi-panel">
        <h5 class="sec-label">干支关系分析</h5>
        <div class="bazi-rel-wrap">
          <div class="bazi-rel-col">
            <h6 class="bazi-mini-title">地支关系</h6>
            <div v-if="baziRelationAnalyze.branchRelations.length" class="bazi-simple-list">
              <div v-for="(r, idx) in baziRelationAnalyze.branchRelations" :key="'b' + idx" class="bazi-rel-item">
                <span class="bri-type">{{ r.type }}</span>
                <span class="bri-pair">{{ r.a }} × {{ r.b }}</span>
                <span class="bri-pillars">{{ r.pillars }}</span>
              </div>
            </div>
            <p v-else class="muted">地支关系以平和为主。</p>
          </div>
          <div class="bazi-rel-col">
            <h6 class="bazi-mini-title">天干关系</h6>
            <div v-if="baziRelationAnalyze.stemRelations.length" class="bazi-simple-list">
              <div v-for="(r, idx) in baziRelationAnalyze.stemRelations" :key="'s' + idx" class="bazi-rel-item">
                <span class="bri-type">{{ r.type }}</span>
                <span class="bri-pair">{{ r.a }} × {{ r.b }}</span>
                <span class="bri-pillars">{{ r.pillars }}</span>
              </div>
            </div>
            <p v-else class="muted">天干关系以平衡为主。</p>
          </div>
        </div>
      </div>

      <div v-if="activeMenu === 'geju'" class="bazi-panel">
        <h5 class="sec-label">格局判定与用神</h5>
        <div v-if="baziGejuYongshen" class="bazi-simple-card">
          <div class="bsc-head">
            <span class="bsc-name">{{ baziGejuYongshen.gejuName }}</span>
            <span class="bsc-badge ok">主导：{{ baziGejuYongshen.dominant }}</span>
          </div>
          <p class="bsc-text">{{ baziGejuYongshen.rationale }}</p>
          <div class="bazi-tags-row">
            <span class="btr-label">宜：</span>
            <span v-for="x in baziGejuYongshen.favor" :key="'f' + x" class="btr-tag good">{{ x }}</span>
          </div>
          <div class="bazi-tags-row">
            <span class="btr-label">慎：</span>
            <span v-for="x in baziGejuYongshen.avoid" :key="'a' + x" class="btr-tag bad">{{ x }}</span>
          </div>
        </div>
        <p v-else class="muted">暂无足够数据进行格局判定。</p>
      </div>

      <div v-if="activeMenu === 'dayun'" class="bazi-panel">
        <h5 class="sec-label">大运 / 流年 / 流月</h5>
        <div class="bazi-simple-card">
          <p class="bsc-sub">当前大运：<b>{{ baziLuckOverview.currentDayun || '未定位' }}</b></p>
          <p class="bsc-sub">流年：<b>{{ baziLuckOverview.liunianYear || '-' }}</b> {{ baziLuckOverview.liunianGz || '' }}</p>
        </div>
        <div v-if="baziLuckOverview.dayun.length" class="bazi-timeline">
          <div
            v-for="d in baziLuckOverview.dayun"
            :key="d.idx + d.ganzhi"
            :class="['btl-item', { cur: d.isCurrent, active: baziDayunFocusDetail?.idx === d.idx }]"
            @click="emit('set-dayun-focus', d.rawIdx)"
          >
            <div class="btl-gz">{{ d.ganzhi }}</div>
            <div class="btl-age">{{ d.startAge }}-{{ d.endAge }}岁</div>
            <div class="btl-year">{{ d.startYear }}年起</div>
          </div>
        </div>

        <div v-if="baziDayunFocusDetail" class="bazi-simple-card bazi-dayun-detail">
          <div class="bsc-head">
            <span class="bsc-name">第{{ baziDayunFocusDetail.idx }}步大运 · {{ baziDayunFocusDetail.ganzhi }}</span>
            <span class="bsc-badge mid">{{ baziDayunFocusDetail.startAge }}-{{ baziDayunFocusDetail.endAge }}岁</span>
          </div>
          <p class="bsc-sub">起始年份：{{ baziDayunFocusDetail.startYear || '未知' }}<span v-if="baziDayunFocusDetail.tenGod">｜十神：{{ baziDayunFocusDetail.tenGod }}</span></p>
          <p v-if="baziDayunFocusDetail.narrative" class="bsc-text">{{ baziDayunFocusDetail.narrative }}</p>
          <p v-else class="bsc-text">此步大运建议结合流年与流月同步观察，重点关注阶段性机会与风险管理。</p>
        </div>

        <div v-if="baziLuckOverview.liuyue.length" class="bazi-month-grid">
          <div
            v-for="m in baziLuckOverview.liuyue"
            :key="m.month"
            :class="['bmg-item', { related: (baziRelatedLiuyueMap[m.month] || 0) > 0 }]"
          >
            <span class="bmg-month">{{ m.monthName }}</span>
            <span class="bmg-gz">{{ m.monthGz || '-' }}</span>
            <span class="bmg-palace">{{ m.palace || '-' }}</span>
            <span v-if="(baziRelatedLiuyueMap[m.month] || 0) > 0" class="bmg-link">同星{{ baziRelatedLiuyueMap[m.month] }}个</span>
          </div>
        </div>
        <p v-if="baziFocusedDayunSihuaStars.length" class="bsc-sub bazi-sihua-link-tip">
          联动依据：已高亮与该步大运四化同星的流月（{{ baziFocusedDayunSihuaStars.join('、') }}）。
        </p>
      </div>

      <div v-if="activeMenu === 'shishen'" class="bazi-panel">
        <h5 class="sec-label">十神宫位用法</h5>
        <div v-if="baziTenGodUsage.length" class="bazi-simple-list">
          <div v-for="item in baziTenGodUsage" :key="item.pillar" class="bazi-simple-card">
            <div class="bsc-head">
              <span class="bsc-name">{{ item.pillar }}</span>
              <span class="bsc-badge mid">{{ item.stem }} → {{ item.tenGod }}</span>
            </div>
            <p class="bsc-text">{{ item.interpretation }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.bazi-detail-section { margin: var(--sp-4) 0; }
.bazi-head { margin-bottom: var(--sp-3); }

.bazi-menu-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: var(--sp-4);
  padding-bottom: var(--sp-3);
  border-bottom: 1px solid var(--border);
}

.bazi-menu-btn {
  padding: 6px 12px;
  font-size: var(--fs-xs);
  font-family: var(--font-cn);
  background: var(--surface-2);
  color: var(--text-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.2s;
}

.bazi-menu-btn:hover { border-color: var(--accent); color: var(--accent); }
.bazi-menu-btn.active {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
  font-weight: 600;
}

.bazi-copy-btn {
  margin-left: auto;
  padding: 6px 12px;
  font-size: var(--fs-xs);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-md);
  background: var(--surface);
  color: var(--text-2);
  cursor: pointer;
  transition: all 0.2s;
}

.bazi-copy-btn:hover { border-color: var(--accent); color: var(--accent); }
.bazi-content-panels { min-height: 100px; }
.bazi-panel { animation: fadeIn 0.3s ease-in; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

.bazi-info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--sp-3);
}

@media (max-width: 480px) {
  .bazi-info-grid { grid-template-columns: 1fr; }
}

.bazi-info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: var(--sp-2);
  background: var(--surface-2);
  border-radius: var(--radius-sm);
}

.bazi-label { font-size: var(--fs-xs); font-weight: 700; color: var(--text-3); }
.bazi-value { font-size: var(--fs-sm); color: var(--text); font-family: var(--font-cn); }

.sec-label { font-size: var(--fs-sm); color: var(--text-3); margin-bottom: var(--sp-3); font-weight: 500; }
.sec-label-gap { margin-top: var(--sp-3); }

.bazi-daymaster { padding: var(--sp-3); }
.bazi-dm-info {
  display: flex;
  gap: var(--sp-3);
  align-items: center;
  padding: var(--sp-3);
  background: var(--surface-2);
  border-radius: var(--radius-sm);
  margin-bottom: var(--sp-3);
}

.bazi-dm-stem {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.bazi-dm-char { font-size: var(--fs-2xl); font-weight: 800; font-family: var(--font-cn); color: var(--accent); }
.bazi-dm-text { font-size: var(--fs-xs); color: var(--text-3); }
.bazi-dm-desc { font-size: var(--fs-sm); color: var(--text-2); }

.shishen-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  gap: var(--sp-2);
}

.shishen-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: var(--sp-2);
  background: var(--surface-2);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
}

.shishen-stem { font-size: var(--fs-lg); font-weight: 800; font-family: var(--font-cn); color: var(--accent); }
.shishen-relation { font-size: var(--fs-xs); color: var(--text-2); }

.canggan-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: var(--sp-3);
}

.canggan-col {
  padding: var(--sp-3);
  background: var(--surface-2);
  border-radius: var(--radius-sm);
}

.canggan-header { font-size: var(--fs-sm); font-weight: 700; margin-bottom: var(--sp-2); }
.canggan-item { display: flex; flex-direction: column; gap: var(--sp-2); }
.canggan-cg,
.canggan-ny {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px;
  background: var(--surface);
  border-radius: var(--radius-xs);
}

.canggan-label { font-size: var(--fs-xs); color: var(--text-3); font-weight: 700; }
.canggan-main {
  font-size: var(--fs-sm);
  font-weight: 700;
  font-family: var(--font-cn);
  color: var(--accent);
}

.canggan-aux { font-size: var(--fs-xs); color: var(--text-2); }
.canggan-value { font-size: var(--fs-sm); color: var(--text); }

.bazi-simple-list { display: grid; gap: var(--sp-2); }
.bazi-simple-card {
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: var(--sp-3);
}

.bsc-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-2);
  margin-bottom: 6px;
}

.bsc-name { font-size: var(--fs-sm); font-weight: 700; color: var(--text); }
.bsc-badge {
  font-size: var(--fs-xs);
  padding: 2px 8px;
  border-radius: 999px;
  font-weight: 700;
}

.bsc-badge.ok { background: rgba(22, 163, 74, 0.15); color: #166534; }
.bsc-badge.mid { background: rgba(217, 119, 6, 0.15); color: #92400e; }
.bsc-badge.warn { background: rgba(220, 38, 38, 0.15); color: #991b1b; }
.bsc-sub { font-size: var(--fs-xs); color: var(--text-3); margin: 0 0 6px; }
.bsc-text { margin: 0; font-size: var(--fs-sm); color: var(--text-2); line-height: 1.6; }

.bazi-rel-wrap {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--sp-3);
}

@media (max-width: 640px) {
  .bazi-rel-wrap { grid-template-columns: 1fr; }
}

.bazi-rel-col {
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: var(--sp-3);
}

.bazi-mini-title { margin: 0 0 var(--sp-2); font-size: var(--fs-sm); color: var(--text); }
.bazi-rel-item {
  display: grid;
  grid-template-columns: 60px 58px 1fr;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  border-bottom: 1px dashed var(--border);
}

.bazi-rel-item:last-child { border-bottom: none; }
.bri-type { font-size: var(--fs-xs); font-weight: 700; color: var(--accent); }
.bri-pair { font-size: var(--fs-sm); font-family: var(--font-cn); color: var(--text); }
.bri-pillars { font-size: var(--fs-xs); color: var(--text-3); }

.bazi-tags-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
}

.btr-label { font-size: var(--fs-xs); color: var(--text-3); }
.btr-tag {
  font-size: var(--fs-xs);
  border-radius: 999px;
  padding: 2px 8px;
  font-weight: 700;
}

.btr-tag.good { background: rgba(22, 163, 74, 0.15); color: #166534; }
.btr-tag.bad { background: rgba(220, 38, 38, 0.15); color: #991b1b; }

.bazi-timeline {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: var(--sp-2);
  margin-top: var(--sp-3);
}

.btl-item {
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface-2);
  padding: var(--sp-2);
  cursor: pointer;
}

.btl-item.cur {
  border-color: var(--accent);
  box-shadow: 0 0 0 1px rgba(217, 119, 6, 0.2);
}

.btl-item.active {
  border-color: #2563eb;
  box-shadow: 0 0 0 1px rgba(37, 99, 235, 0.2);
  background: linear-gradient(135deg, var(--surface-2) 0%, rgba(37, 99, 235, 0.08) 100%);
}

.btl-gz { font-size: var(--fs-md); font-weight: 800; font-family: var(--font-cn); color: var(--accent); }
.btl-age, .btl-year { font-size: var(--fs-xs); color: var(--text-3); }
.bazi-dayun-detail { margin-top: var(--sp-3); }

.bazi-month-grid {
  margin-top: var(--sp-3);
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(95px, 1fr));
  gap: var(--sp-2);
}

.bmg-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-xs);
  padding: 6px;
}

.bmg-item.related {
  border-color: #2563eb;
  box-shadow: 0 0 0 1px rgba(37, 99, 235, 0.2);
  background: linear-gradient(135deg, var(--surface) 0%, rgba(37, 99, 235, 0.08) 100%);
}

.bmg-month { font-size: var(--fs-xs); color: var(--text-3); }
.bmg-gz { font-size: var(--fs-sm); color: var(--text); font-family: var(--font-cn); }
.bmg-palace { font-size: var(--fs-xs); color: var(--accent); }
.bmg-link { margin-top: 2px; font-size: var(--fs-xs); color: #1d4ed8; font-weight: 700; }
.bazi-sihua-link-tip { margin-top: 8px; }

.bazi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: var(--sp-3);
  margin-bottom: var(--sp-4);
}

.bazi-col {
  padding: var(--sp-3);
  background: var(--surface-2);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
}

.bazi-col-header {
  font-size: var(--fs-sm);
  font-weight: 700;
  color: var(--text-2);
  margin-bottom: var(--sp-2);
  display: flex;
  align-items: center;
  gap: var(--sp-1);
}

.bazi-jieqi-badge {
  font-size: var(--fs-xs);
  padding: 1px 6px;
  background: var(--accent);
  color: #fff;
  border-radius: 999px;
  font-weight: 600;
}

.bazi-item {
  display: flex;
  gap: 4px;
  margin-bottom: var(--sp-2);
}

.bazi-gz {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: var(--sp-2);
  background: var(--surface);
  border-radius: var(--radius-xs);
}

.bazi-char {
  font-size: var(--fs-lg);
  font-weight: 800;
  font-family: var(--font-cn);
  color: var(--accent);
}

.bazi-meaning { font-size: var(--fs-xs); color: var(--text-3); line-height: 1; }
.bazi-meaning-text {
  font-size: var(--fs-xs);
  color: var(--text-2);
  padding-top: var(--sp-2);
  border-top: 1px solid var(--border);
}

.bazi-meaning-line { margin: 4px 0; line-height: 1.4; }
.bazi-meaning-line b { color: var(--accent); font-weight: 700; }

.bazi-wuxing-summary {
  padding: var(--sp-3);
  background: var(--surface-2);
  border-radius: var(--radius-sm);
}

.bazi-wuxing-grid {
  display: flex;
  gap: var(--sp-2);
  justify-content: space-around;
  margin-top: var(--sp-2);
}

.bazi-wx-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: var(--sp-2);
  background: var(--surface);
  border-radius: var(--radius-xs);
  border: 1px solid var(--border);
  opacity: 0.5;
  transition: all 0.2s;
}

.bazi-wx-item.bazi-wx-active {
  opacity: 1;
  border-color: var(--accent);
  background: linear-gradient(135deg, var(--surface) 0%, rgba(var(--accent-rgb), 0.05) 100%);
}

.bazi-wx-name {
  font-size: var(--fs-sm);
  font-weight: 700;
  font-family: var(--font-cn);
  color: var(--text);
}

.bazi-wx-count { font-size: var(--fs-lg); font-weight: 800; color: var(--accent); }
</style>
