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

make_log_path() {
  local log_dir="$1"
  local log_name="$2"
  local log_path="$log_dir/$log_name"

  if [[ ! -f "$log_path" ]]; then
    printf '%s\n' "$log_path"
    return 0
  fi

  local stem="${log_name%.*}"
  local extension=""
  if [[ "$log_name" == *.* ]]; then
    extension=".${log_name##*.}"
  fi
  local stamp
  stamp="$("$PYTHON_BIN" - <<'PY'
from datetime import UTC, datetime

print(datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ"))
PY
)"
  printf '%s/%s-%s%s\n' "$log_dir" "$stem" "$stamp" "$extension"
}

run_python_with_log() {
  local label="$1"
  local log_name="$2"
  shift 2
  local log_dir="$ROOT_DIR/local_artifacts"

  mkdir -p "$log_dir"
  local log_path
  log_path="$(make_log_path "$log_dir" "$log_name")"
  if "$PYTHON_BIN" "$@" > "$log_path" 2>&1; then
    cat "$log_path"
    echo "$label log: $log_path"
    return 0
  fi

  local status=$?
  cat "$log_path"
  echo "$label log: $log_path"
  return "$status"
}

echo "== agent context =="
./scripts/agent-context-check.sh

echo "== workspace validation =="
PYTHON_BIN="$PYTHON_BIN" ./scripts/validate_workspace.sh

echo "== qualification selftest =="
"$PYTHON_BIN" scripts/selftest_qualification_validator.py

echo "== qualification validation =="
"$PYTHON_BIN" scripts/validate_qualification.py --root . --layout repo

echo "== qualification status =="
"$PYTHON_BIN" scripts/qualification_status_check.py --root . --python-command "$PYTHON_BIN"

echo "== qualification change impact =="
"$PYTHON_BIN" scripts/qualification_change_impact_check.py --root .

echo "== qualification P0 auto evidence =="
"$PYTHON_BIN" scripts/qualification_p0_evidence_check.py --root .

echo "== qualification parameterization backlog =="
"$PYTHON_BIN" scripts/qualification_parameterization_backlog_check.py --root .

echo "== authority evidence intake =="
"$PYTHON_BIN" scripts/authority_evidence_intake_check.py

if [[ "${RUN_DB_SMOKE:-0}" == "1" ]]; then
  echo "== db migration =="
  ./scripts/db_apply_migrations.sh
fi

echo "== backend tests =="
(
  cd backend
  PYTHONPATH=. run_python_with_log "backend tests" "backend-pytest.log" -m pytest -q
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
  echo "== db smoke =="
  "$PYTHON_BIN" scripts/db_smoke_check.py
else
  echo "db smoke skipped; set RUN_DB_SMOKE=1 after 'make db-up'"
fi

echo "verify: ok"
