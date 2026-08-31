"""Unit 1: DTO round-trip Property-Based Tests (PBT-02, PBT-07, PBT-08).

business-logic-model.md §6.5:
- deserialize(serialize(dto)) == dto
- Σ line_total == total_amount (일관성)
"""
from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from app.core.models import (
    OrderDetail,
    OrderItemDetail,
    OrderSummary,
    make_item_preview,
)
from tests import generators as gen


# --- 도메인 제너레이터 (DTO 전용, generators 재사용) ---

# 비공백 메뉴명: 공백 아닌 문자를 최소 1자 포함하도록 처음부터 구성(filter 미사용 — 생성 효율).
st_menu_name = st.text(
    alphabet=st.characters(min_codepoint=0x21, max_codepoint=0x7E),
    min_size=1,
    max_size=20,
)
st_status = st.sampled_from(["pending", "preparing", "completed"])
st_iso_time = st.just("2026-08-31T09:30:00Z")


@st.composite
def st_order_item_detail(draw):
    return OrderItemDetail(
        menu_name=draw(st_menu_name),
        unit_price=draw(gen.st_money),
        quantity=draw(gen.st_quantity),
    )


@st.composite
def st_order_detail(draw):
    items = draw(st.lists(st_order_item_detail(), max_size=10))
    total = sum(it.line_total for it in items)
    return OrderDetail(
        order_id=draw(st.integers(1, 10_000)),
        order_number="A-20260831-0007",
        table_id=draw(st.integers(1, 100)),
        table_number=draw(st.integers(1, 100)),
        status=draw(st_status),
        total_amount=total,
        ordered_at=draw(st_iso_time),
        items=items,
    )


@st.composite
def st_order_summary(draw):
    return OrderSummary(
        order_id=draw(st.integers(1, 10_000)),
        order_number="A-20260831-0007",
        table_id=draw(st.integers(1, 100)),
        table_number=draw(st.integers(1, 100)),
        status=draw(st_status),
        total_amount=draw(gen.st_money),
        item_preview=draw(st.text(max_size=30)),
        ordered_at=draw(st_iso_time),
    )


@given(st_order_detail())
def test_order_detail_roundtrip(detail):
    """[PBT-02/07/08] OrderDetail: from_dict(to_dict(x)) == x."""
    restored = OrderDetail.from_dict(detail.to_dict())
    assert restored == detail


@given(st_order_summary())
def test_order_summary_roundtrip(summary):
    """[PBT-02/07/08] OrderSummary: from_dict(to_dict(x)) == x."""
    restored = OrderSummary.from_dict(summary.to_dict())
    assert restored == summary


@given(st_order_detail())
def test_line_total_sum_matches_total(detail):
    """[PBT-03] Σ line_total == total_amount (일관성)."""
    line_sum = sum(it["line_total"] for it in detail.to_dict()["items"])
    assert line_sum == detail.total_amount


@given(st.lists(st_order_item_detail(), max_size=10))
def test_item_preview_shape(items):
    """[PBT-03] 미리보기: 빈 목록→'', 1건→이름, n건→'이름 외 (n-1)건'."""
    preview = make_item_preview(items)
    if not items:
        assert preview == ""
    elif len(items) == 1:
        assert preview == items[0].menu_name
    else:
        assert preview.endswith(f"외 {len(items) - 1}건")
