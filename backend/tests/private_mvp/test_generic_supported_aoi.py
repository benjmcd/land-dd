from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from app.api.dependencies import create_api_services
from app.domain.area_contracts import AreaContract
from app.domain.enums import IntentCode, JobStatus, ReportReviewStatus
from app.operator_cases import (
    UnsupportedSelectedCountyAoiError,
    create_supported_aoi_report,
)

ROOT = Path(__file__).resolve().parents[3]
GOLDEN_AOI_DIR = ROOT / "tests" / "fixtures" / "golden_aois"
_WORKSPACE_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
_USER_ID = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")


@dataclass(frozen=True)
class _GenericAoiCase:
    county: str
    geometry_file: str
    expected_domains: frozenset[str]


_GENERIC_AOI_CASES = (
    _GenericAoiCase(
        county="buncombe",
        geometry_file="bun_slope.geojson",
        expected_domains=frozenset({"access", "buildability", "flood", "parcels", "terrain"}),
    ),
    _GenericAoiCase(
        county="chatham",
        geometry_file="cha_rural_use.geojson",
        expected_domains=frozenset({"access", "flood", "parcels"}),
    ),
    _GenericAoiCase(
        county="brunswick",
        geometry_file="bru_coastal_flood.geojson",
        expected_domains=frozenset({"flood", "parcels", "soils", "wetlands"}),
    ),
)


def _load_geometry(filename: str) -> dict[str, object]:
    data = json.loads((GOLDEN_AOI_DIR / filename).read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    if data.get("type") == "Feature":
        geometry = data["geometry"]
        assert isinstance(geometry, dict)
        return geometry
    return data


@pytest.mark.parametrize("case", _GENERIC_AOI_CASES, ids=lambda case: case.county)
def test_supported_generic_aoi_creates_approved_selected_county_report(
    case: _GenericAoiCase,
) -> None:
    services = create_api_services()
    area_id = uuid4()
    area = services.area_service.create(
        AreaContract(
            area_id=area_id,
            workspace_id=_WORKSPACE_ID,
            created_by=_USER_ID,
            label=f"operator-upload-{case.county}",
            geom_geojson=_load_geometry(case.geometry_file),
            geom_source=f"operator-upload://{case.geometry_file}",
        )
    )

    result = create_supported_aoi_report(
        services,
        area_id=area.area_id,
        intent_code=IntentCode.RURAL_LAND_PURCHASE,
        reviewer_id="generic-aoi-test",
        reason="generic selected-county AOI fixture approval",
        workspace_id=_WORKSPACE_ID,
        requested_by=_USER_ID,
    )

    assert result.support_profile.county == case.county
    assert set(result.support_profile.connector_fixture_files) == case.expected_domains
    assert result.report_run.area_id == area.area_id
    assert result.report_run.workspace_id == _WORKSPACE_ID
    assert result.report_run.requested_by == _USER_ID
    assert result.report_run.status == JobStatus.SUCCEEDED
    assert result.report_run.review_status == ReportReviewStatus.APPROVED
    assert result.report_run.reviewed_by == "generic-aoi-test"
    assert result.evidence_created_count >= len(case.expected_domains)

    stored_area = services.area_service.get(area.area_id)
    assert stored_area is not None
    assert stored_area.label == f"operator-upload-{case.county}"
    assert stored_area.geom_source == f"operator-upload://{case.geometry_file}"

    report_domains = {
        evidence.domain
        for evidence in result.report_run.evidence
        if not evidence.is_source_failure
    }
    assert case.expected_domains <= report_domains
    source_names = result.report_run.source_manifest["source_names"]
    assert isinstance(source_names, list)
    assert "Selected County Private MVP Fixtures" in source_names

    queue_items = services.connector_review_queue.list_connector_runs(
        workspace_id=_WORKSPACE_ID,
        limit=100,
    )
    assert len(queue_items) == result.connector_count
    assert {item.workspace_id for item in queue_items} == {_WORKSPACE_ID}
    assert {item.payload["requested_by"] for item in queue_items} == {str(_USER_ID)}


def test_supported_generic_aoi_fails_closed_outside_selected_counties() -> None:
    services = create_api_services()
    area = services.area_service.create(
        AreaContract(
            workspace_id=_WORKSPACE_ID,
            created_by=_USER_ID,
            label="operator-upload-outside-selected-counties",
            geom_geojson={
                "type": "Polygon",
                "coordinates": [
                    [
                        [-80.05, 36.25],
                        [-80.04, 36.25],
                        [-80.04, 36.26],
                        [-80.05, 36.26],
                        [-80.05, 36.25],
                    ]
                ],
            },
            geom_source="operator-upload://outside-selected-counties.geojson",
        )
    )

    with pytest.raises(
        UnsupportedSelectedCountyAoiError,
        match="outside selected NC counties",
    ):
        create_supported_aoi_report(
            services,
            area_id=area.area_id,
            intent_code=IntentCode.RURAL_LAND_PURCHASE,
            reviewer_id="generic-aoi-test",
            workspace_id=_WORKSPACE_ID,
            requested_by=_USER_ID,
        )


def test_supported_generic_aoi_matches_db_normalized_multipolygon() -> None:
    services = create_api_services()
    polygon = _load_geometry("bun_slope.geojson")
    area = services.area_service.create(
        AreaContract(
            workspace_id=_WORKSPACE_ID,
            created_by=_USER_ID,
            label="operator-upload-buncombe-db-shape",
            geom_geojson={
                "type": "MultiPolygon",
                "coordinates": [polygon["coordinates"]],
            },
            geom_source="operator-upload://bun_slope-db-normalized.geojson",
        )
    )

    result = create_supported_aoi_report(
        services,
        area_id=area.area_id,
        intent_code=IntentCode.RURAL_LAND_PURCHASE,
        reviewer_id="generic-aoi-test",
        workspace_id=_WORKSPACE_ID,
        requested_by=_USER_ID,
    )

    assert result.support_profile.county == "buncombe"
    assert result.report_run.area_id == area.area_id
    assert result.evidence_created_count > 0
