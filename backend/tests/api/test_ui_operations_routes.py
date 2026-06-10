from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app

_FIXTURE_REVIEWER_ID = "fixture-reviewer"
_FIXTURE_REVIEWER_TOKEN = "fixture-token-123"


def _client() -> TestClient:
    return TestClient(create_app())


def test_ui_operations_get_returns_200_with_form() -> None:
    tc = _client()
    resp = tc.get("/ui/operations")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "Operations Dashboard" in resp.text
    assert "reviewer_id" in resp.text
    assert "reviewer_token" in resp.text


def test_ui_operations_post_no_credentials_returns_401() -> None:
    tc = _client()
    resp = tc.post("/ui/operations", data={})
    assert resp.status_code == 401
    assert "text/html" in resp.headers["content-type"]
    assert "Authentication Error" in resp.text


def test_ui_operations_post_wrong_token_returns_403() -> None:
    tc = _client()
    resp = tc.post(
        "/ui/operations",
        data={
            "reviewer_id": _FIXTURE_REVIEWER_ID,
            "reviewer_token": "wrong-token",
        },
    )
    assert resp.status_code == 403
    assert "text/html" in resp.headers["content-type"]
    assert "Authentication Error" in resp.text


def test_ui_operations_post_valid_creds_without_operations_scope_returns_403() -> None:
    settings = Settings(
        REVIEWER_ACCOUNTS="ops-reviewer:ops-token",
        REVIEWER_ACCOUNT_SCOPES="ops-reviewer:report:approve",
    )
    tc = TestClient(create_app(settings))
    resp = tc.post(
        "/ui/operations",
        data={
            "reviewer_id": "ops-reviewer",
            "reviewer_token": "ops-token",
        },
    )
    assert resp.status_code == 403
    assert "text/html" in resp.headers["content-type"]
    assert "Authentication Error" in resp.text


def test_ui_operations_post_valid_creds_renders_counts() -> None:
    tc = _client()
    resp = tc.post(
        "/ui/operations",
        data={
            "reviewer_id": _FIXTURE_REVIEWER_ID,
            "reviewer_token": _FIXTURE_REVIEWER_TOKEN,
        },
    )
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "Operations Dashboard" in resp.text
    # Should render both queue sections
    assert "Report Jobs" in resp.text
    assert "Live Connector Jobs" in resp.text
    # Table headers present
    assert "Queued" in resp.text
    assert "Running" in resp.text
    assert "Failed" in resp.text


def test_ui_operations_post_shows_authenticated_reviewer() -> None:
    tc = _client()
    resp = tc.post(
        "/ui/operations",
        data={
            "reviewer_id": _FIXTURE_REVIEWER_ID,
            "reviewer_token": _FIXTURE_REVIEWER_TOKEN,
        },
    )
    assert resp.status_code == 200
    assert _FIXTURE_REVIEWER_ID in resp.text


def test_ui_operations_post_unconfigured_accounts_returns_503() -> None:
    from typing import cast
    from unittest.mock import patch

    from fastapi import HTTPException, status

    from app.api.dependencies import ApiServices

    app = create_app()
    tc = TestClient(app)
    services = cast(ApiServices, app.state.services)

    def _unconfigured(**kwargs: object) -> None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="connector reviewer auth is not configured",
        )

    with patch.object(services, "reviewer_auth", side_effect=_unconfigured):
        resp = tc.post(
            "/ui/operations",
            data={
                "reviewer_id": "any",
                "reviewer_token": "any",
            },
        )
    assert resp.status_code == 503
    assert "text/html" in resp.headers["content-type"]
    assert "Authentication Error" in resp.text
