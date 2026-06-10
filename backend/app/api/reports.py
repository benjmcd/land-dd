from __future__ import annotations

import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import Annotated, cast
from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Header,
    HTTPException,
    Query,
    Request,
    Response,
    status,
)
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.api.dependencies import (
    ApiServices,
    RequestAuthContext,
    create_db_api_services,
    get_request_auth_context,
    get_services,
)
from app.api.live_connectors import orchestrate_request_time_live_connectors_for_area
from app.api.reviewer_auth import (
    REVIEWER_SCOPE_REPORT_APPROVE,
    REVIEWER_SCOPE_REPORT_RETRY,
    ReviewerPrincipal,
    require_reviewer_scope,
)
from app.core.config import Settings
from app.db.engine import get_session_factory
from app.domain.claim_contracts import ClaimContract
from app.domain.enums import IntentCode, JobStatus, ReportReviewStatus, SeverityBand
from app.domain.report_contracts import ReportRunContract
from app.reports.dossier import build_rural_land_dossier
from app.reports.job_store import SqlAlchemyAsyncReportJobStore

router = APIRouter(prefix="/report-runs", tags=["report-runs"])
ServicesDep = Annotated[ApiServices, Depends(get_services)]
logger = logging.getLogger(__name__)

_RED_FLAG_BANDS: frozenset[SeverityBand] = frozenset({SeverityBand.HIGH, SeverityBand.CRITICAL})


def _flat_claims(report: ReportRunContract) -> list[ClaimContract]:
    return list(report.claims) + list(report.unknowns) + list(report.red_flags)


class ReportRunCreateRequest(BaseModel):
    area_id: UUID
    intent_code: IntentCode


class AsyncReportRunResponse(BaseModel):
    report_run_id: UUID | None = None
    status: str
    connector_ingest_run_id: UUID | None = None
    connector_review_status: str | None = None
    retry_of_report_run_id: UUID | None = None


class LineageSourceEntry(BaseModel):
    source_id: UUID
    source_name: str
    ingest_run_ids: list[UUID]


class LineageEvidenceEntry(BaseModel):
    evidence_id: UUID
    source_id: UUID
    evidence_code: str
    domain: str
    claim_ids: list[UUID]


class LineageClaimEntry(BaseModel):
    claim_id: UUID
    claim_code: str
    domain: str
    evidence_ids: list[UUID]


class ReportLineageResponse(BaseModel):
    report_run_id: UUID
    area_id: UUID
    intent_code: str
    sources: list[LineageSourceEntry]
    evidence_lineage: list[LineageEvidenceEntry]
    claim_lineage: list[LineageClaimEntry]


def get_reviewer_principal(
    services: ServicesDep,
    reviewer_id: Annotated[str | None, Header(alias="X-Reviewer-Id")] = None,
    reviewer_token: Annotated[str | None, Header(alias="X-Reviewer-Token")] = None,
) -> ReviewerPrincipal:
    return services.reviewer_auth(reviewer_id=reviewer_id, reviewer_token=reviewer_token)


def run_report_background(
    *,
    services: ApiServices,
    report_run_id: UUID,
    area_id: UUID,
    intent_code: IntentCode,
) -> None:
    services.async_report_jobs.mark_running(report_run_id)
    logger.info(
        "report job running",
        extra=_job_log_context(report_run_id, area_id, intent_code),
    )
    try:
        services.report_service.create_report_run(
            area_id=area_id,
            intent_code=intent_code,
            report_run_id=report_run_id,
        )
        services.async_report_jobs.mark_succeeded(report_run_id)
        logger.info(
            "report job succeeded",
            extra=_job_log_context(report_run_id, area_id, intent_code),
        )
    except Exception as exc:  # noqa: BLE001
        services.async_report_jobs.mark_failed(report_run_id, error_msg=str(exc))
        logger.exception(
            "report job failed",
            extra=_job_log_context(report_run_id, area_id, intent_code),
        )


