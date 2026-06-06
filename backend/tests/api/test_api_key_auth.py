from __future__ import annotations

import os
from hashlib import sha256
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from app.api import api_key_auth
from app.api.auth_audit import (
    ApiKeyAuthAuditEvent,
    ApiKeyAuthAuditOutcome,
    InMemoryApiKeyAuthAuditLog,
    SqlAlchemyApiKeyAuthAuditLog,
)
from app.core.config import Settings
from app.db.engine import build_engine
from app.main import create_app


def test_api_key_auth_allows_local_development_by_default() -> None:
    client = TestClient(create_app())

    response = client.get("/areas")

    assert response.status_code == 200


def test_api_key_auth_ignores_api_key_config_when_disabled() -> None:
    client = TestClient(
        create_app(Settings(REQUIRE_API_KEY=False, API_KEYS="duplicate,duplicate"))
    )

    response = client.get("/areas")

    assert response.status_code == 200


def test_api_key_auth_leaves_health_and_version_public() -> None:
    client = TestClient(
        create_app(Settings(REQUIRE_API_KEY=True, API_KEYS="production-key"))
    )

    assert client.get("/health").status_code == 200
    assert client.get("/version").status_code == 200


@pytest.mark.parametrize(
    "path",
    ["/areas", "/docs", "/openapi.json"],
)
def test_api_key_auth_requires_key_for_protected_paths(path: str) -> None:
    client = TestClient(
        create_app(Settings(REQUIRE_API_KEY=True, API_KEYS="production-key"))
    )

    response = client.get(path)

    assert response.status_code == 401
    assert response.json()["detail"] == "API key is required"


def test_api_key_auth_rejects_invalid_key() -> None:
    client = TestClient(
        create_app(Settings(REQUIRE_API_KEY=True, API_KEYS="production-key"))
    )

    response = client.get("/areas", headers={"X-API-Key": "wrong-key"})

    assert response.status_code == 403
    assert response.json()["detail"] == "API key is invalid"


def test_api_key_auth_accepts_configured_key() -> None:
    client = TestClient(
        create_app(Settings(REQUIRE_API_KEY=True, API_KEYS=" production-key "))
    )

    response = client.get("/areas", headers={"X-API-Key": "production-key"})

    assert response.status_code == 200
    assert response.json() == []


def test_api_key_auth_accepts_configured_sha256_key_hash() -> None:
    digest = sha256(b"production-key").hexdigest()
    client = TestClient(
        create_app(Settings(REQUIRE_API_KEY=True, API_KEYS=f"sha256:{digest}"))
    )

    response = client.get("/areas", headers={"X-API-Key": "production-key"})

    assert response.status_code == 200
    assert response.json() == []


def test_api_key_auth_accepts_active_api_key_spec() -> None:
    client = TestClient(
        create_app(
            Settings(
                REQUIRE_API_KEY=True,
                API_KEY_SPECS="primary|active|production-key",
            )
        )
    )

    response = client.get("/areas", headers={"X-API-Key": "production-key"})

    assert response.status_code == 200
    assert response.json() == []


def test_api_key_auth_rejects_retired_api_key_spec() -> None:
    client = TestClient(
        create_app(
            Settings(
                REQUIRE_API_KEY=True,
                API_KEY_SPECS="old|retired|production-key",
            )
        )
    )

    response = client.get("/areas", headers={"X-API-Key": "production-key"})

    assert response.status_code == 503
    assert response.json()["detail"] == "API key auth is not configured"


def test_api_key_auth_accepts_active_sha256_api_key_spec() -> None:
    digest = sha256(b"production-key").hexdigest()
    client = TestClient(
        create_app(
            Settings(
                REQUIRE_API_KEY=True,
                API_KEY_SPECS=f"primary|active|sha256:{digest}",
            )
        )
    )

    response = client.get("/areas", headers={"X-API-Key": "production-key"})

    assert response.status_code == 200
    assert response.json() == []


