"""Unit 4: FastAPI 라우터 — 테이블 & 세션 관리 API (§3.3).

경로(app include prefix `/api` 기준):
- POST   /api/admin/tables
- DELETE /api/admin/orders/{order_id}
- POST   /api/admin/tables/{table_id}/close-session
- GET    /api/admin/tables/{table_id}/orders
- GET    /api/admin/tables/{table_id}/history

모든 엔드포인트는 관리자 JWT 필요(require_admin, U4-BR-6).
"""
from __future__ import annotations

import sqlite3
from typing import Any

from fastapi import APIRouter, Depends, Query

from app.core import pagination
from app.tables import service
from app.tables.deps import get_conn, require_admin, resolve_store_id
from app.tables.schemas import (
    CloseSessionResp,
    CreateTableReq,
    CreateTableResp,
    DeleteOrderResp,
)

router = APIRouter(prefix="/admin", tags=["tables"])


@router.post("/tables", response_model=CreateTableResp, status_code=201)
async def create_table(
    body: CreateTableReq,
    conn: sqlite3.Connection = Depends(get_conn),
    claims: dict[str, Any] = Depends(require_admin),
) -> CreateTableResp:
    store_id = resolve_store_id(conn, claims)
    result = service.create_table(conn, store_id, body.table_number, body.password)
    return CreateTableResp(**result)


@router.delete("/orders/{order_id}", response_model=DeleteOrderResp)
async def delete_order(
    order_id: int,
    conn: sqlite3.Connection = Depends(get_conn),
    claims: dict[str, Any] = Depends(require_admin),
) -> DeleteOrderResp:
    result = await service.delete_order(conn, order_id)
    return DeleteOrderResp(**result)


@router.post("/tables/{table_id}/close-session", response_model=CloseSessionResp)
async def close_session(
    table_id: int,
    conn: sqlite3.Connection = Depends(get_conn),
    claims: dict[str, Any] = Depends(require_admin),
) -> CloseSessionResp:
    store_id = resolve_store_id(conn, claims)
    result = await service.close_session(conn, store_id, table_id)
    return CloseSessionResp(**result)


@router.get("/tables/{table_id}/orders")
async def current_orders(
    table_id: int,
    conn: sqlite3.Connection = Depends(get_conn),
    claims: dict[str, Any] = Depends(require_admin),
) -> list[dict[str, Any]]:
    return service.current_orders(conn, table_id)


@router.get("/tables/{table_id}/history")
async def order_history(
    table_id: int,
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    page: int | None = Query(default=None),
    size: int | None = Query(default=None),
    conn: sqlite3.Connection = Depends(get_conn),
    claims: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    p, s = pagination.normalize(page, size)
    items, total = service.history(
        conn, table_id, date_from, date_to, pagination.offset(p, s), s
    )
    return pagination.paginate_response(items, p, s, total)
