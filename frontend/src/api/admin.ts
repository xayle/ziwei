import apiClient from './client'

// ── 仪表盘 ────────────────────────────────────────────────
export interface DailyActivity {
  date: string
  count: number
}

export interface CaseSummary {
  case_id: string
  name: string
  created_at: string
}

export interface DashboardResponse {
  cases_total: number
  cases_this_month: number
  snapshots_total: number
  snapshots_this_month: number
  reviews_pending: number
  reviews_approved: number
  reviews_rejected: number
  reviews_revised: number
  daily_activity: DailyActivity[]
  recent_cases: CaseSummary[]
  generated_at: string
  owner_id: number | null
}

export async function getDashboard(): Promise<DashboardResponse> {
  const { data } = await apiClient.get<DashboardResponse>('/api/v1/analytics/dashboard')
  return data
}

export interface AdminStatsBucket {
  total: number
  active?: number
  inactive?: number
  running?: number
  total_events?: number
}

export interface AdminStatsCountItem {
  name: string
  count: number
}

export interface AdminStatsResponse {
  users: AdminStatsBucket
  audit_logs: AdminStatsBucket
  cases: AdminStatsBucket
  snapshots: AdminStatsBucket
  chart_cases: AdminStatsBucket
  reviews: {
    total: number
    pending: number
    approved: number
    rejected: number
    revised: number
  }
  api_keys: AdminStatsBucket
  experiments: AdminStatsBucket
  top_patterns: AdminStatsCountItem[]
  top_wuxing: AdminStatsCountItem[]
  generated_at: string
}

export async function getAdminStats(): Promise<AdminStatsResponse> {
  const { data } = await apiClient.get<AdminStatsResponse>('/api/v1/admin/stats')
  return data
}

// ── 审计日志 ──────────────────────────────────────────────
export interface AuditLogItem {
  id: number
  user_id: number
  action: string
  resource_type: string
  resource_id: string | null
  details: string | null
  ip_address: string | null
  status: string
  created_at: string
}

export interface AuditLogsResponse {
  items: AuditLogItem[]
  total: number
  next_cursor: number | null
}

export async function getAuditLogs(params?: {
  limit?: number
  before_id?: number
  action?: string
  resource_type?: string
}): Promise<AuditLogsResponse> {
  const { data } = await apiClient.get<AuditLogsResponse>('/api/v1/audit-logs', { params })
  return data
}

// ── 案例列表 ──────────────────────────────────────────────
export interface CaseItem {
  id: string
  name: string
  bazi_input?: Record<string, unknown>
  tags: string[] | null
  created_at: string
  updated_at: string
  last_snapshot_at?: string | null
}

export interface CaseListResponse {
  items: CaseItem[]
  total: number
  next_cursor: string | null
}

export async function getCases(params?: {
  limit?: number
  before_created_at?: string
  q?: string
}): Promise<CaseListResponse> {
  const { data } = await apiClient.get<CaseListResponse>('/api/v1/cases', { params })
  return data
}

export async function deleteCase(caseId: string): Promise<void> {
  await apiClient.delete(`/api/v1/cases/${caseId}`)
}

// ══════════════════════════════════════════════════════════
// ── Reviews 审查管理 ────────────────────────────────────
// ══════════════════════════════════════════════════════════

export interface ChartReviewCreate {
  case_id?: string
  chart_hash?: string
  chart_type?: string
  notes?: string
  [key: string]: unknown
}

export interface ChartReviewUpdate {
  status: string
  reviewer?: string
  notes?: string
  reject_reason?: string
}

export interface ChartReviewResponse {
  id: number
  case_id: string | null
  chart_hash: string | null
  chart_type: string | null
  status: string
  reviewer: string | null
  notes: string | null
  reject_reason: string | null
  created_at: string
  updated_at: string
  [key: string]: unknown
}

export interface ChartReviewListResponse {
  total: number
  items: ChartReviewResponse[]
}

export interface ReviewStats {
  total: number
  pending: number
  approved: number
  rejected: number
  revised: number
}

export interface BulkReviewAction {
  ids: number[]
  action: string
  reviewer?: string
  notes?: string
  reject_reason?: string
}

export interface BulkReviewResult {
  succeeded: number[]
  failed: number[]
  total: number
  action: string
}

export interface ReviewHistoryItem {
  action: string
  actor: string | null
  timestamp: string
  notes: string | null
  [key: string]: unknown
}

export interface ReviewHistoryResponse {
  review_id: number
  items: ReviewHistoryItem[]
  total: number
}

