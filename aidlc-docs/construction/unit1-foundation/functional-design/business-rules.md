# Business Rules — Unit 1: Foundation & Shared Core

> **소유**: Unit 1 (김주영). 아래 규칙은 전 유닛이 준수한다.
> **기준**: Integration Contract §0.5, §1, §2. 결정 Q1~Q6=A.

## BR-1. 금액·시각 표준
- **BR-1.1** 모든 금액은 정수(원 단위). 부동소수점 연산 금지.
- **BR-1.2** 모든 시각은 UTC ISO8601 문자열로 저장/전송.

## BR-2. 총액 계산 (Q4=A — 실시간)
- **BR-2.1** 주문 총액: `order.total_amount = Σ(order_item.unit_price × order_item.quantity)`. 주문 확정 시 스냅샷으로 저장.
  → 순수 함수 `calc_order_total(items)`.
- **BR-2.2** 테이블 현재 총액: 현재 active 세션에 속한 **미삭제(is_deleted=0)** 주문들의 `total_amount` 합. 별도 캐시 저장 없이 항상 계산.
  → 순수 함수 `calc_table_total(orders)`.
- **BR-2.3** 총액은 항상 비음수(모든 unit_price ≥ 0, quantity > 0이므로 자연 성립).

## BR-3. 세션 판별 (현재 세션)
- **BR-3.1** 테이블의 현재 세션 = `status='active'`인 TableSession. 테이블당 active 세션은 **최대 1개**(BR-4.4).
- **BR-3.2** 주문이 "현재 세션 주문"인지 판별: 주문의 `session_id`가 테이블의 active 세션 id와 같고, 세션이 `active`일 것.
  → 순수 함수 `is_current_session_order(order, session)`. `closed` 세션의 주문은 항상 `false`.
- **BR-3.3** 고객 주문 내역 조회(§3.1.4)는 **현재 active 세션의 미삭제 주문만** 반환.

## BR-4. 세션 라이프사이클
- **BR-4.1 세션 시작**: 테이블에 active 세션이 없는 상태에서 **첫 주문 생성** 시, 새 `TableSession(status='active', opened_at=now)` 생성 후 그 세션에 주문을 소속시킨다.
- **BR-4.2 주문 추가**: active 세션이 이미 있으면 기존 세션에 주문을 추가(새 세션 생성 안 함).
- **BR-4.3 세션 종료(이용 완료, Unit 4)**: active 세션을 `closed`로 전환하고 `closed_at=now` 기록. 해당 세션의 주문(+항목)을 `order_history`로 이동. 테이블 현재 주문/총액은 자동으로 0이 됨(active 세션이 사라지므로 BR-2.2 결과가 0).
- **BR-4.4 불변식 (Q3=A)**: 한 테이블에 active 세션은 최대 1개. DB 부분 유니크 인덱스 + 트랜잭션 내 원자적 "조회 후 없으면 생성"으로 동시성 상황에서도 보장. 위반 시도는 `409 CONFLICT`.

## BR-5. 주문 상태 전이 (Unit 3 실행, Unit 1 규칙 정의)
- **BR-5.1** 상태값: `pending` → `preparing` → `completed`. 신규 주문 기본값 `pending`.
- **BR-5.2** 허용 전이: 계약상 상태 변경 API(§3.2.5)는 목표 상태를 직접 지정. 유효 상태값(3종) 외 값은 `400 VALIDATION_ERROR`.
- **BR-5.3** (설계 지침) MVP에서는 임의 상태 간 전이를 허용하되, 상태값 자체의 유효성만 검증. 엄격한 전이 그래프 강제는 범위 외.

