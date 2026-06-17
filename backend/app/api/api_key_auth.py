from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from string import hexdigits
from urllib.parse import quote

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from starlette.types import ASGIApp

from app.api.auth_audit import (
    ApiKeyAuthAuditEvent,
    ApiKeyAuthAuditLog,
    ApiKeyAuthAuditOutcome,
)
from app.api.secret_specs import matches_any_secret_spec, matches_secret_spec

API_KEY_HEADER = "X-API-Key"
UI_API_KEY_COOKIE = "land_dd_ui_api_key"
UI_API_KEY_COOKIE_MAX_AGE_SECONDS = 8 * 60 * 60
UI_API_KEY_COOKIE_TOKEN_PREFIX = "land-dd-ui-api-key-v1"
UI_CSRF_FORM_FIELD = "csrf_token"
UI_CSRF_TOKEN_PREFIX = "land-dd-ui-csrf-v1"
PUBLIC_PATHS = frozenset({"/health", "/version"})
PUBLIC_UI_AUTH_PATHS = frozenset({"/ui/auth"})
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
class ApiKeyDigestMatch:
    key_id: str | None
    source: str
    secret_spec: str


@dataclass(frozen=True)
class ApiKeyAuthConfig:
    required: bool
    api_keys: frozenset[str]
    api_key_credentials: tuple[ApiKeyCredential, ...] = ()
    audit_log: ApiKeyAuthAuditLog | None = None
    ui_cookie_signing_secret: str | None = None
    ui_cookie_secure: bool = False


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
            or request.url.path in PUBLIC_UI_AUTH_PATHS
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
            if _is_ui_path(request.url.path):
                return _ui_auth_error_response("API key auth is not configured", 503)
            return JSONResponse(
                {"detail": "API key auth is not configured"},
                status_code=503,
            )

        provided, auth_source = _provided_api_key(request)
        if provided is None:
            if not _record_api_key_audit_event(
                self._config.audit_log,
                request,
                outcome=ApiKeyAuthAuditOutcome.MISSING,
                status_code=401,
            ):
                return _audit_failure_response()
            if _is_ui_path(request.url.path):
                return _ui_login_redirect(request)
            return JSONResponse(
                {"detail": "API key is required"},
                status_code=401,
            )
        if auth_source == "ui_cookie":
            match = verify_ui_api_key_cookie_token(provided, self._config)
        else:
            match = _match_api_key(provided, self._config)
        if match is None:
            if not _record_api_key_audit_event(
                self._config.audit_log,
                request,
                outcome=ApiKeyAuthAuditOutcome.INVALID,
                status_code=403,
            ):
                return _audit_failure_response()
            if _is_ui_path(request.url.path):
                return _ui_login_redirect()
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
            source=auth_source if auth_source == "ui_cookie" else match.source,
        ):
            return _audit_failure_response()
        request.state.api_key_auth_source = (
            auth_source if auth_source == "ui_cookie" else match.source
        )
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


def create_ui_api_key_cookie_token(
    provided: str,
    config: ApiKeyAuthConfig,
    *,
    issued_at: datetime | None = None,
) -> str:
    digest = _api_key_digest(provided)
    match = _match_api_key_digest(digest, config)
    if match is None:
        raise ValueError("API key is invalid")
    now = issued_at or datetime.now(UTC)
    payload: dict[str, object] = {
        "digest": digest,
        "exp": int((now + timedelta(seconds=UI_API_KEY_COOKIE_MAX_AGE_SECONDS)).timestamp()),
    }
    payload_segment = _base64url_encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    signed_part = f"{UI_API_KEY_COOKIE_TOKEN_PREFIX}.{payload_segment}"
    return f"{signed_part}.{_sign_ui_cookie_token(signed_part, config)}"


def verify_ui_api_key_cookie_token(
    token: str,
    config: ApiKeyAuthConfig,
    *,
    now: datetime | None = None,
) -> ApiKeyAuthMatch | None:
    parts = token.split(".")
    if len(parts) != 3 or parts[0] != UI_API_KEY_COOKIE_TOKEN_PREFIX:
        return None
    signed_part = f"{parts[0]}.{parts[1]}"
    payload = _decode_ui_cookie_payload(parts[1])
    if payload is None or not _ui_cookie_payload_is_unexpired(
        payload,
        now or datetime.now(UTC),
    ):
        return None
    digest = payload.get("digest")
    if not isinstance(digest, str) or not _is_sha256_digest(digest):
        return None
    match = _match_api_key_digest(digest, config)
    if match is None:
        return None
    if config.ui_cookie_signing_secret is None:
        return None
    expected_signature = _sign_ui_cookie_token(signed_part, config)
    if not hmac.compare_digest(parts[2], expected_signature):
        return None
    return ApiKeyAuthMatch(key_id=match.key_id, source=match.source)


