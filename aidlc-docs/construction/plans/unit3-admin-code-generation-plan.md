# Code Generation Plan — Unit 3: Admin Auth & Real-time Monitoring (임동규)

> **담당**: 임동규 · **유닛**: Unit 3 (Admin Auth & Real-time Monitoring, 요구사항 3.2.1 / 3.2.2)
> **단일 진실 원천**: 이 계획이 Code Generation의 SSOT. 단계는 순서대로 실행하며 완료 즉시 [x] 표기.
> **기준 산출물**: `construction/unit3-admin/functional-design/*` · `inception/application-design/integration-contract.md`
> **기술 스택(확정)**: 백엔드 Python 3.9 · FastAPI · sqlite3(Unit 1 `db`) · pytest · Hypothesis(PBT) / 프론트 Vue 3 · Vite · Pinia · Vue Router
> **활성 확장**: PBT Partial — 강제 PBT-02·03·07·08·09 (코드 생성 시 반드시 반영)
> **NFR**: 생략(Unit 1 선례 — 스택 확정, 소규모 로컬)

## 유닛 컨텍스트
- **구현 스토리/책임**: 3.2.1 매장 인증(JWT/bcrypt/16h/시도제한/새로고침 세션 유지), 3.2.2 실시간 모니터링(SSE 구독, 대시보드 그리드, 상태 변경, 신규 강조, 필터).
- **의존성**: Unit 1 코어(확정·사용 가능). Unit 2/4가 발행하는 SSE 이벤트 소비.
- **소비 인터페이스(Unit 1, 재사용 — 재구현 금지)**:
  - `app.core.security`: `verify_password`, `create_token(claims, expires_seconds=)`, `decode_token`
  - `app.core.sse`: `publish(event, payload)`, `subscribe(last_event_id)`, `format_sse`
  - `app.core.domain`: `calc_table_total(orders)`
  - `app.core.models`: `OrderSummary`, `OrderDetail`, `OrderItemDetail`, `make_item_preview`
  - `app.core.validation`: `validate_order_status(status)`  ← **이미 존재, 재사용**(BR-A4.2)
  - `app.core.errors`: `Unauthorized`, `TooManyAttempts`, `OrderNotFound`, `ValidationError`, `register_exception_handlers`
  - `app.core.db`: `connect`, `transaction`
  - `app.core.config`: `JWT_EXPIRE_SECONDS`(57600), `DEFAULT_STORE_CODE`
- **소유 엔티티**: 없음(스키마 변경 없음). Unit 3 전용 런타임: `LoginAttemptTracker`(인메모리), `AdminPrincipal`.

## 코드 위치 (aidlc-state.md 기준, 절대 aidlc-docs/ 아님)
- 애플리케이션 코드: 워크스페이스 루트 (`backend/app/admin_auth/`, `backend/tests/`, `frontend/admin/`)
- 문서(마크다운 요약): `aidlc-docs/construction/unit3-admin/code/`

```text
table-order/
├── backend/
│   ├── app/
│   │   ├── main.py                     # (수정) admin_router include (기존 주석 위치)
│   │   └── admin_auth/
│   │       ├── __init__.py
│   │       ├── router.py               # 6개 엔드포인트(§3.2.1~3.2.6)
│   │       ├── service.py              # 로그인/대시보드/상태변경 오케스트레이션
│   │       ├── deps.py                 # get_current_admin → AdminPrincipal
│   │       ├── attempts.py             # LoginAttemptTracker(인메모리) + evaluate_login_attempt(순수)
│   │       ├── logic.py                # 순수 함수: select_recent_orders, build_admin_claims
│   │       ├── repository.py           # sqlite 조회(store/admin/tables/sessions/orders) — Unit 1 db 사용
│   │       └── schemas.py              # Pydantic 요청/응답 모델
│   └── tests/
│       ├── test_admin_auth_pbt.py      # PBT-02/03/07/08: 순수함수 속성
│       ├── test_admin_auth_examples.py # 예제 기반(PBT-10): 시도제한/상태전이/claims
│       └── test_admin_api.py           # FastAPI TestClient: 로그인/me/dashboard/status/detail/stream
└── frontend/admin/                     # Vue 3 앱 뼈대(Unit 3 세팅, Unit 4/5 확장)
    ├── package.json / vite.config.js / index.html
    └── src/
        ├── main.js
        ├── App.vue
        ├── router/index.js             # 라우트 + 인증 가드
        ├── stores/{auth.js,dashboard.js}
        ├── api/{client.js,sse.js}      # fetch 래퍼 + fetch+ReadableStream SSE(Q9=A)
        ├── views/{LoginView.vue,DashboardView.vue}
        └── components/{TableCard.vue,OrderDetailModal.vue,StatusControl.vue,TableFilter.vue}
```

---

## 생성 단계 (번호별, 순서 실행)

