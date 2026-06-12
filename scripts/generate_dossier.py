#!/usr/bin/env python3
"""One-shot land due-diligence dossier generator (in-memory, no DB required).

Usage (from repo root)::

    py -3.12 scripts/generate_dossier.py \\
        --aoi tests/fixtures/golden_aois/bun_flood.geojson \\
        --intent rural_land_purchase
    py -3.12 scripts/generate_dossier.py \\
        --aoi tests/fixtures/golden_aois/cha_rural_use.geojson \\
        --intent homestead_feasibility --output /tmp/report.md
    py -3.12 scripts/generate_dossier.py --connector flood \\
        --aoi tests/fixtures/golden_aois/bru_coastal_flood.geojson \\
        --intent rural_land_purchase
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from uuid import UUID

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.api.dependencies import create_api_services  # noqa: E402
from app.connectors import (  # noqa: E402
    StaticAccessFixtureConnector,
    StaticBuildabilityFixtureConnector,
    StaticFloodFixtureConnector,
    StaticParcelFixtureConnector,
    StaticSoilsFixtureConnector,
    StaticTerrainFixtureConnector,
    StaticWetlandsFixtureConnector,
    StaticZoningFixtureConnector,
    build_connector_review_handoff,
    build_connector_run_review_packet,
    build_connector_run_review_status,
    build_fixture_workflow_with_public_lane_services,
    evaluate_access_fixture_quality,
    evaluate_buildability_fixture_quality,
    evaluate_flood_fixture_quality,
    evaluate_parcel_fixture_quality,
    evaluate_soils_fixture_quality,
    evaluate_terrain_fixture_quality,
    evaluate_wetlands_fixture_quality,
    evaluate_zoning_fixture_quality,
)
from app.connectors.fixture_resources import (  # noqa: E402
    fixture_dataset_contract,
    fixture_dataset_version_contract,
)
from app.connectors.review_handoff import ConnectorReviewDisposition  # noqa: E402
from app.domain.area_contracts import AreaContract  # noqa: E402
from app.domain.enums import IntentCode  # noqa: E402
from app.domain.source_contracts import SourceContract  # noqa: E402
from app.reports.dossier import build_rural_land_dossier  # noqa: E402

_FIXTURE_SOURCE_ID = UUID("55555555-5555-4555-8555-555555555555")
_FIXTURE_AREA_ID = UUID("44444444-4444-4444-8444-444444444444")

CONNECTOR_DIR = ROOT_DIR / "tests" / "fixtures" / "connectors"

# AOI stem prefix -> county segment used in fixture filenames
_AOI_PREFIX_TO_COUNTY: dict[str, str] = {
    "bun": "buncombe",
    "cha": "chatham",
    "bru": "brunswick",
}

_CONNECTOR_CHOICES = ("flood", "access", "zoning", "parcels", "buildability", "soils", "terrain", "wetlands", "all")

_CONNECTOR_CLS = {
    "flood": StaticFloodFixtureConnector,
    "access": StaticAccessFixtureConnector,
    "zoning": StaticZoningFixtureConnector,
    "parcels": StaticParcelFixtureConnector,
    "buildability": StaticBuildabilityFixtureConnector,
    "soils": StaticSoilsFixtureConnector,
    "terrain": StaticTerrainFixtureConnector,
    "wetlands": StaticWetlandsFixtureConnector,
}

_QUALITY_EVALUATORS = {
    "flood": evaluate_flood_fixture_quality,
    "access": evaluate_access_fixture_quality,
    "zoning": evaluate_zoning_fixture_quality,
    "parcels": evaluate_parcel_fixture_quality,
    "buildability": evaluate_buildability_fixture_quality,
    "soils": evaluate_soils_fixture_quality,
    "terrain": evaluate_terrain_fixture_quality,
    "wetlands": evaluate_wetlands_fixture_quality,
}

_INTENT_MAP: dict[str, IntentCode] = {
    "rural_land_purchase": IntentCode.RURAL_LAND_PURCHASE,
    "homestead_feasibility": IntentCode.HOMESTEAD_FEASIBILITY,
}


def _load_geojson_geometry(path: Path) -> dict[str, object]:
    data: object = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict), f"expected GeoJSON dict, got {type(data)}"
    if data.get("type") == "Feature":
        geom = data["geometry"]
    else:
        geom = data
    assert isinstance(geom, dict), f"expected geometry dict, got {type(geom)}"
    return geom


def _resolve_fixture_path(aoi_path: Path, connector: str) -> Path:
    """Derive the connector fixture path from the AOI filename.

    Convention: nc_<county>_<aoi_stem>_<connector>.json
    e.g. bun_flood.geojson + flood -> nc_buncombe_bun_flood_flood.json
    """
    aoi_stem = aoi_path.stem  # e.g. "bun_flood"
    prefix = aoi_stem.split("_")[0]  # e.g. "bun"
    county = _AOI_PREFIX_TO_COUNTY.get(prefix)
    if county is None:
        raise ValueError(
            f"Cannot derive county for AOI prefix {prefix!r}. "
            f"Known prefixes: {list(_AOI_PREFIX_TO_COUNTY)}"
        )
    fixture_name = f"nc_{county}_{aoi_stem}_{connector}.json"
    fixture_path = CONNECTOR_DIR / fixture_name
    if not fixture_path.exists():
        raise FileNotFoundError(
            f"Connector fixture not found: {fixture_path}\n"
            f"Available fixtures in {CONNECTOR_DIR}:\n"
            + "\n".join(f"  {p.name}" for p in sorted(CONNECTOR_DIR.glob("*.json")))
        )
    return fixture_path


def main() -> int:  # noqa: C901
    parser = argparse.ArgumentParser(
        description="Generate a land due-diligence dossier using in-memory services."
    )
    parser.add_argument(
        "--aoi",
        required=True,
        help="Path to a GeoJSON AOI file (Feature or Geometry).",
    )
    parser.add_argument(
        "--intent",
        required=True,
        choices=list(_INTENT_MAP),
        help="Intent code for the report run.",
    )
    parser.add_argument(
        "--connector",
        default="flood",
        choices=list(_CONNECTOR_CHOICES),
        help="Fixture connector to run (default: flood).",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Write dossier to this file path instead of stdout.",
    )
    args = parser.parse_args()

    aoi_path = Path(args.aoi)
    if not aoi_path.is_absolute():
        # Resolve relative to cwd so the script works from repo root or backend/
        aoi_path = Path.cwd() / aoi_path
    aoi_path = aoi_path.resolve()

    if not aoi_path.exists():
        print(f"ERROR: AOI file not found: {aoi_path}", file=sys.stderr)
        return 1

    print(f"[generate_dossier] AOI: {aoi_path}", file=sys.stderr)
    print(f"[generate_dossier] Intent: {args.intent}", file=sys.stderr)
    print(f"[generate_dossier] Connector: {args.connector}", file=sys.stderr)

    # Load geometry
    try:
        geom = _load_geojson_geometry(aoi_path)
    except Exception as exc:
        print(f"ERROR: Failed to load GeoJSON: {exc}", file=sys.stderr)
        return 1

    # Create in-memory services
    services = create_api_services()

    # Register fixture source (all 8 usage fields set to "approved")
    services.source_service.register(
        SourceContract(
            source_id=_FIXTURE_SOURCE_ID,
            name="CLI Fixture Source",
            organization="fixture",
            domain="fixture",
            license_status="approved",
            commercial_use_status="approved",
            redistribution_status="approved",
            cache_allowed="approved",
            export_allowed="approved",
            raw_data_allowed="approved",
            ai_use_allowed="approved",
            review_status="approved",
        )
    )

    # Register fixture dataset + version so the provenance service accepts the retrieval run.
    # Fixture files embed dataset_version_id=FIXTURE_DATASET_VERSION_ID; this must exist first.
    services.source_provenance_service.ensure_dataset(fixture_dataset_contract())
    services.source_provenance_service.ensure_dataset_version(fixture_dataset_version_contract())

    # Register area
    services.area_service.create(
        AreaContract(
            area_id=_FIXTURE_AREA_ID,
            label=f"cli-{aoi_path.stem}",
            geom_geojson=geom,
            geom_source="cli-aoi-input",
        )
    )

    if args.connector == "all":
        # Run all three connectors in sequence; warn-and-continue on missing fixtures
        _CONNECTOR_SEQUENCE = ("parcels", "flood", "access", "zoning", "buildability", "soils", "terrain", "wetlands")
        total_evidence = 0
        for connector_name in _CONNECTOR_SEQUENCE:
            print(
                f"[generate_dossier] Running connector: {connector_name}...",
                file=sys.stderr,
            )
            try:
                fixture_path = _resolve_fixture_path(aoi_path, connector_name)
            except (ValueError, FileNotFoundError) as exc:
                print(
                    f"[generate_dossier] WARNING: Skipping {connector_name}: {exc}",
                    file=sys.stderr,
                )
                continue

            print(f"[generate_dossier] Fixture: {fixture_path.name}", file=sys.stderr)

            connector_cls = _CONNECTOR_CLS[connector_name]
            quality_evaluator = _QUALITY_EVALUATORS[connector_name]
            workflow = build_fixture_workflow_with_public_lane_services(
                source_provenance_service=services.source_provenance_service,
                evidence_service=services.evidence_service,
                connector=connector_cls(),
                quality_evaluator=quality_evaluator,
            )

            try:
                workflow_result = workflow.ingest_fixture(fixture_path)
            except Exception as exc:
                print(
                    f"[generate_dossier] WARNING: Connector {connector_name} workflow failed: {exc}",
                    file=sys.stderr,
                )
                continue

            ingest_run_id = workflow_result.connector_result.retrieval_run.ingest_run_id
            evidence_created = len(workflow_result.evidence_ingestion.created_evidence)
            total_evidence += evidence_created
            print(
                f"[generate_dossier] {connector_name}: {evidence_created} evidence records created.",
                file=sys.stderr,
            )

            # Build review packet + handoff; auto-approve if eligible
            packet = build_connector_run_review_packet(workflow_result)
            handoff = build_connector_review_handoff(packet)
            quality_profile = quality_evaluator(workflow_result.connector_result)
            review_status = build_connector_run_review_status(handoff, quality_profile)

            services.connector_review_queue.enqueue_review_status(review_status)
            if handoff.disposition == ConnectorReviewDisposition.READY_FOR_CONNECTOR_QA:
                services.connector_review_queue.approve_for_connector_qa(
                    ingest_run_id,
                    reviewer_id="cli",
                    reason="auto-approved by generate_dossier",
                )
                print(
                    f"[generate_dossier] {connector_name}: Auto-approved for connector QA.",
                    file=sys.stderr,
                )
            else:
                print(
                    f"[generate_dossier] {connector_name}: Disposition: {handoff.disposition.value} "
                    "(evidence may not appear in report without human review).",
                    file=sys.stderr,
                )

        print(
            f"[generate_dossier] All connectors complete: {total_evidence} evidence records created.",
            file=sys.stderr,
        )
    else:
        # Single-connector path — existing behavior unchanged
        try:
            fixture_path = _resolve_fixture_path(aoi_path, args.connector)
        except (ValueError, FileNotFoundError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1

        print(f"[generate_dossier] Fixture: {fixture_path.name}", file=sys.stderr)
        print("[generate_dossier] Running fixture connector workflow...", file=sys.stderr)

        connector_cls = _CONNECTOR_CLS[args.connector]
        quality_evaluator = _QUALITY_EVALUATORS[args.connector]

        workflow = build_fixture_workflow_with_public_lane_services(
            source_provenance_service=services.source_provenance_service,
            evidence_service=services.evidence_service,
            connector=connector_cls(),
            quality_evaluator=quality_evaluator,
        )

        try:
            workflow_result = workflow.ingest_fixture(fixture_path)
        except Exception as exc:
            print(f"ERROR: Connector workflow failed: {exc}", file=sys.stderr)
            return 1

        ingest_run_id = workflow_result.connector_result.retrieval_run.ingest_run_id
        evidence_created = len(workflow_result.evidence_ingestion.created_evidence)
        print(
            f"[generate_dossier] Workflow complete: {evidence_created} evidence records created.",
            file=sys.stderr,
        )

        # Build review packet + handoff to determine auto-approval eligibility
        packet = build_connector_run_review_packet(workflow_result)
        handoff = build_connector_review_handoff(packet)
        quality_profile = quality_evaluator(workflow_result.connector_result)
        review_status = build_connector_run_review_status(handoff, quality_profile)

        # Enqueue and auto-approve if READY_FOR_CONNECTOR_QA
        services.connector_review_queue.enqueue_review_status(review_status)
        if handoff.disposition == ConnectorReviewDisposition.READY_FOR_CONNECTOR_QA:
            services.connector_review_queue.approve_for_connector_qa(
                ingest_run_id,
                reviewer_id="cli",
                reason="auto-approved by generate_dossier",
            )
            print("[generate_dossier] Auto-approved for connector QA.", file=sys.stderr)
        else:
            print(
                f"[generate_dossier] Disposition: {handoff.disposition.value} "
                "(evidence may not appear in report without human review).",
                file=sys.stderr,
            )

    # Create report run
    intent_code = _INTENT_MAP[args.intent]
    print(f"[generate_dossier] Creating report run (intent={intent_code})...", file=sys.stderr)

    try:
        report_run = services.report_service.create_report_run(
            area_id=_FIXTURE_AREA_ID,
            intent_code=intent_code,
        )
    except Exception as exc:
        print(f"ERROR: Report run failed: {exc}", file=sys.stderr)
        return 1

    print(
        f"[generate_dossier] Report run status: {report_run.status}",
        file=sys.stderr,
    )

    # Build dossier
    dossier = build_rural_land_dossier(report_run)

    # Output
    if args.output:
        out_path = Path(args.output)
        out_path.write_text(dossier, encoding="utf-8")
        print(f"[generate_dossier] Dossier written to: {out_path}", file=sys.stderr)
    else:
        print(dossier)

    return 0


if __name__ == "__main__":
    sys.exit(main())
