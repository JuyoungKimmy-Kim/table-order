"""Unit 5: 메뉴/카테고리 데이터 접근 계층 (SQLite, ORM 없음 — Q6=A).

기준: Integration Contract §1.5(categories), §1.6(menus), §3.4 / business-rules BR-8, BR-9.
쓰기 작업은 호출측에서 db.transaction() 으로 감싼다.
"""
from __future__ import annotations

import datetime as _dt
import sqlite3
from typing import Any, Mapping, Sequence

from app.core import config
from app.core.errors import Conflict, MenuNotFound, NotFound, ValidationError


def _now_iso() -> str:
    """UTC ISO8601 문자열 (BR-1.2)."""
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --------------------------------------------------------------------------
# 매장 (단일 매장 MVP — store_code 로 store_id 해석)
# --------------------------------------------------------------------------

def get_default_store_id(conn: sqlite3.Connection) -> int:
    """단일 매장 가정: config.DEFAULT_STORE_CODE 에 해당하는 store.id 반환."""
    row = conn.execute(
        "SELECT id FROM stores WHERE store_code = ?", (config.DEFAULT_STORE_CODE,)
    ).fetchone()
    if row is None:
        raise NotFound(
            "매장이 초기화되지 않았습니다. seed 를 실행하세요.",
            code="STORE_NOT_FOUND",
        )
    return int(row["id"])


# --------------------------------------------------------------------------
# 직렬화 (§4 스타일 — is_available 은 bool 로 노출)
# --------------------------------------------------------------------------

def menu_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "category_id": row["category_id"],
        "name": row["name"],
        "price": row["price"],
        "description": row["description"],
        "image_url": row["image_url"],
        "display_order": row["display_order"],
        "is_available": bool(row["is_available"]),
    }


def category_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "name": row["name"],
        "display_order": row["display_order"],
    }


# --------------------------------------------------------------------------
# 카테고리
# --------------------------------------------------------------------------

def list_categories(conn: sqlite3.Connection, store_id: int) -> list[dict[str, Any]]:
    """카테고리 목록 (BR-8.3: display_order ASC, id ASC)."""
    rows = conn.execute(
        "SELECT * FROM categories WHERE store_id = ? "
        "ORDER BY display_order ASC, id ASC",
        (store_id,),
    ).fetchall()
    return [category_to_dict(r) for r in rows]


def get_category_row(conn: sqlite3.Connection, store_id: int, category_id: int) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM categories WHERE id = ? AND store_id = ?",
        (category_id, store_id),
    ).fetchone()


def create_category(conn: sqlite3.Connection, store_id: int, payload: Mapping[str, Any]) -> dict[str, Any]:
    now = _now_iso()
    cur = conn.execute(
        "INSERT INTO categories (store_id, name, display_order, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (store_id, payload["name"].strip(), int(payload.get("display_order", 0)), now, now),
    )
    return category_to_dict(get_category_row(conn, store_id, cur.lastrowid))


def update_category(conn: sqlite3.Connection, store_id: int, category_id: int,
                    payload: Mapping[str, Any]) -> dict[str, Any]:
    if get_category_row(conn, store_id, category_id) is None:
        raise NotFound("해당 카테고리를 찾을 수 없습니다.", code="CATEGORY_NOT_FOUND")
    conn.execute(
        "UPDATE categories SET name = ?, display_order = ?, updated_at = ? "
        "WHERE id = ? AND store_id = ?",
        (payload["name"].strip(), int(payload.get("display_order", 0)), _now_iso(),
         category_id, store_id),
    )
    return category_to_dict(get_category_row(conn, store_id, category_id))


def delete_category(conn: sqlite3.Connection, store_id: int, category_id: int) -> None:
    """카테고리 삭제. 하위 메뉴가 있으면 409 (결정 #3, FK 일관)."""
    if get_category_row(conn, store_id, category_id) is None:
        raise NotFound("해당 카테고리를 찾을 수 없습니다.", code="CATEGORY_NOT_FOUND")
    menu_count = conn.execute(
        "SELECT COUNT(*) AS c FROM menus WHERE category_id = ?", (category_id,)
    ).fetchone()["c"]
    if menu_count > 0:
        raise Conflict(
            "메뉴가 남아 있는 카테고리는 삭제할 수 없습니다. 메뉴를 먼저 이동/삭제하세요.",
            details={"menu_count": menu_count},
            code="CATEGORY_IN_USE",
        )
    conn.execute("DELETE FROM categories WHERE id = ? AND store_id = ?", (category_id, store_id))


# --------------------------------------------------------------------------
# 메뉴
# --------------------------------------------------------------------------

def list_menus_grouped(conn: sqlite3.Connection, store_id: int) -> dict[str, Any]:
    """카테고리별 메뉴(§3.4.1: is_available 무관 전체 포함, BR-8.2/8.3)."""
    categories = conn.execute(
        "SELECT * FROM categories WHERE store_id = ? ORDER BY display_order ASC, id ASC",
        (store_id,),
    ).fetchall()
    result = []
    for cat in categories:
        menus = conn.execute(
            "SELECT * FROM menus WHERE category_id = ? "
            "ORDER BY display_order ASC, id ASC",
            (cat["id"],),
        ).fetchall()
        result.append({
            "id": cat["id"],
            "name": cat["name"],
            "display_order": cat["display_order"],
            "menus": [menu_to_dict(m) for m in menus],
        })
    return {"categories": result}


