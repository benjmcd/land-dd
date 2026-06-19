from __future__ import annotations

import contextlib
import importlib.util
import io
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
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
REQUIRED_AUTOMATION_TARGET_CLASSES = {"audit_events", "api_key_audit_events"}
REQUIRED_AUTOMATION_EVENT_TYPES = {"api_key_auth", "created", "superseded"}
REQUIRED_AUTOMATION_APPLY_GATES = {
    "--apply",
    "backup_or_export",
    "security_reviewer_approval",
    "state_worklog_entry",
}
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
    "repo-local audit retention schedule contract",
    "hosted scheduler is not provisioned",
    "manual operator action",
    "The default retention window is",
    "read from that catalog",
    "fails closed",
    "`--retention-days`",
    "operator override",
    "Every purge validates `config/data_retention.yaml`",
    "after the catalog has validated",
)
DISALLOWED_RUNBOOK_PHRASES = (
    "falls back to 90 days if the YAML is unreadable",
    "fallback if YAML is absent or unparseable",
)
DISALLOWED_PURGE_SCRIPT_FALLBACK_SNIPPETS = (
    "_DEFAULT_RETENTION_DAYS = 90  # fallback",
    "pass  # keep the hard-coded default",
    "fallback if YAML is absent or unparseable",
)
REQUIRED_PURGE_SCRIPT_FAIL_CLOSED_SNIPPETS = (
    "_resolve_default_retention_days",
    "RetentionCatalogError",
    "default=None",
    "fails closed if invalid",
)
RETENTION_PERIOD_SUFFIX = "_days_target"


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
    for phrase in DISALLOWED_RUNBOOK_PHRASES:
        require(
            phrase not in runbook,
            f"data retention runbook preserves obsolete fallback claim: {phrase}",
        )


def validate_purge_default_retention_semantics() -> None:
    purge_script = read_text("scripts/purge_audit_events.py")
    for snippet in DISALLOWED_PURGE_SCRIPT_FALLBACK_SNIPPETS:
        require(
            snippet not in purge_script,
            "purge script must fail closed when catalog retention cannot be read; "
            f"remove obsolete fallback snippet: {snippet}",
        )
    require(
        "--retention-days" in purge_script,
        "purge script must preserve explicit --retention-days override",
    )
    require(
        "config/data_retention.yaml" in purge_script,
        "purge script default retention must be catalog-derived",
    )
    for snippet in REQUIRED_PURGE_SCRIPT_FAIL_CLOSED_SNIPPETS:
        require(
            snippet in purge_script,
            f"purge script missing fail-closed catalog-default marker: {snippet}",
        )


def load_purge_module() -> ModuleType:
    script_path = ROOT / "scripts" / "purge_audit_events.py"
    spec = importlib.util.spec_from_file_location("purge_audit_events_check", script_path)
    if spec is None or spec.loader is None:
        raise SystemExit("unable to load purge script")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_days_target(class_id: str, retention_period: Any) -> int:
    require(
        isinstance(retention_period, str)
        and retention_period.endswith(RETENTION_PERIOD_SUFFIX),
        f"{class_id} retention_period must end with {RETENTION_PERIOD_SUFFIX}",
    )
    days_text = retention_period[: -len(RETENTION_PERIOD_SUFFIX)]
    require(days_text.isdigit() and int(days_text) > 0, f"{class_id} days target invalid")
    return int(days_text)


def expected_audit_retention_days(catalog: dict[str, Any]) -> int:
    classes = catalog.get("retention_classes")
    if not isinstance(classes, list):
        raise SystemExit("retention_classes must be a list")
    classes_by_id: dict[str, dict[str, Any]] = {}
    for cls in classes:
        if not isinstance(cls, dict):
            continue
        cls = cast(dict[str, Any], cls)
        class_id = cls.get("id")
        if isinstance(class_id, str):
            classes_by_id[class_id] = cls
    missing_classes = REQUIRED_AUTOMATION_TARGET_CLASSES - set(classes_by_id)
    require(
        not missing_classes,
        f"retention_classes missing audit purge targets: {sorted(missing_classes)}",
    )
    resolved_days = {
        parse_days_target(class_id, classes_by_id[class_id].get("retention_period"))
        for class_id in REQUIRED_AUTOMATION_TARGET_CLASSES
    }
    require(
        len(resolved_days) == 1,
        "audit retention classes must share one positive days_target retention_period",
    )
    return resolved_days.pop()


