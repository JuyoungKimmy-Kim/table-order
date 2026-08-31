# Business Rules — Unit 4: Table & Session Management

> **소유**: Unit 4 (이명우). 아래 규칙은 테이블·세션 관리 기능에 한정한다.
> **기준**: Integration Contract §0.5, §3.3, §2 · requirements 3.2.3 · Unit 1 business-rules.md(BR-2·3·4·11 준수).
> **의존**: Unit 1 코어(도메인 함수/DB/SSE/에러/보안)에만 의존. 다른 기능 유닛과 코드 의존 없음.

## 원칙
Unit 4는 새 도메인 규칙을 만들지 않고, Unit 1이 정의한 세션 라이프사이클·총액 규칙(BR-2, BR-3, BR-4, BR-11)을 **실행하는 유닛**이다. 아래는 그 실행 관점의 세부 규칙이다.

## U4-BR-1. 테이블 초기 설정 (요구 3.2.3-1)
- **U4-BR-1.1** `table_number`는 정수, 단일 매장 내 **유일**(`UNIQUE(store_id, table_number)`). 중복 시 `409 CONFLICT`.
- **U4-BR-1.2** `password`는 평문 수신 후 **bcrypt 해시로만 저장**(`core.security.hash_password`). 평문·응답 노출 금지 (Unit 1 BR-10.1).
- **U4-BR-1.3** 검증: `table_number` 필수(정수), `password` 필수(비어있지 않음). 위반 시 `400 VALIDATION_ERROR`(details에 필드별 사유).
- **U4-BR-1.4** "16시간 세션 생성 / 자동 로그인 활성화"는 테이블 자격 등록으로 충족된다. 실제 세션(TableSession)은 **첫 주문 시점에 생성**(Unit 1 BR-4.1)되며, 이 API는 세션 레코드를 미리 만들지 않는다. 16시간은 로그인 시 발급되는 토큰 수명(Unit 2/§0.3)으로 실현된다.

## U4-BR-2. 주문 직권 삭제 (요구 3.2.3-2)
- **U4-BR-2.1** 삭제는 **소프트 삭제**: `orders.is_deleted = 1`로 표시(물리 삭제 아님). 감사/이력 보존 목적.
- **U4-BR-2.2** 삭제 후 테이블 현재 총액을 **재계산**한다. 저장하지 않고 현재 active 세션의 미삭제 주문으로 실시간 계산 → `core.domain.calc_table_total` 호출 (Unit 1 BR-2.2).
- **U4-BR-2.3** 존재하지 않는 주문이면 `404 ORDER_NOT_FOUND`.
- **U4-BR-2.4** 이미 삭제된 주문(`is_deleted=1`) 재삭제 요청은 **멱등** 처리(현재 상태·재계산 총액 반환, 오류 아님).
- **U4-BR-2.5** 삭제 성공 후 `order.deleted` SSE 발행: `{order_id, table_id, table_total}` (재계산된 총액 포함, Unit 1 BR-11).

## U4-BR-3. 세션 종료 — 이용 완료 (요구 3.2.3-3)
- **U4-BR-3.1** 대상 테이블에 `active` 세션이 없으면 `409 NO_ACTIVE_SESSION`.
- **U4-BR-3.2** 종료는 **원자적 트랜잭션**으로 수행 (Unit 1 BR-4.3):
  1. active 세션 `status='closed'`, `closed_at = now(UTC)` 기록.
  2. 해당 세션의 **모든 주문(+항목)** 을 `order_history`(+`order_history_items`)로 **스냅샷 복사 이동**. `session_closed_at`·`store_id` 기록, `original_order_id`에 원본 id 보존.
  3. 이동 시 `is_deleted` 값도 그대로 보존(삭제된 주문도 이력에 남기되 플래그 유지).
- **U4-BR-3.3** 종료 후 테이블 현재 주문 목록·총액은 자동으로 0/빈 목록이 된다(active 세션이 사라져 BR-2.2·BR-3.3 결과가 0). 별도 리셋 컬럼 조작 불필요.
- **U4-BR-3.4** 새 고객은 이전 주문 없이 시작 가능(다음 첫 주문이 새 active 세션 생성, BR-4.1).
- **U4-BR-3.5** 종료 성공 후 `session.closed` SSE 발행: `{table_id, session_id}` (Unit 1 BR-11).
- **U4-BR-3.6** 응답: `{table_id, closed_session_id, moved_orders}` (이동된 주문 건수).

## U4-BR-4. 현재 테이블 주문 목록 (요구 3.2.3, 계약 §3.3.4)
- **U4-BR-4.1** 현재 `active` 세션의 **미삭제(is_deleted=0)** 주문만 반환. active 세션 없으면 빈 목록.
- **U4-BR-4.2** 각 주문은 `OrderDetail`(§4.2) 형식(항목 포함, `line_total` 파생).
- **U4-BR-4.3** 정렬: `ordered_at` 오름차순(발생 순).

## U4-BR-5. 과거 주문 내역 조회 (요구 3.2.3-4, 계약 §3.3.5)
- **U4-BR-5.1** `order_history`에서 해당 `table_id` 이력을 `ordered_at` **역순**(최신 먼저)으로 반환.
- **U4-BR-5.2** 날짜 필터: `date_from`·`date_to`(YYYY-MM-DD, 선택). 지정 시 `ordered_at`이 `[date_from 00:00, date_to 24:00)` UTC 범위에 드는 주문만. 경계 포함은 `date_from <= ordered_at < (date_to + 1일)`.
- **U4-BR-5.3** 페이지네이션 적용(§0.4): `page`(기본 1), `size`(기본 20, 상한 지정) → 응답 래퍼 `{items, page, size, total}`. `core.pagination` 사용.
- **U4-BR-5.4** 각 항목은 `OrderDetail` + `session_closed_at`(매장 이용 완료 시각) 포함.
- **U4-BR-5.5** 잘못된 날짜 형식은 `400 VALIDATION_ERROR`.

## U4-BR-6. 인증·권한
- **U4-BR-6.1** Unit 4의 모든 엔드포인트는 관리자 API(`/api/admin/...`)로 `Authorization: Bearer <JWT>` 필요(§0.3). 토큰 검증은 `core.security.decode_token` 사용, 실패 시 `401 UNAUTHORIZED`.
- **U4-BR-6.2** 인증 **정책**(로그인/발급)은 Unit 3 소유. Unit 4는 검증 의존성(dependency)만 로컬로 두되, Unit 3의 토큰 클레임(`store_id`)과 동일 규약을 따른다. 단일 매장 가정으로 `store_id`는 고정값 사용 가능.

## U4-BR-7. 금액·시각·매장
- **U4-BR-7.1** 금액은 정수(원), 시각은 UTC ISO8601 문자열 (Unit 1 BR-1).
- **U4-BR-7.2** 단일 매장 가정: `store_id`는 고정값(시드 매장)으로 처리.

---

## 규칙 → SSE 이벤트 매핑
| 트리거 | event | 페이로드 | 규칙 |
|---|---|---|---|
| 주문 직권 삭제 성공 | `order.deleted` | `{order_id, table_id, table_total}` | U4-BR-2.5 |
| 세션 종료 성공 | `session.closed` | `{table_id, session_id}` | U4-BR-3.5 |

> 구독은 Unit 3(모니터링). Unit 4는 발행만 담당하며 반드시 `core.sse.publish`를 통한다.
