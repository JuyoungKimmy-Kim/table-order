"""Unit 1: 개발/데모 시드 스크립트.

bcrypt 해시가 필요하므로 SQL 대신 파이썬 스크립트로 시드한다.
실행: (backend 디렉토리에서)  python -m migrations.seed
멱등: store_code/username/table_number 기준으로 이미 있으면 건너뛴다.

시드 내용(단일 매장):
- store: STORE001 / 홍길동식당
- admin: admin / admin1234
- tables: 1~3번 (비밀번호 각각 '1234')
- categories: 메인, 사이드, 음료
- menus: 카테고리별 샘플 메뉴
"""
from __future__ import annotations

import datetime as _dt

from app.core import config, db
from app.core.security import hash_password


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def seed() -> None:
    conn = db.connect()
    try:
        db.apply_migrations(conn)
        now = _now()
        with db.transaction(conn):
            # store
            store = conn.execute(
                "SELECT id FROM stores WHERE store_code = ?", (config.DEFAULT_STORE_CODE,)
            ).fetchone()
            if store is None:
                cur = conn.execute(
                    "INSERT INTO stores(store_code, name, created_at, updated_at) VALUES (?,?,?,?)",
                    (config.DEFAULT_STORE_CODE, "홍길동식당", now, now),
                )
                store_id = cur.lastrowid
            else:
                store_id = store["id"]

            # admin
            if conn.execute(
                "SELECT 1 FROM admin_users WHERE store_id=? AND username=?", (store_id, "admin")
            ).fetchone() is None:
                conn.execute(
                    "INSERT INTO admin_users(store_id, username, password_hash, created_at, updated_at)"
                    " VALUES (?,?,?,?,?)",
                    (store_id, "admin", hash_password("admin1234"), now, now),
                )

            # tables 1~3
            for tn in (1, 2, 3):
                if conn.execute(
                    "SELECT 1 FROM tables WHERE store_id=? AND table_number=?", (store_id, tn)
                ).fetchone() is None:
                    conn.execute(
                        "INSERT INTO tables(store_id, table_number, password_hash, created_at, updated_at)"
                        " VALUES (?,?,?,?,?)",
                        (store_id, tn, hash_password("1234"), now, now),
                    )

            # categories
            cat_ids: dict[str, int] = {}
            for order, cname in enumerate(["메인", "사이드", "음료"]):
                row = conn.execute(
                    "SELECT id FROM categories WHERE store_id=? AND name=?", (store_id, cname)
                ).fetchone()
                if row is None:
                    cur = conn.execute(
                        "INSERT INTO categories(store_id, name, display_order, created_at, updated_at)"
                        " VALUES (?,?,?,?,?)",
                        (store_id, cname, order, now, now),
                    )
                    cat_ids[cname] = cur.lastrowid
                else:
                    cat_ids[cname] = row["id"]

            # menus
            samples = [
                ("메인", "김치찌개", 8000, "얼큰한 김치찌개"),
                ("메인", "된장찌개", 8000, "구수한 된장찌개"),
                ("사이드", "계란말이", 6000, "폭신한 계란말이"),
                ("음료", "콜라", 2000, None),
                ("음료", "사이다", 2000, None),
            ]
            for order, (cname, mname, price, desc) in enumerate(samples):
                if conn.execute(
                    "SELECT 1 FROM menus WHERE store_id=? AND name=?", (store_id, mname)
                ).fetchone() is None:
                    conn.execute(
                        "INSERT INTO menus(store_id, category_id, name, price, description,"
                        " image_url, display_order, is_available, created_at, updated_at)"
                        " VALUES (?,?,?,?,?,?,?,1,?,?)",
                        (store_id, cat_ids[cname], mname, price, desc, None, order, now, now),
                    )
        print(f"seed 완료: store_id={store_id}")
    finally:
        conn.close()


if __name__ == "__main__":
    seed()
