<script setup lang="ts">
import { useRouter } from 'vue-router'
import { BRAND_HOME_OPEN, BRAND_HOME_VOLUMES } from '@/constants/brandHome'

const props = defineProps<{
  canOpenReport?: boolean
}>()

const router = useRouter()

function openVolume(entry: (typeof BRAND_HOME_VOLUMES)[number]) {
  if (entry.requiresReport && !props.canOpenReport) {
    router.push({ path: '/profile', query: { reason: 'archive', redirect: entry.path } })
    return
  }
  router.push(entry.path)
}
</script>

<template>
  <section id="brand-codex" class="brand-codex" aria-label="六卷" data-testid="brand-codex">
    <div class="brand-codex__panel">
      <p class="brand-codex__k">{{ BRAND_HOME_OPEN.k }}</p>
      <p class="brand-codex__open">
        {{ BRAND_HOME_OPEN.lines[0] }}<br />
        {{ BRAND_HOME_OPEN.lines[1] }}
      </p>

      <ol id="brand-register" class="brand-register" aria-label="六卷卷目">
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
  </section>
</template>

<style scoped>
.brand-codex {
  padding: 0 var(--sp-8) 96px;
}

.brand-codex__panel {
  background: var(--surface);
  border: 1px solid var(--border);
  padding: 48px 56px 56px;
}

.brand-codex__k {
  margin: 0 0 24px;
  font-size: 12px;
  letter-spacing: 0.28em;
  color: var(--brand-gold);
  font-family: var(--font-display);
}

.brand-codex__open {
  margin: 0 0 48px;
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
  grid-template-columns: 56px 1fr minmax(120px, 34%);
  gap: 16px;
  align-items: baseline;
  width: 100%;
  padding: 18px 0;
  border: none;
  border-bottom: 1px solid var(--border);
  background: transparent;
  text-align: left;
  cursor: pointer;
  font-family: var(--font-display);
  color: var(--brand-ink);
  transition: color var(--dur-fast);
}

.brand-register__row:hover {
  color: var(--brand-gold-dark);
}

.brand-register__row:hover .brand-register__title {
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

@media (max-width: 720px) {
  .brand-codex {
    padding-left: 20px;
    padding-right: 20px;
  }

  .brand-codex__panel {
    padding: 32px 24px;
  }

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
