# Integration Contract — 유닛 통합 계약 (테이블오더 서비스)

<!--
  이 파일은 개발자 참조 편의를 위한 사본입니다.
  변경 관리(SSOT) 원본: aidlc-docs/inception/application-design/integration-contract.md
  계약 변경 시 원본을 먼저 수정하고 이 사본에 반영합니다 (§6 변경 관리).
-->

> **소유**: Unit 1 (Foundation & Shared Core, 김주영)
> **대상**: 전 개발자(박찬준·임동규·이명우·윤태경)
> **목적**: 5개 유닛이 병렬 개발하기 위한 **단일 진실 원천(Single Source of Truth)**. 모든 API·데이터 모델·이벤트는 이 문서를 기준으로 구현한다. 계약 변경은 반드시 이 문서를 먼저 수정하고 전원 공유 후 반영한다.

**스택**: Python 백엔드 · Vue 프론트엔드 · SQLite · SSE · 모노레포 · 로컬 실행
**규모**: 소규모(단일 매장). **단일 매장 가정** — `store_id`는 스키마에 존재하나 MVP에서는 단일 값 고정.

---

## 0. 공통 규칙

### 0.1 Base URL & 버전
- 모든 API 경로 접두사: `/api`
- 콘텐츠 타입: `application/json; charset=utf-8` (SSE 제외)
- 시각 표기: **ISO 8601 UTC** 문자열 (예: `2026-08-31T09:30:00Z`)
- 금액: **정수(원 단위)**. 부동소수점 미사용.

### 0.2 표준 에러 응답 포맷
모든 4xx/5xx 응답은 아래 구조를 따른다.

```json
{
  "error": {
    "code": "MENU_NOT_FOUND",
    "message": "해당 메뉴를 찾을 수 없습니다.",
    "details": {}
  }
}
```

| 필드 | 타입 | 설명 |
|---|---|---|
| `error.code` | string | 대문자 스네이크 케이스 에러 코드 (아래 표) |
| `error.message` | string | 사용자 표시용 한국어 메시지 |
| `error.details` | object | 선택. 필드별 검증 오류 등 부가 정보 |

**공통 에러 코드**

| HTTP | code | 의미 |
|---|---|---|
| 400 | `VALIDATION_ERROR` | 요청 검증 실패 (`details`에 필드별 사유) |
| 401 | `UNAUTHORIZED` | 인증 토큰 없음/만료/무효 |
| 403 | `FORBIDDEN` | 권한 없음 |
| 404 | `NOT_FOUND` | 리소스 없음(구체 코드로 대체 가능: `MENU_NOT_FOUND` 등) |
| 409 | `CONFLICT` | 상태 충돌(예: 이미 완료된 세션) |
| 429 | `TOO_MANY_ATTEMPTS` | 로그인 시도 제한 초과 |
| 500 | `INTERNAL_ERROR` | 서버 내부 오류 |

### 0.3 인증 규약 (관리자)
- 관리자 API는 `Authorization: Bearer <JWT>` 헤더 필요.
- 고객 API는 **테이블 세션 토큰**(자동 로그인 시 발급, 아래 3.1)을 `Authorization: Bearer <table_token>` 로 전달.
- JWT 유효기간: **16시간**. 만료 시 `401 UNAUTHORIZED`.

### 0.4 페이지네이션 규약
목록 조회는 쿼리 파라미터 `?page=1&size=20` (기본 page=1, size=20). 응답 공통 래퍼:

```json
{ "items": [], "page": 1, "size": 20, "total": 137 }
```

### 0.5 핵심 도메인 규칙 (Unit 1 소유 · 전 유닛 준수)
아래 규칙은 **순수 함수로 구현**하고 PBT 대상으로 삼는다(§5 참조).

