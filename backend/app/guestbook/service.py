"""방명록 비즈니스 서비스.

- 작성: 이미지 DataURL 검증(PNG data URL 형식 + 크기 제한) 후 저장.
- 조회: 매장 단위 공유. 최신순 페이지네이션(§0.4 래퍼).
Unit 1 core 유틸(pagination/errors/db)을 재사용한다.
"""
from __future__ import annotations

import datetime as _dt
import sqlite3
from typing import Any

from app.core import pagination
from app.core.db import transaction
from app.core.errors import ValidationError
from app.guestbook import repository as repo

# 그림 DataURL 최대 길이(문자 수). base64 는 원본의 약 4/3 → 약 2MB 이미지 상당.
_MAX_IMAGE_DATA_LEN = 3_000_000
_ALLOWED_PREFIXES = ("data:image/png;base64,", "data:image/jpeg;base64,")
_MAX_AUTHOR_NAME_LEN = 30


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def create_entry(
    conn: sqlite3.Connection, store_id: int, table_id: int | None,
    author_name: str | None, image_data: str,
) -> dict[str, Any]:
    image = (image_data or "").strip()
    if not image.startswith(_ALLOWED_PREFIXES):
        raise ValidationError("이미지 형식이 올바르지 않습니다.",
                              details={"field": "image_data"})
    # prefix 뒤에 실제 데이터가 있어야 함(빈 캔버스 저장 방지 최소선).
    if len(image) <= max(len(p) for p in _ALLOWED_PREFIXES):
        raise ValidationError("빈 이미지는 저장할 수 없습니다.",
                              details={"field": "image_data"})
    if len(image) > _MAX_IMAGE_DATA_LEN:
        raise ValidationError("이미지 용량이 너무 큽니다.",
                              details={"field": "image_data", "max": _MAX_IMAGE_DATA_LEN})

    name = (author_name or "").strip() or None
    if name is not None and len(name) > _MAX_AUTHOR_NAME_LEN:
        raise ValidationError("작성자명이 너무 깁니다.",
                              details={"field": "author_name", "max": _MAX_AUTHOR_NAME_LEN})

    now = _now()
    with transaction(conn):
        entry_id = repo.insert_entry(conn, store_id, table_id, name, image, now)

    return {"id": entry_id, "author_name": name, "image_data": image, "created_at": now}


def list_entries(conn: sqlite3.Connection, store_id: int, page: int, size: int) -> dict[str, Any]:
    p, s = pagination.normalize(page, size)
    total = repo.count_by_store(conn, store_id)
    rows = repo.list_by_store(conn, store_id, pagination.offset(p, s), s)
    items = [
        {"id": r["id"], "author_name": r["author_name"],
         "image_data": r["image_data"], "created_at": r["created_at"]}
        for r in rows
    ]
    return pagination.paginate_response(items, p, s, total)
