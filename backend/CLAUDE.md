@AGENTS.md

## Backend-specific Claude note
- Keep API handlers thin.
- Put business invariants in domain/service layers, not route functions.
- Add/adjust tests in `backend/tests/` for behavior changes.
