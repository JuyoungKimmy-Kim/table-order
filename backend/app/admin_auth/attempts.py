"""Unit 3: 로그인 시도 제한 (BR-A2, Q1=A/Q2=A).

정책: 동일 (store_code, username) 기준 연속 5회 실패 → 5분 잠금.
성공 시 카운터 리셋. 저장은 인메모리(재시작 리셋 허용).

판정 로직 `evaluate_login_attempt` 는 순수 함수(부작용 없음) — PBT 대상.
`LoginAttemptTracker` 는 그 결과를 프로세스 dict 에 저장만 한다.
"""
from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass
from typing import Optional

DEFAULT_THRESHOLD = 5
DEFAULT_LOCKOUT_SECONDS = 5 * 60


@dataclass(frozen=True)
class AttemptState:
    """(store_code, username) 별 시도 상태."""
    fail_count: int = 0
    locked_until: Optional[_dt.datetime] = None


@dataclass(frozen=True)
class Decision:
    """시도 판정 결과.

    - allow: 이번 요청에 대해 인증 시도를 허용할지(잠금 중이면 False).
    - locked: 현재 잠금 상태인지.
    - next_state: 갱신할 상태. None 이면 상태 제거(리셋).
    """
    allow: bool
    locked: bool
    next_state: Optional[AttemptState]


def is_locked(state: Optional[AttemptState], now: _dt.datetime) -> bool:
    """현재 잠금 상태 여부(순수)."""
    return bool(state and state.locked_until is not None and now < state.locked_until)


def evaluate_login_attempt(
    state: Optional[AttemptState],
    now: _dt.datetime,
    *,
    success: bool,
    threshold: int = DEFAULT_THRESHOLD,
    lockout_seconds: int = DEFAULT_LOCKOUT_SECONDS,
) -> Decision:
    """로그인 시도 판정 (순수 함수, BR-A2).

    호출 순서 규약:
      1) 요청 진입 시 `evaluate_login_attempt(state, now, success=False가 아닌)`가 아니라,
         먼저 잠금이면 인증을 건너뛰어야 하므로 `is_locked` 로 사전 확인한다.
      2) 인증 결과가 나온 뒤 success 값으로 이 함수를 호출해 next_state 를 얻는다.

    규칙:
      - 잠금 중(now < locked_until): allow=False, locked=True, 상태 불변.
      - success=True: 상태 리셋(next_state=None), allow=True.
      - success=False: fail_count += 1. threshold 도달 시 now+lockout 로 잠금.
    """
    if is_locked(state, now):
        return Decision(allow=False, locked=True, next_state=state)

    if success:
        return Decision(allow=True, locked=False, next_state=None)

    prev = state.fail_count if state else 0
    fail = prev + 1
    if fail >= threshold:
        locked_until = now + _dt.timedelta(seconds=lockout_seconds)
        return Decision(allow=False, locked=True,
                        next_state=AttemptState(fail_count=fail, locked_until=locked_until))
    return Decision(allow=True, locked=False,
                    next_state=AttemptState(fail_count=fail, locked_until=None))


class LoginAttemptTracker:
    """인메모리 시도 추적기(BR-A2.1). 단일 프로세스 가정."""

    def __init__(self, *, threshold: int = DEFAULT_THRESHOLD,
                 lockout_seconds: int = DEFAULT_LOCKOUT_SECONDS) -> None:
        self._store: dict[tuple[str, str], AttemptState] = {}
        self._threshold = threshold
        self._lockout_seconds = lockout_seconds

    @staticmethod
    def _now() -> _dt.datetime:
        return _dt.datetime.now(_dt.timezone.utc)

    def is_locked(self, store_code: str, username: str) -> bool:
        return is_locked(self._store.get((store_code, username)), self._now())

    def record(self, store_code: str, username: str, *, success: bool) -> Decision:
        """인증 결과를 반영하고 상태를 갱신한다. Decision 반환."""
        key = (store_code, username)
        decision = evaluate_login_attempt(
            self._store.get(key), self._now(), success=success,
            threshold=self._threshold, lockout_seconds=self._lockout_seconds,
        )
        if decision.next_state is None:
            self._store.pop(key, None)
        else:
            self._store[key] = decision.next_state
        return decision

    def reset(self, store_code: str, username: str) -> None:
        self._store.pop((store_code, username), None)


# 프로세스 전역 트래커(단일 프로세스 가정).
tracker = LoginAttemptTracker()
