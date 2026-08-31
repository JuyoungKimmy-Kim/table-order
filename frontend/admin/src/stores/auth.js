import { defineStore } from 'pinia'
import { api, setUnauthorizedHandler } from '../api/client'

const TOKEN_KEY = 'admin_token'

// JWT payload 디코드(검증 아님, 표시/만료 힌트용).
function decodePayload(token) {
  try {
    const [, payload] = token.split('.')
    return JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/')))
  } catch (_) { return null }
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: null,
    username: null,
    storeId: null,
  }),
  getters: {
    isAuthenticated: (s) => {
      if (!s.token) return false
      const p = decodePayload(s.token)
      if (p?.exp && Date.now() / 1000 >= p.exp) return false
      return true
    },
  },
  actions: {
    loadFromStorage() {
      // 401 수신 시 자동 로그아웃 콜백 등록
      setUnauthorizedHandler(() => this.logout())
      const token = localStorage.getItem(TOKEN_KEY)
      if (token) {
        this.token = token
        const p = decodePayload(token)
        this.username = p?.username ?? null
        this.storeId = p?.store_id ?? null
      }
    },
    async login(storeCode, username, password) {
      const res = await api.post('/admin/login', {
        store_code: storeCode, username, password,
      })
      this.token = res.token
      localStorage.setItem(TOKEN_KEY, res.token)
      const p = decodePayload(res.token)
      this.username = p?.username ?? username
      this.storeId = p?.store_id ?? null
      return res
    },
    async fetchMe() {
      const me = await api.get('/admin/me')
      this.username = me.username
      this.storeId = me.store_id
      return me
    },
    logout() {
      this.token = null
      this.username = null
      this.storeId = null
      localStorage.removeItem(TOKEN_KEY)
    },
  },
})
