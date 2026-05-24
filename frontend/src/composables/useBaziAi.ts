/**
 * useBaziAi.ts — 八字 AI 深度解读状态管理
 *
 * 提供：
 *  - aiModule / aiLoading / aiError / aiStatus / aiDraft
 *  - aiParagraphs        解读文本段落数组（computed）
 *  - AI_MODULE_OPTIONS   下拉选项列表
 *  - generateAiInterpretation()  调用后端生成解读
 *  - resetAiState()              清空所有 AI 状态
 */
import { ref, computed, type Ref } from 'vue'
import { interpretBazi } from '@/api/llm'

export interface AiDraft {
  draft_text:     string
  provider:       string
  model:          string
  prompt_version: string
  status:         string
  input_tokens:   number
  output_tokens:  number
}

export const AI_MODULE_OPTIONS = [
  { value: '',                  label: '（全局解读）' },
  { value: 'career_detail',     label: '事业详解' },
  { value: 'wealth_detail',     label: '财富详解' },
  { value: 'marriage_detail',   label: '婚恋详解' },
  { value: 'dayun_narrative',   label: '大运叙述' },
  { value: 'fengshui_suggestion', label: '风水建议' },
]

export function useBaziAi(savedCaseId: Ref<string | null>) {
  const aiModule  = ref('')
  const aiLoading = ref(false)
  const aiError   = ref('')
  const aiStatus  = ref('')
  const aiDraft   = ref<AiDraft | null>(null)

  const aiParagraphs = computed(() => {
    const text = aiDraft.value?.draft_text ?? ''
    return text
      .split(/\n{2,}/)
      .map(item => item.trim())
      .filter(Boolean)
  })

  function resetAiState(): void {
    aiModule.value  = ''
    aiLoading.value = false
    aiError.value   = ''
    aiStatus.value  = ''
    aiDraft.value   = null
  }

  function extractErrorMessage(e: unknown, fallback: string): string {
    return (e as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
      ?? (e as { message?: string })?.message
      ?? fallback
  }

  async function generateAiInterpretation(): Promise<void> {
    if (!savedCaseId.value) {
      aiError.value = '请先保存案例，再生成深度解读'
      return
    }
    aiLoading.value = true
    aiError.value   = ''
    aiStatus.value  = '生成中，请稍候…'
    try {
      const draft   = await interpretBazi(savedCaseId.value, aiModule.value || undefined)
      aiDraft.value  = draft as AiDraft
      aiStatus.value = '生成完成'
    } catch (e: unknown) {
      aiError.value  = extractErrorMessage(e, '深度解读生成失败，请稍后重试')
      aiStatus.value = ''
    } finally {
      aiLoading.value = false
    }
  }

  return {
    aiModule,
    aiLoading,
    aiError,
    aiStatus,
    aiDraft,
    aiParagraphs,
    AI_MODULE_OPTIONS,
    generateAiInterpretation,
    resetAiState,
  }
}
