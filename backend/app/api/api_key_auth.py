from __future__ import annotations

import logging
from dataclasses import dataclass

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from app.api.auth_audit import (
    ApiKeyAuthAuditEvent,
    ApiKeyAuthAuditLog,
    ApiKeyAuthAuditOutcome,
)
from app.api.secret_specs import matches_any_secret_spec, matches_secret_spec

API_KEY_HEADER = "X-API-Key"
PUBLIC_PATHS = frozenset({"/health", "/version"})
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ApiKeyCredential:
    key_id: str
    secret_spec: str


@dataclass(frozen=True)
class ApiKeyAuthMatch:
    key_id: str | None
    source: str


@dataclass(frozen=True)
class ApiKeyAuthConfig:
    required: bool
    api_keys: frozenset[str]
    api_key_credentials: tuple[ApiKeyCredential, ...] = ()
    audit_log: ApiKeyAuthAuditLog | None = None


class ApiKeyAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, *, config: ApiKeyAuthConfig) -> None:
        super().__init__(app)
        self._config = config

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        if (
            not self._config.required
            or request.scope["type"] != "http"
            or request.url.path in PUBLIC_PATHS
        ):
            return await call_next(request)

        if not self._config.api_keys:
            if not _record_api_key_audit_event(
                self._config.audit_log,
                request,
                outcome=ApiKeyAuthAuditOutcome.UNCONFIGURED,
                status_code=503,
            ):
                return _audit_failure_response()
            return JSONResponse(
                {"detail": "API key auth is not configured"},
                status_code=503,
            )

        provided = _clean_api_key(request.headers.get(API_KEY_HEADER))
        if provided is None:
            if not _record_api_key_audit_event(
                self._config.audit_log,
                request,
                outcome=ApiKeyAuthAuditOutcome.MISSING,
                status_code=401,
            ):
                return _audit_failure_response()
            return JSONResponse(
                {"detail": "API key is required"},
                status_code=401,
            )
        match = _match_api_key(provided, self._config)
        if match is None:
            if not _record_api_key_audit_event(
                self._config.audit_log,
                request,
                outcome=ApiKeyAuthAuditOutcome.INVALID,
                status_code=403,
            ):
                return _audit_failure_response()
            return JSONResponse(
                {"detail": "API key is invalid"},
                status_code=403,
            )
        if not _record_api_key_audit_event(
            self._config.audit_log,
            request,
            outcome=ApiKeyAuthAuditOutcome.ACCEPTED,
            status_code=200,
            key_id=match.key_id,
            source=match.source,
        ):
            return _audit_failure_response()
        return await call_next(request)


def _clean_api_key(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _match_api_key(provided: str, config: ApiKeyAuthConfig) -> ApiKeyAuthMatch | None:
    for credential in config.api_key_credentials:
        if matches_secret_spec(provided, credential.secret_spec):
            return ApiKeyAuthMatch(key_id=credential.key_id, source="api_key_specs")
    if matches_any_secret_spec(provided, config.api_keys):
        return ApiKeyAuthMatch(key_id=None, source="api_keys")
    return None


def _matches_api_key(provided: str, api_keys: frozenset[str]) -> bool:
    return matches_any_secret_spec(provided, api_keys)


def _record_api_key_audit_event(
    audit_log: ApiKeyAuthAuditLog | None,
    request: Request,
    *,
    outcome: ApiKeyAuthAuditOutcome,
    status_code: int,
    key_id: str | None = None,
    source: str | None = None,
) -> bool:
    event = ApiKeyAuthAuditEvent(
        outcome=outcome,
        status_code=status_code,
        method=request.method,
        path=request.url.path,
        key_id=key_id,
        source=source,
        ip_address=request.client.host if request.client is not None else None,
        user_agent=request.headers.get("user-agent"),
    )
    logger.info(
        "api key auth",
        extra={
            "event_type": "api_key_auth",
            "outcome": outcome.value,
            "status_code": status_code,
            "api_key_id": key_id,
            "api_key_source": source,
            "method": request.method,
            "path": request.url.path,
        },
    )
    if audit_log is None:
        return True
    try:
        audit_log.record(event)
    except Exception:
        logger.exception(
            "api key audit persistence failed",
            extra={
                "event_type": "api_key_auth_persistence_failed",
                "outcome": outcome.value,
                "status_code": 503,
                "api_key_id": key_id,
                "api_key_source": source,
                "method": request.method,
                "path": request.url.path,
            },
        )
        return False
    return True


def _audit_failure_response() -> JSONResponse:
    return JSONResponse(
        {"detail": "API key audit logging failed"},
        status_code=503,
    )
