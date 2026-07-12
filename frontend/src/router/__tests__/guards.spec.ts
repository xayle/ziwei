import { describe, expect, it } from 'vitest'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { registerRouterGuards } from '@/router/index'
import { useProfileStore } from '@/stores/profile'

describe('router archive guard', () => {
  it('redirects to profile when archive incomplete', async () => {
    setActivePinia(createPinia())
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/profile', component: { template: '<div />' } },
        { path: '/new/bazi', meta: { requiresArchive: true }, component: { template: '<div />' } },
      ],
    })
    registerRouterGuards(router)
    const profile = useProfileStore()
    profile.setProfile({
      birthDt: '',
      gender: '',
      cityName: '',
      lon: undefined,
    })

    await router.push('/new/bazi')
    expect(router.currentRoute.value.path).toBe('/profile')
    expect(router.currentRoute.value.query.reason).toBe('archive')
  })
})
