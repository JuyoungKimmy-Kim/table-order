# 관리자 프론트엔드 (frontend/admin)

Table Order 관리자용 Vue 3 앱. **Unit 3(임동규)** 이 앱 뼈대(라우터·인증 가드·상태관리·API/SSE 클라이언트)를 세팅했으며, **Unit 4(테이블·세션)·Unit 5(메뉴)** 는 이 앱에 라우트/뷰/스토어를 추가한다.

## 스택
Vue 3 · Vite · Pinia · Vue Router (확정 Q8=A)

## 실행
```bash
# 백엔드(FastAPI)를 먼저 8000 포트로 실행
cd ../../backend && uvicorn app.main:app --reload   # 예시

# 관리자 프론트 (dev, /api → localhost:8000 프록시)
npm install
npm run dev        # http://localhost:5174
npm run build      # 프로덕션 빌드(dist/)
```

## 구조 (Unit 3 소유)
```
src/
├── router/index.js        # 라우트 + 인증 가드(미인증 → /login)
├── stores/auth.js         # 로그인/세션(localStorage 토큰, 새로고침 유지)
├── stores/dashboard.js    # 대시보드 스냅샷 + SSE 이벤트 반영(BR-A6.4)
├── api/client.js          # fetch 래퍼(Bearer 자동첨부, 401→로그아웃)
├── api/sse.js             # fetch+ReadableStream SSE(Authorization 헤더, Q9=A)
├── views/LoginView.vue    # 3.2.1 로그인
├── views/DashboardView.vue# 3.2.2 실시간 모니터링
└── components/            # TableCard, OrderDetailModal, StatusControl, TableFilter
```

## 기능 (요구사항 3.2.1 / 3.2.2)
- 매장 로그인(JWT, 새로고침 세션 유지), 로그인 시도 제한 안내(429).
- 실시간 대시보드: 테이블 카드 그리드(총 주문액·최신 3건), SSE 실시간 갱신.
- 신규 주문 10초 강조, 주문 상세/상태 변경(자유 전이), 상태·테이블 클라이언트 필터.

## 백엔드 연동
- API: `/api/admin/*` (login, me, dashboard, orders/stream, orders/{id}, orders/{id}/status)
- 계약: `shared/integration-contract.md` §3.2 / §2 / §4
