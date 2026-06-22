from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from importlib.resources import as_file, files
from types import MappingProxyType
from typing import Any, cast
from uuid import NAMESPACE_URL, UUID, uuid5

from app.api.dependencies import ApiServices
from app.connectors import (
    ConnectorEvidenceIngestionAdapter,
    ConnectorRetrievalProvenanceAdapter,
    ConnectorReviewDisposition,
    FixtureConnectorIngestWorkflowResult,
    StaticAccessFixtureConnector,
    StaticBuildabilityFixtureConnector,
    StaticFloodFixtureConnector,
    StaticParcelFixtureConnector,
    StaticSoilsFixtureConnector,
    StaticTerrainFixtureConnector,
    StaticWetlandsFixtureConnector,
    StaticZoningFixtureConnector,
    build_connector_review_handoff,
    build_connector_run_review_packet,
    build_connector_run_review_status,
    evaluate_access_fixture_quality,
    evaluate_buildability_fixture_quality,
    evaluate_flood_fixture_quality,
    evaluate_parcel_fixture_quality,
    evaluate_soils_fixture_quality,
    evaluate_terrain_fixture_quality,
    evaluate_wetlands_fixture_quality,
    evaluate_zoning_fixture_quality,
)
from app.connectors.fixture_quality import ConnectorFixtureQualityProfile
from app.connectors.flood_fixture import FixtureConnectorProtocol
from app.connectors.result import ConnectorResult
from app.connectors.retrieval_provenance import SourceRetrievalProvenancePort
from app.domain.area_contracts import AreaContract
from app.domain.enums import IntentCode, JobStatus
from app.domain.evidence_contracts import EvidenceContract
from app.domain.report_contracts import ReportRunContract
from app.domain.source_contracts import (
    SourceContract,
    SourceDatasetContract,
    SourceDatasetVersionContract,
    SourceRetrievalRunContract,
)

_SOURCE_ID = UUID("55555555-5555-4555-8555-555555555555")
_DATASET_ID = UUID("11111111-2222-4333-8444-555555555555")
_DATASET_VERSION_ID = UUID("22222222-2222-4222-8222-222222222222")
# The report-service writes sentinel/not-evaluated evidence under this source ID
# during create_report_run (for domains that were not evaluated by any connector).
# This is an internal infrastructure source, not a live or manual one, so it is
# part of the fixture-only report contract and must not trigger the F3 foreign-
# evidence guard on retry.
_NOT_EVALUATED_SENTINEL_SOURCE_ID = UUID("00000000-0000-4000-8000-0000000007d0")

# All source IDs that are written as part of the fixture-only route's normal
# operation (connector fixtures + report-service sentinels).  Evidence from any
# other source is considered "foreign" and causes F3 to fail closed.
_FIXTURE_ROUTE_SOURCE_IDS: frozenset[UUID] = frozenset(
    {_SOURCE_ID, _NOT_EVALUATED_SENTINEL_SOURCE_ID}
)

_CONNECTORS: dict[
    str,
    tuple[
        Callable[[], FixtureConnectorProtocol],
        Callable[[ConnectorResult], ConnectorFixtureQualityProfile],
    ],
] = {
    "access": (StaticAccessFixtureConnector, evaluate_access_fixture_quality),
    "buildability": (StaticBuildabilityFixtureConnector, evaluate_buildability_fixture_quality),
    "flood": (StaticFloodFixtureConnector, evaluate_flood_fixture_quality),
    "parcels": (StaticParcelFixtureConnector, evaluate_parcel_fixture_quality),
    "soils": (StaticSoilsFixtureConnector, evaluate_soils_fixture_quality),
    "terrain": (StaticTerrainFixtureConnector, evaluate_terrain_fixture_quality),
    "wetlands": (StaticWetlandsFixtureConnector, evaluate_wetlands_fixture_quality),
    "zoning": (StaticZoningFixtureConnector, evaluate_zoning_fixture_quality),
}
_SELECTED_COUNTY_BOUNDS: Mapping[str, tuple[float, float, float, float]] = MappingProxyType(
    {
        "buncombe": (-83.05, 35.28, -82.15, 35.79),
        "chatham": (-79.44, 35.53, -78.89, 35.89),
        "brunswick": (-78.65, 33.88, -77.93, 34.35),
    }
)


