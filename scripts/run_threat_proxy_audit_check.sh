#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f "./scripts/threat_proxy_audit_check.py" ]]; then
  echo "required threat/proxy artifact missing: scripts/threat_proxy_audit_check.py" >&2
  exit 1
fi

PYTHON_BIN="${PYTHON_BIN:-python}"
"$PYTHON_BIN" ./scripts/threat_proxy_audit_check.py

echo "threat/proxy audit check: ok"
