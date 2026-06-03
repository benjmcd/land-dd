# Backward-compatibility shim. Lane A owns the canonical code at:
#   app/source_registry/service.py
# Do not add new code here. Lane A will delete this module.
from app.source_registry.service import SourceService as SourceService

__all__ = ["SourceService"]
