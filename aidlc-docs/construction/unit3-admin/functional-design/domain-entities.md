# Domain Entities — Unit 3: Admin Auth & Real-time Monitoring (임동규)

> **소유**: Unit 3 (임동규). **범위**: 요구사항 3.2.1(매장 인증) / 3.2.2(실시간 주문 모니터링).
> **기준**: Integration Contract §0.3, §1.2, §2, §3.2, §4. 결정 Q1~Q9 = 전부 A(기본값).
> **원칙**: 영속 데이터 모델(테이블)은 **Unit 1 소유** — 재정의하지 않고 **재사용**만 한다. 본 문서는 Unit 3이 다루는 (a) 재사용 엔티티, (b) Unit 3 전용 런타임/뷰모델 구조를 정의한다.

---

## 1. 재사용 엔티티 (Unit 1 소유 — 참조만)

| 엔티티 | 출처 | Unit 3 사용처 |
|---|---|---|
| `AdminUser` (§1.2: id, store_id, username, password_hash) | Unit 1 `app.core.models` / `admin_users` 테이블 | 로그인 인증(bcrypt 검증), JWT claims 소스 |
| `Store` (§1.1: id, store_code, name) | Unit 1 | 로그인 시 `store_code`→`store_id` 조회, `store_name` 응답 |
| `Table` (§1.3) | Unit 1 | 대시보드 카드 구성(테이블 목록) |
| `TableSession` (§1.4: status active/closed) | Unit 1 | 카드의 `session_active`, 현재 총액 산정 대상 세션 판별 |
| `Order` (§1.7: status, total_amount, is_deleted, ordered_at) | Unit 1 | 상태 변경 대상, 카드 `recent_orders`, 상세 조회 |
| `OrderItem` (§1.8) | Unit 1 | 주문 상세(OrderDetail) 항목 |
| `OrderStatus` enum: `pending`/`preparing`/`completed` (§1.10) | Unit 1 | 상태 변경 검증, 필터 |

> Unit 3은 위 테이블에 **스키마를 추가/변경하지 않는다**. 상태 변경(§3.2.5)은 `orders.status` 컬럼 UPDATE만 수행.

---

## 2. Unit 3 전용 런타임 구조 (비영속)

### 2.1 `LoginAttemptTracker` (Q1=A, Q2=A) — 인메모리
로그인 시도 제한 상태. **프로세스 인메모리**(딕셔너리), 재시작 시 리셋 허용.

| 키 | 값 |
|---|---|
| key = `(store_code, username)` | `AttemptState { fail_count: int, locked_until: datetime \| None }` |

- 정책(Q1=A): **연속 5회 실패 → 5분 잠금**. 로그인 성공 시 해당 key 상태 삭제(리셋).
- 잠금 중 요청은 인증 시도 없이 `429 TOO_MANY_ATTEMPTS`.
- 단일 프로세스·소규모 가정(계약 §0 규모). 다중 워커 확장은 범위 외.

### 2.2 `AdminPrincipal` (Q3=A) — 요청 컨텍스트 뷰
JWT claims를 검증·디코드한 결과. 인증 의존성(dependency)이 요청마다 생성, DB 재조회 없음.

```
AdminPrincipal {
  admin_user_id: int    # sub
  store_id: int
  username: str
  role: "admin"
}
```
JWT payload(claims) 구조(Q3=A):
```json
{ "sub": <admin_user_id>, "store_id": 1, "username": "admin", "role": "admin", "iat": ..., "exp": ... }
```
> `exp`는 Unit 1 `create_token`이 `config.JWT_EXPIRE_SECONDS`(57600s=16h)로 자동 부여(§0.3).

---

## 3. 뷰모델 (프론트엔드 상태·응답 조립용)

### 3.1 `DashboardSnapshot` ↔ `GET /api/admin/dashboard` (§3.2.4)
```
DashboardSnapshot {
  tables: TableCard[]
}
TableCard {
  table_id: int
  table_number: int
  session_active: bool
  table_total: int              # calc_table_total() 호출 결과 — 직접 계산 금지
  recent_orders: OrderSummary[] # 최신 3건 (Q6=A), ordered_at 내림차순
}
```
- `OrderSummary`는 계약 §4.1 DTO(Unit 1 `models.OrderSummary`) 재사용.
- `table_total`은 active 세션의 미삭제 주문 합. active 세션 없으면 0, `recent_orders`는 현재 세션 기준.

### 3.2 프론트엔드 클라이언트 상태 (Q8=A: Pinia 스토어)

**`authStore`**
```
{ token: string | null, username: string | null, store_id: number | null,
  isAuthenticated: getter(token != null && not expired) }
```
토큰은 `localStorage`에 저장(Q8=A) → 새로고침 세션 유지(3.2.1 요구). 부팅 시 `GET /api/admin/me`로 유효성 확인.

**`dashboardStore`** (프론트 전용 뷰 상태)
```
{
  tables: Map<table_id, TableCardVM>,   # dashboard 스냅샷으로 초기화, SSE로 갱신
  filter: { status: OrderStatus|null, table_number: int|null },  # Q7=A 클라이언트 측 필터
  connection: "connecting" | "open" | "reconnecting" | "closed",
  lastEventId: number | null            # SSE 재연결용(Q5=A)
}
TableCardVM = TableCard + { highlightUntil: timestamp | null }  # Q6=A 신규주문 10초 강조
```
> `filter`는 **클라이언트 측**(Q7=A). 백엔드 대시보드 API에 필터 파라미터 없음. `highlightUntil`은 `order.created` 수신 시 now+10s.

---

## 4. 상태 열거값 (Unit 1 enum 재사용)
- `OrderStatus`: `pending`(대기중) · `preparing`(준비중) · `completed`(완료) — §1.10.
- SSE 이벤트 타입(§2.3, 구독): `order.created` · `order.status_changed` · `order.deleted` · `session.closed`.

## 5. 소유권 요약
| 항목 | 소유 |
|---|---|
| admin_users/orders/tables/... 스키마 | **Unit 1** (재사용) |
| 로그인 시도 추적(인메모리) | **Unit 3** |
| JWT claims 구조·인증 dependency | **Unit 3** (토큰 유틸은 Unit 1) |
| 대시보드 뷰모델 조립 | **Unit 3** |
| 프론트 Pinia 스토어(auth/dashboard) | **Unit 3** (Unit 4/5는 동일 앱에 라우트/스토어 추가) |
