from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import yaml

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "config/data_retention.yaml",
    "docs/runbooks/data_retention.md",
    "scripts/data_retention_check.py",
    "scripts/run_data_retention_check.ps1",
    "scripts/run_data_retention_check.sh",
    "scripts/purge_audit_events.py",
    "scripts/run_purge_audit_events.ps1",
    "scripts/run_purge_audit_events.sh",
)
REQUIRED_FIELDS = {"id", "description", "retention_period", "deletion_approach", "blocker"}
REQUIRED_IDS = {"report_runs", "evidence_observations", "audit_events", "source_ingest_runs"}
REQUIRED_PURGE_REFERENCES = (
    "scripts/purge_audit_events.py",
    ".\\scripts\\run_purge_audit_events.ps1",
    "py -3.12 scripts/purge_audit_events.py --apply",
)
REQUIRED_RUNBOOK_PHRASES = (
    "scripts/data_retention_check.py",
    "scripts/purge_audit_events.py",
    ".\\scripts\\run_purge_audit_events.ps1",
    "py -3.12 scripts/purge_audit_events.py --apply",
    "No automated deletion procedures are implemented",
    "manual operator action",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def read_text(path_text: str) -> str:
    return (ROOT / path_text).read_text(encoding="utf-8")


def validate_required_files() -> None:
    for path_text in REQUIRED_FILES:
        require((ROOT / path_text).is_file(), f"{path_text} not found")


def load_catalog() -> dict[str, Any]:
    catalog = yaml.safe_load(read_text("config/data_retention.yaml"))
    require(isinstance(catalog, dict), "data_retention.yaml must be a mapping")
    return cast(dict[str, Any], catalog)


def validate_runbook() -> None:
    runbook = read_text("docs/runbooks/data_retention.md")
    for expected in REQUIRED_PURGE_REFERENCES:
        require(
            expected in runbook,
            f"data retention runbook missing expected purge reference: {expected}",
        )
    for phrase in REQUIRED_RUNBOOK_PHRASES:
        require(phrase in runbook, f"data retention runbook missing phrase: {phrase}")


def validate_catalog(catalog: dict[str, Any]) -> None:
    require(catalog.get("schema_version") == "data_retention_v1", "unexpected schema_version")
    require(
        catalog.get("operator_runbook") == "docs/runbooks/data_retention.md",
        "operator_runbook mismatch",
    )

    classes = catalog.get("retention_classes")
    if not isinstance(classes, list) or len(classes) < 6:
        raise SystemExit("retention_classes must be a list with at least 6 items")

    ids_seen: set[str] = set()
    for cls in classes:
        require(isinstance(cls, dict), "each retention class must be a mapping")
        cls = cast(dict[str, Any], cls)
        missing = REQUIRED_FIELDS - set(cls.keys())
        require(
            not missing,
            f"retention class missing fields: {sorted(missing)} in {cls.get('id', '?')}",
        )
        cls_id = cls["id"]
        require(
            isinstance(cls_id, str) and bool(cls_id),
            f"retention class id invalid: {cls_id}",
        )
        require(cls_id not in ids_seen, f"duplicate retention class id: {cls_id}")
        ids_seen.add(cls_id)

    missing_ids = REQUIRED_IDS - ids_seen
    require(not missing_ids, f"retention_classes missing required ids: {sorted(missing_ids)}")

    blockers = catalog.get("retention_blockers")
    if not isinstance(blockers, list) or not blockers:
        raise SystemExit("retention_blockers must be a non-empty list")
    for blocker in blockers:
        require(isinstance(blocker, dict), "each retention blocker must be a mapping")
        blocker = cast(dict[str, Any], blocker)
        require(
            "id" in blocker and "status" in blocker and "reason" in blocker,
            f"blocker missing fields: {blocker}",
        )
        require(blocker["status"] == "blocked", f"blocker {blocker['id']} must have status=blocked")


def main() -> int:
    validate_required_files()
    catalog = load_catalog()
    print("config/data_retention.yaml: parseable")
    print("docs/runbooks/data_retention.md: exists")
    validate_runbook()
    print("audit purge tooling: exists and documented")
    validate_catalog(catalog)
    print("retention catalog validation: ok")
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
