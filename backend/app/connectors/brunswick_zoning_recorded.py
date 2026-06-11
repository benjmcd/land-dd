from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid5

from app.domain.enums import ConfidenceBand, EvidenceType
from app.domain.evidence_contracts import EvidenceContract
from app.domain.source_contracts import (
    SourceContract,
    SourceRetrievalRunContract,
    SourceRetrievalStatus,
)

BRUNSWICK_ZONING_CONNECTOR_NAME = "brunswick_zoning_udo_recorded"
BRUNSWICK_ZONING_METHOD_CODE = "brunswick_udo_district_lookup"
BRUNSWICK_ZONING_METHOD_VERSION = "0.1.0"
BRUNSWICK_ZONING_UDO_URL = (
    "https://www.brunswickcountync.gov/874/Unified-Development-Ordinance"
)
BRUNSWICK_ZONING_UDO_ADOPTED = "2024-08-19"
BRUNSWICK_ZONING_UDO_EFFECTIVE = "2024-08-19"
BRUNSWICK_ZONING_CAVEAT = (
    "Brunswick County UDO district classification — screening only. "
    "Zoning code is sourced from county parcel/GIS data. "
    "UDO text context is a human-reviewed recorded snapshot (most recent revision 2024-08-19). "
    "Does not constitute a zoning compliance determination, permitted-use decision, "
    "entitlement, permit eligibility finding, buildability conclusion, or legal opinion. "
    "Verify all zoning context with Brunswick County Planning before any legal, "
    "permitting, construction, or financing decision."
)

_NAMESPACE = UUID("b3c7d4e2-6a5f-4c9b-8e7d-1f2a3b4c5d6e")

