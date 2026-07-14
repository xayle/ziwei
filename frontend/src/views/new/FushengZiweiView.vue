<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import SummaryStrip from '@/components/fusheng/SummaryStrip.vue'
import AnalysisPanel, { type AnalysisBlock } from '@/components/fusheng/AnalysisPanel.vue'
import FushengZiweiPlate from '@/components/fusheng/FushengZiweiPlate.vue'
import ResultStateCard from '@/components/new/ResultStateCard.vue'
import { useFushengFlow } from '@/composables/useFushengFlow'
import { useFushengReport } from '@/composables/useFushengReport'
import { useZiweiPageExplain } from '@/composables/useZiweiPageExplain'
import { validateBaziZiweiConsistency } from '@/utils/crossValidation'
import { useEngineTrustDisplay } from '@/composables/useEngineTrustDisplay'
import EngineTrustPanel from '@/components/fusheng/EngineTrustPanel.vue'
import TrustDegradedBanner from '@/components/fusheng/TrustDegradedBanner.vue'
import CodexPanel from '@/components/fusheng/CodexPanel.vue'
import ZiweiFlyingTab from '@/components/ziwei/ZiweiFlyingTab.vue'
import ZiweiAlgoSettings from '@/components/ziwei/ZiweiAlgoSettings.vue'
import { useProfileStore } from '@/stores/profile'
import PalaceAnalysisGrid from '@/components/fusheng/PalaceAnalysisGrid.vue'
import VolumeHead from '@/components/fusheng/VolumeHead.vue'
import { buildZiweiInsightBlocks, buildPatternAnalysisBlocks } from '@/utils/buildZiweiInsightBlocks'
import { truncateText } from '@/utils/truncateText'
import '@/assets/fusheng-page.css'

const depth = ref<'overview' | 'structure' | 'deep'>('overview')

const router = useRouter()
const profile = useProfileStore()
const { isArchiveComplete, navigateToStep, profileData } = useFushengFlow()
const {
  loadingZiwei,
  error,
  ziwei,
  bazi,
  isCacheValid,
  requestMeta,
  loadZiwei,
} = useFushengReport()
const {
  loadingExplain,
  explainFailed,
  explainAnalysisBlocks,
  loadPageExplain,
  resetPageExplain,
} = useZiweiPageExplain()
const {
  missingFields,
  provenanceRows,
  ziweiStructural,
  palaceStructured,
  iztro,
} = useEngineTrustDisplay(ref(null), ziwei)

const crossValidation = computed(() => validateBaziZiweiConsistency(bazi.value, ziwei.value))
const showCrossValidationHint = computed(() =>
  Boolean(bazi.value) && crossValidation.value.overall !== 'pass',
)

const summaryItems = computed(() => {
  const r = ziwei.value
  if (!r) return [{ label: '状态', value: '待计算' }]
  return [
    { label: '五行局', value: r.wuxing_ju_name || '缺失' },
    { label: '命宫', value: r.life_palace_gz || '缺失' },
    { label: '身宫', value: r.body_palace_gz || '缺失' },
    { label: '命主', value: r.life_ruler_star || '缺失' },
  ]
})

const patternBlocks = computed((): AnalysisBlock[] => {
  const r = ziwei.value
  if (!r) return []
  const patternItems = buildPatternAnalysisBlocks(r.patterns, 6)
  const blocks: AnalysisBlock[] = [
    ...patternItems,
    {
      id: 'ziwei-dayun',
      title: '大运概览（引擎）',
      lead: r.dayun?.items?.[0]?.ganzhi || '大运序列',
      body: `共 ${r.dayun?.items?.length ?? 0} 步大运（列表数据，未叠盘）。`,
      bullets: (r.dayun?.items ?? []).slice(0, 6).map((item) => {
        const age = item.start_age ?? '—'
        return `${item.ganzhi || '—'}（${age} 岁起）`
      }),
      layer: 'engine',
    },
  ]
  if (r.summary?.trim()) {
    blocks.push({
      id: 'ziwei-heuristic',
      title: '命盘摘要（启发式）',
      lead: '仅供参考',
      body: truncateText(r.summary, 80),
      layer: 'heuristic',
    })
  }
  return blocks
})

