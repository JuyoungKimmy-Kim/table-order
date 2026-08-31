import { useSessionStore } from '../stores/session'

// 고객 API fetch 래퍼 (frontend-components.md §5).
// - Bearer table_token 자동 주입.
// - 401 응답 시 세션 로그아웃 + /setup 리다이렉트 (BR-C1.4).
// - 에러는 {status, code, details, message} 를 실은 Error 로 throw.
const BASE = '/api/customer'

async function request(path, { method = 'GET', body, auth = true } = {}) {
  const session = useSessionStore()
  const headers = { 'Content-Type': 'application/json' }
  if (auth && session.tableToken) {
    headers['Authorization'] = `Bearer ${session.tableToken}`
  }

  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })

  let data = null
  if (res.status !== 204) {
    data = await res.json().catch(() => null)
  }

  if (res.status === 401 && auth) {
    session.logout()
    // router 는 client ↔ router 순환을 피하기 위해 지연 로딩.
    const { default: router } = await import('../router')
    router.push({ name: 'setup' })
  }

  if (!res.ok) {
    const err = new Error(data?.error?.message || `요청 실패 (${res.status})`)
    err.status = res.status
    err.code = data?.error?.code
    err.details = data?.error?.details || {}
    throw err
  }
  return data
}

export const api = {
  login: (payload) => request('/login', { method: 'POST', body: payload, auth: false }),
  menus: () => request('/menus'),
  createOrder: (items) => request('/orders', { method: 'POST', body: { items } }),
  orders: (page = 1, size = 20) => request(`/orders?page=${page}&size=${size}`),
}
