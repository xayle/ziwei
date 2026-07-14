import axios, { type InternalAxiosRequestConfig } from 'axios'

function emitBackendUnavailable(status?: number, path?: string): void {
  if (typeof window === 'undefined') return
  window.dispatchEvent(new CustomEvent('app:backend-unavailable', {
    detail: {
      status: typeof status === 'number' ? status : null,
      path: path ?? '',
    },
  }))
}

function getToken(): string | null {
  return localStorage.getItem('token')
}

function getRefreshToken(): string | null {
  return localStorage.getItem('refresh_token')
}

function resolveApiBaseUrl(): string {
  const configured = (import.meta.env.VITE_API_BASE_URL || '').trim()
  if (!configured) {
    return '/'
  }
  return configured.endsWith('/') ? configured : `${configured}/`
}

const apiClient = axios.create({
  baseURL: resolveApiBaseUrl(),
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

type RetryConfig = InternalAxiosRequestConfig & { _retry?: boolean }

/** AUTH-04：并发 401 共用一次 refresh */
let refreshInFlight: Promise<string | null> | null = null

async function refreshAccessTokenShared(): Promise<string | null> {
  if (refreshInFlight) return refreshInFlight
  const refreshToken = getRefreshToken()
  if (!refreshToken) return null

  refreshInFlight = (async () => {
    try {
      const { data } = await axios.post<{
        access_token: string
        refresh_token: string
      }>(`${resolveApiBaseUrl()}api/v1/auth/refresh`, { refresh_token: refreshToken })
      localStorage.setItem('token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('app:tokens-refreshed', {
          detail: {
            access_token: data.access_token,
            refresh_token: data.refresh_token,
          },
        }))
      }
      return data.access_token
    } catch {
      return null
    } finally {
      refreshInFlight = null
    }
  })()

  return refreshInFlight
}

function clearLocalAuthAndEmitUnauthorized(): void {
  localStorage.removeItem('token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('username')
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent('app:unauthorized'))
  }
}

apiClient.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

apiClient.interceptors.response.use(
  (res) => res,
  async (err) => {
    const status = err?.response?.status as number | undefined
    const path = (err?.config?.url as string | undefined) ?? ''
    const original = err?.config as RetryConfig | undefined

    if (!err?.response || (typeof status === 'number' && status >= 500)) {
      emitBackendUnavailable(status, path)
    }

    if (status === 401 && original && !original._retry) {
      const isAuthPath = path.includes('/auth/login') || path.includes('/auth/refresh')
      if (!isAuthPath && getRefreshToken()) {
        original._retry = true
        const accessToken = await refreshAccessTokenShared()
        if (accessToken) {
          original.headers = original.headers || {}
          original.headers.Authorization = `Bearer ${accessToken}`
          return apiClient(original)
        }
      }
      clearLocalAuthAndEmitUnauthorized()
    }
    return Promise.reject(err)
  },
)

export default apiClient
