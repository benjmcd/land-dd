from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
GOLDEN_AOI_DIR = ROOT / "tests" / "fixtures" / "golden_aois"
CONNECTOR_FIXTURE_DIR = ROOT / "tests" / "fixtures" / "connectors"
MANIFEST_PATH = GOLDEN_AOI_DIR / "manifest.yaml"

REQUIRED_CASE_FIELDS = {
    "case_id",
    "county",
    "state",
    "intent",
    "geometry_file",
    "connector_fixture_files",
    "expected_connector_workflow_domains",
    "expected_not_evaluated_domains",
    "forbidden_claims",
}

ALLOWED_CONNECTOR_DOMAINS = {"flood", "access", "zoning", "buildability"}
EXPECTED_NOT_EVALUATED_DOMAINS = {"parcels", "assessor"}
SUPPORTED_COUNTIES = {"buncombe", "chatham", "brunswick"}
EXPECTED_STATE = "nc"

MANIFEST_FORBIDDEN_PHRASES = (
    "legal access",
    "legal boundary",
    "zoning entitlement",
    "septic suitability",
    "wetland jurisdiction",
    "buildability",
    "property value",
    "good investment",
)


def _load_manifest() -> dict[str, Any]:
    data: Any = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    return data  # type: ignore[no-any-return]


def _load_geojson(geometry_file: str) -> dict[str, Any]:
    path = GOLDEN_AOI_DIR / geometry_file
    data: Any = json.loads(path.read_text(encoding="utf-8"))
    return data  # type: ignore[no-any-return]


def test_manifest_file_exists() -> None:
    assert MANIFEST_PATH.exists(), f"Golden AOI manifest not found at {MANIFEST_PATH}"


def test_manifest_loads_as_yaml() -> None:
    manifest = _load_manifest()
    assert isinstance(manifest, dict), "Manifest YAML must be a mapping"
    assert "cases" in manifest, "Manifest must have a 'cases' key"


def test_manifest_has_nine_cases() -> None:
    manifest = _load_manifest()
    cases = manifest["cases"]
    assert len(cases) == 9, f"Expected 9 golden AOI cases, got {len(cases)}"


def test_all_case_ids_are_unique() -> None:
    manifest = _load_manifest()
    ids = [case["case_id"] for case in manifest["cases"]]
    assert len(ids) == len(set(ids)), f"Duplicate case_ids found: {ids}"


def test_required_fields_present_for_each_case() -> None:
    manifest = _load_manifest()
    for case in manifest["cases"]:
        case_id = case.get("case_id", "<unknown>")
        missing = REQUIRED_CASE_FIELDS - set(case.keys())
        assert not missing, (
            f"Case {case_id!r} is missing required fields: {sorted(missing)}"
        )


def test_all_counties_are_valid() -> None:
    manifest = _load_manifest()
    for case in manifest["cases"]:
        county = case["county"]
        assert county in SUPPORTED_COUNTIES, (
            f"Case {case['case_id']!r} has unsupported county {county!r}; "
            f"expected one of {sorted(SUPPORTED_COUNTIES)}"
        )


def test_all_states_are_nc() -> None:
    manifest = _load_manifest()
    for case in manifest["cases"]:
        assert case["state"] == EXPECTED_STATE, (
            f"Case {case['case_id']!r} has state {case['state']!r}; expected {EXPECTED_STATE!r}"
        )


def test_all_geometry_files_exist() -> None:
    manifest = _load_manifest()
    for case in manifest["cases"]:
        case_id = case["case_id"]
        geometry_file = case["geometry_file"]
        path = GOLDEN_AOI_DIR / geometry_file
        assert path.exists(), (
            f"Case {case_id!r}: geometry_file {geometry_file!r} not found at {path}"
        )


