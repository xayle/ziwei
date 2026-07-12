<script setup lang="ts">
import { useRouter } from 'vue-router'
import { LIFE_VOLUME_LABELS, type LifeVolumeId } from '@/types/life-volume'
import { reportVolumeHref } from '@/composables/useVolumeRouteMeta'

const props = defineProps<{
  canOpenReport?: boolean
}>()

const router = useRouter()

const entries: Array<{
  id: LifeVolumeId
  hint: string
  path: string
  requiresReport?: boolean
}> = [
  { id: 'preface', hint: '读法与免责', path: reportVolumeHref('preface'), requiresReport: true },
  { id: 'vol1', hint: '四柱 · 格局', path: '/new/bazi' },
  { id: 'vol2', hint: '关系 · 神煞', path: reportVolumeHref('vol2'), requiresReport: true },
  { id: 'vol3', hint: '大运 · 运限', path: '/new/ziwei/timeline' },
  { id: 'vol4', hint: '紫微方盘', path: '/new/ziwei' },
  { id: 'vol5', hint: '域分析 · 默认折叠', path: reportVolumeHref('vol5'), requiresReport: true },
  { id: 'vol6', hint: '问书 · 主动展开', path: reportVolumeHref('vol6'), requiresReport: true },
  { id: 'colophon', hint: '校勘 · 跋', path: reportVolumeHref('colophon'), requiresReport: true },
]

function navigate(entry: (typeof entries)[number]) {
  if (entry.requiresReport && !props.canOpenReport) {
    router.push('/profile')
    return
  }
  if (entry.path.startsWith('/report')) {
    router.push(entry.path)
    return
  }
  router.push(entry.path)
}
</script>

<template>
  <section class="fs-card fs-card--register volume-toc-grid" aria-label="六卷卷目">
    <div class="volume-toc-grid__head">
      <h2 class="volume-toc-grid__title">人生六卷</h2>
      <p class="volume-toc-grid__lead">卷一 / 卷三 / 卷四为工作台；其余卷在报告中连续阅读。</p>
    </div>
    <ul class="volume-toc-grid__list">
      <li v-for="entry in entries" :key="entry.id">
        <button
          type="button"
          class="fs-register-row"
          :data-volume-id="entry.id"
          :disabled="entry.requiresReport && !canOpenReport"
          @click="navigate(entry)"
        >
          <span class="fs-register-row__label">{{ LIFE_VOLUME_LABELS[entry.id] }}</span>
          <span class="fs-register-row__hint">{{ entry.hint }}</span>
        </button>
      </li>
    </ul>
  </section>
</template>

<style scoped>
.volume-toc-grid__head {
  display: grid;
  gap: 6px;
}

.volume-toc-grid__title {
  margin: 0;
  font-family: var(--font-display);
  font-size: 17px;
  font-weight: 600;
  color: var(--brand-ink);
}

.volume-toc-grid__lead {
  margin: 0;
  font-size: 13px;
  line-height: 1.65;
  color: var(--brand-mist);
}

.volume-toc-grid__list {
  margin: 0;
  padding: 0;
  list-style: none;
}
</style>
