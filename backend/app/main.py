"""Unit 1: FastAPI 앱 부트스트랩.

여기서는 앱 생성 / 에러 핸들러 등록 / 시작 시 마이그레이션 적용 / health check 만
담당한다. 기능 라우터(고객/관리자/테이블/메뉴)는 각 유닛이 소유하며,
아래 '유닛 라우터 등록' 주석 위치에 include_router 로 결합한다.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core import db
from app.core.errors import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시 스키마 적용(멱등). 데모/로컬 편의.
    conn = db.connect()
    try:
        db.apply_migrations(conn)
    finally:
        conn.close()
    yield


app = FastAPI(title="Table Order Service", version="0.1.0", lifespan=lifespan)
register_exception_handlers(app)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


# --- 유닛 라우터 등록 (각 유닛이 아래에 추가) ---
# Unit 2: Customer Ordering (박찬준)
from app.customer.router import router as customer_router
app.include_router(customer_router, prefix="/api")
# Unit 3: Admin Auth & Real-time Monitoring (임동규)
from app.admin_auth.router import router as admin_router
app.include_router(admin_router, prefix="/api")
# Unit 4: Table & Session Management (이명우)
from app.tables.router import router as tables_router
app.include_router(tables_router, prefix="/api")
# Unit 5: Menu Management (윤태경)
from app.menu.router import router as menu_router
app.include_router(menu_router, prefix="/api")
# 방명록(Guestbook): 고객 그림판 카드메모 (매장 공유)
from app.guestbook.router import router as guestbook_router
app.include_router(guestbook_router, prefix="/api")
