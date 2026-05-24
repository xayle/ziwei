<script setup lang="ts">
import { onMounted, nextTick } from 'vue'
import { CANG_GAN, NAYIN_MAP, STEM_ELEMENT, stemColor } from '@/data/ganzhi'
import CityPicker from '@/components/CityPicker.vue'
import BaziEventSection from '@/components/bazi/BaziEventSection.vue'
import BaziSaveDialog from '@/components/bazi/BaziSaveDialog.vue'
import { useBaziForm } from '@/composables/useBaziForm'
import { useBaziComputation } from '@/composables/useBaziComputation'
import { useBaziAi } from '@/composables/useBaziAi'
import { useBaziResults } from '@/composables/useBaziResults'

// ── Composables ────────────────────────────────────────────────────────────
const {
  birthDt, lon, tz, gender, mode, solarTime, surname,
  initCity, cityName, showForm,
  syncFromProfile, onCityChange, gotoNameSuggest, gotoZeri, profile,
} = useBaziForm()

const {
  loading, error, result, savedCaseId,
  saveCaseName, saveCaseNotes, saveDialogOpen,
  saveCaseSaving, saveCaseError, saveCaseSuccess,
  doCalculate, openSaveDialog, closeSaveDialog,
  saveCurrentCase, resetSaveState, resetResult,
} = useBaziComputation({ birthDt, lon, tz, gender, mode, solarTime, cityName, initCity })

const {
  aiModule, aiLoading, aiError, aiStatus, aiDraft,
  AI_MODULE_OPTIONS, aiParagraphs,
  generateAiInterpretation, resetAiState,
} = useBaziAi(savedCaseId)

const {
  currentYear, dayunSelected, dayunItems, dayunActiveIdx,
  pillars, wuxingBars, RADAR_ANGLES, RADAR_CX, RADAR_CY, RADAR_R,
  radarBg, radarBgHalf, radarPoints, radarLabels,
  tgColor, wxColor, wxZh, scoreColor,
  dayMasterDesc, baziSummaryFallback, currentDayunDesc,
  overviewGuideCards, overviewReadingSteps, overviewTerms, rawResultJson,
} = useBaziResults(result)

// ── 生命周期 ──────────────────────────────────────────────────────────────
onMounted(() => {
  syncFromProfile()
  if (profile.saved) {
    showForm.value = false
    nextTick(() => doCalculate())
  }
})

/** 根据用神推荐改名 */
function gotoNameSuggestWithResult() {
  gotoNameSuggest(result.value?.yongshen?.favor ?? [])
}

