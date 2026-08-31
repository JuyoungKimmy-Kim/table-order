# Business Logic Model — Unit 1: Foundation & Shared Core

> **소유**: Unit 1 (김주영). 코어 모듈(`backend/app/core/`)이 제공하는 로직 설계.
> **기준**: Integration Contract §0.5, §2, §5 · business-rules.md · domain-entities.md.
> **활성 확장**: PBT Partial — 강제 PBT-02·03·07·08·09. 본 문서는 **PBT-01(속성 식별)** 을 충족한다.

## 1. 코어 모듈 구성 (backend/app/core/)

```text
core/
├── db.py            # 연결/트랜잭션 컨텍스트, 스키마 부트스트랩 (Q6=A: sqlite3 경량)
├── models.py        # 엔티티 dataclass/TypedDict + 직렬화(DTO) 헬퍼
├── domain.py        # 순수 함수: calc_order_total / calc_table_total /
│                    #            is_current_session_order / order_number_format
├── errors.py        # 표준 에러 응답 포맷 + 도메인 예외 → HTTP 매핑
├── validation.py    # 검증 헬퍼 (BR-9)
├── security.py      # bcrypt 해싱/검증, JWT 유틸/상수 (헬퍼만)
├── sse.py           # SSE 브로커: publish(event, payload) / subscribe()
└── pagination.py    # page/size 정규화 + 응답 래퍼(§0.4)
```

## 2. 순수 함수 계약 (PBT 대상 · `core/domain.py`)

모든 유닛은 총액/세션 판별을 **직접 계산하지 말고 이 함수를 호출**한다.

### 2.1 `calc_order_total(items) -> int`
- **입력**: `[{"unit_price": int>=0, "quantity": int>=1}, ...]`
- **출력**: `Σ(unit_price × quantity)` (정수)
- **규칙**: BR-2.1. 빈 목록 → 0.

### 2.2 `calc_table_total(orders) -> int`
- **입력**: `[{"total_amount": int, "is_deleted": bool}, ...]`
- **출력**: `Σ total_amount where is_deleted == False`
- **규칙**: BR-2.2. 삭제 주문 제외. 빈 목록 → 0.

### 2.3 `is_current_session_order(order, session) -> bool`
- **입력**: `order{session_id}`, `session{id, status}`
- **출력**: `order.session_id == session.id AND session.status == 'active'`
- **규칙**: BR-3.2. `closed` 세션이면 항상 `False`.

### 2.4 `order_number_format(prefix: str, date: date, seq: int) -> str`
- **출력**: `f"{prefix}-{date:%Y%m%d}-{seq:04d}"` (예: `A-20260831-0007`)
- **규칙**: BR-6.1. `seq`는 1..9999. `parse_order_number(s)`로 역파싱 가능(round-trip).

> 시퀀스 채번(다음 seq 결정)은 DB 트랜잭션 책임이며 순수 함수가 아니다. 순수 함수는 **형식 조립/파싱**만 담당.

## 3. 상태를 다루는 로직 (트랜잭션 · 순수 아님)

### 3.1 주문 생성 흐름 (Unit 2가 호출, Unit 1이 코어 제공)
```text
BEGIN TX
  session = get_active_session(table_id)
  if session is None:
      session = create_session(table_id, opened_at=now)   # BR-4.1, 부분 유니크 인덱스로 중복 방지
  validate items (BR-9.2)
  for each item: menu = load_menu(menu_id)
      if not found -> 404 MENU_NOT_FOUND
      if not menu.is_available -> 409 MENU_UNAVAILABLE
      snapshot menu_name, unit_price (BR-7)
  total = calc_order_total(snapshotted items)
  seq = next_daily_seq(store_id, utc_date(now))            # BR-6.2 (원자적 채번)
  order_number = order_number_format('A', utc_date(now), seq)
  insert order(status='pending', total_amount=total, ...)
COMMIT
publish('order.created', OrderSummary)                     # BR-11
```

### 3.2 세션 종료 흐름 (Unit 4가 호출)
```text
BEGIN TX
  session = get_active_session(table_id)
  if None -> 409 NO_ACTIVE_SESSION
  session.status = 'closed'; session.closed_at = now       # BR-4.3
  move session orders (+items) to order_history            # 스냅샷 유지
COMMIT
publish('session.closed', {table_id, session_id})
```

### 3.3 직권 삭제 흐름 (Unit 4가 호출)
```text
order.is_deleted = 1
table_total = calc_table_total(active session orders)      # 실시간 재계산 (Q4=A)
publish('order.deleted', {order_id, table_id, table_total})
```

## 4. 표준 에러 처리 (`core/errors.py`)
- 도메인 예외 클래스 → 계약 §0.2 에러 응답으로 매핑.
- 공통 코드: `VALIDATION_ERROR(400)`, `UNAUTHORIZED(401)`, `FORBIDDEN(403)`, `NOT_FOUND(404)`, `CONFLICT(409)`, `TOO_MANY_ATTEMPTS(429)`, `INTERNAL_ERROR(500)`.
- 구체 코드: `MENU_NOT_FOUND`, `MENU_UNAVAILABLE`, `ORDER_NOT_FOUND`, `NO_ACTIVE_SESSION`.

