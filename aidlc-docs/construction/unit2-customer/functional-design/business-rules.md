# Business Rules — Unit 2: Customer Ordering (고객 주문)

> **담당**: 박찬준 · **기준**: 계약 §0.5·§3.1 / 요구사항 3.1.1~3.1.5 / 인터뷰 결정 Q1~Q8
> 규칙 ID 접두사 `BR-C` (Customer). 총액·세션·주문번호 계산은 **Unit 1 순수함수 위임**(직접 계산 금지).

## BR-C1. 자동 로그인 / 인증 (3.1.1)
- **BR-C1.1** 로그인은 `(store_code, table_number, password)` 3요소로 검증한다. `store_code`→store 조회, `(store_id, table_number)`→table 조회, `verify_password(password, table.password_hash)` 성공해야 한다. 하나라도 실패 시 **401 `UNAUTHORIZED`** (사유 미노출, 계정 존재 여부 누설 금지).
- **BR-C1.2** 성공 시 `table_token`(JWT, 16h, 클레임=table_id/store_id/table_number)을 발급한다.
- **BR-C1.3** (Q1) 클라이언트는 **table_token 만** 로컬 저장한다. 평문 비밀번호는 저장하지 않는다.
- **BR-C1.4** (Q2) 이후 모든 고객 API는 `Authorization: Bearer <table_token>`. 토큰 만료/무효 시 **401** → 클라이언트는 재로그인(초기 설정) 화면으로 전환한다(무인 재로그인 없음).
- **BR-C1.5** 인증 컨텍스트의 `table_id`/`store_id`는 토큰에서만 취득한다. 요청 본문의 table/store 값은 신뢰하지 않는다.

## BR-C2. 메뉴 조회 (3.1.2)
- **BR-C2.1** 인증된 테이블의 `store_id` 기준 메뉴만 반환한다.
- **BR-C2.2** (품절 규칙) `is_available=0` 메뉴는 응답에서 **제외**한다.
- **BR-C2.3** 정렬: 카테고리 `display_order ASC, id ASC`, 카테고리 내 메뉴 동일 정렬.
- **BR-C2.4** 메뉴가 하나도 없는 카테고리도 응답에 포함하되 `menus: []` (프론트 빈 상태 처리).

## BR-C3. 장바구니 (3.1.3, 클라이언트 규칙)
- **BR-C3.1** 장바구니는 **클라이언트 전용**. 서버 전송은 주문 확정 시에만 발생.
- **BR-C3.2** (Q4) localStorage 키 `cart:{table_id}` 로 테이블별 분리 저장, 새로고침 시 복원.
- **BR-C3.3** 총액은 화면에서 `Σ(unit_price × quantity)` 로 실시간 표시(참고용). **확정 총액은 서버 재계산이 진실**(BR-C4.3).
- **BR-C3.4** 수량은 1 이상 정수. 수량 0으로 감소 시 항목 제거. 장바구니 비우기 = 키 삭제.
- **BR-C3.5** 주문 확정 성공 시 해당 `cart:{table_id}` 를 비운다(BR-C4.6).

## BR-C4. 주문 생성 (3.1.4)
- **BR-C4.1** 요청 검증: `core.validation.validate_order_items` — items 비어있지 않음, 각 `quantity>=1` 정수, `menu_id` 정수. 위반 시 **400 `VALIDATION_ERROR`**.
- **BR-C4.2** (품절/삭제 재검증, Q5) 각 `menu_id` 를 서버에서 조회한다. 존재하지 않으면 **404 `MENU_NOT_FOUND`**, 존재하나 `is_available=0` 이면 **409 `MENU_UNAVAILABLE`**. 이 경우 주문 **전체를 거부**(원자적)하고, `error.details` 에 문제 menu_id 목록(`not_found_menu_ids` / `unavailable_menu_ids`)을 담아 프론트가 품절 표시하도록 한다.
- **BR-C4.3** (신뢰 경계) 단가·메뉴명은 **서버가 메뉴 마스터에서 재조회**하여 스냅샷한다. 클라이언트가 보낸 가격은 신뢰하지 않는다. 주문 총액 = `core.domain.calc_order_total(재조회 항목)`.
- **BR-C4.4** (세션 시작, §0.5) 테이블에 `active` 세션이 없으면 새 `TableSession(active, opened_at=now)` 를 생성한다. 있으면 그 세션을 사용한다. active 세션 최대 1개 제약은 DB 부분 유니크 인덱스가 보장.
- **BR-C4.5** (주문번호 채번, Q7) 동일 트랜잭션 내에서 `order_sequences(store_id, seq_date=UTC YYYYMMDD)` 를 UPSERT 하여 `last_seq += 1` 로 seq 획득 → `core.domain.order_number_format("A", today_utc, seq)`. 하루 9999 초과 시 `INTERNAL_ERROR`(운영상 도달 불가 가정).
- **BR-C4.6** (성공 플로우) `orders`(status=pending, total_amount 스냅샷, ordered_at=now) + `order_items`(menu_name/unit_price 스냅샷) INSERT. 성공 시 `OrderSummary` 페이로드로 **`order.created` SSE 발행**. 프론트는 주문번호 표시 → 장바구니 비우기 → 메뉴 화면 리다이렉트.
- **BR-C4.7** (원자성) 세션 생성·채번·주문/항목 INSERT·SSE 준비는 **단일 트랜잭션**. 실패 시 롤백하고 클라이언트 장바구니는 유지(프론트는 에러 표시).
- **BR-C4.8** SSE 발행은 DB 커밋 성공 이후 수행한다(커밋 실패 시 유령 이벤트 방지).

## BR-C5. 주문 내역 조회 (3.1.5)
- **BR-C5.1** (필터) 인증 테이블의 **현재 active 세션**에 속한 주문만 반환. `is_current_session_order` 의미 준수. active 세션이 없으면 빈 목록.
- **BR-C5.2** `is_deleted=1`(직권 삭제, Unit 4) 주문은 제외.
- **BR-C5.3** 정렬: `ordered_at` **오름차순**(주문 시간순). 페이지네이션 §0.4(`core.pagination`).
- **BR-C5.4** 각 주문은 `OrderDetail`(주문번호·시각·상태·총액·항목목록[menu_name/unit_price/quantity/line_total]).
- **BR-C5.5** (Q6) 실시간 갱신 미구현. 화면 진입/수동 새로고침 시 재조회로 최신 상태 반영.

## BR-C6. 공통/에러
- **BR-C6.1** 모든 에러 응답은 계약 §0.2 표준 포맷(`error.code/message/details`). Unit 1 `core.errors` 예외 사용.
- **BR-C6.2** 금액은 정수(원). 시각은 UTC ISO8601 문자열.
- **BR-C6.3** 다른 테이블/세션의 주문 접근 불가(토큰의 table_id 범위로만 조회).

## 규칙 → 요구사항 추적성
| BR | 요구사항 | 계약 |
|---|---|---|
| BR-C1 | 3.1.1 | §3.1.1, §0.3 |
| BR-C2 | 3.1.2 | §3.1.2 |
| BR-C3 | 3.1.3 | (클라이언트) |
| BR-C4 | 3.1.4 | §3.1.3, §0.5, §2.3 |
| BR-C5 | 3.1.5 | §3.1.4, §0.4 |
