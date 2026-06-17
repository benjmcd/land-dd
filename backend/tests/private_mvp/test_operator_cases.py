from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest
import yaml

import app.operator_cases as operator_cases_module
from app.api.dependencies import create_api_services
from app.domain.enums import JobStatus, ReportReviewStatus
from app.operator_cases import (
    create_selected_county_report,
    get_selected_county_case,
    list_selected_county_cases,
)

ROOT = Path(__file__).resolve().parents[3]
GOLDEN_AOI_MANIFEST = ROOT / "tests" / "fixtures" / "golden_aois" / "manifest.yaml"
_WORKSPACE_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
_USER_ID = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
_SECOND_WORKSPACE_ID = UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc")
_SECOND_USER_ID = UUID("dddddddd-dddd-4ddd-8ddd-dddddddddddd")


def _golden_cases_by_id() -> dict[str, dict[str, Any]]:
    data: Any = yaml.safe_load(GOLDEN_AOI_MANIFEST.read_text(encoding="utf-8"))
    return {case["case_id"]: case for case in data["cases"]}


def _app_manifest_cases_by_id() -> dict[str, dict[str, Any]]:
    manifest_path = files("app.operator_cases").joinpath("manifest.json")
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    return {case["case_id"]: case for case in data["cases"]}


def test_selected_county_cases_list_exact_private_mvp_set() -> None:
    cases = list_selected_county_cases()

    assert len(cases) == 9
    assert tuple(case.case_id for case in cases) == tuple(_golden_cases_by_id())
    assert get_selected_county_case("CHA-rural-use") is not None
    assert get_selected_county_case("not-a-case") is None
    for case in cases:
        assert case.fixture_scope == "private_mvp_fixture"
        assert case.geometry_file.endswith(".geojson")
        assert case.connector_fixture_files


def test_app_manifest_matches_golden_aoi_manifest_by_case_and_domains() -> None:
    golden_cases = _golden_cases_by_id()
    app_cases = _app_manifest_cases_by_id()

    assert set(app_cases) == set(golden_cases)
    for case_id, golden_case in golden_cases.items():
        app_case = app_cases[case_id]
        assert app_case["county"] == golden_case["county"]
        assert app_case["state"] == golden_case["state"]
        assert set(app_case["connector_fixture_files"]) == set(
            golden_case["connector_fixture_files"]
        )
        assert sorted(app_case["expected_connector_workflow_domains"]) == sorted(
            golden_case["expected_connector_workflow_domains"]
        )


def test_selected_county_manifest_declares_package_local_resources() -> None:
    package_root = files("app.operator_cases")
    for case in _app_manifest_cases_by_id().values():
        assert package_root.joinpath(case["geometry_file"]).is_file()
        for fixture_file in case["connector_fixture_files"].values():
            assert package_root.joinpath(fixture_file).is_file()


@pytest.mark.parametrize(
    "case_id",
    [case.case_id for case in list_selected_county_cases()],
)
def test_every_selected_county_case_creates_approved_report(case_id: str) -> None:
    services = create_api_services()

    result = create_selected_county_report(
        services,
        case_id,
        reviewer_id="operator-case-test",
        reason="private MVP fixture case approval",
    )

    assert result.case.case_id == case_id
    assert result.case.fixture_scope == "private_mvp_fixture"
    assert result.connector_count == len(result.case.connector_fixture_files)
    assert result.evidence_created_count > 0
    assert result.report_run.status == JobStatus.SUCCEEDED
    assert result.report_run.review_status == ReportReviewStatus.APPROVED
    assert result.report_run.reviewed_by == "operator-case-test"
    assert result.report_run.source_manifest["source_ids"]
    assert result.report_run.source_manifest["source_details"]

    all_claims = (
        result.report_run.claims
        + result.report_run.unknowns
        + result.report_run.red_flags
    )
    assert all_claims
    for claim in all_claims:
        assert claim.evidence_ids


