#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python}"

echo "== bootstrap =="
"$PYTHON_BIN" - <<'PY'
import sys

if sys.version_info < (3, 12):
    raise SystemExit(
        f"Python 3.12+ is required; found {sys.version.split()[0]}"
    )
print(f"python: {sys.version.split()[0]}")
PY

echo "== install backend dev dependencies =="
"$PYTHON_BIN" -m pip install -e "backend[dev]"

mkdir -p local_artifacts/object_store

echo "bootstrap: ok"
echo "Next: ./scripts/verify.sh"
echo "Run in-memory API: ./scripts/run_api.sh --memory"
echo "Run Postgres API after db-up/migrate: ./scripts/run_api.sh --postgres"
