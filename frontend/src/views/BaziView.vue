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

<style src="./BaziView.css" scoped />