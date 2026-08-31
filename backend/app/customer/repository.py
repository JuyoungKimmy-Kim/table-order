"""Unit 2: 고객 주문 리포지토리 (SQLite 접근, core.db 사용).

경량 함수형 리포지토리(Q6=A). 모든 함수는 sqlite3.Connection 을 받는다.
쓰기 대상: table_sessions(생성), orders, order_items, order_sequences.
그 외(stores/tables/categories/menus)는 읽기 전용.
기준: business-logic-model.md §0~4 / business-rules.md BR-C*.
"""
from __future__ import annotations

import sqlite3
from typing import Any, Sequence


# --- 읽기 (다른 유닛 소유 데이터) ---

def get_store_by_code(conn: sqlite3.Connection, store_code: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM stores WHERE store_code = ?", (store_code,)
    ).fetchone()


def get_table(conn: sqlite3.Connection, store_id: int, table_number: int) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM tables WHERE store_id = ? AND table_number = ?",
        (store_id, table_number),
    ).fetchone()


def get_table_number(conn: sqlite3.Connection, table_id: int) -> int | None:
    row = conn.execute(
        "SELECT table_number FROM tables WHERE id = ?", (table_id,)
    ).fetchone()
    return row["table_number"] if row else None


def list_categories(conn: sqlite3.Connection, store_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM categories WHERE store_id = ? "
        "ORDER BY display_order ASC, id ASC",
        (store_id,),
    ).fetchall()


def list_available_menus(conn: sqlite3.Connection, store_id: int) -> list[sqlite3.Row]:
    """is_available=1 메뉴만, 노출 순서대로 (BR-C2.2, BR-C2.3)."""
    return conn.execute(
        "SELECT * FROM menus WHERE store_id = ? AND is_available = 1 "
        "ORDER BY display_order ASC, id ASC",
        (store_id,),
    ).fetchall()


def get_menus_for_order(
    conn: sqlite3.Connection, store_id: int, menu_ids: Sequence[int]
) -> dict[int, sqlite3.Row]:
    """주문 재검증용: 요청 menu_id 들을 조회해 {id: row} 로 반환 (is_available 무관)."""
    ids = list(dict.fromkeys(menu_ids))  # 중복 제거·순서 유지
    if not ids:
        return {}
    placeholders = ",".join("?" for _ in ids)
    rows = conn.execute(
        f"SELECT * FROM menus WHERE store_id = ? AND id IN ({placeholders})",
        (store_id, *ids),
    ).fetchall()
    return {row["id"]: row for row in rows}


# --- 세션 (읽기/쓰기) ---

def get_active_session(conn: sqlite3.Connection, table_id: int) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM table_sessions WHERE table_id = ? AND status = 'active'",
        (table_id,),
    ).fetchone()


def create_active_session(conn: sqlite3.Connection, table_id: int, now: str) -> int:
    """첫 주문 시 active 세션 생성 (BR-C4.4). 부분 유니크 인덱스가 최대 1개 보장."""
    cur = conn.execute(
        "INSERT INTO table_sessions(table_id, status, opened_at, created_at, updated_at) "
        "VALUES (?, 'active', ?, ?, ?)",
        (table_id, now, now, now),
    )
    return int(cur.lastrowid)


# --- 주문번호 채번 (원자적, BR-C4.5) ---

def next_sequence(conn: sqlite3.Connection, store_id: int, seq_date: str) -> int:
    """order_sequences UPSERT 로 당일 시퀀스를 원자적으로 증가시키고 값을 반환.

    단일 트랜잭션/연결 내에서 호출되어 seq 유일성을 보장한다(단일 프로세스 가정).
    """
    conn.execute(
        "INSERT INTO order_sequences(store_id, seq_date, last_seq) VALUES (?, ?, 1) "
        "ON CONFLICT(store_id, seq_date) DO UPDATE SET last_seq = last_seq + 1",
        (store_id, seq_date),
    )
    row = conn.execute(
        "SELECT last_seq FROM order_sequences WHERE store_id = ? AND seq_date = ?",
        (store_id, seq_date),
    ).fetchone()
    return int(row["last_seq"])


# --- 주문 쓰기 ---

def insert_order(
    conn: sqlite3.Connection, session_id: int, table_id: int,
    order_number: str, total_amount: int, ordered_at: str, now: str,
) -> int:
    cur = conn.execute(
        "INSERT INTO orders(session_id, table_id, order_number, status, total_amount, "
        "is_deleted, ordered_at, created_at, updated_at) "
        "VALUES (?, ?, ?, 'pending', ?, 0, ?, ?, ?)",
        (session_id, table_id, order_number, total_amount, ordered_at, now, now),
    )
    return int(cur.lastrowid)


def insert_order_items(
    conn: sqlite3.Connection, order_id: int, items: Sequence[dict[str, Any]], now: str
) -> None:
    """items: [{menu_id, menu_name, unit_price, quantity}] 스냅샷."""
    for it in items:
        conn.execute(
            "INSERT INTO order_items(order_id, menu_id, menu_name, unit_price, quantity, "
            "created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (order_id, it["menu_id"], it["menu_name"], it["unit_price"], it["quantity"], now, now),
        )


# --- 주문 내역 조회 (BR-C5) ---

def count_session_orders(conn: sqlite3.Connection, session_id: int) -> int:
    row = conn.execute(
        "SELECT COUNT(*) AS c FROM orders WHERE session_id = ? AND is_deleted = 0",
        (session_id,),
    ).fetchone()
    return int(row["c"])


def list_session_orders(
    conn: sqlite3.Connection, session_id: int, offset: int, size: int
) -> list[sqlite3.Row]:
    """현재 세션 미삭제 주문, ordered_at 오름차순 (BR-C5.1~5.3)."""
    return conn.execute(
        "SELECT * FROM orders WHERE session_id = ? AND is_deleted = 0 "
        "ORDER BY ordered_at ASC, id ASC LIMIT ? OFFSET ?",
        (session_id, size, offset),
    ).fetchall()


def list_order_items(conn: sqlite3.Connection, order_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM order_items WHERE order_id = ? ORDER BY id ASC", (order_id,)
    ).fetchall()
