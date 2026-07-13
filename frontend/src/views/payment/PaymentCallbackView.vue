<script setup lang="ts">
/**
 * T094 · 支付成功回调页（沙箱）：刷新 entitlement → 报告卷解锁
 */
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useEntitlementStore } from '@/stores/entitlement'
import type { PaymentPlan } from '@/api/auth'
import { track } from '@/utils/analytics'
import '@/assets/variables.css'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const entitlement = useEntitlementStore()

const status = ref<'working' | 'ok' | 'error'>('working')
const message = ref('正在确认权益…')

function resolvePlan(): PaymentPlan {
  const raw = String(route.query.plan || 'volume_pass').toLowerCase()
  const allowed: PaymentPlan[] = ['free', 'volume_pass', 'full_book', 'pro', 'pass', 'book']
  return (allowed.includes(raw as PaymentPlan) ? raw : 'volume_pass') as PaymentPlan
}

onMounted(async () => {
  if (!auth.isLoggedIn) {
    status.value = 'error'
    message.value = '请先登录后再完成支付回调'
    await router.replace({
      name: 'login',
      query: { redirect: route.fullPath },
    })
    return
  }

  const plan = resolvePlan()
  track({
    event_type: 'funnel_step',
    properties: { step: 'payment_callback', plan },
  })

  const ok = await entitlement.sandboxPurchase(plan)
  if (!ok) {
    status.value = 'error'
    message.value = entitlement.lastError || '权益更新失败'
    return
  }

  status.value = 'ok'
  message.value = `已开通 ${entitlement.tier}，正在打开报告…`
  sessionStorage.setItem('fusheng-entitlement-refreshed', '1')
  // 演示锁关闭，避免与真实权益打架
  try {
    localStorage.removeItem('fusheng-demo-volume-locks')
  } catch {
    /* ignore */
  }

  await router.replace({
    path: '/report',
    query: { unlocked: '1', plan },
    hash: '#report-volume-vol3',
  })
})
</script>

<template>
  <div class="payment-callback" data-testid="payment-callback">
    <p class="payment-callback__brand">浮生</p>
    <p class="payment-callback__status" :data-status="status">{{ message }}</p>
    <p v-if="status === 'error'" class="payment-callback__hint">
      <router-link to="/report">返回报告</router-link>
      ·
      <router-link to="/profile">档案</router-link>
    </p>
  </div>
</template>

<style scoped>
.payment-callback {
  min-height: 100dvh;
  display: grid;
  place-content: center;
  gap: 0.75rem;
  padding: 2rem 1.25rem;
  text-align: center;
  background: var(--brand-paper, #f5f0e6);
  color: var(--brand-ink, #1a1410);
  font-family: "LXGW Neo ZhiSong", "Noto Serif SC", serif;
}

.payment-callback__brand {
  margin: 0;
  font-size: 1.75rem;
  letter-spacing: 0.28em;
  font-weight: 700;
}

.payment-callback__status {
  margin: 0;
  font-size: 1rem;
  color: var(--brand-mist, #6b5d4f);
}

.payment-callback__status[data-status='error'] {
  color: var(--brand-cinnabar, #8b3a2a);
}

.payment-callback__hint {
  margin: 0.5rem 0 0;
  font-size: 0.85rem;
}

.payment-callback__hint a {
  color: var(--brand-gold-dark, #8b5e34);
}
</style>
