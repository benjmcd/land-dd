from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path
from typing import Any

import pytest
import yaml

from app.api.dependencies import create_api_services
from app.domain.enums import JobStatus, ReportReviewStatus
from app.operator_cases import (
    create_selected_county_report,
    get_selected_county_case,
    list_selected_county_cases,
)

ROOT = Path(__file__).resolve().parents[3]
GOLDEN_AOI_MANIFEST = ROOT / "tests" / "fixtures" / "golden_aois" / "manifest.yaml"


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


def test_selected_county_case_report_fails_closed_for_unsupported_case() -> None:
    with pytest.raises(ValueError, match="Unsupported selected-county private-MVP case"):
        create_selected_county_report(create_api_services(), "WAKE-not-selected")