## BR-6. 주문번호 생성 (Q1=A, Q2=A)
- **BR-6.1** 형식: `A-{YYYYMMDD(UTC)}-{NNNN}` (접두사 고정 `A`, UTC 날짜, 당일 시퀀스 4자리 zero-pad).
- **BR-6.2** 시퀀스: 매장+UTC 날짜 단위로 1부터 증가, 다음 날 리셋. 하루 최대 9999.
- **BR-6.3** 유일성: `order_number`는 전역 UNIQUE. (날짜가 포함되므로 날짜별 리셋과 양립.)
  → 순수 함수 `order_number_format(prefix, date, seq)` (형식 조립부만 순수; 시퀀스 채번은 DB 트랜잭션).

## BR-7. 스냅샷 원칙
- **BR-7.1** OrderItem은 주문 시점의 `menu_name`, `unit_price`를 복사 저장. 이후 메뉴 변경/삭제(Unit 5)에 영향받지 않음.
- **BR-7.2** 주문 생성 시 서버는 클라이언트가 보낸 가격/총액을 신뢰하지 않고, 메뉴 마스터의 현재 `price`로 재계산하여 스냅샷을 만든다(§3.1.3).

## BR-8. 메뉴 노출/가용성
- **BR-8.1** 고객 메뉴 조회(§3.1.2)는 `is_available=1` 메뉴만 반환(제외가 기본).
- **BR-8.2** 관리자 메뉴 목록(§3.4.1)은 `is_available` 무관 전체 반환.
- **BR-8.3** 정렬: 카테고리 `display_order ASC, id ASC` → 메뉴 `display_order ASC, id ASC`.
- **BR-8.4** 주문 생성 시 대상 메뉴가 `is_available=0`이면 `409 MENU_UNAVAILABLE`, 존재하지 않으면 `404 MENU_NOT_FOUND`.

## BR-9. 검증 규칙 (공통 검증 헬퍼로 제공)
- **BR-9.1** 메뉴: `name` 필수(비어있지 않음), `price` 정수 ≥ 0. 위반 시 `400 VALIDATION_ERROR`(details에 필드별 사유).
- **BR-9.2** 주문 생성: `items` 비어있지 않음, 각 `quantity` ≥ 1(정수). 위반 시 `400 VALIDATION_ERROR`.
- **BR-9.3** 페이지네이션: `page ≥ 1`, `size` 기본 20(상한 지정 가능). 범위 밖 값은 기본값으로 정규화.

## BR-10. 인증·해싱 (헬퍼만 Unit 1 제공, 정책은 Unit 3)
- **BR-10.1** 비밀번호(관리자·테이블)는 bcrypt 해시로 저장. 평문 저장 금지.
- **BR-10.2** JWT 유효기간 16시간(57600초). 만료 시 `401 UNAUTHORIZED`. (발급/검증 정책은 Unit 3, Unit 1은 토큰 유틸/상수만.)

## BR-11. SSE 이벤트 규약 (Unit 1 브로커, 발행은 각 유닛)
| event | 발행 유닛 | 트리거 규칙 |
|---|---|---|
| `order.created` | Unit 2 | 주문 생성 성공 직후 |
| `order.status_changed` | Unit 3 | 상태 변경 성공 직후 |
| `order.deleted` | Unit 4 | 직권 삭제 성공 후(재계산된 table_total 포함) |
| `session.closed` | Unit 4 | 세션 종료 성공 후 |

- **BR-11.1** 발행은 반드시 공통 브로커 `core.sse.publish(event, payload)`를 통해서만 수행.
- **BR-11.2** 이벤트 id는 단조 증가 시퀀스. 구독측은 `Last-Event-ID`로 재연결(서버 best-effort 재전송).

---

## 규칙 → 순수 함수/PBT 매핑 (요약, 상세는 business-logic-model)
| 규칙 | 순수 함수 | PBT 대상 |
|---|---|---|
| BR-2.1 | `calc_order_total` | ✔ (PBT-03 불변, 결합/교환) |
| BR-2.2 | `calc_table_total` | ✔ (PBT-03 불변) |
| BR-3.2 | `is_current_session_order` | ✔ (PBT-03 불변) |
| BR-6.1 | `order_number_format` | ✔ (PBT-02 round-trip / PBT-03 형식 불변) |
