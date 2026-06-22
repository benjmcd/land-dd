from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from app.api.dependencies import ApiServices, create_api_services
from app.domain.area_contracts import AreaContract
from app.domain.enums import IntentCode, JobStatus, ReportReviewStatus
from app.operator_cases import (
    SupportedAoiAreaNotFoundError,
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


# ---------------------------------------------------------------------------
# Finding 1 — Cross-workspace area_id must not leak existence (IDOR / enumeration)
# ---------------------------------------------------------------------------


def test_cross_workspace_area_id_yields_not_found_not_existence_disclosure() -> None:
    """A caller must receive SupportedAoiAreaNotFoundError (→ 404) when the
    area_id exists but belongs to a different workspace.  The error must be
    indistinguishable from "area does not exist" — same exception type, same
    opaque message.
    """
    # Register the area in workspace A.
    services = create_api_services()
    other_workspace = UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc")
    area = services.area_service.create(
        AreaContract(
            workspace_id=other_workspace,
            created_by=_USER_ID,
            label="operator-upload-buncombe-other-ws",
            geom_geojson=_load_geometry("bun_slope.geojson"),
            geom_source="operator-upload://bun_slope.geojson",
        )
    )

    # Caller from workspace B supplies the area_id that belongs to workspace A.
    caller_workspace = UUID("dddddddd-dddd-4ddd-8ddd-dddddddddddd")
    with pytest.raises(SupportedAoiAreaNotFoundError, match="area not found"):
        create_supported_aoi_report(
            services,
            area_id=area.area_id,
            intent_code=IntentCode.RURAL_LAND_PURCHASE,
            reviewer_id="generic-aoi-test",
            workspace_id=caller_workspace,
            requested_by=_USER_ID,
        )


def test_missing_area_id_yields_same_not_found_error_as_cross_workspace() -> None:
    """A completely absent area_id must raise SupportedAoiAreaNotFoundError with
    the same opaque message — confirming no distinguishable difference between
    'not found' and 'wrong workspace'.
    """
    services = create_api_services()
    nonexistent_id = uuid4()

    with pytest.raises(SupportedAoiAreaNotFoundError, match="area not found"):
        create_supported_aoi_report(
            services,
            area_id=nonexistent_id,
            intent_code=IntentCode.RURAL_LAND_PURCHASE,
            reviewer_id="generic-aoi-test",
            workspace_id=_WORKSPACE_ID,
            requested_by=_USER_ID,
        )


# ---------------------------------------------------------------------------
# Finding 2 — Retry idempotency: _ingest_connector_fixtures must not crash when
#              queue items are already in a terminal (SUCCEEDED) state
# ---------------------------------------------------------------------------


def test_ingest_connector_fixtures_is_idempotent_when_queue_items_already_approved() -> None:
    """_ingest_connector_fixtures must skip the approve call when the connector
    review queue item is already in a terminal state (SUCCEEDED from a prior run).
    Before the fix, calling approve_for_connector_qa on a SUCCEEDED item raised
    "connector review queue job cannot be approved" which would surface as 422.

    This tests the fix at the service layer by calling _ingest_connector_fixtures
    twice with identical deterministic IDs — the same path that a route-level retry
    would trigger if the existing-evidence guard were absent.
    """
    from app.connectors.result import ConnectorResult as _CR
    from app.operator_cases import (
        _connector_result_for_supported_aoi,
        _ensure_fixture_provenance,
        _ingest_connector_fixtures,
    )

    services = create_api_services()
    area = services.area_service.create(
        AreaContract(
            workspace_id=_WORKSPACE_ID,
            created_by=_USER_ID,
            label="operator-upload-buncombe-f2-idempotent",
            geom_geojson=_load_geometry("bun_slope.geojson"),
            geom_source="operator-upload://bun_slope.geojson",
        )
    )

    # Use only one connector domain so the test is fast.
    connector_fixture_files = {"access": "bun-slope-access.json"}

    # _ingest_connector_fixtures requires source/dataset provenance to be set up.
    _ensure_fixture_provenance(
        services,
        fixture_scope="private_mvp_fixture",
        connector_fixture_files=connector_fixture_files,
        manifest={
            "support_mode": "generic_supported_aoi",
            "county": "buncombe",
            "fixture_scope": "private_mvp_fixture",
            "connector_domains": ["access"],
        },
    )

    def _factory(result: _CR) -> _CR:
        return _connector_result_for_supported_aoi(
            result,
            area_id=area.area_id,
            workspace_id=_WORKSPACE_ID,
        )

    # First ingest: creates queue items and approves them.
    _ingest_connector_fixtures(
        services,
        connector_fixture_files=connector_fixture_files,
        area_id=area.area_id,
        reviewer_id="f2-test",
        reason="idempotency test first pass",
        workspace_id=_WORKSPACE_ID,
        requested_by=_USER_ID,
        connector_result_factory=_factory,
    )

    # Verify the item is already SUCCEEDED.
    queue_items = services.connector_review_queue.list_connector_runs(
        workspace_id=_WORKSPACE_ID, limit=10
    )
    assert len(queue_items) == 1
    assert queue_items[0].status == JobStatus.SUCCEEDED

    # Second ingest with the same deterministic IDs: must NOT raise.
    _ingest_connector_fixtures(
        services,
        connector_fixture_files=connector_fixture_files,
        area_id=area.area_id,
        reviewer_id="f2-test",
        reason="idempotency test second pass",
        workspace_id=_WORKSPACE_ID,
        requested_by=_USER_ID,
        connector_result_factory=_factory,
    )

    # Queue still has exactly one item (idempotent — no duplicate created).
    queue_items_after = services.connector_review_queue.list_connector_runs(
        workspace_id=_WORKSPACE_ID, limit=10
    )
    assert len(queue_items_after) == 1
    assert queue_items_after[0].status == JobStatus.SUCCEEDED


# ---------------------------------------------------------------------------
# Finding 3 (narrowed) — F3 guard distinguishes foreign vs. fixture evidence
# ---------------------------------------------------------------------------

_FOREIGN_SOURCE_ID = UUID("99999999-9999-4999-8999-999999999999")


def _register_foreign_source(services: ApiServices) -> None:
    """Register a foreign (non-fixture) source that passes production-use checks.

    Used to inject foreign evidence onto an area to verify the F3 guard fires.
    """
    from app.domain.source_contracts import SourceContract as _SC

    services.source_service.get_or_register_by_id(
        _SC(
            source_id=_FOREIGN_SOURCE_ID,
            name="Foreign Live Source (F3 test)",
            organization="Test Org",
            domain="access",
            review_status="approved",
            license_status="yes",
            commercial_use_status="yes",
            redistribution_status="yes",
            cache_allowed="yes",
            export_allowed="yes",
            raw_data_allowed="yes",
            ai_use_allowed="yes",
        )
    )


def test_area_with_foreign_evidence_is_rejected_fail_closed() -> None:
    """The F3 guard must fire when the area has evidence from a source OTHER than
    the fixture source — foreign (live/manual) evidence would produce a mislabeled
    fixture_only report.  The guard must not fire for fixture-source evidence.
    """
    from app.domain.enums import ConfidenceBand, EvidenceType
    from app.domain.evidence_contracts import EvidenceContract as _EC

    services = create_api_services()
    _register_foreign_source(services)

    area = services.area_service.create(
        AreaContract(
            workspace_id=_WORKSPACE_ID,
            created_by=_USER_ID,
            label="operator-upload-buncombe-foreign-evidence",
            geom_geojson=_load_geometry("bun_slope.geojson"),
            geom_source="operator-upload://bun_slope.geojson",
        )
    )

    # Plant foreign evidence directly via create_observation (source is registered above).
    services.evidence_service.create_observation(
        _EC(
            area_id=area.area_id,
            evidence_type=EvidenceType.SOURCE_OBSERVATION,
            evidence_code="ACCESS_ROAD_PRESENT",
            domain="access",
            observation="Foreign live source evidence",
            observed_value={"status": "present"},
            source_id=_FOREIGN_SOURCE_ID,
            method_code="foreign_live_connector_v1",
            confidence=ConfidenceBand.HIGH,
        )
    )

    # The F3 guard must reject: foreign evidence present.
    with pytest.raises(ValueError, match="non-fixture source"):
        create_supported_aoi_report(
            services,
            area_id=area.area_id,
            intent_code=IntentCode.RURAL_LAND_PURCHASE,
            reviewer_id="generic-aoi-test",
            workspace_id=_WORKSPACE_ID,
            requested_by=_USER_ID,
        )


def test_same_fixture_retry_succeeds_idempotently() -> None:
    """A second identical call to create_supported_aoi_report on the same area
    (after run 1 left fixture evidence) must succeed and return a valid approved
    report — NOT raise 422.  This is the route-level retry path:

    - F3 (narrowed) sees only fixture-source evidence → does NOT reject.
    - _ingest_connector_fixtures is idempotent (deterministic IDs → returns existing).
    - F2 (SUCCEEDED-only) skips re-approval for already-SUCCEEDED queue items.
    - create_report_run + approve produce a fresh approved report.

    evidence_count on the retry reflects the fixture evidence (unchanged pool).
    """
    services = create_api_services()
    area = services.area_service.create(
        AreaContract(
            workspace_id=_WORKSPACE_ID,
            created_by=_USER_ID,
            label="operator-upload-buncombe-retry-idempotent",
            geom_geojson=_load_geometry("bun_slope.geojson"),
            geom_source="operator-upload://bun_slope.geojson",
        )
    )

    # RUN 1 — must succeed.
    first = create_supported_aoi_report(
        services,
        area_id=area.area_id,
        intent_code=IntentCode.RURAL_LAND_PURCHASE,
        reviewer_id="generic-aoi-test",
        workspace_id=_WORKSPACE_ID,
        requested_by=_USER_ID,
    )
    assert first.evidence_created_count > 0
    assert first.report_run.review_status == ReportReviewStatus.APPROVED

    # RUN 2 (identical) — must also succeed, NOT raise 422.
    second = create_supported_aoi_report(
        services,
        area_id=area.area_id,
        intent_code=IntentCode.RURAL_LAND_PURCHASE,
        reviewer_id="generic-aoi-test",
        workspace_id=_WORKSPACE_ID,
        requested_by=_USER_ID,
    )
    assert second.report_run.review_status == ReportReviewStatus.APPROVED
    # evidence_count reflects the fixture evidence pool (idempotent ingest — same items).
    assert second.evidence_created_count >= 0


# ---------------------------------------------------------------------------
# Finding 4 — intent_code must match the matched fixture profile's intent
# ---------------------------------------------------------------------------


def test_unsupported_intent_code_is_rejected_with_validation_error() -> None:
    """Supplying an intent_code that differs from the profile's manifest intent
    must be rejected with a ValueError — not silently approved under the wrong
    intent.
    """
    services = create_api_services()
    area = services.area_service.create(
        AreaContract(
            workspace_id=_WORKSPACE_ID,
            created_by=_USER_ID,
            label="operator-upload-buncombe-wrong-intent",
            geom_geojson=_load_geometry("bun_slope.geojson"),
            geom_source="operator-upload://bun_slope.geojson",
        )
    )

    # All buncombe profiles have intent "rural_land_purchase"; "solar" is wrong.
    with pytest.raises(ValueError, match="intent_code.*not supported"):
        create_supported_aoi_report(
            services,
            area_id=area.area_id,
            intent_code=IntentCode.SOLAR,
            reviewer_id="generic-aoi-test",
            workspace_id=_WORKSPACE_ID,
            requested_by=_USER_ID,
        )
