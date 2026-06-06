from __future__ import annotations

from datetime import UTC, datetime
from typing import Self
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator

from app.domain.enums import ConfidenceBand, EvidenceType

SUPPORTED_EVIDENCE_GEOMETRY_TYPES = {
    "Point",
    "MultiPoint",
    "LineString",
    "MultiLineString",
    "Polygon",
    "MultiPolygon",
}


class EvidenceContract(BaseModel):
    evidence_id: UUID = Field(default_factory=uuid4)
    area_id: UUID
    evidence_type: EvidenceType = EvidenceType.SOURCE_OBSERVATION
    evidence_code: str
    domain: str
    observation: str
    observed_value: dict[str, object] = Field(default_factory=dict)
    source_id: UUID
    dataset_version_id: UUID | None = None
    source_ingest_run_id: UUID | None = None
    method_code: str
    method_version: str = "0.1.0"
    confidence: ConfidenceBand = ConfidenceBand.UNKNOWN
    caveat: str | None = None
    is_negative_evidence: bool = False
    is_source_failure: bool = False
    superseded_by: UUID | None = None
    source_date: str | None = None
    observed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    geometry_geojson: dict[str, object] | None = None
    geometry_srid: int = 4326
    spatial_precision_meters: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_geometry(self) -> Self:
        if self.geometry_geojson is None:
            return self
        if self.geometry_srid != 4326:
            raise ValueError("evidence geometry SRID must be 4326")

        geom_type = self.geometry_geojson.get("type")
        if geom_type not in SUPPORTED_EVIDENCE_GEOMETRY_TYPES:
            raise ValueError("evidence geometry.type is not supported")
        coordinates = self.geometry_geojson.get("coordinates")
        if not isinstance(coordinates, list) or not coordinates:
            raise ValueError("evidence geometry.coordinates must be non-empty")
        return self
