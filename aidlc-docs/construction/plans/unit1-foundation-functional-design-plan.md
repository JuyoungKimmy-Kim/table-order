# Functional Design Plan — Unit 1: Foundation & Shared Core

> **담당**: 김주영 · **유닛**: Unit 1 (Foundation & Shared Core)
> **기준 문서**: `inception/application-design/integration-contract.md` (Single Source of Truth)
> **활성 확장**: PBT Partial (강제: PBT-02, PBT-03, PBT-07, PBT-08, PBT-09) · Security/Resiliency 비활성
> **기술 스택(확정)**: Python · FastAPI · sqlite3(표준 라이브러리) · Hypothesis(PBT) · SSE · 모노레포

## 목적
Integration Contract가 스키마·API·이벤트를 이미 상세 정의했으므로, 본 Functional Design은 **Unit 1이 코어 모듈로 제공하는 도메인 로직·비즈니스 규칙·PBT 속성 식별(PBT-01)** 에 집중한다. 개별 유닛의 화면/플로우는 각 유닛 소유이므로 다루지 않는다.

---

## 계획 단계 (체크박스)

- [x] **P1. 도메인 엔티티 모델링** — domain-entities.md 생성 (9개 엔티티 + enum + 관계도 + 소유권).
- [x] **P2. 비즈니스 규칙 정의** — business-rules.md 생성 (BR-1~BR-11).
- [x] **P3. PBT 대상 순수 함수 계약 & 속성 식별 (PBT-01)** — business-logic-model §2, §6 Testable Properties.
- [x] **P4. 공통 유틸 설계** — business-logic-model §1(코어 모듈), §4 errors, §5 DTO.
- [x] **P5. Functional Design 산출물 생성** — 3개 문서 생성 (UI 없음 → frontend-components 생략).
- [x] **P6. PBT 준수 요약 & 완료 메시지** — PBT-01 충족(§6 Testable Properties), 완료 메시지 제시.

---

## 확인 질문 (Functional Design)

아래 각 항목의 `[Answer]:` 뒤에 답을 적어주세요. 답이 없으면 괄호 안 **기본값(권장)** 으로 진행합니다.

### Q1. 주문번호(order_number) 생성 형식
Integration Contract §4.1 예시는 `A-20260831-0007` 형식입니다. 이 형식의 규칙을 확정하고 싶습니다.
- A) `{접두사 1글자}-{YYYYMMDD}-{당일 4자리 시퀀스}` (예: `A-20260831-0007`) — 접두사는 고정 문자 `A`
- B) 접두사 없이 `{YYYYMMDD}-{시퀀스}`
- C) 단순 전역 시퀀스(예: UUID 또는 순번)

[Answer]: A

### Q2. 당일 시퀀스 범위
Q1에서 시퀀스를 쓴다면, 그 카운터의 리셋/유일성 기준은?
- A) 매장(store) + UTC 날짜 단위로 리셋 (하루 최대 9999건 = 4자리)
- B) 테이블 단위로 리셋
- C) 전역(리셋 없음, 계속 증가)

[Answer]: A (매장+UTC 날짜별 리셋)

### Q3. 세션-주문 정합성: active 세션이 없을 때 주문 생성
§0.5는 "active 세션 없으면 첫 주문 시 새 세션 생성"입니다. 동시성(같은 테이블에서 거의 동시에 2건 주문) 상황에서 세션 중복 생성을 어떻게 막을까요?
- A) DB 레벨 제약 + 트랜잭션 내 "active 세션 조회 후 없으면 생성"을 원자적으로 처리 (UNIQUE 부분 인덱스: table_id WHERE status='active')
- B) 애플리케이션 레벨 락(단일 프로세스 가정, 소규모라 충분)
- C) 신경 쓰지 않음(데모 범위)

[Answer]: A (부분 유니크 인덱스로 테이블당 active 세션 1개 보장)

### Q4. 총액 재계산의 진실 원천
테이블 현재 총액을 어디서 계산할까요?
- A) 항상 미삭제 주문들의 `total_amount` 합을 실시간 계산 (별도 저장 필드 없음) — 단순·정합성 안전
- B) 테이블에 캐시 컬럼을 두고 주문/삭제 시 갱신 — 성능 우선

[Answer]: A (실시간 계산, `calc_table_total`이 진실 원천)

### Q5. 메뉴 삭제 방식 (Unit 5가 소비하지만 스키마는 Unit 1 소유)
Integration Contract §3.4.4는 메뉴 삭제 `204`입니다. 물리 삭제 vs 소프트 삭제?
- A) 소프트 삭제 없이 물리 삭제 허용 (주문 항목은 스냅샷이라 영향 없음, §1.8) — 스키마 단순
- B) `is_deleted` 소프트 삭제 컬럼 추가

[Answer]: A (물리 삭제, 스냅샷 원칙에 근거)

### Q6. DB 접근 계층 스타일
Unit 1이 제공할 공통 DB 접근 계층 형태는?
- A) 경량 Repository 함수 + `sqlite3` 직접 사용(ORM 없음) — 워크숍/데모에 가볍고 명시적
- B) SQLAlchemy Core/ORM 도입

[Answer]: A (sqlite3 경량 Repository, ORM 없음)

---

**답변 완료 후** 모호성 점검(Step 5) → 이상 없으면 Functional Design 산출물 생성(Step 6)으로 진행합니다.
