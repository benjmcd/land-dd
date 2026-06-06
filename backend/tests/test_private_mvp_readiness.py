from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
READINESS_YAML = ROOT / "config" / "private_mvp_beta_readiness.yaml"

EXPECTED_PRIVATE_MVP_GATES = {
    "geography_selected",
    "county_manifests_present",
    "golden_aoi_fixture_manifest",
    "fixture_regression_path",
    "db_backed_regression_path",
    "ds010_011_023_selected_county_behavior",
    "ds010_source_review_gate",
    "unauthenticated_workspace_isolation",
    "sync_async_create_divergence",
    "ds017_not_required",
    "markdown_dossier_delivery",
    "overclaim_checks",
    "evidence_lineage_checks",
    "unknowns_visible",
    "operator_runbook_current",
}

HOSTED_PRODUCTION_ONLY_ITEMS = {
    "hosted_deployment",
    "oauth_oidc",
    "registry_publication",
    "billing",
    "external_secret_manager",
}


@pytest.fixture
def readiness() -> dict[str, Any]:
    data: Any = yaml.safe_load(READINESS_YAML.read_text(encoding="utf-8"))
    return data  # type: ignore[no-any-return]


def test_readiness_yaml_loads(readiness: dict[str, Any]) -> None:
    assert isinstance(readiness, dict), "Readiness YAML must be a mapping"


def test_private_mvp_beta_section_exists(readiness: dict[str, Any]) -> None:
    assert "private_mvp_beta" in readiness, (
        "private_mvp_beta section missing from readiness YAML"
    )


def test_hosted_production_section_exists(readiness: dict[str, Any]) -> None:
    assert "hosted_production" in readiness, (
        "hosted_production section missing from readiness YAML"
    )


def test_all_private_mvp_gates_present(readiness: dict[str, Any]) -> None:
    gates = set(readiness["private_mvp_beta"].keys())
    missing = EXPECTED_PRIVATE_MVP_GATES - gates
    assert not missing, (
        f"private_mvp_beta section is missing required gates: {sorted(missing)}"
    )


def test_private_mvp_gates_have_status_and_note(readiness: dict[str, Any]) -> None:
    for gate_name, gate in readiness["private_mvp_beta"].items():
        assert isinstance(gate, dict), (
            f"private_mvp_beta.{gate_name} must be a mapping with status/note fields"
        )
        assert "status" in gate, (
            f"private_mvp_beta.{gate_name} is missing required 'status' field"
        )
        assert gate["status"] in {"complete", "pending", "blocked", "accepted_with_risk"}, (
            f"private_mvp_beta.{gate_name}.status must be"
            " complete/pending/blocked/accepted_with_risk,"
            f" got {gate['status']!r}"
        )
        assert "note" in gate, (
            f"private_mvp_beta.{gate_name} is missing required 'note' field"
        )


def test_no_private_mvp_gate_is_blocked(readiness: dict[str, Any]) -> None:
    blocked_gates = [
        name
        for name, gate in readiness["private_mvp_beta"].items()
        if isinstance(gate, dict) and gate.get("status") == "blocked"
    ]
    assert not blocked_gates, (
        "private_mvp_beta gates must not be blocked — all blocking conditions "
        "belong in hosted_production. Blocked gates: "
        + str(sorted(blocked_gates))
    )


def test_no_private_mvp_required_gate_is_pending(readiness: dict[str, Any]) -> None:
    """Gates that are implemented and verified must not linger as pending."""
    pending_gates = [
        name
        for name, gate in readiness["private_mvp_beta"].items()
        if isinstance(gate, dict) and gate.get("status") == "pending"
    ]
    assert not pending_gates, (
        "private_mvp_beta has pending gates — either promote to complete/accepted_with_risk "
        "with evidence, or document a real blocker. Pending: "
        + str(sorted(pending_gates))
    )


def test_hosted_production_not_required_flag(readiness: dict[str, Any]) -> None:
    hosted = readiness["hosted_production"]
    assert hosted.get("_not_required_for_private_mvp") is True, (
        "hosted_production._not_required_for_private_mvp must be true to "
        "explicitly mark these gates as out of scope for private MVP"
    )


def test_hosted_production_items_present(readiness: dict[str, Any]) -> None:
    hosted_keys = set(readiness["hosted_production"].keys())
    missing = HOSTED_PRODUCTION_ONLY_ITEMS - hosted_keys
    assert not missing, (
        f"hosted_production section is missing expected items: {sorted(missing)}"
    )


def test_hosted_production_items_are_blocked(readiness: dict[str, Any]) -> None:
    for item_name in HOSTED_PRODUCTION_ONLY_ITEMS:
        item = readiness["hosted_production"].get(item_name)
        assert isinstance(item, dict), (
            f"hosted_production.{item_name} must be a mapping with status/note"
        )
        assert item.get("status") == "blocked", (
            f"hosted_production.{item_name} should have status=blocked to "
            "explicitly document it is not required for private MVP; "
            f"got {item.get('status')!r}"
        )
