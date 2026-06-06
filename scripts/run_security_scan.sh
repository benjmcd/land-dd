#!/usr/bin/env bash
# Run bandit static security analysis on backend/app.
#
# Usage:
#   ./scripts/run_security_scan.sh              # full scan
#   ./scripts/run_security_scan.sh --validate-only  # check bandit is importable

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BACKEND_DIR="${REPO_ROOT}/backend"

if [[ "${1:-}" == "--validate-only" ]]; then
    python -c "import bandit" 2>&1
    echo "bandit importable: OK"
    exit 0
fi

echo "Running bandit on backend/app (severity threshold: medium+) ..."
BANDIT_OUTPUT="$(cd "${BACKEND_DIR}" && python -m bandit -r app -ll -q 2>&1 || true)"
echo "${BANDIT_OUTPUT}"

if echo "${BANDIT_OUTPUT}" | grep -qE "Severity:[[:space:]]+(High|Critical)"; then
    echo ""
    echo "Security scan FAILED: HIGH or CRITICAL severity issues found."
    echo "Review the output above and either fix the code or add '# nosec <BXXX> # justification' comments for confirmed false positives."
    exit 1
fi

echo ""
echo "Security scan PASSED: no HIGH or CRITICAL issues found."
exit 0
