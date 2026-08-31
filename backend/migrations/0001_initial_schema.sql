-- Unit 1: Foundation & Shared Core — Initial Schema
-- 기준: aidlc-docs/inception/application-design/integration-contract.md §1
--       aidlc-docs/construction/unit1-foundation/functional-design/domain-entities.md
-- 규약: 금액=정수(원), 시각=UTC ISO8601 문자열(TEXT), 소유=Unit 1(김주영)

PRAGMA foreign_keys = ON;

-- 1. stores (매장)
CREATE TABLE IF NOT EXISTS stores (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    store_code  TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

-- 2. admin_users (관리자 계정)
CREATE TABLE IF NOT EXISTS admin_users (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id       INTEGER NOT NULL REFERENCES stores(id),
    username       TEXT NOT NULL,
    password_hash  TEXT NOT NULL,           -- bcrypt
    created_at     TEXT NOT NULL,
    updated_at     TEXT NOT NULL,
    UNIQUE(store_id, username)
);

-- 3. tables (테이블)
CREATE TABLE IF NOT EXISTS tables (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id       INTEGER NOT NULL REFERENCES stores(id),
    table_number   INTEGER NOT NULL,
    password_hash  TEXT NOT NULL,           -- bcrypt
    created_at     TEXT NOT NULL,
    updated_at     TEXT NOT NULL,
    UNIQUE(store_id, table_number)
);

-- 4. table_sessions (테이블 세션)
CREATE TABLE IF NOT EXISTS table_sessions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    table_id    INTEGER NOT NULL REFERENCES tables(id),
    status      TEXT NOT NULL CHECK(status IN ('active', 'closed')),
    opened_at   TEXT NOT NULL,
    closed_at   TEXT,                        -- active면 NULL
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);
-- 불변식(Q3=A): 한 테이블에 active 세션은 최대 1개 (부분 유니크 인덱스)
CREATE UNIQUE INDEX IF NOT EXISTS ux_active_session
    ON table_sessions(table_id) WHERE status = 'active';

-- 5. categories (메뉴 카테고리)
CREATE TABLE IF NOT EXISTS categories (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id       INTEGER NOT NULL REFERENCES stores(id),
    name           TEXT NOT NULL,
    display_order  INTEGER NOT NULL DEFAULT 0,
    created_at     TEXT NOT NULL,
    updated_at     TEXT NOT NULL
);

-- 6. menus (메뉴)
CREATE TABLE IF NOT EXISTS menus (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id       INTEGER NOT NULL REFERENCES stores(id),
    category_id    INTEGER NOT NULL REFERENCES categories(id),
    name           TEXT NOT NULL,
    price          INTEGER NOT NULL CHECK(price >= 0),
    description    TEXT,
    image_url      TEXT,
    display_order  INTEGER NOT NULL DEFAULT 0,
    is_available   INTEGER NOT NULL DEFAULT 1 CHECK(is_available IN (0, 1)),
    created_at     TEXT NOT NULL,
    updated_at     TEXT NOT NULL
);

-- 7. orders (주문)
CREATE TABLE IF NOT EXISTS orders (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id    INTEGER NOT NULL REFERENCES table_sessions(id),
    table_id      INTEGER NOT NULL REFERENCES tables(id),
    order_number  TEXT NOT NULL UNIQUE,        -- 예: A-20260831-0007
    status        TEXT NOT NULL DEFAULT 'pending'
                       CHECK(status IN ('pending', 'preparing', 'completed')),
    total_amount  INTEGER NOT NULL,            -- 주문 총액 스냅샷
    is_deleted    INTEGER NOT NULL DEFAULT 0 CHECK(is_deleted IN (0, 1)),
    ordered_at    TEXT NOT NULL,
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_orders_session ON orders(session_id);
CREATE INDEX IF NOT EXISTS ix_orders_table   ON orders(table_id);

-- 8. order_items (주문 항목) — 스냅샷(menu_name, unit_price) 저장
CREATE TABLE IF NOT EXISTS order_items (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id   INTEGER NOT NULL REFERENCES orders(id),
    menu_id    INTEGER NOT NULL REFERENCES menus(id),
    menu_name  TEXT NOT NULL,                  -- 주문 시점 스냅샷
    unit_price INTEGER NOT NULL CHECK(unit_price >= 0),  -- 주문 시점 스냅샷
    quantity   INTEGER NOT NULL CHECK(quantity > 0),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_order_items_order ON order_items(order_id);

-- 9. order_history (과거 주문 이력) — 세션 종료 시 이동본 (orders 동일 컬럼 + 추가)
CREATE TABLE IF NOT EXISTS order_history (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    original_order_id  INTEGER,                -- 이동 전 orders.id (추적용)
    store_id           INTEGER NOT NULL REFERENCES stores(id),
    session_id         INTEGER NOT NULL,
    table_id           INTEGER NOT NULL,
    order_number       TEXT NOT NULL,
    status             TEXT NOT NULL,
    total_amount       INTEGER NOT NULL,
    is_deleted         INTEGER NOT NULL DEFAULT 0,
    ordered_at         TEXT NOT NULL,
    session_closed_at  TEXT NOT NULL,          -- 세션 종료 시각
    created_at         TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_history_table ON order_history(table_id);
CREATE INDEX IF NOT EXISTS ix_history_ordered ON order_history(ordered_at);

-- 9b. order_history_items — 이력 주문의 항목 스냅샷 사본
CREATE TABLE IF NOT EXISTS order_history_items (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    history_order_id  INTEGER NOT NULL REFERENCES order_history(id),
    menu_id           INTEGER,
    menu_name         TEXT NOT NULL,
    unit_price        INTEGER NOT NULL,
    quantity          INTEGER NOT NULL,
    created_at        TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_history_items_order ON order_history_items(history_order_id);

-- daily order sequence — 주문번호 당일 시퀀스 채번 (Q1=A, Q2=A: store+UTC날짜별 리셋)
CREATE TABLE IF NOT EXISTS order_sequences (
    store_id   INTEGER NOT NULL,
    seq_date   TEXT NOT NULL,                  -- YYYYMMDD (UTC)
    last_seq   INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (store_id, seq_date)
);