/** 重置整个表单（联动 computation + AI 状态） */
function resetForm() {
  syncFromProfile()
  resetResult()
  resetSaveState()
  resetAiState()
  saveCaseName.value  = ''
  saveCaseNotes.value = ''
}
</script>
<template>
  <div class="wrap bazi-view">
    <h1 class="page-title">八字排盘</h1>

    <!-- 表单折叠控制栏 -->
    <div class="form-toggle-bar">
      <button class="btn-toggle-form" @click="showForm = !showForm">
        {{ showForm ? '▴ 收起参数' : '▾ 修改参数' }}
      </button>
      <span v-if="!showForm && result" class="current-params">
        {{ birthDt }} · {{ initCity }} · {{ gender === 'male' ? '男' : gender === 'female' ? '女' : '不指定' }}
      </span>
    </div>

    <!-- 输入表单 -->
    <section v-show="showForm" class="card form-card">
      <div class="form-grid">
        <div class="form-row">
          <label>出生时间</label>
          <input type="datetime-local" v-model="birthDt" />
        </div>
        <div class="form-row">
          <CityPicker v-model="lon" :initial-city="initCity" @city-change="onCityChange" />
        </div>
        <div class="form-row">
          <label>时区</label>
          <select v-model="tz">
            <option value="Asia/Shanghai">Asia/Shanghai（东八区）</option>
            <option value="Asia/Tokyo">Asia/Tokyo（东九区）</option>
            <option value="UTC">UTC</option>
          </select>
        </div>
        <div class="form-row">
          <label>性别</label>
          <label class="radio-opt"><input type="radio" v-model="gender" value="male" />男</label>
          <label class="radio-opt"><input type="radio" v-model="gender" value="female" />女</label>
          <label class="radio-opt"><input type="radio" v-model="gender" value="" />不指定</label>
        </div>
        <div class="form-row">
          <label>计算模式</label>
          <label class="radio-opt"><input type="radio" v-model="mode" value="dual" />双历（节气校正）</label>
          <label class="radio-opt"><input type="radio" v-model="mode" value="single" />单历</label>
        </div>
        <div class="form-row">
          <label>真太阳时</label>
          <label class="check-opt"><input type="checkbox" v-model="solarTime" />启用真太阳时修正</label>
        </div>
        <div class="form-row">
          <label>姓氏（选填）</label>
          <input v-model="surname" placeholder="如：张" maxlength="3" />
          <span class="hint">用于改名建议联动</span>
        </div>
      </div>
      <div class="form-actions">
        <button class="btn-primary" :disabled="loading" @click="doCalculate">
          {{ loading ? '排盘中…' : '✦ 开始排盘' }}
        </button>
        <button class="btn-sec" @click="resetForm">重置</button>
        <span v-if="error" class="error-msg">{{ error }}</span>
      </div>
    </section>

    <!-- 错误提示（表单折叠时也显示） -->
    <div v-if="error && !showForm" class="error-msg" style="padding: 8px 0">{{ error }}</div>

    <!-- 骨架屏 -->
    <div v-if="loading" class="skeleton-wrap">
      <div class="skel-line" style="width:60%"></div>
      <div class="skel-line" style="width:80%"></div>
      <div class="skel-box"></div>
    </div>

    <!-- 结果区 -->
    <template v-if="result">
      <!-- 四柱 -->
      <section class="card pillars-card">
        <h2 class="card-title">四柱命盘</h2>
        <!-- 新版四柱表格 -->
        <div class="pillars-tbl-wrap" v-if="result.pillars_primary">
          <table class="pillars-tbl">
            <thead>
              <tr>
                <th class="row-lbl-th"></th>
                <th>年柱</th>
                <th>月柱</th>
                <th class="day-col-th">日柱</th>
                <th>时柱</th>
              </tr>
            </thead>
            <tbody>
              <!-- 十神行 -->
              <tr>
                <td class="row-lbl">十神</td>
                <td v-for="col in (['year','month','day','hour'] as const)" :key="'ss-'+col">
                  <span class="tg-chip"
                    :class="{ 'tg-day': col==='day' }"
                    :style="col==='day' ? {} : { color: tgColor((result.ten_gods as any)?.[col] ?? '') }">
                    {{ col === 'day' ? '日主' : ((result.ten_gods as any)?.[col] ?? '') }}
                  </span>
                </td>
              </tr>
              <!-- 天干行 -->
              <tr>
                <td class="row-lbl">天干</td>
                <td v-for="col in (['year','month','day','hour'] as const)" :key="'stem-'+col"
                    :class="{ 'day-col-th': col==='day' }">
                  <span class="gz-char"
                    :style="{ color: stemColor((result.pillars_primary as any)[col].stem) }">
                    {{ (result.pillars_primary as any)[col].stem }}
                  </span>
                </td>
              </tr>
              <!-- 地支行 -->
              <tr>
                <td class="row-lbl">地支</td>
                <td v-for="col in (['year','month','day','hour'] as const)" :key="'br-'+col"
                    :class="{ 'day-col-th': col==='day' }">
                  <span class="gz-char gz-branch">
                    {{ (result.pillars_primary as any)[col].branch }}
                  </span>
                </td>
              </tr>
              <!-- 藏干行 -->
              <tr>
                <td class="row-lbl">藏干</td>
                <td v-for="col in (['year','month','day','hour'] as const)" :key="'cg-'+col">
                  <span v-for="s in (CANG_GAN[(result.pillars_primary as any)[col].branch] ?? [])"
                        :key="s" class="cang-stem"
                        :style="{ color: stemColor(s) }">{{ s }}</span>
                </td>
              </tr>
              <!-- 纳音行 -->
              <tr>
                <td class="row-lbl">纳音</td>
                <td v-for="col in (['year','month','day','hour'] as const)" :key="'ny-'+col">
                  <span class="nayin-text">
                    {{ NAYIN_MAP[(result.pillars_primary as any)[col].stem + (result.pillars_primary as any)[col].branch] ?? '' }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="pillars-meta">
          <span v-if="result.methods?.solar_date" class="meta-item">
            阳历 <b>{{ result.methods.solar_date }}</b>
          </span>
          <span v-if="result.methods?.lunar_date" class="meta-item">
            农历 <b>{{ result.methods.lunar_date }}</b>
          </span>
          <span v-if="result.start_dayun_age != null" class="meta-item">
            起运 <b>{{ result.start_dayun_age }} 岁</b>
          </span>
        </div>
        <!-- 命盘速读：日主·强弱·格局·用神 -->
        <div v-if="result.day_master_strength || result.geju || result.yongshen" class="pillars-qbar">
          <div v-if="result.pillars_primary" class="pqb-item">
            <span class="pqb-key">日主</span>
            <span class="pqb-gz" :style="{ color: stemColor((result.pillars_primary as any).day.stem) }">
              {{ (result.pillars_primary as any).day.stem }}{{ (result.pillars_primary as any).day.branch }}
            </span>
            <span class="pqb-wx">（{{ (STEM_ELEMENT as any)[(result.pillars_primary as any).day.stem] ?? '' }}行）</span>
          </div>
          <span v-if="result.day_master_strength" class="pqb-dot">·</span>
          <div v-if="result.day_master_strength" class="pqb-item">
            <span class="pqb-key">强弱</span>
            <span class="pqb-main">{{ result.day_master_strength.tier }}</span>
          </div>
          <span v-if="result.geju" class="pqb-dot">·</span>
          <div v-if="result.geju" class="pqb-item">
            <span class="pqb-key">格局</span>
            <span class="pqb-main">{{ result.geju.geju_name }}</span>
            <span v-if="result.geju.geju_level" class="pqb-badge">{{ result.geju.geju_level }}</span>
          </div>
          <span v-if="result.yongshen?.favor?.length" class="pqb-dot">·</span>
          <div v-if="result.yongshen?.favor?.length" class="pqb-item">
            <span class="pqb-key">用神</span>
            <span v-for="f in result.yongshen.favor" :key="'pf'+f" class="pqb-favor-tag">{{ wxZh(f) }}</span>
            <span v-if="result.yongshen.avoid?.length" class="pqb-avoid-sep">忌</span>
            <span v-for="a in (result.yongshen.avoid ?? []).slice(0, 2)" :key="'pa'+a" class="pqb-avoid-tag">{{ wxZh(a) }}</span>
          </div>
        </div>
        <div class="case-actions-row">
          <button class="btn-case-save" @click="openSaveDialog">
            {{ savedCaseId ? '另存到案例库' : '保存到案例库' }}
          </button>
          <span v-if="savedCaseId" class="case-save-pill case-save-pill-success">
            已保存 · {{ savedCaseId }}
          </span>
          <span v-else class="case-save-pill">保存后生成深度解读</span>
          <span v-if="saveCaseSuccess" class="case-save-msg">{{ saveCaseSuccess }}</span>
        </div>
        <!-- 推荐改名按钮 -->
        <div v-if="result.yongshen?.favor?.length" class="suggest-name-row">
          <button class="btn-suggest-name" @click="gotoNameSuggestWithResult">
            ✦ 根据用神推荐改名
          </button>
          <span class="hint">用神：{{ result.yongshen.favor.map(wxZh).join('、') }}</span>
        </div>
      </section>

      <!-- ── 命盘三核 ── -->
      <div v-if="result.day_master_strength || result.geju || result.yongshen" class="ov-core-trio ov-core-full">
        <div v-if="result.day_master_strength" class="ov-trio-card">
          <div class="ov-trio-kv">
            <span class="ov-trio-label">日元强弱</span>
            <span class="ov-trio-main">{{ result.day_master_strength.tier }}</span>
            <span v-if="result.day_master_strength.score != null" class="ov-trio-score">{{ result.day_master_strength.score.toFixed(1) }} 分</span>
          </div>
          <p class="ov-trio-hint" v-if="dayMasterDesc">{{ dayMasterDesc }}</p>
          <p class="ov-trio-hint" v-else>日主强弱决定用神与忌神的取舍方向，是命理分析的核心基础。</p>
        </div>
        <div v-if="result.geju" class="ov-trio-card">
          <div class="ov-trio-kv">
            <span class="ov-trio-label">命盘格局</span>
            <span class="ov-trio-main">
              {{ result.geju.geju_name }}
              <span v-if="result.geju.geju_level" class="ov-trio-subbadge">{{ result.geju.geju_level }}</span>
              <span v-if="result.geju.is_broken" class="ov-trio-broken">破格</span>
            </span>
          </div>
          <p class="ov-trio-hint" v-if="result.geju.geju_detail">{{ result.geju.geju_detail.slice(0, 80) }}{{ result.geju.geju_detail.length > 80 ? '…' : '' }}</p>
          <p class="ov-trio-hint" v-else-if="result.geju.interpretation_text">{{ result.geju.interpretation_text.slice(0, 80) }}…</p>
          <p class="ov-trio-hint" v-else>格局决定命盘整体气质，是命理分析的骨干结构。</p>
        </div>
        <div v-if="result.yongshen" class="ov-trio-card">
          <div class="ov-trio-kv">
            <span class="ov-trio-label">用神 / 忌神</span>
            <div class="ov-trio-yg">
              <span v-for="t in result.yongshen.favor" :key="'tf'+t" class="ov-trio-favor">{{ wxZh(t) }}</span>
              <span v-if="result.yongshen.avoid?.length" class="ov-trio-avoidlbl">忌</span>
              <span v-for="t in result.yongshen.avoid" :key="'ta'+t" class="ov-trio-avoid">{{ wxZh(t) }}</span>
            </div>
          </div>
          <p class="ov-trio-hint" v-if="result.yongshen.rationale">{{ result.yongshen.rationale.slice(0, 80) }}{{ result.yongshen.rationale.length > 80 ? '…' : '' }}</p>
          <p class="ov-trio-hint" v-else>用神五行应尽量接触；忌神五行对应的人事物应适度规避。</p>
        </div>
      </div>

      <!-- ── 命局总评 ── -->
      <div v-if="baziSummaryFallback" class="bazi-summary-block">
        <div class="summary-label">命局综合总评</div>
        <p class="bazi-summary-text">{{ baziSummaryFallback }}</p>
      </div>

      <!-- ── 大运 ── -->
      <section class="card section-inline">
        <h2 class="card-title">大运</h2>
        <div class="dy-header">
          <span v-if="result.start_dayun_age != null">起运 <b>{{ result.start_dayun_age }} 岁</b></span>
          <span v-if="result.dayun?.direction" class="dy-dir">
            {{ result.dayun.direction === 'forward' ? '顺运' : '逆运' }}
          </span>
          <span v-if="dayunActiveIdx >= 0" class="dy-cur-lbl">
            当前大运：<b>{{ (dayunItems[dayunActiveIdx].stem ?? '') + (dayunItems[dayunActiveIdx].branch ?? '') }}</b>
            &nbsp;<span class="dy-cur-age">（{{ dayunItems[dayunActiveIdx].start_age ?? '?' }}–{{ (dayunItems[dayunActiveIdx].start_age ?? 0) + 9 }}岁）</span>
          </span>
        </div>
        <div v-if="dayunItems.length" class="dy-timeline-wrap">
          <div class="dy-track">
            <div v-for="(c, i) in dayunItems" :key="i"
                 :class="['dy-step',
                   { 'dy-cur':  i === dayunActiveIdx },
                   { 'dy-past': c.start_year != null && (c.start_year + 10) <= currentYear },
                   { 'dy-sel':  dayunSelected === i },
                 ]"
                 @click="dayunSelected = dayunSelected === i ? -1 : i">
              <div class="dy-dot-row">
                <div class="dy-line-l" v-if="i > 0"></div>
                <div class="dy-dot">
                  <div v-if="i === dayunActiveIdx" class="dy-dot-ring"></div>
                </div>
                <div class="dy-line-r" v-if="i < dayunItems.length - 1"></div>
              </div>
              <div class="dy-card">
                <div class="dy-gz">{{ (c.stem ?? '') + (c.branch ?? '') }}</div>
                <div v-if="c.ten_god" class="dy-tg-chip"
                     :style="{ background: tgColor(c.ten_god) + '22', color: tgColor(c.ten_god), borderColor: tgColor(c.ten_god) + '55' }">
                  {{ c.ten_god }}
                </div>
                <div class="dy-age-range">{{ c.start_age ?? '?' }}–{{ (c.start_age ?? 0) + 9 }}岁</div>
                <div class="dy-yr">{{ c.start_year ?? '' }}年</div>
              </div>
            </div>
          </div>
        </div>
        <!-- 当前大运解读摘要 -->
        <div v-if="dayunActiveIdx >= 0 && dayunItems[dayunActiveIdx]" class="dy-cur-summary">
          <div class="dy-cur-summary-title">当前大运解读</div>
          <p v-if="currentDayunDesc" class="dy-cur-narrative">{{ currentDayunDesc }}</p>
          <p v-else class="dy-cur-narrative muted">点击时间轴中的大运节点可展开详情。</p>
          <div v-if="dayunItems[dayunActiveIdx].wealth_hint || dayunItems[dayunActiveIdx].health_hint || dayunItems[dayunActiveIdx].love_hint"
               class="dayun-hints">
            <span v-if="dayunItems[dayunActiveIdx].wealth_hint" class="dh-tag dh-wealth">财运：{{ dayunItems[dayunActiveIdx].wealth_hint }}</span>
            <span v-if="dayunItems[dayunActiveIdx].health_hint" class="dh-tag dh-health">健康：{{ dayunItems[dayunActiveIdx].health_hint }}</span>
            <span v-if="dayunItems[dayunActiveIdx].love_hint"   class="dh-tag dh-love">感情：{{ dayunItems[dayunActiveIdx].love_hint }}</span>
          </div>
        </div>
        <transition name="dy-expand">
          <div v-if="dayunSelected >= 0 && dayunItems[dayunSelected]" class="dy-detail-card">
            <div class="dy-detail-header">
              <span class="dy-detail-gz">
                {{ (dayunItems[dayunSelected].stem ?? '') + (dayunItems[dayunSelected].branch ?? '') }}
              </span>
              <span v-if="dayunItems[dayunSelected].ten_god" class="tg-chip"
                    :style="{ background: tgColor(dayunItems[dayunSelected].ten_god!) + '22', color: tgColor(dayunItems[dayunSelected].ten_god!) }">
                {{ dayunItems[dayunSelected].ten_god }}
              </span>
              <span class="dy-detail-period">
                {{ dayunItems[dayunSelected].start_age ?? '?' }}–{{ (dayunItems[dayunSelected].start_age ?? 0) + 9 }}岁
                &nbsp;({{ dayunItems[dayunSelected].start_year ?? '' }}–{{ (dayunItems[dayunSelected].start_year ?? 0) + 9 }}年)
              </span>
              <button class="dy-detail-close" @click="dayunSelected = -1">×</button>
            </div>
            <p v-if="dayunItems[dayunSelected].narrative" class="dy-detail-narrative">{{ dayunItems[dayunSelected].narrative }}</p>
            <div v-if="dayunItems[dayunSelected].wealth_hint || dayunItems[dayunSelected].health_hint || dayunItems[dayunSelected].love_hint"
                 class="dayun-hints">
              <span v-if="dayunItems[dayunSelected].wealth_hint" class="dh-tag dh-wealth">财运：{{ dayunItems[dayunSelected].wealth_hint }}</span>
              <span v-if="dayunItems[dayunSelected].health_hint" class="dh-tag dh-health">健康：{{ dayunItems[dayunSelected].health_hint }}</span>
              <span v-if="dayunItems[dayunSelected].love_hint"   class="dh-tag dh-love">感情：{{ dayunItems[dayunSelected].love_hint }}</span>
            </div>
          </div>
        </transition>
        <p v-if="!dayunItems.length" class="muted">暂无大运数据</p>
      </section>

      <!-- ── 五行格局 ── -->
      <section class="card section-inline">
        <h2 class="card-title">五行格局</h2>
        <div class="wx-chart-row">
          <div v-if="result.wuxing_score" class="wx-radar-wrap">
            <svg viewBox="0 0 200 200" class="wx-radar-svg">
              <polygon :points="radarBgHalf" fill="none" stroke="var(--border)" stroke-width="0.8" stroke-dasharray="3,2"/>
              <polygon :points="radarBg"     fill="none" stroke="var(--border)" stroke-width="1"/>
              <line v-for="(angle, i) in RADAR_ANGLES" :key="`axis-${i}`"
                :x1="RADAR_CX" :y1="RADAR_CY"
                :x2="+(RADAR_CX + RADAR_R * Math.cos(angle)).toFixed(1)"
                :y2="+(RADAR_CY + RADAR_R * Math.sin(angle)).toFixed(1)"
                stroke="var(--border)" stroke-width="0.6" />
              <polygon :points="radarPoints"
                fill="var(--accent-soft)" fill-opacity="0.6"
                stroke="var(--accent)" stroke-width="2"/>
              <circle v-for="(pt, i) in radarPoints.split(' ')" :key="`dot-${i}`"
                :cx="+pt.split(',')[0]" :cy="+pt.split(',')[1]" r="3"
                fill="var(--accent)" />
              <text v-for="lb in radarLabels" :key="lb.el"
                :x="lb.x" :y="lb.y"
                text-anchor="middle" dominant-baseline="middle"
                class="radar-label" :fill="lb.color">{{ lb.el }}</text>
            </svg>
          </div>
          <div v-if="wuxingBars.length" class="wuxing-list">
            <div v-for="bar in wuxingBars" :key="bar.key" class="wx-row">
              <div class="wx-lbl" :style="{ color: bar.color }">{{ bar.label }}</div>
              <div class="wx-bar-wrap">
                <div class="wx-bar" :style="{ width: bar.pct + '%', background: bar.color }"></div>
              </div>
              <div class="wx-val">{{ bar.val.toFixed(1) }}（{{ bar.pct }}%）</div>
            </div>
          </div>
        </div>
        <div v-if="result.wuxing_balance_score != null" class="wx-balance">
          <div class="wx-balance-row">
            <span class="wx-bal-lbl">五行均衡分</span>
            <span class="wx-bal-val" :style="{ color: scoreColor(result.wuxing_balance_score) }">
              {{ result.wuxing_balance_score.toFixed(0) }}/100
            </span>
          </div>
          <div v-if="result.wuxing_weak?.length || result.wuxing_strong?.length" class="wx-imbalance">
            <span v-if="result.wuxing_weak?.length" class="wx-weak">偏缺：{{ result.wuxing_weak.join('、') }}</span>
            <span v-if="result.wuxing_strong?.length" class="wx-strong">偏旺：{{ result.wuxing_strong.join('、') }}</span>
          </div>
          <p v-if="result.balance_advice" class="wx-advice">💡 {{ result.balance_advice }}</p>
        </div>
        <p v-else-if="!wuxingBars.length" class="muted">暂无五行数据</p>
      </section>

      <!-- ── 底部操作 ── -->
      <div v-if="result.yongshen?.favor?.length" class="suggest-name-row suggest-name-row--bottom">
        <button class="btn-suggest-name" @click="gotoNameSuggestWithResult">✦ 根据用神推荐改名</button>
        <button class="btn-zeri-link" @click="gotoZeri">📅 择日</button>
        <span class="hint">用神：{{ result.yongshen.favor.map(wxZh).join('、') }}</span>
      </div>

      <!-- ── 人生弧线 ── -->
      <section v-if="result.life_arc" class="card section-inline">
        <h2 class="card-title">人生弧线</h2>
        <blockquote v-if="result.life_arc.life_motto" class="life-motto">"{{ result.life_arc.life_motto }}"</blockquote>
        <div v-if="result.life_arc.overall_tier" class="life-tier-badge">
          命格层级：<strong>{{ result.life_arc.overall_tier }}</strong>
        </div>
        <div class="life-arc-phases">
          <div v-if="result.life_arc.early_fortune" class="arc-phase">
            <span class="arc-phase-label">早年</span>
            <p class="arc-phase-text">{{ result.life_arc.early_fortune }}</p>
          </div>
          <div v-if="result.life_arc.mid_fortune" class="arc-phase">
            <span class="arc-phase-label">中年</span>
            <p class="arc-phase-text">{{ result.life_arc.mid_fortune }}</p>
          </div>
          <div v-if="result.life_arc.late_fortune" class="arc-phase">
            <span class="arc-phase-label">晚年</span>
            <p class="arc-phase-text">{{ result.life_arc.late_fortune }}</p>
          </div>
        </div>
        <div v-if="result.life_arc.optimal_action" class="life-action-hint">
          💡 当前最优行动：{{ result.life_arc.optimal_action }}
        </div>
        <div v-if="result.life_arc.peak_periods?.length || result.life_arc.caution_periods?.length" class="life-periods">
          <div v-if="result.life_arc.peak_periods?.length" class="period-group">
            <span class="period-lbl period-peak">高峰期</span>
            <span v-for="p in result.life_arc.peak_periods" :key="p" class="period-tag period-tag-peak">{{ p }}</span>
          </div>
          <div v-if="result.life_arc.caution_periods?.length" class="period-group">
            <span class="period-lbl period-caution">谨慎期</span>
            <span v-for="p in result.life_arc.caution_periods" :key="p" class="period-tag period-tag-caution">{{ p }}</span>
          </div>
        </div>
      </section>

      <!-- ── 性格分析 ── -->
      <section v-if="result.personality" class="card section-inline">
        <h2 class="card-title">性格分析</h2>
        <p v-if="result.personality.day_stem_trait" class="personality-trait">{{ result.personality.day_stem_trait }}</p>
        <div class="personality-cols">
          <div v-if="result.personality.advantages?.length" class="personality-col">
            <span class="plist-label plist-adv">✦ 性格优势</span>
            <ul class="plist">
              <li v-for="a in result.personality.advantages" :key="a">{{ a }}</li>
            </ul>
          </div>
          <div v-if="result.personality.disadvantages?.length" class="personality-col">
            <span class="plist-label plist-dis">◆ 性格劣势</span>
            <ul class="plist plist-dis-items">
              <li v-for="d in result.personality.disadvantages" :key="d">{{ d }}</li>
            </ul>
          </div>
        </div>
        <div v-if="result.personality.communication_style" class="personality-extra-row">
          <span class="pex-key">沟通风格</span>
          <span class="pex-val">{{ result.personality.communication_style }}</span>
        </div>
        <div v-if="result.personality.stress_coping_mode" class="personality-extra-row">
          <span class="pex-key">压力应对</span>
          <span class="pex-val">{{ result.personality.stress_coping_mode }}</span>
        </div>
        <div v-if="result.personality.growth_advice" class="personality-growth">
          💡 成长建议：{{ result.personality.growth_advice }}
        </div>
      </section>

      <!-- ── 四维分析（财运/事业/婚恋/健康）── -->
      <section v-if="result.wealth_analysis || result.career || result.marriage_analysis || result.health" class="card section-inline">
        <h2 class="card-title">四维分析</h2>
        <div class="quad-scores">
          <div v-if="result.wealth_analysis" class="quad-card">
            <div class="quad-score-num" :style="{ color: scoreColor(result.wealth_analysis.wealth_score) }">{{ result.wealth_analysis.wealth_score }}</div>
            <div class="quad-label">财运</div>
            <div class="quad-tier">{{ result.wealth_analysis.wealth_tier }}</div>
          </div>
          <div v-if="result.career" class="quad-card">
            <div class="quad-score-num" :style="{ color: scoreColor(result.career.career_score) }">{{ result.career.career_score }}</div>
            <div class="quad-label">事业</div>
          </div>
          <div v-if="result.marriage_analysis" class="quad-card">
            <div class="quad-score-num" :style="{ color: scoreColor(result.marriage_analysis.marriage_score) }">{{ result.marriage_analysis.marriage_score }}</div>
            <div class="quad-label">婚恋</div>
          </div>
          <div v-if="result.health" class="quad-card">
            <div class="quad-score-num" :style="{ color: scoreColor(result.health.health_score) }">{{ result.health.health_score }}</div>
            <div class="quad-label">健康</div>
            <div class="quad-tier" :style="{ color: result.health.risk_level === '高' ? 'var(--danger-dark)' : '' }">{{ result.health.risk_level }}风险</div>
          </div>
        </div>

        <!-- 财运详情 -->
        <details v-if="result.wealth_analysis" class="quad-detail">
          <summary class="quad-summary">💰 财运详情</summary>
          <div class="quad-body">
            <p v-if="result.wealth_analysis.annual_range" class="quad-row"><span class="qk">年收参考</span><span>{{ result.wealth_analysis.annual_range }}</span></p>
            <p v-if="result.wealth_analysis.industries?.length" class="quad-row"><span class="qk">适合行业</span><span>{{ result.wealth_analysis.industries.join('、') }}</span></p>
            <p v-if="result.wealth_analysis.investment_preference" class="quad-row"><span class="qk">投资偏好</span><span>{{ result.wealth_analysis.investment_preference }}</span></p>
            <p v-if="result.wealth_analysis.financial_taboos" class="quad-row"><span class="qk">财务忌讳</span><span>{{ result.wealth_analysis.financial_taboos }}</span></p>
            <p v-if="result.wealth_analysis.strategy" class="quad-text">{{ result.wealth_analysis.strategy }}</p>
          </div>
        </details>

        <!-- 事业详情 -->
        <details v-if="result.career" class="quad-detail">
          <summary class="quad-summary">🏢 事业详情</summary>
          <div class="quad-body">
            <p v-if="result.career.career_directions?.length" class="quad-row"><span class="qk">发展方向</span><span>{{ result.career.career_directions.join('、') }}</span></p>
            <p v-if="result.career.suitable_industries?.length" class="quad-row"><span class="qk">适合行业</span><span>{{ result.career.suitable_industries.join('、') }}</span></p>
            <p v-if="result.career.leadership_potential != null" class="quad-row"><span class="qk">领导潜质</span><span>{{ result.career.leadership_potential ? '✦ 具备领导力' : '偏重执行' }}</span></p>
            <p v-if="result.career.entrepreneurship_assessment" class="quad-row"><span class="qk">创业适合度</span><span>{{ result.career.entrepreneurship_assessment }}</span></p>
            <p v-if="result.career.five_year_roadmap" class="quad-text">五年路线图：{{ result.career.five_year_roadmap }}</p>
          </div>
        </details>

        <!-- 婚恋详情 -->
        <details v-if="result.marriage_analysis" class="quad-detail">
          <summary class="quad-summary">💑 婚恋详情</summary>
          <div class="quad-body">
            <p v-if="result.marriage_analysis.peach_blossom" class="quad-row"><span class="qk">桃花运</span><span>{{ result.marriage_analysis.peach_blossom }}</span></p>
            <p v-if="result.marriage_analysis.partner_wuxing" class="quad-row"><span class="qk">配偶五行</span><span>{{ result.marriage_analysis.partner_wuxing }}</span></p>
            <p v-if="result.marriage_analysis.partner_profile" class="quad-row"><span class="qk">配偶画像</span><span>{{ result.marriage_analysis.partner_profile }}</span></p>
            <p v-if="result.marriage_analysis.optimal_marriage_age" class="quad-row"><span class="qk">最佳婚龄</span><strong>{{ result.marriage_analysis.optimal_marriage_age }}</strong></p>
            <p v-if="result.marriage_analysis.marriage_windows?.length" class="quad-row"><span class="qk">婚姻窗口</span><span>{{ result.marriage_analysis.marriage_windows.join('、') }}</span></p>
            <p v-if="result.marriage_analysis.emotional_pitfalls" class="quad-row"><span class="qk">感情易犯错</span><span>{{ result.marriage_analysis.emotional_pitfalls }}</span></p>
            <p v-if="result.marriage_analysis.children_outlook" class="quad-row"><span class="qk">子嗣运</span><span>{{ result.marriage_analysis.children_outlook }}</span></p>
          </div>
        </details>

        <!-- 健康详情 -->
        <details v-if="result.health" class="quad-detail">
          <summary class="quad-summary">🏥 健康详情</summary>
          <div class="quad-body">
            <p v-if="result.health.risk_organs?.length" class="quad-row"><span class="qk">注意脏器</span><span>{{ result.health.risk_organs.join('、') }}</span></p>
            <p v-if="result.health.constitution_type" class="quad-row"><span class="qk">体质类型</span><span>{{ result.health.constitution_type }}</span></p>
            <p v-if="result.health.exercise?.length" class="quad-row"><span class="qk">适合运动</span><span>{{ result.health.exercise.join('、') }}</span></p>
            <p v-if="result.health.diet?.length" class="quad-row"><span class="qk">饮食建议</span><span>{{ result.health.diet.join('、') }}</span></p>
            <p v-if="result.health.seasonal_health" class="quad-row"><span class="qk">季节注意</span><span>{{ result.health.seasonal_health }}</span></p>
            <p v-if="result.health.health_advice" class="quad-text">{{ result.health.health_advice }}</p>
          </div>
        </details>
      </section>

      <!-- ── 开运信息 ── -->
      <section v-if="result.lucky" class="card section-inline">
        <h2 class="card-title">开运信息</h2>
        <div class="lucky-grid">
          <div v-if="result.lucky.lucky_colors?.length" class="lucky-item">
            <span class="lucky-key">吉祥色</span>
            <div class="lucky-colors">
              <span v-for="c in result.lucky.lucky_colors" :key="c" class="lucky-color-tag">{{ c }}</span>
            </div>
          </div>
          <div v-if="result.lucky.avoid_colors?.length" class="lucky-item">
            <span class="lucky-key">忌用色</span>
            <div class="lucky-colors">
              <span v-for="c in result.lucky.avoid_colors" :key="c" class="avoid-color-tag">{{ c }}</span>
            </div>
          </div>
          <div v-if="result.lucky.lucky_numbers?.length" class="lucky-item">
            <span class="lucky-key">吉祥数</span>
            <span class="lucky-val">{{ result.lucky.lucky_numbers.join('、') }}</span>
          </div>
          <div v-if="result.lucky.lucky_direction" class="lucky-item">
            <span class="lucky-key">吉祥方位</span>
            <span class="lucky-val">{{ result.lucky.lucky_direction }}</span>
          </div>
          <div v-if="result.lucky.lucky_item" class="lucky-item">
            <span class="lucky-key">开运物</span>
            <span class="lucky-val">{{ result.lucky.lucky_item }}</span>
          </div>
        </div>
      </section>

      <!-- ── 神煞 ── -->
      <section v-if="result.shensha?.length" class="card section-inline">
        <h2 class="card-title">神煞</h2>
        <div class="shensha-table-wrap">
          <table class="shensha-table">
            <thead>
              <tr><th>名称</th><th>所在柱</th><th>地支</th><th>吉凶</th><th>含义</th></tr>
            </thead>
            <tbody>
              <tr v-for="s in result.shensha" :key="s.name + s.pillar" :class="s.is_beneficial ? 'ss-good' : 'ss-bad'">
                <td><strong>{{ s.name }}</strong></td>
                <td>{{ s.pillar }}</td>
                <td>{{ s.dizhi }}</td>
                <td><span class="ss-badge" :class="s.is_beneficial ? 'ss-ji' : 'ss-xiong'">{{ s.is_beneficial ? '吉' : '凶' }}</span></td>
                <td class="ss-meaning">{{ s.meaning }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- ── 人生里程碑 ── -->
      <section v-if="result.milestones?.length" class="card section-inline">
        <h2 class="card-title">人生里程碑</h2>
        <div class="milestones-list">
          <div v-for="m in result.milestones" :key="m.year" class="milestone-item"
            :class="m.risk_level === 'high' ? 'ms-high' : m.risk_level === 'medium' ? 'ms-mid' : 'ms-low'">
            <div class="ms-timeline-dot" />
            <div class="ms-content">
              <div class="ms-header">
                <span class="ms-age">{{ m.age }}岁</span>
                <span class="ms-year">（{{ m.year }}年）</span>
                <span class="ms-type">{{ m.milestone_type }}</span>
                <span class="ms-gz">{{ m.ganzhi_context }}</span>
              </div>
              <p class="ms-desc">{{ m.description }}</p>
              <p v-if="m.advice" class="ms-advice">💡 {{ m.advice }}</p>
            </div>
          </div>
        </div>
      </section>

      <!-- ── 月运概览 ── -->
      <section v-if="result.monthly_fortune?.length" class="card section-inline">
        <h2 class="card-title">月运概览</h2>
        <div class="monthly-grid">
          <div
            v-for="mf in result.monthly_fortune"
            :key="mf.month"
            class="monthly-cell"
            :class="mf.luck_level === '吉' ? 'mo-ji' : mf.luck_level === '凶' ? 'mo-xiong' : 'mo-ping'"
            :title="mf.tip + (mf.clash_with ? '  冲：' + mf.clash_with : '')"
          >
            <span class="mo-month">{{ mf.month }}月</span>
            <span class="mo-gz">{{ mf.month_dizhi }}</span>
            <span class="mo-level">{{ mf.luck_level }}</span>
          </div>
        </div>
        <p class="monthly-hint">悬停查看提示；绿=吉，红=凶，灰=平</p>
      </section>

      <BaziEventSection :case-id="savedCaseId" @open-save-dialog="openSaveDialog" />

      <!-- 警告信息 -->
      <div v-if="result.warnings?.length" class="bazi-warnings">
        <div v-for="(w, i) in result.warnings" :key="i" class="bw-item">
          ⚠ <span class="bw-code">[{{ w.code }}]</span> {{ w.message }}
        </div>
      </div>

      <!-- 版本信息 -->
      <div class="bazi-version-footer">
        <span v-if="result.api_version">API {{ result.api_version }}</span>
        <span v-if="result.rule_version">规则 {{ result.rule_version }}</span>
        <span v-if="result.schema_version">{{ result.schema_version }}</span>
      </div>
    </template>

    <BaziSaveDialog
      :open="saveDialogOpen"
      :birth-dt="birthDt"
      :city-name="cityName"
      :init-city="initCity"
      :gender="gender"
      v-model:save-case-name="saveCaseName"
      v-model:save-case-notes="saveCaseNotes"
      :save-case-saving="saveCaseSaving"
      :save-case-error="saveCaseError"
      @close="closeSaveDialog()"
      @save="saveCurrentCase()"
    />
  </div>
</template>

<style scoped>
.bazi-view { padding-bottom: var(--sp-8); }
.page-title { font-size: var(--fs-2xl); font-weight: 700; color: var(--text); margin-bottom: var(--sp-3); font-family: var(--font-cn); }

/* 表单折叠控制栏 */
.form-toggle-bar {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  margin-bottom: var(--sp-3);
}
.btn-toggle-form {
  padding: 5px 14px;
  border: 1px solid var(--border-md);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text-2);
  font-size: var(--fs-sm);
  cursor: pointer;
  transition: border-color var(--dur-fast), color var(--dur-fast);
}
.btn-toggle-form:hover { border-color: var(--accent); color: var(--accent); }
.current-params { font-size: var(--fs-sm); color: var(--text-3); }

