from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

EXPECTED_ALERT_SCHEMA = "ops_alert_rules_v1"
EXPECTED_RETENTION_SCHEMA = "data_retention_v1"
EXPECTED_COST_SCHEMA = "ops_cost_monitoring_v1"
EXPECTED_INCIDENT_RUNBOOK = "docs/runbooks/incident_response.md"
EXPECTED_ALERTING_RUNBOOK = "docs/runbooks/alerting.md"
EXPECTED_BACKUP_RESTORE_RUNBOOK = "docs/runbooks/backup_restore.md"
EXPECTED_DATA_RETENTION_RUNBOOK = "docs/runbooks/data_retention.md"
EXPECTED_COST_RUNBOOK = "docs/runbooks/cost_monitoring.md"
EXPECTED_REPORT_COST_AUTHORITY = "schemas/report_run_schema.json"
EXPECTED_PLANNING_COST_INPUTS = "docs/planning_pack/registers/cost_model_inputs.csv"
EXPECTED_RECOVERY_PREVIEW_PATH = "/operations/recovery-preview"
EXPECTED_VALIDATION_COMMANDS = (
    "scripts/run_alert_rules_check.ps1",
    "scripts/run_incident_rollback_check.ps1",
    "scripts/run_backup_restore_check.ps1",
    "scripts/run_data_retention_check.ps1",
    "scripts/run_cost_monitoring_check.ps1",
)
ALLOWED_SEVERITIES = {"SEV0", "SEV1", "SEV2", "SEV3"}
REQUIRED_ALERT_RULE_IDS = {
    "safety_contract_check_failed",
    "api_health_down",
    "deployment_smoke_failed",
    "db_smoke_failed",
    "backup_restore_failed",
    "metrics_endpoint_down",
    "report_queue_backlog_high",
    "report_running_stale",
    "report_failures_high",
    "live_connector_queue_backlog_high",
    "live_connector_running_stale",
    "live_connector_failures_high",
    "source_readiness_ready_drop",
    "source_registry_last_checked_stale",
    "cost_monitoring_check_failed",
}
REQUIRED_ALERT_FIELDS = {
    "id",
    "severity",
    "signal",
    "condition",
    "window",
    "owner",
    "escalation",
    "runbook",
    "validation",
}
REQUIRED_RETENTION_CLASSES = {
    "report_runs",
    "evidence_observations",
    "audit_events",
    "api_key_audit_events",
    "connector_review_queue",
    "job_queue_report_jobs",
    "source_ingest_runs",
}
REQUIRED_RETENTION_LIMITS = {
    "validate_only_catalog": True,
    "deletes_by_default": False,
    "requires_explicit_apply": True,
    "writes_secrets": False,
}
REQUIRED_COST_CATEGORIES = {
    "compute",
    "storage",
    "llm",
    "maps",
    "geocoding",
    "data_vendors",
}
BLOCKED_OR_DISABLED_COST_STATUSES = {
    "disabled_until_metered",
    "blocked_until_reviewed",
}
REQUIRED_STATIC_FILES = (
    EXPECTED_ALERTING_RUNBOOK,
    EXPECTED_INCIDENT_RUNBOOK,
    EXPECTED_BACKUP_RESTORE_RUNBOOK,
    EXPECTED_DATA_RETENTION_RUNBOOK,
    EXPECTED_COST_RUNBOOK,
    "backend/app/api/operations.py",
    "backend/app/api/ui_operations.py",
    "backend/app/operations/recovery_preview.py",
    "scripts/alert_rules_check.py",
    "scripts/incident_rollback_check.py",
    "scripts/data_retention_check.py",
    "scripts/cost_monitoring_check.py",
    *EXPECTED_VALIDATION_COMMANDS,
)
INCIDENT_REQUIRED_PHRASES = (
    "## Severity Levels",
    "## Ownership",
    "## Escalation",
    "## Rollback and Mitigation",
    "## Recovery Criteria",
    "Deployment Rollback",
    "Database Rollback or Migration Mitigation",
    "Connector or Source Outage",
    "Queue or Report Failure",
)
ALERTING_REQUIRED_PHRASES = (
    "/operations/queue-health",
    EXPECTED_RECOVERY_PREVIEW_PATH,
    "dashboards",
    "alert routing",
    "pager",
)