def run_db_report_background(
    *,
    report_run_id: UUID,
    area_id: UUID,
    intent_code: IntentCode,
    object_store_root: str,
    settings: Settings,
) -> None:
    job_store = SqlAlchemyAsyncReportJobStore()
    try:
        job_store.mark_running(report_run_id)
        logger.info(
            "report job running",
            extra=_job_log_context(report_run_id, area_id, intent_code),
        )
        with get_session_factory()() as session:
            services = create_db_api_services(
                session,
                object_store_root=object_store_root,
                settings=settings,
            )
            services.report_service.create_report_run(
                area_id=area_id,
                intent_code=intent_code,
                report_run_id=report_run_id,
            )
            session.commit()
        job_store.mark_succeeded(report_run_id)
        logger.info(
            "report job succeeded",
            extra=_job_log_context(report_run_id, area_id, intent_code),
        )
    except Exception as exc:  # noqa: BLE001
        job_store.mark_failed(report_run_id, error_msg=str(exc))
        logger.exception(
            "report job failed",
            extra=_job_log_context(report_run_id, area_id, intent_code),
        )


def schedule_report_background(
    *,
    background_tasks: BackgroundTasks,
    request_context: Request,
    services: ApiServices,
    report_run_id: UUID,
    area_id: UUID,
    intent_code: IntentCode,
) -> None:
    logger.info(
        "report job queued",
        extra=_job_log_context(report_run_id, area_id, intent_code),
    )
    if bool(getattr(request_context.app.state, "use_db_services", False)):
        background_tasks.add_task(
            run_db_report_background,
            report_run_id=report_run_id,
            area_id=area_id,
            intent_code=intent_code,
            object_store_root=str(request_context.app.state.object_store_root),
            settings=cast(Settings, request_context.app.state.settings),
        )
        return
    background_tasks.add_task(
        run_report_background,
        services=services,
        report_run_id=report_run_id,
        area_id=area_id,
        intent_code=intent_code,
    )


@router.post(
    "",
    response_model=AsyncReportRunResponse | ReportRunContract,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_report_run(
    request: ReportRunCreateRequest,
    background_tasks: BackgroundTasks,
    request_context: Request,
    services: ServicesDep,
    response: Response,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
    x_user_id: Annotated[str | None, Header(alias="X-User-Id")] = None,
) -> AsyncReportRunResponse | ReportRunContract:
    auth = _optional_report_auth_context(
        request_context,
        authorization=authorization,
        x_workspace_id=x_workspace_id,
        x_user_id=x_user_id,
    )
    area = services.area_service.get(request.area_id)
    if area is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Area '{request.area_id}' is not registered",
        )
    if auth is not None:
        if area.workspace_id != auth.workspace_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="area not found",
            )
        try:
            report = services.report_service.create_report_run(
                area_id=request.area_id,
                intent_code=request.intent_code,
                workspace_id=auth.workspace_id,
                requested_by=auth.user_id,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=str(exc),
            ) from exc
        response.status_code = status.HTTP_201_CREATED
        return report
    if _live_connectors_enabled(request_context):
        connector_result = orchestrate_request_time_live_connectors_for_area(
            services=services,
            area=area,
        )
        if connector_result is not None:
            return AsyncReportRunResponse(
                status="pending_connector_review",
                connector_ingest_run_id=connector_result.ingest_run_id,
                connector_review_status=connector_result.queue_item.status.value,
            )
    job = services.async_report_jobs.create(
        area_id=request.area_id,
        intent_code=request.intent_code,
    )
    schedule_report_background(
        background_tasks=background_tasks,
        request_context=request_context,
        services=services,
        report_run_id=job.report_run_id,
        area_id=request.area_id,
        intent_code=request.intent_code,
    )
    return AsyncReportRunResponse(
        report_run_id=job.report_run_id,
        status="queued",
    )


class ReportApproveRequest(BaseModel):
    reason: str | None = None


@router.post("/{report_run_id}/approve", response_model=ReportRunContract)
def approve_report_run(
    report_run_id: UUID,
    services: ServicesDep,
    principal: Annotated[ReviewerPrincipal, Depends(get_reviewer_principal)],
    body: ReportApproveRequest | None = None,
) -> ReportRunContract:
    require_reviewer_scope(principal, REVIEWER_SCOPE_REPORT_APPROVE)
    report = services.report_service.get_report_run(report_run_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="report run not found")
    if report.review_status == ReportReviewStatus.APPROVED:
        return report
    updated = services.report_service.approve_report_run(
        report_run_id,
        reviewer_id=principal.reviewer_id,
        reason=body.reason if body else None,
    )
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="report run not found")
    return updated


