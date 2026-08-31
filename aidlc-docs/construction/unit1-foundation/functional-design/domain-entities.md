# Domain Entities — Unit 1: Foundation & Shared Core

> **소유**: Unit 1 (김주영). 아래 엔티티는 전 유닛이 공유한다.
> **기준**: `inception/application-design/integration-contract.md` §1. 본 문서는 스키마를 **도메인 관점**으로 정의한다(속성 의미·관계·불변식). 물리 DDL은 Code Generation의 마이그레이션에서 생성.
> **결정 반영**: Q1~Q6 = 모두 A.

## 공통 규약
- 모든 엔티티: `id INTEGER PK AUTOINCREMENT`, `created_at`/`updated_at` (UTC ISO8601 문자열).
- 금액: **정수(원 단위)**. 부동소수점 미사용.
- 시각: **UTC ISO8601 문자열**.
- 단일 매장 가정: `store_id`는 모든 엔티티에 존재하나 MVP에서는 단일 값 고정.

## 열거형 (공유 enum)
| enum | 값 | 의미 |
|---|---|---|
| `OrderStatus` | `pending` / `preparing` / `completed` | 대기중 / 준비중 / 완료 |
| `SessionStatus` | `active` / `closed` | 이용 중 / 이용 완료 |

---

## 엔티티 정의

### 1. Store (매장)
| 속성 | 타입 | 제약 | 의미 |
|---|---|---|---|
| id | int | PK | |
| store_code | str | UNIQUE, NOT NULL | 매장 식별자 (예: `STORE001`) |
| name | str | NOT NULL | 매장명 |

- **관계**: 1 Store ─< AdminUser, Table, Category, Menu (모든 하위 엔티티의 루트)

### 2. AdminUser (관리자 계정)
| 속성 | 타입 | 제약 | 의미 |
|---|---|---|---|
| id | int | PK | |
| store_id | int | FK → Store | |
| username | str | NOT NULL, UNIQUE(store_id, username) | 로그인 사용자명 |
| password_hash | str | NOT NULL | **bcrypt** 해시 |

- **소비**: Unit 3(관리자 인증). Unit 1은 스키마·해싱 헬퍼만 제공.

### 3. Table (테이블)
| 속성 | 타입 | 제약 | 의미 |
|---|---|---|---|
| id | int | PK | |
| store_id | int | FK → Store | |
| table_number | int | NOT NULL, UNIQUE(store_id, table_number) | 테이블 번호 |
| password_hash | str | NOT NULL | 테이블 비밀번호 (bcrypt) |

- **관계**: 1 Table ─< TableSession (시간에 따라 여러 세션)
- **소비**: Unit 4(초기 설정), Unit 2(자동 로그인 인증)

### 4. TableSession (테이블 세션)
| 속성 | 타입 | 제약 | 의미 |
|---|---|---|---|
| id | int | PK | |
| table_id | int | FK → Table | |
| status | `SessionStatus` | NOT NULL | `active` \| `closed` |
| opened_at | str | NOT NULL | 첫 주문 시각 |
| closed_at | str | NULL | 이용 완료 시각 (active일 때 NULL) |

- **불변식 (Q3=A)**: 한 테이블에 `status='active'` 세션은 **최대 1개**. DB 부분 유니크 인덱스로 강제.
  `CREATE UNIQUE INDEX ux_active_session ON table_sessions(table_id) WHERE status = 'active';`
- **관계**: 1 TableSession ─< Order

### 5. Category (메뉴 카테고리)
| 속성 | 타입 | 제약 | 의미 |
|---|---|---|---|
| id | int | PK | |
| store_id | int | FK → Store | |
| name | str | NOT NULL | 카테고리명 |
| display_order | int | NOT NULL, DEFAULT 0 | 노출 순서(오름차순) |

- **소유**: Unit 5(관리). 정렬은 `display_order ASC, id ASC`.

### 6. Menu (메뉴)
| 속성 | 타입 | 제약 | 의미 |
|---|---|---|---|
| id | int | PK | |
| store_id | int | FK → Store | |
| category_id | int | FK → Category | |
| name | str | NOT NULL | 메뉴명 |
| price | int | NOT NULL, CHECK(price >= 0) | 가격(원) |
| description | str | NULL | 설명 |
| image_url | str | NULL | 이미지 URL |
| display_order | int | NOT NULL, DEFAULT 0 | 노출 순서 |
| is_available | int(bool) | NOT NULL, DEFAULT 1 | 1=노출, 0=숨김 |

