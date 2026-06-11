#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-python}"
"$PYTHON_BIN" - <<'PY'
import sys
if sys.version_info < (3, 12):
    raise SystemExit(
        f"Python 3.12+ is required; found {sys.version.split()[0]}"
    )
PY

echo "purge_audit_events: running dry-run (validate only, no deletes)"

"$PYTHON_BIN" scripts/purge_audit_events.py

echo "purge_audit_events: dry-run complete (PASS)"
echo ""
echo "To apply deletions (manual operator action), run:"
echo "  python scripts/purge_audit_events.py --apply"
echo "  python scripts/purge_audit_events.py --apply --retention-days 90"
