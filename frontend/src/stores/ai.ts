/**
 * ai.ts — AI 助手面板状态
 * 管理聊天消息列表、流式输出态、当前命盘哈希
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { streamInterpretation, interpretModule } from '@/api/llm'
import type { StreamParams } from '@/api/llm'

export interface AiMessage {
  role: 'user' | 'ai'
  text: string
  streaming?: boolean
}

export const useAiStore = defineStore('ai', () => {
  const messages = ref<AiMessage[]>([
    { role: 'ai', text: '你好！我是命理 AI 助手，可以帮你生成解读草稿、分析八字格局。请选择一个案例或输入问题。' },
  ])
  const streaming = ref(false)
  const currentChartHash = ref<string | null>(null)
  const currentCaseId = ref<string | null>(null)

  /** 流式发送消息 */
  async function sendMessage(
    text: string,
    streamParams?: Omit<StreamParams, 'chart_hash'> & { chart_hash?: string }
  ) {
    if (streaming.value) return

    messages.value.push({ role: 'user', text })

    const aiMsg: AiMessage = { role: 'ai', text: '', streaming: true }
    messages.value.push(aiMsg)
    streaming.value = true

    try {
      await streamInterpretation(
        {
          chart_hash: streamParams?.chart_hash ?? currentChartHash.value ?? `chat_${Date.now()}`,
          life_palace_gz: streamParams?.life_palace_gz ?? '',
          wuxing_ju_name: streamParams?.wuxing_ju_name ?? '',
          pattern_summary: streamParams?.pattern_summary ?? text,
          birth_info_summary: streamParams?.birth_info_summary ?? '',
        },
        (chunk: string) => {
          aiMsg.text += chunk
        },
        (_fullText: string) => {
          aiMsg.streaming = false
        },
        (_savedId: number) => {
          // 草稿已自动保存到后端
        }
      )
    } catch (err) {
      aiMsg.text = '⚠️ AI 请求失败，请检查网络或重试。'
    } finally {
      aiMsg.streaming = false
      streaming.value = false
    }
  }

  /** 快捷模板：调用 interpret-module */
  async function sendModuleRequest(module: string, label: string) {
    if (!currentCaseId.value) {
      messages.value.push({ role: 'ai', text: '⚠️ 请先在案例中心选择一个案例，再使用快捷模板。' })
      return
    }
    if (streaming.value) return

    messages.value.push({ role: 'user', text: `请帮我分析：${label}` })
    const aiMsg: AiMessage = { role: 'ai', text: '', streaming: true }
    messages.value.push(aiMsg)
    streaming.value = true

    try {
      const res = await interpretModule(currentCaseId.value, module)
      aiMsg.text = res.interpretation
    } catch (err) {
      aiMsg.text = '⚠️ 模板分析失败，请重试。'
    } finally {
      aiMsg.streaming = false
      streaming.value = false
    }
  }

  function setCurrentCase(caseId: string, chartHash?: string) {
    currentCaseId.value = caseId
    if (chartHash) currentChartHash.value = chartHash
  }

  function clearMessages() {
    messages.value = [
      { role: 'ai', text: '已切换上下文，请继续提问。' }
    ]
  }

  return {
    messages,
    streaming,
    currentChartHash,
    currentCaseId,
    sendMessage,
    sendModuleRequest,
    setCurrentCase,
    clearMessages,
  }
})
