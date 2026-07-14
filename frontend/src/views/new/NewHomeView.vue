<script setup lang="ts">
import { useRouter } from 'vue-router'
import {
  BRAND_HOME_LAYERS,
  BRAND_HOME_OPEN,
  BRAND_HOME_POEM,
  BRAND_HOME_VOLUMES,
  BRAND_HOME_WATERMARK,
} from '@/constants/brandHome'
import { useFushengFlow } from '@/composables/useFushengFlow'
import songMarginalCorner from '@/assets/brand/song-marginal-corner.svg'
import '@/assets/fusheng-page.css'

const router = useRouter()
const { isArchiveComplete } = useFushengFlow()

function goProfile() {
  router.push('/profile')
}

function openVolume(entry: (typeof BRAND_HOME_VOLUMES)[number]) {
  if (entry.requiresReport && !isArchiveComplete.value) {
    router.push({ path: '/profile', query: { reason: 'archive', redirect: entry.path } })
    return
  }
  router.push(entry.path)
}
</script>

<template>
  <div class="brand-home" aria-label="品牌首页">
    <span class="brand-home__scene" aria-hidden="true">案</span>

    <section class="brand-spread" aria-label="浮生 · 人生六卷">
      <figure class="brand-spread__marginal" aria-hidden="true">
        <img :src="songMarginalCorner" alt="" width="320" height="240" decoding="async" />
      </figure>

      <div class="brand-spread__frame">
        <span class="brand-spread__glyph brand-spread__glyph--right" aria-hidden="true">
          {{ BRAND_HOME_WATERMARK.right }}
        </span>

        <div class="brand-spread__left">
          <span class="brand-spread__glyph brand-spread__glyph--left" aria-hidden="true">
            {{ BRAND_HOME_WATERMARK.left }}
          </span>
          <div class="brand-island">
            <div class="brand-island__mast">
              <blockquote class="brand-island__poem" aria-label="录辰">
                <p
                  v-for="(line, index) in BRAND_HOME_POEM"
                  :key="index"
                  class="brand-island__poem-line"
                >
                  {{ line }}
                </p>
              </blockquote>

              <div class="brand-island__body">
                <div class="brand-island__head">
                  <h1 class="brand-island__word hero-copy__title">浮生</h1>
                  <p class="brand-island__tag">浮生若梦</p>
                  <p class="brand-island__series">人生六卷辑录</p>
                </div>
                <button type="button" class="brand-island__profile" @click="goProfile">
                  录入生辰
                </button>
              </div>
            </div>
          </div>
        </div>

        <div id="brand-codex" class="brand-spread__right" aria-label="六卷卷目" data-testid="brand-codex">
          <p class="brand-spread__k">{{ BRAND_HOME_OPEN.k }}</p>
          <p class="brand-spread__open">
            {{ BRAND_HOME_OPEN.lines[0] }}<br />
            {{ BRAND_HOME_OPEN.lines[1] }}
          </p>
          <p class="brand-spread__lane-note" data-testid="brand-lane-note">
            排盘台 · 成书分流：点卷进入对应工作台或报告成书。
          </p>
          <ol id="brand-register" class="brand-register" aria-label="六卷">
            <li v-for="entry in BRAND_HOME_VOLUMES" :key="entry.id">
              <button
                type="button"
                class="brand-register__row"
                :data-volume-id="entry.id"
                :data-lane="entry.lane || 'book'"
                @click="openVolume(entry)"
              >
                <span class="brand-register__n">{{ entry.num }}</span>
                <span class="brand-register__title">{{ entry.title }}</span>
                <span class="brand-register__pi">
                  <span class="brand-register__lane">{{ entry.lane === 'desk' ? '排盘台' : '成书' }}</span>
                  {{ entry.pi }}
                </span>
              </button>
            </li>
          </ol>
        </div>

        <div class="brand-spread__layers" aria-label="读法三层">
          <div v-for="layer in BRAND_HOME_LAYERS" :key="layer.label" class="brand-layer">
            <b>{{ layer.label }}</b>
            <p>{{ layer.text }}</p>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.brand-home {
  position: relative;
  max-width: min(1180px, 100%);
  margin: 0 auto;
  color: var(--brand-ink);
  isolation: isolate;
}

.brand-home__scene {
  position: absolute;
  left: 50%;
  top: clamp(280px, 42vh, 480px);
  transform: translate(-50%, -50%);
  font-family: var(--font-display);
  font-size: clamp(200px, 38vw, 420px);
  font-weight: 600;
  line-height: 1;
  letter-spacing: 0.08em;
  color: var(--brand-gold);
  opacity: 0.08;
  pointer-events: none;
  user-select: none;
  z-index: 0;
}

.brand-spread {
  position: relative;
  z-index: 1;
  padding: clamp(12px, 2vw, 24px) clamp(20px, 3vw, 32px) clamp(24px, 3vw, 40px);
}

