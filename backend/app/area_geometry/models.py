from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import ENUM, JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import UserDefinedType

from app.db.base import AppBase
from app.db.types import confidence_band_enum

# Backward-compat alias
AreaGeometryBase = AppBase


class PostGISGeometry(UserDefinedType[str]):
    cache_ok = True

    def __init__(self, geometry_type: str, srid: int) -> None:
        self.geometry_type = geometry_type
        self.srid = srid

    def get_col_spec(self, **_kw: object) -> str:
        return f"geometry({self.geometry_type}, {self.srid})"


# area_type values are literal strings matching the SQL enum in 0001_initial_spine.sql.
# Note: Python AreaType enum has different values (domain representation);
# the DB mapping is handled in SqlAlchemyAreaRepository. See TODO in area_repo.py.
area_type_enum = ENUM(
    "parcel",
    "multi_parcel",
    "polygon",
    "address",
    "locality",
    "county",
    "watershed",
    "corridor",
    "generated_candidate",
    name="area_type",
    schema="core",
    create_type=False,
)


class AreaModel(AppBase):
    __tablename__ = "areas"
    __table_args__ = {"schema": "core"}

    area_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    workspace_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    area_type: Mapped[str] = mapped_column(area_type_enum, nullable=False)
    label: Mapped[str | None] = mapped_column(Text)
    input_reference: Mapped[str | None] = mapped_column(Text)
    geom: Mapped[str] = mapped_column(
        PostGISGeometry("MultiPolygon", 4326),
        nullable=False,
    )
    geom_validated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )
    geom_source: Mapped[str | None] = mapped_column(Text)
    geom_confidence: Mapped[str] = mapped_column(
        confidence_band_enum,
        nullable=False,
        server_default=text("'unknown'"),
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=text("now()"),
    )
    created_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    area_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )


class AreaVersionModel(AppBase):
    __tablename__ = "area_versions"
    __table_args__ = (
        UniqueConstraint("area_id", "version_num"),
        {"schema": "core"},
    )

    area_version_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    area_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core.areas.area_id"),
        nullable=False,
    )
    version_num: Mapped[int] = mapped_column(Integer, nullable=False)
    geom: Mapped[str] = mapped_column(
        PostGISGeometry("MultiPolygon", 4326),
        nullable=False,
    )
    change_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=text("now()"),
    )
    created_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))


__all__ = [
    "AppBase",
    "AreaGeometryBase",  # backward-compat alias for AppBase
    "AreaModel",
    "AreaVersionModel",
    "PostGISGeometry",
    "area_type_enum",
]
