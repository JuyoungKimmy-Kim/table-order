"""Unit 3: 인증 dependency (BR-A3).

Authorization: Bearer <JWT> → decode → AdminPrincipal. DB 재조회 없음(Q3=A).
토큰 없음/무효/만료는 Unit 1 errors.Unauthorized 로 통일(§0.2).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import jwt
from fastapi import Header

from app.core import security
from app.core.errors import Unauthorized


@dataclass(frozen=True)
class AdminPrincipal:
    admin_user_id: int
    store_id: int
    username: str
    role: str = "admin"


def _extract_bearer(authorization: Optional[str]) -> str:
    if not authorization:
        raise Unauthorized("인증 토큰이 없습니다.")
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise Unauthorized("인증 형식이 올바르지 않습니다.")
    return parts[1].strip()


def principal_from_token(token: str) -> AdminPrincipal:
    """토큰을 검증하고 AdminPrincipal 을 만든다(순수에 가까운 헬퍼)."""
    try:
        claims = security.decode_token(token)
    except jwt.PyJWTError:
        raise Unauthorized("인증 토큰이 유효하지 않습니다.")
    try:
        return AdminPrincipal(
            admin_user_id=int(claims["sub"]),
            store_id=int(claims["store_id"]),
            username=str(claims["username"]),
            role=str(claims.get("role", "admin")),
        )
    except (KeyError, TypeError, ValueError):
        raise Unauthorized("인증 토큰 정보가 올바르지 않습니다.")


async def get_current_admin(authorization: Optional[str] = Header(default=None)) -> AdminPrincipal:
    """FastAPI dependency. 보호 엔드포인트에서 Depends 로 사용."""
    token = _extract_bearer(authorization)
    return principal_from_token(token)
