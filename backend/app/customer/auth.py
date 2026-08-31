"""Unit 2: 고객 인증 의존성 (BR-C1.4, BR-C1.5).

table_token(JWT)을 검증하여 인증 컨텍스트(table_id/store_id/table_number)를 제공한다.
table/store 식별자는 요청 본문이 아닌 토큰에서만 취득한다(BR-C1.5).
토큰 없음/만료/무효 시 core.errors.Unauthorized (401 표준 응답).
"""
from __future__ import annotations

from typing import Any

from fastapi import Header

from app.core import security
from app.core.errors import Unauthorized


def get_table_context(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    """Authorization: Bearer <table_token> 를 검증해 인증 컨텍스트 반환."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise Unauthorized("인증 토큰이 필요합니다.")
    token = authorization.split(" ", 1)[1].strip()
    try:
        claims = security.decode_token(token)
    except Exception:  # jwt 만료/무효 등 — 사유 미노출
        raise Unauthorized("인증 토큰이 유효하지 않거나 만료되었습니다.")
    sub = claims.get("sub")
    return {
        # sub 는 문자열로 발급되므로(로그인) 정수 table_id 로 복원.
        "table_id": int(sub) if sub is not None else None,
        "store_id": claims.get("store_id"),
        "table_number": claims.get("table_number"),
    }