@router.post(
    "/{report_run_id}/retry",
    response_model=AsyncReportRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def retry_report_run(
    report_run_id: UUID,
    background_tasks: BackgroundTasks,
    request_context: Request,
    services: ServicesDep,
    principal: Annotated[ReviewerPrincipal, Depends(get_reviewer_principal)],
) -> AsyncReportRunResponse:
    require_reviewer_scope(principal, REVIEWER_SCOPE_REPORT_RETRY)
    failed_job = services.async_report_jobs.get(report_run_id)
    if failed_job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="report run job not found",
        )
    if failed_job.status != JobStatus.FAILED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="report run retry requires a failed report job",
        )

    retry_job = services.async_report_jobs.create(
        area_id=failed_job.area_id,
        intent_code=failed_job.intent_code,
        retry_of_report_run_id=failed_job.report_run_id,
    )
    schedule_report_background(
        background_tasks=background_tasks,
        request_context=request_context,
        services=services,
        report_run_id=retry_job.report_run_id,
        area_id=retry_job.area_id,
        intent_code=retry_job.intent_code,
    )
    return AsyncReportRunResponse(
        report_run_id=retry_job.report_run_id,
        status="queued",
        retry_of_report_run_id=failed_job.report_run_id,
    )


class ReportRunComparisonSummary(BaseModel):
    report_run_id: UUID
    area_id: UUID
    intent_code: str
    claims_count: int
    unknowns_count: int
    red_flags_count: int
    high_severity_claims: list[dict[str, str]]
    verification_tasks_count: int


def _build_comparison_summary(report: ReportRunContract) -> ReportRunComparisonSummary:
    """Build a ReportRunComparisonSummary from a report contract.

    Module-level helper used by both the API compare route and the UI compare page
    so that summary construction stays in one place.
    """
    all_claims = _flat_claims(report)
    high_severity = [
        {"claim_code": c.claim_code, "domain": c.domain}
        for c in all_claims
        if c.severity in _RED_FLAG_BANDS
    ]
    return ReportRunComparisonSummary(
        report_run_id=report.report_run_id,
        area_id=report.area_id,
        intent_code=report.intent_code.value,
        claims_count=len(report.claims),
        unknowns_count=len(report.unknowns),
        red_flags_count=len(report.red_flags),
        high_severity_claims=high_severity,
        verification_tasks_count=len(report.verification_tasks),
    )


def _parse_compare_ids(ids: str) -> list[UUID]:
    """Parse and validate the comma-separated compare ``ids`` query value.

    Module-level helper used by both the API compare route and the UI compare page
    so the 2..4 bounds and UUID semantics stay in one place. Raises HTTPException
    with the canonical status codes and messages on invalid input.
    """
    raw_ids = [part.strip() for part in ids.split(",") if part.strip()]
    if len(raw_ids) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="at least 2 report run IDs are required for comparison",
        )
    if len(raw_ids) > 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="at most 4 report run IDs are allowed for comparison",
        )
    try:
        return [UUID(rid) for rid in raw_ids]
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"malformed UUID in ids: {exc}",
        ) from exc


class ReportRunCompareResponse(BaseModel):
    summaries: list[ReportRunComparisonSummary]


class ReportRunDiffResponse(BaseModel):
    report_run_id: UUID
    base_report_run_id: UUID
    area_id: UUID
    same_area: bool
    ruleset_changed: bool
    added_claim_codes: list[str]
    removed_claim_codes: list[str]
    added_sources: list[str]
    removed_sources: list[str]
    evidence_count_delta: int


class ReportRunListItem(BaseModel):
    report_run_id: UUID
    intent_code: str
    status: str
    created_at: str
    review_status: str | None


