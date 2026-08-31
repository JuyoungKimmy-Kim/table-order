"""Unit 2: 고객 API 통합 테스트 (BR-C1~C5).

FastAPI TestClient + 임시 파일 DB(시드 포함)로 4개 엔드포인트를 예제 기반 검증한다.
- config.DB_PATH 를 tmp 파일로 monkeypatch → db.connect()/seed() 모두 해당 DB 사용.
- 로그인 성공/실패, 메뉴 노출 규칙, 주문 생성(세션·서버 총액 재계산·주문번호·SSE),
  품절/미존재 거부, 현재 세션 내역(정렬·삭제 제외·페이지네이션)을 다룬다.
"""
from __future__ import annotations

import datetime as _dt
import re

import pytest
from fastapi.testclient import TestClient

from app.core import config, db, sse

ORDER_NO_RE = re.compile(r"^A-\d{8}-\d{4}$")


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """tmp DB 로 시드한 뒤 lifespan 이 도는 TestClient 를 제공한다."""
    db_file = tmp_path / "api_test.db"
    monkeypatch.setattr(config, "DB_PATH", str(db_file))
    from migrations.seed import seed
    seed()  # apply_migrations + 시드 데이터 (STORE001, 테이블 1~3, 메뉴 5개)
    from app.main import app
    with TestClient(app) as c:
        yield c


# --- 헬퍼 ---

def _login(client, table_number=1, password="1234", store_code="STORE001"):
    return client.post("/api/customer/login", json={
        "store_code": store_code, "table_number": table_number, "password": password,
    })


def _token(client, **kw) -> str:
    r = _login(client, **kw)
    assert r.status_code == 200, r.text
    return r.json()["table_token"]


def _auth(token) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _menu_by_name(client, token, name):
    r = client.get("/api/customer/menus", headers=_auth(token))
    assert r.status_code == 200, r.text
    for cat in r.json()["categories"]:
        for m in cat["menus"]:
            if m["name"] == name:
                return m
    return None


def _set_available(name: str, available: int) -> None:
    conn = db.connect()
    try:
        with db.transaction(conn):
            conn.execute("UPDATE menus SET is_available=? WHERE name=?", (available, name))
    finally:
        conn.close()


def _soft_delete_order(order_id: int) -> None:
    conn = db.connect()
    try:
        with db.transaction(conn):
            conn.execute("UPDATE orders SET is_deleted=1 WHERE id=?", (order_id,))
    finally:
        conn.close()


# --- 3.1.1 로그인 (BR-C1) ---

def test_login_success_returns_contract_fields(client):
    r = _login(client, table_number=1)
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body) == {"table_token", "table_id", "table_number", "store_name"}
    assert body["table_number"] == 1
    assert body["store_name"] == "홍길동식당"
    assert isinstance(body["table_token"], str) and body["table_token"]


def test_login_wrong_password_401(client):
    r = _login(client, table_number=1, password="wrong")
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "UNAUTHORIZED"


def test_login_unknown_store_401(client):
    r = _login(client, store_code="NOPE")
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "UNAUTHORIZED"


# --- 3.1.2 메뉴 (BR-C2) ---

def test_menus_requires_auth(client):
    r = client.get("/api/customer/menus")
    assert r.status_code == 401


def test_menus_excludes_unavailable(client):
    token = _token(client)
    before = _menu_by_name(client, token, "콜라")
    assert before is not None  # 시드는 모두 available

    _set_available("콜라", 0)
    r = client.get("/api/customer/menus", headers=_auth(token))
    assert r.status_code == 200
    names = [m["name"] for cat in r.json()["categories"] for m in cat["menus"]]
    assert "콜라" not in names           # 품절 제외 (BR-C2.2)
    assert "김치찌개" in names            # 나머지는 노출


# --- 3.1.4 주문 생성 (BR-C4) ---

def test_create_order_success_recalculates_and_publishes_sse(client):
    token = _token(client)
    kimchi = _menu_by_name(client, token, "김치찌개")  # 8000
    cola = _menu_by_name(client, token, "콜라")        # 2000
    expected_total = kimchi["price"] * 2 + cola["price"] * 1

    before_events = len(sse.broker._recent)
    r = client.post("/api/customer/orders", headers=_auth(token), json={
        "items": [
            {"menu_id": kimchi["id"], "quantity": 2},
            {"menu_id": cola["id"], "quantity": 1},
        ],
    })
    assert r.status_code == 201, r.text
    body = r.json()
    assert set(body) == {"order_id", "order_number", "total_amount", "status", "ordered_at"}
    assert body["status"] == "pending"
    # 서버가 메뉴 마스터 단가로 재계산(클라 단가 미신뢰)
    assert body["total_amount"] == expected_total
    # 주문번호 형식 A-YYYYMMDD-NNNN, 당일 첫 주문 → 0001
    assert ORDER_NO_RE.match(body["order_number"])
    today = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%d")
    assert body["order_number"] == f"A-{today}-0001"

    # order.created SSE 발행(커밋 이후, BR-C4.8)
    new = sse.broker._recent[before_events:]
    created = [f for f in new if f["event"] == "order.created"]
    assert created, "order.created 이벤트가 발행되어야 함"
    assert created[-1]["data"]["order_id"] == body["order_id"]


