#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
python scripts/bologna_odp4_db_report_proof_response_gate_check.py
echo "Bologna ODP-BOL-004 DB report proof response gate check: ok"
