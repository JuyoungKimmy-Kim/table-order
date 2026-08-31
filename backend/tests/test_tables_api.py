"""Unit 4: 테이블 & 세션 관리 API 통합 테스트 (예제 기반).

FastAPI TestClient + 임시 sqlite. 5개 엔드포인트의 정상/에러 경로를 고정한다.
lifespan(기본 DB 연결)을 트리거하지 않도록 `with` 없이 TestClient 를 사용하고,
get_conn 의존성을 임시 DB 연결로 오버라이드한다.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core import db
from app.core.security import create_token
from app.main import app
from app.tables.deps import get_conn

NOW = "2026-08-31T09:30:00Z"


def _seed_store(conn) -> int:
    cur = conn.execute(
        "INSERT INTO stores(store_code, name, created_at, updated_at) VALUES (?,?,?,?)",
        ("STORE001", "홍길동식당", NOW, NOW),
    )
    store_id = cur.lastrowid
    cur = conn.execute(
        "INSERT INTO categories(store_id, name, display_order, created_at, updated_at)"
        " VALUES (?,?,?,?,?)",
        (store_id, "메인", 0, NOW, NOW),
    )
    cat_id = cur.lastrowid
    for name, price in (("김치찌개", 8000), ("공기밥", 1000)):
        conn.execute(
            "INSERT INTO menus(store_id, category_id, name, price, description, image_url,"
            " display_order, is_available, created_at, updated_at) VALUES (?,?,?,?,?,?,?,1,?,?)",
            (store_id, cat_id, name, price, None, None, 0, NOW, NOW),
        )
    conn.commit()
    return store_id


def _seed_table(conn, store_id, number=5) -> int:
    cur = conn.execute(
        "INSERT INTO tables(store_id, table_number, password_hash, created_at, updated_at)"
        " VALUES (?,?,?,?,?)",
        (store_id, number, "x", NOW, NOW),
    )
    conn.commit()
    return cur.lastrowid


def _seed_order(conn, table_id, session_id, order_number, total, *, deleted=0,
                ordered_at=NOW) -> int:
    cur = conn.execute(
        "INSERT INTO orders(session_id, table_id, order_number, status, total_amount,"
        " is_deleted, ordered_at, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (session_id, table_id, order_number, "pending", total, deleted, ordered_at, NOW, NOW),
    )
    order_id = cur.lastrowid
    conn.execute(
        "INSERT INTO order_items(order_id, menu_id, menu_name, unit_price, quantity,"
        " created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
        (order_id, 1, "김치찌개", 8000, 2, NOW, NOW),
    )
    conn.execute(
        "INSERT INTO order_items(order_id, menu_id, menu_name, unit_price, quantity,"
        " created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
        (order_id, 2, "공기밥", 1000, 1, NOW, NOW),
    )
    conn.commit()
    return order_id


def _open_session(conn, table_id) -> int:
    cur = conn.execute(
        "INSERT INTO table_sessions(table_id, status, opened_at, created_at, updated_at)"
        " VALUES (?,?,?,?,?)",
        (table_id, "active", NOW, NOW, NOW),
    )
    conn.commit()
    return cur.lastrowid


@pytest.fixture()
def api(tmp_path):
    """파일 기반 임시 DB + store 시드 + 인증 토큰 + get_conn 오버라이드된 TestClient.

    TestClient 는 sync 엔드포인트를 워커 스레드에서 실행하므로 연결 객체를
    스레드 간 공유할 수 없다. 요청마다 동일 DB 파일에 새 연결을 열어 준다
    (커밋된 데이터는 연결 간 공유됨). 검증(assert)은 별도 verify 연결로 수행.
    """
    db_file = str(tmp_path / "test.db")
    setup = db.connect(db_file)
    db.apply_migrations(setup)
    store_id = _seed_store(setup)
    setup.close()

    async def _override_conn():
        conn = db.connect(db_file)
        try:
            yield conn
        finally:
            conn.close()

    app.dependency_overrides[get_conn] = _override_conn
    token = create_token({"store_id": store_id, "username": "admin"})
    headers = {"Authorization": f"Bearer {token}"}
    verify = db.connect(db_file)
    client = TestClient(app)
    try:
        yield client, verify, store_id, headers
    finally:
        app.dependency_overrides.clear()
        verify.close()


# --- 인증 ------------------------------------------------------------------

def test_requires_auth(api):
    client, _, _, _ = api
    r = client.post("/api/admin/tables", json={"table_number": 9, "password": "1234"})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "UNAUTHORIZED"


# --- 초기 설정 -------------------------------------------------------------

def test_create_table_ok(api):
    client, conn, store_id, headers = api
    r = client.post("/api/admin/tables", json={"table_number": 7, "password": "1234"},
                    headers=headers)
    assert r.status_code == 201
    body = r.json()
    assert body["table_number"] == 7 and isinstance(body["table_id"], int)
    # bcrypt 해시로 저장(평문 아님)
    row = conn.execute("SELECT password_hash FROM tables WHERE id=?", (body["table_id"],)).fetchone()
    assert row["password_hash"] != "1234"


def test_create_table_duplicate_conflict(api):
    client, conn, store_id, headers = api
    _seed_table(conn, store_id, number=5)
    r = client.post("/api/admin/tables", json={"table_number": 5, "password": "1234"},
                    headers=headers)
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "CONFLICT"


def test_create_table_empty_password_400(api):
    client, _, _, headers = api
    r = client.post("/api/admin/tables", json={"table_number": 8, "password": "   "},
                    headers=headers)
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


# --- 직권 삭제 -------------------------------------------------------------

def test_delete_order_recomputes_total(api):
    client, conn, store_id, headers = api
    table_id = _seed_table(conn, store_id)
    session_id = _open_session(conn, table_id)
    o1 = _seed_order(conn, table_id, session_id, "A-20260831-0001", 17000)
    _seed_order(conn, table_id, session_id, "A-20260831-0002", 5000)

    r = client.delete(f"/api/admin/orders/{o1}", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["order_id"] == o1 and body["table_id"] == table_id
    assert body["table_total"] == 5000  # 17000 삭제 → 5000 남음
    assert conn.execute("SELECT is_deleted FROM orders WHERE id=?", (o1,)).fetchone()["is_deleted"] == 1


def test_delete_order_not_found(api):
    client, _, _, headers = api
    r = client.delete("/api/admin/orders/9999", headers=headers)
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "ORDER_NOT_FOUND"


def test_delete_order_idempotent(api):
    client, conn, store_id, headers = api
    table_id = _seed_table(conn, store_id)
    session_id = _open_session(conn, table_id)
    o1 = _seed_order(conn, table_id, session_id, "A-20260831-0001", 17000)
    client.delete(f"/api/admin/orders/{o1}", headers=headers)
    r = client.delete(f"/api/admin/orders/{o1}", headers=headers)  # 재삭제
    assert r.status_code == 200
    assert r.json()["table_total"] == 0


# --- 세션 종료 -------------------------------------------------------------

def test_close_session_moves_history_and_resets(api):
    client, conn, store_id, headers = api
    table_id = _seed_table(conn, store_id)
    session_id = _open_session(conn, table_id)
    _seed_order(conn, table_id, session_id, "A-20260831-0001", 17000)
    _seed_order(conn, table_id, session_id, "A-20260831-0002", 5000)

    r = client.post(f"/api/admin/tables/{table_id}/close-session", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["closed_session_id"] == session_id and body["moved_orders"] == 2
    # 세션 closed, 이력 이동, 현재 목록 0
    assert conn.execute("SELECT status FROM table_sessions WHERE id=?", (session_id,)).fetchone()["status"] == "closed"
    assert conn.execute("SELECT COUNT(*) c FROM order_history WHERE table_id=?", (table_id,)).fetchone()["c"] == 2
    cur = client.get(f"/api/admin/tables/{table_id}/orders", headers=headers)
    assert cur.json() == []


def test_close_session_no_active_409(api):
    client, conn, store_id, headers = api
    table_id = _seed_table(conn, store_id)
    r = client.post(f"/api/admin/tables/{table_id}/close-session", headers=headers)
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "NO_ACTIVE_SESSION"


# --- 현재 주문 목록 --------------------------------------------------------

def test_current_orders_excludes_deleted(api):
    client, conn, store_id, headers = api
    table_id = _seed_table(conn, store_id)
    session_id = _open_session(conn, table_id)
    _seed_order(conn, table_id, session_id, "A-20260831-0001", 17000)
    _seed_order(conn, table_id, session_id, "A-20260831-0002", 5000, deleted=1)

    r = client.get(f"/api/admin/tables/{table_id}/orders", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 1
    assert body[0]["order_number"] == "A-20260831-0001"
    # OrderDetail 형식 + line_total 파생
    assert body[0]["items"][0]["line_total"] == 16000


# --- 과거 내역 -------------------------------------------------------------

def test_history_pagination_and_desc(api):
    client, conn, store_id, headers = api
    table_id = _seed_table(conn, store_id)
    session_id = _open_session(conn, table_id)
    _seed_order(conn, table_id, session_id, "A-20260831-0001", 1000, ordered_at="2026-08-30T10:00:00Z")
    _seed_order(conn, table_id, session_id, "A-20260831-0002", 2000, ordered_at="2026-08-31T10:00:00Z")
    client.post(f"/api/admin/tables/{table_id}/close-session", headers=headers)

    r = client.get(f"/api/admin/tables/{table_id}/history", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2 and body["page"] == 1
    # 역순: 최신(0002) 먼저, session_closed_at 포함
    assert body["items"][0]["order_number"] == "A-20260831-0002"
    assert "session_closed_at" in body["items"][0]


def test_history_date_filter(api):
    client, conn, store_id, headers = api
    table_id = _seed_table(conn, store_id)
    session_id = _open_session(conn, table_id)
    _seed_order(conn, table_id, session_id, "A-20260830-0001", 1000, ordered_at="2026-08-30T10:00:00Z")
    _seed_order(conn, table_id, session_id, "A-20260831-0001", 2000, ordered_at="2026-08-31T10:00:00Z")
    client.post(f"/api/admin/tables/{table_id}/close-session", headers=headers)

    r = client.get(f"/api/admin/tables/{table_id}/history?date_from=2026-08-31&date_to=2026-08-31",
                   headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert body["items"][0]["order_number"] == "A-20260831-0001"


def test_history_bad_date_400(api):
    client, conn, store_id, headers = api
    table_id = _seed_table(conn, store_id)
    r = client.get(f"/api/admin/tables/{table_id}/history?date_from=2026/08/31", headers=headers)
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"
