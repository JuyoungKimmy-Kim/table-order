# Functional Design Plan — Unit 3: Admin Auth & Real-time Monitoring (임동규)

> **단계**: CONSTRUCTION → Per-Unit Loop → Functional Design (Part 1: Planning)
> **담당**: 임동규
> **범위(요구사항)**: 3.2.1 매장 인증 / 3.2.2 실시간 주문 모니터링
> **기준 계약**: `shared/integration-contract.md` (SSOT: `aidlc-docs/inception/application-design/integration-contract.md`)
> **의존**: Unit 1 코어(`app.core.security`, `app.core.sse`, `app.core.models/db/errors/pagination`) — 확정·사용 가능

---

## 컨텍스트 요약 (Step 1 — 분석 완료)

**계약이 이미 확정한 것 (재설계 대상 아님, 준수만):**
- API 시그니처: `POST /api/admin/login`, `GET /api/admin/me`, `GET /api/admin/orders/stream`(SSE), `GET /api/admin/dashboard`, `PATCH /api/admin/orders/{id}/status`, `GET /api/admin/orders/{id}` (§3.2)
- 인증: `Authorization: Bearer <JWT>`, 16시간 만료, bcrypt (§0.3, §3.2.1)
- SSE: 구독 엔드포인트·프레임 형식·이벤트 타입(`order.created`/`order.status_changed`/`order.deleted`/`session.closed`) (§2)
- DTO: OrderSummary(§4.1), OrderDetail(§4.2), 표준 에러 포맷(§0.2), 페이지네이션(§0.4)
- 상태 enum: `pending`/`preparing`/`completed` (§1.10)
- 코어 헬퍼: `verify_password`, `create_token`, `decode_token`, `sse.subscribe()`, `sse.publish()`

**Functional Design에서 새로 정의할 것(계약이 정하지 않은 세부 비즈니스 로직):**
- 로그인 시도 제한(threshold/lockout) 정책
- JWT claims 구조 및 인증 의존성(dependency) 검증 흐름
- 상태 변경 허용 전이 규칙
- 대시보드 스냅샷 ↔ SSE 스트림 정합/재연결 처리
- 신규 주문 강조·테이블 필터 등 프론트 상호작용
- 관리자 프론트 컴포넌트 구조·상태관리

---

## 명확화 질문 (Step 3)

각 질문의 `[Answer]:` 태그에 A~E 중 선택 또는 자유 답변을 적어주세요. **전부 기본값(A)로 진행을 원하면 "전부 기본값" 한 줄로 답해도 됩니다.**

### Q1. 로그인 시도 제한 — 임계값/잠금 (3.2.1)
계약 §3.2.1은 `429 TOO_MANY_ATTEMPTS`만 정의하고 구체 정책은 미정입니다.
- **A. (기본/권장)** 동일 (store_code, username) 기준 **5회 연속 실패 시 5분 잠금**. 성공하면 카운터 리셋.
- B. 3회 실패 시 1분, 지수 백오프(1→2→4분).
- C. IP 기준으로 집계.
- D. 시도 제한 없음(MVP 단순화, 429 미구현).
- E. 기타(직접 기술)

[Answer]: A

### Q2. 시도 카운터 저장 위치 (3.2.1)
- **A. (기본/권장)** **인메모리**(프로세스 딕셔너리). 단일 프로세스·소규모 가정, 재시작 시 리셋 허용.
- B. SQLite 테이블에 영속화(재시작에도 유지).
- C. 기타

[Answer]: A

### Q3. JWT payload(claims) 구성 (3.2.1)
- **A. (기본/권장)** `{ sub: admin_user_id, store_id, username, role: "admin", iat, exp }`. `GET /api/admin/me`는 토큰 claims만으로 응답(DB 재조회 없음).
- B. 위 + 매 요청 시 DB로 사용자 유효성 재확인.
- C. 기타

[Answer]: A

### Q4. 주문 상태 변경 허용 전이 (3.2.2 / §3.2.5)
- **A. (기본/권장)** **자유 전이 허용** — 임의 상태로 변경 가능(되돌리기 포함: completed→preparing 등). 잘못 누른 경우 정정 편의.
- B. 순방향만 허용(pending→preparing→completed), 역방향은 `409 CONFLICT`.
- C. 순방향 + 1단계 되돌리기만 허용.
- D. 기타

[Answer]: A

### Q5. 대시보드 스냅샷 ↔ SSE 실시간 정합 (3.2.2)
프론트가 초기 로드 후 스트림으로 갱신하는 방식입니다.
- **A. (기본/권장)** 프론트: `GET /api/admin/dashboard`로 초기 상태 로드 → **직후** `GET /api/admin/orders/stream` 연결. 재연결 시 `Last-Event-ID` 헤더 사용, 유실 의심 시 dashboard 재호출로 재동기화.
- B. 스냅샷 없이 스트림만으로 상태 구성(초기 빈 화면에서 이벤트로 채움).
- C. 주기적 폴링(SSE 미사용).
- D. 기타

