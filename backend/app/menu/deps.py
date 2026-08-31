"""Unit 5: FastAPI 의존성 (DB 연결 · 관리자 인증).

주의: 관리자 인증 정책의 최종 소유는 Unit 3(임동규)이다. Unit 3의 공용 인증
의존성이 준비되면 아래 require_admin 은 그쪽으로 교체/통합한다. 병렬 개발 동안
Unit 5가 독립적으로 동작하도록 core.security 만 사용하는 경량 구현을 둔다.
"""
from __future__ import annotations

import sqlite3
from typing import Any, Iterator

from fastapi import Header

from app.core import db, security
from app.core.errors import Unauthorized


def get_conn() -> Iterator[sqlite3.Connection]:
    """요청 범위 SQLite 연결. 종료 시 닫는다."""
    conn = db.connect()
    try:
        yield conn
    finally:
        conn.close()


def require_admin(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    """Authorization: Bearer <JWT> 검증 (§0.3). 실패 시 401 UNAUTHORIZED."""
    if not authorization or not authorization.startswith("Bearer "):
        raise Unauthorized("인증 토큰이 필요합니다.")
    token = authorization[len("Bearer "):]
    try:
        return security.decode_token(token)
    except Exception:  # 만료/무효 토큰 (jwt 예외 전부)
        raise Unauthorized("유효하지 않거나 만료된 토큰입니다.")
