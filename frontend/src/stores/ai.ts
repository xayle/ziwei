/**
 * ai.ts — LLM 解读面板（登录后接 /api/v1/llm）
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { BaziResponse } from '@/api/bazi'
import type { ZiweiResponse } from '@/api/ziwei'
import {
  getLlmConfig,
  interpretBaziByCase,
  interpretChart,
  interpretModule,
  type LlmDraftResponse,
  type LlmModuleId,
} from '@/api/llm'
import { useAuthStore } from '@/stores/auth'
import { useProfileStore } from '@/stores/profile'
import { buildChartHash } from '@/utils/chartHash'
import { formatAxiosError } from '@/utils/formatApiDetail'

export interface AiMessage {
  role: 'user' | 'ai'
  text: string
  streaming?: boolean
}

export const useAiStore = defineStore('ai', () => {
  const messages = ref<AiMessage[]>([])
  const streaming = ref(false)
  const loading = ref(false)
  const error = ref('')
  const configAvailable = ref(false)
  const configNote = ref('')
  const currentDraft = ref<LlmDraftResponse | null>(null)
  const currentChartHash = ref<string | null>(null)
  const currentCaseId = ref<string | null>(null)
  const moduleInterpretation = ref('')
  const moduleLoading = ref(false)
  const moduleError = ref('')

  async function loadConfig() {
    try {
      const cfg = await getLlmConfig()
      configAvailable.value = cfg.available
      configNote.value = cfg.note || `提供商 ${cfg.provider} · 模型 ${cfg.model}`
    } catch {
      configAvailable.value = false
      configNote.value = '问书大模型配置不可用'
    }
  }

  async function generateInterpretation(params: {
    bazi: BaziResponse | null
    ziwei: ZiweiResponse | null
    profileSignature: string
  }): Promise<LlmDraftResponse | null> {
    const auth = useAuthStore()
    if (!auth.isLoggedIn) {
      error.value = '请先登录后使用 AI 解读。'
      return null
    }

    const profile = useProfileStore()
    const remoteCaseId = profile.activeProfile?.remoteCaseId ?? null

    loading.value = true
    error.value = ''
    streaming.value = true
    messages.value = []

    try {
      if (remoteCaseId) {
        currentCaseId.value = remoteCaseId
        const draft = await interpretBaziByCase({ case_id: remoteCaseId })
        currentDraft.value = draft
        currentChartHash.value = draft.chart_hash
        messages.value = [{ role: 'ai', text: draft.draft_text }]
        return draft
      }

      const hash = await buildChartHash(params.profileSignature)
      currentChartHash.value = hash
      const bazi = params.bazi
      const ziwei = params.ziwei
      const draft = await interpretChart({
        chart_hash: hash,
        life_palace_gz: ziwei?.life_palace_gz || '',
        wuxing_ju_name: ziwei?.wuxing_ju_name || '',
        pattern_summary: bazi?.geju?.interpretation_text?.slice(0, 300) || bazi?.geju?.geju_name || '',
        birth_info_summary: profile.activeProfile?.label || '',
        geju_name: bazi?.geju?.geju_name || '',
        yongshen_favor: bazi?.yongshen?.favor || [],
      })
      currentDraft.value = draft
      messages.value = [{ role: 'ai', text: draft.draft_text }]
      return draft
    } catch (e: unknown) {
      error.value = formatAxiosError(e, '问书解读生成失败，请稍后重试。').replace(/\bLLM\b/g, '问书')
      return null
    } finally {
      loading.value = false
      streaming.value = false
    }
  }

  async function sendMessage(text: string) {
    messages.value.push({ role: 'user', text })
    messages.value.push({
      role: 'ai',
      text: '暂不支持多轮对话，请使用「生成 AI 解读」。',
    })
  }

  async function generateModuleInterpretation(module: LlmModuleId): Promise<string | null> {
    const auth = useAuthStore()
    if (!auth.isLoggedIn) {
      moduleError.value = '请先登录后使用分模块解读。'
      return null
    }

    const profile = useProfileStore()
    const remoteCaseId = profile.activeProfile?.remoteCaseId ?? null
    if (!remoteCaseId) {
      moduleError.value = '请先同步档案到云端后再使用分模块解读。'
      return null
    }

    moduleLoading.value = true
    moduleError.value = ''
    moduleInterpretation.value = ''

    try {
      const res = await interpretModule({ case_id: remoteCaseId, module })
      moduleInterpretation.value = res.interpretation
      return res.interpretation
    } catch (e: unknown) {
      moduleError.value = formatAxiosError(e, '分模块解读生成失败，请稍后重试。').replace(/\bLLM\b/g, '问书')
      return null
    } finally {
      moduleLoading.value = false
    }
  }

  return {
    messages,
    streaming,
    loading,
    error,
    configAvailable,
    configNote,
    currentDraft,
    currentChartHash,
    currentCaseId,
    moduleInterpretation,
    moduleLoading,
    moduleError,
    loadConfig,
    generateInterpretation,
    generateModuleInterpretation,
    sendMessage,
  }
})
