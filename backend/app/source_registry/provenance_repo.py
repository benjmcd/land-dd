from __future__ import annotations

from typing import Any, Protocol, cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.source_contracts import (
    SourceDatasetContract,
    SourceDatasetVersionContract,
    SourceRetrievalRunContract,
    SourceRetrievalStatus,
)
from app.source_registry.models import (
    SourceDatasetModel,
    SourceDatasetVersionModel,
    SourceIngestRunModel,
)


class SourceProvenanceRepository(Protocol):
    def add_dataset(self, dataset: SourceDatasetContract) -> SourceDatasetContract: ...

    def get_dataset(self, dataset_id: UUID) -> SourceDatasetContract | None: ...

    def list_datasets_by_source(self, source_id: UUID) -> list[SourceDatasetContract]: ...

    def add_dataset_version(
        self,
        version: SourceDatasetVersionContract,
    ) -> SourceDatasetVersionContract: ...

    def get_dataset_version(
        self,
        dataset_version_id: UUID,
    ) -> SourceDatasetVersionContract | None: ...

    def list_versions_by_dataset(
        self,
        dataset_id: UUID,
    ) -> list[SourceDatasetVersionContract]: ...

    def add_retrieval_run(
        self,
        retrieval_run: SourceRetrievalRunContract,
    ) -> SourceRetrievalRunContract: ...

    def get_retrieval_run(
        self,
        ingest_run_id: UUID,
    ) -> SourceRetrievalRunContract | None: ...

    def list_runs_by_dataset_version(
        self,
        dataset_version_id: UUID,
    ) -> list[SourceRetrievalRunContract]: ...


class InMemorySourceProvenanceRepository:
    def __init__(self) -> None:
        self._datasets: dict[UUID, SourceDatasetContract] = {}
        self._versions: dict[UUID, SourceDatasetVersionContract] = {}
        self._runs: dict[UUID, SourceRetrievalRunContract] = {}

    def add_dataset(self, dataset: SourceDatasetContract) -> SourceDatasetContract:
        self._datasets[dataset.dataset_id] = dataset
        return dataset

    def get_dataset(self, dataset_id: UUID) -> SourceDatasetContract | None:
        return self._datasets.get(dataset_id)

    def list_datasets_by_source(self, source_id: UUID) -> list[SourceDatasetContract]:
        return [
            dataset
            for dataset in self._datasets.values()
            if dataset.source_id == source_id
        ]

    def add_dataset_version(
        self,
        version: SourceDatasetVersionContract,
    ) -> SourceDatasetVersionContract:
        self._versions[version.dataset_version_id] = version
        return version

    def get_dataset_version(
        self,
        dataset_version_id: UUID,
    ) -> SourceDatasetVersionContract | None:
        return self._versions.get(dataset_version_id)

    def list_versions_by_dataset(
        self,
        dataset_id: UUID,
    ) -> list[SourceDatasetVersionContract]:
        return [
            version
            for version in self._versions.values()
            if version.dataset_id == dataset_id
        ]

    def add_retrieval_run(
        self,
        retrieval_run: SourceRetrievalRunContract,
    ) -> SourceRetrievalRunContract:
        self._runs[retrieval_run.ingest_run_id] = retrieval_run
        return retrieval_run

    def get_retrieval_run(
        self,
        ingest_run_id: UUID,
    ) -> SourceRetrievalRunContract | None:
        return self._runs.get(ingest_run_id)

    def list_runs_by_dataset_version(
        self,
        dataset_version_id: UUID,
    ) -> list[SourceRetrievalRunContract]:
        return [
            run
            for run in self._runs.values()
            if run.dataset_version_id == dataset_version_id
        ]


class SqlAlchemySourceProvenanceRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add_dataset(self, dataset: SourceDatasetContract) -> SourceDatasetContract:
        model = _dataset_to_model(dataset)
        self._session.add(model)
        self._session.flush()
        return _model_to_dataset(model)

    def get_dataset(self, dataset_id: UUID) -> SourceDatasetContract | None:
        model = self._session.get(SourceDatasetModel, dataset_id)
        if model is None:
            return None
        return _model_to_dataset(model)

    def list_datasets_by_source(self, source_id: UUID) -> list[SourceDatasetContract]:
        stmt = (
            select(SourceDatasetModel)
            .where(SourceDatasetModel.source_id == source_id)
            .order_by(SourceDatasetModel.dataset_name)
        )
        return [
            _model_to_dataset(model)
            for model in self._session.execute(stmt).scalars().all()
        ]

    def add_dataset_version(
        self,
        version: SourceDatasetVersionContract,
    ) -> SourceDatasetVersionContract:
        model = _version_to_model(version)
        self._session.add(model)
        self._session.flush()
        return _model_to_version(model)

    def get_dataset_version(
        self,
        dataset_version_id: UUID,
    ) -> SourceDatasetVersionContract | None:
        model = self._session.get(SourceDatasetVersionModel, dataset_version_id)
        if model is None:
            return None
        return _model_to_version(model)

    def list_versions_by_dataset(
        self,
        dataset_id: UUID,
    ) -> list[SourceDatasetVersionContract]:
        stmt = (
            select(SourceDatasetVersionModel)
            .where(SourceDatasetVersionModel.dataset_id == dataset_id)
            .order_by(
                SourceDatasetVersionModel.version_label,
                SourceDatasetVersionModel.retrieved_at,
            )
        )
        return [
            _model_to_version(model)
            for model in self._session.execute(stmt).scalars().all()
        ]

    def add_retrieval_run(
        self,
        retrieval_run: SourceRetrievalRunContract,
    ) -> SourceRetrievalRunContract:
        model = _run_to_model(retrieval_run)
        self._session.add(model)
        self._session.flush()
        return _model_to_run(model)

    def get_retrieval_run(
        self,
        ingest_run_id: UUID,
    ) -> SourceRetrievalRunContract | None:
        model = self._session.get(SourceIngestRunModel, ingest_run_id)
        if model is None:
            return None
        return _model_to_run(model)

    def list_runs_by_dataset_version(
        self,
        dataset_version_id: UUID,
    ) -> list[SourceRetrievalRunContract]:
        stmt = (
            select(SourceIngestRunModel)
            .where(SourceIngestRunModel.dataset_version_id == dataset_version_id)
            .order_by(SourceIngestRunModel.started_at, SourceIngestRunModel.ingest_run_id)
        )
        return [
            _model_to_run(model)
            for model in self._session.execute(stmt).scalars().all()
        ]


