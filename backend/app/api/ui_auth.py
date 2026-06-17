from __future__ import annotations

from html import escape
from typing import Annotated, cast
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.responses import Response

from app.api.api_key_auth import (
    UI_API_KEY_COOKIE,
    UI_API_KEY_COOKIE_MAX_AGE_SECONDS,
    ApiKeyAuthConfig,
    _audit_failure_response,
    _clean_api_key,
    _match_api_key,
    _record_api_key_audit_event,
    create_ui_api_key_cookie_token,
)
from app.api.auth_audit import ApiKeyAuthAuditOutcome
from app.api.dependencies import ApiServices, get_services
from app.api.ui_shared import (
    UI_REVIEWER_COOKIE,
    UI_REVIEWER_COOKIE_MAX_AGE_SECONDS,
    create_ui_reviewer_cookie_token,
    csrf_form_field,
    delete_ui_reviewer_session_cookie,
    require_ui_csrf,
    ui_reviewer_principal_from_cookie,
)

router = APIRouter(prefix="/ui/auth", tags=["ui"])
ServicesDep = Annotated[ApiServices, Depends(get_services)]


@router.get("", response_class=HTMLResponse)
def ui_auth_form(next: str | None = None) -> HTMLResponse:
    return _login_page(next_path=next)


@router.post("", response_class=HTMLResponse)
def ui_auth_submit(
    request: Request,
    api_key: Annotated[str | None, Form()] = None,
    next: Annotated[str | None, Form()] = None,
) -> Response:
    provided = _clean_api_key(api_key)
    config = _auth_config(request)
    if provided is None or not config.required or not config.api_keys:
        if not _record_api_key_audit_event(
            config.audit_log,
            request,
            outcome=ApiKeyAuthAuditOutcome.MISSING
            if provided is None
            else ApiKeyAuthAuditOutcome.UNCONFIGURED,
            status_code=401,
        ):
            return _audit_failure_response()
        return _invalid_login_response(next_path=next, secure=config.ui_cookie_secure)
    match = _match_api_key(provided, config)
    if match is None:
        if not _record_api_key_audit_event(
            config.audit_log,
            request,
            outcome=ApiKeyAuthAuditOutcome.INVALID,
            status_code=401,
        ):
            return _audit_failure_response()
        return _invalid_login_response(next_path=next, secure=config.ui_cookie_secure)
    if not _record_api_key_audit_event(
        config.audit_log,
        request,
        outcome=ApiKeyAuthAuditOutcome.ACCEPTED,
        status_code=303,
        key_id=match.key_id,
        source=match.source,
    ):
        return _audit_failure_response()

    response = RedirectResponse(_safe_next_path(next), status_code=303)
    response.set_cookie(
        UI_API_KEY_COOKIE,
        create_ui_api_key_cookie_token(provided, config),
        max_age=UI_API_KEY_COOKIE_MAX_AGE_SECONDS,
        path="/ui",
        httponly=True,
        samesite="lax",
        secure=config.ui_cookie_secure,
    )
    return response


@router.get("/logout", response_class=HTMLResponse)
def ui_auth_logout_form(request: Request) -> HTMLResponse:
    csrf_field = csrf_form_field(request)
    html = (
        "<!DOCTYPE html><html lang='en'><head><meta charset='UTF-8'>"
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        "<title>Sign out</title>"
        "<style>"
        "body { font-family: system-ui, sans-serif; max-width: 34rem; margin: 4rem auto;"
        " padding: 0 1rem; color: #1f2933; }"
        "form { display: grid; gap: 0.75rem; }"
        "button { background: #155e75; border: 0; border-radius: 4px; color: white;"
        " cursor: pointer; font-weight: 700; padding: 0.65rem 0.9rem; }"
        "</style></head><body>"
        "<h1>Sign out</h1>"
        "<p>End this browser session for the operator UI.</p>"
        "<form method='POST' action='/ui/auth/logout'>"
        f"{csrf_field}"
        "<button type='submit'>Sign out</button>"
        "</form></body></html>"
    )
    return HTMLResponse(html, status_code=200)