[Answer]:A

### Q6. 대시보드 카드의 `recent_orders` 개수 및 신규 강조 (3.2.2 / §3.2.4)
- **A. (기본/권장)** 카드당 최신 **3건** 미리보기. 신규 주문(`order.created`) 수신 시 해당 카드를 **10초간** 시각 강조.
- B. 최신 5건 / 강조 5초.
- C. 개수·시간 커스텀(직접 기술).

[Answer]:A

### Q7. 테이블 필터링 위치 (3.2.2)
- **A. (기본/권장)** **프론트엔드 클라이언트 측** 필터(대시보드 전체 로드 후 UI에서 상태/테이블번호 필터). 백엔드 필터 파라미터 없음.
- B. 백엔드 쿼리 파라미터(`?status=pending&table_number=5`)로 서버 필터.
- C. 기타

[Answer]:A

### Q8. 관리자 프론트엔드 기술 구성 (3.2.2)
`frontend/admin/`은 Unit 3/4/5 공용 Vue 앱입니다. Unit 3이 앱 뼈대(라우터·인증 가드·상태관리)를 세팅합니다.
- **A. (기본/권장)** **Vue 3 + Vite + Pinia(상태) + Vue Router**. 로그인 라우트 + 모니터링 대시보드 라우트. 인증 가드로 미인증 시 로그인 리다이렉트. 토큰은 localStorage 저장(새로고침 세션 유지).
- B. Vue 3 + Vite, 상태관리는 컴포저블(Pinia 미사용).
- C. 기타(직접 기술)

[Answer]: A

### Q9. SSE 구독 시 인증 헤더 처리 (3.2.2)
브라우저 `EventSource`는 커스텀 헤더(Authorization)를 지원하지 않습니다.
- **A. (기본/권장)** `fetch` + `ReadableStream` 기반 SSE 클라이언트로 `Authorization: Bearer` 헤더 전송(예: `@microsoft/fetch-event-source` 또는 직접 구현). 백엔드는 헤더 인증 유지.
- B. 쿼리 파라미터로 토큰 전달(`/stream?token=...`) 후 백엔드가 쿼리에서 인증. (헤더 대신)
- C. 기타

[Answer]:A

---

## Functional Design 실행 단계 (Step 6 — 답변 확정 후 산출물 생성)

- [x] **P1. domain-entities.md** — Unit 3 관점 엔티티/뷰모델: AdminUser(인증), 로그인 시도 추적 구조(Q1/Q2), 대시보드 뷰모델(TableCard = table + session_active + table_total + recent_orders), Order 상태 뷰. Unit 1 모델 재사용 명시.
- [x] **P2. business-rules.md** — 인증 규칙(bcrypt 검증, JWT 발급/만료, 시도 제한 BR), 상태 전이 규칙(Q4), 대시보드 총액 계산은 `calc_table_total` 호출(직접 계산 금지), SSE 이벤트→화면 갱신 매핑 규칙.
- [x] **P3. business-logic-model.md** — 인증 플로우(로그인→토큰 발급→가드), 시도 제한 알고리즘, 대시보드 스냅샷 조립 로직, SSE 구독/재연결/재동기화 흐름(Q5), 상태 변경 시 `order.status_changed` 발행. PBT 대상 순수함수 식별(강제 PBT-02/03/07/08/09 해당 여부).
- [x] **P4. frontend-components.md** — 컴포넌트 계층(LoginView, DashboardView, TableCard, OrderDetailModal, StatusControl, TableFilter), props/state, 사용자 상호작용 플로우, 폼 검증, 각 컴포넌트↔백엔드 엔드포인트 매핑, Pinia 스토어(auth/dashboard) 설계(Q8).
- [x] **P5. 계약 준수/추적성 검증** — 6개 API·SSE 이벤트·DTO가 §3.2/§2/§4와 일치하는지 대조표(frontend-components §6). 계약 변경 필요 항목 없음 확인.
- [x] **P6. PBT 적용 판단** — Unit 3 순수함수(상태값 검증, 시도 제한 판정, recent 선별, claims 라운드트립)에 강제 PBT 규칙 적용 대상 명시(business-logic-model §6), PBT-04/05/06 N/A 사유 기재.

## 완료 조건
- [x] 모든 `[Answer]:` 태그 응답 수집 및 모호성 해소(Step 5) — Q1~Q9 전부 A(기본값), 모순/모호 없음
- [x] 산출물 4종 생성: `aidlc-docs/construction/unit3-admin/functional-design/{domain-entities,business-rules,business-logic-model,frontend-components}.md`
- [ ] 완료 메시지 제시 후 승인 대기(Step 7~8)