export interface AssignReviewRequest {
  assignee: string
}

export interface ReviewAssigneeItem {
  id: number
  username: string
  email: string
  role: string
  is_admin: boolean
  is_current_user: boolean
}

export interface ReviewAssigneeListResponse {
  current_username: string
  items: ReviewAssigneeItem[]
}

/** POST /api/v1/reviews — 创建审查 */
export async function createReview(req: ChartReviewCreate): Promise<ChartReviewResponse> {
  const { data } = await apiClient.post<ChartReviewResponse>('/api/v1/reviews', req)
  return data
}

/** GET /api/v1/reviews — 审查列表 */
export async function listReviews(params?: { status?: string; page?: number; page_size?: number }): Promise<ChartReviewListResponse> {
  const { data } = await apiClient.get<ChartReviewListResponse>('/api/v1/reviews', { params })
  return data
}

/** GET /api/v1/reviews/stats — 审查统计 */
export async function getReviewStats(): Promise<ReviewStats> {
  const { data } = await apiClient.get<ReviewStats>('/api/v1/reviews/stats')
  return data
}

/** GET /api/v1/reviews/queue — 审查队列 */
export async function getReviewQueue(params?: { page?: number; page_size?: number }): Promise<ChartReviewListResponse> {
  const { data } = await apiClient.get<ChartReviewListResponse>('/api/v1/reviews/queue', { params })
  return data
}

/** GET /api/v1/reviews/my-queue — 我的审查队列 */
export async function getMyReviewQueue(params?: { page?: number; page_size?: number }): Promise<ChartReviewListResponse> {
  const { data } = await apiClient.get<ChartReviewListResponse>('/api/v1/reviews/my-queue', { params })
  return data
}

/** GET /api/v1/reviews/assignees — 审核员候选列表 */
export async function getReviewAssignees(): Promise<ReviewAssigneeListResponse> {
  const { data } = await apiClient.get<ReviewAssigneeListResponse>('/api/v1/reviews/assignees')
  return data
}

/** POST /api/v1/reviews/bulk_action — 批量操作 */
export async function bulkReviewAction(req: BulkReviewAction): Promise<BulkReviewResult> {
  const { data } = await apiClient.post<BulkReviewResult>('/api/v1/reviews/bulk_action', req)
  return data
}

/** GET /api/v1/reviews/:id — 审查详情 */
export async function getReview(reviewId: number): Promise<ChartReviewResponse> {
  const { data } = await apiClient.get<ChartReviewResponse>(`/api/v1/reviews/${reviewId}`)
  return data
}

/** PATCH /api/v1/reviews/:id — 更新审查 */
export async function updateReview(reviewId: number, req: ChartReviewUpdate): Promise<ChartReviewResponse> {
  const { data } = await apiClient.patch<ChartReviewResponse>(`/api/v1/reviews/${reviewId}`, req)
  return data
}

/** DELETE /api/v1/reviews/:id — 删除审查 */
export async function deleteReview(reviewId: number): Promise<void> {
  await apiClient.delete(`/api/v1/reviews/${reviewId}`)
}

/** GET /api/v1/reviews/:id/history — 审查历史 */
export async function getReviewHistory(reviewId: number): Promise<ReviewHistoryResponse> {
  const { data } = await apiClient.get<ReviewHistoryResponse>(`/api/v1/reviews/${reviewId}/history`)
  return data
}

/** POST /api/v1/reviews/:id/assign — 分配审查 */
export async function assignReview(reviewId: number, req: AssignReviewRequest): Promise<ChartReviewResponse> {
  const { data } = await apiClient.post<ChartReviewResponse>(`/api/v1/reviews/${reviewId}/assign`, req)
  return data
}

// ══════════════════════════════════════════════════════════
// ── Experiments 实验管理 ─────────────────────────────────
// ══════════════════════════════════════════════════════════

export interface VariantDef { name: string; description: string; weight: number }

export interface ExperimentCreate {
  name: string
  description: string
  variants: VariantDef[]
  target_metric: string
  hypothesis: string
  min_sample_size: number
}

export interface ExperimentUpdate {
  name?: string
  description?: string
  status?: string
  hypothesis?: string
  min_sample_size?: number
  target_metric?: string
}

export interface ExperimentResponse {
  id: number
  name: string
  description: string
  status: string
  variants: VariantDef[]
  target_metric: string
  hypothesis: string
  min_sample_size: number
  created_at: string
  updated_at: string
  [key: string]: unknown
}

export interface ExperimentListResponse {
  total: number
  items: ExperimentResponse[]
}

