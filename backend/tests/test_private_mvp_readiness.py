from __future__ import annotations

import copy
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
IMPLEMENTATION_READINESS_PATH = ROOT / "docs" / "IMPLEMENTATION_READINESS.md"
MANIFEST_PATHS_BY_KEY = {
    "buncombe_nc": ROOT / "docs" / "geographies" / "nc" / "buncombe" / "source_manifest.md",
    "chatham_nc": ROOT / "docs" / "geographies" / "nc" / "chatham" / "source_manifest.md",
    "brunswick_nc": ROOT / "docs" / "geographies" / "nc" / "brunswick" / "source_manifest.md",
}
MANIFEST_PATHS = tuple(MANIFEST_PATHS_BY_KEY.values())


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


def test_selected_county_manifest_scope_is_structured(readiness: dict[str, Any]) -> None:
    scope = readiness["selected_county_manifest_scope"]
    assert set(scope["stale_fragments"]) >= {
        "No machine-queryable county parcel connection is wired for private MVP",
        "No machine-queryable assessor connection is wired for private MVP",
        "was not available through the data pipeline",
    }

    counties = scope["counties"]
    assert set(counties) == set(MANIFEST_PATHS_BY_KEY)
    for county_key, manifest_path in MANIFEST_PATHS_BY_KEY.items():
        county_scope = counties[county_key]
        assert county_scope["source_manifest"] == str(
            manifest_path.relative_to(ROOT).as_posix(),
        )
        assert set(county_scope["source_fragments"]) == {"DS-010", "DS-011", "DS-023"}

    assert (
        "No Buncombe DS-023 recorded-fixture UDO lookup or live PDF connector is currently claimed"
        in counties["buncombe_nc"]["source_fragments"]["DS-023"]
    )
    assert (
        "DS-023 is connector-ready for Chatham County recorded-fixture UDO district lookup only"
        in counties["chatham_nc"]["source_fragments"]["DS-023"]
    )
    assert (
        "DS-023 is connector-ready for Brunswick County recorded-fixture UDO district lookup only"
        in counties["brunswick_nc"]["source_fragments"]["DS-023"]
    )


def test_selected_county_source_provenance_scope_is_structured(
    readiness: dict[str, Any],
) -> None:
    scope = readiness["selected_county_source_provenance_scope"]
    assert scope["expectation_enums"] == {
        "dataset": [
            "county_source_dataset",
            "not_evaluated_sentinel",
            "recorded_fixture_dataset",
            "not_required_out_of_scope",
        ],
        "version": [
            "source_version_or_access_date",
            "static_sentinel_version",
            "recorded_fixture_version",
            "not_required_out_of_scope",
        ],
        "retrieval": [
            "connector_retrieval_metadata",
            "source_failure_metadata",
            "fixture_retrieval_metadata",
            "not_required_out_of_scope",
        ],
    }

    counties = scope["counties"]
    assert set(counties) == set(MANIFEST_PATHS_BY_KEY)
    assert set(counties["buncombe_nc"]["sources"]) == {"DS-010", "DS-011", "DS-023"}
    assert counties["buncombe_nc"]["sources"]["DS-010"] == {
        "source_registry_id": "DS-010",
        "connector_names": ["buncombe_parcels_live"],
        "dataset_expectation": "county_source_dataset",
        "version_expectation": "source_version_or_access_date",
        "retrieval_expectation": "connector_retrieval_metadata",
        "out_of_scope": False,
    }
    assert counties["chatham_nc"]["sources"]["DS-023"]["connector_names"] == [
        "chatham_zoning_udo_recorded",
    ]
    assert counties["brunswick_nc"]["sources"]["DS-023"]["connector_names"] == [
        "brunswick_zoning_udo_recorded",
    ]


def test_private_mvp_validator_rejects_missing_source_provenance_scope() -> None:
    validator = _load_validator_module()
    catalog = copy.deepcopy(validator.load_catalog())
    selected_county_scope = validator.validate_selected_county_source_scope_catalog(
        catalog,
    )
    manifest_scope = validator.validate_selected_county_manifest_scope_catalog(catalog)
    del catalog["selected_county_source_provenance_scope"]

    assert hasattr(validator, "validate_selected_county_source_provenance_scope_catalog")
    with pytest.raises(SystemExit) as exc_info:
        validator.validate_selected_county_source_provenance_scope_catalog(
            catalog,
            selected_county_scope,
            manifest_scope,
        )

    assert "selected_county_source_provenance_scope section missing" in str(
        exc_info.value,
    )


