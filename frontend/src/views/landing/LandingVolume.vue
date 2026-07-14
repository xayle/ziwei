<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  LANDING_BRAND,
  LANDING_CTA,
  LANDING_DISCLAIMER,
  LANDING_HEADLINE,
  LANDING_HOOK_SNIPPETS,
  LANDING_HOOKS_DISCLAIMER,
  LANDING_HOOKS_TITLE,
  LANDING_LEAD,
  LANDING_PREFACE_PARAS,
  LANDING_TAGLINE,
  LANDING_VOL_TEASERS,
} from '@/constants/landingVolume'
import { captureUtmFromQuery, utmAsQuery } from '@/utils/utmCapture'
import { flushAnalytics, track, trackLandingCta, trackVolumeView } from '@/utils/analytics'
import { fetchLifeVol1Preview } from '@/api/life'
import type { LifeVolumeResponse } from '@/types/life-volume'
import SnippetHooksPanel from '@/components/fusheng/SnippetHooksPanel.vue'
import DouyinShareCard from '@/components/fusheng/DouyinShareCard.vue'
import '@/assets/variables.css'

const route = useRoute()
const router = useRouter()

const previewLoading = ref(false)
const previewError = ref('')
const previewDoc = ref<LifeVolumeResponse | null>(null)

const previewCaseId = computed(() => {
  const raw = route.query.case_id
  return typeof raw === 'string' ? raw.trim() : ''
})
const previewToken = computed(() => {
  const raw = route.query.token
  return typeof raw === 'string' ? raw.trim() : ''
})
const hasPreviewQuery = computed(() => Boolean(previewCaseId.value && previewToken.value))

const previewParagraphs = computed(() => {
  const doc = previewDoc.value
  if (!doc) return [] as string[]
  const lines: string[] = []
  for (const vol of doc.volumes ?? []) {
    if (vol.id !== 'preface' && vol.id !== 'vol1') continue
    for (const section of vol.sections ?? []) {
      for (const block of section.blocks ?? []) {
        const text = block.text?.trim()
        if (text) lines.push(text)
      }
    }
  }
  return lines.slice(0, 8)
})

onMounted(() => {
  captureUtmFromQuery(route.query as Record<string, unknown>)
  trackVolumeView('preface')
  track({
    event_type: 'funnel_step',
    properties: { step: 'landing_view', path: 'landing' },
  })
  if (hasPreviewQuery.value) {
    void loadPreview()
  }
})

onUnmounted(() => {
  void flushAnalytics()
})

async function loadPreview() {
  previewLoading.value = true
  previewError.value = ''
  previewDoc.value = null
  const doc = await fetchLifeVol1Preview(previewCaseId.value, previewToken.value)
  previewLoading.value = false
  if (!doc) {
    previewError.value = '试读链接无效或已过期，请重新向分享者索取。'
    track({
      event_type: 'funnel_step',
      case_id: previewCaseId.value,
      properties: { step: 'landing_preview_fail' },
    })
    return
  }
  previewDoc.value = doc
  track({
    event_type: 'funnel_step',
    case_id: previewCaseId.value,
    properties: { step: 'landing_preview_ok' },
  })
}

function goArchive() {
  trackLandingCta('register_profile')
  const utm = captureUtmFromQuery(route.query as Record<string, unknown>)
  void flushAnalytics()
  router.push({ path: '/profile', query: { ...utmAsQuery(utm), from: 'landing' } })
}
</script>