const pageLead = computed(() => {
  if (!ziwei.value?.summary?.trim()) {
    return '盘面由档案单一真相源生成，修改出生信息请回到档案页。'
  }
  return truncateText(ziwei.value.summary)
})

const degradedBannerMessage = computed(() => {
  if (iztro.value?.status === 'degraded' || iztro.value?.status === 'life_palace_mismatch') {
    return iztro.value.message
  }
  if (ziwei.value?.trust_level === 'degraded') {
    return '紫微排盘可信度已降级，请结合下方校勘与双轨对照阅读。'
  }
  if (ziwei.value?.trust_level === 'advisory') {
    return '紫微排盘为顾问级（advisory）：部分字段或月系星可能不完整，请结合校勘阅读。'
  }
  if (ziwei.value?.trust_level === 'reference') {
    return '紫微排盘为参考级（reference）：请勿单独作为完整定论。'
  }
  return null
})

const degradedBannerStatus = computed<'degraded' | 'warn'>(() => (
  ziwei.value?.trust_level === 'advisory' || ziwei.value?.trust_level === 'reference'
    ? 'warn'
    : 'degraded'
))

const insightBlocks = computed(() => buildZiweiInsightBlocks(ziwei.value))

const metaText = computed(() => {
  const meta = requestMeta.value
  if (!meta) return '口径说明将在排盘后显示。'
  return `${meta.precisionLabel} · ${meta.calendarNote} · ${meta.timeRiskLabel}`
})

const defaultExplainOpenId = computed(() => explainAnalysisBlocks.value[0]?.id ?? 'explain-palaces')
const explainPanelKey = computed(() => (
  explainAnalysisBlocks.value.map((block) => block.id).join('|') || 'pending'
))

async function load() {
  await loadZiwei()
}

watch(depth, (level) => {
  if (level !== 'deep' || !ziwei.value) return
  void loadPageExplain(profile.asProfileData())
})

watch(() => ziwei.value, () => {
  resetPageExplain()
})

function onBrightnessMethod(value: 'standard' | 'zhongzhou' | 'mod1' | 'mod2') {
  profile.setProfile({ ziweiBrightnessMethod: value })
  resetPageExplain()
  void loadZiwei(true)
}

function onYoubiMethod(value: 'month' | 'hour') {
  profile.setProfile({ ziweiYoubiMethod: value })
  resetPageExplain()
  void loadZiwei(true)
}

onMounted(() => {
  if (!isArchiveComplete.value) {
    navigateToStep('/profile')
    return
  }
  void load()
})
</script>

