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
- [~] CONSTRUCTION - Per-Unit Loop (Unit 1 진행 중)
  - [x] Unit 1: Functional Design (승인 완료)
  - [x] Unit 1: NFR Requirements/Design (SKIP — 기술 스택 기본값 확정: FastAPI + Hypothesis + sqlite3)
  - [~] Unit 1: Code Generation (Part 2 Generation 완료 — 승인 대기; 24 tests pass)
- [ ] CONSTRUCTION - Build and Test

## Current Status
- **Current Stage**: CONSTRUCTION - Per-Unit Loop / Unit 1 (Foundation & Shared Core, 김주영) - Code Generation Part 2 완료 (승인 대기)
- **Unit 1 결과물**: backend/(app/core 9모듈, migrations 2, tests 5), shared/integration-contract.md, frontend 스캐폴딩, 루트/backend README. pytest 24 passed(default+ci), seed 정상, /health 200. → Unit 2~5 병렬 착수 가능 상태 도달.
- **Active Developer**: 김주영 → Unit 1 (Foundation & Shared Core)
- **Note**: Q1~Q6 전부 기본값(A) 확정 — 주문번호 A-YYYYMMDD-NNNN(매장+UTC 날짜별 리셋), active 세션 부분유니크 인덱스, 총액 실시간 계산, 메뉴 물리삭제, sqlite3 경량 Repository. Functional Design 산출물 3종 생성: construction/unit1-foundation/functional-design/{domain-entities,business-rules,business-logic-model}.md. PBT-01 충족(Testable Properties §6). 완료 메시지 제시 후 승인 시 Code Generation 진입(NFR 생략).
