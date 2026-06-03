from __future__ import annotations

import uuid

import pytest

from app.domain.enums import AuthorityLevel
from app.domain.source_contracts import SourceContract
from app.source_registry.service import SourceService
from app.source_registry.source_repo import InMemorySourceRepository


def _make_source(
    name: str = "Fixture Source",
    organization: str | None = "Fixture Org",
    domain: str = "flood",
) -> SourceContract:
    return SourceContract(
        name=name,
        organization=organization,
        domain=domain,
        authority_level=AuthorityLevel.OFFICIAL_PRIMARY,
        commercial_use_status="yes",
    )


@pytest.fixture()
def service() -> SourceService:
    return SourceService(InMemorySourceRepository())


def test_register_new_source_returns_stored_source(service: SourceService) -> None:
    source = _make_source()
    result = service.register(source)
    assert result.source_id == source.source_id
    assert result.name == "Fixture Source"


def test_register_duplicate_name_and_org_raises(service: SourceService) -> None:
    service.register(_make_source())
    with pytest.raises(ValueError, match="already registered"):
        service.register(_make_source())


def test_register_same_name_different_org_is_allowed(service: SourceService) -> None:
    service.register(_make_source(organization="Org A"))
    result = service.register(_make_source(organization="Org B"))
    assert result.organization == "Org B"


def test_register_same_name_none_org_deduplicates(service: SourceService) -> None:
    service.register(_make_source(organization=None))
    with pytest.raises(ValueError, match="already registered"):
        service.register(_make_source(organization=None))


def test_get_registered_source_by_id(service: SourceService) -> None:
    registered = service.register(_make_source())
    retrieved = service.get(registered.source_id)
    assert retrieved is not None
    assert retrieved.source_id == registered.source_id


def test_get_unknown_id_returns_none(service: SourceService) -> None:
    assert service.get(uuid.uuid4()) is None


def test_list_all_returns_all_registered_sources(service: SourceService) -> None:
    service.register(_make_source(name="Source A", organization="Org A"))
    service.register(_make_source(name="Source B", organization="Org B"))
    sources = service.list_all()
    assert len(sources) == 2
    names = {s.name for s in sources}
    assert names == {"Source A", "Source B"}


def test_list_all_empty_when_no_sources_registered(service: SourceService) -> None:
    assert service.list_all() == []
