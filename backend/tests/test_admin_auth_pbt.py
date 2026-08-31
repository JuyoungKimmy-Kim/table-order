"""Unit 3 PBT: 순수 함수 속성 (PBT-02/03/07/08).

대상:
- evaluate_login_attempt (attempts.py): 성공→리셋, 임계값 도달 시에만 잠금, 잠금 중 상태 불변.
- select_recent_orders (logic.py): 길이<=n, 미삭제만, ordered_at 내림차순, 입력순서 무관.
- build_admin_claims → create_token → decode_token round-trip 보존.

제너레이터는 Unit 1 tests/generators.py 를 재사용/확장한다(PBT-07).
"""
from __future__ import annotations

import datetime as _dt

from hypothesis import given, strategies as st

from tests.generators import st_money

from app.admin_auth.attempts import (
    AttemptState, DEFAULT_THRESHOLD, evaluate_login_attempt, is_locked,
)
from app.admin_auth.logic import build_admin_claims, select_recent_orders
from app.core import security


_NOW = _dt.datetime(2026, 8, 31, 12, 0, 0, tzinfo=_dt.timezone.utc)


# --- evaluate_login_attempt (PBT-03) ---

st_state = st.one_of(
    st.none(),
    st.builds(AttemptState,
              fail_count=st.integers(min_value=0, max_value=DEFAULT_THRESHOLD - 1),
              locked_until=st.none()),
)


@given(state=st_state)
def test_success_always_resets(state):
    """성공하면 항상 상태 리셋(next_state=None), allow=True."""
    d = evaluate_login_attempt(state, _NOW, success=True)
    assert d.allow is True
    assert d.next_state is None
    assert d.locked is False


@given(state=st_state)
def test_failure_increments_until_threshold(state):
    """임계값 미만 실패는 카운터 +1, 잠금 없음. 도달 시에만 잠금."""
    prev = state.fail_count if state else 0
    d = evaluate_login_attempt(state, _NOW, success=False)
    assert d.next_state is not None
    assert d.next_state.fail_count == prev + 1
    if prev + 1 >= DEFAULT_THRESHOLD:
        assert d.locked is True and d.allow is False
        assert d.next_state.locked_until is not None
    else:
        assert d.locked is False and d.allow is True
        assert d.next_state.locked_until is None


@given(extra_seconds=st.integers(min_value=1, max_value=299),
       success=st.booleans())
def test_locked_state_is_immutable(extra_seconds, success):
    """잠금 중에는 결과와 무관하게 상태 불변, allow=False."""
    locked_until = _NOW + _dt.timedelta(seconds=extra_seconds)
    state = AttemptState(fail_count=DEFAULT_THRESHOLD, locked_until=locked_until)
    assert is_locked(state, _NOW) is True
    d = evaluate_login_attempt(state, _NOW, success=success)
    assert d.allow is False and d.locked is True
    assert d.next_state == state


# --- select_recent_orders (PBT-03/07) ---

@st.composite
def st_monitor_order(draw):
    return {
        "id": draw(st.integers(min_value=1, max_value=10_000)),
        "total_amount": draw(st_money),
        "is_deleted": draw(st.booleans()),
        "ordered_at": draw(st.datetimes(
            min_value=_dt.datetime(2026, 1, 1),
            max_value=_dt.datetime(2026, 12, 31),
        ).map(lambda d: d.strftime("%Y-%m-%dT%H:%M:%SZ"))),
    }


st_monitor_orders = st.lists(st_monitor_order(), max_size=25,
                             unique_by=lambda o: o["id"])


@given(orders=st_monitor_orders, n=st.integers(min_value=0, max_value=5))
def test_recent_length_and_no_deleted(orders, n):
    res = select_recent_orders(orders, n)
    assert len(res) <= n
    assert all(not o["is_deleted"] for o in res)


@given(orders=st_monitor_orders)
def test_recent_sorted_desc(orders):
    res = select_recent_orders(orders)
    keys = [(o["ordered_at"], o["id"]) for o in res]
    assert keys == sorted(keys, reverse=True)


@given(orders=st_monitor_orders, seed=st.randoms(use_true_random=False))
def test_recent_input_order_independent(orders, seed):
    """입력 순서를 섞어도 결과는 동일(결정적 정렬)."""
    shuffled = list(orders)
    seed.shuffle(shuffled)
    assert select_recent_orders(orders) == select_recent_orders(shuffled)


# --- build_admin_claims round-trip (PBT-02) ---

@given(admin_id=st.integers(min_value=1, max_value=10_000),
       store_id=st.integers(min_value=1, max_value=1000),
       username=st.text(min_size=1, max_size=30))
def test_claims_token_roundtrip(admin_id, store_id, username):
    claims = build_admin_claims({"id": admin_id, "store_id": store_id, "username": username})
    token = security.create_token(claims)
    decoded = security.decode_token(token)
    assert decoded["sub"] == str(admin_id)
    assert decoded["store_id"] == store_id
    assert decoded["username"] == username
    assert decoded["role"] == "admin"
    assert "exp" in decoded and "iat" in decoded