@dataclass(frozen=True)
class SelectedCountyCase:
    case_id: str
    county: str
    state: str
    intent: str
    description: str
    fixture_scope: str
    fixture_language: str
    geometry_file: str
    connector_fixture_files: Mapping[str, str]
    expected_connector_workflow_domains: tuple[str, ...]
    expected_not_evaluated_domains: tuple[str, ...]
    expected_unknowns: tuple[str, ...]


@dataclass(frozen=True)
class SelectedCountyReportResult:
    case: SelectedCountyCase
    report_run: ReportRunContract
    evidence_created_count: int
    connector_count: int

    @property
    def report_run_id(self) -> UUID:
        return self.report_run.report_run_id

    @property
    def status(self) -> object:
        return self.report_run.status

    @property
    def review_status(self) -> object:
        return self.report_run.review_status

    @property
    def evidence_count(self) -> int:
        return self.evidence_created_count


class UnsupportedSelectedCountyCaseError(ValueError):
    """Raised when a private-MVP operator case is not in the selected package."""


@dataclass(frozen=True)
class SelectedCountyAoiSupportProfile:
    county: str
    state: str
    intent: str
    description: str
    fixture_scope: str
    fixture_language: str
    connector_fixture_files: Mapping[str, str]
    expected_connector_workflow_domains: tuple[str, ...]
    expected_not_evaluated_domains: tuple[str, ...]
    expected_unknowns: tuple[str, ...]


@dataclass(frozen=True)
class SupportedSelectedCountyAoiReportResult:
    support_profile: SelectedCountyAoiSupportProfile
    report_run: ReportRunContract
    evidence_created_count: int
    connector_count: int

    @property
    def report_run_id(self) -> UUID:
        return self.report_run.report_run_id

    @property
    def status(self) -> object:
        return self.report_run.status

    @property
    def review_status(self) -> object:
        return self.report_run.review_status

    @property
    def evidence_count(self) -> int:
        return self.evidence_created_count


class UnsupportedSelectedCountyAoiError(ValueError):
    """Raised when a generic AOI cannot be mapped to selected-county support scope."""


class SupportedAoiAreaNotFoundError(UnsupportedSelectedCountyAoiError):
    """Raised when the caller-supplied area_id cannot be resolved for this workspace.

    Intentionally opaque: both "does not exist" and "exists in another workspace"
    raise this with the same message so callers cannot distinguish the two cases
    (prevents cross-workspace UUID enumeration / IDOR).  The API layer maps this
    to 404 rather than 422.
    """


# Internal alias so in-module raise sites are concise.
_AoiNotFoundError = SupportedAoiAreaNotFoundError


@dataclass(frozen=True)
class _SelectedCountyConnectorResult:
    retrieval_run: SourceRetrievalRunContract
    evidence_inputs: tuple[EvidenceContract, ...]


def list_selected_county_cases() -> tuple[SelectedCountyCase, ...]:
    return _load_cases()


def get_selected_county_case(case_id: str) -> SelectedCountyCase | None:
    normalized = case_id.strip()
    return next(
        (case for case in _load_cases() if case.case_id == normalized),
        None,
    )


