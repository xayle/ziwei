/**
 * api/admin.spec.ts — Admin API 模块单元测试（mock axios）
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { Mock } from 'vitest'

vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  },
}))

import apiClient from '@/api/client'
import {
  getDashboard, getAuditLogs, getCases, deleteCase,
} from '@/api/admin'
import type { DashboardResponse, AuditLogsResponse, CaseListResponse } from '@/api/admin'

// ── 测试数据 ─────────────────────────────────────────────
const MOCK_DASHBOARD: DashboardResponse = {
  cases_total: 42,
  cases_this_month: 7,
  snapshots_total: 128,
  snapshots_this_month: 15,
  reviews_pending: 3,
  reviews_approved: 20,
  reviews_rejected: 2,
  reviews_revised: 1,
  daily_activity: [
    { date: '2026-03-20', count: 5 },
    { date: '2026-03-21', count: 3 },
    { date: '2026-03-22', count: 8 },
    { date: '2026-03-23', count: 2 },
    { date: '2026-03-24', count: 6 },
    { date: '2026-03-25', count: 4 },
    { date: '2026-03-26', count: 9 },
  ],
  recent_cases: [
    { case_id: 'abc-001', name: '张三', created_at: '2026-03-25T10:00:00Z' },
    { case_id: 'abc-002', name: '李四', created_at: '2026-03-24T08:00:00Z' },
  ],
  generated_at: '2026-03-26T00:00:00Z',
  owner_id: 1,
}

const MOCK_AUDIT: AuditLogsResponse = {
  items: [
    {
      id: 101,
      user_id: 1,
      action: 'create_case',
      resource_type: 'case',
      resource_id: 'abc-001',
      details: null,
      ip_address: '127.0.0.1',
      status: 'success',
      created_at: '2026-03-26T10:00:00Z',
    },
    {
      id: 100,
      user_id: 1,
      action: 'compute_bazi',
      resource_type: 'computation',
      resource_id: null,
      details: null,
      ip_address: '127.0.0.1',
      status: 'success',
      created_at: '2026-03-26T09:00:00Z',
    },
  ],
  total: 50,
  next_cursor: 99,
}

const MOCK_CASES: CaseListResponse = {
  items: [
    {
      id: 'case-001',
      name: '张三命盘',
      tags: ['八字', '流年'],
      created_at: '2026-03-25T10:00:00Z',
      updated_at: '2026-03-25T10:00:00Z',
      last_snapshot_at: '2026-03-25T11:00:00Z',
    },
    {
      id: 'case-002',
      name: '李四紫微',
      tags: null,
      created_at: '2026-03-24T08:00:00Z',
      updated_at: '2026-03-24T08:00:00Z',
      last_snapshot_at: null,
    },
  ],
  total: 42,
  next_cursor: null,
}

describe('getDashboard()', () => {
  beforeEach(() => vi.clearAllMocks())

  it('调用 GET /api/v1/analytics/dashboard', async () => {
    ;(apiClient.get as Mock).mockResolvedValueOnce({ data: MOCK_DASHBOARD })

    const result = await getDashboard()

    expect(apiClient.get).toHaveBeenCalledOnce()
    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/analytics/dashboard')
    expect(result.cases_total).toBe(42)
    expect(result.daily_activity).toHaveLength(7)
    expect(result.recent_cases[0].name).toBe('张三')
  })
})

describe('getAuditLogs()', () => {
  beforeEach(() => vi.clearAllMocks())

  it('不传参数时调用 GET /api/v1/audit-logs', async () => {
    ;(apiClient.get as Mock).mockResolvedValueOnce({ data: MOCK_AUDIT })

    const result = await getAuditLogs()

    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/audit-logs', { params: undefined })
    expect(result.items).toHaveLength(2)
    expect(result.total).toBe(50)
    expect(result.next_cursor).toBe(99)
  })

  it('传入 before_id 和 action 时一并发送', async () => {
    ;(apiClient.get as Mock).mockResolvedValueOnce({ data: MOCK_AUDIT })

    await getAuditLogs({ limit: 50, before_id: 100, action: 'create_case' })

    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/audit-logs', {
      params: { limit: 50, before_id: 100, action: 'create_case' },
    })
  })
})

describe('getCases()', () => {
  beforeEach(() => vi.clearAllMocks())

  it('调用 GET /api/v1/cases 并返回案例列表', async () => {
    ;(apiClient.get as Mock).mockResolvedValueOnce({ data: MOCK_CASES })

    const result = await getCases({ limit: 20 })

    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/cases', {
      params: { limit: 20 },
    })
    expect(result.items).toHaveLength(2)
    expect(result.items[0].tags).toEqual(['八字', '流年'])
    expect(result.items[1].tags).toBeNull()
    expect(result.next_cursor).toBeNull()
  })
})

describe('deleteCase()', () => {
  beforeEach(() => vi.clearAllMocks())

  it('调用 DELETE /api/v1/cases/:id', async () => {
    ;(apiClient.delete as Mock).mockResolvedValueOnce({})

    await deleteCase('case-001')

    expect(apiClient.delete).toHaveBeenCalledOnce()
    expect(apiClient.delete).toHaveBeenCalledWith('/api/v1/cases/case-001')
  })
})
