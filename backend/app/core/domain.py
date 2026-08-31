"""Unit 1: 핵심 도메인 순수 함수.

모든 유닛은 총액/세션 판별을 직접 계산하지 말고 이 함수들을 호출한다.
부작용 없음(순수). PBT 대상 — business-logic-model.md §2, §6.

기준: Integration Contract §0.5, §5 / business-rules.md BR-2, BR-3, BR-6.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Mapping, Sequence

# 주문번호 형식: A-YYYYMMDD-NNNN
ORDER_NUMBER_RE = re.compile(r"^([A-Z])-(\d{8})-(\d{4})$")
_MIN_SEQ = 1
_MAX_SEQ = 9999


def calc_order_total(items: Sequence[Mapping[str, int]]) -> int:
    """주문 총액 = Σ(unit_price × quantity).  (BR-2.1)

    - items: [{"unit_price": int>=0, "quantity": int>=1}, ...]
    - 빈 목록 → 0. 결과는 항상 비음수.
    """
    return sum(int(item["unit_price"]) * int(item["quantity"]) for item in items)


def calc_table_total(orders: Sequence[Mapping[str, object]]) -> int:
    """테이블 현재 총액 = 미삭제 주문들의 total_amount 합.  (BR-2.2, Q4=A)

    - orders: [{"total_amount": int, "is_deleted": bool|0|1}, ...]
    - 삭제된(is_deleted True/1) 주문은 제외. 빈 목록 → 0.
    """
    return sum(
        int(order["total_amount"])
        for order in orders
        if not order.get("is_deleted")
    )


def is_current_session_order(
    order: Mapping[str, object], session: Mapping[str, object]
) -> bool:
    """주문이 현재(active) 세션에 속하는지 판별.  (BR-3.2)

    - order.session_id == session.id AND session.status == 'active'
    - closed 세션이면 항상 False.
    """
    return (
        order.get("session_id") == session.get("id")
        and session.get("status") == "active"
    )


def order_number_format(prefix: str, on_date: date, seq: int) -> str:
    """주문번호 조립: '{prefix}-{YYYYMMDD}-{seq:04d}'.  (BR-6.1)

    - prefix: 단일 대문자(예: 'A'). seq: 1..9999.
    - parse_order_number 로 역파싱 가능(round-trip, PBT-02).
    """
    if not (len(prefix) == 1 and prefix.isalpha() and prefix.isupper()):
        raise ValueError("prefix must be a single uppercase letter")
    if not (_MIN_SEQ <= seq <= _MAX_SEQ):
        raise ValueError(f"seq must be in [{_MIN_SEQ}, {_MAX_SEQ}]")
    return f"{prefix}-{on_date:%Y%m%d}-{seq:04d}"


@dataclass(frozen=True)
class ParsedOrderNumber:
    prefix: str
    on_date: date
    seq: int


def parse_order_number(value: str) -> ParsedOrderNumber:
    """주문번호 역파싱.  order_number_format 의 역함수(round-trip, PBT-02)."""
    m = ORDER_NUMBER_RE.match(value)
    if not m:
        raise ValueError(f"invalid order_number: {value!r}")
    prefix, ymd, seq_s = m.groups()
    parsed_date = date(int(ymd[0:4]), int(ymd[4:6]), int(ymd[6:8]))
    return ParsedOrderNumber(prefix=prefix, on_date=parsed_date, seq=int(seq_s))