def create_supported_aoi_report(
    services: ApiServices,
    *,
    area_id: UUID,
    intent_code: IntentCode,
    reviewer_id: str = "operator-private-mvp",
    reason: str = "generic selected-county private MVP fixture approval",
    workspace_id: UUID | None = None,
    requested_by: UUID | None = None,
) -> SupportedSelectedCountyAoiReportResult:
    area = services.area_service.get(area_id)
    if area is None or (workspace_id is not None and area.workspace_id != workspace_id):
        # Return the same indistinguishable error for both "does not exist" and
        # "exists in a different workspace" to prevent cross-workspace UUID enumeration.
        raise _AoiNotFoundError("area not found")

    county = _classify_selected_county_area(area)
    if county is None:
        raise UnsupportedSelectedCountyAoiError(
            "generic AOI is outside selected NC counties "
            "(Buncombe, Chatham, Brunswick)",
        )
    profile = _support_profile_for_area(area, county)
    if profile is None:
        raise UnsupportedSelectedCountyAoiError(
            "generic AOI is inside selected county bounds but does not match a "
            "recorded generic AOI fixture profile",
        )

    # Finding 4: enforce that the caller's intent_code matches the profile's intent.
    # The fixture set was built for a specific intent; approving it under a different
    # intent would produce a mislabeled report.
    if intent_code.value != profile.intent:
        raise ValueError(
            f"intent_code '{intent_code.value}' is not supported for this AOI; "
            f"supported intent for this profile is '{profile.intent}'",
        )

    # Finding 3 (narrowed): fail closed only when the area carries evidence from a
    # source OTHER than this route's fixture source.  Foreign (live/manual) evidence
    # would produce a mislabeled fixture_only report, so we reject.  Evidence that
    # is already from this fixture source means this is a legitimate retry — we
    # proceed; _ingest_connector_fixtures is idempotent and F2 skips re-approval for
    # already-SUCCEEDED queue items, so the route produces a fresh approved report.
    foreign_evidence = [
        e
        for e in services.evidence_service.list_by_area(area.area_id)
        if e.source_id not in _FIXTURE_ROUTE_SOURCE_IDS
    ]
    if foreign_evidence:
        raise ValueError(
            "area already has existing evidence from a non-fixture source; "
            "fixture-only report cannot be created on an area with prior evidence",
        )

    _ensure_fixture_provenance(
        services,
        fixture_scope=profile.fixture_scope,
        connector_fixture_files=profile.connector_fixture_files,
        manifest={
            "support_mode": "generic_supported_aoi",
            "county": profile.county,
            "fixture_scope": profile.fixture_scope,
            "connector_domains": sorted(profile.connector_fixture_files),
        },
    )
    evidence_created_count = _ingest_connector_fixtures(
        services,
        connector_fixture_files=profile.connector_fixture_files,
        area_id=area.area_id,
        reviewer_id=reviewer_id,
        reason=reason,
        workspace_id=workspace_id,
        requested_by=requested_by,
        connector_result_factory=lambda result: _connector_result_for_supported_aoi(
            result,
            area_id=area.area_id,
            workspace_id=workspace_id,
        ),
    )

    report_run = services.report_service.create_report_run(
        area_id=area.area_id,
        intent_code=intent_code,
        workspace_id=workspace_id,
        requested_by=requested_by,
    )
    approved = services.report_service.approve_report_run(
        report_run.report_run_id,
        reviewer_id=reviewer_id,
        reason=reason,
    )
    if approved is None:
        raise ValueError("generic selected-county AOI report approval failed")

    return SupportedSelectedCountyAoiReportResult(
        support_profile=profile,
        report_run=approved,
        evidence_created_count=evidence_created_count,
        connector_count=len(profile.connector_fixture_files),
    )


