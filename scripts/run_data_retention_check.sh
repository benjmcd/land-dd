#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f "./scripts/data_retention_check.py" ]]; then
  echo "required data-retention artifact missing: scripts/data_retention_check.py" >&2
  exit 1
fi

PYTHON_BIN="${PYTHON_BIN:-python}"
"$PYTHON_BIN" ./scripts/data_retention_check.py
