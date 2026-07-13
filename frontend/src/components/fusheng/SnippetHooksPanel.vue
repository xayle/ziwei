<script setup lang="ts">
import { computed, ref } from 'vue'
import type { LifeSnippetHookModel } from '@/api/openapiTypes'
import { copyTextToClipboard } from '@/utils/copyText'
import { track } from '@/utils/analytics'

export type SnippetHookItem = Pick<LifeSnippetHookModel, 'tag' | 'text' | 'layer'>

const props = withDefaults(
  defineProps<{
    hooks: SnippetHookItem[]
    caseId?: string | null
    verticalTitle?: string | null
    disclaimer?: string | null
    /** 埋点来源：report | landing */
    source?: string
  }>(),
  {
    caseId: null,
    verticalTitle: null,
    disclaimer: null,
    source: 'report',
  },
)

const copiedKey = ref<string | null>(null)
let copiedTimer: ReturnType<typeof setTimeout> | null = null

const hasHooks = computed(() => props.hooks.length > 0)

function flashCopied(key: string) {
  copiedKey.value = key
  if (copiedTimer) clearTimeout(copiedTimer)
  copiedTimer = setTimeout(() => {
    copiedKey.value = null
    copiedTimer = null
  }, 1600)
}

function trackCopy(action: string, hook?: SnippetHookItem, index?: number) {
  track({
    event_type: 'funnel_step',
    case_id: props.caseId,
    properties: {
      step: 'snippet_copy',
      action,
      source: props.source,
      tag: hook?.tag ?? null,
      layer: hook?.layer ?? null,
      index: index ?? null,
    },
  })
}

async function copyOne(hook: SnippetHookItem, index: number) {
  const ok = await copyTextToClipboard(hook.text)
  if (!ok) return
  flashCopied(`i-${index}`)
  trackCopy('one', hook, index)
}

async function copyAll() {
  const blob = props.hooks.map((h) => h.text).filter(Boolean).join('\n')
  const ok = await copyTextToClipboard(blob)
  if (!ok) return
  flashCopied('all')
  trackCopy('all')
}
</script>

<template>
  <section
    v-if="hasHooks"
    class="snippet-hooks"
    data-testid="snippet-hooks"
    aria-label="抖音钩子句"
  >
    <header class="snippet-hooks__head">
      <div class="snippet-hooks__titles">
        <p class="snippet-hooks__kicker">拍视频 · 钩子句</p>
        <p v-if="verticalTitle" class="snippet-hooks__volume">{{ verticalTitle }}</p>
      </div>
      <button
        type="button"
        class="snippet-hooks__copy-all"
        data-testid="snippet-copy-all"
        @click="copyAll"
      >
        {{ copiedKey === 'all' ? '已复制全部' : '复制全部' }}
      </button>
    </header>

    <ul class="snippet-hooks__list">
      <li
        v-for="(hook, index) in hooks"
        :key="`${hook.tag}-${index}`"
        class="snippet-hooks__item"
        :data-layer="hook.layer"
      >
        <span class="snippet-hooks__tag">{{ hook.tag }}</span>
        <p class="snippet-hooks__text">{{ hook.text }}</p>
        <button
          type="button"
          class="snippet-hooks__copy"
          :data-testid="`snippet-copy-${index}`"
          @click="copyOne(hook, index)"
        >
          {{ copiedKey === `i-${index}` ? '已复制' : '复制' }}
        </button>
      </li>
    </ul>

    <p v-if="disclaimer" class="snippet-hooks__disclaimer">{{ disclaimer }}</p>
  </section>
</template>

<style scoped>
.snippet-hooks {
  margin: 1.25rem 0 1.5rem;
  padding: 1rem 0.9rem 0.85rem;
  border-top: 1px solid var(--border-md, #d4c4a8);
  border-bottom: 1px solid var(--border-md, #d4c4a8);
  max-width: 100%;
  box-sizing: border-box;
}

.snippet-hooks__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.snippet-hooks__kicker {
  margin: 0;
  font-size: 0.72rem;
  letter-spacing: 0.14em;
  color: var(--brand-mist, #6b5d4f);
  text-transform: none;
}

.snippet-hooks__volume {
  margin: 0.2rem 0 0;
  font-family: var(--font-display, "LXGW Neo ZhiSong", serif);
  font-size: 1rem;
  letter-spacing: 0.06em;
  color: var(--brand-ink, #1a1410);
}

.snippet-hooks__copy-all,
.snippet-hooks__copy {
  flex-shrink: 0;
  padding: 0.35rem 0.65rem;
  border: 1px solid var(--brand-gold-dark, #8b5e34);
  background: transparent;
  color: var(--brand-gold-dark, #8b5e34);
  font: inherit;
  font-size: 0.78rem;
  letter-spacing: 0.06em;
  cursor: pointer;
}

.snippet-hooks__copy-all:focus-visible,
.snippet-hooks__copy:focus-visible {
  outline: 2px solid var(--brand-gold, #b8894d);
  outline-offset: 2px;
}

.snippet-hooks__list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}

.snippet-hooks__item {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 0.55rem 0.65rem;
  align-items: start;
}

.snippet-hooks__tag {
  margin-top: 0.15rem;
  font-size: 0.7rem;
  letter-spacing: 0.1em;
  color: var(--brand-cinnabar, #8b3a2a);
  border: 1px solid color-mix(in srgb, var(--brand-cinnabar, #8b3a2a) 35%, transparent);
  padding: 0.12rem 0.35rem;
  line-height: 1.2;
}

.snippet-hooks__text {
  margin: 0;
  font-size: 0.92rem;
  line-height: 1.65;
  color: var(--brand-ink, #1a1410);
  word-break: break-word;
}

.snippet-hooks__disclaimer {
  margin: 0.75rem 0 0;
  font-size: 0.72rem;
  line-height: 1.5;
  color: var(--text-3, #9a8b7a);
}

@media (max-width: 420px) {
  .snippet-hooks__item {
    grid-template-columns: auto 1fr;
  }

  .snippet-hooks__copy {
    grid-column: 1 / -1;
    justify-self: start;
  }
}
</style>
