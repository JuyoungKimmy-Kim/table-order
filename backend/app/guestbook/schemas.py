"""방명록 API 요청/응답 스키마 (pydantic).

고객이 그림판으로 그린 카드메모를 남기고 조회한다.
그림은 PNG DataURL(base64) 문자열(`image_data`)로 주고받는다.
"""
from __future__ import annotations

from pydantic import BaseModel


class CreateGuestbookRequest(BaseModel):
    author_name: str | None = None
    image_data: str


class GuestbookEntry(BaseModel):
    id: int
    author_name: str | None
    image_data: str
    created_at: str
