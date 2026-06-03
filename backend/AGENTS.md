# backend/AGENTS.md

Backend-specific guidance:
- API routes must stay thin.
- Domain contracts own validation semantics.
- Services/repositories should be fixture-testable without live vendors.
- Do not import DB engine at module import time in tests unless needed.
