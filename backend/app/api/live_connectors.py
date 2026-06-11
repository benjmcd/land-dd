from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from fastapi import HTTPException, status

from app.api.dependencies import ApiServices
from app.connectors import (
    AssessorNotEvaluatedConnector,
    BrunswickParcelsBbox,
    BrunswickParcelsConnector,
    BrunswickParcelsConnectorError,
    BuncombeParcelsBbox,
    BuncombeParcelsConnector,
    BuncombeParcelsConnectorError,
    ChathamParcelsBbox,
    ChathamParcelsConnector,
    ChathamParcelsConnectorError,
    ChathamZoningConnectorResult,
    ChathamZoningRecordedConnector,
    ConnectorEvidenceIngestionAdapter,
    ConnectorFixtureQualityProfile,
    ConnectorRetrievalProvenanceAdapter,
    FemaNfhlBbox,
    FemaNfhlConnector,
    FemaNfhlConnectorError,
    NwiBbox,
    NwiConnector,
    NwiConnectorError,
    SourceProvenanceServiceRetrievalPort,
    SsurgoBbox,
    SsurgoConnector,
    SsurgoConnectorError,
    UsgsTnmBbox,
    UsgsTnmConnectorError,
    UsgsTnmElevationConnector,
    build_connector_review_handoff,
    build_connector_run_review_packet,
    build_connector_run_review_status,
)
from app.connectors.brunswick_parcels import (
    BRUNSWICK_PARCELS_MAX_FEATURES as _BRUNSWICK_MAX_FEATURES,
)
from app.connectors.buncombe_parcels import BUNCOMBE_PARCELS_MAX_FEATURES as _BUNCOMBE_MAX_FEATURES
from app.connectors.chatham_parcels import CHATHAM_PARCELS_MAX_FEATURES
from app.connectors.evidence_ingestion import ConnectorEvidenceIngestionResult
from app.connectors.fema_nfhl import FEMA_NFHL_MAX_FEATURES
from app.connectors.nwi import NWI_MAX_FEATURES
from app.connectors.result import ConnectorResult
from app.connectors.retrieval_provenance import ConnectorRetrievalProvenanceResult
from app.connectors.review_queue import ConnectorReviewQueueItem
from app.connectors.ssurgo import SSURGO_MAX_ROWS
from app.connectors.usgs_tnm import USGS_TNM_MAX_SAMPLE_POINTS
from app.domain.area_contracts import AreaContract
from app.domain.enums import JobStatus
from app.domain.source_contracts import SourceContract

DS_001_REGISTRY_ID = "DS-001"
DS_002_REGISTRY_ID = "DS-002"
DS_003_REGISTRY_ID = "DS-003"
DS_004_REGISTRY_ID = "DS-004"
DS_010_REGISTRY_ID = "DS-010"
DS_011_REGISTRY_ID = "DS-011"
DS_023_REGISTRY_ID = "DS-023"

# NC private-MVP county coordinate bounds (WGS84, approximate centroid check)
_BUNCOMBE_BOUNDS = (-83.05, 35.28, -82.15, 35.79)
_CHATHAM_BOUNDS = (-79.44, 35.53, -78.89, 35.89)
_BRUNSWICK_BOUNDS = (-78.65, 33.88, -77.93, 34.35)


@dataclass(frozen=True)
class ApiConnectorIngestWorkflowResult:
    connector_result: ConnectorResult
    retrieval_provenance: ConnectorRetrievalProvenanceResult
    evidence_ingestion: ConnectorEvidenceIngestionResult


@dataclass(frozen=True)
class FemaNfhlOrchestrationResult:
    ingest_run_id: UUID
    queue_item: ConnectorReviewQueueItem
    report_ready: bool
    request_url: str


@dataclass(frozen=True)
class UsgsTnmOrchestrationResult:
    ingest_run_id: UUID
    queue_item: ConnectorReviewQueueItem
    report_ready: bool
    request_url: str


@dataclass(frozen=True)
class NwiOrchestrationResult:
    ingest_run_id: UUID
    queue_item: ConnectorReviewQueueItem
    report_ready: bool
    request_url: str


