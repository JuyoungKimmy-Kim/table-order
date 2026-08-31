# Backend — Table Order Service

Python · FastAPI · SQLite(sqlite3) · Hypothesis(PBT)

## 설치
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 실행
```bash
# backend 디렉토리에서
export PYTHONPATH=.
uvicorn app.main:app --reload
# 앱 시작 시 스키마가 자동 적용됨. 헬스체크: GET http://127.0.0.1:8000/health
```

## 시드 데이터(개발/데모)
```bash
export PYTHONPATH=.
python -m migrations.seed
# store=STORE001(홍길동식당), admin/admin1234, table 1~3(비번 1234),
# 카테고리 3, 메뉴 5개. 멱등(이미 있으면 건너뜀).
```

## 테스트
```bash
export PYTHONPATH=.
python -m pytest            # 로컬(default 프로파일)
HYPOTHESIS_PROFILE=ci python -m pytest   # CI(고정 seed, 재현 가능 — PBT-08)
```
- PBT 실패 시 Hypothesis 가 최소 반례와 `--hypothesis-seed=...` 재현 정보를 출력한다(shrinking 유지).

## Unit 1(Foundation) 코어 사용법 — 다른 유닛용
```python
from app.core import db, domain, models, errors, validation, pagination, security, sse

# 1) DB 접근
conn = db.connect()
with db.transaction(conn):
    ...

# 2) 도메인 순수 함수 (직접 계산 금지, 반드시 호출)
domain.calc_order_total(items)          # Σ(unit_price*quantity)
domain.calc_table_total(orders)         # 미삭제 total_amount 합
domain.is_current_session_order(o, s)   # active 세션 판별
domain.order_number_format("A", d, seq) # A-YYYYMMDD-NNNN

# 3) 표준 에러
raise errors.MenuNotFound("해당 메뉴를 찾을 수 없습니다.")

# 4) 검증
validation.validate_order_items(items)

# 5) SSE 발행(발행 유닛) / 구독(Unit 3)
await sse.publish("order.created", summary.to_dict())
async for frame in sse.subscribe(last_event_id): ...

# 6) DTO
models.OrderSummary(...).to_dict()
```

## 디렉토리
```text
app/
  main.py            # FastAPI 부트스트랩 + /health (유닛 라우터는 여기 include)
  core/              # Unit 1 소유 — 전 유닛 공유
    config.py db.py models.py domain.py errors.py
    validation.py pagination.py security.py sse.py
migrations/
  0001_initial_schema.sql   # 9개 테이블 + active 세션 부분 유니크 인덱스
  seed.py                   # 개발/데모 시드(bcrypt 해시 런타임 생성)
tests/
  generators.py             # PBT 도메인 제너레이터(중앙화, PBT-07)
  test_domain_pbt.py        # 순수함수 PBT (PBT-02/03)
  test_dto_roundtrip_pbt.py # DTO round-trip PBT (PBT-02/07/08)
  test_domain_examples.py   # 예제 기반(PBT-10 상호보완)
  conftest.py               # Hypothesis 프로파일 + tmp DB fixture
```