/* 卡片 */
.card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: var(--sp-5); box-shadow: var(--shadow); margin-bottom: var(--sp-5); }
.card-title { font-size: var(--fs-lg); font-weight: 600; margin-bottom: var(--sp-4); }

/* 表单 */
.form-grid { display: flex; flex-direction: column; gap: var(--sp-3); margin-bottom: var(--sp-4); }
.form-row { display: flex; align-items: center; gap: var(--sp-3); flex-wrap: wrap; }
.form-row > label:first-child { width: 90px; font-size: var(--fs-md); color: var(--text-2); flex-shrink: 0; }
.form-row input[type="datetime-local"],
.form-row input[type="number"],
.form-row input:not([type]),
.form-row select { padding: 7px 10px; border: 1px solid var(--border-md); border-radius: var(--radius-sm); font-size: var(--fs-md); }
.form-row input:focus, .form-row select:focus { outline: none; border-color: var(--accent); }
.radio-opt { display: flex; align-items: center; gap: 4px; cursor: pointer; font-size: var(--fs-md); }
.check-opt { display: flex; align-items: center; gap: 6px; cursor: pointer; font-size: var(--fs-md); }
.hint { font-size: var(--fs-xs); color: var(--text-3); }

.form-actions { display: flex; align-items: center; gap: var(--sp-3); flex-wrap: wrap; }
.btn-primary { padding: 9px 22px; background: var(--accent); color: #fff; border: none; border-radius: var(--radius-sm); font-size: var(--fs-md); font-weight: 600; cursor: pointer; transition: background var(--dur-fast); }
.btn-primary:hover { background: var(--accent-dark); }
.btn-primary:disabled { opacity: .6; cursor: not-allowed; }
.btn-sec { padding: 9px 18px; background: var(--surface); color: var(--text-2); border: 1px solid var(--border-md); border-radius: var(--radius-sm); font-size: var(--fs-md); cursor: pointer; transition: border-color var(--dur-fast); }
.btn-sec:hover { border-color: var(--accent); color: var(--accent); }
.error-msg { color: var(--danger-dark); font-size: var(--fs-sm); }

/* 骨架屏 */
.skeleton-wrap { padding: var(--sp-5); }
.skel-line { height: 16px; background: var(--border); border-radius: 4px; margin-bottom: var(--sp-3); animation: shimmer 1.2s infinite; }
.skel-box { height: 80px; background: var(--border); border-radius: var(--radius-sm); margin-top: var(--sp-4); animation: shimmer 1.2s infinite; }
@keyframes shimmer { 0%,100% { opacity: 1; } 50% { opacity: .4; } }

/* 四柱表格（新版） */
.pillars-tbl-wrap { overflow-x: auto; margin-bottom: var(--sp-4); }
.pillars-tbl { width: 100%; border-collapse: collapse; font-family: var(--font-cn); text-align: center; font-size: var(--fs-md); }
.pillars-tbl th, .pillars-tbl td { padding: 8px 10px; border: 1px solid var(--border); }
.pillars-tbl thead th { background: var(--surface-2); font-size: var(--fs-sm); font-weight: 600; color: var(--text-2); }
.pillars-tbl thead th.day-col-th { background: rgba(217,119,6,.08); color: var(--accent-dark); }
.pillars-tbl td.day-col-th { background: rgba(217,119,6,.04); }
.row-lbl-th, .row-lbl { width: 40px; font-size: var(--fs-xs); color: var(--text-3); background: var(--surface-2); font-weight: 600; }
.gz-char { font-size: var(--fs-2xl); font-weight: 700; display: block; }
.gz-branch { font-size: var(--fs-xl); }
.tg-chip { font-size: var(--fs-sm); font-weight: 700; }
.tg-day { color: var(--accent-dark) !important; }
.cang-stem { font-size: var(--fs-sm); font-weight: 600; margin-right: 2px; }
.nayin-text { font-size: 11px; color: var(--text-3); }

.pillars-meta { display: flex; flex-wrap: wrap; gap: var(--sp-3); font-size: var(--fs-sm); color: var(--text-2); }
.meta-item b { color: var(--text); }

.case-actions-row {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  flex-wrap: wrap;
  margin-top: var(--sp-4);
}
.btn-case-save {
  padding: 8px 18px;
  border: 1.5px solid var(--accent);
  border-radius: var(--radius-sm);
  background: rgba(217, 119, 6, 0.08);
  color: var(--accent-dark);
  font-size: var(--fs-md);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--dur-fast);
}
.btn-case-save:hover {
  background: var(--accent);
  color: #fff;
}
.case-save-pill {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  border: 1px solid var(--border-md);
  border-radius: 999px;
  background: var(--surface-2);
  color: var(--text-2);
  font-size: var(--fs-xs);
}
.case-save-pill-success {
  border-color: rgba(21, 128, 61, 0.3);
  background: rgba(220, 252, 231, 0.9);
  color: #166534;
}
.case-save-msg {
  font-size: var(--fs-xs);
  color: #166534;
}