def test_api_key_auth_logs_accepted_lifecycle_key_without_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[dict[str, object]] = []

    def capture_info(message: str, *, extra: dict[str, object]) -> None:
        events.append({"message": message, **extra})

    monkeypatch.setattr(api_key_auth.logger, "info", capture_info)
    client = TestClient(
        create_app(
            Settings(
                REQUIRE_API_KEY=True,
                API_KEY_SPECS="primary|active|production-key",
            )
        )
    )

    response = client.get("/areas", headers={"X-API-Key": "production-key"})

    assert response.status_code == 200
    assert events == [
        {
            "message": "api key auth",
            "event_type": "api_key_auth",
            "outcome": "accepted",
            "status_code": 200,
            "api_key_id": "primary",
            "api_key_source": "api_key_specs",
            "method": "GET",
            "path": "/areas",
        }
    ]
    assert "production-key" not in repr(events)


def test_api_key_auth_logs_invalid_key_without_secret_or_key_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[dict[str, object]] = []

    def capture_info(message: str, *, extra: dict[str, object]) -> None:
        events.append({"message": message, **extra})

    monkeypatch.setattr(api_key_auth.logger, "info", capture_info)
    client = TestClient(
        create_app(
            Settings(
                REQUIRE_API_KEY=True,
                API_KEY_SPECS="primary|active|production-key",
            )
        )
    )

    response = client.get("/areas", headers={"X-API-Key": "wrong-key"})

    assert response.status_code == 403
    assert events == [
        {
            "message": "api key auth",
            "event_type": "api_key_auth",
            "outcome": "invalid",
            "status_code": 403,
            "api_key_id": None,
            "api_key_source": None,
            "method": "GET",
            "path": "/areas",
        }
    ]
    assert "wrong-key" not in repr(events)
    assert "production-key" not in repr(events)


def test_api_key_auth_logs_legacy_key_without_key_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[dict[str, object]] = []

    def capture_info(message: str, *, extra: dict[str, object]) -> None:
        events.append({"message": message, **extra})

    monkeypatch.setattr(api_key_auth.logger, "info", capture_info)
    client = TestClient(
        create_app(Settings(REQUIRE_API_KEY=True, API_KEYS="production-key"))
    )

    response = client.get("/areas", headers={"X-API-Key": "production-key"})

    assert response.status_code == 200
    assert events[0]["api_key_id"] is None
    assert events[0]["api_key_source"] == "api_keys"
    assert "production-key" not in repr(events)


def test_api_key_auth_records_accepted_lifecycle_key_audit_event_without_secret() -> None:
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

    response = client.get("/areas", headers={"X-API-Key": "production-key"})

    assert response.status_code == 200
    events = audit_log.list_all()
    assert len(events) == 1
    assert events[0].outcome == "accepted"
    assert events[0].status_code == 200
    assert events[0].method == "GET"
    assert events[0].path == "/areas"
    assert events[0].key_id == "primary"
    assert events[0].source == "api_key_specs"
    assert "production-key" not in repr(events)


def test_api_key_auth_records_invalid_key_audit_event_without_secret_or_key_id() -> None:
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

    response = client.get("/areas", headers={"X-API-Key": "wrong-key"})

    assert response.status_code == 403
    events = audit_log.list_all()
    assert len(events) == 1
    assert events[0].outcome == "invalid"
    assert events[0].status_code == 403
    assert events[0].key_id is None
    assert events[0].source is None
    assert "wrong-key" not in repr(events)
    assert "production-key" not in repr(events)


def test_api_key_auth_fails_closed_when_audit_event_persistence_fails() -> None:
    class FailingAuditLog:
        def record(self, event: ApiKeyAuthAuditEvent) -> ApiKeyAuthAuditEvent:
            raise RuntimeError("audit unavailable")

    client = TestClient(
        create_app(
            Settings(
                REQUIRE_API_KEY=True,
                API_KEY_SPECS="primary|active|production-key",
            ),
            api_key_audit_log=FailingAuditLog(),
        )
    )

    response = client.get("/areas", headers={"X-API-Key": "production-key"})

    assert response.status_code == 503
    assert response.json()["detail"] == "API key audit logging failed"


