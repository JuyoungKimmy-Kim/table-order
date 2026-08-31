"""pytest 공통 fixture + Hypothesis 프로파일 (PBT-08).

- Hypothesis 프로파일:
    * default: shrinking 유지, 로컬 개발용.
    * ci: derandomize=True(고정 seed) — 재현 가능한 CI 실행.
  환경변수 HYPOTHESIS_PROFILE 로 선택(기본 default). 실패 시 Hypothesis 가
  최소 반례와 재현 정보를 출력한다(shrinking 비활성화하지 않음).
- tmp DB fixture: 파일 기반 임시 SQLite 에 스키마를 적용해 제공.
"""
from __future__ import annotations

import os

import pytest
from hypothesis import settings, Verbosity


settings.register_profile("default", max_examples=200, verbosity=Verbosity.normal)
# CI: 고정 seed 로 결정적 실행(PBT-08 재현성). shrinking 은 그대로 유지.
settings.register_profile("ci", max_examples=300, derandomize=True,
                          print_blob=True, verbosity=Verbosity.normal)
settings.load_profile(os.environ.get("HYPOTHESIS_PROFILE", "default"))


@pytest.fixture()
def db_conn(tmp_path):
    """임시 파일 DB 에 스키마를 적용한 연결을 제공한다."""
    from app.core import db

    db_file = tmp_path / "test.db"
    conn = db.connect(str(db_file))
    db.apply_migrations(conn)
    try:
        yield conn
    finally:
        conn.close()