- **삭제 방식 (Q5=A)**: 물리 삭제 허용. 소프트삭제 컬럼 없음 — 주문 항목이 스냅샷(§8)이라 과거 주문에 영향 없음.
- **소유**: Unit 5(CRUD). 소비: Unit 2(고객 조회, `is_available=1`만).

### 7. Order (주문)
| 속성 | 타입 | 제약 | 의미 |
|---|---|---|---|
| id | int | PK | |
| session_id | int | FK → TableSession | 소속 세션 |
| table_id | int | FK → Table | 조회 편의용(비정규화) |
| order_number | str | UNIQUE, NOT NULL | 표시용 주문번호 (§Q1 형식) |
| status | `OrderStatus` | NOT NULL, DEFAULT `pending` | |
| total_amount | int | NOT NULL | 주문 총액 스냅샷 = Σ(item.unit_price × quantity) |
| is_deleted | int(bool) | NOT NULL, DEFAULT 0 | 직권 삭제 플래그(Unit 4) |
| ordered_at | str | NOT NULL | 주문 시각 |

- **주문번호 형식 (Q1=A, Q2=A)**: `{접두사 'A'}-{YYYYMMDD(UTC)}-{당일 시퀀스 4자리}` 예: `A-20260831-0007`.
  시퀀스는 매장+UTC 날짜 단위로 리셋, 하루 최대 9999건.
- **총액 (Q4=A)**: `total_amount`는 주문 확정 시점의 스냅샷. 테이블 현재 총액은 저장하지 않고 미삭제 주문의 `total_amount` 합으로 실시간 계산(`calc_table_total`).
- **관계**: 1 Order ─< OrderItem

### 8. OrderItem (주문 항목)
| 속성 | 타입 | 제약 | 의미 |
|---|---|---|---|
| id | int | PK | |
| order_id | int | FK → Order | |
| menu_id | int | FK → Menu | 참조용(삭제돼도 스냅샷 유지) |
| menu_name | str | NOT NULL | **주문 시점 메뉴명 스냅샷** |
| unit_price | int | NOT NULL | **주문 시점 단가 스냅샷** |
| quantity | int | NOT NULL, CHECK(quantity > 0) | 수량 |

- **스냅샷 원칙**: `menu_name`, `unit_price`를 주문 시점 값으로 복사 저장. 이후 메뉴 변경/삭제(Unit 5)에 영향받지 않음.

### 9. OrderHistory (과거 주문 이력)
- 세션 종료(이용 완료) 시 이동된 주문 이력. `Order`와 **동일 컬럼** + 아래 추가.

| 추가 속성 | 타입 | 의미 |
|---|---|---|
| session_closed_at | str | 세션 종료 시각 |
| store_id | int | 매장 식별(조회 편의) |

- **구현 기준(계약 §1.9)**: 별도 테이블(`order_history`)로 물리 이동. 항목(OrderItem)도 함께 이동하거나, 이력 전용 항목 테이블(`order_history_items`)로 복사. → business-logic-model에서 상세.
- **소유**: Unit 1 스키마. 이동 로직 트리거는 Unit 4(세션 종료), 조회는 Unit 4(§3.3.5).

---

## 엔티티 관계도 (텍스트)

```text
Store (1)
 ├─< AdminUser
 ├─< Table (1) ─< TableSession (1) ─< Order (1) ─< OrderItem
 ├─< Category (1) ─< Menu
 └─< (OrderHistory: 종료된 세션의 Order 스냅샷 이동본)

Order.total_amount = Σ(OrderItem.unit_price × OrderItem.quantity)   # 주문 스냅샷
Table 현재 총액    = Σ(active 세션의 미삭제 Order.total_amount)      # 실시간 계산 (Q4=A)
```

## 소유권 요약
| 엔티티 | 스키마 소유 | 주요 소비 유닛 |
|---|---|---|
| Store, AdminUser | Unit 1 | Unit 3 |
| Table, TableSession | Unit 1 | Unit 2, Unit 3, Unit 4 |
| Category, Menu | Unit 1 | Unit 5(쓰기), Unit 2(읽기) |
| Order, OrderItem | Unit 1 | Unit 2(생성), Unit 3(상태), Unit 4(삭제/종료) |
| OrderHistory | Unit 1 | Unit 4 |
