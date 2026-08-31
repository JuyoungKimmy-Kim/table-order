# Business Logic Model — Unit 4: Table & Session Management

> **소유**: Unit 4 (이명우). `backend/app/tables/`(API) + `frontend/admin/`(테이블 관리 화면) 로직 설계.
> **기준**: Integration Contract §3.3, §2, §4 · business-rules.md(U4-BR-*) · Unit 1 domain-entities.md / business-logic-model.md.
> **활성 확장**: PBT Partial(강제 PBT-02·03·07·08·09). 본 문서는 **PBT-01(속성 식별)** 을 충족한다.

## 1. 모듈 구성

### 1.1 백엔드 (`backend/app/tables/`)
```text
tables/
├── __init__.py
├── router.py       # FastAPI APIRouter — 5개 엔드포인트(§3.3), main.py에 include
├── service.py      # 트랜잭션/비즈니스 흐름(세션 종료·삭제·조회). core.domain 호출
├── repository.py   # sqlite3 접근 (tables/table_sessions/orders/order_history CRUD)
├── schemas.py      # 요청/응답 Pydantic 모델 (CreateTableReq 등)
└── deps.py         # 관리자 JWT 인증 의존성 (core.security.decode_token 래핑)
```
> 계약상 삭제 엔드포인트는 `DELETE /api/admin/orders/{order_id}` 로 "orders" 경로지만, **직권 삭제는 Unit 4 책임**(§3.3.2)이므로 이 라우터에 포함한다. Unit 3의 상태변경/상세와 경로 접두사만 공유하며 함수는 분리 → 충돌 없음.

### 1.2 프론트엔드 (`frontend/admin/` 내 테이블 관리 모듈)
> Unit 3/4/5가 동일 admin Vue 앱을 공유. Unit 4는 **별도 라우트/컴포넌트**로 분리(스캐폴딩 규칙).
```text
admin/src/features/tables/
├── TableSetupView.vue        # 초기 설정 폼(번호+비밀번호) — POST /admin/tables
├── TableOrdersView.vue       # 현재 세션 주문 목록 + 주문별 삭제 버튼
├── DeleteOrderDialog.vue     # 삭제 확인 팝업 → DELETE /admin/orders/{id}
├── CloseSessionDialog.vue    # 이용 완료 확인 팝업 → POST /admin/tables/{id}/close-session
├── OrderHistoryView.vue      # 과거 내역(날짜 필터, 역순, 페이지네이션) + 닫기
└── api.ts                    # Unit 4 엔드포인트 호출 래퍼
```

## 2. 엔드포인트 로직 (§3.3)

### 2.1 `POST /api/admin/tables` — 테이블 초기 설정 (U4-BR-1)
```text
검증: table_number(int), password(non-empty)         # 실패 → 400 VALIDATION_ERROR
BEGIN TX
  if exists table(store_id, table_number) -> 409 CONFLICT   # U4-BR-1.1
  password_hash = core.security.hash_password(password)     # U4-BR-1.2
  insert tables(store_id, table_number, password_hash, ts)
COMMIT
→ 201 {table_id, table_number}
```

### 2.2 `DELETE /api/admin/orders/{order_id}` — 직권 삭제 (U4-BR-2)
```text
order = repo.get_order(order_id)
if None -> 404 ORDER_NOT_FOUND
if not order.is_deleted:                              # U4-BR-2.4 멱등
  BEGIN TX; order.is_deleted = 1; COMMIT
orders = repo.active_session_orders(order.table_id)  # 현재 active 세션 주문
table_total = core.domain.calc_table_total(orders)   # U4-BR-2.2 (Unit 1 순수함수)
publish('order.deleted', {order_id, table_id, table_total})   # U4-BR-2.5
→ 200 {order_id, table_id, table_total}
```

### 2.3 `POST /api/admin/tables/{table_id}/close-session` — 이용 완료 (U4-BR-3)
```text
BEGIN TX
  session = repo.get_active_session(table_id)
  if None -> 409 NO_ACTIVE_SESSION                    # U4-BR-3.1
  now = utcnow_iso()
  orders = repo.session_orders(session.id)            # 삭제 포함 전부
  for o in orders:
     hist_id = repo.insert_history(o, store_id, session_closed_at=now)   # 스냅샷 이동
     repo.copy_items_to_history(o.id, hist_id)        # order_history_items
  session.status='closed'; session.closed_at=now      # U4-BR-3.2
COMMIT
publish('session.closed', {table_id, session_id})     # U4-BR-3.5
→ 200 {table_id, closed_session_id, moved_orders=len(orders)}
# 현재 총액/목록은 active 세션 부재로 자동 0 (U4-BR-3.3)
```

### 2.4 `GET /api/admin/tables/{table_id}/orders` — 현재 주문 목록 (U4-BR-4)
```text
session = repo.get_active_session(table_id)
if None -> 200 []                                     # 빈 목록
rows = repo.active_undeleted_orders_with_items(session.id)  # is_deleted=0, ordered_at ASC
→ 200 [OrderDetail...]                                # §4.2
```

### 2.5 `GET /api/admin/tables/{table_id}/history` — 과거 내역 (U4-BR-5)
```text
page,size = pagination.normalize(q.page, q.size)
validate date_from/date_to (YYYY-MM-DD) -> 400 if bad
total = repo.count_history(table_id, date_from, date_to)
rows  = repo.history_page(table_id, date_from, date_to, offset, size)  # ordered_at DESC
items = [OrderDetail + session_closed_at ...]
→ 200 pagination.paginate_response(items, page, size, total)   # §0.4
```