.brand-spread__marginal {
  position: absolute;
  left: clamp(8px, 2vw, 24px);
  bottom: clamp(8px, 1.5vh, 20px);
  z-index: 0;
  margin: 0;
  width: clamp(140px, 19vw, 220px);
  pointer-events: none;
  user-select: none;
  opacity: 0.44;
  -webkit-mask-image: radial-gradient(ellipse 120% 90% at 30% 70%, #000 40%, transparent 78%);
  mask-image: radial-gradient(ellipse 120% 90% at 30% 70%, #000 40%, transparent 78%);
}

.brand-spread__marginal img {
  display: block;
  width: 100%;
  height: auto;
}

.brand-spread::before {
  content: '';
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  width: min(calc(100% - 4px), 1160px);
  height: calc(100% - 12px);
  pointer-events: none;
  z-index: 0;
  background: radial-gradient(
    ellipse 100% 86% at 50% 48%,
    rgba(255, 250, 245, 0.82),
    transparent 68%
  );
}

.brand-spread__frame {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: minmax(240px, 0.92fr) minmax(0, 1.18fr);
  grid-template-rows: 1fr auto;
  gap: clamp(24px, 4vw, 48px) clamp(24px, 4vw, 56px);
  min-height: auto;
  padding: clamp(32px, 5vw, 56px) clamp(28px, 4vw, 52px);
  background:
    radial-gradient(ellipse 80% 60% at 100% 100%, rgba(184, 137, 77, 0.09), transparent 55%),
    var(--surface);
  border: 1px solid var(--border-md);
  box-shadow:
    inset 0 0 0 1px var(--border),
    0 28px 64px rgba(26, 20, 16, 0.11),
    0 10px 24px rgba(184, 137, 77, 0.1);
}

.brand-spread__glyph {
  position: absolute;
  z-index: 0;
  line-height: 1;
  letter-spacing: 0.06em;
  font-family: var(--font-display);
  font-weight: 600;
  color: var(--brand-gold);
  pointer-events: none;
  user-select: none;
}

.brand-spread__glyph--left {
  left: clamp(0px, 6%, 28px);
  top: 46%;
  transform: translateY(-50%);
  font-size: clamp(120px, 19vw, 196px);
  opacity: 0.055;
}

.brand-spread__glyph--right {
  right: clamp(16px, 4vw, 36px);
  bottom: clamp(80px, 14vw, 128px);
  font-size: clamp(104px, 17vw, 172px);
  opacity: 0.065;
}

.brand-spread__left {
  position: relative;
  isolation: isolate;
  overflow: hidden;
  grid-column: 1;
  grid-row: 1;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-right: clamp(8px, 2vw, 16px);
}

.brand-spread__left::after {
  content: '';
  position: absolute;
  inset: 0;
  background:
    url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='4' height='5' viewBox='0 0 4 5'%3E%3Crect width='4' height='1' fill='rgba(184,137,77,0.022)'/%3E%3C/svg%3E"),
    radial-gradient(ellipse 85% 75% at 15% 50%, rgba(184, 137, 77, 0.09), transparent 68%);
  pointer-events: none;
}

.brand-island {
  position: relative;
  z-index: 1;
  width: min(100%, 380px);
}

.brand-island__mast {
  display: flex;
  align-items: stretch;
  gap: clamp(20px, 3.5vw, 32px);
}

.brand-island__poem {
  display: flex;
  flex-direction: row-reverse;
  justify-content: flex-start;
  gap: clamp(10px, 2vw, 16px);
  margin: 0;
  padding: 4px clamp(16px, 2.5vw, 22px) 4px 0;
  border: none;
  border-right: 1px solid var(--border-md);
  flex-shrink: 0;
}

.brand-island__poem-line {
  margin: 0;
  writing-mode: vertical-rl;
  text-orientation: mixed;
  font-size: 14px;
  font-weight: 500;
  letter-spacing: 0.12em;
  line-height: 1;
  color: var(--brand-mist);
  font-family: var(--font-display);
}

.brand-island__body {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  flex: 1;
  min-width: 0;
  padding: 2px 0;
}

.brand-island__word {
  margin: 0 0 14px;
  font-size: clamp(3.25rem, 8vw, 4.5rem);
  font-weight: 600;
  line-height: 1;
  letter-spacing: 0.18em;
  padding-left: 0.08em;
  font-family: var(--font-display);
  color: var(--brand-ink);
}

.brand-island__tag {
  margin: 0;
  font-size: 14px;
  letter-spacing: 0.3em;
  color: var(--brand-mist);
  font-family: var(--font-display);
}

.brand-island__series {
  margin: 6px 0 0;
  font-size: 12px;
  letter-spacing: 0.24em;
  color: var(--brand-gold-dark);
  font-family: var(--font-display);
}

.brand-island__profile {
  align-self: flex-start;
  margin-top: clamp(24px, 4vw, 40px);
  padding: 0 0 3px;
  border: none;
  border-bottom: 1px solid var(--brand-ink);
  background: transparent;
  font-family: var(--font-display);
  font-size: 13px;
  letter-spacing: 0.1em;
  color: var(--text-3);
  cursor: pointer;
}

.brand-island__profile:hover {
  color: var(--brand-mist);
  border-color: var(--brand-gold);
}

.brand-spread__right {
  position: relative;
  z-index: 1;
  grid-column: 2;
  grid-row: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding-left: clamp(16px, 3vw, 32px);
  border-left: 1px solid var(--border-md);
}

.brand-spread__k {
  margin: 0 0 16px;
  font-size: 12px;
  letter-spacing: 0.28em;
  color: var(--brand-gold);
  font-family: var(--font-display);
}

.brand-spread__open {
  margin: 0 0 16px;
  max-width: 28em;
  font-size: 16px;
  line-height: 2;
  letter-spacing: 0.06em;
  color: var(--brand-mist);
  font-family: var(--font-display);
}

.brand-spread__lane-note {
  margin: 0 0 24px;
  font-size: 12px;
  letter-spacing: 0.08em;
  color: var(--text-3);
  font-family: var(--font-display);
}

.brand-register__lane {
  display: inline-block;
  margin-right: 0.45em;
  font-size: 11px;
  letter-spacing: 0.1em;
  color: var(--brand-gold-dark);
}

.brand-register {
  list-style: none;
  margin: 0;
  padding: 0;
  border-top: 1px solid var(--border-md);
}

.brand-register__row {
  display: grid;
  grid-template-columns: 56px 1fr minmax(108px, 34%);
  gap: 16px;
  align-items: baseline;
  width: 100%;
  padding: 16px 0;
  border: none;
  border-bottom: 1px solid var(--border);
  background: transparent;
  text-align: left;
  cursor: pointer;
  font-family: var(--font-display);
  color: var(--brand-ink);
}

.brand-register__row:hover,
.brand-register__row:focus-visible {
  color: var(--brand-gold-dark);
  outline: none;
}

.brand-register__row:hover .brand-register__title,
.brand-register__row:focus-visible .brand-register__title {
  color: var(--brand-gold-dark);
}

.brand-register__n {
  font-size: 12px;
  letter-spacing: 0.08em;
  color: var(--text-3);
}

.brand-register__title {
  font-size: 17px;
  font-weight: 600;
  letter-spacing: 0.14em;
}

.brand-register__pi {
  font-size: 13px;
  line-height: 1.65;
  letter-spacing: 0.04em;
  color: var(--text-3);
  text-align: right;
}

.brand-spread__layers {
  grid-column: 1 / -1;
  grid-row: 2;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: clamp(20px, 4vw, 40px);
  padding-top: clamp(24px, 4vw, 36px);
  border-top: 1px solid var(--border-md);
}

.brand-layer b {
  display: block;
  margin-bottom: 8px;
  font-size: 13px;
  letter-spacing: 0.1em;
  color: var(--brand-gold);
  font-weight: 600;
  font-family: var(--font-display);
}

.brand-layer p {
  margin: 0;
  font-size: 14px;
  line-height: 1.85;
  color: var(--brand-mist);
  font-family: var(--font-display);
}

@media (max-width: 860px) {
  .brand-home__scene {
    font-size: clamp(160px, 50vw, 280px);
    opacity: 0.04;
  }

  .brand-spread__marginal {
    width: clamp(120px, 30vw, 180px);
    opacity: 0.36;
  }

  .brand-spread__frame {
    grid-template-columns: 1fr;
    grid-template-rows: auto auto auto;
    min-height: auto;
  }

  .brand-spread__left {
    grid-column: 1;
    grid-row: 1;
    justify-content: center;
    padding-right: 0;
  }

  .brand-spread__right {
    grid-column: 1;
    grid-row: 2;
    padding-left: 0;
    border-left: none;
    padding-top: 24px;
    border-top: 1px solid var(--border-md);
  }

  .brand-spread__layers {
    grid-column: 1;
    grid-row: 3;
    grid-template-columns: 1fr;
  }

  .brand-island__mast {
    flex-direction: column;
    align-items: stretch;
  }

  .brand-island__poem {
    justify-content: center;
    padding: 20px 0 0;
    border-right: none;
    border-top: 1px solid var(--border-md);
  }
}

@media (max-width: 720px) {
  .brand-register__row {
    grid-template-columns: 48px 1fr;
  }

  .brand-register__pi {
    grid-column: 2;
    text-align: left;
    margin-top: 4px;
  }
}
</style>
