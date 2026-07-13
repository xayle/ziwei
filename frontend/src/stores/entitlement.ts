/**
 * 当前用户权益（T086 / T094）— 来自 GET /auth/me
 */

import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import {
  fetchAuthMe,
  postSandboxPaymentWebhook,
  type AuthMeResponse,
  type EntitlementTier,
  type PaymentPlan,
} from '@/api/auth'
import type { LifeVolumeId } from '@/types/life-volume'

export const useEntitlementStore = defineStore('entitlement', () => {
  const userId = ref<number | null>(null)
  const tier = ref<EntitlementTier>('free')
  const unlockedVolumeIds = ref<LifeVolumeId[]>([])
  const loading = ref(false)
  const lastError = ref<string | null>(null)
  const loaded = ref(false)

  const unlockedSet = computed(() => new Set(unlockedVolumeIds.value))

  function applyMe(me: AuthMeResponse) {
    userId.value = me.user_id
    tier.value = me.entitlement ?? me.entitlement_info?.tier ?? 'free'
    unlockedVolumeIds.value = (me.entitlement_info?.unlocked_volume_ids ?? []) as LifeVolumeId[]
    loaded.value = true
    lastError.value = null
  }

  async function refreshFromServer(): Promise<AuthMeResponse | null> {
    loading.value = true
    lastError.value = null
    try {
      const me = await fetchAuthMe()
      applyMe(me)
      return me
    } catch (e) {
      lastError.value = e instanceof Error ? e.message : '刷新权益失败'
      return null
    } finally {
      loading.value = false
    }
  }

  /** 沙箱：调支付 webhook 再拉 /auth/me */
  async function sandboxPurchase(plan: PaymentPlan): Promise<boolean> {
    loading.value = true
    lastError.value = null
    try {
      let uid = userId.value
      if (uid == null) {
        const me = await fetchAuthMe()
        applyMe(me)
        uid = me.user_id
      }
      await postSandboxPaymentWebhook({
        user_id: uid,
        plan,
        event_type: 'checkout.completed',
        provider: 'stripe',
      })
      const me = await fetchAuthMe()
      applyMe(me)
      return true
    } catch (e) {
      lastError.value = e instanceof Error ? e.message : '沙箱支付失败'
      return false
    } finally {
      loading.value = false
    }
  }

  function isVolumeUnlockedByEntitlement(volumeId: string): boolean {
    if (!loaded.value) return false
    return unlockedSet.value.has(volumeId as LifeVolumeId)
  }

  function reset() {
    userId.value = null
    tier.value = 'free'
    unlockedVolumeIds.value = []
    loaded.value = false
    lastError.value = null
  }

  return {
    userId,
    tier,
    unlockedVolumeIds,
    loading,
    lastError,
    loaded,
    refreshFromServer,
    sandboxPurchase,
    isVolumeUnlockedByEntitlement,
    reset,
  }
})
