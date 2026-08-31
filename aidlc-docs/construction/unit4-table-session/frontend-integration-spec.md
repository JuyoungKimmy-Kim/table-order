# Frontend Integration Spec — Unit 4 (Table & Session Management)

> **소유**: Unit 4 (이명우).
> **목적**: Integration Contract(`shared/integration-contract.md`)가 **정의하지 않은 프론트엔드 통합 지점**을 명세하고, 관련 기능(Unit 3 인증, 공유 admin 앱 골격)이 개발된 뒤 **소급 적용(retrofit)** 이 용이하도록 가정·인터페이스·연결 지점을 문서화한다.
> **전제**: JWT 기반 관리자 인증 체계(§0.3). 병렬 개발 중이라 아직 존재하지 않는 공유 모듈은 **임시 shim** 으로 격리한다.

---

## 0. 배경 — 계약이 정의한 것 / 안 한 것

| 구분 | 항목 | 상태 |
|---|---|---|
| ✅ 정의됨 | Unit 4 API 5종(§3.3), `OrderDetail`(§4.2), 에러 포맷(§0.2), 인증 헤더 규약(§0.3), 페이지네이션(§0.4) | Unit 4 프론트가 **바로 구현 가능** |
| ⬛ 미정의 | admin Vue 앱 골격(package.json/vite/router), 인증 토큰 저장·주입, 공유 HTTP 클라이언트, 레이아웃/네비 | **공유·미조율** → 아래 shim + retrofit |

> 프론트 조율 근거는 계약이 아니라 `aidlc-docs/inception/application-design/unit-of-work.md`:
> "관리자용 프론트(Unit 3/4/5)는 동일한 `frontend/admin/` Vue 앱 내 **별도 라우트/모듈로 분리**." 로그인/토큰 발급(§3.2.1)은 **Unit 3 소유**이므로 인증 토큰 처리도 Unit 3에 귀속되는 것이 자연스럽다.

---

## 1. 코드 마커 규약 (grep 가능)

모든 미정의 통합 지점은 아래 마커로 코드에 표기한다. retrofit 시 이 마커만 검색하면 된다.

| 마커 | 의미 |
|---|---|
| `CONTRACT-GAP` | 계약에 없어서 Unit 4가 잠정 가정한 지점. 공유 결정이 나오면 교체 대상. |
| `INTEGRATION-TODO(unit3-auth)` | Unit 3 인증(토큰 store)이 준비되면 연결할 지점. |
| `INTEGRATION-TODO(admin-scaffold)` | 공유 admin 앱 골격(라우터/HTTP/레이아웃)이 준비되면 연결할 지점. |

검색 예: `grep -rn "CONTRACT-GAP\|INTEGRATION-TODO" frontend/admin/src/features/tables/`

---

## 2. 미정의 통합 지점별 명세 & Retrofit 방법

### 2.1 인증 토큰 소스 (`auth-bridge.ts`)
- **계약**: §0.3 — 관리자 API는 `Authorization: Bearer <JWT>` 필요. **토큰을 어디서 얻는지는 미정의.**
- **Unit 4 잠정 구현**: `getAdminToken()` 가 `localStorage['admin_token']` 를 읽는다(개발용 stopgap). 토큰이 없으면 `null` → 호출부는 401 처리.
- **의존 기능**: Unit 3 §3.2.1 로그인이 발급하는 토큰 + 토큰 보관소(예: Pinia `useAuthStore`).
- **Retrofit**: Unit 3 auth store 완성 시 `auth-bridge.ts` 의 `getAdminToken()` 본문을 `useAuthStore().token` 반환으로 **한 곳만 교체**. 나머지 코드(api/http)는 무변경.
  ```ts
  // 교체 예시
  import { useAuthStore } from '@/stores/auth'   // Unit 3 제공(예정)
  export function getAdminToken() { return useAuthStore().token }
  ```

