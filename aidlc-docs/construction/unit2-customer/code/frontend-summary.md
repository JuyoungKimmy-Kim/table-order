# Frontend Code Summary — Unit 2: Customer Ordering

> **담당**: 박찬준 · 위치: `frontend/customer/` · 스택: Vue 3 + Vite + Pinia + Vue Router

## 빌드 검증
- `npm install` (38 packages) → `npm run build` **성공** (47 modules, ~4s, dist 산출).
- 경고 1건(무해): `client.js` 가 순환참조 회피를 위해 router 를 지연 import → 청크 분리 안 됨 안내(정상 동작).

## 라우트 (§1)
| 경로 | 뷰 | 가드 |
|---|---|---|
| `/setup` | SetupView | public |
| `/` | MenuView (기본) | requireTableToken |
| `/cart` | CartView | requireTableToken |
| `/orders` | OrdersView | requireTableToken |
- 가드: 미인증 → `/setup`, 인증 상태로 `/setup` 진입 → `/` (router/index.js).

## 스토어 (Pinia)
| 스토어 | 상태/영속 | 핵심 |
|---|---|---|
| `session` | tableToken/tableId/tableNumber/storeName · localStorage(`session`) | `login()`/`logout()`/`isAuthenticated` (Q1) |
| `cart` | items[] · localStorage(`cart:{tableId}`) | `totalAmount`(실시간)·`add/updateQty/remove/clear/markUnavailable` (Q4/Q5) |
| `menu` | categories/activeCategoryId/loading | `fetchMenus()`·`activeMenus` |

## API 클라이언트 (api/client.js)
- fetch 래퍼 + Bearer 자동 주입. 401 → `session.logout()` + `/setup` 리다이렉트(BR-C1.4).
- 에러를 `{status, code, details, message}` 로 정규화해 throw → 화면이 품절 처리 등에 사용.
- 엔드포인트: `login/menus/createOrder/orders` (계약 §3.1).

## 컴포넌트 (§3)
- MenuView: CategoryTabs · MenuGrid · MenuCard · MenuDetailModal(수량 스텝퍼→담기, Q3) · CartFab
- CartView: CartItemRow(±/삭제·품절 배지) · CartSummary(실시간 총액) · ConfirmOrderButton · OrderConfirmModal(주문번호)
- OrdersView: OrderCard(주문번호·시각·항목·총액·상태 배지). 진입 시 재조회(Q6).

## 요구사항 매핑
| 요구사항 | 구현 |
|---|---|
| 3.1.1 로그인/세션 | SetupView + session store + 가드 |
| 3.1.2 메뉴 조회/탐색 | MenuView/CategoryTabs/MenuGrid/MenuCard/MenuDetailModal |
| 3.1.3 장바구니 | cart store + CartView/CartItemRow/CartSummary/CartFab |
| 3.1.4 주문 생성 | CartView.submitOrder → POST orders, 성공 모달·실패 품절표시(Q5) |
| 3.1.5 주문 내역 | OrdersView/OrderCard (진입 재조회) |

## 자동화 친화
주요 요소에 `data-testid` 부여(setup-view, menu-card-{id}, btn-add-cart, cart-fab, cart-row-{id},
btn-submit-order, confirm-order-number, order-card-{id}, soldout-badge 등).

## 설계 원칙 반영
- 금액 표시는 참고용, 최종 금액은 서버 재계산(신뢰 경계).
- 품절/미존재는 서버 `error.details` 기반으로 표시(계약 §0.2 활용, 계약 변경 없음).
