#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-python}"

# 1. Validate config/data_retention.yaml exists and is parseable
if [[ ! -f "config/data_retention.yaml" ]]; then
  echo "config/data_retention.yaml not found" >&2
  exit 1
fi

"$PYTHON_BIN" -c "import yaml; yaml.safe_load(open('config/data_retention.yaml', encoding='utf-8'))"
echo "config/data_retention.yaml: parseable"

# 2. Validate docs/runbooks/data_retention.md exists
if [[ ! -f "docs/runbooks/data_retention.md" ]]; then
  echo "docs/runbooks/data_retention.md not found" >&2
  exit 1
fi
echo "docs/runbooks/data_retention.md: exists"

# 3. Validate purge tooling exists and is referenced by the runbook
for path in \
  "scripts/purge_audit_events.py" \
  "scripts/run_purge_audit_events.ps1" \
  "scripts/run_purge_audit_events.sh"
do
  if [[ ! -f "$path" ]]; then
    echo "$path not found" >&2
    exit 1
  fi
done

for expected in \
  "scripts/purge_audit_events.py" \
  ".\\scripts\\run_purge_audit_events.ps1" \
  "py -3.12 scripts/purge_audit_events.py --apply"
do
  if ! grep -Fq "$expected" docs/runbooks/data_retention.md; then
    echo "data retention runbook missing expected purge reference: $expected" >&2
    exit 1
  fi
done
echo "audit purge tooling: exists and documented"

# 4. Validate each retention class has required fields
"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path.cwd()
REQUIRED_FIELDS = {"id", "description", "retention_period", "deletion_approach", "blocker"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


catalog = yaml.safe_load((ROOT / "config" / "data_retention.yaml").read_text(encoding="utf-8"))
require(isinstance(catalog, dict), "data_retention.yaml must be a mapping")
require(catalog.get("schema_version") == "data_retention_v1", "unexpected schema_version")
require(catalog.get("operator_runbook") == "docs/runbooks/data_retention.md", "operator_runbook mismatch")
require((ROOT / "scripts" / "purge_audit_events.py").is_file(), "purge_audit_events.py missing")
require((ROOT / "scripts" / "run_purge_audit_events.ps1").is_file(), "run_purge_audit_events.ps1 missing")
require((ROOT / "scripts" / "run_purge_audit_events.sh").is_file(), "run_purge_audit_events.sh missing")

classes = catalog.get("retention_classes")
require(isinstance(classes, list) and len(classes) >= 6, "retention_classes must be a list with at least 6 items")

ids_seen: set[str] = set()
for cls in classes:
    require(isinstance(cls, dict), "each retention class must be a mapping")
    missing = REQUIRED_FIELDS - set(cls.keys())
    require(not missing, f"retention class missing fields: {sorted(missing)} in {cls.get('id', '?')}")
    cls_id = cls["id"]
    require(cls_id not in ids_seen, f"duplicate retention class id: {cls_id}")
    ids_seen.add(cls_id)

REQUIRED_IDS = {"report_runs", "evidence_observations", "audit_events", "source_ingest_runs"}
missing_ids = REQUIRED_IDS - ids_seen
require(not missing_ids, f"retention_classes missing required ids: {sorted(missing_ids)}")

blockers = catalog.get("retention_blockers")
require(isinstance(blockers, list) and blockers, "retention_blockers must be a non-empty list")
for blocker in blockers:
    require(isinstance(blocker, dict), "each retention blocker must be a mapping")
    require("id" in blocker and "status" in blocker and "reason" in blocker, f"blocker missing fields: {blocker}")
    require(blocker["status"] == "blocked", f"blocker {blocker['id']} must have status=blocked")

print("retention catalog validation: ok")
PY

echo "PASS"
exit 0
