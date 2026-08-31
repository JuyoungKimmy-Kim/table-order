# Frontend Components — Unit 2: Customer Ordering (고객용 Vue 앱)

> **담당**: 박찬준 · **위치**: `frontend/customer/`
> **스택(Q8)**: Vue 3 + Vite + Pinia + Vue Router, `<script setup>` SFC, fetch 기반 API 클라이언트
> **기준**: 요구사항 3.1.1~3.1.5 / business-rules.md(BR-C*) / 인터뷰 Q1~Q8

## 1. 라우트 구조 (Vue Router)
| 경로 | 화면 | 가드 |
|---|---|---|
| `/setup` | 초기 설정/로그인(재로그인) | 인증 불필요 |
| `/` (기본) | 메뉴 화면 (기본 화면, 항상 표시 — 3.1.2) | requireTableToken |
| `/cart` | 장바구니/주문 확인 | requireTableToken |
| `/orders` | 현재 세션 주문 내역 | requireTableToken |
- **네비게이션 가드**: 토큰 없음/만료(401) → `/setup` 리다이렉트 (BR-C1.4). 로그인 성공 → `/`.

## 2. 상태 스토어 (Pinia)
### 2.1 `useSessionStore`
- state: `tableToken`, `tableId`, `tableNumber`, `storeName`
- 영속: `tableToken`/`tableId` 등을 **localStorage 저장(Q1)**. 앱 부팅 시 복원.
- actions: `login(store_code, table_number, password)`, `logout()`, `isAuthenticated`
### 2.2 `useCartStore`
- state: `items: [{ menu_id, name, price, quantity, image_url }]`
- 영속: `cart:{tableId}` 키로 localStorage(Q4). tableId 변경 시 해당 키 로드.
- getters: `totalAmount`(Σ price×qty, 실시간 — BR-C3.3), `itemCount`
- actions: `add(menu, qty)`, `updateQty(menu_id, qty)`(0이면 remove), `remove(menu_id)`, `clear()`, `markUnavailable(menu_ids)`(품절 표시 — Q5)
### 2.3 `useMenuStore`
- state: `categories`(메뉴 포함), `activeCategoryId`, `loading`
- actions: `fetchMenus()`

## 3. 컴포넌트 계층
```text
App.vue
├─ SetupView            (/setup)   자동 로그인 폼
├─ MenuView (기본)       (/)
│  ├─ CategoryTabs        props: categories, activeCategoryId; emit: select
│  ├─ MenuGrid            props: menus(활성 카테고리)
│  │  └─ MenuCard         props: menu; emit: open → 상세 모달  (터치 44px+)
│  ├─ MenuDetailModal     props: menu; state: qty; emit: addToCart (Q3)
│  └─ CartFab             props: itemCount, totalAmount; → /cart
├─ CartView             (/cart)
│  ├─ CartItemRow         props: item; emit: inc/dec/remove; 품절 배지(unavailable)
│  ├─ CartSummary         props: totalAmount
│  └─ ConfirmOrderButton  emit: submitOrder
├─ OrderConfirmModal      props: orderNumber (주문 성공 표시)
└─ OrdersView           (/orders)  주문 내역(시간순, 상태 배지)
   └─ OrderCard           props: order(OrderDetail); 상태(대기중/준비중/완료)
```

## 4. 컴포넌트별 props / state / 상호작용
### 4.1 SetupView (3.1.1)
- form: `store_code`, `table_number`, `password`
- submit → `sessionStore.login()` → 성공 시 `/` 이동, 실패(401) 시 "로그인 정보를 확인하세요" 표시.
### 4.2 MenuView / MenuCard / MenuDetailModal (3.1.2, Q3)
- MenuCard: 이미지·메뉴명·가격 표시, 클릭 → 상세 모달.
- MenuDetailModal: 설명·큰 이미지·수량 스텝퍼 → "장바구니 담기" → `cartStore.add`.
- CategoryTabs: 카테고리 클릭 시 스크롤/필터(빠른 이동).
### 4.3 CartView (3.1.3, 3.1.4)
- CartItemRow: 수량 +/- (BR-C3.4), 삭제. `unavailable=true` 면 품절 배지 + 주문 버튼 비활성 유도(Q5).
- CartSummary: 실시간 총액(BR-C3.3).
- ConfirmOrderButton → `submitOrder()`:
  - `POST /api/customer/orders` 호출
  - **성공**: OrderConfirmModal(주문번호) → `cartStore.clear()` → `/` 리다이렉트 (BR-C4.6)
  - **실패 409/404**: `error.details.unavailable_menu_ids`/`not_found_menu_ids` → `cartStore.markUnavailable(...)`, 장바구니 유지, 품절 표시 (Q5)
  - **실패 기타**: 에러 토스트, 장바구니 유지
### 4.4 OrdersView / OrderCard (3.1.5)
- 진입 시 `GET /api/customer/orders` 재조회(Q6). 페이지네이션/무한스크롤.
- OrderCard: 주문번호·시각·항목·총액·상태 배지(대기중/준비중/완료).

## 5. API 연동 지점 (api client)
| 화면/액션 | 호출 | 인증 |
|---|---|---|
| SetupView.login | `POST /api/customer/login` | 없음 |
| MenuView.fetchMenus | `GET /api/customer/menus` | Bearer table_token |
| CartView.submitOrder | `POST /api/customer/orders` | Bearer table_token |
| OrdersView.fetch | `GET /api/customer/orders?page&size` | Bearer table_token |
- 공통 fetch 래퍼: 401 응답 시 `sessionStore.logout()` + `/setup` 리다이렉트(BR-C1.4).

## 6. 폼 검증 (클라이언트)
- 로그인: 3필드 필수, table_number 정수.
- 장바구니: quantity>=1(0이면 자동 제거), 빈 장바구니면 주문 버튼 비활성.
- 서버 검증이 최종(BR-C4.1~4.3) — 클라이언트 검증은 UX 보조.

## 7. UI/UX 요구 반영 (3.1.2)
- 카드형 메뉴 레이아웃, 터치 버튼 최소 44×44px, 명확한 시각적 계층.
- 기본 화면 = 메뉴(`/`). 장바구니는 FAB/배지로 상시 접근.