def create_ui_csrf_token(ui_cookie_token: str, config: ApiKeyAuthConfig) -> str:
    return _sign_ui_csrf_token(ui_cookie_token, config)


def verify_ui_csrf_token(
    ui_cookie_token: str,
    csrf_token: str | None,
    config: ApiKeyAuthConfig,
) -> bool:
    if csrf_token is None or config.ui_cookie_signing_secret is None:
        return False
    expected = _sign_ui_csrf_token(ui_cookie_token, config)
    return hmac.compare_digest(csrf_token, expected)


def _match_api_key_digest(
    digest: str,
    config: ApiKeyAuthConfig,
) -> ApiKeyDigestMatch | None:
    for credential in config.api_key_credentials:
        if _secret_spec_matches_digest(credential.secret_spec, digest):
            return ApiKeyDigestMatch(
                key_id=credential.key_id,
                source="api_key_specs",
                secret_spec=credential.secret_spec,
            )
    for secret_spec in config.api_keys:
        if _secret_spec_matches_digest(secret_spec, digest):
            return ApiKeyDigestMatch(
                key_id=None,
                source="api_keys",
                secret_spec=secret_spec,
            )
    return None


def _secret_spec_matches_digest(secret_spec: str, digest: str) -> bool:
    if secret_spec.startswith("sha256:"):
        expected_digest = secret_spec.removeprefix("sha256:")
    else:
        expected_digest = _api_key_digest(secret_spec)
    return hmac.compare_digest(expected_digest, digest)


def _api_key_digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _decode_ui_cookie_payload(payload_segment: str) -> dict[str, object] | None:
    try:
        payload = json.loads(_base64url_decode(payload_segment).decode("utf-8"))
    except (binascii.Error, ValueError, UnicodeDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _ui_cookie_payload_is_unexpired(
    payload: dict[str, object],
    now: datetime,
) -> bool:
    expires_at = payload.get("exp")
    return isinstance(expires_at, int) and expires_at > int(now.timestamp())


def _is_sha256_digest(value: str) -> bool:
    return len(value) == 64 and all(char in hexdigits for char in value)


def _sign_ui_cookie_token(signed_part: str, config: ApiKeyAuthConfig) -> str:
    if config.ui_cookie_signing_secret is None:
        raise ValueError("UI auth cookie signing secret is not configured")
    signing_key = hashlib.sha256(
        f"{UI_API_KEY_COOKIE_TOKEN_PREFIX}:{config.ui_cookie_signing_secret}".encode()
    ).digest()
    return _base64url_encode(
        hmac.new(signing_key, signed_part.encode("utf-8"), hashlib.sha256).digest()
    )


def _sign_ui_csrf_token(ui_cookie_token: str, config: ApiKeyAuthConfig) -> str:
    if config.ui_cookie_signing_secret is None:
        raise ValueError("UI auth cookie signing secret is not configured")
    signing_key = hashlib.sha256(
        f"{UI_CSRF_TOKEN_PREFIX}:{config.ui_cookie_signing_secret}".encode()
    ).digest()
    return _base64url_encode(
        hmac.new(signing_key, ui_cookie_token.encode("utf-8"), hashlib.sha256).digest()
    )


def _base64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _base64url_decode(encoded: str) -> bytes:
    padding = "=" * (-len(encoded) % 4)
    return base64.urlsafe_b64decode(f"{encoded}{padding}".encode("ascii"))


def _provided_api_key(request: Request) -> tuple[str | None, str | None]:
    header_value = _clean_api_key(request.headers.get(API_KEY_HEADER))
    if header_value is not None:
        return header_value, "header"
    if _is_ui_path(request.url.path):
        cookie_value = _clean_api_key(request.cookies.get(UI_API_KEY_COOKIE))
        if cookie_value is not None:
            return cookie_value, "ui_cookie"
    return None, None


def _is_ui_path(path: str) -> bool:
    return path == "/ui" or path.startswith("/ui/")


def _ui_login_redirect(request: Request | None = None) -> RedirectResponse:
    location = "/ui/auth"
    if request is not None:
        next_path = _ui_next_path(request)
        if next_path is not None:
            location = f"{location}?next={quote(next_path, safe='')}"
    return RedirectResponse(location, status_code=303)


def _ui_next_path(request: Request) -> str | None:
    path = request.url.path
    if not _is_ui_path(path):
        return None
    query = request.url.query
    if query:
        return f"{path}?{query}"
    return path


def _ui_auth_error_response(message: str, status_code: int) -> HTMLResponse:
    return HTMLResponse(
        "<!DOCTYPE html><html lang='en'><head><meta charset='UTF-8'>"
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        "<title>UI access unavailable</title></head><body>"
        "<h1>UI access unavailable</h1>"
        f"<p>{message}</p>"
        "<a href='/ui/auth'>Back to sign in</a>"
        "</body></html>",
        status_code=status_code,
    )


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
