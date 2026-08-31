"""Unit 1: 공통 검증 헬퍼 (business-rules.md BR-9).

검증 실패 시 errors.ValidationError 를 raise 한다(details 에 필드별 사유).
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from app.core.errors import ValidationError


def validate_menu_payload(payload: Mapping[str, Any]) -> None:
    """메뉴 등록/수정 검증 (BR-9.1): name 필수, price 정수 >= 0."""
    details: dict[str, str] = {}
    name = payload.get("name")
    if not isinstance(name, str) or name.strip() == "":
        details["name"] = "메뉴명은 비어 있을 수 없습니다."
    price = payload.get("price")
    if not isinstance(price, int) or isinstance(price, bool) or price < 0:
        details["price"] = "가격은 0 이상의 정수여야 합니다."
    if details:
        raise ValidationError("메뉴 입력이 올바르지 않습니다.", details=details)


def validate_order_items(items: Sequence[Mapping[str, Any]]) -> None:
    """주문 생성 검증 (BR-9.2): items 비어있지 않음, quantity >= 1 정수."""
    if not items:
        raise ValidationError("주문 항목이 비어 있습니다.", details={"items": "최소 1개 이상"})
    for idx, item in enumerate(items):
        qty = item.get("quantity")
        if not isinstance(qty, int) or isinstance(qty, bool) or qty < 1:
            raise ValidationError(
                "수량이 올바르지 않습니다.",
                details={f"items[{idx}].quantity": "1 이상의 정수여야 합니다."},
            )
        if not isinstance(item.get("menu_id"), int) or isinstance(item.get("menu_id"), bool):
            raise ValidationError(
                "menu_id 가 올바르지 않습니다.",
                details={f"items[{idx}].menu_id": "정수여야 합니다."},
            )


def validate_order_status(status: str) -> None:
    """주문 상태값 검증 (BR-5.2)."""
    if status not in ("pending", "preparing", "completed"):
        raise ValidationError(
            "허용되지 않는 상태값입니다.",
            details={"status": "pending|preparing|completed 중 하나여야 합니다."},
        )
