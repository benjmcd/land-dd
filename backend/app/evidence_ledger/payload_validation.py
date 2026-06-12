from __future__ import annotations

from typing import cast

from app.domain.enums import EvidenceType
from app.domain.evidence_contracts import EvidenceContract

SOURCE_FAILURE_ALLOWED_KEYS = {
    "attempted_url",
    "connector",
    "error_code",
    "error_message",
    "failure_reason",
    "not_evaluated",
    "reason",
    "retryable",
    "status_code",
}
SOURCE_OBSERVATION_ALLOWED_KEYS = {
    "flood_zone",
    "flood_zones",
    "flood_zone_code",
    "has_public_road_adjacency",
    "intended_residential_use_allowed",
    "intended_residential_use_prohibited",
    "jurisdiction_boundary_proximity",
    "jurisdiction_edge",
    "municipal_jurisdiction_possible",
    "monitoring_station_count",
    "nearby_well_log_count",
    "no_public_road_adjacency",
    "no_plausible_water_context",
    "observed_status",
    "plausible_water_context",
    "public_road_adjacency",
    "raw_value",
    "road_distance_m",
    "source_record_id",
    "source_stale",
    "source_url",
    "status",
    "value",
    "water_context_status",
    "zone",
    "zoning_district",
    # zoning connector fields (DS-023)
    "classification_indeterminate",
    "district_name",
    "lookup_type",
    "note",
    "reason",
    "residential_use_screening",
    "udo_effective",
    "udo_note",
    "udo_source_url",
    "use_category",
    "zoning_code",
    # env_hazard connector fields (DS-006)
    "epa_echo_bbox",
    "env_hazard_status",
    "has_env_hazard_proximity",
    "no_env_hazard_proximity",
    "regulated_facility_count",
    # BLM MLRS connector fields (DS-007)
    "blm_active_mining_claim_count",
    "blm_mlrs_bbox",
    "blm_mlrs_case_dispositions",
    "blm_mlrs_case_names",
    "blm_mlrs_case_serial_numbers",
    "blm_mlrs_case_type_numbers",
    "blm_mlrs_data_quality_notes",
    "blm_mlrs_layer_url",
    "blm_mlrs_legacy_case_serial_numbers",
    "blm_mlrs_products",
    "blm_mlrs_recorded_acres",
    "has_blm_active_mining_claim_context",
    "no_blm_active_mining_claim_context",
    "primary_blm_mlrs_case_name",
    "primary_blm_mlrs_case_serial_number",
    # broadband connector fields (DS-021)
    "fcc_bdc_lat",
    "fcc_bdc_lon",
    "has_any_broadband",
    "has_high_speed_broadband",
    "max_download_mbps",
    "max_upload_mbps",
    "provider_count",
    "technology_types",
    # climate connector fields (DS-020)
    "has_nws_coverage",
    "nws_forecast_zone",
    "nws_forecast_zone_name",
    "nws_nearest_city",
    "nws_nearest_state",
    "nws_office_code",
    "nws_radar_station",
    "timezone",
    # Census TIGER connector fields (DS-022)
    "census_block_group_count",
    "census_block_group_geoids",
    "census_demographics_used",
    "census_tiger_bbox",
    "census_tiger_vintage",
    "census_tract_count",
    "census_tract_geoids",
    "has_census_geography_context",
    "primary_census_block_group_geoid",
    "primary_census_block_group_name",
    "primary_census_tract_geoid",
    "primary_census_tract_name",
    # USGS MRDS connector fields (DS-008)
    "has_mineral_occurrence_context",
    "mineral_commodity_codes",
    "mineral_deposit_ids",
    "mineral_development_statuses",
    "mineral_occurrence_count",
    "mineral_rights_determined",
    "mineral_site_names",
    "mrds_bbox",
    "mrds_record_urls",
    "mrds_systematic_updates_ceased",
    "no_mineral_occurrence_context",
    "primary_mineral_deposit_id",
    "primary_mineral_development_status",
    "primary_mineral_site_name",
    # NC geologic map connector fields (DS-015)
    "buildability_determined",
    "geologic_belts",
    "geologic_descriptions",
    "geologic_formations",
    "geologic_hazard_determined",
    "geologic_types",
    "geologic_unit_count",
    "geologic_unit_labels",
    "has_geologic_map_context",
    "nc_geologic_map_bbox",
    "nc_geologic_map_deprecated",
    "nc_geologic_map_year",
    "no_geologic_map_context",
    "primary_geologic_formation",
    "primary_geologic_unit_label",
}
SPATIAL_INTERSECTION_KEYS = {
    "flood_zone",
    "flood_zones",
    "flood_zone_code",
    "geometry_relation",
    "has_public_road_adjacency",
    "intersection_area_sq_m",
    "intersection_ratio",
    "intersects",
    "intersects_high_risk_flood_zone",
    "intersects_mapped_wetlands",
    "mapped_wetland_area_sq_m",
    "no_public_road_adjacency",
    "public_road_adjacency",
    "road_distance_m",
    "source_stale",
    "drainage_class",
    "wetland_type",
    "wetland_types",
    "hydric_rating",
    "hydrologic_group",
    "intersects_soil_mapunit",
    "slope_percent",
    "soil_component_key",
    "soil_component_name",
    "soil_component_percent",
    "soil_major_component",
    "soil_mapunit_key",
    "soil_mapunit_name",
    "soil_mapunit_symbol",
    "parcel_pin",
    "parcel_county",
    "parcel_owner",
    "parcel_land_value",
    "parcel_bldg_value",
    "parcel_total_value",
    "parcel_acres",
    "parcel_zoning",
    "parcel_address",
    "parcel_city",
    "parcel_state",
    "parcel_zip",
    # wetland connector fields
    "acres_approx",
    "source_note",
    "wetland_class",
    "wetland_system",
    # soils connector fields
    "dominant_condition",
    "dominant_map_unit",
    "water_table_depth_cm",
    # parcel connector fields
    "owner_display",
    "parcel_class",
    "parcel_count",
    "total_acres_approx",
    # osm road access connector fields
    "lookup_type",
    "osm_query_bbox",
    "road_count",
    # usgs water monitoring connector fields
    "monitoring_station_count",
    "water_context_status",
    "usgs_water_bbox",
    "plausible_water_context",
    "no_plausible_water_context",
    # env_hazard connector fields (DS-006)
    "epa_echo_bbox",
    "env_hazard_status",
    "has_env_hazard_proximity",
    "no_env_hazard_proximity",
    "regulated_facility_count",
}
SPATIAL_RESULT_KEYS = {
    "flood_zone",
    "flood_zones",
    "flood_zone_code",
    "geometry_relation",
    "has_public_road_adjacency",
    "intersects",
    "intersects_high_risk_flood_zone",
    "intersects_mapped_wetlands",
    "intersects_soil_mapunit",
    "no_public_road_adjacency",
    "public_road_adjacency",
    # domain-specific presence indicators (wetland/soils/parcel connectors)
    "drainage_class",
    "parcel_count",
    "wetland_type",
    # water monitoring presence indicators (DS-005)
    "plausible_water_context",
    "no_plausible_water_context",
    # env_hazard presence indicators (DS-006)
    "has_env_hazard_proximity",
    "no_env_hazard_proximity",
}
DERIVED_METRIC_KEYS = {
    "calculation_method",
    "insufficient_low_slope_buildable_area",
    "low_slope_buildable_area_sufficient",
    "low_slope_area_ratio",
    "max_elevation_m",
    "mean_elevation_m",
    "mean_slope_pct",
    "metric_code",
    "min_elevation_m",
    "relief_m",
    "sample_count",
    "screening_note",
    "source_stale",
    "unit",
    "value",
}
DOCUMENT_EXTRACT_KEYS = {
    "document_id",
    "document_title",
    "extract_text",
    "page",
    "section",
}
HUMAN_NOTE_ALLOWED_KEYS = {
    "note_status",
    "reviewer_role",
    "review_scope",
}


