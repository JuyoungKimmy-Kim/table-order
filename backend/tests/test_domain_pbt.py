"""Unit 1: 순수 함수 Property-Based Tests (PBT-02, PBT-03).

business-logic-model.md §6 Testable Properties 를 검증한다.
제너레이터는 tests/generators.py (PBT-07) 를 재사용한다.
"""
from __future__ import annotations

from datetime import date

from hypothesis import given
from hypothesis import strategies as st

from app.core.domain import (
    calc_order_total,
    calc_table_total,
    is_current_session_order,
    order_number_format,
    parse_order_number,
)
from tests import generators as gen


# --- calc_order_total (§6.1) ---

@given(gen.st_order_items)
def test_order_total_nonnegative(items):
    """[PBT-03] 결과는 항상 비음수."""
    assert calc_order_total(items) >= 0


@given(gen.st_order_items, st.randoms())
def test_order_total_order_independent(items, rnd):
    """[PBT-03] 항목 순서를 섞어도 총액 동일 (교환/불변)."""
    shuffled = list(items)
    rnd.shuffle(shuffled)
    assert calc_order_total(items) == calc_order_total(shuffled)


def test_order_total_empty_is_zero():
    """[PBT-03] 빈 목록 → 0."""
    assert calc_order_total([]) == 0


@given(gen.st_order_items, gen.st_order_items)
def test_order_total_additive(a, b):
    """[PBT-03] total(a+b) == total(a) + total(b)  (분할합/귀납)."""
    assert calc_order_total(list(a) + list(b)) == calc_order_total(a) + calc_order_total(b)


# --- calc_table_total (§6.2) ---

@given(gen.st_orders)
def test_table_total_excludes_deleted(orders):
    """[PBT-03] 삭제 주문은 합에서 제외 — 미삭제 total_amount 단순 합과 일치(oracle)."""
    expected = sum(o["total_amount"] for o in orders if not o["is_deleted"])
    assert calc_table_total(orders) == expected


def test_table_total_empty_is_zero():
    """[PBT-03] 빈 목록 → 0."""
    assert calc_table_total([]) == 0


@given(gen.st_orders)
def test_table_total_nonnegative(orders):
    """[PBT-03] 결과 비음수."""
    assert calc_table_total(orders) >= 0


# --- is_current_session_order (§6.3) ---

@given(gen.st_session(status="closed"), st.integers(min_value=1, max_value=10_000))
def test_closed_session_never_current(session, order_session_id):
    """[PBT-03] closed 세션 주문은 항상 False."""
    order = {"session_id": order_session_id}
    assert is_current_session_order(order, session) is False


@given(gen.st_session(status="active"), st.integers(min_value=1, max_value=10_000))
def test_active_session_matches_by_id(session, other_id):
    """[PBT-03] active 세션이라도 session_id 불일치면 False, 일치하면 True."""
    matching = {"session_id": session["id"]}
    assert is_current_session_order(matching, session) is True

    if other_id != session["id"]:
        non_matching = {"session_id": other_id}
        assert is_current_session_order(non_matching, session) is False


# --- order_number_format / parse (§6.4) ---

@given(gen.st_prefix, gen.st_date, gen.st_seq)
def test_order_number_roundtrip(prefix, on_date, seq):
    """[PBT-02] parse(format(p, d, s)) == (p, d, s)  (round-trip)."""
    s = order_number_format(prefix, on_date, seq)
    parsed = parse_order_number(s)
    assert parsed.prefix == prefix
    assert parsed.on_date == on_date
    assert parsed.seq == seq


@given(gen.st_prefix, gen.st_date, gen.st_seq)
def test_order_number_format_invariant(prefix, on_date, seq):
    """[PBT-03] 형식 정규식 ^[A-Z]-\\d{8}-\\d{4}$ 를 항상 만족."""
    import re

    s = order_number_format(prefix, on_date, seq)
    assert re.match(r"^[A-Z]-\d{8}-\d{4}$", s)
