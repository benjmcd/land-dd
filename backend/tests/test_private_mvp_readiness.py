from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
READINESS_YAML = ROOT / "config" / "private_mvp_beta_readiness.yaml"
RUNBOOK_PATH = ROOT / "docs" / "runbooks" / "mvp_operator.md"
MANIFEST_PATHS = (
    ROOT / "docs" / "geographies" / "nc" / "buncombe" / "source_manifest.md",
    ROOT / "docs" / "geographies" / "nc" / "chatham" / "source_manifest.md",
    ROOT / "docs" / "geographies" / "nc" / "brunswick" / "source_manifest.md",
)


def _load_validator_module() -> ModuleType:
    module_path = ROOT / "scripts" / "private_mvp_readiness_check.py"
    spec = importlib.util.spec_from_file_location("private_mvp_readiness", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

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


def test_readiness_catalog_metadata(readiness: dict[str, Any]) -> None:
    assert readiness["schema_version"] == "private_mvp_beta_readiness_v1"
    assert readiness["operator_runbook"] == "docs/runbooks/mvp_operator.md"
    assert readiness["validation"] == "scripts/run_private_mvp_readiness_check.ps1"


def test_selected_county_source_scope_is_structured(readiness: dict[str, Any]) -> None:
    scope = readiness["selected_county_source_scope"]
    assert set(scope) == {"DS-010", "DS-011", "DS-023"}

    assert scope["DS-010"]["connector_names"] == [
        "chatham_parcels_live",
        "buncombe_parcels_live",
        "brunswick_parcels_live",
    ]
    assert scope["DS-010"]["required_surfaces"] == [
        "immediate_operator_api",
        "request_time_orchestration",
    ]
    assert "no owner/value/title fields" in scope["DS-010"]["scope_note_fragments"]
    assert "durable live-job support" in scope["DS-010"]["out_of_scope"]

    assert scope["DS-011"]["connector_names"] == [
        "county_assessor_not_evaluated",
    ]
    assert "no live assessor portal query" in scope["DS-011"]["scope_note_fragments"]
    assert "owner/value/sale-history fields" in scope["DS-011"]["out_of_scope"]

    assert scope["DS-023"]["connector_names"] == [
        "chatham_zoning_udo_recorded",
        "brunswick_zoning_udo_recorded",
    ]
    assert "Buncombe zoning" in scope["DS-023"]["out_of_scope"]
    assert "legal zoning interpretation" in scope["DS-023"]["out_of_scope"]


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


def test_private_mvp_readiness_validator_and_wrappers_exist() -> None:
    assert (ROOT / "scripts" / "private_mvp_readiness_check.py").is_file()
    assert (ROOT / "scripts" / "run_private_mvp_readiness_check.ps1").is_file()
    assert (ROOT / "scripts" / "run_private_mvp_readiness_check.sh").is_file()


def test_private_mvp_readiness_validator_passes() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/private_mvp_readiness_check.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout == ""


def test_private_mvp_validator_rejects_missing_selected_county_connector() -> None:
    validator = _load_validator_module()
    validate_scopes = validator.validate_selected_county_source_scopes
    selected_county_scope = validator.validate_selected_county_source_scope_catalog(
        validator.load_catalog(),
    )
    sources = [
        {
            "source_registry_id": "DS-010",
            "connector_names": ["chatham_parcels_live", "buncombe_parcels_live"],
            "connector_scope_notes": [
                "Chatham County NC parcel screening only",
                "Buncombe County NC parcel screening only",
                "Brunswick County NC parcel screening only",
                "no owner/value/title fields",
                "durable live-job support not claimed",
            ],
        },
        {
            "source_registry_id": "DS-011",
            "connector_names": ["county_assessor_not_evaluated"],
            "connector_surfaces": [
                "immediate_operator_api",
                "request_time_orchestration",
            ],
            "connector_scope_notes": [
                "Assessor NOT_EVALUATED sentinel only",
                "no live assessor portal query",
                "no owner/value/sale-history data",
            ],
        },
        {
            "source_registry_id": "DS-023",
            "connector_names": [
                "chatham_zoning_udo_recorded",
                "brunswick_zoning_udo_recorded",
            ],
            "connector_scope_notes": [
                "Chatham County NC recorded-fixture UDO district lookup only",
                "Brunswick County NC recorded-fixture UDO district lookup only",
                "not live PDF ingestion or legal zoning advice",
            ],
        },
    ]

    with pytest.raises(SystemExit) as exc_info:
        validate_scopes(sources, selected_county_scope)

    assert "DS-010 connector_names mismatch" in str(exc_info.value)
    assert "brunswick_parcels_live" in str(exc_info.value)


def test_private_mvp_validator_accepts_selected_county_connector_names_in_any_order() -> None:
    validator = _load_validator_module()
    validate_scopes = validator.validate_selected_county_source_scopes
    selected_county_scope = validator.validate_selected_county_source_scope_catalog(
        validator.load_catalog(),
    )
    sources = [
        {
            "source_registry_id": "DS-010",
            "connector_names": [
                "brunswick_parcels_live",
                "chatham_parcels_live",
                "buncombe_parcels_live",
            ],
            "connector_surfaces": [
                "request_time_orchestration",
                "immediate_operator_api",
            ],
            "connector_scope_notes": [
                "Chatham County NC parcel screening only",
                "Buncombe County NC parcel screening only",
                "Brunswick County NC parcel screening only",
                "no owner/value/title fields",
                "durable live-job support not claimed",
            ],
        },
        {
            "source_registry_id": "DS-011",
            "connector_names": ["county_assessor_not_evaluated"],
            "connector_surfaces": [
                "request_time_orchestration",
                "immediate_operator_api",
            ],
            "connector_scope_notes": [
                "Assessor NOT_EVALUATED sentinel only; no live assessor portal "
                "query and no owner/value/sale-history data.",
            ],
        },
        {
            "source_registry_id": "DS-023",
            "connector_names": [
                "brunswick_zoning_udo_recorded",
                "chatham_zoning_udo_recorded",
            ],
            "connector_surfaces": [
                "request_time_orchestration",
                "immediate_operator_api",
            ],
            "connector_scope_notes": [
                "Chatham County NC recorded-fixture UDO district lookup only",
                "Brunswick County NC recorded-fixture UDO district lookup only",
                "not live PDF ingestion or legal zoning advice",
            ],
        },
    ]

    validate_scopes(sources, selected_county_scope)


def test_private_mvp_validator_rejects_incomplete_structured_source_scope() -> None:
    validator = _load_validator_module()
    catalog = validator.load_catalog()
    catalog["selected_county_source_scope"] = {
        "DS-010": catalog["selected_county_source_scope"]["DS-010"],
        "DS-023": catalog["selected_county_source_scope"]["DS-023"],
    }

    with pytest.raises(SystemExit) as exc_info:
        validator.validate_selected_county_source_scope_catalog(catalog)

    assert "selected_county_source_scope source IDs mismatch" in str(exc_info.value)
    assert "DS-011" in str(exc_info.value)


def test_private_mvp_readiness_wrappers_delegate_to_shared_validator() -> None:
    for script_name in (
        "run_private_mvp_readiness_check.ps1",
        "run_private_mvp_readiness_check.sh",
    ):
        script = (ROOT / "scripts" / script_name).read_text(encoding="utf-8")

        assert "private_mvp_readiness_check.py" in script
        assert "private MVP readiness check: ok" in script


def test_operator_runbook_tracks_current_selected_county_source_scope() -> None:
    runbook = RUNBOOK_PATH.read_text(encoding="utf-8")

    for phrase in (
        "County/vendor coverage is intentionally scoped",
        "DS-010 parcel connectors are limited to Buncombe/Chatham/Brunswick",
        "DS-011 assessor remains explicit NOT_EVALUATED evidence",
        "DS-023 covers Chatham/Brunswick recorded-fixture zoning only",
    ):
        assert phrase in runbook

    for stale_phrase in (
        "County/vendor sources not ready",
        "Parcel, assessor, commercial parcel, and local zoning sources still require",
        "No machine-queryable county parcel connector",
        "No machine-queryable assessor connector; recorded as unknown",
        "| `terrain/slope` | live-connector only |",
        "| `wetlands` | live-connector only |",
    ):
        assert stale_phrase not in runbook


def test_county_source_manifests_track_structured_selected_county_scope() -> None:
    validator = _load_validator_module()

    validator.validate_county_source_manifests()

    manifest_text = "\n".join(path.read_text(encoding="utf-8") for path in MANIFEST_PATHS)
    for phrase in (
        "No Buncombe DS-023 recorded-fixture UDO lookup or live PDF connector is currently claimed",
        "DS-023 is connector-ready for Chatham County recorded-fixture UDO district lookup only",
        "DS-023 is connector-ready for Brunswick County recorded-fixture UDO district lookup only",
        "DS-010 is connector-ready for Buncombe County parcel screening only",
        "DS-010 is connector-ready for Chatham County parcel screening only",
        "DS-010 is connector-ready for Brunswick County parcel screening only",
        "AssessorNotEvaluatedConnector sentinel",
    ):
        assert phrase in manifest_text

    for stale_phrase in (
        "No machine-queryable county parcel connection is wired for private MVP",
        "No machine-queryable assessor connection is wired for private MVP",
        "was not available through the data pipeline",
        "fixture-backed (StaticZoningFixtureConnector) for private MVP regression",
    ):
        assert stale_phrase not in manifest_text


def test_private_mvp_catalog_rejects_stale_selected_county_source_scope_prose() -> None:
    catalog = READINESS_YAML.read_text(encoding="utf-8")

    for stale_phrase in (
        "Chatham parcels/zoning, Brunswick coastal/wetlands",
        "DS-010 (county GIS parcels) and DS-011 (county assessor): added to",
        "DS-023 (local zoning PDFs): covered by fixture-backed zoning connector",
        "terrain/wetlands as live-connector-only",
        "parcels/assessor as NOT_EVALUATED for fixture regression",
    ):
        assert stale_phrase not in catalog
