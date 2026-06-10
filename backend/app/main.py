from __future__ import annotations

from fastapi import FastAPI

from app.api.api_key_auth import ApiKeyAuthConfig, ApiKeyAuthMiddleware, ApiKeyCredential
from app.api.areas import router as areas_router
from app.api.auth_audit import ApiKeyAuthAuditLog, SqlAlchemyApiKeyAuthAuditLog
from app.api.connectors import review_queue_router as connector_review_queue_router
from app.api.connectors import router as connectors_router
from app.api.dependencies import create_api_services, get_db_services, get_services
from app.api.evidence import router as evidence_router
from app.api.health import router as health_router
from app.api.intake import router as intake_router
from app.api.metrics import router as metrics_router
from app.api.operations import router as operations_router
from app.api.rate_limit import RateLimitConfig, RateLimitMiddleware
from app.api.reports import router as reports_router
from app.api.sources import router as sources_router
from app.api.ui import router as ui_router
from app.api.ui_operations import router as ui_operations_router
from app.api.ui_review import router as ui_review_router
from app.core.config import Settings, get_settings
from app.core.logging import configure_json_logging
from app.core.metrics import MetricsMiddleware, RuntimeMetrics
from app.db.engine import get_session_factory


def create_app(
    settings: Settings | None = None,
    *,
    use_db_services: bool | None = None,
    api_key_audit_log: ApiKeyAuthAuditLog | None = None,
) -> FastAPI:
    resolved = settings or get_settings()
    resolved_use_db_services = (
        resolved.use_db_services if use_db_services is None else use_db_services
    )
    configure_json_logging(resolved.log_level)
    app = FastAPI(
        title=resolved.app_name,
        version="0.1.0",
        description="Intent-aware land/locality due-diligence backend scaffold.",
    )
    app.state.settings = resolved
    app.state.object_store_root = resolved.object_store_root
    app.state.use_db_services = resolved_use_db_services
    app.state.metrics = RuntimeMetrics() if resolved.enable_metrics else None
    app.add_middleware(
        ApiKeyAuthMiddleware,
        config=ApiKeyAuthConfig(
            required=resolved.require_api_key,
            api_keys=resolved.parsed_api_keys() if resolved.require_api_key else frozenset(),
            api_key_credentials=(
                tuple(
                    ApiKeyCredential(key_id=spec.key_id, secret_spec=spec.secret_spec)
                    for spec in resolved.parsed_api_key_specs()
                    if spec.status == "active"
                )
                if resolved.require_api_key
                else ()
            ),
            audit_log=(
                api_key_audit_log
                if api_key_audit_log is not None
                else _build_api_key_audit_log(
                    require_api_key=resolved.require_api_key,
                    use_db_services=resolved_use_db_services,
                )
            ),
        ),
    )
    max_requests, window_seconds = (
        resolved.parsed_rate_limit()
        if resolved.enable_rate_limit
        else (resolved.rate_limit_requests, resolved.rate_limit_window_seconds)
    )
    app.add_middleware(
        RateLimitMiddleware,
        config=RateLimitConfig(
            enabled=resolved.enable_rate_limit,
            max_requests=max_requests,
            window_seconds=window_seconds,
        ),
    )
    if isinstance(app.state.metrics, RuntimeMetrics):
        app.add_middleware(MetricsMiddleware, metrics=app.state.metrics)
    if resolved_use_db_services:
        app.dependency_overrides[get_services] = get_db_services
    else:
        app.state.services = create_api_services(resolved)
    app.include_router(health_router)
    app.include_router(sources_router)
    app.include_router(areas_router)
    app.include_router(evidence_router)
    app.include_router(reports_router)
    app.include_router(intake_router)
    app.include_router(connectors_router)
    app.include_router(connector_review_queue_router)
    app.include_router(operations_router)
    app.include_router(metrics_router)
    app.include_router(ui_router)
    app.include_router(ui_operations_router)
    app.include_router(ui_review_router)
    return app


def _build_api_key_audit_log(
    *,
    require_api_key: bool,
    use_db_services: bool,
) -> ApiKeyAuthAuditLog | None:
    if not require_api_key or not use_db_services:
        return None
    return SqlAlchemyApiKeyAuthAuditLog(get_session_factory())


app = create_app()
