#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
python scripts/bol_scope_auth_check.py
echo "Bologna scope authority readiness check: ok"