class OperationsGuardrailsError(RuntimeError):
    """Raised when operations guardrail artifacts cannot be trusted for rendering."""


@dataclass(frozen=True)
class AlertRule:
    rule_id: str
    severity: str
    signal_kind: str
    signal_target: str
    proof: str
    runbook: str


@dataclass(frozen=True)
class RetentionClass:
    class_id: str
    retention_period: str
    deletion_approach: str
    blocker: str


@dataclass(frozen=True)
class CostCategory:
    category_id: str
    status: str
    meter: str
    validation: str


@dataclass(frozen=True)
class OperationsGuardrailsReadiness:
    alert_schema_version: str
    alert_rules: tuple[AlertRule, ...]
    alert_severity_counts: dict[str, int]
    queue_signal_targets: tuple[str, ...]
    recovery_preview_path: str
    incident_runbook: str
    backup_restore_runbook: str
    validation_commands: tuple[str, ...]
    retention_schema_version: str
    retention_classes: tuple[RetentionClass, ...]
    retention_automation_status: str
    retention_automation_mode: str
    hosted_scheduler_status: str
    retention_limits: dict[str, bool]
    retention_blocker_ids: tuple[str, ...]
    cost_schema_version: str
    cost_categories: tuple[CostCategory, ...]
    cost_blocked_or_disabled_ids: tuple[str, ...]
    report_cost_metrics_authority: str
    planning_cost_inputs: str

    @property
    def alert_rule_ids(self) -> tuple[str, ...]:
        return tuple(rule.rule_id for rule in self.alert_rules)

    @property
    def retention_class_ids(self) -> tuple[str, ...]:
        return tuple(retention_class.class_id for retention_class in self.retention_classes)

    @property
    def cost_category_ids(self) -> tuple[str, ...]:
        return tuple(category.category_id for category in self.cost_categories)


def repo_root_from_app() -> Path:
    return Path(__file__).resolve().parents[2]


def load_operations_guardrails(
    repo_root: Path | None = None,
) -> OperationsGuardrailsReadiness:
    root = repo_root or repo_root_from_app()
    alert_catalog = _read_yaml(root / "config" / "ops_alert_rules.yaml")
    retention_catalog = _read_yaml(root / "config" / "data_retention.yaml")
    cost_catalog = _read_yaml(root / "config" / "ops_cost_monitoring.yaml")
    return parse_operations_guardrails(
        alert_catalog,
        retention_catalog,
        cost_catalog,
        root=root,
    )


def parse_operations_guardrails(
    alert_catalog: dict[str, Any],
    retention_catalog: dict[str, Any],
    cost_catalog: dict[str, Any],
    *,
    root: Path,
) -> OperationsGuardrailsReadiness:
    for path_text in REQUIRED_STATIC_FILES:
        _require_existing(root, path_text)
    _validate_runbook_text(root)

    alert_schema, alert_rules, queue_targets = _parse_alert_catalog(alert_catalog, root)
    retention = _parse_retention_catalog(retention_catalog, root)
    cost = _parse_cost_catalog(cost_catalog, root)

    severity_counts = Counter(rule.severity for rule in alert_rules)
    return OperationsGuardrailsReadiness(
        alert_schema_version=alert_schema,
        alert_rules=alert_rules,
        alert_severity_counts={
            severity: severity_counts.get(severity, 0)
            for severity in sorted(ALLOWED_SEVERITIES)
        },
        queue_signal_targets=queue_targets,
        recovery_preview_path=EXPECTED_RECOVERY_PREVIEW_PATH,
        incident_runbook=EXPECTED_INCIDENT_RUNBOOK,
        backup_restore_runbook=EXPECTED_BACKUP_RESTORE_RUNBOOK,
        validation_commands=EXPECTED_VALIDATION_COMMANDS,
        retention_schema_version=retention["schema_version"],
        retention_classes=retention["classes"],
        retention_automation_status=retention["automation_status"],
        retention_automation_mode=retention["automation_mode"],
        hosted_scheduler_status=retention["hosted_scheduler_status"],
        retention_limits=retention["limits"],
        retention_blocker_ids=retention["blocker_ids"],
        cost_schema_version=cost["schema_version"],
        cost_categories=cost["categories"],
        cost_blocked_or_disabled_ids=cost["blocked_or_disabled_ids"],
        report_cost_metrics_authority=cost["report_cost_metrics_authority"],
        planning_cost_inputs=cost["planning_cost_inputs"],
    )