def create_selected_county_report(
    services: ApiServices,
    case_id: str,
    reviewer_id: str = "operator-private-mvp",
    reason: str = "selected-county private MVP fixture approval",
    workspace_id: UUID | None = None,
    requested_by: UUID | None = None,
) -> SelectedCountyReportResult:
    case = get_selected_county_case(case_id)
    if case is None:
        raise UnsupportedSelectedCountyCaseError(
            f"Unsupported selected-county private-MVP case: {case_id}",
        )

    area_id = _area_id_for(case, workspace_id=workspace_id)
    _ensure_area(
        services,
        case,
        area_id,
        workspace_id=workspace_id,
        requested_by=requested_by,
    )

    _ensure_fixture_provenance(
        services,
        fixture_scope=case.fixture_scope,
        connector_fixture_files=case.connector_fixture_files,
        manifest={
            "case_id": case.case_id,
            "fixture_scope": case.fixture_scope,
            "connector_domains": sorted(case.connector_fixture_files),
        },
    )
    evidence_created_count = _ingest_connector_fixtures(
        services,
        connector_fixture_files=case.connector_fixture_files,
        area_id=area_id,
        reviewer_id=reviewer_id,
        reason=reason,
        workspace_id=workspace_id,
        requested_by=requested_by,
        connector_result_factory=lambda result: _connector_result_for_area(
            result,
            area_id,
            workspace_id=workspace_id,
        ),
    )

    report_run = services.report_service.create_report_run(
        area_id=area_id,
        intent_code=IntentCode(case.intent),
        workspace_id=workspace_id,
        requested_by=requested_by,
    )
    approved = services.report_service.approve_report_run(
        report_run.report_run_id,
        reviewer_id=reviewer_id,
        reason=reason,
    )
    if approved is None:
        raise ValueError("selected-county private-MVP report approval failed")

    return SelectedCountyReportResult(
        case=case,
        report_run=approved,
        evidence_created_count=evidence_created_count,
        connector_count=len(case.connector_fixture_files),
    )


def _load_cases() -> tuple[SelectedCountyCase, ...]:
    manifest = json.loads(_resource_root().joinpath("manifest.json").read_text("utf-8"))
    return tuple(_case_from_manifest(item) for item in manifest["cases"])


def _case_from_manifest(item: dict[str, Any]) -> SelectedCountyCase:
    return SelectedCountyCase(
        case_id=item["case_id"],
        county=item["county"],
        state=item["state"],
        intent=item["intent"],
        description=item["description"],
        fixture_scope=item["fixture_scope"],
        fixture_language=item["fixture_language"],
        geometry_file=item["geometry_file"],
        connector_fixture_files=MappingProxyType(dict(item["connector_fixture_files"])),
        expected_connector_workflow_domains=tuple(item["expected_connector_workflow_domains"]),
        expected_not_evaluated_domains=tuple(item["expected_not_evaluated_domains"]),
        expected_unknowns=tuple(item["expected_unknowns"]),
    )


def _support_profile_for_area(
    area: AreaContract,
    county: str,
) -> SelectedCountyAoiSupportProfile | None:
    case = next(
        (
            candidate
            for candidate in _load_cases()
            if candidate.county == county
            and _geometries_match(area.geom_geojson, _case_geometry(candidate))
        ),
        None,
    )
    if case is None:
        return None
    return SelectedCountyAoiSupportProfile(
        county=case.county,
        state=case.state,
        intent=case.intent,
        description=f"Generic supported AOI fixture profile for {case.county} County",
        fixture_scope=case.fixture_scope,
        fixture_language=case.fixture_language,
        connector_fixture_files=MappingProxyType(dict(case.connector_fixture_files)),
        expected_connector_workflow_domains=case.expected_connector_workflow_domains,
        expected_not_evaluated_domains=case.expected_not_evaluated_domains,
        expected_unknowns=case.expected_unknowns,
    )


def _case_geometry(case: SelectedCountyCase) -> dict[str, object]:
    raw = _load_json_resource(case.geometry_file)
    if raw.get("type") == "Feature":
        geometry = raw["geometry"]
        if isinstance(geometry, dict):
            return geometry
        raise ValueError(f"selected-county geometry is invalid: {case.geometry_file}")
    return raw


def _geometries_match(
    left: Mapping[str, object],
    right: Mapping[str, object],
) -> bool:
    return _canonical_geometry(_profile_match_geometry(left)) == _canonical_geometry(
        _profile_match_geometry(right)
    )


def _canonical_geometry(geometry: Mapping[str, object]) -> str:
    return json.dumps(geometry, sort_keys=True, separators=(",", ":"))


