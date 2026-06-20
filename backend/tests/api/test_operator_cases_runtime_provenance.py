from __future__ import annotations

from typing import Any, cast

import app.operator_cases as selected_county_cases
from app.api.dependencies import ApiServices, create_api_services
from app.domain.source_contracts import SourceContract

_SELECTED_FIXTURE_SOURCE = "Selected County Private MVP Fixtures"
_UNSUPPORTED_SOURCE = "Land Diligence MVP - Unsupported Screening Categories"
_CONNECTOR_BY_DOMAIN = {
    "access": "fixture_access_static",
    "buildability": "fixture_buildability_static",
    "flood": "fixture_flood_static",
    "parcels": "fixture_parcel_static",
    "soils": "fixture_soils_static",
    "terrain": "fixture_terrain_static",
    "wetlands": "fixture_wetlands_static",
    "zoning": "fixture_zoning_static",
}


def _source_by_name(services: ApiServices, source_name: str) -> SourceContract:
    source = next(
        (
            candidate
            for candidate in services.source_service.list_all()
            if candidate.name == source_name
        ),
        None,
    )
    assert source is not None, f"{source_name} source was not registered"
    return source


def _review_bundle(services: ApiServices, source_name: str) -> dict[str, Any]:
    source = _source_by_name(services, source_name)
    bundle = services.source_provenance_service.export_review_bundle(source.source_id)
    assert isinstance(bundle, dict)
    return bundle


def _fixture_bundle(services: ApiServices) -> dict[str, Any]:
    return _review_bundle(services, _SELECTED_FIXTURE_SOURCE)


def _expected_connector_names(case_id: str) -> set[str]:
    case = selected_county_cases.get_selected_county_case(case_id)
    assert case is not None
    return {
        _CONNECTOR_BY_DOMAIN[domain]
        for domain in case.connector_fixture_files
    }


def _runs_by_connector(bundle: dict[str, Any]) -> dict[str, dict[str, Any]]:
    runs = bundle["retrieval_runs"]
    assert isinstance(runs, list)
    by_connector: dict[str, dict[str, Any]] = {}
    for run in runs:
        assert isinstance(run, dict)
        connector_name = run["connector_name"]
        assert isinstance(connector_name, str)
        assert connector_name not in by_connector
        by_connector[connector_name] = run
    return by_connector


def test_selected_county_runtime_provenance_review_bundle_records_fixture_runs() -> None:
    services = create_api_services()

    result = selected_county_cases.create_selected_county_report(services, "BUN-slope")
    fixture_source = _source_by_name(services, _SELECTED_FIXTURE_SOURCE)
    bundle = _fixture_bundle(services)
    runs_by_connector = _runs_by_connector(bundle)
    expected_connectors = _expected_connector_names("BUN-slope")
    source_names = cast(list[str], result.report_run.source_manifest["source_names"])
    source_ids = cast(list[str], result.report_run.source_manifest["source_ids"])

    assert _SELECTED_FIXTURE_SOURCE in source_names
    assert str(fixture_source.source_id) in source_ids
    assert bundle["review_summary"] == {
        "source_count": 1,
        "dataset_count": 1,
        "dataset_version_count": 1,
        "retrieval_run_count": result.connector_count,
    }
    assert set(runs_by_connector) == expected_connectors
    for run in runs_by_connector.values():
        assert run["status"] == "succeeded"
        assert run["metrics"]["fixture_only"] is True
        assert run["metrics"]["source"] == "local_json"


def test_selected_county_runtime_provenance_is_idempotent_for_repeated_case_runs() -> None:
    services = create_api_services()

    selected_county_cases.create_selected_county_report(services, "BUN-slope")
    selected_county_cases.create_selected_county_report(services, "BUN-slope")

    bundle = _fixture_bundle(services)
    runs_by_connector = _runs_by_connector(bundle)
    ingest_run_ids = {run["ingest_run_id"] for run in runs_by_connector.values()}

    assert bundle["review_summary"]["dataset_count"] == 1
    assert bundle["review_summary"]["dataset_version_count"] == 1
    assert bundle["review_summary"]["retrieval_run_count"] == len(
        _expected_connector_names("BUN-slope")
    )
    assert len(ingest_run_ids) == len(runs_by_connector)


def test_selected_county_runtime_provenance_preserves_case_specific_scope() -> None:
    services = create_api_services()

    result = selected_county_cases.create_selected_county_report(
        services,
        "BRU-jurisdiction",
    )
    runs_by_connector = _runs_by_connector(_fixture_bundle(services))

    assert result.connector_count == 3
    assert set(runs_by_connector) == _expected_connector_names("BRU-jurisdiction")
    assert "fixture_zoning_static" in runs_by_connector
    assert "fixture_flood_static" not in runs_by_connector
    assert "fixture_soils_static" not in runs_by_connector


def test_unsupported_screening_source_has_no_fixture_retrieval_runs() -> None:
    services = create_api_services()

    selected_county_cases.create_selected_county_report(services, "CHA-zoning-edge")

    bundle = _review_bundle(services, _UNSUPPORTED_SOURCE)

    assert bundle["review_summary"] == {
        "source_count": 1,
        "dataset_count": 0,
        "dataset_version_count": 0,
        "retrieval_run_count": 0,
    }
    assert bundle["datasets"] == []
    assert bundle["dataset_versions"] == []
    assert bundle["retrieval_runs"] == []
