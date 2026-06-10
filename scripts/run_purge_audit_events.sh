#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "purge_audit_events: running dry-run (validate only, no deletes)"

python scripts/purge_audit_events.py

echo "purge_audit_events: dry-run complete (PASS)"
echo ""
echo "To apply deletions (manual operator action), run:"
echo "  python scripts/purge_audit_events.py --apply"
echo "  python scripts/purge_audit_events.py --apply --retention-days 90"
