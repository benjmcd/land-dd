from __future__ import annotations

from enum import StrEnum


class AuthorityLevel(StrEnum):
    OFFICIAL_PRIMARY = "official_primary"
    OFFICIAL_SECONDARY = "official_secondary"
    COMMERCIAL_NORMALIZED = "commercial_normalized"
    OPEN_COMMUNITY = "open_community"
    DERIVED_MODEL = "derived_model"
    USER_SUPPLIED = "user_supplied"
    UNKNOWN = "unknown"


class ConfidenceBand(StrEnum):
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"
    UNKNOWN = "unknown"


class SeverityBand(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"
    UNKNOWN = "unknown"


class EvidenceType(StrEnum):
    SOURCE_OBSERVATION = "source_observation"
    SPATIAL_INTERSECTION = "spatial_intersection"
    DERIVED_METRIC = "derived_metric"
    DOCUMENT_EXTRACT = "document_extract"
    SOURCE_FAILURE = "source_failure"
    HUMAN_VERIFICATION = "human_verification"
    MANUAL_NOTE = "manual_note"


class AreaType(StrEnum):
    PARCEL_LIKE = "parcel_like"
    DRAWN_POLYGON = "drawn_polygon"
    MULTI_POLYGON = "multi_polygon"
    LOCALITY = "locality"
    BUFFER = "buffer"
    GENERATED_CANDIDATE = "generated_candidate"


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    NEEDS_REVIEW = "needs_review"


class IntentCode(StrEnum):
    """Intent codes that drive report evaluation.

    Values must exactly match the core.intent_code SQL enum defined in
    db/migrations/0001_initial_spine.sql. Two intents are seeded in
    db/seeds/001_seed_intents.sql; others are defined for future use.

    Do not add or rename values here without a coordinated schema migration.
    """

    RURAL_LAND_PURCHASE = "rural_land_purchase"
    HOMESTEAD_FEASIBILITY = "homestead_feasibility"
    FARMLAND = "farmland"
    DEVELOPMENT = "development"
    SOLAR = "solar"
    DATA_CENTER = "data_center"
    CONSERVATION = "conservation"
    MINERAL_RESOURCE_SCREEN = "mineral_resource_screen"
    SPECULATIVE_HOLD = "speculative_hold"
