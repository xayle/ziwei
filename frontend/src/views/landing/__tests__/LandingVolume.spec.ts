import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import LandingVolume from '@/views/landing/LandingVolume.vue'
import { LANDING_BRAND, LANDING_CTA, LANDING_DISCLAIMER } from '@/constants/landingVolume'
import { UTM_STORAGE_KEY } from '@/utils/utmCapture'

vi.mock('@/utils/analytics', () => ({
  track: vi.fn(),
  trackVolumeView: vi.fn(),
  trackLandingCta: vi.fn(),
  flushAnalytics: vi.fn(async () => null),
}))

describe('LandingVolume (T091)', () => {
  beforeEach(() => {
    sessionStorage.clear()
  })

  async function mountLanding(query: Record<string, string> = {}) {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/landing', name: 'landing', component: LandingVolume },
        { path: '/profile', name: 'profile', component: { template: '<div />' } },
      ],
    })
    await router.push({ path: '/landing', query })
    await router.isReady()
    return mount(LandingVolume, {
      global: { plugins: [router] },
    })
  }

  it('renders brand, preface CTA and disclaimer', async () => {
    const wrapper = await mountLanding()
    expect(wrapper.get('[data-testid="landing-volume"]').exists()).toBe(true)
    expect(wrapper.text()).toContain(LANDING_BRAND)
    expect(wrapper.get('[data-testid="landing-cta"]').text()).toContain(LANDING_CTA)
    expect(wrapper.get('[data-testid="landing-disclaimer"]').text()).toBe(LANDING_DISCLAIMER)
  })

  it('captures utm and navigates to profile on CTA', async () => {
    const wrapper = await mountLanding({
      utm_source: 'douyin',
      utm_campaign: 'geju_hook',
      content_id: 'video_1',
    })
    await flushPromises()
    const stored = JSON.parse(sessionStorage.getItem(UTM_STORAGE_KEY) || '{}') as {
      utm_source?: string
      content_id?: string
    }
    expect(stored.utm_source).toBe('douyin')
    expect(stored.content_id).toBe('video_1')

    await wrapper.get('[data-testid="landing-cta"]').trigger('click')
    await flushPromises()
    const router = wrapper.vm.$router
    expect(router.currentRoute.value.path).toBe('/profile')
    expect(router.currentRoute.value.query.utm_source).toBe('douyin')
    expect(router.currentRoute.value.query.from).toBe('landing')
  })

  it('root landing node is present for mobile layout', async () => {
    const wrapper = await mountLanding()
    expect(wrapper.get('[data-testid="landing-volume"]').classes()).toContain('landing-volume')
  })
})
