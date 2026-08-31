# Backend Code Summary — Unit 2: Customer Ordering

> **담당**: 박찬준 · 위치: `backend/app/customer/`

## 생성 모듈
| 파일 | 역할 |
|---|---|
| `__init__.py` | 패키지 문서 |
| `schemas.py` | 요청/응답 pydantic 모델(Login/CreateOrder). 상세는 core.models 재사용 |
| `auth.py` | `get_table_context` — Bearer table_token 검증 의존성(BR-C1.4/5) |
| `repository.py` | SQLite 접근(core.db). 조회/세션/채번(UPSERT)/주문 INSERT/내역 |
| `service.py` | BR-C 로직. 주문 생성 단일 트랜잭션 + 커밋 후 SSE 발행 |
| `router.py` | 4개 엔드포인트, service 위임, 요청별 커넥션 의존성 |
| `app/main.py` | (수정) customer_router include (`/api`) |

## 엔드포인트 (계약 §3.1)
| 메서드 | 경로 | 인증 | 규칙 |
|---|---|---|---|
| POST | `/api/customer/login` | 없음 | BR-C1: 3요소 검증, table_token 발급 |
| GET | `/api/customer/menus` | table_token | BR-C2: is_available=1만, 정렬 |
| POST | `/api/customer/orders` | table_token | BR-C4: 재검증·서버 총액 재계산·세션시작·채번·SSE |
| GET | `/api/customer/orders` | table_token | BR-C5: 현재 세션·미삭제·시간순·페이지네이션 |

## 핵심 설계 포인트
- **신뢰 경계**: 단가/메뉴명은 서버가 메뉴 마스터에서 재조회·스냅샷. 클라 값 불신.
- **총액**: `domain.calc_order_total` 위임(직접 계산 없음).
- **주문번호**: `order_sequences` UPSERT 로 당일 시퀀스 원자 증가 → `domain.order_number_format("A", date, seq)`.
- **세션**: active 없으면 생성(부분 유니크 인덱스가 최대 1개 보장).
- **품절/미존재(Q5)**: 전체 거부(원자) + `error.details.{not_found_menu_ids|unavailable_menu_ids}` 로 프론트 품절 표시 지원. 계약 §0.2 details 활용(계약 변경 아님).
- **SSE**: 커밋 이후 `order.created`(OrderSummary) 발행(BR-C4.8).

## 재사용 (Unit 1 core)
db, domain(calc_order_total/order_number_format), models(OrderDetail/OrderSummary/OrderItemDetail/make_item_preview), errors(Unauthorized/MenuNotFound/MenuUnavailable/AppError), validation(validate_order_items), pagination(normalize/offset/paginate_response), security(verify_password/create_token/decode_token), sse(publish).

## 신규 마이그레이션
없음 — 모든 테이블은 Unit 1 소유·기존 스키마 사용.