.ai-panel {
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
}
.ai-disclaimer-bar {
  padding: 12px 14px;
  border: 1px solid rgba(217, 119, 6, 0.18);
  border-radius: var(--radius-sm);
  background: rgba(254, 243, 199, 0.7);
  color: #92400e;
  font-size: var(--fs-sm);
  line-height: 1.7;
}
.ai-actions-row {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  flex-wrap: wrap;
}
.btn-ai-generate {
  padding: 9px 18px;
  border: none;
  border-radius: var(--radius-sm);
  background: linear-gradient(135deg, #7c3aed, #a855f7);
  color: #fff;
  font-size: var(--fs-md);
  font-weight: 600;
  cursor: pointer;
}
.btn-ai-generate:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.ai-module-select {
  min-width: 180px;
  padding: 9px 12px;
  border: 1px solid var(--border-md);
  border-radius: var(--radius-sm);
  font-size: var(--fs-sm);
  background: var(--surface);
}
.ai-status-text {
  font-size: var(--fs-sm);
  color: var(--text-2);
}
.ai-status-warn { color: #b45309; }
.ai-error-msg { margin: 0; }
.ai-result-wrap {
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
}
.ai-result-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  font-size: var(--fs-xs);
  color: var(--text-3);
}
.ai-result-meta span {
  padding: 4px 8px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--surface-2);
}
.ai-schema-badge {
  color: #6d28d9;
  border-color: rgba(109, 40, 217, 0.18) !important;
  background: rgba(243, 232, 255, 0.9) !important;
}
.ai-result-box {
  padding: 16px 18px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: linear-gradient(180deg, rgba(250, 245, 255, 0.75), rgba(255, 255, 255, 0.95));
}
.ai-paragraph {
  margin: 0 0 12px;
  line-height: 1.9;
  color: var(--text);
  white-space: pre-wrap;
}
.ai-paragraph:last-child { margin-bottom: 0; }
.ai-empty-state {
  margin: 0;
  color: var(--text-3);
  font-size: var(--fs-sm);
}

.raw-panel {
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
}
.raw-panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--sp-3);
  flex-wrap: wrap;
}
.raw-panel-title {
  margin: 0 0 6px;
  font-size: var(--fs-lg);
  font-weight: 700;
  color: var(--text);
}
.raw-panel-desc {
  margin: 0;
  font-size: var(--fs-sm);
  color: var(--text-3);
  line-height: 1.7;
}
.raw-panel-meta {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  border: 1px solid var(--border-md);
  border-radius: 999px;
  background: var(--surface-2);
  color: var(--text-2);
  font-size: var(--fs-xs);
}
.raw-json-block {
  margin: 0;
  padding: 16px 18px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: #0f172a;
  color: #e2e8f0;
  font-size: 12px;
  line-height: 1.7;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-word;
}

.bazi-modal-mask {
  position: fixed;
  inset: 0;
  z-index: 60;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: rgba(15, 23, 42, 0.45);
}
.bazi-modal {
  width: min(100%, 520px);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg, 18px);
  box-shadow: 0 24px 60px rgba(15, 23, 42, 0.24);
  padding: 22px;
}
.bazi-modal-title {
  margin: 0 0 8px;
  font-size: var(--fs-xl);
  font-weight: 700;
  color: var(--text);
}
.bazi-modal-desc {
  margin: 0 0 var(--sp-4);
  font-size: var(--fs-sm);
  color: var(--text-3);
  line-height: 1.7;
}
.bazi-modal-body {
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
}
.bazi-form-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.bazi-form-label {
  font-size: var(--fs-sm);
  color: var(--text-2);
  font-weight: 600;
}
.bazi-form-input,
.bazi-form-textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-md);
  border-radius: var(--radius-sm);
  font-size: var(--fs-md);
  background: var(--surface);
}
.bazi-form-input:focus,
.bazi-form-textarea:focus {
  outline: none;
  border-color: var(--accent);
}
.bazi-form-textarea {
  resize: vertical;
  min-height: 84px;
}
.bazi-save-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  font-size: var(--fs-xs);
  color: var(--text-3);
}
.bazi-save-summary span {
  padding: 4px 8px;
  border-radius: 999px;
  background: var(--surface-2);
  border: 1px solid var(--border);
}
.bazi-save-error { margin: 0; }
.bazi-modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--sp-3);
  margin-top: var(--sp-4);
}

/* 推荐改名 */
.suggest-name-row { margin-top: var(--sp-4); display: flex; align-items: center; gap: var(--sp-3); flex-wrap: wrap; }
.btn-suggest-name { padding: 8px 18px; background: var(--surface); color: var(--accent); border: 1.5px solid var(--accent); border-radius: var(--radius-sm); font-size: var(--fs-md); font-weight: 600; cursor: pointer; transition: all var(--dur-fast); }
.btn-suggest-name:hover { background: var(--accent); color: #fff; }
.btn-zeri-link { padding: 8px 16px; background: var(--surface); color: #d97706; border: 1.5px solid #fbbf24; border-radius: var(--radius-sm); font-size: var(--fs-md); font-weight: 600; cursor: pointer; transition: all var(--dur-fast); }
.btn-zeri-link:hover { background: #fef3c7; }

/* Tabs */
.tabs { display: flex; gap: var(--sp-2); margin-bottom: var(--sp-4); border-bottom: 2px solid var(--border); }
.tab-btn { padding: 8px 20px; border: none; background: none; cursor: pointer; font-size: var(--fs-md); color: var(--text-2); border-bottom: 2px solid transparent; margin-bottom: -2px; transition: color var(--dur-fast), border-color var(--dur-fast); }
.tab-btn.active { color: var(--accent); border-bottom-color: var(--accent); font-weight: 600; }
.tab-btn:hover { color: var(--text); }

/* 综合概览 */
.overview-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: var(--sp-4); margin-bottom: var(--sp-5); }
.ov-card { background: var(--surface-2); border-radius: var(--radius-sm); border: 1px solid var(--border); padding: var(--sp-4); }
.ov-title { font-size: var(--fs-xs); color: var(--text-3); margin-bottom: var(--sp-2); font-weight: 600; text-transform: uppercase; }
.ov-body { font-size: var(--fs-md); }
.ov-summary { font-size: var(--fs-xs); color: var(--text-3); margin-top: 4px; }

.overview-guide {
  margin-bottom: var(--sp-5);
  padding: 18px 20px;
  border-radius: 16px;
  background: linear-gradient(180deg, #fffaf0 0%, var(--surface) 100%);
}

.overview-guide-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
}

.overview-guide-title {
  margin: 2px 0 0;
  font-size: var(--fs-xl);
  color: var(--text);
  font-family: var(--font-cn);
}

.overview-guide-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.btn-soft {
  min-height: 34px;
  padding: 0 12px;
  border-radius: 8px;
  border: 1px solid var(--border-md);
  background: #fff;
  color: var(--text-2);
  font-size: var(--fs-xs);
  font-weight: 700;
  cursor: pointer;
}

.btn-soft:hover {
  border-color: var(--accent);
  color: var(--accent-dark);
}

.overview-guide-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-top: 16px;
}

.overview-guide-card {
  padding: 14px;
  border-radius: 12px;
  border: 1px solid var(--border);
  background: rgba(255, 255, 255, 0.82);
}

.overview-guide-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: .06em;
  color: var(--text-3);
}