def _profile_match_geometry(geometry: Mapping[str, object]) -> Mapping[str, object]:
    if geometry.get("type") != "MultiPolygon":
        return geometry
    coordinates = geometry.get("coordinates")
    if (
        isinstance(coordinates, list)
        and len(coordinates) == 1
        and isinstance(coordinates[0], list)
    ):
        return {"type": "Polygon", "coordinates": coordinates[0]}
    return geometry


def _classify_selected_county_area(area: AreaContract) -> str | None:
    positions = _collect_positions(area.geom_geojson)
    if not positions:
        return None
    cx = sum(position[0] for position in positions) / len(positions)
    cy = sum(position[1] for position in positions) / len(positions)
    for county, bounds in _SELECTED_COUNTY_BOUNDS.items():
        xmin, ymin, xmax, ymax = bounds
        if xmin <= cx <= xmax and ymin <= cy <= ymax:
            return county
    return None


def _collect_positions(geometry: Mapping[str, object]) -> list[tuple[float, float]]:
    positions: list[tuple[float, float]] = []
    _walk_coordinates(geometry.get("coordinates"), positions)
    return positions


def _walk_coordinates(value: object, positions: list[tuple[float, float]]) -> None:
    if not isinstance(value, list):
        return
    if len(value) >= 2 and all(isinstance(item, int | float) for item in value[:2]):
        positions.append((float(value[0]), float(value[1])))
        return
    for item in value:
        _walk_coordinates(item, positions)


def _ingest_connector_fixtures(
    services: ApiServices,
    *,
    connector_fixture_files: Mapping[str, str],
    area_id: UUID,
    reviewer_id: str,
    reason: str,
    workspace_id: UUID | None,
    requested_by: UUID | None,
    connector_result_factory: Callable[[ConnectorResult], ConnectorResult],
) -> int:
    evidence_created_count = 0
    for domain, fixture_file in connector_fixture_files.items():
        connector_factory, quality_evaluator = _connector_for_domain(domain)
        with as_file(_resource_root().joinpath(fixture_file)) as fixture_path:
            raw_result = connector_factory().load_fixture(fixture_path)

        connector_result = connector_result_factory(raw_result)
        quality_profile = quality_evaluator(connector_result)
        if quality_profile.blocking_issue_count:
            issue_codes = ", ".join(issue.code.value for issue in quality_profile.issues)
            raise ValueError(f"selected-county fixture quality gate failed: {issue_codes}")
        workflow_result = FixtureConnectorIngestWorkflowResult(
            connector_result=connector_result,
            retrieval_provenance=ConnectorRetrievalProvenanceAdapter(
                cast(
                    SourceRetrievalProvenancePort,
                    services.source_provenance_service,
                ),
            ).record(connector_result),
            evidence_ingestion=ConnectorEvidenceIngestionAdapter(
                services.evidence_service,
            ).ingest(connector_result),
        )
        packet = build_connector_run_review_packet(workflow_result)
        handoff = build_connector_review_handoff(packet)
        review_status = build_connector_run_review_status(handoff, quality_profile)
        services.connector_review_statuses[packet.ingest_run_id] = review_status
        queued = services.connector_review_queue.enqueue_review_status(
            review_status,
            workspace_id=workspace_id,
            requested_by=requested_by,
        )
        # Finding 2: on a retry the queue item already exists and may already be
        # SUCCEEDED.  Calling approve_for_connector_qa on a SUCCEEDED item raises
        # "cannot be approved".  Skip the approve call only when the item has already
        # SUCCEEDED — its approval is still valid.  For FAILED/CANCELLED items we do
        # NOT skip: those are error states and the approve call should surface its
        # error rather than silently yielding an "approved" report over a failed item.
        _already_succeeded = queued.status == JobStatus.SUCCEEDED
        if (
            handoff.disposition == ConnectorReviewDisposition.READY_FOR_CONNECTOR_QA
            and not _already_succeeded
        ):
            services.connector_review_queue.approve_for_connector_qa(
                queued.job_id,
                reviewer_id=reviewer_id,
                reason=reason,
            )
        evidence_created_count += len(workflow_result.evidence_ingestion.created_evidence)
    return evidence_created_count


