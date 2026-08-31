"""방명록 API 라우터.

경로(최종): /api/customer/guestbook (main.py 가 prefix="/api" 로 include).
고객 인증(table_token)을 사용하며 매장 단위로 공유 조회한다.
"""
from __future__ import annotations

from typing import Any, AsyncIterator

from fastapi import APIRouter, Depends

from app.core import db
from app.customer.auth import get_table_context
from app.guestbook import service
from app.guestbook.schemas import CreateGuestbookRequest, GuestbookEntry

router = APIRouter(prefix="/customer/guestbook", tags=["guestbook"])


async def get_conn() -> AsyncIterator[Any]:
    conn = db.connect()
    try:
        yield conn
    finally:
        conn.close()


@router.post("", status_code=201, response_model=GuestbookEntry)
async def create_entry(
    body: CreateGuestbookRequest,
    ctx=Depends(get_table_context), conn=Depends(get_conn),
) -> dict[str, Any]:
    return service.create_entry(
        conn, ctx["store_id"], ctx["table_id"], body.author_name, body.image_data,
    )


@router.get("")
async def list_entries(
    page: int = 1, size: int = 20,
    ctx=Depends(get_table_context), conn=Depends(get_conn),
) -> dict[str, Any]:
    return service.list_entries(conn, ctx["store_id"], page, size)
