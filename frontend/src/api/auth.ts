import apiClient from './client'
import type { LoginRequest, RefreshTokenResponse, TokenResponse } from './openapiTypes'

export type { LoginRequest, RefreshTokenResponse, TokenResponse }

export type EntitlementTier = 'free' | 'volume_pass' | 'full_book'

export type AuthMeResponse = {
  user_id: number
  username: string
  email?: string
  role?: string
  /** T100：创作者看板门禁 */
  is_admin?: boolean
  entitlement?: EntitlementTier
  entitlement_info?: {
    tier: EntitlementTier
    unlocked_volume_ids: string[]
    schema_version?: string
  }
}

export type PaymentPlan = 'free' | 'volume_pass' | 'full_book' | 'pro' | 'pass' | 'book'

export async function login(username: string, password: string): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>('/api/v1/auth/login', { username, password })
  return data
}

export async function refreshAccessToken(refreshToken: string): Promise<RefreshTokenResponse> {
  const { data } = await apiClient.post<RefreshTokenResponse>('/api/v1/auth/refresh', {
    refresh_token: refreshToken,
  })
  return data
}

export async function logout(refreshToken: string): Promise<void> {
  await apiClient.post('/api/v1/auth/logout', { refresh_token: refreshToken })
}

/** T094：拉取当前用户权益 */
export async function fetchAuthMe(): Promise<AuthMeResponse> {
  const { data } = await apiClient.get<AuthMeResponse>('/api/v1/auth/me')
  return data
}

/** T093/T094：沙箱支付回调（写 entitlement） */
export async function postSandboxPaymentWebhook(body: {
  user_id: number
  plan: PaymentPlan
  event_type?: string
  provider?: 'stripe' | 'wechat'
}): Promise<{
  accepted: boolean
  entitlement_applied?: EntitlementTier | null
  user_id?: number | null
}> {
  const { data } = await apiClient.post('/api/v1/payment/webhook', {
    provider: body.provider ?? 'stripe',
    event_type: body.event_type ?? 'checkout.completed',
    user_id: body.user_id,
    plan: body.plan,
  })
  return data
}

export type H5PreviewTokenResponse = {
  access_token: string
  token_type: string
  expires_in: number
  case_id: string
  scope: string
}

/** T095 / SHARE-02：签发落地页试读短 token（需登录，绑定 case） */
export async function mintH5PreviewToken(caseId: string): Promise<H5PreviewTokenResponse> {
  const { data } = await apiClient.post<H5PreviewTokenResponse>('/api/v1/auth/h5-preview-token', {
    case_id: caseId.trim(),
  })
  return data
}
