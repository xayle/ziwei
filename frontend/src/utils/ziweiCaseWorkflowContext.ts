import type { ZiweiResponse } from '@/api/ziwei'
import { readStorage, removeStorage, writeStorage } from '@/utils/browserStorage'

export interface ZiweiCaseWorkflowInput {
  year: number
  month: number
  day: number
  hour: number
  minute: number
  gender: '男' | '女'
  longitude: number | null
  liunian_year: number | null
  template_version?: string | null
  city_name?: string | null
}

export interface ZiweiCaseWorkflowContext {
  chartInput: ZiweiCaseWorkflowInput | null
  chartResult: ZiweiResponse | null
  savedCaseId: string
  savedCaseName: string
  currentSnapshotId: string
  summary: string
  createdAt: string
}

const STORAGE_KEY = 'ziwei_case_workflow_context'

export function saveZiweiCaseWorkflowContext(context: ZiweiCaseWorkflowContext): void {
  writeStorage(STORAGE_KEY, JSON.stringify(context), 'session')
}

export function loadZiweiCaseWorkflowContext(): ZiweiCaseWorkflowContext | null {
  const raw = readStorage(STORAGE_KEY, 'session')
  if (!raw) return null

  try {
    return JSON.parse(raw) as ZiweiCaseWorkflowContext
  } catch {
    return null
  }
}

export function clearZiweiCaseWorkflowContext(): void {
  removeStorage(STORAGE_KEY, 'session')
}