def test_private_mvp_validator_rejects_unknown_source_provenance_scope() -> None:
    validator = _load_validator_module()
    catalog = copy.deepcopy(validator.load_catalog())
    selected_county_scope = validator.validate_selected_county_source_scope_catalog(
        catalog,
    )
    manifest_scope = validator.validate_selected_county_manifest_scope_catalog(catalog)
    catalog["selected_county_source_provenance_scope"]["counties"]["chatham_nc"][
        "sources"
    ]["DS-017"] = {
        "source_registry_id": "DS-017",
        "connector_names": ["commercial_parcel_vendor"],
        "dataset_expectation": "county_source_dataset",
        "version_expectation": "source_version_or_access_date",
        "retrieval_expectation": "connector_retrieval_metadata",
        "out_of_scope": False,
    }

    with pytest.raises(SystemExit) as exc_info:
        validator.validate_selected_county_source_provenance_scope_catalog(
            catalog,
            selected_county_scope,
            manifest_scope,
        )

    assert "selected_county_source_provenance_scope.counties.chatham_nc" in str(
        exc_info.value,
    )
    assert "DS-017" in str(exc_info.value)


def test_private_mvp_validator_rejects_source_provenance_connector_mismatch() -> None:
    validator = _load_validator_module()
    catalog = copy.deepcopy(validator.load_catalog())
    selected_county_scope = validator.validate_selected_county_source_scope_catalog(
        catalog,
    )
    manifest_scope = validator.validate_selected_county_manifest_scope_catalog(catalog)
    catalog["selected_county_source_provenance_scope"]["counties"]["chatham_nc"][
        "sources"
    ]["DS-010"]["connector_names"] = ["buncombe_parcels_live"]

    with pytest.raises(SystemExit) as exc_info:
        validator.validate_selected_county_source_provenance_scope_catalog(
            catalog,
            selected_county_scope,
            manifest_scope,
        )

    assert "DS-010 connector_names mismatch" in str(exc_info.value)
    assert "chatham_parcels_live" in str(exc_info.value)


def test_private_mvp_validator_rejects_cross_county_connector_swap() -> None:
    validator = _load_validator_module()
    catalog = copy.deepcopy(validator.load_catalog())
    selected_county_scope = validator.validate_selected_county_source_scope_catalog(
        catalog,
    )
    manifest_scope = validator.validate_selected_county_manifest_scope_catalog(catalog)
    catalog["selected_county_source_provenance_scope"]["counties"]["buncombe_nc"][
        "sources"
    ]["DS-010"]["connector_names"] = ["chatham_parcels_live"]
    catalog["selected_county_source_provenance_scope"]["counties"]["chatham_nc"][
        "sources"
    ]["DS-010"]["connector_names"] = ["buncombe_parcels_live"]

    with pytest.raises(SystemExit) as exc_info:
        validator.validate_selected_county_source_provenance_scope_catalog(
            catalog,
            selected_county_scope,
            manifest_scope,
        )

    assert "buncombe_nc.sources.DS-010.connector_names" in str(exc_info.value)


def test_private_mvp_validator_rejects_wrong_source_provenance_expectation_class() -> None:
    validator = _load_validator_module()
    catalog = copy.deepcopy(validator.load_catalog())
    selected_county_scope = validator.validate_selected_county_source_scope_catalog(
        catalog,
    )
    manifest_scope = validator.validate_selected_county_manifest_scope_catalog(catalog)
    catalog["selected_county_source_provenance_scope"]["counties"]["chatham_nc"][
        "sources"
    ]["DS-011"]["dataset_expectation"] = "county_source_dataset"
    catalog["selected_county_source_provenance_scope"]["counties"]["chatham_nc"][
        "sources"
    ]["DS-011"]["version_expectation"] = "source_version_or_access_date"
    catalog["selected_county_source_provenance_scope"]["counties"]["chatham_nc"][
        "sources"
    ]["DS-011"]["retrieval_expectation"] = "connector_retrieval_metadata"

    with pytest.raises(SystemExit) as exc_info:
        validator.validate_selected_county_source_provenance_scope_catalog(
            catalog,
            selected_county_scope,
            manifest_scope,
        )

    assert "chatham_nc.sources.DS-011 provenance expectations mismatch" in str(
        exc_info.value,
    )


def test_buncombe_ds023_source_provenance_remains_out_of_scope(
    readiness: dict[str, Any],
) -> None:
    buncombe_ds023 = readiness["selected_county_source_provenance_scope"]["counties"][
        "buncombe_nc"
    ]["sources"]["DS-023"]

    assert buncombe_ds023 == {
        "source_registry_id": "DS-023",
        "connector_names": [],
        "dataset_expectation": "not_required_out_of_scope",
        "version_expectation": "not_required_out_of_scope",
        "retrieval_expectation": "not_required_out_of_scope",
        "out_of_scope": True,
        "out_of_scope_reason": (
            "Buncombe zoning is explicitly outside selected-county DS-023 scope"
        ),
    }


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


def test_private_mvp_validator_rejects_incomplete_manifest_scope_catalog() -> None:
    validator = _load_validator_module()
    catalog = validator.load_catalog()
    del catalog["selected_county_manifest_scope"]["counties"]["buncombe_nc"][
        "source_fragments"
    ]["DS-023"]

    with pytest.raises(SystemExit) as exc_info:
        validator.validate_selected_county_manifest_scope_catalog(catalog)

    assert "selected_county_manifest_scope.counties.buncombe_nc" in str(
        exc_info.value,
    )
    assert "source IDs mismatch" in str(exc_info.value)
    assert "DS-023" in str(exc_info.value)


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


