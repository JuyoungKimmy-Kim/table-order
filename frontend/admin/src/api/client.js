// fetch 래퍼 (Unit 3/4/5 공용).
// - Authorization: Bearer 자동 첨부(토큰은 authStore→localStorage).
// - 표준 에러(§0.2) 파싱, 401 수신 시 로그아웃 콜백 호출.

const BASE = '/api'

let onUnauthorized = null
export function setUnauthorizedHandler(fn) { onUnauthorized = fn }

function authHeader() {
  const token = localStorage.getItem('admin_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export class ApiError extends Error {
  constructor(status, code, message, details) {
    super(message || code || `HTTP ${status}`)
    this.status = status
    this.code = code
    this.details = details || {}
  }
}

async function request(method, path, body) {
  const res = await fetch(BASE + path, {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...authHeader(),
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })

  if (res.status === 401 && onUnauthorized) onUnauthorized()

  if (!res.ok) {
    let code, message, details
    try {
      const data = await res.json()
      code = data?.error?.code
      message = data?.error?.message
      details = data?.error?.details
    } catch (_) { /* non-JSON */ }
    throw new ApiError(res.status, code, message, details)
  }
  if (res.status === 204) return null
  return res.json()
}

export const api = {
  get: (p) => request('GET', p),
  post: (p, b) => request('POST', p, b),
  patch: (p, b) => request('PATCH', p, b),
  del: (p) => request('DELETE', p),
}