<template>
  <main class="fs-page ziwei-page">
    <VolumeHead
      volume-id="vol4"
      title="紫微命盘"
      title-tag="p"
      :desc="pageLead"
    >
      <template #actions>
        <button class="fs-btn fs-btn--ghost" @click="router.push('/profile')">编辑档案</button>
        <button class="fs-btn fs-btn--ghost" @click="router.push('/new/bazi')">查看八字</button>
        <button class="fs-btn fs-btn--primary" @click="router.push('/report')">进入报告</button>
      </template>
    </VolumeHead>

    <p v-if="metaText" class="fs-caliber-banner">{{ metaText }}</p>
    <p v-if="isCacheValid" class="fs-hint fs-hint--cache">已复用本次会话排盘缓存。</p>

    <ResultStateCard v-if="loadingZiwei" compact title="正在载入紫微盘" message="请稍候。" />
    <template v-else>
      <ResultStateCard
        v-if="error"
        title="紫微服务暂时不可用"
        :message="error"
        action-label="重新计算"
        @action="load"
      />

      <template v-if="ziwei">
        <TrustDegradedBanner
          v-if="degradedBannerMessage"
          :message="degradedBannerMessage"
          :status="degradedBannerStatus"
        />

        <section
          v-if="iztro?.showDualTrackTable"
          class="ziwei-zw03"
          data-testid="ziwei-zw03-dual-track"
        >
          <h3>紫微双轨对照（ZW03）</h3>
          <p class="fs-hint">
            立春前 + 晚子时等边界：引擎主盘为 canonical，不与 iztro 静默对齐。
            完整说明见报告卷二。
          </p>
          <table class="ziwei-zw03__table">
            <thead>
              <tr><th>轨道</th><th>年界</th><th>换日</th><th>命宫</th></tr>
            </thead>
            <tbody>
              <tr>
                <td>引擎主盘</td>
                <td>{{ iztro.engineTrack?.yearDivide || '—' }}</td>
                <td>{{ iztro.engineTrack?.dayDivide || '—' }}</td>
                <td><strong>{{ iztro.engineLifePalaceGz || ziwei.life_palace_gz || '—' }}</strong></td>
              </tr>
              <tr v-if="iztro.dualTrack">
                <td>{{ iztro.dualTrack.label }}</td>
                <td>{{ iztro.dualTrack.yearDivide }}</td>
                <td>{{ iztro.dualTrack.dayDivide }}</td>
                <td><strong>{{ iztro.dualTrack.lifePalaceGz }}</strong></td>
              </tr>
            </tbody>
          </table>
        </section>

        <section data-testid="ziwei-layer-summary">
          <SummaryStrip :items="summaryItems" />
        </section>

        <div class="ziwei-page__depth-row" role="group" aria-label="阅读深度">
          <div class="fs-depth-toggle" data-testid="ziwei-depth-toggle">
            <button
              type="button"
              class="fs-depth-toggle__btn"
              :class="{ 'is-active': depth === 'overview' }"
              @click="depth = 'overview'"
            >
              速览
            </button>
            <button
              type="button"
              class="fs-depth-toggle__btn"
              :class="{ 'is-active': depth === 'structure' }"
              @click="depth = 'structure'"
            >
              结构
            </button>
            <button
              type="button"
              class="fs-depth-toggle__btn"
              :class="{ 'is-active': depth === 'deep' }"
              @click="depth = 'deep'"
            >
              深读
            </button>
          </div>
        </div>

        <CodexPanel class="ziwei-hero" data-testid="ziwei-layer-plate">
          <p class="fs-section-kicker">传统方盘（本命）</p>
          <p v-if="depth === 'overview'" class="natal-scope-note natal-scope-note--compact">
            运限时间轴见
            <router-link to="/new/ziwei/timeline">紫微运限</router-link>。
          </p>
          <p v-else class="natal-scope-note">
            本命盘支持<strong>大限 / 流年 / 流月 / 飞星叠宫</strong>（方盘上方切换）。
            完整时间轴见
            <router-link to="/new/ziwei/timeline">紫微时间轴</router-link>。
          </p>
          <div class="ziwei-hero__plate">
            <FushengZiweiPlate :result="ziwei" />
          </div>
        </CodexPanel>

        <section
          v-if="depth === 'overview' && (missingFields.length || provenanceRows.length)"
          class="fs-trust-footnote"
          data-testid="ziwei-trust-overview"
        >
          <details>
            <summary>校勘提示（{{ missingFields.length }} 项）</summary>
            <EngineTrustPanel
              compact
              :missing-fields="missingFields"
              :provenance-rows="provenanceRows.slice(0, 4)"
            />
          </details>
        </section>

        <section v-if="depth !== 'overview'" class="fs-trust-footnote" data-testid="ziwei-layer-trust">
          <details :open="depth !== 'deep'">
            <summary>引擎可信度与结构（默认折叠）</summary>
            <EngineTrustPanel
              :missing-fields="missingFields"
              :provenance-rows="provenanceRows"
              :ziwei-structural="ziweiStructural"
              :palace-structured="palaceStructured"
              :iztro="iztro"
              :cross-validation-items="showCrossValidationHint ? crossValidation.items : undefined"
            />
          </details>
        </section>

        <CodexPanel v-if="depth === 'structure'">
          <h3 class="fs-section-rule">算法口径（ZiweiAlgo）</h3>
          <ZiweiAlgoSettings
            :profile="profileData"
            :provenance="ziwei.provenance"
            @update:brightness-method="onBrightnessMethod"
            @update:youbi-method="onYoubiMethod"
          />
        </CodexPanel>

        <CodexPanel v-if="depth === 'deep'" data-testid="ziwei-layer-explain">
          <h3 class="fs-section-rule">卷四·星之命（解读）</h3>
          <div v-if="explainFailed" data-testid="ziwei-explain-banner">
            <TrustDegradedBanner
              message="典籍解读暂不可用，下方为引擎宫论与格局摘要。"
              status="warn"
            />
          </div>
          <p v-else-if="loadingExplain" class="fs-hint fs-hint--cache">正在加载典籍解读…</p>
          <AnalysisPanel
            v-else-if="explainAnalysisBlocks.length"
            :key="explainPanelKey"
            :blocks="explainAnalysisBlocks"
            :default-open-id="defaultExplainOpenId"
          />
        </CodexPanel>

        <CodexPanel v-if="depth === 'deep'">
          <h3 class="fs-section-rule">飞星盘（flying）</h3>
          <ZiweiFlyingTab :flying="ziwei.flying" />
        </CodexPanel>

        <CodexPanel v-if="depth === 'deep'" data-testid="ziwei-palace-structured">
          <h3 class="fs-section-rule">宫论</h3>
          <p class="palace-structured-lead">十二宫结构化解读（引擎 COMBO 层），与报告紫微章同源。</p>
          <PalaceAnalysisGrid :rows="palaceStructured" />
        </CodexPanel>

        <CodexPanel v-if="depth === 'deep'">
          <h3 class="fs-section-rule">格局·大运分析</h3>
          <AnalysisPanel :blocks="patternBlocks" :default-open-id="patternBlocks[0]?.id" />
        </CodexPanel>

        <CodexPanel v-if="depth === 'deep' && insightBlocks.length" data-testid="ziwei-insight-section">
          <h3 class="fs-section-rule">运势与生活建议</h3>
          <AnalysisPanel :blocks="insightBlocks" default-open-id="ziwei-forecast-year" />
        </CodexPanel>
      </template>
    </template>
  </main>
