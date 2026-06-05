#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python}"
"$PYTHON_BIN" - <<'PY'
import sys

if sys.version_info < (3, 12):
    raise SystemExit(
        f"Python 3.12+ is required; found {sys.version.split()[0]}"
    )
print(f"python: {sys.version.split()[0]}")
PY

echo "== workspace validation =="
PYTHON_BIN="$PYTHON_BIN" ./scripts/validate_workspace.sh

if [[ "${RUN_DB_SMOKE:-0}" == "1" ]]; then
  echo "== db migration + seed =="
  ./scripts/db_apply_migrations.sh
fi

echo "== backend tests =="
(
  cd backend
  PYTHONPATH=. "$PYTHON_BIN" -m pytest -q
)

echo "== backend lint =="
(cd backend && "$PYTHON_BIN" -m ruff check .)

echo "== backend typecheck =="
(cd backend && "$PYTHON_BIN" -m mypy app tests)

if [[ "${RUN_DB_SMOKE:-0}" == "1" ]]; then
  echo "== db smoke =="
  "$PYTHON_BIN" scripts/db_smoke_check.py
else
  echo "db smoke skipped; set RUN_DB_SMOKE=1 after 'make db-up'"
fi

echo "verify: ok"
