# Domain Entities — Unit 2: Customer Ordering (고객 주문)

> **담당**: 박찬준
> **기준**: `shared/integration-contract.md` §1·§3.1·§4 / Unit 1 `domain-entities.md`
> **원칙**: 도메인 엔티티·스키마는 **Unit 1 소유**. 본 문서는 Unit 2가 **읽기/쓰기하는 대상**과 요청/응답 DTO 매핑만 정의한다(중복 정의 금지).

## 1. Unit 2가 다루는 공유 엔티티 (Unit 1 소유)

| 엔티티 | Unit 2 접근 | 용도 |
|---|---|---|
| `Store` | 읽기 | 로그인 시 store_code → store_id 해석, store_name 응답 |
| `Table` | 읽기 | 자동 로그인 인증(table_number + password_hash 검증) |
| `TableSession` | 읽기/쓰기 | 주문 생성 시 active 세션 조회, 없으면 생성. 조회 시 현재 세션 필터 |
| `Category` | 읽기 | 메뉴 조회 응답 그룹핑(display_order ASC) |
| `Menu` | 읽기 | 메뉴 조회(is_available=1만), 주문 시 단가/이용가능 재검증 |
| `Order` | 쓰기/읽기 | 주문 생성(INSERT), 현재 세션 주문 내역 조회 |
| `OrderItem` | 쓰기/읽기 | 주문 항목 INSERT(스냅샷), 상세 조회 |
| `order_sequences` | 읽기/쓰기 | 주문번호 당일 시퀀스 채번(UPSERT, Q7=A) |

> **쓰기 금지**: `Store`, `Table`, `Category`, `Menu`, `AdminUser`, `OrderHistory` 는 Unit 2가 생성/수정하지 않는다(다른 유닛 소유).

## 2. 요청/응답 DTO (계약 §3.1·§4)

### 2.1 로그인 (§3.1.1)
- **요청** `LoginRequest`: `{ store_code: str, table_number: int, password: str }`
- **응답** `LoginResponse`: `{ table_token: str(JWT), table_id: int, table_number: int, store_name: str }`
- **JWT 클레임(발급)**: `{ sub: table_id, store_id, table_number, exp(16h) }` — `core.security.create_token` 사용.

### 2.2 메뉴 조회 (§3.1.2)
- **응답** `MenuListResponse`:
  ```
  { categories: [ { id, name, display_order,
                    menus: [ { id, name, price, description, image_url, display_order, is_available } ] } ] }
  ```
- **규칙**: `is_available=0` 메뉴 **제외**(BR-C2.2). 카테고리·메뉴 모두 `display_order ASC, id ASC`.

### 2.3 주문 생성 (§3.1.3)
- **요청** `CreateOrderRequest`: `{ items: [ { menu_id: int, quantity: int>=1 } ] }`
- **응답 201** `CreateOrderResponse`: `{ order_id, order_number, total_amount, status:"pending", ordered_at }`
- **에러 상세(Q5)**: 400 `VALIDATION_ERROR` / 404 `MENU_NOT_FOUND` / 409 `MENU_UNAVAILABLE`. 후자 두 경우 `error.details = { "unavailable_menu_ids": [..], "not_found_menu_ids": [..] }` 로 프론트 품절 표시 지원.

### 2.4 현재 세션 주문 내역 (§3.1.4)
- **응답**: `core.models.OrderDetail`(§4.2) 배열을 페이지네이션 래퍼(§0.4)로 감쌈. `ordered_at` 오름차순, 현재 active 세션의 `is_deleted=0` 주문만.

## 3. 재사용 (Unit 1 core, 재정의 금지)
- `core.models.OrderDetail`, `OrderItemDetail`(line_total 파생), `make_item_preview`
- `core.domain.calc_order_total`, `order_number_format`, `is_current_session_order`
- `core.errors.MenuNotFound / MenuUnavailable / Unauthorized / ValidationError`
- `core.validation.validate_order_items`
- `core.pagination.normalize / offset / paginate_response`
- `core.security.hash_password/verify_password/create_token/decode_token`
- `core.sse.publish`

## 4. 데이터 소유·경계 요약
```text
[읽기] Store, Table, Category, Menu        (다른 유닛 소유 데이터 소비)
[읽기/쓰기] TableSession(생성), Order, OrderItem, order_sequences   (Unit 2 주문 플로우)
[발행] SSE order.created  → core.sse.publish (Unit 3 구독)
```