def validate_observed_value(evidence: EvidenceContract) -> None:
    _validate_payload_shape(evidence)
    match evidence.evidence_type:
        case EvidenceType.SOURCE_OBSERVATION:
            _validate_source_observation(evidence)
        case EvidenceType.SPATIAL_INTERSECTION:
            _validate_spatial_intersection(evidence)
        case EvidenceType.DERIVED_METRIC:
            _validate_derived_metric(evidence)
        case EvidenceType.DOCUMENT_EXTRACT:
            _validate_document_extract(evidence)
        case EvidenceType.SOURCE_FAILURE:
            _validate_source_failure(evidence)
        case EvidenceType.HUMAN_VERIFICATION | EvidenceType.MANUAL_NOTE:
            _validate_human_note(evidence)


def _validate_payload_shape(evidence: EvidenceContract) -> None:
    for key, value in evidence.observed_value.items():
        if not key.strip():
            raise ValueError("observed_value keys must be non-empty")
        if not _is_allowed_value(value):
            raise ValueError(
                f"{evidence.evidence_type} observed_value '{key}' must be a scalar "
                "or list of scalars"
            )


def _validate_source_observation(evidence: EvidenceContract) -> None:
    if not evidence.observed_value:
        raise ValueError("source_observation observed_value must contain at least one field")
    unknown_keys = set(evidence.observed_value) - SOURCE_OBSERVATION_ALLOWED_KEYS
    if unknown_keys:
        raise ValueError(
            "source_observation observed_value contains unsupported fields: "
            f"{', '.join(sorted(unknown_keys))}"
        )
    for key in (
        "classification_indeterminate",
        "intended_residential_use_allowed",
        "intended_residential_use_prohibited",
        "jurisdiction_edge",
        "municipal_jurisdiction_possible",
        "no_plausible_water_context",
        "plausible_water_context",
        "source_stale",
        "has_env_hazard_proximity",
        "no_env_hazard_proximity",
        "has_blm_active_mining_claim_context",
        "no_blm_active_mining_claim_context",
        "has_census_geography_context",
        "census_demographics_used",
        "has_mineral_occurrence_context",
        "mineral_rights_determined",
        "no_mineral_occurrence_context",
        "buildability_determined",
        "geologic_hazard_determined",
        "has_geologic_map_context",
        "nc_geologic_map_deprecated",
        "no_geologic_map_context",
    ):
        if key in evidence.observed_value and not isinstance(evidence.observed_value[key], bool):
            raise ValueError(f"source_observation observed_value '{key}' must be boolean")
    if "nearby_well_log_count" in evidence.observed_value:
        _require_non_negative_number(
            evidence.observed_value["nearby_well_log_count"],
            "nearby_well_log_count",
        )
    if "monitoring_station_count" in evidence.observed_value:
        _require_non_negative_number(
            evidence.observed_value["monitoring_station_count"],
            "monitoring_station_count",
        )
    if "regulated_facility_count" in evidence.observed_value:
        _require_non_negative_number(
            evidence.observed_value["regulated_facility_count"],
            "regulated_facility_count",
        )
    if "blm_active_mining_claim_count" in evidence.observed_value:
        _require_non_negative_number(
            evidence.observed_value["blm_active_mining_claim_count"],
            "blm_active_mining_claim_count",
        )
    if "census_tract_count" in evidence.observed_value:
        _require_non_negative_number(
            evidence.observed_value["census_tract_count"],
            "census_tract_count",
        )
    if "census_block_group_count" in evidence.observed_value:
        _require_non_negative_number(
            evidence.observed_value["census_block_group_count"],
            "census_block_group_count",
        )
    if "mineral_occurrence_count" in evidence.observed_value:
        _require_non_negative_number(
            evidence.observed_value["mineral_occurrence_count"],
            "mineral_occurrence_count",
        )
    if "geologic_unit_count" in evidence.observed_value:
        _require_non_negative_number(
            evidence.observed_value["geologic_unit_count"],
            "geologic_unit_count",
        )