## 5. DTO 직렬화 (`core/models.py`)
- `OrderSummary`(§4.1), `OrderDetail`(§4.2) 직렬화/역직렬화 헬퍼.
- `OrderDetail.items[].line_total = unit_price × quantity` (계산 필드).
- **PBT-07/08 round-trip 대상**: DTO ↔ dict/JSON 왕복이 항등이어야 함.

---

## 6. Testable Properties (PBT-01 준수)

각 컴포넌트별 식별된 속성. 강제 규칙(PBT-02·03·07·08·09)은 **[강제]** 표기.

### 6.1 `calc_order_total`
| 속성 | 카테고리 | 설명 | 규칙 |
|---|---|---|---|
| 비음수 | Invariant **[강제 PBT-03]** | 결과 ≥ 0 (unit_price≥0, quantity≥1) | BR-2.3 |
| 순서 무관 | Commutativity/Invariant **[강제 PBT-03]** | 항목 순서를 섞어도 결과 동일 | BR-2.1 |
| 빈 목록 = 0 | Invariant **[강제 PBT-03]** | `calc_order_total([]) == 0` | |
| 결합(분할합) | Induction/Invariant **[강제 PBT-03]** | `total(a+b) == total(a)+total(b)` | |

### 6.2 `calc_table_total`
| 속성 | 카테고리 | 설명 | 규칙 |
|---|---|---|---|
| 삭제 제외 | Invariant **[강제 PBT-03]** | is_deleted=True 주문은 합에서 제외 | BR-2.2 |
| 부분합 일치 | Oracle/Invariant **[강제 PBT-03]** | 미삭제 total_amount 단순 합과 일치 | |
| 빈 목록 = 0 | Invariant **[강제 PBT-03]** | | |

### 6.3 `is_current_session_order`
| 속성 | 카테고리 | 설명 | 규칙 |
|---|---|---|---|
| closed → False | Invariant **[강제 PBT-03]** | session.status='closed'면 무조건 False | BR-3.2 |
| id 불일치 → False | Invariant **[강제 PBT-03]** | session_id 다르면 False | |

### 6.4 `order_number_format` / `parse_order_number`
| 속성 | 카테고리 | 설명 | 규칙 |
|---|---|---|---|
| round-trip | Round-trip **[강제 PBT-02]** | `parse(format(p,d,s)) == (p,d,s)` (1≤s≤9999) | BR-6 |
| 형식 불변 | Invariant **[강제 PBT-03]** | 정규식 `^A-\d{8}-\d{4}$` 항상 만족 | BR-6.1 |

### 6.5 DTO 직렬화 (`OrderSummary`, `OrderDetail`)
| 속성 | 카테고리 | 설명 | 규칙 |
|---|---|---|---|
| serialize round-trip | Round-trip **[강제 PBT-02/PBT-07/08]** | `deserialize(serialize(dto)) == dto` | §4 |
| line_total 일관성 | Invariant **[강제 PBT-03]** | `Σ line_total == total_amount` | |

### 6.6 검증 헬퍼 (`validation.py`)
| 속성 | 카테고리 | 설명 |
|---|---|---|
| 유효 입력 통과 | Invariant (advisory) | 유효 범위 입력은 항상 통과 |
| 경계 거부 | Invariant (advisory) | price<0, quantity<1, 빈 name/items는 항상 거부 |

### 컴포넌트별 "No PBT" 명시 (PBT-01)
- `db.py`, `sse.py`, `security.py`(bcrypt/JWT I/O 래핑): **순수 속성 없음** — I/O·부작용 중심이라 PBT 미적용. 예제 기반 테스트로 커버. (round-trip 성격의 security 유틸이 있으면 해당 부분만 PBT-02 검토.)

---

## 7. 제너레이터 계획 (PBT-07 [강제])
`backend/tests/generators.py`에 도메인 제너레이터를 중앙화:
- `st_money` = `integers(min_value=0, max_value=10_000_000)` (원 단위 현실 범위)
- `st_quantity` = `integers(min_value=1, max_value=99)`
- `st_order_item` = money·quantity 조합 fixed_dictionaries
- `st_order` = total_amount + is_deleted(booleans) fixed_dictionaries
- `st_seq` = `integers(min_value=1, max_value=9999)`
- `st_date` = `dates()` (형식 함수용)
- 각 유닛의 PBT는 이 제너레이터를 재사용(중복 정의 금지).

## 8. 재현성/CI 계획 (PBT-08 [강제])
- Hypothesis 기본 shrinking 사용(비활성화 금지).
- 실패 시 seed + 최소 반례 출력. CI에서 seed 로깅 또는 고정 seed 프로파일 사용.
- 상세 실행 지침은 Build & Test 단계에서 정의.

## 9. 프레임워크 선택 (PBT-09 [강제])
- PBT 프레임워크: **Hypothesis** (Python). `requirements.txt`에 포함 예정(Code Generation).
- 커스텀 제너레이터·shrinking·seed 재현성·pytest 통합 모두 지원.
