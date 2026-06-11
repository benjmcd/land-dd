#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f "./scripts/hosted_deployment_check.py" ]]; then
  echo "required hosted-deployment artifact missing: scripts/hosted_deployment_check.py" >&2
  exit 1
fi

PYTHON_BIN="${PYTHON_BIN:-python}"
"$PYTHON_BIN" ./scripts/hosted_deployment_check.py

echo "hosted deployment check: ok"