### 2.2 HTTP 클라이언트 (`http.ts`)
- **계약**: §0.1 base `/api`, JSON, §0.2 에러 envelope.
- **Unit 4 잠정 구현**: `fetch` 기반 경량 래퍼. base URL `/api`, `auth-bridge` 토큰을 헤더에 주입, §0.2 에러를 `ApiError{code,message,details}` 로 파싱해 throw.
- **의존 기능**: 공유 HTTP 클라이언트(공통 axios 인스턴스/인터셉터) — admin 골격이 소유할 가능성.
- **Retrofit**: 공유 클라이언트가 생기면 `api.ts` 의 import 를 공유 클라이언트로 바꾸고 `http.ts` 삭제. 함수 시그니처(`request(method,path,opts)`)를 동일하게 맞춰 두어 교체 비용 최소화.

### 2.3 라우터 마운트 (`routes.ts`)
- **계약**: 미정의. 유닛 정의서만 "별도 라우트로 분리".
- **Unit 4 잠정 구현**: `tableRoutes: RouteRecordRaw[]` 를 **배열로 export** (자체 라우터 생성 안 함 — 공유 골격의 단일 라우터에 흡수시키기 위함). `meta.requiresAuth = true`.
- **Retrofit**: 공유 `router/index.ts` 가 준비되면 아래처럼 **한 줄로 흡수**. Unit 4는 공유 라우터 파일을 직접 수정하지 않는다(충돌 회피).
  ```ts
  import { tableRoutes } from '@/features/tables/routes'
  const routes = [ ...monitoringRoutes, ...tableRoutes, ...menuRoutes ]
  ```

### 2.4 라우트 경로 (제안 — 조율 필요)
계약 미정의. Unit 4가 **제안**하는 경로(충돌 시 조율):
| 화면 | 경로(제안) | 컴포넌트 |
|---|---|---|
| 테이블 초기 설정 | `/tables/setup` | `TableSetupView.vue` |
| 현재 주문 목록/삭제 | `/tables/:tableId/orders` | `TableOrdersView.vue` |
| 과거 주문 내역 | `/tables/:tableId/history` | `OrderHistoryView.vue` |
> 삭제/세션종료 확인 팝업은 라우트가 아닌 다이얼로그 컴포넌트(`DeleteOrderDialog`, `CloseSessionDialog`).

### 2.5 인증 만료(401) 처리
- **Unit 4 잠정**: `http.ts` 가 401 수신 시 `ApiError(code='UNAUTHORIZED')` throw. 화면은 "다시 로그인" 안내만.
- **Retrofit**: Unit 3 인증 완성 시, 401 → 로그인 라우트 리다이렉트를 공유 라우터 가드/HTTP 인터셉터에서 처리하도록 이관. Unit 4 화면 코드 변경 불필요.

### 2.6 빌드/실행
- 현재 `frontend/admin/` 에 Vue 앱 골격(package.json/vite/tsconfig)이 없어 **단독 빌드 불가**. 본 모듈 파일들은 골격 완성 시 그대로 편입되는 소스다.
- 필요 npm 의존성(골격 담당이 추가): `vue`, `vue-router`. (본 모듈은 Pinia 등 특정 상태관리에 하드 의존하지 않음 — auth-bridge 로 격리.)

---

## 3. Retrofit 체크리스트 (관련 기능 완성 후)
- [ ] `auth-bridge.ts` → Unit 3 auth store 연결 (2.1)
- [ ] `http.ts` → 공유 HTTP 클라이언트로 대체(또는 유지) (2.2)
- [ ] 공유 `router/index.ts` 에 `...tableRoutes` 흡수 (2.3)
- [ ] 라우트 경로 팀 조율 확정 (2.4)
- [ ] 401 리다이렉트를 공유 가드로 이관 (2.5)
- [ ] admin 골격에 npm 의존성(`vue`,`vue-router`) 확인 (2.6)
- [ ] 위 완료 후 `CONTRACT-GAP`/`INTEGRATION-TODO` 마커 제거

---

## 4. 참조
- API/DTO/에러/인증 규약: `shared/integration-contract.md` §0, §3.3, §4.2
- Unit 4 업무 규칙: `business-rules.md`, 흐름: `business-logic-model.md`
- 프론트 분리 원칙: `aidlc-docs/inception/application-design/unit-of-work.md`
