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
from app.domain.enums import IntentCode
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


def create_selected_county_report(
    services: ApiServices,
    case_id: str,
    reviewer_id: str = "operator-private-mvp",
    reason: str = "selected-county private MVP fixture approval",
) -> SelectedCountyReportResult:
    case = get_selected_county_case(case_id)
    if case is None:
        raise UnsupportedSelectedCountyCaseError(
            f"Unsupported selected-county private-MVP case: {case_id}",
        )

    _ensure_fixture_provenance(services, case)
    area_id = _area_id_for(case)
    _ensure_area(services, case, area_id)

    evidence_created_count = 0
    for domain, fixture_file in case.connector_fixture_files.items():
        connector_factory, quality_evaluator = _connector_for_domain(domain)
        with as_file(_resource_root().joinpath(fixture_file)) as fixture_path:
            raw_result = connector_factory().load_fixture(fixture_path)

        connector_result = _connector_result_for_area(raw_result, area_id)
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
        queued = services.connector_review_queue.enqueue_review_status(review_status)
        if handoff.disposition == ConnectorReviewDisposition.READY_FOR_CONNECTOR_QA:
            services.connector_review_queue.approve_for_connector_qa(
                queued.job_id,
                reviewer_id=reviewer_id,
                reason=reason,
            )
        evidence_created_count += len(workflow_result.evidence_ingestion.created_evidence)

    report_run = services.report_service.create_report_run(
        area_id=area_id,
        intent_code=IntentCode(case.intent),
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


def _ensure_fixture_provenance(
    services: ApiServices,
    case: SelectedCountyCase,
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
                metadata={"fixture_scope": case.fixture_scope},
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
                "case_id": case.case_id,
                "fixture_scope": case.fixture_scope,
                "connector_domains": sorted(case.connector_fixture_files),
            },
            is_current=True,
            notes="Packaged selected-county private MVP fixture version.",
        ),
    )


def _ensure_area(
    services: ApiServices,
    case: SelectedCountyCase,
    area_id: UUID,
) -> None:
    if services.area_service.get(area_id) is not None:
        return
    raw = _load_json_resource(case.geometry_file)
    geometry = raw["geometry"] if raw.get("type") == "Feature" else raw
    services.area_service.create(
        AreaContract(
            area_id=area_id,
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


def _area_id_for(case: SelectedCountyCase) -> UUID:
    return uuid5(NAMESPACE_URL, f"land-dd:selected-county:{case.case_id}")


def _connector_result_for_area(
    connector_result: ConnectorResult,
    area_id: UUID,
) -> _SelectedCountyConnectorResult:
    return _SelectedCountyConnectorResult(
        retrieval_run=connector_result.retrieval_run,
        evidence_inputs=tuple(
            evidence.model_copy(update={"area_id": area_id})
            for evidence in connector_result.evidence_inputs
        ),
    )


def _resource_root() -> Any:
    return files(__name__)


__all__ = [
    "SelectedCountyCase",
    "SelectedCountyReportResult",
    "UnsupportedSelectedCountyCaseError",
    "create_selected_county_report",
    "get_selected_county_case",
    "list_selected_county_cases",
]
