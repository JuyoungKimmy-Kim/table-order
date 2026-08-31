"""Unit 2: 고객 응답 DTO round-trip PBT (PBT-02/07/08).

OrderDetail / OrderItemDetail 의 to_dict ↔ from_dict 왕복 동등성과
line_total·total_amount 일관성(core.domain.calc_order_total 위임)을 검증한다.
제너레이터는 tests/generators.py 를 재사용한다(PBT-07).
"""
from __future__ import annotations

from hypothesis import given, strategies as st

from app.core import domain
from app.core.models import OrderDetail, OrderItemDetail
from tests.generators import st_money, st_quantity


st_item = st.builds(OrderItemDetail,
                    menu_name=st.text(min_size=1, max_size=20),
                    unit_price=st_money,
                    quantity=st_quantity)


@given(st_item)
def test_order_item_line_total(item):
    """line_total == unit_price * quantity (파생 필드 불변식)."""
    d = item.to_dict()
    assert d["line_total"] == item.unit_price * item.quantity
    # from_dict 왕복 (line_total 은 파생이므로 코어 필드 동등성으로 비교)
    back = OrderItemDetail.from_dict(d)
    assert (back.menu_name, back.unit_price, back.quantity) == \
           (item.menu_name, item.unit_price, item.quantity)


@given(
    order_id=st.integers(min_value=1, max_value=10_000),
    table_id=st.integers(min_value=1, max_value=1000),
    table_number=st.integers(min_value=1, max_value=999),
    status=st.sampled_from(["pending", "preparing", "completed"]),
    items=st.lists(st_item, max_size=15),
)
def test_order_detail_roundtrip(order_id, table_id, table_number, status, items):
    """OrderDetail.from_dict(to_dict()) 는 원본과 동등(PBT-02/07/08)."""
    total = domain.calc_order_total(
        [{"unit_price": it.unit_price, "quantity": it.quantity} for it in items]
    )
    detail = OrderDetail(
        order_id=order_id, order_number=f"A-20260831-{order_id % 10000:04d}",
        table_id=table_id, table_number=table_number, status=status,
        total_amount=total, ordered_at="2026-08-31T09:30:00Z", items=items,
    )
    d = detail.to_dict()
    back = OrderDetail.from_dict(d)
    assert back.to_dict() == d
    # 총액 = 항목 line_total 합 (일관성)
    assert d["total_amount"] == sum(it["line_total"] for it in d["items"])
