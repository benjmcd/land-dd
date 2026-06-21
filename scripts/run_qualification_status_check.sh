#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f "./scripts/qualification_status_check.py" ]]; then
  echo "required qualification artifact missing: scripts/qualification_status_check.py" >&2
  exit 1
fi

PYTHON_BIN="${PYTHON_BIN:-python}"
"$PYTHON_BIN" ./scripts/qualification_status_check.py --root . --python-command "$PYTHON_BIN" "$@"

echo "qualification status check: wrapper ok"