def _ensure_fixture_provenance(
    services: ApiServices,
    *,
    fixture_scope: str,
    connector_fixture_files: Mapping[str, str],
    manifest: dict[str, object],
) -> None:
    if services.source_service.get(_SOURCE_ID) is None:
        services.source_service.register(
            SourceContract(
                source_id=_SOURCE_ID,
                name="Selected County Private MVP Fixtures",
                organization="Land DD fixture package",
                source_type="packaged_fixture",
                domain="private_mvp_fixture",
                geographic_scope="NC selected-county private MVP fixture cases",
                license_status="approved",
                commercial_use_status="approved",
                redistribution_status="approved",
                cache_allowed="approved",
                export_allowed="approved",
                raw_data_allowed="approved",
                ai_use_allowed="approved",
                review_status="approved",
                notes=(
                    "Packaged fixture-only source for selected-county private MVP "
                    "operator cases; not live county coverage."
                ),
                metadata={"fixture_scope": fixture_scope},
            ),
        )

    dataset = SourceDatasetContract(
        dataset_id=_DATASET_ID,
        source_id=_SOURCE_ID,
        dataset_name="Selected County Private MVP Fixture Dataset",
        dataset_code="selected-county-private-mvp",
        domain="private_mvp_fixture",
        geometry_type="mixed",
        legal_caveat="Fixture/private-MVP data only; not live county coverage.",
        metadata={"case_count": len(_load_cases())},
    )
    services.source_provenance_service.ensure_dataset(dataset)
    services.source_provenance_service.ensure_dataset_version(
        SourceDatasetVersionContract(
            dataset_version_id=_DATASET_VERSION_ID,
            dataset_id=_DATASET_ID,
            version_label="fixture-2026-06-14",
            storage_uri="package://app.operator_cases/manifest.json",
            manifest={
                "manifest_file": "manifest.json",
                **manifest,
            },
            is_current=True,
            notes="Packaged selected-county private MVP fixture version.",
        ),
    )


def _ensure_area(
    services: ApiServices,
    case: SelectedCountyCase,
    area_id: UUID,
    *,
    workspace_id: UUID | None = None,
    requested_by: UUID | None = None,
) -> None:
    existing = services.area_service.get(area_id)
    if existing is not None:
        if workspace_id is not None and existing.workspace_id != workspace_id:
            raise ValueError(
                "selected-county area belongs to a different workspace",
            )
        return
    raw = _load_json_resource(case.geometry_file)
    geometry = raw["geometry"] if raw.get("type") == "Feature" else raw
    services.area_service.create(
        AreaContract(
            area_id=area_id,
            workspace_id=workspace_id,
            created_by=requested_by,
            label=f"selected-county-private-mvp-{case.case_id}",
            geom_geojson=geometry,
            geom_source=f"package://app.operator_cases/{case.geometry_file}",
        ),
    )


def _connector_for_domain(
    domain: str,
) -> tuple[
    Callable[[], FixtureConnectorProtocol],
    Callable[[ConnectorResult], ConnectorFixtureQualityProfile],
]:
    try:
        return _CONNECTORS[domain]
    except KeyError as exc:
        raise ValueError(f"Unsupported selected-county connector domain: {domain}") from exc


