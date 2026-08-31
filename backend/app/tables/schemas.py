"""Unit 4: 요청/응답 스키마 (Pydantic v2).

조회 응답(OrderDetail)은 core.models 를 재사용하고, 여기서는 Unit 4 고유
요청/간단 응답만 정의한다. 기준: Integration Contract §3.3.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class CreateTableReq(BaseModel):
    """POST /api/admin/tables 요청 (U4-BR-1).

    비어있음 등 업무 검증은 service 에서 표준 에러(400 VALIDATION_ERROR)로 처리한다
    (계약 §0.2 envelope 일관성). 여기서는 타입만 강제한다.
    """
    table_number: int = Field(..., description="테이블 번호(매장 내 유일)")
    password: str = Field(..., description="테이블 비밀번호(평문 수신 → bcrypt 저장)")


class CreateTableResp(BaseModel):
    table_id: int
    table_number: int


class DeleteOrderResp(BaseModel):
    """DELETE /api/admin/orders/{order_id} 응답 (U4-BR-2)."""
    order_id: int
    table_id: int
    table_total: int


class CloseSessionResp(BaseModel):
    """POST /api/admin/tables/{table_id}/close-session 응답 (U4-BR-3)."""
    table_id: int
    closed_session_id: int
    moved_orders: int
