# Functional Design Plan — Unit 2: Customer Ordering (고객 주문)

> **담당**: 박찬준
> **단계**: CONSTRUCTION → Per-Unit Loop → Functional Design (Part 1 — Planning)
> **기준 문서**: `shared/integration-contract.md` §3.1 · 요구사항 3.1.1~3.1.5 · `unit-of-work.md` Unit 2
> **재사용(Unit 1)**: `core.domain`(calc_order_total/order_number_format 등) · `core.models`(OrderDetail/OrderItemDetail) · `core.errors` · `core.validation`(validate_order_items) · `core.pagination` · `core.security`(bcrypt/JWT) · `core.sse`(publish)
> **활성 확장**: PBT Partial — 강제 규칙 PBT-02·03·07·08·09 (해당 시 적용)

---

## 1. 범위 (Scope)

**백엔드** `backend/app/customer/` (신규) — 계약 §3.1의 4개 엔드포인트:
1. `POST /api/customer/login` — 테이블 자동 로그인, table_token(JWT) 발급
2. `GET  /api/customer/menus` — 카테고리별 메뉴 조회(`is_available=1`만)
3. `POST /api/customer/orders` — 주문 생성(세션 시작·단가/총액 재계산·주문번호 채번·`order.created` SSE 발행)
4. `GET  /api/customer/orders` — 현재 세션 주문 내역(미삭제, 시간순, 페이지네이션)

**프론트엔드** `frontend/customer/` (신규 Vue 앱) — 초기 설정/자동 로그인 · 메뉴 탐색 · 장바구니 · 주문 확정 · 주문 내역

**테스트** — 주문/총액은 core 순수함수 위임, DTO round-trip(PBT-07/08) + 주문 플로우 예제

---

## 2. Functional Design 산출물 계획 (체크박스)

- [x] `business-logic-model.md` — 4개 API의 처리 흐름(로그인 인증→토큰, 주문 생성 트랜잭션: 세션 조회/생성→단가 재계산→주문번호 채번→저장→SSE), 상태 전이, 데이터 흐름
- [x] `business-rules.md` — 고객 유닛 비즈니스 규칙(BR): 인증 규칙, 메뉴 노출 규칙, 주문 검증/재계산 규칙, 세션 시작 규칙, 조회 필터 규칙, 주문번호 채번 규칙
- [x] `domain-entities.md` — Unit 1 공유 엔티티 참조 + Unit 2 관점의 사용(읽기/쓰기 대상, 요청/응답 DTO 매핑)
- [x] `frontend-components.md` — Vue 컴포넌트 계층·props/state·사용자 인터랙션 흐름·폼 검증·API 연동 지점

---

## 3. 설계 확정 질문 (Answer 태그에 A~E 중 선택 또는 자유 기술)

> 각 질문의 `[Answer]:` 뒤에 선택지 문자 또는 내용을 적어주세요. 비워두면 **권장(A)** 로 진행합니다.

### Q1. 자동 로그인 자격증명 저장 위치 (요구사항 3.1.1)
매장식별자/테이블번호/비밀번호를 "최종 로그인 정보 로컬 저장" 한다고 되어 있습니다. 무엇을 저장할까요?
- A. (권장) 최초 1회 로그인 성공 시 받은 **table_token(JWT)** 을 localStorage 에 저장, 이후 토큰으로 자동 인증. 토큰 만료(16h) 시에만 재로그인 화면.
- B. store_code/table_number/password 평문을 localStorage 에 저장하고 앱 시작 시마다 `/login` 자동 호출.
- C. 둘 다 저장(자격증명 + 토큰), 토큰 우선 사용·만료 시 자격증명으로 무인 재로그인.

[Answer]: A — 토큰(JWT)만 localStorage 저장, 이후 토큰으로 자동 인증. 평문 비밀번호 미저장.

### Q2. 토큰 만료/무효 시 UX
table_token 이 만료(401)되면 고객 태블릿은 어떻게 동작할까요?
- A. (권장) Q1=C 방식이면 저장된 자격증명으로 **자동 재로그인**(무인 운영). 실패 시에만 관리자용 설정 화면 노출.
- B. 즉시 초기 설정(재로그인) 화면으로 전환하고 직원 개입 요구.
- C. 만료 무시(데모 목적, MVP에서는 재로그인 처리 생략).

[Answer]: B(원안) — 401 감지 시 초기 설정/재로그인 화면으로 전환, 직원이 자격증명 재입력. (Q1=토큰만 저장과 정합)

### Q3. 메뉴 상세 정보 표시 방식 (요구사항 3.1.2)
메뉴명/가격/설명/이미지 상세를 어떻게 보여줄까요?
- A. (권장) 카드 클릭 시 **모달(다이얼로그)** 로 상세 표시 + 수량 선택 후 장바구니 담기.
- B. 카드에 모든 정보를 항상 노출(상세 화면 없음), 카드에서 바로 담기.
- C. 별도 상세 페이지로 라우팅.

[Answer]: A — 카드 클릭 시 모달로 상세 표시 + 수량 선택 후 장바구니 담기.

### Q4. 장바구니 로컬 저장 범위/키 (요구사항 3.1.3)
새로고침 유지를 위해 localStorage 에 저장합니다. 스코프는?
- A. (권장) `cart:{table_id}` 키로 **테이블별 분리** 저장. 주문 확정/세션 종료 시 해당 키 비움.
- B. 단일 전역 키(`cart`) 하나만 사용.
- C. sessionStorage 사용(탭 종료 시 소멸) — 단, 새로고침 유지 요구와 상충하므로 비권장.

[Answer]: A — cart:{table_id} 키로 테이블별 분리 저장. 주문 확정 시 해당 키 비움.

