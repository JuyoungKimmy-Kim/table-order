import { defineStore } from 'pinia'
import { useSessionStore } from './session'

// 장바구니 스토어 (frontend-components.md §2.2).
// 테이블별 분리(Q4): `cart:{tableId}` 키로 localStorage 영속.
function keyFor(tableId) {
  return `cart:${tableId ?? 'anon'}`
}

export const useCartStore = defineStore('cart', {
  // items: [{ menu_id, name, price, quantity, image_url, unavailable }]
  state: () => ({ items: [] }),
  getters: {
    // 실시간 총액(BR-C3.3) — 클라이언트 표시용. 최종 금액은 서버가 재계산.
    totalAmount: (s) => s.items.reduce((sum, it) => sum + it.price * it.quantity, 0),
    itemCount: (s) => s.items.reduce((sum, it) => sum + it.quantity, 0),
  },
  actions: {
    _key() {
      return keyFor(useSessionStore().tableId)
    },
    load() {
      try {
        this.items = JSON.parse(localStorage.getItem(this._key())) || []
      } catch {
        this.items = []
      }
    },
    persist() {
      localStorage.setItem(this._key(), JSON.stringify(this.items))
    },
    add(menu, qty = 1) {
      const existing = this.items.find((it) => it.menu_id === menu.id)
      if (existing) {
        existing.quantity += qty
        existing.unavailable = false
      } else {
        this.items.push({
          menu_id: menu.id,
          name: menu.name,
          price: menu.price,
          quantity: qty,
          image_url: menu.image_url || null,
          unavailable: false,
        })
      }
      this.persist()
    },
    updateQty(menuId, qty) {
      const it = this.items.find((i) => i.menu_id === menuId)
      if (!it) return
      if (qty <= 0) {
        this.remove(menuId)
      } else {
        it.quantity = qty
        this.persist()
      }
    },
    remove(menuId) {
      this.items = this.items.filter((i) => i.menu_id !== menuId)
      this.persist()
    },
    clear() {
      this.items = []
      this.persist()
    },
    // 주문 거부 시 서버가 알려준 품절/미존재 menu_id 표시(Q5).
    markUnavailable(menuIds) {
      const set = new Set(menuIds)
      this.items.forEach((it) => {
        if (set.has(it.menu_id)) it.unavailable = true
      })
      this.persist()
    },
  },
})