- **총액 계산**: `order_total = Σ(order_item.unit_price × order_item.quantity)`. 테이블 현재 총액 = 현재 세션에 속한 미삭제 주문들의 `order_total` 합.
- **현재 세션 판별**: 테이블의 `status = 'active'` 인 `TableSession` 이 현재 세션. `closed` 세션의 주문은 고객 조회에서 제외되고 OrderHistory로 이동.
- **세션 시작**: 테이블에 active 세션이 없는 상태에서 첫 주문 생성 시 새 `TableSession(active)` 생성.
- **세션 종료(이용 완료)**: active 세션을 `closed`로 전환, `closed_at` 기록, 해당 세션 주문을 OrderHistory로 이동, 테이블 현재 주문/총액 리셋.

---

## 1. 공유 데이터 모델 (SQLite 스키마) — Unit 1 소유

> 모든 테이블은 `id INTEGER PRIMARY KEY AUTOINCREMENT`, 생성/수정 시각(`created_at`, `updated_at`)을 가진다. 시각은 UTC ISO8601 문자열 저장.

### 1.1 `stores` (매장)
| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| id | INTEGER | PK | |
| store_code | TEXT | UNIQUE, NOT NULL | 매장 식별자 |
| name | TEXT | NOT NULL | 매장명 |

### 1.2 `admin_users` (관리자 계정)
| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| id | INTEGER | PK | |
| store_id | INTEGER | FK stores.id | |
| username | TEXT | NOT NULL | 로그인 사용자명 |
| password_hash | TEXT | NOT NULL | **bcrypt** 해시 |
| UNIQUE(store_id, username) | | | |

### 1.3 `tables` (테이블)
| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| id | INTEGER | PK | |
| store_id | INTEGER | FK stores.id | |
| table_number | INTEGER | NOT NULL | 테이블 번호 |
| password_hash | TEXT | NOT NULL | 테이블 비밀번호(bcrypt) |
| UNIQUE(store_id, table_number) | | | |

### 1.4 `table_sessions` (테이블 세션)
| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| id | INTEGER | PK | |
| table_id | INTEGER | FK tables.id | |
| status | TEXT | NOT NULL | `active` \| `closed` |
| opened_at | TEXT | NOT NULL | 첫 주문 시각 |
| closed_at | TEXT | NULL | 이용 완료 시각 |

> 규칙: 한 테이블에 `active` 세션은 **최대 1개**.

### 1.5 `categories` (메뉴 카테고리)
| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| id | INTEGER | PK | |
| store_id | INTEGER | FK stores.id | |
| name | TEXT | NOT NULL | 카테고리명 |
| display_order | INTEGER | NOT NULL, DEFAULT 0 | 노출 순서(오름차순) |

### 1.6 `menus` (메뉴)
| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| id | INTEGER | PK | |
| store_id | INTEGER | FK stores.id | |
| category_id | INTEGER | FK categories.id | |
| name | TEXT | NOT NULL | 메뉴명 |
| price | INTEGER | NOT NULL, CHECK(price >= 0) | 가격(원) |
| description | TEXT | NULL | 설명 |
| image_url | TEXT | NULL | 이미지 URL |
| display_order | INTEGER | NOT NULL, DEFAULT 0 | 노출 순서 |
| is_available | INTEGER | NOT NULL, DEFAULT 1 | 1=노출, 0=숨김 |

### 1.7 `orders` (주문)
| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| id | INTEGER | PK | |
| session_id | INTEGER | FK table_sessions.id | |
| table_id | INTEGER | FK tables.id | 조회 편의용 |
| order_number | TEXT | UNIQUE, NOT NULL | 표시용 주문번호 |
| status | TEXT | NOT NULL | `pending` \| `preparing` \| `completed` (기본 `pending`) |
| total_amount | INTEGER | NOT NULL | 주문 총액(스냅샷) |
| is_deleted | INTEGER | NOT NULL, DEFAULT 0 | 직권 삭제 플래그 |
| ordered_at | TEXT | NOT NULL | 주문 시각 |

### 1.8 `order_items` (주문 항목)
| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| id | INTEGER | PK | |
| order_id | INTEGER | FK orders.id | |
| menu_id | INTEGER | FK menus.id | |
| menu_name | TEXT | NOT NULL | 주문 시점 메뉴명(스냅샷) |
| unit_price | INTEGER | NOT NULL | 주문 시점 단가(스냅샷) |
| quantity | INTEGER | NOT NULL, CHECK(quantity > 0) | 수량 |

