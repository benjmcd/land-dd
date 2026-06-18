from __future__ import annotations

from typing import Any, cast
from uuid import UUID, uuid4

from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session

from app.domain.enums import AuthorityLevel
from app.domain.source_contracts import SourceContract
from app.source_registry.models import SourceModel
from app.source_registry.source_repo import SqlAlchemySourceRepository


class _ScalarResult:
    def __init__(self, models: list[SourceModel]) -> None:
        self._models = models

    def all(self) -> list[SourceModel]:
        return self._models


class _ExecuteResult:
    def __init__(self, exists: bool) -> None:
        self._exists = exists

    def first(self) -> tuple[int] | None:
        if self._exists:
            return (1,)
        return None


class _FakeSession:
    def __init__(self) -> None:
        self.added: list[SourceModel] = []
        self.flushed = False
        self.get_value: SourceModel | None = None
        self.get_values: list[SourceModel | None] = []
        self.scalar_models: list[SourceModel] = []
        self.execute_exists = False
        self.last_get_model: type[SourceModel] | None = None
        self.last_get_id: UUID | None = None
        self.last_scalar_statement: Any | None = None
        self.last_execute_statement: Any | None = None

    def add(self, model: object) -> None:
        assert isinstance(model, SourceModel)
        self.added.append(model)

    def flush(self) -> None:
        self.flushed = True

    def get(self, model: type[SourceModel], source_id: UUID) -> SourceModel | None:
        self.last_get_model = model
        self.last_get_id = source_id
        if self.get_values:
            return self.get_values.pop(0)
        return self.get_value

    def scalars(self, statement: Any) -> _ScalarResult:
        self.last_scalar_statement = statement
        return _ScalarResult(self.scalar_models)

    def execute(self, statement: Any) -> _ExecuteResult:
        self.last_execute_statement = statement
        return _ExecuteResult(self.execute_exists)


def _make_source() -> SourceContract:
    return SourceContract(
        source_id=uuid4(),
        name="FEMA NFHL",
        organization="FEMA",
        homepage_url=cast(
            Any,
            "https://www.fema.gov/flood-maps/national-flood-hazard-layer",
        ),
        source_type="Public official",
        authority_level=AuthorityLevel.OFFICIAL_PRIMARY,
        domain="flood",
        geographic_scope="US",
        update_cadence="continuous",
        license_status="pending-review",
        commercial_use_status="yes",
        redistribution_status="restricted",
        license_summary="Public official data with caveats.",
        attribution_required=True,
        ai_use_allowed="unknown",
        cache_allowed="yes",
        export_allowed="unknown",
        raw_data_allowed="unknown",
        freshness_class="current",
        last_checked_at="2026-06-03",
        review_owner="lane-a",
        review_status="pending",
        notes="Fixture source.",
        metadata={"source_registry_id": "DS-002"},
    )


def _make_model(source: SourceContract) -> SourceModel:
    return SourceModel(
        source_id=source.source_id,
        name=source.name,
        organization=source.organization,
        homepage_url=str(source.homepage_url),
        authority_level=source.authority_level.value,
        geographic_scope=source.geographic_scope,
        domain=source.domain,
        update_cadence=source.update_cadence,
        commercial_use_status=source.commercial_use_status,
        license_summary=source.license_summary,
        attribution_required=source.attribution_required,
        ai_use_allowed=source.ai_use_allowed,
        cache_allowed=source.cache_allowed,
        export_allowed=source.export_allowed,
        raw_data_allowed=source.raw_data_allowed,
        notes=source.notes,
        source_metadata={
            "fixture": True,
            "source_type": source.source_type,
            "license_status": source.license_status,
            "redistribution_status": source.redistribution_status,
            "freshness_class": source.freshness_class,
            "last_checked_at": source.last_checked_at,
            "review_owner": source.review_owner,
            "review_status": source.review_status,
        },
    )


