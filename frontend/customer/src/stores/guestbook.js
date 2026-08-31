import { defineStore } from 'pinia'
import { api } from '../api/client'

// 방명록 스토어. 매장 단위로 공유되는 카드메모 목록을 관리한다.
export const useGuestbookStore = defineStore('guestbook', {
  state: () => ({
    entries: [], // [{ id, author_name, image_data, created_at }]
    loading: false,
    saving: false,
    error: '',
  }),
  actions: {
    async fetch() {
      this.loading = true
      this.error = ''
      try {
        const data = await api.guestbookList()
        this.entries = data.items || []
      } catch (e) {
        this.error = e.message || '방명록을 불러오지 못했습니다.'
      } finally {
        this.loading = false
      }
    },
    async create({ authorName, imageData }) {
      this.saving = true
      this.error = ''
      try {
        const entry = await api.createGuestbook({
          author_name: authorName || null,
          image_data: imageData,
        })
        // 최신순 목록 맨 앞에 삽입(서버 재조회 없이 즉시 반영).
        this.entries.unshift(entry)
        return entry
      } catch (e) {
        this.error = e.message || '방명록 저장에 실패했습니다.'
        throw e
      } finally {
        this.saving = false
      }
    },
  },
})