> 스냅샷 원칙: 주문 항목은 메뉴명·단가를 **주문 시점 값으로 복사** 저장하여, 이후 메뉴 변경/삭제(Unit 5)에 영향받지 않는다.

### 1.9 `order_history` (과거 주문 이력)
세션 종료 시 이동된 주문의 이력. 스키마는 `orders`와 동일 컬럼 + `session_closed_at TEXT`, `store_id INTEGER`.
> 구현 선택지: 별도 테이블로 물리 이동, 또는 `orders`에 `archived` 상태 부여. **본 계약은 별도 테이블(`order_history`)을 기준**으로 하며 조회는 §3.4.5로 제공.

### 1.10 상태 열거값 (공유 enum)
- `OrderStatus`: `pending`(대기중) · `preparing`(준비중) · `completed`(완료)
- `SessionStatus`: `active` · `closed`

---

## 2. SSE 이벤트 규약 — Unit 1 소유

### 2.1 구독 엔드포인트 (Unit 3 소비)
```
GET /api/admin/orders/stream
Authorization: Bearer <JWT>
Accept: text/event-stream
```
- 서버는 `text/event-stream`으로 이벤트를 push. 관리자 인증 필수.
- 재연결: 클라이언트는 `Last-Event-ID` 헤더로 마지막 수신 ID 전달 가능(서버는 best-effort로 이후 이벤트 재전송).

### 2.2 이벤트 프레임 형식
```
id: <이벤트 시퀀스 번호>
event: <이벤트 타입>
data: <JSON 페이로드>

```

### 2.3 이벤트 타입 (발행 유닛 → 구독 유닛)
| event | 발행 | 페이로드 | 의미 |
|---|---|---|---|
| `order.created` | Unit 2 | OrderSummary(§4.1) | 신규 주문 생성 → 카드 강조 |
| `order.status_changed` | Unit 3 | `{ order_id, table_id, status }` | 주문 상태 변경 |
| `order.deleted` | Unit 4 | `{ order_id, table_id, table_total }` | 직권 삭제 → 총액 갱신 |
| `session.closed` | Unit 4 | `{ table_id, session_id }` | 이용 완료 → 테이블 리셋 |

> 발행은 각 유닛이 Unit 1이 제공하는 **공통 브로커 모듈**(`core.sse.publish(event, payload)`)을 호출하여 수행한다. 구독측(Unit 3)은 이벤트 타입만으로 화면을 갱신할 수 있어야 한다.

---

## 3. REST API 계약 (유닛별)

### 3.1 Unit 2 — 고객 (Customer) API

#### 3.1.1 테이블 자동 로그인 — `POST /api/customer/login`
Req:
```json
{ "store_code": "STORE001", "table_number": 5, "password": "1234" }
```
Resp 200:
```json
{ "table_token": "<JWT>", "table_id": 12, "table_number": 5, "store_name": "홍길동식당" }
```
에러: 401 `UNAUTHORIZED`(자격 불일치).

#### 3.1.2 메뉴 조회 — `GET /api/customer/menus`
> 데이터는 Unit 5가 관리, Unit 2가 소비.
Resp 200:
```json
{
  "categories": [
    { "id": 1, "name": "메인", "display_order": 0,
      "menus": [ { "id": 10, "name": "김치찌개", "price": 8000, "description": "...", "image_url": "...", "display_order": 0, "is_available": true } ] }
  ]
}
```
> `is_available: false` 메뉴는 응답에서 제외(또는 표시하되 주문 불가) — **제외를 기본**으로 한다.

