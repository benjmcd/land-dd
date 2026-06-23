#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
python scripts/bologna_odp1_owner_answer_packet_check.py
echo "Bologna ODP-BOL-001 owner answer packet check: ok"
