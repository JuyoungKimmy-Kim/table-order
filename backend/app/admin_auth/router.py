"""Unit 3: 관리자 인증 & 모니터링 라우터 (§3.2).

경로 접두사 /api 는 main.py 의 include_router 에서 부여한다.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Header, Path
from fastapi.responses import StreamingResponse

from app.core import db, sse
from app.admin_auth import service
from app.admin_auth.deps import AdminPrincipal, get_current_admin
from app.admin_auth.schemas import (
    DashboardResponse, LoginRequest, LoginResponse, MeResponse,
    StatusUpdateRequest, StatusUpdateResponse,
)

router = APIRouter(prefix="/admin", tags=["admin-auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest):
    conn = db.connect()
    try:
        return service.login(conn, payload.store_code, payload.username, payload.password)
    finally:
        conn.close()


@router.get("/me", response_model=MeResponse)
def me(principal: AdminPrincipal = Depends(get_current_admin)):
    return service.me(principal)


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(principal: AdminPrincipal = Depends(get_current_admin)):
    conn = db.connect()
    try:
        return service.build_dashboard(conn, principal.store_id)
    finally:
        conn.close()


@router.get("/orders/stream")
async def orders_stream(
    principal: AdminPrincipal = Depends(get_current_admin),
    last_event_id: Optional[str] = Header(default=None, alias="Last-Event-ID"),
):
    """SSE 구독 (§3.2.3 / §2.1). 인증은 fetch 헤더(Q9=A)."""
    try:
        start_id = int(last_event_id) if last_event_id is not None else None
    except (TypeError, ValueError):
        start_id = None
    return StreamingResponse(
        sse.subscribe(start_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.patch("/orders/{order_id}/status", response_model=StatusUpdateResponse)
async def change_status(payload: StatusUpdateRequest,
                        order_id: int = Path(..., ge=1),
                        principal: AdminPrincipal = Depends(get_current_admin)):
    conn = db.connect()
    try:
        return await service.change_status(conn, order_id, payload.status)
    finally:
        conn.close()


@router.get("/orders/{order_id}")
def order_detail(order_id: int = Path(..., ge=1),
                 principal: AdminPrincipal = Depends(get_current_admin)):
    conn = db.connect()
    try:
        return service.get_order_detail(conn, order_id)
    finally:
        conn.close()
