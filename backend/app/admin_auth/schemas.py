"""Unit 3: 요청/응답 스키마 (Pydantic).

응답의 대시보드/주문 DTO 는 Unit 1 `app.core.models` 을 재사용하고,
여기서는 인증·상태변경 등 Unit 3 고유 페이로드만 정의한다.
기준: Integration Contract §3.2.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """POST /api/admin/login 요청 (§3.2.1)."""
    store_code: str = Field(..., min_length=1)
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    """POST /api/admin/login 응답 (§3.2.1)."""
    token: str
    expires_in: int
    store_name: str


class MeResponse(BaseModel):
    """GET /api/admin/me 응답 (§3.2.2)."""
    username: str
    store_id: int


class StatusUpdateRequest(BaseModel):
    """PATCH /api/admin/orders/{id}/status 요청 (§3.2.5)."""
    status: str


class StatusUpdateResponse(BaseModel):
    """PATCH /api/admin/orders/{id}/status 응답 (§3.2.5)."""
    order_id: int
    status: str


class TableCard(BaseModel):
    """대시보드 카드 (§3.2.4). recent_orders 는 OrderSummary(§4.1) dict."""
    table_id: int
    table_number: int
    session_active: bool
    table_total: int
    recent_orders: list[dict]


class DashboardResponse(BaseModel):
    """GET /api/admin/dashboard 응답 (§3.2.4)."""
    tables: list[TableCard]


# OrderDetail(§4.2) 은 Unit 1 models.OrderDetail.to_dict() 를 그대로 반환하므로
# 별도 Pydantic 모델 없이 dict 로 응답한다(response_model 미지정).
