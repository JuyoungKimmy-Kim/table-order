"""Unit 1: SQLite 접근 계층 (경량, ORM 없음 — Q6=A).

- `connect()`: Row 팩토리·외래키 제약이 켜진 연결 반환.
- `transaction()`: 커밋/롤백을 자동 처리하는 컨텍스트 매니저.
- `apply_migrations()`: migrations/*.sql 을 순서대로 적용(멱등).

모든 유닛은 이 모듈을 통해 DB에 접근한다.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from app.core import config


def connect(db_path: str | None = None) -> sqlite3.Connection:
    """SQLite 연결을 생성한다. Row 팩토리와 FK 제약을 활성화한다."""
    path = db_path or config.DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


@contextmanager
def transaction(conn: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    """트랜잭션 컨텍스트. 정상 종료 시 commit, 예외 시 rollback."""
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def apply_migrations(conn: sqlite3.Connection, migrations_dir: Path | None = None) -> None:
    """migrations 디렉토리의 .sql 파일을 이름 오름차순으로 적용한다.

    스키마는 `CREATE TABLE IF NOT EXISTS` 로 작성되어 있어 반복 적용해도 안전하다.
    seed.sql 은 마이그레이션 대상에서 제외한다(선택적 시드).
    """
    directory = migrations_dir or config.MIGRATIONS_DIR
    sql_files = sorted(
        p for p in directory.glob("*.sql") if p.name != "seed.sql"
    )
    for sql_file in sql_files:
        conn.executescript(sql_file.read_text(encoding="utf-8"))
    conn.commit()


def apply_seed(conn: sqlite3.Connection, migrations_dir: Path | None = None) -> None:
    """seed.sql 을 적용한다(개발/데모용). 존재하지 않으면 무시."""
    directory = migrations_dir or config.MIGRATIONS_DIR
    seed = directory / "seed.sql"
    if seed.exists():
        conn.executescript(seed.read_text(encoding="utf-8"))
        conn.commit()