@dataclass(frozen=True)
class SsurgoOrchestrationResult:
    ingest_run_id: UUID
    queue_item: ConnectorReviewQueueItem
    report_ready: bool
    request_url: str


@dataclass(frozen=True)
class ChathamParcelsOrchestrationResult:
    ingest_run_id: UUID
    queue_item: ConnectorReviewQueueItem
    report_ready: bool
    request_url: str


RequestTimeLiveConnectorResult = (
    UsgsTnmOrchestrationResult
    | FemaNfhlOrchestrationResult
    | NwiOrchestrationResult
    | SsurgoOrchestrationResult
    | ChathamParcelsOrchestrationResult
)


def orchestrate_request_time_live_connectors_for_area(
    *,
    services: ApiServices,
    area: AreaContract,
) -> RequestTimeLiveConnectorResult | None:
    for orchestrate in (
        orchestrate_usgs_tnm_for_area,
        orchestrate_fema_nfhl_for_area,
        orchestrate_nwi_for_area,
        orchestrate_ssurgo_for_area,
    ):
        result = orchestrate(services=services, area=area)
        if not result.report_ready:
            return result
    if _source_registry_id_available(services, DS_010_REGISTRY_ID):
        county = _classify_area_county(area)
        if county == "chatham":
            parcels_result: ChathamParcelsOrchestrationResult | None = (
                orchestrate_chatham_parcels_for_area(services=services, area=area)
            )
        elif county == "buncombe":
            parcels_result = orchestrate_buncombe_parcels_for_area(
                services=services, area=area
            )
        elif county == "brunswick":
            parcels_result = orchestrate_brunswick_parcels_for_area(
                services=services, area=area
            )
        else:
            parcels_result = None
        if parcels_result is not None:
            if not parcels_result.report_ready:
                return parcels_result
            if county == "chatham" and _source_registry_id_available(
                services, DS_023_REGISTRY_ID
            ):
                zoning_code = _extract_chatham_parcel_zoning_code(
                    services, area.area_id
                )
                orchestrate_chatham_zoning_for_area(
                    services=services, area=area, zoning_code=zoning_code
                )
    if _source_registry_id_available(services, DS_011_REGISTRY_ID):
        orchestrate_assessor_not_evaluated_for_area(services=services, area=area)
    return None


def orchestrate_fema_nfhl_for_area(
    *,
    services: ApiServices,
    area: AreaContract,
    max_features: int = FEMA_NFHL_MAX_FEATURES,
) -> FemaNfhlOrchestrationResult:
    source = get_source_by_registry_id(services, DS_002_REGISTRY_ID)
    try:
        connector_result = FemaNfhlConnector(
            source=source,
            fetch_json=services.fema_nfhl_fetch_json,
        ).query_bbox(
            area_id=area.area_id,
            bbox=bbox_from_area(area),
            max_features=max_features,
        )
        retrieval_provenance = ConnectorRetrievalProvenanceAdapter(
            SourceProvenanceServiceRetrievalPort(services.source_provenance_service),
        ).record(connector_result)
        evidence_ingestion = ConnectorEvidenceIngestionAdapter(
            services.evidence_service,
        ).ingest(connector_result)
    except FemaNfhlConnectorError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    workflow_result = ApiConnectorIngestWorkflowResult(
        connector_result=connector_result,
        retrieval_provenance=retrieval_provenance,
        evidence_ingestion=evidence_ingestion,
    )
    packet = build_connector_run_review_packet(workflow_result)
    handoff = build_connector_review_handoff(packet)
    quality = ConnectorFixtureQualityProfile(
        connector_name=packet.connector_name,
        evidence_count=packet.evidence_input_count,
        source_failure_count=(
            packet.source_failure_created_count + packet.source_failure_skipped_count
        ),
        issues=(),
    )
    review_status = build_connector_run_review_status(handoff, quality)
    services.connector_review_statuses[packet.ingest_run_id] = review_status
    queue_item = services.connector_review_queue.enqueue_review_status(review_status)
    return FemaNfhlOrchestrationResult(
        ingest_run_id=packet.ingest_run_id,
        queue_item=queue_item,
        report_ready=_queue_item_approved_for_report(queue_item),
        request_url=connector_result.request_url,
    )


