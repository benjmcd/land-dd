"""Backward-compatibility re-exports. Import from per-lane contract modules instead."""
from __future__ import annotations

from app.domain.claim_contracts import ClaimContract as ClaimContract
from app.domain.evidence_contracts import EvidenceContract as EvidenceContract
from app.domain.source_contracts import SourceContract as SourceContract

__all__ = ["ClaimContract", "EvidenceContract", "SourceContract"]
