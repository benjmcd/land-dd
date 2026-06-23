#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
python scripts/bologna_odp1_owner_response_gate_check.py
echo "Bologna ODP-BOL-001 owner response gate check: ok"
