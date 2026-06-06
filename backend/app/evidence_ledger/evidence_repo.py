from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Protocol
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import TextClause

from app.domain.enums import EvidenceType
from app.domain.evidence_contracts import EvidenceContract


class EvidenceRepository(Protocol):
    def add(self, evidence: EvidenceContract) -> EvidenceContract: ...

    def get(self, evidence_id: UUID) -> EvidenceContract | None: ...

    def exists(self, evidence_id: UUID) -> bool: ...

    def mark_superseded(
        self,
        evidence_id: UUID,
        superseded_by: UUID,
    ) -> EvidenceContract: ...

    def list_by_area(self, area_id: UUID) -> list[EvidenceContract]: ...

    def list_by_source(self, source_id: UUID) -> list[EvidenceContract]: ...

    def list_by_type(self, evidence_type: EvidenceType) -> list[EvidenceContract]: ...

    def list_all(self) -> list[EvidenceContract]: ...


class InMemoryEvidenceRepository:
    def __init__(self) -> None:
        self._store: dict[UUID, EvidenceContract] = {}

    def add(self, evidence: EvidenceContract) -> EvidenceContract:
        if evidence.evidence_id in self._store:
            raise ValueError(f"Evidence '{evidence.evidence_id}' is already stored")
        self._store[evidence.evidence_id] = evidence
        return evidence

    def get(self, evidence_id: UUID) -> EvidenceContract | None:
        return self._store.get(evidence_id)

    def exists(self, evidence_id: UUID) -> bool:
        return evidence_id in self._store

    def mark_superseded(
        self,
        evidence_id: UUID,
        superseded_by: UUID,
    ) -> EvidenceContract:
        original = self._store.get(evidence_id)
        if original is None:
            raise ValueError(f"Evidence '{evidence_id}' is not stored")
        superseded = original.model_copy(update={"superseded_by": superseded_by})
        self._store[evidence_id] = superseded
        return superseded

    def list_by_area(self, area_id: UUID) -> list[EvidenceContract]:
        return [
            evidence
            for evidence in self._store.values()
            if evidence.area_id == area_id
        ]

    def list_by_source(self, source_id: UUID) -> list[EvidenceContract]:
        return [
            evidence
            for evidence in self._store.values()
            if evidence.source_id == source_id
        ]

    def list_by_type(self, evidence_type: EvidenceType) -> list[EvidenceContract]:
        return [
            evidence
            for evidence in self._store.values()
            if evidence.evidence_type == evidence_type
        ]

    def list_all(self) -> list[EvidenceContract]:
        return list(self._store.values())


class SqlAlchemyEvidenceRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, evidence: EvidenceContract) -> EvidenceContract:
        if self.exists(evidence.evidence_id):
            raise ValueError(f"Evidence '{evidence.evidence_id}' is already stored")

        row = self._session.execute(
            text(
                """
                INSERT INTO evidence.observations (
                    evidence_id,
                    area_id,
                    evidence_type,
                    domain,
                    observation,
                    observed_value,
                    method_code,
                    method_version,
                    confidence,
                    source_date,
                    retrieved_at,
                    caveat,
                    is_negative_evidence,
                    is_source_failure,
                    geometry,
                    metadata
                )
                VALUES (
                    :evidence_id,
                    :area_id,
                    :evidence_type,
                    :domain,
                    :observation,
                    CAST(:observed_value AS jsonb),
                    :method_code,
                    :method_version,
                    CAST(:confidence AS evidence.confidence_band),
                    CAST(:source_date AS date),
                    :observed_at,
                    :caveat,
                    :is_negative_evidence,
                    :is_source_failure,
                    ST_SetSRID(
                        ST_GeomFromGeoJSON(CAST(:geometry_geojson AS text)),
                        :geometry_srid
                    ),
                    CAST(:metadata AS jsonb)
                )
                RETURNING
                    evidence_id,
                    area_id,
                    evidence_type,
                    domain,
                    observation,
                    observed_value,
                    method_code,
                    method_version,
                    confidence::text AS confidence,
                    source_date,
                    retrieved_at,
                    caveat,
                    is_negative_evidence,
                    is_source_failure,
                    ST_AsGeoJSON(geometry) AS geometry_geojson,
                    ST_SRID(geometry) AS geometry_srid,
                    metadata AS evidence_metadata
                """
            ),
            _evidence_params(evidence),
        ).mappings().one()
        self._session.flush()
        return _row_to_evidence(row)

    def get(self, evidence_id: UUID) -> EvidenceContract | None:
        row = self._session.execute(
            _select_evidence_statement("WHERE evidence_id = :evidence_id"),
            {"evidence_id": evidence_id},
        ).mappings().one_or_none()
        if row is None:
            return None
        return _row_to_evidence(row)

    def exists(self, evidence_id: UUID) -> bool:
        return (
            self._session.execute(
                text(
                    """
                    SELECT 1
                    FROM evidence.observations
                    WHERE evidence_id = :evidence_id
                    LIMIT 1
                    """
                ),
                {"evidence_id": evidence_id},
            ).first()
            is not None
        )

    def mark_superseded(
        self,
        evidence_id: UUID,
        superseded_by: UUID,
    ) -> EvidenceContract:
        row = self._session.execute(
            text(
                """
                UPDATE evidence.observations
                SET metadata = metadata || CAST(:supersession_metadata AS jsonb)
                WHERE evidence_id = :evidence_id
                RETURNING
                    evidence_id,
                    area_id,
                    evidence_type,
                    domain,
                    observation,
                    observed_value,
                    method_code,
                    method_version,
                    confidence::text AS confidence,
                    source_date,
                    retrieved_at,
                    caveat,
                    is_negative_evidence,
                    is_source_failure,
                    ST_AsGeoJSON(geometry) AS geometry_geojson,
                    ST_SRID(geometry) AS geometry_srid,
                    metadata AS evidence_metadata
                """
            ),
            {
                "evidence_id": evidence_id,
                "supersession_metadata": json.dumps(
                    {"superseded_by": str(superseded_by)}
                ),
            },
        ).mappings().one_or_none()
        if row is None:
            raise ValueError(f"Evidence '{evidence_id}' is not stored")
        self._session.flush()
        return _row_to_evidence(row)

    def list_by_area(self, area_id: UUID) -> list[EvidenceContract]:
        rows = self._session.execute(
            _select_evidence_statement(
                "WHERE area_id = :area_id ORDER BY retrieved_at, evidence_id"
            ),
            {"area_id": area_id},
        ).mappings().all()
        return [_row_to_evidence(row) for row in rows]

    def list_by_source(self, source_id: UUID) -> list[EvidenceContract]:
        rows = self._session.execute(
            _select_evidence_statement(
                """
                WHERE metadata->>'source_id' = :source_id
                ORDER BY retrieved_at, evidence_id
                """
            ),
            {"source_id": str(source_id)},
        ).mappings().all()
        return [_row_to_evidence(row) for row in rows]

    def list_by_type(self, evidence_type: EvidenceType) -> list[EvidenceContract]:
        rows = self._session.execute(
            _select_evidence_statement(
                """
                WHERE evidence_type = :evidence_type
                ORDER BY retrieved_at, evidence_id
                """
            ),
            {"evidence_type": evidence_type.value},
        ).mappings().all()
        return [_row_to_evidence(row) for row in rows]

    def list_all(self) -> list[EvidenceContract]:
        rows = self._session.execute(
            _select_evidence_statement("ORDER BY retrieved_at, evidence_id")
        ).mappings().all()
        return [_row_to_evidence(row) for row in rows]


def _select_evidence_statement(suffix: str) -> TextClause:
    return text(
        f"""
        SELECT
            evidence_id,
            area_id,
            evidence_type,
            domain,
            observation,
            observed_value,
            method_code,
            method_version,
            confidence::text AS confidence,
            source_date,
            retrieved_at,
            caveat,
            is_negative_evidence,
            is_source_failure,
            ST_AsGeoJSON(geometry) AS geometry_geojson,
            ST_SRID(geometry) AS geometry_srid,
            metadata AS evidence_metadata
        FROM evidence.observations
        {suffix}
        """
    )


