"""Unit 3 API 테스트 (FastAPI TestClient).

임시 DB 로 config.DB_PATH 를 지정하고 시드 + 세션/주문을 만든 뒤
6개 엔드포인트를 검증한다.
"""
from __future__ import annotations

import datetime as _dt

import pytest
from fastapi.testclient import TestClient


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """임시 DB + 시드 + 세션/주문 1건을 준비한 TestClient."""
    from app.core import config, db
    from app.admin_auth import attempts

    db_file = str(tmp_path / "api.db")
    monkeypatch.setattr(config, "DB_PATH", db_file)
    # 시도 제한 트래커를 테스트 간 격리(service.login 이 호출 시 attempts.tracker 를 해석)
    monkeypatch.setattr(attempts, "tracker", attempts.LoginAttemptTracker())

    from migrations.seed import seed
    seed()

    # 테이블 1에 active 세션 + 주문 1건(항목 2개) 삽입
    conn = db.connect(db_file)
    try:
        now = _now()
        with db.transaction(conn):
            table_id = conn.execute(
                "SELECT id FROM tables WHERE table_number=1"
            ).fetchone()["id"]
            sid = conn.execute(
                "INSERT INTO table_sessions(table_id, status, opened_at, created_at, updated_at)"
                " VALUES (?, 'active', ?, ?, ?)", (table_id, now, now, now)
            ).lastrowid
            oid = conn.execute(
                "INSERT INTO orders(session_id, table_id, order_number, status, total_amount,"
                " is_deleted, ordered_at, created_at, updated_at)"
                " VALUES (?,?,?,?,?,0,?,?,?)",
                (sid, table_id, "A-20260831-0001", "pending", 22000, now, now, now),
            ).lastrowid
            for mn, up, q in [("김치찌개", 8000, 2), ("콜라", 2000, 3)]:
                conn.execute(
                    "INSERT INTO order_items(order_id, menu_id, menu_name, unit_price, quantity,"
                    " created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
                    (oid, 1, mn, up, q, now, now),
                )
    finally:
        conn.close()

    from app.main import app
    with TestClient(app) as c:
        c._order_id = oid  # type: ignore[attr-defined]
        c._table_id = table_id  # type: ignore[attr-defined]
        yield c


def _login(client) -> str:
    r = client.post("/api/admin/login", json={
        "store_code": "STORE001", "username": "admin", "password": "admin1234"})
    assert r.status_code == 200, r.text
    return r.json()["token"]


def test_login_success(client):
    r = client.post("/api/admin/login", json={
        "store_code": "STORE001", "username": "admin", "password": "admin1234"})
    assert r.status_code == 200
    body = r.json()
    assert body["expires_in"] == 57600
    assert body["store_name"] == "홍길동식당"
    assert body["token"]


def test_login_wrong_password_401(client):
    r = client.post("/api/admin/login", json={
        "store_code": "STORE001", "username": "admin", "password": "nope"})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "UNAUTHORIZED"


def test_login_lockout_429(client):
    for _ in range(4):
        client.post("/api/admin/login", json={
            "store_code": "STORE001", "username": "admin", "password": "nope"})
    # 5번째 실패 → 잠금 발동(429)
    r5 = client.post("/api/admin/login", json={
        "store_code": "STORE001", "username": "admin", "password": "nope"})
    assert r5.status_code == 429
    assert r5.json()["error"]["code"] == "TOO_MANY_ATTEMPTS"
    # 잠금 중에는 올바른 비밀번호도 429
    r6 = client.post("/api/admin/login", json={
        "store_code": "STORE001", "username": "admin", "password": "admin1234"})
    assert r6.status_code == 429


def test_me_requires_auth(client):
    assert client.get("/api/admin/me").status_code == 401
    token = _login(client)
    r = client.get("/api/admin/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["username"] == "admin"


def test_dashboard_structure(client):
    token = _login(client)
    r = client.get("/api/admin/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    tables = r.json()["tables"]
    assert len(tables) == 3  # 시드 테이블 3개
    active = [t for t in tables if t["session_active"]]
    assert len(active) == 1
    card = active[0]
    assert card["table_total"] == 22000
    assert len(card["recent_orders"]) == 1
    assert card["recent_orders"][0]["item_preview"] == "김치찌개 외 1건"


def test_change_status_and_validation(client):
    token = _login(client)
    h = {"Authorization": f"Bearer {token}"}
    oid = client._order_id
    r = client.patch(f"/api/admin/orders/{oid}/status", json={"status": "preparing"}, headers=h)
    assert r.status_code == 200
    assert r.json() == {"order_id": oid, "status": "preparing"}
    # 잘못된 상태값 → 400
    rb = client.patch(f"/api/admin/orders/{oid}/status", json={"status": "done"}, headers=h)
    assert rb.status_code == 400
    assert rb.json()["error"]["code"] == "VALIDATION_ERROR"
    # 없는 주문 → 404
    rn = client.patch("/api/admin/orders/999999/status", json={"status": "completed"}, headers=h)
    assert rn.status_code == 404


def test_order_detail(client):
    token = _login(client)
    h = {"Authorization": f"Bearer {token}"}
    oid = client._order_id
    r = client.get(f"/api/admin/orders/{oid}", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["order_id"] == oid
    assert len(body["items"]) == 2
    assert body["items"][0]["line_total"] == body["items"][0]["unit_price"] * body["items"][0]["quantity"]


def test_stream_requires_auth(client):
    """인증 없으면 스트림 진입 전 401(무한 스트림 소비 없이 검증)."""
    assert client.get("/api/admin/orders/stream").status_code == 401


def test_stream_returns_event_stream_response():
    """라우트 핸들러를 직접 호출해 StreamingResponse/미디어타입만 검증(본문 미소비)."""
    import asyncio
    from starlette.responses import StreamingResponse
    from app.admin_auth.router import orders_stream
    from app.admin_auth.deps import AdminPrincipal

    principal = AdminPrincipal(admin_user_id=1, store_id=1, username="admin")
    resp = asyncio.get_event_loop().run_until_complete(
        orders_stream(principal=principal, last_event_id=None)
    )
    assert isinstance(resp, StreamingResponse)
    assert resp.media_type == "text/event-stream"
