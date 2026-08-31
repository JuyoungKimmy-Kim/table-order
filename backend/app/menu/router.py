"""Unit 5: 메뉴 관리 라우터 (Integration Contract §3.4).

라우트(관리자 인증 필요):
  GET    /api/admin/menus                메뉴 목록(카테고리별, 숨김 포함)
  POST   /api/admin/menus                메뉴 등록
  PATCH  /api/admin/menus/order          노출 순서 조정
  PUT    /api/admin/menus/{menu_id}      메뉴 수정(전체 교체)
  DELETE /api/admin/menus/{menu_id}      메뉴 삭제(참조 주문 있으면 409)
  GET/POST/PUT/DELETE /api/admin/categories[...]

요청 본문은 dict 로 받아 core.validation 으로 검증한다(§0.2 표준 에러 포맷 유지).
Pydantic 자동 검증(422)은 표준 포맷을 벗어나므로 사용하지 않는다.
"""
from __future__ import annotations

import sqlite3
from typing import Any

from fastapi import APIRouter, Body, Depends, Response

from app.core import db
from app.core.errors import ValidationError
from app.core.validation import validate_menu_payload
from app.menu import repository as repo
from app.menu.deps import get_conn, require_admin

router = APIRouter(prefix="/admin", tags=["menu"])


def _validate_category_payload(payload: dict[str, Any]) -> None:
    """카테고리 검증: name 필수. display_order 는 정수(선택)."""
    details: dict[str, str] = {}
    name = payload.get("name")
    if not isinstance(name, str) or name.strip() == "":
        details["name"] = "카테고리명은 비어 있을 수 없습니다."
    display_order = payload.get("display_order", 0)
    if not isinstance(display_order, int) or isinstance(display_order, bool):
        details["display_order"] = "노출 순서는 정수여야 합니다."
    if details:
        raise ValidationError("카테고리 입력이 올바르지 않습니다.", details=details)


# --------------------------------------------------------------------------
# 메뉴
# --------------------------------------------------------------------------

@router.get("/menus")
def list_menus(conn: sqlite3.Connection = Depends(get_conn),
               _admin: dict = Depends(require_admin)) -> dict[str, Any]:
    store_id = repo.get_default_store_id(conn)
    return repo.list_menus_grouped(conn, store_id)


@router.post("/menus", status_code=201)
def create_menu(payload: dict[str, Any] = Body(...),
                conn: sqlite3.Connection = Depends(get_conn),
                _admin: dict = Depends(require_admin)) -> dict[str, Any]:
    validate_menu_payload(payload)  # BR-9.1
    store_id = repo.get_default_store_id(conn)
    with db.transaction(conn):
        return repo.create_menu(conn, store_id, payload)


@router.patch("/menus/order")
def reorder_menus(payload: dict[str, Any] = Body(...),
                  conn: sqlite3.Connection = Depends(get_conn),
                  _admin: dict = Depends(require_admin)) -> dict[str, Any]:
    store_id = repo.get_default_store_id(conn)
    with db.transaction(conn):
        updated = repo.reorder_menus(conn, store_id, payload.get("orders"))
    return {"updated": updated}


@router.put("/menus/{menu_id}")
def update_menu(menu_id: int, payload: dict[str, Any] = Body(...),
                conn: sqlite3.Connection = Depends(get_conn),
                _admin: dict = Depends(require_admin)) -> dict[str, Any]:
    validate_menu_payload(payload)  # 전체 교체 → name/price 필수
    store_id = repo.get_default_store_id(conn)
    with db.transaction(conn):
        return repo.update_menu(conn, store_id, menu_id, payload)


@router.delete("/menus/{menu_id}", status_code=204)
def delete_menu(menu_id: int,
                conn: sqlite3.Connection = Depends(get_conn),
                _admin: dict = Depends(require_admin)) -> Response:
    store_id = repo.get_default_store_id(conn)
    with db.transaction(conn):
        repo.delete_menu(conn, store_id, menu_id)
    return Response(status_code=204)


# --------------------------------------------------------------------------
# 카테고리 (§3.4.6)
# --------------------------------------------------------------------------

@router.get("/categories")
def list_categories(conn: sqlite3.Connection = Depends(get_conn),
                    _admin: dict = Depends(require_admin)) -> dict[str, Any]:
    store_id = repo.get_default_store_id(conn)
    return {"categories": repo.list_categories(conn, store_id)}


@router.post("/categories", status_code=201)
def create_category(payload: dict[str, Any] = Body(...),
                    conn: sqlite3.Connection = Depends(get_conn),
                    _admin: dict = Depends(require_admin)) -> dict[str, Any]:
    _validate_category_payload(payload)
    store_id = repo.get_default_store_id(conn)
    with db.transaction(conn):
        return repo.create_category(conn, store_id, payload)


@router.put("/categories/{category_id}")
def update_category(category_id: int, payload: dict[str, Any] = Body(...),
                    conn: sqlite3.Connection = Depends(get_conn),
                    _admin: dict = Depends(require_admin)) -> dict[str, Any]:
    _validate_category_payload(payload)
    store_id = repo.get_default_store_id(conn)
    with db.transaction(conn):
        return repo.update_category(conn, store_id, category_id, payload)


@router.delete("/categories/{category_id}", status_code=204)
def delete_category(category_id: int,
                    conn: sqlite3.Connection = Depends(get_conn),
                    _admin: dict = Depends(require_admin)) -> Response:
    store_id = repo.get_default_store_id(conn)
    with db.transaction(conn):
        repo.delete_category(conn, store_id, category_id)
    return Response(status_code=204)
