from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status

from app.core.metrics import RuntimeMetrics

router = APIRouter(tags=["metrics"])


@router.get("/metrics")
def metrics(request: Request) -> dict[str, object]:
    runtime_metrics = getattr(request.app.state, "metrics", None)
    if not isinstance(runtime_metrics, RuntimeMetrics):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="runtime metrics are not enabled",
        )
    return runtime_metrics.snapshot()
