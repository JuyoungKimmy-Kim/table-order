# Business Logic Model — Unit 3: Admin Auth & Real-time Monitoring (임동규)

> **소유**: Unit 3 (임동규). **기준**: Integration Contract §0.3, §2, §3.2, §4 · Unit 3 business-rules(BR-A*).
> **코드 위치**: 백엔드 `backend/app/admin_auth/`, 프론트 `frontend/admin/`(Q8=A). Unit 1 `app.core.*` 재사용.

---

## 1. 백엔드 모듈 구성 (`backend/app/admin_auth/`)
| 모듈 | 책임 |
|---|---|
| `router.py` | FastAPI 라우터 6개 엔드포인트(§3.2.1~3.2.6). `app.main`이 `include_router(prefix="/api")`. |
| `service.py` | 인증/대시보드/상태변경 비즈니스 로직(오케스트레이션). |
| `deps.py` | 인증 dependency `get_current_admin()` → `AdminPrincipal`(BR-A3). |
| `attempts.py` | `LoginAttemptTracker`(인메모리) + **순수 판정 함수**(BR-A2). |
| `logic.py` | Unit 3 **순수 함수**(상태값 검증, recent 선별, claims 조립). PBT 대상. |
| `schemas.py` | 요청/응답 Pydantic 모델(LoginReq, StatusReq 등). 응답 DTO는 Unit 1 `models` 재사용. |

---

## 2. 인증 플로우 (3.2.1)

### 2.1 로그인 (`POST /api/admin/login`)
```
1. tracker.is_locked(store_code, username, now)?  → yes: 429 TOO_MANY_ATTEMPTS   (BR-A2.2)
2. Store(store_code) 조회 → 없으면 실패로 간주
3. AdminUser(store_id, username) 조회 → 없으면 실패로 간주
4. verify_password(password, admin.password_hash)  (Unit 1)
5. 실패: tracker.record_failure(...) → 401 UNAUTHORIZED  (BR-A1.3: 원인 구분 없이 동일 응답)
6. 성공: tracker.reset(...) → build_admin_claims(admin) → create_token(claims) (Unit 1)
        → 200 { token, expires_in=57600, store_name }
```
> 시도 제한 판정과 상태 갱신은 순수 함수 `evaluate_login_attempt`를 통해 계산하고, tracker는 그 결과를 저장만 한다.

### 2.2 인증 dependency (`get_current_admin`) — 보호 엔드포인트 공통
```
1. Authorization 헤더에서 Bearer 토큰 추출 → 없으면 401 UNAUTHORIZED
2. decode_token(token)  (Unit 1; 만료/무효는 jwt 예외)
   - 예외 → 401 UNAUTHORIZED   (BR-A3.3)
3. claims → AdminPrincipal(admin_user_id, store_id, username, role)
4. 반환. DB 재조회 없음(Q3=A)
```
`GET /api/admin/me`: dependency 결과에서 `{ username, store_id }` 반환(BR-A3.4).

### 2.3 시도 제한 알고리즘 (BR-A2)
```
evaluate_login_attempt(state, now, *, success, threshold=5, lockout=5m) -> Decision
  # state: AttemptState{fail_count, locked_until} | None
  locked = state.locked_until is not None and now < state.locked_until
  if locked:            return Decision(allow=False, reason="locked", next=state)
  if success:           return Decision(allow=True,  next=None)          # reset
  fail = (state.fail_count if state else 0) + 1
  if fail >= threshold: return Decision(allow=False, reason="lock_now",
                                        next=AttemptState(fail, now+lockout))
  return Decision(allow=True/False..., next=AttemptState(fail, None))
```
> 순수 함수(입력=상태+now+결과, 부수효과 없음). tracker는 `Decision.next`를 dict에 반영.

---

## 3. 대시보드 스냅샷 조립 (`GET /api/admin/dashboard`, BR-A5)
```
1. principal.store_id의 tables 전체 조회
2. 각 table:
   a. active TableSession 조회
   b. 없으면 TableCard(session_active=False, table_total=0, recent_orders=[])
   c. 있으면 세션의 미삭제 orders 조회
      - table_total = calc_table_total(orders)           (Unit 1 순수함수, BR-A5.2)
      - recent = select_recent_orders(orders, n=3)       (Unit 3 순수함수, 정렬+상한)
      - recent → OrderSummary[]  (Unit 1 models)
3. { tables: [TableCard...] }
```

