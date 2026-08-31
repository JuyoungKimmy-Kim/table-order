"""Unit 3 예제 기반 테스트 (PBT-10 보완).

시도 제한 시나리오와 상태값 검증을 고정 예제로 확인한다.
"""
from __future__ import annotations

import datetime as _dt

import pytest

from app.admin_auth.attempts import LoginAttemptTracker
from app.core.errors import ValidationError
from app.core.validation import validate_order_status


def test_five_failures_then_locked():
    """연속 5회 실패 → 5번째부터 잠금(BR-A2.2)."""
    t = LoginAttemptTracker()
    for _ in range(4):
        d = t.record("STORE001", "admin", success=False)
        assert d.locked is False
    d5 = t.record("STORE001", "admin", success=False)
    assert d5.locked is True
    assert t.is_locked("STORE001", "admin") is True


def test_success_resets_counter():
    t = LoginAttemptTracker()
    for _ in range(3):
        t.record("STORE001", "admin", success=False)
    t.record("STORE001", "admin", success=True)
    assert t.is_locked("STORE001", "admin") is False
    # 리셋되었으므로 다시 4회까지는 잠기지 않음
    for _ in range(4):
        d = t.record("STORE001", "admin", success=False)
        assert d.locked is False


def test_lockout_expires():
    """잠금 만료 후 첫 시도는 카운터 0에서 재시작(BR-A2.4)."""
    t = LoginAttemptTracker(lockout_seconds=0)  # 즉시 만료
    for _ in range(5):
        t.record("STORE001", "admin", success=False)
    # lockout_seconds=0 → locked_until == now, is_locked(now<until)=False 곧 해제
    assert t.is_locked("STORE001", "admin") is False


@pytest.mark.parametrize("status", ["pending", "preparing", "completed"])
def test_valid_status_ok(status):
    validate_order_status(status)  # 예외 없어야 함


@pytest.mark.parametrize("status", ["done", "", "PENDING", "cancelled"])
def test_invalid_status_rejected(status):
    with pytest.raises(ValidationError):
        validate_order_status(status)