### Q5. 장바구니 담은 메뉴가 주문 시점에 품절/삭제된 경우 (계약 §3.1.3 에러)
주문 생성 시 서버가 재검증하는데, 일부 메뉴가 `is_available=0` 또는 삭제(404)면?
- A. (권장) **주문 전체 거부**(원자적) — 서버가 409 `MENU_UNAVAILABLE`/404 `MENU_NOT_FOUND` 반환, 프론트는 해당 항목 표시하며 장바구니 유지·수정 유도.
- B. 유효한 항목만 부분 주문 진행하고 품절 항목은 자동 제거.
- C. 프론트에서 메뉴 조회 시점 스냅샷으로 그대로 진행(서버 재검증 최소화) — 비권장.

[Answer]: A — 주문 전체 거부(원자적). **추가 요구**: 서버가 반환한 문제 항목(409 MENU_UNAVAILABLE / 404 MENU_NOT_FOUND)을 프론트가 파싱해 장바구니의 해당 항목에 "품절/판매불가" 배지·표시를 노출하고, 장바구니는 유지하여 고객이 해당 항목 제거 후 재주문하도록 유도. → 이를 위해 서버 에러 응답 `error.details` 에 문제된 menu_id 목록을 포함(계약 §0.2 details 활용, 계약 변경 아님).

### Q6. 주문 내역 실시간 상태 업데이트 (요구사항 3.1.5, "선택사항")
관리자가 주문 상태를 바꾸면(pending→preparing→completed) 고객 화면 반영 방식은?
- A. (권장) MVP는 **수동 새로고침 / 화면 진입 시 재조회** (실시간 미구현). 계약상 고객용 SSE 엔드포인트 없음.
- B. 주기적 폴링(예: 10초마다 `GET /api/customer/orders` 재호출).
- C. 고객용 SSE 엔드포인트를 계약에 추가 요청(Unit 1 계약 변경 필요 → 김주영 협의).

[Answer]: A — MVP는 화면 진입 시 / 수동 새로고침 시 재조회. 실시간 미구현(계약 그대로).

### Q7. 주문번호 당일 시퀀스 채번 소유 (계약 스키마 `order_sequences`)
주문 생성 시 `order_sequences`(store+UTC날짜) 를 원자적으로 증가시켜 seq 를 얻고 `order_number_format` 로 조립합니다. 이 채번 로직은?
- A. (권장) **Unit 2 가 트랜잭션 내에서 직접 구현**(UPSERT + last_seq 증가). 단일 프로세스/SQLite 트랜잭션으로 원자성 보장.
- B. Unit 1 에 `core` 헬퍼(`next_order_number`) 추가 요청 후 호출(공유). → 김주영 협의 필요.

[Answer]: A — Unit 2가 주문 생성 트랜잭션 내에서 직접 채번(UPSERT + last_seq 원자적 증가), order_number_format 로 조립.

### Q8. 프론트엔드 빌드 스택 세부 (Vue)
`frontend/customer/` Vue 앱 구성은?
- A. (권장) **Vue 3 + Vite + Pinia(상태) + Vue Router**, `<script setup>` SFC. fetch 로 API 호출.
- B. Vue 3 + Vite, 상태관리 없이 composable 로만 처리(경량).
- C. 기타(자유 기술).

[Answer]: A — Vue 3 + Vite + Pinia(상태) + Vue Router, <script setup> SFC, fetch 기반 API 클라이언트.

---

## 6. 답변 요약 (인터뷰 완료 — 2026-08-31)
| Q | 결정 | 비고 |
|---|---|---|
| Q1 | 토큰(JWT)만 localStorage 저장 | 평문 비밀번호 미저장 |
| Q2 | 401 시 재로그인 화면 전환 | Q1과 정합(무인 재로그인 없음) |
| Q3 | 카드 클릭 → 모달 상세 + 수량 선택 | |
| Q4 | cart:{table_id} 테이블별 분리 | 주문/세션종료 시 비움 |
| Q5 | 주문 전체 거부(원자) + **프론트 품절 표시** | 서버 `error.details`에 문제 menu_id 목록 포함 |
| Q6 | 진입 시 재조회(실시간 미구현) | 계약 그대로 |
| Q7 | Unit 2가 채번 직접 구현 | order_sequences UPSERT, 트랜잭션 원자성 |
| Q8 | Vue3 + Vite + Pinia + Router | |

**계약 영향**: 없음(모두 기존 `shared/integration-contract.md` 범위 내). Q5의 품절 표시는 `error.details`(기존 optional 필드) 활용 → 계약 변경 아님. 모호 응답 없음 → 후속 질문 불필요, 산출물 생성 진행 가능.

---

## 4. 후속 단계 (승인 후)
- 답변 수집 → 모호한 응답 재확인 → §2 산출물 4종 생성 → Functional Design 완료 메시지(2옵션) 제시
- 이후 NFR(스택 확정으로 SKIP 예정) → Code Generation(Part 1 플랜 → Part 2 구현)

---

## 5. 스토리 추적성
| 요구사항 | 계약 | 산출물 반영 |
|---|---|---|
| 3.1.1 자동 로그인/세션 | §3.1.1 login | business-logic-model(인증 흐름), frontend(자동 로그인) |
| 3.1.2 메뉴 조회/탐색 | §3.1.2 menus | business-rules(노출 규칙), frontend(카드/카테고리/상세) |
| 3.1.3 장바구니 | (클라이언트) | frontend-components(장바구니 상태/로컬저장) |
| 3.1.4 주문 생성 | §3.1.3 orders | business-logic-model(주문 트랜잭션/SSE), business-rules(재계산) |
| 3.1.5 주문 내역 조회 | §3.1.4 orders(GET) | business-rules(세션 필터), frontend(내역 화면) |
