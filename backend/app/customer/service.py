"""Unit 2: 고객 주문 비즈니스 서비스 (BR-C1~C6).

Unit 1 core 순수함수/유틸을 호출하며 도메인 계산을 직접 하지 않는다.
주문 생성은 단일 트랜잭션으로 처리하고, SSE 발행은 커밋 이후 수행한다(BR-C4.8).
"""
from __future__ import annotations

import datetime as _dt
import sqlite3
from typing import Any, Sequence

from app.core import config, domain, pagination, security, sse
from app.core.db import transaction
from app.core.errors import (
    AppError, MenuNotFound, MenuUnavailable, Unauthorized,
)
from app.core.models import OrderDetail, OrderItemDetail, OrderSummary, make_item_preview
from app.core.validation import validate_order_items
from app.customer import repository as repo


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --- 3.1.1 로그인 (BR-C1) ---

def login(conn: sqlite3.Connection, store_code: str, table_number: int, password: str) -> dict[str, Any]:
    store = repo.get_store_by_code(conn, store_code)
    if store is None:
        raise Unauthorized("로그인 정보를 확인하세요.")
    table = repo.get_table(conn, store["id"], table_number)
    if table is None or not security.verify_password(password, table["password_hash"]):
        raise Unauthorized("로그인 정보를 확인하세요.")
    token = security.create_token({
        # JWT 표준상 sub 는 문자열이어야 함(PyJWT 가 디코드 시 검증). 정수 id 는 문자열로 보관.
        "sub": str(table["id"]),
        "store_id": store["id"],
        "table_number": table["table_number"],
    })
    return {
        "table_token": token,
        "table_id": table["id"],
        "table_number": table["table_number"],
        "store_name": store["name"],
    }


# --- 3.1.2 메뉴 조회 (BR-C2) ---

def get_menus(conn: sqlite3.Connection, store_id: int) -> dict[str, Any]:
    categories = repo.list_categories(conn, store_id)
    menus = repo.list_available_menus(conn, store_id)
    by_cat: dict[int, list[dict[str, Any]]] = {}
    for m in menus:  # 쿼리에서 이미 display_order, id 정렬됨
        by_cat.setdefault(m["category_id"], []).append({
            "id": m["id"], "name": m["name"], "price": m["price"],
            "description": m["description"], "image_url": m["image_url"],
            "display_order": m["display_order"], "is_available": bool(m["is_available"]),
        })
    result = [
        {"id": c["id"], "name": c["name"], "display_order": c["display_order"],
         "menus": by_cat.get(c["id"], [])}
        for c in categories
    ]
    return {"categories": result}


# --- 3.1.4 주문 생성 (BR-C4) ---

async def create_order(
    conn: sqlite3.Connection, table_id: int, store_id: int, items: Sequence[dict[str, Any]]
) -> dict[str, Any]:
    validate_order_items(items)  # 400 VALIDATION_ERROR (BR-C4.1)

    now = _now()
    today = _dt.datetime.now(_dt.timezone.utc).date()
    menu_ids = [int(it["menu_id"]) for it in items]

    with transaction(conn):
        # 재검증 (BR-C4.2): 미존재 → 404, 품절 → 409. 문제 menu_id 를 details 로 반환.
        found = repo.get_menus_for_order(conn, store_id, menu_ids)
        not_found = sorted({mid for mid in menu_ids if mid not in found})
        if not_found:
            raise MenuNotFound("일부 메뉴를 찾을 수 없습니다.",
                               details={"not_found_menu_ids": not_found})
        unavailable = sorted({mid for mid in menu_ids if not found[mid]["is_available"]})
        if unavailable:
            raise MenuUnavailable("일부 메뉴는 현재 주문할 수 없습니다.",
                                  details={"unavailable_menu_ids": unavailable})

        # 스냅샷 + 서버 총액 재계산 (BR-C4.3)
        snapshot = [
            {"menu_id": found[int(it["menu_id"])]["id"],
             "menu_name": found[int(it["menu_id"])]["name"],
             "unit_price": found[int(it["menu_id"])]["price"],
             "quantity": int(it["quantity"])}
            for it in items
        ]
        total = domain.calc_order_total(snapshot)

        # 세션 확보 (BR-C4.4)
        session = repo.get_active_session(conn, table_id)
        session_id = session["id"] if session else repo.create_active_session(conn, table_id, now)

        # 주문번호 채번 (BR-C4.5)
        seq = repo.next_sequence(conn, store_id, today.strftime("%Y%m%d"))
        if seq > 9999:
            raise AppError("당일 주문 한도를 초과했습니다.")  # 500 INTERNAL_ERROR
        order_number = domain.order_number_format(config.ORDER_NUMBER_PREFIX, today, seq)

        # 저장 (BR-C4.6)
        order_id = repo.insert_order(conn, session_id, table_id, order_number, total, now, now)
        repo.insert_order_items(conn, order_id, snapshot, now)
    # ---- 커밋 완료 ----

    # SSE 발행 (BR-C4.8, 커밋 이후)
    table_number = repo.get_table_number(conn, table_id)
    summary = OrderSummary(
        order_id=order_id, order_number=order_number, table_id=table_id,
        table_number=table_number or 0, status="pending", total_amount=total,
        item_preview=make_item_preview([
            OrderItemDetail(menu_name=s["menu_name"], unit_price=s["unit_price"], quantity=s["quantity"])
            for s in snapshot
        ]),
        ordered_at=now,
    )
    await sse.publish("order.created", summary.to_dict())

    return {
        "order_id": order_id, "order_number": order_number,
        "total_amount": total, "status": "pending", "ordered_at": now,
    }


# --- 3.1.5 현재 세션 주문 내역 (BR-C5) ---

def list_orders(conn: sqlite3.Connection, table_id: int, page: int, size: int) -> dict[str, Any]:
    p, s = pagination.normalize(page, size)
    session = repo.get_active_session(conn, table_id)
    if session is None:
        return pagination.paginate_response([], p, s, 0)

    total = repo.count_session_orders(conn, session["id"])
    rows = repo.list_session_orders(conn, session["id"], pagination.offset(p, s), s)
    table_number = repo.get_table_number(conn, table_id) or 0

    details = []
    for o in rows:
        items = repo.list_order_items(conn, o["id"])
        details.append(OrderDetail(
            order_id=o["id"], order_number=o["order_number"], table_id=o["table_id"],
            table_number=table_number, status=o["status"], total_amount=o["total_amount"],
            ordered_at=o["ordered_at"],
            items=[OrderItemDetail(menu_name=it["menu_name"], unit_price=it["unit_price"],
                                   quantity=it["quantity"]) for it in items],
        ).to_dict())
    return pagination.paginate_response(details, p, s, total)
