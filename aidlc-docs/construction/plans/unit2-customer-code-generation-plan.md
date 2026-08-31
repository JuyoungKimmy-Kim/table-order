# Code Generation Plan — Unit 2: Customer Ordering (고객 주문)

> **담당**: 박찬준 · **단계**: CONSTRUCTION → Per-Unit Loop → Code Generation (Part 1 — Planning)
> **SSOT**: 이 플랜이 Unit 2 코드 생성의 단일 진실 원천. Part 2는 이 순서를 정확히 따른다.
> **설계 기준**: `construction/unit2-customer/functional-design/*` (business-rules BR-C*, business-logic-model, domain-entities, frontend-components) · `shared/integration-contract.md` §3.1
> **활성 확장**: PBT Partial — 강제 PBT-02·03·07·08·09 (해당 시 적용)

---

## Unit 생성 컨텍스트

**구현 스토리 (요구사항)**
- 3.1.1 테이블 자동 로그인/세션 · 3.1.2 메뉴 조회/탐색 · 3.1.3 장바구니 · 3.1.4 주문 생성 · 3.1.5 주문 내역 조회

**의존성**
- **Unit 1 (완료)**: `core.db/domain/models/errors/validation/pagination/security/sse`, SQLite 스키마, 계약. → 재사용, 재정의 금지.
- **Unit 5 (메뉴 데이터)**: 런타임에 `menus`/`categories` 읽기. 스키마는 Unit 1 소유이므로 병렬 진행 가능(시드 데이터로 개발).
- **Unit 3 (SSE 구독)**: Unit 2는 `order.created` **발행만**. 구독측 없어도 발행은 무해.

**소유 엔티티(쓰기)**: `TableSession`(생성), `Order`, `OrderItem`, `order_sequences`. (그 외 읽기 전용)

**인터페이스/계약**: 계약 §3.1.1~3.1.4 (login/menus/orders POST/orders GET), 에러 §0.2, SSE §2.3 `order.created`.

**코드 위치 (Greenfield 모노레포)**
- 백엔드: `backend/app/customer/` · 테스트: `backend/tests/`
- 프론트: `frontend/customer/`
- 문서(요약): `aidlc-docs/construction/unit2-customer/code/`

---

## 생성 단계 (번호·체크박스)

### A. 백엔드 — 비즈니스/API/리포지토리

- [x] **Step 1 — 패키지 스캐폴딩**: `backend/app/customer/__init__.py` 생성. `app/main.py`의 라우터 등록 주석을 해제하여 `customer_router` include (`prefix="/api"`).  [3.1.1~3.1.5]

- [x] **Step 2 — 스키마(schemas.py)**: 요청/응답 pydantic 모델 — `LoginRequest/LoginResponse`, `MenuListResponse`(category/menu 중첩), `CreateOrderRequest`(items), `CreateOrderResponse`. 응답 상세는 `core.models.OrderDetail` 재사용.  [3.1.1~3.1.4]

- [x] **Step 3 — 인증 의존성(auth.py)**: `get_table_context` — `Authorization: Bearer` 파싱 → `core.security.decode_token` → 만료/무효 시 `core.errors.Unauthorized`. 반환: `{table_id, store_id, table_number}`.  [3.1.1 / BR-C1.4·C1.5]

- [x] **Step 4 — 리포지토리(repository.py)**: `core.db` 기반 함수 —
  `get_store_by_code`, `get_table`, `list_categories`, `list_available_menus`, `get_menus_for_order(store_id, menu_ids)`, `get_active_session(table_id)`, `create_active_session(table_id, now)`, `next_sequence(store_id, seq_date)`(UPSERT+RETURNING, 원자적), `insert_order(...)`, `insert_order_items(...)`, `count_session_orders(session_id)`, `list_session_orders(session_id, offset, size)`.  [BR-C2·C4·C5]

- [x] **Step 5 — 비즈니스 서비스(service.py)**: BR-C 로직 오케스트레이션 —
  `login()`(BR-C1), `get_menus()`(BR-C2), `create_order()`(BR-C4: validate→트랜잭션[재검증/재계산/세션/채번/INSERT]→커밋 후 `sse.publish("order.created")`), `list_orders()`(BR-C5). 총액=`domain.calc_order_total`, 주문번호=`domain.order_number_format`. 품절/미존재 시 `error.details`에 menu_id 목록.  [3.1.1~3.1.5]

- [x] **Step 6 — API 라우터(router.py)**: `POST /customer/login`, `GET /customer/menus`, `POST /customer/orders`(201), `GET /customer/orders`(페이지네이션). service 호출·에러 위임. (`prefix`는 §3.1 경로에 맞춰 `/customer`)  [3.1.1~3.1.5]

- [x] **Step 7 — 백엔드 요약**: `aidlc-docs/construction/unit2-customer/code/backend-summary.md` (모듈·엔드포인트·규칙 매핑).

### B. 백엔드 테스트 (PBT Partial + 통합 예제)

