import { defineStore } from 'pinia'
import { api } from '../api/client'

// 세션 스토어 (frontend-components.md §2.1).
// table_token 등을 localStorage 에 저장(Q1)하고 부팅 시 복원.
const LS_KEY = 'session'

function load() {
  try {
    return JSON.parse(localStorage.getItem(LS_KEY)) || {}
  } catch {
    return {}
  }
}

export const useSessionStore = defineStore('session', {
  state: () => {
    const s = load()
    return {
      tableToken: s.tableToken || '',
      tableId: s.tableId || null,
      tableNumber: s.tableNumber || null,
      storeName: s.storeName || '',
    }
  },
  getters: {
    isAuthenticated: (s) => !!s.tableToken,
  },
  actions: {
    persist() {
      localStorage.setItem(LS_KEY, JSON.stringify({
        tableToken: this.tableToken,
        tableId: this.tableId,
        tableNumber: this.tableNumber,
        storeName: this.storeName,
      }))
    },
    async login(storeCode, tableNumber, password) {
      const data = await api.login({
        store_code: storeCode,
        table_number: Number(tableNumber),
        password,
      })
      this.tableToken = data.table_token
      this.tableId = data.table_id
      this.tableNumber = data.table_number
      this.storeName = data.store_name
      this.persist()
    },
    logout() {
      this.tableToken = ''
      this.tableId = null
      this.tableNumber = null
      this.storeName = ''
      localStorage.removeItem(LS_KEY)
    },
  },
})
