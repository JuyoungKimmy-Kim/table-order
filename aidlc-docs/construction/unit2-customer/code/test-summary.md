# Test Summary — Unit 2: Customer Ordering

> **담당**: 박찬준 · 위치: `backend/tests/` · 실행: `cd backend && python -m pytest`

## 결과 (검증 완료)
- **Unit 2 신규 테스트**: 16개 통과 (`test_customer_api.py` 13 + `test_customer_dto_pbt.py` 3 그룹)
- **전체 백엔드 스위트**: **40 passed** — default 프로파일 & `HYPOTHESIS_PROFILE=ci`(derandomized) 양쪽 그린. Unit 1 회귀 없음.
- 실행 환경: Python 3.14, FastAPI TestClient(httpx), Hypothesis.

## 테스트 파일
| 파일 | 유형 | 대상 |
|---|---|---|
| `test_customer_dto_pbt.py` | PBT (property) | `OrderDetail`/`OrderItemDetail` to_dict↔from_dict round-trip, `line_total`·`total_amount` 일관성 |
| `test_customer_api.py` | 통합 예제 (TestClient + tmp DB + seed) | 4개 엔드포인트 계약·비즈니스 규칙 |

## 커버리지 (BR-C 매핑)
| 규칙/요구사항 | 케이스 |
|---|---|
| BR-C1 로그인 | 성공(계약 필드) · 오답 비밀번호 401 · 미존재 매장 401 |
| BR-C1.4 인증 | 토큰 없는 `/menus`·`/orders` 401 |
| BR-C2 메뉴 | `is_available=0` 제외, 나머지 노출 |
| BR-C4 주문 생성 | 201·필드 · 서버 총액 재계산(클라 단가 미신뢰) · 주문번호 `A-YYYYMMDD-0001` · 당일 시퀀스 증가(0001→0002) · `order.created` SSE 발행 |
| BR-C4.1 검증 | 빈 items 400 VALIDATION_ERROR |
| BR-C4.2 재검증 | 미존재 404 MENU_NOT_FOUND(+`details.not_found_menu_ids`) · 품절 409 MENU_UNAVAILABLE(+`details.unavailable_menu_ids`) |
| BR-C5 내역 | 세션 없음→빈 목록 · ordered_at ASC 정렬 · soft-delete 제외 · 페이지네이션(page/size/total) |

## PBT 규칙 준수 (활성: PBT Partial)
| 규칙 | 준수 | 근거 |
|---|---|---|
| PBT-02 (round-trip 속성) | ✅ | DTO 직렬화↔역직렬화 동등성, 총액=Σline_total 불변식 |
| PBT-03 (경계/대표 입력) | ✅ | `st_money`(0~10M)·`st_quantity`(1~99)·다양한 status/항목 수 |
| PBT-07 (제너레이터 재사용) | ✅ | `tests/generators.py` 의 `st_money`/`st_quantity` 재사용 |
| PBT-08 (재현성) | ✅ | `conftest.py` `ci` 프로파일 derandomize=True, print_blob=True 로 실행 확인 |
| PBT-09 (도메인 계산 위임 검증) | ✅ | 총액은 `domain.calc_order_total` 위임을 속성으로 확인(직접 계산 금지 원칙 반영) |

## 통합 검증에서 발견·수정한 결함 2건
1. **JWT sub 타입** — `service.login` 이 `sub` 를 정수로 저장 → PyJWT 2.10+ 디코드 검증(sub=문자열) 실패로 인증 전면 401. 수정: `sub=str(table_id)` 저장 + `auth.py` 에서 `int()` 복원.
2. **sqlite 스레드 교차** — async `create_order` 엔드포인트 + sync `get_conn` 의존성 조합에서 연결이 스레드풀에서 생성되어 이벤트 루프 스레드에서 사용 → `sqlite3.ProgrammingError`. 수정: `router.py` 의 `get_conn` 및 4개 엔드포인트를 모두 `async` 로 통일.

## 수동 스모크 (참고)
`python -m migrations.seed` 후 `uvicorn app.main:app` → 로그인(테이블 1/`1234`) → `/api/customer/menus` → 주문 생성 → `/api/customer/orders` 내역 확인.
