from __future__ import annotations

from fastapi import FastAPI

from app.api.areas import router as areas_router
from app.api.dependencies import create_api_services
from app.api.evidence import router as evidence_router
from app.api.health import router as health_router
from app.api.reports import router as reports_router
from app.api.sources import router as sources_router
from app.core.config import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or get_settings()
    app = FastAPI(
        title=resolved.app_name,
        version="0.1.0",
        description="Intent-aware land/locality due-diligence backend scaffold.",
    )
    app.state.services = create_api_services()
    app.include_router(health_router)
    app.include_router(sources_router)
    app.include_router(areas_router)
    app.include_router(evidence_router)
    app.include_router(reports_router)
    return app


app = create_app()