def _validate_spatial_intersection(evidence: EvidenceContract) -> None:
    if not evidence.observed_value:
        raise ValueError("spatial_intersection observed_value must contain spatial result fields")
    unknown_keys = set(evidence.observed_value) - SPATIAL_INTERSECTION_KEYS
    if unknown_keys:
        raise ValueError(
            "spatial_intersection observed_value contains unsupported fields: "
            f"{', '.join(sorted(unknown_keys))}"
        )
    if not any(key in evidence.observed_value for key in SPATIAL_RESULT_KEYS):
        raise ValueError("spatial_intersection observed_value must contain a spatial result field")
    for key in (
        "intersects",
        "intersects_high_risk_flood_zone",
        "has_public_road_adjacency",
        "intersects_mapped_wetlands",
        "intersects_soil_mapunit",
        "no_public_road_adjacency",
        "public_road_adjacency",
        "soil_major_component",
        "plausible_water_context",
        "no_plausible_water_context",
        "has_env_hazard_proximity",
        "no_env_hazard_proximity",
    ):
        if key in evidence.observed_value and not isinstance(evidence.observed_value[key], bool):
            raise ValueError(f"spatial_intersection observed_value '{key}' must be boolean")
    for key in (
        "intersection_area_sq_m",
        "intersection_ratio",
        "mapped_wetland_area_sq_m",
        "road_distance_m",
        "slope_percent",
        "soil_component_percent",
        "monitoring_station_count",
        "regulated_facility_count",
    ):
        if key in evidence.observed_value:
            _require_non_negative_number(evidence.observed_value[key], key)
    ratio = evidence.observed_value.get("intersection_ratio")
    if ratio is not None and cast(int | float, ratio) > 1:
        raise ValueError("intersection_ratio must be less than or equal to 1")


