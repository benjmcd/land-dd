from __future__ import annotations

import base64
import hashlib
import hmac
import json
import re
from datetime import UTC, datetime, timedelta
from typing import cast
from urllib.parse import parse_qs, urlsplit

import pytest
from fastapi.testclient import TestClient

from app.api.api_key_auth import (
    UI_API_KEY_COOKIE_TOKEN_PREFIX,
    ApiKeyAuthConfig,
    create_ui_api_key_cookie_token,
    verify_ui_api_key_cookie_token,
)
from app.api.auth_audit import InMemoryApiKeyAuthAuditLog
from app.api.dependencies import ApiServices
from app.api.ui_shared import (
    UI_REVIEWER_COOKIE,
    create_ui_reviewer_cookie_token,
    verify_ui_reviewer_cookie_token,
)
from app.core.config import Settings
from app.main import create_app

UI_AUTH_COOKIE = "land_dd_ui_api_key"
CSRF_FIELD = "csrf_token"
_FIXTURE_REVIEWER_ID = "fixture-reviewer"
_FIXTURE_REVIEWER_TOKEN = "fixture-token-123"


def _client(settings: Settings | None = None) -> TestClient:
    return TestClient(
        create_app(settings or Settings(REQUIRE_API_KEY=True, API_KEYS="production-key"))
    )


def _next_query(location: str) -> str | None:
    values = parse_qs(urlsplit(location).query).get("next")
    if values is None:
        return None
    return values[0]


def _csrf_token_from(html: str) -> str:
    match = re.search(r'name="csrf_token" type="hidden" value="([^"]+)"', html)
    assert match is not None
    return match.group(1)


def test_ui_auth_form_is_public_and_does_not_expose_configured_secret() -> None:
    client = _client()

    response = client.get("/ui/auth")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert 'name="api_key"' in response.text
    assert "box-sizing: border-box" in response.text
    assert "production-key" not in response.text


def test_ui_cookie_auth_forms_include_csrf_token() -> None:
    client = _client()
    assert client.post(
        "/ui/auth",
        data={"api_key": "production-key"},
        follow_redirects=False,
    ).status_code == 303

    home = client.get("/ui/")
    operations = client.get("/ui/operations")

    assert home.status_code == 200
    assert f'name="{CSRF_FIELD}"' in home.text
    assert operations.status_code == 200
    assert f'name="{CSRF_FIELD}"' in operations.text


def test_ui_cookie_auth_post_requires_valid_csrf_token() -> None:
    client = _client()
    assert client.post(
        "/ui/auth",
        data={"api_key": "production-key"},
        follow_redirects=False,
    ).status_code == 303

    missing = client.post(
        "/ui/intake",
        data={"area_geojson": "not-json", "intent": "rural_land_purchase"},
    )
    tampered = client.post(
        "/ui/intake",
        data={
            "area_geojson": "not-json",
            "intent": "rural_land_purchase",
            CSRF_FIELD: "bad-token",
        },
    )
    token = _csrf_token_from(client.get("/ui/").text)
    valid = client.post(
        "/ui/intake",
        data={
            "area_geojson": "not-json",
            "intent": "rural_land_purchase",
            CSRF_FIELD: token,
        },
    )

    assert missing.status_code == 403
    assert tampered.status_code == 403
    assert valid.status_code == 422
    assert "Invalid GeoJSON" in valid.text


def test_ui_header_auth_post_does_not_require_csrf_token() -> None:
    client = _client()

    response = client.post(
        "/ui/intake",
        headers={"X-API-Key": "production-key"},
        data={"area_geojson": "not-json", "intent": "rural_land_purchase"},
    )

    assert response.status_code == 422
    assert "Invalid GeoJSON" in response.text


