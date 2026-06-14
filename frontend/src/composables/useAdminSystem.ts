import { ref } from 'vue'
import {
  listExperiments, deleteExperiment, getExperimentResults,
  listApiKeys, createApiKey, revokeApiKey,
  getRules, updateRules, getRemediesRules, updateRemediesRules,
} from '@/api/admin'
import type {
  ExperimentResponse, ExperimentResults,
  ApiKeyResponse, ApiKeyCreateResponse,
} from '@/api/admin'

/** 实验管理 + API 密钥管理 + 规则管理 */
export function useAdminSystem() {
  // ── 实验管理 ──────────────────────────────────────────────
  const experiments = ref<ExperimentResponse[]>([])
  const experimentsTotal = ref(0)
  const experimentsLoading = ref(false)
  const experimentsLoaded = ref(false)
  const expResults = ref<ExperimentResults | null>(null)

  async function loadExperiments() {
    if (experimentsLoading.value) return
    experimentsLoading.value = true
    try {
      const res = await listExperiments({ limit: 30 })
      experiments.value = res.items
      experimentsTotal.value = res.total
      experimentsLoaded.value = true
    } catch { /* ignore */ }
    finally { experimentsLoading.value = false }
  }

  async function handleDeleteExperiment(id: number) {
    if (!confirm('确认删除实验？')) return
    try { await deleteExperiment(id); await loadExperiments() } catch { alert('删除失败') }
  }

  async function handleViewResults(id: number) {
    try { expResults.value = await getExperimentResults(id) } catch { alert('获取结果失败') }
  }

  // ── API 密钥管理 ─────────────────────────────────────────
  const apiKeys = ref<ApiKeyResponse[]>([])
  const apiKeysLoading = ref(false)
  const apiKeysLoaded = ref(false)
  const newKeyName = ref('')
  const newKeyResult = ref<ApiKeyCreateResponse | null>(null)

  async function loadApiKeys() {
    if (apiKeysLoading.value) return
    apiKeysLoading.value = true
    try {
      const res = await listApiKeys({ limit: 50 })
      apiKeys.value = res.items
      apiKeysLoaded.value = true
    } catch { /* ignore */ }
    finally { apiKeysLoading.value = false }
  }

  async function handleCreateApiKey() {
    if (!newKeyName.value.trim()) return
    try {
      newKeyResult.value = await createApiKey({ name: newKeyName.value.trim() })
      newKeyName.value = ''
      await loadApiKeys()
    } catch { alert('创建失败') }
  }

  async function handleRevokeApiKey(id: number) {
    if (!confirm('确认吊销此密钥？')) return
    try { await revokeApiKey(id); await loadApiKeys() } catch { alert('吊销失败') }
  }

  // ── 规则管理 ─────────────────────────────────────────────
  const rulesData = ref<Array<Record<string, unknown>>>([])
  const remediesData = ref<Array<Record<string, unknown>>>([])
  const rulesLoading = ref(false)
  const rulesLoaded = ref(false)
  const rulesEditJson = ref('')
  const remediesEditJson = ref('')
  const rulesSaving = ref(false)

  async function loadRules() {
    if (rulesLoading.value) return
    rulesLoading.value = true
    try {
      const [r, rem] = await Promise.all([getRules(), getRemediesRules()])
      rulesData.value = r
      remediesData.value = rem
      rulesEditJson.value = JSON.stringify(r, null, 2)
      remediesEditJson.value = JSON.stringify(rem, null, 2)
      rulesLoaded.value = true
    } catch { /* ignore */ }
    finally { rulesLoading.value = false }
  }

  async function saveRules() {
    rulesSaving.value = true
    try {
      const parsed = JSON.parse(rulesEditJson.value)
      await updateRules(parsed)
      alert('生活建议规则已保存')
    } catch (e: unknown) { alert('保存失败: ' + (e as Error).message) }
    finally { rulesSaving.value = false }
  }

  async function saveRemedies() {
    rulesSaving.value = true
    try {
      const parsed = JSON.parse(remediesEditJson.value)
      await updateRemediesRules(parsed)
      alert('化解建议规则已保存')
    } catch (e: unknown) { alert('保存失败: ' + (e as Error).message) }
    finally { rulesSaving.value = false }
  }

  return {
    experiments, experimentsTotal, experimentsLoading, experimentsLoaded, expResults,
    loadExperiments, handleDeleteExperiment, handleViewResults,
    apiKeys, apiKeysLoading, apiKeysLoaded, newKeyName, newKeyResult,
    loadApiKeys, handleCreateApiKey, handleRevokeApiKey,
    rulesData, remediesData, rulesLoading, rulesLoaded, rulesEditJson, remediesEditJson, rulesSaving,
    loadRules, saveRules, saveRemedies,
  }
}
