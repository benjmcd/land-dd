from __future__ import annotations

import secrets

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
from app.api.operator_cases import router as operator_cases_router
from app.api.rate_limit import RateLimitConfig, RateLimitMiddleware
from app.api.reports import router as reports_router
from app.api.sources import router as sources_router
from app.api.ui import router as ui_router
from app.api.ui_auth import router as ui_auth_router
from app.api.ui_lineage import router as ui_lineage_router
from app.api.ui_live_connector_jobs import router as ui_live_connector_jobs_router
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
    resolved.validate_secret_hygiene()
    _validate_runtime_state_config(resolved, use_db_services=resolved_use_db_services)
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
    ui_auth_routes_enabled = _include_ui_auth_router(resolved)
    app.state.ui_auth_routes_enabled = ui_auth_routes_enabled
    api_key_auth_config = ApiKeyAuthConfig(
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
        ui_cookie_signing_secret=_ui_cookie_signing_secret(resolved),
        ui_cookie_secure=_ui_auth_cookie_secure(resolved),
    )
    app.state.api_key_auth_config = api_key_auth_config
    app.add_middleware(
        ApiKeyAuthMiddleware,
        config=api_key_auth_config,
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
    app.include_router(operator_cases_router)
    if ui_auth_routes_enabled:
        app.include_router(ui_auth_router)
    app.include_router(ui_router)
    app.include_router(ui_lineage_router)
    app.include_router(ui_live_connector_jobs_router)
    app.include_router(ui_operations_router)
    app.include_router(ui_review_router)
    return app


def _ui_auth_cookie_secure(settings: Settings) -> bool:
    if settings.ui_auth_cookie_secure:
        return True
    return not _is_local_app_env(settings)


def _include_ui_auth_router(settings: Settings) -> bool:
    return settings.require_api_key or not _is_local_app_env(settings)


def _validate_runtime_state_config(
    settings: Settings,
    *,
    use_db_services: bool,
) -> None:
    if use_db_services and not settings.database_url.strip():
        raise ValueError("DATABASE_URL is required when USE_DB_SERVICES is true.")
    if not use_db_services and not _is_local_app_env(settings):
        raise ValueError(
            "USE_DB_SERVICES=true is required outside local/dev/development/test "
            "APP_ENV values so operator state is durable across restarts."
        )


def _ui_cookie_signing_secret(settings: Settings) -> str:
    if settings.ui_auth_cookie_secret and settings.ui_auth_cookie_secret.strip():
        return settings.ui_auth_cookie_secret
    if settings.require_api_key and not _is_local_app_env(settings):
        raise ValueError(
            "UI_AUTH_COOKIE_SECRET is required when REQUIRE_API_KEY is true "
            "outside local/dev/development/test APP_ENV values."
        )
    return secrets.token_urlsafe(48)


def _is_local_app_env(settings: Settings) -> bool:
    return settings.is_local_app_env()


def _build_api_key_audit_log(
    *,
    require_api_key: bool,
    use_db_services: bool,
) -> ApiKeyAuthAuditLog | None:
    if not require_api_key or not use_db_services:
        return None
    return SqlAlchemyApiKeyAuthAuditLog(get_session_factory())


app = create_app()