#### 3.1.3 주문 생성 — `POST /api/customer/orders`
Req (인증: table_token):
```json
{ "items": [ { "menu_id": 10, "quantity": 2 }, { "menu_id": 11, "quantity": 1 } ] }
```
Resp 201:
```json
{ "order_id": 100, "order_number": "A-20260831-0007", "total_amount": 25000, "status": "pending", "ordered_at": "2026-08-31T09:30:00Z" }
```
동작: active 세션 없으면 세션 시작(§0.5). 서버가 단가·총액을 메뉴 마스터에서 재계산(클라이언트 값 신뢰 안 함). 성공 시 `order.created` SSE 발행.
에러: 400 `VALIDATION_ERROR`(빈 items/수량≤0), 404 `MENU_NOT_FOUND`, 409 `MENU_UNAVAILABLE`.

#### 3.1.4 현재 세션 주문 내역 — `GET /api/customer/orders`
Resp 200: `OrderDetail`(§4.2) 배열. **현재 active 세션의 미삭제 주문만**, `ordered_at` 오름차순. 페이지네이션 적용.

---

### 3.2 Unit 3 — 관리자 인증 & 모니터링 API

#### 3.2.1 관리자 로그인 — `POST /api/admin/login`
Req:
```json
{ "store_code": "STORE001", "username": "admin", "password": "secret" }
```
Resp 200: `{ "token": "<JWT>", "expires_in": 57600, "store_name": "홍길동식당" }`
에러: 401 `UNAUTHORIZED`, 429 `TOO_MANY_ATTEMPTS`(시도 제한 초과).

#### 3.2.2 세션 확인 — `GET /api/admin/me`
Resp 200: `{ "username": "admin", "store_id": 1 }` — 새로고침 시 세션 유지 확인용.

#### 3.2.3 실시간 스트림 — `GET /api/admin/orders/stream` (§2.1)

#### 3.2.4 대시보드 스냅샷 — `GET /api/admin/dashboard`
> SSE 연결 직전/직후 현재 상태 로드용.
Resp 200:
```json
{
  "tables": [
    { "table_id": 12, "table_number": 5, "session_active": true, "table_total": 25000,
      "recent_orders": [ /* OrderSummary 최신 n개 */ ] }
  ]
}
```

#### 3.2.5 주문 상태 변경 — `PATCH /api/admin/orders/{order_id}/status`
Req: `{ "status": "preparing" }`
Resp 200: `{ "order_id": 100, "status": "preparing" }`. 성공 시 `order.status_changed` SSE 발행.
에러: 400 `VALIDATION_ERROR`(허용되지 않는 상태), 404 `ORDER_NOT_FOUND`.

#### 3.2.6 주문 상세 — `GET /api/admin/orders/{order_id}`
Resp 200: `OrderDetail`(§4.2).

---

### 3.3 Unit 4 — 테이블 & 세션 관리 API

#### 3.3.1 테이블 초기 설정 — `POST /api/admin/tables`
Req: `{ "table_number": 5, "password": "1234" }`
Resp 201: `{ "table_id": 12, "table_number": 5 }`. 비밀번호는 bcrypt 저장.

#### 3.3.2 주문 삭제(직권) — `DELETE /api/admin/orders/{order_id}`
Resp 200: `{ "order_id": 100, "table_id": 12, "table_total": 17000 }`. `is_deleted=1` 처리 후 현재 총액 재계산. `order.deleted` SSE 발행.
에러: 404 `ORDER_NOT_FOUND`.

#### 3.3.3 세션 종료(이용 완료) — `POST /api/admin/tables/{table_id}/close-session`
Resp 200: `{ "table_id": 12, "closed_session_id": 45, "moved_orders": 3 }`.
동작: active 세션 `closed` 처리, 주문을 `order_history`로 이동, 현재 주문/총액 리셋. `session.closed` SSE 발행.
에러: 409 `NO_ACTIVE_SESSION`.

#### 3.3.4 현재 테이블 주문 목록 — `GET /api/admin/tables/{table_id}/orders`
Resp 200: 현재 세션 미삭제 주문의 `OrderDetail` 배열.

#### 3.3.5 과거 주문 내역 — `GET /api/admin/tables/{table_id}/history`
쿼리: `?date_from=2026-08-01&date_to=2026-08-31&page=1&size=20`
Resp 200: 페이지네이션 래퍼(§0.4) + `OrderDetail` 배열(각 항목에 `session_closed_at` 포함), `ordered_at` **역순**.

