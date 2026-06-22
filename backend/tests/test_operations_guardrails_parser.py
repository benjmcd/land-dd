"""Tests for operations_guardrails.py parser hardening (OG-1, OG-2).

Each test drifts the valid retention or cost catalog in one specific way and
asserts parse_operations_guardrails raises OperationsGuardrailsError (fail-closed).
Happy-path is covered by a single test that uses the real catalogs.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from app.operations_guardrails import (
    BLOCKED_OR_DISABLED_COST_STATUSES,
    REQUIRED_RETENTION_BLOCKER_IDS,
    OperationsGuardrailsError,
    parse_operations_guardrails,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_alert_catalog() -> dict[str, Any]:
    return yaml.safe_load(
        (REPO_ROOT / "config" / "ops_alert_rules.yaml").read_text(encoding="utf-8")
    )


def _load_retention_catalog() -> dict[str, Any]:
    return yaml.safe_load(
        (REPO_ROOT / "config" / "data_retention.yaml").read_text(encoding="utf-8")
    )


def _load_cost_catalog() -> dict[str, Any]:
    return yaml.safe_load(
        (REPO_ROOT / "config" / "ops_cost_monitoring.yaml").read_text(encoding="utf-8")
    )


# ---------------------------------------------------------------------------
# Happy-path: real catalogs parse without error
# ---------------------------------------------------------------------------


def test_operations_guardrails_parse_happy_path() -> None:
    result = parse_operations_guardrails(
        _load_alert_catalog(),
        _load_retention_catalog(),
        _load_cost_catalog(),
        root=REPO_ROOT,
    )
    assert result.retention_schema_version == "data_retention_v1"
    assert set(result.retention_blocker_ids) >= REQUIRED_RETENTION_BLOCKER_IDS
    assert result.cost_schema_version == "ops_cost_monitoring_v1"


# ---------------------------------------------------------------------------
# OG-1: required retention blocker ids
# ---------------------------------------------------------------------------


def test_og1_missing_automated_deletion_blocker_raises() -> None:
    """Removing the automated_deletion retention blocker must raise OperationsGuardrailsError."""
    retention = _load_retention_catalog()
    retention["retention_blockers"] = [
        b for b in retention["retention_blockers"] if b["id"] != "automated_deletion"
    ]
    with pytest.raises(OperationsGuardrailsError, match="blocker"):
        parse_operations_guardrails(
            _load_alert_catalog(),
            retention,
            _load_cost_catalog(),
            root=REPO_ROOT,
        )


def test_og1_missing_hosted_log_retention_blocker_raises() -> None:
    """Removing the hosted_log_retention retention blocker must raise OperationsGuardrailsError."""
    retention = _load_retention_catalog()
    retention["retention_blockers"] = [
        b for b in retention["retention_blockers"] if b["id"] != "hosted_log_retention"
    ]
    with pytest.raises(OperationsGuardrailsError, match="blocker"):
        parse_operations_guardrails(
            _load_alert_catalog(),
            retention,
            _load_cost_catalog(),
            root=REPO_ROOT,
        )


def test_og1_required_blocker_ids_constant_matches_catalog() -> None:
    """Sanity: REQUIRED_RETENTION_BLOCKER_IDS is a subset of the real catalog blocker ids."""
    retention = _load_retention_catalog()
    actual_ids = {b["id"] for b in retention["retention_blockers"]}
    assert REQUIRED_RETENTION_BLOCKER_IDS.issubset(actual_ids)


# ---------------------------------------------------------------------------
# OG-2: must-be-blocked cost categories drift to enabled-looking status
# ---------------------------------------------------------------------------


def test_og2_llm_drifts_to_enabled_raises() -> None:
    """llm category status changing to 'enabled' must raise OperationsGuardrailsError."""
    cost = _load_cost_catalog()
    for cat in cost["categories"]:
        if cat["id"] == "llm":
            cat["status"] = "enabled"
    with pytest.raises(OperationsGuardrailsError, match="llm"):
        parse_operations_guardrails(
            _load_alert_catalog(),
            _load_retention_catalog(),
            cost,
            root=REPO_ROOT,
        )


def test_og2_maps_drifts_to_enabled_raises() -> None:
    """maps category status changing to 'monitored' must raise OperationsGuardrailsError."""
    cost = _load_cost_catalog()
    for cat in cost["categories"]:
        if cat["id"] == "maps":
            cat["status"] = "monitored"
    with pytest.raises(OperationsGuardrailsError, match="maps"):
        parse_operations_guardrails(
            _load_alert_catalog(),
            _load_retention_catalog(),
            cost,
            root=REPO_ROOT,
        )


def test_og2_geocoding_drifts_to_enabled_raises() -> None:
    """geocoding category status changing to 'enabled' must raise OperationsGuardrailsError."""
    cost = _load_cost_catalog()
    for cat in cost["categories"]:
        if cat["id"] == "geocoding":
            cat["status"] = "enabled"
    with pytest.raises(OperationsGuardrailsError, match="geocoding"):
        parse_operations_guardrails(
            _load_alert_catalog(),
            _load_retention_catalog(),
            cost,
            root=REPO_ROOT,
        )


def test_og2_data_vendors_drifts_to_enabled_raises() -> None:
    """data_vendors category status changing to 'enabled' must raise OperationsGuardrailsError."""
    cost = _load_cost_catalog()
    for cat in cost["categories"]:
        if cat["id"] == "data_vendors":
            cat["status"] = "enabled"
    with pytest.raises(OperationsGuardrailsError, match="data_vendors"):
        parse_operations_guardrails(
            _load_alert_catalog(),
            _load_retention_catalog(),
            cost,
            root=REPO_ROOT,
        )


def test_og2_blocked_statuses_constant_matches_catalog() -> None:
    """Sanity: all must-be-blocked categories have a BLOCKED_OR_DISABLED status in real catalog."""
    cost = _load_cost_catalog()
    must_blocked = {"llm", "maps", "geocoding", "data_vendors"}
    for cat in cost["categories"]:
        if cat["id"] in must_blocked:
            assert cat["status"] in BLOCKED_OR_DISABLED_COST_STATUSES, (
                f"{cat['id']} status {cat['status']!r} not in BLOCKED_OR_DISABLED_COST_STATUSES"
            )
