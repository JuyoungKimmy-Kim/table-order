"""개발용 메뉴/카테고리 초기화 스크립트.

frontend/customer/src/mock/restaurant-menu.js 에서 생성한
dev/dev_menu_reset.sql 을 적용해 STORE001 의 메뉴/카테고리를 mock 데이터로
재설정한다. 다른 데이터(stores/admin/tables/sessions/orders/guestbook)는
건드리지 않는다.

실행(backend 디렉토리에서):
    export PYTHONPATH=.
    python -m dev.dev_reset

주의:
- 이 스크립트는 **개발 전용**이다. 프로덕션에서 실행하지 말 것.
- dev_menu_reset.sql 은 migrations 디렉토리 밖(dev/)에 있으므로
  db.apply_migrations() 로 자동 적용되지 않는다. 초기화는 오직 여기서만.
- order_items.menu_id 가 menus 를 FK 참조하므로 삭제 시 PRAGMA foreign_keys=OFF
  로 감싼다(주문 항목은 menu_name/unit_price 를 스냅샷 보관 — §1.8, 안전).
"""
from __future__ import annotations

from pathlib import Path

from app.core import db
from migrations.seed import seed

_SQL_PATH = Path(__file__).resolve().parent / "dev_menu_reset.sql"


def reset_dev_menu() -> None:
    # 1) STORE001/관리자/테이블 등 기본 데이터 보장(멱등). 마이그레이션도 함께 적용.
    seed()

    if not _SQL_PATH.exists():
        raise FileNotFoundError(
            f"{_SQL_PATH} 이 없습니다. 먼저 'node dev/gen_dev_menu_sql.mjs' 로 생성하세요."
        )

    sql = _SQL_PATH.read_text(encoding="utf-8")

    conn = db.connect()
    try:
        # FK 제약을 잠시 끄고 메뉴 삭제/재삽입(order_items 스냅샷은 유지).
        conn.execute("PRAGMA foreign_keys = OFF;")
        with db.transaction(conn):
            conn.executescript(sql)
        conn.execute("PRAGMA foreign_keys = ON;")

        store = conn.execute(
            "SELECT id FROM stores WHERE store_code = 'STORE001'"
        ).fetchone()
        store_id = store["id"] if store else None
        cats = conn.execute(
            "SELECT COUNT(*) AS c FROM categories WHERE store_id = ?", (store_id,)
        ).fetchone()["c"]
        menus = conn.execute(
            "SELECT COUNT(*) AS c FROM menus WHERE store_id = ?", (store_id,)
        ).fetchone()["c"]
        print(f"dev 메뉴 초기화 완료: 카테고리 {cats}개, 메뉴 {menus}개 (STORE001)")
    finally:
        conn.close()


if __name__ == "__main__":
    reset_dev_menu()
