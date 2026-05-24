import { computed } from 'vue'
import { useZiweiChartCanvasBindings } from '@/composables/useZiweiChartCanvasBindings'
import { useZiweiChartHeaderBindings } from '@/composables/useZiweiChartHeaderBindings'
import { useZiweiChartWorkspaceBindings } from '@/composables/useZiweiChartWorkspaceBindings'

type UseZiweiChartSectionBindingsOptions = {
  header: Parameters<typeof useZiweiChartHeaderBindings>[0]
  canvas: Parameters<typeof useZiweiChartCanvasBindings>[0]
  workspace: Omit<Parameters<typeof useZiweiChartWorkspaceBindings>[0], 'chartCanvasBindings'>
}

export function useZiweiChartSectionBindings(options: UseZiweiChartSectionBindingsOptions) {
  const { chartHeaderBindings } = useZiweiChartHeaderBindings(options.header)
  const { chartCanvasBindings } = useZiweiChartCanvasBindings(options.canvas)
  const { chartWorkspaceBindings } = useZiweiChartWorkspaceBindings({
    ...options.workspace,
    chartCanvasBindings,
  })

  const chartSectionBindings = computed(() => ({
    header: chartHeaderBindings.value,
    workspace: chartWorkspaceBindings.value,
  }))

  return {
    chartSectionBindings,
  }
}
