import { describe, expect, it } from 'vitest'
import { formatApiDetail, formatAxiosError } from '@/utils/formatApiDetail'

describe('formatApiDetail', () => {
  it('keeps string detail', () => {
    expect(formatApiDetail('密码错误')).toBe('密码错误')
  })

  it('joins FastAPI 422 array detail', () => {
    expect(formatApiDetail([
      { loc: ['body', 'password'], msg: 'Field required', type: 'missing' },
      { msg: 'too short' },
    ])).toBe('Field required；too short')
  })

  it('reads object msg', () => {
    expect(formatApiDetail({ msg: '无权访问' })).toBe('无权访问')
  })
})

describe('formatAxiosError', () => {
  it('reads response detail', () => {
    expect(formatAxiosError({ response: { data: { detail: [{ msg: 'invalid' }] } } })).toBe('invalid')
  })

  it('maps opaque network messages to Chinese fallback', () => {
    expect(formatAxiosError(new Error('Network Error'), '登录失败，请检查服务是否启动'))
      .toBe('登录失败，请检查服务是否启动')
    expect(formatAxiosError(new Error('Failed to fetch'), '请求失败，请稍后重试。'))
      .toBe('请求失败，请稍后重试。')
  })
})