@router.get("", response_model=list[ReportRunListItem])
def list_report_runs(
    services: ServicesDep,
    status: Annotated[JobStatus | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ReportRunListItem]:
    jobs = services.async_report_jobs.list_recent(
        limit=limit, offset=offset, status=status
    )
    items: list[ReportRunListItem] = []
    for job in jobs:
        review_status: str | None = None
        if job.status == JobStatus.SUCCEEDED:
            report = services.report_service.get_report_run(job.report_run_id)
            if report is not None:
                review_status = report.review_status.value
        items.append(
            ReportRunListItem(
                report_run_id=job.report_run_id,
                intent_code=job.intent_code.value,
                status=job.status.value,
                created_at=job.created_at.isoformat(),
                review_status=review_status,
            )
        )
    return items


@router.get("/compare", response_model=ReportRunCompareResponse)
def compare_report_runs(
    ids: str,
    services: ServicesDep,
    request_context: Request,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
    x_user_id: Annotated[str | None, Header(alias="X-User-Id")] = None,
) -> ReportRunCompareResponse:
    auth = _optional_report_auth_context(
        request_context,
        authorization=authorization,
        x_workspace_id=x_workspace_id,
        x_user_id=x_user_id,
    )
    run_ids = _parse_compare_ids(ids)

    summaries: list[ReportRunComparisonSummary] = []
    for run_id in run_ids:
        report = services.report_service.get_report_run(run_id)
        if report is None or (auth is not None and report.workspace_id != auth.workspace_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"report run '{run_id}' not found",
            )
        summaries.append(_build_comparison_summary(report))
    return ReportRunCompareResponse(summaries=summaries)


@router.get("/{report_run_id}", response_model=ReportRunContract)
def get_report_run(
    report_run_id: UUID,
    services: ServicesDep,
    request_context: Request,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
    x_user_id: Annotated[str | None, Header(alias="X-User-Id")] = None,
) -> ReportRunContract:
    auth = _optional_report_auth_context(
        request_context,
        authorization=authorization,
        x_workspace_id=x_workspace_id,
        x_user_id=x_user_id,
    )
    job = services.async_report_jobs.get(report_run_id)
    if job is not None:
        if job.status in (JobStatus.QUEUED, JobStatus.RUNNING):
            return ReportRunContract(
                report_run_id=report_run_id,
                area_id=job.area_id,
                intent_code=job.intent_code,
                status=job.status,
            )
        if job.status == JobStatus.FAILED:
            return ReportRunContract(
                report_run_id=report_run_id,
                area_id=job.area_id,
                intent_code=job.intent_code,
                status=JobStatus.FAILED,
                caveats=[job.error_msg or "Report generation failed"],
            )
        # SUCCEEDED — fall through to fetch full report from repo

    report = services.report_service.get_report_run(report_run_id)
    if report is None or (auth is not None and report.workspace_id != auth.workspace_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="report run not found")
    return report


@router.get("/{report_run_id}/dossier")
def get_report_run_dossier(
    report_run_id: UUID,
    services: ServicesDep,
    request_context: Request,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
    x_user_id: Annotated[str | None, Header(alias="X-User-Id")] = None,
    download: Annotated[bool, Query()] = False,
) -> Response:
    auth = _optional_report_auth_context(
        request_context,
        authorization=authorization,
        x_workspace_id=x_workspace_id,
        x_user_id=x_user_id,
    )
    report = services.report_service.get_report_run(report_run_id)
    if report is not None:
        if auth is not None and report.workspace_id != auth.workspace_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="report run not found",
            )
        if report.review_status != ReportReviewStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"report run is not approved for delivery (review_status={report.review_status})",  # noqa: E501
            )
        dossier_md = build_rural_land_dossier(report)
        headers: dict[str, str] = {}
        if download:
            headers["Content-Disposition"] = (
                f'attachment; filename="dossier_{report_run_id}.md"'
            )
        return Response(
            content=dossier_md,
            media_type="text/markdown; charset=utf-8",
            headers=headers,
        )
    job = services.async_report_jobs.get(report_run_id)
    if job is not None and job.status in (JobStatus.QUEUED, JobStatus.RUNNING):
        return JSONResponse(
            status_code=202,
            content={"status": "pending", "report_run_id": str(report_run_id)},
        )
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="report run not found")


