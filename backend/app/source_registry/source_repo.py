from __future__ import annotations

from typing import Any, Protocol, cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.enums import AuthorityLevel
from app.domain.source_contracts import SourceContract
from app.source_registry.models import SourceModel


class SourceRepository(Protocol):
    def add(self, source: SourceContract) -> SourceContract: ...

    def get(self, source_id: UUID) -> SourceContract | None: ...

    def list_all(self) -> list[SourceContract]: ...

    def exists_by_name_org(self, name: str, organization: str | None) -> bool: ...


class InMemorySourceRepository:
    def __init__(self) -> None:
        self._store: dict[UUID, SourceContract] = {}

    def add(self, source: SourceContract) -> SourceContract:
        self._store[source.source_id] = source
        return source

    def get(self, source_id: UUID) -> SourceContract | None:
        return self._store.get(source_id)

    def list_all(self) -> list[SourceContract]:
        return list(self._store.values())

    def exists_by_name_org(self, name: str, organization: str | None) -> bool:
        return any(
            s.name == name and s.organization == organization
            for s in self._store.values()
        )


class SqlAlchemySourceRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, source: SourceContract) -> SourceContract:
        model = _source_to_model(source)
        self._session.add(model)
        self._session.flush()
        return _model_to_source(model)

    def get(self, source_id: UUID) -> SourceContract | None:
        model = self._session.get(SourceModel, source_id)
        if model is None:
            return None
        return _model_to_source(model)

    def list_all(self) -> list[SourceContract]:
        statement = select(SourceModel).order_by(SourceModel.name, SourceModel.organization)
        return [
            _model_to_source(model)
            for model in self._session.scalars(statement).all()
        ]

    def exists_by_name_org(self, name: str, organization: str | None) -> bool:
        statement = select(SourceModel.source_id).where(SourceModel.name == name)
        if organization is None:
            statement = statement.where(SourceModel.organization.is_(None))
        else:
            statement = statement.where(SourceModel.organization == organization)
        return self._session.execute(statement.limit(1)).first() is not None


def _source_to_model(source: SourceContract) -> SourceModel:
    source_metadata = {
        **source.metadata,
        "source_type": source.source_type,
        "license_status": source.license_status,
        "redistribution_status": source.redistribution_status,
        "freshness_class": source.freshness_class,
        "last_checked_at": source.last_checked_at,
        "review_owner": source.review_owner,
        "review_status": source.review_status,
    }
    return SourceModel(
        source_id=source.source_id,
        name=source.name,
        organization=source.organization,
        homepage_url=str(source.homepage_url) if source.homepage_url is not None else None,
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
        source_metadata=source_metadata,
    )


def _model_to_source(model: SourceModel) -> SourceContract:
    metadata = model.source_metadata
    return SourceContract(
        source_id=model.source_id,
        name=model.name,
        organization=model.organization,
        homepage_url=cast(Any, model.homepage_url),
        source_type=_metadata_str(metadata, "source_type"),
        authority_level=AuthorityLevel(model.authority_level),
        domain=model.domain,
        geographic_scope=model.geographic_scope,
        update_cadence=model.update_cadence,
        license_status=_metadata_required_str(
            metadata,
            "license_status",
            default="unknown",
        ),
        commercial_use_status=model.commercial_use_status,
        redistribution_status=_metadata_required_str(
            metadata,
            "redistribution_status",
            default="unknown",
        ),
        license_summary=model.license_summary,
        attribution_required=model.attribution_required,
        cache_allowed=model.cache_allowed,
        export_allowed=model.export_allowed,
        ai_use_allowed=model.ai_use_allowed,
        raw_data_allowed=model.raw_data_allowed,
        freshness_class=_metadata_required_str(
            metadata,
            "freshness_class",
            default="unknown",
        ),
        last_checked_at=_metadata_str(metadata, "last_checked_at"),
        review_owner=_metadata_str(metadata, "review_owner"),
        review_status=_metadata_required_str(
            metadata,
            "review_status",
            default="pending",
        ),
        notes=model.notes,
        metadata=metadata,
    )


def _metadata_str(
    metadata: dict[str, Any],
    key: str,
) -> str | None:
    value = metadata.get(key)
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return str(value)


def _metadata_required_str(
    metadata: dict[str, Any],
    key: str,
    *,
    default: str,
) -> str:
    value = _metadata_str(metadata, key)
    if value is None:
        return default
    return value


__all__ = [
    "InMemorySourceRepository",
    "SourceRepository",
    "SqlAlchemySourceRepository",
]
