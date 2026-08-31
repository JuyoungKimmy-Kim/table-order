"""Unit 3: 서비스 레이어 (비즈니스 오케스트레이션).

Unit 1 코어를 조합한다: security(해싱/JWT), domain.calc_table_total,
models(OrderSummary/OrderDetail), validation.validate_order_status,
sse.publish, errors, db.
"""
from __future__ import annotations

import sqlite3
from typing import Any

from app.core import config, security
from app.core import sse
from app.core.domain import calc_table_total
from app.core.errors import Unauthorized, TooManyAttempts, OrderNotFound
from app.core.models import OrderDetail, OrderItemDetail, OrderSummary, make_item_preview
from app.core.validation import validate_order_status

from app.admin_auth import attempts
from app.admin_auth import repository as repo
from app.admin_auth.attempts import LoginAttemptTracker
from app.admin_auth.deps import AdminPrincipal
from app.admin_auth.logic import build_admin_claims, select_recent_orders


# --- 인증 (§3.2.1) ---

def login(conn: sqlite3.Connection, store_code: str, username: str, password: str,
          *, tracker: LoginAttemptTracker = None) -> dict[str, Any]:
    """관리자 로그인. 성공 시 {token, expires_in, store_name}.

    실패는 원인(매장/사용자/비밀번호)을 구분하지 않고 401(BR-A1.3).
    잠금 중이면 인증 시도 없이 429(BR-A2.2).

    tracker 는 호출 시점에 모듈 전역(attempts.tracker)을 해석한다
    (테스트에서 monkeypatch 로 교체 가능).
    """
    if tracker is None:
        tracker = attempts.tracker
    if tracker.is_locked(store_code, username):
        raise TooManyAttempts("로그인 시도가 많습니다. 잠시 후 다시 시도하세요.")

    store = repo.get_store_by_code(conn, store_code)
    admin = repo.get_admin(conn, store["id"], username) if store else None

    ok = bool(admin) and security.verify_password(password, admin["password_hash"])
    decision = tracker.record(store_code, username, success=ok)
    if not ok:
        # 방금 실패로 잠금이 발동된 경우엔 429, 그 외는 401 (원인 비노출).
        if decision.locked:
            raise TooManyAttempts("로그인 시도가 많습니다. 잠시 후 다시 시도하세요.")
        raise Unauthorized("아이디 또는 비밀번호가 올바르지 않습니다.")

    claims = build_admin_claims({"id": admin["id"], "store_id": admin["store_id"],
                                 "username": admin["username"]})
    token = security.create_token(claims)
    return {"token": token, "expires_in": config.JWT_EXPIRE_SECONDS, "store_name": store["name"]}


def me(principal: AdminPrincipal) -> dict[str, Any]:
    """세션 확인 (§3.2.2). claims 만으로 응답(DB 재조회 없음, Q3=A)."""
    return {"username": principal.username, "store_id": principal.store_id}


# --- 대시보드 (§3.2.4) ---

def build_dashboard(conn: sqlite3.Connection, store_id: int) -> dict[str, Any]:
    """매장 전체 테이블의 카드 목록 조립 (BR-A5)."""
    cards: list[dict[str, Any]] = []
    for table in repo.list_tables(conn, store_id):
        session = repo.get_active_session(conn, table["id"])
        if session is None:
            cards.append({
                "table_id": table["id"], "table_number": table["table_number"],
                "session_active": False, "table_total": 0, "recent_orders": [],
            })
            continue
        orders = repo.list_session_orders(conn, session["id"])
        total = calc_table_total(orders)  # Unit 1 순수함수 (직접 계산 금지)
        recent = select_recent_orders(orders)
        summaries = [_order_summary(conn, table["table_number"], o).to_dict() for o in recent]
        cards.append({
            "table_id": table["id"], "table_number": table["table_number"],
            "session_active": True, "table_total": total, "recent_orders": summaries,
        })
    return {"tables": cards}


def _order_summary(conn: sqlite3.Connection, table_number: int, order: dict[str, Any]) -> OrderSummary:
    items = [OrderItemDetail(menu_name=r["menu_name"], unit_price=r["unit_price"],
                             quantity=r["quantity"]) for r in repo.get_order_items(conn, order["id"])]
    return OrderSummary(
        order_id=order["id"], order_number=order["order_number"],
        table_id=order["table_id"], table_number=table_number,
        status=order["status"], total_amount=order["total_amount"],
        item_preview=make_item_preview(items), ordered_at=order["ordered_at"],
    )


# --- 주문 상세 (§3.2.6) ---

def get_order_detail(conn: sqlite3.Connection, order_id: int) -> dict[str, Any]:
    order = repo.get_order(conn, order_id)
    if order is None or order["is_deleted"]:
        raise OrderNotFound("주문을 찾을 수 없습니다.")
    table = repo.get_table(conn, order["table_id"])
    items = [OrderItemDetail(menu_name=r["menu_name"], unit_price=r["unit_price"],
                             quantity=r["quantity"]) for r in repo.get_order_items(conn, order_id)]
    detail = OrderDetail(
        order_id=order["id"], order_number=order["order_number"],
        table_id=order["table_id"], table_number=table["table_number"] if table else 0,
        status=order["status"], total_amount=order["total_amount"],
        ordered_at=order["ordered_at"], items=items,
    )
    return detail.to_dict()


# --- 상태 변경 (§3.2.5) ---

async def change_status(conn: sqlite3.Connection, order_id: int, status: str) -> dict[str, Any]:
    """주문 상태 변경 후 order.status_changed SSE 발행 (BR-A4)."""
    validate_order_status(status)  # Unit 1 검증 재사용 → 잘못된 값은 400
    order = repo.get_order(conn, order_id)
    if order is None or order["is_deleted"]:
        raise OrderNotFound("주문을 찾을 수 없습니다.")
    repo.update_order_status(conn, order_id, status)
    conn.commit()
    await sse.publish("order.status_changed",
                      {"order_id": order_id, "table_id": order["table_id"], "status": status})
    return {"order_id": order_id, "status": status}
