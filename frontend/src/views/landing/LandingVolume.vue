<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  LANDING_BRAND,
  LANDING_CTA,
  LANDING_DISCLAIMER,
  LANDING_HEADLINE,
  LANDING_LEAD,
  LANDING_PREFACE_PARAS,
  LANDING_TAGLINE,
  LANDING_VOL_TEASERS,
} from '@/constants/landingVolume'
import { captureUtmFromQuery, utmAsQuery } from '@/utils/utmCapture'
import { flushAnalytics, track, trackLandingCta, trackVolumeView } from '@/utils/analytics'
import '@/assets/variables.css'

const route = useRoute()
const router = useRouter()

onMounted(() => {
  captureUtmFromQuery(route.query as Record<string, unknown>)
  trackVolumeView('preface')
  track({
    event_type: 'funnel_step',
    properties: { step: 'landing_view', path: 'landing' },
  })
})

onUnmounted(() => {
  void flushAnalytics()
})

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
  background:
    radial-gradient(ellipse 120% 80% at 50% -10%, rgba(184, 137, 77, 0.12), transparent 55%),
    linear-gradient(180deg, #f7f1e8 0%, var(--brand-paper, #f5f0e6) 42%, #efe6d6 100%);
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

.landing-volume__headline {
  margin: 0;
  font-size: 1.35rem;
  font-weight: 600;
  line-height: 1.45;
  letter-spacing: 0.04em;
}

.landing-volume__lead {
  margin: 0.75rem 0 0;
  font-size: 0.95rem;
  line-height: 1.65;
  color: var(--brand-mist, #6b5d4f);
}

.landing-volume__preface {
  margin-top: 1.5rem;
  padding: 1rem 0 0.25rem;
  border-top: 1px solid var(--border-md, #d4c4a8);
}

.landing-volume__kicker {
  margin: 0 0 0.75rem;
  font-size: 0.78rem;
  letter-spacing: 0.18em;
  color: var(--brand-gold-dark, #8b5e34);
  text-transform: none;
}

.landing-volume__para {
  margin: 0 0 0.85rem;
  font-size: 0.98rem;
  line-height: 1.75;
}

.landing-volume__teasers {
  list-style: none;
  margin: 1.25rem 0 0;
  padding: 0;
  border-top: 1px solid var(--border, #e5dcc8);
}

.landing-volume__teaser {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.7rem 0;
  border-bottom: 1px solid var(--border, #e5dcc8);
  font-size: 0.9rem;
}

.landing-volume__teaser-label {
  min-width: 0;
}

.landing-volume__teaser-note {
  flex-shrink: 0;
  color: var(--brand-gold-dark, #8b5e34);
  letter-spacing: 0.06em;
}

.landing-volume__cta-row {
  margin-top: 1.75rem;
}

.landing-volume__cta {
  display: block;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  padding: 0.95rem 1rem;
  border: 1px solid var(--brand-gold-dark, #8b5e34);
  border-radius: 2px;
  background: var(--brand-ink, #1a1410);
  color: var(--brand-paper, #f5f0e6);
  font: inherit;
  font-size: 1.05rem;
  letter-spacing: 0.14em;
  cursor: pointer;
}

.landing-volume__cta:focus-visible {
  outline: 2px solid var(--brand-gold, #b8894d);
  outline-offset: 3px;
}

.landing-volume__foot {
  max-width: 26rem;
  margin: 2rem auto 0;
}

.landing-volume__disclaimer {
  margin: 0;
  font-size: 0.72rem;
  line-height: 1.6;
  color: var(--text-3, #9a8b7a);
}
</style>