export interface AssignRequest { session_id: string }
export interface AssignResponse { experiment_id: number; session_id: string; variant: string; is_new: boolean }

export interface ExperimentEventCreate { variant: string; event_type: string; session_id: string; meta?: Record<string, unknown> }

export interface VariantStats { variant: string; assigned: number; conversions: number; conversion_rate: number; other_events: Record<string, number> }
export interface ExperimentResults {
  experiment_id: number; experiment_name: string; status: string; target_metric: string
  min_sample_size: number; total_assigned: number; variants: VariantStats[]; winner: string | null; note: string
}

/** POST /api/v1/experiments — 创建实验 */
export async function createExperiment(req: ExperimentCreate): Promise<ExperimentResponse> {
  const { data } = await apiClient.post<ExperimentResponse>('/api/v1/experiments', req)
  return data
}

/** GET /api/v1/experiments — 实验列表 */
export async function listExperiments(params?: { status?: string; skip?: number; limit?: number }): Promise<ExperimentListResponse> {
  const { data } = await apiClient.get<ExperimentListResponse>('/api/v1/experiments', { params })
  return data
}

/** GET /api/v1/experiments/:id — 实验详情 */
export async function getExperiment(expId: number): Promise<ExperimentResponse> {
  const { data } = await apiClient.get<ExperimentResponse>(`/api/v1/experiments/${expId}`)
  return data
}

/** PUT /api/v1/experiments/:id — 更新实验 */
export async function updateExperiment(expId: number, req: ExperimentUpdate): Promise<ExperimentResponse> {
  const { data } = await apiClient.put<ExperimentResponse>(`/api/v1/experiments/${expId}`, req)
  return data
}

/** DELETE /api/v1/experiments/:id — 删除实验 */
export async function deleteExperiment(expId: number): Promise<void> {
  await apiClient.delete(`/api/v1/experiments/${expId}`)
}

/** POST /api/v1/experiments/:id/assign — 分配变体 */
export async function assignExperiment(expId: number, req: AssignRequest): Promise<AssignResponse> {
  const { data } = await apiClient.post<AssignResponse>(`/api/v1/experiments/${expId}/assign`, req)
  return data
}

/** POST /api/v1/experiments/:id/event — 记录实验事件 */
export async function recordExperimentEvent(expId: number, req: ExperimentEventCreate): Promise<{ ok: boolean; event_type: string; variant: string }> {
  const { data } = await apiClient.post(`/api/v1/experiments/${expId}/event`, req)
  return data
}

/** GET /api/v1/experiments/:id/results — 实验结果 */
export async function getExperimentResults(expId: number): Promise<ExperimentResults> {
  const { data } = await apiClient.get<ExperimentResults>(`/api/v1/experiments/${expId}/results`)
  return data
}

// ══════════════════════════════════════════════════════════
// ── API Keys 管理 ───────────────────────────────────────
// ══════════════════════════════════════════════════════════

export interface ApiKeyCreate {
  name: string
  scopes?: string
  rate_limit_per_min?: number
  expires_in_days?: number
}

export interface ApiKeyCreateResponse {
  id: number; name: string; key_prefix: string; scopes: string; rate_limit_per_min: number
  expires_at: string | null; created_at: string; plaintext_key: string
}

export interface ApiKeyResponse {
  id: number; name: string; key_prefix: string; scopes: string; rate_limit_per_min: number
  last_used_at: string | null; expires_at: string | null; revoked_at: string | null; created_at: string
}

export interface ApiKeyListResponse { total: number; items: ApiKeyResponse[] }

/** POST /api/v1/api-keys — 创建 API Key */
export async function createApiKey(req: ApiKeyCreate): Promise<ApiKeyCreateResponse> {
  const { data } = await apiClient.post<ApiKeyCreateResponse>('/api/v1/api-keys', req)
  return data
}

/** GET /api/v1/api-keys — API Key 列表 */
export async function listApiKeys(params?: { skip?: number; limit?: number }): Promise<ApiKeyListResponse> {
  const { data } = await apiClient.get<ApiKeyListResponse>('/api/v1/api-keys', { params })
  return data
}

/** GET /api/v1/api-keys/:id — API Key 详情 */
export async function getApiKey(keyId: number): Promise<ApiKeyResponse> {
  const { data } = await apiClient.get<ApiKeyResponse>(`/api/v1/api-keys/${keyId}`)
  return data
}

