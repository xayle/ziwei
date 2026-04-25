/**
 * api/auth.spec.ts — Auth API 模块单元测试（mock axios）
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { Mock } from 'vitest'

// mock apiClient
vi.mock('@/api/client', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  },
}))

import apiClient from '@/api/client'
import { login } from '@/api/auth'

describe('login()', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('调用 POST /api/v1/auth/login 并返回 token', async () => {
    const mockResponse = {
      data: {
        access_token: 'eyJhbGci.test',
        refresh_token: 'refresh-tok',
        token_type: 'bearer',
        expires_in: 3600,
      },
    }
    ;(apiClient.post as Mock).mockResolvedValueOnce(mockResponse)

    const result = await login('admin', 'password123')
    expect(apiClient.post).toHaveBeenCalledWith('/api/v1/auth/login', {
      username: 'admin',
      password: 'password123',
    })
    expect(result.access_token).toBe('eyJhbGci.test')
    expect(result.token_type).toBe('bearer')
  })

  it('登录失败时向上抛出错误', async () => {
    const axiosError = { response: { status: 401, data: { detail: 'Invalid credentials' } } }
    ;(apiClient.post as Mock).mockRejectedValueOnce(axiosError)

    await expect(login('wrong', 'wrong')).rejects.toMatchObject({
      response: { status: 401 },
    })
  })
})
