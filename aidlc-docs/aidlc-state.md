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
- [ ] CONSTRUCTION - Per-Unit Loop
- [ ] CONSTRUCTION - Build and Test

## Current Status
- **Current Stage**: INCEPTION - Units Generation (Part 2: Generation — 승인 대기)
- **Note**: 사용자가 5명 개발자(김주영, 박찬준, 임동규, 이명우, 윤태경) 병렬 개발을 위해 5개 유닛 분할을 명시적으로 요청. User Stories / Workflow Planning / Application Design 은 요구사항 문서가 충분히 상세하여 유닛 도출에 필요한 범위 내에서 압축 수행. Part 1 질문(Q1~Q5) 답변 완료·모호성 없음 → Part 2 생성 완료: unit-of-work.md / unit-of-work-dependency.md / unit-of-work-story-map.md 생성됨. 완료 메시지 제시 후 사용자 승인 시 CONSTRUCTION 진입.