def test_sqlalchemy_source_repository_add_maps_contract_to_model() -> None:
    fake_session = _FakeSession()
    repo = SqlAlchemySourceRepository(cast(Session, fake_session))
    source = _make_source()

    result = repo.add(source)

    assert fake_session.flushed is True
    assert len(fake_session.added) == 1
    added = fake_session.added[0]
    assert added.source_id == source.source_id
    assert added.name == source.name
    assert added.organization == source.organization
    assert added.homepage_url == str(source.homepage_url)
    assert added.authority_level == source.authority_level.value
    assert added.source_metadata["source_registry_id"] == "DS-002"
    assert added.source_metadata["license_status"] == "pending-review"
    assert added.source_metadata["redistribution_status"] == "restricted"
    assert result.source_id == source.source_id
    assert result.source_type == source.source_type
    assert result.license_status == source.license_status
    assert result.redistribution_status == source.redistribution_status
    assert result.freshness_class == source.freshness_class
    assert result.review_owner == source.review_owner


def test_sqlalchemy_source_repository_get_or_add_returns_existing_source() -> None:
    fake_session = _FakeSession()
    source = _make_source()
    fake_session.get_value = _make_model(source)
    repo = SqlAlchemySourceRepository(cast(Session, fake_session))

    result = repo.get_or_add(source)

    assert result.source_id == source.source_id
    assert fake_session.flushed is False
    assert fake_session.last_execute_statement is None


def test_sqlalchemy_source_repository_get_or_add_uses_conflict_safe_insert() -> None:
    fake_session = _FakeSession()
    source = _make_source()
    fake_session.get_values = [None, _make_model(source)]
    repo = SqlAlchemySourceRepository(cast(Session, fake_session))

    result = repo.get_or_add(source)

    assert result.source_id == source.source_id
    assert fake_session.flushed is True
    assert fake_session.last_execute_statement is not None
    compiled = str(
        fake_session.last_execute_statement.compile(
            dialect=cast(Any, postgresql).dialect(),
        ),
    )
    assert "ON CONFLICT" in compiled
    assert "DO NOTHING" in compiled


def test_sqlalchemy_source_repository_get_maps_model_to_contract() -> None:
    fake_session = _FakeSession()
    source = _make_source()
    fake_session.get_value = _make_model(source)
    repo = SqlAlchemySourceRepository(cast(Session, fake_session))

    result = repo.get(source.source_id)

    assert fake_session.last_get_model is SourceModel
    assert fake_session.last_get_id == source.source_id
    assert result is not None
    assert result.source_id == source.source_id
    assert result.authority_level == AuthorityLevel.OFFICIAL_PRIMARY
    assert result.cache_allowed == "yes"
    assert result.metadata["fixture"] is True
    assert result.source_type == "Public official"
    assert result.license_status == "pending-review"
    assert result.redistribution_status == "restricted"
    assert result.freshness_class == "current"


def test_sqlalchemy_source_repository_list_all_maps_models_to_contracts() -> None:
    fake_session = _FakeSession()
    source = _make_source()
    fake_session.scalar_models = [_make_model(source)]
    repo = SqlAlchemySourceRepository(cast(Session, fake_session))

    results = repo.list_all()

    assert fake_session.last_scalar_statement is not None
    assert [result.source_id for result in results] == [source.source_id]


def test_sqlalchemy_source_repository_preserves_placeholder_homepage_as_metadata() -> None:
    fake_session = _FakeSession()
    source = _make_source()
    model = _make_model(source)
    model.homepage_url = "TBD"
    fake_session.scalar_models = [model]
    repo = SqlAlchemySourceRepository(cast(Session, fake_session))

    results = repo.list_all()

    assert len(results) == 1
    assert results[0].homepage_url is None
    assert results[0].metadata["raw_url"] == "TBD"


def test_sqlalchemy_source_repository_exists_by_name_org_uses_session() -> None:
    fake_session = _FakeSession()
    fake_session.execute_exists = True
    repo = SqlAlchemySourceRepository(cast(Session, fake_session))

    assert repo.exists_by_name_org("FEMA NFHL", "FEMA") is True
    assert fake_session.last_execute_statement is not None
