"""Unit 2: 고객 API 요청/응답 스키마 (pydantic).

응답 상세(OrderDetail/OrderSummary)는 core.models 를 재사용한다.
기준: Integration Contract §3.1 / domain-entities.md §2.
"""
from __future__ import annotations

from pydantic import BaseModel


# --- 3.1.1 로그인 ---

class LoginRequest(BaseModel):
    store_code: str
    table_number: int
    password: str


class LoginResponse(BaseModel):
    table_token: str
    table_id: int
    table_number: int
    store_name: str


# --- 3.1.3 주문 생성 ---

class OrderItemInput(BaseModel):
    menu_id: int
    quantity: int


class CreateOrderRequest(BaseModel):
    items: list[OrderItemInput] = []


class CreateOrderResponse(BaseModel):
    order_id: int
    order_number: str
    total_amount: int
    status: str
    ordered_at: str
