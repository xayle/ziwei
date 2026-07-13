import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import PaymentCallbackView from '@/views/payment/PaymentCallbackView.vue'

const sandboxPurchase = vi.fn()

vi.mock('@/utils/analytics', () => ({
  track: vi.fn(),
}))

vi.mock('@/stores/auth', () => ({
  useAuthStore: () => ({ isLoggedIn: true }),
}))

vi.mock('@/stores/entitlement', () => ({
  useEntitlementStore: () => ({
    sandboxPurchase,
    lastError: null,
    tier: 'volume_pass',
    loading: false,
  }),
}))

describe('PaymentCallbackView (T094)', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    sandboxPurchase.mockReset()
    sandboxPurchase.mockResolvedValue(true)
    sessionStorage.clear()
  })

  it('runs sandbox purchase and routes to report', async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/payment/callback', name: 'payment-callback', component: PaymentCallbackView },
        { path: '/report', name: 'report', component: { template: '<div />' } },
        { path: '/login', name: 'login', component: { template: '<div />' } },
      ],
    })
    await router.push({ path: '/payment/callback', query: { plan: 'volume_pass' } })
    await router.isReady()

    mount(PaymentCallbackView, { global: { plugins: [router] } })
    await flushPromises()

    expect(sandboxPurchase).toHaveBeenCalledWith('volume_pass')
    expect(router.currentRoute.value.path).toBe('/report')
    expect(router.currentRoute.value.query.unlocked).toBe('1')
  })
})