def _load_json_resource(resource_name: str) -> dict[str, Any]:
    data = json.loads(_resource_root().joinpath(resource_name).read_text("utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"selected-county resource is not a JSON object: {resource_name}")
    return data


def _area_id_for(case: SelectedCountyCase, workspace_id: UUID | None = None) -> UUID:
    if workspace_id is None:
        return uuid5(NAMESPACE_URL, f"land-dd:selected-county:{case.case_id}")
    return uuid5(
        NAMESPACE_URL,
        f"land-dd:selected-county:{workspace_id}:{case.case_id}",
    )


def _connector_result_for_area(
    connector_result: ConnectorResult,
    area_id: UUID,
    *,
    workspace_id: UUID | None = None,
) -> _SelectedCountyConnectorResult:
    ingest_run_id = _ingest_run_id_for(
        connector_result.retrieval_run.ingest_run_id,
        workspace_id=workspace_id,
    )
    return _SelectedCountyConnectorResult(
        retrieval_run=connector_result.retrieval_run.model_copy(
            update={"ingest_run_id": ingest_run_id},
        ),
        evidence_inputs=tuple(
            evidence.model_copy(
                update={
                    "evidence_id": _evidence_id_for(
                        evidence.evidence_id,
                        workspace_id=workspace_id,
                    ),
                    "area_id": area_id,
                    "source_ingest_run_id": (
                        ingest_run_id
                        if workspace_id is not None
                        else evidence.source_ingest_run_id
                    ),
                },
            )
            for evidence in connector_result.evidence_inputs
        ),
    )


def _connector_result_for_supported_aoi(
    connector_result: ConnectorResult,
    area_id: UUID,
    *,
    workspace_id: UUID | None = None,
) -> _SelectedCountyConnectorResult:
    ingest_run_id = _ingest_run_id_for_supported_aoi(
        connector_result.retrieval_run.ingest_run_id,
        area_id=area_id,
        workspace_id=workspace_id,
    )
    return _SelectedCountyConnectorResult(
        retrieval_run=connector_result.retrieval_run.model_copy(
            update={"ingest_run_id": ingest_run_id},
        ),
        evidence_inputs=tuple(
            evidence.model_copy(
                update={
                    "evidence_id": _evidence_id_for_supported_aoi(
                        evidence.evidence_id,
                        area_id=area_id,
                        workspace_id=workspace_id,
                    ),
                    "area_id": area_id,
                    "source_ingest_run_id": ingest_run_id,
                },
            )
            for evidence in connector_result.evidence_inputs
        ),
    )


def _ingest_run_id_for(ingest_run_id: UUID, *, workspace_id: UUID | None = None) -> UUID:
    if workspace_id is None:
        return ingest_run_id
    return uuid5(
        NAMESPACE_URL,
        f"land-dd:selected-county:{workspace_id}:ingest-run:{ingest_run_id}",
    )


def _evidence_id_for(evidence_id: UUID, *, workspace_id: UUID | None = None) -> UUID:
    if workspace_id is None:
        return evidence_id
    return uuid5(
        NAMESPACE_URL,
        f"land-dd:selected-county:{workspace_id}:evidence:{evidence_id}",
    )


def _ingest_run_id_for_supported_aoi(
    ingest_run_id: UUID,
    *,
    area_id: UUID,
    workspace_id: UUID | None = None,
) -> UUID:
    return uuid5(
        NAMESPACE_URL,
        (
            "land-dd:generic-supported-aoi:"
            f"{workspace_id}:area:{area_id}:ingest-run:{ingest_run_id}"
        ),
    )


def _evidence_id_for_supported_aoi(
    evidence_id: UUID,
    *,
    area_id: UUID,
    workspace_id: UUID | None = None,
) -> UUID:
    return uuid5(
        NAMESPACE_URL,
        (
            "land-dd:generic-supported-aoi:"
            f"{workspace_id}:area:{area_id}:evidence:{evidence_id}"
        ),
    )


def _resource_root() -> Any:
    return files(__name__)


__all__ = [
    "SelectedCountyCase",
    "SelectedCountyAoiSupportProfile",
    "SelectedCountyReportResult",
    "SupportedSelectedCountyAoiReportResult",
    "UnsupportedSelectedCountyAoiError",
    "SupportedAoiAreaNotFoundError",
    "UnsupportedSelectedCountyCaseError",
    "create_supported_aoi_report",
    "create_selected_county_report",
    "get_selected_county_case",
    "list_selected_county_cases",
]