def test_operator_runbook_has_selected_county_proof_matrix() -> None:
    runbook = RUNBOOK_PATH.read_text(encoding="utf-8")

    for phrase in (
        "## Operator Path Proof Matrix",
        "### Operator path execution qualifiers",
        (
            "| Path | Evidence richness | Approval gate | DB required | "
            "Live network required | Main limitation |"
        ),
        "### Identifier glossary",
        "Packaged selected-county fixture case slug (not an AOI UUID)",
        "Connector evidence/review run ID",
        "| `{report_run_id}` | Report/job ID |",
        "`scripts/generate_dossier.py --connector all --approve --artifact`",
        "`POST /operator-cases/{case_id}/report`",
        "Generic `POST /report-runs`",
        "DB-backed verification with `RUN_DB_SMOKE=1`",
        "same in-memory report artifact contract shape",
        (
            "code-level integration pattern over an existing `{area_id}` plus "
            "whatever evidence is already ingested/reviewed"
        ),
        "not the packaged selected-county corpus path",
        (
            "does not exercise HTTP routing, access gates, or DB artifact "
            "persistence"
        ),
        (
            "It does not prove the HTTP `POST /report-runs` surface, "
            "`/operator-cases/{case_id}/report`, or DB artifact persistence"
        ),
        (
            "all nine packaged selected-county operator DB smoke cases"
        ),
        "backend/tests/api/test_operator_cases_db.py",
        "does not prove full hosted production",
        "outside the selected private-MVP set",
        "the `/ui/operator-cases/report` launcher",
        "approved UI delivery links",
        "follows the approved report lineage route",
        "--reviewer-id fixture-reviewer",
        "--reviewer-token fixture-token-123",
        "--expect-artifact-persistence postgres+object_store",
        "artifact_metadata.persistence",
    ):
        assert phrase in runbook

    for stale_phrase in (
        "emits the same JSON serialization the API serves",
        "generic report creation loads the packaged selected-county connector fixtures",
        "/report-runs/{id}",
        "/ui/report-runs/{id}",
    ):
        assert stale_phrase not in runbook


def test_implementation_readiness_routes_after_selected_county_proof() -> None:
    readiness_doc = IMPLEMENTATION_READINESS_PATH.read_text(encoding="utf-8")
    normalized_doc = " ".join(readiness_doc.split())

    for phrase in (
        "Pick the state/counties",
        "one selected-county fixture-backed source adapter",
        "first source candidates",
    ):
        assert phrase not in readiness_doc

    for phrase in (
        "Buncombe, Chatham, and Brunswick",
        "selected NC counties",
        "`/operator-cases/{case_id}/report`",
        "Operator Path Proof Matrix",
        "source-management/live connector tenancy",
        "report job scheduling",
        "dossier surface expansion",
        "legacy/null ownership",
        "hosted-production blockers",
    ):
        assert phrase in normalized_doc


def test_county_source_manifests_track_structured_selected_county_scope() -> None:
    validator = _load_validator_module()
    manifest_scope = validator.validate_selected_county_manifest_scope_catalog(
        validator.load_catalog(),
    )

    validator.validate_county_source_manifests(manifest_scope)

    counties = manifest_scope["counties"]
    for county_scope in counties.values():
        manifest = (ROOT / county_scope["source_manifest"]).read_text(encoding="utf-8")
        for fragments in county_scope["source_fragments"].values():
            for phrase in fragments:
                assert phrase in manifest

    manifest_text = "\n".join(path.read_text(encoding="utf-8") for path in MANIFEST_PATHS)
    for stale_phrase in manifest_scope["stale_fragments"]:
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


def test_db_backed_regression_path_names_all_packaged_operator_cases(
    readiness: dict[str, Any],
) -> None:
    gate = readiness["private_mvp_beta"]["db_backed_regression_path"]
    proof_text = f"{gate['evidence']}\n{gate['note']}"

    for phrase in (
        "backend/tests/api/test_report_runs_db.py",
        "test_db_backed_full_reviewed_dossier_path",
        "backend/tests/api/test_operator_cases_db.py",
        "test_db_operator_case_report_persists_selected_county_fixture",
        "test_db_ui_operator_case_report_persists_selected_county_fixture",
        "BUN-slope",
        "BUN-flood",
        "BUN-access",
        "CHA-rural-use",
        "CHA-zoning-edge",
        "CHA-parcel-tax",
        "BRU-coastal-flood",
        "BRU-wetlands-soils",
        "BRU-jurisdiction",
        "all nine packaged selected-county operator cases",
        "/ui/operator-cases/report",
        "approved UI delivery links",
    ):
        assert phrase in proof_text

    assert "Full AOI-to-approved-dossier DB-backed path proven" in proof_text
    assert (
        "does not prove full hosted production or live-source production coverage"
        in proof_text
    )