def orchestrate_usgs_tnm_for_area(
    *,
    services: ApiServices,
    area: AreaContract,
    max_sample_points: int = USGS_TNM_MAX_SAMPLE_POINTS,
) -> UsgsTnmOrchestrationResult:
    source = get_source_by_registry_id(services, DS_001_REGISTRY_ID)
    try:
        connector_result = UsgsTnmElevationConnector(
            source=source,
            fetch_json=services.usgs_tnm_fetch_json,
        ).query_bbox(
            area_id=area.area_id,
            bbox=usgs_tnm_bbox_from_area(area),
            max_sample_points=max_sample_points,
        )
        retrieval_provenance = ConnectorRetrievalProvenanceAdapter(
            SourceProvenanceServiceRetrievalPort(services.source_provenance_service),
        ).record(connector_result)
        evidence_ingestion = ConnectorEvidenceIngestionAdapter(
            services.evidence_service,
        ).ingest(connector_result)
    except UsgsTnmConnectorError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    workflow_result = ApiConnectorIngestWorkflowResult(
        connector_result=connector_result,
        retrieval_provenance=retrieval_provenance,
        evidence_ingestion=evidence_ingestion,
    )
    packet = build_connector_run_review_packet(workflow_result)
    handoff = build_connector_review_handoff(packet)
    quality = ConnectorFixtureQualityProfile(
        connector_name=packet.connector_name,
        evidence_count=packet.evidence_input_count,
        source_failure_count=(
            packet.source_failure_created_count + packet.source_failure_skipped_count
        ),
        issues=(),
    )
    review_status = build_connector_run_review_status(handoff, quality)
    services.connector_review_statuses[packet.ingest_run_id] = review_status
    queue_item = services.connector_review_queue.enqueue_review_status(review_status)
    return UsgsTnmOrchestrationResult(
        ingest_run_id=packet.ingest_run_id,
        queue_item=queue_item,
        report_ready=_queue_item_approved_for_report(queue_item),
        request_url=connector_result.request_url,
    )


def orchestrate_nwi_for_area(
    *,
    services: ApiServices,
    area: AreaContract,
    max_features: int = NWI_MAX_FEATURES,
) -> NwiOrchestrationResult:
    source = get_source_by_registry_id(services, DS_004_REGISTRY_ID)
    try:
        connector_result = NwiConnector(
            source=source,
            fetch_json=services.nwi_fetch_json,
        ).query_bbox(
            area_id=area.area_id,
            bbox=nwi_bbox_from_area(area),
            max_features=max_features,
        )
        retrieval_provenance = ConnectorRetrievalProvenanceAdapter(
            SourceProvenanceServiceRetrievalPort(services.source_provenance_service),
        ).record(connector_result)
        evidence_ingestion = ConnectorEvidenceIngestionAdapter(
            services.evidence_service,
        ).ingest(connector_result)
    except NwiConnectorError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    workflow_result = ApiConnectorIngestWorkflowResult(
        connector_result=connector_result,
        retrieval_provenance=retrieval_provenance,
        evidence_ingestion=evidence_ingestion,
    )
    packet = build_connector_run_review_packet(workflow_result)
    handoff = build_connector_review_handoff(packet)
    quality = ConnectorFixtureQualityProfile(
        connector_name=packet.connector_name,
        evidence_count=packet.evidence_input_count,
        source_failure_count=(
            packet.source_failure_created_count + packet.source_failure_skipped_count
        ),
        issues=(),
    )
    review_status = build_connector_run_review_status(handoff, quality)
    services.connector_review_statuses[packet.ingest_run_id] = review_status
    queue_item = services.connector_review_queue.enqueue_review_status(review_status)
    return NwiOrchestrationResult(
        ingest_run_id=packet.ingest_run_id,
        queue_item=queue_item,
        report_ready=_queue_item_approved_for_report(queue_item),
        request_url=connector_result.request_url,
    )