@router.post("/logout")
def ui_auth_logout(
    request: Request,
    csrf_token: Annotated[str | None, Form()] = None,
) -> Response:
    config = _auth_config(request)
    csrf_error = require_ui_csrf(request, csrf_token, back_url="/ui/auth/logout")
    if csrf_error is not None:
        return csrf_error
    response = RedirectResponse("/ui/auth", status_code=303)
    response.delete_cookie(
        UI_API_KEY_COOKIE,
        path="/ui",
        httponly=True,
        samesite="lax",
        secure=config.ui_cookie_secure,
    )
    delete_ui_reviewer_session_cookie(response, request)
    return response


@router.get("/reviewer", response_class=HTMLResponse)
def ui_reviewer_auth_form(
    request: Request,
    services: ServicesDep,
    next: str | None = None,
) -> HTMLResponse:
    return _reviewer_login_page(
        request,
        services,
        next_path=next,
    )


@router.post("/reviewer", response_class=HTMLResponse)
def ui_reviewer_auth_submit(
    request: Request,
    services: ServicesDep,
    reviewer_id: Annotated[str | None, Form()] = None,
    reviewer_token: Annotated[str | None, Form()] = None,
    next: Annotated[str | None, Form()] = None,
    csrf_token: Annotated[str | None, Form()] = None,
) -> Response:
    csrf_error = require_ui_csrf(request, csrf_token, back_url="/ui/auth/reviewer")
    if csrf_error is not None:
        return csrf_error
    try:
        principal = services.reviewer_auth(
            reviewer_id=reviewer_id,
            reviewer_token=reviewer_token,
        )
    except HTTPException as exc:
        return _reviewer_login_page(
            request,
            services,
            error="Reviewer credentials are invalid",
            next_path=next,
            status_code=exc.status_code,
        )
    config = _auth_config(request)
    response = RedirectResponse(_safe_next_path(next), status_code=303)
    response.set_cookie(
        UI_REVIEWER_COOKIE,
        create_ui_reviewer_cookie_token(principal, services, config),
        max_age=UI_REVIEWER_COOKIE_MAX_AGE_SECONDS,
        path="/ui",
        httponly=True,
        samesite="lax",
        secure=config.ui_cookie_secure,
    )
    return response


@router.post("/reviewer/logout")
def ui_reviewer_auth_logout(
    request: Request,
    csrf_token: Annotated[str | None, Form()] = None,
) -> Response:
    csrf_error = require_ui_csrf(request, csrf_token, back_url="/ui/auth/reviewer")
    if csrf_error is not None:
        return csrf_error
    response = RedirectResponse("/ui/auth/reviewer", status_code=303)
    delete_ui_reviewer_session_cookie(response, request)
    return response


def _auth_config(request: Request) -> ApiKeyAuthConfig:
    return cast(ApiKeyAuthConfig, request.app.state.api_key_auth_config)


def _invalid_login_response(
    next_path: str | None = None,
    *,
    secure: bool = False,
) -> HTMLResponse:
    response = _login_page(
        error="API key is invalid",
        next_path=next_path,
        status_code=401,
    )
    response.delete_cookie(
        UI_API_KEY_COOKIE,
        path="/ui",
        httponly=True,
        samesite="lax",
        secure=secure,
    )
    return response


def _login_page(
    error: str | None = None,
    next_path: str | None = None,
    status_code: int = 200,
) -> HTMLResponse:
    error_html = ""
    if error is not None:
        error_html = f"<p class='error'>{escape(error)}</p>"
    next_input = ""
    safe_next = _safe_next_path(next_path)
    if safe_next != "/ui/":
        next_input = (
            f'<input name="next" type="hidden" value="{escape(safe_next, quote=True)}">'
        )
    html = (
        "<!DOCTYPE html><html lang='en'><head><meta charset='UTF-8'>"
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        "<title>Operator UI access</title>"
        "<style>"
        "body { font-family: system-ui, sans-serif; max-width: 34rem; margin: 4rem auto;"
        " padding: 0 1rem; color: #1f2933; }"
        "form { display: grid; gap: 0.75rem; }"
        "label { font-weight: 700; }"
        "input { border: 1px solid #b8c2cf; border-radius: 4px; font-size: 1rem;"
        " box-sizing: border-box; padding: 0.6rem; width: 100%; }"
        "button { background: #155e75; border: 0; border-radius: 4px; color: white;"
        " cursor: pointer; font-weight: 700; padding: 0.65rem 0.9rem; }"
        ".error { background: #fee2e2; border: 1px solid #fecaca; border-radius: 4px;"
        " color: #991b1b; padding: 0.75rem; }"
        "</style></head><body>"
        "<h1>Operator UI access</h1>"
        f"{error_html}"
        "<form method='POST' action='/ui/auth'>"
        f"{next_input}"
        "<label for='api_key'>API key</label>"
        '<input id="api_key" name="api_key" type="password" autocomplete="off" required>'
        "<button type='submit'>Continue</button>"
        "</form></body></html>"
    )
    return HTMLResponse(html, status_code=status_code)


