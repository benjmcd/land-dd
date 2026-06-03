#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "== agent context =="
./scripts/agent-context-check.sh

echo "== workspace validation =="
./scripts/validate_workspace.sh

echo "== backend tests =="
(
  cd backend
  PYTHONPATH=. python -m pytest -q
)

if command -v ruff >/dev/null 2>&1; then
  echo "== backend lint =="
  (cd backend && ruff check .)
else
  echo "ruff not installed; skipping lint"
fi

if command -v mypy >/dev/null 2>&1; then
  echo "== backend typecheck =="
  (cd backend && mypy app tests)
else
  echo "mypy not installed; skipping typecheck"
fi

if [[ "${RUN_DB_SMOKE:-0}" == "1" ]]; then
  echo "== db migration + smoke =="
  ./scripts/db_apply_migrations.sh
  python scripts/db_smoke_check.py
else
  echo "db smoke skipped; set RUN_DB_SMOKE=1 after 'make db-up'"
fi

echo "verify: ok"