def get_menu_row(conn: sqlite3.Connection, store_id: int, menu_id: int) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM menus WHERE id = ? AND store_id = ?", (menu_id, store_id)
    ).fetchone()


def _require_category(conn: sqlite3.Connection, store_id: int, category_id: Any) -> int:
    """category_id 가 해당 매장에 존재하는지 확인. 없으면 400 VALIDATION_ERROR."""
    if not isinstance(category_id, int) or isinstance(category_id, bool):
        raise ValidationError("입력이 올바르지 않습니다.",
                              details={"category_id": "정수여야 합니다."})
    if get_category_row(conn, store_id, category_id) is None:
        raise ValidationError("입력이 올바르지 않습니다.",
                              details={"category_id": "존재하지 않는 카테고리입니다."})
    return category_id


def create_menu(conn: sqlite3.Connection, store_id: int, payload: Mapping[str, Any]) -> dict[str, Any]:
    """메뉴 등록(§3.4.2). name/price 는 호출 전에 validate_menu_payload 로 검증됨."""
    category_id = _require_category(conn, store_id, payload.get("category_id"))
    now = _now_iso()
    cur = conn.execute(
        "INSERT INTO menus "
        "(store_id, category_id, name, price, description, image_url, display_order, "
        " is_available, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            store_id, category_id, payload["name"].strip(), int(payload["price"]),
            payload.get("description"), payload.get("image_url"),
            int(payload.get("display_order", 0)),
            1 if payload.get("is_available", True) else 0,
            now, now,
        ),
    )
    return menu_to_dict(get_menu_row(conn, store_id, cur.lastrowid))


def update_menu(conn: sqlite3.Connection, store_id: int, menu_id: int,
                payload: Mapping[str, Any]) -> dict[str, Any]:
    """메뉴 수정(§3.4.3) — 전체 교체(결정 #2)."""
    if get_menu_row(conn, store_id, menu_id) is None:
        raise MenuNotFound("해당 메뉴를 찾을 수 없습니다.")
    category_id = _require_category(conn, store_id, payload.get("category_id"))
    conn.execute(
        "UPDATE menus SET category_id = ?, name = ?, price = ?, description = ?, "
        "image_url = ?, display_order = ?, is_available = ?, updated_at = ? "
        "WHERE id = ? AND store_id = ?",
        (
            category_id, payload["name"].strip(), int(payload["price"]),
            payload.get("description"), payload.get("image_url"),
            int(payload.get("display_order", 0)),
            1 if payload.get("is_available", True) else 0,
            _now_iso(), menu_id, store_id,
        ),
    )
    return menu_to_dict(get_menu_row(conn, store_id, menu_id))


def _order_reference_count(conn: sqlite3.Connection, menu_id: int) -> int:
    """이 메뉴를 참조하는 주문 항목 수(현재 주문 + 과거 이력)."""
    live = conn.execute(
        "SELECT COUNT(*) AS c FROM order_items WHERE menu_id = ?", (menu_id,)
    ).fetchone()["c"]
    hist = conn.execute(
        "SELECT COUNT(*) AS c FROM order_history_items WHERE menu_id = ?", (menu_id,)
    ).fetchone()["c"]
    return live + hist


def delete_menu(conn: sqlite3.Connection, store_id: int, menu_id: int) -> None:
    """메뉴 삭제(§3.4.4). 참조 주문이 있으면 409 (결정 #1=a).

    order_items.menu_id 는 NOT NULL FK 이므로 참조가 있으면 물리삭제가 무결성을
    위반한다. 스냅샷(menu_name/unit_price)은 유지되지만 이력 추적을 위해 참조가
    존재하는 메뉴는 삭제를 거부한다.
    """
    if get_menu_row(conn, store_id, menu_id) is None:
        raise MenuNotFound("해당 메뉴를 찾을 수 없습니다.")
    ref_count = _order_reference_count(conn, menu_id)
    if ref_count > 0:
        raise Conflict(
            "주문 내역이 있는 메뉴는 삭제할 수 없습니다. 대신 노출을 끄세요(is_available=false).",
            details={"order_reference_count": ref_count},
            code="MENU_IN_USE",
        )
    conn.execute("DELETE FROM menus WHERE id = ? AND store_id = ?", (menu_id, store_id))


def reorder_menus(conn: sqlite3.Connection, store_id: int,
                  orders: Sequence[Mapping[str, Any]]) -> int:
    """노출 순서 일괄 조정(§3.4.5). 반환: 실제 갱신된 행 수."""
    if not isinstance(orders, list):
        raise ValidationError("입력이 올바르지 않습니다.",
                              details={"orders": "배열이어야 합니다."})
    now = _now_iso()
    updated = 0
    for idx, item in enumerate(orders):
        menu_id = item.get("menu_id")
        display_order = item.get("display_order")
        if not isinstance(menu_id, int) or isinstance(menu_id, bool):
            raise ValidationError("입력이 올바르지 않습니다.",
                                  details={f"orders[{idx}].menu_id": "정수여야 합니다."})
        if not isinstance(display_order, int) or isinstance(display_order, bool):
            raise ValidationError("입력이 올바르지 않습니다.",
                                  details={f"orders[{idx}].display_order": "정수여야 합니다."})
        cur = conn.execute(
            "UPDATE menus SET display_order = ?, updated_at = ? WHERE id = ? AND store_id = ?",
            (display_order, now, menu_id, store_id),
        )
        updated += cur.rowcount
    return updated
