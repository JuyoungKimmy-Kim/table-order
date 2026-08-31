"""Unit 5: 메뉴 관리 테스트 (예제 기반).

레포지토리 로직 + 라우터(API)를 검증한다. 확정 결정 반영:
  #1 메뉴 삭제: 참조 주문 있으면 409 (MENU_IN_USE)
  #2 PUT: 전체 교체 (name/price 필수)
  #3 카테고리 삭제: 하위 메뉴 있으면 409 (CATEGORY_IN_USE)
"""
from __future__ import annotations

import datetime as _dt
import sqlite3

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core import config, db, security
from app.core.errors import register_exception_handlers
from app.menu import repository as repo
from app.menu.deps import get_conn, require_admin
from app.menu.router import router as menu_router


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@pytest.fixture()
def store_conn(tmp_path):
    """스키마 적용된 임시 DB 에 단일 매장(STORE001)을 삽입한 연결.

    check_same_thread=False: TestClient 가 엔드포인트를 워커 스레드에서 실행하므로
    단일 연결을 스레드 간 공유하려면 필요하다(테스트는 요청이 직렬 실행되어 안전).
    실제 앱은 요청마다 get_conn 이 새 연결을 열어 이 문제가 없다.
    """
    db_file = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_file), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    db.apply_migrations(conn)
    now = _now()
    conn.execute(
        "INSERT INTO stores (store_code, name, created_at, updated_at) VALUES (?, ?, ?, ?)",
        (config.DEFAULT_STORE_CODE, "테스트식당", now, now),
    )
    conn.commit()
    try:
        yield conn
    finally:
        conn.close()


def _make_client(conn, *, with_auth: bool = True) -> TestClient:
    """lifespan 없는 테스트 전용 앱 (기본 DB 오염 방지)."""
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(menu_router, prefix="/api")
    app.dependency_overrides[get_conn] = lambda: conn
    if with_auth:
        app.dependency_overrides[require_admin] = lambda: {"sub": "test-admin"}
    return TestClient(app)


def _seed_category(conn, store_id, name="메인", display_order=0) -> int:
    return repo.create_category(conn, store_id, {"name": name, "display_order": display_order})["id"]


def _seed_order_item(conn, store_id, menu_id, *, table_number=1):
    """menu_id 를 참조하는 주문/항목을 만든다(삭제 가드 검증용)."""
    now = _now()
    tid = conn.execute(
        "INSERT INTO tables (store_id, table_number, password_hash, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (store_id, table_number, "x", now, now),
    ).lastrowid
    sid = conn.execute(
        "INSERT INTO table_sessions (table_id, status, opened_at, created_at, updated_at) "
        "VALUES (?, 'active', ?, ?, ?)",
        (tid, now, now, now),
    ).lastrowid
    oid = conn.execute(
        "INSERT INTO orders (session_id, table_id, order_number, status, total_amount, "
        "is_deleted, ordered_at, created_at, updated_at) "
        "VALUES (?, ?, ?, 'pending', ?, 0, ?, ?, ?)",
        (sid, tid, f"A-20260831-{table_number:04d}", 8000, now, now, now),
    ).lastrowid
    conn.execute(
        "INSERT INTO order_items (order_id, menu_id, menu_name, unit_price, quantity, "
        "created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (oid, menu_id, "김치찌개", 8000, 1, now, now),
    )
    conn.commit()


# --------------------------------------------------------------------------
# 레포지토리 로직
# --------------------------------------------------------------------------

def test_create_and_list_menu_grouped(store_conn):
    store_id = repo.get_default_store_id(store_conn)
    cat = _seed_category(store_conn, store_id)
    repo.create_menu(store_conn, store_id, {
        "category_id": cat, "name": "김치찌개", "price": 8000, "display_order": 1,
    })
    repo.create_menu(store_conn, store_id, {
        "category_id": cat, "name": "된장찌개", "price": 7000, "display_order": 0,
        "is_available": False,
    })
    store_conn.commit()

    grouped = repo.list_menus_grouped(store_conn, store_id)
    menus = grouped["categories"][0]["menus"]
    # BR-8.3: display_order ASC 정렬
    assert [m["name"] for m in menus] == ["된장찌개", "김치찌개"]
    # is_available 은 bool 로 노출, 숨김 메뉴도 관리자 목록엔 포함(BR-8.2)
    assert menus[0]["is_available"] is False
    assert menus[1]["is_available"] is True


def test_delete_menu_without_orders(store_conn):
    store_id = repo.get_default_store_id(store_conn)
    cat = _seed_category(store_conn, store_id)
    menu = repo.create_menu(store_conn, store_id, {"category_id": cat, "name": "라면", "price": 5000})
    store_conn.commit()
    repo.delete_menu(store_conn, store_id, menu["id"])
    store_conn.commit()
    assert repo.get_menu_row(store_conn, store_id, menu["id"]) is None


