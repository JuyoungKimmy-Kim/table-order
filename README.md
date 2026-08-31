# Table Order Service (테이블오더 서비스)

소규모 단일 매장용 테이블오더 서비스. 고객은 테이블 태블릿으로 주문하고, 관리자는 실시간으로 주문을 모니터링·관리한다.

## 기술 스택
- **Backend**: Python · FastAPI · SQLite(sqlite3 표준 라이브러리)
- **Frontend**: Vue (고객용 + 관리자용)
- **Real-time**: Server-Sent Events (SSE)
- **Test**: pytest + Hypothesis (Property-Based Testing)
- **구성**: 모노레포

## 디렉토리 구조
```text
table-order/
├── backend/            # Python 백엔드 (FastAPI)
│   ├── app/core/       # [Unit 1] 공통 코어: DB, 모델, 도메인 순수함수, 에러, SSE 브로커
│   ├── app/customer/   # [Unit 2] 고객 주문 API (박찬준)
│   ├── app/admin_auth/ # [Unit 3] 관리자 인증 + 모니터링 API (임동규)
│   ├── app/tables/     # [Unit 4] 테이블·세션 관리 API (이명우)
│   ├── app/menu/       # [Unit 5] 메뉴 관리 API (윤태경)
│   ├── migrations/     # [Unit 1] SQLite 스키마/시드
│   └── tests/          # 유닛별 테스트 (PBT 포함)
├── frontend/
│   ├── customer/       # [Unit 2] 고객용 Vue 앱
│   └── admin/          # [Unit 3/4/5] 관리자용 Vue 앱
├── shared/             # [Unit 1] API 통합 계약 (integration-contract.md)
└── aidlc-docs/         # AI-DLC 문서 (코드 아님)
```

## 유닛 배정 (5명 병렬 개발)
| 유닛 | 담당 | 범위 |
|---|---|---|
| Unit 1: Foundation & Shared Core | 김주영 | 스키마·도메인 모델·공통 계약·순수함수·SSE 브로커 (기반) |
| Unit 2: Customer Ordering | 박찬준 | 고객 주문 풀스택 (3.1.1~3.1.5) |
| Unit 3: Admin Auth & Monitoring | 임동규 | 관리자 인증 + 실시간 모니터링 (3.2.1, 3.2.2) |
| Unit 4: Table & Session Mgmt | 이명우 | 테이블·세션 관리 (3.2.3) |
| Unit 5: Menu Management | 윤태경 | 메뉴 CRUD (3.2.4) |

## 병렬 개발 규칙
1. **Unit 1(기반)이 먼저 확정** — `shared/integration-contract.md`(API 계약)와 `backend/app/core/`(모델·스키마·순수함수·SSE 브로커)를 확정한 뒤 Unit 2~5가 동시 착수한다.
2. 모든 유닛은 총액/세션 판별을 직접 계산하지 말고 `app.core.domain`의 순수 함수를 호출한다.
3. SSE 발행은 `app.core.sse.publish(event, payload)`만 사용한다.
4. 계약 변경은 Unit 1(김주영)이 조율: 원본 문서 수정 → 전원 공지 → 반영.

## 실행
백엔드 실행/테스트는 [backend/README.md](backend/README.md) 참조.