---

### 3.4 Unit 5 — 메뉴 관리 API

#### 3.4.1 메뉴 목록 — `GET /api/admin/menus`
Resp 200: 카테고리별 메뉴(§3.1.2와 동일 구조, `is_available` 무관 전체 포함).

#### 3.4.2 메뉴 등록 — `POST /api/admin/menus`
Req:
```json
{ "category_id": 1, "name": "김치찌개", "price": 8000, "description": "얼큰한", "image_url": "https://...", "display_order": 0 }
```
Resp 201: 생성된 메뉴 객체. 검증: `name` 필수, `price` 정수 ≥ 0(§0.5·§5). 위반 시 400 `VALIDATION_ERROR`.

#### 3.4.3 메뉴 수정 — `PUT /api/admin/menus/{menu_id}`
Req: 등록과 동일 필드(부분/전체). Resp 200: 수정된 객체.

#### 3.4.4 메뉴 삭제 — `DELETE /api/admin/menus/{menu_id}`
Resp 204. (기존 주문 항목은 스냅샷이므로 영향 없음, §1.8.)

#### 3.4.5 노출 순서 조정 — `PATCH /api/admin/menus/order`
Req: `{ "orders": [ { "menu_id": 10, "display_order": 0 }, { "menu_id": 11, "display_order": 1 } ] }`
Resp 200: `{ "updated": 2 }`.

#### 3.4.6 카테고리 관리
- `GET /api/admin/categories` · `POST /api/admin/categories` `{ name, display_order }` · `PUT /api/admin/categories/{id}` · `DELETE /api/admin/categories/{id}`

---

## 4. 공유 응답 DTO

### 4.1 OrderSummary (모니터링 카드·SSE용)
```json
{ "order_id": 100, "order_number": "A-20260831-0007", "table_id": 12, "table_number": 5,
  "status": "pending", "total_amount": 25000, "item_preview": "김치찌개 외 2건", "ordered_at": "2026-08-31T09:30:00Z" }
```

### 4.2 OrderDetail (상세·내역용)
```json
{ "order_id": 100, "order_number": "A-20260831-0007", "table_id": 12, "table_number": 5,
  "status": "pending", "total_amount": 25000, "ordered_at": "2026-08-31T09:30:00Z",
  "items": [ { "menu_name": "김치찌개", "unit_price": 8000, "quantity": 2, "line_total": 16000 } ] }
```

---

## 5. PBT(속성 기반 테스트) 대상 순수 함수 계약

활성 확장: PBT **Partial** — 강제 규칙 PBT-02·03·07·08·09. 아래 순수 함수는 Unit 1이 `core` 모듈로 제공하고 PBT를 작성한다. 모든 유닛은 총액/세션 판별을 **직접 계산하지 말고 이 함수를 호출**한다.

| 함수 | 시그니처(개념) | 검증 속성(예) |
|---|---|---|
| `calc_order_total(items)` | `[{unit_price, quantity}] → int` | 비음수, 항목 순서 무관, 빈 목록=0, 결합법칙 |
| `calc_table_total(orders)` | `[Order] → int` | 삭제 주문 제외, 개별 total 합과 일치 |
| `is_current_session_order(order, session)` | `→ bool` | closed 세션 주문은 항상 false |
| `order_number_format(...)` | `→ str` | 고유성·형식 불변 |

> 직렬화 라운드트립(DTO ↔ JSON)이 있는 경우 PBT-07/08 round-trip 속성을 작성한다.

---

## 6. 변경 관리
- 이 계약의 변경은 **Unit 1(김주영)**이 조율. 변경 시: (1) 본 문서 수정 → (2) 전원 공지 → (3) 영향 유닛 반영.
- Phase 0(계약 확정) 동안 활발히 수정하고, 이후에는 **호환성 우선**(필드 추가는 허용, 제거/의미 변경은 합의 필요).
