from __future__ import annotations

from app.domain.enums import AuthorityLevel
from app.domain.source_contracts import SourceContract


def test_source_contract_includes_license_and_authority_fields() -> None:
    source = SourceContract(
        name="Fixture Source",
        organization="Fixture Org",
        authority_level=AuthorityLevel.OFFICIAL_PRIMARY,
        domain="fixture",
        commercial_use_status="unknown",
        cache_allowed="unknown",
        export_allowed="unknown",
        ai_use_allowed="unknown",
    )
    assert source.authority_level == AuthorityLevel.OFFICIAL_PRIMARY
    assert source.cache_allowed == "unknown"


def test_source_contract_stores_geographic_scope_and_cadence() -> None:
    source = SourceContract(
        name="FEMA NFHL",
        organization="FEMA",
        domain="flood",
        commercial_use_status="yes",
        geographic_scope="US",
        update_cadence="continuous",
    )
    assert source.geographic_scope == "US"
    assert source.update_cadence == "continuous"


def test_source_contract_defaults_usage_flags_to_unknown() -> None:
    source = SourceContract(name="Minimal Source", domain="test", commercial_use_status="unknown")
    assert source.ai_use_allowed == "unknown"
    assert source.export_allowed == "unknown"
    assert source.attribution_required is False
