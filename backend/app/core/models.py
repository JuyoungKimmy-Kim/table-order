"""Unit 1: 공유 엔티티 모델 + 응답 DTO.

- 엔티티 dataclass: DB 행(sqlite3.Row) ↔ 파이썬 객체 변환 편의.
- DTO: OrderSummary(§4.1), OrderDetail(§4.2) — SSE/모니터링/상세 공용.
- DTO 는 serialize/deserialize round-trip 을 만족한다(PBT-02/07/08).

기준: Integration Contract §1, §4 / domain-entities.md.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping


# --------------------------------------------------------------------------
# 엔티티 (DB 매핑) — 필요한 유닛이 확장/사용
# --------------------------------------------------------------------------

@dataclass
class Store:
    id: int
    store_code: str
    name: str


@dataclass
class Table:
    id: int
    store_id: int
    table_number: int


@dataclass
class TableSession:
    id: int
    table_id: int
    status: str  # 'active' | 'closed'
    opened_at: str
    closed_at: str | None = None


@dataclass
class Category:
    id: int
    store_id: int
    name: str
    display_order: int = 0


@dataclass
class Menu:
    id: int
    store_id: int
    category_id: int
    name: str
    price: int
    description: str | None = None
    image_url: str | None = None
    display_order: int = 0
    is_available: bool = True


# --------------------------------------------------------------------------
# 응답 DTO (§4)
# --------------------------------------------------------------------------

@dataclass
class OrderItemDetail:
    """OrderDetail.items[] 요소. line_total 은 파생 필드."""
    menu_name: str
    unit_price: int
    quantity: int

    @property
    def line_total(self) -> int:
        return self.unit_price * self.quantity

    def to_dict(self) -> dict[str, Any]:
        return {
            "menu_name": self.menu_name,
            "unit_price": self.unit_price,
            "quantity": self.quantity,
            "line_total": self.line_total,
        }

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> "OrderItemDetail":
        return cls(
            menu_name=d["menu_name"],
            unit_price=int(d["unit_price"]),
            quantity=int(d["quantity"]),
        )


@dataclass
class OrderSummary:
    """모니터링 카드·SSE 페이로드용 (§4.1)."""
    order_id: int
    order_number: str
    table_id: int
    table_number: int
    status: str
    total_amount: int
    item_preview: str
    ordered_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> "OrderSummary":
        return cls(**{k: d[k] for k in cls.__dataclass_fields__})


@dataclass
class OrderDetail:
    """주문 상세·내역용 (§4.2)."""
    order_id: int
    order_number: str
    table_id: int
    table_number: int
    status: str
    total_amount: int
    ordered_at: str
    items: list[OrderItemDetail] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "order_id": self.order_id,
            "order_number": self.order_number,
            "table_id": self.table_id,
            "table_number": self.table_number,
            "status": self.status,
            "total_amount": self.total_amount,
            "ordered_at": self.ordered_at,
            "items": [it.to_dict() for it in self.items],
        }

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> "OrderDetail":
        return cls(
            order_id=d["order_id"],
            order_number=d["order_number"],
            table_id=d["table_id"],
            table_number=d["table_number"],
            status=d["status"],
            total_amount=int(d["total_amount"]),
            ordered_at=d["ordered_at"],
            items=[OrderItemDetail.from_dict(it) for it in d.get("items", [])],
        )


def make_item_preview(items: list[OrderItemDetail]) -> str:
    """'김치찌개 외 2건' 형태의 미리보기 문자열 생성 (OrderSummary용)."""
    if not items:
        return ""
    first = items[0].menu_name
    extra = len(items) - 1
    return first if extra == 0 else f"{first} 외 {extra}건"
