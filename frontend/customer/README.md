# 고객 주문 프론트엔드 (Unit 2)

테이블에서 손님이 직접 로그인 → 메뉴 탐색 → 장바구니 → 주문 → 내역 확인하는 모바일 웹 앱.

- **스택**: Vue 3 (`<script setup>`) + Vite + Pinia + Vue Router
- **담당**: 박찬준 · **요구사항**: 3.1.1 ~ 3.1.5
- **백엔드 계약**: `shared/integration-contract.md` §3.1 (`/api/customer/*`)

## 설치 & 실행

```bash
cd frontend/customer
npm install
npm run dev      # http://localhost:5173  (dev 서버)
```

개발 서버는 `/api` 요청을 백엔드(`http://localhost:8000`)로 프록시한다(`vite.config.js`).
따라서 백엔드를 먼저 띄워야 한다:

```bash
# 별도 터미널 (프로젝트 backend/)
cd backend
python -m migrations.seed          # 최초 1회: 매장/테이블/메뉴 시드
uvicorn app.main:app --reload      # http://localhost:8000
```

로그인 정보(시드 기준): 매장코드 `STORE001`, 테이블 번호 `1`~`3`, 비밀번호 `1234`.

## 빌드

```bash
npm run build     # dist/ 정적 산출물 생성
npm run preview   # 빌드 결과 미리보기
```

## 구조

```text
src/
├─ main.js                 앱 부트스트랩(Pinia + Router)
├─ App.vue                 RouterView
├─ router/index.js         라우트 + 인증 가드(미인증 → /setup)
├─ api/client.js           fetch 래퍼(Bearer 주입, 401 → 로그아웃/리다이렉트)
├─ stores/
│  ├─ session.js           table_token localStorage 영속(Q1)
│  ├─ cart.js              cart:{tableId} 로컬 저장, 실시간 총액, 품절 표시(Q4/Q5)
│  └─ menu.js              메뉴 조회/카테고리 상태
├─ views/
│  ├─ SetupView.vue        /setup  로그인 (3.1.1)
│  ├─ MenuView.vue         /       메뉴(기본 화면) (3.1.2)
│  ├─ CartView.vue         /cart   장바구니/주문 (3.1.3, 3.1.4)
│  └─ OrdersView.vue       /orders 주문 내역(진입 시 재조회) (3.1.5)
└─ components/             CategoryTabs · MenuGrid · MenuCard · MenuDetailModal ·
                           CartFab · CartItemRow · CartSummary · ConfirmOrderButton ·
                           OrderConfirmModal · OrderCard
```

## 설계 메모
- **금액 표시는 참고용**: 최종 주문 금액은 서버가 메뉴 마스터 단가로 재계산한다(클라 값 미신뢰).
- **품절 대응(Q5)**: 주문이 409/404 로 거부되면 서버가 준 `error.details` 의 menu_id 를
  장바구니에 품절로 표시하고 주문 버튼을 비활성화한다(장바구니는 유지).
- **자동화 친화**: 주요 요소에 `data-testid` 부여.