def test_all_geometry_files_are_valid_wgs84_polygons() -> None:
    manifest = _load_manifest()
    for case in manifest["cases"]:
        case_id = case["case_id"]
        geojson = _load_geojson(case["geometry_file"])

        geom = geojson.get("geometry") or geojson
        assert geom.get("type") == "Polygon", (
            f"Case {case_id!r}: geometry type must be 'Polygon', got {geom.get('type')!r}"
        )

        coords = geom.get("coordinates", [])
        assert coords and len(coords) > 0, (
            f"Case {case_id!r}: geometry has no coordinate rings"
        )

        ring = coords[0]
        assert len(ring) >= 4, (
            f"Case {case_id!r}: exterior ring must have at least 4 points (closed polygon)"
        )

        for lon, lat in ring:
            assert -180.0 <= lon <= 180.0, (
                f"Case {case_id!r}: longitude {lon} out of WGS84 range"
            )
            assert -90.0 <= lat <= 90.0, (
                f"Case {case_id!r}: latitude {lat} out of WGS84 range"
            )

        assert ring[0] == ring[-1], (
            f"Case {case_id!r}: polygon ring is not closed (first != last coordinate)"
        )


def test_all_connector_fixture_files_exist() -> None:
    manifest = _load_manifest()
    for case in manifest["cases"]:
        case_id = case["case_id"]
        for domain, filename in case["connector_fixture_files"].items():
            path = CONNECTOR_FIXTURE_DIR / filename
            assert path.exists(), (
                f"Case {case_id!r}: connector fixture file for domain {domain!r} "
                f"({filename!r}) not found at {path}"
            )


def test_connector_fixture_domains_are_supported() -> None:
    manifest = _load_manifest()
    for case in manifest["cases"]:
        case_id = case["case_id"]
        for domain in case["connector_fixture_files"]:
            assert domain in ALLOWED_CONNECTOR_DOMAINS, (
                f"Case {case_id!r}: connector domain {domain!r} not in "
                f"supported domains {ALLOWED_CONNECTOR_DOMAINS}. "
                "Only flood, access, zoning, and buildability fixture connectors exist."
            )


def test_expected_connector_domains_match_fixture_files() -> None:
    manifest = _load_manifest()
    for case in manifest["cases"]:
        case_id = case["case_id"]
        fixture_domains = set(case["connector_fixture_files"].keys())
        expected_domains = set(case["expected_connector_workflow_domains"])
        assert fixture_domains == expected_domains, (
            f"Case {case_id!r}: connector_fixture_files domains {fixture_domains} "
            f"do not match expected_connector_workflow_domains {expected_domains}"
        )


def test_all_cases_declare_parcels_and_assessor_as_not_evaluated() -> None:
    manifest = _load_manifest()
    for case in manifest["cases"]:
        case_id = case["case_id"]
        not_evaluated = set(case["expected_not_evaluated_domains"])
        assert EXPECTED_NOT_EVALUATED_DOMAINS <= not_evaluated, (
            f"Case {case_id!r}: expected_not_evaluated_domains must include "
            f"{sorted(EXPECTED_NOT_EVALUATED_DOMAINS)}; got {sorted(not_evaluated)}"
        )


def test_all_cases_have_forbidden_claims_list() -> None:
    manifest = _load_manifest()
    for case in manifest["cases"]:
        case_id = case["case_id"]
        claims = case["forbidden_claims"]
        assert isinstance(claims, list) and len(claims) > 0, (
            f"Case {case_id!r}: forbidden_claims must be a non-empty list"
        )


def test_manifest_prose_does_not_contain_forbidden_phrases() -> None:
    manifest = _load_manifest()
    prose_fields = ("description", "case_id", "county", "state", "intent")
    for case in manifest["cases"]:
        case_id = case.get("case_id", "<unknown>")
        for field in prose_fields:
            value = str(case.get(field, "")).lower()
            for phrase in MANIFEST_FORBIDDEN_PHRASES:
                assert phrase.lower() not in value, (
                    f"Case {case_id!r} field {field!r} contains forbidden phrase "
                    f"{phrase!r}. Use hedged, caveat-first language in prose fields."
                )


def test_each_county_has_at_least_two_cases() -> None:
    manifest = _load_manifest()
    from collections import Counter
    counts: Counter[str] = Counter(case["county"] for case in manifest["cases"])
    for county in SUPPORTED_COUNTIES:
        assert counts[county] >= 2, (
            f"County {county!r} has only {counts[county]} case(s); expected at least 2"
        )
