#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f "./scripts/readiness_matrix_check.py" ]]; then
  echo "required readiness-matrix artifact missing: scripts/readiness_matrix_check.py" >&2
  exit 1
fi

PYTHON_BIN="${PYTHON_BIN:-python}"
"$PYTHON_BIN" ./scripts/readiness_matrix_check.py

echo "readiness matrix check: ok"
