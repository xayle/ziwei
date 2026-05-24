<script setup lang="ts">
import type { ZiweiChartHeaderBindings } from '@/composables/useZiweiChartHeaderBindings'
import type { ZiweiChartWorkspaceBindings } from '@/composables/useZiweiChartWorkspaceBindings'
import ZiweiChartHeader from './ZiweiChartHeader.vue'
import ZiweiChartWorkspace from './ZiweiChartWorkspace.vue'

const props = defineProps<{
  header: ZiweiChartHeaderBindings
  workspace: ZiweiChartWorkspaceBindings
}>()
</script>

<template>
  <div class="chart-section">
    <ZiweiChartHeader v-bind="props.header" />
    <ZiweiChartWorkspace v-bind="props.workspace" />
  </div>
</template>