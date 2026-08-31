"""Unit 2: 고객 API 라우터 (Integration Contract §3.1).

경로(최종): /api/customer/... (main.py 가 prefix="/api" 로 include).
service 계층에 위임하고 에러는 core.errors 예외 핸들러가 표준 응답으로 변환한다.
"""
from __future__ import annotations

from typing import Any, AsyncIterator

from fastapi import APIRouter, Depends

from app.core import db
from app.customer import service
from app.customer.auth import get_table_context
from app.customer.schemas import (
    CreateOrderRequest, CreateOrderResponse, LoginRequest, LoginResponse,
)

router = APIRouter(prefix="/customer", tags=["customer"])


async def get_conn() -> AsyncIterator[Any]:
    """요청 단위 SQLite 연결(요청 종료 시 닫음).

    async 의존성으로 두어 연결의 생성·사용·종료가 모두 이벤트 루프 스레드에서
    일어나게 한다. sqlite3 객체는 스레드 간 공유가 금지되므로, 주문 생성(async)이
    스레드풀에서 만든 연결을 루프 스레드에서 쓰는 상황을 방지한다.
    """
    conn = db.connect()
    try:
        yield conn
    finally:
        conn.close()


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, conn=Depends(get_conn)) -> dict[str, Any]:
    return service.login(conn, body.store_code, body.table_number, body.password)


@router.get("/menus")
async def menus(ctx=Depends(get_table_context), conn=Depends(get_conn)) -> dict[str, Any]:
    return service.get_menus(conn, ctx["store_id"])


@router.post("/orders", status_code=201, response_model=CreateOrderResponse)
async def create_order(
    body: CreateOrderRequest, ctx=Depends(get_table_context), conn=Depends(get_conn)
) -> dict[str, Any]:
    items = [{"menu_id": it.menu_id, "quantity": it.quantity} for it in body.items]
    return await service.create_order(conn, ctx["table_id"], ctx["store_id"], items)


@router.get("/orders")
async def list_orders(
    page: int = 1, size: int = 20,
    ctx=Depends(get_table_context), conn=Depends(get_conn),
) -> dict[str, Any]:
    return service.list_orders(conn, ctx["table_id"], page, size)