## 4. 상태 변경 플로우 (`PATCH /.../status`, BR-A4)
```
1. get_current_admin (인증)
2. validate_order_status(target)  → 유효 3종 아니면 400 VALIDATION_ERROR   (Unit 1 validation)
3. Order(id) 조회, is_deleted=0 확인 → 없으면 404 ORDER_NOT_FOUND
4. UPDATE orders.status = target   (자유 전이, BR-A4.3)
5. await sse.publish("order.status_changed", {order_id, table_id, status})  (BR-A6.1)
6. 200 { order_id, status }
```

## 5. SSE 구독 / 재연결 / 재동기화 (Q5=A, BR-A6/A7)

### 5.1 백엔드 (`GET /api/admin/orders/stream`)
```
1. get_current_admin (인증; 토큰은 fetch 헤더로 전달 — Q9=A)
2. last_event_id = Last-Event-ID 헤더(int) or None
3. StreamingResponse(sse.subscribe(last_event_id), media_type="text/event-stream")
```

### 5.2 프론트 흐름 (Pinia `dashboardStore`)
```
로그인 완료
  → GET /api/admin/dashboard         # 초기 스냅샷 (Q5=A)
  → 스냅샷으로 tables 채움
  → SSE 연결(fetch+ReadableStream, Authorization 헤더)  # 직후
  → 이벤트 수신 시 lastEventId 갱신 + BR-A6.4 매핑으로 tables 갱신
재연결(끊김 감지):
  → Last-Event-ID: <lastEventId> 로 재연결(백엔드 best-effort 백로그 재전송)
  → 유실 의심(장시간 단절 등) 시 GET /api/admin/dashboard 재호출로 전체 재동기화
```

## 6. PBT 적용 판단 (P6)
활성 확장: **PBT Partial** — 강제 규칙 PBT-02, 03, 07, 08, 09. Unit 3의 순수 함수에 대해:

| 순수 함수(Unit 3) | 강제 규칙 적용 | 판단 |
|---|---|---|
| `evaluate_login_attempt(state, now, success)` | **PBT-03(불변), PBT-07(제너레이터), PBT-08(재현), PBT-09(프레임워크)** | **적용** — 속성: 성공→항상 리셋(next=None); 임계값 도달 시에만 lock_now; 잠금 중이면 결과 상태 불변; fail_count 단조 증가(리셋 전까지) |
| `validate_order_status(target)` | **PBT-03** | **적용** — 속성: 3종 enum이면 통과, 그 외 전부 거부(전수/생성 검증) |
| `select_recent_orders(orders, n=3)` | **PBT-03, PBT-07** | **적용** — 속성: 결과 길이 ≤ n; 항상 미삭제만; ordered_at 내림차순; 입력 순서 무관(정렬 후 동일) |
| `build_admin_claims(admin)` | **PBT-02(round-trip)** | **적용(경량)** — claims→create_token→decode_token 라운드트립 시 sub/store_id/username/role 보존 |
| `PBT-04/05/06` (idempotency/oracle/stateful) | — | **N/A** — Unit 3 순수함수에 해당 패턴 없음(사유 명시). |

- **PBT-07 제너레이터**: Unit 1 `tests/generators.py` 재사용/확장(주문·상태·시각 제너레이터). 신규 제너레이터는 `admin_users`, `AttemptState`.
- **PBT-08 재현성**: Unit 1 conftest의 `ci` 프로파일(derandomize) 재사용.
- **PBT-09 프레임워크**: hypothesis(이미 requirements.txt 포함).
- 테스트 위치: `backend/tests/test_admin_auth_pbt.py` (예정, Code Generation 단계).

> 계약 §5의 총액/세션 순수함수는 **Unit 1 소유**이며 Unit 3은 호출만 하므로 해당 PBT는 Unit 1이 소유(중복 작성 안 함).
