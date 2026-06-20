from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

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
EXPECTED_HOSTED_BLOCKERS = {
    "hosted_dashboard",
    "hosted_alert_routing",
    "pager_on_call",
    "hosted_log_retention",
    "production_traffic_observability",
}
EXPECTED_ALERT_RULE_IDS = {
    "metrics_endpoint_down",
    "report_queue_backlog_high",
    "report_running_stale",
    "live_connector_queue_backlog_high",
    "live_connector_running_stale",
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


class ObservabilityReadinessError(RuntimeError):
    """Raised when observability readiness artifacts cannot be trusted for rendering."""


@dataclass(frozen=True)
class ObservabilitySignal:
    signal_id: str
    label: str
    surface: str
    schema_ref: str
    source_files: tuple[str, ...]
    validation: tuple[str, ...]


@dataclass(frozen=True)
class HostedObservabilityBlocker:
    blocker_id: str
    status: str
    authority: str


@dataclass(frozen=True)
class ObservabilityReadiness:
    schema_version: str
    scope: str
    status: str
    signals: tuple[ObservabilitySignal, ...]
    alert_rule_ids: tuple[str, ...]
    hosted_blockers: tuple[HostedObservabilityBlocker, ...]
    validation_commands: tuple[str, ...]
    limits: dict[str, bool]

    @property
    def signal_ids(self) -> tuple[str, ...]:
        return tuple(signal.signal_id for signal in self.signals)

    @property
    def schema_refs(self) -> tuple[str, ...]:
        return tuple(signal.schema_ref for signal in self.signals)

    @property
    def hosted_blocker_ids(self) -> tuple[str, ...]:
        return tuple(blocker.blocker_id for blocker in self.hosted_blockers)


def repo_root_from_app() -> Path:
    return Path(__file__).resolve().parents[2]


def load_observability_readiness(
    repo_root: Path | None = None,
) -> ObservabilityReadiness:
    root = repo_root or repo_root_from_app()
    payload = _read_yaml(root / "config" / "observability_readiness.yaml")
    return parse_observability_readiness(payload, root=root)


def parse_observability_readiness(
    payload: dict[str, Any],
    *,
    root: Path,
) -> ObservabilityReadiness:
    schema = _require_exact_text(
        payload.get("schema_version"),
        EXPECTED_SCHEMA,
        "observability schema",
    )
    scope = _require_exact_text(
        payload.get("scope"),
        EXPECTED_SCOPE,
        "observability scope",
    )
    status = _require_exact_text(
        payload.get("status"),
        EXPECTED_STATUS,
        "observability status",
    )
    signals = _parse_signals(payload.get("signals"), root)
    alert_rule_ids = _parse_alert_rule_ids(payload.get("alert_rule_ids"), root)
    blockers = _parse_hosted_blockers(payload.get("hosted_blockers"), root)
    validation_commands = _parse_validation_commands(
        payload.get("validation_commands"),
        root,
    )
    limits = _parse_limits(payload.get("limits"))

    return ObservabilityReadiness(
        schema_version=schema,
        scope=scope,
        status=status,
        signals=signals,
        alert_rule_ids=alert_rule_ids,
        hosted_blockers=blockers,
        validation_commands=validation_commands,
        limits=limits,
    )


def _parse_signals(value: Any, root: Path) -> tuple[ObservabilitySignal, ...]:
    signals: list[ObservabilitySignal] = []
    for item in _require_list(value, "observability signals missing"):
        signal = _require_mapping(item, "observability signal must be a mapping")
        signal_id = _require_text(signal.get("id"), "observability signal id missing")
        source_files = _require_text_tuple(
            signal.get("source_files"),
            f"{signal_id} source files missing",
        )
        validation = _require_text_tuple(
            signal.get("validation"),
            f"{signal_id} validation missing",
        )
        for path_text in (*source_files, *validation):
            _require_existing(root, path_text)
        signals.append(
            ObservabilitySignal(
                signal_id=signal_id,
                label=_require_text(signal.get("label"), f"{signal_id} label missing"),
                surface=_require_text(signal.get("surface"), f"{signal_id} surface missing"),
                schema_ref=_require_text(
                    signal.get("schema_ref"),
                    f"{signal_id} schema ref missing",
                ),
                source_files=source_files,
                validation=validation,
            )
        )
    signal_ids = {signal.signal_id for signal in signals}
    missing = sorted(EXPECTED_SIGNAL_IDS - signal_ids)
    unexpected = sorted(signal_ids - EXPECTED_SIGNAL_IDS)
    if missing or unexpected:
        raise ObservabilityReadinessError(
            f"observability signal set mismatch missing={missing} unexpected={unexpected}"
        )
    schema_refs = {signal.schema_ref for signal in signals}
    if schema_refs != EXPECTED_SCHEMA_REFS:
        raise ObservabilityReadinessError(
            f"observability schema refs mismatch: {sorted(schema_refs)}"
        )
    return tuple(sorted(signals, key=lambda signal: signal.signal_id))


def _parse_alert_rule_ids(value: Any, root: Path) -> tuple[str, ...]:
    alert_rule_ids = set(_require_text_tuple(value, "alert rule ids missing"))
    missing = sorted(EXPECTED_ALERT_RULE_IDS - alert_rule_ids)
    if missing:
        raise ObservabilityReadinessError(f"alert rule ids missing: {missing}")
    ops_catalog = _read_yaml(root / "config" / "ops_alert_rules.yaml")
    rules = _require_list(ops_catalog.get("rules"), "alert rules missing")
    catalog_ids = {
        _require_text(rule.get("id"), "alert rule id missing")
        for rule in rules
        if isinstance(rule, dict)
    }
    if not alert_rule_ids.issubset(catalog_ids):
        raise ObservabilityReadinessError("observability alert rule not in catalog")
    return tuple(sorted(alert_rule_ids))


def _parse_hosted_blockers(
    value: Any,
    root: Path,
) -> tuple[HostedObservabilityBlocker, ...]:
    blockers: list[HostedObservabilityBlocker] = []
    for item in _require_list(value, "hosted blockers missing"):
        blocker = _require_mapping(item, "hosted blocker must be a mapping")
        blocker_id = _require_text(blocker.get("id"), "hosted blocker id missing")
        status = _require_exact_text(
            blocker.get("status"),
            "blocked",
            f"{blocker_id} status",
        )
        authority = _require_text(blocker.get("authority"), f"{blocker_id} authority missing")
        _require_existing(root, authority)
        blockers.append(
            HostedObservabilityBlocker(
                blocker_id=blocker_id,
                status=status,
                authority=authority,
            )
        )
    blocker_ids = {blocker.blocker_id for blocker in blockers}
    if blocker_ids != EXPECTED_HOSTED_BLOCKERS:
        raise ObservabilityReadinessError(
            f"hosted blocker set mismatch: {sorted(blocker_ids)}"
        )
    return tuple(sorted(blockers, key=lambda blocker: blocker.blocker_id))


def _parse_validation_commands(value: Any, root: Path) -> tuple[str, ...]:
    commands = _require_text_tuple(value, "validation commands missing")
    for command in commands:
        _require_existing(root, command.split()[0])
    return commands


def _parse_limits(value: Any) -> dict[str, bool]:
    limits = _bool_mapping(value, "observability limits missing")
    for key, expected in EXPECTED_LIMITS.items():
        if limits.get(key) is not expected:
            if key == "creates_hosted_dashboard":
                raise ObservabilityReadinessError("hosted dashboard limit changed")
            raise ObservabilityReadinessError(f"observability limit changed: {key}")
    return {key: limits[key] for key in sorted(EXPECTED_LIMITS)}


def _read_yaml(path: Path) -> dict[str, Any]:
    label = _catalog_label(path)
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ObservabilityReadinessError(f"cannot read {label}") from exc
    return _require_mapping(payload, f"{label} must be a mapping")


def _require_existing(root: Path, path_text: str) -> None:
    path = _resolved_repo_path(root, path_text)
    if not path.exists():
        raise ObservabilityReadinessError(
            f"referenced observability readiness artifact missing: {path_text}"
        )


def _resolved_repo_path(root: Path, path_text: str) -> Path:
    if not path_text:
        raise ObservabilityReadinessError("empty path reference")
    candidate = Path(_normalize_path(path_text))
    if candidate.is_absolute():
        raise ObservabilityReadinessError(f"path must be repo-relative: {path_text}")
    root_resolved = root.resolve()
    resolved = (root_resolved / candidate).resolve()
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise ObservabilityReadinessError(f"path escapes repo root: {path_text}") from exc
    return resolved


def _require_mapping(value: Any, message: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ObservabilityReadinessError(message)
    return value


def _require_list(value: Any, message: str) -> list[Any]:
    if not isinstance(value, list) or not value:
        raise ObservabilityReadinessError(message)
    return value


def _require_text(value: Any, message: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ObservabilityReadinessError(message)
    return value.strip()


def _require_exact_text(value: Any, expected: str, label: str) -> str:
    text = _require_text(value, f"{label} missing")
    if text != expected:
        raise ObservabilityReadinessError(f"{label} must be {expected}")
    return text


def _require_text_tuple(value: Any, message: str) -> tuple[str, ...]:
    values = _require_list(value, message)
    text_values = tuple(_require_text(item, message) for item in values)
    if not text_values:
        raise ObservabilityReadinessError(message)
    return text_values


def _bool_mapping(value: Any, message: str) -> dict[str, bool]:
    raw = _require_mapping(value, message)
    if not all(isinstance(key, str) and isinstance(val, bool) for key, val in raw.items()):
        raise ObservabilityReadinessError(message)
    return {str(key): bool(val) for key, val in raw.items()}


def _normalize_path(path_text: str) -> str:
    return path_text.replace("\\", "/")


def _catalog_label(path: Path) -> str:
    parts = path.parts
    if len(parts) >= 2:
        return f"{parts[-2]}/{parts[-1]}"
    return path.name


__all__ = [
    "HostedObservabilityBlocker",
    "ObservabilityReadiness",
    "ObservabilityReadinessError",
    "ObservabilitySignal",
    "load_observability_readiness",
    "parse_observability_readiness",
]
