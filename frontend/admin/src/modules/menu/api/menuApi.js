// Unit 5: 메뉴 관리 API 클라이언트 (Integration Contract §3.4)
// 담당: 윤태경
//
// - 표준 에러 포맷(§0.2) { error: { code, message, details } } 를 ApiError 로 파싱한다.
// - 관리자 인증 토큰(§0.3)은 authTokenGetter 로 주입받는다.
//   * 기본값: localStorage 'admin_token' 읽기.
//   * Unit 3(임동규) 인증 스토어가 준비되면 setAuthTokenGetter(() => store.token) 로 교체.
//   → 이 지점이 Unit 3 과의 통합 seam 이다.

let API_BASE = '/api/admin' // 동일 오리진/프록시 가정. setApiBase 로 재정의 가능.
let authTokenGetter = () => localStorage.getItem('admin_token') || ''

export function setApiBase(base) {
  API_BASE = base
}

export function setAuthTokenGetter(fn) {
  authTokenGetter = fn
}

export class ApiError extends Error {
  constructor(status, code, message, details) {
    super(message || code || 'API error')
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.details = details || {}
  }
}

async function request(method, path, body) {
  const headers = { Accept: 'application/json' }
  const token = authTokenGetter()
  if (token) headers['Authorization'] = `Bearer ${token}`
  if (body !== undefined) headers['Content-Type'] = 'application/json; charset=utf-8'

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })

  if (res.status === 204) return null

  let data = null
  const text = await res.text()
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      data = null
    }
  }

  if (!res.ok) {
    const err = data && data.error ? data.error : {}
    throw new ApiError(res.status, err.code, err.message, err.details)
  }
  return data
}

// --- 메뉴 (§3.4.1 ~ §3.4.5) ---
export const menuApi = {
  listMenus: () => request('GET', '/menus'),
  createMenu: (payload) => request('POST', '/menus', payload),
  updateMenu: (menuId, payload) => request('PUT', `/menus/${menuId}`, payload),
  deleteMenu: (menuId) => request('DELETE', `/menus/${menuId}`),
  reorderMenus: (orders) => request('PATCH', '/menus/order', { orders }),

  // --- 카테고리 (§3.4.6) ---
  listCategories: () => request('GET', '/categories'),
  createCategory: (payload) => request('POST', '/categories', payload),
  updateCategory: (categoryId, payload) => request('PUT', `/categories/${categoryId}`, payload),
  deleteCategory: (categoryId) => request('DELETE', `/categories/${categoryId}`),
}

export default menuApi