@router.get("/{report_run_id}/artifact")
def get_report_run_artifact(
    report_run_id: UUID,
    services: ServicesDep,
    request_context: Request,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
    x_user_id: Annotated[str | None, Header(alias="X-User-Id")] = None,
) -> Response:
    auth = _optional_report_auth_context(
        request_context,
        authorization=authorization,
        x_workspace_id=x_workspace_id,
        x_user_id=x_user_id,
    )
    report = services.report_service.get_report_run(report_run_id)
    if report is not None:
        if auth is not None and report.workspace_id != auth.workspace_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="report run not found",
            )
        if report.review_status != ReportReviewStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"report run is not approved for delivery (review_status={report.review_status})",  # noqa: E501
            )
        # DB mode: serve persisted artifact file if available
        artifact_uri = report.artifact_metadata.get("machine_json_uri") or report.output_uri
        if artifact_uri is not None:
            artifact_path = Path(str(artifact_uri))
            if artifact_path.exists():
                artifact_bytes = artifact_path.read_bytes()
                return Response(
                    content=artifact_bytes,
                    media_type="application/json",
                    headers={
                        "Content-Disposition": (
                            f'attachment; filename="report_{report_run_id}.json"'
                        )
                    },
                )
        # In-memory mode (or missing file): serialize the contract
        artifact_json = json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True)
        return Response(
            content=artifact_json.encode("utf-8"),
            media_type="application/json",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="report_{report_run_id}.json"'
                )
            },
        )
    job = services.async_report_jobs.get(report_run_id)
    if job is not None and job.status in (JobStatus.QUEUED, JobStatus.RUNNING):
        return JSONResponse(
            status_code=202,
            content={"status": "pending", "report_run_id": str(report_run_id)},
        )
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="report run not found")


def build_lineage_response(report: ReportRunContract) -> ReportLineageResponse:
    """Compute the full lineage response for a report run contract.

    Extracted for reuse by both the API route and the UI lineage page.
    """
    # Build a map from evidence_id -> list of claim_ids that cite it
    evidence_to_claims: dict[UUID, list[UUID]] = defaultdict(list)
    all_claims = _flat_claims(report)
    for claim in all_claims:
        for eid in claim.evidence_ids:
            evidence_to_claims[eid].append(claim.claim_id)

    # Build evidence lineage entries
    evidence_lineage: list[LineageEvidenceEntry] = [
        LineageEvidenceEntry(
            evidence_id=ev.evidence_id,
            source_id=ev.source_id,
            evidence_code=ev.evidence_code,
            domain=ev.domain,
            claim_ids=evidence_to_claims.get(ev.evidence_id, []),
        )
        for ev in report.evidence
    ]

    # Build claim lineage entries
    claim_lineage: list[LineageClaimEntry] = [
        LineageClaimEntry(
            claim_id=cl.claim_id,
            claim_code=cl.claim_code,
            domain=cl.domain,
            evidence_ids=cl.evidence_ids,
        )
        for cl in all_claims
    ]

    # Build sources from source_manifest; fall back to evidence if manifest is empty
    sources_map: dict[UUID, LineageSourceEntry] = {}
    for key, val in report.source_manifest.items():
        if not isinstance(val, dict):
            continue
        raw_id = val.get("source_id")
        if raw_id is None:
            continue
        try:
            sid = UUID(str(raw_id))
        except (ValueError, AttributeError):
            continue
        ingest_ids: list[UUID] = []
        for iid in val.get("ingest_run_ids", []):
            try:
                ingest_ids.append(UUID(str(iid)))
            except (ValueError, AttributeError):
                pass
        sources_map[sid] = LineageSourceEntry(
            source_id=sid,
            source_name=str(val.get("source_name", key)),
            ingest_run_ids=ingest_ids,
        )

    # Fall back: derive sources from evidence when manifest produced nothing
    if not sources_map:
        for ev in report.evidence:
            if ev.source_id not in sources_map:
                ingest_ids = [ev.source_ingest_run_id] if ev.source_ingest_run_id else []
                sources_map[ev.source_id] = LineageSourceEntry(
                    source_id=ev.source_id,
                    source_name=str(ev.source_id),
                    ingest_run_ids=ingest_ids,
                )
            elif ev.source_ingest_run_id and (
                ev.source_ingest_run_id not in sources_map[ev.source_id].ingest_run_ids
            ):
                sources_map[ev.source_id].ingest_run_ids.append(ev.source_ingest_run_id)

    return ReportLineageResponse(
        report_run_id=report.report_run_id,
        area_id=report.area_id,
        intent_code=report.intent_code.value,
        sources=list(sources_map.values()),
        evidence_lineage=evidence_lineage,
        claim_lineage=claim_lineage,
    )