@pytest.mark.skipif(os.getenv("RUN_DB_SMOKE") != "1", reason="DB smoke not enabled")
def test_sqlalchemy_api_key_auth_audit_log_persists_event_without_secret() -> None:
    engine = build_engine()
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    audit_log = SqlAlchemyApiKeyAuthAuditLog(session_factory)
    event_id = uuid4()
    event = ApiKeyAuthAuditEvent(
        outcome=ApiKeyAuthAuditOutcome.ACCEPTED,
        status_code=200,
        method="GET",
        path="/areas",
        key_id="primary",
        source="api_key_specs",
        ip_address="127.0.0.1",
        user_agent="pytest",
        event_id=event_id,
    )

    try:
        recorded = audit_log.record(event)
        events = [stored for stored in audit_log.list_all() if stored.event_id == event_id]
    finally:
        with session_factory() as session:
            session.execute(
                text("DELETE FROM audit.events WHERE audit_event_id = :event_id"),
                {"event_id": event_id},
            )
            session.commit()

    assert recorded == event
    assert events == [event]
    assert "production-key" not in repr(events)


def test_api_key_auth_fails_closed_when_required_but_unconfigured() -> None:
    client = TestClient(create_app(Settings(REQUIRE_API_KEY=True, API_KEYS=" ")))

    response = client.get("/areas", headers={"X-API-Key": "production-key"})

    assert response.status_code == 503
    assert response.json()["detail"] == "API key auth is not configured"


def test_settings_parses_api_keys() -> None:
    settings = Settings(API_KEYS=" key-a , key-b ")

    assert settings.parsed_api_keys() == frozenset({"key-a", "key-b"})


def test_settings_parses_api_key_hash_specs() -> None:
    digest = sha256(b"key-a").hexdigest().upper()
    settings = Settings(API_KEYS=f" sha256:{digest} ")

    assert settings.parsed_api_keys() == frozenset({f"sha256:{digest.lower()}"})


def test_settings_parses_api_key_lifecycle_specs() -> None:
    digest = sha256(b"key-b").hexdigest().upper()
    settings = Settings(
        API_KEY_SPECS=f" key-a | active | raw-a , key-b | retired | sha256:{digest} "
    )

    specs = settings.parsed_api_key_specs()

    assert [spec.key_id for spec in specs] == ["key-a", "key-b"]
    assert [spec.status for spec in specs] == ["active", "retired"]
    assert [spec.secret_spec for spec in specs] == ["raw-a", f"sha256:{digest.lower()}"]


def test_settings_active_api_key_specs_join_legacy_api_keys() -> None:
    settings = Settings(
        API_KEYS="legacy-key",
        API_KEY_SPECS="new|active|new-key,old|retired|old-key",
    )

    assert settings.parsed_api_keys() == frozenset({"legacy-key", "new-key"})


def test_settings_api_keys_fail_closed_for_duplicates() -> None:
    settings = Settings(API_KEYS="key-a,key-a")

    with pytest.raises(ValueError, match="Duplicate API_KEYS"):
        settings.parsed_api_keys()


@pytest.mark.parametrize(
    "api_keys,match",
    [
        ("SHA256:" + ("a" * 64), "hash prefix must be lowercase"),
        ("sha256:not-hex", "64 hex characters"),
        ("sha256:" + ("a" * 63), "64 hex characters"),
    ],
)
def test_settings_api_key_hash_specs_fail_closed_for_malformed_entries(
    api_keys: str,
    match: str,
) -> None:
    settings = Settings(API_KEYS=api_keys)

    with pytest.raises(ValueError, match=match):
        settings.parsed_api_keys()


@pytest.mark.parametrize(
    "api_key_specs,match",
    [
        ("key-a|active", "id\\|status\\|secret"),
        ("key-a||secret", "include id, status, and secret"),
        ("key-a|paused|secret", "status must be active or retired"),
        ("key-a|active|secret,key-a|retired|other", "Duplicate API_KEY_SPECS id"),
        ("key-a|active|secret,key-b|retired|secret", "Duplicate API_KEY_SPECS secret"),
        ("key-a|active|SHA256:" + ("a" * 64), "hash prefix must be lowercase"),
    ],
)
def test_settings_api_key_lifecycle_specs_fail_closed_for_malformed_entries(
    api_key_specs: str,
    match: str,
) -> None:
    settings = Settings(API_KEY_SPECS=api_key_specs)

    with pytest.raises(ValueError, match=match):
        settings.parsed_api_key_specs()
