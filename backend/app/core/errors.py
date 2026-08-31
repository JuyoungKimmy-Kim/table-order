"""Unit 1: 표준 에러 응답 포맷 + 도메인 예외 (Integration Contract §0.2).

모든 4xx/5xx 응답은 {"error": {"code", "message", "details"}} 구조를 따른다.
FastAPI 앱은 register_exception_handlers(app) 로 핸들러를 등록한다.
"""
from __future__ import annotations

from typing import Any


class AppError(Exception):
    """도메인 예외의 기반. code/http_status/message/details 를 가진다."""

    code: str = "INTERNAL_ERROR"
    http_status: int = 500

    def __init__(self, message: str, details: dict[str, Any] | None = None,
                 *, code: str | None = None, http_status: int | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        if code is not None:
            self.code = code
        if http_status is not None:
            self.http_status = http_status

    def to_response(self) -> dict[str, Any]:
        return {"error": {"code": self.code, "message": self.message, "details": self.details}}


# --- 공통 에러 (§0.2) ---

class ValidationError(AppError):
    code = "VALIDATION_ERROR"
    http_status = 400


class Unauthorized(AppError):
    code = "UNAUTHORIZED"
    http_status = 401


class Forbidden(AppError):
    code = "FORBIDDEN"
    http_status = 403


class NotFound(AppError):
    code = "NOT_FOUND"
    http_status = 404


class Conflict(AppError):
    code = "CONFLICT"
    http_status = 409


class TooManyAttempts(AppError):
    code = "TOO_MANY_ATTEMPTS"
    http_status = 429


# --- 구체 에러 코드 (§3) ---

class MenuNotFound(NotFound):
    code = "MENU_NOT_FOUND"


class MenuUnavailable(Conflict):
    code = "MENU_UNAVAILABLE"


class OrderNotFound(NotFound):
    code = "ORDER_NOT_FOUND"


class NoActiveSession(Conflict):
    code = "NO_ACTIVE_SESSION"


def register_exception_handlers(app) -> None:
    """FastAPI 앱에 AppError → 표준 응답 핸들러를 등록한다."""
    from fastapi import Request
    from fastapi.responses import JSONResponse

    @app.exception_handler(AppError)
    async def _handle_app_error(_: Request, exc: AppError):  # noqa: ANN001
        return JSONResponse(status_code=exc.http_status, content=exc.to_response())