@router.get("/{report_run_id}/lineage", response_model=ReportLineageResponse)
def get_report_run_lineage(
    report_run_id: UUID,
    services: ServicesDep,
    request_context: Request,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
    x_user_id: Annotated[str | None, Header(alias="X-User-Id")] = None,
) -> ReportLineageResponse:
    auth = _optional_report_auth_context(
        request_context,
        authorization=authorization,
        x_workspace_id=x_workspace_id,
        x_user_id=x_user_id,
    )
    report = services.report_service.get_report_run(report_run_id)
    if report is None or (auth is not None and report.workspace_id != auth.workspace_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="report run not found")
    return build_lineage_response(report)


@router.get("/{report_run_id}/diff", response_model=ReportRunDiffResponse)
def diff_report_runs(
    report_run_id: UUID,
    base_id: UUID,
    services: ServicesDep,
    request_context: Request,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
    x_user_id: Annotated[str | None, Header(alias="X-User-Id")] = None,
) -> ReportRunDiffResponse:
    auth = _optional_report_auth_context(
        request_context,
        authorization=authorization,
        x_workspace_id=x_workspace_id,
        x_user_id=x_user_id,
    )
    report = services.report_service.get_report_run(report_run_id)
    if report is None or (auth is not None and report.workspace_id != auth.workspace_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"report run '{report_run_id}' not found",
        )
    base = services.report_service.get_report_run(base_id)
    if base is None or (auth is not None and base.workspace_id != auth.workspace_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"base report run '{base_id}' not found",
        )
    same_area = report.area_id == base.area_id
    if not same_area:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="diff requires both report runs to share the same area_id",
        )

    all_report_claims = _flat_claims(report)
    all_base_claims = _flat_claims(base)
    report_codes = {c.claim_code for c in all_report_claims}
    base_codes = {c.claim_code for c in all_base_claims}

    report_sources = set(report.source_manifest.keys())
    base_sources = set(base.source_manifest.keys())

    report_ruleset = {c.ruleset_id for c in all_report_claims if c.ruleset_id}
    base_ruleset = {c.ruleset_id for c in all_base_claims if c.ruleset_id}
    ruleset_changed = report_ruleset != base_ruleset

    return ReportRunDiffResponse(
        report_run_id=report.report_run_id,
        base_report_run_id=base.report_run_id,
        area_id=report.area_id,
        same_area=same_area,
        ruleset_changed=ruleset_changed,
        added_claim_codes=sorted(report_codes - base_codes),
        removed_claim_codes=sorted(base_codes - report_codes),
        added_sources=sorted(report_sources - base_sources),
        removed_sources=sorted(base_sources - report_sources),
        evidence_count_delta=len(report.evidence) - len(base.evidence),
    )


def _job_log_context(
    report_run_id: UUID,
    area_id: UUID,
    intent_code: IntentCode,
) -> dict[str, str]:
    return {
        "report_run_id": str(report_run_id),
        "area_id": str(area_id),
        "intent_code": intent_code.value,
    }


def _live_connectors_enabled(request_context: Request) -> bool:
    settings = cast(Settings, request_context.app.state.settings)
    return settings.enable_live_connectors


def _optional_report_auth_context(
    request_context: Request,
    *,
    authorization: str | None,
    x_workspace_id: str | None,
    x_user_id: str | None,
) -> RequestAuthContext | None:
    settings = cast(Settings, request_context.app.state.settings)
    if (
        settings.report_auth_mode != "signed_token"
        and (not x_workspace_id or not x_user_id)
    ):
        return None
    return get_request_auth_context(
        request_context,
        authorization=authorization,
        x_workspace_id=x_workspace_id,
        x_user_id=x_user_id,
    )
