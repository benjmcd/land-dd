#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

PYTHON_BIN="${PYTHON_BIN:-${LAND_DD_PYTHON_EXECUTABLE:-python}}"

"$PYTHON_BIN" scripts/authority_follow_on_sequence_check.py
echo "authority follow-on sequence: ok"
