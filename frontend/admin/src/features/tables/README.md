# Unit 4 — Table & Session (frontend)

이명우 담당. `frontend/admin/` 공유 Vue 앱에 흡수되는 **Unit 4 전용** 모듈.
공유 골격(scaffold/router/auth-store/http)은 건드리지 않고, 이 폴더 안에서만 완결된다.

## 파일

| 파일 | 역할 |
| --- | --- |
| `types.ts` | 계약 DTO 타입 (§4.2, §3.3) |
| `api.ts` | §3.3 엔드포인트 호출 래퍼 (백엔드 `app/tables/router.py` 와 1:1) |
| `http.ts` | 경량 HTTP 클라이언트 **shim** (CONTRACT-GAP) |
| `auth-bridge.ts` | 관리자 토큰 조회 **shim** — 현재 `localStorage['admin_token']` (INTEGRATION-TODO unit3-auth) |
| `routes.ts` | `RouteRecordRaw[]` **배열 export** (자체 라우터 X) |
| `TableSetupView.vue` | 테이블 초기 설정 |
| `TableOrdersView.vue` | 현재 주문 목록 · 직권 삭제 · 이용 완료 |
| `DeleteOrderDialog.vue` / `CloseSessionDialog.vue` | 확인 팝업 (프레젠테이션) |
| `OrderHistoryView.vue` | 과거 내역 (날짜 필터 · 페이지네이션) |

## 통합(retrofit) 요약

계약 미정의 부분은 코드에 `CONTRACT-GAP` / `INTEGRATION-TODO(...)` 주석으로 표기.
grep 으로 전부 찾을 수 있다:

```
grep -rn "CONTRACT-GAP\|INTEGRATION-TODO" frontend/admin/src/features/tables
```

의존 기능(Unit 3 로그인/토큰 저장소, 공유 admin 골격)이 개발되면
`auth-bridge.ts`, `http.ts`, `routes.ts` 세 shim 만 교체하면 된다.

**전체 명세·체크리스트:** [`aidlc-docs/construction/unit4-table-session/frontend-integration-spec.md`](../../../../../aidlc-docs/construction/unit4-table-session/frontend-integration-spec.md)
