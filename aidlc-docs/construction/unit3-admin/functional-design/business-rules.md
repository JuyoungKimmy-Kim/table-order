# Business Rules — Unit 3: Admin Auth & Real-time Monitoring (임동규)

> **소유**: Unit 3 (임동규). **기준**: Integration Contract §0.3, §2, §3.2, §4. 결정 Q1~Q9 = 전부 A.
> **의존 규칙**: Unit 1 BR-5(상태 전이), BR-10(인증·해싱), BR-11(SSE 이벤트)을 상속·구체화한다.

## BR-A1. 매장 인증 — 로그인 (3.2.1, §3.2.1)
- **BR-A1.1** `POST /api/admin/login` 요청 `{ store_code, username, password }`. `store_code`로 `Store`, `(store_id, username)`으로 `AdminUser` 조회.
- **BR-A1.2** 비밀번호 검증은 Unit 1 `security.verify_password(plain, admin.password_hash)`. bcrypt(BR-10.1).
- **BR-A1.3** 실패(매장/사용자 없음 또는 비밀번호 불일치)는 **모두 동일한** `401 UNAUTHORIZED`로 응답(사용자/매장 존재 여부 노출 금지).
- **BR-A1.4** 성공 시 `{ token, expires_in: 57600, store_name }` 반환. `token`은 BR-A3 claims로 발급.

## BR-A2. 로그인 시도 제한 (Q1=A, Q2=A / §3.2.1, 429)
- **BR-A2.1** 집계 단위: `(store_code, username)`. 저장: **인메모리**(재시작 리셋 허용).
- **BR-A2.2** **연속 5회 실패 시 5분 잠금**. 잠금 중에는 자격 검증 없이 즉시 `429 TOO_MANY_ATTEMPTS`.
- **BR-A2.3** 로그인 **성공 시** 해당 key의 실패 카운터·잠금 상태를 리셋(삭제).
- **BR-A2.4** 잠금 만료(`now >= locked_until`) 후 첫 시도는 카운터 0에서 재시작.
- **BR-A2.5** 판정 로직(카운트/잠금 여부 계산)은 **순수 함수**로 분리하여 PBT 대상(→ business-logic-model §PBT).

## BR-A3. JWT 발급·검증 (Q3=A / §0.3)
- **BR-A3.1** claims = `{ sub: admin_user_id, store_id, username, role: "admin" }`. `iat`/`exp`는 Unit 1 `create_token`이 부여(exp=16h).
- **BR-A3.2** 관리자 API는 `Authorization: Bearer <JWT>` 필수. 인증 dependency가 `decode_token`으로 검증.
- **BR-A3.3** 토큰 없음/형식오류/서명오류/만료 → `401 UNAUTHORIZED`(Unit 1 jwt 예외를 표준 에러로 변환).
- **BR-A3.4** 검증은 **claims만**으로 수행, 매 요청 DB 재조회 없음(Q3=A). `GET /api/admin/me`도 claims에서 `{ username, store_id }`를 그대로 반환.

## BR-A4. 주문 상태 변경 (Q4=A / §3.2.5, BR-5 상속)
- **BR-A4.1** `PATCH /api/admin/orders/{id}/status` 요청 `{ status }`. 대상 주문 없으면 `404 ORDER_NOT_FOUND`.
- **BR-A4.2** `status`는 `OrderStatus` 3종 중 하나여야 함. 그 외 값은 `400 VALIDATION_ERROR`(Unit 1 `validation` 헬퍼 사용).
- **BR-A4.3** **전이 제약 없음(자유 전이)** — 유효 상태값이면 임의 전이 허용(되돌리기 포함, 오조작 정정 편의). BR-5.3 지침과 일치.
- **BR-A4.4** 성공 시 `orders.status` UPDATE 후 `order.status_changed` SSE 발행(BR-A6).
- **BR-A4.5** 삭제된 주문(`is_deleted=1`) 상태 변경은 `404 ORDER_NOT_FOUND`로 취급(모니터링 대상 아님).

## BR-A5. 대시보드 스냅샷 (3.2.2 / §3.2.4)
- **BR-A5.1** `GET /api/admin/dashboard`는 매장의 전체 테이블에 대해 `TableCard`를 조립하여 반환.
- **BR-A5.2** `table_total`은 반드시 Unit 1 `domain.calc_table_total(orders)` 호출로 계산(**직접 합산 금지**, §0.5/§5).
- **BR-A5.3** `recent_orders`는 현재 active 세션의 **미삭제** 주문 중 최신 **3건**(Q6=A), `ordered_at` 내림차순, `OrderSummary`(§4.1)로 직렬화.
- **BR-A5.4** active 세션이 없는 테이블: `session_active=false`, `table_total=0`, `recent_orders=[]`.

## BR-A6. SSE 발행·구독 (BR-11 상속 / §2)
- **BR-A6.1** Unit 3은 상태 변경 시 `order.status_changed` **발행**: payload `{ order_id, table_id, status }`. 반드시 Unit 1 `sse.publish(event, payload)` 사용(BR-11.1).
- **BR-A6.2** Unit 3은 `GET /api/admin/orders/stream`으로 **구독**: `sse.subscribe(last_event_id)` → `StreamingResponse(media_type="text/event-stream")`. 관리자 인증 필수(BR-A3).
- **BR-A6.3** 구독 응답은 계약 §2.2 프레임 형식(`id`/`event`/`data`) — Unit 1 `format_sse`가 보장.
- **BR-A6.4** 이벤트→화면 갱신 매핑(프론트, Q5=A):
  | event | 화면 반영 |
  |---|---|
  | `order.created` | 해당 `table_id` 카드에 주문 prepend, `recent_orders` 3건 유지, **10초 강조**(Q6=A) |
  | `order.status_changed` | 카드 내 해당 주문 status 갱신 |
  | `order.deleted` | 해당 주문 제거, 카드 `table_total`을 payload 값으로 갱신 |
  | `session.closed` | 해당 테이블 카드 리셋(session_active=false, total=0, recent 비움) |

## BR-A7. SSE 인증 헤더 (Q9=A)
- **BR-A7.1** 브라우저 `EventSource`는 커스텀 헤더 미지원 → 프론트는 `fetch`+`ReadableStream` 기반 SSE 클라이언트로 `Authorization: Bearer` 전송. 백엔드는 헤더 인증 유지(쿼리 토큰 미사용).

## BR-A8. 테이블 필터 (Q7=A)
- **BR-A8.1** 상태/테이블번호 필터는 **클라이언트 측**에서 수행. dashboard/stream API에 필터 파라미터 없음(서버 부하·계약 단순화).

---

## 규칙 → 순수 함수/PBT 매핑 (요약, 상세는 business-logic-model)
| 규칙 | 순수 함수(Unit 3) | PBT 대상 |
|---|---|---|
| BR-A2.2/A2.4 | `evaluate_login_attempt(state, now)` → 잠금여부/갱신상태 | ✔ 후보(PBT-03 불변) |
| BR-A4.2/A4.3 | `validate_status_transition(target)` (상태값 유효성) | ✔ 후보(PBT-03) |
| BR-A5.2 | `domain.calc_table_total` (Unit 1) | Unit 1이 PBT 소유 |
| BR-A5.3 | `select_recent_orders(orders, n=3)` | ✔ 후보(PBT-03 순서/개수 불변) |
