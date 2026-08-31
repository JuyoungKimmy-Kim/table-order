"""Unit 4: sqlite 접근 계층 (tables / table_sessions / orders / order_history).

순수 I/O. 비즈니스 흐름은 service.py 가 조립한다. 모든 시각은 UTC ISO8601.
기준: Integration Contract §1 스키마 · business-logic-model §3.
"""
from __future__ import annotations

import datetime as _dt
import sqlite3
from typing import Any

from app.core.models import OrderDetail, OrderItemDetail


def utcnow_iso() -> str:
    """UTC ISO8601 문자열(초 단위). seed.py 와 동일 포맷."""
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --- tables ---------------------------------------------------------------

def table_number_exists(conn: sqlite3.Connection, store_id: int, table_number: int) -> bool:
    row = conn.execute(
        "SELECT 1 FROM tables WHERE store_id = ? AND table_number = ?",
        (store_id, table_number),
    ).fetchone()
    return row is not None


def create_table(conn: sqlite3.Connection, store_id: int, table_number: int,
                 password_hash: str) -> int:
    now = utcnow_iso()
    cur = conn.execute(
        "INSERT INTO tables(store_id, table_number, password_hash, created_at, updated_at)"
        " VALUES (?,?,?,?,?)",
        (store_id, table_number, password_hash, now, now),
    )
    return int(cur.lastrowid)


# --- orders ---------------------------------------------------------------

def get_order(conn: sqlite3.Connection, order_id: int) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()


def soft_delete_order(conn: sqlite3.Connection, order_id: int) -> None:
    conn.execute(
        "UPDATE orders SET is_deleted = 1, updated_at = ? WHERE id = ?",
        (utcnow_iso(), order_id),
    )


def active_session_orders(conn: sqlite3.Connection, table_id: int) -> list[dict[str, Any]]:
    """현재 active 세션에 속한 주문(삭제 포함). calc_table_total 입력용 {total_amount,is_deleted}."""
    rows = conn.execute(
        "SELECT o.total_amount, o.is_deleted FROM orders o"
        " JOIN table_sessions s ON s.id = o.session_id"
        " WHERE o.table_id = ? AND s.status = 'active'",
        (table_id,),
    ).fetchall()
    return [{"total_amount": r["total_amount"], "is_deleted": r["is_deleted"]} for r in rows]


# --- sessions -------------------------------------------------------------

def get_active_session(conn: sqlite3.Connection, table_id: int) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM table_sessions WHERE table_id = ? AND status = 'active'",
        (table_id,),
    ).fetchone()


def session_orders(conn: sqlite3.Connection, session_id: int) -> list[sqlite3.Row]:
    """세션의 모든 주문(삭제 포함) — 이력 이동용."""
    return conn.execute(
        "SELECT * FROM orders WHERE session_id = ? ORDER BY ordered_at ASC",
        (session_id,),
    ).fetchall()


def close_session(conn: sqlite3.Connection, session_id: int, closed_at: str) -> None:
    conn.execute(
        "UPDATE table_sessions SET status = 'closed', closed_at = ?, updated_at = ? WHERE id = ?",
        (closed_at, closed_at, session_id),
    )


# --- order_history (세션 종료 시 이동) ------------------------------------

def insert_history(conn: sqlite3.Connection, order: sqlite3.Row, store_id: int,
                   session_closed_at: str) -> int:
    now = utcnow_iso()
    cur = conn.execute(
        "INSERT INTO order_history(original_order_id, store_id, session_id, table_id,"
        " order_number, status, total_amount, is_deleted, ordered_at, session_closed_at, created_at)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (order["id"], store_id, order["session_id"], order["table_id"],
         order["order_number"], order["status"], order["total_amount"],
         order["is_deleted"], order["ordered_at"], session_closed_at, now),
    )
    return int(cur.lastrowid)


def copy_items_to_history(conn: sqlite3.Connection, order_id: int, history_order_id: int) -> None:
    now = utcnow_iso()
    conn.execute(
        "INSERT INTO order_history_items(history_order_id, menu_id, menu_name, unit_price,"
        " quantity, created_at)"
        " SELECT ?, menu_id, menu_name, unit_price, quantity, ? FROM order_items WHERE order_id = ?",
        (history_order_id, now, order_id),
    )


