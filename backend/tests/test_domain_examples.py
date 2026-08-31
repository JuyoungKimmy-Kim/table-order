"""Unit 1: 예제 기반 테스트 (PBT-10 상호보완).

핵심 비즈니스 시나리오를 명시적 기대값으로 고정한다. PBT 가 일반 속성을,
이 테스트가 구체 사례를 문서화한다.
"""
from __future__ import annotations

from datetime import date

import pytest

from app.core.domain import (
    calc_order_total,
    calc_table_total,
    is_current_session_order,
    order_number_format,
    parse_order_number,
)
from app.core.validation import (
    validate_menu_payload,
    validate_order_items,
    validate_order_status,
)
from app.core.errors import ValidationError


def test_calc_order_total_example():
    # 김치찌개 8000 x2 + 공기밥 1000 x1 = 17000
    items = [{"unit_price": 8000, "quantity": 2}, {"unit_price": 1000, "quantity": 1}]
    assert calc_order_total(items) == 17000


def test_calc_table_total_excludes_deleted_example():
    orders = [
        {"total_amount": 17000, "is_deleted": False},
        {"total_amount": 8000, "is_deleted": True},   # 삭제 → 제외
        {"total_amount": 5000, "is_deleted": False},
    ]
    assert calc_table_total(orders) == 22000


def test_is_current_session_order_examples():
    active = {"id": 45, "status": "active"}
    closed = {"id": 45, "status": "closed"}
    assert is_current_session_order({"session_id": 45}, active) is True
    assert is_current_session_order({"session_id": 45}, closed) is False
    assert is_current_session_order({"session_id": 99}, active) is False


def test_order_number_format_example():
    s = order_number_format("A", date(2026, 8, 31), 7)
    assert s == "A-20260831-0007"
    parsed = parse_order_number(s)
    assert (parsed.prefix, parsed.on_date, parsed.seq) == ("A", date(2026, 8, 31), 7)


def test_order_number_seq_bounds():
    with pytest.raises(ValueError):
        order_number_format("A", date(2026, 8, 31), 0)
    with pytest.raises(ValueError):
        order_number_format("A", date(2026, 8, 31), 10000)


def test_parse_invalid_order_number():
    with pytest.raises(ValueError):
        parse_order_number("invalid")


def test_validate_menu_payload_ok_and_fail():
    validate_menu_payload({"name": "김치찌개", "price": 8000})  # ok
    with pytest.raises(ValidationError):
        validate_menu_payload({"name": "", "price": 8000})
    with pytest.raises(ValidationError):
        validate_menu_payload({"name": "된장찌개", "price": -1})


def test_validate_order_items_fail():
    with pytest.raises(ValidationError):
        validate_order_items([])
    with pytest.raises(ValidationError):
        validate_order_items([{"menu_id": 1, "quantity": 0}])


def test_validate_order_status():
    validate_order_status("preparing")  # ok
    with pytest.raises(ValidationError):
        validate_order_status("done")
