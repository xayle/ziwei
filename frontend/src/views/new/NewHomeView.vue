<script setup lang="ts">
import { useRouter } from 'vue-router'
import { BRAND_HOME_LAYERS, BRAND_HOME_OPEN, BRAND_HOME_VOLUMES } from '@/constants/brandHome'
import { useFushengFlow } from '@/composables/useFushengFlow'
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
    <section class="brand-spread" aria-label="浮生 · 人生六卷">
      <div class="brand-spread__frame">
        <div class="brand-spread__watermark" aria-hidden="true">卷</div>

        <div class="brand-spread__left">
          <div class="brand-island">
            <h1 class="brand-island__word">浮生</h1>
            <p class="brand-island__tag">浮生若梦</p>
            <p class="brand-island__series">人生六卷辑录</p>
            <p class="brand-island__verse">读人生如戏，展卷而后，方入其事。</p>
            <button type="button" class="brand-island__profile" @click="goProfile">录入生辰</button>
          </div>
        </div>

        <div id="brand-codex" class="brand-spread__right" aria-label="六卷卷目" data-testid="brand-codex">
          <p class="brand-spread__k">{{ BRAND_HOME_OPEN.k }}</p>
          <p class="brand-spread__open">
            {{ BRAND_HOME_OPEN.lines[0] }}<br />
            {{ BRAND_HOME_OPEN.lines[1] }}
          </p>
          <ol id="brand-register" class="brand-register" aria-label="六卷">
            <li v-for="entry in BRAND_HOME_VOLUMES" :key="entry.id">
              <button
                type="button"
                class="brand-register__row"
                :data-volume-id="entry.id"
                @click="openVolume(entry)"
              >
                <span class="brand-register__n">{{ entry.num }}</span>
                <span class="brand-register__title">{{ entry.title }}</span>
                <span class="brand-register__pi">{{ entry.pi }}</span>
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
  max-width: min(1180px, 100%);
  margin: 0 auto;
  color: var(--brand-ink);
}

.brand-spread {
  padding: 0 20px 64px;
}

.brand-spread__frame {
  position: relative;
  display: grid;
  grid-template-columns: minmax(240px, 0.92fr) minmax(0, 1.18fr);
  grid-template-rows: 1fr auto;
  gap: clamp(24px, 4vw, 48px) clamp(24px, 4vw, 56px);
  min-height: calc(100dvh - 56px - 48px);
  padding: clamp(32px, 5vw, 56px) clamp(28px, 4vw, 52px);
  background:
    radial-gradient(ellipse 80% 60% at 100% 100%, rgba(184, 137, 77, 0.06), transparent 55%),
    var(--surface);
  border: 1px solid var(--border-md);
  box-shadow:
    inset 0 0 0 1px var(--border),
    0 18px 48px rgba(26, 20, 16, 0.06);
}

.brand-spread__watermark {
  position: absolute;
  right: clamp(12px, 3vw, 28px);
  bottom: clamp(72px, 12vw, 120px);
  font-size: clamp(96px, 16vw, 168px);
  line-height: 1;
  letter-spacing: 0.08em;
  color: var(--brand-gold);
  opacity: 0.06;
  pointer-events: none;
  font-family: var(--font-display);
  user-select: none;
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

.brand-spread__left::before {
  content: '若';
  position: absolute;
  left: -6%;
  top: 50%;
  transform: translateY(-52%);
  font-size: clamp(160px, 26vw, 260px);
  line-height: 1;
  letter-spacing: 0.06em;
  font-family: var(--font-display);
  color: var(--brand-gold);
  opacity: 0.04;
  pointer-events: none;
  user-select: none;
}

.brand-spread__left::after {
  content: '';
  position: absolute;
  inset: 0;
  background:
    repeating-linear-gradient(
      0deg,
      transparent,
      transparent 3px,
      rgba(184, 137, 77, 0.018) 3px,
      rgba(184, 137, 77, 0.018) 4px
    ),
    radial-gradient(ellipse 85% 75% at 15% 50%, rgba(184, 137, 77, 0.07), transparent 68%);
  pointer-events: none;
}

.brand-island {
  position: relative;
  z-index: 1;
  width: min(100%, 300px);
}

.brand-island__word {
  margin: 0 0 16px;
  font-size: clamp(3.75rem, 9.5vw, 5.25rem);
  font-weight: 600;
  line-height: 1;
  letter-spacing: 0.2em;
  padding-left: 0.1em;
  font-family: var(--font-display);
  color: var(--brand-ink);
}

.brand-island__tag {
  margin: 0;
  font-size: 15px;
  letter-spacing: 0.34em;
  color: var(--brand-mist);
  font-family: var(--font-display);
}

.brand-island__series {
  margin: 8px 0 0;
  font-size: 12px;
  letter-spacing: 0.26em;
  color: var(--brand-gold-dark);
  font-family: var(--font-display);
}

.brand-island__verse {
  margin: 28px 0 0;
  max-width: 16em;
  font-size: 14px;
  line-height: 1.85;
  letter-spacing: 0.06em;
  color: var(--text-3);
  font-family: var(--font-display);
}

.brand-island__profile {
  margin-top: 24px;
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
  margin: 0 0 32px;
  max-width: 28em;
  font-size: 16px;
  line-height: 2;
  letter-spacing: 0.06em;
  color: var(--brand-mist);
  font-family: var(--font-display);
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

  .brand-island__verse {
    max-width: none;
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
