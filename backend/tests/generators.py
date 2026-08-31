"""Unit 1: PBT 도메인 제너레이터 (중앙화 — PBT-07).

모든 유닛의 PBT는 이 제너레이터를 재사용한다(중복 정의 금지).
원시 타입이 아닌 도메인 제약을 반영한 현실적 입력을 생성한다.
"""
from __future__ import annotations

from hypothesis import strategies as st

# 금액: 원 단위 정수, 0 이상 현실 범위 (경계값 0 포함)
st_money = st.integers(min_value=0, max_value=10_000_000)

# 수량: 1 이상 (주문 항목 quantity > 0)
st_quantity = st.integers(min_value=1, max_value=99)

# 주문번호 시퀀스: 1..9999
st_seq = st.integers(min_value=1, max_value=9999)

# 주문번호 접두사: 단일 대문자
st_prefix = st.sampled_from(list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"))

# 날짜 (order_number_format 용)
st_date = st.dates(min_value=__import__("datetime").date(2000, 1, 1),
                   max_value=__import__("datetime").date(2099, 12, 31))


@st.composite
def st_order_item(draw):
    """주문 항목: {unit_price, quantity}."""
    return {
        "unit_price": draw(st_money),
        "quantity": draw(st_quantity),
    }


st_order_items = st.lists(st_order_item(), max_size=20)


@st.composite
def st_order(draw):
    """주문(총액 계산용): {total_amount, is_deleted}."""
    return {
        "total_amount": draw(st_money),
        "is_deleted": draw(st.booleans()),
    }


st_orders = st.lists(st_order(), max_size=20)


@st.composite
def st_session(draw, status=None):
    """테이블 세션: {id, status}."""
    return {
        "id": draw(st.integers(min_value=1, max_value=10_000)),
        "status": status if status is not None else draw(st.sampled_from(["active", "closed"])),
    }