def test_ui_auth_cookie_enables_ui_when_api_key_required() -> None:
    client = _client()

    login = client.post(
        "/ui/auth",
        data={"api_key": "production-key"},
        follow_redirects=False,
    )

    assert login.status_code == 303
    assert login.headers["location"] == "/ui/"
    assert UI_AUTH_COOKIE in login.cookies
    set_cookie = login.headers["set-cookie"]
    assert "HttpOnly" in set_cookie
    assert "SameSite=lax" in set_cookie
    assert "Path=/ui" in set_cookie
    assert "Max-Age=" in set_cookie
    assert "production-key" not in set_cookie
    assert "production-key" not in login.cookies[UI_AUTH_COOKIE]

    response = client.get("/ui/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_ui_reviewer_auth_sets_bound_session_cookie_without_exposing_token() -> None:
    app = create_app(
        Settings(
            REQUIRE_API_KEY=False,
            UI_AUTH_COOKIE_SECRET="stable-ui-cookie-secret",
        )
    )
    client = TestClient(app)

    login = client.post(
        "/ui/auth/reviewer",
        data={
            "reviewer_id": _FIXTURE_REVIEWER_ID,
            "reviewer_token": _FIXTURE_REVIEWER_TOKEN,
        },
        follow_redirects=False,
    )

    assert login.status_code == 303
    assert UI_REVIEWER_COOKIE in login.cookies
    set_cookie = login.headers["set-cookie"]
    assert "HttpOnly" in set_cookie
    assert "SameSite=lax" in set_cookie
    assert "Path=/ui" in set_cookie
    assert _FIXTURE_REVIEWER_TOKEN not in set_cookie
    assert _FIXTURE_REVIEWER_TOKEN not in login.cookies[UI_REVIEWER_COOKIE]
    assert _FIXTURE_REVIEWER_TOKEN not in login.text

    services = cast(ApiServices, app.state.services)
    principal = verify_ui_reviewer_cookie_token(
        login.cookies[UI_REVIEWER_COOKIE],
        services,
        app.state.api_key_auth_config,
    )
    assert principal is not None
    assert principal.reviewer_id == _FIXTURE_REVIEWER_ID
    assert principal.auth_scheme == "ui_reviewer_session"


def test_ui_reviewer_cookie_rejects_tampering_expiry_and_token_rotation() -> None:
    issuer_settings = Settings(
        REQUIRE_API_KEY=False,
        UI_AUTH_COOKIE_SECRET="stable-ui-cookie-secret",
        REVIEWER_ACCOUNTS=f"{_FIXTURE_REVIEWER_ID}:{_FIXTURE_REVIEWER_TOKEN}",
        REVIEWER_ACCOUNT_SCOPES=f"{_FIXTURE_REVIEWER_ID}:operations:read",
    )
    issuer_app = create_app(issuer_settings)
    issuer_services = cast(ApiServices, issuer_app.state.services)
    principal = issuer_services.reviewer_auth(
        reviewer_id=_FIXTURE_REVIEWER_ID,
        reviewer_token=_FIXTURE_REVIEWER_TOKEN,
    )
    token = create_ui_reviewer_cookie_token(
        principal,
        issuer_services,
        issuer_app.state.api_key_auth_config,
    )

    assert (
        verify_ui_reviewer_cookie_token(
            token,
            issuer_services,
            issuer_app.state.api_key_auth_config,
        )
        is not None
    )
    assert (
        verify_ui_reviewer_cookie_token(
            f"{token}tampered",
            issuer_services,
            issuer_app.state.api_key_auth_config,
        )
        is None
    )
    expired_token = create_ui_reviewer_cookie_token(
        principal,
        issuer_services,
        issuer_app.state.api_key_auth_config,
        issued_at=datetime.now(UTC) - timedelta(hours=9),
    )
    assert (
        verify_ui_reviewer_cookie_token(
            expired_token,
            issuer_services,
            issuer_app.state.api_key_auth_config,
        )
        is None
    )

    rotated_app = create_app(
        Settings(
            REQUIRE_API_KEY=False,
            UI_AUTH_COOKIE_SECRET="stable-ui-cookie-secret",
            REVIEWER_ACCOUNTS=f"{_FIXTURE_REVIEWER_ID}:rotated-token",
            REVIEWER_ACCOUNT_SCOPES=f"{_FIXTURE_REVIEWER_ID}:operations:read",
        )
    )
    rotated_services = cast(ApiServices, rotated_app.state.services)
    assert (
        verify_ui_reviewer_cookie_token(
            token,
            rotated_services,
            rotated_app.state.api_key_auth_config,
        )
        is None
    )


def test_api_routes_do_not_accept_ui_reviewer_session_cookie_for_header_auth() -> None:
    client = TestClient(create_app(Settings(REQUIRE_API_KEY=False)))
    login = client.post(
        "/ui/auth/reviewer",
        data={
            "reviewer_id": _FIXTURE_REVIEWER_ID,
            "reviewer_token": _FIXTURE_REVIEWER_TOKEN,
        },
        follow_redirects=False,
    )
    assert login.status_code == 303

    response = client.get("/operations/queue-health")

    assert response.status_code == 401
    assert response.json()["detail"] == "connector reviewer credentials are required"


def test_tampered_ui_auth_cookie_redirects_to_login() -> None:
    client = _client()
    login = client.post(
        "/ui/auth",
        data={"api_key": "production-key"},
        follow_redirects=False,
    )
    assert login.status_code == 303
    token = login.cookies[UI_AUTH_COOKIE]

    response = client.get(
        "/ui/",
        headers={"Cookie": f"{UI_AUTH_COOKIE}={token}tampered"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/ui/auth"


def test_malformed_ui_auth_cookie_payload_redirects_to_login() -> None:
    client = _client()
    payload = base64.urlsafe_b64encode(
        json.dumps({"exp": int((datetime.now(UTC) + timedelta(hours=1)).timestamp())}).encode(
            "utf-8"
        )
    ).rstrip(b"=").decode("ascii")

    response = client.get(
        "/ui/",
        headers={"Cookie": f"{UI_AUTH_COOKIE}=land-dd-ui-api-key-v1.{payload}.invalid"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/ui/auth"


def test_badly_encoded_ui_auth_cookie_payload_redirects_to_login() -> None:
    client = _client()

    response = client.get(
        "/ui/",
        headers={"Cookie": f"{UI_AUTH_COOKIE}=land-dd-ui-api-key-v1.a.invalid"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/ui/auth"


def test_ui_auth_cookie_is_rejected_when_active_api_key_config_changes() -> None:
    issuer = _client(Settings(REQUIRE_API_KEY=True, API_KEYS="first-production-key"))
    login = issuer.post(
        "/ui/auth",
        data={"api_key": "first-production-key"},
        follow_redirects=False,
    )
    assert login.status_code == 303
    token = login.cookies[UI_AUTH_COOKIE]

    verifier = _client(Settings(REQUIRE_API_KEY=True, API_KEYS="second-production-key"))
    response = verifier.get(
        "/ui/",
        headers={"Cookie": f"{UI_AUTH_COOKIE}={token}"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/ui/auth"


def test_sha256_api_key_digest_cannot_forge_ui_auth_cookie() -> None:
    digest = hashlib.sha256(b"production-key").hexdigest()
    client = _client(
        Settings(
            REQUIRE_API_KEY=True,
            API_KEYS=f"sha256:{digest}",
            UI_AUTH_COOKIE_SECRET="independent-ui-cookie-secret",
        )
    )
    payload = base64.urlsafe_b64encode(
        json.dumps(
            {
                "digest": digest,
                "exp": int((datetime.now(UTC) + timedelta(hours=1)).timestamp()),
            },
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).rstrip(b"=").decode("ascii")
    signed_part = f"{UI_API_KEY_COOKIE_TOKEN_PREFIX}.{payload}"
    old_signing_key = hashlib.sha256(
        f"{UI_API_KEY_COOKIE_TOKEN_PREFIX}:sha256:{digest}".encode()
    ).digest()
    old_signature = base64.urlsafe_b64encode(
        hmac.new(old_signing_key, signed_part.encode("utf-8"), hashlib.sha256).digest()
    ).rstrip(b"=").decode("ascii")

    response = client.get(
        "/ui/",
        headers={"Cookie": f"{UI_AUTH_COOKIE}={signed_part}.{old_signature}"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/ui/auth"


def test_ui_auth_cookie_verification_fails_closed_without_signing_secret() -> None:
    issuer_config = ApiKeyAuthConfig(
        required=True,
        api_keys=frozenset({"production-key"}),
        ui_cookie_signing_secret="issuer-ui-cookie-secret",
    )
    token = create_ui_api_key_cookie_token("production-key", issuer_config)
    verifier_config = ApiKeyAuthConfig(
        required=True,
        api_keys=frozenset({"production-key"}),
    )

    assert verify_ui_api_key_cookie_token(token, verifier_config) is None


def test_configured_ui_auth_cookie_secret_allows_restart_with_same_api_key() -> None:
    settings = Settings(
        REQUIRE_API_KEY=True,
        API_KEYS="production-key",
        UI_AUTH_COOKIE_SECRET="stable-ui-cookie-secret",
    )
    issuer = _client(settings)
    login = issuer.post(
        "/ui/auth",
        data={"api_key": "production-key"},
        follow_redirects=False,
    )
    assert login.status_code == 303
    token = login.cookies[UI_AUTH_COOKIE]

    verifier = _client(settings)
    response = verifier.get(
        "/ui/",
        headers={"Cookie": f"{UI_AUTH_COOKIE}={token}"},
        follow_redirects=False,
    )

    assert response.status_code == 200


def test_non_local_app_env_sets_secure_ui_auth_cookie() -> None:
    app = create_app(
        Settings(
            APP_ENV="production",
            USE_DB_SERVICES=True,
            REQUIRE_API_KEY=True,
            API_KEYS="production-key",
            UI_AUTH_COOKIE_SECRET="stable-ui-cookie-secret",
        ),
        api_key_audit_log=InMemoryApiKeyAuthAuditLog(),
    )
    client = TestClient(app)

    response = client.post(
        "/ui/auth",
        data={"api_key": "production-key"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert "Secure" in response.headers["set-cookie"]


def test_non_local_api_key_auth_requires_configured_ui_auth_cookie_secret() -> None:
    with pytest.raises(ValueError, match="UI_AUTH_COOKIE_SECRET"):
        create_app(
            Settings(
                APP_ENV="production",
                USE_DB_SERVICES=True,
                REQUIRE_API_KEY=True,
                API_KEYS="production-key",
            )
        )


def test_expired_ui_auth_cookie_redirects_to_login() -> None:
    settings = Settings(REQUIRE_API_KEY=True, API_KEYS="production-key")
    app = create_app(settings)
    issuer = TestClient(app)
    expired_token = create_ui_api_key_cookie_token(
        "production-key",
        app.state.api_key_auth_config,
        issued_at=datetime.now(UTC) - timedelta(hours=9),
    )

    response = issuer.get(
        "/ui/",
        headers={"Cookie": f"{UI_AUTH_COOKIE}={expired_token}"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/ui/auth"


def test_api_routes_reject_ui_auth_cookie_without_header_key() -> None:
    client = _client()
    login = client.post(
        "/ui/auth",
        data={"api_key": "production-key"},
        follow_redirects=False,
    )
    assert login.status_code == 303

    response = client.get("/areas")

    assert response.status_code == 401
    assert response.json()["detail"] == "API key is required"


def test_api_routes_reject_forced_ui_auth_cookie_header_without_header_key() -> None:
    client = _client()

    response = client.get(
        "/areas",
        headers={"Cookie": f"{UI_AUTH_COOKIE}=production-key"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "API key is required"


def test_ui_auth_redirect_preserves_safe_next_path_for_unauthenticated_ui_get() -> None:
    client = _client()

    response = client.get("/ui/report-runs", follow_redirects=False)

    assert response.status_code == 303
    assert urlsplit(response.headers["location"]).path == "/ui/auth"
    assert _next_query(response.headers["location"]) == "/ui/report-runs"


def test_successful_ui_auth_redirects_to_safe_next_path() -> None:
    client = _client()

    response = client.post(
        "/ui/auth",
        data={"api_key": "production-key", "next": "/ui/report-runs"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/ui/report-runs"
    assert UI_AUTH_COOKIE in response.cookies


def test_successful_ui_auth_falls_back_when_next_path_is_unsafe() -> None:
    client = _client()

    external = client.post(
        "/ui/auth",
        data={"api_key": "production-key", "next": "https://example.test/ui"},
        follow_redirects=False,
    )
    api_path = client.post(
        "/ui/auth",
        data={"api_key": "production-key", "next": "/areas"},
        follow_redirects=False,
    )

    assert external.status_code == 303
    assert external.headers["location"] == "/ui/"
    assert api_path.status_code == 303
    assert api_path.headers["location"] == "/ui/"


def test_ui_auth_accepts_active_api_key_spec() -> None:
    client = _client(
        Settings(
            REQUIRE_API_KEY=True,
            API_KEY_SPECS="primary|active|production-key",
        )
    )

    login = client.post(
        "/ui/auth",
        data={"api_key": "production-key"},
        follow_redirects=False,
    )

    assert login.status_code == 303
    assert login.headers["location"] == "/ui/"
    assert UI_AUTH_COOKIE in login.cookies
    assert client.get("/ui/").status_code == 200


def test_ui_auth_cookie_records_api_key_spec_id_and_ui_cookie_source() -> None:
    audit_log = InMemoryApiKeyAuthAuditLog()
    client = TestClient(
        create_app(
            Settings(
                REQUIRE_API_KEY=True,
                API_KEY_SPECS="primary|active|production-key",
            ),
            api_key_audit_log=audit_log,
        )
    )
    login = client.post(
        "/ui/auth",
        data={"api_key": "production-key"},
        follow_redirects=False,
    )
    assert login.status_code == 303

    response = client.get("/ui/")

    assert response.status_code == 200
    events = audit_log.list_all()
    assert len(events) == 2
    assert events[0].outcome == "accepted"
    assert events[0].key_id == "primary"
    assert events[0].source == "api_key_specs"
    assert events[0].path == "/ui/auth"
    assert events[1].outcome == "accepted"
    assert events[1].key_id == "primary"
    assert events[1].source == "ui_cookie"
    assert events[1].path == "/ui/"
    assert "production-key" not in repr(events)


def test_invalid_ui_auth_login_records_audit_event_without_secret() -> None:
    audit_log = InMemoryApiKeyAuthAuditLog()
    client = TestClient(
        create_app(
            Settings(REQUIRE_API_KEY=True, API_KEYS="production-key"),
            api_key_audit_log=audit_log,
        )
    )

    response = client.post("/ui/auth", data={"api_key": "wrong-key"})

    assert response.status_code == 401
    events = audit_log.list_all()
    assert len(events) == 1
    assert events[0].outcome == "invalid"
    assert events[0].status_code == 401
    assert events[0].key_id is None
    assert events[0].source is None
    assert events[0].path == "/ui/auth"
    assert "wrong-key" not in repr(events)
    assert "production-key" not in repr(events)


def test_invalid_ui_header_auth_redirects_to_login_instead_of_json() -> None:
    client = _client()

    response = client.get(
        "/ui/",
        headers={"X-API-Key": "wrong-key"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/ui/auth"


def test_invalid_or_blank_ui_login_returns_safe_html_without_cookie() -> None:
    client = _client()

    invalid = client.post("/ui/auth", data={"api_key": "wrong-key"})
    blank = client.post("/ui/auth", data={"api_key": " "})

    for response in (invalid, blank):
        assert response.status_code == 401
        assert "text/html" in response.headers["content-type"]
        assert 'name="api_key"' in response.text
        assert "API key is invalid" in response.text
        assert UI_AUTH_COOKIE not in response.cookies
        assert "wrong-key" not in response.text
        assert "production-key" not in response.text


def test_ui_logout_requires_post_with_csrf_token() -> None:
    client = _client()
    login = client.post(
        "/ui/auth",
        data={"api_key": "production-key"},
        follow_redirects=False,
    )
    assert login.status_code == 303
    assert client.get("/ui/").status_code == 200
    reviewer_form = client.get("/ui/auth/reviewer")
    reviewer_login = client.post(
        "/ui/auth/reviewer",
        data={
            "reviewer_id": _FIXTURE_REVIEWER_ID,
            "reviewer_token": _FIXTURE_REVIEWER_TOKEN,
            CSRF_FIELD: _csrf_token_from(reviewer_form.text),
        },
        follow_redirects=False,
    )
    assert reviewer_login.status_code == 303
    assert UI_REVIEWER_COOKIE in reviewer_login.cookies

    logout_form = client.get("/ui/auth/logout")
    missing_csrf = client.post("/ui/auth/logout", follow_redirects=False)
    assert client.get("/ui/").status_code == 200

    token = _csrf_token_from(logout_form.text)
    logout = client.post(
        "/ui/auth/logout",
        data={CSRF_FIELD: token},
        follow_redirects=False,
    )

    assert logout_form.status_code == 200
    assert f'name="{CSRF_FIELD}"' in logout_form.text
    assert missing_csrf.status_code == 403
    assert logout.status_code == 303
    assert logout.headers["location"] == "/ui/auth"
    set_cookie = "\n".join(logout.headers.get_list("set-cookie"))
    assert f"{UI_AUTH_COOKIE}=" in set_cookie
    assert f"{UI_REVIEWER_COOKIE}=" in set_cookie
    assert "Max-Age=0" in set_cookie
    assert "Path=/ui" in set_cookie
    assert client.get("/ui/", follow_redirects=False).status_code == 303


def test_existing_api_key_header_still_enables_areas_route() -> None:
    client = _client()

    response = client.get("/areas", headers={"X-API-Key": "production-key"})

    assert response.status_code == 200
    assert response.json() == []