_VERIFY = "Verify with Brunswick County Planning."
_BRUNSWICK_UDO_DISTRICTS: dict[str, dict[str, object]] = {
    "RR": {
        "district_name": "Rural Low Density Residential",
        "use_category": "rural_low_density_residential",
        "residential_use_screening": "ALLOWED_WITH_RESTRICTIONS",
        "udo_note": (
            f"Rural low-density residential; individual wells and septic typical; "
            f"agricultural uses permitted. {_VERIFY}"
        ),
    },
    "R-7500": {
        "district_name": "Medium Density Residential",
        "use_category": "medium_density_residential",
        "residential_use_screening": "ALLOWED_WITH_RESTRICTIONS",
        "udo_note": (
            f"Medium-density residential; public water and sewer service expected. {_VERIFY}"
        ),
    },
    "R-6000": {
        "district_name": "High Density Residential",
        "use_category": "high_density_residential",
        "residential_use_screening": "ALLOWED_WITH_RESTRICTIONS",
        "udo_note": f"High-density residential; public water and sewer service expected. {_VERIFY}",
    },
    "SBR-6000": {
        "district_name": "High Density Site Built Residential",
        "use_category": "high_density_site_built_residential",
        "residential_use_screening": "ALLOWED_WITH_RESTRICTIONS",
        "udo_note": (
            f"High-density site-built residential; manufactured housing excluded. {_VERIFY}"
        ),
    },
    "MR-3200": {
        "district_name": "Multifamily Residential",
        "use_category": "multifamily_residential",
        "residential_use_screening": "ALLOWED_WITH_RESTRICTIONS",
        "udo_note": (
            f"Multifamily residential; up to 14 units per acre; "
            f"public sewer and water required. {_VERIFY}"
        ),
    },
    "C-LD": {
        "district_name": "Commercial-Low Density",
        "use_category": "commercial_low_density",
        "residential_use_screening": "NEEDS_REVIEW",
        "udo_note": (
            f"Low-density commercial (outlying/highway commercial); "
            f"residential compatibility requires review. {_VERIFY}"
        ),
    },
    "N-C": {
        "district_name": "Neighborhood-Commercial",
        "use_category": "commercial_neighborhood",
        "residential_use_screening": "NEEDS_REVIEW",
        "udo_note": (
            f"Neighborhood-scale office, retail, and personal services; "
            f"residential compatibility requires review. {_VERIFY}"
        ),
    },
    "C-I": {
        "district_name": "Commercial-Intensive",
        "use_category": "commercial_intensive",
        "residential_use_screening": "UNLIKELY_VERIFY",
        "udo_note": (
            f"Highway-intensive commercial, warehousing, and distribution; "
            f"residential uses typically not permitted. {_VERIFY}"
        ),
    },
    "RU-I": {
        "district_name": "Industrial-Rural",
        "use_category": "industrial_rural",
        "residential_use_screening": "UNLIKELY_VERIFY",
        "udo_note": (
            f"Rural agricultural-industrial; residential uses not permitted. {_VERIFY}"
        ),
    },
    "I-G": {
        "district_name": "Industrial-General",
        "use_category": "industrial_general",
        "residential_use_screening": "UNLIKELY_VERIFY",
        "udo_note": (
            f"General manufacturing and processing on major thoroughfares; "
            f"residential uses not permitted. {_VERIFY}"
        ),
    },
    "MI": {
        "district_name": "Military Installation",
        "use_category": "military_installation",
        "residential_use_screening": "NEEDS_REVIEW",
        "udo_note": (
            f"Military installation special purpose district; "
            f"residential uses vary; verify with Brunswick County Planning. {_VERIFY}"
        ),
    },
    "CP": {
        "district_name": "Conservation and Protection",
        "use_category": "conservation_protection",
        "residential_use_screening": "UNLIKELY_VERIFY",
        "udo_note": (
            f"Conservation and protection district for environmentally sensitive lands; "
            f"residential uses restricted or prohibited. {_VERIFY}"
        ),
    },
    "CZ": {
        "district_name": "Conditional Zoning",
        "use_category": "conditional_zoning_overlay",
        "residential_use_screening": "NEEDS_REVIEW",
        "udo_note": (
            f"Conditional zoning overlay; uses are set by individual conditional "
            f"zoning approval; verify base district and conditions. {_VERIFY}"
        ),
    },
    "ED": {
        "district_name": "Economic Development",
        "use_category": "economic_development_overlay",
        "residential_use_screening": "NEEDS_REVIEW",
        "udo_note": (
            f"Economic development overlay; permitted uses vary by overlay approval. {_VERIFY}"
        ),
    },
    "PD": {
        "district_name": "Planned Development",
        "use_category": "planned_development_overlay",
        "residential_use_screening": "NEEDS_REVIEW",
        "udo_note": (
            f"Planned development overlay; uses vary by approved plan. {_VERIFY}"
        ),
    },
    "TO": {
        "district_name": "Transitional Office",
        "use_category": "transitional_office_overlay",
        "residential_use_screening": "NEEDS_REVIEW",
        "udo_note": (
            f"Transitional office overlay; permitted uses vary by overlay approval. {_VERIFY}"
        ),
    },
    "WQP": {
        "district_name": "Water Quality Protection",
        "use_category": "water_quality_protection_overlay",
        "residential_use_screening": "NEEDS_REVIEW",
        "udo_note": (
            f"Water quality protection overlay; development restrictions may apply. {_VERIFY}"
        ),
    },
}


@dataclass(frozen=True)
class BrunswickZoningConnectorResult:
    retrieval_run: SourceRetrievalRunContract
    evidence_inputs: tuple[EvidenceContract, ...]


