#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python}"

echo "== workspace structure =="
required=(
  README.md
  MILESTONE_MAP.md
  LANE_OWNERSHIP.md
  docs/ARCHITECTURE.md
  docs/PRODUCT_SPEC.md
  docs/POSTGRES_FIRST_STORAGE.md
  docs/DATA_SOURCE_STRATEGY.md
  docs/IMPLEMENTATION_READINESS.md
  docs/TESTING.md
  state/PROJECT_STATE.md
  state/OPEN_QUESTIONS.md
  state/VALIDATION_LOG.md
  scripts/check_json_files.py
  scripts/check_csv_files.py
  backend/pyproject.toml
  db/migrations/0001_initial_spine.sql
)
for f in "${required[@]}"; do
  [[ -f "$f" ]] || { echo "missing $f" >&2; exit 1; }
done

"$PYTHON_BIN" scripts/check_json_files.py
"$PYTHON_BIN" scripts/check_csv_files.py

echo "workspace validation: ok"
