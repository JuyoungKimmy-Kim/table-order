"""방명록 리포지토리 (SQLite 접근, core.db 사용).

경량 함수형 리포지토리(customer 유닛과 동일 패턴). 모든 함수는 sqlite3.Connection 을 받는다.
쓰기 대상: guestbook_entries.
"""
from __future__ import annotations

import sqlite3


def insert_entry(
    conn: sqlite3.Connection, store_id: int, table_id: int | None,
    author_name: str | None, image_data: str, now: str,
) -> int:
    cur = conn.execute(
        "INSERT INTO guestbook_entries(store_id, table_id, author_name, image_data, created_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (store_id, table_id, author_name, image_data, now),
    )
    return int(cur.lastrowid)


def count_by_store(conn: sqlite3.Connection, store_id: int) -> int:
    row = conn.execute(
        "SELECT COUNT(*) AS c FROM guestbook_entries WHERE store_id = ?",
        (store_id,),
    ).fetchone()
    return int(row["c"])


def list_by_store(
    conn: sqlite3.Connection, store_id: int, offset: int, size: int
) -> list[sqlite3.Row]:
    """매장 방명록을 최신순(created_at 역순)으로 페이지 조회."""
    return conn.execute(
        "SELECT * FROM guestbook_entries WHERE store_id = ? "
        "ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?",
        (store_id, size, offset),
    ).fetchall()
