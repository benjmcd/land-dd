#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python}"

if [[ ! -f "./scripts/bologna_source_candidates_check.py" ]]; then
  echo "required Bologna source-candidates artifact missing: scripts/bologna_source_candidates_check.py" >&2
  exit 1
fi

"$PYTHON_BIN" ./scripts/bologna_source_candidates_check.py
echo "Bologna source candidates check: ok"
