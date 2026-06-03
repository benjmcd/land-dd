# Backward-compatibility shim. Lane A owns the canonical code at:
#   app/source_registry/source_repo.py
# Do not add new code here. Lane A will delete this module.
from app.source_registry.source_repo import InMemorySourceRepository as InMemorySourceRepository
from app.source_registry.source_repo import SourceRepository as SourceRepository

__all__ = ["InMemorySourceRepository", "SourceRepository"]
