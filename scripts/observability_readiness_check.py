from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import yaml

ROOT = Path(__file__).resolve().parents[1]

CONFIG_PATH = "config/observability_readiness.yaml"
EXPECTED_SCHEMA = "observability_readiness_v1"
EXPECTED_SCOPE = "local_release_candidate_observability"
EXPECTED_STATUS = "local_only"
EXPECTED_SIGNAL_IDS = {
    "runtime_metrics",
    "queue_health",
    "recovery_preview",
    "connector_observability",
    "source_failure_evidence",
    "deployment_smoke",
    "alert_rule_catalog",
}
EXPECTED_ALERT_RULE_IDS = {
    "metrics_endpoint_down",
    "report_queue_backlog_high",
    "report_running_stale",
    "live_connector_queue_backlog_high",
    "live_connector_running_stale",
}
EXPECTED_HOSTED_BLOCKERS = {
    "hosted_dashboard",
    "hosted_alert_routing",
    "pager_on_call",
    "hosted_log_retention",
    "production_traffic_observability",
}
EXPECTED_LIMITS = {
    "validate_only": True,
    "creates_hosted_dashboard": False,
    "dispatches_alerts": False,
    "provisions_pager": False,
    "provisions_hosted_log_retention": False,
    "mutates_hosted_infrastructure": False,
    "writes_secrets": False,
    "opens_public_endpoint": False,
    "runs_deployment_smoke": False,
}
EXPECTED_SCHEMA_REFS = {
    "runtime_metrics_v1",
    "operations_queue_health_v1",
    "operations_recovery_preview_v1",
    "connector_observability_events",
    "source_failure_stored",
    "deployment_smoke",
    "ops_alert_rules_v1",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def require_mapping(value: Any, message: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SystemExit(message)
    return cast(dict[str, Any], value)


def require_list(value: Any, message: str) -> list[Any]:
    if not isinstance(value, list) or not value:
        raise SystemExit(message)
    return value


def require_text(value: Any, message: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SystemExit(message)
    return value.strip()


def require_existing(path_text: str) -> None:
    normalized = path_text.replace("\\", "/")
    require(not Path(normalized).is_absolute(), f"path must be repo-relative: {path_text}")
    require(
        (ROOT / normalized).exists(),
        f"referenced observability artifact missing: {normalized}",
    )


def load_catalog() -> dict[str, Any]:
    try:
        payload = yaml.safe_load((ROOT / CONFIG_PATH).read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise SystemExit(f"cannot read {CONFIG_PATH}") from exc
    return require_mapping(payload, "observability readiness catalog must be a mapping")


def validate_catalog(payload: dict[str, Any]) -> None:
    require(payload.get("schema_version") == EXPECTED_SCHEMA, "unexpected schema")
    require(payload.get("scope") == EXPECTED_SCOPE, "unexpected scope")
    require(payload.get("status") == EXPECTED_STATUS, "unexpected status")

    signals = require_list(payload.get("signals"), "signals missing")
    signal_ids: set[str] = set()
    schema_refs: set[str] = set()
    for item in signals:
        signal = require_mapping(item, "signal must be a mapping")
        signal_id = require_text(signal.get("id"), "signal id missing")
        require(signal_id not in signal_ids, f"duplicate signal id: {signal_id}")
        signal_ids.add(signal_id)
        require_text(signal.get("label"), f"{signal_id} label missing")
        require_text(signal.get("surface"), f"{signal_id} surface missing")
        schema_refs.add(require_text(signal.get("schema_ref"), f"{signal_id} schema missing"))
        for path_text in require_list(
            signal.get("source_files"),
            f"{signal_id} source files missing",
        ):
            require_existing(require_text(path_text, f"{signal_id} source path invalid"))
        for path_text in require_list(
            signal.get("validation"),
            f"{signal_id} validation missing",
        ):
            require_existing(require_text(path_text, f"{signal_id} validation path invalid"))
    require(signal_ids == EXPECTED_SIGNAL_IDS, f"signal set mismatch: {sorted(signal_ids)}")
    require(
        EXPECTED_SCHEMA_REFS.issubset(schema_refs),
        f"schema refs missing: {sorted(EXPECTED_SCHEMA_REFS - schema_refs)}",
    )

    alert_rule_ids = {
        require_text(item, "alert rule id invalid")
        for item in require_list(payload.get("alert_rule_ids"), "alert rule ids missing")
    }
    require(
        EXPECTED_ALERT_RULE_IDS.issubset(alert_rule_ids),
        f"alert rule ids missing: {sorted(EXPECTED_ALERT_RULE_IDS - alert_rule_ids)}",
    )

    blockers = require_list(payload.get("hosted_blockers"), "hosted blockers missing")
    blocker_ids: set[str] = set()
    for item in blockers:
        blocker = require_mapping(item, "hosted blocker must be a mapping")
        blocker_id = require_text(blocker.get("id"), "hosted blocker id missing")
        blocker_ids.add(blocker_id)
        require(blocker.get("status") == "blocked", f"{blocker_id} must stay blocked")
        require_existing(require_text(blocker.get("authority"), f"{blocker_id} authority missing"))
    require(
        blocker_ids == EXPECTED_HOSTED_BLOCKERS,
        f"hosted blocker set mismatch: {sorted(blocker_ids)}",
    )

    limits = require_mapping(payload.get("limits"), "limits missing")
    for key, expected in EXPECTED_LIMITS.items():
        require(limits.get(key) is expected, f"limit changed: {key}")

    for command in require_list(
        payload.get("validation_commands"),
        "validation commands missing",
    ):
        command_text = require_text(command, "validation command invalid")
        require_existing(command_text.split()[0])


def validate_cross_catalogs(payload: dict[str, Any]) -> None:
    alert_rules = require_mapping(
        yaml.safe_load((ROOT / "config" / "ops_alert_rules.yaml").read_text(encoding="utf-8")),
        "alert rules catalog missing",
    )
    rule_ids = {
        require_text(rule.get("id"), "alert rule id missing")
        for rule in require_list(alert_rules.get("rules"), "alert rules missing")
        if isinstance(rule, dict)
    }
    expected_rules = {
        require_text(item, "alert rule id invalid")
        for item in require_list(payload.get("alert_rule_ids"), "alert ids missing")
    }
    require(expected_rules.issubset(rule_ids), "observability alert rule not in catalog")

    hosted = require_mapping(
        yaml.safe_load(
            (ROOT / "config" / "hosted_deployment.yaml").read_text(encoding="utf-8"),
        ),
        "hosted deployment catalog missing",
    )
    hosted_blockers = set(require_list(hosted.get("blocked_until"), "hosted blockers missing"))
    require("hosted_alerting_route" in hosted_blockers, "hosted alerting route not blocked")
    limits = require_mapping(hosted.get("limits"), "hosted deployment limits missing")
    require(limits.get("creates_hosted_deployment") is False, "hosted deployment limit drift")
    require(limits.get("opens_public_endpoint") is False, "hosted public endpoint limit drift")

    retention = require_mapping(
        yaml.safe_load((ROOT / "config" / "data_retention.yaml").read_text(encoding="utf-8")),
        "data retention catalog missing",
    )
    retention_blockers = {
        require_text(blocker.get("id"), "retention blocker id missing")
        for blocker in require_list(
            retention.get("retention_blockers"),
            "retention blockers missing",
        )
        if isinstance(blocker, dict)
    }
    require("hosted_log_retention" in retention_blockers, "hosted log retention not blocked")

    metrics_text = (ROOT / "backend" / "app" / "core" / "metrics.py").read_text(
        encoding="utf-8",
    )
    require(
        'METRICS_SCHEMA_VERSION = "runtime_metrics_v1"' in metrics_text,
        "metrics schema drift",
    )
    connector_text = (ROOT / "backend" / "app" / "connectors" / "observability.py").read_text(
        encoding="utf-8",
    )
    for event_type in ("run_started", "run_succeeded", "run_failed", "source_failure_stored"):
        require(event_type in connector_text, f"connector observability missing {event_type}")


def main() -> int:
    payload = load_catalog()
    validate_catalog(payload)
    validate_cross_catalogs(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
