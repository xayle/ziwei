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
})
