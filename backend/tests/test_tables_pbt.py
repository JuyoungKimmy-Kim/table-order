"""Unit 4: 속성 기반 테스트 (PBT — business-logic-model §6).

DB I/O 가 얽혀 있어 순수 PBT 대상은 제한적이다. 여기서는 상태 기반 불변식을
Hypothesis 로 검증한다. 각 예제는 독립 in-memory DB 를 사용(상태 누수 방지).

강제 규칙 관점:
- PBT-03 (Invariant): 세션 종료 보존/총액 리셋, 삭제 후 총액 재계산.
- 제너레이터는 Unit 1 generators 를 재사용 가능하나, 여기서는 간단한 로컬 전략 사용.
"""
from __future__ import annotations

import asyncio

from hypothesis import given, settings
from hypothesis import strategies as st

from app.core import db
from app.core.domain import calc_table_total
from app.tables import repository as repo, service

NOW = "2026-08-31T09:30:00Z"

# 주문: (총액, 삭제여부)
st_orders = st.lists(
    st.tuples(st.integers(min_value=0, max_value=1_000_000), st.booleans()),
    min_size=0, max_size=8,
)


def _fresh_active_session():
    """독립 in-memory DB 에 store/menu/table/active-session 을 만들고 핸들을 반환."""
    conn = db.connect(":memory:")
    db.apply_migrations(conn)
    cur = conn.execute(
        "INSERT INTO stores(store_code, name, created_at, updated_at) VALUES (?,?,?,?)",
        ("STORE001", "홍길동식당", NOW, NOW),
    )
    store_id = cur.lastrowid
    cur = conn.execute(
        "INSERT INTO categories(store_id, name, display_order, created_at, updated_at)"
        " VALUES (?,?,?,?,?)", (store_id, "메인", 0, NOW, NOW),
    )
    cat_id = cur.lastrowid
    cur = conn.execute(
        "INSERT INTO menus(store_id, category_id, name, price, description, image_url,"
        " display_order, is_available, created_at, updated_at) VALUES (?,?,?,?,?,?,?,1,?,?)",
        (store_id, cat_id, "김치찌개", 8000, None, None, 0, NOW, NOW),
    )
    menu_id = cur.lastrowid
    cur = conn.execute(
        "INSERT INTO tables(store_id, table_number, password_hash, created_at, updated_at)"
        " VALUES (?,?,?,?,?)", (store_id, 5, "x", NOW, NOW),
    )
    table_id = cur.lastrowid
    cur = conn.execute(
        "INSERT INTO table_sessions(table_id, status, opened_at, created_at, updated_at)"
        " VALUES (?,?,?,?,?)", (table_id, "active", NOW, NOW, NOW),
    )
    session_id = cur.lastrowid
    conn.commit()
    return conn, store_id, table_id, session_id, menu_id


def _insert_order(conn, table_id, session_id, menu_id, seq, total, deleted):
    cur = conn.execute(
        "INSERT INTO orders(session_id, table_id, order_number, status, total_amount,"
        " is_deleted, ordered_at, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (session_id, table_id, f"A-20260831-{seq:04d}", "pending", total,
         1 if deleted else 0, NOW, NOW, NOW),
    )
    order_id = cur.lastrowid
    conn.execute(
        "INSERT INTO order_items(order_id, menu_id, menu_name, unit_price, quantity,"
        " created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
        (order_id, menu_id, "김치찌개", total, 1, NOW, NOW),
    )
    conn.commit()
    return order_id


@settings(max_examples=50)
@given(orders=st_orders)
def test_close_session_conserves_all_orders(orders):
    """[PBT-03] 세션 종료 시 이동 건수 == 세션 주문 수, 종료 후 현재 총액/목록 0."""
    conn, store_id, table_id, session_id, menu_id = _fresh_active_session()
    try:
        for i, (total, deleted) in enumerate(orders, start=1):
            _insert_order(conn, table_id, session_id, menu_id, i, total, deleted)

        result = asyncio.run(service.close_session(conn, store_id, table_id))

        assert result["moved_orders"] == len(orders)          # 보존
        assert repo.count_history(conn, table_id, None, None) == len(orders)
        assert service.current_orders(conn, table_id) == []   # 현재 목록 리셋
        # active 세션 없음 → 현재 총액 0
        assert calc_table_total(repo.active_session_orders(conn, table_id)) == 0
    finally:
        conn.close()


@settings(max_examples=50)
@given(orders=st.lists(
    st.tuples(st.integers(min_value=0, max_value=1_000_000), st.booleans()),
    min_size=1, max_size=8))
def test_delete_recomputes_total_excluding_deleted(orders):
    """[PBT-03] 첫 주문 삭제 후 재계산 총액 == 남은 미삭제 주문 total 합."""
    conn, store_id, table_id, session_id, menu_id = _fresh_active_session()
    try:
        order_ids = []
        for i, (total, deleted) in enumerate(orders, start=1):
            order_ids.append(
                (_insert_order(conn, table_id, session_id, menu_id, i, total, deleted), total, deleted)
            )
        target_id, _, _ = order_ids[0]

        result = asyncio.run(service.delete_order(conn, target_id))

        # 독립 오라클: target 및 원래 삭제분 제외한 total 합
        expected = sum(t for (oid, t, d) in order_ids if oid != target_id and not d)
        assert result["table_total"] == expected
    finally:
        conn.close()
