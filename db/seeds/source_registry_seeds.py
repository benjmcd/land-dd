from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, cast

from app.domain.enums import AuthorityLevel
from app.domain.source_contracts import SourceContract

ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_REGISTER_PATH = ROOT_DIR / "registers" / "data_source_registry.csv"
DEFAULT_PRIORITY = "Must"

_AUTHORITY_BY_SOURCE_TYPE = {
    "Public official": AuthorityLevel.OFFICIAL_PRIMARY,
    "Local official": AuthorityLevel.OFFICIAL_PRIMARY,
    "Local official/varies": AuthorityLevel.OFFICIAL_PRIMARY,
    "State official": AuthorityLevel.OFFICIAL_PRIMARY,
    "Commercial": AuthorityLevel.COMMERCIAL_NORMALIZED,
    "Open community/open data": AuthorityLevel.OPEN_COMMUNITY,
    "Public/stale official": AuthorityLevel.OFFICIAL_SECONDARY,
    "Nonprofit/open where available": AuthorityLevel.OFFICIAL_SECONDARY,
    "Professional/manual": AuthorityLevel.USER_SUPPLIED,
}


def load_seed_sources(
    register_path: Path = DEFAULT_REGISTER_PATH,
    *,
    priority: str = DEFAULT_PRIORITY,
) -> list[SourceContract]:
    rows = _load_rows(register_path)
    return [_row_to_source(row) for row in rows if row["MVP Priority"] == priority]


def _load_rows(register_path: Path) -> list[dict[str, str]]:
    with register_path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        return [dict(row) for row in reader]


def _row_to_source(row: dict[str, str]) -> SourceContract:
    url = _typed_homepage_url(row["URL"])
    metadata: dict[str, object] = {
        "source_registry_id": row["Source ID"],
        "source_type": row["Source Type"],
        "mvp_priority": row["MVP Priority"],
        "use": row["Use"],
        "caveats": row["Caveats"],
        "raw_url": row["URL"],
        "license_status": row["License Status"],
        "redistribution_status": row["Redistribution Status"],
        "attribution_required_status": row["Attribution Required"],
        "freshness_class": row["Freshness Class"],
        "last_checked_at": _optional_text(row["Last Checked At"]),
        "review_owner": row["Review Owner"],
        "review_status": row["Review Status"],
    }

    return SourceContract(
        name=row["Name"],
        organization=row["Organization"],
        homepage_url=url,
        source_type=row["Source Type"],
        authority_level=_authority_for(row["Source Type"]),
        domain=row["Domain"],
        geographic_scope=row["Geography"],
        update_cadence=row["Update Cadence"],
        license_status=row["License Status"],
        commercial_use_status=row["Commercial Use Status"],
        redistribution_status=row["Redistribution Status"],
        license_summary=row["Caveats"],
        attribution_required=_status_to_bool(row["Attribution Required"]),
        cache_allowed=row["Cache Allowed"],
        export_allowed=row["Export Allowed"],
        ai_use_allowed=row["AI Use Status"],
        raw_data_allowed=row["Raw Data Allowed"],
        freshness_class=row["Freshness Class"],
        last_checked_at=_optional_text(row["Last Checked At"]),
        review_owner=row["Review Owner"],
        review_status=row["Review Status"],
        notes=row["Use"],
        metadata=metadata,
    )


def _typed_homepage_url(raw_url: str) -> Any | None:
    if raw_url.startswith(("http://", "https://")):
        return cast(Any, raw_url)
    return None


def _authority_for(source_type: str) -> AuthorityLevel:
    return _AUTHORITY_BY_SOURCE_TYPE.get(source_type, AuthorityLevel.UNKNOWN)


def _optional_text(value: str) -> str | None:
    if not value.strip():
        return None
    return value


def _status_to_bool(value: str) -> bool:
    return value.strip().lower() == "yes"


__all__ = ["DEFAULT_PRIORITY", "DEFAULT_REGISTER_PATH", "load_seed_sources"]