# --- 조회 (OrderDetail 조립) ----------------------------------------------

def _items_for_order(conn: sqlite3.Connection, order_id: int) -> list[OrderItemDetail]:
    rows = conn.execute(
        "SELECT menu_name, unit_price, quantity FROM order_items WHERE order_id = ? ORDER BY id ASC",
        (order_id,),
    ).fetchall()
    return [OrderItemDetail(r["menu_name"], r["unit_price"], r["quantity"]) for r in rows]


def _items_for_history(conn: sqlite3.Connection, history_order_id: int) -> list[OrderItemDetail]:
    rows = conn.execute(
        "SELECT menu_name, unit_price, quantity FROM order_history_items"
        " WHERE history_order_id = ? ORDER BY id ASC",
        (history_order_id,),
    ).fetchall()
    return [OrderItemDetail(r["menu_name"], r["unit_price"], r["quantity"]) for r in rows]


def active_undeleted_orders(conn: sqlite3.Connection, table_id: int,
                            session_id: int) -> list[OrderDetail]:
    """현재 세션의 미삭제 주문 OrderDetail 목록 (U4-BR-4). ordered_at ASC."""
    rows = conn.execute(
        "SELECT o.id, o.order_number, o.table_id, t.table_number, o.status,"
        " o.total_amount, o.ordered_at FROM orders o"
        " JOIN tables t ON t.id = o.table_id"
        " WHERE o.session_id = ? AND o.is_deleted = 0"
        " ORDER BY o.ordered_at ASC, o.id ASC",
        (session_id,),
    ).fetchall()
    return [
        OrderDetail(
            order_id=r["id"], order_number=r["order_number"], table_id=r["table_id"],
            table_number=r["table_number"], status=r["status"],
            total_amount=r["total_amount"], ordered_at=r["ordered_at"],
            items=_items_for_order(conn, r["id"]),
        )
        for r in rows
    ]


def count_history(conn: sqlite3.Connection, table_id: int,
                  lo: str | None, hi: str | None) -> int:
    sql = "SELECT COUNT(*) AS c FROM order_history WHERE table_id = ?"
    params: list[Any] = [table_id]
    if lo is not None:
        sql += " AND ordered_at >= ?"
        params.append(lo)
    if hi is not None:
        sql += " AND ordered_at < ?"
        params.append(hi)
    return int(conn.execute(sql, params).fetchone()["c"])


def history_page(conn: sqlite3.Connection, table_id: int, lo: str | None, hi: str | None,
                 offset: int, size: int) -> list[dict[str, Any]]:
    """과거 내역 페이지 (U4-BR-5). ordered_at DESC. 각 항목에 session_closed_at 포함."""
    sql = (
        "SELECT h.id, h.original_order_id, h.order_number, h.table_id, t.table_number,"
        " h.status, h.total_amount, h.ordered_at, h.session_closed_at FROM order_history h"
        " JOIN tables t ON t.id = h.table_id WHERE h.table_id = ?"
    )
    params: list[Any] = [table_id]
    if lo is not None:
        sql += " AND h.ordered_at >= ?"
        params.append(lo)
    if hi is not None:
        sql += " AND h.ordered_at < ?"
        params.append(hi)
    sql += " ORDER BY h.ordered_at DESC, h.id DESC LIMIT ? OFFSET ?"
    params += [size, offset]

    result: list[dict[str, Any]] = []
    for r in conn.execute(sql, params).fetchall():
        detail = OrderDetail(
            order_id=r["id"], order_number=r["order_number"], table_id=r["table_id"],
            table_number=r["table_number"], status=r["status"],
            total_amount=r["total_amount"], ordered_at=r["ordered_at"],
            items=_items_for_history(conn, r["id"]),
        ).to_dict()
        detail["session_closed_at"] = r["session_closed_at"]
        result.append(detail)
    return result
