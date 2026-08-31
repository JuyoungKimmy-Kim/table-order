// Unit 4: 테이블 & 세션 관리 API 호출 래퍼 (Integration Contract §3.3)
// 백엔드 backend/app/tables/router.py 와 1:1 대응.

import { request } from './http'
import type {
  CloseSessionResp,
  CreateTableReq,
  CreateTableResp,
  DeleteOrderResp,
  HistoryOrderDetail,
  HistoryQuery,
  OrderDetail,
  Paginated,
} from './types'

/** §3.3.1 테이블 초기 설정 */
export function createTable(body: CreateTableReq): Promise<CreateTableResp> {
  return request<CreateTableResp>('POST', '/admin/tables', { body })
}

/** §3.3.2 주문 직권 삭제 (soft delete → 총액 재계산) */
export function deleteOrder(orderId: number): Promise<DeleteOrderResp> {
  return request<DeleteOrderResp>('DELETE', `/admin/orders/${orderId}`)
}

/** §3.3.3 세션 종료(이용 완료) */
export function closeSession(tableId: number): Promise<CloseSessionResp> {
  return request<CloseSessionResp>('POST', `/admin/tables/${tableId}/close-session`)
}

/** §3.3.4 현재 세션 미삭제 주문 목록 */
export function getCurrentOrders(tableId: number): Promise<OrderDetail[]> {
  return request<OrderDetail[]>('GET', `/admin/tables/${tableId}/orders`)
}

/** §3.3.5 과거 주문 내역 (날짜 필터·역순·페이지네이션) */
export function getHistory(tableId: number, q: HistoryQuery = {}): Promise<Paginated<HistoryOrderDetail>> {
  return request<Paginated<HistoryOrderDetail>>('GET', `/admin/tables/${tableId}/history`, {
    query: { date_from: q.date_from, date_to: q.date_to, page: q.page, size: q.size },
  })
}