def orchestrate_ssurgo_for_area(
    *,
    services: ApiServices,
    area: AreaContract,
    max_rows: int = SSURGO_MAX_ROWS,
) -> SsurgoOrchestrationResult:
    source = get_source_by_registry_id(services, DS_003_REGISTRY_ID)
    try:
        connector_result = SsurgoConnector(
            source=source,
            fetch_json=services.ssurgo_fetch_json,
        ).query_bbox(
            area_id=area.area_id,
            bbox=ssurgo_bbox_from_area(area),
            max_rows=max_rows,
        )
        retrieval_provenance = ConnectorRetrievalProvenanceAdapter(
            SourceProvenanceServiceRetrievalPort(services.source_provenance_service),
        ).record(connector_result)
        evidence_ingestion = ConnectorEvidenceIngestionAdapter(
            services.evidence_service,
        ).ingest(connector_result)
    except SsurgoConnectorError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    workflow_result = ApiConnectorIngestWorkflowResult(
        connector_result=connector_result,
        retrieval_provenance=retrieval_provenance,
        evidence_ingestion=evidence_ingestion,
    )
    packet = build_connector_run_review_packet(workflow_result)
    handoff = build_connector_review_handoff(packet)
    quality = ConnectorFixtureQualityProfile(
        connector_name=packet.connector_name,
        evidence_count=packet.evidence_input_count,
        source_failure_count=(
            packet.source_failure_created_count + packet.source_failure_skipped_count
        ),
        issues=(),
    )
    review_status = build_connector_run_review_status(handoff, quality)
    services.connector_review_statuses[packet.ingest_run_id] = review_status
    queue_item = services.connector_review_queue.enqueue_review_status(review_status)
    return SsurgoOrchestrationResult(
        ingest_run_id=packet.ingest_run_id,
        queue_item=queue_item,
        report_ready=_queue_item_approved_for_report(queue_item),
        request_url=connector_result.request_url,
    )


def orchestrate_chatham_parcels_for_area(
    *,
    services: ApiServices,
    area: AreaContract,
    max_features: int = CHATHAM_PARCELS_MAX_FEATURES,
) -> ChathamParcelsOrchestrationResult:
    source = get_source_by_registry_id(services, DS_010_REGISTRY_ID)
    try:
        connector_result = ChathamParcelsConnector(
            source=source,
            fetch_json=services.chatham_parcels_fetch_json,
        ).query_bbox(
            area_id=area.area_id,
            bbox=chatham_parcels_bbox_from_area(area),
            max_features=max_features,
        )
        retrieval_provenance = ConnectorRetrievalProvenanceAdapter(
            SourceProvenanceServiceRetrievalPort(services.source_provenance_service),
        ).record(connector_result)
        evidence_ingestion = ConnectorEvidenceIngestionAdapter(
            services.evidence_service,
        ).ingest(connector_result)
    except ChathamParcelsConnectorError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    workflow_result = ApiConnectorIngestWorkflowResult(
        connector_result=connector_result,
        retrieval_provenance=retrieval_provenance,
        evidence_ingestion=evidence_ingestion,
    )
    packet = build_connector_run_review_packet(workflow_result)
    handoff = build_connector_review_handoff(packet)
    quality = ConnectorFixtureQualityProfile(
        connector_name=packet.connector_name,
        evidence_count=packet.evidence_input_count,
        source_failure_count=(
            packet.source_failure_created_count + packet.source_failure_skipped_count
        ),
        issues=(),
    )
    review_status = build_connector_run_review_status(handoff, quality)
    services.connector_review_statuses[packet.ingest_run_id] = review_status
    queue_item = services.connector_review_queue.enqueue_review_status(review_status)
    return ChathamParcelsOrchestrationResult(
        ingest_run_id=packet.ingest_run_id,
        queue_item=queue_item,
        report_ready=_queue_item_approved_for_report(queue_item),
        request_url=connector_result.request_url,
    )