def validate_purge_runtime_contract(catalog: dict[str, Any]) -> None:
    module = load_purge_module()
    resolver_attr = getattr(module, "_resolve_default_retention_days", None)
    require(callable(resolver_attr), "purge script must expose default retention resolver")
    default_resolver = cast(Callable[..., int], resolver_attr)
    require(
        default_resolver() == expected_audit_retention_days(catalog),
        "purge script default retention days must match the retention catalog",
    )

    in_scope_event_types = getattr(module, "IN_SCOPE_EVENT_TYPES", None)
    require(
        set(in_scope_event_types or []) == REQUIRED_AUTOMATION_EVENT_TYPES,
        "purge script event allowlist must match automation target event types",
    )

    missing_catalog = ROOT / "config" / "__missing_data_retention.yaml"
    require(
        not missing_catalog.exists(),
        "unexpected missing-catalog sentinel exists in config/",
    )
    try:
        default_resolver(missing_catalog)
    except Exception as exc:  # noqa: BLE001 - validator checks fail-closed exception shape.
        require(
            exc.__class__.__name__ == "RetentionCatalogError",
            "missing retention catalog must raise RetentionCatalogError",
        )
        require(
            "unable to read" in str(exc),
            "missing retention catalog error must explain read failure",
        )
    else:
        raise SystemExit("missing retention catalog must fail closed")

    original_config_path = getattr(module, "_CONFIG_PATH", None)
    original_run_purge = getattr(module, "run_purge", None)

    def forbidden_run_purge(**_: Any) -> None:
        raise AssertionError("run_purge executed despite missing catalog")

    try:
        module.__dict__["_CONFIG_PATH"] = missing_catalog
        module.__dict__["run_purge"] = forbidden_run_purge
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                module.main(
                    [
                        "--retention-days",
                        "30",
                        "--apply",
                        "--db-url",
                        "postgresql://example/db",
                    ]
                )
        except SystemExit as exc:
            require(
                exc.code == 1,
                "explicit --retention-days with missing catalog must exit 1",
            )
        except AssertionError as exc:
            raise SystemExit(
                "explicit --retention-days must not bypass retention catalog validation"
            ) from exc
        else:
            raise SystemExit(
                "explicit --retention-days must fail closed when catalog is missing"
            )
    finally:
        module.__dict__["_CONFIG_PATH"] = original_config_path
        module.__dict__["run_purge"] = original_run_purge


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

    validate_automation_plan(catalog)

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


def validate_automation_plan(catalog: dict[str, Any]) -> None:
    plan = catalog.get("automation_plan")
    require(isinstance(plan, dict), "automation_plan must be a mapping")
    plan = cast(dict[str, Any], plan)
    require(
        plan.get("status") == "repo_local_schedule_contract",
        "automation_plan status must be repo_local_schedule_contract",
    )
    require(plan.get("runner") == "scripts/purge_audit_events.py", "automation runner mismatch")
    require(
        plan.get("windows_dry_run_wrapper") == "scripts/run_purge_audit_events.ps1",
        "automation Windows wrapper mismatch",
    )
    require(
        plan.get("posix_dry_run_wrapper") == "scripts/run_purge_audit_events.sh",
        "automation POSIX wrapper mismatch",
    )
    for path_text in (
        plan["runner"],
        plan["windows_dry_run_wrapper"],
        plan["posix_dry_run_wrapper"],
    ):
        require((ROOT / path_text).is_file(), f"automation artifact missing: {path_text}")
    require(plan.get("cadence") == "weekly", "automation cadence must be weekly")
    require(plan.get("mode") == "dry_run_by_default", "automation mode must be dry_run_by_default")
    require(
        set(plan.get("target_retention_classes", [])) == REQUIRED_AUTOMATION_TARGET_CLASSES,
        "automation target retention classes mismatch",
    )
    require(
        set(plan.get("target_event_types", [])) == REQUIRED_AUTOMATION_EVENT_TYPES,
        "automation target event types mismatch",
    )
    require(
        REQUIRED_AUTOMATION_APPLY_GATES.issubset(set(plan.get("apply_requires", []))),
        "automation apply gates missing required entries",
    )
    require(
        plan.get("hosted_scheduler_status") == "blocked",
        "hosted scheduler status must remain blocked until provisioned",
    )
    limits = plan.get("limits")
    require(isinstance(limits, dict), "automation_plan limits must be a mapping")
    limits = cast(dict[str, Any], limits)
    require(limits.get("validate_only_catalog") is True, "automation catalog must be validate-only")
    require(limits.get("deletes_by_default") is False, "automation must not delete by default")
    require(
        limits.get("requires_explicit_apply") is True,
        "automation must require explicit --apply",
    )
    require(limits.get("writes_secrets") is False, "automation must not write secrets")


def main() -> int:
    validate_required_files()
    catalog = load_catalog()
    print("config/data_retention.yaml: parseable")
    print("docs/runbooks/data_retention.md: exists")
    validate_runbook()
    validate_purge_default_retention_semantics()
    validate_purge_runtime_contract(catalog)
    print("audit purge tooling: exists and documented")
    validate_catalog(catalog)
    print("retention catalog validation: ok")
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