</template>

<style scoped>
.ziwei-page {
  gap: 14px;
  min-width: 0;
  overflow-x: clip;
}

.ziwei-zw03 {
  display: grid;
  gap: 8px;
  padding: 12px 14px;
  border: 1px solid var(--border);
  background: var(--surface);
}

.ziwei-zw03 h3 {
  margin: 0;
  font-size: 14px;
  font-family: var(--font-cn);
  color: var(--brand-ink);
}

.ziwei-zw03__table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.ziwei-zw03__table th,
.ziwei-zw03__table td {
  border: 1px solid var(--border);
  padding: 6px 8px;
  text-align: left;
}

.fs-section-kicker {
  margin: 0 0 10px;
  font-family: var(--font-cn);
  font-size: 13px;
  color: var(--brand-mist);
  letter-spacing: 0.04em;
}

.fs-card h2 {
  margin: 0 0 14px;
  font-family: var(--font-cn);
}

.natal-scope-note--compact {
  margin: 0 0 10px;
  padding: 8px 10px;
  font-size: 12px;
}

.natal-scope-note {
  margin: 0 0 12px;
  padding: 10px 12px 10px 10px;
  border-radius: var(--radius-sm);
  background: var(--surface);
  border: 1px solid var(--border);
  border-left: 3px solid var(--brand-gold);
  font-size: 13px;
  line-height: 1.6;
  color: var(--brand-mist);
}

.natal-scope-note a {
  color: var(--brand-gold-dark);
  font-weight: 600;
}

.palace-structured-lead {
  margin: 0 0 12px;
  font-size: 13px;
  color: var(--text-3);
  line-height: 1.6;
}

.palace-structured-row {
  padding: 12px 0;
  border-top: 1px solid var(--border-soft, #e7e0d5);
}

.palace-structured-row:first-of-type {
  border-top: none;
  padding-top: 0;
}

.palace-structured-row h3 {
  margin: 0 0 8px;
  font-size: 15px;
  font-family: var(--font-cn);
}

.palace-structured-tags {
  font-weight: 400;
  font-size: 12px;
  color: var(--text-3);
}
</style>
