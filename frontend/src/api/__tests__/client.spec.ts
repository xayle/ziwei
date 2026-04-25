/**
 * client.spec.ts — axios 客户端拦截器单元测试
 * 测试：Bearer Token 注入 / 401 自动清 token / 401 派发 app:unauthorized 事件
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import axios from 'axios'

// ── 不直接 import client.ts，通过 axios mock 测试拦截逻辑 ────
// 重新 import client 时让拦截器真正注册
vi.mock('axios', async () => {
  const actual = await vi.importActual<typeof import('axios')>('axios')
  const { default: _default, ...rest } = actual as Record<string, unknown>
  return { default: _default, ...rest }
})

// ─────────────────────────────────────────────────────────
describe('apiClient — 请求拦截器（Bearer Token 注入）', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.resetModules()
  })
  afterEach(() => {
    localStorage.clear()
  })

  it('有 token 时在 Authorization 头注入 Bearer', async () => {
    localStorage.setItem('token', 'test-token-abc')

    // 重新加载模块使拦截器读取新的 localStorage
    const { default: client } = await import('@/api/client')

    // mock adapter 截获请求，检查 headers
    const adapter = vi.fn().mockResolvedValue({
      data: {}, status: 200, statusText: 'OK', headers: {}, config: {} as never,
    })
    const config = await (client.interceptors.request as unknown as {
      handlers: Array<{ fulfilled: (c: object) => object }>
    }).handlers[0].fulfilled({
      headers: { Authorization: undefined },
    })
    expect((config as { headers: { Authorization?: string } }).headers.Authorization)
      .toBe('Bearer test-token-abc')
    void adapter // 避免 unused warning
  })

  it('无 token 时不注入 Authorization 头', async () => {
    const { default: client } = await import('@/api/client')
    const config = await (client.interceptors.request as unknown as {
      handlers: Array<{ fulfilled: (c: object) => object }>
    }).handlers[0].fulfilled({
      headers: {},
    })
    expect((config as { headers: { Authorization?: string } }).headers.Authorization)
      .toBeUndefined()
  })
})

// ─────────────────────────────────────────────────────────
describe('apiClient — 响应拦截器（401 处理）', () => {
  beforeEach(() => {
    localStorage.setItem('token', 'some-token')
    localStorage.setItem('username', 'admin')
    vi.resetModules()
  })
  afterEach(() => {
    localStorage.clear()
  })

  it('收到 401 时清除 token 和 username', async () => {
    const { default: client } = await import('@/api/client')

    const errHandler = (client.interceptors.response as unknown as {
      handlers: Array<{ rejected: (e: object) => Promise<unknown> }>
    }).handlers[0].rejected

    const err = { response: { status: 401 } }
    await expect(errHandler(err)).rejects.toEqual(err)

    expect(localStorage.getItem('token')).toBeNull()
    expect(localStorage.getItem('username')).toBeNull()
  })

  it('收到 401 时派发 app:unauthorized 自定义事件', async () => {
    const { default: client } = await import('@/api/client')
    const dispatchSpy = vi.spyOn(window, 'dispatchEvent')

    const errHandler = (client.interceptors.response as unknown as {
      handlers: Array<{ rejected: (e: object) => Promise<unknown> }>
    }).handlers[0].rejected

    await expect(errHandler({ response: { status: 401 } })).rejects.toBeDefined()

    expect(dispatchSpy).toHaveBeenCalledOnce()
    const evt = dispatchSpy.mock.calls[0][0] as CustomEvent
    expect(evt.type).toBe('app:unauthorized')

    dispatchSpy.mockRestore()
  })

  it('非 401 错误（如 500）不清除 token 也不派发事件', async () => {
    const { default: client } = await import('@/api/client')
    const dispatchSpy = vi.spyOn(window, 'dispatchEvent')

    const errHandler = (client.interceptors.response as unknown as {
      handlers: Array<{ rejected: (e: object) => Promise<unknown> }>
    }).handlers[0].rejected

    await expect(errHandler({ response: { status: 500 } })).rejects.toBeDefined()

    expect(localStorage.getItem('token')).toBe('some-token')  // 未被清除
    expect(dispatchSpy).not.toHaveBeenCalled()

    dispatchSpy.mockRestore()
  })
})