def _reviewer_login_page(
    request: Request,
    services: ApiServices,
    *,
    error: str | None = None,
    next_path: str | None = None,
    status_code: int = 200,
) -> HTMLResponse:
    current = ui_reviewer_principal_from_cookie(request, services)
    current_html = ""
    if current is not None:
        scopes = ", ".join(sorted(current.scopes))
        current_html = (
            "<section class='session'>"
            f"<p>Reviewer session: <strong>{escape(current.reviewer_id)}</strong></p>"
            f"<p><small>{escape(scopes)}</small></p>"
            "<form method='POST' action='/ui/auth/reviewer/logout'>"
            f"{csrf_form_field(request)}"
            "<button type='submit'>Sign out reviewer</button>"
            "</form></section>"
        )
    error_html = ""
    if error is not None:
        error_html = f"<p class='error'>{escape(error)}</p>"
    safe_next = _safe_next_path(next_path)
    next_input = ""
    if safe_next != "/ui/":
        next_input = (
            f'<input name="next" type="hidden" value="{escape(safe_next, quote=True)}">'
        )
    html = (
        "<!DOCTYPE html><html lang='en'><head><meta charset='UTF-8'>"
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        "<title>Reviewer session</title>"
        "<style>"
        "body { font-family: system-ui, sans-serif; max-width: 34rem; margin: 4rem auto;"
        " padding: 0 1rem; color: #1f2933; }"
        "form { display: grid; gap: 0.75rem; margin-top: 1rem; }"
        "label { font-weight: 700; }"
        "input { border: 1px solid #b8c2cf; border-radius: 4px; font-size: 1rem;"
        " padding: 0.6rem; width: 100%; box-sizing: border-box; }"
        "button { background: #155e75; border: 0; border-radius: 4px; color: white;"
        " cursor: pointer; font-weight: 700; padding: 0.65rem 0.9rem; }"
        ".error { background: #fee2e2; border: 1px solid #fecaca; border-radius: 4px;"
        " color: #991b1b; padding: 0.75rem; }"
        ".session { background: #ecfeff; border: 1px solid #a5f3fc; border-radius: 4px;"
        " padding: 0.75rem; margin-bottom: 1rem; }"
        "</style></head><body>"
        "<h1>Reviewer session</h1>"
        "<p>Sign in once for reviewer-scoped UI actions. API routes still require "
        "<code>X-Reviewer-Id</code> and <code>X-Reviewer-Token</code> headers.</p>"
        f"{current_html}"
        f"{error_html}"
        "<form method='POST' action='/ui/auth/reviewer'>"
        f"{csrf_form_field(request)}"
        f"{next_input}"
        "<label for='reviewer_id'>Reviewer ID</label>"
        '<input id="reviewer_id" name="reviewer_id" type="text" '
        'autocomplete="off" required>'
        "<label for='reviewer_token'>Reviewer token</label>"
        '<input id="reviewer_token" name="reviewer_token" type="password" '
        'autocomplete="off" required>'
        "<button type='submit'>Start reviewer session</button>"
        "</form></body></html>"
    )
    return HTMLResponse(html, status_code=status_code)


def _safe_next_path(next_path: str | None) -> str:
    if next_path is None:
        return "/ui/"
    candidate = next_path.strip()
    if not candidate:
        return "/ui/"
    parsed = urlsplit(candidate)
    if parsed.scheme or parsed.netloc or not parsed.path.startswith("/ui"):
        return "/ui/"
    if parsed.path != "/ui" and not parsed.path.startswith("/ui/"):
        return "/ui/"
    if parsed.query:
        return f"{parsed.path}?{parsed.query}"
    return parsed.path
