from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_rate_limit_allows_local_development_by_default() -> None:
    client = TestClient(create_app(Settings(ENABLE_RATE_LIMIT=False, RATE_LIMIT_REQUESTS=1)))

    assert client.get("/areas").status_code == 200
    assert client.get("/areas").status_code == 200


def test_rate_limit_ignores_limit_config_when_disabled() -> None:
    client = TestClient(
        create_app(
            Settings(
                ENABLE_RATE_LIMIT=False,
                RATE_LIMIT_REQUESTS=0,
                RATE_LIMIT_WINDOW_SECONDS=0,
            )
        )
    )

    assert client.get("/areas").status_code == 200


def test_rate_limit_rejects_requests_after_configured_window_budget() -> None:
    client = TestClient(
        create_app(
            Settings(
                ENABLE_RATE_LIMIT=True,
                RATE_LIMIT_REQUESTS=2,
                RATE_LIMIT_WINDOW_SECONDS=60,
            )
        )
    )

    first = client.get("/areas")
    second = client.get("/areas")
    third = client.get("/areas")

    assert first.status_code == 200
    assert first.headers["X-RateLimit-Limit"] == "2"
    assert first.headers["X-RateLimit-Remaining"] == "1"
    assert second.status_code == 200
    assert second.headers["X-RateLimit-Remaining"] == "0"
    assert third.status_code == 429
    assert third.json()["detail"] == "rate limit exceeded"
    assert third.headers["Retry-After"] == third.headers["X-RateLimit-Reset"]


def test_rate_limit_keeps_health_and_version_public() -> None:
    client = TestClient(
        create_app(
            Settings(
                ENABLE_RATE_LIMIT=True,
                RATE_LIMIT_REQUESTS=1,
                RATE_LIMIT_WINDOW_SECONDS=60,
            )
        )
    )

    assert client.get("/health").status_code == 200
    assert client.get("/health").status_code == 200
    assert client.get("/version").status_code == 200
    assert client.get("/version").status_code == 200


def test_rate_limit_uses_api_key_identity_when_available() -> None:
    client = TestClient(
        create_app(
            Settings(
                REQUIRE_API_KEY=True,
                API_KEYS="key-a,key-b",
                ENABLE_RATE_LIMIT=True,
                RATE_LIMIT_REQUESTS=1,
                RATE_LIMIT_WINDOW_SECONDS=60,
            )
        )
    )

    assert client.get("/areas", headers={"X-API-Key": "key-a"}).status_code == 200
    assert client.get("/areas", headers={"X-API-Key": "key-a"}).status_code == 429
    assert client.get("/areas", headers={"X-API-Key": "key-b"}).status_code == 200


@pytest.mark.parametrize(
    "settings,match",
    [
        (
            Settings(RATE_LIMIT_REQUESTS=0),
            "RATE_LIMIT_REQUESTS must be at least 1",
        ),
        (
            Settings(RATE_LIMIT_WINDOW_SECONDS=0),
            "RATE_LIMIT_WINDOW_SECONDS must be at least 1",
        ),
    ],
)
def test_settings_rate_limit_fails_closed_for_invalid_enabled_config(
    settings: Settings,
    match: str,
) -> None:
    with pytest.raises(ValueError, match=match):
        settings.parsed_rate_limit()
