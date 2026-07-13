import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

const getMock = vi.fn()
const postMock = vi.fn()

vi.mock('@/api/client', () => ({
  default: {
    get: (...args: unknown[]) => getMock(...args),
    post: (...args: unknown[]) => postMock(...args),
  },
}))

describe('entitlement store (T094)', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    getMock.mockReset()
    postMock.mockReset()
  })

  it('refreshFromServer loads unlocked volumes', async () => {
    getMock.mockResolvedValue({
      data: {
        user_id: 7,
        username: 'u',
        entitlement: 'volume_pass',
        entitlement_info: {
          tier: 'volume_pass',
          unlocked_volume_ids: ['preface', 'vol1', 'vol2', 'vol3', 'vol4', 'colophon'],
          schema_version: 'entitlement@1.0',
        },
      },
    })
    const { useEntitlementStore } = await import('@/stores/entitlement')
    const store = useEntitlementStore()
    await store.refreshFromServer()
    expect(store.tier).toBe('volume_pass')
    expect(store.isVolumeUnlockedByEntitlement('vol3')).toBe(true)
    expect(store.isVolumeUnlockedByEntitlement('vol5')).toBe(false)
  })

  it('sandboxPurchase posts webhook then refreshes me', async () => {
    getMock
      .mockResolvedValueOnce({
        data: {
          user_id: 3,
          username: 'u',
          entitlement: 'free',
          entitlement_info: { tier: 'free', unlocked_volume_ids: ['preface', 'vol1', 'colophon'] },
        },
      })
      .mockResolvedValueOnce({
        data: {
          user_id: 3,
          username: 'u',
          entitlement: 'volume_pass',
          entitlement_info: {
            tier: 'volume_pass',
            unlocked_volume_ids: ['preface', 'vol1', 'vol2', 'vol3', 'vol4', 'colophon'],
          },
        },
      })
    postMock.mockResolvedValue({
      data: { accepted: true, entitlement_applied: 'volume_pass', user_id: 3 },
    })

    const { useEntitlementStore } = await import('@/stores/entitlement')
    const store = useEntitlementStore()
    const ok = await store.sandboxPurchase('volume_pass')
    expect(ok).toBe(true)
    expect(postMock).toHaveBeenCalledWith(
      '/api/v1/payment/webhook',
      expect.objectContaining({ user_id: 3, plan: 'volume_pass' }),
    )
    expect(store.tier).toBe('volume_pass')
    expect(store.isVolumeUnlockedByEntitlement('vol4')).toBe(true)
  })
})
