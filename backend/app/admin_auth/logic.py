"""Unit 3: 순수 로직 유틸 (PBT 대상).

- select_recent_orders: 대시보드 카드용 최신 주문 선별(BR-A5.3).
- build_admin_claims: JWT claims 조립(BR-A3.1).
부작용 없음. business-logic-model.md §6 참조.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

RECENT_LIMIT = 3  # Q6=A


def select_recent_orders(
    orders: Sequence[Mapping[str, Any]], n: int = RECENT_LIMIT
) -> list[dict[str, Any]]:
    """미삭제 주문을 ordered_at 내림차순으로 정렬해 최신 n건 반환 (BR-A5.3).

    - is_deleted(True/1) 주문 제외.
    - 정렬 키: (ordered_at, id) 내림차순 → 입력 순서와 무관하게 결정적.
    - 결과 길이 <= n.
    """
    visible = [dict(o) for o in orders if not o.get("is_deleted")]
    visible.sort(key=lambda o: (o.get("ordered_at", ""), o.get("id", 0)), reverse=True)
    return visible[: max(0, n)]


def build_admin_claims(admin: Mapping[str, Any]) -> dict[str, Any]:
    """JWT payload claims 조립 (BR-A3.1, Q3=A).

    admin: {id, store_id, username, ...}
    → {sub, store_id, username, role}. iat/exp 는 security.create_token 이 부여.

    sub 는 PyJWT 규약상 문자열이어야 하므로 str 로 저장한다(decode 검증 통과).
    """
    return {
        "sub": str(admin["id"]),
        "store_id": admin["store_id"],
        "username": admin["username"],
        "role": "admin",
    }
