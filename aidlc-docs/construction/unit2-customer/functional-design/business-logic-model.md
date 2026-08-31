# Business Logic Model — Unit 2: Customer Ordering (고객 주문)

> **담당**: 박찬준 · **기준**: business-rules.md(BR-C*) / 계약 §3.1 / 인터뷰 Q1~Q8
> 기술-불문 처리 흐름. 구현은 `backend/app/customer/`(라우터/서비스/리포지토리) + Unit 1 `core`.

## 0. 컴포넌트 구조 (백엔드)
```text
app/customer/
  router.py       # FastAPI APIRouter — 4개 엔드포인트, 요청/응답 검증, 인증 의존성
  service.py      # 비즈니스 로직(BR-C*), 트랜잭션 오케스트레이션
  repository.py   # SQLite 접근(core.db 사용) — 조회/INSERT/채번
  auth.py         # table_token 발급/검증 의존성 (core.security 래핑)
  schemas.py      # 요청/응답 pydantic 모델 (DTO는 core.models 재사용)
```

## 1. 흐름 A — 테이블 자동 로그인 `POST /api/customer/login` (BR-C1)
```text
1. LoginRequest 파싱
2. store = repo.get_store_by_code(store_code)         # 없으면 → 401 UNAUTHORIZED
3. table = repo.get_table(store.id, table_number)     # 없으면 → 401 UNAUTHORIZED
4. verify_password(password, table.password_hash)     # 실패 → 401 UNAUTHORIZED
5. token = security.create_token({sub, store_id, table_number})  # 16h
6. return LoginResponse(table_token, table_id, table_number, store_name)
```
- 실패 사유를 구분 노출하지 않음(BR-C1.1). 클라이언트는 token만 저장(BR-C1.3).

## 2. 흐름 B — 메뉴 조회 `GET /api/customer/menus` (BR-C2)
```text
1. auth: table_token 검증 → store_id 추출
2. categories = repo.list_categories(store_id)        # display_order ASC, id ASC
3. menus = repo.list_available_menus(store_id)        # is_available=1 만, 정렬
4. group menus by category_id → MenuListResponse
5. return (빈 카테고리는 menus:[] 로 포함)
```

## 3. 흐름 C — 주문 생성 `POST /api/customer/orders` (BR-C4) ★핵심
```text
1. auth: table_token → table_id, store_id
2. validate_order_items(items)                         # 위반 → 400 VALIDATION_ERROR
3. with db.transaction(conn):
   3a. 메뉴 재조회/재검증 (BR-C4.2, BR-C4.3)
       - rows = repo.get_menus_for_order(store_id, [menu_id...])
       - not_found = 요청에 있으나 조회 안 된 menu_id → 있으면 404 MENU_NOT_FOUND
         (error.details.not_found_menu_ids)
       - unavailable = is_available=0 인 menu_id → 있으면 409 MENU_UNAVAILABLE
         (error.details.unavailable_menu_ids)
       - 항목 스냅샷 구성: [{menu_id, menu_name, unit_price, quantity}]
   3b. total = domain.calc_order_total(스냅샷 항목)      # 서버 계산이 진실
   3c. 세션 확보 (BR-C4.4)
       - session = repo.get_active_session(table_id)
       - if None: session = repo.create_active_session(table_id, opened_at=now)
   3d. 채번 (BR-C4.5)
       - seq = repo.next_sequence(store_id, today_utc)  # UPSERT last_seq+1 (원자)
       - order_number = domain.order_number_format("A", today_utc, seq)
   3e. INSERT orders(session_id, table_id, order_number, 'pending', total, ordered_at=now)
   3f. INSERT order_items[] (menu_name/unit_price 스냅샷)
   # 트랜잭션 커밋
4. publish "order.created" (OrderSummary) via core.sse   # 커밋 이후 (BR-C4.8)
5. return 201 CreateOrderResponse(order_id, order_number, total, 'pending', ordered_at)
예외 발생 시: 롤백 → 표준 에러 응답, 클라이언트 장바구니 유지
```

### 3.1 상태 전이 (세션·주문)
```text
Table 첫 주문 → TableSession: (없음) → active         [BR-C4.4]
Order 생성    → status = pending                       [기본값]
(이후 preparing/completed 는 Unit 3, 삭제는 Unit 4 — 본 유닛 관여 안 함)
```

### 3.2 채번 원자성 (order_sequences)
```text
INSERT INTO order_sequences(store_id, seq_date, last_seq) VALUES(?, ?, 1)
  ON CONFLICT(store_id, seq_date) DO UPDATE SET last_seq = last_seq + 1
  RETURNING last_seq;
```
- 단일 프로세스 + SQLite 트랜잭션(직렬화)로 동시 주문 시에도 seq 유일성 보장. seq>9999 → INTERNAL_ERROR.

## 4. 흐름 D — 현재 세션 주문 내역 `GET /api/customer/orders` (BR-C5)
```text
1. auth: table_token → table_id
2. session = repo.get_active_session(table_id)
   - None → 빈 페이지네이션 응답(items:[], total:0)
3. page,size = pagination.normalize(page,size)
4. total = repo.count_session_orders(session.id)         # is_deleted=0
5. rows = repo.list_session_orders(session.id, offset, size)  # ordered_at ASC
6. 각 주문 → OrderDetail(items 포함, line_total 파생)
7. return pagination.paginate_response([OrderDetail...], page, size, total)
```

## 5. 데이터 흐름 요약
```text
Menu(읽기, Unit5 데이터) ─┐
                          ├─> 주문 생성(재계산·스냅샷) ─> Order/OrderItem(쓰기) ─> SSE order.created ─> Unit3
TableSession(조회/생성) ──┘                                        │
order_sequences(채번) ────────────────────────────────────────────┘
Order(현재 세션, is_deleted=0, ASC) ─> OrderDetail ─> 고객 주문 내역
```

## 6. PBT / 테스트 대상 (PBT Partial: PBT-02·03·07·08·09 해당 시)
| 대상 | 속성/검증 | 규칙 |
|---|---|---|
| 주문 생성 응답 DTO ↔ JSON | round-trip 동등(PBT-07/08) | core.models 재사용, Unit2 스키마 round-trip |
| 총액 | `calc_order_total`(Unit1 PBT 커버) 위임 확인 | 직접계산 금지 |
| 채번 형식 | order_number == `A-YYYYMMDD-NNNN`, parse round-trip(PBT-02) | BR-C4.5 |
| 주문 생성 예제 | 세션 시작 / 품절 거부(details) / 총액 재계산 신뢰경계 | BR-C4.2~4.6 |
| 내역 필터 | closed 세션·삭제·타세션 제외, ASC 정렬 | BR-C5 |
> 순수함수는 Unit1 PBT가 커버. Unit2는 **엔드포인트 통합 예제 테스트 + DTO round-trip**에 집중(PBT-10 상호보완).
