<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Colophon } from '@/types/life-volume'
import { formatMissingFieldLine } from '@/utils/buildEngineTrustDisplay'

const props = defineProps<{
  colophon: Colophon
}>()

const expanded = ref(false)

const missingLines = computed(() =>
  (props.colophon.missing_fields ?? []).map((field) => ({
    field,
    ...formatMissingFieldLine(field),
  })),
)
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
        <strong>对照轨：</strong>{{ colophon.iztro_advisory }}
      </p>
      <p v-if="colophon.dual_track_note">{{ colophon.dual_track_note }}</p>
      <ul v-if="missingLines.length" class="colophon-footnote__missing">
        <li v-for="line in missingLines" :key="line.field">
          <span>{{ line.main }}</span>
          <small v-if="line.note">{{ line.note }}</small>
        </li>
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

.colophon-footnote__missing {
  margin: 0;
  padding-left: 1.1em;
  display: grid;
  gap: 6px;
}

.colophon-footnote__missing li {
  display: grid;
  gap: 2px;
}

.colophon-footnote__missing small {
  color: var(--text-3, #8a8580);
  font-size: 12px;
}
</style>
