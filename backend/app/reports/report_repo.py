from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol
from uuid import UUID

from sqlalchemy import text as sql_text
from sqlalchemy.orm import Session

from app.domain.enums import ReportReviewStatus
from app.domain.report_contracts import ReportReviewActionContract, ReportRunContract
from app.reports.artifacts import serialize_report_artifact
from app.reports.models import ReportRunModel


class ReportRunRepository(Protocol):
    def add(self, report_run: ReportRunContract) -> ReportRunContract: ...

    def get(self, report_run_id: UUID) -> ReportRunContract | None: ...

    def update_review_status(
        self,
        report_run_id: UUID,
        *,
        new_status: ReportReviewStatus,
        reviewer_id: str,
        reason: str | None = None,
    ) -> ReportRunContract | None: ...


class InMemoryReportRunRepository:
    def __init__(self) -> None:
        self._store: dict[UUID, ReportRunContract] = {}

    def add(self, report_run: ReportRunContract) -> ReportRunContract:
        stored = report_run.model_copy(
            update={
                "artifact_metadata": _with_persistence(
                    report_run.artifact_metadata,
                    persistence="memory",
                )
            }
        )
        self._store[stored.report_run_id] = stored
        return stored

    def get(self, report_run_id: UUID) -> ReportRunContract | None:
        return self._store.get(report_run_id)

    def update_review_status(
        self,
        report_run_id: UUID,
        *,
        new_status: ReportReviewStatus,
        reviewer_id: str,
        reason: str | None = None,
    ) -> ReportRunContract | None:
        existing = self._store.get(report_run_id)
        if existing is None:
            return None
        action = ReportReviewActionContract(
            action=new_status,
            from_status=existing.review_status,
            to_status=new_status,
            reviewer_id=reviewer_id,
            reason=reason,
        )
        updated = existing.model_copy(
            update={
                "review_status": new_status,
                "reviewed_by": reviewer_id,
                "reviewed_at": datetime.now(UTC),
                "review_actions": [*existing.review_actions, action],
            }
        )
        self._store[report_run_id] = updated
        return updated


