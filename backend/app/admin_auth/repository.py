"""Unit 3: 데이터 접근 (읽기 위주 + 상태 UPDATE).

Unit 1 `app.core.db` 연결을 사용한다. 스키마는 Unit 1 소유(변경 없음).
반환은 sqlite3.Row / dict 로, 서비스 레이어가 DTO 로 조립한다.
"""
from __future__ import annotations

import sqlite3
from typing import Any, Optional


def get_store_by_code(conn: sqlite3.Connection, store_code: str) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT id, store_code, name FROM stores WHERE store_code = ?",
        (store_code,),
    ).fetchone()


def get_admin(conn: sqlite3.Connection, store_id: int, username: str) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT id, store_id, username, password_hash FROM admin_users "
        "WHERE store_id = ? AND username = ?",
        (store_id, username),
    ).fetchone()


def list_tables(conn: sqlite3.Connection, store_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT id, store_id, table_number FROM tables "
        "WHERE store_id = ? ORDER BY table_number ASC",
        (store_id,),
    ).fetchall()


def get_active_session(conn: sqlite3.Connection, table_id: int) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT id, table_id, status, opened_at, closed_at FROM table_sessions "
        "WHERE table_id = ? AND status = 'active'",
        (table_id,),
    ).fetchone()


def list_session_orders(conn: sqlite3.Connection, session_id: int) -> list[dict[str, Any]]:
    """세션의 주문 목록(항목 미포함). is_deleted 포함하여 반환(총액 계산은 순수함수가 필터)."""
    rows = conn.execute(
        "SELECT id, session_id, table_id, order_number, status, total_amount, "
        "is_deleted, ordered_at FROM orders WHERE session_id = ? "
        "ORDER BY ordered_at DESC, id DESC",
        (session_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def get_order(conn: sqlite3.Connection, order_id: int) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT id, session_id, table_id, order_number, status, total_amount, "
        "is_deleted, ordered_at FROM orders WHERE id = ?",
        (order_id,),
    ).fetchone()


def get_order_items(conn: sqlite3.Connection, order_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT menu_name, unit_price, quantity FROM order_items "
        "WHERE order_id = ? ORDER BY id ASC",
        (order_id,),
    ).fetchall()


def get_table(conn: sqlite3.Connection, table_id: int) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT id, store_id, table_number FROM tables WHERE id = ?",
        (table_id,),
    ).fetchone()


def update_order_status(conn: sqlite3.Connection, order_id: int, status: str) -> int:
    """orders.status UPDATE. 영향 행 수 반환(0=대상 없음)."""
    cur = conn.execute(
        "UPDATE orders SET status = ?, updated_at = ? WHERE id = ? AND is_deleted = 0",
        (status, _now_iso(), order_id),
    )
    return cur.rowcount


def _now_iso() -> str:
    import datetime as _dt
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