/** DELETE /api/v1/api-keys/:id — 吊销 API Key */
export async function revokeApiKey(keyId: number): Promise<{ message: string; revoked_at: string }> {
  const { data } = await apiClient.delete(`/api/v1/api-keys/${keyId}`)
  return data
}

// ══════════════════════════════════════════════════════════
// ── Rules 规则管理 ──────────────────────────────────────
// ══════════════════════════════════════════════════════════

/** GET /api/v1/rules — 生活建议规则 */
export async function getRules(): Promise<Array<Record<string, unknown>>> {
  const { data } = await apiClient.get<Array<Record<string, unknown>>>('/api/v1/rules')
  return data
}

/** PUT /api/v1/rules — 更新生活建议规则 */
export async function updateRules(rules: Array<Record<string, unknown>>): Promise<{ status: string; message: string }> {
  const { data } = await apiClient.put('/api/v1/rules', rules)
  return data
}

/** GET /api/v1/rules/remedies-rules — 化解建议规则 */
export async function getRemediesRules(): Promise<Array<Record<string, unknown>>> {
  const { data } = await apiClient.get<Array<Record<string, unknown>>>('/api/v1/rules/remedies-rules')
  return data
}

/** PUT /api/v1/rules/remedies-rules — 更新化解建议规则 */
export async function updateRemediesRules(rules: Array<Record<string, unknown>>): Promise<{ status: string; message: string }> {
  const { data } = await apiClient.put('/api/v1/rules/remedies-rules', rules)
  return data
}

// ══════════════════════════════════════════════════════════
// ── Delegations 权限委派 ────────────────────────────────
// ══════════════════════════════════════════════════════════

export interface DelegationCreateRequest {
  to_user_id: number
  permission_type: 'view' | 'edit' | 'share' | 'manage'
  member_id?: number
  expires_days?: number
}

export interface DelegationResponse {
  id: number
  from_user_id: number
  to_user_id: number
  permission_type: string
  member_scope: number | null
  is_active: boolean
  created_at: string
  expires_at: string
}

export interface DelegationListResponse {
  delegations: DelegationResponse[]
  total: number
}

export interface PermissionRequestBody {
  permission_type: string
  from_user_id?: number
  member_scope?: number
  expires_days?: number
}

/** POST /api/v1/delegations — 创建委派 */
export async function createDelegation(req: DelegationCreateRequest): Promise<DelegationResponse> {
  const { data } = await apiClient.post<DelegationResponse>('/api/v1/delegations', req)
  return data
}

/** GET /api/v1/delegations/outgoing — 主动委派列表 */
export async function getOutgoingDelegations(): Promise<DelegationListResponse> {
  const { data } = await apiClient.get<DelegationListResponse>('/api/v1/delegations/outgoing')
  return data
}

/** GET /api/v1/delegations/incoming — 被委派列表 */
export async function getIncomingDelegations(): Promise<DelegationListResponse> {
  const { data } = await apiClient.get<DelegationListResponse>('/api/v1/delegations/incoming')
  return data
}

/** DELETE /api/v1/delegations/:id — 撤销委派 */
export async function deleteDelegation(delegationId: number): Promise<void> {
  await apiClient.delete(`/api/v1/delegations/${delegationId}`)
}

/** POST /api/v1/permissions/request — 请求权限 */
export async function requestPermission(req: PermissionRequestBody): Promise<Record<string, unknown>> {
  const { data } = await apiClient.post('/api/v1/permissions/request', req)
  return data
}

/** PUT /api/v1/permissions/request/:id/approve — 批准权限请求 */
export async function approvePermissionRequest(delegationId: number): Promise<Record<string, unknown>> {
  const { data } = await apiClient.put(`/api/v1/permissions/request/${delegationId}/approve`)
  return data
}

/** PUT /api/v1/permissions/request/:id/reject — 拒绝权限请求 */
export async function rejectPermissionRequest(delegationId: number, body?: { reject_reason?: string }): Promise<Record<string, unknown>> {
  const { data } = await apiClient.put(`/api/v1/permissions/request/${delegationId}/reject`, body)
  return data
}

/** DELETE /api/v1/permissions/request/:id/revoke — 撤销权限请求 */
export async function revokePermissionRequest(delegationId: number): Promise<Record<string, unknown>> {
  const { data } = await apiClient.delete(`/api/v1/permissions/request/${delegationId}/revoke`)
  return data
}

/** POST /api/v1/admin/expire-delegations — 过期委派清理 */
export async function expireDelegations(): Promise<{ revoked: number; message: string }> {
  const { data } = await apiClient.post('/api/v1/admin/expire-delegations')
  return data
}