## 3. Repository 연산 (sqlite3, `core.db` 사용)
| 함수 | SQL 개요 |
|---|---|
| `create_table(store_id, number, pw_hash)` | INSERT tables |
| `table_number_exists(store_id, number)` | SELECT 1 FROM tables |
| `get_order(order_id)` | SELECT orders WHERE id |
| `soft_delete_order(order_id)` | UPDATE orders SET is_deleted=1 |
| `get_active_session(table_id)` | SELECT table_sessions WHERE table_id AND status='active' |
| `session_orders(session_id)` | SELECT orders WHERE session_id (전부) |
| `active_undeleted_orders_with_items(session_id)` | orders(is_deleted=0) + order_items JOIN, ordered_at ASC |
| `insert_history(order, store_id, closed_at)` | INSERT order_history |
| `copy_items_to_history(order_id, hist_id)` | INSERT order_history_items SELECT order_items |
| `count_history / history_page(...)` | SELECT/COUNT order_history WHERE table_id [+날짜], ordered_at DESC |

> 모든 쓰기 흐름은 `core.db.transaction(conn)` 컨텍스트로 감싼다. 세션 종료는 **단일 트랜잭션**(이동+상태변경 원자성, U4-BR-3.2).

## 4. Unit 1 재사용 (직접 구현 금지)
- `core.domain.calc_table_total(orders)` — 삭제 후 총액 재계산.
- `core.db.connect / transaction` — 연결·트랜잭션.
- `core.sse.publish(event, payload)` — `order.deleted` / `session.closed` 발행.
- `core.security.hash_password / decode_token` — 비밀번호 해싱, 관리자 인증.
- `core.errors.{ValidationError, NotFound, Conflict, OrderNotFound, NoActiveSession}` — 표준 에러.
- `core.models.{OrderDetail, OrderItemDetail}` — 응답 DTO.
- `core.pagination.{normalize, offset, paginate_response}` — 이력 페이지네이션.

## 5. DTO / 스키마 (`schemas.py`)
- `CreateTableReq{table_number:int, password:str}` → `CreateTableResp{table_id, table_number}`
- `DeleteOrderResp{order_id, table_id, table_total}`
- `CloseSessionResp{table_id, closed_session_id, moved_orders}`
- 조회 응답은 `core.models.OrderDetail.to_dict()` 재사용, 이력은 `session_closed_at` 필드 추가.

---

## 6. Testable Properties (PBT-01 준수)

Unit 4는 대부분 I/O·트랜잭션 중심이므로, **순수 속성이 있는 지점만** PBT 대상으로 삼고 나머지는 예제 기반(FastAPI TestClient + in-memory sqlite) 테스트로 커버한다.

### 6.1 총액 재계산 위임 (`calc_table_total` 사용)
| 속성 | 카테고리 | 설명 | 규칙 |
|---|---|---|---|
| 삭제분 제외 | Invariant **[강제 PBT-03]** | 삭제한 주문은 재계산 총액에 미포함 | U4-BR-2.2 |
| 삭제 멱등 | Idempotence(advisory) | 같은 주문 2회 삭제 결과 동일 | U4-BR-2.4 |
> 순수 함수 자체는 Unit 1이 PBT 소유. Unit 4는 **서비스가 이를 올바르게 호출**함을 예제로 검증(오라클: 수기 합).

### 6.2 세션 종료 불변식 (상태 기반 속성)
| 속성 | 카테고리 | 설명 | 규칙 |
|---|---|---|---|
| 이동 보존 | Conservation **[강제 PBT-03]** | 종료 전 세션 주문 수 == order_history 이동 건수(moved_orders) | U4-BR-3.2 |
| 종료 후 총액 0 | Invariant **[강제 PBT-03]** | 종료 후 현재 테이블 총액 == 0 (active 세션 부재) | U4-BR-3.3 |
| active 유일 | Invariant | 종료 후 해당 테이블 active 세션 0개 | Unit 1 BR-4.4 |

### 6.3 이력 조회 DTO round-trip
| 속성 | 카테고리 | 설명 | 규칙 |
|---|---|---|---|
| OrderDetail round-trip | Round-trip **[강제 PBT-02/07/08]** | `from_dict(to_dict(d)) == d` (Unit 1 DTO 재사용) | §4.2 |
| 역순 정렬 | Invariant | 이력은 항상 ordered_at DESC | U4-BR-5.1 |

### "No PBT" 명시 (PBT-01)
- `repository.py`(sqlite I/O), `deps.py`(JWT 검증 래핑): 순수 속성 없음 → 예제 기반 테스트로 커버.

## 7. 제너레이터 (PBT-07 [강제])
- Unit 1 `backend/tests/generators.py`의 `st_order`, `st_money`, `st_quantity` **재사용**(중복 정의 금지).
- Unit 4 전용이 필요하면 `st_session_orders`(같은 session_id를 가진 order 리스트) 추가.

## 8. 테스트 전략
- **API 통합 테스트**: FastAPI `TestClient` + in-memory/temp sqlite(마이그레이션 적용) — 5개 엔드포인트의 정상/에러(404/409/400) 경로.
- **세션 종료 시나리오**: 주문 생성(시드) → close-session → history에 이동·현재 목록 0·SSE 발행 확인.
- **PBT**: §6의 강제 속성. Hypothesis(PBT-09), shrinking·seed 재현성(PBT-08).
