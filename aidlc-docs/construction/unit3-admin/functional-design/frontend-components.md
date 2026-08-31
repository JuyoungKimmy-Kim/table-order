# Frontend Components — Unit 3: Admin Auth & Real-time Monitoring (임동규)

> **소유**: Unit 3 (임동규). **위치**: `frontend/admin/`(Unit 3/4/5 공용 Vue 앱). Unit 3이 앱 뼈대(라우터·인증 가드·스토어)를 세팅.
> **스택(Q8=A)**: Vue 3 + Vite + Pinia + Vue Router. **기준**: Integration Contract §2, §3.2, §4.

---

## 1. 앱 뼈대 (Unit 3 세팅, Unit 4/5 확장)
```
frontend/admin/
├── src/
│   ├── main.js                 # Vue 앱 부트스트랩, Pinia/Router 등록
│   ├── router/index.js         # 라우트 + 인증 가드 (Unit 3)
│   ├── stores/
│   │   ├── auth.js             # authStore (Unit 3)
│   │   └── dashboard.js        # dashboardStore (Unit 3)
│   ├── api/
│   │   ├── client.js           # fetch 래퍼(Authorization 자동 첨부, 401→로그아웃)
│   │   └── sse.js              # fetch+ReadableStream SSE 클라이언트 (Q9=A)
│   ├── views/
│   │   ├── LoginView.vue       # (Unit 3) 3.2.1
│   │   └── DashboardView.vue   # (Unit 3) 3.2.2
│   └── components/
│       ├── TableCard.vue
│       ├── OrderDetailModal.vue
│       ├── StatusControl.vue
│       └── TableFilter.vue
└── (vite.config.js, package.json)
```
> **병렬 규칙**: Unit 4(테이블·세션)·Unit 5(메뉴)는 이 앱에 **별도 라우트·뷰·스토어**를 추가한다. Unit 3은 `router`·`api/client`·`auth` 스토어를 공용 인프라로 제공하되 그 외 파일은 건드리지 않아 충돌 최소화.

---

## 2. 라우팅 & 인증 가드 (3.2.1)
| 경로 | 뷰 | 가드 |
|---|---|---|
| `/login` | LoginView | 인증 상태면 `/`로 리다이렉트 |
| `/` (또는 `/dashboard`) | DashboardView | 미인증이면 `/login`으로 리다이렉트 |

- 앱 부팅 시: `authStore`가 `localStorage`에서 토큰 로드 → `GET /api/admin/me`로 유효성 확인. 실패 시 로그아웃 후 `/login`.
- 전역 응답 인터셉터: `401 UNAUTHORIZED` 수신 시 `authStore.logout()` + `/login` 리다이렉트.

## 3. 컴포넌트 명세

### 3.1 `LoginView.vue` (3.2.1)
- **State**: `{ store_code, username, password, submitting, error }`.
- **폼 검증**: 세 필드 모두 비어있지 않을 것(클라이언트 1차), 실제 검증은 서버.
- **동작**: submit → `authStore.login(...)` → 성공 시 `/`로 이동.
- **에러 표시**: `401` → "아이디 또는 비밀번호가 올바르지 않습니다"; `429` → "로그인 시도가 많습니다. 5분 후 다시 시도하세요"(BR-A2).
- **엔드포인트**: `POST /api/admin/login`(§3.2.1).

### 3.2 `DashboardView.vue` (3.2.2)
- **역할**: 대시보드 컨테이너. 마운트 시 `dashboardStore.init()`(스냅샷 로드 → SSE 연결, Q5=A).
- **레이아웃**: 테이블 카드 **그리드**. 상단에 `TableFilter`.
- **표시**: `dashboardStore`의 필터 적용된 `TableCard` 목록. 연결 상태 배지(connecting/open/reconnecting).
- **엔드포인트**: `GET /api/admin/dashboard`(초기), `GET /api/admin/orders/stream`(SSE).

### 3.3 `TableCard.vue`
- **Props**: `tableCardVM`(table_number, session_active, table_total, recent_orders, highlightUntil).
- **표시**: 테이블 번호, 현재 총 주문액(`table_total`), 최신 **3건** 미리보기(§4.1 OrderSummary: order_number/status/total_amount/item_preview).
- **신규 강조(Q6=A)**: `highlightUntil > now`이면 **10초간** 시각 강조(하이라이트 클래스).
- **상호작용**: 카드/주문 클릭 → `OrderDetailModal` 오픈.

### 3.4 `OrderDetailModal.vue`
- **Props**: `order_id`.
- **동작**: 오픈 시 `GET /api/admin/orders/{id}` → `OrderDetail`(§4.2) 표시(항목별 menu_name/unit_price/quantity/line_total).
- **포함**: `StatusControl`(상태 변경).

