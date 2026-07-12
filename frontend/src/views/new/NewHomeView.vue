<script setup lang="ts">
import { computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import ProfileReadinessCard from '@/components/fusheng/ProfileReadinessCard.vue'
import { useFushengFlow } from '@/composables/useFushengFlow'
import { useReadingGuideExplain } from '@/composables/useReadingGuideExplain'
import ReadingGuide from '@/components/fusheng/ReadingGuide.vue'
import VolumeTocGrid from '@/components/fusheng/VolumeTocGrid.vue'
import { useReadingProgress } from '@/composables/useReadingProgress'
import { defaultDisclaimerBlock } from '@/utils/buildColophonSummary'
import { LIFE_VOLUME_LABELS } from '@/types/life-volume'
import '@/assets/fusheng-page.css'

const router = useRouter()
const {
  profile,
  completeness,
  archiveBlockers,
  archiveEnhancers,
  timeConfidence,
  isArchiveComplete,
  getArchiveBlockerLabel,
  getArchiveEnhancerLabel,
  navigateToStep,
} = useFushengFlow()
const {
  loadingReading,
  readingFailed,
  readingParagraphs,
  usingDynamicReading,
  loadReadingGuide,
} = useReadingGuideExplain()

const { lastVolumeId, save: saveReadingProgress } = useReadingProgress(() => profile.activeProfileId || 'local')
const disclaimer = defaultDisclaimerBlock()

function resumeReport() {
  if (!lastVolumeId.value) return
  saveReadingProgress(lastVolumeId.value)
  router.push('/report')
}

const resumeVolumeLabel = computed(() => (
  lastVolumeId.value ? LIFE_VOLUME_LABELS[lastVolumeId.value] : null
))

const profileLabel = computed(() => profile.activeProfile?.label || '默认档案')
const birthText = computed(() => {
  if (!profile.birthDt) return '出生信息未填写，请先补全档案'
  return `${profile.birthDt.replace('T', ' ')} · ${profile.cityName || '未填写城市'}`
})

const previewItems = computed(() => [
  { label: '档案名', value: profileLabel.value },
  { label: '完整度', value: `${completeness.value}%` },
  { label: '时间可信度', value: timeConfidence.value.label },
  { label: '关注', value: profile.focusTopic || '未填写' },
])

function goProfile() {
  router.push('/profile')
}

watch(
  () => [isArchiveComplete.value, profile.birthDt] as const,
  ([ready, birthDt]) => {
    if (!ready || !birthDt) return
    void loadReadingGuide(profile.asProfileData())
  },
  { immediate: true },
)
</script>

<template>
  <main class="fs-page home-page" aria-label="首页">

    <section class="hero-card fs-card fs-card--seal">
      <div class="hero-copy">
        <p class="hero-copy__eyebrow">浮生 · 人生六卷</p>
        <h1 class="hero-copy__title">{{ profileLabel }}</h1>
        <p class="hero-copy__desc">{{ birthText }}</p>
        <dl class="hero-copy__kpi" aria-label="档案摘要">
          <div v-for="item in previewItems" :key="item.label">
            <dt>{{ item.label }}</dt>
            <dd>{{ item.value }}</dd>
          </div>
        </dl>
      </div>

      <div class="hero-actions" aria-label="主要操作">
        <button class="fs-btn fs-btn--ghost" @click="goProfile">补全档案</button>
        <button
          class="fs-btn fs-btn--primary"
          :disabled="!isArchiveComplete"
          @click="navigateToStep('/report', true)"
        >
          生成报告
        </button>
      </div>
    </section>

    <ReadingGuide
      :disclaimer="disclaimer"
      :resume-volume-id="lastVolumeId"
      :resume-label="resumeVolumeLabel"
      :reading-paragraphs="readingParagraphs"
      :reading-loading="loadingReading"
      :reading-failed="readingFailed"
      :using-dynamic-reading="usingDynamicReading"
      @resume="resumeReport"
    />

    <VolumeTocGrid :can-open-report="isArchiveComplete" />

    <hr class="fs-codex-divider" aria-hidden="true" />

    <ProfileReadinessCard
      :completeness="completeness"
      :blockers="archiveBlockers"
      :enhancers="archiveEnhancers"
      :time-label="timeConfidence.label"
      :time-hint="timeConfidence.hint"
      :get-blocker-label="getArchiveBlockerLabel"
      :get-enhancer-label="getArchiveEnhancerLabel"
      @action="goProfile"
    />

    <section class="flow-card fs-card">
      <h2>路径与扩展</h2>
      <p class="flow-card__desc">主路径：录入 → 排盘验证 → 正式报告。每步遵循「先摘要、再结构、后解释」。</p>
      <p class="flow-card__tip">使用顶部或底部导航切换步骤；必填项未齐时，八字/紫微/报告会自动引导至档案页。</p>
      <p class="flow-card__desc flow-card__desc--secondary">合婚、相似盘与择日为独立模块，不影响主路径报告。</p>
      <button class="fs-btn fs-btn--ghost" data-testid="home-extensions" @click="router.push('/extensions')">
        打开工具箱
      </button>
    </section>
  </main>
</template>

<style scoped>
.home-page {
  gap: 14px;
}

.hero-card {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
  padding: 24px 22px;
}

.hero-copy {
  display: grid;
  gap: 14px;
}

.hero-copy__eyebrow {
  margin: 0;
  font-size: 12px;
  letter-spacing: 0.12em;
  color: var(--brand-gold-dark);
  font-family: var(--font-display);
  padding-left: 10px;
  border-left: 3px solid var(--brand-gold);
}

.hero-copy__tagline {
  margin: 6px 0 0;
  font-size: 13px;
  color: var(--brand-mist);
  font-family: var(--font-ui);
  line-height: 1.6;
}

.hero-copy__title {
  margin: 0;
  font-size: clamp(26px, 4vw, 38px);
  line-height: 1.15;
  color: var(--brand-ink);
  font-family: var(--font-display);
  font-weight: 600;
  text-wrap: balance;
}

.hero-copy__desc {
  margin: 0;
  color: var(--brand-mist);
  line-height: 1.75;
  font-size: var(--fs-sm);
}

.hero-copy__kpi {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px 16px;
  margin: 0;
  font-size: 12px;
}

.hero-copy__kpi dt {
  margin: 0;
  font-weight: 500;
  color: var(--brand-gold-dark);
}

.hero-copy__kpi dd {
  margin: 0;
  color: var(--brand-ink);
}

.hero-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.preview-card h2 {
  margin: 0 0 12px;
}

.flow-card h2 {
  margin: 0 0 8px;
}

.flow-card__desc,
.flow-card__tip {
  margin: 8px 0 0;
  color: var(--text-2);
  line-height: 1.7;
  font-size: 14px;
}

.flow-card__tip {
  font-size: 13px;
  color: var(--text-3);
}

.flow-card__desc--secondary {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed var(--border);
}

@media (max-width: 720px) {
  .hero-card {
    flex-direction: column;
    align-items: flex-start;
  }

  .hero-actions {
    width: 100%;
  }

  .hero-actions .fs-btn {
    flex: 1 1 0;
  }
}
</style>
