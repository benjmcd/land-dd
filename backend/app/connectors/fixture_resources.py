from __future__ import annotations

from importlib.resources import files
from importlib.resources.abc import Traversable
from uuid import UUID

from app.domain.source_contracts import (
    SourceDatasetContract,
    SourceDatasetVersionContract,
)

FIXTURE_SOURCE_ID = UUID("55555555-5555-4555-8555-555555555555")
FIXTURE_DATASET_ID = UUID("11111111-2222-4333-8444-555555555555")
FIXTURE_DATASET_VERSION_ID = UUID("22222222-2222-4222-8222-222222222222")

_FIXTURE_PACKAGE = "app.connectors.fixtures"


def connector_fixture_resource(fixture_key: str) -> Traversable | None:
    resource = files(_FIXTURE_PACKAGE).joinpath(f"{fixture_key}.json")
    if not resource.is_file():
        return None
    return resource


def fixture_dataset_contract() -> SourceDatasetContract:
    return SourceDatasetContract(
        dataset_id=FIXTURE_DATASET_ID,
        source_id=FIXTURE_SOURCE_ID,
        dataset_name="Static Connector Fixture Dataset",
        dataset_code="fixture-static-connectors",
        domain="fixture",
        metadata={"fixture_only": True},
    )


def fixture_dataset_version_contract() -> SourceDatasetVersionContract:
    return SourceDatasetVersionContract(
        dataset_version_id=FIXTURE_DATASET_VERSION_ID,
        dataset_id=FIXTURE_DATASET_ID,
        version_label="fixture-2026-06-04",
        storage_uri=f"package://{_FIXTURE_PACKAGE}",
        manifest={
            "fixtures": ("flood_success", "flood_failure"),
            "connector_names": ("fixture_flood_static",),
        },
        is_current=True,
        notes="Packaged static fixtures for connector API smoke coverage.",
    )


__all__ = [
    "FIXTURE_DATASET_ID",
    "FIXTURE_DATASET_VERSION_ID",
    "FIXTURE_SOURCE_ID",
    "connector_fixture_resource",
    "fixture_dataset_contract",
    "fixture_dataset_version_contract",
]
