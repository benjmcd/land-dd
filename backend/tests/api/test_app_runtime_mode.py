from __future__ import annotations

from app.api.dependencies import get_db_services, get_services
from app.core.config import Settings
from app.main import create_app


def test_create_app_defaults_to_in_memory_services() -> None:
    app = create_app(Settings(USE_DB_SERVICES=False))

    assert app.state.use_db_services is False
    assert get_services not in app.dependency_overrides
    assert hasattr(app.state, "services")


def test_create_app_can_use_settings_backed_db_services() -> None:
    app = create_app(Settings(USE_DB_SERVICES=True))

    assert app.state.use_db_services is True
    assert app.dependency_overrides[get_services] is get_db_services
    assert not hasattr(app.state, "services")


def test_create_app_explicit_override_wins_over_settings() -> None:
    app = create_app(Settings(USE_DB_SERVICES=True), use_db_services=False)

    assert app.state.use_db_services is False
    assert get_services not in app.dependency_overrides
    assert hasattr(app.state, "services")