def orchestrate_buncombe_parcels_for_area(
    *,
    services: ApiServices,
    area: AreaContract,
    max_features: int = _BUNCOMBE_MAX_FEATURES,
) -> ChathamParcelsOrchestrationResult:
    source = get_source_by_registry_id(services, DS_010_REGISTRY_ID)
    try:
        connector_result = BuncombeParcelsConnector(
            source=source,
            fetch_json=services.buncombe_parcels_fetch_json,
        ).query_bbox(
            area_id=area.area_id,
            bbox=buncombe_parcels_bbox_from_area(area),
            max_features=max_features,
        )
        retrieval_provenance = ConnectorRetrievalProvenanceAdapter(
            SourceProvenanceServiceRetrievalPort(services.source_provenance_service),
        ).record(connector_result)
        evidence_ingestion = ConnectorEvidenceIngestionAdapter(
            services.evidence_service,
        ).ingest(connector_result)
    except BuncombeParcelsConnectorError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    workflow_result = ApiConnectorIngestWorkflowResult(
        connector_result=connector_result,
        retrieval_provenance=retrieval_provenance,
        evidence_ingestion=evidence_ingestion,
    )
    packet = build_connector_run_review_packet(workflow_result)
    handoff = build_connector_review_handoff(packet)
    quality = ConnectorFixtureQualityProfile(
        connector_name=packet.connector_name,
        evidence_count=packet.evidence_input_count,
        source_failure_count=(
            packet.source_failure_created_count + packet.source_failure_skipped_count
        ),
        issues=(),
    )
    review_status = build_connector_run_review_status(handoff, quality)
    services.connector_review_statuses[packet.ingest_run_id] = review_status
    queue_item = services.connector_review_queue.enqueue_review_status(review_status)
    return ChathamParcelsOrchestrationResult(
        ingest_run_id=packet.ingest_run_id,
        queue_item=queue_item,
        report_ready=_queue_item_approved_for_report(queue_item),
        request_url=connector_result.request_url,
    )


def orchestrate_brunswick_parcels_for_area(
    *,
    services: ApiServices,
    area: AreaContract,
    max_features: int = _BRUNSWICK_MAX_FEATURES,
) -> ChathamParcelsOrchestrationResult:
    source = get_source_by_registry_id(services, DS_010_REGISTRY_ID)
    try:
        connector_result = BrunswickParcelsConnector(
            source=source,
            fetch_json=services.brunswick_parcels_fetch_json,
        ).query_bbox(
            area_id=area.area_id,
            bbox=brunswick_parcels_bbox_from_area(area),
            max_features=max_features,
        )
        retrieval_provenance = ConnectorRetrievalProvenanceAdapter(
            SourceProvenanceServiceRetrievalPort(services.source_provenance_service),
        ).record(connector_result)
        evidence_ingestion = ConnectorEvidenceIngestionAdapter(
            services.evidence_service,
        ).ingest(connector_result)
    except BrunswickParcelsConnectorError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    workflow_result = ApiConnectorIngestWorkflowResult(
        connector_result=connector_result,
        retrieval_provenance=retrieval_provenance,
        evidence_ingestion=evidence_ingestion,
    )
    packet = build_connector_run_review_packet(workflow_result)
    handoff = build_connector_review_handoff(packet)
    quality = ConnectorFixtureQualityProfile(
        connector_name=packet.connector_name,
        evidence_count=packet.evidence_input_count,
        source_failure_count=(
            packet.source_failure_created_count + packet.source_failure_skipped_count
        ),
        issues=(),
    )
    review_status = build_connector_run_review_status(handoff, quality)
    services.connector_review_statuses[packet.ingest_run_id] = review_status
    queue_item = services.connector_review_queue.enqueue_review_status(review_status)
    return ChathamParcelsOrchestrationResult(
        ingest_run_id=packet.ingest_run_id,
        queue_item=queue_item,
        report_ready=_queue_item_approved_for_report(queue_item),
        request_url=connector_result.request_url,
    )


