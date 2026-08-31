// Unit 4: 계약 DTO 타입 (shared/integration-contract.md §4.2, §3.3)
// 백엔드 응답과 1:1 대응. 계약 변경 시 이 파일도 함께 갱신.

/** OrderItemDetail — §4.2 items[] 요소. line_total = unit_price × quantity */
export interface OrderItemDetail {
  menu_name: string
  unit_price: number
  quantity: number
  line_total: number
}

/** OrderDetail — §4.2 상세·내역용 */
export interface OrderDetail {
  order_id: number
  order_number: string
  table_id: number
  table_number: number
  status: 'pending' | 'preparing' | 'completed'
  total_amount: number
  ordered_at: string // ISO8601 UTC
  items: OrderItemDetail[]
}

/** 과거 내역 항목 — OrderDetail + 세션 종료 시각(§3.3.5) */
export interface HistoryOrderDetail extends OrderDetail {
  session_closed_at: string
}

/** 페이지네이션 래퍼 — §0.4 */
export interface Paginated<T> {
  items: T[]
  page: number
  size: number
  total: number
}

// --- 요청/응답 (§3.3) ---

export interface CreateTableReq {
  table_number: number
  password: string
}
export interface CreateTableResp {
  table_id: number
  table_number: number
}
export interface DeleteOrderResp {
  order_id: number
  table_id: number
  table_total: number
}
export interface CloseSessionResp {
  table_id: number
  closed_session_id: number
  moved_orders: number
}

export interface HistoryQuery {
  date_from?: string // YYYY-MM-DD
  date_to?: string // YYYY-MM-DD
  page?: number
  size?: number
}