def test_delete_menu_with_orders_rejected(store_conn):
    from app.core.errors import Conflict
    store_id = repo.get_default_store_id(store_conn)
    cat = _seed_category(store_conn, store_id)
    menu = repo.create_menu(store_conn, store_id, {"category_id": cat, "name": "김치찌개", "price": 8000})
    store_conn.commit()
    _seed_order_item(store_conn, store_id, menu["id"])

    with pytest.raises(Conflict) as ei:
        repo.delete_menu(store_conn, store_id, menu["id"])
    assert ei.value.code == "MENU_IN_USE"
    assert ei.value.http_status == 409
    # 거부됐으므로 메뉴는 그대로 존재
    assert repo.get_menu_row(store_conn, store_id, menu["id"]) is not None


def test_delete_category_with_menus_rejected(store_conn):
    from app.core.errors import Conflict
    store_id = repo.get_default_store_id(store_conn)
    cat = _seed_category(store_conn, store_id)
    repo.create_menu(store_conn, store_id, {"category_id": cat, "name": "라면", "price": 5000})
    store_conn.commit()
    with pytest.raises(Conflict) as ei:
        repo.delete_category(store_conn, store_id, cat)
    assert ei.value.code == "CATEGORY_IN_USE"


def test_reorder_menus(store_conn):
    store_id = repo.get_default_store_id(store_conn)
    cat = _seed_category(store_conn, store_id)
    a = repo.create_menu(store_conn, store_id, {"category_id": cat, "name": "A", "price": 1000})
    b = repo.create_menu(store_conn, store_id, {"category_id": cat, "name": "B", "price": 2000})
    store_conn.commit()
    updated = repo.reorder_menus(store_conn, store_id, [
        {"menu_id": a["id"], "display_order": 5},
        {"menu_id": b["id"], "display_order": 1},
    ])
    store_conn.commit()
    assert updated == 2
    menus = repo.list_menus_grouped(store_conn, store_id)["categories"][0]["menus"]
    assert [m["name"] for m in menus] == ["B", "A"]


# --------------------------------------------------------------------------
# API (라우터)
# --------------------------------------------------------------------------

def test_api_create_menu_and_get(store_conn):
    store_id = repo.get_default_store_id(store_conn)
    cat = _seed_category(store_conn, store_id)
    client = _make_client(store_conn)
    r = client.post("/api/admin/menus", json={"category_id": cat, "name": "김치찌개", "price": 8000})
    assert r.status_code == 201
    assert r.json()["name"] == "김치찌개"
    assert r.json()["is_available"] is True

    r2 = client.get("/api/admin/menus")
    assert r2.status_code == 200
    assert r2.json()["categories"][0]["menus"][0]["name"] == "김치찌개"


def test_api_validation_error_format(store_conn):
    store_id = repo.get_default_store_id(store_conn)
    cat = _seed_category(store_conn, store_id)
    client = _make_client(store_conn)
    # price 누락 → 400 표준 포맷 (§0.2)
    r = client.post("/api/admin/menus", json={"category_id": cat, "name": "김치찌개"})
    assert r.status_code == 400
    body = r.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "price" in body["error"]["details"]


def test_api_bad_category_rejected(store_conn):
    client = _make_client(store_conn)
    r = client.post("/api/admin/menus", json={"category_id": 999, "name": "x", "price": 100})
    assert r.status_code == 400
    assert r.json()["error"]["details"].get("category_id")


def test_api_update_full_replace_and_not_found(store_conn):
    store_id = repo.get_default_store_id(store_conn)
    cat = _seed_category(store_conn, store_id)
    client = _make_client(store_conn)
    created = client.post(
        "/api/admin/menus", json={"category_id": cat, "name": "김치찌개", "price": 8000}
    ).json()
    r = client.put(f"/api/admin/menus/{created['id']}", json={
        "category_id": cat, "name": "김치찌개(대)", "price": 9000, "is_available": False,
    })
    assert r.status_code == 200
    assert r.json()["price"] == 9000
    assert r.json()["is_available"] is False

    r404 = client.put("/api/admin/menus/99999", json={"category_id": cat, "name": "x", "price": 1})
    assert r404.status_code == 404
    assert r404.json()["error"]["code"] == "MENU_NOT_FOUND"


def test_api_delete_in_use_returns_409(store_conn):
    store_id = repo.get_default_store_id(store_conn)
    cat = _seed_category(store_conn, store_id)
    client = _make_client(store_conn)
    menu = client.post(
        "/api/admin/menus", json={"category_id": cat, "name": "김치찌개", "price": 8000}
    ).json()
    _seed_order_item(store_conn, store_id, menu["id"])
    r = client.delete(f"/api/admin/menus/{menu['id']}")
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "MENU_IN_USE"


def test_api_requires_auth(store_conn):
    client = _make_client(store_conn, with_auth=False)
    # Authorization 헤더 없음 → 401
    r = client.get("/api/admin/menus")
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "UNAUTHORIZED"
    # 유효한 토큰이면 통과
    token = security.create_token({"sub": "admin"})
    r2 = client.get("/api/admin/menus", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
