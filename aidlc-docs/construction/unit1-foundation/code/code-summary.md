# Code Generation Summary — Unit 1: Foundation & Shared Core

> **담당**: 김주영 · **상태**: 코드 생성 완료, 테스트 24개 통과 (default/ci 프로파일)
> **목적**: 계약+코어 확정 → Unit 2~5 병렬 착수 가능 상태 도달.

## 생성 파일 (Greenfield — 모두 신규 생성)

### 애플리케이션 코드 (backend/)
| 경로 | 내용 |
|---|---|
| `backend/app/main.py` | FastAPI 부트스트랩, 에러 핸들러 등록, 시작 시 마이그레이션, `GET /health` |
| `backend/app/core/config.py` | 설정(DB 경로, JWT 16h 상수, 페이지네이션, 주문번호 접두사) |
| `backend/app/core/db.py` | sqlite3 연결/트랜잭션 컨텍스트, `apply_migrations`/`apply_seed` (ORM 없음, Q6=A) |
| `backend/app/core/domain.py` | **순수 함수 4종** + `parse_order_number` (PBT 대상) |
| `backend/app/core/models.py` | 엔티티 dataclass + `OrderSummary`/`OrderDetail` DTO(직렬화) |
| `backend/app/core/errors.py` | 표준 에러 포맷 + 도메인 예외 + FastAPI 핸들러 |
| `backend/app/core/validation.py` | 검증 헬퍼(BR-9): 메뉴/주문항목/상태 |
| `backend/app/core/pagination.py` | page/size 정규화 + 응답 래퍼(§0.4) |
| `backend/app/core/security.py` | bcrypt 해싱/검증, JWT 발급/검증(16h) |
| `backend/app/core/sse.py` | SSE 브로커 `publish`/`subscribe` + 프레임 직렬화(§2) |
| `backend/migrations/0001_initial_schema.sql` | 9개 테이블 + active 세션 부분 유니크 인덱스 + 시퀀스 테이블 |
| `backend/migrations/seed.py` | 개발/데모 시드(bcrypt 해시 런타임 생성, 멱등) |

### 테스트 (backend/tests/)
| 경로 | 내용 | PBT |
|---|---|---|
| `tests/generators.py` | 도메인 제너레이터 중앙화 | PBT-07 |
| `tests/test_domain_pbt.py` | 순수함수 속성(비음수/순서무관/삭제제외/closed→False/round-trip/형식) | PBT-02, 03 |
| `tests/test_dto_roundtrip_pbt.py` | DTO round-trip + line_total 합 일관성 | PBT-02, 07, 08 |
| `tests/test_domain_examples.py` | 예제 기반 시나리오 고정 | PBT-10 |
| `tests/conftest.py` | Hypothesis 프로파일(default/ci) + tmp DB fixture | PBT-08 |

### 스캐폴딩 / 설정 / 문서
| 경로 | 내용 |
|---|---|
| `backend/requirements.txt` | fastapi, uvicorn, pydantic, bcrypt, PyJWT, pytest, **hypothesis**, httpx |
| `backend/pytest.ini` | pytest 설정 |
| `backend/README.md` | 설치/실행/시드/테스트/코어 사용법 |
| `shared/integration-contract.md` | 계약 사본(전 유닛 참조, SSOT는 aidlc-docs 원본) |
| `frontend/customer/.gitkeep`, `frontend/admin/.gitkeep` | Unit 2/3/4/5 프론트 자리 |
| `README.md` (루트) | 모노레포 개요 + 유닛 배정 + 병렬 개발 규칙 |

## 계획 대비 변경점
- **seed.sql → seed.py**: 비밀번호 bcrypt 해시가 필요해 SQL 하드코딩 대신 파이썬 스크립트로 런타임 해시 생성(멱등). 스키마 DDL은 예정대로 `0001_initial_schema.sql`.

## 검증 결과
- `pytest`: **24 passed** (default 프로파일)
- `HYPOTHESIS_PROFILE=ci pytest`: **24 passed** (고정 seed, 재현 가능)
- `python -m migrations.seed`: 정상 (store 1 / admin 1 / tables 3 / categories 3 / menus 5)
- `GET /health` → 200 `{"status":"ok"}`

## 다른 유닛(2~5)이 즉시 쓸 수 있는 것
1. `shared/integration-contract.md` — API/스키마/이벤트 계약(SSOT).
2. `app.core.domain` — 총액/세션/주문번호 순수 함수(직접 계산 금지).
3. `app.core.db` — 연결/트랜잭션.
4. `app.core.models` — 공유 DTO.
5. `app.core.errors` / `validation` / `pagination` / `security` — 공통 유틸.
6. `app.core.sse.publish` — 이벤트 발행(발행 유닛), `subscribe` — 구독(Unit 3).
7. `app.main.app` — 각 유닛 라우터를 `include_router(prefix="/api")` 로 결합.

## PBT Compliance (Code Generation)
| 규칙 | 상태 | 근거 |
|---|---|---|
| PBT-02 round-trip | ✅ | order_number format↔parse, DTO serialize↔deserialize |
| PBT-03 invariant | ✅ | 비음수/순서무관/삭제제외/closed→False/형식/line_total 합 |
| PBT-07 generator | ✅ | `tests/generators.py` 중앙화, 도메인 제약 반영 |
| PBT-08 shrink/재현 | ✅ | Hypothesis shrinking 유지, ci 프로파일 derandomize+print_blob |
| PBT-09 framework | ✅ | hypothesis 의존성 포함, pytest 통합 |
| PBT-10 complementary | ✅ | 예제 기반 테스트 병행(advisory이나 충족) |
| PBT-04/05/06 | N/A | idempotency/oracle/stateful — 현 코어 순수함수에 해당 없음 |
