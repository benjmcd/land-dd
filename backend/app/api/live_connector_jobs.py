from __future__ import annotations

from dataclasses import dataclass

from app.api.dependencies import ApiServices
from app.api.live_connectors import (
    DS_001_REGISTRY_ID,
    DS_002_REGISTRY_ID,
    DS_003_REGISTRY_ID,
    DS_004_REGISTRY_ID,
    FemaNfhlOrchestrationResult,
    NwiOrchestrationResult,
    SsurgoOrchestrationResult,
    UsgsTnmOrchestrationResult,
    orchestrate_fema_nfhl_for_area,
    orchestrate_nwi_for_area,
    orchestrate_ssurgo_for_area,
    orchestrate_usgs_tnm_for_area,
)
from app.connectors.live_jobs import LiveConnectorBbox, LiveConnectorJobRecord
from app.domain.area_contracts import AreaContract


@dataclass(frozen=True)
class LiveConnectorJobRunResult:
    job: LiveConnectorJobRecord
    connector_result: (
        UsgsTnmOrchestrationResult
        | FemaNfhlOrchestrationResult
        | SsurgoOrchestrationResult
        | NwiOrchestrationResult
        | None
    )
    succeeded: bool
    error: str | None = None


def run_next_live_connector_job(
    *,
    services: ApiServices,
    worker_id: str,
) -> LiveConnectorJobRunResult | None:
    job = services.live_connector_jobs.lease_next(worker_id=worker_id)
    if job is None:
        return None
    try:
        area = services.area_service.get(job.area_id)
        if area is None:
            raise ValueError(f"area '{job.area_id}' is not registered")
        if job.workspace_id is not None and area.workspace_id != job.workspace_id:
            raise ValueError("area not found")
        area_for_job = _area_with_job_bbox(area, job.bbox)
        if job.source_registry_id == DS_001_REGISTRY_ID:
            connector_result: (
                UsgsTnmOrchestrationResult
                | FemaNfhlOrchestrationResult
                | SsurgoOrchestrationResult
                | NwiOrchestrationResult
            )
            connector_result = orchestrate_usgs_tnm_for_area(
                services=services,
                area=area_for_job,
                max_sample_points=job.max_features,
            )
        elif job.source_registry_id == DS_002_REGISTRY_ID:
            connector_result = orchestrate_fema_nfhl_for_area(
                services=services,
                area=area_for_job,
                max_features=job.max_features,
            )
        elif job.source_registry_id == DS_003_REGISTRY_ID:
            connector_result = orchestrate_ssurgo_for_area(
                services=services,
                area=area_for_job,
                max_rows=job.max_features,
            )
        elif job.source_registry_id == DS_004_REGISTRY_ID:
            connector_result = orchestrate_nwi_for_area(
                services=services,
                area=area_for_job,
                max_features=job.max_features,
            )
        else:
            raise ValueError(f"unsupported live connector source: {job.source_registry_id}")
        finished = services.live_connector_jobs.mark_succeeded(
            job.job_id,
            connector_ingest_run_id=connector_result.ingest_run_id,
            connector_review_status=connector_result.queue_item.status.value,
            request_url=connector_result.request_url,
        )
        return LiveConnectorJobRunResult(
            job=finished,
            connector_result=connector_result,
            succeeded=True,
        )
    except Exception as exc:  # noqa: BLE001
        failed = services.live_connector_jobs.mark_failed(
            job.job_id,
            error_msg=str(exc),
        )
        return LiveConnectorJobRunResult(
            job=failed,
            connector_result=None,
            succeeded=False,
            error=str(exc),
        )


def _area_with_job_bbox(
    area: AreaContract,
    bbox: LiveConnectorBbox | None,
) -> AreaContract:
    if bbox is None:
        return area
    return area.model_copy(
        update={
            "geom_geojson": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [bbox.xmin, bbox.ymin],
                        [bbox.xmax, bbox.ymin],
                        [bbox.xmax, bbox.ymax],
                        [bbox.xmin, bbox.ymax],
                        [bbox.xmin, bbox.ymin],
                    ]
                ],
            }
        }
    )


__all__ = [
    "LiveConnectorJobRunResult",
    "run_next_live_connector_job",
]