def test_create_order_sequence_increments_per_day(client):
    token = _token(client)
    kimchi = _menu_by_name(client, token, "김치찌개")
    today = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%d")
    nums = []
    for _ in range(2):
        r = client.post("/api/customer/orders", headers=_auth(token),
                        json={"items": [{"menu_id": kimchi["id"], "quantity": 1}]})
        assert r.status_code == 201, r.text
        nums.append(r.json()["order_number"])
    assert nums == [f"A-{today}-0001", f"A-{today}-0002"]


def test_create_order_menu_not_found_404(client):
    token = _token(client)
    r = client.post("/api/customer/orders", headers=_auth(token),
                    json={"items": [{"menu_id": 999999, "quantity": 1}]})
    assert r.status_code == 404
    err = r.json()["error"]
    assert err["code"] == "MENU_NOT_FOUND"
    assert 999999 in err["details"]["not_found_menu_ids"]


def test_create_order_menu_unavailable_409(client):
    token = _token(client)
    cola = _menu_by_name(client, token, "콜라")
    _set_available("콜라", 0)
    r = client.post("/api/customer/orders", headers=_auth(token),
                    json={"items": [{"menu_id": cola["id"], "quantity": 1}]})
    assert r.status_code == 409
    err = r.json()["error"]
    assert err["code"] == "MENU_UNAVAILABLE"
    assert cola["id"] in err["details"]["unavailable_menu_ids"]


def test_create_order_empty_items_400(client):
    token = _token(client)
    r = client.post("/api/customer/orders", headers=_auth(token), json={"items": []})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


def test_create_order_requires_auth(client):
    r = client.post("/api/customer/orders", json={"items": [{"menu_id": 1, "quantity": 1}]})
    assert r.status_code == 401


# --- 3.1.5 주문 내역 (BR-C5) ---

def test_list_orders_no_session_returns_empty(client):
    # 테이블 2는 주문한 적이 없어 active 세션이 없음 → 빈 목록
    token = _token(client, table_number=2)
    r = client.get("/api/customer/orders", headers=_auth(token))
    assert r.status_code == 200
    body = r.json()
    assert body["items"] == [] and body["total"] == 0


def test_list_orders_sorted_and_excludes_deleted(client):
    token = _token(client)
    kimchi = _menu_by_name(client, token, "김치찌개")
    order_ids = []
    for _ in range(2):
        r = client.post("/api/customer/orders", headers=_auth(token),
                        json={"items": [{"menu_id": kimchi["id"], "quantity": 1}]})
        order_ids.append(r.json()["order_id"])

    r = client.get("/api/customer/orders", headers=_auth(token))
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2
    nums = [o["order_number"] for o in body["items"]]
    assert nums == sorted(nums)  # ordered_at ASC, id ASC
    # 응답 항목이 계약 필드를 갖는지 (OrderDetail)
    first = body["items"][0]
    assert {"order_id", "order_number", "table_id", "table_number",
            "status", "total_amount", "ordered_at", "items"} <= set(first)

    # 첫 주문 soft-delete → 내역에서 제외 (BR-C5.2)
    _soft_delete_order(order_ids[0])
    r2 = client.get("/api/customer/orders", headers=_auth(token))
    body2 = r2.json()
    assert body2["total"] == 1
    assert [o["order_id"] for o in body2["items"]] == [order_ids[1]]


def test_list_orders_pagination(client):
    token = _token(client)
    kimchi = _menu_by_name(client, token, "김치찌개")
    for _ in range(2):
        client.post("/api/customer/orders", headers=_auth(token),
                    json={"items": [{"menu_id": kimchi["id"], "quantity": 1}]})

    r = client.get("/api/customer/orders?page=1&size=1", headers=_auth(token))
    body = r.json()
    assert body["total"] == 2 and body["size"] == 1 and body["page"] == 1
    assert len(body["items"]) == 1
