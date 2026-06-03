from __future__ import annotations

from typing import cast

from sqlalchemy import Table, UniqueConstraint

from app.source_registry.models import SourceModel


def test_source_model_maps_to_source_sources_table() -> None:
    assert SourceModel.__tablename__ == "sources"
    assert SourceModel.__table__.schema == "source"


def test_source_model_columns_match_migration_contract() -> None:
    table = cast(Table, SourceModel.__table__)
    columns = table.columns

    assert set(columns.keys()) == {
        "source_id",
        "name",
        "organization",
        "homepage_url",
        "authority_level",
        "geographic_scope",
        "domain",
        "update_cadence",
        "commercial_use_status",
        "license_summary",
        "attribution_required",
        "ai_use_allowed",
        "cache_allowed",
        "export_allowed",
        "raw_data_allowed",
        "notes",
        "created_at",
        "metadata",
    }
    assert columns["source_id"].primary_key is True
    assert columns["name"].nullable is False
    assert columns["domain"].nullable is False
    assert columns["commercial_use_status"].nullable is False
    assert columns["metadata"].nullable is False


def test_source_model_preserves_name_organization_unique_constraint() -> None:
    table = cast(Table, SourceModel.__table__)
    unique_constraints = [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    ]

    assert any(
        [column.name for column in constraint.columns] == ["name", "organization"]
        for constraint in unique_constraints
    )


def test_source_model_maps_reserved_metadata_column_to_safe_attribute() -> None:
    assert SourceModel.source_metadata.property.columns[0].name == "metadata"
