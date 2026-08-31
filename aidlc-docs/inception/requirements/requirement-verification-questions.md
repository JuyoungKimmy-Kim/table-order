# Requirements Clarification Questions (요구사항 명확화 질문)

테이블오더 서비스 요구사항 문서는 기능적으로 매우 상세합니다. 아래는 구현 방향을 확정하기 위해 아직 명시되지 않은 항목들과, AI-DLC 확장(extension) 활성화 여부를 묻는 질문입니다.

각 질문의 `[Answer]:` 태그 뒤에 선택한 옵션의 **글자(A, B, C...)**를 적어주세요. 마땅한 옵션이 없으면 마지막 옵션(Other)을 고르고 설명을 덧붙여 주세요. 모두 작성하신 후 "완료" 또는 "done"이라고 알려주시면 됩니다.

---

## Question 1
백엔드 서버 기술 스택은 무엇을 사용하시겠습니까?

A) Node.js (Express / NestJS 등)

B) Python (FastAPI / Django 등)

C) Java / Kotlin (Spring Boot 등)

D) Go

X) Other (please describe after [Answer]: tag below)

[Answer]: B

## Question 2
프론트엔드(고객용 웹UI + 관리자용 인터페이스) 기술 스택은 무엇을 사용하시겠습니까?

A) React (Vite / Next.js 등)

B) Vue

C) Svelte / SvelteKit

D) 순수 HTML/CSS/JS (프레임워크 없음)

X) Other (please describe after [Answer]: tag below)

[Answer]: B

## Question 3
데이터 저장소(데이터베이스)는 무엇을 사용하시겠습니까?

A) 관계형 DB (PostgreSQL / MySQL)

B) NoSQL 문서형 DB (MongoDB / DynamoDB)

C) 로컬/임베디드 DB (SQLite) — 데모/워크숍 목적에 적합

D) 인메모리 저장소 — 재시작 시 데이터 초기화 (가장 단순, 프로토타입용)

X) Other (please describe after [Answer]: tag below)

[Answer]: C

## Question 4
배포/실행 대상 환경은 무엇을 목표로 하시겠습니까?

A) 로컬 개발 환경에서 실행 (워크숍/데모 목적)

B) 컨테이너(Docker) 기반 로컬 실행

C) 클라우드 배포 (AWS 등)

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 5
고객용/관리자용 프론트엔드와 백엔드 서버의 코드 구성 방식은?

A) 모노레포 단일 저장소 안에 백엔드 + 프론트엔드 분리 디렉토리 (권장)

B) 백엔드가 프론트엔드 정적 파일을 함께 서빙하는 단일 애플리케이션

C) 완전히 분리된 별도 프로젝트

X) Other (please describe after [Answer]: tag below)

[Answer]: A 

## Question 6
동시성 규모(예상 최대 동시 사용 테이블/관리자 수)는 어느 정도로 설계하면 될까요?

A) 소규모 — 단일 매장, 수십 개 테이블 수준 (워크숍/데모)

B) 중규모 — 여러 매장, 수백 개 테이블 수준

C) 대규모 — 다수 매장 멀티테넌시, 확장성 우선

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 7
관리자용 실시간 주문 모니터링은 요구사항대로 **Server-Sent Events (SSE)** 방식으로 확정할까요?

A) 예 — SSE로 확정 (요구사항 명시대로)

B) 아니오 — WebSocket으로 변경

C) 아니오 — 단순 폴링(polling)으로 변경

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

# 확장(Extension) 활성화 여부

아래는 AI-DLC 확장 규칙의 적용 여부를 묻는 질문입니다. 각 확장을 활성화하면 해당 규칙이 이후 모든 단계에서 하드 제약(blocking constraint)으로 강제됩니다.

## Question 8: Security Extensions
Should security extension rules be enforced for this project?
(이 프로젝트에 보안 확장 규칙을 강제할까요?)

A) Yes — enforce all SECURITY rules as blocking constraints (recommended for production-grade applications)

B) No — skip all SECURITY rules (suitable for PoCs, prototypes, and experimental projects)

X) Other (please describe after [Answer]: tag below)

[Answer]: B

## Question 9: Resiliency Extensions
Should the resiliency baseline be applied to this project?
(복원력(resiliency) 베이스라인을 적용할까요?)

**이 확장이란**: AWS Well-Architected Framework(신뢰성 기둥)에서 파생된 **설계 시점의 방향성 있는 모범 사례** 모음을 요구사항/설계/코드에 적용합니다. 내결함성, 고가용성, 관측성, 복구성 방향으로 유도합니다.

**이 확장이 아닌 것**: 이것만으로 워크로드가 프로덕션 준비 완료가 되지 않으며, 가용성/RTO/RPO 목표를 보증하지 않습니다. 좋은 복원력 결정을 초기에 스캐폴딩하는 **출발점**일 뿐입니다.

A) Yes — apply the resiliency baseline as directional best practices and design-time guidance (recommended for business-critical workloads)

B) No — skip the resiliency baseline (suitable for PoCs, prototypes, and experimental projects where rapid iteration matters more than reliability)

X) Other (please describe after [Answer]: tag below)

[Answer]: B 

## Question 10: Property-Based Testing Extension
Should property-based testing (PBT) rules be enforced for this project?
(속성 기반 테스트(PBT) 규칙을 강제할까요?)

A) Yes — enforce all PBT rules as blocking constraints (recommended for projects with business logic, data transformations, serialization, or stateful components)

B) Partial — enforce PBT rules only for pure functions and serialization round-trips (suitable for projects with limited algorithmic complexity)

C) No — skip all PBT rules (suitable for simple CRUD applications, UI-only projects, or thin integration layers with no significant business logic)

X) Other (please describe after [Answer]: tag below)

[Answer]: B
