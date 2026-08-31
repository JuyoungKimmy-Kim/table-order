"""Unit 4: FastAPI 의존성 (DB 연결 · 관리자 인증).

- get_conn: 요청 단위 sqlite 연결 제공(종료 시 close).
- require_admin: Authorization: Bearer <JWT> 검증 (§0.3, U4-BR-6).
  인증 정책은 Unit 3 소유이나, Unit 4는 병렬 개발을 위해 core.security 기반의
  로컬 검증 의존성만 둔다. Unit 3의 토큰 클레임(store_id) 규약을 따른다.
"""
from __future__ import annotations

import sqlite3
from typing import Any, AsyncIterator

from fastapi import Header

from app.core import config, db, security
from app.core.errors import Conflict, Unauthorized


async def get_conn() -> AsyncIterator[sqlite3.Connection]:
    """요청 단위 DB 연결. 종료 시 닫는다.

    async 로 두어 (async 핸들러와 동일한) 이벤트 루프 스레드에서 연결이 생성/사용되도록
    한다. sqlite 연결은 스레드 바인딩되므로, 핸들러도 모두 async 로 통일한다.
    소규모/로컬 가정이라 이벤트 루프에서의 동기 sqlite I/O 는 허용한다.
    """
    conn = db.connect()
    try:
        yield conn
    finally:
        conn.close()


def require_admin(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    """Bearer JWT 검증 후 클레임 반환. 실패 시 401 UNAUTHORIZED (U4-BR-6.1)."""
    if not authorization or not authorization.startswith("Bearer "):
        raise Unauthorized("인증 토큰이 필요합니다.")
    token = authorization.split(" ", 1)[1]
    try:
        return security.decode_token(token)
    except Exception:  # noqa: BLE001 — jwt 예외 전반을 401로 매핑
        raise Unauthorized("유효하지 않거나 만료된 토큰입니다.")


def resolve_store_id(conn: sqlite3.Connection, claims: dict[str, Any]) -> int:
    """토큰 클레임의 store_id 우선, 없으면 단일 매장 기본값 (U4-BR-7.2)."""
    sid = claims.get("store_id")
    if isinstance(sid, int) and not isinstance(sid, bool):
        return sid
    row = conn.execute(
        "SELECT id FROM stores WHERE store_code = ?", (config.DEFAULT_STORE_CODE,)
    ).fetchone()
    if row is None:
        raise Conflict("매장 정보가 없습니다. 시드를 먼저 실행하세요.")
    return int(row["id"])
