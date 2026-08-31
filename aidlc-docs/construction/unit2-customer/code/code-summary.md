# Code Summary — Unit 2: Customer Ordering (전체)

> **담당**: 박찬준 · **요구사항**: 3.1.1 ~ 3.1.5 · **계약**: `shared/integration-contract.md` §3.1
> **상태**: 코드 생성 완료 · 백엔드 40 테스트 통과 · 프론트 빌드 성공.

## 산출물
### 백엔드 (`backend/app/customer/`)
`__init__.py` · `schemas.py` · `auth.py` · `repository.py` · `service.py` · `router.py`
+ `app/main.py` 라우터 등록. → 상세 `backend-summary.md`.

### 테스트 (`backend/tests/`)
`test_customer_dto_pbt.py`(DTO PBT) · `test_customer_api.py`(TestClient 통합 16케이스). → `test-summary.md`.

### 프론트엔드 (`frontend/customer/`)
Vite+Vue3+Pinia+Router 앱(뷰 4 + 컴포넌트 10 + 스토어 3 + api client). → `frontend-summary.md`.

## 엔드포인트 (계약 §3.1)
| 메서드 | 경로 | 규칙 |
|---|---|---|
| POST | `/api/customer/login` | BR-C1 3요소 검증 → table_token |
| GET | `/api/customer/menus` | BR-C2 is_available=1만, 정렬 |
| POST | `/api/customer/orders` | BR-C4 재검증·서버 총액 재계산·세션 시작·채번·`order.created` SSE |
| GET | `/api/customer/orders` | BR-C5 현재 세션·미삭제·시간순·페이지네이션 |

## 검증 결과
- 백엔드: `python -m pytest` **40 passed** (default & `HYPOTHESIS_PROFILE=ci`). Unit 1 회귀 없음.
- 프론트: `npm run build` 성공(47 modules).

## 생성 중 수정한 결함 2건 (통합 검증으로 조기 발견)
1. **JWT sub 타입** — 정수 sub 저장 → PyJWT 2.10+ 디코드 검증 실패(인증 401). → `sub=str(id)` + `auth.py` `int()` 복원.
2. **sqlite 스레드 교차** — async 엔드포인트 + sync 연결 의존성 조합 오류. → `router.py` 연결 의존성/엔드포인트 async 통일.

## 계약/의존성
- **계약 변경 없음**. 품절/미존재 시 기존 `error.details`(선택 필드) 활용.
- **신규 마이그레이션 없음** — 모든 테이블은 Unit 1 소유·기존 스키마.
- **재사용**: Unit 1 core 8모듈(db/domain/models/errors/validation/pagination/security/sse).
- **발행만**: `order.created` SSE (구독은 Unit 3). 병렬 개발과 충돌 없음.

## 실행 (개발)
```bash
# 백엔드
cd backend && python -m migrations.seed && uvicorn app.main:app --reload   # :8000
# 프론트
cd frontend/customer && npm install && npm run dev                          # :5173 (/api → :8000 프록시)
# 로그인: STORE001 / 테이블 1~3 / 1234
```

## 미해결/후속(범위 밖)
- 환경: Python 3.14 로 인해 `requirements.txt` 핀 버전(pydantic 2.10.3 등)이 소스빌드에 실패 →
  로컬 검증은 3.14 호환 버전(pydantic 2.12.5/fastapi 0.141/PyJWT 2.13 등)으로 수행. 핀 버전 정비는 Unit 1(공용 requirements) 소관으로 협의 필요.
