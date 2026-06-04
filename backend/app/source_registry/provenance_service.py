from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.domain.source_contracts import (
    SourceContract,
    SourceDatasetContract,
    SourceDatasetVersionContract,
    SourceRetrievalRunContract,
    SourceRetrievalStatus,
)
from app.source_registry.provenance_repo import SourceProvenanceRepository
from app.source_registry.service import SourceService


class SourceProvenanceService:
    def __init__(
        self,
        *,
        source_service: SourceService,
        repo: SourceProvenanceRepository,
    ) -> None:
        self._source_service = source_service
        self._repo = repo

    def create_dataset(
        self,
        *,
        source_id: UUID,
        dataset_name: str,
        domain: str,
        dataset_code: str | None = None,
        geometry_type: str | None = None,
        spatial_resolution: str | None = None,
        temporal_coverage: str | None = None,
        legal_caveat: str | None = None,
        source_url: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> SourceDatasetContract:
        self._require_source(source_id)
        _require_non_empty(dataset_name, "dataset_name")
        _require_non_empty(domain, "domain")
        dataset = SourceDatasetContract.model_validate(
            {
                "source_id": source_id,
                "dataset_name": dataset_name,
                "domain": domain,
                "dataset_code": dataset_code,
                "geometry_type": geometry_type,
                "spatial_resolution": spatial_resolution,
                "temporal_coverage": temporal_coverage,
                "legal_caveat": legal_caveat,
                "source_url": source_url,
                "metadata": metadata or {},
            }
        )
        return self._repo.add_dataset(dataset)

    def create_dataset_version(
        self,
        *,
        dataset_id: UUID,
        version_label: str,
        published_at: datetime | None = None,
        retrieved_at: datetime | None = None,
        valid_from: datetime | None = None,
        valid_to: datetime | None = None,
        checksum: str | None = None,
        storage_uri: str | None = None,
        manifest: dict[str, object] | None = None,
        is_current: bool = False,
        notes: str | None = None,
    ) -> SourceDatasetVersionContract:
        self._require_dataset(dataset_id)
        _require_non_empty(version_label, "version_label")
        version_kwargs: dict[str, object] = {
            "dataset_id": dataset_id,
            "version_label": version_label,
            "manifest": manifest or {},
            "is_current": is_current,
        }
        if published_at is not None:
            version_kwargs["published_at"] = published_at
        if retrieved_at is not None:
            version_kwargs["retrieved_at"] = retrieved_at
        if valid_from is not None:
            version_kwargs["valid_from"] = valid_from
        if valid_to is not None:
            version_kwargs["valid_to"] = valid_to
        if checksum is not None:
            version_kwargs["checksum"] = checksum
        if storage_uri is not None:
            version_kwargs["storage_uri"] = storage_uri
        if notes is not None:
            version_kwargs["notes"] = notes
        version = SourceDatasetVersionContract.model_validate(version_kwargs)
        return self._repo.add_dataset_version(version)

    def record_retrieval_run(
        self,
        *,
        dataset_version_id: UUID | None,
        connector_name: str,
        status: SourceRetrievalStatus = SourceRetrievalStatus.PENDING,
        started_at: datetime | None = None,
        finished_at: datetime | None = None,
        row_count: int | None = None,
        error_count: int = 0,
        warning_count: int = 0,
        log_uri: str | None = None,
        metrics: dict[str, object] | None = None,
    ) -> SourceRetrievalRunContract:
        if dataset_version_id is not None:
            self._require_dataset_version(dataset_version_id)
        _require_non_empty(connector_name, "connector_name")
        run_kwargs: dict[str, object] = {
            "connector_name": connector_name,
            "status": status,
            "row_count": row_count,
            "error_count": error_count,
            "warning_count": warning_count,
            "metrics": metrics or {},
        }
        if dataset_version_id is not None:
            run_kwargs["dataset_version_id"] = dataset_version_id
        if started_at is not None:
            run_kwargs["started_at"] = started_at
        if finished_at is not None:
            run_kwargs["finished_at"] = finished_at
        if log_uri is not None:
            run_kwargs["log_uri"] = log_uri
        run = SourceRetrievalRunContract.model_validate(run_kwargs)
        return self._repo.add_retrieval_run(run)

    def record_retrieval_run_contract(
        self,
        retrieval_run: SourceRetrievalRunContract,
    ) -> SourceRetrievalRunContract:
        if retrieval_run.dataset_version_id is not None:
            self._require_dataset_version(retrieval_run.dataset_version_id)
        _require_non_empty(retrieval_run.connector_name, "connector_name")
        if self.retrieval_run_exists(retrieval_run.ingest_run_id):
            raise ValueError(
                f"Retrieval run '{retrieval_run.ingest_run_id}' is already registered"
            )
        return self._repo.add_retrieval_run(retrieval_run)

    def retrieval_run_exists(self, ingest_run_id: UUID) -> bool:
        return self._repo.get_retrieval_run(ingest_run_id) is not None

    def export_review_bundle(self, source_id: UUID) -> dict[str, object]:
        source = self._require_source(source_id)
        datasets = self._repo.list_datasets_by_source(source_id)
        versions = [
            version
            for dataset in datasets
            for version in self._repo.list_versions_by_dataset(dataset.dataset_id)
        ]
        retrieval_runs = [
            run
            for version in versions
            for run in self._repo.list_runs_by_dataset_version(version.dataset_version_id)
        ]
        latest_status = (
            max(retrieval_runs, key=lambda run: run.started_at).status
            if retrieval_runs
            else SourceRetrievalStatus.PENDING
        )
        return {
            "source": source.model_dump(mode="json"),
            "production_use_allowed": self._source_service.source_production_use_allowed(
                source_id
            ),
            "datasets": [dataset.model_dump(mode="json") for dataset in datasets],
            "dataset_versions": [version.model_dump(mode="json") for version in versions],
            "retrieval_runs": [
                run.model_dump(mode="json") for run in retrieval_runs
            ],
            "latest_retrieval_status": latest_status.value,
            "review_summary": {
                "source_count": 1,
                "dataset_count": len(datasets),
                "dataset_version_count": len(versions),
                "retrieval_run_count": len(retrieval_runs),
            },
        }

    def _require_source(self, source_id: UUID) -> SourceContract:
        source = self._source_service.get(source_id)
        if source is None:
            raise ValueError(f"Source '{source_id}' is not registered")
        return source

    def _require_dataset(self, dataset_id: UUID) -> SourceDatasetContract:
        dataset = self._repo.get_dataset(dataset_id)
        if dataset is None:
            raise ValueError(f"Dataset '{dataset_id}' is not registered")
        return dataset

    def _require_dataset_version(
        self,
        dataset_version_id: UUID,
    ) -> SourceDatasetVersionContract:
        version = self._repo.get_dataset_version(dataset_version_id)
        if version is None:
            raise ValueError(f"Dataset version '{dataset_version_id}' is not registered")
        return version


def _require_non_empty(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} is required")


__all__ = ["SourceProvenanceService"]
