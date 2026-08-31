"""Unit 4: 비즈니스 흐름 (트랜잭션 조립 + 도메인 함수 호출 + SSE 발행).

순수 계산은 core.domain 에 위임한다(직접 계산 금지). SSE 는 core.sse.publish.
기준: business-logic-model §2 · business-rules U4-BR-2·3.
"""
from __future__ import annotations

import datetime as _dt
import sqlite3
from typing import Any

from app.core import db, sse
from app.core.domain import calc_table_total
from app.core.errors import NoActiveSession, OrderNotFound, ValidationError
from app.core.security import hash_password
from app.tables import repository as repo


# --- 테이블 초기 설정 (U4-BR-1) ------------------------------------------

def create_table(conn: sqlite3.Connection, store_id: int, table_number: int,
                 password: str) -> dict[str, int]:
    from app.core.errors import Conflict

    if not password or not password.strip():  # U4-BR-1.3
        raise ValidationError("테이블 비밀번호는 비어 있을 수 없습니다.",
                              details={"password": "필수 값입니다."})
    if repo.table_number_exists(conn, store_id, table_number):
        raise Conflict(f"이미 존재하는 테이블 번호입니다: {table_number}")
    with db.transaction(conn):
        table_id = repo.create_table(conn, store_id, table_number, hash_password(password))
    return {"table_id": table_id, "table_number": table_number}


# --- 주문 직권 삭제 (U4-BR-2) --------------------------------------------

async def delete_order(conn: sqlite3.Connection, order_id: int) -> dict[str, int]:
    order = repo.get_order(conn, order_id)
    if order is None:
        raise OrderNotFound(f"주문을 찾을 수 없습니다: {order_id}")
    table_id = order["table_id"]

    if not order["is_deleted"]:  # U4-BR-2.4 멱등
        with db.transaction(conn):
            repo.soft_delete_order(conn, order_id)

    # U4-BR-2.2 현재 active 세션 미삭제 주문으로 총액 재계산 (Unit 1 순수 함수)
    table_total = calc_table_total(repo.active_session_orders(conn, table_id))

    await sse.publish("order.deleted", {
        "order_id": order_id, "table_id": table_id, "table_total": table_total,
    })
    return {"order_id": order_id, "table_id": table_id, "table_total": table_total}


# --- 세션 종료 · 이용 완료 (U4-BR-3) -------------------------------------

async def close_session(conn: sqlite3.Connection, store_id: int,
                        table_id: int) -> dict[str, int]:
    session = repo.get_active_session(conn, table_id)
    if session is None:
        raise NoActiveSession(f"진행 중인 세션이 없습니다: table {table_id}")
    session_id = session["id"]
    closed_at = repo.utcnow_iso()

    with db.transaction(conn):  # U4-BR-3.2 원자적 이동 + 종료
        orders = repo.session_orders(conn, session_id)
        for o in orders:
            hist_id = repo.insert_history(conn, o, store_id, closed_at)
            repo.copy_items_to_history(conn, o["id"], hist_id)
        repo.close_session(conn, session_id, closed_at)

    await sse.publish("session.closed", {"table_id": table_id, "session_id": session_id})
    return {
        "table_id": table_id, "closed_session_id": session_id, "moved_orders": len(orders),
    }


# --- 현재 주문 목록 (U4-BR-4) --------------------------------------------

def current_orders(conn: sqlite3.Connection, table_id: int) -> list[dict[str, Any]]:
    session = repo.get_active_session(conn, table_id)
    if session is None:
        return []
    return [d.to_dict() for d in repo.active_undeleted_orders(conn, table_id, session["id"])]


# --- 과거 내역 (U4-BR-5) --------------------------------------------------

def _parse_date_bounds(date_from: str | None, date_to: str | None) -> tuple[str | None, str | None]:
    """YYYY-MM-DD → ISO8601 UTC 경계. [from 00:00, to+1일 00:00). 잘못된 형식 → 400."""
    def parse(s: str, field: str) -> _dt.date:
        try:
            return _dt.datetime.strptime(s, "%Y-%m-%d").date()
        except ValueError:
            raise ValidationError("날짜 형식이 올바르지 않습니다.",
                                  details={field: "YYYY-MM-DD 형식이어야 합니다."})

    lo = None if not date_from else parse(date_from, "date_from").strftime("%Y-%m-%dT00:00:00Z")
    hi = None
    if date_to:
        hi_date = parse(date_to, "date_to") + _dt.timedelta(days=1)  # 경계 포함(< 다음날)
        hi = hi_date.strftime("%Y-%m-%dT00:00:00Z")
    return lo, hi


def history(conn: sqlite3.Connection, table_id: int, date_from: str | None,
            date_to: str | None, offset: int, size: int) -> tuple[list[dict[str, Any]], int]:
    lo, hi = _parse_date_bounds(date_from, date_to)
    total = repo.count_history(conn, table_id, lo, hi)
    items = repo.history_page(conn, table_id, lo, hi, offset, size)
    return items, total