class BrunswickZoningRecordedConnector:
    """Recorded-fixture connector for Brunswick County UDO zoning district context.

    Uses a human-reviewed snapshot of the Brunswick County UDO (most recent revision
    2024-08-19). Does not perform live network requests. Output is screening-only and
    requires verification with Brunswick County Planning before any legal or permitting
    decision.
    """

    connector_name = BRUNSWICK_ZONING_CONNECTOR_NAME
    domain = "zoning"

    def query_district(
        self,
        *,
        area_id: UUID,
        zoning_code: str | None,
        source: SourceContract,
    ) -> BrunswickZoningConnectorResult:
        started_at = _utcnow()
        normalized = (zoning_code or "").strip().upper() if zoning_code else None

        ingest_run_id = _stable_uuid(
            "retrieval",
            str(source.source_id),
            str(area_id),
            normalized or "NONE",
        )

        if not normalized:
            return self._unknown_result(
                area_id=area_id,
                source=source,
                ingest_run_id=ingest_run_id,
                started_at=started_at,
                reason="no_zoning_code",
                note="No zoning code available from parcel data; context cannot be determined.",
            )

        district = _BRUNSWICK_UDO_DISTRICTS.get(normalized)
        if district is None:
            return self._needs_review_result(
                area_id=area_id,
                source=source,
                ingest_run_id=ingest_run_id,
                started_at=started_at,
                zoning_code=normalized,
            )

        return self._known_district_result(
            area_id=area_id,
            source=source,
            ingest_run_id=ingest_run_id,
            started_at=started_at,
            zoning_code=normalized,
            district=district,
        )

    def _known_district_result(
        self,
        *,
        area_id: UUID,
        source: SourceContract,
        ingest_run_id: UUID,
        started_at: datetime,
        zoning_code: str,
        district: dict[str, object],
    ) -> BrunswickZoningConnectorResult:
        finished_at = _utcnow()
        retrieval_run = SourceRetrievalRunContract(
            ingest_run_id=ingest_run_id,
            connector_name=self.connector_name,
            status=SourceRetrievalStatus.SUCCEEDED,
            started_at=started_at,
            finished_at=finished_at,
            row_count=1,
            error_count=0,
            warning_count=0,
            log_uri=BRUNSWICK_ZONING_UDO_URL,
            metrics={
                "source_registry_id": source.metadata.get("source_registry_id"),
                "udo_effective": BRUNSWICK_ZONING_UDO_EFFECTIVE,
                "udo_adopted": BRUNSWICK_ZONING_UDO_ADOPTED,
                "zoning_code": zoning_code,
                "lookup_type": "recorded_fixture",
            },
        )
        evidence = EvidenceContract(
            evidence_id=_stable_uuid(
                "evidence",
                str(source.source_id),
                str(area_id),
                zoning_code,
            ),
            area_id=area_id,
            evidence_type=EvidenceType.SOURCE_OBSERVATION,
            evidence_code="ZONING_USE_CLASSIFICATION",
            domain=self.domain,
            observation=(
                f"Brunswick County UDO zoning district lookup: code '{zoning_code}' "
                f"matches '{district['district_name']}'"
                f" (use category: {district['use_category']}). "
                "Screening only — verify with Brunswick County Planning."
            ),
            observed_value={
                "zoning_code": zoning_code,
                "district_name": district["district_name"],
                "use_category": district["use_category"],
                "residential_use_screening": district["residential_use_screening"],
                "udo_note": district["udo_note"],
                "udo_effective": BRUNSWICK_ZONING_UDO_EFFECTIVE,
                "udo_source_url": BRUNSWICK_ZONING_UDO_URL,
                "lookup_type": "recorded_fixture",
            },
            source_id=source.source_id,
            source_ingest_run_id=ingest_run_id,
            method_code=BRUNSWICK_ZONING_METHOD_CODE,
            method_version=BRUNSWICK_ZONING_METHOD_VERSION,
            confidence=ConfidenceBand.LOW,
            caveat=BRUNSWICK_ZONING_CAVEAT,
            is_source_failure=False,
            observed_at=finished_at,
            source_date=BRUNSWICK_ZONING_UDO_EFFECTIVE,
        )
        return BrunswickZoningConnectorResult(
            retrieval_run=retrieval_run,
            evidence_inputs=(evidence,),
        )

    def _needs_review_result(
        self,
        *,
        area_id: UUID,
        source: SourceContract,
        ingest_run_id: UUID,
        started_at: datetime,
        zoning_code: str,
    ) -> BrunswickZoningConnectorResult:
        finished_at = _utcnow()
        retrieval_run = SourceRetrievalRunContract(
            ingest_run_id=ingest_run_id,
            connector_name=self.connector_name,
            status=SourceRetrievalStatus.SUCCEEDED,
            started_at=started_at,
            finished_at=finished_at,
            row_count=1,
            error_count=0,
            warning_count=1,
            log_uri=BRUNSWICK_ZONING_UDO_URL,
            metrics={
                "source_registry_id": source.metadata.get("source_registry_id"),
                "udo_effective": BRUNSWICK_ZONING_UDO_EFFECTIVE,
                "zoning_code": zoning_code,
                "lookup_type": "recorded_fixture",
                "warning": "zoning_code_not_in_recorded_fixture",
            },
        )
        evidence = EvidenceContract(
            evidence_id=_stable_uuid(
                "evidence",
                str(source.source_id),
                str(area_id),
                zoning_code,
                "needs_review",
            ),
            area_id=area_id,
            evidence_type=EvidenceType.SOURCE_OBSERVATION,
            evidence_code="ZONING_EVIDENCE_NEEDS_REVIEW",
            domain=self.domain,
            observation=(
                f"Brunswick County zoning code '{zoning_code}' is not in the recorded UDO "
                "district fixture. District context cannot be determined from this connector. "
                "Verify zoning designation and permitted uses with Brunswick County Planning."
            ),
            observed_value={
                "zoning_code": zoning_code,
                "district_name": None,
                "use_category": None,
                "residential_use_screening": "NEEDS_REVIEW",
                "udo_note": "Zoning code not in recorded fixture; verify with Brunswick County Planning.",  # noqa: E501
                "udo_effective": BRUNSWICK_ZONING_UDO_EFFECTIVE,
                "udo_source_url": BRUNSWICK_ZONING_UDO_URL,
                "lookup_type": "recorded_fixture",
            },
            source_id=source.source_id,
            source_ingest_run_id=ingest_run_id,
            method_code=BRUNSWICK_ZONING_METHOD_CODE,
            method_version=BRUNSWICK_ZONING_METHOD_VERSION,
            confidence=ConfidenceBand.UNKNOWN,
            caveat=BRUNSWICK_ZONING_CAVEAT,
            is_source_failure=False,
            observed_at=finished_at,
            source_date=BRUNSWICK_ZONING_UDO_EFFECTIVE,
        )
        return BrunswickZoningConnectorResult(
            retrieval_run=retrieval_run,
            evidence_inputs=(evidence,),
        )

    def _unknown_result(
        self,
        *,
        area_id: UUID,
        source: SourceContract,
        ingest_run_id: UUID,
        started_at: datetime,
        reason: str,
        note: str,
    ) -> BrunswickZoningConnectorResult:
        finished_at = _utcnow()
        retrieval_run = SourceRetrievalRunContract(
            ingest_run_id=ingest_run_id,
            connector_name=self.connector_name,
            status=SourceRetrievalStatus.SUCCEEDED,
            started_at=started_at,
            finished_at=finished_at,
            row_count=0,
            error_count=0,
            warning_count=1,
            log_uri=BRUNSWICK_ZONING_UDO_URL,
            metrics={
                "source_registry_id": source.metadata.get("source_registry_id"),
                "udo_effective": BRUNSWICK_ZONING_UDO_EFFECTIVE,
                "reason": reason,
                "lookup_type": "recorded_fixture",
            },
        )
        evidence = EvidenceContract(
            evidence_id=_stable_uuid(
                "evidence",
                str(source.source_id),
                str(area_id),
                reason,
                "unknown",
            ),
            area_id=area_id,
            evidence_type=EvidenceType.SOURCE_OBSERVATION,
            evidence_code="ZONING_UNKNOWN",
            domain=self.domain,
            observation=f"Brunswick County zoning context is unknown: {note}",
            observed_value={
                "zoning_code": None,
                "district_name": None,
                "use_category": None,
                "residential_use_screening": "UNKNOWN",
                "reason": reason,
                "note": note,
                "udo_effective": BRUNSWICK_ZONING_UDO_EFFECTIVE,
                "udo_source_url": BRUNSWICK_ZONING_UDO_URL,
                "lookup_type": "recorded_fixture",
            },
            source_id=source.source_id,
            source_ingest_run_id=ingest_run_id,
            method_code=BRUNSWICK_ZONING_METHOD_CODE,
            method_version=BRUNSWICK_ZONING_METHOD_VERSION,
            confidence=ConfidenceBand.UNKNOWN,
            caveat=BRUNSWICK_ZONING_CAVEAT,
            is_source_failure=False,
            observed_at=finished_at,
            source_date=BRUNSWICK_ZONING_UDO_EFFECTIVE,
        )
        return BrunswickZoningConnectorResult(
            retrieval_run=retrieval_run,
            evidence_inputs=(evidence,),
        )


def _stable_uuid(*parts: str) -> UUID:
    return uuid5(_NAMESPACE, "|".join(parts))


def _utcnow() -> datetime:
    return datetime.now(UTC)


__all__ = [
    "BRUNSWICK_ZONING_CAVEAT",
    "BRUNSWICK_ZONING_CONNECTOR_NAME",
    "BRUNSWICK_ZONING_METHOD_CODE",
    "BRUNSWICK_ZONING_UDO_EFFECTIVE",
    "BRUNSWICK_ZONING_UDO_URL",
    "BrunswickZoningConnectorResult",
    "BrunswickZoningRecordedConnector",
]
