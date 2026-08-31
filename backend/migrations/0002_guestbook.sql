-- 방명록(Guestbook) — 고객이 그림판으로 그려 남기는 카드메모
-- 그림은 PNG DataURL(base64) 문자열로 저장. 매장 단위 공유(같은 store 전체 조회).
-- 규약: 시각=UTC ISO8601 문자열(TEXT), 금액 미사용.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS guestbook_entries (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id     INTEGER NOT NULL REFERENCES stores(id),
    table_id     INTEGER,               -- 작성 테이블(추적용, NULL 허용)
    author_name  TEXT,                  -- 선택 입력 닉네임(미입력 시 NULL)
    image_data   TEXT NOT NULL,         -- data:image/png;base64,... (크기 제한은 서비스 계층 검증)
    created_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_guestbook_store ON guestbook_entries(store_id);