def _parse_alert_catalog(
    payload: dict[str, Any],
    root: Path,
) -> tuple[str, tuple[AlertRule, ...], tuple[str, ...]]:
    schema = _require_exact_text(
        payload.get("schema_version"),
        EXPECTED_ALERT_SCHEMA,
        "alert schema",
    )
    incident_runbook = _require_exact_text(
        payload.get("incident_runbook"),
        EXPECTED_INCIDENT_RUNBOOK,
        "incident runbook",
    )
    _require_existing(root, incident_runbook)

    rules: list[AlertRule] = []
    queue_targets: set[str] = set()
    for item in _require_list(payload.get("rules"), "alert rules missing"):
        rule = _require_mapping(item, "alert rule must be a mapping")
        missing = REQUIRED_ALERT_FIELDS - set(rule)
        if missing:
            raise OperationsGuardrailsError(
                f"alert rule missing fields: {sorted(missing)}"
            )
        rule_id = _require_text(rule.get("id"), "alert rule id missing")
        severity = _require_text(rule.get("severity"), f"{rule_id} severity missing")
        if severity not in ALLOWED_SEVERITIES:
            raise OperationsGuardrailsError(f"{rule_id} invalid severity")
        signal = _require_mapping(rule.get("signal"), f"{rule_id} signal missing")
        signal_kind = _require_text(
            signal.get("kind"),
            f"{rule_id} signal kind missing",
        )
        signal_target = _require_text(
            signal.get("target"),
            f"{rule_id} signal target missing",
        )
        target_path = signal_target.split()[0]
        if target_path.startswith("/operations/"):
            queue_targets.add(target_path)
        validation = _require_mapping(
            rule.get("validation"),
            f"{rule_id} validation missing",
        )
        proof = _require_text(validation.get("proof"), f"{rule_id} proof missing")
        _require_existing_if_repo_path(root, proof)
        runbook = _require_text(rule.get("runbook"), f"{rule_id} runbook missing")
        if not runbook.startswith("docs/runbooks/"):
            raise OperationsGuardrailsError(f"{rule_id} runbook invalid")
        _require_existing(root, runbook)
        rules.append(
            AlertRule(
                rule_id=rule_id,
                severity=severity,
                signal_kind=signal_kind,
                signal_target=signal_target,
                proof=proof,
                runbook=runbook,
            )
        )

    rule_ids = {rule.rule_id for rule in rules}
    missing_rules = sorted(REQUIRED_ALERT_RULE_IDS - rule_ids)
    if missing_rules:
        raise OperationsGuardrailsError(f"required alert rules missing: {missing_rules}")
    if "/operations/queue-health" not in queue_targets:
        raise OperationsGuardrailsError("operations queue-health alert signal missing")
    return schema, tuple(sorted(rules, key=lambda rule: rule.rule_id)), tuple(sorted(queue_targets))