### 백엔드
- [x] **Step 1. admin_auth 패키지 골격** — `__init__.py`, `schemas.py`(LoginReq/LoginResp/MeResp/StatusReq/StatusResp), `repository.py`(store/admin/table/session/order 조회 함수, Unit 1 `db` 사용).
- [x] **Step 2. 순수 함수 — 시도 제한** — `attempts.py`: `AttemptState`, `evaluate_login_attempt(state, now, *, success, threshold=5, lockout=300s)` (부작용 없음) + `LoginAttemptTracker`(인메모리 dict, evaluate 결과 저장/조회). (BR-A2)
- [x] **Step 3. 순수 함수 — 로직 유틸** — `logic.py`: `select_recent_orders(orders, n=3)`(미삭제·ordered_at 내림차순·상한), `build_admin_claims(admin)`(sub/store_id/username/role). (BR-A3.1, BR-A5.3)
- [x] **Step 4. 인증 dependency** — `deps.py`: `get_current_admin()` — Bearer 추출→`decode_token`→`AdminPrincipal`. 실패 시 `Unauthorized`. (BR-A3.2~3.4)
- [x] **Step 5. 서비스 레이어** — `service.py`: `login()`(tracker+verify_password+create_token, 실패=401 동일 응답, 잠금=429), `build_dashboard()`(테이블별 TableCard, `calc_table_total`·`select_recent_orders`·`OrderSummary`), `change_status()`(validate_order_status+UPDATE+`sse.publish("order.status_changed")`), `get_order_detail()`(OrderDetail 조립). (BR-A1/A2/A4/A5/A6)
- [x] **Step 6. 라우터** — `router.py`: `POST /api/admin/login`, `GET /api/admin/me`, `GET /api/admin/orders/stream`(StreamingResponse+`sse.subscribe`, Last-Event-ID 헤더), `GET /api/admin/dashboard`, `PATCH /api/admin/orders/{id}/status`, `GET /api/admin/orders/{id}`. (§3.2)
- [x] **Step 7. main.py 라우터 등록** — 기존 주석 위치에 `admin_router` include(`prefix="/api"`). Unit 1 파일 최소 수정.

### 백엔드 테스트 (PBT 강제)
- [x] **Step 8. 순수함수 PBT** — `test_admin_auth_pbt.py`: `evaluate_login_attempt`(성공→리셋, 임계값 도달 시에만 잠금, 잠금 중 상태 불변), `select_recent_orders`(길이≤n·미삭제만·내림차순·입력순서 무관), `build_admin_claims` round-trip(claims→create_token→decode_token 보존). 제너레이터는 Unit 1 `tests/generators.py` 확장. (PBT-02/03/07/08)
- [x] **Step 9. 예제/API 테스트** — `test_admin_auth_examples.py`(시도제한 5회→429, 잠금 만료 재시작 등 고정 시나리오, PBT-10), `test_admin_api.py`(TestClient: 로그인 200/401/429, me, dashboard 구조, status 200/400/404, detail, stream 헤더/프레임).

### 프론트엔드 (Vue 앱 뼈대)
- [x] **Step 10. Vite/Vue 프로젝트 스캐폴딩** — `package.json`(vue3/vite/pinia/vue-router), `vite.config.js`(dev proxy `/api`→backend), `index.html`, `main.js`, `App.vue`.
- [x] **Step 11. 라우터·인증 가드·API 클라이언트** — `router/index.js`(login/dashboard + 가드), `api/client.js`(fetch 래퍼, Authorization 자동첨부, 401→logout), `api/sse.js`(fetch+ReadableStream, Bearer 헤더, Last-Event-ID, Q9=A).
- [x] **Step 12. Pinia 스토어** — `stores/auth.js`(login/fetchMe/logout/loadFromStorage, localStorage 토큰), `stores/dashboard.js`(init/applySnapshot/handleEvent(BR-A6.4)/reconnect/resync/setFilter/visibleTables).
- [x] **Step 13. 뷰·컴포넌트** — `LoginView.vue`, `DashboardView.vue`, `TableCard.vue`(3건·10초 강조), `OrderDetailModal.vue`, `StatusControl.vue`(자유 전이), `TableFilter.vue`(클라이언트 필터).

### 문서
- [x] **Step 14. 코드 요약 문서** — `aidlc-docs/construction/unit3-admin/code/code-summary.md`(생성 파일·검증 결과·PBT 준수·계약 준수), frontend/admin/README(실행법).

**검증(Part 2 종료 시)**: `pytest`(기존 24 + Unit 3 신규) 전부 통과, `GET /health` 200 유지, admin 로그인→dashboard→status→SSE 프레임 수동 확인, frontend `npm run build` 성공.

---

## PBT 준수 매핑 (코드 생성 시 강제)
| 규칙 | 반영 단계 | 내용 |
|---|---|---|
| PBT-02 (round-trip) | Step 8 | `build_admin_claims`→토큰→decode 보존; 응답 DTO는 Unit 1 round-trip 재사용 |
| PBT-03 (invariant) | Step 8 | 시도제한 상태 전이 불변, recent 선별 불변(길이/정렬/필터) |
| PBT-07 (generator) | Step 8 | Unit 1 generators 확장(admin_user, AttemptState, orders) |
| PBT-08 (shrink/재현) | Step 8 | Unit 1 conftest 프로파일(default/ci) 재사용 |
| PBT-09 (framework) | Step 8 | hypothesis(이미 requirements.txt 포함) |
| PBT-10 (complementary) | Step 9 | 예제 기반 테스트 병행 |
| PBT-04/05/06 | N/A | idempotency/oracle/stateful — Unit 3 순수함수에 해당 없음 |

## 스토리 추적성
| 단계 | 요구사항/스토리 | 계약 |
|---|---|---|
| Step 4~6(login/me) | 3.2.1 매장 인증 | §3.2.1, §3.2.2, §0.3 |
| Step 5~6(dashboard/stream/status/detail) | 3.2.2 실시간 모니터링 | §3.2.3~3.2.6, §2, §4 |
| Step 10~13(프론트) | 3.2.1+3.2.2 UI | §3.2, §2 |

## 계약 준수 (변경 없음)
- 6개 API·SSE 이벤트·DTO 전부 계약 §3.2/§2/§4 준수. 신규 필드/스키마 변경 없음 → Unit 1 조율 불필요.

## 총 규모
- 14개 단계. 백엔드 파일 ~7 + 테스트 3 + 프론트 ~15. Unit 1 코어 재사용으로 중복 구현 없음.