def test_selected_county_case_report_threads_workspace_user_and_reviewer_provenance() -> None:
    services = create_api_services()

    result = create_selected_county_report(
        services,
        "BUN-slope",
        reviewer_id="operator-case-test",
        reason="private MVP fixture case approval",
        workspace_id=_WORKSPACE_ID,
        requested_by=_USER_ID,
    )

    expected_area_id = operator_cases_module._area_id_for(
        result.case,
        workspace_id=_WORKSPACE_ID,
    )
    assert result.report_run.area_id == expected_area_id
    area = services.area_service.get(result.report_run.area_id)
    assert area is not None
    assert area.workspace_id == _WORKSPACE_ID
    assert area.created_by == _USER_ID

    queue_items = services.connector_review_queue.list_connector_runs(
        workspace_id=_WORKSPACE_ID,
        limit=100,
    )
    assert len(queue_items) == result.connector_count
    assert {item.workspace_id for item in queue_items} == {_WORKSPACE_ID}
    assert {item.payload["requested_by"] for item in queue_items} == {str(_USER_ID)}
    assert {
        item.payload["review_decision"]["reviewer_id"] for item in queue_items
    } == {"operator-case-test"}

    assert result.report_run.workspace_id == _WORKSPACE_ID
    assert result.report_run.requested_by == _USER_ID
    assert result.report_run.reviewed_by == "operator-case-test"


def test_selected_county_case_report_scopes_connector_queue_runs_by_workspace() -> None:
    services = create_api_services()

    first = create_selected_county_report(
        services,
        "BUN-slope",
        reviewer_id="operator-case-test",
        reason="private MVP fixture case approval",
        workspace_id=_WORKSPACE_ID,
        requested_by=_USER_ID,
    )
    second = create_selected_county_report(
        services,
        "BUN-slope",
        reviewer_id="operator-case-test",
        reason="private MVP fixture case approval",
        workspace_id=_SECOND_WORKSPACE_ID,
        requested_by=_SECOND_USER_ID,
    )

    first_area = services.area_service.get(first.report_run.area_id)
    second_area = services.area_service.get(second.report_run.area_id)
    assert first_area is not None
    assert second_area is not None
    assert first.report_run.area_id != second.report_run.area_id
    assert first_area.workspace_id == _WORKSPACE_ID
    assert second_area.workspace_id == _SECOND_WORKSPACE_ID
    assert first.report_run.workspace_id == _WORKSPACE_ID
    assert second.report_run.workspace_id == _SECOND_WORKSPACE_ID
    first_evidence = [
        item
        for item in services.evidence_service.list_by_area(first.report_run.area_id)
        if item.source_ingest_run_id is not None
    ]
    second_evidence = [
        item
        for item in services.evidence_service.list_by_area(second.report_run.area_id)
        if item.source_ingest_run_id is not None
    ]
    assert len(first_evidence) == first.evidence_created_count
    assert len(second_evidence) == second.evidence_created_count
    assert first.evidence_created_count > 0
    assert second.evidence_created_count > 0
    assert {item.evidence_id for item in first_evidence}.isdisjoint(
        {item.evidence_id for item in second_evidence},
    )
    assert {item.source_ingest_run_id for item in first_evidence}.isdisjoint(
        {item.source_ingest_run_id for item in second_evidence},
    )

    first_items = services.connector_review_queue.list_connector_runs(
        workspace_id=_WORKSPACE_ID,
        limit=100,
    )
    second_items = services.connector_review_queue.list_connector_runs(
        workspace_id=_SECOND_WORKSPACE_ID,
        limit=100,
    )
    assert len(first_items) == first.connector_count
    assert len(second_items) == second.connector_count
    assert {item.workspace_id for item in first_items} == {_WORKSPACE_ID}
    assert {item.workspace_id for item in second_items} == {_SECOND_WORKSPACE_ID}
    assert {item.ingest_run_id for item in first_items}.isdisjoint(
        {item.ingest_run_id for item in second_items},
    )
    assert {item.idempotency_key for item in first_items}.isdisjoint(
        {item.idempotency_key for item in second_items},
    )


def test_selected_county_case_report_fails_closed_for_unsupported_case() -> None:
    with pytest.raises(ValueError, match="Unsupported selected-county private-MVP case"):
        create_selected_county_report(create_api_services(), "WAKE-not-selected")