def orchestrate_assessor_not_evaluated_for_area(
    *,
    services: ApiServices,
    area: AreaContract,
) -> None:
    source = get_source_by_registry_id(services, DS_011_REGISTRY_ID)
    connector_result = AssessorNotEvaluatedConnector().query_area(
        area_id=area.area_id,
        source=source,
    )
    ConnectorRetrievalProvenanceAdapter(
        SourceProvenanceServiceRetrievalPort(services.source_provenance_service),
    ).record(connector_result)
    ConnectorEvidenceIngestionAdapter(
        services.evidence_service,
    ).ingest(connector_result)


def orchestrate_chatham_zoning_for_area(
    *,
    services: ApiServices,
    area: AreaContract,
    zoning_code: str | None,
) -> ChathamZoningConnectorResult:
    source = get_source_by_registry_id(services, DS_023_REGISTRY_ID)
    connector_result = ChathamZoningRecordedConnector().query_district(
        area_id=area.area_id,
        zoning_code=zoning_code,
        source=source,
    )
    ConnectorRetrievalProvenanceAdapter(
        SourceProvenanceServiceRetrievalPort(services.source_provenance_service),
    ).record(connector_result)
    ConnectorEvidenceIngestionAdapter(
        services.evidence_service,
    ).ingest(connector_result)
    return connector_result


def _extract_chatham_parcel_zoning_code(
    services: ApiServices,
    area_id: UUID,
) -> str | None:
    for evidence in services.evidence_service.list_by_area(area_id):
        if evidence.domain == "parcels" and not evidence.is_source_failure:
            zoning = evidence.observed_value.get("parcel_zoning")
            if isinstance(zoning, str) and zoning:
                return zoning
    return None


def get_source_by_registry_id(
    services: ApiServices,
    source_registry_id: str,
) -> SourceContract:
    for source in services.source_service.list_all():
        if source.metadata.get("source_registry_id") == source_registry_id:
            return source
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=f"source registry id {source_registry_id} is not registered",
    )


def _source_registry_id_available(services: ApiServices, source_registry_id: str) -> bool:
    return any(
        source.metadata.get("source_registry_id") == source_registry_id
        for source in services.source_service.list_all()
    )


def bbox_from_area(area: AreaContract) -> FemaNfhlBbox:
    coordinates = _coordinates_for_bbox(area, "FEMA NFHL")
    xs = [position[0] for position in coordinates]
    ys = [position[1] for position in coordinates]
    return FemaNfhlBbox(
        xmin=min(xs),
        ymin=min(ys),
        xmax=max(xs),
        ymax=max(ys),
    )


def usgs_tnm_bbox_from_area(area: AreaContract) -> UsgsTnmBbox:
    coordinates = _coordinates_for_bbox(area, "USGS TNM EPQS")
    xs = [position[0] for position in coordinates]
    ys = [position[1] for position in coordinates]
    return UsgsTnmBbox(
        xmin=min(xs),
        ymin=min(ys),
        xmax=max(xs),
        ymax=max(ys),
    )


def nwi_bbox_from_area(area: AreaContract) -> NwiBbox:
    coordinates = _coordinates_for_bbox(area, "NWI")
    xs = [position[0] for position in coordinates]
    ys = [position[1] for position in coordinates]
    return NwiBbox(
        xmin=min(xs),
        ymin=min(ys),
        xmax=max(xs),
        ymax=max(ys),
    )


def ssurgo_bbox_from_area(area: AreaContract) -> SsurgoBbox:
    coordinates = _coordinates_for_bbox(area, "SSURGO")
    xs = [position[0] for position in coordinates]
    ys = [position[1] for position in coordinates]
    return SsurgoBbox(
        xmin=min(xs),
        ymin=min(ys),
        xmax=max(xs),
        ymax=max(ys),
    )


