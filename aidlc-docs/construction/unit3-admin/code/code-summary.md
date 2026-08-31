# Code Generation Summary — Unit 3: Admin Auth & Real-time Monitoring (임동규)

> **담당**: 임동규 · **상태**: 코드 생성 완료. 백엔드 pytest 50 passed(24 Unit1 + 26 Unit3, default & ci), `/health` 200, frontend `npm run build` 성공.
> **범위**: 요구사항 3.2.1(매장 인증) / 3.2.2(실시간 주문 모니터링). Unit 1 코어 재사용, 스키마 변경 없음.

## 생성 파일

### 백엔드 (`backend/app/admin_auth/`)
| 경로 | 내용 |
|---|---|
| `__init__.py` | 패키지 |
| `schemas.py` | Pydantic 요청/응답(LoginRequest/Response, MeResponse, StatusUpdate*, DashboardResponse, TableCard) |
| `repository.py` | sqlite 조회/UPDATE(store/admin/tables/session/orders/items), Unit 1 `db` 사용 |
| `attempts.py` | `evaluate_login_attempt`(순수, PBT) + `AttemptState`/`Decision` + `LoginAttemptTracker`(인메모리 전역) |
| `logic.py` | 순수 함수 `select_recent_orders`(3건·미삭제·내림차순), `build_admin_claims`(sub=str) |
| `deps.py` | `get_current_admin` → `AdminPrincipal`(Bearer→decode_token, DB 재조회 없음) |
| `service.py` | login/me/build_dashboard/get_order_detail/change_status 오케스트레이션 |
| `router.py` | 6개 엔드포인트(§3.2.1~3.2.6) |
| `app/main.py` | (수정) `admin_router` include(`prefix="/api"`) — 1줄 활성화 |

### 백엔드 테스트 (`backend/tests/`)
| 경로 | 내용 | PBT |
|---|---|---|
| `test_admin_auth_pbt.py` | 시도제한 상태전이·recent 선별 불변·claims round-trip | PBT-02/03/07/08 |
| `test_admin_auth_examples.py` | 5회→잠금, 성공→리셋, 만료 재시작, 상태값 검증 | PBT-10 |
| `test_admin_api.py` | TestClient: login 200/401/429, me, dashboard, status 200/400/404, detail, stream 인증/타입 | — |

### 프론트엔드 (`frontend/admin/` — Vue3+Vite+Pinia+Router, Q8=A)
| 경로 | 내용 |
|---|---|
| `package.json`/`vite.config.js`/`index.html`/`src/main.js`/`src/App.vue` | 앱 뼈대, `/api` 프록시 |
| `src/router/index.js` | 라우트 + 인증 가드 |
| `src/api/client.js` | fetch 래퍼(Bearer 자동첨부, 401→logout, ApiError) |
| `src/api/sse.js` | fetch+ReadableStream SSE(Authorization 헤더, Last-Event-ID, Q9=A) |
| `src/stores/auth.js` | login/fetchMe/logout/loadFromStorage(localStorage 토큰) |
| `src/stores/dashboard.js` | init/loadSnapshot/connect/resync/handleEvent(BR-A6.4)/setFilter/visibleTables |
| `src/views/LoginView.vue`·`DashboardView.vue` | 3.2.1 / 3.2.2 화면 |
| `src/components/{TableCard,OrderDetailModal,StatusControl,TableFilter}.vue` | 카드(10초 강조)/상세/상태변경(자유 전이)/클라이언트 필터 |
| `README.md` | 실행/구조 |

## 계획 대비 변경점
- **JWT `sub` 문자열화**: PyJWT 2.10 이 `sub` 를 문자열로 강제 → `build_admin_claims` 가 `sub=str(admin_id)`. `deps` 는 `int(claims["sub"])` 로 복원. (테스트로 회귀 방지)
- **SSE 테스트 방식**: 무한 스트림을 TestClient 로 소비하면 행(hang) → 스트림 테스트는 (a)미인증 401, (b)라우트 직접 호출로 `StreamingResponse`/`text/event-stream` 확인으로 대체(본문 미소비).
- **시도 트래커 주입**: `service.login` 이 호출 시점에 `attempts.tracker` 를 해석하도록 변경(기본 인자 바인딩 제거) → 테스트 격리 가능.

## 검증 결과
- `pytest`: **50 passed** (default), `HYPOTHESIS_PROFILE=ci pytest tests/test_admin_auth_pbt.py`: **7 passed**(재현성).
- `GET /health` → 200. admin 라우트 6개 등록 확인.
- `frontend/admin`: `npm install`(37 pkgs) → `npm run build` 성공(45 modules).

## PBT Compliance
| 규칙 | 상태 | 근거 |
|---|---|---|
| PBT-02 round-trip | ✅ | claims→create_token→decode_token 보존 |
| PBT-03 invariant | ✅ | 시도제한 전이(성공→리셋/임계값 잠금/잠금 중 불변), recent(길이≤n·미삭제·정렬·입력순서 무관) |
| PBT-07 generator | ✅ | Unit 1 `generators.py`(st_money) 재사용 + admin/monitor-order 제너레이터 |
| PBT-08 shrink/재현 | ✅ | Unit 1 conftest default/ci 프로파일 재사용 |
| PBT-09 framework | ✅ | hypothesis(기존 requirements.txt) |
| PBT-10 complementary | ✅ | 예제 기반 테스트 병행 |
| PBT-04/05/06 | N/A | idempotency/oracle/stateful — Unit 3 순수함수에 해당 없음 |

## 계약 준수 (변경 없음)
- 6개 API(§3.2)·SSE 이벤트(§2, `order.status_changed` 발행 + 4종 구독)·DTO(§4 OrderSummary/OrderDetail) 준수.
- 신규 필드/스키마/엔드포인트 변경 없음 → Unit 1(김주영) 조율 불필요.

## 다른 유닛 연계
- **Unit 4/5**: `frontend/admin/` 앱 뼈대(router/auth store/api client) 재사용, 라우트·뷰·스토어만 추가.
- **SSE**: Unit 2(`order.created`)·Unit 4(`order.deleted`/`session.closed`) 발행 이벤트를 대시보드가 구독·반영.
