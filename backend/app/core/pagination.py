"""Unit 1: 페이지네이션 헬퍼 (Integration Contract §0.4).

- normalize(page, size): 범위 밖 값을 기본값으로 정규화.
- paginate_response(items, page, size, total): 공통 응답 래퍼.
"""
from __future__ import annotations

from typing import Any, Sequence

from app.core import config


def normalize(page: int | None, size: int | None) -> tuple[int, int]:
    """page>=1, 1<=size<=MAX_PAGE_SIZE 로 정규화. 잘못된 값은 기본값."""
    p = page if isinstance(page, int) and page >= 1 else 1
    if not isinstance(size, int) or size < 1:
        s = config.DEFAULT_PAGE_SIZE
    else:
        s = min(size, config.MAX_PAGE_SIZE)
    return p, s


def offset(page: int, size: int) -> int:
    """SQL OFFSET 계산."""
    return (page - 1) * size


def paginate_response(items: Sequence[Any], page: int, size: int, total: int) -> dict[str, Any]:
    """{"items", "page", "size", "total"} 래퍼 생성."""
    return {"items": list(items), "page": page, "size": size, "total": total}