def _parse_retention_catalog(
    payload: dict[str, Any],
    root: Path,
) -> dict[str, Any]:
    schema = _require_exact_text(
        payload.get("schema_version"),
        EXPECTED_RETENTION_SCHEMA,
        "retention schema",
    )
    operator_runbook = _require_exact_text(
        payload.get("operator_runbook"),
        EXPECTED_DATA_RETENTION_RUNBOOK,
        "retention runbook",
    )
    _require_existing(root, operator_runbook)

    classes: list[RetentionClass] = []
    for item in _require_list(payload.get("retention_classes"), "retention classes missing"):
        retention_class = _require_mapping(item, "retention class must be a mapping")
        class_id = _require_text(retention_class.get("id"), "retention class id missing")
        purge_script = retention_class.get("purge_script")
        if isinstance(purge_script, str) and purge_script:
            _require_existing(root, purge_script)
        classes.append(
            RetentionClass(
                class_id=class_id,
                retention_period=_require_text(
                    retention_class.get("retention_period"),
                    f"{class_id} retention period missing",
                ),
                deletion_approach=_require_text(
                    retention_class.get("deletion_approach"),
                    f"{class_id} deletion approach missing",
                ),
                blocker=_require_text(
                    retention_class.get("blocker"),
                    f"{class_id} blocker missing",
                ),
            )
        )

    class_ids = {retention_class.class_id for retention_class in classes}
    missing_classes = sorted(REQUIRED_RETENTION_CLASSES - class_ids)
    if missing_classes:
        raise OperationsGuardrailsError(
            f"retention classes missing required ids: {missing_classes}"
        )

    automation = _require_mapping(
        payload.get("automation_plan"),
        "retention automation plan missing",
    )
    automation_status = _require_exact_text(
        automation.get("status"),
        "repo_local_schedule_contract",
        "retention automation status",
    )
    automation_mode = _require_exact_text(
        automation.get("mode"),
        "dry_run_by_default",
        "retention automation mode",
    )
    hosted_scheduler_status = _require_exact_text(
        automation.get("hosted_scheduler_status"),
        "blocked",
        "hosted scheduler status",
    )
    for path_text in (
        automation.get("runner"),
        automation.get("windows_dry_run_wrapper"),
        automation.get("posix_dry_run_wrapper"),
    ):
        _require_existing(root, _require_text(path_text, "automation path missing"))

    limits = _bool_mapping(automation.get("limits"), "retention limits missing")
    for key, expected in REQUIRED_RETENTION_LIMITS.items():
        if limits.get(key) is not expected:
            raise OperationsGuardrailsError(f"retention limit changed: {key}")

    blocker_ids: list[str] = []
    for item in _require_list(payload.get("retention_blockers"), "retention blockers missing"):
        blocker = _require_mapping(item, "retention blocker must be a mapping")
        blocker_id = _require_text(blocker.get("id"), "retention blocker id missing")
        status = _require_exact_text(
            blocker.get("status"),
            "blocked",
            f"{blocker_id} retention blocker status",
        )
        if status != "blocked":
            raise OperationsGuardrailsError("retention blocker must remain blocked")
        blocker_ids.append(blocker_id)

    return {
        "schema_version": schema,
        "classes": tuple(sorted(classes, key=lambda item: item.class_id)),
        "automation_status": automation_status,
        "automation_mode": automation_mode,
        "hosted_scheduler_status": hosted_scheduler_status,
        "limits": limits,
        "blocker_ids": tuple(sorted(blocker_ids)),
    }


def _parse_cost_catalog(payload: dict[str, Any], root: Path) -> dict[str, Any]:
    schema = _require_exact_text(
        payload.get("schema_version"),
        EXPECTED_COST_SCHEMA,
        "cost schema",
    )
    _require_exact_text(
        payload.get("incident_runbook"),
        EXPECTED_INCIDENT_RUNBOOK,
        "cost incident runbook",
    )
    _require_exact_text(
        payload.get("operator_runbook"),
        EXPECTED_COST_RUNBOOK,
        "cost runbook",
    )
    report_cost_metrics = _require_exact_text(
        payload.get("report_cost_metrics_authority"),
        EXPECTED_REPORT_COST_AUTHORITY,
        "report cost metrics authority",
    )
    planning_cost_inputs = _require_exact_text(
        payload.get("planning_cost_inputs"),
        EXPECTED_PLANNING_COST_INPUTS,
        "planning cost inputs",
    )
    _require_existing(root, report_cost_metrics)
    _require_existing(root, planning_cost_inputs)

    categories: list[CostCategory] = []
    blocked_or_disabled_ids: list[str] = []
    for item in _require_list(payload.get("categories"), "cost categories missing"):
        category = _require_mapping(item, "cost category must be a mapping")
        category_id = _require_text(category.get("id"), "cost category id missing")
        status = _require_text(category.get("status"), f"{category_id} status missing")
        source_paths = _require_text_tuple(
            category.get("source_of_truth"),
            f"{category_id} source_of_truth missing",
        )
        for path_text in source_paths:
            _require_existing_if_repo_path(root, path_text)
        validation = _require_exact_text(
            category.get("validation"),
            "scripts/run_cost_monitoring_check.ps1",
            f"{category_id} validation",
        )
        _require_existing(root, validation)
        if status in BLOCKED_OR_DISABLED_COST_STATUSES:
            blocked_or_disabled_ids.append(category_id)
        categories.append(
            CostCategory(
                category_id=category_id,
                status=status,
                meter=_require_text(category.get("meter"), f"{category_id} meter missing"),
                validation=validation,
            )
        )

    category_ids = {category.category_id for category in categories}
    missing_categories = sorted(REQUIRED_COST_CATEGORIES - category_ids)
    if missing_categories:
        raise OperationsGuardrailsError(
            f"cost categories missing required ids: {missing_categories}"
        )
    return {
        "schema_version": schema,
        "categories": tuple(sorted(categories, key=lambda category: category.category_id)),
        "blocked_or_disabled_ids": tuple(sorted(blocked_or_disabled_ids)),
        "report_cost_metrics_authority": report_cost_metrics,
        "planning_cost_inputs": planning_cost_inputs,
    }


