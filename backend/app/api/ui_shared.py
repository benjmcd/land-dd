"""Shared HTML/CSS helpers for the operator UI modules.

All four UI modules (ui, ui_review, ui_operations, ui_lineage) share:
- A base CSS block (body, h1, h2, table, th/td, a, .meta, .error-page)
- An error-page builder
- A reviewer-credential form-fields helper

Zero routes are defined here.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import html as _html
import json
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol, cast

from fastapi import HTTPException
from fastapi.responses import HTMLResponse
from starlette.requests import Request
from starlette.responses import Response

from app.api.api_key_auth import (
    UI_API_KEY_COOKIE,
    UI_CSRF_FORM_FIELD,
    ApiKeyAuthConfig,
    create_ui_csrf_token,
    verify_ui_csrf_token,
)
from app.api.reviewer_auth import ReviewerPrincipal, require_reviewer_scope

UI_REVIEWER_COOKIE = "land_dd_ui_reviewer"
UI_REVIEWER_COOKIE_MAX_AGE_SECONDS = 8 * 60 * 60
UI_REVIEWER_COOKIE_TOKEN_PREFIX = "land-dd-ui-reviewer-v1"


class ReviewerAuthSessionProtocol(Protocol):
    def __call__(
        self,
        reviewer_id: str | None = None,
        reviewer_token: str | None = None,
    ) -> ReviewerPrincipal: ...

    def principal_from_session(
        self,
        *,
        reviewer_id: str,
        scopes: Iterable[str],
        session_binding: str,
        signing_secret: str,
    ) -> ReviewerPrincipal: ...

    def session_binding(self, *, reviewer_id: str, signing_secret: str) -> str: ...


class UiReviewerServicesProtocol(Protocol):
    @property
    def reviewer_auth(self) -> ReviewerAuthSessionProtocol: ...


@dataclass(frozen=True)
class UiReviewerAuthResult:
    principal: ReviewerPrincipal
    from_submitted_credentials: bool


# ---------------------------------------------------------------------------
# Base CSS — common to every operator page
# ---------------------------------------------------------------------------

BASE_CSS = (
    "body { font-family: system-ui, sans-serif; max-width: 960px; margin: 2rem auto;"
    " padding: 0 1rem; }\n"
    "h1 { color: #2c3e50; } h2 { color: #34495e; border-bottom: 1px solid #eee; }\n"
    "table { border-collapse: collapse; width: 100%; }\n"
    "th, td { text-align: left; padding: 0.5rem 1rem; border-bottom: 1px solid #dee2e6; }\n"
    "th { background: #f8f9fa; }\n"
    "a { color: #2c3e50; }\n"
    ".meta { background: #f8f9fa; padding: 1rem; border-radius: 4px;"
    " font-family: monospace; font-size: 0.9rem; }\n"
    ".reviewer-session { color: #495766; display: flex; flex-wrap: wrap;"
    " align-items: baseline; gap: 0.25rem 0.45rem; line-height: 1.45;"
    " margin: 0.35rem 0; }\n"
    ".reviewer-session.warning { display: block; }\n"
    ".reviewer-session-link { background: transparent; border: 0; color: #2c3e50;"
    " display: inline; padding: 0; text-decoration: underline; }\n"
    ".error-page { background: #f8d7da; border: 1px solid #f5c6cb; padding: 1rem;"
    " border-radius: 4px; }\n"
)


def build_css(*extra: str) -> str:
    """Return BASE_CSS optionally followed by additional page-specific rules."""
    if extra:
        return BASE_CSS + "\n".join(extra)
    return BASE_CSS


# ---------------------------------------------------------------------------
# Page head and error-page builders
# ---------------------------------------------------------------------------


def page_head(
    title: str,
    *,
    css: str | None = BASE_CSS,
    refresh_url: str | None = None,
) -> str:
    """Return a viewport-aware HTML ``<head>`` block for server-rendered UI pages."""
    head = (
        "<head><meta charset='UTF-8'>"
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{_html.escape(title)}</title>"
    )
    if refresh_url is not None:
        refresh_url_esc = _html.escape(refresh_url, quote=True)
        head += f"<meta http-equiv='refresh' content='1;url={refresh_url_esc}'>"
    if css is not None:
        head += f"<style>{css}</style>"
    return f"{head}</head>"


def error_page(
    title: str,
    message: str,
    back_url: str,
    status_code: int,
    *,
    css: str = BASE_CSS,
) -> HTMLResponse:
    """Return a minimal HTML error page with the given title, message, and back link.

    The ``css`` parameter lets callers pass a page-specific stylesheet so the
    error page matches the surrounding UI.  Defaults to BASE_CSS.
    """
    body = (
        "<!DOCTYPE html><html lang='en'>"
        f"{page_head(title, css=css)}"
        "<body>"
        f"<div class='error-page'><h1>{_html.escape(title)}</h1>"
        f"<p>{_html.escape(message)}</p>"
        f"<a href='{_html.escape(back_url, quote=True)}'>Back</a>"
        "</div></body></html>"
    )
    return HTMLResponse(content=body, status_code=status_code)


def csrf_form_field(request: Request) -> str:
    """Return a hidden CSRF field for cookie-authenticated UI forms."""
    if not ui_csrf_required(request):
        return ""
    cookie_token = request.cookies.get(UI_API_KEY_COOKIE)
    if cookie_token is None:
        return ""
    config = _auth_config(request)
    token = create_ui_csrf_token(cookie_token, config)
    return (
        f'<input name="{UI_CSRF_FORM_FIELD}" type="hidden" '
        f'value="{_html.escape(token, quote=True)}">'
    )


def require_ui_csrf(
    request: Request,
    submitted_token: str | None,
    *,
    back_url: str,
    css: str = BASE_CSS,
) -> HTMLResponse | None:
    """Fail closed for unsafe UI posts authenticated by the browser cookie."""
    if not ui_csrf_required(request):
        return None
    cookie_token = request.cookies.get(UI_API_KEY_COOKIE)
    if cookie_token is not None and verify_ui_csrf_token(
        cookie_token,
        submitted_token,
        _auth_config(request),
    ):
        return None
    return error_page(
        "Security Check Failed",
        "Refresh the page and retry the action.",
        back_url,
        403,
        css=css,
    )


def ui_csrf_required(request: Request) -> bool:
    return getattr(request.state, "api_key_auth_source", None) == "ui_cookie"


def _auth_config(request: Request) -> ApiKeyAuthConfig:
    return cast(ApiKeyAuthConfig, request.app.state.api_key_auth_config)


# ---------------------------------------------------------------------------
# Reviewer session and credential form fields
# ---------------------------------------------------------------------------


def create_ui_reviewer_cookie_token(
    principal: ReviewerPrincipal,
    services: UiReviewerServicesProtocol,
    config: ApiKeyAuthConfig,
    *,
    issued_at: datetime | None = None,
) -> str:
    if config.ui_cookie_signing_secret is None:
        raise ValueError("UI reviewer cookie signing secret is not configured")
    now = issued_at or datetime.now(UTC)
    payload: dict[str, object] = {
        "rid": principal.reviewer_id,
        "scopes": sorted(principal.scopes),
        "sb": services.reviewer_auth.session_binding(
            reviewer_id=principal.reviewer_id,
            signing_secret=config.ui_cookie_signing_secret,
        ),
        "exp": int(
            (now + timedelta(seconds=UI_REVIEWER_COOKIE_MAX_AGE_SECONDS)).timestamp()
        ),
    }
    payload_segment = _base64url_encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    signed_part = f"{UI_REVIEWER_COOKIE_TOKEN_PREFIX}.{payload_segment}"
    return f"{signed_part}.{_sign_ui_reviewer_token(signed_part, config)}"


def verify_ui_reviewer_cookie_token(
    token: str,
    services: UiReviewerServicesProtocol,
    config: ApiKeyAuthConfig,
    *,
    now: datetime | None = None,
) -> ReviewerPrincipal | None:
    parts = token.split(".")
    if len(parts) != 3 or parts[0] != UI_REVIEWER_COOKIE_TOKEN_PREFIX:
        return None
    signed_part = f"{parts[0]}.{parts[1]}"
    payload = _decode_ui_reviewer_payload(parts[1])
    if payload is None or not _ui_reviewer_payload_is_unexpired(
        payload,
        now or datetime.now(UTC),
    ):
        return None
    if config.ui_cookie_signing_secret is None:
        return None
    expected_signature = _sign_ui_reviewer_token(signed_part, config)
    if not hmac.compare_digest(parts[2], expected_signature):
        return None
    reviewer_id = payload.get("rid")
    scopes = payload.get("scopes")
    session_binding = payload.get("sb")
    if (
        not isinstance(reviewer_id, str)
        or not isinstance(scopes, list)
        or not isinstance(session_binding, str)
    ):
        return None
    if not all(isinstance(scope, str) for scope in scopes):
        return None
    try:
        return services.reviewer_auth.principal_from_session(
            reviewer_id=reviewer_id,
            scopes=[cast(str, scope) for scope in scopes],
            session_binding=session_binding,
            signing_secret=config.ui_cookie_signing_secret,
        )
    except (HTTPException, ValueError, TypeError):
        return None


def ui_reviewer_principal_from_cookie(
    request: Request,
    services: UiReviewerServicesProtocol,
) -> ReviewerPrincipal | None:
    cookie_token = request.cookies.get(UI_REVIEWER_COOKIE)
    if cookie_token is None:
        return None
    return verify_ui_reviewer_cookie_token(cookie_token, services, _auth_config(request))


def require_ui_reviewer(
    request: Request,
    services: UiReviewerServicesProtocol,
    *,
    reviewer_id: str | None,
    reviewer_token: str | None,
    required_scope: str,
) -> UiReviewerAuthResult:
    if _submitted_reviewer_credentials_present(reviewer_id, reviewer_token):
        principal = services.reviewer_auth(
            reviewer_id=reviewer_id,
            reviewer_token=reviewer_token,
        )
        require_reviewer_scope(principal, required_scope)
        return UiReviewerAuthResult(
            principal=principal,
            from_submitted_credentials=True,
        )
    session_principal = ui_reviewer_principal_from_cookie(request, services)
    if session_principal is None:
        principal = services.reviewer_auth(
            reviewer_id=reviewer_id,
            reviewer_token=reviewer_token,
        )
    else:
        principal = session_principal
    require_reviewer_scope(principal, required_scope)
    return UiReviewerAuthResult(principal=principal, from_submitted_credentials=False)


def attach_ui_reviewer_session_cookie(
    response: Response,
    request: Request,
    services: UiReviewerServicesProtocol,
    auth_result: UiReviewerAuthResult,
) -> None:
    if not auth_result.from_submitted_credentials:
        return
    config = _auth_config(request)
    response.set_cookie(
        UI_REVIEWER_COOKIE,
        create_ui_reviewer_cookie_token(auth_result.principal, services, config),
        max_age=UI_REVIEWER_COOKIE_MAX_AGE_SECONDS,
        path="/ui",
        httponly=True,
        samesite="lax",
        secure=config.ui_cookie_secure,
    )


def delete_ui_reviewer_session_cookie(response: Response, request: Request) -> None:
    response.delete_cookie(
        UI_REVIEWER_COOKIE,
        path="/ui",
        httponly=True,
        samesite="lax",
        secure=_auth_config(request).ui_cookie_secure,
    )


def reviewer_credential_fields(
    request: Request | None = None,
    services: UiReviewerServicesProtocol | None = None,
    *,
    required_scope: str | None = None,
) -> str:
    """Return the two reviewer-credential ``<input>`` elements used in action forms.

    Produces:
        <label>Reviewer ID: <input type="text" name="reviewer_id" required
            autocomplete="off"></label>
        <label>Reviewer token: <input type="password" name="reviewer_token" required
            autocomplete="off"></label>

    The caller is responsible for wrapping these in a ``<form>``.
    """
    if request is not None and services is not None:
        principal = ui_reviewer_principal_from_cookie(request, services)
        if principal is not None and (
            required_scope is None or required_scope in principal.scopes
        ):
            reviewer_id = _html.escape(principal.reviewer_id)
            return (
                "<div class='reviewer-session'><span>Using reviewer session: "
                f"<strong>{reviewer_id}</strong>.</span> "
                "<a class='reviewer-session-link' href='/ui/auth/reviewer'>"
                "Manage reviewer session</a></div>"
            )
        if principal is not None and required_scope is not None:
            reviewer_id = _html.escape(principal.reviewer_id)
            required_scope_esc = _html.escape(required_scope)
            return (
                "<p class='reviewer-session warning'>Reviewer session "
                f"<strong>{reviewer_id}</strong> lacks <code>{required_scope_esc}</code>; "
                "enter reviewer credentials for this action.</p>"
                f"{_reviewer_credential_inputs()}"
            )
    return (
        "<div class='reviewer-session'>"
        "<a class='reviewer-session-link' href='/ui/auth/reviewer'>"
        "Sign in reviewer session</a><span>or enter credentials.</span>"
        "</div>"
        f"{_reviewer_credential_inputs()}"
    )


def _reviewer_credential_inputs() -> str:
    return (
        "<label>Reviewer ID:"
        " <input type='text' name='reviewer_id' required autocomplete='off'></label>"
        "<label>Reviewer token:"
        " <input type='password' name='reviewer_token' required autocomplete='off'></label>"
    )


def _submitted_reviewer_credentials_present(
    reviewer_id: str | None,
    reviewer_token: str | None,
) -> bool:
    return bool(
        (reviewer_id and reviewer_id.strip())
        or (reviewer_token and reviewer_token.strip())
    )


def _sign_ui_reviewer_token(signed_part: str, config: ApiKeyAuthConfig) -> str:
    if config.ui_cookie_signing_secret is None:
        raise ValueError("UI reviewer cookie signing secret is not configured")
    signing_key = hashlib.sha256(
        f"{UI_REVIEWER_COOKIE_TOKEN_PREFIX}:{config.ui_cookie_signing_secret}".encode()
    ).digest()
    return _base64url_encode(
        hmac.new(signing_key, signed_part.encode("utf-8"), hashlib.sha256).digest()
    )


def _decode_ui_reviewer_payload(payload_segment: str) -> dict[str, object] | None:
    try:
        payload = json.loads(_base64url_decode(payload_segment).decode("utf-8"))
    except (binascii.Error, ValueError, UnicodeDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _ui_reviewer_payload_is_unexpired(
    payload: dict[str, object],
    now: datetime,
) -> bool:
    expires_at = payload.get("exp")
    return isinstance(expires_at, int) and expires_at > int(now.timestamp())


def _base64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _base64url_decode(encoded: str) -> bytes:
    padding = "=" * (-len(encoded) % 4)
    return base64.urlsafe_b64decode(f"{encoded}{padding}".encode("ascii"))
