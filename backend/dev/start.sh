#!/usr/bin/env bash
# 개발 서버 시작 (backend). 시작 시 STORE001 메뉴/카테고리를 mock 데이터로 항상 초기화한다.
#
# 사용법 (backend 디렉토리에서):
#   ./dev/start.sh
#
# 동작:
#   1) 기존 8000 포트 리스너 정리
#   2) mock → dev/dev_menu_reset.sql 재생성 (node 있을 때만)
#   3) DEV_MENU_RESET=1 로 uvicorn --reload 실행
#      → main.py lifespan 이 매 시작 시 dev.dev_reset 을 호출해 메뉴 초기화
#
# ⚠️ 개발 전용. 프로덕션에서는 이 스크립트/환경변수를 사용하지 말 것.
set -euo pipefail

cd "$(dirname "$0")/.."   # backend/

# 1) 기존 개발 서버 정리
if lsof -ti tcp:8000 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "기존 8000 포트 서버 정리 중…"
  lsof -ti tcp:8000 -sTCP:LISTEN | xargs kill 2>/dev/null || true
  sleep 1
fi

# 2) mock 기준으로 SQL 재생성 (node 가 있을 때만; 실패해도 기존 SQL 로 진행)
if command -v node >/dev/null 2>&1; then
  echo "mock → dev/dev_menu_reset.sql 재생성…"
  node dev/gen_dev_menu_sql.mjs || echo "(SQL 재생성 실패 — 기존 파일로 진행)"
fi

# 3) 개발 서버 실행 (시작 시 메뉴 초기화)
export PYTHONPATH=.
export DEV_MENU_RESET=1

if [ -f .venv/bin/activate ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

echo "uvicorn 시작 (DEV_MENU_RESET=1)…"
exec uvicorn app.main:app --reload