def _validate_runbook_text(root: Path) -> None:
    incident = _read_text(root, EXPECTED_INCIDENT_RUNBOOK)
    for phrase in INCIDENT_REQUIRED_PHRASES:
        if phrase not in incident:
            raise OperationsGuardrailsError(
                f"incident response runbook missing phrase: {phrase}"
            )
    alerting = _read_text(root, EXPECTED_ALERTING_RUNBOOK)
    for phrase in ALERTING_REQUIRED_PHRASES:
        if phrase not in alerting:
            raise OperationsGuardrailsError(f"alerting runbook missing phrase: {phrase}")
    backup = _read_text(root, EXPECTED_BACKUP_RESTORE_RUNBOOK)
    if "run_backup_restore_check.ps1" not in backup:
        raise OperationsGuardrailsError("backup/restore runbook missing validator")


def _read_yaml(path: Path) -> dict[str, Any]:
    label = _catalog_label(path)
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise OperationsGuardrailsError(f"cannot read {label}") from exc
    return _require_mapping(payload, f"{label} must be a mapping")


def _read_text(root: Path, path_text: str) -> str:
    path = _resolved_repo_path(root, path_text)
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise OperationsGuardrailsError(f"cannot read {path_text}") from exc


def _require_existing_if_repo_path(root: Path, path_text: str) -> None:
    if path_text.startswith(
        ("backend/", "config/", "docs/", "registers/", "schemas/", "scripts/")
    ):
        _require_existing(root, path_text)


def _require_existing(root: Path, path_text: str) -> None:
    path = _resolved_repo_path(root, path_text)
    if not path.exists():
        raise OperationsGuardrailsError(
            f"referenced operations guardrail artifact missing: {path_text}"
        )


def _resolved_repo_path(root: Path, path_text: str) -> Path:
    if not path_text:
        raise OperationsGuardrailsError("empty path reference")
    candidate = Path(_normalize_path(path_text))
    if candidate.is_absolute():
        raise OperationsGuardrailsError(f"path must be repo-relative: {path_text}")
    root_resolved = root.resolve()
    resolved = (root_resolved / candidate).resolve()
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise OperationsGuardrailsError(f"path escapes repo root: {path_text}") from exc
    return resolved


def _require_mapping(value: Any, message: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise OperationsGuardrailsError(message)
    return value


def _require_list(value: Any, message: str) -> list[Any]:
    if not isinstance(value, list) or not value:
        raise OperationsGuardrailsError(message)
    return value


def _require_text(value: Any, message: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise OperationsGuardrailsError(message)
    return value.strip()


def _require_exact_text(value: Any, expected: str, label: str) -> str:
    text = _require_text(value, f"{label} missing")
    if text != expected:
        raise OperationsGuardrailsError(f"{label} must be {expected}")
    return text


def _require_text_tuple(value: Any, message: str) -> tuple[str, ...]:
    values = _require_list(value, message)
    text_values = tuple(_require_text(item, message) for item in values)
    if not text_values:
        raise OperationsGuardrailsError(message)
    return text_values


def _bool_mapping(value: Any, message: str) -> dict[str, bool]:
    raw = _require_mapping(value, message)
    if not all(isinstance(key, str) and isinstance(val, bool) for key, val in raw.items()):
        raise OperationsGuardrailsError(message)
    return {str(key): bool(val) for key, val in raw.items()}


def _normalize_path(path_text: str) -> str:
    return path_text.replace("\\", "/")


def _catalog_label(path: Path) -> str:
    parts = path.parts
    if len(parts) >= 2:
        return f"{parts[-2]}/{parts[-1]}"
    return path.name