def chatham_parcels_bbox_from_area(area: AreaContract) -> ChathamParcelsBbox:
    coordinates = _coordinates_for_bbox(area, "Chatham Parcels")
    xs = [position[0] for position in coordinates]
    ys = [position[1] for position in coordinates]
    return ChathamParcelsBbox(
        xmin=min(xs),
        ymin=min(ys),
        xmax=max(xs),
        ymax=max(ys),
    )


def buncombe_parcels_bbox_from_area(area: AreaContract) -> BuncombeParcelsBbox:
    coordinates = _coordinates_for_bbox(area, "Buncombe Parcels")
    xs = [position[0] for position in coordinates]
    ys = [position[1] for position in coordinates]
    return BuncombeParcelsBbox(
        xmin=min(xs),
        ymin=min(ys),
        xmax=max(xs),
        ymax=max(ys),
    )


def brunswick_parcels_bbox_from_area(area: AreaContract) -> BrunswickParcelsBbox:
    coordinates = _coordinates_for_bbox(area, "Brunswick Parcels")
    xs = [position[0] for position in coordinates]
    ys = [position[1] for position in coordinates]
    return BrunswickParcelsBbox(
        xmin=min(xs),
        ymin=min(ys),
        xmax=max(xs),
        ymax=max(ys),
    )


def _classify_area_county(area: AreaContract) -> str | None:
    """Return 'buncombe', 'chatham', or 'brunswick' based on bbox centroid, else None."""
    try:
        positions = _collect_positions(area.geom_geojson)
    except Exception:
        return None
    if not positions:
        return None
    cx = sum(p[0] for p in positions) / len(positions)
    cy = sum(p[1] for p in positions) / len(positions)
    for county, bounds in (
        ("buncombe", _BUNCOMBE_BOUNDS),
        ("chatham", _CHATHAM_BOUNDS),
        ("brunswick", _BRUNSWICK_BOUNDS),
    ):
        xmin, ymin, xmax, ymax = bounds
        if xmin <= cx <= xmax and ymin <= cy <= ymax:
            return county
    return None


def _coordinates_for_bbox(
    area: AreaContract,
    connector_label: str,
) -> list[tuple[float, float]]:
    coordinates = _collect_positions(area.geom_geojson)
    if not coordinates:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"area geometry has no coordinates for {connector_label} bbox",
        )
    return coordinates


def _collect_positions(geometry: dict[str, object]) -> list[tuple[float, float]]:
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


def _queue_item_approved_for_report(queue_item: ConnectorReviewQueueItem) -> bool:
    if queue_item.status != JobStatus.SUCCEEDED:
        return False
    decision = queue_item.payload.get("review_decision")
    if not isinstance(decision, dict):
        return False
    return decision.get("action") == "approve_for_connector_qa"


__all__ = [
    "DS_001_REGISTRY_ID",
    "DS_002_REGISTRY_ID",
    "DS_003_REGISTRY_ID",
    "DS_004_REGISTRY_ID",
    "DS_010_REGISTRY_ID",
    "DS_011_REGISTRY_ID",
    "DS_023_REGISTRY_ID",
    "ChathamParcelsOrchestrationResult",
    "FemaNfhlOrchestrationResult",
    "NwiOrchestrationResult",
    "SsurgoOrchestrationResult",
    "UsgsTnmOrchestrationResult",
    "bbox_from_area",
    "buncombe_parcels_bbox_from_area",
    "brunswick_parcels_bbox_from_area",
    "chatham_parcels_bbox_from_area",
    "get_source_by_registry_id",
    "nwi_bbox_from_area",
    "orchestrate_assessor_not_evaluated_for_area",
    "orchestrate_buncombe_parcels_for_area",
    "orchestrate_brunswick_parcels_for_area",
    "orchestrate_chatham_parcels_for_area",
    "orchestrate_chatham_zoning_for_area",
    "orchestrate_fema_nfhl_for_area",
    "orchestrate_nwi_for_area",
    "orchestrate_request_time_live_connectors_for_area",
    "orchestrate_ssurgo_for_area",
    "orchestrate_usgs_tnm_for_area",
    "ssurgo_bbox_from_area",
    "usgs_tnm_bbox_from_area",
]