<template>
  <div class="landing-volume" data-testid="landing-volume" aria-label="浮生抖音落地页">
    <header class="landing-volume__mast">
      <p class="landing-volume__brand hero-copy__title">{{ LANDING_BRAND }}</p>
      <p class="landing-volume__tag">{{ LANDING_TAGLINE }}</p>
    </header>

    <main class="landing-volume__main">
      <h1 class="landing-volume__headline">{{ LANDING_HEADLINE }}</h1>
      <p class="landing-volume__lead">{{ LANDING_LEAD }}</p>

      <section
        v-if="hasPreviewQuery"
        class="landing-volume__preview"
        aria-label="卷一试读"
        data-testid="landing-h5-preview"
      >
        <p class="landing-volume__kicker">试读 · 卷首与卷一摘要</p>
        <p v-if="previewLoading" class="landing-volume__para">正在载入试读…</p>
        <p v-else-if="previewError" class="landing-volume__preview-error" data-testid="landing-h5-preview-error">
          {{ previewError }}
        </p>
        <template v-else-if="previewParagraphs.length">
          <p
            v-for="(para, index) in previewParagraphs"
            :key="index"
            class="landing-volume__para"
            data-testid="landing-h5-preview-line"
          >
            {{ para }}
          </p>
          <p v-if="previewDoc?.disclaimer_block?.text" class="landing-volume__disclaimer">
            {{ previewDoc.disclaimer_block.text }}
          </p>
        </template>
      </section>

      <section class="landing-volume__preface" aria-label="卷首摘要">
        <p class="landing-volume__kicker">卷首 · 读法</p>
        <p
          v-for="(para, index) in LANDING_PREFACE_PARAS"
          :key="index"
          class="landing-volume__para"
        >
          {{ para }}
        </p>
      </section>

      <ul class="landing-volume__teasers" aria-label="卷目预告">
        <li v-for="item in LANDING_VOL_TEASERS" :key="item.id" class="landing-volume__teaser">
          <span class="landing-volume__teaser-label">{{ item.label }}</span>
          <span class="landing-volume__teaser-note">{{ item.note }}</span>
        </li>
      </ul>

      <SnippetHooksPanel
        :hooks="LANDING_HOOK_SNIPPETS"
        :vertical-title="LANDING_HOOKS_TITLE"
        :disclaimer="LANDING_HOOKS_DISCLAIMER"
        source="landing"
      />

      <DouyinShareCard
        :volume-title="LANDING_HOOKS_TITLE"
        :fact-lines="LANDING_HOOK_SNIPPETS.map((h) => h.text)"
        :disclaimer="LANDING_HOOKS_DISCLAIMER"
        source="landing"
      />

      <div class="landing-volume__cta-row">
        <button
          type="button"
          class="landing-volume__cta"
          data-testid="landing-cta"
          @click="goArchive"
        >
          {{ LANDING_CTA }}
        </button>
      </div>
    </main>

    <footer class="landing-volume__foot">
      <p class="landing-volume__disclaimer" data-testid="landing-disclaimer">
        {{ LANDING_DISCLAIMER }}
      </p>
    </footer>
  </div>
</template>

<style scoped>
.landing-volume {
  min-height: 100dvh;
  max-width: 100%;
  overflow-x: hidden;
  box-sizing: border-box;
  padding: 1.75rem 1.25rem 2.5rem;
  color: var(--brand-ink, #1a1410);
  background-color: var(--brand-paper, #f5f0e6);
  background-image: radial-gradient(
    ellipse 120% 80% at 50% -10%,
    rgba(184, 137, 77, 0.12),
    transparent 55%
  );
  font-family: "LXGW Neo ZhiSong", "Noto Serif SC", "Songti SC", serif;
}

.landing-volume__mast {
  text-align: center;
  margin-bottom: 1.75rem;
}

.landing-volume__brand {
  margin: 0;
  font-size: clamp(2.4rem, 12vw, 3rem);
  font-weight: 700;
  letter-spacing: 0.28em;
  line-height: 1.1;
}

.landing-volume__tag {
  margin: 0.55rem 0 0;
  font-size: 0.92rem;
  color: var(--brand-mist, #6b5d4f);
  letter-spacing: 0.12em;
}

.landing-volume__main {
  max-width: 26rem;
  margin: 0 auto;
}

.landing-volume__preview {
  margin: 0 0 1.5rem;
  padding: 1rem 0.85rem;
  border: 1px solid var(--border-md, #d4c4a8);
  background: rgba(255, 255, 255, 0.35);
}

.landing-volume__preview-error {
  margin: 0;
  font-size: 0.88rem;
  line-height: 1.6;
  color: var(--brand-cinnabar, #8b3a2a);
}

.landing-volume__headline {
  margin: 0 0 0.75rem;
  font-size: 1.35rem;
  letter-spacing: 0.08em;
  line-height: 1.45;
}

.landing-volume__lead {
  margin: 0 0 1.5rem;
  font-size: 0.95rem;
  line-height: 1.7;
  color: var(--brand-mist, #6b5d4f);
}

.landing-volume__kicker {
  margin: 0 0 0.65rem;
  font-size: 0.72rem;
  letter-spacing: 0.2em;
  color: var(--brand-gold-dark, #8b5e34);
}

.landing-volume__para {
  margin: 0 0 0.75rem;
  font-size: 0.9rem;
  line-height: 1.75;
}

.landing-volume__teasers {
  list-style: none;
  margin: 0 0 1.5rem;
  padding: 0;
}

.landing-volume__teaser {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.55rem 0;
  border-bottom: 1px solid var(--border, #e8dfd0);
  font-size: 0.85rem;
}

.landing-volume__teaser-note {
  color: var(--text-3, #9a8b7a);
}

.landing-volume__cta-row {
  margin: 1.5rem 0 1rem;
}

.landing-volume__cta {
  width: 100%;
  padding: 0.85rem 1rem;
  border: 1px solid var(--brand-ink, #1a1410);
  background: var(--brand-ink, #1a1410);
  color: var(--brand-paper, #f5f0e6);
  font: inherit;
  letter-spacing: 0.14em;
  cursor: pointer;
}

.landing-volume__foot {
  margin-top: 2rem;
  text-align: center;
}

.landing-volume__disclaimer {
  margin: 0.5rem 0 0;
  font-size: 0.72rem;
  line-height: 1.55;
  color: var(--text-3, #9a8b7a);
}
</style>
