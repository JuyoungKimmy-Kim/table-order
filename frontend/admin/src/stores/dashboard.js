import { defineStore } from 'pinia'
import { api } from '../api/client'
import { openOrderStream } from '../api/sse'

const HIGHLIGHT_MS = 10_000 // Q6=A: 신규 주문 10초 강조

// BR-A6.4 이벤트→화면 매핑을 담당하는 스토어.
export const useDashboardStore = defineStore('dashboard', {
  state: () => ({
    tables: {},                 // table_id → card VM
    filter: { status: null, tableNumber: null },
    connection: 'closed',       // connecting | open | reconnecting | closed
    lastEventId: null,
    _stream: null,
  }),
  getters: {
    // 클라이언트 측 필터(Q7=A)
    visibleTables: (s) => {
      let list = Object.values(s.tables).sort((a, b) => a.table_number - b.table_number)
      if (s.filter.tableNumber != null) {
        list = list.filter((t) => t.table_number === s.filter.tableNumber)
      }
      if (s.filter.status) {
        list = list.filter((t) =>
          (t.recent_orders || []).some((o) => o.status === s.filter.status))
      }
      return list
    },
  },
  actions: {
    async init() {
      await this.loadSnapshot()
      this.connect()
    },
    async loadSnapshot() {
      const data = await api.get('/admin/dashboard')
      this.applySnapshot(data)
    },
    applySnapshot(data) {
      const next = {}
      for (const card of data.tables) {
        next[card.table_id] = { ...card, highlightUntil: null }
      }
      this.tables = next
    },
    connect() {
      this.connection = 'connecting'
      this._stream?.close()
      this._stream = openOrderStream({
        getLastEventId: () => this.lastEventId,
        onOpen: () => { this.connection = 'open' },
        onError: () => {
          this.connection = 'reconnecting'
          // 간단한 재연결: 스냅샷 재동기화 후 재연결(Q5=A)
          setTimeout(() => this.resync(), 2000)
        },
        onEvent: (frame) => this.handleEvent(frame),
      })
    },
    async resync() {
      try {
        await this.loadSnapshot()
      } catch (_) { /* 인증 만료 등은 client 인터셉터가 처리 */ }
      this.connect()
    },
    handleEvent(frame) {
      if (frame.id != null) this.lastEventId = frame.id
      const { event, data } = frame
      if (!data) return
      const card = this.tables[data.table_id]
      switch (event) {
        case 'order.created': {
          if (!card) return
          card.recent_orders = [data, ...(card.recent_orders || [])].slice(0, 3)
          card.highlightUntil = Date.now() + HIGHLIGHT_MS
          break
        }
        case 'order.status_changed': {
          if (!card) return
          const o = (card.recent_orders || []).find((x) => x.order_id === data.order_id)
          if (o) o.status = data.status
          break
        }
        case 'order.deleted': {
          if (!card) return
          card.recent_orders = (card.recent_orders || []).filter((x) => x.order_id !== data.order_id)
          if (data.table_total != null) card.table_total = data.table_total
          break
        }
        case 'session.closed': {
          if (!card) return
          card.session_active = false
          card.table_total = 0
          card.recent_orders = []
          break
        }
      }
    },
    setFilter(patch) { this.filter = { ...this.filter, ...patch } },
    disconnect() {
      this._stream?.close()
      this._stream = null
      this.connection = 'closed'
    },
  },
})
