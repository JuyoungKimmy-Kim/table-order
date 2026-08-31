# Code Generation Plan — Unit 1: Foundation & Shared Core

> **담당**: 김주영 · **유닛**: Unit 1 (Foundation & Shared Core)
> **단일 진실 원천**: 이 계획이 Code Generation의 SSOT. 단계는 순서대로 실행하며 완료 즉시 [x] 표기.
> **기준 산출물**: `construction/unit1-foundation/functional-design/*` · `inception/application-design/integration-contract.md`
> **기술 스택(확정)**: Python 3.11+ · FastAPI · sqlite3(표준 라이브러리, Q6=A) · Hypothesis(PBT) · pytest · bcrypt · PyJWT
> **활성 확장**: PBT Partial — 강제 PBT-02·03·07·08·09 (코드 생성 시 반드시 반영)
> **범위(확정)**: 코어 + 모노레포 스캐폴딩 + 시드 데이터 + FastAPI 앱 부트스트랩(health) + shared/ 계약 복사

## 유닛 컨텍스트
- **구현 스토리/책임**: 횡단 기반 — 스키마·도메인 모델·공통 계약·순수 함수·SSE 브로커 (story-map "Unit 1 소유 항목").
- **의존성**: 없음(다른 유닛이 Unit 1에 의존). Unit 1이 먼저 확정되어야 Unit 2~5 병렬 착수 가능.
- **제공 인터페이스**: `backend/app/core/*` 모듈, `shared/` API 계약, SQLite 스키마/마이그레이션.
- **소유 엔티티**: Store, AdminUser, Table, TableSession, Category, Menu, Order, OrderItem, OrderHistory.

## 코드 위치 (aidlc-state.md 기준, 절대 aidlc-docs/ 아님)
- 애플리케이션 코드: 워크스페이스 루트 (`backend/`, `frontend/`, `shared/`)
- 문서(마크다운 요약): `aidlc-docs/construction/unit1-foundation/code/`

```text
table-order/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI 앱 부트스트랩 + /health (부트스트랩만)
│   │   └── core/
│   │       ├── __init__.py
│   │       ├── config.py           # 설정(DB 경로, JWT 상수 16h 등)
│   │       ├── db.py               # sqlite3 연결/트랜잭션 컨텍스트, 스키마 적용
│   │       ├── models.py           # 엔티티 dataclass + DTO(OrderSummary/OrderDetail) 직렬화
│   │       ├── domain.py           # 순수 함수 4종 + parse_order_number
│   │       ├── errors.py           # 표준 에러 포맷 + 도메인 예외 + FastAPI 핸들러
│   │       ├── validation.py       # 검증 헬퍼 (BR-9)
│   │       ├── security.py         # bcrypt 해싱/검증, JWT 발급/검증 유틸
│   │       ├── sse.py              # SSE 브로커: publish/subscribe (asyncio 기반)
│   │       └── pagination.py       # page/size 정규화 + 응답 래퍼
│   ├── migrations/
│   │   ├── 0001_initial_schema.sql # 9개 테이블 + 부분 유니크 인덱스
│   │   └── seed.sql                # 시드: 매장 1, 관리자 1, 테이블 몇 개, 카테고리/메뉴 샘플
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── generators.py           # PBT-07 도메인 제너레이터 (중앙화)
│   │   ├── test_domain_pbt.py      # PBT-02/03: 순수 함수 속성 테스트
│   │   ├── test_dto_roundtrip_pbt.py # PBT-02/07/08: DTO round-trip
│   │   ├── test_domain_examples.py # PBT-10: 예제 기반 테스트(핵심 시나리오 고정)
│   │   └── conftest.py             # 임시 DB fixture, Hypothesis 프로파일(seed/CI)
│   ├── requirements.txt            # fastapi, uvicorn, pydantic, bcrypt, pyjwt, pytest, hypothesis
│   ├── pytest.ini                  # Hypothesis 프로파일 등록(PBT-08)
│   └── README.md                   # backend 실행/테스트 방법
├── shared/
│   └── integration-contract.md     # 계약 사본(전 유닛 참조용, SSOT는 aidlc-docs 원본 링크)
├── frontend/
│   ├── customer/.gitkeep           # Unit 2 소유(빈 디렉토리)
│   └── admin/.gitkeep              # Unit 3/4/5 소유(빈 디렉토리)
└── README.md                       # 모노레포 개요 + 유닛 배정 + 실행 가이드
```

