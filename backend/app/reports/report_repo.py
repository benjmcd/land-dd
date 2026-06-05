from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol
from uuid import UUID

from sqlalchemy import text as sql_text
from sqlalchemy.orm import Session

from app.domain.enums import IntentCode
from app.domain.report_contracts import ReportRunContract
from app.reports.models import ReportRunModel
from app.reports.scope import validate_scope_refs


class ReportRunRepository(Protocol):
    def add(self, report_run: ReportRunContract) -> ReportRunContract: ...

    def update(self, report_run: ReportRunContract) -> ReportRunContract: ...

    def get(self, report_run_id: UUID) -> ReportRunContract | None: ...

    def get_by_idempotency_key(
        self,
        idempotency_key: str,
        *,
        workspace_id: UUID | None = None,
    ) -> ReportRunContract | None: ...

    def list(
        self,
        *,
        workspace_id: UUID | None = None,
        area_id: UUID | None = None,
        intent_code: IntentCode | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ReportRunContract]: ...


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

    def update(self, report_run: ReportRunContract) -> ReportRunContract:
        if report_run.report_run_id not in self._store:
            raise ValueError(f"Report run '{report_run.report_run_id}' was not found")
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

    def get_by_idempotency_key(
        self,
        idempotency_key: str,
        *,
        workspace_id: UUID | None = None,
    ) -> ReportRunContract | None:
        normalized = _normalize_idempotency_key(idempotency_key)
        for report in self._store.values():
            if report.idempotency_key == normalized and report.workspace_id == workspace_id:
                return report
        return None

    def list(
        self,
        *,
        workspace_id: UUID | None = None,
        area_id: UUID | None = None,
        intent_code: IntentCode | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ReportRunContract]:
        reports = list(self._store.values())
        if workspace_id is not None:
            reports = [report for report in reports if report.workspace_id == workspace_id]
        if area_id is not None:
            reports = [report for report in reports if report.area_id == area_id]
        if intent_code is not None:
            reports = [
                report for report in reports if report.intent_code == intent_code
            ]
        reports.sort(
            key=lambda report: (report.started_at, str(report.report_run_id)),
            reverse=True,
        )
        return reports[offset : offset + limit]


class SqlAlchemyReportRunRepository:
    def __init__(self, session: Session, object_store_root: str | Path) -> None:
        self._session = session
        self._object_store_root = Path(object_store_root)

    def add(self, report_run: ReportRunContract) -> ReportRunContract:
        validate_scope_refs(
            self._session,
            workspace_id=report_run.workspace_id,
            requested_by=report_run.requested_by,
        )
        persisted = self._prepare_persisted_report(report_run)
        artifact_path = self._artifact_path(persisted.report_run_id).resolve()
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(
            json.dumps(persisted.model_dump(mode="json"), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        model = self._contract_to_model(persisted, artifact_path)
        self._session.add(model)
        self._session.flush()
        return persisted

    def update(self, report_run: ReportRunContract) -> ReportRunContract:
        model = self._session.get(ReportRunModel, report_run.report_run_id)
        if model is None:
            raise ValueError(f"Report run '{report_run.report_run_id}' was not found")
        artifact_path = self._artifact_path_from_model(model)
        persisted = report_run.model_copy(
            update={
                "output_uri": str(artifact_path),
                "artifact_metadata": _with_persistence(
                    report_run.artifact_metadata,
                    persistence="postgres+object_store",
                    output_uri=str(artifact_path),
                    machine_json_uri=str(artifact_path),
                    cost_metrics=_report_cost_metrics(report_run),
                ),
            }
        )
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(
            json.dumps(persisted.model_dump(mode="json"), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        model.review_status = persisted.review_status.value
        model.reviewed_by = persisted.reviewed_by
        model.reviewed_at = persisted.reviewed_at
        model.review_actions = [
            action.model_dump(mode="json") for action in persisted.review_actions
        ]
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

    def get_by_idempotency_key(
        self,
        idempotency_key: str,
        *,
        workspace_id: UUID | None = None,
    ) -> ReportRunContract | None:
        row = self._session.execute(
            sql_text(
                """
                SELECT report_run_id
                FROM reports.report_runs
                WHERE idempotency_key = :idempotency_key
                  AND (
                    (
                        CAST(:workspace_id AS uuid) IS NULL
                        AND workspace_id IS NULL
                    )
                    OR workspace_id = CAST(:workspace_id AS uuid)
                  )
                LIMIT 1
                """
            ),
            {
                "idempotency_key": _normalize_idempotency_key(idempotency_key),
                "workspace_id": str(workspace_id) if workspace_id is not None else None,
            },
        ).one_or_none()
        if row is None:
            return None
        return self.get(UUID(str(row[0])))

    def list(
        self,
        *,
        workspace_id: UUID | None = None,
        area_id: UUID | None = None,
        intent_code: IntentCode | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ReportRunContract]:
        rows = self._session.execute(
            sql_text(
                """
                SELECT report_run_id
                FROM reports.report_runs
                WHERE (
                    CAST(:workspace_id AS uuid) IS NULL
                    OR workspace_id = CAST(:workspace_id AS uuid)
                )
                AND (
                    CAST(:area_id AS uuid) IS NULL
                    OR area_id = CAST(:area_id AS uuid)
                )
                ORDER BY started_at DESC, report_run_id DESC
                """
            ),
            {
                "workspace_id": str(workspace_id) if workspace_id is not None else None,
                "area_id": str(area_id) if area_id is not None else None,
            },
        ).all()
        reports: list[ReportRunContract] = []
        for row in rows:
            report = self.get(UUID(str(row[0])))
            if report is None:
                continue
            if intent_code is not None and report.intent_code != intent_code:
                continue
            reports.append(report)
        return reports[offset : offset + limit]

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
            workspace_id=report_run.workspace_id,
            area_id=report_run.area_id,
            intent_id=intent_id,
            requested_by=report_run.requested_by,
            idempotency_key=report_run.idempotency_key,
            status=report_run.status.value,
            review_status=report_run.review_status.value,
            reviewed_by=report_run.reviewed_by,
            reviewed_at=report_run.reviewed_at,
            review_actions=[
                action.model_dump(mode="json") for action in report_run.review_actions
            ],
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


def _normalize_idempotency_key(idempotency_key: str) -> str:
    return idempotency_key.strip()


def _report_cost_metrics(report_run: ReportRunContract) -> dict[str, Any]:
    cost_metrics = report_run.artifact_metadata.get("cost_metrics")
    if isinstance(cost_metrics, dict):
        return cost_metrics
    return {
        "evidence_count": len(report_run.evidence),
        "claim_count": len(report_run.claims),
        "unknown_count": len(report_run.unknowns),
        "red_flag_count": len(report_run.red_flags),
        "verification_task_count": len(report_run.verification_tasks),
    }


__all__ = [
    "InMemoryReportRunRepository",
    "ReportRunRepository",
    "SqlAlchemyReportRunRepository",
]