class SqlAlchemyReportRunRepository:
    def __init__(self, session: Session, object_store_root: str | Path) -> None:
        self._session = session
        self._object_store_root = Path(object_store_root)

    def add(self, report_run: ReportRunContract) -> ReportRunContract:
        persisted = self._prepare_persisted_report(report_run)
        artifact_path = self._artifact_path(persisted.report_run_id).resolve()
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(
            serialize_report_artifact(persisted),
            encoding="utf-8",
        )
        model = self._contract_to_model(persisted, artifact_path)
        self._session.add(model)
        self._session.flush()
        return persisted

    def get(self, report_run_id: UUID) -> ReportRunContract | None:
        model = self._session.get(ReportRunModel, report_run_id)
        if model is None:
            return None
        artifact_path = self._artifact_path_from_model(model)
        if not artifact_path.exists():
            raise ValueError(f"Report artifact '{artifact_path}' is missing")
        return ReportRunContract.model_validate(
            json.loads(artifact_path.read_text(encoding="utf-8"))
        )

    def update_review_status(
        self,
        report_run_id: UUID,
        *,
        new_status: ReportReviewStatus,
        reviewer_id: str,
        reason: str | None = None,
    ) -> ReportRunContract | None:
        model = self._session.get(ReportRunModel, report_run_id)
        if model is None:
            return None
        artifact_path = self._artifact_path_from_model(model)
        if not artifact_path.exists():
            raise ValueError(f"Report artifact '{artifact_path}' is missing")
        report = ReportRunContract.model_validate(
            json.loads(artifact_path.read_text(encoding="utf-8"))
        )
        action = ReportReviewActionContract(
            action=new_status,
            from_status=report.review_status,
            to_status=new_status,
            reviewer_id=reviewer_id,
            reason=reason,
        )
        updated = report.model_copy(
            update={
                "review_status": new_status,
                "reviewed_by": reviewer_id,
                "reviewed_at": datetime.now(UTC),
                "review_actions": [*report.review_actions, action],
            }
        )
        artifact_path.write_text(
            serialize_report_artifact(updated),
            encoding="utf-8",
        )
        return updated

    def _prepare_persisted_report(
        self,
        report_run: ReportRunContract,
    ) -> ReportRunContract:
        artifact_path = self._artifact_path(report_run.report_run_id).resolve()
        artifact_uri = str(artifact_path.resolve())
        cost_metrics = _report_cost_metrics(report_run)
        artifact_metadata = _with_persistence(
            report_run.artifact_metadata,
            persistence="postgres+object_store",
            output_uri=artifact_uri,
            machine_json_uri=artifact_uri,
            cost_metrics=cost_metrics,
        )
        return report_run.model_copy(
            update={
                "output_uri": artifact_uri,
                "artifact_metadata": artifact_metadata,
            }
        )

    def _artifact_path(self, report_run_id: UUID) -> Path:
        return self._object_store_root / f"{report_run_id}.json"

    def _artifact_path_from_model(self, model: ReportRunModel) -> Path:
        uri = model.machine_json_uri or model.output_uri
        if uri is None:
            raise ValueError(f"Report run '{model.report_run_id}' has no artifact URI")
        return Path(uri)

    def _resolve_intent_id(self, intent_code: str) -> UUID | None:
        """Look up intent_id from core.intents by intent_code string.

        Returns None if the intent_code is not present in the DB (e.g. when
        a new IntentCode value has been added but the seed has not been applied).
        Callers should log a warning but not fail hard — the row can still be
        stored without the FK; it simply won't be linked until seeds are applied.
        """
        row = self._session.execute(
            sql_text(
                "SELECT intent_id FROM core.intents WHERE intent_code = :intent_code LIMIT 1"
            ),
            {"intent_code": str(intent_code)},
        ).one_or_none()
        if row is None:
            return None
        return UUID(str(row[0]))

    def _contract_to_model(
        self,
        report_run: ReportRunContract,
        artifact_path: Path,
    ) -> ReportRunModel:
        intent_id = self._resolve_intent_id(report_run.intent_code)
        return ReportRunModel(
            report_run_id=report_run.report_run_id,
            area_id=report_run.area_id,
            intent_id=intent_id,
            status=report_run.status.value,
            started_at=report_run.started_at,
            finished_at=report_run.finished_at,
            output_uri=str(artifact_path),
            machine_json_uri=str(artifact_path),
            source_manifest=report_run.source_manifest,
            assumptions=report_run.assumptions,
            caveats=report_run.caveats,
            cost_metrics=_report_cost_metrics(report_run),
        )


def _with_persistence(
    metadata: dict[str, object],
    *,
    persistence: str,
    output_uri: str | None = None,
    machine_json_uri: str | None = None,
    cost_metrics: dict[str, Any] | None = None,
) -> dict[str, object]:
    merged: dict[str, object] = dict(metadata)
    merged.setdefault("artifact_kind", "report_run")
    merged.setdefault("report_schema", "report_run_contract_v1")
    merged["persistence"] = persistence
    if output_uri is not None:
        merged["output_uri"] = output_uri
    if machine_json_uri is not None:
        merged["machine_json_uri"] = machine_json_uri
    if cost_metrics is not None:
        merged["cost_metrics"] = cost_metrics
    return merged


def _report_cost_metrics(report_run: ReportRunContract) -> dict[str, Any]:
    default_metrics: dict[str, Any] = {
        "evidence_count": len(report_run.evidence),
        "claim_count": len(report_run.claims),
        "unknown_count": len(report_run.unknowns),
        "advisory_count": len(report_run.advisory_claims),
        "red_flag_count": len(report_run.red_flags),
        "verification_task_count": len(report_run.verification_tasks),
        "estimated_total_usd_cents": 0,
        "compute_usd_cents": 0,
        "storage_usd_cents": 0,
        "llm_usd_cents": 0,
        "map_tile_usd_cents": 0,
        "geocoding_usd_cents": 0,
        "paid_data_usd_cents": 0,
        "human_review_usd_cents": 0,
        "human_review_minutes": 0,
    }
    cost_metrics = report_run.artifact_metadata.get("cost_metrics")
    if isinstance(cost_metrics, dict):
        return {**default_metrics, **cost_metrics}
    return default_metrics


__all__ = [
    "InMemoryReportRunRepository",
    "ReportRunRepository",
    "SqlAlchemyReportRunRepository",
]
