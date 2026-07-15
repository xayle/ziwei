import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import PaymentCallbackView from '@/views/payment/PaymentCallbackView.vue'
import { useProfileStore } from '@/stores/profile'

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

async function mountCallback(query: Record<string, string> = { plan: 'volume_pass' }) {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/payment/callback', name: 'payment-callback', component: PaymentCallbackView },
      { path: '/report', name: 'report', component: { template: '<div />' } },
      { path: '/profile', name: 'profile', component: { template: '<div />' } },
      { path: '/login', name: 'login', component: { template: '<div />' } },
    ],
  })
  await router.push({ path: '/payment/callback', query })
  await router.isReady()
  mount(PaymentCallbackView, { global: { plugins: [router] } })
  await flushPromises()
  return router
}

describe('PaymentCallbackView (T094)', () => {
  beforeEach(() => {
    localStorage.clear()
    sessionStorage.clear()
    setActivePinia(createPinia())
    sandboxPurchase.mockReset()
    sandboxPurchase.mockResolvedValue(true)
  })

  it('runs sandbox purchase and routes to report when archive is ready', async () => {
    const profile = useProfileStore()
    profile.setProfile({
      birthDt: '1990-01-15T08:30',
      gender: 'male',
      cityName: '北京',
      lon: 116.41,
    })

    const router = await mountCallback()

    expect(sandboxPurchase).toHaveBeenCalledWith('volume_pass')
    expect(router.currentRoute.value.path).toBe('/report')
    expect(router.currentRoute.value.query.unlocked).toBe('1')
  })

  it('routes to profile with redirect when archive is incomplete', async () => {
    // 默认空档案 + 不清的 LS：AUTH-02 应把门禁带回档案并带 redirect
    const profile = useProfileStore()
    profile.setProfile({
      birthDt: '',
      gender: '',
      cityName: '',
      lon: undefined,
    })

    const router = await mountCallback({ plan: 'full_book' })

    expect(sandboxPurchase).toHaveBeenCalledWith('full_book')
    expect(router.currentRoute.value.path).toBe('/profile')
    expect(router.currentRoute.value.query.reason).toBe('archive')
    expect(router.currentRoute.value.query.redirect).toBe('/report?unlocked=1')
    expect(router.currentRoute.value.query.plan).toBe('full_book')
  })
})
