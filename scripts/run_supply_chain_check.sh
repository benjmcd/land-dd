#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f "./scripts/supply_chain_check.py" ]]; then
  echo "required supply-chain artifact missing: scripts/supply_chain_check.py" >&2
  exit 1
fi

PYTHON_BIN="${PYTHON_BIN:-python}"
"$PYTHON_BIN" ./scripts/supply_chain_check.py

echo "supply-chain check: ok"