- [x] **Step 8 — DTO round-trip PBT**: `backend/tests/test_customer_dto_pbt.py` — Order 응답 DTO ↔ dict round-trip + line_total/total 일관성 (PBT-02/07/08). 제너레이터는 `tests/generators.py` 재사용. ✅ 통과.

- [x] **Step 9 — API/서비스 통합 예제 테스트**: `backend/tests/test_customer_api.py` (FastAPI `TestClient` + tmp DB fixture + seed) —
  로그인 성공/401 · 메뉴 조회(is_available=0 제외) · 주문 생성(세션 시작·총액 서버 재계산·주문번호 형식·order.created 발행) · 품절/미존재 거부(409/404 + details) · 현재 세션 내역(정렬·삭제/타세션 제외·페이지네이션). [BR-C1~C5] ✅ 16개 케이스 통과.
  - **발견·수정한 결함 2건**(통합 검증으로 조기 발견):
    1. `service.login` 이 JWT `sub` 를 정수로 저장 → PyJWT 2.10+ 가 디코드 시 `sub`(문자열 강제) 검증에 실패해 모든 인증 요청 401. → `sub=str(id)` 저장, `auth.py` 에서 `int()` 복원.
    2. `create_order`(async) + `get_conn`(sync) 조합으로 sqlite 연결이 스레드풀↔이벤트루프 간 교차 사용 → `sqlite3.ProgrammingError`. → `router.py` 의 연결 의존성/엔드포인트를 모두 async 로 통일(연결 생성·사용·종료를 동일 루프 스레드에서).

- [x] **Step 10 — 테스트 요약**: `.../code/test-summary.md` (커버리지·PBT 규칙 준수 표). ✅

### C. 프론트엔드 — Vue 앱

- [x] **Step 11 — 프론트 스캐폴딩**: `frontend/customer/` Vite+Vue3 프로젝트(package.json, vite.config[+dev proxy], index.html, src/main.js, App.vue, router[가드]). `.gitkeep` 제거.  [3.1.2] ✅

- [x] **Step 12 — 상태 스토어(Pinia)**: `stores/session.js`(토큰 localStorage), `stores/cart.js`(`cart:{table_id}` 로컬저장·실시간 총액·markUnavailable), `stores/menu.js`.  [3.1.1·3.1.3 / Q1·Q4·Q5] ✅

- [x] **Step 13 — API 클라이언트**: `api/client.js` — fetch 래퍼, Bearer 토큰 주입, 401 시 logout+/setup 리다이렉트, 에러 정규화(code/details).  [BR-C1.4] ✅

- [x] **Step 14 — 뷰/컴포넌트**: `SetupView`, `MenuView`(CategoryTabs/MenuGrid/MenuCard/MenuDetailModal/CartFab), `CartView`(CartItemRow/CartSummary/ConfirmOrderButton/OrderConfirmModal), `OrdersView`(OrderCard) + styles.css. `data-testid` 부여.  [3.1.2~3.1.5] ✅

- [x] **Step 15 — 프론트 요약**: `.../code/frontend-summary.md` (컴포넌트·라우트·스토어·API 매핑). ✅

### D. 문서/마무리

- [x] **Step 16 — README/문서 갱신**: `frontend/customer/README.md`(설치/실행/dev proxy) 작성 + `code-summary.md`로 Unit 2 전체 요약. ✅

- [x] **Step 17 — 검증**: 백엔드 `python -m pytest` **40 passed** (default & `HYPOTHESIS_PROFILE=ci`), 프론트 `npm install`+`npm run build` **성공**(47 modules). 스모크 절차는 README/test-summary 에 기록. 환경 이슈(Py3.14 핀버전 소스빌드 실패)는 3.14 호환 버전으로 검증하고 code-summary 후속 항목에 명시. ✅

> **DB 마이그레이션**: 신규 스키마 불필요(모든 테이블은 Unit 1 소유·기존). → 별도 마이그레이션 스텝 없음.

---

## 스토리 추적성
| 요구사항 | 백엔드 | 프론트 | 테스트 |
|---|---|---|---|
| 3.1.1 자동 로그인/세션 | Step 3,5,6 (login) | Step 12,13,14(SetupView) | Step 9 |
| 3.1.2 메뉴 조회/탐색 | Step 4,5,6 (menus) | Step 14(MenuView/모달) | Step 9 |
| 3.1.3 장바구니 | (클라이언트) | Step 12,14(cart store/CartView) | (수동/컴포넌트) |
| 3.1.4 주문 생성 | Step 4,5,6 (orders POST, 채번, SSE) | Step 14(ConfirmOrder), 13 | Step 8,9 |
| 3.1.5 주문 내역 | Step 4,5,6 (orders GET) | Step 14(OrdersView) | Step 9 |

## 규모 요약
- **총 17 스텝** (백엔드 7 + 테스트 3 + 프론트 5 + 문서/검증 2). 신규 마이그레이션 없음.
- 재사용 극대화(core 8모듈), 계약 변경 없음. 승인 시 Step 1부터 순차 실행하고 각 스텝 완료 즉시 [x] 갱신.
