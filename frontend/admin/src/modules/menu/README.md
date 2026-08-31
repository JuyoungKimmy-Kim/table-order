# Unit 5 — 메뉴 관리 프론트 모듈 (윤태경)

관리자용 Vue 앱(`frontend/admin`) 안에 **plug-in** 되는 메뉴 관리 기능 모듈이다.
앱 셸(라우터 루트·인증 가드·공통 레이아웃)은 **Unit 3(임동규) 소유**이며, 본 모듈은
그 셸에 라우트/화면만 얹는다.

## 구성
```
src/modules/menu/
├── api/menuApi.js          # 계약 §3.4 API 클라이언트 + ApiError(§0.2 파싱)
├── routes.js               # 메뉴/카테고리 라우트 정의(셸 라우터에 병합)
├── views/
│   ├── MenuListView.vue      # 메뉴 CRUD + 노출 순서 조정 (경로: /menus)
│   └── CategoryManageView.vue# 카테고리 CRUD (경로: /menu-categories)
└── components/
    ├── MenuFormModal.vue     # 등록/수정 폼(클라 검증 + 서버 400 매핑)
    └── ConfirmDialog.vue     # 삭제 확인 팝업
```

## Unit 3 앱 셸과의 통합 지점 (2가지)

1. **라우터 병합** — 셸 라우터의 인증 레이아웃 children 에 `menuRoutes` 추가:
   ```js
   import menuRoutes from '@/modules/menu/routes.js'
   // children: [ ...menuRoutes, ...otherUnitRoutes ]
   ```

2. **인증 토큰 주입** — 기본은 `localStorage['admin_token']` 을 읽는다.
   Unit 3 인증 스토어가 준비되면 앱 부트스트랩에서 교체:
   ```js
   import { setAuthTokenGetter, setApiBase } from '@/modules/menu/api/menuApi.js'
   setAuthTokenGetter(() => authStore.token)   // 선택
   setApiBase('/api/admin')                     // 기본값과 동일(생략 가능)
   ```

## 계약/결정 준수
- 모든 API는 §3.4 시그니처, 에러는 §0.2 표준 포맷을 파싱.
- 관리자 목록은 `is_available` 무관 전체 표시(BR-8.2), 정렬 `display_order ASC`(BR-8.3).
- **삭제 결정 반영**: 메뉴 삭제 시 참조 주문 있으면 서버가 409 `MENU_IN_USE` → "노출 끄기" 안내(#1).
  카테고리 삭제 시 하위 메뉴 있으면 409 `CATEGORY_IN_USE` → 안내(#3).
- 메뉴 숨김은 삭제 대신 **수정 폼의 '노출' 체크 해제**(is_available=false)로 처리(#4).

## 전제 (앱 셸이 제공해야 함, Unit 3)
- Vue 3 + Vue Router 4 + Vite 기반 앱.
- `@` alias → `src/`.
- 로그인/인증 가드, 상단 네비게이션에 '메뉴 관리'/'카테고리 관리' 링크.
- dev 서버에서 `/api` → 백엔드(FastAPI) 프록시.

## 검증 상태
- 백엔드(§3.4) API는 `backend/tests/test_menu_unit5.py` 로 검증 완료(11 pass).
- 프론트는 Node/앱 셸 미비로 빌드 검증 전. 셸 준비 후 `npm run dev` 로 확인 예정.
