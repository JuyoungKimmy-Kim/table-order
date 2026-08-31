"""방명록 API 통합 테스트.

FastAPI TestClient + 임시 파일 DB(시드 포함)로 작성/조회/검증을 다룬다.
- 작성(인증), 검증 실패(형식/빈 이미지/용량 초과),
- 매장 단위 공유 조회(다른 테이블이 남긴 카드도 보임), 최신순 정렬, 페이지네이션.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core import config

# 1x1 투명 PNG DataURL (검증 통과용 최소 유효 데이터)
PNG_1PX = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_file = tmp_path / "gb_test.db"
    monkeypatch.setattr(config, "DB_PATH", str(db_file))
    from migrations.seed import seed
    seed()  # apply_migrations + 시드(STORE001, 테이블 1~3)
    from app.main import app
    with TestClient(app) as c:
        yield c


def _token(client, table_number=1, password="1234", store_code="STORE001") -> str:
    r = client.post("/api/customer/login", json={
        "store_code": store_code, "table_number": table_number, "password": password,
    })
    assert r.status_code == 200, r.text
    return r.json()["table_token"]


def _auth(token) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# --- 작성 ---

def test_create_guestbook_success(client):
    token = _token(client)
    r = client.post("/api/customer/guestbook", headers=_auth(token),
                    json={"author_name": "찬준", "image_data": PNG_1PX})
    assert r.status_code == 201, r.text
    body = r.json()
    assert set(body) == {"id", "author_name", "image_data", "created_at"}
    assert body["author_name"] == "찬준"
    assert body["image_data"] == PNG_1PX


def test_create_guestbook_author_optional(client):
    token = _token(client)
    r = client.post("/api/customer/guestbook", headers=_auth(token),
                    json={"image_data": PNG_1PX})
    assert r.status_code == 201, r.text
    assert r.json()["author_name"] is None


def test_create_guestbook_requires_auth(client):
    r = client.post("/api/customer/guestbook", json={"image_data": PNG_1PX})
    assert r.status_code == 401


def test_create_guestbook_bad_format_400(client):
    token = _token(client)
    r = client.post("/api/customer/guestbook", headers=_auth(token),
                    json={"image_data": "not-a-data-url"})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


def test_create_guestbook_empty_image_400(client):
    token = _token(client)
    r = client.post("/api/customer/guestbook", headers=_auth(token),
                    json={"image_data": "data:image/png;base64,"})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


def test_create_guestbook_too_large_400(client):
    token = _token(client)
    huge = "data:image/png;base64," + ("A" * 3_000_001)
    r = client.post("/api/customer/guestbook", headers=_auth(token),
                    json={"image_data": huge})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


# --- 조회 ---

def test_list_guestbook_shared_across_tables_newest_first(client):
    # 테이블 1이 2건, 테이블 2가 1건 작성 → 매장 단위로 모두 조회됨
    t1 = _token(client, table_number=1)
    t2 = _token(client, table_number=2)
    client.post("/api/customer/guestbook", headers=_auth(t1),
                json={"author_name": "A", "image_data": PNG_1PX})
    client.post("/api/customer/guestbook", headers=_auth(t1),
                json={"author_name": "B", "image_data": PNG_1PX})
    client.post("/api/customer/guestbook", headers=_auth(t2),
                json={"author_name": "C", "image_data": PNG_1PX})

    r = client.get("/api/customer/guestbook", headers=_auth(t2))
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 3
    # 최신순(created_at DESC, id DESC) → 마지막에 넣은 것이 먼저. id 역순 확인.
    ids = [e["id"] for e in body["items"]]
    assert ids == sorted(ids, reverse=True)


def test_list_guestbook_requires_auth(client):
    r = client.get("/api/customer/guestbook")
    assert r.status_code == 401


def test_list_guestbook_pagination(client):
    token = _token(client)
    for _ in range(3):
        client.post("/api/customer/guestbook", headers=_auth(token),
                    json={"image_data": PNG_1PX})
    r = client.get("/api/customer/guestbook?page=1&size=2", headers=_auth(token))
    body = r.json()
    assert body["total"] == 3 and body["size"] == 2 and body["page"] == 1
    assert len(body["items"]) == 2
