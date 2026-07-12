<script setup lang="ts">
import { ref } from 'vue'
import type { Colophon } from '@/types/life-volume'

defineProps<{
  colophon: Colophon
}>()

const expanded = ref(false)
</script>

<template>
  <footer class="colophon-footnote fs-card">
    <div class="colophon-footnote__summary">
      <p v-for="(line, idx) in colophon.summary_lines" :key="idx">{{ line }}</p>
    </div>
    <button
      v-if="colophon.expandable"
      type="button"
      class="fs-btn fs-btn--ghost colophon-footnote__toggle"
      :aria-expanded="expanded"
      @click="expanded = !expanded"
    >
      {{ expanded ? '收起校勘' : '展开校勘' }}
    </button>
    <div v-show="expanded" class="colophon-footnote__detail">
      <p v-if="colophon.wenmo_advisory" class="colophon-footnote__wenmo">
        <strong>文墨对照：</strong>{{ colophon.wenmo_advisory }}
      </p>
      <p v-if="colophon.iztro_advisory" class="colophon-footnote__iztro">
        <strong>iztro 对照：</strong>{{ colophon.iztro_advisory }}
      </p>
      <p v-if="colophon.dual_track_note">{{ colophon.dual_track_note }}</p>
      <ul v-if="colophon.missing_fields?.length">
        <li v-for="field in colophon.missing_fields" :key="field">缺失：{{ field }}</li>
      </ul>
    </div>
  </footer>
</template>

<style scoped>
.colophon-footnote {
  display: grid;
  gap: 10px;
  font-size: 13px;
  color: var(--text-2);
  line-height: 1.65;
}

.colophon-footnote__summary p {
  margin: 0;
}

.colophon-footnote__wenmo,
.colophon-footnote__iztro {
  color: var(--brand-cinnabar);
}
</style>
