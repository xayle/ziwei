import axios from 'axios'

function emitBackendUnavailable(status?: number, path?: string): void {
  if (typeof window === 'undefined') return
  window.dispatchEvent(new CustomEvent('app:backend-unavailable', {
    detail: {
      status: typeof status === 'number' ? status : null,
      path: path ?? '',
    },
  }))
}

// 从 localStorage 读 token（与旧版 window.getToken 行为一致）
function getToken(): string | null {
  return localStorage.getItem('token')
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

// 请求拦截：自动注入 Bearer Token
apiClient.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截：401 自动跳登录（派发自定义事件，避免 window.location.href 被 StaticFiles 404）
apiClient.interceptors.response.use(
  (res) => res,
  (err) => {
    const status = err?.response?.status as number | undefined
    const path = (err?.config?.url as string | undefined) ?? ''

    if (!err?.response || (typeof status === 'number' && status >= 500)) {
      emitBackendUnavailable(status, path)
    }

    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('username')
      window.dispatchEvent(new CustomEvent('app:unauthorized'))
    }
    return Promise.reject(err)
  },
)

export default apiClient