---

## 생성 단계 (번호별, 순서 실행)

- [x] **Step 1. 모노레포 스캐폴딩** — 디렉토리 트리, 루트/backend README, .gitkeep, shared/ 계약 사본, requirements.txt, pytest.ini, __init__.py.
- [x] **Step 2. DB 마이그레이션 스크립트** — `0001_initial_schema.sql`: 9테이블 + CHECK/UNIQUE + active 세션 부분 유니크 인덱스 + order_history/items + order_sequences.
- [x] **Step 3. 설정 & DB 접근 계층** — `config.py`, `db.py`(connect/transaction/apply_migrations/apply_seed).
- [x] **Step 4. 순수 함수(domain.py)** — 4종 + parse_order_number. 부작용 없음.
- [x] **Step 5. 순수 함수 PBT** — generators.py + test_domain_pbt.py + conftest.py(프로파일). PBT-02/03/07/08.
- [x] **Step 6. 모델 & DTO(models.py)** — 엔티티 dataclass + OrderSummary/OrderDetail + line_total.
- [x] **Step 7. DTO round-trip PBT** — test_dto_roundtrip_pbt.py. PBT-02/07/08.
- [x] **Step 8. 공통 유틸** — errors/validation/pagination/security.
- [x] **Step 9. SSE 브로커(sse.py)** — publish/subscribe/format_sse, 전역 broker.
- [x] **Step 10. 예제 기반 테스트** — test_domain_examples.py. PBT-10.
- [x] **Step 11. FastAPI 앱 부트스트랩** — main.py + /health + lifespan 마이그레이션.
- [x] **Step 12. 시드 데이터** — `migrations/seed.py`(bcrypt 해시 런타임 생성, 멱등). ※ seed.sql→seed.py 조정.
- [x] **Step 13. 문서 생성** — backend/README.md, 루트 README.md, code/code-summary.md.

**검증**: pytest 24 passed (default & ci 프로파일), seed 정상, /health 200.

---

## PBT 준수 매핑 (코드 생성 시 강제)
| 규칙 | 반영 단계 | 내용 |
|---|---|---|
| PBT-02 (round-trip) | Step 5, 7 | order_number format↔parse, DTO serialize↔deserialize |
| PBT-03 (invariant) | Step 5, 7 | 비음수·순서무관·삭제제외·closed→False·형식불변·line_total 합 |
| PBT-07 (generator) | Step 5 | 도메인 제너레이터 중앙화(st_money/quantity/order/seq/date) |
| PBT-08 (shrink/재현) | Step 5 | Hypothesis shrinking 유지, seed 로깅/CI 프로파일 |
| PBT-09 (framework) | Step 1 | requirements.txt에 hypothesis 포함, pytest 통합 |
| PBT-10 (complementary) | Step 10 | 예제 기반 테스트 병행 |

## 스토리 추적성
- Unit 1은 특정 3.1.x/3.2.x 스토리가 아닌 횡단 기반 소유. 각 단계는 story-map "Unit 1 소유 산출물"(도메인 모델·OrderHistory·세션/총액 규칙·SSE 계약·스키마/계약/에러포맷/스캐폴딩)에 대응.

## 총 규모
- 13개 단계. 애플리케이션 파일 약 20여 개(core 9 + tests 5 + migrations 2 + 앱/설정/문서). 다른 유닛의 착수 전제.
