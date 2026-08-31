"""Unit 1: 인증/해싱 헬퍼 (BR-10).

- 비밀번호(관리자·테이블) bcrypt 해싱/검증.
- JWT 발급/검증 유틸 (16시간 유효, §0.3). 인증 정책은 Unit 3 소유,
  여기서는 저수준 헬퍼만 제공한다.
"""
from __future__ import annotations

import datetime as _dt
from typing import Any

import bcrypt
import jwt

from app.core import config


# --- 비밀번호 해싱 ---

def hash_password(plain: str) -> str:
    """bcrypt 해시 문자열 반환."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """평문과 bcrypt 해시 비교."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# --- JWT ---

def create_token(claims: dict[str, Any], *, expires_seconds: int | None = None) -> str:
    """JWT 발급. exp 자동 설정(기본 16시간)."""
    exp_seconds = expires_seconds if expires_seconds is not None else config.JWT_EXPIRE_SECONDS
    now = _dt.datetime.now(_dt.timezone.utc)
    payload = dict(claims)
    payload["iat"] = int(now.timestamp())
    payload["exp"] = int((now + _dt.timedelta(seconds=exp_seconds)).timestamp())
    return jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """JWT 검증·디코드. 만료/무효 시 jwt 예외를 그대로 raise(Unit 3에서 처리)."""
    return jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
