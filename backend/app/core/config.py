"""Unit 1: 공통 설정.

환경 변수로 재정의 가능하지만 소규모/로컬 데모 기본값을 제공한다.
"""
from __future__ import annotations

import os
from pathlib import Path

# 프로젝트 루트(backend/) 기준 경로
BACKEND_DIR = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = BACKEND_DIR / "migrations"

# --- Database ---
# 기본: backend/table_order.db (로컬 파일). 테스트는 별도 임시 DB 사용(conftest).
DB_PATH: str = os.environ.get("TABLE_ORDER_DB", str(BACKEND_DIR / "table_order.db"))

# --- Auth (헬퍼 상수만 Unit 1 제공. 정책은 Unit 3) ---
JWT_SECRET: str = os.environ.get("TABLE_ORDER_JWT_SECRET", "dev-secret-change-me")
JWT_ALGORITHM: str = "HS256"
JWT_EXPIRE_SECONDS: int = 16 * 60 * 60  # 16시간 (Integration Contract §0.3)

# --- Pagination (§0.4) ---
DEFAULT_PAGE_SIZE: int = 20
MAX_PAGE_SIZE: int = 100

# --- Order number (BR-6) ---
ORDER_NUMBER_PREFIX: str = "A"

# 단일 매장 가정: 기본 store_code
DEFAULT_STORE_CODE: str = "STORE001"