def _evidence_params(evidence: EvidenceContract) -> dict[str, object]:
    return {
        "evidence_id": evidence.evidence_id,
        "area_id": evidence.area_id,
        "evidence_type": evidence.evidence_type.value,
        "domain": evidence.domain,
        "observation": evidence.observation,
        "observed_value": json.dumps(evidence.observed_value),
        "method_code": evidence.method_code,
        "method_version": evidence.method_version,
        "confidence": evidence.confidence.value,
        "source_date": evidence.source_date,
        "observed_at": evidence.observed_at,
        "caveat": evidence.caveat,
        "is_negative_evidence": evidence.is_negative_evidence,
        "is_source_failure": evidence.is_source_failure,
        "geometry_geojson": (
            json.dumps(evidence.geometry_geojson)
            if evidence.geometry_geojson is not None
            else None
        ),
        "geometry_srid": evidence.geometry_srid,
        "metadata": json.dumps(_evidence_metadata(evidence)),
    }


def _evidence_metadata(evidence: EvidenceContract) -> dict[str, object]:
    metadata: dict[str, object] = {
        "source_id": str(evidence.source_id),
        "evidence_code": evidence.evidence_code,
        "observed_at": evidence.observed_at.isoformat(),
    }
    if evidence.superseded_by is not None:
        metadata["superseded_by"] = str(evidence.superseded_by)
    if evidence.source_ingest_run_id is not None:
        metadata["source_ingest_run_id"] = str(evidence.source_ingest_run_id)
    if evidence.spatial_precision_meters is not None:
        metadata["spatial_precision_meters"] = evidence.spatial_precision_meters
    return metadata


def _row_to_evidence(row: Any) -> EvidenceContract:
    metadata = _json_object(row["evidence_metadata"], "evidence metadata")
    return EvidenceContract(
        evidence_id=row["evidence_id"],
        area_id=row["area_id"],
        evidence_type=EvidenceType(row["evidence_type"]),
        evidence_code=_required_metadata_str(metadata, "evidence_code"),
        domain=row["domain"],
        observation=row["observation"],
        observed_value=_json_object(row["observed_value"], "observed_value"),
        source_id=_required_metadata_uuid(metadata, "source_id"),
        source_ingest_run_id=_optional_metadata_uuid(metadata, "source_ingest_run_id"),
        method_code=row["method_code"],
        method_version=row["method_version"],
        confidence=row["confidence"],
        caveat=row["caveat"],
        is_negative_evidence=row["is_negative_evidence"],
        is_source_failure=row["is_source_failure"],
        superseded_by=_optional_metadata_uuid(metadata, "superseded_by"),
        source_date=_source_date_string(row["source_date"]),
        observed_at=_observed_at(metadata, row["retrieved_at"]),
        geometry_geojson=_optional_json_object(row["geometry_geojson"], "geometry"),
        geometry_srid=row["geometry_srid"] or 4326,
        spatial_precision_meters=_optional_metadata_float(
            metadata,
            "spatial_precision_meters",
        ),
    )


def _required_metadata_str(metadata: dict[str, object], key: str) -> str:
    value = metadata.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"evidence.observations metadata.{key} is required")
    return value


def _required_metadata_uuid(metadata: dict[str, object], key: str) -> UUID:
    return UUID(_required_metadata_str(metadata, key))


def _optional_metadata_uuid(metadata: dict[str, object], key: str) -> UUID | None:
    value = metadata.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise ValueError(f"evidence.observations metadata.{key} must be a UUID string")
    return UUID(value)


def _optional_metadata_float(metadata: dict[str, object], key: str) -> float | None:
    value = metadata.get(key)
    if value is None:
        return None
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise ValueError(f"evidence.observations metadata.{key} must be numeric")
    return float(value)


def _observed_at(
    metadata: dict[str, object],
    retrieved_at: datetime,
) -> datetime:
    value = metadata.get("observed_at")
    if value is None:
        return retrieved_at
    if not isinstance(value, str) or not value:
        raise ValueError("evidence.observations metadata.observed_at must be a string")
    return datetime.fromisoformat(value)


def _source_date_string(value: object) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return str(value.isoformat())
    return str(value)


def _json_object(value: object, label: str) -> dict[str, object]:
    if isinstance(value, str):
        value = json.loads(value)
    if not isinstance(value, dict):
        raise ValueError(f"evidence.observations returned invalid {label}")
    return value


def _optional_json_object(value: object, label: str) -> dict[str, object] | None:
    if value is None:
        return None
    return _json_object(value, label)


__all__ = [
    "EvidenceRepository",
    "InMemoryEvidenceRepository",
    "SqlAlchemyEvidenceRepository",
]
