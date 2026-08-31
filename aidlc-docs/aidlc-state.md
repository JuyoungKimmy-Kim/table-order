# AI-DLC State Tracking

## Project Information
- **Project Name**: Table Order Service (테이블오더 서비스)
- **Project Type**: Greenfield
- **Start Date**: 2026-08-31T00:00:00Z
- **Current Stage**: INCEPTION - Requirements Analysis

## Workspace State
- **Existing Code**: No
- **Programming Languages**: N/A (신규)
- **Build System**: N/A (신규)
- **Project Structure**: Empty (요구사항 문서만 존재)
- **Reverse Engineering Needed**: No
- **Workspace Root**: /Users/juyoungkim/aidlc-workshop/table-order

## Code Location Rules
- **Application Code**: Workspace root (NEVER in aidlc-docs/)
- **Documentation**: aidlc-docs/ only
- **Structure patterns**: See code-generation.md Critical Rules

## Technology Stack (Requirements Analysis 확정)
- **Backend**: Python
- **Frontend**: Vue (고객용 + 관리자용)
- **Database**: SQLite (로컬/임베디드)
- **Deployment**: 로컬 개발 환경 (워크숍/데모)
- **Code Organization**: 모노레포 (백엔드 + 프론트엔드 분리 디렉토리)
- **Scale**: 소규모 (단일 매장, 수십 개 테이블)
- **Real-time**: Server-Sent Events (SSE)

## Extension Configuration
| Extension | Enabled | Decided At |
|---|---|---|
| Security Baseline | No | Requirements Analysis |
| Resiliency Baseline | No | Requirements Analysis |
| Property-Based Testing | Partial — 강제 규칙: PBT-02, PBT-03, PBT-07, PBT-08, PBT-09 (그 외 advisory) | Requirements Analysis |

## Stage Progress
- [x] INCEPTION - Workspace Detection (COMPLETED - Greenfield 판별)
- [x] INCEPTION - Requirements Analysis (COMPLETED - 10개 질문 답변 완료, 스택/확장 확정)
- [~] INCEPTION - User Stories (사용자 요청으로 Units Generation 우선 진행)
- [~] INCEPTION - Workflow Planning (Units Generation 우선 진행)
- [~] INCEPTION - Application Design (Units Generation 우선 진행)
- [~] INCEPTION - Units Generation (Part 1 Planning 완료, Part 2 Generation 산출물 생성 완료 — 사용자 승인 대기)
- [~] CONSTRUCTION - Per-Unit Loop (Unit 1 완료 → Unit 2/3/4 병렬 진행)
  - [x] Unit 1: Functional Design (승인 완료)
  - [x] Unit 1: NFR Requirements/Design (SKIP — 기술 스택 기본값 확정: FastAPI + Hypothesis + sqlite3)
  - [x] Unit 1: Code Generation (Part 2 Generation 완료; 24 tests pass, 커밋됨 340bf5e) — Unit 2~5 병렬 착수 가능
  - [x] Unit 2 (박찬준): Functional Design (산출물 4종, 인터뷰 Q1~Q8 확정 — 승인 완료)
  - [x] Unit 2 (박찬준): NFR Requirements/Design (SKIP — 스택 확정 FastAPI+Vue+SQLite, 소규모 로컬 데모, Security/Resiliency 비활성)
  - [x] Unit 2 (박찬준): Code Generation (Part 1 Planning 승인 → Part 2 Generation 완료; 백엔드 40 tests pass[default+ci], 프론트 build 성공)
  - [x] Unit 3 (임동규): Functional Design (승인 완료 — Q1~Q9 전부 A, 산출물 4종)
  - [x] Unit 3 (임동규): NFR Requirements/Design (SKIP — Unit 1 선례, 스택 확정: FastAPI + sqlite3 + Vue3/Vite/Pinia)
  - [x] Unit 3 (임동규): Code Generation Part 1 Planning 완료 — 계획서 승인
  - [~] Unit 3 (임동규): Code Generation Part 2 Generation 완료 (backend 8파일+main.py, tests 3파일 50 passed[24 Unit1+26 Unit3, default & ci], /health 200, admin 6라우트, frontend/admin Vue앱 15파일 npm build 성공)
  - [x] Unit 4 (이명우): Table & Session Management (origin/main 머지 완료 — PR #1)
- [ ] CONSTRUCTION - Build and Test

## Current Status
- **Current Stage**: CONSTRUCTION - Per-Unit Loop / Unit 2 (Customer Ordering, 박찬준) - Code Generation Part 2 Generation 완료 → 완료 메시지 제시(승인 대기)
- **Unit 2 결과물**: backend/app/customer(schemas/auth/repository/service/router) + tests(test_customer_api 16케이스, test_customer_dto_pbt) → pytest **40 passed**(default & ci). frontend/customer(Vue3+Vite+Pinia+Router: 뷰4·컴포넌트10·스토어3·api client) → `npm run build` 성공. 문서: construction/unit2-customer/code/{backend,frontend,test,code}-summary.md. 계약 변경 없음, 신규 마이그레이션 없음. 생성 중 결함 2건 수정(JWT sub 문자열화, sqlite 스레드 교차→라우터 async 통일).
- **Unit 1 결과물**: backend/(app/core 9모듈, migrations 2, tests 5), shared/integration-contract.md, frontend 스캐폴딩, 루트/backend README. pytest 24 passed(default+ci), seed 정상, /health 200. → Unit 2~5 병렬 착수 가능 상태 도달.
- **Active Developer**: 박찬준 → Unit 2 (Customer Ordering, 풀스택). 범위: 고객 API 4종(§3.1) + frontend/customer Vue 앱 + 테스트. 재사용: core(domain/models/errors/validation/pagination/security/sse).
- **Unit 3 진행**: Functional Design 산출물 4종 생성 완료 — construction/unit3-admin/functional-design/{domain-entities,business-rules,business-logic-model,frontend-components}.md. Q1~Q9=A(시도제한 5회/5분 인메모리, JWT claims-only, 자유 상태전이, 스냅샷→SSE 정합/Last-Event-ID 재연결, recent 3건/10초 강조, 클라이언트 필터, Vue3+Vite+Pinia+Router, fetch+ReadableStream SSE 인증). 계약 변경 필요 없음. PBT: evaluate_login_attempt/validate_order_status/select_recent_orders/build_admin_claims 대상, PBT-04/05/06 N/A.
- **Note**: Q1~Q6 전부 기본값(A) 확정 — 주문번호 A-YYYYMMDD-NNNN(매장+UTC 날짜별 리셋), active 세션 부분유니크 인덱스, 총액 실시간 계산, 메뉴 물리삭제, sqlite3 경량 Repository. Functional Design 산출물 3종 생성: construction/unit1-foundation/functional-design/{domain-entities,business-rules,business-logic-model}.md. PBT-01 충족(Testable Properties §6). 완료 메시지 제시 후 승인 시 Code Generation 진입(NFR 생략).
