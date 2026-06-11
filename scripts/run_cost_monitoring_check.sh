#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f "./scripts/cost_monitoring_check.py" ]]; then
  echo "required cost-monitoring artifact missing: scripts/cost_monitoring_check.py" >&2
  exit 1
fi

PYTHON_BIN="${PYTHON_BIN:-python}"
"$PYTHON_BIN" ./scripts/cost_monitoring_check.py

echo "cost monitoring check: ok"