def _dataset_to_model(dataset: SourceDatasetContract) -> SourceDatasetModel:
    return SourceDatasetModel(
        dataset_id=dataset.dataset_id,
        source_id=dataset.source_id,
        dataset_name=dataset.dataset_name,
        dataset_code=dataset.dataset_code,
        domain=dataset.domain,
        geometry_type=dataset.geometry_type,
        spatial_resolution=dataset.spatial_resolution,
        temporal_coverage=dataset.temporal_coverage,
        legal_caveat=dataset.legal_caveat,
        source_url=str(dataset.source_url) if dataset.source_url is not None else None,
        dataset_metadata=dataset.metadata,
    )


def _model_to_dataset(model: SourceDatasetModel) -> SourceDatasetContract:
    return SourceDatasetContract(
        dataset_id=model.dataset_id,
        source_id=model.source_id,
        dataset_name=model.dataset_name,
        dataset_code=model.dataset_code,
        domain=model.domain,
        geometry_type=model.geometry_type,
        spatial_resolution=model.spatial_resolution,
        temporal_coverage=model.temporal_coverage,
        legal_caveat=model.legal_caveat,
        source_url=cast(Any, model.source_url),
        metadata=model.dataset_metadata,
    )


def _version_to_model(version: SourceDatasetVersionContract) -> SourceDatasetVersionModel:
    return SourceDatasetVersionModel(
        dataset_version_id=version.dataset_version_id,
        dataset_id=version.dataset_id,
        version_label=version.version_label,
        published_at=version.published_at,
        retrieved_at=version.retrieved_at,
        valid_from=version.valid_from,
        valid_to=version.valid_to,
        checksum=version.checksum,
        storage_uri=version.storage_uri,
        manifest=version.manifest,
        is_current=version.is_current,
        notes=version.notes,
    )


def _model_to_version(model: SourceDatasetVersionModel) -> SourceDatasetVersionContract:
    return SourceDatasetVersionContract(
        dataset_version_id=model.dataset_version_id,
        dataset_id=model.dataset_id,
        version_label=model.version_label,
        published_at=model.published_at,
        retrieved_at=model.retrieved_at,
        valid_from=model.valid_from,
        valid_to=model.valid_to,
        checksum=model.checksum,
        storage_uri=model.storage_uri,
        manifest=model.manifest,
        is_current=model.is_current,
        notes=model.notes,
    )


def _run_to_model(run: SourceRetrievalRunContract) -> SourceIngestRunModel:
    return SourceIngestRunModel(
        ingest_run_id=run.ingest_run_id,
        dataset_version_id=run.dataset_version_id,
        connector_name=run.connector_name,
        started_at=run.started_at,
        finished_at=run.finished_at,
        status=_status_to_job_status(run.status),
        row_count=run.row_count,
        error_count=run.error_count,
        warning_count=run.warning_count,
        log_uri=run.log_uri,
        metrics=run.metrics,
    )


def _model_to_run(model: SourceIngestRunModel) -> SourceRetrievalRunContract:
    return SourceRetrievalRunContract(
        ingest_run_id=model.ingest_run_id,
        dataset_version_id=model.dataset_version_id,
        connector_name=model.connector_name,
        started_at=model.started_at,
        finished_at=model.finished_at,
        status=_job_status_to_status(model.status),
        row_count=model.row_count,
        error_count=model.error_count,
        warning_count=model.warning_count,
        log_uri=model.log_uri,
        metrics=model.metrics,
    )


def _status_to_job_status(status: SourceRetrievalStatus) -> str:
    return {
        SourceRetrievalStatus.PENDING: "queued",
        SourceRetrievalStatus.RUNNING: "running",
        SourceRetrievalStatus.SUCCEEDED: "succeeded",
        SourceRetrievalStatus.FAILED: "failed",
        SourceRetrievalStatus.BLOCKED: "needs_review",
        SourceRetrievalStatus.SKIPPED: "cancelled",
    }[status]


def _job_status_to_status(status: str) -> SourceRetrievalStatus:
    normalized = status.strip().lower()
    mapping = {
        "queued": SourceRetrievalStatus.PENDING,
        "running": SourceRetrievalStatus.RUNNING,
        "succeeded": SourceRetrievalStatus.SUCCEEDED,
        "failed": SourceRetrievalStatus.FAILED,
        "needs_review": SourceRetrievalStatus.BLOCKED,
        "cancelled": SourceRetrievalStatus.SKIPPED,
    }
    if normalized not in mapping:
        raise ValueError(f"unsupported retrieval status '{status}'")
    return mapping[normalized]


__all__ = [
    "InMemorySourceProvenanceRepository",
    "SourceProvenanceRepository",
    "SqlAlchemySourceProvenanceRepository",
]