.overview-guide-value {
  margin-top: 8px;
  font-size: var(--fs-sm);
  line-height: 1.7;
  color: var(--text-2);
}

.overview-reading-block {
  margin-top: 16px;
  padding: 14px;
  border-radius: 12px;
  background: var(--surface-2);
  border: 1px solid var(--border);
}

.overview-reading-title {
  font-size: var(--fs-sm);
  font-weight: 700;
  color: var(--text);
}

.overview-reading-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 12px;
}

.overview-reading-item {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.overview-reading-index {
  width: 20px;
  height: 20px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--accent-lt);
  color: var(--accent-dark);
  font-size: 11px;
  font-weight: 700;
  flex-shrink: 0;
}

.overview-reading-text {
  font-size: var(--fs-sm);
  line-height: 1.7;
  color: var(--text-2);
}

.overview-terms {
  margin-top: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.overview-terms-label {
  font-size: var(--fs-xs);
  color: var(--text-3);
}

.overview-term-chip {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: #fff;
  font-size: var(--fs-xs);
  color: var(--text-2);
}

.tag-row { display: flex; flex-wrap: wrap; gap: 4px; }
.tag { padding: 2px 8px; border-radius: 12px; font-size: var(--fs-xs); font-weight: 600; }
.tag-favor  { background: #dcfce7; color: #15803d; }
.tag-avoid  { background: #fee2e2; color: #dc2626; }
.tag-neutral{ background: #f0f9ff; color: #0369a1; }

/* ── 大运时间轴 ── */
.dy-header {
  display: flex; align-items: center; gap: var(--sp-3); flex-wrap: wrap;
  font-size: var(--fs-sm); color: var(--text-2); margin-bottom: var(--sp-5);
}
.dy-dir {
  padding: 2px 10px; background: var(--surface-2);
  border: 1px solid var(--border-md); border-radius: 20px;
}
.dy-cur-lbl { margin-left: auto; color: var(--accent); font-weight: 600; }
.dy-cur-age { font-weight: 400; color: var(--text-2); }

.dy-timeline-wrap { overflow-x: auto; padding-bottom: var(--sp-3); }
.dy-track {
  display: flex; align-items: flex-start;
  min-width: max-content; padding: 24px 16px 8px;
}

.dy-step {
  display: flex; flex-direction: column; align-items: center;
  width: 96px; cursor: pointer; position: relative;
}
.dy-step:hover .dy-card { border-color: var(--accent); }

/* 节点行（线 + 点） */
.dy-dot-row {
  display: flex; align-items: center; width: 100%;
  height: 20px; margin-bottom: 10px;
}
.dy-line-l, .dy-line-r { flex: 1; height: 2px; background: var(--border); }
.dy-dot {
  width: 14px; height: 14px; border-radius: 50%;
  background: var(--border-md);
  border: 2px solid var(--surface);
  box-shadow: 0 0 0 2px var(--border-md);
  flex-shrink: 0; position: relative; z-index: 1;
  transition: background .2s, box-shadow .2s;
}
.dy-dot-ring {
  position: absolute; top: -5px; left: -5px;
  width: 20px; height: 20px; border-radius: 50%;
  border: 2px solid var(--accent);
  animation: dy-ring-pulse 2s ease-in-out infinite;
}
@keyframes dy-ring-pulse {
  0%, 100% { transform: scale(1);   opacity: .9; }
  50%       { transform: scale(1.4); opacity: 0; }
}

.dy-cur  .dy-dot { background: var(--accent); box-shadow: 0 0 0 2px var(--surface), 0 0 0 4px var(--accent); }
.dy-past .dy-dot { background: var(--text-3); box-shadow: 0 0 0 2px var(--text-3); }

/* 卡片 */
.dy-card {
  width: 80px; padding: 6px 4px; text-align: center;
  border-radius: var(--radius-sm);
  border: 1.5px solid var(--border);
  background: var(--surface);
  transition: border-color .15s, box-shadow .15s;
  user-select: none;
}
.dy-cur .dy-card {
  border-color: var(--accent);
  background: linear-gradient(150deg, var(--surface) 0%, var(--accent-soft) 100%);
  box-shadow: 0 2px 8px var(--accent-soft);
}
.dy-past .dy-card { opacity: .55; }
.dy-sel .dy-card  { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-soft); }

.dy-gz { font-size: 22px; font-weight: 700; font-family: var(--font-cn); letter-spacing: 2px; }
.dy-tg-chip {
  font-size: 10px; padding: 1px 6px;
  border-radius: 10px; border: 1px solid transparent;
  display: inline-block; margin: 3px auto 0;
}
.dy-age-range { font-size: 11px; color: var(--text-2); margin-top: 4px; }
.dy-yr        { font-size: 10px; color: var(--text-3); margin-top: 1px; }

/* 详情面板 */
/* 当前大运解读摘要 */
.dy-cur-summary {
  margin-top: var(--sp-4);
  padding: var(--sp-4) var(--sp-5);
  background: var(--surface-2, #f8f9ff);
  border: 1px solid var(--accent-soft);
  border-radius: var(--radius-sm);
}
.dy-cur-summary-title {
  font-size: var(--fs-sm);
  font-weight: 700;
  color: var(--accent);
  margin-bottom: var(--sp-2);
  letter-spacing: .04em;
}
.dy-cur-narrative {
  font-size: var(--fs-md);
  color: var(--text);
  line-height: 1.8;
  margin-bottom: var(--sp-3);
}
.dy-cur-narrative.muted { color: var(--text-3); font-size: var(--fs-sm); }

.dy-detail-card {
  margin-top: var(--sp-5);
  padding: var(--sp-4) var(--sp-5);
  background: var(--surface);
  border: 1.5px solid var(--accent);
  border-radius: var(--radius-sm);
  box-shadow: 0 2px 12px var(--accent-soft);
}
.dy-detail-header {
  display: flex; align-items: center; gap: var(--sp-3); flex-wrap: wrap;
  margin-bottom: var(--sp-3);
}
.dy-detail-gz    { font-size: var(--fs-2xl); font-weight: 700; font-family: var(--font-cn); }
.dy-detail-period{ font-size: var(--fs-sm); color: var(--text-2); }
.dy-detail-close {
  margin-left: auto; background: none; border: none;
  font-size: 22px; cursor: pointer; color: var(--text-3); line-height: 1;
}
.dy-detail-close:hover { color: var(--text); }
.dy-detail-narrative { font-size: var(--fs-md); color: var(--text); line-height: 1.8; margin-bottom: var(--sp-3); }

/* 展开过渡 */
.dy-expand-enter-active, .dy-expand-leave-active  { transition: opacity .2s, transform .2s; }
.dy-expand-enter-from,   .dy-expand-leave-to      { opacity: 0; transform: translateY(-6px); }

/* 大运提示标签（复用于详情面板） */
.dayun-hints { display: flex; gap: var(--sp-2); flex-wrap: wrap; }
.dh-tag  { padding: 3px 10px; border-radius: 12px; font-size: var(--fs-xs); font-weight: 600; }
.dh-wealth { background: #fef9c3; color: #a16207; }
.dh-health { background: #dcfce7; color: #15803d; }
.dh-love   { background: #fce7f3; color: #9d174d; }

/* 五行 */
.wuxing-list { display: flex; flex-direction: column; gap: var(--sp-3); }
.wx-row { display: flex; align-items: center; gap: var(--sp-3); }
.wx-lbl { width: 28px; font-size: var(--fs-md); font-weight: 700; text-align: center; }
.wx-bar-wrap { flex: 1; height: 18px; background: var(--surface-2); border-radius: 9px; overflow: hidden; }
.wx-bar { height: 100%; border-radius: 9px; transition: width .5s ease; }
.wx-val { width: 100px; font-size: var(--fs-sm); color: var(--text-2); text-align: right; }

.muted { color: var(--text-3); font-size: var(--fs-sm); }

/* 命局总评 */
.bazi-summary-block {
  background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
  border: 1px solid #fbbf24;
  border-left: 4px solid #d97706;
  border-radius: var(--radius-sm);
  padding: var(--sp-4) var(--sp-5);
  margin-bottom: var(--sp-5);
}
.summary-label { font-size: var(--fs-xs); color: #92400e; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: var(--sp-2); }
.bazi-summary-text { font-size: var(--fs-md); color: var(--text); line-height: 1.8; white-space: pre-line; }

/* 当前运势摘要卡片 */
.cur-fortune-card {
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: var(--sp-4);
  margin-bottom: var(--sp-5);
}
.cf-row { display: flex; gap: var(--sp-6); margin-bottom: var(--sp-3); }
.cf-item { text-align: center; }
.cf-lbl { font-size: var(--fs-xs); color: var(--text-3); margin-bottom: 2px; }
.cf-val { font-size: var(--fs-xl); font-weight: 700; font-family: var(--font-cn); }
.cf-sub { font-size: var(--fs-xs); color: var(--text-3); }
.cf-actions { margin-bottom: var(--sp-3); }
.cf-action-list { font-size: var(--fs-sm); color: var(--text); padding-left: 1.2em; margin: 4px 0; }
.cf-action-list li { margin-bottom: 3px; }
.cf-domains { display: flex; flex-wrap: wrap; gap: var(--sp-2); }
.cf-domain-item { padding: 4px 10px; background: var(--surface); border: 1px solid var(--border-md); border-radius: var(--radius-sm); font-size: var(--fs-xs); }
.cf-domain-key { color: var(--text-3); margin-right: 4px; }
.cf-domain-val { color: var(--text); }

/* 格局等级标签 */
.geju-level-badge { display: inline-block; font-size: 10px; padding: 1px 6px; border-radius: 10px; background: rgba(217,119,6,.12); color: #92400e; font-weight: 600; margin-left: 6px; vertical-align: middle; }

/* 开运数据 */
.lucky-row { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; flex-wrap: wrap; }
.lucky-lbl { font-size: var(--fs-xs); color: var(--text-3); width: 60px; flex-shrink: 0; }
.lucky-tag { font-size: var(--fs-xs); padding: 2px 8px; background: var(--surface); border: 1px solid var(--border-md); border-radius: 10px; }

/* 人生弧线（升级版）*/
.life-arc-block { background: var(--surface-2); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: var(--sp-5); margin-bottom: var(--sp-5); }
.life-arc-header { display: flex; align-items: center; gap: var(--sp-3); margin-bottom: var(--sp-3); }
.life-arc-title { font-size: var(--fs-md); font-weight: 600; color: var(--text); }
.life-arc-tier { font-size: var(--fs-xs); padding: 2px 9px; border-radius: 10px; background: rgba(217,119,6,.12); color: #92400e; font-weight: 700; }
.life-motto { font-size: var(--fs-md); color: #78716c; font-style: italic; border-left: 3px solid #d97706; padding-left: var(--sp-3); margin: 0 0 var(--sp-4); font-family: var(--font-cn); }
.life-arc-periods { display: grid; grid-template-columns: repeat(3,1fr); gap: var(--sp-3); margin-bottom: var(--sp-4); }
.lp-item { }
.lp-label { font-size: var(--fs-xs); color: var(--accent); font-weight: 700; display: block; margin-bottom: 3px; }
.lp-text { font-size: var(--fs-sm); color: var(--text); line-height: 1.6; margin: 0; }
.life-arc-body { font-size: var(--fs-md); color: var(--text); line-height: 1.7; margin-bottom: var(--sp-4); }
.life-arc-peaks { display: flex; flex-direction: column; gap: var(--sp-2); }
.peak-item { display: flex; align-items: center; flex-wrap: wrap; gap: 6px; }
.peak-lbl { font-size: var(--fs-xs); font-weight: 700; width: 64px; flex-shrink: 0; }
.peak-good { color: #15803d; }
.peak-warn { color: #dc2626; }
.peak-tag { font-size: var(--fs-xs); padding: 2px 8px; border-radius: 10px; }
.peak-tag-good { background: #dcfce7; color: #15803d; }
.peak-tag-warn { background: #fee2e2; color: #dc2626; }

/* 性格分析 */
.personality-block { background: var(--surface-2); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: var(--sp-4); margin-bottom: var(--sp-5); }
.personality-trait { font-size: var(--fs-md); color: var(--text); margin: var(--sp-2) 0 var(--sp-3); }
.personality-cols { display: grid; grid-template-columns: 1fr 1fr; gap: var(--sp-4); margin-bottom: var(--sp-3); }
.pers-col { }
.pers-lbl { font-size: var(--fs-xs); font-weight: 700; margin-bottom: 4px; }
.pers-good { color: #15803d; }
.pers-warn { color: #dc2626; }
.pers-list { font-size: var(--fs-sm); color: var(--text); padding-left: 1.2em; margin: 0; }
.pers-list li { margin-bottom: 3px; }
.pers-advice { font-size: var(--fs-sm); color: var(--accent-dark); background: rgba(217,119,6,.08); border-radius: var(--radius-sm); padding: var(--sp-2) var(--sp-3); margin: 0; }

/* 神煞 */
.shensha-section { margin-bottom: var(--sp-5); }
.shensha-list { display: flex; flex-direction: column; gap: 6px; }
.shensha-item { display: flex; align-items: baseline; gap: var(--sp-2); padding: 6px 10px; border-radius: var(--radius-sm); font-size: var(--fs-sm); }
.sh-good { background: rgba(21,128,61,.06); border-left: 3px solid #15803d; }
.sh-bad  { background: rgba(220,38,38,.04); border-left: 3px solid #dc2626; }
.sh-name { font-weight: 700; min-width: 50px; }
.sh-pillar { color: var(--text-3); font-size: var(--fs-xs); min-width: 30px; }
.sh-meaning { color: var(--text-2); flex: 1; }

/* 大运升级 */
.dayun-item { text-align: center; padding: var(--sp-3) var(--sp-4); background: var(--surface-2); border-radius: var(--radius-sm); border: 1px solid var(--border); min-width: 90px; max-width: 160px; flex: 1; }
.dayun-item.cur { border-color: var(--accent); background: rgba(217,119,6,.06); }
.dayun-tg { font-size: var(--fs-xs); color: var(--text-3); margin-top: 2px; }
.dayun-narrative { font-size: 10px; color: var(--text-2); line-height: 1.5; margin-top: 4px; text-align: left; }
.dayun-hints { display: flex; flex-direction: column; gap: 2px; margin-top: 4px; }
.dh-tag { font-size: 9px; padding: 1px 4px; border-radius: 2px; text-align: left; }
.dh-wealth { background: rgba(21,128,61,.1); color: #15803d; }
.dh-health { background: rgba(37,99,235,.1); color: #1d4ed8; }
.dh-love { background: rgba(217,119,6,.1); color: #92400e; }

/* 五行均衡 */
.wx-balance { margin-top: var(--sp-4); padding: var(--sp-4); background: var(--surface-2); border-radius: var(--radius-sm); border: 1px solid var(--border); }
.wx-balance-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--sp-2); }
.wx-bal-lbl { font-size: var(--fs-sm); color: var(--text-2); }
.wx-bal-val { font-size: var(--fs-xl); font-weight: 700; }
.wx-imbalance { display: flex; gap: var(--sp-4); margin-bottom: var(--sp-2); font-size: var(--fs-sm); }
.wx-weak { color: #dc2626; }
.wx-strong { color: #d97706; }
.wx-advice { font-size: var(--fs-sm); color: var(--text-2); margin: 0; }

/* 四维分析 */
.analysis-card { background: var(--surface-2); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: var(--sp-5); margin-bottom: var(--sp-4); }
.ac-header { display: flex; align-items: center; gap: var(--sp-2); margin-bottom: var(--sp-3); flex-wrap: wrap; }
.ac-icon { font-size: var(--fs-lg); }
.ac-title { font-size: var(--fs-lg); font-weight: 700; flex: 1; }
.ac-score { font-size: var(--fs-2xl); font-weight: 800; }
.ac-score small { font-size: var(--fs-xs); font-weight: 400; color: var(--text-3); }
.ac-tier { font-size: var(--fs-xs); padding: 2px 8px; border-radius: 10px; background: rgba(217,119,6,.10); color: #92400e; font-weight: 600; }
.tier-warn { background: rgba(220,38,38,.1); color: #dc2626; }
.ac-range { font-size: var(--fs-sm); color: var(--text-2); margin-bottom: var(--sp-3); }
.ac-tags { display: flex; align-items: center; flex-wrap: wrap; gap: 5px; margin-bottom: var(--sp-2); }
.ac-tag-lbl { font-size: var(--fs-xs); color: var(--text-3); flex-shrink: 0; }
.ac-tag { font-size: var(--fs-xs); padding: 2px 8px; background: var(--surface); border: 1px solid var(--border-md); border-radius: 10px; }
.ac-tag-warn { background: #fee2e2; border-color: #fca5a5; color: #dc2626; }
.ac-row { display: flex; flex-wrap: wrap; gap: var(--sp-4); font-size: var(--fs-sm); color: var(--text-2); margin-bottom: var(--sp-2); }
.ac-text { font-size: var(--fs-md); color: var(--text); line-height: 1.7; margin-bottom: var(--sp-2); }
.ac-sub { font-size: var(--fs-sm); color: var(--text-2); margin-bottom: 3px; }
.ac-interp { font-size: var(--fs-sm); color: var(--text-3); line-height: 1.6; border-top: 1px solid var(--border); padding-top: var(--sp-2); margin-top: var(--sp-2); }
.ac-health-tips { display: flex; flex-direction: column; gap: 4px; margin: var(--sp-2) 0; }
.ht-row { display: flex; align-items: center; gap: 5px; flex-wrap: wrap; }
.ht-lbl { font-size: var(--fs-xs); color: var(--text-3); width: 32px; flex-shrink: 0; }
.ht-item { font-size: var(--fs-xs); padding: 2px 7px; background: var(--surface); border: 1px solid var(--border-md); border-radius: 10px; }

/* 流年四维 */
.liunian-detail-list { display: flex; flex-direction: column; gap: var(--sp-3); margin-bottom: var(--sp-5); }
.ld-item { padding: var(--sp-4); background: var(--surface-2); border: 1px solid var(--border); border-radius: var(--radius-sm); }
.ld-head { display: flex; align-items: center; gap: var(--sp-3); margin-bottom: var(--sp-2); }
.ld-gz { font-size: var(--fs-lg); font-weight: 700; font-family: var(--font-cn); }
.ld-year { font-size: var(--fs-sm); color: var(--text-2); }
.ld-score { font-size: var(--fs-xl); font-weight: 700; margin-left: auto; }
.ld-tg { font-size: var(--fs-xs); color: var(--text-3); padding: 1px 6px; background: var(--surface); border: 1px solid var(--border-md); border-radius: 10px; }
.ld-domains { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 6px; }
.ld-domain { display: flex; gap: 4px; font-size: var(--fs-xs); padding: 3px 8px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-sm); }
.ld-dk { color: var(--text-3); }
.ld-dv { color: var(--text); }
.ld-action { font-size: var(--fs-sm); color: var(--accent-dark); background: rgba(217,119,6,.08); border-radius: var(--radius-sm); padding: 4px 10px; margin: 0; }
.ld-taisui { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 4px; }
.ld-ts-tag { font-size: var(--fs-xs); padding: 1px 6px; background: #fef3c7; color: #b45309; border-radius: 4px; }
.ld-notable { display: flex; align-items: center; gap: var(--sp-2); flex-wrap: wrap; margin-top: 4px; }
.ld-notable-lbl { font-size: var(--fs-xs); color: var(--text-3); }
.ld-notable-m { font-size: var(--fs-xs); padding: 1px 6px; background: var(--accent-soft); color: var(--accent); border-radius: 4px; font-weight: 600; }

/* 当前运势概况 */
.cfs-info { display: flex; flex-wrap: wrap; gap: var(--sp-3); margin-bottom: var(--sp-3); font-size: var(--fs-sm); color: var(--text-2); }
.cfs-info b { color: var(--text); font-weight: 700; }
.cfs-domains { display: flex; flex-wrap: wrap; gap: var(--sp-2); margin-bottom: var(--sp-3); }
.cfs-dom { display: flex; gap: 4px; font-size: var(--fs-sm); padding: 3px 8px; background: var(--surface-2); border: 1px solid var(--border); border-radius: var(--radius-sm); }
.cfs-dk { color: var(--accent); font-weight: 600; }
.cfs-dv { color: var(--text); }
.cfs-actions { padding: var(--sp-3); background: rgba(217,119,6,.05); border-radius: var(--radius-sm); }
.cfs-actions-title { font-size: var(--fs-sm); font-weight: 600; color: var(--accent-dark); margin-bottom: var(--sp-2); }
.cfs-action { font-size: var(--fs-sm); color: var(--text); margin-bottom: 2px; }

/* 人生里程碑 */
.milestones-list { display: flex; flex-direction: column; gap: var(--sp-3); }
.ms-item { padding: var(--sp-3); background: var(--surface-2); border-radius: var(--radius-sm); border-left: 3px solid var(--border-md); }
.ms-item.ms-高 { border-left-color: #dc2626; }
.ms-item.ms-中 { border-left-color: #f59e0b; }
.ms-item.ms-低 { border-left-color: #22c55e; }
.ms-head { display: flex; flex-wrap: wrap; align-items: center; gap: var(--sp-2); margin-bottom: var(--sp-2); }
.ms-age { font-weight: 700; font-size: var(--fs-md); color: var(--accent); }
.ms-year { font-size: var(--fs-sm); color: var(--text-3); }
.ms-type { font-size: var(--fs-xs); padding: 1px 8px; border-radius: 10px; background: var(--accent-soft); color: var(--accent); font-weight: 600; }
.ms-gz { font-size: var(--fs-xs); color: var(--text-3); margin-left: auto; }
.ms-desc { font-size: var(--fs-sm); color: var(--text); line-height: 1.5; margin: 0 0 4px; }
.ms-advice { font-size: var(--fs-sm); color: var(--accent-dark); margin: 0; }

/* 月运 */
.monthly-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); gap: var(--sp-2); }
.monthly-item { padding: var(--sp-3); border-radius: var(--radius-sm); border: 1px solid var(--border); background: var(--surface-2); }
.ml-head { display: flex; align-items: center; gap: 4px; margin-bottom: 4px; }
.ml-month { font-size: var(--fs-sm); font-weight: 700; }
.ml-gz { font-size: 10px; color: var(--text-3); flex: 1; }
.ml-luck { font-size: 10px; padding: 0 4px; border-radius: 3px; font-weight: 700; }
.ml-luck-吉 { background: #dcfce7; color: #15803d; }
.ml-luck-凶 { background: #fee2e2; color: #dc2626; }
.ml-luck-平 { background: var(--surface); color: var(--text-3); border: 1px solid var(--border-md); }
.ml-tip { font-size: 10px; color: var(--text-2); line-height: 1.4; margin: 0; }
.ml-color { width: 100%; height: 3px; border-radius: 2px; margin-top: 4px; opacity: 0.6; }

.section-block { margin-bottom: var(--sp-6); }
.section-title { font-size: var(--fs-lg); font-weight: 600; margin-bottom: var(--sp-4); color: var(--text); }

/* 免责声明 */
.ac-disclaimer { font-size: var(--fs-xs); color: var(--text-3); font-style: italic; background: rgba(0,0,0,.03); border-radius: var(--radius-sm); padding: 4px 10px; margin-top: var(--sp-2); }
.ac-sub-warn { color: #dc2626; }

/* 大运财运趋势 */
.ac-dayun-fc { margin: var(--sp-2) 0; }
.ac-df-item { display: inline-flex; gap: 4px; font-size: var(--fs-xs); padding: 2px 8px; background: var(--surface); border: 1px solid var(--border-md); border-radius: var(--radius-sm); margin: 2px 4px 2px 0; }
.ac-df-gz { font-weight: 600; color: var(--text); }
.ac-df-trend { color: var(--text-2); }

/* 性格扩展 */
.pers-extra { margin-top: var(--sp-2); display: flex; flex-direction: column; gap: 2px; }
.pers-sub { font-size: var(--fs-sm); color: var(--text-2); margin: 0; }

/* 格局增强 */
.geju-broken-badge { display: inline-block; font-size: 10px; padding: 1px 6px; border-radius: 10px; background: rgba(220,38,38,.12); color: #dc2626; font-weight: 600; margin-left: 4px; }
.geju-conf { font-size: var(--fs-xs); color: var(--text-3); margin-left: 6px; }
.ov-classic-ref { font-size: var(--fs-xs); color: var(--text-3); font-style: italic; margin-top: 4px; }

/* 开运忌讳 */
.lucky-avoid { opacity: .85; }
.lucky-tag-avoid { background: #fee2e2; border-color: #fca5a5; color: #dc2626; }

/* 十二宫 */
.ov-card-wide { grid-column: 1 / -1; }
.twelve-palaces { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 6px; margin: var(--sp-3) 0; }
.tp-item { display: flex; align-items: center; gap: 4px; padding: 4px 8px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-sm); font-size: var(--fs-xs); }
.tp-name { font-weight: 600; color: var(--text); }
.tp-dizhi { color: var(--accent); font-weight: 600; }
.tp-ss { color: var(--text-3); }
.tp-tg { color: var(--text-2); }
.tp-str { font-size: 10px; padding: 0 4px; border-radius: 3px; }
.tp-str-旺 { background: #dcfce7; color: #15803d; }
.tp-str-相 { background: #e0f2fe; color: #0369a1; }
.tp-str-休 { background: #f5f5f4; color: #78716c; }
.tp-str-囚 { background: #fef3c7; color: #b45309; }
.tp-str-死 { background: #fee2e2; color: #dc2626; }
.tp-note { color: var(--text-3); flex: 1; text-align: right; }

/* 六亲人际 */
.ac-liuqin { display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); gap: 6px; margin-bottom: var(--sp-3); }
.lq-item { display: flex; gap: 4px; font-size: var(--fs-sm); padding: 3px 8px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-sm); }
.lq-key { color: var(--text-3); font-weight: 600; }
.lq-val { color: var(--text); }
.ac-tag-noble { background: #fef3c7; border-color: #fbbf24; color: #92400e; }

/* 饰品 */
.jewelry-items { display: grid; grid-template-columns: 1fr 1fr; gap: var(--sp-3); margin-bottom: var(--sp-3); }
.ji-card { padding: var(--sp-3); background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-sm); }
.ji-primary { border-color: var(--accent); border-width: 1.5px; }
.ji-label { font-size: var(--fs-xs); color: var(--text-3); font-weight: 600; margin-bottom: 4px; }
.ji-detail { font-size: var(--fs-md); font-weight: 600; margin-bottom: 4px; }
.ji-gem { color: var(--accent); margin-left: 6px; }
.ji-meta { font-size: var(--fs-xs); color: var(--text-2); display: flex; gap: var(--sp-3); }

/* 月运扩展 */
.ml-extra { display: flex; gap: 4px; flex-wrap: wrap; margin-top: 2px; }
.ml-clash { font-size: 9px; padding: 0 4px; border-radius: 3px; background: #fee2e2; color: #dc2626; }
.ml-rel { font-size: 9px; padding: 0 4px; border-radius: 3px; background: #f0f9ff; color: #0369a1; }

/* 流年冲克 */
.ld-clash-pillars { display: flex; align-items: center; gap: var(--sp-2); flex-wrap: wrap; margin-top: 4px; }
.ld-flow-wx { font-size: var(--fs-xs); color: var(--text-3); margin-top: 4px; display: inline-block; }

/* 警告 + 版本 */
.bazi-warnings { margin-top: var(--sp-4); }
.bw-item { font-size: var(--fs-sm); color: #b45309; background: #fef3c7; border: 1px solid #fbbf24; border-radius: var(--radius-sm); padding: 6px 12px; margin-bottom: 4px; }
.bw-code { font-weight: 600; font-size: var(--fs-xs); }
/* ─── 年份事件预测 ─────────────────────────────────────────── */
.yev-timeline-summary { font-size: var(--fs-sm); color: var(--text-2); margin-bottom: var(--sp-3); }
.yev-year-track { display: flex; gap: var(--sp-2); margin-bottom: var(--sp-4); overflow-x: auto; padding-bottom: 4px; }
.yev-year-chip { display: flex; flex-direction: column; align-items: center; gap: 2px; padding: 6px 10px; border-radius: 8px; cursor: pointer; border: 1px solid var(--border); background: var(--surface-2); min-width: 52px; transition: border-color 0.2s, background 0.2s; }
.yev-year-chip:hover { border-color: var(--accent); }
.yev-year-active { border-color: var(--accent) !important; background: color-mix(in srgb, var(--accent) 10%, var(--surface-2)) !important; }
.yev-year-num { font-size: var(--fs-xs); color: var(--text-2); }
.yev-year-gz { font-size: var(--fs-sm); font-weight: 600; color: var(--text); }
.yev-year-score-bar { width: 24px; border-radius: 3px; margin: 2px 0; }
.bar-good { background: #4ade80; } .bar-bad { background: #f87171; } .bar-mid { background: #fbbf24; }
.yev-year-risk { font-size: 10px; }
.yev-controls { display: flex; align-items: center; gap: var(--sp-4); flex-wrap: wrap; margin-bottom: var(--sp-4); }
.yev-year-pick { display: flex; align-items: center; gap: var(--sp-2); } .yev-year-pick label { font-size: var(--fs-sm); color: var(--text-2); white-space: nowrap; } .yev-year-pick input { width: 80px; padding: 4px 8px; border: 1px solid var(--border); border-radius: 6px; background: var(--surface-2); color: var(--text); }
.yev-event-pills { display: flex; gap: var(--sp-2); flex-wrap: wrap; }
.evt-pill { padding: 5px 14px; border-radius: 20px; border: 1px solid var(--border); background: var(--surface-2); font-size: var(--fs-sm); color: var(--text-2); cursor: pointer; transition: all 0.15s; }
.evt-pill:hover { border-color: var(--accent); color: var(--text); }
.evt-pill-active { border-color: var(--accent); background: color-mix(in srgb, var(--accent) 15%, var(--surface-2)); color: var(--accent); font-weight: 600; }
.yev-result-card { border: 1px solid var(--border); border-radius: 12px; padding: var(--sp-4); margin-bottom: var(--sp-4); }
.yev-result-header { display: flex; flex-wrap: wrap; align-items: center; gap: var(--sp-2); margin-bottom: var(--sp-3); }
.yev-event-name { font-size: var(--fs-lg); font-weight: 700; color: var(--text); }
.yev-gz { font-size: var(--fs-sm); color: var(--text-2); }
.yev-risk-badge, .yev-opp-badge { font-size: var(--fs-xs); padding: 2px 8px; border-radius: 4px; font-weight: 600; }
.risk-high { background: #fee2e2; color: #dc2626; } .risk-medium_high { background: #fef3c7; color: #d97706; } .risk-medium { background: #fef3c7; color: #ca8a04; } .risk-low { background: #f0fdf4; color: #16a34a; } .risk-none { background: var(--surface-2); color: var(--text-2); }
.opp-high { background: #d1fae5; color: #059669; } .opp-medium_high { background: #d1fae5; color: #16a34a; } .opp-medium { background: #ecfdf5; color: #22c55e; } .opp-low { background: var(--surface-2); color: var(--text-2); } .opp-none { background: var(--surface-2); color: var(--text-2); }
.yev-conf { font-size: var(--fs-xs); color: var(--text-2); margin-left: auto; }
.yev-main-judgment { font-size: var(--fs-md); color: var(--text); line-height: 1.6; margin-bottom: var(--sp-2); font-weight: 500; }
.yev-trigger-summary { font-size: var(--fs-sm); color: var(--text-2); margin-bottom: var(--sp-3); }
.yev-signals { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: var(--sp-3); }
.yev-sig-chip { display: inline-flex; align-items: center; gap: 4px; padding: 3px 10px; border-radius: 12px; font-size: var(--fs-xs); border: 1px solid var(--border); background: var(--surface-2); }
.layer-natal_base { border-color: #c4b5fd; background: #f5f3ff; } .layer-dayun_trigger { border-color: #93c5fd; background: #eff6ff; } .layer-liunian_trigger { border-color: #6ee7b7; background: #ecfdf5; } .layer-month_trigger { border-color: #fde68a; background: #fffbeb; }
.sig-layer-lbl { font-size: 10px; color: var(--text-2); }
.sig-label { font-size: var(--fs-xs); color: var(--text); }
.yev-months { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; margin-bottom: var(--sp-3); }
.yev-months-lbl { font-size: var(--fs-sm); color: var(--text-2); white-space: nowrap; }
.yev-month-tag { padding: 2px 8px; background: color-mix(in srgb, var(--accent) 15%, var(--surface-2)); color: var(--accent); border-radius: 4px; font-size: var(--fs-xs); font-weight: 600; }
.yev-list-block { margin-bottom: var(--sp-3); }
.yev-list-title { font-size: var(--fs-sm); font-weight: 600; color: var(--text-2); margin-bottom: var(--sp-1); }
.yev-list { margin: 0; padding-left: 1.2em; font-size: var(--fs-sm); color: var(--text); line-height: 1.7; }
.yev-advice .yev-list-title { color: var(--accent); }
.yev-classical { font-size: var(--fs-xs); color: var(--text-2); margin-bottom: var(--sp-2); }
.yev-classical-note { margin-right: var(--sp-3); }
.yev-overclaim { font-size: var(--fs-xs); color: #d97706; background: #fffbeb; border: 1px solid #fde68a; border-radius: 6px; padding: 6px 10px; margin-top: var(--sp-2); }
.yev-consult-block { margin-top: var(--sp-4); border-top: 1px solid var(--border); padding-top: var(--sp-4); }
.yev-consult-title { font-size: var(--fs-md); font-weight: 700; color: var(--text); margin-bottom: var(--sp-3); }
.yev-consult-input-row { display: flex; gap: var(--sp-2); margin-bottom: var(--sp-3); }
.yev-consult-input { flex: 1; padding: 8px 12px; border: 1px solid var(--border); border-radius: 8px; background: var(--surface-2); color: var(--text); font-size: var(--fs-sm); }
.yev-consult-input:focus { outline: none; border-color: var(--accent); }
.yev-ask-btn { white-space: nowrap; }
.yev-followup-row { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: var(--sp-3); }
.yev-followup-btn { padding: 4px 12px; font-size: var(--fs-xs); border: 1px solid var(--border); border-radius: 14px; background: var(--surface-2); color: var(--text-2); cursor: pointer; transition: border-color 0.15s; }
.yev-followup-btn:hover { border-color: var(--accent); color: var(--text); }
.yev-consult-result { background: var(--surface-2); border-radius: 8px; padding: var(--sp-4); border: 1px solid var(--border); }
.yev-consult-pre { white-space: pre-wrap; word-break: break-word; font-family: var(--font-cn); font-size: var(--fs-sm); color: var(--text); line-height: 1.8; margin: 0; }
.yev-no-trend, .yev-empty { padding: var(--sp-4) 0; }
.yev-loading { color: var(--text-2); font-size: var(--fs-sm); padding: var(--sp-3) 0; }
.yev-save-hint {
  display: flex; flex-direction: column; align-items: flex-start;
  padding: var(--sp-3) var(--sp-4);
  background: color-mix(in srgb, var(--accent) 6%, var(--surface-2));
  border: 1px dashed var(--border);
  border-radius: 8px;
  margin-bottom: var(--sp-3);
}
.yev-save-hint p { margin: 0; font-size: var(--fs-sm); }
.yev-trend-block { margin-bottom: var(--sp-4); }

.bazi-version-footer { margin-top: var(--sp-4); font-size: var(--fs-xs); color: var(--text-3); display: flex; gap: var(--sp-3); justify-content: flex-end; opacity: .6; }

@media (max-width: 600px) {
  .pillars-tbl th { font-size: 11px; padding: 6px 6px; }
  .pillars-tbl td { padding: 6px 6px; }
  .gz-char { font-size: var(--fs-xl); }
  .overview-guide-head { flex-direction: column; }
  .overview-guide-grid { grid-template-columns: 1fr; }
  .overview-grid { grid-template-columns: 1fr; }
  .life-arc-periods { grid-template-columns: 1fr; }
  .personality-cols { grid-template-columns: 1fr; }
  .wx-chart-row { flex-direction: column; }
  .wx-radar-wrap { width: 100%; max-width: 220px; margin: 0 auto; }
}

/* ── 打印 / PDF 样式 ── */
@media print {
  .app-nav, .form-card-wrap, .tabs, .suggest-name-row, .no-print { display: none !important; }
  .wrap { padding: 0 !important; }
  .tab-panel { display: block !important; page-break-inside: avoid; }
  .pillars-tbl-wrap { overflow: visible; }
  .dayun-timeline-wrap { overflow: visible; }
  .dy-track { flex-wrap: wrap; min-width: 0; }
  h1, h2, h3 { page-break-after: avoid; }
  .card, .ov-card { box-shadow: none; border: 1px solid #ccc; }
  .bazi-summary-block { background: #fffbeb !important; }
  body { font-size: 11pt; }
}

/* 五行雷达图 */
.wx-chart-row { display: flex; gap: var(--sp-6); align-items: flex-start; margin-bottom: var(--sp-4); flex-wrap: wrap; }
.wx-radar-wrap { flex: 0 0 200px; }
.wx-radar-svg { width: 200px; height: 200px; }
.radar-label { font-size: 12px; font-family: var(--font-cn); font-weight: 700; }
.wuxing-list { flex: 1; min-width: 200px; display: flex; flex-direction: column; gap: var(--sp-3); }

/* ── 无 Tab 直接展示的内联节 ── */
.section-inline { margin-bottom: var(--sp-5); }
.section-inline .card-title { font-size: var(--fs-xl); font-weight: 700; padding-bottom: var(--sp-3); border-bottom: 1px solid var(--border); margin-bottom: var(--sp-4); }

/* 三核铺满 */
.ov-core-full { margin-bottom: var(--sp-4); }

/* 底部操作行 */
.suggest-name-row--bottom { margin-top: var(--sp-2); margin-bottom: var(--sp-6); }

/* ══ 人生弧线 ══ */
.life-motto { font-size: var(--fs-lg); font-style: italic; color: var(--text-2); border-left: 3px solid var(--accent); padding: 6px 12px; margin-bottom: var(--sp-3); }
.life-tier-badge { display: inline-block; font-size: var(--fs-sm); background: var(--accent-soft); color: var(--accent-dark); border-radius: 20px; padding: 2px 12px; margin-bottom: var(--sp-3); }
.life-arc-phases { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: var(--sp-3); margin-bottom: var(--sp-4); }
.arc-phase { background: var(--surface-2); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: var(--sp-3); }
.arc-phase-label { display: inline-block; font-size: var(--fs-xs); font-weight: 700; padding: 1px 8px; border-radius: 10px; background: var(--accent-soft); color: var(--accent-dark); margin-bottom: var(--sp-2); }
.arc-phase-text { font-size: var(--fs-sm); color: var(--text); line-height: 1.55; margin: 0; }
.life-action-hint { font-size: var(--fs-sm); color: var(--accent-dark); background: rgba(217,119,6,.07); border-radius: var(--radius-sm); padding: 6px 12px; margin-bottom: var(--sp-3); }
.life-periods { display: flex; flex-direction: column; gap: var(--sp-2); margin-top: var(--sp-3); }
.period-group { display: flex; align-items: center; gap: var(--sp-2); flex-wrap: wrap; }
.period-lbl { font-size: var(--fs-xs); font-weight: 700; padding: 1px 8px; border-radius: 10px; }
.period-peak { background: #dcfce7; color: #15803d; }
.period-caution { background: #fee2e2; color: #dc2626; }
.period-tag { font-size: var(--fs-xs); padding: 2px 8px; border-radius: 10px; }
.period-tag-peak { background: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; }
.period-tag-caution { background: #fff1f2; color: #be123c; border: 1px solid #fecdd3; }

/* ══ 性格分析 ══ */
.personality-col { flex: 1; min-width: 140px; }
.plist-label { display: block; font-size: var(--fs-xs); font-weight: 700; padding: 1px 8px; border-radius: 10px; margin-bottom: var(--sp-2); }
.plist-adv { background: #dcfce7; color: #15803d; }
.plist-dis { background: #fee2e2; color: #dc2626; }
.plist { margin: 0; padding-left: 18px; }
.plist li { font-size: var(--fs-sm); color: var(--text); line-height: 1.6; }
.plist-dis-items li { color: #b45309; }
.personality-extra-row { display: flex; gap: var(--sp-3); font-size: var(--fs-sm); padding: 4px 0; border-top: 1px solid var(--border); }
.pex-key { color: var(--text-3); font-weight: 600; min-width: 70px; }
.pex-val { color: var(--text); flex: 1; }
.personality-growth { font-size: var(--fs-sm); color: var(--accent-dark); background: rgba(217,119,6,.07); border-radius: var(--radius-sm); padding: 6px 12px; margin-top: var(--sp-3); }

/* ══ 四维分析 ══ */
.quad-scores { display: grid; grid-template-columns: repeat(auto-fit, minmax(100px, 1fr)); gap: var(--sp-3); margin-bottom: var(--sp-4); }
.quad-card { text-align: center; padding: var(--sp-3); background: var(--surface-2); border: 1px solid var(--border); border-radius: var(--radius-sm); }
.quad-score-num { font-size: 28px; font-weight: 700; line-height: 1; margin-bottom: 4px; }
.quad-label { font-size: var(--fs-xs); font-weight: 700; color: var(--text-2); }
.quad-tier { font-size: var(--fs-xs); color: var(--text-3); margin-top: 2px; }
.quad-detail { margin-bottom: var(--sp-2); background: var(--surface-2); border: 1px solid var(--border); border-radius: var(--radius-sm); overflow: hidden; }
.quad-summary { font-size: var(--fs-sm); font-weight: 600; padding: var(--sp-2) var(--sp-3); cursor: pointer; list-style: none; user-select: none; }
.quad-summary::-webkit-details-marker { display: none; }
.quad-summary::before { content: '▶ '; font-size: 10px; color: var(--text-3); transition: transform .2s; }
details[open] .quad-summary::before { content: '▼ '; }
.quad-body { padding: 0 var(--sp-3) var(--sp-3); border-top: 1px solid var(--border); }
.quad-row { display: flex; gap: var(--sp-3); font-size: var(--fs-sm); padding: 3px 0; margin: 0; }
.qk { color: var(--text-3); font-weight: 600; min-width: 72px; flex-shrink: 0; }
.quad-text { font-size: var(--fs-sm); color: var(--text); line-height: 1.55; margin: var(--sp-2) 0 0; padding: var(--sp-2); background: var(--surface); border-radius: 4px; }

/* ══ 开运信息 ══ */
.lucky-grid { display: flex; flex-direction: column; gap: var(--sp-3); }
.lucky-item { display: flex; align-items: center; gap: var(--sp-3); flex-wrap: wrap; }
.lucky-key { font-size: var(--fs-xs); font-weight: 700; color: var(--text-3); min-width: 60px; }
.lucky-colors { display: flex; flex-wrap: wrap; gap: 6px; }
.lucky-color-tag { font-size: var(--fs-xs); padding: 2px 10px; border-radius: 10px; background: #fef3c7; color: #92400e; border: 1px solid #fbbf24; font-weight: 600; }
.avoid-color-tag { font-size: var(--fs-xs); padding: 2px 10px; border-radius: 10px; background: #fee2e2; color: #dc2626; border: 1px solid #fca5a5; font-weight: 600; }
.lucky-val { font-size: var(--fs-sm); color: var(--text); font-weight: 500; }

/* ══ 神煞 ══ */
.shensha-table-wrap { overflow-x: auto; }
.shensha-table { width: 100%; border-collapse: collapse; font-size: var(--fs-sm); }
.shensha-table th { font-size: var(--fs-xs); font-weight: 700; color: var(--text-3); padding: 5px 10px; background: var(--surface-2); border-bottom: 2px solid var(--border-md); text-align: left; }
.shensha-table td { padding: 6px 10px; border-bottom: 1px solid var(--border); vertical-align: middle; }
.shensha-table tr.ss-good { background: rgba(21,128,61,.04); }
.shensha-table tr.ss-bad { background: rgba(220,38,38,.03); }
.ss-badge { display: inline-block; font-size: var(--fs-xs); font-weight: 700; padding: 1px 8px; border-radius: 10px; }
.ss-ji { background: #dcfce7; color: #15803d; }
.ss-xiong { background: #fee2e2; color: #dc2626; }
.ss-meaning { color: var(--text-2); line-height: 1.5; max-width: 380px; }

/* ══ 人生里程碑（新模板）══ */
.milestone-item { display: flex; gap: var(--sp-3); padding: var(--sp-3) 0; border-bottom: 1px solid var(--border); position: relative; }
.milestone-item:last-child { border-bottom: none; }
.ms-timeline-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; margin-top: 5px; background: var(--border-md); }
.ms-high .ms-timeline-dot { background: #dc2626; }
.ms-mid .ms-timeline-dot { background: #f59e0b; }
.ms-low .ms-timeline-dot { background: #22c55e; }
.ms-content { flex: 1; min-width: 0; }
.ms-header { display: flex; flex-wrap: wrap; align-items: center; gap: var(--sp-2); margin-bottom: 4px; }
.ms-age { font-weight: 700; font-size: var(--fs-md); color: var(--accent); }
.ms-year { font-size: var(--fs-sm); color: var(--text-3); }
.ms-type { font-size: var(--fs-xs); padding: 1px 8px; border-radius: 10px; background: var(--accent-soft); color: var(--accent); font-weight: 600; }
.ms-gz { font-size: var(--fs-xs); color: var(--text-3); margin-left: auto; }
.ms-desc { font-size: var(--fs-sm); color: var(--text); line-height: 1.55; margin: 0 0 4px; }
.ms-advice { font-size: var(--fs-sm); color: var(--accent-dark); margin: 0; }

/* ══ 月运概览（新模板）══ */
.monthly-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(66px, 1fr)); gap: 6px; margin-bottom: var(--sp-2); }
.monthly-cell { padding: var(--sp-2) 6px; border-radius: var(--radius-sm); border: 1px solid var(--border); cursor: default; text-align: center; display: flex; flex-direction: column; align-items: center; gap: 2px; transition: opacity .15s; }
.monthly-cell:hover { opacity: .8; }
.mo-ji { background: #f0fdf4; border-color: #86efac; }
.mo-xiong { background: #fff1f2; border-color: #fda4af; }
.mo-ping { background: var(--surface-2); border-color: var(--border); }
.mo-month { font-size: var(--fs-xs); font-weight: 700; color: var(--text); }
.mo-gz { font-size: 10px; color: var(--text-3); }
.mo-level { font-size: var(--fs-xs); font-weight: 700; padding: 0 4px; border-radius: 3px; }
.mo-ji .mo-level { color: #15803d; }
.mo-xiong .mo-level { color: #dc2626; }
.mo-ping .mo-level { color: var(--text-3); }
.monthly-hint { font-size: var(--fs-xs); color: var(--text-3); text-align: right; margin: 0; }

/* ══ 命盘速读条 (pillars-qbar) ══ */
.pillars-qbar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px 0;
  padding: 11px 16px;
  margin: var(--sp-3) 0 var(--sp-2);
  background: linear-gradient(135deg, rgba(217,119,6,.06), var(--surface));
  border: 1px solid rgba(217,119,6,.20);
  border-radius: var(--radius-sm);
}
.pqb-item   { display: flex; align-items: center; gap: 5px; }
.pqb-key    { font-size: 11px; color: var(--text-3); font-weight: 600; letter-spacing: .04em; }
.pqb-gz     { font-size: var(--fs-lg); font-weight: 700; font-family: var(--font-cn); }
.pqb-wx     { font-size: var(--fs-xs); color: var(--text-3); }
.pqb-main   { font-size: var(--fs-md); font-weight: 700; color: var(--text); }
.pqb-badge  { font-size: 10px; padding: 1px 6px; border-radius: 10px; background: rgba(217,119,6,.12); color: #92400e; font-weight: 600; }
.pqb-favor-tag { font-size: var(--fs-xs); padding: 2px 8px; border-radius: 10px; background: #dcfce7; color: #15803d; font-weight: 600; }
.pqb-avoid-sep { font-size: var(--fs-xs); color: var(--text-3); margin: 0 3px; }
.pqb-avoid-tag { font-size: var(--fs-xs); padding: 2px 8px; border-radius: 10px; background: #fee2e2; color: #dc2626; font-weight: 600; }
.pqb-dot    { color: var(--border-md); padding: 0 9px; font-size: var(--fs-md); user-select: none; }

/* ══ 综合概览 - 命盘三核 (ov-core-trio) ══ */
.ov-core-trio {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--sp-3);
  margin-bottom: var(--sp-4);
}
.ov-trio-card {
  padding: var(--sp-4);
  background: var(--surface);
  border: 1px solid var(--border);
  border-top: 3px solid var(--accent);
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow);
}
.ov-trio-kv {
  display: flex;
  align-items: baseline;
  gap: var(--sp-2);
  flex-wrap: wrap;
  margin-bottom: 6px;
}
.ov-trio-label {
  font-size: 11px;
  color: var(--text-3);
  font-weight: 600;
  letter-spacing: .04em;
  text-transform: uppercase;
  white-space: nowrap;
  flex-shrink: 0;
}
.ov-trio-main {
  font-size: var(--fs-xl);
  font-weight: 700;
  color: var(--text);
  font-family: var(--font-cn);
  display: flex;
  align-items: baseline;
  gap: 4px;
  flex-wrap: wrap;
}
.ov-trio-score  { font-size: var(--fs-xs); color: var(--text-3); font-weight: 400; margin-left: 4px; }
.ov-trio-subbadge { font-size: 11px; padding: 1px 6px; border-radius: 10px; background: rgba(217,119,6,.12); color: #92400e; font-weight: 600; }
.ov-trio-broken { font-size: 11px; padding: 1px 6px; border-radius: 10px; background: rgba(220,38,38,.10); color: #dc2626; font-weight: 600; }
.ov-trio-hint   { font-size: var(--fs-xs); color: var(--text-3); line-height: 1.6; margin: 0; }
.ov-trio-yg     { display: flex; align-items: center; gap: 4px; flex-wrap: wrap; }
.ov-trio-favor  { font-size: var(--fs-sm); padding: 2px 10px; border-radius: 10px; background: #dcfce7; color: #15803d; font-weight: 600; }
.ov-trio-avoidlbl { font-size: var(--fs-xs); color: var(--text-3); margin: 0 2px; }
.ov-trio-avoid  { font-size: var(--fs-sm); padding: 2px 10px; border-radius: 10px; background: #fee2e2; color: #dc2626; font-weight: 600; }

@media (max-width: 600px) {
  .ov-core-trio { grid-template-columns: 1fr; }
  .pillars-qbar { gap: 6px; }
  .pqb-dot { padding: 0 4px; }
}
</style>