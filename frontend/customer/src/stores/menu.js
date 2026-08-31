import { defineStore } from 'pinia'
import { api } from '../api/client'

// 메뉴 스토어 (frontend-components.md §2.3).
export const useMenuStore = defineStore('menu', {
  state: () => ({
    categories: [], // [{ id, name, display_order, menus: [...] }]
    activeCategoryId: null,
    loading: false,
    error: '',
  }),
  getters: {
    activeMenus: (s) => {
      const cat = s.categories.find((c) => c.id === s.activeCategoryId)
      return cat ? cat.menus : (s.categories[0]?.menus || [])
    },
  },
  actions: {
    async fetchMenus() {
      this.loading = true
      this.error = ''
      try {
        const data = await api.menus()
        this.categories = data.categories || []
        if (this.categories.length && this.activeCategoryId == null) {
          this.activeCategoryId = this.categories[0].id
        }
      } catch (e) {
        this.error = e.message || '메뉴를 불러오지 못했습니다.'
      } finally {
        this.loading = false
      }
    },
    setActiveCategory(id) {
      this.activeCategoryId = id
    },
  },
})