### 3.5 `StatusControl.vue` (3.2.2)
- **Props**: `order_id`, 현재 `status`.
- **UI**: 3개 상태 버튼/셀렉트(대기중/준비중/완료). 자유 전이(Q4=A) — 모든 상태 선택 가능.
- **동작**: 선택 → `PATCH /api/admin/orders/{id}/status`(§3.2.5). 성공 시 낙관적 갱신, 실제 반영은 `order.status_changed` SSE로 확정.
- **엔드포인트**: `PATCH /api/admin/orders/{id}/status`.

### 3.6 `TableFilter.vue` (Q7=A 클라이언트 필터)
- **State**: `{ status: OrderStatus|null, table_number: int|null }` → `dashboardStore.filter`에 바인딩.
- **동작**: **클라이언트 측** 필터링만 수행(서버 요청 없음). 상태별/테이블번호별 카드 표시 토글.

## 4. Pinia 스토어

### `authStore`
- **state**: `token, username, store_id`.
- **getters**: `isAuthenticated`.
- **actions**: `login(store_code, username, password)`, `fetchMe()`, `logout()`, `loadFromStorage()`.
- **영속**: `token`을 `localStorage`에 저장/복원(새로고침 세션 유지, 3.2.1).

### `dashboardStore`
- **state**: `tables(Map)`, `filter`, `connection`, `lastEventId`.
- **actions**: `init()`(스냅샷+SSE), `applySnapshot(data)`, `handleEvent(evt)`(BR-A6.4 매핑), `reconnect()`, `resync()`(dashboard 재호출), `setFilter(...)`.
- **getters**: `visibleTables`(필터 적용).

## 5. 사용자 상호작용 플로우 (요약)
```
로그인 → (가드 통과) → 대시보드 마운트 → 스냅샷 로드 → SSE 연결
  → 신규 주문 이벤트 → 카드 강조(10s) + recent 갱신
  → 카드 클릭 → 상세 모달 → 상태 변경 → SSE로 전 화면 동기화
  → 필터로 특정 상태/테이블만 표시(클라이언트)
```

---

## 6. 계약 준수 / 추적성 검증 (P5)

### 6.1 API 대조표 (계약 §3.2 ↔ Unit 3 구현)
| 계약 | 메서드/경로 | Unit 3 구현 | DTO/이벤트 | 일치 |
|---|---|---|---|---|
| §3.2.1 | `POST /api/admin/login` | LoginView→authStore, service | req{store_code,username,password} / resp{token,expires_in=57600,store_name}; 401/429 | ✅ |
| §3.2.2 | `GET /api/admin/me` | 부팅 가드, authStore.fetchMe | resp{username,store_id} | ✅ |
| §3.2.3/§2.1 | `GET /api/admin/orders/stream` | api/sse.js + backend StreamingResponse | §2.2 프레임, `sse.subscribe` | ✅ |
| §3.2.4 | `GET /api/admin/dashboard` | dashboardStore.init | resp{tables:[TableCard]}, recent=OrderSummary×3(Q6) | ✅ |
| §3.2.5 | `PATCH /api/admin/orders/{id}/status` | StatusControl | req{status} / resp{order_id,status}; `order.status_changed` 발행 | ✅ |
| §3.2.6 | `GET /api/admin/orders/{id}` | OrderDetailModal | resp OrderDetail(§4.2) | ✅ |

### 6.2 SSE 이벤트 대조 (§2.3)
| event | Unit 3 역할 | 일치 |
|---|---|---|
| `order.created` (Unit 2 발행) | 구독→카드 강조 | ✅ |
| `order.status_changed` (Unit 3 발행) | 발행 payload{order_id,table_id,status} + 구독 반영 | ✅ |
| `order.deleted` (Unit 4 발행) | 구독→주문 제거·total 갱신 | ✅ |
| `session.closed` (Unit 4 발행) | 구독→테이블 리셋 | ✅ |

### 6.3 DTO 준수
- `OrderSummary`(§4.1)·`OrderDetail`(§4.2)는 Unit 1 `app.core.models` **재사용**(재정의 없음).
- 에러 포맷(§0.2)·페이지네이션(§0.4)은 Unit 1 `errors`/`pagination` 사용.

### 6.4 계약 변경 필요 항목
- **없음.** Unit 3은 계약 §3.2/§2/§4 범위 내에서만 구현하며, 신규 필드/엔드포인트/스키마 변경 요구가 없다.
- (참고) Q9=A(SSE 헤더 인증)는 계약 §2.1 "Authorization: Bearer" 규약과 정합 → **Unit 1 조율 불필요**.
