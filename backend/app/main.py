from __future__ import annotations

from fastapi import FastAPI

from app.api.areas import router as areas_router
from app.api.connectors import router as connectors_router
from app.api.connectors import runs_router as connector_runs_router
from app.api.dependencies import create_api_services, get_db_services, get_services
from app.api.evidence import router as evidence_router
from app.api.health import router as health_router
from app.api.reports import router as reports_router
from app.api.sources import router as sources_router
from app.core.config import Settings, get_settings


def create_app(
    settings: Settings | None = None,
    *,
    use_db_services: bool | None = False,
) -> FastAPI:
    resolved = settings or get_settings()
    db_services_enabled = (
        resolved.storage_backend == "postgres"
        if use_db_services is None
        else use_db_services
    )
    app = FastAPI(
        title=resolved.app_name,
        version="0.1.0",
        description="Intent-aware land/locality due-diligence backend scaffold.",
    )
    app.state.settings = resolved
    app.state.object_store_root = resolved.object_store_root
    app.state.storage_backend = "postgres" if db_services_enabled else "memory"
    if db_services_enabled:
        app.dependency_overrides[get_services] = get_db_services
    else:
        app.state.services = create_api_services()
    app.include_router(health_router)
    app.include_router(sources_router)
    app.include_router(areas_router)
    app.include_router(connectors_router)
    app.include_router(connector_runs_router)
    app.include_router(evidence_router)
    app.include_router(reports_router)
    return app


app = create_app(use_db_services=None)