def _validate_derived_metric(evidence: EvidenceContract) -> None:
    unknown_keys = set(evidence.observed_value) - DERIVED_METRIC_KEYS
    if unknown_keys:
        raise ValueError(
            "derived_metric observed_value contains unsupported fields: "
            f"{', '.join(sorted(unknown_keys))}"
        )
    metric_code = evidence.observed_value.get("metric_code")
    if not isinstance(metric_code, str) or not metric_code.strip():
        raise ValueError("derived_metric observed_value requires non-empty metric_code")
    value = evidence.observed_value.get("value")
    if not _is_number(value):
        raise ValueError("derived_metric observed_value requires numeric value")
    unit = evidence.observed_value.get("unit")
    if unit is not None and (not isinstance(unit, str) or not unit.strip()):
        raise ValueError("derived_metric observed_value unit must be non-empty when present")
    for key in (
        "insufficient_low_slope_buildable_area",
        "low_slope_buildable_area_sufficient",
        "source_stale",
    ):
        if key in evidence.observed_value and not isinstance(evidence.observed_value[key], bool):
            raise ValueError(f"derived_metric observed_value '{key}' must be boolean")


def _validate_document_extract(evidence: EvidenceContract) -> None:
    if not any(key in evidence.observed_value for key in DOCUMENT_EXTRACT_KEYS):
        raise ValueError("document_extract observed_value must contain document/extract fields")
    unknown_keys = set(evidence.observed_value) - DOCUMENT_EXTRACT_KEYS
    if unknown_keys:
        raise ValueError(
            "document_extract observed_value contains unsupported fields: "
            f"{', '.join(sorted(unknown_keys))}"
        )
    extract_text = evidence.observed_value.get("extract_text")
    if extract_text is not None and (not isinstance(extract_text, str) or not extract_text.strip()):
        raise ValueError("document_extract observed_value extract_text must be non-empty")


def _validate_source_failure(evidence: EvidenceContract) -> None:
    unknown_keys = set(evidence.observed_value) - SOURCE_FAILURE_ALLOWED_KEYS
    if unknown_keys:
        raise ValueError(
            "source_failure observed_value contains unsupported fields: "
            f"{', '.join(sorted(unknown_keys))}"
        )
    for key in ("error_code", "error_message", "failure_reason"):
        value = evidence.observed_value.get(key)
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise ValueError(f"source_failure observed_value '{key}' must be non-empty text")
    status_code = evidence.observed_value.get("status_code")
    if status_code is not None:
        _require_non_negative_number(status_code, "status_code")
    retryable = evidence.observed_value.get("retryable")
    if retryable is not None and not isinstance(retryable, bool):
        raise ValueError("source_failure observed_value 'retryable' must be boolean")


def _validate_human_note(evidence: EvidenceContract) -> None:
    unknown_keys = set(evidence.observed_value) - HUMAN_NOTE_ALLOWED_KEYS
    if unknown_keys:
        raise ValueError(
            "human note observed_value contains unsupported fields: "
            f"{', '.join(sorted(unknown_keys))}"
        )


def _require_non_negative_number(value: object, field_name: str) -> None:
    if not _is_number(value):
        raise ValueError(f"{field_name} must be numeric")
    numeric_value = cast(int | float, value)
    if numeric_value < 0:
        raise ValueError(f"{field_name} must be non-negative")


def _is_allowed_value(value: object) -> bool:
    if _is_scalar(value):
        return True
    if isinstance(value, list):
        return all(_is_scalar(item) for item in value)
    return False


def _is_scalar(value: object) -> bool:
    return value is None or isinstance(value, str | int | float | bool)


def _is_number(value: object) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


__all__ = ["validate_observed_value"]
